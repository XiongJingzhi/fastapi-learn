# Level 5 基础练习题

## 🎯 练习目标

通过实战练习，掌握 Docker 容器化和本地部署的基本技能。

---

## 练习 1: 编写基础 Dockerfile

### 题目

为一个简单的 FastAPI 应用编写 Dockerfile。

### 要求

1. 创建一个简单的 FastAPI 应用（`main.py`）
2. 编写 Dockerfile 容器化该应用
3. 构建并运行容器
4. 访问 http://localhost:8000/docs 验证

### 示例代码

`main.py`:

```python
from fastapi import FastAPI

app = FastAPI(title="Docker Test App")

@app.get("/")
def read_root():
    return {"message": "Hello from Docker!"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
```

`Dockerfile`:

```dockerfile
# 你的代码在这里

# 提示：
# 1. 选择合适的基础镜像
# 2. 安装依赖
# 3. 复制代码
# 4. 暴露端口
# 5. 定义启动命令
```

### 检查清单

完成练习后，确认你可以：

- [ ] 成功构建 Docker 镜像
- [ ] 运行容器并访问应用
- [ ] 看到容器日志输出
- [ ] 容器重启后应用正常运行

### 提示

```bash
# 构建镜像
docker build -t fastapi-test:latest .

# 运行容器
docker run -d -p 8000:8000 --name fastapi-test fastapi-test:latest

# 查看日志
docker logs -f fastapi-test

# 停止容器
docker stop fastapi-test

# 删除容器
docker rm fastapi-test
```

---

## 练习 2: 优化 Dockerfile（多阶段构建）

### 题目

优化上一个练习的 Dockerfile，使用多阶段构建减小镜像大小。

### 要求

1. 使用多阶段构建（Builder + Runtime）
2. 创建非特权用户运行应用
3. 添加健康检查
4. 优化镜像大小

### 示例代码

`Dockerfile`:

```dockerfile
# 阶段 1: 构建阶段
FROM ??? as builder

# 你的代码在这里

# 阶段 2: 运行阶段
FROM ???

# 你的代码在这里

# 提示：
# - 使用 python:3.11-slim 作为基础镜像
# - 创建非 root 用户
# - 安装依赖到单独的目录
# - 复制应用代码
# - 配置健康检查
```

### 对比镜像大小

```bash
# 查看镜像大小
docker images | grep fastapi

# 应该看到优化后的镜像更小
```

### 检查清单

- [ ] 使用多阶段构建
- [ ] 非 root 用户运行
- [ ] 健康检查正常工作
- [ ] 镜像大小小于优化前

---

## 练习 3: 使用 Docker Compose

### 题目

使用 Docker Compose 编排 FastAPI 应用和 PostgreSQL 数据库。

### 要求

1. 创建 `docker-compose.yml`
2. 包含 FastAPI 应用服务
3. 包含 PostgreSQL 数据库服务
4. 配置网络和卷
5. 一键启动整个系统

### 示例代码

`docker-compose.yml`:

```yaml
version: '3.8'

services:
  # FastAPI 应用
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/appdb
    depends_on:
      - db
    # 你的代码在这里

  # PostgreSQL 数据库
  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=appdb
    # 你的代码在这里

# 提示：
# - 配置数据卷（持久化）
# - 配置健康检查
# - 配置网络
```

`main.py`:

```python
from fastapi import FastAPI
from databases import Database

app = FastAPI()
database = Database("postgresql://user:pass@db:5432/appdb")

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.get("/")
async def read_root():
    # 查询数据库
    query = "SELECT NOW()"
    result = await database.fetch_one(query)
    return {"db_time": str(result["now"])}
```

### 检查清单

- [ ] 使用 `docker-compose up -d` 启动
- [ ] 应用成功连接数据库
- [ ] 数据持久化（重启容器后数据还在）
- [ ] 使用 `docker-compose down` 停止并删除

### 提示

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 进入容器
docker-compose exec app /bin/bash
docker-compose exec db psql -U user -d appdb

# 停止服务
docker-compose stop

# 停止并删除
docker-compose down

# 停止并删除数据卷
docker-compose down -v
```

---

## 练习 4: 添加 Redis 缓存

### 题目

在 Docker Compose 中添加 Redis 服务，并在 FastAPI 中使用缓存。

### 要求

1. 在 `docker-compose.yml` 中添加 Redis 服务
2. 在 FastAPI 中实现缓存功能
3. 对比有无缓存的性能差异

### 示例代码

`docker-compose.yml`:

```yaml
services:
  # ... 其他服务 ...

  # Redis 缓存
  redis:
    image: redis:7-alpine
    # 你的代码在这里
    # - 配置数据持久化
    # - 配置端口
```

`main.py`:

```python
from fastapi import FastAPI
import redis
import time

app = FastAPI()
r = redis.Redis(host='redis', port=6379, decode_responses=True)

@app.get("/slow")
async def slow_endpoint():
    """模拟慢接口（2秒）"""
    time.sleep(2)
    return {"message": "This took 2 seconds"}

@app.get("/cached")
async def cached_endpoint():
    """使用缓存的接口"""
    # 尝试从缓存获取
    cached = r.get("data")

    if cached:
        return {"message": f"From cache: {cached}"}

    # 缓存未命中，计算并缓存
    time.sleep(2)  # 模拟耗时操作
    result = "expensive computation result"
    r.setex("data", 60, result)  # 缓存 60 秒

    return {"message": f"Computed: {result}"}
```

### 测试

```bash
# 第一次访问（缓存未命中，慢）
time curl http://localhost:8000/cached

# 第二次访问（缓存命中，快）
time curl http://localhost:8000/cached
```

### 检查清单

- [ ] Redis 服务正常运行
- [ ] 缓存功能正常
- [ ] 缓存显著提升性能
- [ ] 缓存过期后重新计算

---

## 练习 5: 环境变量配置

### 题目

使用环境变量管理应用配置，而不是硬编码。

### 要求

1. 创建 `.env` 文件存储配置
2. 使用 `python-dotenv` 或 `pydantic-settings` 加载配置
3. 在 Docker Compose 中使用环境变量
4. 不要将敏感信息提交到代码库

### 示例代码

`.env`:

```env
# 应用配置
APP_NAME=FastAPI App
DEBUG=true

# 数据库配置
DATABASE_URL=postgresql://user:pass@db:5432/appdb

# Redis 配置
REDIS_URL=redis://redis:6379/0

# 密钥
SECRET_KEY=your-secret-key-here
```

`config.py`:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str
    debug: bool
    database_url: str
    redis_url: str
    secret_key: str

    model_config = ConfigDict(
        env_file=".env"
    )

settings = Settings()
```

`main.py`:

```python
from fastapi import FastAPI
from config import settings

app = FastAPI(title=settings.app_name, debug=settings.debug)

@app.get("/config")
def read_config():
    return {
        "app_name": settings.app_name,
        "debug": settings.debug,
    }
```

`.gitignore`:

```gitignore
# 环境变量文件
.env
.env.local
.env.*.local
```

### 检查清单

- [ ] `.env` 文件不在代码库中
- [ ] 应用从环境变量读取配置
- [ ] Docker Compose 使用环境变量
- [ ] 提供 `.env.example` 示例文件

---

## 练习 6: 综合项目

### 题目

创建一个完整的 FastAPI 应用，包含：

1. FastAPI 应用
2. PostgreSQL 数据库
3. Redis 缓存
4. 数据持久化
5. 环境变量配置
6. 健康检查
7. 日志记录

### 要求

1. 完整的 `docker-compose.yml`
2. 优化的 `Dockerfile`
3. 环境变量配置
4. 健康检查端点
5. 数据库迁移（Alembic）
6. Redis 缓存
7. 日志持久化

### 项目结构

```
fastapi-docker-project/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── models.py
│   └── api/
├── alembic/
├── logs/
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
└── requirements.txt
```

### 检查清单

- [ ] 使用 `docker-compose up -d` 一键启动
- [ ] 所有服务正常运行
- [ ] 数据持久化
- [ ] 健康检查正常
- [ ] 日志持久化
- [ ] 缓存功能正常
- [ ] 环境变量配置正确

---

## ✅ 完成标准

完成所有练习后，你应该能够：

- [ ] 编写基础的 Dockerfile
- [ ] 优化 Dockerfile（多阶段构建）
- [ ] 使用 Docker Compose 编排多容器应用
- [ ] 配置环境变量
- [ ] 实现健康检查
- [ ] 数据持久化
- [ ] 添加缓存服务
- [ ] 理解容器网络和卷

---

## 💡 学习建议

1. **循序渐进**
   - 先掌握单容器部署
   - 再学习多容器编排
   - 最后学习高级配置

2. **实践为主**
   - 每个练习都要实际运行
   - 观察容器日志
   - 理解每个配置的作用

3. **错误调试**
   - 学会查看容器日志
   - 使用 `docker inspect` 排查问题
   - 进入容器调试

4. **记录笔记**
   - 记录常用的 Docker 命令
   - 记录遇到的问题和解决方案
   - 总结最佳实践

---

**祝你练习愉快！记住：多动手，多实践，才能掌握容器化部署！** 🚀
