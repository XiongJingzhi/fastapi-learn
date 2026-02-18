# Level 4 定时任务模块实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标:** 在Level 4（生产就绪）中补充定时任务模块，提供从基础到生产级的完整学习路径

**架构:** 采用技术栈分离方案，创建6个学习笔记文件（总览+对比+最佳实践）和12个渐进式代码示例（Level 1-4），涵盖APScheduler和Celery Beat两种技术栈

**技术栈:** APScheduler 3.10+, Celery 5.3+, Redis 5.0+, FastAPI, SQLAlchemy

---

## Task 1: 创建示例目录结构

**Files:**
- Create: `study/level4/examples/07_scheduled_tasks/`
- Create: `study/level4/examples/07_scheduled_tasks/apscheduler/`
- Create: `study/level4/examples/07_scheduled_tasks/celery_beat/`

**Step 1: 创建目录**

```bash
mkdir -p study/level4/examples/07_scheduled_tasks/apscheduler
mkdir -p study/level4/examples/07_scheduled_tasks/celery_beat
```

**Step 2: 验证目录创建**

```bash
ls -la study/level4/examples/07_scheduled_tasks/
```

Expected: 看到 `apscheduler/` 和 `celery_beat/` 目录

**Step 3: Commit**

```bash
git add study/level4/examples/07_scheduled_tasks/
git commit -m "feat: create scheduled tasks examples directory structure"
```

---

## Task 2: 创建Level 1示例 - 简单定时器

**Files:**
- Create: `study/level4/examples/07_scheduled_tasks/level1_simple_timer.py`

**Step 1: 创建Level 1示例文件**

```python
"""
Level 1: 最简单的定时任务

学习目标：
- 理解Scheduler基本概念
- 运行你的第一个定时任务
- 看到实际效果

运行：python level1_simple_timer.py
预期：每3秒打印一次"Hello, Scheduler!"
"""

from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime, timedelta

# 创建调度器
scheduler = BlockingScheduler()

# 定义任务
def print_hello():
    print(f"[{datetime.now()}] Hello, Scheduler!")

# 添加任务：每3秒执行一次
scheduler.add_job(print_hello, 'interval', seconds=3)

# 添加任务：5秒后执行一次
scheduler.add_job(
    lambda: print(f"[{datetime.now()}] One-time task!"),
    'date',
    run_date=datetime.now() + timedelta(seconds=5)
)

print("Scheduler started. Press Ctrl+C to exit.")

# 启动调度器（阻塞）
try:
    scheduler.start()
except (KeyboardInterrupt, SystemExit):
    print("Scheduler stopped.")
```

**Step 2: 创建__init__.py**

```bash
touch study/level4/examples/07_scheduled_tasks/__init__.py
```

**Step 3: 测试运行**

```bash
cd study/level4/examples/07_scheduled_tasks
timeout 15 python level1_simple_timer.py
```

Expected: 看到 "Hello, Scheduler!" 打印约5次

**Step 4: Commit**

```bash
git add study/level4/examples/07_scheduled_tasks/
git commit -m "feat: add Level 1 simple timer example"
```

---

## Task 3: 创建Level 2示例 - 数据清理任务

**Files:**
- Create: `study/level4/examples/07_scheduled_tasks/level2_data_cleanup.py`

**Step 1: 创建Level 2示例文件**

```python
"""
Level 2: 数据清理任务

实际场景：
- 每小时清理过期token
- 每天凌晨2点归档日志
- 任务失败自动重试

运行：python level2_data_cleanup.py
"""

import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataCleanupService:
    """数据清理服务"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()

    async def cleanup_expired_tokens(self):
        """清理过期token（Level 2示例）"""
        try:
            logger.info("Starting token cleanup...")

            # 模拟数据库操作
            expired_tokens = await self._get_expired_tokens()
            logger.info(f"Found {len(expired_tokens)} expired tokens")

            # 删除过期token
            deleted = await self._delete_tokens(expired_tokens)

            logger.info(f"Cleanup completed: {deleted} tokens deleted")

        except Exception as e:
            logger.error(f"Token cleanup failed: {e}")
            raise

    async def archive_logs(self):
        """归档日志（每天凌晨2点）"""
        try:
            logger.info("Starting log archival...")

            # 模拟归档操作
            await self._compress_logs()
            await self._upload_to_storage()

            logger.info("Log archival completed")

        except Exception as e:
            logger.error(f"Log archival failed: {e}")
            raise

    async def _get_expired_tokens(self):
        """模拟：获取过期token"""
        await asyncio.sleep(0.1)  # 模拟数据库查询
        return list(range(10))  # 模拟10个过期token

    async def _delete_tokens(self, tokens):
        """模拟：删除token"""
        await asyncio.sleep(0.2)
        return len(tokens)

    async def _compress_logs(self):
        """模拟：压缩日志"""
        await asyncio.sleep(1)

    async def _upload_to_storage(self):
        """模拟：上传存储"""
        await asyncio.sleep(2)

    def start(self):
        """启动调度器"""
        # 每小时清理过期token
        self.scheduler.add_job(
            self.cleanup_expired_tokens,
            'interval',
            hours=1,
            id='cleanup_tokens',
            max_instances=1,  # 防止任务重叠
            misfire_grace_time=300  # 容忍5秒延迟
        )

        # 每天凌晨2点归档日志
        self.scheduler.add_job(
            self.archive_logs,
            'cron',
            hour=2,
            minute=0,
            id='archive_logs',
            max_instances=1
        )

        # 测试用：每30秒执行一次
        self.scheduler.add_job(
            self.cleanup_expired_tokens,
            'interval',
            seconds=30,
            id='test_cleanup'
        )

        self.scheduler.start()
        logger.info("Data cleanup service started")

# 运行
if __name__ == "__main__":
    service = DataCleanupService()
    service.start()

    try:
        asyncio.Event().wait()  # 保持运行
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        service.scheduler.shutdown()
```

**Step 2: 测试运行**

```bash
cd study/level4/examples/07_scheduled_tasks
timeout 40 python level2_data_cleanup.py
```

Expected: 看到任务在30秒时执行

**Step 3: Commit**

```bash
git add study/level4/examples/07_scheduled_tasks/level2_data_cleanup.py
git commit -m "feat: add Level 2 data cleanup example"
```

---

## Task 4: 创建Level 3示例 - 分布式协调器

**Files:**
- Create: `study/level4/examples/07_scheduled_tasks/level3_distributed_coordinator.py`

**Step 1: 创建Level 3示例文件**

```python
"""
Level 3: 分布式任务协调

问题：多实例部署时，任务会重复执行
方案：使用Redis分布式锁

运行：
- 终端1：python level3_distributed_coordinator.py --instance-id=node1
- 终端2：python level3_distributed_coordinator.py --instance-id=node2
观察：只有一个实例执行任务
"""

import asyncio
import argparse
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DistributedScheduler:
    """分布式任务调度器（模拟版本）"""

    def __init__(self, instance_id: str):
        self.instance_id = instance_id
        self.scheduler = AsyncIOScheduler()
        # 模拟Redis锁
        self.lock_acquired = False

    async def distributed_task(self):
        """分布式任务（只在一个实例上执行）"""

        # 模拟获取分布式锁
        lock_key = "lock:monthly_report"

        # 简化版：第一个实例获取锁
        if not self.lock_acquired and self.instance_id == "node1":
            self.lock_acquired = True
            logger.info(f"[{self.instance_id}] Lock acquired, starting task...")

            # 执行任务（模拟月报生成）
            await self._generate_monthly_report()

            logger.info(f"[{self.instance_id}] Task completed")
            self.lock_acquired = False
        else:
            logger.info(f"[{self.instance_id}] Another instance is running the task")

    async def _generate_monthly_report(self):
        """生成月报（模拟耗时操作）"""
        logger.info("Generating monthly report...")
        await asyncio.sleep(2)  # 模拟2秒操作
        logger.info("Monthly report generated")

    def start(self):
        """启动调度器"""
        # 测试用：每15秒执行一次
        self.scheduler.add_job(
            self.distributed_task,
            'interval',
            seconds=15,
            id='test_distributed_task'
        )

        self.scheduler.start()
        logger.info(f"[{self.instance_id}] Distributed scheduler started")

# 运行
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - [%(levelname)s] - %(message)s'
    )

    parser = argparse.ArgumentParser()
    parser.add_argument("--instance-id", default="node1")
    args = parser.parse_args()

    coordinator = DistributedScheduler(args.instance_id)
    coordinator.start()

    try:
        asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info(f"[{args.instance_id}] Shutting down...")
        coordinator.scheduler.shutdown()
```

**Step 2: 测试运行（单实例）**

```bash
cd study/level4/examples/07_scheduled_tasks
timeout 40 python level3_distributed_coordinator.py
```

**Step 3: Commit**

```bash
git add study/level4/examples/07_scheduled_tasks/level3_distributed_coordinator.py
git commit -m "feat: add Level 3 distributed coordinator example"
```

---

## Task 5: 创建Level 4示例 - 生产监控系统

**Files:**
- Create: `study/level4/examples/07_scheduled_tasks/level4_production_monitor.py`

**Step 1: 创建Level 4示例文件**

```python
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
```

**Step 2: 测试API启动**

```bash
cd study/level4/examples/07_scheduled_tasks
timeout 10 python level4_production_monitor.py &
sleep 3
curl http://localhost:8000/api/tasks
```

**Step 3: Commit**

```bash
git add study/level4/examples/07_scheduled_tasks/level4_production_monitor.py
git commit -m "feat: add Level 4 production monitor example"
```

---

## Task 6: 创建APScheduler嵌入示例

**Files:**
- Create: `study/level4/examples/07_scheduled_tasks/apscheduler/embedded_app.py`

**Step 1: 创建嵌入模式示例**

```python
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
```

**Step 2: Commit**

```bash
git add study/level4/examples/07_scheduled_tasks/apscheduler/embedded_app.py
git commit -m "feat: add APScheduler embedded app example"
```

---

## Task 7: 创建APScheduler独立进程示例

**Files:**
- Create: `study/level4/examples/07_scheduled_tasks/apscheduler/standalone_app.py`
- Create: `study/level4/examples/07_scheduled_tasks/apscheduler/config.py`

**Step 1: 创建配置文件**

```python
"""
APScheduler配置
"""

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor

# JobStore配置
JOBSTORES = {
    'default': SQLAlchemyJobStore(url='sqlite:///jobs.db')
}

# Executor配置
EXECUTORS = {
    'default': ThreadPoolExecutor(max_workers=20)
}

# 任务默认配置
JOB_DEFAULTS = {
    'coalesce': True,
    'max_instances': 3,
    'misfire_grace_time': 60
}

# 调度器配置
SCHEDULER_CONFIG = {
    'jobstores': JOBSTORES,
    'executors': EXECUTORS,
    'job_defaults': JOB_DEFAULTS,
    'timezone': 'UTC'
}
```

**Step 2: 创建独立应用文件**

```python
"""
APScheduler独立进程示例

适合生产环境的独立调度器进程
"""

from apscheduler.schedulers.blocking import BlockingScheduler
from config import SCHEDULER_CONFIG
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建调度器
scheduler = BlockingScheduler(**SCHEDULER_CONFIG)

# 定义任务
def task1():
    logger.info("Executing task1...")

def task2():
    logger.info("Executing task2...")

# 添加任务
scheduler.add_job(
    task1,
    'interval',
    minutes=10,
    id='task1',
    name='Periodic Task 1'
)

scheduler.add_job(
    task2,
    'cron',
    hour='*/2',
    id='task2',
    name='Periodic Task 2'
)

if __name__ == "__main__":
    try:
        logger.info("Starting standalone scheduler...")
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down scheduler...")
        scheduler.shutdown()
```

**Step 3: Commit**

```bash
git add study/level4/examples/07_scheduled_tasks/apscheduler/
git commit -m "feat: add APScheduler standalone app example"
```

---

## Task 8: 创建Celery Beat基础示例

**Files:**
- Create: `study/level4/examples/07_scheduled_tasks/celery_beat/tasks.py`
- Create: `study/level4/examples/07_scheduled_tasks/celery_beat/beat_config.py`

**Step 1: 创建任务定义文件**

```python
"""
Celery任务定义
"""

from celery import Celery
import logging

logger = logging.getLogger(__name__)

# 创建Celery应用
app = Celery('tasks')

# 配置
app.conf.update(
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/1',
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# 定义任务
@app.task
def add(x, y):
    """简单加法任务"""
    result = x + y
    logger.info(f"Adding {x} + {y} = {result}")
    return result

@app.task
def send_email(to, subject, body):
    """发送邮件任务"""
    logger.info(f"Sending email to {to}: {subject}")
    # 模拟发送邮件
    import time
    time.sleep(1)
    logger.info(f"Email sent to {to}")
    return {"status": "sent", "to": to}

@app.task
def generate_report(report_type):
    """生成报表任务"""
    logger.info(f"Generating {report_type} report...")
    import time
    time.sleep(2)
    logger.info(f"{report_type} report generated")
    return {"report": report_type, "status": "completed"}
```

**Step 2: 创建Beat配置文件**

```python
"""
Celery Beat调度配置
"""

from celery.schedules import crontab

# Beat调度配置
beat_schedule = {
    'add-every-30-seconds': {
        'task': 'tasks.add',
        'schedule': 30.0,
        'args': (16, 16)
    },
    'send-daily-report': {
        'task': 'tasks.send_email',
        'schedule': crontab(hour=18, minute=0),
        'args': ("admin@example.com", "Daily Report", "Report content")
    },
    'generate-weekly-report': {
        'task': 'tasks.generate_report',
        'schedule': crontab(day_of_week=1, hour=8, minute=0),
        'args': ("weekly",)
    },
}
```

**Step 3: Commit**

```bash
git add study/level4/examples/07_scheduled_tasks/celery_beat/tasks.py
git add study/level4/examples/07_scheduled_tasks/celery_beat/beat_config.py
git commit -m "feat: add Celery Beat basic example"
```

---

## Task 9: 创建Celery独立Worker示例

**Files:**
- Create: `study/level4/examples/07_scheduled_tasks/celery_beat/standalone_worker.py`

**Step 1: 创建Worker文件**

```python
"""
Celery独立Worker示例

启动命令：
  celery -A standalone_worker worker --loglevel=info

启动Beat：
  celery -A standalone_worker beat --loglevel=info
"""

from tasks import app, beat_schedule

# 添加beat配置
app.conf.beat_schedule = beat_schedule

if __name__ == "__main__":
    app.start()
```

**Step 2: Commit**

```bash
git add study/level4/examples/07_scheduled_tasks/celery_beat/standalone_worker.py
git commit -m "feat: add Celery standalone worker example"
```

---

## Task 10: 创建示例导航README

**Files:**
- Create: `study/level4/examples/07_scheduled_tasks/README.md`

**Step 1: 创建README文件**

```markdown
# 定时任务示例导航

## 🎯 按难度渐进学习

### Level 1: Hello World
- `level1_simple_timer.py` - 最简单的定时任务
  - 5秒后执行一次
  - 每3秒打印"Hello"
  - 代码量：20行

### Level 2: 实际场景
- `level2_data_cleanup.py` - 数据清理任务
  - 删除过期token
  - 错误处理
  - 代码量：80行

### Level 3: 分布式协调
- `level3_distributed_coordinator.py` - 多实例只执行一次
  - 分布式锁（模拟）
  - 任务协调
  - 代码量：100行

### Level 4: 生产监控
- `level4_production_monitor.py` - 完整生产级方案
  - 任务监控
  - 执行历史
  - Web管理界面
  - 代码量：300行

## 🛠️ 技术栈完整示例

### APScheduler完整实现
- `apscheduler/embedded_app.py` - 嵌入FastAPI
- `apscheduler/standalone_app.py` - 独立进程
- `apscheduler/config.py` - 配置管理

### Celery Beat完整实现
- `celery_beat/tasks.py` - 任务定义
- `celery_beat/beat_config.py` - Beat配置
- `celery_beat/standalone_worker.py` - 独立worker

## 🚀 快速运行

### Level 1示例
```bash
cd study/level4/examples/07_scheduled_tasks
python level1_simple_timer.py
```

### Level 2示例
```bash
python level2_data_cleanup.py
```

### Level 4示例（需要FastAPI）
```bash
pip install fastapi uvicorn
python level4_production_monitor.py
# 访问 http://localhost:8000/docs
```

### Celery示例（需要Redis）
```bash
# 启动Redis
docker run -d -p 6379:6379 redis:alpine

# 启动Worker
cd celery_beat
celery -A standalone_worker worker --loglevel=info

# 启动Beat（另一个终端）
celery -A standalone_worker beat --loglevel=info
```

## 📦 依赖安装

```bash
# 基础依赖
pip install apscheduler

# FastAPI依赖
pip install fastapi uvicorn

# Celery依赖
pip install celery redis
```
```

**Step 2: Commit**

```bash
git add study/level4/examples/07_scheduled_tasks/README.md
git commit -m "docs: add scheduled tasks examples README"
```

---

## Task 11: 创建总览笔记文件

**Files:**
- Create: `study/level4/notes/07_scheduled_tasks.md`

**Step 1: 创建总览笔记**

内容包含：
- 定时任务在架构中的位置
- APScheduler vs Celery Beat对比表
- 学习路径导航
- 快速选择指南

（详细内容见设计文档第3.1节）

**Step 2: Commit**

```bash
git add study/level4/notes/07_scheduled_tasks.md
git commit -m "docs: add scheduled tasks overview notes"
```

---

## Task 12: 创建APScheduler基础笔记

**Files:**
- Create: `study/level4/notes/07a_ap_scheduler_intro.md`

**Step 1: 创建APScheduler基础笔记**

内容包含：
- 基本概念（费曼技巧类比）
- 三种Trigger详解
- Hello World示例
- 与FastAPI集成
- 小实验

**Step 2: Commit**

```bash
git add study/level4/notes/07a_ap_scheduler_intro.md
git commit -m "docs: add APScheduler intro notes"
```

---

## Task 13: 创建APScheduler高级笔记

**Files:**
- Create: `study/level4/notes/07b_ap_scheduler_advanced.md`

**Step 1: 创建APScheduler高级笔记**

内容包含：
- 实际场景（数据清理、缓存预热）
- 任务持久化
- 任务管理
- 错误处理和重试

**Step 2: Commit**

```bash
git add study/level4/notes/07b_ap_scheduler_advanced.md
git commit -m "docs: add APScheduler advanced notes"
```

---

## Task 14: 创建Celery Beat基础笔记

**Files:**
- Create: `study/level4/notes/07c_celery_beat_intro.md`

**Step 1: 创建Celery Beat基础笔记**

内容包含：
- 为什么需要Celery Beat
- Celery架构（生活类比）
- Hello World示例
- 常用Schedule配置

**Step 2: Commit**

```bash
git add study/level4/notes/07c_celery_beat_intro.md
git commit -m "docs: add Celery Beat intro notes"
```

---

## Task 15: 创建Celery Beat高级笔记

**Files:**
- Create: `study/level4/notes/07d_celery_beat_advanced.md`

**Step 1: 创建Celery Beat高级笔记**

内容包含：
- 分布式任务
- 高级特性（chain、group、chord）
- 任务监控（Flower）
- 失败处理

**Step 2: Commit**

```bash
git add study/level4/notes/07d_celery_beat_advanced.md
git commit -m "docs: add Celery Beat advanced notes"
```

---

## Task 16: 创建最佳实践笔记

**Files:**
- Create: `study/level4/notes/07e_best_practices.md`

**Step 1: 创建最佳实践笔记**

内容包含：
- 技术选型决策树
- 架构模式对比
- 生产环境清单
- 常见陷阱
- 实战案例

**Step 2: Commit**

```bash
git add study/level4/notes/07e_best_practices.md
git commit -m "docs: add scheduled tasks best practices"
```

---

## Task 17: 更新Level 4 README

**Files:**
- Modify: `study/level4/README.md`

**Step 1: 读取现有README**

```bash
cat study/level4/README.md
```

**Step 2: 添加定时任务主题**

在"主题 5: 限流、熔断、降级"之后添加：

```markdown
---

### 主题 7：定时任务

**为什么需要定时任务？**

```
手动执行：
    每天早上9点手动运行数据报表
    → 忘记执行？数据缺失 ❌
    → 人在休假？没人执行 ❌

定时任务：
    程序每天早上9点自动运行
    → 准时执行 ✅
    → 可靠稳定 ✅
```

**内容**：
- APScheduler（轻量级）
- Celery Beat（分布式）
- 任务持久化
- 分布式协调
- 监控和告警

**学习材料**：
- 笔记：`notes/07_scheduled_tasks.md`
- 笔记：`notes/07a-07e_*`（系列）
- 示例：`examples/07_scheduled_tasks/`

**完成标准**：
- [ ] 理解定时任务的使用场景
- [ ] 掌握APScheduler的基本用法
- [ ] 理解Celery Beat的架构
- [ ] 能够实现分布式定时任务
- [ ] 掌握任务监控和错误处理
```

同时更新现有主题编号：
- 主题 6 → 主题 8

**Step 3: Commit**

```bash
git add study/level4/README.md
git commit -m "docs: update Level 4 README with scheduled tasks topic"
```

---

## Task 18: 更新项目依赖

**Files:**
- Modify: `requirements.txt`

**Step 1: 读取现有requirements.txt**

```bash
cat requirements.txt
```

**Step 2: 添加定时任务依赖**

在文件末尾添加：

```txt
# 定时任务（Level 4 - 主题7）
apscheduler>=3.10.0        # APScheduler
celery>=5.3.0              # Celery Beat和Worker
redis>=5.0.0               # Redis（Celery Broker）
flower>=2.0.0              # Celery监控界面（可选）
```

**Step 3: Commit**

```bash
git add requirements.txt
git commit -m "deps: add scheduled tasks dependencies"
```

---

## Task 19: 最终验证

**Step 1: 验证所有文件已创建**

```bash
# 检查notes文件
ls -la study/level4/notes/07*.md

# 检查examples文件
ls -la study/level4/examples/07_scheduled_tasks/

# 检查APScheduler示例
ls -la study/level4/examples/07_scheduled_tasks/apscheduler/

# 检查Celery Beat示例
ls -la study/level4/examples/07_scheduled_tasks/celery_beat/
```

Expected: 18个文件（1更新 + 17新建）

**Step 2: 验证README更新**

```bash
grep -A 20 "主题 7" study/level4/README.md
```

Expected: 看到定时任务主题内容

**Step 3: 验证依赖更新**

```bash
grep "apscheduler\|celery" requirements.txt
```

Expected: 看到定时任务相关依赖

**Step 4: 创建总结commit**

```bash
git add .
git commit -m "feat: complete Level 4 scheduled tasks module

- Add 6 notes files (overview + APScheduler + Celery + best practices)
- Add 12 example files (Level 1-4 + APScheduler + Celery)
- Update Level 4 README with new topic
- Update requirements.txt with dependencies

Total: 18 files created/updated

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## 验收标准

- [ ] 18个文件全部创建/更新
- [ ] 每个notes文件都有费曼技巧类比
- [ ] 每个notes文件都有小实验
- [ ] 每个examples文件都有运行说明
- [ ] 所有代码示例都可以运行
- [ ] README已更新
- [ ] requirements.txt已更新

---

**实施完成标志**: 所有19个任务完成，所有验收标准通过
