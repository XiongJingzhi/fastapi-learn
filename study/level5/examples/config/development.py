# ========================================
# 开发环境配置
# ========================================
# 说明：本地开发环境的配置
# 特点：
# 1. 启用调试模式
# 2. 使用本地数据库和 Redis
# 3. 启用详细日志
# 4. 禁用限流和缓存
# ========================================

from config.base import Settings


class DevelopmentSettings(Settings):
    """开发环境配置"""

    # ----------------------------------------
    # 应用配置
    # ----------------------------------------
    DEBUG: bool = True  # 启用调试模式
    LOG_LEVEL: str = "DEBUG"  # 详细日志

    # ----------------------------------------
    # 数据库配置（本地开发数据库）
    # ----------------------------------------
    DATABASE_URL: str = "postgresql://appuser:apppass@localhost:5432/appdb_dev"
    DB_ECHO: bool = True  # 打印 SQL 语句（方便调试）

    # ----------------------------------------
    # Redis 配置（本地 Redis）
    # ----------------------------------------
    REDIS_URL: str = "redis://localhost:6379/0"

    # ----------------------------------------
    # 安全配置（开发环境使用弱密钥）
    # ----------------------------------------
    SECRET_KEY: str = "development-secret-key-do-not-use-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 开发环境令牌过期时间更长

    # ----------------------------------------
    # CORS 配置（允许所有源）
    # ----------------------------------------
    CORS_ALLOW_ORIGINS: list[str] = [
        "http://localhost:3000",  # React Dev Server
        "http://localhost:8000",  # FastAPI
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]
    CORS_ALLOW_CREDENTIALS: bool = True

    # ----------------------------------------
    # OpenAPI 文档配置
    # ----------------------------------------
    OPENAPI_URL: str = "/docs"  # 启用 Swagger UI
    OPENAPI_TITLE: str = "FastAPI Development API"

    # ----------------------------------------
    # 缓存配置（禁用缓存，方便调试）
    # ----------------------------------------
    CACHE_ENABLED: bool = False  # 开发环境禁用缓存
    CACHE_DEFAULT_TTL: int = 60  # 短过期时间

    # ----------------------------------------
    # 限流配置（禁用限流）
    # ----------------------------------------
    RATE_LIMIT_ENABLED: bool = False  # 开发环境禁用限流

    # ----------------------------------------
    # 日志配置（控制台输出）
    # ----------------------------------------
    LOG_FILE: str = "logs/development.log"

    # ----------------------------------------
    # 邮件配置（可选：使用 MailHog 测试）
    # ----------------------------------------
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025  # MailHog 默认端口
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@localhost"
    SMTP_TLS: bool = False

    # ----------------------------------------
    # 文件上传配置
    # ----------------------------------------
    UPLOAD_DIR: str = "uploads/development"

    # ----------------------------------------
    # 服务器配置
    # ----------------------------------------
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1  # 开发环境使用单进程（支持热重载）


# ========================================
# 创建配置实例
# ========================================
# 使用方式：
# from config.development import settings
# print(settings.APP_NAME)
# ========================================

settings = DevelopmentSettings()


# ========================================
# 使用说明
# ========================================
#
# 1. 开发环境启动应用：
#    # 使用 uvicorn 启动（支持热重载）
#    uvicorn main:app --reload --host 0.0.0.0 --port 8000
#
# 2. 使用 Docker Compose 启动：
#    docker-compose -f docker-compose.dev.yml up -d
#
# 3. 访问 API 文档：
#    http://localhost:8000/docs
#
# 4. 访问数据库：
#    psql -h localhost -U appuser -d appdb_dev
#
# 5. 访问 Redis：
#    redis-cli
#
# ========================================
# 开发环境最佳实践
# ========================================
#
# 1. 数据库：
#    - 使用 Docker Compose 启动 PostgreSQL
#    - 定期备份数据
#    - 使用 pgAdmin 管理数据库
#
# 2. Redis：
#    - 使用 Docker Compose 启动 Redis
#    - 使用 Redis Commander 管理
#
# 3. 邮件测试：
#    - 使用 MailHog 捕获邮件
#    - 访问 http://localhost:8025 查看邮件
#
# 4. 日志：
#    - 使用 DEBUG 级别
#    - 实时查看日志：tail -f logs/development.log
#
# 5. 热重载：
#    - 使用 uvicorn --reload
#    - 代码修改后自动重启
#
# ========================================
