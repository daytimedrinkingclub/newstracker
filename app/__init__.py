# backend/app/__init__.py
from flask import Flask
from datetime import datetime
from dotenv import load_dotenv
import os
from .config import config
from .extensions import init_extensions
from .routes import auth, main
from jinja2 import Undefined
import logging

# Load environment variables
load_dotenv()

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

log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.log')
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filename=log_file_path,
                    filemode='a')

def create_app():
    app = Flask(__name__, static_folder='static', static_url_path='/static')
    app.config.from_object(config)
    
    # Initialize extensions
    init_extensions(app)
    
    # Register blueprints
    app.register_blueprint(auth.bp)
    app.register_blueprint(main.bp)
    
    # Register custom Jinja2 filter
    app.jinja_env.filters['to_datetime'] = to_datetime
    
    return app