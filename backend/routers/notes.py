"""笔记 CRUD 路由（含回收站相关接口）

注意：固定路径（trash、restore-all、empty-trash）必须定义在动态路径
/{note_id} 之前，否则 FastAPI 会尝试将固定字符串解析为 int 并返回 422。
"""
from typing import Optional

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from database import get_db
from models import note as note_model
from schemas import ok
from schemas.note import NoteCreate, NoteUpdate

router = APIRouter(prefix="/notes", tags=["笔记"])


# ==================== 固定路径路由（必须在 /{note_id} 之前） ====================

@router.get("")
async def list_notes(
    category_id: Optional[int] = None,
    tag_id: Optional[int] = None,
    q: Optional[str] = None,
    sort: str = "updated_at",
    order: str = "desc",
    page: int = 1,
    page_size: int = 20,
    db: aiosqlite.Connection = Depends(get_db),
):
    """获取笔记列表（支持分类/标签/关键词过滤、排序方向与分页）"""
    result = await note_model.get_notes(
        db,
        category_id=category_id,
        tag_id=tag_id,
        q=q,
        sort=sort,
        order=order,
        page=page,
        page_size=page_size,
    )
    return ok(result)


@router.get("/trash")
async def get_trash(
    page: int = 1,
    page_size: int = 50,
    db: aiosqlite.Connection = Depends(get_db),
):
    """获取回收站中已软删除的笔记列表"""
    result = await note_model.get_trash_notes(db, page=page, page_size=page_size)
    return ok(result)


@router.post("")
async def create_note(body: NoteCreate, db: aiosqlite.Connection = Depends(get_db)):
    """新建笔记"""
    item = await note_model.create_note(db, body.model_dump())
    return ok(item, message="创建成功")


@router.post("/restore-all")
async def restore_all_notes(db: aiosqlite.Connection = Depends(get_db)):
    """批量恢复所有已软删除的笔记"""
    count = await note_model.restore_all_notes(db)
    return ok(data={"restored_count": count}, message=f"已恢复 {count} 条笔记")


@router.delete("/empty-trash")
async def empty_trash(db: aiosqlite.Connection = Depends(get_db)):
    """清空回收站（永久删除所有已软删除的笔记）"""
    count = await note_model.empty_trash(db)
    return ok(data={"deleted_count": count}, message=f"已清空 {count} 条笔记")


# ==================== 动态路径路由（/{note_id}） ====================

@router.get("/{note_id}")
async def get_note(note_id: int, db: aiosqlite.Connection = Depends(get_db)):
    """获取笔记详情"""
    item = await note_model.get_note_by_id(db, note_id)
    if not item:
        raise HTTPException(status_code=404, detail="笔记不存在")
    return ok(item)


@router.put("/{note_id}")
async def update_note(
    note_id: int, body: NoteUpdate, db: aiosqlite.Connection = Depends(get_db)
):
    """更新笔记"""
    item = await note_model.update_note(db, note_id, body.model_dump(exclude_unset=True))
    if not item:
        raise HTTPException(status_code=404, detail="笔记不存在")
    return ok(item, message="更新成功")


@router.delete("/{note_id}")
async def delete_note(note_id: int, db: aiosqlite.Connection = Depends(get_db)):
    """软删除笔记（设置 deleted_at，不真正删除）"""
    success = await note_model.soft_delete_note(db, note_id)
    if not success:
        raise HTTPException(status_code=404, detail="笔记不存在或已删除")
    return ok(message="删除成功")


@router.delete("/{note_id}/force")
async def force_delete_note(note_id: int, db: aiosqlite.Connection = Depends(get_db)):
    """永久删除笔记（从数据库中真正删除，不可恢复）"""
    success = await note_model.force_delete_note(db, note_id)
    if not success:
        raise HTTPException(status_code=404, detail="笔记不存在或未被删除")
    return ok(message="已永久删除")


@router.post("/{note_id}/restore")
async def restore_note(note_id: int, db: aiosqlite.Connection = Depends(get_db)):
    """恢复已软删除的笔记"""
    success = await note_model.restore_note(db, note_id)
    if not success:
        raise HTTPException(status_code=404, detail="笔记不存在或未被删除")
    return ok(message="恢复成功")
