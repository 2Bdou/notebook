"""认证路由：注册、登录、获取当前用户信息

注册安全控制：
1. 注册开关（ALLOW_REGISTRATION=false 时拒绝注册）
2. 邀请码（REGISTRATION_CODE 设置后注册必须提供正确码）
3. 单 IP 每小时注册次数限制
4. 认证接口全局速率限制 + 单 IP 每分钟速率限制（防暴力破解）
"""
import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, Request

from config import settings
from database import get_db
from deps import (
    get_current_user,
    create_access_token,
    check_registration_ip_limit,
    check_auth_rate_limit,
    check_auth_ip_limit,
)
from models import user as user_model
from schemas import ok
from schemas.user import UserRegister, UserLogin

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register")
async def register(
    body: UserRegister,
    request: Request,
    db: aiosqlite.Connection = Depends(get_db),
    _ip_limit: None = Depends(check_registration_ip_limit),
    _rate_limit: None = Depends(check_auth_rate_limit),
    _ip_auth_limit: None = Depends(check_auth_ip_limit),
):
    """用户注册

    安全控制：
    - ALLOW_REGISTRATION=false 时拒绝注册
    - REGISTRATION_CODE 设置后必须提供正确邀请码
    - 单 IP 每小时最多注册 REGISTRATION_IP_HOURLY_LIMIT 次
    - 全局每分钟最多 AUTH_RATE_LIMIT_PER_MINUTE 次认证请求
    - 单 IP 每分钟最多 AUTH_IP_RATE_LIMIT_PER_MINUTE 次认证请求
    """
    # ① 注册开关
    if not settings.ALLOW_REGISTRATION:
        raise HTTPException(status_code=403, detail="注册已关闭，请联系管理员创建账号")

    # ② 邀请码校验
    if settings.REGISTRATION_CODE:
        if body.registration_code != settings.REGISTRATION_CODE:
            raise HTTPException(status_code=403, detail="邀请码错误")

    # 基本参数校验
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
async def login(
    body: UserLogin,
    request: Request,
    db: aiosqlite.Connection = Depends(get_db),
    _rate_limit: None = Depends(check_auth_rate_limit),
    _ip_auth_limit: None = Depends(check_auth_ip_limit),
):
    """用户登录：验证用户名密码，返回 JWT token

    安全控制：全局每分钟最多 AUTH_RATE_LIMIT_PER_MINUTE 次 + 单 IP 每分钟最多 AUTH_IP_RATE_LIMIT_PER_MINUTE 次认证请求
    """
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


@router.get("/config")
async def get_auth_config():
    """获取认证配置（前端用于决定注册表单是否显示邀请码输入框）

    仅暴露是否需要邀请码、是否允许注册，不泄露邀请码本身。
    """
    return ok({
        "allow_registration": settings.ALLOW_REGISTRATION,
        "need_registration_code": bool(settings.REGISTRATION_CODE),
    })
