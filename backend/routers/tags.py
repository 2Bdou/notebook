"""标签 CRUD 路由"""
import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from database import get_db
from models import tag as tag_model
from schemas import ok
from schemas.tag import TagCreate

router = APIRouter(prefix="/tags", tags=["标签"])


@router.get("")
async def list_tags(db: aiosqlite.Connection = Depends(get_db)):
    """获取所有标签及关联笔记计数"""
    items = await tag_model.get_tags(db)
    return ok(items)


@router.post("")
async def create_tag(body: TagCreate, db: aiosqlite.Connection = Depends(get_db)):
    """新建标签（name 唯一）"""
    item = await tag_model.create_tag(db, body.name)
    if not item:
        raise HTTPException(status_code=409, detail="标签已存在")
    return ok(item, message="创建成功")


@router.delete("/{tag_id}")
async def delete_tag(tag_id: int, db: aiosqlite.Connection = Depends(get_db)):
    """删除标签"""
    success = await tag_model.delete_tag(db, tag_id)
    if not success:
        raise HTTPException(status_code=404, detail="标签不存在")
    return ok(message="删除成功")
