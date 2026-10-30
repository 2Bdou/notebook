"""应用配置模块：从环境变量读取运行参数"""
import os


class Settings:
    """全局配置类

    通过环境变量注入，便于在容器 / 不同环境中灵活部署。
    """

    # SQLite 数据库文件路径，默认指向容器内数据目录
    DB_PATH: str = os.getenv("DB_PATH", "/app/data/notebook.db")

    # CORS 允许的来源（开发阶段允许所有来源）
    CORS_ORIGINS: list[str] = ["*"]


# 全局配置单例
settings = Settings()
