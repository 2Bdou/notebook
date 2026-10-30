"""Note 数据访问层：封装笔记的 CRUD SQL 操作"""
from typing import Optional

import aiosqlite


async def _get_note_tags(db: aiosqlite.Connection, note_id: int) -> list[dict]:
    """获取某笔记关联的标签列表"""
    sql = """
    SELECT t.id, t.name FROM tags t
    JOIN note_tags nt ON nt.tag_id = t.id
    WHERE nt.note_id = ?
    """
    async with db.execute(sql, [note_id]) as cur:
        rows = await cur.fetchall()
    return [{"id": r["id"], "name": r["name"]} for r in rows]


def _normalize(row_dict: dict) -> dict:
    """将数据库行字典中的整型标记转换为布尔值"""
    row_dict["is_pinned"] = bool(row_dict.get("is_pinned", 0))
    return row_dict


def _build_snippet(content: str, keyword: str, radius: int = 50) -> str:
    """从内容中提取匹配关键词附近的文本片段"""
    pos = content.lower().find(keyword.lower())
    if pos == -1:
        return content[:radius * 2] if content else ""
    start = max(0, pos - radius)
    end = min(len(content), pos + len(keyword) + radius)
    snippet = content[start:end]
    if start > 0:
        snippet = "..." + snippet
    if end < len(content):
        snippet = snippet + "..."
    return snippet


async def get_notes(
    db: aiosqlite.Connection,
    category_id: Optional[int] = None,
    tag_id: Optional[int] = None,
    q: Optional[str] = None,
    sort: str = "updated_at",
    order: str = "desc",
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """查询笔记列表（默认排除已软删除的笔记）

    支持按分类、标签、关键词过滤，以及多种排序与分页。
    sort: updated_at / created_at / title / word_count
    order: desc / asc
    """
    where = ["deleted_at IS NULL"]
    params: list = []

    if category_id is not None:
        where.append("category_id = ?")
        params.append(category_id)
    if tag_id is not None:
        where.append("id IN (SELECT note_id FROM note_tags WHERE tag_id = ?)")
        params.append(tag_id)
    if q:
        where.append("(title LIKE ? OR content LIKE ?)")
        params.extend([f"%{q}%", f"%{q}%"])

    where_sql = " AND ".join(where)

    # 排序方向
    direction = "DESC" if order == "desc" else "ASC"
    # 排序方式映射
    field_map = {
        "updated_at": "updated_at",
        "created_at": "created_at",
        "title": "title",
        "word_count": "word_count",
    }
    order_field = field_map.get(sort, "updated_at")
    order_sql = f"{order_field} {direction}"
    # 置顶笔记始终排在最前
    order_sql = f"is_pinned DESC, {order_sql}"

    # 查询总数
    async with db.execute(f"SELECT COUNT(*) FROM notes WHERE {where_sql}", params) as cur:
        total = (await cur.fetchone())[0]

    # 分页查询
    offset = (page - 1) * page_size
    list_sql = (
        f"SELECT * FROM notes WHERE {where_sql} ORDER BY {order_sql} LIMIT ? OFFSET ?"
    )
    async with db.execute(list_sql, params + [page_size, offset]) as cur:
        rows = await cur.fetchall()

    items = []
    for r in rows:
        item = _normalize(dict(r))
        item["tags"] = await _get_note_tags(db, item["id"])
        items.append(item)

    return {"total": total, "page": page, "page_size": page_size, "items": items}


async def search_notes(
    db: aiosqlite.Connection,
    q: str,
    category_id: Optional[int] = None,
    tag_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """全文搜索笔记（匹配标题与正文），按相关度排序并返回匹配信息

    相关度：标题匹配(2) + 正文匹配(1)，得分越高越靠前。
    """
    where = ["deleted_at IS NULL"]
    params: list = []

    # 关键词匹配条件
    like_q = f"%{q}%"
    where.append("(title LIKE ? OR content LIKE ?)")
    params.extend([like_q, like_q])

    # 二次过滤：分类
    if category_id is not None:
        where.append("category_id = ?")
        params.append(category_id)
    # 二次过滤：标签
    if tag_id is not None:
        where.append("id IN (SELECT note_id FROM note_tags WHERE tag_id = ?)")
        params.append(tag_id)

    where_sql = " AND ".join(where)

    # 相关度计算：标题匹配得 2 分，正文匹配得 1 分
    relevance_sql = (
        f"(CASE WHEN title LIKE ? THEN 2 ELSE 0 END) + "
        f"(CASE WHEN content LIKE ? THEN 1 ELSE 0 END)"
    )
    relevance_params = [like_q, like_q]

    # 查询总数
    async with db.execute(
        f"SELECT COUNT(*) FROM notes WHERE {where_sql}", params
    ) as cur:
        total = (await cur.fetchone())[0]

    # 分页查询，按相关度降序、置顶优先、更新时间降序排列
    offset = (page - 1) * page_size
    list_sql = (
        f"SELECT *, {relevance_sql} as _relevance FROM notes "
        f"WHERE {where_sql} "
        f"ORDER BY _relevance DESC, is_pinned DESC, updated_at DESC "
        f"LIMIT ? OFFSET ?"
    )
    async with db.execute(
        list_sql, relevance_params + params + [page_size, offset]
    ) as cur:
        rows = await cur.fetchall()

    items = []
    for r in rows:
        item = _normalize(dict(r))
        item["tags"] = await _get_note_tags(db, item["id"])
        # 匹配信息
        title_match = q.lower() in item["title"].lower()
        content_match = q.lower() in item["content"].lower()
        item["match_type"] = "both" if (title_match and content_match) else ("title" if title_match else "content")
        item["snippet"] = _build_snippet(item["content"], q)
        items.append(item)

    return {"total": total, "page": page, "page_size": page_size, "items": items}


async def get_note_by_id(
    db: aiosqlite.Connection, note_id: int, include_deleted: bool = False
) -> Optional[dict]:
    """根据 ID 获取笔记详情"""
    if include_deleted:
        sql = "SELECT * FROM notes WHERE id = ?"
    else:
        sql = "SELECT * FROM notes WHERE id = ? AND deleted_at IS NULL"
    async with db.execute(sql, [note_id]) as cur:
        row = await cur.fetchone()
    if not row:
        return None
    item = _normalize(dict(row))
    item["tags"] = await _get_note_tags(db, note_id)
    return item


async def create_note(db: aiosqlite.Connection, data: dict) -> dict:
    """新建笔记，并关联标签"""
    word_count = len(data.get("content", "") or "")
    sql = """
    INSERT INTO notes (title, content, content_html, category_id, is_pinned, word_count)
    VALUES (?, ?, ?, ?, ?, ?)
    """
    params = [
        data.get("title", ""),
        data.get("content", ""),
        data.get("content_html", ""),
        data.get("category_id"),
        1 if data.get("is_pinned") else 0,
        word_count,
    ]
    async with db.execute(sql, params) as cur:
        note_id = cur.lastrowid

    # 关联标签（忽略不存在的标签）
    for tid in data.get("tag_ids", []) or []:
        await db.execute(
            "INSERT OR IGNORE INTO note_tags (note_id, tag_id) VALUES (?, ?)",
            [note_id, tid],
        )
    await db.commit()
    return await get_note_by_id(db, note_id, include_deleted=True)


async def update_note(db: aiosqlite.Connection, note_id: int, data: dict) -> Optional[dict]:
    """更新笔记（仅更新请求中提供的字段），并可替换标签关联"""
    fields: list[str] = []
    params: list = []

    for key in ("title", "content", "content_html", "category_id"):
        if data.get(key) is not None:
            fields.append(f"{key} = ?")
            params.append(data[key])
    if data.get("is_pinned") is not None:
        fields.append("is_pinned = ?")
        params.append(1 if data["is_pinned"] else 0)
    # 内容变更时同步更新字数
    if data.get("content") is not None:
        fields.append("word_count = ?")
        params.append(len(data["content"]))

    has_tag_update = data.get("tag_ids") is not None

    if not fields and not has_tag_update:
        return await get_note_by_id(db, note_id)

    if fields:
        fields.append("updated_at = datetime('now')")
        sql = f"UPDATE notes SET {', '.join(fields)} WHERE id = ? AND deleted_at IS NULL"
        await db.execute(sql, params + [note_id])

    # 替换标签关联：先清空再重建
    if has_tag_update:
        await db.execute("DELETE FROM note_tags WHERE note_id = ?", [note_id])
        for tid in data["tag_ids"]:
            await db.execute(
                "INSERT OR IGNORE INTO note_tags (note_id, tag_id) VALUES (?, ?)",
                [note_id, tid],
            )

    await db.commit()
    return await get_note_by_id(db, note_id)


async def soft_delete_note(db: aiosqlite.Connection, note_id: int) -> bool:
    """软删除笔记（仅设置 deleted_at，不真正删除数据）"""
    sql = "UPDATE notes SET deleted_at = datetime('now') WHERE id = ? AND deleted_at IS NULL"
    async with db.execute(sql, [note_id]) as cur:
        affected = cur.rowcount
    await db.commit()
    return affected > 0


async def restore_note(db: aiosqlite.Connection, note_id: int) -> bool:
    """恢复已软删除的笔记（清空 deleted_at）"""
    sql = "UPDATE notes SET deleted_at = NULL WHERE id = ? AND deleted_at IS NOT NULL"
    async with db.execute(sql, [note_id]) as cur:
        affected = cur.rowcount
    await db.commit()
    return affected > 0


async def get_trash_notes(
    db: aiosqlite.Connection, page: int = 1, page_size: int = 20
) -> dict:
    """获取回收站中已软删除的笔记列表"""
    # 查询总数
    async with db.execute(
        "SELECT COUNT(*) FROM notes WHERE deleted_at IS NOT NULL"
    ) as cur:
        total = (await cur.fetchone())[0]

    # 分页查询，按删除时间降序
    offset = (page - 1) * page_size
    sql = (
        "SELECT * FROM notes WHERE deleted_at IS NOT NULL "
        "ORDER BY deleted_at DESC LIMIT ? OFFSET ?"
    )
    async with db.execute(sql, [page_size, offset]) as cur:
        rows = await cur.fetchall()

    items = []
    for r in rows:
        item = _normalize(dict(r))
        item["tags"] = await _get_note_tags(db, item["id"])
        items.append(item)

    return {"total": total, "page": page, "page_size": page_size, "items": items}


async def force_delete_note(db: aiosqlite.Connection, note_id: int) -> bool:
    """永久删除笔记（从数据库中真正删除，含标签关联）"""
    # 先删除标签关联
    await db.execute("DELETE FROM note_tags WHERE note_id = ?", [note_id])
    # 再删除笔记本身
    async with db.execute(
        "DELETE FROM notes WHERE id = ? AND deleted_at IS NOT NULL", [note_id]
    ) as cur:
        affected = cur.rowcount
    await db.commit()
    return affected > 0


async def restore_all_notes(db: aiosqlite.Connection) -> int:
    """批量恢复所有已软删除的笔记，返回恢复数量"""
    async with db.execute(
        "UPDATE notes SET deleted_at = NULL WHERE deleted_at IS NOT NULL"
    ) as cur:
        affected = cur.rowcount
    await db.commit()
    return affected


async def empty_trash(db: aiosqlite.Connection) -> int:
    """清空回收站：永久删除所有已软删除的笔记，返回删除数量"""
    # 先查询数量
    async with db.execute(
        "SELECT COUNT(*) FROM notes WHERE deleted_at IS NOT NULL"
    ) as cur:
        count = (await cur.fetchone())[0]

    if count == 0:
        return 0

    # 删除标签关联
    await db.execute(
        "DELETE FROM note_tags WHERE note_id IN "
        "(SELECT id FROM notes WHERE deleted_at IS NOT NULL)"
    )
    # 删除笔记
    await db.execute("DELETE FROM notes WHERE deleted_at IS NOT NULL")
    await db.commit()
    return count
