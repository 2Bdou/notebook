"""备份导入导出路由

GET  /api/backup/export — 导出当前用户全部数据为 JSON 文件下载
POST /api/backup/import — 上传 JSON 文件导入到当前用户名下

导入冲突策略：
- 分类按 name 合并（已有同名则复用，否则新建）
- 标签按 name 合并（已有同名则复用，否则新建）
- 笔记全部导入为新笔记，归属当前用户
"""
import json
from datetime import datetime, timezone

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
import io

from database import get_db
from deps import get_current_user

router = APIRouter(prefix="/backup", tags=["备份"])


@router.get("/export")
async def export_backup(
    db: aiosqlite.Connection = Depends(get_db),
    user=Depends(get_current_user),
):
    """导出当前用户的全部笔记、分类、标签为 JSON 文件"""
    user_id = user["id"]

    # 查询分类
    cursor = await db.execute(
        "SELECT id, name, parent_id, sort_order FROM categories WHERE user_id = ? ORDER BY sort_order",
        (user_id,),
    )
    categories = await cursor.fetchall()
    await cursor.close()

    # 构建 parent_id → name 映射
    cat_id_to_name = {c["id"]: c["name"] for c in categories}

    # 查询标签
    cursor = await db.execute(
        "SELECT id, name FROM tags WHERE user_id = ? ORDER BY name",
        (user_id,),
    )
    tags = await cursor.fetchall()
    await cursor.close()

    # 查询笔记（含分类名称）
    cursor = await db.execute(
        """SELECT n.id, n.title, n.content, n.content_html,
                  n.category_id, n.is_pinned, n.word_count,
                  n.created_at, n.updated_at
           FROM notes n
           WHERE n.user_id = ? AND n.deleted_at IS NULL
           ORDER BY n.updated_at DESC""",
        (user_id,),
    )
    notes = await cursor.fetchall()
    await cursor.close()

    # 查询笔记-标签关联
    cursor = await db.execute(
        """SELECT nt.note_id, nt.tag_id
           FROM note_tags nt
           JOIN notes n ON nt.note_id = n.id
           WHERE n.user_id = ? AND n.deleted_at IS NULL""",
        (user_id,),
    )
    note_tags = await cursor.fetchall()
    await cursor.close()

    # 构建 note_id → [tag_name] 映射
    tag_id_to_name = {t["id"]: t["name"] for t in tags}
    note_id_to_tags: dict[int, list[str]] = {}
    for nt in note_tags:
        tag_name = tag_id_to_name.get(nt["tag_id"])
        if tag_name:
            note_id_to_tags.setdefault(nt["note_id"], []).append(tag_name)

    # 组装 JSON
    data = {
        "version": "1.0",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "categories": [
            {
                "name": c["name"],
                "parent_name": cat_id_to_name.get(c["parent_id"]) if c["parent_id"] else None,
                "sort_order": c["sort_order"],
            }
            for c in categories
        ],
        "tags": [{"name": t["name"]} for t in tags],
        "notes": [
            {
                "title": n["title"],
                "content": n["content"],
                "content_html": n["content_html"],
                "category_name": cat_id_to_name.get(n["category_id"]) if n["category_id"] else None,
                "is_pinned": n["is_pinned"],
                "word_count": n["word_count"],
                "tag_names": note_id_to_tags.get(n["id"], []),
                "created_at": n["created_at"],
                "updated_at": n["updated_at"],
            }
            for n in notes
        ],
    }

    # 生成文件名
    filename = f"notebook-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    json_bytes = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")

    return StreamingResponse(
        io.BytesIO(json_bytes),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/import")
async def import_backup(
    file: UploadFile = File(...),
    db: aiosqlite.Connection = Depends(get_db),
    user=Depends(get_current_user),
):
    """上传 JSON 文件导入到当前用户名下

    分类/标签按名称合并，笔记全部新建。
    返回导入统计信息。
    """
    user_id = user["id"]

    # 读取并解析文件
    raw = await file.read()
    if len(raw) > 50 * 1024 * 1024:  # 50MB 限制
        raise HTTPException(status_code=413, detail="文件过大，最大 50MB")

    try:
        data = json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise HTTPException(status_code=400, detail=f"JSON 解析失败: {e}")

    if not isinstance(data, dict) or "notes" not in data:
        raise HTTPException(status_code=400, detail="无效的备份文件格式")

    # 开启外键
    await db.execute("PRAGMA foreign_keys = ON")

    imported_categories = 0
    imported_tags = 0
    imported_notes = 0

    # 1) 导入分类：按 name 合并
    cat_name_to_id: dict[str, int] = {}
    # 先加载已有分类
    cursor = await db.execute(
        "SELECT id, name FROM categories WHERE user_id = ?", (user_id,)
    )
    existing_cats = await cursor.fetchall()
    await cursor.close()
    for c in existing_cats:
        cat_name_to_id[c["name"]] = c["id"]

    for cat in data.get("categories", []):
        name = cat.get("name", "").strip()
        if not name or name in cat_name_to_id:
            continue
        cursor = await db.execute(
            "INSERT INTO categories (name, sort_order, user_id) VALUES (?, ?, ?)",
            (name, cat.get("sort_order", 0), user_id),
        )
        await db.commit()
        cat_name_to_id[name] = cursor.lastrowid
        imported_categories += 1
        await cursor.close()

    # 2) 导入标签：按 name 合并
    tag_name_to_id: dict[str, int] = {}
    cursor = await db.execute(
        "SELECT id, name FROM tags WHERE user_id = ?", (user_id,)
    )
    existing_tags = await cursor.fetchall()
    await cursor.close()
    for t in existing_tags:
        tag_name_to_id[t["name"]] = t["id"]

    for tag in data.get("tags", []):
        name = tag.get("name", "").strip()
        if not name or name in tag_name_to_id:
            continue
        cursor = await db.execute(
            "INSERT INTO tags (name, user_id) VALUES (?, ?)",
            (name, user_id),
        )
        await db.commit()
        tag_name_to_id[name] = cursor.lastrowid
        imported_tags += 1
        await cursor.close()

    # 3) 导入笔记
    for note in data.get("notes", []):
        title = note.get("title", "")
        content = note.get("content", "")
        content_html = note.get("content_html", "")
        is_pinned = note.get("is_pinned", 0)
        word_count = note.get("word_count", len(content))
        created_at = note.get("created_at", datetime.now().isoformat())
        updated_at = note.get("updated_at", datetime.now().isoformat())

        # 分类映射
        category_name = note.get("category_name")
        category_id = cat_name_to_id.get(category_name) if category_name else None

        cursor = await db.execute(
            """INSERT INTO notes (title, content, content_html, category_id,
               is_pinned, word_count, user_id, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (title, content, content_html, category_id, is_pinned,
             word_count, user_id, created_at, updated_at),
        )
        await db.commit()
        new_note_id = cursor.lastrowid
        imported_notes += 1
        await cursor.close()

        # 关联标签
        for tag_name in note.get("tag_names", []):
            tag_id = tag_name_to_id.get(tag_name.strip())
            if tag_id:
                try:
                    await db.execute(
                        "INSERT INTO note_tags (note_id, tag_id) VALUES (?, ?)",
                        (new_note_id, tag_id),
                    )
                    await db.commit()
                except aiosqlite.IntegrityError:
                    pass  # 重复关联，忽略

    return {
        "code": 0,
        "message": "导入成功",
        "data": {
            "categories": imported_categories,
            "tags": imported_tags,
            "notes": imported_notes,
        },
    }
