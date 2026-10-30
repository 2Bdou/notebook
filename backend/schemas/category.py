"""分类相关的 Pydantic 请求/响应模型"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class CategoryCreate(BaseModel):
    """新建分类请求体"""

    name: str
    parent_id: Optional[int] = None
    sort_order: int = 0


class CategoryUpdate(BaseModel):
    """更新分类请求体（重命名 / 移动父级 / 调整排序）"""

    name: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: Optional[int] = None


class CategoryResponse(BaseModel):
    """分类响应模型（含子分类，构成树形结构）"""

    id: int
    name: str
    parent_id: Optional[int] = None
    sort_order: int = 0
    created_at: str
    children: list[CategoryResponse] = []


# 重建模型以支持自引用（children 字段引用自身）
CategoryResponse.model_rebuild()
