from app.supabase_config import get_supabase_client
from typing import Dict, Any, Optional

def sign_up(email: str, password: str) -> Dict[str, Any]:
    supabase = get_supabase_client()
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password,
        })
        print(f"Sign up response: {response}")  # Add this line for debugging
        return response.dict()
    except Exception as e:
        print(f"Sign up error: {str(e)}")
        return {"error": {"message": str(e)}}

def sign_in(email: str, password: str) -> Dict[str, Any]:
    supabase = get_supabase_client()
    response = supabase.auth.sign_in_with_password({
        "email": email,
        "password": password,
    })
    return response.dict()

def sign_out(jwt: str) -> None:
    supabase = get_supabase_client()
    supabase.auth.sign_out(jwt)

def anonymous_sign_in() -> Dict[str, Any]:
    supabase = get_supabase_client()
    response = supabase.auth.sign_in_with_password({})
    return response.dict()

def get_user(jwt: str) -> Optional[Dict[str, Any]]:
    supabase = get_supabase_client()
    response = supabase.auth.get_user(jwt)
    return response.user.dict() if response.user else None

def is_authenticated(jwt: str) -> bool:
    user = get_user(jwt)
    return user is not None