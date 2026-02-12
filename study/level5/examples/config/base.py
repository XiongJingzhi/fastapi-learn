# ========================================
# 基础配置（所有环境共享）
# ========================================
# 说明：定义所有环境的公共配置
# 特定环境配置在对应文件中覆盖
# ========================================

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator
from typing import Optional
import os


class Settings(BaseSettings):
    """应用基础配置类"""

    # ----------------------------------------
    # 配置文件加载方式
    # ----------------------------------------
    model_config = SettingsConfigDict(
        env_file=".env",  # 从 .env 文件加载环境变量
        env_file_encoding="utf-8",
        case_sensitive=False,  # 不区分大小写
        extra="ignore",  # 忽略额外的字段
    )

    # ----------------------------------------
    # 应用基础配置
    # ----------------------------------------
    APP_NAME: str = Field(default="FastAPI Application", description="应用名称")
    APP_VERSION: str = Field(default="1.0.0", description="应用版本")
    APP_DESCRIPTION: str = Field(default="Production FastAPI Application", description="应用描述")
    DEBUG: bool = Field(default=False, description="调试模式")

    # 服务器配置
    HOST: str = Field(default="0.0.0.0", description="监听地址")
    PORT: int = Field(default=8000, description="监听端口")
    WORKERS: int = Field(default=1, description="工作进程数")

    # ----------------------------------------
    # 数据库配置
    # ----------------------------------------
    # 数据库连接 URL 格式：
    # postgresql://user:password@host:port/database
    DATABASE_URL: str = Field(default="postgresql://user:pass@localhost:5432/appdb", description="数据库连接 URL")

    # 数据库连接池配置
    DB_POOL_SIZE: int = Field(default=20, description="数据库连接池大小")
    DB_MAX_OVERFLOW: int = Field(default=10, description="连接池最大溢出")
    DB_POOL_TIMEOUT: int = Field(default=30, description="连接池超时（秒）")
    DB_POOL_RECYCLE: int = Field(default=3600, description="连接回收时间（秒）")
    DB_ECHO: bool = Field(default=False, description="是否打印 SQL 语句")

    # ----------------------------------------
    # Redis 配置
    # ----------------------------------------
    # Redis 连接 URL 格式：
    # redis://[[username]:[password]]@localhost:6379/0
    REDIS_URL: str = Field(default="redis://localhost:6379/0", description="Redis 连接 URL")

    # Redis 连接池配置
    REDIS_MAX_CONNECTIONS: int = Field(default=50, description="Redis 最大连接数")
    REDIS_SOCKET_TIMEOUT: int = Field(default=5, description="Redis Socket 超时（秒）")
    REDIS_SOCKET_CONNECT_TIMEOUT: int = Field(default=5, description="Redis 连接超时（秒）")

    # ----------------------------------------
    # 安全配置
    # ----------------------------------------
    # 密钥配置（用于 JWT, 加密等）
    SECRET_KEY: str = Field(default="change-this-in-production", description="应用密钥")
    ALGORITHM: str = Field(default="HS256", description="JWT 算法")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="访问令牌过期时间（分钟）")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="刷新令牌过期时间（天）")

    # ----------------------------------------
    # CORS 配置
    # ----------------------------------------
    CORS_ENABLED: bool = Field(default=True, description="是否启用 CORS")
    CORS_ALLOW_ORIGINS: list[str] = Field(default=["http://localhost:3000"], description="允许的源")
    CORS_ALLOW_METHODS: list[str] = Field(default=["GET", "POST", "PUT", "DELETE", "OPTIONS"], description="允许的方法")
    CORS_ALLOW_HEADERS: list[str] = Field(default=["*"], description="允许的请求头")
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True, description="是否允许携带凭证")

    # ----------------------------------------
    # API 配置
    # ----------------------------------------
    API_PREFIX: str = Field(default="/api/v1", description="API 路由前缀")
    OPENAPI_URL: Optional[str] = Field(default="/docs", description="OpenAPI 文档 URL")
    OPENAPI_TITLE: str = Field(default="FastAPI API", description="API 标题")
    OPENAPI_VERSION: str = Field(default="1.0.0", description="API 版本")
    OPENAPI_DESCRIPTION: str = Field(default="FastAPI Application API", description="API 描述")

    # ----------------------------------------
    # 日志配置
    # ----------------------------------------
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")
    LOG_FORMAT: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s", description="日志格式")
    LOG_FILE: str = Field(default="logs/app.log", description="日志文件路径")

    # ----------------------------------------
    # 缓存配置
    # ----------------------------------------
    CACHE_ENABLED: bool = Field(default=True, description="是否启用缓存")
    CACHE_DEFAULT_TTL: int = Field(default=300, description="缓存默认过期时间（秒）")
    CACHE_MAX_SIZE: int = Field(default=10000, description="缓存最大条目数")

    # ----------------------------------------
    # 限流配置
    # ----------------------------------------
    RATE_LIMIT_ENABLED: bool = Field(default=False, description="是否启用限流")
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = Field(default=60, description="每分钟请求数限制")

    # ----------------------------------------
    # 文件上传配置
    # ----------------------------------------
    MAX_UPLOAD_SIZE: int = Field(default=10485760, description="最大上传文件大小（字节，默认 10MB）")
    ALLOWED_EXTENSIONS: list[str] = Field(default=["jpg", "jpeg", "png", "gif", "pdf"], description="允许的文件扩展名")
    UPLOAD_DIR: str = Field(default="uploads", description="上传文件保存目录")

    # ----------------------------------------
    # 邮件配置（可选）
    # ----------------------------------------
    SMTP_HOST: Optional[str] = Field(default=None, description="SMTP 服务器地址")
    SMTP_PORT: int = Field(default=587, description="SMTP 端口")
    SMTP_USER: Optional[str] = Field(default=None, description="SMTP 用户名")
    SMTP_PASSWORD: Optional[str] = Field(default=None, description="SMTP 密码")
    SMTP_FROM: Optional[str] = Field(default=None, description="发件人地址")
    SMTP_TLS: bool = Field(default=True, description="是否使用 TLS")

    # ----------------------------------------
    # 外部 API 配置（可选）
    # ----------------------------------------
    EXTERNAL_API_TIMEOUT: int = Field(default=30, description="外部 API 超时时间（秒）")
    EXTERNAL_API_RETRIES: int = Field(default=3, description="外部 API 重试次数")

    # ----------------------------------------
    # 验证器
    # ----------------------------------------
    @validator("DATABASE_URL")
    def validate_database_url(cls, v):
        """验证数据库 URL 格式"""
        if not v.startswith(("postgresql://", "postgresql+asyncpg://")):
            raise ValueError("DATABASE_URL must start with 'postgresql://' or 'postgresql+asyncpg://'")
        return v

    @validator("REDIS_URL")
    def validate_redis_url(cls, v):
        """验证 Redis URL 格式"""
        if not v.startswith("redis://"):
            raise ValueError("REDIS_URL must start with 'redis://'")
        return v

    @validator("SECRET_KEY")
    def validate_secret_key(cls, v):
        """验证密钥强度"""
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v

    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        """验证日志级别"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v.upper()

    # ----------------------------------------
    # 辅助方法
    # ----------------------------------------
    def get_database_url(self, async_mode: bool = True) -> str:
        """
        获取数据库连接 URL

        Args:
            async_mode: 是否使用异步模式

        Returns:
            数据库连接 URL
        """
        if async_mode:
            # 使用 asyncpg 驱动（异步）
            return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
        return self.DATABASE_URL

    def get_redis_url(self, db: int = 0) -> str:
        """
        获取 Redis 连接 URL

        Args:
            db: Redis 数据库编号

        Returns:
            Redis 连接 URL
        """
        return f"{self.REDIS_URL.rstrip('/')}/{db}"


# ========================================
# 创建配置实例
# ========================================
# 使用方式：
# from config.base import settings
# print(settings.APP_NAME)
# ========================================

settings = Settings()


# ========================================
# 使用说明
# ========================================
#
# 1. 基础使用：
#    from config.base import settings
#
#    print(settings.APP_NAME)
#    print(settings.DATABASE_URL)
#
# 2. 获取数据库 URL（异步）：
#    db_url = settings.get_database_url(async_mode=True)
#
# 3. 获取 Redis URL（指定数据库）：
#    redis_url = settings.get_redis_url(db=1)
#
# 4. 在 FastAPI 中使用：
#    from fastapi import FastAPI
#    from config.base import settings
#
#    app = FastAPI(
#         title=settings.OPENAPI_TITLE,
#         version=settings.OPENAPI_VERSION,
#         debug=settings.DEBUG,
#     )
#
# 5. 从环境变量加载：
#    # 创建 .env 文件
#    APP_NAME=My App
#    DATABASE_URL=postgresql://user:pass@localhost/db
#
#    # 配置会自动从 .env 加载
#
# ========================================
