from flask import Blueprint, render_template, jsonify, request, redirect, url_for, session, flash
import logging
from ..models.data_service import DataService
from ..services.supabase_auth import is_authenticated, get_user
from ..services.agent import AnthropicChat
from functools import wraps
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
    try:
        new_keyword = DataService.add_user_keyword(user['id'], keyword)
        return jsonify(success=True, keyword=new_keyword), 201
    except Exception as e:
        logging.error(f"Error adding keyword for user {user['id']}: {str(e)}")
        return jsonify(success=False, error=str(e)), 400

@bp.route('/keyword/<uuid:keyword_id>', methods=['DELETE'])
@login_required
def delete_keyword(keyword_id):
    user = get_user(session['jwt'])
    result = DataService.delete_user_keyword(str(keyword_id))
    if result:
        logging.info(f"Successfully deleted keyword {keyword_id} for user {user['id']}")
        return jsonify(success=True), 200
    else:
        logging.warning(f"Failed to delete keyword {keyword_id} for user {user['id']}")
        return jsonify(success=False, error="Failed to delete keyword or keyword not found"), 404

@bp.route('/feed')
@login_required
def feed():
    user = get_user(session['jwt'])
    feed_data = DataService.get_news_feed(user['id'])
    return render_template('main/feed.html', feed_data=feed_data)

@bp.route('/feed/<uuid:keyword_id>/summary')
@login_required
def get_news_summary(keyword_id):
    user = get_user(session['jwt'])
    keyword = DataService.get_keyword_analysis_details(keyword_id)
    if keyword:
        return render_template('main/news.html', keyword=keyword)
    else:
        flash('Summary not found', 'error')
        return redirect(url_for('main.feed'))

@bp.route('/feed/<uuid:keyword_id>/news')
@login_required
def keyword_feed(keyword_id):
    feed_data = DataService.get_news_details(keyword_id)
    return render_template('main/news.html', feed_data=feed_data)

@bp.route('/startanalysis/<uuid:keyword_id>', methods=['POST'])
@login_required
def start_analysis(keyword_id):
    logging.info(f"Entering start_analysis for keyword_id: {keyword_id}")
    user = get_user(session['jwt'])
    logging.info(f"User: {user['id']}")
    keyword = DataService.get_keyword_by_id(keyword_id)
    logging.info(f"Keyword: {keyword}")
    
    try:
        # Check if there's an active analysis for this keyword
        active_analysis = DataService.get_active_analysis_for_keyword(str(keyword_id))
        
        if active_analysis:
            logging.info(f"Reusing existing analysis: {active_analysis['id']}")
            analysis_id = active_analysis['id']
        else:
            logging.info("Creating new analysis")
            analysis_id = DataService.create_keyword_analysis(str(user['id']), str(keyword_id))
        
        if not analysis_id:
            raise Exception("Failed to create or retrieve analysis")
        
        # Start the analysis
        result = AnthropicChat.handle_chat(str(user['id']), keyword_id=str(keyword_id), analysis_id=analysis_id)
        
        return jsonify(success=True, analysis_id=analysis_id, status=result['status'], message=result['message']), 200
    except Exception as e:
        logging.error(f"Error starting analysis: {str(e)}")
        return jsonify(success=False, message=str(e)), 400

@bp.route('/task_status/<uuid:keyword_id>', methods=['GET'])
@login_required
def task_status(keyword_id):
    analysis = DataService.get_latest_analysis_for_keyword(str(keyword_id))
    if analysis:
        response = {
            'status': analysis['status'],
            'job_id': analysis['job_id']
        }
        
        # Include error message if it exists and status is 'failed'
        if analysis['status'] == 'failed' and analysis.get('error_message'):
            response['error_message'] = analysis['error_message']
        
        # Include updated_at timestamp
        if analysis.get('updated_at'):
            response['updated_at'] = analysis['updated_at']
        
        return jsonify(response)
    
    return jsonify(status='not_found'), 404