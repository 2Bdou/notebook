"""笔记 CRUD 路由（含回收站相关接口）

所有接口都需要登录认证，数据按当前用户隔离。
注意：固定路径（trash、restore-all、empty-trash）必须定义在动态路径
/{note_id} 之前，否则 FastAPI 会尝试将固定字符串解析为 int 并返回 422。
"""
from typing import Optional

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, Query

from database import get_db
from deps import get_current_user
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
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取笔记列表（支持分类/标签/关键词过滤、排序与分页）"""
    result = await note_model.get_notes(
        db,
        user_id=current_user["id"],
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
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取回收站中已软删除的笔记列表"""
    result = await note_model.get_trash_notes(
        db, user_id=current_user["id"], page=page, page_size=page_size
    )
    return ok(result)


@router.post("")
async def create_note(
    body: NoteCreate,
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """新建笔记"""
    try:
        item = await note_model.create_note(db, current_user["id"], body.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return ok(item, message="创建成功")


@router.post("/restore-all")
async def restore_all_notes(
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """批量恢复所有已软删除的笔记"""
    count = await note_model.restore_all_notes(db, current_user["id"])
    return ok(data={"restored_count": count}, message=f"已恢复 {count} 条笔记")


@router.delete("/empty-trash")
async def empty_trash(
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """清空回收站（永久删除所有已软删除的笔记）"""
    count = await note_model.empty_trash(db, current_user["id"])
    return ok(data={"deleted_count": count}, message=f"已清空 {count} 条笔记")


# ==================== 动态路径路由（/{note_id}） ====================

@router.get("/{note_id}")
async def get_note(
    note_id: int,
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取笔记详情"""
    item = await note_model.get_note_by_id(db, note_id, current_user["id"])
    if not item:
        raise HTTPException(status_code=404, detail="笔记不存在")
    return ok(item)


@router.put("/{note_id}")
async def update_note(
    note_id: int,
    body: NoteUpdate,
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """更新笔记"""
    try:
        item = await note_model.update_note(
            db, note_id, current_user["id"], body.model_dump(exclude_unset=True)
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not item:
        raise HTTPException(status_code=404, detail="笔记不存在")
    return ok(item, message="更新成功")


@router.delete("/{note_id}")
async def delete_note(
    note_id: int,
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """软删除笔记（设置 deleted_at，不真正删除）"""
    success = await note_model.soft_delete_note(db, note_id, current_user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="笔记不存在或已删除")
    return ok(message="删除成功")


@router.delete("/{note_id}/force")
async def force_delete_note(
    note_id: int,
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """永久删除笔记（从数据库中真正删除，不可恢复）"""
    success = await note_model.force_delete_note(db, note_id, current_user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="笔记不存在或未被删除")
    return ok(message="已永久删除")


@router.post("/{note_id}/restore")
async def restore_note(
    note_id: int,
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """恢复已软删除的笔记"""
    success = await note_model.restore_note(db, note_id, current_user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="笔记不存在或未被删除")
    return ok(message="恢复成功")
