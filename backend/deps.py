"""认证依赖：从请求头解析 JWT token，返回当前用户

所有需要登录的路由通过 Depends(get_current_user) 注入当前用户。
"""
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
import aiosqlite

from config import settings
from database import get_db
from models import user as user_model

# HTTP Bearer 认证方案：从 Authorization: Bearer <token> 头提取 token
security = HTTPBearer()


def create_access_token(user_id: int) -> str:
    """生成 JWT access token

    token 中携带用户 ID (sub) 和过期时间 (exp)。
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    """从 Bearer token 解析当前用户，失败抛 401

    返回的 dict 包含 id, username, password_hash, created_at 等字段。
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        user_id_str: str | None = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(status_code=401, detail="无效的认证令牌")
    except JWTError:
        raise HTTPException(status_code=401, detail="无效的认证令牌")

    user = await user_model.get_user_by_id(db, int(user_id_str))
    if user is None:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user
