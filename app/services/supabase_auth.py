from app.supabase_config import get_supabase_client
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import jwt

def sign_up(email: str, password: str) -> Dict[str, Any]:
    supabase = get_supabase_client()
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password,
        })
        if response.user:
            # Create a record in the users table
            supabase.table('users').insert({
                'id': response.user.id,
                'email': email
            }).execute()
        return response.dict()
    except Exception as e:
        print(f"Sign up error: {str(e)}")
        return None

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

def get_user(jwt_token: str) -> Optional[Dict[str, Any]]:
    supabase = get_supabase_client()
    try:
        # Decode the JWT token to check its expiration
        decoded_token = jwt.decode(jwt_token, options={"verify_signature": False})
        exp = datetime.fromtimestamp(decoded_token['exp'])
        if exp < datetime.utcnow():
            raise ValueError("Token is expired")

        response = supabase.auth.get_user(jwt_token)
        return response.user.dict() if response.user else None
    except jwt.ExpiredSignatureError:
        raise ValueError("Token is expired")
    except Exception as e:
        raise e

def is_authenticated(jwt: str) -> bool:
    user = get_user(jwt)
    return user is not None