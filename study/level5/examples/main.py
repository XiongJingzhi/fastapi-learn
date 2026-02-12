# ========================================
# FastAPI 应用主文件
# ========================================
# 说明：生产级 FastAPI 应用示例
# 包含：配置加载、数据库连接、Redis 缓存、健康检查
# ========================================

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from typing import Optional

# 尝试导入配置（如果存在）
try:
    from config.base import Settings
    settings = Settings()
except ImportError:
    from pydantic_settings import BaseSettings

    class Settings(BaseSettings):
        APP_NAME: str = "FastAPI Application"
        DEBUG: bool = False
        VERSION: str = "1.0.0"

    settings = Settings()

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper() if hasattr(settings, 'LOG_LEVEL') else 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ----------------------------------------
# 应用生命周期管理
# ----------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动和关闭时的操作"""
    # 启动时执行
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.VERSION}")
    logger.info(f"📝 Debug mode: {settings.DEBUG}")

    # 这里可以连接数据库、Redis 等
    # await database.connect()
    # await redis.connect()

    yield

    # 关闭时执行
    logger.info("🛑 Shutting down application...")
    # await database.disconnect()
    # await redis.close()


# ----------------------------------------
# 创建 FastAPI 应用
# ----------------------------------------
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Production-ready FastAPI Application",
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# ----------------------------------------
# CORS 配置
# ----------------------------------------
if hasattr(settings, 'CORS_ENABLED') and settings.CORS_ENABLED:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=getattr(settings, 'CORS_ALLOW_ORIGINS', ['*']),
        allow_credentials=getattr(settings, 'CORS_ALLOW_CREDENTIALS', True),
        allow_methods=getattr(settings, 'CORS_ALLOW_METHODS', ['*']),
        allow_headers=getattr(settings, 'CORS_ALLOW_HEADERS', ['*']),
    )


# ----------------------------------------
# 全局异常处理
# ----------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "message": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "An error occurred"
        }
    )


# ----------------------------------------
# 根路径
# ----------------------------------------
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.VERSION,
        "status": "running"
    }


# ----------------------------------------
# 健康检查端点（用于 Kubernetes 探针）
# ----------------------------------------
@app.get("/health")
async def health_check():
    """健康检查（Liveness 和 Readiness 探针）"""
    return {
        "status": "healthy",
        "version": settings.VERSION
    }


@app.get("/ready")
async def readiness_check():
    """就绪检查（Readiness 探针）"""
    # 这里可以检查数据库、Redis 等依赖服务
    # 示例：
    # try:
    #     await database.execute("SELECT 1")
    #     await redis.ping()
    #     return {"status": "ready"}
    # except Exception as e:
    #     raise HTTPException(status_code=503, detail="Service not ready")

    return {"status": "ready"}


# ----------------------------------------
# 配置信息端点（开发环境）
# ----------------------------------------
@app.get("/config")
async def get_config():
    """获取配置信息（仅开发环境）"""
    if not settings.DEBUG:
        return {"message": "Config endpoint is disabled in production"}

    return {
        "app_name": settings.APP_NAME,
        "version": settings.VERSION,
        "debug": settings.DEBUG,
        # 不要暴露敏感信息（密码、密钥等）
    }


# ----------------------------------------
# 示例 API 路由
# ----------------------------------------
@app.get("/api/v1/users")
async def list_users():
    """示例：获取用户列表"""
    # 这里从数据库查询用户
    return {
        "users": [
            {"id": 1, "name": "User 1"},
            {"id": 2, "name": "User 2"},
        ]
    }


@app.get("/api/v1/users/{user_id}")
async def get_user(user_id: int):
    """示例：获取单个用户"""
    # 这里从数据库查询用户
    return {
        "id": user_id,
        "name": f"User {user_id}",
        "email": f"user{user_id}@example.com"
    }


# ----------------------------------------
# 中间件：请求日志
# ----------------------------------------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录所有请求"""
    import time
    start_time = time.time()

    # 处理请求
    response = await call_next(request)

    # 计算处理时间
    process_time = time.time() - start_time

    # 记录日志
    logger.info(
        f"{request.method} {request.url.path} "
        f"- Status: {response.status_code} "
        f"- Time: {process_time:.3f}s"
    )

    # 添加响应头
    response.headers["X-Process-Time"] = str(process_time)

    return response


# ----------------------------------------
# 如果直接运行此文件
# ----------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=getattr(settings, 'HOST', '0.0.0.0'),
        port=getattr(settings, 'PORT', 8000),
        reload=settings.DEBUG,  # 开发环境自动重载
        workers=getattr(settings, 'WORKERS', 1),
        log_level=settings.LOG_LEVEL.lower() if hasattr(settings, 'LOG_LEVEL') else 'info'
    )

# ========================================
# 使用说明
# ========================================
#
# 1. 启动应用：
#    # 开发环境
#    uvicorn main:app --reload --host 0.0.0.0 --port 8000
#
#    # 生产环境
#    uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
#
# 2. 访问 API 文档：
#    http://localhost:8000/docs
#    http://localhost:8000/redoc
#
# 3. 健康检查：
#    curl http://localhost:8000/health
#
# 4. 使用 Docker：
#    docker build -t fastapi-app .
#    docker run -p 8000:8000 fastapi-app
#
# 5. 使用 Docker Compose：
#    docker-compose up -d
#
# ========================================
