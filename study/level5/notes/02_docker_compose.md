# 02. Docker Compose - Docker Compose

## 📍 在架构中的位置

**从"单容器"到"多容器编排"**

```
┌─────────────────────────────────────────────────────────────┐
│          单个 Docker 容器                                    │
└─────────────────────────────────────────────────────────────┘

问题：
    FastAPI 应用容器
    └─ 数据库在哪？
    └─ Redis 在哪？

    需要手动：
    1. 启动 FastAPI 容器
    2. 启动 PostgreSQL 容器
    3. 启动 Redis 容器
    4. 配置网络（让容器互通）
    5. 配置数据卷（数据持久化）

    问题：命令复杂、容易出错 ❌

═══════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────┐
│          Docker Compose（多容器编排）                        │
└─────────────────────────────────────────────────────────────┘

一键启动：

    docker-compose up

    自动完成：
    1. ✅ 启动 FastAPI 容器
    2. ✅ 启动 PostgreSQL 容器
    3. ✅ 启动 Redis 容器
    4. ✅ 配置网络（容器互通）
    5. ✅ 配置数据卷（数据持久化）
    6. ✅ 按依赖顺序启动（数据库先启动）

    好处：简单、可靠、可重复 ✅
```

**🎯 你的学习目标**：掌握 Docker Compose，能够一键启动完整的 FastAPI 应用系统。

---

## 🎯 什么是 Docker Compose？

### 生活类比：搬家

**手动搬家（没有 Docker Compose）**：

```
搬家流程：
1. 租卡车
2. 装家具
3. 开车
4. 卸家具
5. 还卡车

问题：
- 步骤多，容易遗漏
- 需要协调多个任务
- 容易出错 ❌
```

**搬家套餐（有 Docker Compose）**：

```
一键服务：
- 搬家公司包办一切
- 只要说"搬家"
- 所有事情自动完成

好处：
- 简单 ✅
- 可靠 ✅
- 省心 ✅
```

---

### Docker Compose vs Docker

**对比表格**：

| 特性 | Docker | Docker Compose |
|------|--------|----------------|
| **管理容器** | 单个 | 多个 |
| **命令复杂度** | 高（需要多个命令） | 低（一个文件） |
| **网络配置** | 手动 | 自动 |
| **数据卷** | 手动 | 自动 |
| **依赖管理** | 手动 | 自动 |
| **适用场景** | 单容器 | 多容器应用 |

---

## 📝 docker-compose.yml 基础

### 基本结构

```yaml
# docker-compose.yml

version: '3.8'  # Compose 文件版本

services:        # 定义服务
  fastapi:       # 服务名称
    image: ...   # 镜像
    ports: ...   # 端口映射

volumes:         # 数据卷
networks:        # 网络
```

---

### FastAPI 应用示例

**完整 docker-compose.yml**：

```yaml
version: '3.8'

# ═══════════════════════════════════════════════════════════
# 服务定义
# ═══════════════════════════════════════════════════════════

services:
  # FastAPI 应用
  fastapi:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: fastapi-app
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/mydb
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - ./app:/app/app
    networks:
      - app-network

  # PostgreSQL 数据库
  db:
    image: postgres:15-alpine
    container_name: postgres-db
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=mydb
    volumes:
      - postgres-data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - app-network

  # Redis 缓存
  redis:
    image: redis:7-alpine
    container_name: redis-cache
    ports:
      - "6379:6379"
    networks:
      - app-network

  # Nginx 反向代理
  nginx:
    image: nginx:alpine
    container_name: nginx-proxy
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - fastapi
    networks:
      - app-network

# ═══════════════════════════════════════════════════════════
# 数据卷
# ═══════════════════════════════════════════════════════════

volumes:
  postgres-data:

# ═══════════════════════════════════════════════════════════
# 网络
# ═══════════════════════════════════════════════════════════

networks:
  app-network:
    driver: bridge
```

---

## 🔧 Compose 文件详解

### 1. 服务（services）

**FastAPI 服务**：

```yaml
services:
  fastapi:
    # 构建配置
    build:
      context: .              # 构建上下文
      dockerfile: Dockerfile  # Dockerfile 路径

    # 或使用已有镜像
    image: fastapi-app:v1.0

    # 容器名称
    container_name: fastapi-app

    # 端口映射（主机:容器）
    ports:
      - "8000:8000"
      - "8001:8001"  # 多个端口

    # 环境变量
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/mydb
      - REDIS_URL=redis://redis:6379

    # 或从文件读取
    env_file:
      - .env

    # 依赖（启动顺序）
    depends_on:
      - db
      - redis

    # 数据卷（主机:容器）
    volumes:
      - ./app:/app/app        # 开发时代码热更新
      - static-data:/app/static  # 命名卷

    # 网络
    networks:
      - app-network

    # 重启策略
    restart: always  # 总是重启
    # restart: on-failure  # 失败时重启
    # restart: no  # 不重启

    # 健康检查
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

---

### 2. PostgreSQL 服务

```yaml
services:
  db:
    image: postgres:15-alpine

    # 环境变量
    environment:
      - POSTGRES_USER=postgres        # 用户名
      - POSTGRES_PASSWORD=password    # 密码
      - POSTGRES_DB=mydb              # 数据库名

    # 数据卷（持久化）
    volumes:
      - postgres-data:/var/lib/postgresql/data

    # 端口（可选，用于本地连接）
    ports:
      - "5432:5432"

    # 健康检查
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
```

---

### 3. Redis 服务

```yaml
services:
  redis:
    image: redis:7-alpine

    # 端口
    ports:
      - "6379:6379"

    # 命令（带持久化）
    command: redis-server --appendonly yes

    # 数据卷
    volumes:
      - redis-data:/data

    # 健康检查
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
```

---

### 4. Nginx 反向代理

```yaml
services:
  nginx:
    image: nginx:alpine

    # 端口
    ports:
      - "80:80"
      - "443:443"

    # 配置文件
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro

    # 依赖
    depends_on:
      - fastapi
```

**nginx.conf 配置**：

```nginx
events {
    worker_connections 1024;
}

http {
    upstream fastapi {
        server fastapi:8000;
    }

    server {
        listen 80;

        location / {
            proxy_pass http://fastapi;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
```

---

## 🚀 Compose 命令

### 基本命令

```bash
# ═══════════════════════════════════════════════════════════
# 启动服务
# ═══════════════════════════════════════════════════════════

# 启动所有服务（前台运行）
docker-compose up

# 启动所有服务（后台运行）
docker-compose up -d

# 启动指定服务
docker-compose up fastapi db

# ═══════════════════════════════════════════════════════════
# 停止服务
# ═══════════════════════════════════════════════════════════

# 停止所有服务
docker-compose stop

# 停止指定服务
docker-compose stop fastapi

# ═══════════════════════════════════════════════════════════
# 重启服务
# ═══════════════════════════════════════════════════════════

docker-compose restart

# 重启指定服务
docker-compose restart fastapi

# ═══════════════════════════════════════════════════════════
# 删除服务
# ═══════════════════════════════════════════════════════════

# 停止并删除所有服务
docker-compose down

# 删除服务并删除数据卷
docker-compose down -v

# ═══════════════════════════════════════════════════════════
# 查看日志
# ═══════════════════════════════════════════════════════════

# 查看所有服务日志
docker-compose logs

# 查看指定服务日志
docker-compose logs fastapi

# 实时跟踪日志
docker-compose logs -f fastapi

# 查看最近 100 行
docker-compose logs --tail=100 fastapi

# ═══════════════════════════════════════════════════════════
# 查看状态
# ═══════════════════════════════════════════════════════════

# 查看运行中的服务
docker-compose ps

# 查看服务详情
docker-compose top
```

---

### 构建和运行

```bash
# ═══════════════════════════════════════════════════════════
# 构建镜像
# ═══════════════════════════════════════════════════════════

# 构建所有服务的镜像
docker-compose build

# 构建指定服务的镜像
docker-compose build fastapi

# 重新构建（不使用缓存）
docker-compose build --no-cache

# ═══════════════════════════════════════════════════════════
# 构建并启动
# ═══════════════════════════════════════════════════════════

# 构建并启动所有服务
docker-compose up -d --build

# ═══════════════════════════════════════════════════════════
# 执行命令
# ═══════════════════════════════════════════════════════════

# 在运行的容器中执行命令
docker-compose exec fastapi bash

# 运行一次性命令
docker-compose run fastapi python -m pytest
```

---

## 🎨 实际场景：完整应用

### 目录结构

```
myapp/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env
├── .env.example
├── nginx.conf
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   ├── models/
│   └── services/
└── tests/
```

---

### docker-compose.yml（生产环境）

```yaml
version: '3.8'

services:
  # FastAPI 应用
  api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: fastapi-api
    restart: always
    environment:
      - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
      - REDIS_URL=redis://redis:6379
      - SECRET_KEY=${SECRET_KEY}
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # PostgreSQL 数据库
  db:
    image: postgres:15-alpine
    container_name: postgres-db
    restart: always
    environment:
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=${POSTGRES_DB}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - app-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis 缓存
  redis:
    image: redis:7-alpine
    container_name: redis-cache
    restart: always
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis-data:/data
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Nginx 反向代理
  nginx:
    image: nginx:alpine
    container_name: nginx-proxy
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - api
    networks:
      - app-network

volumes:
  postgres-data:
  redis-data:

networks:
  app-network:
    driver: bridge
```

---

### .env.example（环境变量模板）

```bash
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password_here
POSTGRES_DB=myapp

# Redis
REDIS_PASSWORD=your_redis_password_here

# App
SECRET_KEY=your_secret_key_here

# Environment
ENVIRONMENT=production
DEBUG=false
```

---

## 🎯 小实验：自己动手

### 实验 1：基本 Compose 应用

```yaml
# docker-compose.yml
version: '3.8'

services:
  fastapi:
    image: fastapi-app:v1.0
    ports:
      - "8000:8000"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

```bash
# 启动
docker-compose up -d

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs

# 停止
docker-compose down
```

---

### 实验 2：多环境配置

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    image: fastapi-app:${APP_VERSION:-latest}
    environment:
      - DEBUG=${DEBUG:-false}
```

```bash
# 开发环境
export APP_VERSION=dev
export DEBUG=true
docker-compose up

# 生产环境
export APP_VERSION=v1.0
export DEBUG=false
docker-compose up
```

---

## 📚 检查理解

回答这些问题来测试你的理解：

1. **什么是 Docker Compose？**
   - 提示：多容器编排工具

2. **Docker 和 Docker Compose 的区别？**
   - 提示：单容器 vs 多容器

3. **depends_on 的作用？**
   - 提示：控制启动顺序

4. **为什么需要数据卷（volumes）？**
   - 提示：数据持久化

5. **如何实现服务间通信？**
   - 提示：网络（networks）

---

## 🚀 下一步

现在你已经掌握了 Docker Compose，接下来：

1. **学习 Kubernetes**：`notes/03_kubernetes.md`
2. **查看实际代码**：`examples/docker-compose.yml`

**记住**：Docker Compose 让多容器应用管理变得简单，是本地开发和测试的最佳工具！**

---

**费曼技巧总结**：
- ✅ 搬家类比
- ✅ 完整的 docker-compose.yml 示例
- ✅ 常用命令（up, down, logs, ps）
- ✅ 数据卷和网络配置
- ✅ 健康检查和依赖管理
