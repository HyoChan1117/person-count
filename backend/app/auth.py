import os
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
import jwt
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
_raw_domains = os.getenv("ALLOWED_DOMAIN", "g.yju.ac.kr,yju.ac.kr")
ALLOWED_DOMAINS = [d.strip() for d in _raw_domains.split(",") if d.strip()]

ADMIN_EMAILS = {e.strip() for e in os.getenv("ADMIN_EMAILS", "").split(",") if e.strip()}

_ALGORITHM = "HS256"
_EXPIRE_HOURS = 8
_security = HTTPBearer()


def create_jwt(user: dict) -> str:
    email = user["email"]
    payload = {
        "sub": email,
        "name": user.get("name", ""),
        "picture": user.get("picture", ""),
        "is_admin": email in ADMIN_EMAILS,
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


def google_auth_url() -> str:
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "online",
        "hd": ALLOWED_DOMAINS[0],
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"


async def fetch_google_user(code: str) -> dict:
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": GOOGLE_REDIRECT_URI,
            },
        )
        if token_resp.status_code != 200:
            raise HTTPException(400, "Google 토큰 교환 실패")

        access_token = token_resp.json().get("access_token")
        user_resp = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if user_resp.status_code != 200:
            raise HTTPException(400, "사용자 정보 조회 실패")

        return user_resp.json()
