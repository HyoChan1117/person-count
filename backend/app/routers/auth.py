from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from app.auth import (
    google_auth_url, fetch_google_user, create_jwt, verify_jwt,
    ALLOWED_DOMAINS, FRONTEND_URL,
)

router = APIRouter()


@router.get("/google/login")
def google_login():
    return RedirectResponse(google_auth_url())


@router.get("/google/callback")
async def google_callback(code: str = "", state: str = "", error: str = ""):
    if error:
        return RedirectResponse(f"{FRONTEND_URL}/login?error=access_denied")
    if not code:
        return RedirectResponse(f"{FRONTEND_URL}/login?error=auth_failed")

    try:
        user = await fetch_google_user(code)
    except Exception:
        return RedirectResponse(f"{FRONTEND_URL}/login?error=auth_failed")

    email = user.get("email", "")
    if not any(email.endswith(f"@{d}") for d in ALLOWED_DOMAINS):
        return RedirectResponse(f"{FRONTEND_URL}/login?error=unauthorized_domain")

    token = create_jwt(user)
    return RedirectResponse(f"{FRONTEND_URL}/login?token={token}")


@router.get("/me")
def get_me(current_user: dict = Depends(verify_jwt)):
    return {
        "email": current_user["sub"],
        "name": current_user.get("name", ""),
        "picture": current_user.get("picture", ""),
    }
