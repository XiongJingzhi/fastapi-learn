"""
Level 4: 生产级定时任务监控

功能：
- 任务执行历史记录
- 任务状态监控
- Web管理界面
- 失败告警

运行：python level4_production_monitor.py
访问：http://localhost:8000/docs
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import AsyncIOExecutor
from datetime import datetime
import uvicorn
from typing import List, Optional
import logging
import asyncio

# 日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 数据模型
class TaskExecution(BaseModel):
    """任务执行记录"""
    task_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration: Optional[float] = None
    error: Optional[str] = None

class TaskStatus(BaseModel):
    """任务状态"""
    task_id: str
    next_run_time: Optional[datetime]
    trigger: str
    executions: List[TaskExecution]

# 生产级调度器
class ProductionScheduler:
    """生产级定时任务调度器"""

    def __init__(self, db_url: str = "sqlite:///tasks.db"):
        jobstores = {
            'default': SQLAlchemyJobStore(url=db_url)
        }
        executors = {
            'default': AsyncIOExecutor(max_workers=10)
        }

        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults={
                'coalesce': True,
                'max_instances': 1,
                'misfire_grace_time': 300
            }
        )

        self.execution_history: dict = {}

    async def execute_with_monitoring(
        self,
        task_id: str,
        func,
        *args,
        **kwargs
    ):
        """执行任务并记录监控数据"""
        execution = TaskExecution(
            task_id=task_id,
            status="running",
            started_at=datetime.now()
        )

        if task_id not in self.execution_history:
            self.execution_history[task_id] = []

        self.execution_history[task_id].append(execution)

        try:
            result = await func(*args, **kwargs)

            execution.status = "success"
            execution.completed_at = datetime.now()
            execution.duration = (
                execution.completed_at - execution.started_at
            ).total_seconds()

            logger.info(
                f"Task {task_id} completed in {execution.duration:.2f}s"
            )

            return result

        except Exception as e:
            execution.status = "failed"
            execution.completed_at = datetime.now()
            execution.duration = (
                execution.completed_at - execution.started_at
            ).total_seconds()
            execution.error = str(e)

            logger.error(f"Task {task_id} failed: {e}")
            raise

    def get_task_status(self, task_id: str) -> TaskStatus:
        """获取任务状态"""
        job = self.scheduler.get_job(task_id)

        if not job:
            raise HTTPException(status_code=404, detail="Task not found")

        return TaskStatus(
            task_id=task_id,
            next_run_time=job.next_run_time,
            trigger=str(job.trigger),
            executions=self.execution_history.get(task_id, [])
        )

    def list_tasks(self) -> List[dict]:
        """列出所有任务"""
        jobs = self.scheduler.get_jobs()
        return [
            {
                "id": job.id,
                "name": job.name,
                "next_run_time": str(job.next_run_time),
                "trigger": str(job.trigger)
            }
            for job in jobs
        ]

    def start(self):
        """启动调度器"""
        self.scheduler.start()
        logger.info("Production scheduler started")

# FastAPI应用
app = FastAPI(title="定时任务监控系统")
scheduler = ProductionScheduler()

# 示例任务
async def data_report_task():
    """数据报表任务"""
    logger.info("Generating data report...")
    await asyncio.sleep(1)
    logger.info("Data report generated")

async def cache_warmup_task():
    """缓存预热任务"""
    logger.info("Warming up cache...")
    await asyncio.sleep(0.5)
    logger.info("Cache warmed up")

# Endpoints
@app.get("/")
async def root():
    return {
        "message": "定时任务监控系统",
        "docs": "/docs",
        "tasks": len(scheduler.list_tasks())
    }

@app.get("/api/tasks")
async def list_tasks():
    return scheduler.list_tasks()

@app.get("/api/tasks/{task_id}")
async def get_task_status(task_id: str):
    return scheduler.get_task_status(task_id)

@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str):
    scheduler.scheduler.remove_job(task_id)
    return {"message": f"Task {task_id} deleted"}

# 应用生命周期
@app.on_event("startup")
async def startup_event():
    scheduler.scheduler.add_job(
        lambda: scheduler.execute_with_monitoring(
            "data_report",
            data_report_task
        ),
        'interval',
        seconds=30,
        id='data_report',
        name='数据报表'
    )

    scheduler.scheduler.add_job(
        lambda: scheduler.execute_with_monitoring(
            "cache_warmup",
            cache_warmup_task
        ),
        'interval',
        seconds=45,
        id='cache_warmup',
        name='缓存预热'
    )

    scheduler.start()

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.scheduler.shutdown()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
