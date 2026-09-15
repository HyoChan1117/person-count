from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.auth import ADMIN_PASSWORD, create_admin_token

router = APIRouter()


class AdminLoginRequest(BaseModel):
    password: str


@router.post("/admin/login")
def admin_login(body: AdminLoginRequest):
    if not ADMIN_PASSWORD or body.password != ADMIN_PASSWORD:
        raise HTTPException(401, "비밀번호가 일치하지 않습니다.")
    return {"token": create_admin_token()}
