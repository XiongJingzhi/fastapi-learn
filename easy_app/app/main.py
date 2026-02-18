from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.config import settings
from app.database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时创建数据库表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # 关闭时清理资源
    await engine.dispose()


# 创建 FastAPI 应用实例
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="一个用于学习 FastAPI 和 Python Web 开发的应用",
    openapi_url=f"{settings.api_v1_str}/openapi.json",
    docs_url=f"{settings.api_v1_str}/docs",
    redoc_url=f"{settings.api_v1_str}/redoc",
    lifespan=lifespan
)

# 配置 CORS
if settings.backend_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.backend_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# 包含 API 路由
app.include_router(api_router, prefix=settings.api_v1_str)


# 根路径
@app.get("/")
async def root():
    """根路径欢迎信息"""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.version,
        "docs": f"{settings.api_v1_str}/docs"
    }


# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )