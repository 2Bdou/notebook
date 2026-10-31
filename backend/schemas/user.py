"""用户认证相关的 Pydantic 请求/响应模型"""
from pydantic import BaseModel


class UserRegister(BaseModel):
    """注册请求体"""

    username: str
    password: str
    registration_code: str = ""  # 邀请码（后端配置了 REGISTRATION_CODE 时必填）


class UserLogin(BaseModel):
    """登录请求体"""

    username: str
    password: str


class UserResponse(BaseModel):
    """用户信息响应模型"""

    id: int
    username: str
    created_at: str


class TokenResponse(BaseModel):
    """登录/注册成功后的 token 响应"""

    access_token: str
    token_type: str = "bearer"
    user: dict
