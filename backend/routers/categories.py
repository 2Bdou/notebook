"""分类 CRUD 路由（按用户隔离）"""
import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from database import get_db
from deps import get_current_user
from models import category as category_model
from schemas import ok
from schemas.category import CategoryCreate, CategoryUpdate

router = APIRouter(prefix="/categories", tags=["分类"])


@router.get("")
async def list_categories(
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取分类列表（平铺结构，前端可构建树）"""
    items = await category_model.get_categories(db, current_user["id"])
    return ok(items)


@router.post("")
async def create_category(
    body: CategoryCreate,
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """新建分类"""
    item = await category_model.create_category(db, current_user["id"], body.model_dump())
    return ok(item, message="创建成功")


@router.put("/{category_id}")
async def update_category(
    category_id: int,
    body: CategoryUpdate,
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """更新分类（重命名 / 移动父级 / 调整排序）"""
    item = await category_model.update_category(
        db, category_id, current_user["id"], body.model_dump(exclude_unset=True)
    )
    if not item:
        raise HTTPException(status_code=400, detail="分类不存在或参数非法")
    return ok(item, message="更新成功")


@router.delete("/{category_id}")
async def delete_category(
    category_id: int,
    db: aiosqlite.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """删除分类"""
    success = await category_model.delete_category(db, category_id, current_user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="分类不存在")
    return ok(message="删除成功")
