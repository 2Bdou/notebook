"""FastAPI 应用入口

挂载所有路由，启动时自动初始化数据库，并启用 CORS（开发阶段允许所有来源）。
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import init_db
from routers import notes, categories, tags, search, auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化数据库，关闭时无需特殊处理"""
    await init_db()
    yield


# 创建 FastAPI 应用实例
app = FastAPI(title="记事本 API", version="1.1.0", lifespan=lifespan)

# 启用 CORS（开发阶段允许所有来源访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载认证路由
app.include_router(auth.router, prefix="/api")

# 挂载业务路由（统一加 /api 前缀）
app.include_router(notes.router, prefix="/api")
app.include_router(categories.router, prefix="/api")
app.include_router(tags.router, prefix="/api")
app.include_router(search.router, prefix="/api")


@app.get("/api/health")
async def health():
    """健康检查接口"""
    return {"code": 0, "message": "success", "data": {"status": "ok"}}
