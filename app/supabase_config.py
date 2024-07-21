from supabase import create_client, Client
from app.config import config

url = config.SUPABASE_URL
key = config.SUPABASE_KEY

if not url or not key:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in the environment")

supabase: Client = create_client(url, key)

def get_supabase_client():
    return supabase