import os
from dotenv import load_dotenv

# Load environment variables from .env for development
load_dotenv()

class Config(object):
    SECRET_KEY = os.getenv('SECRET_KEY')
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')
    SUPABASE_JWT_SECRET = os.getenv('SUPABASE_JWT_SECRET')
    PAYPAL_CLIENT_ID = os.getenv('PAYPAL_CLIENT_ID')
    PAYPAL_CLIENT_SECRET = os.getenv('PAYPAL_CLIENT_SECRET')
    FLASK_ENV = os.getenv('FLASK_ENV')
    DEBUG = os.getenv('FLASK_ENV') == 'development'

# Use a single Config class
config = Config()