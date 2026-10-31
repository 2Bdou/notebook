"""SQLite 数据库连接管理与表初始化

使用 aiosqlite 提供异步数据库访问，并通过 FastAPI 依赖注入分发连接。
"""
import os
import aiosqlite

from config import settings

# 建表 SQL
# 注意顺序：users 需先于 categories/notes/tags 创建（它们的外键引用 users）
INIT_SQL = """
-- 用户表：存储登录账号和密码哈希
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 分类表：支持自引用 parent_id 形成树形结构，绑定到用户
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    parent_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 笔记表：deleted_at 非空表示已软删除，绑定到用户
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL DEFAULT '',
    content TEXT NOT NULL DEFAULT '',
    content_html TEXT NOT NULL DEFAULT '',
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    is_pinned INTEGER NOT NULL DEFAULT 0,
    word_count INTEGER NOT NULL DEFAULT 0,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    deleted_at TEXT
);

-- 标签表：同一用户下 name 唯一
CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(user_id, name)
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
CREATE INDEX IF NOT EXISTS idx_notes_user ON notes(user_id);
CREATE INDEX IF NOT EXISTS idx_categories_user ON categories(user_id);
CREATE INDEX IF NOT EXISTS idx_tags_user ON tags(user_id);
"""

# 安全添加 user_id 列的 SQL（用于升级已有数据库）
# 如果列已存在，SQLite 会报错，用 try-except 忽略
MIGRATE_SQL = [
    "ALTER TABLE categories ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE",
    "ALTER TABLE notes ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE",
    "ALTER TABLE tags ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE",
]


async def init_db() -> None:
    """初始化数据库：确保数据目录存在并创建所有表"""
    db_dir = os.path.dirname(settings.DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    async with aiosqlite.connect(settings.DB_PATH) as db:
        # 开启外键约束支持
        await db.execute("PRAGMA foreign_keys = ON")
        await db.executescript(INIT_SQL)
        # 尝试为已有表添加 user_id 列（全新数据库不需要，但升级时需要）
        for sql in MIGRATE_SQL:
            try:
                await db.execute(sql)
            except aiosqlite.OperationalError:
                pass  # 列已存在，忽略
        await db.commit()


async def get_db():
    """FastAPI 依赖：提供一个异步数据库连接，请求结束后自动关闭"""
    db = await aiosqlite.connect(settings.DB_PATH)
    db.row_factory = aiosqlite.Row  # 让查询结果支持按列名访问
    try:
        yield db
    finally:
        await db.close()
