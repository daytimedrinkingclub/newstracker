from flask import Blueprint, render_template, jsonify, request, redirect, url_for, session, flash
from ..models.data_service import DataService
from ..services.supabase_auth import is_authenticated, get_user
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
    return render_template('onboarding/plans.html', plans=user_plans)

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

@bp.route('/keyword/<int:keyword_id>', methods=['DELETE'])
@login_required
def delete_keyword(keyword_id):
    result = DataService.delete_user_keyword(keyword_id)
    return jsonify(success=bool(result)), 200 if result else 404

@bp.route('/keyword/<int:keyword_id>', methods=['PUT'])
@login_required
def update_keyword(keyword_id):
    new_keyword = request.json.get('keyword')
    updated_keyword = DataService.update_user_keyword(keyword_id, new_keyword)
    return jsonify(success=bool(updated_keyword), keyword=updated_keyword), 200 if updated_keyword else 404

@bp.route('/keyword/startanalysis/<uuid:keyword_id>')
@login_required
def keyword_analysis(keyword_id):
    user = get_user(session['jwt'])
    keyword = DataService.get_keyword_by_id(str(keyword_id))
    if not keyword or keyword['user_id'] != user['id']:
        return redirect(url_for('main.keyword'))
    conversation = DataService.load_conversation(str(keyword_id))

    return render_template('main/news.html', keyword=keyword, conversation=conversation)


@bp.route('/refreshanalysis/<uuid:keyword_id>', methods=['GET'])
@login_required
def refresh_analysis(keyword_id):
    user = get_user(session['jwt'])
    keyword = DataService.get_keyword_analysis_details(str(keyword_id))
    if not keyword or keyword.user_id != user['id']:
        return redirect(url_for('main.keyword'))
    return jsonify(keyword=keyword.dict())

@bp.route('/keywordsummary/<uuid:keyword_id>', methods=['GET'])
@login_required
def get_news_summary(keyword_id):
    user = get_user(session['jwt'])
    keyword = DataService.get_keyword_analysis_details(str(keyword_id))
    
    if not keyword or keyword.user_id != user['id']:
        flash('Keyword not found or you do not have permission to view it.', 'error')
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