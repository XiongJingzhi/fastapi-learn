# ========================================
# 预发环境配置
# ========================================
# 说明：预发布环境的配置（介于开发和生产之间）
# 特点：
# 1. 接近生产环境配置
# 2. 启用限流和缓存
# 3. 使用预发数据库和 Redis
# 4. 启用监控和告警
# ========================================

from config.base import Settings


class StagingSettings(Settings):
    """预发环境配置"""

    # ----------------------------------------
    # 应用配置
    # ----------------------------------------
    DEBUG: bool = False  # 关闭调试模式
    LOG_LEVEL: str = "INFO"  # 信息日志

    # ----------------------------------------
    # 数据库配置（预发数据库）
    # ----------------------------------------
    DATABASE_URL: str = "postgresql://appuser:CHANGE_ME@staging-db.example.com:5432/appdb_staging"
    DB_POOL_SIZE: int = 10  # 预发环境连接池较小
    DB_MAX_OVERFLOW: int = 5
    DB_ECHO: bool = False  # 关闭 SQL 日志

    # ----------------------------------------
    # Redis 配置（预发 Redis）
    # ----------------------------------------
    REDIS_URL: str = "redis://:CHANGE_ME@staging-redis.example.com:6379/0"
    REDIS_MAX_CONNECTIONS: int = 30

    # ----------------------------------------
    # 安全配置（使用强密钥）
    # ----------------------------------------
    SECRET_KEY: str = "CHANGE_THIS_IN_STAGING_ENVIRONMENT_AT_LEAST_32_CHARS"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ----------------------------------------
    # CORS 配置（仅允许预发域名）
    # ----------------------------------------
    CORS_ALLOW_ORIGINS: list[str] = [
        "https://staging.example.com",
        "https://www.staging.example.com",
    ]
    CORS_ALLOW_CREDENTIALS: bool = True

    # ----------------------------------------
    # OpenAPI 文档配置（启用文档）
    # ----------------------------------------
    OPENAPI_URL: str = "/docs"
    OPENAPI_TITLE: str = "FastAPI Staging API"
    OPENAPI_DESCRIPTION: str = "Staging Environment API"

    # ----------------------------------------
    # 缓存配置（启用缓存）
    # ----------------------------------------
    CACHE_ENABLED: bool = True
    CACHE_DEFAULT_TTL: int = 300  # 5分钟

    # ----------------------------------------
    # 限流配置（启用限流）
    # ----------------------------------------
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 120  # 预发环境限流较宽松

    # ----------------------------------------
    # 日志配置
    # ----------------------------------------
    LOG_FILE: str = "logs/staging.log"

    # ----------------------------------------
    # 邮件配置（真实邮件服务器）
    # ----------------------------------------
    SMTP_HOST: str = "smtp.example.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = "staging@example.com"
    SMTP_PASSWORD: str = "CHANGE_ME"
    SMTP_FROM: str = "noreply@staging.example.com"
    SMTP_TLS: bool = True

    # ----------------------------------------
    # 文件上传配置
    # ----------------------------------------
    UPLOAD_DIR: str = "uploads/staging"

    # ----------------------------------------
    # 服务器配置
    # ----------------------------------------
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 2  # 预发环境使用 2 个工作进程

    # ----------------------------------------
    # 监控配置
    # ----------------------------------------
    # Prometheus metrics
    PROMETHEUS_ENABLED: bool = True
    PROMETHEUS_PORT: int = 9090

    # Health check
    HEALTH_CHECK_ENABLED: bool = True


# ========================================
# 创建配置实例
# ========================================
# 使用方式：
# from config.staging import settings
# print(settings.APP_NAME)
# ========================================

settings = StagingSettings()


# ========================================
# 使用说明
# ========================================
#
# 1. 预发环境部署：
#    # 使用 Docker
#    docker build -t fastapi-app:staging .
#    docker run -d -p 8000:8000 --env-file .env.staging fastapi-app:staging
#
#    # 使用 Kubernetes
#    kubectl apply -f k8s/staging/
#
# 2. 环境变量文件（.env.staging）：
#    DATABASE_URL=postgresql://user:pass@staging-db:5432/appdb_staging
#    REDIS_URL=redis://:password@staging-redis:6379/0
#    SECRET_KEY=your-staging-secret-key
#
# 3. 访问预发环境：
#    https://staging.example.com
#    https://staging.example.com/docs
#
# 4. 数据库迁移：
#    alembic upgrade head
#
# ========================================
# 预发环境最佳实践
# ========================================
#
# 1. 配置管理：
#    - 使用与生产环境相似的配置
#    - 所有敏感信息从环境变量读取
#    - 定期更新密钥和密码
#
# 2. 测试流程：
#    - 部署到预发环境 → 运行集成测试 → 人工测试 → 部署到生产
#    - 使用真实数据（脱敏）
#    - 测试所有关键功能
#
# 3. 监控和告警：
#    - 启用所有监控
#    - 测试告警规则
#    - 配置日志聚合
#
# 4. 性能测试：
#    - 运行负载测试
#    - 检查响应时间
#    - 验证扩缩容
#
# 5. 安全检查：
#    - 扫描漏洞
#    - 检查依赖
#    - 审计权限
#
# ========================================
