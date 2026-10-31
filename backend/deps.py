"""认证依赖：从请求头解析 JWT token，返回当前用户

所有需要登录的路由通过 Depends(get_current_user) 注入当前用户。
同时提供注册 IP 频率限制和认证接口全局速率限制。
"""
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request
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


# ==================== 速率限制器（内存实现，重启后清零） ====================

# 单 IP 注册计数：{ip: deque([timestamp, ...])}
_ip_register_log: defaultdict[str, deque] = defaultdict(deque)

# 全局认证请求计数：deque([timestamp, ...])
_global_auth_log: deque = deque()


def _cleanup_old(entries: deque, window_seconds: int) -> None:
    """移除时间窗口外的过期记录"""
    cutoff = time.time() - window_seconds
    while entries and entries[0] < cutoff:
        entries.popleft()


def check_registration_ip_limit(request: Request) -> None:
    """检查单 IP 注册频率限制（每小时最多 N 次）

    作为 FastAPI 依赖使用：Depends(check_registration_ip_limit)
    """
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    window = 3600  # 1 小时窗口

    log = _ip_register_log[client_ip]
    _cleanup_old(log, window)

    if len(log) >= settings.REGISTRATION_IP_HOURLY_LIMIT:
        raise HTTPException(
            status_code=429,
            detail=f"该 IP 注册过于频繁，每小时最多 {settings.REGISTRATION_IP_HOURLY_LIMIT} 次，请稍后再试",
        )

    log.append(now)


def check_auth_rate_limit(request: Request) -> None:
    """检查认证接口全局速率限制（每分钟最多 N 次请求）

    作为 FastAPI 依赖使用：Depends(check_auth_rate_limit)
    防止密码暴力破解和批量注册请求。
    """
    now = time.time()
    window = 60  # 1 分钟窗口

    _cleanup_old(_global_auth_log, window)

    if len(_global_auth_log) >= settings.AUTH_RATE_LIMIT_PER_MINUTE:
        raise HTTPException(
            status_code=429,
            detail=f"请求过于频繁，每分钟最多 {settings.AUTH_RATE_LIMIT_PER_MINUTE} 次，请稍后再试",
        )

    _global_auth_log.append(now)
