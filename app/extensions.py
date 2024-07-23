# backend/app/extensions.py
from app.supabase_config import get_supabase_client


print("Initializing extensions...")

supabase = None

def init_extensions(app):
    print("Running init_extensions...")
    
    global supabase
    supabase = get_supabase_client()
    
    print("Extensions initialized successfully")