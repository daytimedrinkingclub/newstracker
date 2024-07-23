# backend/app/__init__.py
from app.config import config
from datetime import datetime
from flask import Flask
from redis import Redis
from rq import Queue
from dotenv import load_dotenv
import os
from app.extensions import init_extensions
from app.routes import auth, main
from jinja2 import Undefined

def to_datetime(value, format='%B %d, %Y'):
    if isinstance(value, Undefined):
        return ''
    try:
        if isinstance(value, str):
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        else:
            dt = value
        return dt.strftime(format)
    except ValueError:
        return value

def create_app():
    app = Flask(__name__)
    app.config.from_object(config)

    # Initialize extensions
    init_extensions(app)
    
    # Set up Redis connection
    # Set up Redis connection
    app.redis = Redis.from_url(app.config['REDIS_URL'])
    app.task_queue = Queue(connection=app.redis)
    
    
    # Register blueprints
    app.register_blueprint(auth.bp)
    app.register_blueprint(main.bp)
    
    # Register custom Jinja2 filter
    app.jinja_env.filters['to_datetime'] = to_datetime
    
    return app