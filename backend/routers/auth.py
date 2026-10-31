"""认证路由：注册、登录、获取当前用户信息"""
import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from database import get_db
from deps import get_current_user, create_access_token
from models import user as user_model
from schemas import ok
from schemas.user import UserRegister, UserLogin

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register")
async def register(body: UserRegister, db: aiosqlite.Connection = Depends(get_db)):
    """用户注册：用户名 >= 2 字符，密码 >= 6 字符"""
    if len(body.username) < 2:
        raise HTTPException(status_code=400, detail="用户名至少 2 个字符")
    if len(body.password) < 6:
        raise HTTPException(status_code=400, detail="密码至少 6 个字符")

    user = await user_model.create_user(db, body.username, body.password)
    if not user:
        raise HTTPException(status_code=409, detail="用户名已存在")

    token = create_access_token(user["id"])
    user_info = {
        "id": user["id"],
        "username": user["username"],
        "created_at": user["created_at"],
    }
    return ok(
        {"access_token": token, "token_type": "bearer", "user": user_info},
        message="注册成功",
    )


@router.post("/login")
async def login(body: UserLogin, db: aiosqlite.Connection = Depends(get_db)):
    """用户登录：验证用户名密码，返回 JWT token"""
    user = await user_model.authenticate_user(db, body.username, body.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token = create_access_token(user["id"])
    user_info = {
        "id": user["id"],
        "username": user["username"],
        "created_at": user["created_at"],
    }
    return ok(
        {"access_token": token, "token_type": "bearer", "user": user_info},
        message="登录成功",
    )


@router.get("/me")
async def me(current_user: dict = Depends(get_current_user)):
    """获取当前登录用户信息"""
    user_info = {
        "id": current_user["id"],
        "username": current_user["username"],
        "created_at": current_user["created_at"],
    }
    return ok(user_info)
