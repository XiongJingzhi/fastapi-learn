"""
APScheduler嵌入FastAPI示例

展示如何在FastAPI应用中嵌入调度器
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging

logger = logging.getLogger(__name__)

# 创建调度器
scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("Starting scheduler...")
    scheduler.start()
    yield
    # 关闭时
    logger.info("Shutting down scheduler...")
    scheduler.shutdown()

# 创建FastAPI应用
app = FastAPI(lifespan=lifespan)

# 定义任务
async def health_check_task():
    """健康检查任务"""
    logger.info("Running health check...")

# 添加定时任务
scheduler.add_job(
    health_check_task,
    'interval',
    minutes=5,
    id='health_check'
)

@app.get("/")
async def root():
    return {"message": "FastAPI with embedded APScheduler"}

@app.get("/scheduler/status")
async def scheduler_status():
    jobs = scheduler.get_jobs()
    return {
        "status": "running" if scheduler.running else "stopped",
        "jobs": [
            {"id": job.id, "name": job.name}
            for job in jobs
        ]
    }
