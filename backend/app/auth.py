import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")

_ALGORITHM = "HS256"
_EXPIRE_HOURS = 8
_security = HTTPBearer()


def create_admin_token() -> str:
    payload = {
        "is_admin": True,
        "exp": datetime.now(timezone.utc) + timedelta(hours=_EXPIRE_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=_ALGORITHM)


def verify_jwt(credentials: HTTPAuthorizationCredentials = Security(_security)) -> dict:
    try:
        return jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "토큰이 만료되었습니다. 다시 로그인해 주세요.")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "유효하지 않은 토큰입니다.")


def require_admin(current_user: dict = Depends(verify_jwt)) -> dict:
    if not current_user.get("is_admin"):
        raise HTTPException(403, "관리자만 접근할 수 있습니다.")
    return current_user
