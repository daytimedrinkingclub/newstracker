from supabase import create_client, Client
from app.config import config
import os

url = config.SUPABASE_URL
key = config.SUPABASE_KEY


print(f"SUPABASE_URL: {url}")
print(f"SUPABASE_KEY: {key}")

if not url or not key:
    print("Current working directory:", os.getcwd())
    print("Environment variables:")
    for k, v in os.environ.items():
        print(f"{k}: {v}")
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in the environment. Check your .env file and its location.")

supabase: Client = create_client(url, key)

def get_supabase_client():
    print("Getting supabase client...")
    return supabase