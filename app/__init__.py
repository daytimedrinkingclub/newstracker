from flask import Flask
from app.config import config
from app.extensions import init_extensions
from app.routes import auth, main

def create_app():
    app = Flask(__name__)
    app.config.from_object(config)
    
    # Initialize extensions
    init_extensions(app)
    
    # Register blueprints
    app.register_blueprint(auth.bp)
    app.register_blueprint(main.bp)
    
    return app