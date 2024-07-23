import os
from dotenv import load_dotenv

# Get the directory of the current file (config.py)
current_dir = os.path.dirname(os.path.abspath(__file__))
# Construct the path to the .env file
dotenv_path = os.path.join(current_dir, '.env')

print(f"Attempting to load .env file from: {dotenv_path}")
# Load environment variables from .env file
load_dotenv(dotenv_path)

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
    DEBUG = os.getenv('FLASK_DEBUG', '0') == '1'  
    REDIS_HOST = os.getenv('REDIS_HOST', 'redis-17458.c98.us-east-1-4.ec2.redns.redis-cloud.com')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 17458))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', 'Kabeer@Seth@271998')
    REDIS_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0"
# Print loaded environment variables for debugging
print("Loaded environment variables:")
for key, value in Config.__dict__.items():
    if not key.startswith('__'):
        print(f"{key}: {value}")

# Use a single Config class
config = Config()