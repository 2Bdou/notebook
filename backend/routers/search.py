"""全文搜索路由（基于 LIKE 模糊匹配 title 与 content，支持相关度排序）"""
from typing import Optional

import aiosqlite
from fastapi import APIRouter, Depends

from database import get_db
from models import note as note_model
from schemas import ok

router = APIRouter(prefix="/search", tags=["搜索"])


@router.get("")
async def search(
    q: Optional[str] = None,
    category_id: Optional[int] = None,
    tag_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
    db: aiosqlite.Connection = Depends(get_db),
):
    """全文搜索笔记（匹配标题与正文，支持分类/标签二次过滤、相关度排序）

    - 关键词最少 2 个字符才触发搜索
    - 标题匹配优先于正文匹配（相关度：标题 2 分，正文 1 分）
    - 返回匹配类型和摘要片段供前端高亮展示
    """
    # 关键词为空或不足 2 个字符时返回空结果
    if not q or len(q.strip()) < 2:
        return ok({"total": 0, "page": page, "page_size": page_size, "items": []})

    result = await note_model.search_notes(
        db,
        q=q.strip(),
        category_id=category_id,
        tag_id=tag_id,
        page=page,
        page_size=page_size,
    )
    return ok(result)
