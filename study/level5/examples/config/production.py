# ========================================
# 生产环境配置
# ========================================
# 说明：生产环境的配置（最高安全性和性能）
# 特点：
# 1. 关闭调试模式
# 2. 启用所有安全特性
# 3. 使用高可用数据库和 Redis
# 4. 优化性能和资源使用
# 5. 详细的监控和日志
# ========================================

import os
from config.base import Settings


class ProductionSettings(Settings):
    """生产环境配置"""

    # ----------------------------------------
    # 应用配置
    # ----------------------------------------
    DEBUG: bool = False  # 必须关闭调试模式
    LOG_LEVEL: str = "WARNING"  # 警告及以上级别（减少日志量）

    # ----------------------------------------
    # 数据库配置（生产数据库集群）
    # ----------------------------------------
    # 格式：postgresql://user:password@primary-host:5432/database?options...
    DATABASE_URL: str = "postgresql://appuser:CHANGE_ME@prod-db-cluster.example.com:5432/appdb_prod"

    # 连接池配置（根据数据库服务器资源调整）
    DB_POOL_SIZE: int = 20  # 基础连接池大小
    DB_MAX_OVERFLOW: int = 40  # 最大额外连接数（总共 60 个连接）
    DB_POOL_TIMEOUT: int = 30  # 获取连接超时时间（秒）
    DB_POOL_RECYCLE: int = 3600  # 连接回收时间（1小时，防止连接长时间闲置）
    DB_ECHO: bool = False  # 绝不打印 SQL 语句（性能和安全考虑）

    # ----------------------------------------
    # Redis 配置（生产 Redis 集群）
    # ----------------------------------------
    # 格式：redis://[[username]:password@]host:port/db
    # 或使用 Redis Sentinel：redis://sentinel-password@sentinel-host:26379/mymaster/0
    REDIS_URL: str = "redis://:CHANGE_ME@prod-redis-cluster.example.com:6379/0"

    # Redis 连接池配置
    REDIS_MAX_CONNECTIONS: int = 100  # 最大连接数
    REDIS_SOCKET_TIMEOUT: int = 5  # Socket 读写超时（秒）
    REDIS_SOCKET_CONNECT_TIMEOUT: int = 5  # 连接超时（秒）

    # ----------------------------------------
    # 安全配置（使用强密钥）
    # ----------------------------------------
    # 密钥要求：
    # - 至少 32 字符
    # - 使用随机字符串生成器生成
    # - 定期轮换（建议每 90 天）
    # - 从密钥管理服务读取（AWS Secrets Manager, Azure Key Vault 等）
    SECRET_KEY: str = os.getenv("SECRET_KEY", "MUST_CHANGE_IN_PRODUCTION_AT_LEAST_32_CHARS")

    # JWT 配置
    ALGORITHM: str = "HS256"  # 或 RS256（使用公钥/私钥）
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # 访问令牌 15 分钟过期（安全考虑）
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # 刷新令牌 7 天过期

    # ----------------------------------------
    # CORS 配置（严格限制）
    # ----------------------------------------
    CORS_ENABLED: bool = True
    CORS_ALLOW_ORIGINS: list[str] = [
        "https://api.example.com",  # 仅允许生产域名
        "https://www.example.com",
    ]
    CORS_ALLOW_METHODS: list[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_ALLOW_HEADERS: list[str] = ["Content-Type", "Authorization", "X-Requested-With"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_EXPOSE_HEADERS: list[str] = ["X-Request-ID"]

    # ----------------------------------------
    # OpenAPI 文档配置（生产环境通常禁用或限制访问）
    # ----------------------------------------
    # 方案 1: 完全禁用（推荐）
    OPENAPI_URL: str = ""  # 空字符串表示禁用

    # 方案 2: 限制访问（需要认证）
    # OPENAPI_URL: str = "/docs"
    # docs_username: str = os.getenv("DOCS_USERNAME", "admin")
    # docs_password: str = os.getenv("DOCS_PASSWORD", "CHANGE_ME")

    # ----------------------------------------
    # 缓存配置（启用并优化）
    # ----------------------------------------
    CACHE_ENABLED: bool = True
    CACHE_DEFAULT_TTL: int = 600  # 10 分钟（生产环境缓存时间更长）
    CACHE_MAX_SIZE: int = 100000  # 最多 10 万条缓存

    # ----------------------------------------
    # 限流配置（启用并严格限制）
    # ----------------------------------------
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60  # 每分钟 60 次请求

    # 高级限流（基于 IP 和用户）
    RATE_LIMIT_BY_IP: bool = True
    RATE_LIMIT_PER_IP_PER_MINUTE: int = 100  # 每个 IP 每分钟 100 次

    # ----------------------------------------
    # 日志配置（结构化日志）
    # ----------------------------------------
    LOG_LEVEL: str = "WARNING"  # 只记录 WARNING 及以上级别
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(pathname)s:%(lineno)d"
    LOG_FILE: str = "logs/production.log"

    # 日志轮转
    LOG_ROTATION: bool = True
    LOG_MAX_BYTES: int = 10485760  # 10MB
    LOG_BACKUP_COUNT: int = 10  # 保留 10 个备份

    # 结构化日志（JSON 格式，方便日志聚合）
    LOG_JSON: bool = True

    # ----------------------------------------
    # 邮件配置（生产邮件服务器）
    # ----------------------------------------
    SMTP_HOST: str = "smtp.example.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = "notifications@example.com"
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "CHANGE_ME")
    SMTP_FROM: str = "noreply@example.com"
    SMTP_TLS: bool = True

    # 邮件重试配置
    SMTP_RETRY_ATTEMPTS: int = 3
    SMTP_RETRY_DELAY: int = 5  # 秒

    # ----------------------------------------
    # 文件上传配置（安全和存储）
    # ----------------------------------------
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB（严格限制）
    ALLOWED_EXTENSIONS: list[str] = ["jpg", "jpeg", "png", "gif", "pdf"]
    UPLOAD_DIR: str = "/var/uploads/production"  # 使用持久化存储

    # 文件存储（建议使用对象存储：S3, Azure Blob, GCS）
    STORAGE_TYPE: str = "s3"  # local, s3, azure, gcs
    AWS_S3_BUCKET: str = os.getenv("AWS_S3_BUCKET", "my-app-uploads")
    AWS_ACCESS_KEY: str = os.getenv("AWS_ACCESS_KEY", "")
    AWS_SECRET_KEY: str = os.getenv("AWS_SECRET_KEY", "")
    AWS_REGION: str = "us-east-1"

    # ----------------------------------------
    # 服务器配置（性能优化）
    # ----------------------------------------
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4  # 工作进程数（建议：CPU 核心数 * 2 + 1）

    # ----------------------------------------
    # 监控配置
    # ----------------------------------------
    # Prometheus metrics
    PROMETHEUS_ENABLED: bool = True
    PROMETHEUS_PORT: int = 9090
    PROMETHEUS_PATH: str = "/metrics"

    # Health check（健康检查）
    HEALTH_CHECK_ENABLED: bool = True
    HEALTH_CHECK_PATH: str = "/health"

    # Request ID（请求追踪）
    REQUEST_ID_HEADER: str = "X-Request-ID"
    REQUEST_ID_GENERATE: bool = True

    # ----------------------------------------
    # 外部 API 配置
    # ----------------------------------------
    EXTERNAL_API_TIMEOUT: int = 10  # 10 秒超时
    EXTERNAL_API_RETRIES: int = 3  # 重试 3 次

    # ----------------------------------------
    # 安全头（Security Headers）
    # ----------------------------------------
    # HTTPS 强制
    FORCE_HTTPS: bool = True

    # 安全头
    SECURE_HEADERS: bool = True
    X_FRAME_OPTIONS: str = "DENY"  # 防止点击劫持
    X_CONTENT_TYPE_OPTIONS: str = "nosniff"  # 防止 MIME 类型嗅探
    X_XSS_PROTECTION: str = "1; mode=block"  # XSS 保护
    CONTENT_SECURITY_POLICY: str = "default-src 'self'"  # CSP 策略
    STRICT_TRANSPORT_SECURITY: str = "max-age=31536000; includeSubDomains"  # HSTS

    # ----------------------------------------
    # 数据库备份配置
    # ----------------------------------------
    BACKUP_ENABLED: bool = True
    BACKUP_SCHEDULE: str = "0 2 * * *"  # 每天凌晨 2 点备份
    BACKUP_RETENTION_DAYS: int = 30  # 保留 30 天

    # ----------------------------------------
    # 验证器
    # ----------------------------------------
    def validate_production_config(self) -> None:
        """验证生产环境配置是否正确"""
        errors = []

        # 检查密钥
        if self.SECRET_KEY in ["CHANGE_ME", "MUST_CHANGE_IN_PRODUCTION_AT_LEAST_32_CHARS"]:
            errors.append("SECRET_KEY must be changed in production")

        # 检查数据库 URL
        if "CHANGE_ME" in self.DATABASE_URL:
            errors.append("DATABASE_URL must be set correctly in production")

        # 检查调试模式
        if self.DEBUG:
            errors.append("DEBUG must be False in production")

        # 检查 OpenAPI 文档
        if self.OPENAPI_URL and not self.OPENAPI_URL.startswith("/"):
            errors.append("OPENAPI_URL should be disabled or protected in production")

        # 检查 CORS
        if "localhost" in self.CORS_ALLOW_ORIGINS or "127.0.0.1" in self.CORS_ALLOW_ORIGINS:
            errors.append("CORS_ALLOW_ORIGINS should not include localhost in production")

        if errors:
            raise ValueError(f"Production configuration errors:\n" + "\n".join(f"- {e}" for e in errors))


# ========================================
# 创建配置实例
# ========================================
# 使用方式：
# from config.production import settings
# settings.validate_production_config()  # 验证配置
# print(settings.APP_NAME)
# ========================================

settings = ProductionSettings()

# 在加载配置时验证（可选）
# settings.validate_production_config()


# ========================================
# 使用说明
# ========================================
#
# 1. 生产环境部署：
#    # 设置环境变量（从密钥管理服务读取）
#    export SECRET_KEY=$(aws secretsmanager get-secret-value --secret-id prod/secret-key --query SecretString --output text)
#    export DATABASE_URL=$(aws secretsmanager get-secret-value --secret-id prod/database-url --query SecretString --output text)
#
#    # 使用 Docker
#    docker run -d -p 8000:8000 \
#      -e SECRET_KEY=$SECRET_KEY \
#      -e DATABASE_URL=$DATABASE_URL \
#      fastapi-app:latest
#
#    # 使用 Kubernetes
#    kubectl apply -f k8s/production/
#
# 2. 环境变量文件（.env.production）：
#    # 注意：不要将 .env.production 提交到代码库
#    SECRET_KEY=your-production-secret-key
#    DATABASE_URL=postgresql://user:pass@prod-db:5432/appdb_prod
#    REDIS_URL=redis://:password@prod-redis:6379/0
#    SMTP_PASSWORD=your-smtp-password
#
# 3. 访问生产环境：
#    https://api.example.com
#
# ========================================
# 生产环境最佳实践
# ========================================
#
# 1. 密钥管理：
#    - 使用 AWS Secrets Manager, Azure Key Vault, 或 HashiCorp Vault
#    - 定期轮换密钥（建议每 90 天）
#    - 不要在代码中硬编码密钥
#    - 不要将密钥提交到代码库
#
# 2. 数据库：
#    - 使用主从复制（高可用）
#    - 定期备份（每天至少一次）
#    - 测试备份恢复流程
#    - 监控数据库性能
#
# 3. Redis：
#    - 使用 Redis Cluster（高可用）
#    - 配置持久化（RDB + AOF）
#    - 监控内存使用
#    - 设置最大内存限制
#
# 4. 日志：
#    - 使用结构化日志（JSON）
#    - 集中收集日志（ELK, Loki）
#    - 设置日志保留策略
#    - 监控错误日志
#
# 5. 监控和告警：
#    - 使用 Prometheus + Grafana
#    - 配置告警规则（CPU, 内存, 响应时间, 错误率）
#    - 设置 PagerDuty 或钉钉告警
#    - 定期检查告警规则
#
# 6. 安全：
#    - 启用 HTTPS（Let's Encrypt 或商业证书）
#    - 配置防火墙规则
#    - 使用 Web Application Firewall (WAF)
#    - 定期扫描漏洞
#    - 更新依赖包
#
# 7. 性能优化：
#    - 使用 CDN（CloudFlare, CloudFront）
#    - 启用 gzip 压缩
#    - 配置缓存策略
#    - 使用连接池
#    - 优化数据库查询
#
# 8. 高可用：
#    - 部署多个副本（至少 3 个）
#    - 使用负载均衡
#    - 配置健康检查
#    - 自动故障转移
#    - 跨可用区部署
#
# ========================================
