# 05. 多环境配置 - Multi-Environment Configuration

## 📍 在架构中的位置

**从"硬编码配置"到"环境隔离"**

```
┌─────────────────────────────────────────────────────────────┐
│          硬编码配置（错误做法）                               │
└─────────────────────────────────────────────────────────────┘

代码中：

    DATABASE_PASSWORD = "password123"  # ❌ 密码泄露！

    部署到生产环境：
    → 密码在代码中
    → 代码泄露？密码泄露！❌
    → 无法为不同环境使用不同配置 ❌

═══════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────┐
│          环境变量配置（正确做法）                             │
└─────────────────────────────────────────────────────────────┘

代码中：

    DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")  # ✅

    开发环境：
    .env.development → DATABASE_PASSWORD=dev_password

    测试环境：
    .env.staging → DATABASE_PASSWORD=staging_password

    生产环境：
    .env.production → DATABASE_PASSWORD=prod_password（从密钥管理服务读取）

    好处：
    - 配置不进代码库 ✅
    - 不同环境不同配置 ✅
    - 安全 ✅
```

**🎯 你的学习目标**：掌握多环境配置管理，实现开发、测试、生产环境的配置隔离。

---

## 🎯 为什么需要多环境配置？

### 不同环境的需求

```
开发环境（Development）：
    └─ 目的：日常开发
    └─ 配置：
        ├─ DEBUG=True
        ├─ 数据库：本地 SQLite
        ├─ 日志级别：DEBUG
        └─ 热更新：启用

测试环境（Staging）：
    └─ 目的：预发布测试
    └─ 配置：
        ├─ DEBUG=False
        ├─ 数据库：PostgreSQL（测试服务器）
        ├─ 日志级别：INFO
        └─ 模拟生产环境

生产环境（Production）：
    └─ 目的：线上运行
    └─ 配置：
        ├─ DEBUG=False
        ├─ 数据库：PostgreSQL（高可用集群）
        ├─ 日志级别：WARNING
        └─ 性能优化：全部启用
```

---

## 🔧 配置管理方式

### 1. 环境变量

**FastAPI + pydantic-settings**：

```python
# config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """应用配置"""

    # 应用信息
    app_name: str = "FastAPI App"
    app_version: str = "1.0.0"
    environment: str = "development"  # development, staging, production

    # 服务器
    host: str = "0.0.0.0"
    port: int = 8000

    # 数据库
    database_url: str
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # Redis
    redis_url: str

    # 安全
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # 日志
    log_level: str = "INFO"

    # CORS
    cors_origins: list[str] = []

    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    """获取配置（缓存）"""
    return Settings()

# 使用
settings = get_settings()
print(settings.database_url)
```

---

### 2. 多环境配置文件

**`.env.development`**：

```bash
# Environment
ENVIRONMENT=development
DEBUG=true

# Database
DATABASE_URL=postgresql://postgres:dev_password@localhost:5432/mydb_dev
DATABASE_POOL_SIZE=5

# Redis
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=dev_secret_key_change_in_production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Logging
LOG_LEVEL=DEBUG

# CORS
CORS_ORIGINS=["http://localhost:3000"]
```

---

**`.env.staging`**：

```bash
# Environment
ENVIRONMENT=staging
DEBUG=false

# Database
DATABASE_URL=postgresql://postgres:staging_password@staging-db.example.com:5432/mydb_staging
DATABASE_POOL_SIZE=10

# Redis
REDIS_URL=redis://staging-redis.example.com:6379

# Security
SECRET_KEY=${STAGING_SECRET_KEY}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Logging
LOG_LEVEL=INFO

# CORS
CORS_ORIGINS=["https://staging.example.com"]
```

---

**`.env.production`**：

```bash
# Environment
ENVIRONMENT=production
DEBUG=false

# Database
DATABASE_URL=${PROD_DATABASE_URL}
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40

# Redis
REDIS_URL=${PROD_REDIS_URL}

# Security
SECRET_KEY=${PROD_SECRET_KEY}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15

# Logging
LOG_LEVEL=WARNING

# CORS
CORS_ORIGINS=["https://example.com"]
```

---

### 3. 加载不同环境的配置

**方式 1：通过环境变量**：

```python
import os
from pathlib import Path

# 获取当前环境
ENV = os.getenv("ENVIRONMENT", "development")

# 加载对应的 .env 文件
env_file = f".env.{ENV}"
from dotenv import load_dotenv
load_dotenv(env_file)

settings = Settings()
```

---

**方式 2：通过命令行参数**：

```bash
# 启动时指定环境
ENVIRONMENT=production uvicorn main:app

# 或使用 .env 文件
uvicorn main:app --env-file .env.production
```

---

## 🔐 Kubernetes ConfigMap 和 Secret

### ConfigMap（非敏感配置）

**k8s/production/configmap.yaml**：

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  ENVIRONMENT: "production"
  DEBUG: "false"
  LOG_LEVEL: "WARNING"
  CORS_ORIGINS: '["https://example.com"]'
```

---

### Secret（敏感配置）

**k8s/production/secret.yaml**：

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secret
type: Opaque
stringData:  # 自动 Base64 编码
  DATABASE_URL: "postgresql://user:password@db:5432/mydb"
  REDIS_URL: "redis://redis:6379"
  SECRET_KEY: "production_secret_key"
```

---

**使用 Secret**：

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: fastapi-app
spec:
  containers:
  - name: fastapi
    image: fastapi-app:v1.0
    envFrom:
    - configMapRef:
        name: app-config
    - secretRef:
        name: app-secret
```

---

## 🎨 配置验证

### Pydantic 验证

```python
from pydantic import validator, Field

class Settings(BaseSettings):
    """应用配置（带验证）"""

    # 必填字段
    database_url: str = Field(..., description="Database URL")

    # 验证 URL 格式
    @validator("database_url")
    def validate_database_url(cls, v):
        if not v.startswith(("postgresql://", "postgresql+asyncpg://")):
            raise ValueError("Invalid database URL")
        return v

    # 验证端口号范围
    port: int = Field(ge=1, le=65535, default=8000)

    # 验证环境值
    environment: str = Field(
        ...,
        regex="^(development|staging|production)$"
    )

    # 根据环境设置默认值
    @validator("debug", pre=True)
    def set_debug_default(cls, v, values):
        if v is None:
            env = values.get("environment", "development")
            return env == "development"
        return v

    debug: bool = False
```

---

## 🎯 小实验：自己动手

### 实验 1：基本环境变量

```python
# main.py
import os
from fastapi import FastAPI

app = FastAPI()

@app.get("/config")
async def get_config():
    return {
        "environment": os.getenv("ENVIRONMENT", "development"),
        "debug": os.getenv("DEBUG", "false")
    }
```

```bash
# 运行
ENVIRONMENT=production DEBUG=true uvicorn main:app
```

---

### 实验 2：Pydantic Settings

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    redis_url: str

    class Config:
        env_file = ".env"

settings = Settings()
print(settings.database_url)
```

---

## 📚 检查理解

回答这些问题来测试你的理解：

1. **为什么需要多环境配置？**
   - 提示：不同环境不同需求、安全

2. **环境变量和配置文件的区别？**
   - 提示：动态 vs 静态

3. **ConfigMap 和 Secret 的区别？**
   - 提示：敏感 vs 非敏感

4. **如何验证配置？**
   - 提示：Pydantic 验证器

5. **如何管理敏感配置？**
   - 提示：Secret、密钥管理服务

---

## 🚀 下一步

现在你已经掌握了多环境配置，接下来：

1. **学习部署策略**：`notes/06_deployment_strategies.md`
2. **查看实际代码**：`examples/config.py`

**记住**：配置管理是安全运维的基础，敏感信息永远不要进代码库！**

---

**费曼技巧总结**：
- ✅ 环境隔离的重要性
- ✅ 环境变量配置
- ✅ Pydantic Settings 使用
- ✅ Kubernetes ConfigMap 和 Secret
- ✅ 配置验证方法
