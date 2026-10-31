"""Category 数据访问层：分类的 CRUD（按用户隔离）"""
from typing import Optional

import aiosqlite


async def get_categories(db: aiosqlite.Connection, user_id: int) -> list[dict]:
    """获取指定用户的分类列表（平铺结构，前端可构建树）"""
    sql = "SELECT * FROM categories WHERE user_id = ? ORDER BY sort_order ASC, id ASC"
    async with db.execute(sql, [user_id]) as cur:
        rows = await cur.fetchall()
    return [dict(r) for r in rows]


async def create_category(
    db: aiosqlite.Connection, user_id: int, data: dict
) -> dict:
    """新建分类"""
    sql = "INSERT INTO categories (name, parent_id, sort_order, user_id) VALUES (?, ?, ?, ?)"
    params = [data.get("name", ""), data.get("parent_id"), data.get("sort_order", 0), user_id]
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
    # 禁止将分类的父级设为自身，避免循环引用
    if data.get("parent_id") is not None and data["parent_id"] == category_id:
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
