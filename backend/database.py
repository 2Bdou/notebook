"""SQLite 数据库连接管理与表初始化

使用 aiosqlite 提供异步数据库访问，并通过 FastAPI 依赖注入分发连接。
"""
import os
import aiosqlite

from config import settings

# 建表 SQL
# 注意顺序：categories 需先于 notes 创建（notes.category_id 外键引用 categories）
INIT_SQL = """
-- 分类表：支持自引用 parent_id 形成树形结构
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    parent_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 笔记表：deleted_at 非空表示已软删除
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL DEFAULT '',
    content TEXT NOT NULL DEFAULT '',
    content_html TEXT NOT NULL DEFAULT '',
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    is_pinned INTEGER NOT NULL DEFAULT 0,
    word_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    deleted_at TEXT
);

-- 标签表：name 全局唯一
CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 笔记-标签关联表：多对多关系
CREATE TABLE IF NOT EXISTS note_tags (
    note_id INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (note_id, tag_id)
);

-- 常用查询索引
CREATE INDEX IF NOT EXISTS idx_notes_category ON notes(category_id);
CREATE INDEX IF NOT EXISTS idx_notes_updated ON notes(updated_at);
CREATE INDEX IF NOT EXISTS idx_notes_deleted ON notes(deleted_at);
"""


async def init_db() -> None:
    """初始化数据库：确保数据目录存在并创建所有表"""
    db_dir = os.path.dirname(settings.DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    async with aiosqlite.connect(settings.DB_PATH) as db:
        # 开启外键约束支持
        await db.execute("PRAGMA foreign_keys = ON")
        await db.executescript(INIT_SQL)
        await db.commit()


async def get_db():
    """FastAPI 依赖：提供一个异步数据库连接，请求结束后自动关闭"""
    db = await aiosqlite.connect(settings.DB_PATH)
    db.row_factory = aiosqlite.Row  # 让查询结果支持按列名访问
    try:
        yield db
    finally:
        await db.close()
