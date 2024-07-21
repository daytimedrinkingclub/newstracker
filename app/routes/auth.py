# app/routes/auth.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, g
from ..services.supabase_auth import sign_up, sign_in, sign_out, get_user
from ..models.data_service import DataService

bp = Blueprint('auth', __name__)

@bp.route('/', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        response = sign_up(email, password)
        if response is None:
            flash('Sign up failed. Please try again.')
            return redirect(url_for('auth.signup'))
        
        if 'error' in response:
            flash(response['error']['message'])
            return redirect(url_for('auth.signup'))
        
        if 'session' not in response or 'access_token' not in response.get('session', {}):
            flash('Sign up successful, but login failed. Please log in manually.')
            return redirect(url_for('auth.login'))
        
        session['jwt'] = response['session']['access_token']
        return redirect(url_for('main.plans'))
        
    return render_template('auth/signup.html')

@bp.route('/login', methods=['GET', 'POST']) 
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        response = sign_in(email, password)
        if 'error' in response:
            flash('Please check your login details and try again.')
            return redirect(url_for('auth.login'))
        
        session['jwt'] = response['session']['access_token']
        user = get_user(session['jwt'])
        user_plans = DataService.get_user_plans(user['id'])
        
        if user_plans:
            return redirect(url_for('main.keyword'))
        else:
            return redirect(url_for('main.plans'))
    
    return render_template('auth/login.html')

@bp.route('/logout')
def logout():
    try:
        session.clear()
        return redirect(url_for('auth.login'))
    except Exception as e:
        print(f"Error during sign out: {str(e)}")
        return redirect(url_for('auth.login'))

@bp.before_request
def load_user():
    jwt = session.get('jwt')
    if jwt:
        user = get_user(jwt)
        if user:
            g.user = user
        else:
            session.pop('jwt', None)