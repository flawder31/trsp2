import uuid
import time
from datetime import datetime
from typing import Optional, Tuple
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

SECRET_KEY = "your-secret-key-here-change-in-production-2024"
SERIALIZER = URLSafeTimedSerializer(SECRET_KEY)

USERS_DB = {
    "user123": {
        "password": "password123",
        "user_id": str(uuid.uuid4()),
        "username": "user123",
        "email": "user123@example.com"
    }
}

SESSIONS_DB = {}


def create_session_token(user_id: str, timestamp: int = None) -> str:
    if timestamp is None:
        timestamp = int(time.time())
    
    data = f"{user_id}.{timestamp}"
    signature = SERIALIZER.dumps(data)
    
    return signature


def verify_session_token(token: str) -> Tuple[Optional[str], Optional[int]]:
    try:
        data = SERIALIZER.loads(token, max_age=300)
        
        parts = data.split('.')
        if len(parts) != 2:
            return None, None
        
        user_id = parts[0]
        timestamp = int(parts[1])
        
        return user_id, timestamp
    except (BadSignature, SignatureExpired, ValueError, IndexError):
        return None, None


def validate_and_update_session(token: str, request_time: int) -> Tuple[Optional[str], Optional[str], bool]:
    user_id, token_timestamp = verify_session_token(token)
    
    if user_id is None or token_timestamp is None:
        return None, None, False
    
    time_passed = request_time - token_timestamp
    
    if time_passed > 300:
        return None, None, False
    
    should_update = time_passed >= 180
    
    if user_id in SESSIONS_DB:
        SESSIONS_DB[user_id]['last_activity'] = request_time
    
    return user_id, token, should_update


def authenticate_user(username: str, password: str) -> Optional[dict]:
    user = USERS_DB.get(username)
    if user and user['password'] == password:
        return user
    return None


def get_user_profile(user_id: str) -> Optional[dict]:
    for username, user_data in USERS_DB.items():
        if user_data['user_id'] == user_id:
            return {
                "user_id": user_id,
                "username": username,
                "email": user_data['email']
            }
    return None