import time
import base64
import json
import hmac
import hashlib
from typing import Optional, Dict
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.config import settings
from backend.database import get_db_connection

security = HTTPBearer(auto_error=False)

def create_jwt_token(payload: dict, expires_in_seconds: int = 86400) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    header_bytes = base64.urlsafe_b64encode(json.dumps(header).encode('utf-8')).decode('utf-8').rstrip("=")
    
    body = payload.copy()
    body["exp"] = int(time.time()) + expires_in_seconds
    body_bytes = base64.urlsafe_b64encode(json.dumps(body).encode('utf-8')).decode('utf-8').rstrip("=")
    
    signature_raw = hmac.new(
        settings.SECRET_KEY.encode('utf-8'),
        f"{header_bytes}.{body_bytes}".encode('utf-8'),
        hashlib.sha256
    ).digest()
    sig_bytes = base64.urlsafe_b64encode(signature_raw).decode('utf-8').rstrip("=")
    
    return f"{header_bytes}.{body_bytes}.{sig_bytes}"

def decode_jwt_token(token: str) -> Optional[dict]:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_b64, body_b64, sig_b64 = parts
        
        # Verify signature
        expected_sig = hmac.new(
            settings.SECRET_KEY.encode('utf-8'),
            f"{header_b64}.{body_b64}".encode('utf-8'),
            hashlib.sha256
        ).digest()
        actual_sig = base64.urlsafe_b64decode(sig_b64 + "=" * (-len(sig_b64) % 4))
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None
            
        body_json = base64.urlsafe_b64decode(body_b64 + "=" * (-len(body_b64) % 4)).decode('utf-8')
        payload = json.loads(body_json)
        
        # Check expiry
        if payload.get("exp", 0) < time.time():
            return None
            
        return payload
    except Exception:
        return None

def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[Dict]:
    if not credentials:
        return None
    payload = decode_jwt_token(credentials.credentials)
    if not payload:
        return None
    return payload

def require_admin(user: Optional[Dict] = Depends(get_current_user)) -> Dict:
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Administrative privileges required")
    return user
