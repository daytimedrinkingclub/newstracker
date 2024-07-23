from flask import Blueprint, render_template, jsonify, request, redirect, url_for, session, flash
from rq import get_current_job
from rq.job import Job
from rq.exceptions import NoSuchJobError
from ..redis_config import get_redis_connection
from ..utils.redis_task_manager import enqueue_task, get_task_status
from ..models.data_service import DataService
from ..services.supabase_auth import is_authenticated, get_user
from ..services.agent import AnthropicChat
from ..tasks import analyze_keyword
from functools import wraps
from flask import current_app

bp = Blueprint('main', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        jwt = session.get('jwt')
        if not jwt or not is_authenticated(jwt):
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/plans')
@login_required
def plans():
    user = get_user(session['jwt'])
    user_plans = DataService.get_user_plans(user['id'])
    print(user_plans)
    if user_plans and len(user_plans) > 0:
        current_plan = user_plans[0]['plan']
    else:
        current_plan = None
    return render_template('onboarding/plans.html', plans=user_plans, current_plan=current_plan)

@bp.route('/plan', methods=['POST', 'PUT', 'DELETE'])
@login_required
def manage_plan():
    user = get_user(session['jwt'])
    if request.method == 'POST':
        plan = request.json.get('plan')
        anthropic_api_key = request.json.get('anthropic_api_key')
        tavily_api_key = request.json.get('tavily_api_key')
        new_plan = DataService.add_user_plan(user['id'], plan)
        DataService.update_user_api_tokens(user['id'], anthropic_api_key, tavily_api_key)
        return jsonify(success=True, redirect=url_for('main.keyword')), 200
    elif request.method == 'PUT':
        plan_id = request.json.get('id')
        new_plan = request.json.get('plan')
        anthropic_api_key = request.json.get('anthropic_api_key')
        tavily_api_key = request.json.get('tavily_api_key')
        updated_plan = DataService.update_user_plan(plan_id, new_plan)
        DataService.update_user_api_tokens(user['id'], anthropic_api_key, tavily_api_key)
        return jsonify(updated_plan), 200
    elif request.method == 'DELETE':
        plan_id = request.json.get('id')
        success = DataService.delete_user_plan(plan_id)
        DataService.delete_user_api_tokens(user['id'])
        return jsonify(success=success), 200 if success else 400

@bp.route('/keyword')
@login_required
def keyword():
    user = get_user(session['jwt'])
    user_keywords = DataService.get_user_keywords(user['id'])
    return render_template('onboarding/keyword.html', keywords=user_keywords)

@bp.route('/keyword', methods=['POST'])
@login_required
def add_keyword():
    user = get_user(session['jwt'])
    keyword = request.form.get('keyword')
    if not keyword:
        return jsonify(success=False, error="Keyword is required"), 400
    new_keyword = DataService.add_user_keyword(user['id'], keyword)
    if new_keyword:
        return jsonify(success=True, keyword=new_keyword), 201
    else:
        return jsonify(success=False, error="Failed to add keyword"), 500

@bp.route('/keyword/<uuid:keyword_id>', methods=['DELETE'])
@login_required
def delete_keyword(keyword_id):
    result = DataService.delete_user_keyword(str(keyword_id))
    if result:
        return jsonify(success=True), 200
    else:
        return jsonify(success=False, error="Keyword not found"), 404

@bp.route('/keyword/<int:keyword_id>', methods=['PUT'])
@login_required
def update_keyword(keyword_id):
    new_keyword = request.json.get('keyword')
    updated_keyword = DataService.update_user_keyword(keyword_id, new_keyword)
    return jsonify(success=bool(updated_keyword), keyword=updated_keyword), 200 if updated_keyword else 404

@bp.route('/keywordsummary/<uuid:keyword_id>', methods=['GET'])
@login_required
def get_news_summary(keyword_id):
    user = get_user(session['jwt'])
    keyword = DataService.get_keyword_analysis_details(str(keyword_id))
    
    if not keyword:
        flash('Keyword not found.', 'error')
        return redirect(url_for('main.feed'))
    
    if keyword['user_id'] != user['id']:
        flash('You do not have permission to view this keyword analysis.', 'error')
        return redirect(url_for('main.feed'))
    
    return render_template('main/news.html', keyword=keyword)

@bp.route('/feed')
@login_required
def feed():
    user = get_user(session['jwt'])
    feed_data = DataService.get_news_feed(user['id'])
    return render_template('main/feed.html', feed_data=feed_data)    

@bp.route('/feed/<uuid:keyword_id>/news')
@login_required
def keyword_feed(keyword_id):
    user = get_user(session['jwt'])
    feed_data = DataService.get_news_details(user['id'], keyword_id)
    return render_template('main/news.html', feed_data=feed_data)

@bp.route('/refreshanalysis/<uuid:keyword_id>', methods=['GET'])
@login_required
def refresh_analysis(keyword_id):
    print(f"Entering refresh_analysis for keyword_id: {keyword_id}")
    user = get_user(session['jwt'])
    print(f"User: {user['id']}")
    keyword = DataService.get_keyword_by_id(str(keyword_id))
    print(f"Keyword: {keyword}")
    
    if not keyword or keyword['user_id'] != user['id']:
        print("Keyword not found or permission denied")
        return jsonify(success=False, error="Keyword not found or you don't have permission to refresh it."), 404
    
    try:
        existing_analysis = DataService.get_active_analysis_for_keyword(str(keyword_id))
        print(f"Existing analysis: {existing_analysis}")
        
        if existing_analysis:
            if existing_analysis['status'] == 'queued':
                try:
                    redis_conn = get_redis_connection()
                    job = Job.fetch(existing_analysis['job_id'], connection=redis_conn)
                    if job.is_failed:
                        raise NoSuchJobError
                    print(f"Existing queued job found: {job.id}")
                    return jsonify(success=True, status='queued', message="Analysis is queued and will start soon.", job_id=job.id), 200
                except NoSuchJobError:
                    print(f"Queued job not found in Redis for analysis_id: {existing_analysis['id']}. Creating a new job.")
                    DataService.update_analysis_status(existing_analysis['id'], 'failed')
                except Exception as e:
                    print(f"Error fetching job from Redis: {str(e)}")
                    # Continue to create a new analysis
            else:
                print(f"Active analysis already exists for keyword_id: {keyword_id}")
                return jsonify(success=True, status='in_progress', message="An analysis is already in progress for this keyword."), 200
        
        # Create a new keyword analysis
        print("Creating new keyword analysis")
        new_keyword_analysis_id = DataService.create_keyword_analysis(user['id'], str(keyword_id), None)
        print(f"New keyword analysis id: {new_keyword_analysis_id}")
        
        # Enqueue the task using redis_task_manager
        try:
            print("Enqueueing analyze_keyword task")
            job = enqueue_task(analyze_keyword, current_app.config['ANTHROPIC_API_KEY'], keyword['keyword'], new_keyword_analysis_id)
            print(f"Enqueued job: {job}")
            
            # Update the keyword_analysis with the job_id and set status to 'queued'
            print("Updating analysis status and job_id")
            DataService.update_analysis_status(new_keyword_analysis_id, 'queued')
            DataService.update_analysis_job_id(new_keyword_analysis_id, job.id)
            
            print("Returning success response")
            return jsonify(success=True, message="Analysis refresh initiated", keyword=keyword['keyword'], analysis_id=new_keyword_analysis_id, job_id=job.id), 202
        except Exception as e:
            print(f"Error enqueueing task: {str(e)}")
            DataService.update_analysis_status(new_keyword_analysis_id, 'failed')
            return jsonify(success=False, error="Failed to start analysis. Please try again."), 500
        
    except Exception as e:
        print(f"Error in refresh_analysis: {str(e)}")
        return jsonify(success=False, error=f"An error occurred: {str(e)}"), 500

@bp.route('/task_status/<job_id>', methods=['GET'])
@login_required
def task_status(job_id):
    analysis = DataService.get_analysis_by_job_id(job_id)
    if analysis:
        return jsonify(status=analysis['status'])
    return jsonify(status='not_found')

def analyze_keyword(anthropic_api_key, keyword, analysis_id):
    from flask import current_app
    with current_app.app_context():
        try:
            job = get_current_job()
            print(f"Starting analyze_keyword for analysis_id: {analysis_id}, keyword: {keyword}")
            
            # Update analysis status to 'in_progress'
            update_success = DataService.update_analysis_status(analysis_id, 'in_progress')
            print(f"Updated analysis status to 'in_progress': {update_success}")
            
            # Start the recursive analysis
            print("Initiating recursive_analysis")
            recursive_analysis(keyword, analysis_id, 1)
            
            print(f"analyze_keyword completed for analysis_id: {analysis_id}")
            
        except Exception as e:
            print(f"Error in analyze_keyword task: {str(e)}")
            # Update the analysis status to indicate failure
            update_success = DataService.update_analysis_status(analysis_id, 'failed')
            print(f"Updated analysis status to 'failed': {update_success}")

def recursive_analysis(keyword, analysis_id, step, max_steps=20):
    try:
        print(f"Starting recursive_analysis step {step} for analysis_id: {analysis_id}")
        
        if step > max_steps:
            raise Exception(f"Analysis exceeded maximum steps ({max_steps})")

        # Perform the analysis step
        print(f"Calling AnthropicChat.handle_chat for analysis_id: {analysis_id}")
        response = AnthropicChat.handle_chat(analysis_id, keyword, current_app.config['ANTHROPIC_API_KEY'])
        print(f"AnthropicChat.handle_chat response: {response}")
        
        # Check if the analysis is complete
        if response.get('status') == 'completed':
            print(f"Analysis completed for analysis_id: {analysis_id}")
            # Update the keyword summary with the final results
            update_success = DataService.update_keyword_summary(
                analysis_id,
                news_summary=response.get('news_summary', ''),
                positive_summary=response.get('positive_summary', ''),
                negative_summary=response.get('negative_summary', ''),
                positive_sources_links=response.get('positive_sources_links', ''),
                negative_sources_links=response.get('negative_sources_links', '')
            )
            print(f"Updated keyword summary: {update_success}")
            
            if not update_success:
                raise Exception("Failed to update keyword summary")
            
            # Update analysis status to 'completed'
            status_update = DataService.update_analysis_status(analysis_id, 'completed')
            print(f"Updated analysis status to 'completed': {status_update}")
        else:
            # Update the analysis status with the current step
            status_update = DataService.update_analysis_status(analysis_id, f'in_progress (step {step})')
            print(f"Updated analysis status to 'in_progress (step {step})': {status_update}")
            
            # Enqueue the next step
            print(f"Enqueueing next step for analysis_id: {analysis_id}")
            job = enqueue_task(recursive_analysis, keyword, analysis_id, step + 1, max_steps)
            print(f"Enqueued job: {job}")

    except Exception as e:
        print(f"Error in recursive_analysis task: {str(e)}")
        # Update the analysis status to indicate failure
        status_update = DataService.update_analysis_status(analysis_id, 'failed')
        print(f"Updated analysis status to 'failed': {status_update}")