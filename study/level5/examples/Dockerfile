# ========================================
# FastAPI 应用 Docker 多阶段构建配置
# ========================================
# 说明：生产级 Dockerfile 示例
# 特性：
# 1. 多阶段构建（减小镜像大小）
# 2. 非 root 用户运行（安全最佳实践）
# 3. 依赖缓存优化（加快构建速度）
# 4. 健康检查
# 5. 优化镜像分层
# ========================================

# ----------------------------------------
# 阶段 1: 构建阶段（Builder）
# ----------------------------------------
# 用于编译和安装依赖
FROM python:3.11-slim as builder

# 设置工作目录
WORKDIR /build

# 设置环境变量（禁限 .pyc 文件和缓冲）
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装构建依赖
# 有些 Python 包需要编译，需要系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖到临时目录
# --user: 安装到用户目录（非系统目录）
# --prefix: 指定安装路径
RUN pip install --user --prefix=/install -r requirements.txt


# ----------------------------------------
# 阶段 2: 运行阶段（Runtime）
# ----------------------------------------
# 最小化的运行时镜像
FROM python:3.11-slim

# 设置标签（元数据）
LABEL maintainer="your-email@example.com" \
      app.name="fastapi-app" \
      app.version="1.0.0" \
      app.description="FastAPI Production Application"

# 创建非特权用户（安全最佳实践）
# 不使用 root 用户运行应用
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/install/bin:$PATH

# 从 builder 阶段复制已安装的依赖
COPY --from=builder /install /usr/local

# 复制应用代码
# 注意：这里的复制顺序很重要：
# 1. 先复制依赖（很少变化）
# 2. 再复制代码（经常变化）
# 这样可以利用 Docker 缓存层，加快构建速度
COPY . .

# 创建日志目录（用于持久化日志）
RUN mkdir -p /app/logs && chown -R appuser:appuser /app

# 切换到非特权用户
USER appuser

# 暴露端口（FastAPI 默认端口）
EXPOSE 8000

# 健康检查
# Docker 会定期检查容器是否健康
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# 启动命令
# 使用 uvicorn 启动 FastAPI 应用
# --host 0.0.0.0: 监听所有网络接口
# --port 8000: 监听端口
# --workers 4: 工作进程数（建议值：CPU 核心数 * 2 + 1）
# --access-log: 记录访问日志
# --log-level info: 日志级别
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--access-log", "--log-level", "info"]

# ========================================
# 使用说明
# ========================================
#
# 1. 构建镜像：
#    docker build -t fastapi-app:latest .
#
# 2. 运行容器：
#    docker run -d -p 8000:8000 \
#      -e DATABASE_URL=postgresql://user:pass@host:5432/dbname \
#      -e REDIS_URL=redis://host:6379/0 \
#      --name fastapi-app \
#      fastapi-app:latest
#
# 3. 查看健康状态：
#    docker ps
#    docker inspect --format='{{.State.Health.Status}}' fastapi-app
#
# 4. 查看日志：
#    docker logs -f fastapi-app
#
# 5. 进入容器调试：
#    docker exec -it fastapi-app /bin/bash
#
# ========================================
# 优化建议
# ========================================
#
# 1. 镜像大小优化：
#    - 使用 slim 版本的 Python 镜像（而非 alpine，避免兼容性问题）
#    - 清理不需要的文件（.git, __pycache__）
#    - 使用 .dockerignore 排除不必要的文件
#
# 2. 构建速度优化：
#    - 利用 Docker 缓存层（很少变化的文件先复制）
#    - 使用 BuildKit 并行构建
#    - 考虑使用依赖缓存镜像
#
# 3. 安全优化：
#    - 定期更新基础镜像
#    - 使用非 root 用户运行
#    - 扫描镜像漏洞（docker scan, trivy）
#    - 不要在镜像中硬编码敏感信息
#
# 4. 运行时优化：
#    - 根据服务器资源调整 workers 数量
#    - 配置资源限制（--cpus, --memory）
#    - 使用健康检查自动重启不健康的容器
#    - 配置日志轮转
#
# ========================================
