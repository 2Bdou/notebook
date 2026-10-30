"""Tag 数据访问层：标签的 CRUD"""
from typing import Optional

import aiosqlite


async def get_tags(db: aiosqlite.Connection) -> list[dict]:
    """获取所有标签及关联笔记数（仅统计未软删除的笔记）"""
    sql = """
    SELECT t.id, t.name, t.created_at,
           COUNT(CASE WHEN n.deleted_at IS NULL THEN 1 END) AS note_count
    FROM tags t
    LEFT JOIN note_tags nt ON nt.tag_id = t.id
    LEFT JOIN notes n ON n.id = nt.note_id
    GROUP BY t.id
    ORDER BY t.name ASC
    """
    async with db.execute(sql) as cur:
        rows = await cur.fetchall()
    return [dict(r) for r in rows]


async def create_tag(db: aiosqlite.Connection, name: str) -> Optional[dict]:
    """新建标签（name 唯一，重复时返回 None）"""
    try:
        async with db.execute("INSERT INTO tags (name) VALUES (?)", [name]) as cur:
            tag_id = cur.lastrowid
        await db.commit()
    except aiosqlite.IntegrityError:
        # name 唯一约束冲突
        return None
    async with db.execute("SELECT * FROM tags WHERE id = ?", [tag_id]) as cur:
        row = await cur.fetchone()
    return dict(row)


async def delete_tag(db: aiosqlite.Connection, tag_id: int) -> bool:
    """删除标签（关联表 note_tags 因 ON DELETE CASCADE 自动清理）"""
    async with db.execute("DELETE FROM tags WHERE id = ?", [tag_id]) as cur:
        affected = cur.rowcount
    await db.commit()
    return affected > 0
