"""笔记相关的 Pydantic 请求/响应模型"""
from typing import Optional

from pydantic import BaseModel


class NoteCreate(BaseModel):
    """新建笔记请求体"""

    title: str = ""
    content: str = ""
    content_html: str = ""
    category_id: Optional[int] = None
    is_pinned: bool = False
    tag_ids: list[int] = []


class NoteUpdate(BaseModel):
    """更新笔记请求体（仅传需要修改的字段）"""

    title: Optional[str] = None
    content: Optional[str] = None
    content_html: Optional[str] = None
    category_id: Optional[int] = None
    is_pinned: Optional[bool] = None
    tag_ids: Optional[list[int]] = None


class NoteResponse(BaseModel):
    """笔记响应模型"""

    id: int
    title: str
    content: str
    content_html: str
    category_id: Optional[int] = None
    is_pinned: bool = False
    word_count: int = 0
    created_at: str
    updated_at: str
    deleted_at: Optional[str] = None
    tags: list[dict] = []
