# 07b. APScheduler 高级特性

## 🎯 学习目标

掌握APScheduler的生产级用法，包括任务持久化、错误处理、任务管理。

---

## 📂 实际场景

### 场景 1：数据清理

**问题**：数据库中有很多过期token，需要定期清理

**解决方案**：定时清理任务

```python
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

async def cleanup_expired_tokens():
    """清理过期token"""
    # 1. 查询过期token
    expired_tokens = await get_expired_tokens()
    print(f"Found {len(expired_tokens)} expired tokens")

    # 2. 删除
    for token in expired_tokens:
        await delete_token(token)

    print(f"Deleted {len(expired_tokens)} tokens")

# 每小时执行
scheduler.add_job(
    cleanup_expired_tokens,
    'interval',
    hours=1,
    id='cleanup_tokens'
)
```

**费曼技巧**：
- 就像每天定时清理垃圾
- 不清理会占用空间（过期token占用数据库空间）

---

### 场景 2：缓存预热

**问题**：缓存过期后，第一个用户访问会很慢

**解决方案**：提前加载热点数据

```python
async def cache_warmup():
    """缓存预热"""
    # 加载热点数据到缓存
    hot_data = await get_hot_data()
    for data in hot_data:
        await cache.set(f"data:{data.id}", data)

    print("Cache warmed up")

# 每小时预热
scheduler.add_job(
    cache_warmup,
    'interval',
    hours=1,
    id='cache_warmup'
)
```

**费曼技巧**：
- 就像提前预热烤箱
- 预热后使用更快（缓存命中更快）

---

## 💾 任务持久化

### 为什么需要持久化？

**问题**：程序重启后，任务丢失

```
没有持久化：
    添加任务 → 程序重启 → 任务丢失 ❌

有持久化：
    添加任务 → 保存到数据库 → 程序重启 → 从数据库恢复 ✅
```

---

### 使用SQLAlchemyJobStore

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

# 配置JobStore
jobstores = {
    'default': SQLAlchemyJobStore(url='sqlite:///jobs.db')
}

# 创建调度器
scheduler = AsyncIOScheduler(jobstores=jobstores)

# 添加任务
scheduler.add_job(my_task, 'interval', minutes=5)

# 启动
scheduler.start()

# 任务会保存到jobs.db文件
```

**费曼技巧**：
- JobStore = 任务记事本
- 记下来就不怕忘记

---

## 🔧 任务管理

### 查询任务

```python
# 获取所有任务
jobs = scheduler.get_jobs()
for job in jobs:
    print(f"Job ID: {job.id}, Next run: {job.next_run_time}")

# 获取特定任务
job = scheduler.get_job('my_job_id')
print(f"Job: {job.name}")
```

---

### 暂停/恢复任务

```python
# 暂停任务
scheduler.pause_job('my_job_id')

# 恢复任务
scheduler.resume_job('my_job_id')

# 修改任务
scheduler.modify_job('my_job_id', minutes=10)
```

---

### 删除任务

```python
# 删除特定任务
scheduler.remove_job('my_job_id')

# 删除所有任务
scheduler.remove_all_jobs()
```

---

## ⚠️ 错误处理

### 任务失败处理

```python
import logging

logger = logging.getLogger(__name__)

async def risky_task():
    """可能失败的任务"""
    try:
        # 可能失败的操作
        await do_something_risky()
        logger.info("Task succeeded")
    except Exception as e:
        logger.error(f"Task failed: {e}")
        # 决定是否重新抛出异常
        raise

scheduler.add_job(
    risky_task,
    'interval',
    minutes=5,
    max_instances=1,  # 防止任务重叠
    misfire_grace_time=60  # 容忍1秒延迟
)
```

---

### 任务重叠问题

**问题**：上次任务还没执行完，下次就开始了

**解决方案**：设置`max_instances=1`

```python
scheduler.add_job(
    slow_task,
    'interval',
    minutes=5,
    max_instances=1  # 同时只允许1个实例
)
```

**费曼技巧**：
- 就像电梯（同时只能在一个楼层）
- 防止重复执行导致问题

---

### 任务错过执行

**问题**：系统暂停，任务错过了执行时间

**解决方案**：使用`coalesce`和`misfire_grace_time`

```python
scheduler.add_job(
    my_task,
    'interval',
    minutes=5,
    coalesce=True,  # 错过的任务合并执行
    misfire_grace_time=60  # 容忍60秒延迟
)
```

---

## 🎯 完整示例：数据清理服务

```python
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataCleanupService:
    """数据清理服务"""

    def __init__(self):
        # 配置持久化
        jobstores = {
            'default': SQLAlchemyJobStore(url='sqlite:///cleanup.db')
        }

        self.scheduler = AsyncIOScheduler(jobstores=jobstores)

    async def cleanup_expired_tokens(self):
        """清理过期token"""
        try:
            logger.info("Starting token cleanup...")

            # 模拟数据库操作
            expired = await self._get_expired_tokens()
            logger.info(f"Found {len(expired)} expired tokens")

            deleted = await self._delete_tokens(expired)
            logger.info(f"Deleted {deleted} tokens")

        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            raise

    async def _get_expired_tokens(self):
        await asyncio.sleep(0.1)
        return list(range(10))

    async def _delete_tokens(self, tokens):
        await asyncio.sleep(0.2)
        return len(tokens)

    def start(self):
        # 每小时清理
        self.scheduler.add_job(
            self.cleanup_expired_tokens,
            'interval',
            hours=1,
            id='cleanup_tokens',
            max_instances=1,
            misfire_grace_time=300
        )

        self.scheduler.start()
        logger.info("Data cleanup service started")

# 运行
if __name__ == "__main__":
    service = DataCleanupService()
    service.start()

    try:
        asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        service.scheduler.shutdown()
```

---

## 🎯 小实验

### 实验 1：持久化任务

```python
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

jobstores = {
    'default': SQLAlchemyJobStore(url='sqlite:///test.db')
}

scheduler = BlockingScheduler(jobstores=jobstores)

def job():
    print("Job executed")

scheduler.add_job(job, 'interval', seconds=10, id='test_job')

scheduler.start()
```

**测试**：重启程序，任务仍然存在

---

### 实验 2：任务管理

```python
from apscheduler.schedulers.blocking import BlockingScheduler

scheduler = BlockingScheduler()

def job():
    print("Job running")

job = scheduler.add_job(job, 'interval', seconds=5)

# 5秒后暂停
import time
time.sleep(5)
scheduler.pause_job(job.id)

# 5秒后恢复
time.sleep(5)
scheduler.resume_job(job.id)

scheduler.start()
```

---

## 📚 检查理解

1. **为什么需要任务持久化？**
   - 提示：程序重启

2. **`max_instances`的作用？**
   - 提示：防止任务重叠

3. **`coalesce`的作用？**
   - 提示：合并错过的任务

---

## 🚀 下一步

- 学习Celery Beat → `notes/07c_celery_beat_intro.md`
- 查看完整示例 → `examples/07_scheduled_tasks/level2_data_cleanup.py`

---

**记住：持久化让你的任务不丢失！** 🚀
