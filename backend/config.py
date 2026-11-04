"""应用配置模块：从环境变量读取运行参数"""
import os


class Settings:
    """全局配置类

    通过环境变量注入，便于在容器 / 不同环境中灵活部署。
    """

    # SQLite 数据库文件路径，默认指向容器内数据目录
    DB_PATH: str = os.getenv("DB_PATH", "/app/data/notebook.db")

    # CORS 允许的来源（逗号分隔，默认 *；换为线上域名后可收紧）
    CORS_ORIGINS: list[str] = [
        o.strip()
        for o in os.getenv("CORS_ORIGINS", "*").split(",")
        if o.strip()
    ]

    # JWT 认证配置
    SECRET_KEY: str = os.getenv("SECRET_KEY", "notebook-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080"))

    # ====== 注册安全控制 ======

    # 是否开放注册（false 时注册接口直接拒绝，需管理员手动建账号）
    ALLOW_REGISTRATION: bool = os.getenv("ALLOW_REGISTRATION", "true").lower() == "true"

    # 注册邀请码（留空表示不需要邀请码；设置后注册必须提供正确的码）
    REGISTRATION_CODE: str = os.getenv("REGISTRATION_CODE", "")

    # 单 IP 每小时最多注册次数（防同一 IP 批量注册）
    REGISTRATION_IP_HOURLY_LIMIT: int = int(os.getenv("REGISTRATION_IP_HOURLY_LIMIT", "3"))

    # 认证接口全局速率限制（每分钟最大请求数，防暴力破解）
    AUTH_RATE_LIMIT_PER_MINUTE: int = int(os.getenv("AUTH_RATE_LIMIT_PER_MINUTE", "20"))

    # 认证接口单 IP 速率限制（每分钟最大请求数，防单来源暴力破解）
    AUTH_IP_RATE_LIMIT_PER_MINUTE: int = int(
        os.getenv("AUTH_IP_RATE_LIMIT_PER_MINUTE", "10")
    )


# 全局配置单例
settings = Settings()
