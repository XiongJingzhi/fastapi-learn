# 01. Docker 基础 - Docker Basics

## 📍 在架构中的位置

**从"环境不一致"到"构建一次，到处运行"**

```
┌─────────────────────────────────────────────────────────────┐
│          没有 Docker 的问题                                  │
└─────────────────────────────────────────────────────────────┘

开发环境：
    Python 3.11
    PostgreSQL 15
    Redis 7.0

    → 开发完成，运行正常 ✅

测试环境：
    Python 3.9（系统自带）
    PostgreSQL 13
    Redis 6.0

    → 版本不兼容，运行失败 ❌

生产环境：
    Python 3.10
    PostgreSQL 14
    Redis 6.2

    → 依赖冲突，运行失败 ❌

开发者说：
    "我本地能跑啊！" ❌
    "为什么服务器上不行？" ❌

═══════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────┐
│          使用 Docker                                         │
└─────────────────────────────────────────────────────────────┘

开发环境：
    容器（Python 3.11 + PostgreSQL 15 + Redis 7.0）

    → 构建镜像 ✅

测试环境：
    容器（Python 3.11 + PostgreSQL 15 + Redis 7.0）

    → 运行镜像 ✅（与开发环境完全一致）

生产环境：
    容器（Python 3.11 + PostgreSQL 15 + Redis 7.0）

    → 运行镜像 ✅（与开发环境完全一致）

开发者说：
    "构建一次，到处运行！" ✅
```

**🎯 你的学习目标**：掌握 Docker 基础，能够将 FastAPI 应用容器化。

---

## 🎯 什么是 Docker？

### 生活类比：集装箱运输

**传统运输（没有集装箱）**：

```
问题：
- 码头工人需要手动搬运各种货物
- 货物容易损坏
- 不同货物不能混装
- 运输效率低
```

**集装箱运输（有集装箱）**：

```
好处：
- 统一规格的集装箱
- 货物保护在箱内
- 可以堆叠、吊装
- 船、车、火车通用
- 运输效率高
```

**Docker = 软件行业的集装箱**：

```
容器（Container）：
├─ 应用代码
├─ 运行时（Python）
├─ 依赖包（requirements.txt）
└─ 系统工具

好处：
- 环境一致（开发、测试、生产）
- 依赖隔离（不同应用不冲突）
- 快速部署（启动秒级）
- 资源高效（比虚拟机轻量）
```

---

### Docker vs 虚拟机

**对比表格**：

| 特性 | 虚拟机 | Docker 容器 |
|------|--------|-------------|
| **启动时间** | 分钟级 | 秒级 |
| **磁盘占用** | GB 级别 | MB 级别 |
| **性能** | 接近原生 | 接近原生 |
| **隔离性** | 强（独立操作系统） | 较弱（共享内核） |
| **可移植性** | 差 | 好 |
| **资源利用** | 低（每个虚拟机独立 OS） | 高（共享内核） |

---

## 🔧 Docker 基础概念

### 三大核心概念

```
┌─────────────────────────────────────────────────────────────┐
│                  Docker 三大核心概念                         │
└─────────────────────────────────────────────────────────────┘

1. 镜像（Image）
   └─ 只读模板
   └─ 包含应用代码、运行时、依赖
   └─ 例：python:3.11-slim, fastapi-app:v1.0

2. 容器（Container）
   └─ 镜像的运行实例
   └─ 相互隔离的进程
   └─ 例：运行中的 fastapi-app 容器

3. 仓库（Registry）
   └─ 存储和分发镜像
   └─ 例：Docker Hub, AWS ECR, 阿里云镜像仓库
```

---

### 生活类比：餐厅

**镜像 = 菜谱**：

```
菜谱（镜像是只读的）：
├─ 食材清单（依赖）
├─ 制作步骤（启动命令）
└─ 装盘方式（环境配置）

特点：
- 可以复制（分享给其他人）
- 不会改变（只读）
```

**容器 = 做好的菜**：

```
菜（容器是运行的）：
├─ 按照菜谱制作
├─ 可以品尝（运行应用）
└─ 吃完后没有了（容器删除）

特点：
- 按需制作（从镜像启动）
- 可以修改（容器内修改不保留）
```

**仓库 = 食材超市**：

```
超市（仓库存储镜像）：
├─ 各种菜谱（镜像）
├─ 可以购买（拉取镜像）
└─ 可以上架（推送镜像）
```

---

## 📝 编写 Dockerfile

### Dockerfile 是什么？

**Dockerfile = 构建镜像的脚本**：

```dockerfile
# Dockerfile 是一个文本文件
# 包含构建 Docker 镜像的所有指令

# 例：
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

### FastAPI 应用的 Dockerfile

**基本版本**：

```dockerfile
# ═══════════════════════════════════════════════════════════
# 1. 基础镜像
# ═══════════════════════════════════════════════════════════

FROM python:3.11-slim

# ═══════════════════════════════════════════════════════════
# 2. 设置工作目录
# ═══════════════════════════════════════════════════════════

WORKDIR /app

# ═══════════════════════════════════════════════════════════
# 3. 安装依赖
# ═══════════════════════════════════════════════════════════

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ═══════════════════════════════════════════════════════════
# 4. 复制应用代码
# ═══════════════════════════════════════════════════════════

COPY . .

# ═══════════════════════════════════════════════════════════
# 5. 启动命令
# ═══════════════════════════════════════════════════════════

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

### 优化版 Dockerfile（多阶段构建）

**为什么需要多阶段构建？**

```
单阶段构建：
    → 镜像包含：源代码 + 依赖 + 构建工具
    → 镜像大小：1 GB+ ❌

多阶段构建：
    → 构建阶段：源代码 + 依赖 + 构建工具
    → 运行阶段：只需要依赖 + 应用
    → 镜像大小：200 MB ✅
```

**代码实现**：

```dockerfile
# ═══════════════════════════════════════════════════════════
# 阶段 1：构建阶段
# ═══════════════════════════════════════════════════════════

FROM python:3.11-slim AS builder

WORKDIR /app

# 安装构建依赖
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# ═══════════════════════════════════════════════════════════
# 阶段 2：运行阶段
# ═══════════════════════════════════════════════════════════

FROM python:3.11-slim

WORKDIR /app

# 从构建阶段复制依赖
COPY --from=builder /root/.local /root/.local

# 复制应用代码
COPY . .

# 设置 PATH
ENV PATH=/root/.local/bin:$PATH

# 启动应用
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

### FastAPI 完整 Dockerfile

```dockerfile
# ═══════════════════════════════════════════════════════════
# 基础镜像
# ═══════════════════════════════════════════════════════════

FROM python:3.11-slim

# ═══════════════════════════════════════════════════════════
# 元数据
# ═══════════════════════════════════════════════════════════

LABEL maintainer="your-email@example.com"
LABEL version="1.0.0"
LABEL description="FastAPI application"

# ═══════════════════════════════════════════════════════════
# 环境变量
# ═══════════════════════════════════════════════════════════

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# ═══════════════════════════════════════════════════════════
# 工作目录
# ═══════════════════════════════════════════════════════════

WORKDIR /app

# ═══════════════════════════════════════════════════════════
# 安装系统依赖（如果需要）
# ═══════════════════════════════════════════════════════════

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# ═══════════════════════════════════════════════════════════
# 安装 Python 依赖
# ═══════════════════════════════════════════════════════════

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ═══════════════════════════════════════════════════════════
# 复制应用代码
# ═══════════════════════════════════════════════════════════

COPY . .

# ═══════════════════════════════════════════════════════════
# 创建非 root 用户（安全最佳实践）
# ═══════════════════════════════════════════════════════════

RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# ═══════════════════════════════════════════════════════════
# 暴露端口
# ═══════════════════════════════════════════════════════════

EXPOSE 8000

# ═══════════════════════════════════════════════════════════
# 健康检查
# ═══════════════════════════════════════════════════════════

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# ═══════════════════════════════════════════════════════════
# 启动命令
# ═══════════════════════════════════════════════════════════

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 🔨 构建和运行

### 构建镜像

```bash
# 基本构建
docker build -t fastapi-app:v1.0 .

# 查看镜像
docker images

# 输出：
# REPOSITORY    TAG       IMAGE ID       CREATED          SIZE
# fastapi-app   v1.0      abc123def456   10 seconds ago   200MB
```

---

### 运行容器

```bash
# 基本运行
docker run -d -p 8000:8000 --name my-app fastapi-app:v1.0

# 参数说明：
# -d: 后台运行
# -p 8000:8000: 端口映射（主机端口:容器端口）
# --name my-app: 容器名称

# 查看运行中的容器
docker ps

# 查看容器日志
docker logs my-app

# 停止容器
docker stop my-app

# 删除容器
docker rm my-app
```

---

### 环境变量

```bash
# 传递环境变量
docker run -d \
    -p 8000:8000 \
    -e DATABASE_URL=postgresql://user:pass@localhost/db \
    -e REDIS_URL=redis://localhost:6379 \
    --name my-app \
    fastapi-app:v1.0

# 从文件读取环境变量
docker run -d \
    -p 8000:8000 \
    --env-file .env \
    --name my-app \
    fastapi-app:v1.0
```

---

## 🎨 最佳实践

### 1. .dockerignore

**创建 `.dockerignore` 文件**：

```dockerignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# 虚拟环境
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Git
.git/
.gitignore

# Docker
Dockerfile
.dockerignore

# 测试
.pytest_cache/
.coverage
htmlcov/

# 文档
docs/
*.md
```

**作用**：排除不必要的文件，加快构建速度，减小镜像大小。

---

### 2. 层缓存优化

**利用 Docker 层缓存**：

```dockerfile
# ✅ 好的做法：依赖不变，层缓存命中
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

# ❌ 坏的做法：每次代码改变都重新安装依赖
COPY . .
RUN pip install -r requirements.txt
```

**原理**：
- Docker 镜像由多层组成
- 如果层没变，使用缓存
- 依赖变化少，代码变化多
- 先复制依赖，后复制代码

---

### 3. 最小化镜像大小

**使用 alpine 镜像**：

```dockerfile
# ❌ 大镜像（700 MB）
FROM python:3.11

# ✅ 小镜像（150 MB）
FROM python:3.11-slim

# ✅✅ 最小镜像（50 MB，但可能有兼容性问题）
FROM python:3.11-alpine
```

---

### 4. 安全最佳实践

```dockerfile
# 1. 使用非 root 用户
RUN useradd -m appuser
USER appuser

# 2. 不在镜像中存储敏感信息
# ❌ 错误
ENV DATABASE_PASSWORD=secret123

# ✅ 正确（运行时传入）
docker run -e DATABASE_PASSWORD=secret123 ...

# 3. 及时更新基础镜像
FROM python:3.11-slim  # 定期更新
```

---

## 🎯 小实验：自己动手

### 实验 1：构建第一个镜像

```bash
# 1. 创建 FastAPI 应用
# main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello Docker!"}

# 2. 创建 Dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN pip install fastapi uvicorn
COPY main.py .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# 3. 构建镜像
docker build -t hello-docker .

# 4. 运行容器
docker run -p 8000:8000 hello-docker

# 5. 访问 http://localhost:8000
```

---

### 实验 2：优化镜像大小

```bash
# 1. 查看镜像大小
docker images

# 2. 使用 slim 基础镜像重新构建
docker build -t hello-docker:slim .

# 3. 对比大小
docker images | grep hello-docker
```

---

## 📚 检查理解

回答这些问题来测试你的理解：

1. **什么是 Docker 镜像和容器？**
   - 提示：镜像是模板，容器是实例

2. **Docker 和虚拟机的区别？**
   - 提示：启动时间、资源占用、隔离性

3. **什么是多阶段构建？**
   - 提示：分离构建和运行环境

4. **为什么要用 .dockerignore？**
   - 提示：排除不必要文件，加快构建

5. **如何优化 Docker 镜像大小？**
   - 提示：slim 基础镜像、层缓存、清理缓存

---

## 🚀 下一步

现在你已经掌握了 Docker 基础，接下来：

1. **学习 Docker Compose**：`notes/02_docker_compose.md`
2. **查看实际代码**：`examples/Dockerfile`

**记住**：Docker 让应用"构建一次，到处运行"，是现代应用部署的基础！**

---

**费曼技巧总结**：
- ✅ 集装箱运输类比
- ✅ 餐厅类比（镜像=菜谱，容器=菜）
- ✅ 完整的 Dockerfile 示例
- ✅ 多阶段构建
- ✅ 最佳实践（.dockerignore、层缓存、安全）
