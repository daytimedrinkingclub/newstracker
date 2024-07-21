from datetime import datetime
from flask import Flask
from app.config import config
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
    
    # Register blueprints
    app.register_blueprint(auth.bp)
    app.register_blueprint(main.bp)
    
    # Register custom Jinja2 filter
    app.jinja_env.filters['to_datetime'] = to_datetime
    
    return app