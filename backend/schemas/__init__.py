"""统一响应辅助函数

所有 API 返回统一 JSON 格式：{"code": 0, "message": "...", "data": ...}
"""
from typing import Any


def ok(data: Any = None, message: str = "success") -> dict:
    """构造成功响应"""
    return {"code": 0, "message": message, "data": data}


def fail(message: str = "error", code: int = 1) -> dict:
    """构造失败响应"""
    return {"code": code, "message": message, "data": None}
