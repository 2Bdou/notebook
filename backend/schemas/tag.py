"""标签相关的 Pydantic 请求/响应模型"""
from pydantic import BaseModel


class TagCreate(BaseModel):
    """新建标签请求体"""

    name: str


class TagResponse(BaseModel):
    """标签响应模型（含关联笔记数量）"""

    id: int
    name: str
    created_at: str
    note_count: int = 0
