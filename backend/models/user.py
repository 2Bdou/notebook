"""User 数据访问层：用户注册、查询、密码校验

使用 bcrypt 库直接进行密码哈希（避免 passlib 与 bcrypt>=4.0 的兼容性问题）。
"""
from typing import Optional

import aiosqlite
import bcrypt


def hash_password(password: str) -> str:
    """对明文密码进行 bcrypt 哈希"""
    # bcrypt 限制密码长度 72 字节，超长截断
    pwd_bytes = password.encode("utf-8")[:72]
    return bcrypt.hashpw(pwd_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """验证明文密码是否与哈希匹配"""
    pwd_bytes = plain.encode("utf-8")[:72]
    hash_bytes = hashed.encode("utf-8")
    return bcrypt.checkpw(pwd_bytes, hash_bytes)


async def create_user(
    db: aiosqlite.Connection, username: str, password: str
) -> Optional[dict]:
    """创建用户，用户名重复时返回 None"""
    try:
        password_hash = hash_password(password)
        async with db.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            [username, password_hash],
        ) as cur:
            user_id = cur.lastrowid
        await db.commit()
    except aiosqlite.IntegrityError:
        # username 唯一约束冲突
        return None
    return await get_user_by_id(db, user_id)


async def get_user_by_username(
    db: aiosqlite.Connection, username: str
) -> Optional[dict]:
    """按用户名查询用户"""
    async with db.execute(
        "SELECT * FROM users WHERE username = ?", [username]
    ) as cur:
        row = await cur.fetchone()
    return dict(row) if row else None


async def get_user_by_id(db: aiosqlite.Connection, user_id: int) -> Optional[dict]:
    """按 ID 查询用户"""
    async with db.execute(
        "SELECT * FROM users WHERE id = ?", [user_id]
    ) as cur:
        row = await cur.fetchone()
    return dict(row) if row else None


async def authenticate_user(
    db: aiosqlite.Connection, username: str, password: str
) -> Optional[dict]:
    """验证用户名密码，成功返回用户字典，失败返回 None"""
    user = await get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    return user
