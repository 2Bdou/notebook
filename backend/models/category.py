"""Category 数据访问层：分类的 CRUD（按用户隔离）"""
from typing import Optional

import aiosqlite


async def _parent_belongs_to_user(
    db: aiosqlite.Connection, parent_id: int, user_id: int
) -> bool:
    """确认父分类存在且归属当前用户。"""
    async with db.execute(
        "SELECT 1 FROM categories WHERE id = ? AND user_id = ?", (parent_id, user_id)
    ) as cur:
        return await cur.fetchone() is not None


async def _would_create_cycle(
    db: aiosqlite.Connection, category_id: int, new_parent_id: int
) -> bool:
    """把 category_id 的父级设为 new_parent_id 是否会形成环。

    从 new_parent_id 一路沿父链向上走：只要走到 category_id，
    说明 new_parent_id 是 category_id 的后代，设置后将形成环。
    同时也能发现数据库中已存在的环（防御性截断）。
    """
    current: Optional[int] = new_parent_id
    seen: set[int] = set()
    while current is not None:
        if current == category_id:
            return True
        if current in seen:
            return True
        seen.add(current)
        async with db.execute(
            "SELECT parent_id FROM categories WHERE id = ?", (current,)
        ) as cur:
            row = await cur.fetchone()
        current = row["parent_id"] if row else None
    return False


async def get_categories(db: aiosqlite.Connection, user_id: int) -> list[dict]:
    """获取指定用户的分类列表（平铺结构，前端可构建树）"""
    sql = "SELECT * FROM categories WHERE user_id = ? ORDER BY sort_order ASC, id ASC"
    async with db.execute(sql, [user_id]) as cur:
        rows = await cur.fetchall()
    return [dict(r) for r in rows]


async def create_category(
    db: aiosqlite.Connection, user_id: int, data: dict
) -> Optional[dict]:
    """新建分类（父分类必须存在且归属当前用户）"""
    parent_id = data.get("parent_id")
    if parent_id is not None and not await _parent_belongs_to_user(db, parent_id, user_id):
        return None
    sql = "INSERT INTO categories (name, parent_id, sort_order, user_id) VALUES (?, ?, ?, ?)"
    params = [data.get("name", ""), parent_id, data.get("sort_order", 0), user_id]
    async with db.execute(sql, params) as cur:
        cat_id = cur.lastrowid
    await db.commit()
    async with db.execute("SELECT * FROM categories WHERE id = ?", [cat_id]) as cur:
        row = await cur.fetchone()
    return dict(row)


async def update_category(
    db: aiosqlite.Connection, category_id: int, user_id: int, data: dict
) -> Optional[dict]:
    """更新分类（重命名 / 移动父级 / 调整排序）"""
    # 先确认分类归属于当前用户
    async with db.execute(
        "SELECT id FROM categories WHERE id = ? AND user_id = ?", (category_id, user_id)
    ) as cur:
        if await cur.fetchone() is None:
            return None

    # 禁止将分类的父级设为自身，避免循环引用
    new_parent_id = data.get("parent_id")
    if new_parent_id is not None:
        if new_parent_id == category_id:
            return None
        # 父分类必须存在且归属当前用户
        if not await _parent_belongs_to_user(db, new_parent_id, user_id):
            return None
        # 禁止把父级设为自己的后代（会形成环）
        if await _would_create_cycle(db, category_id, new_parent_id):
            return None

    fields: list[str] = []
    params: list = []
    for key in ("name", "parent_id", "sort_order"):
        if data.get(key) is not None:
            fields.append(f"{key} = ?")
            params.append(data[key])

    if fields:
        sql = f"UPDATE categories SET {', '.join(fields)} WHERE id = ? AND user_id = ?"
        await db.execute(sql, params + [category_id, user_id])
        await db.commit()

    async with db.execute(
        "SELECT * FROM categories WHERE id = ? AND user_id = ?", [category_id, user_id]
    ) as cur:
        row = await cur.fetchone()
    return dict(row) if row else None


async def delete_category(
    db: aiosqlite.Connection, category_id: int, user_id: int
) -> bool:
    """删除分类

    子分类的 parent_id 会因 ON DELETE SET NULL 自动置空，
    笔记的 category_id 同理。
    """
    async with db.execute(
        "DELETE FROM categories WHERE id = ? AND user_id = ?", [category_id, user_id]
    ) as cur:
        affected = cur.rowcount
    await db.commit()
    return affected > 0
