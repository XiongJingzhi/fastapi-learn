# 07e. 定时任务最佳实践

## 🎯 学习目标

掌握定时任务在生产环境中的最佳实践，能够设计可靠的定时任务系统。

---

## 🎯 技术选型决策树

### 根据场景选择

```
你的需求是什么？
    │
    ├─ 单机运行
    │   └─ 任务数量 < 10
    │       └─ → APScheduler ✅
    │
    ├─ 多实例部署
    │   ├─ 任务数量 < 50
    │   │   └─ → APScheduler + 分布式锁 ✅
    │   │
    │   └─ 任务数量 >= 50
    │       ├─ 需要任务链
    │       │   └─ → Celery Beat ✅
    │       │
    │       └─ 不需要复杂特性
    │           └─ → APScheduler + 分布式锁 ✅
    │
    └─ 微服务架构
        └─ → Celery Beat ✅
```

---

### 决策对比表

| 场景 | APScheduler | Celery Beat |
|------|-------------|-------------|
| **个人项目** | ✅ 推荐 | ⚠️ 过度设计 |
| **小型团队** | ✅ 推荐 | ⚠️ 看需求 |
| **中型应用** | ✅ + 分布式锁 | ✅ 推荐 |
| **大型系统** | ❌ 不推荐 | ✅ 推荐 |
| **微服务** | ❌ 不推荐 | ✅ 推荐 |

---

## 🏗️ 架构模式对比

### 模式 1：嵌入式

**描述**：调度器在FastAPI进程中运行

```python
from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@app.on_event("startup")
async def startup():
    scheduler.start()

@app.on_event("shutdown")
async def shutdown():
    scheduler.shutdown()
```

**优点**：
- ✅ 部署简单
- ✅ 共享应用状态
- ✅ 无需额外进程

**缺点**：
- ❌ 耦合度高
- ❌ 任务阻塞影响API
- ❌ 扩展性差

**适用场景**：
- 小型应用
- 任务不频繁（< 10次/小时）
- 任务执行快（< 1分钟）

---

### 模式 2：独立进程

**描述**：调度器作为独立进程运行

```python
# scheduler.py（独立进程）
from apscheduler.schedulers.blocking import BlockingScheduler

scheduler = BlockingScheduler()
scheduler.add_job(task, 'interval', hours=1)
scheduler.start()
```

**优点**：
- ✅ 解耦
- ✅ 独立扩展
- ✅ 任务不影响API

**缺点**：
- ❌ 部署复杂（多进程）
- ❌ 需要进程管理（systemd/supervisor）

**适用场景**：
- 中大型应用
- 任务频繁（> 10次/小时）
- 任务耗时（> 1分钟）

---

### 模式 3：分布式（Celery）

**描述**：Beat + Worker + Broker

```
Beat进程 → Broker → Worker 1, Worker 2, Worker 3
```

**优点**：
- ✅ 完全解耦
- ✅ 高可用
- ✅ 易扩展
- ✅ 任务链支持

**缺点**：
- ❌ 架构复杂
- ❌ 依赖多（Redis/RabbitMQ）
- ❌ 学习曲线陡

**适用场景**：
- 大型系统
- 微服务架构
- 复杂任务依赖

---

## 📋 生产环境清单

### 配置管理

**✅ 必须配置**：

```python
# 1. 时区（重要！）
scheduler.configure(timezone='UTC')

# 2. 任务持久化
jobstores = {
    'default': SQLAlchemyJobStore(url='postgresql://...')
}

# 3. 执行器
executors = {
    'default': ThreadPoolExecutor(max_workers=20)
}

# 4. 任务默认值
job_defaults = {
    'coalesce': True,
    'max_instances': 1,
    'misfire_grace_time': 60
}
```

---

### 日志规范

**✅ 结构化日志**：

```python
import logging
import json

class StructuredLogger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)

    def log(self, level, message, **context):
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message,
            'context': context
        }
        self.logger.log(level, json.dumps(log_entry))

# 使用
logger = StructuredLogger(__name__)
logger.log(logging.INFO, "Task completed", task_id="123", duration=5.2)
```

---

### 监控告警

**✅ 关键指标**：

```python
# 1. 任务执行时间
task_duration = completed_at - started_at

# 2. 任务成功率
success_rate = success_count / total_count

# 3. 任务失败次数
failure_count = get_failure_count(task_id)

# 4. 任务队列长度
queue_length = len(get_pending_tasks())
```

**告警规则**：
- 任务失败 > 3次 → 发送告警
- 任务执行时间 > 预期2倍 → 发送告警
- 任务队列积压 > 100 → 发送告警

---

### 灾难恢复

**✅ 备份策略**：

```bash
# 1. 定期备份数据库
# 2. 备份任务配置
# 3. 备份Beat调度文件（celerybeat-schedule）
```

**✅ 恢复流程**：

```bash
# 1. 恢复数据库
# 2. 恢复任务配置
# 3. 重启Beat和Worker
# 4. 验证任务正常执行
```

---

## ⚠️ 常见陷阱

### 陷阱 1：时区问题

**问题**：

```python
# ❌ 错误：没有指定时区
scheduler.add_job(task, 'cron', hour=10)
# 会在服务器本地时间上午10点执行

# ✅ 正确：显式指定时区
scheduler.add_job(task, 'cron', hour=10, timezone='UTC')
```

**最佳实践**：
- 所有任务使用UTC
- 前端展示时转换为本地时间

---

### 陷阱 2：任务堆积

**问题**：

```
任务执行时间（5分钟）> 任务间隔（1分钟）
→ 任务堆积
→ 内存/数据库耗尽
```

**解决方案**：

```python
# 1. 设置max_instances
scheduler.add_job(
    slow_task,
    'interval',
    minutes=1,
    max_instances=1  # 防止任务重叠
)

# 2. 使用coalesce
scheduler.add_job(
    task,
    'interval',
    minutes=1,
    coalesce=True  # 错过的任务合并执行
)
```

---

### 陷阱 3：死锁

**问题**：

```python
# ❌ 错误：任务中使用阻塞锁
lock.acquire()
slow_operation()  # 如果这里挂了，锁永远不会释放
lock.release()
```

**解决方案**：

```python
# ✅ 正确：使用超时锁
lock.acquire(timeout=60)
try:
    slow_operation()
finally:
    lock.release()
```

---

### 陷阱 4：内存泄漏

**问题**：

```python
# ❌ 错误：任务中累积数据
results = []

@app.task
def process_data():
    data = fetch_large_data()
    results.append(data)  # 永远增长！
```

**解决方案**：

```python
# ✅ 正确：定期清理
@app.task
def process_data():
    data = fetch_large_data()
    process(data)
    del data  # 释放内存
```

---

## 🎯 实战案例

### 案例 1：数据归档任务

**需求**：每天凌晨2点归档前一天的数据

**方案**：APScheduler独立进程

```python
# archive_scheduler.py
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = BlockingScheduler(
    jobstores={
        'default': SQLAlchemyJobStore(url='postgresql://...')
    }
)

def archive_data():
    """归档数据"""
    logger.info("Starting data archival...")
    try:
        # 1. 查询需要归档的数据
        data = query_yesterday_data()
        logger.info(f"Found {len(data)} records")

        # 2. 导出到文件
        export_to_file(data)
        logger.info("Data exported")

        # 3. 删除旧数据
        delete_old_data(data)
        logger.info("Old data deleted")

        # 4. 记录归档日志
        log_archive(data)
        logger.info("Archive logged")

    except Exception as e:
        logger.error(f"Archive failed: {e}")
        # 发送告警
        send_alert(f"Data archival failed: {e}")
        raise

# 每天凌晨2点执行
scheduler.add_job(
    archive_data,
    'cron',
    hour=2,
    minute=0,
    timezone='UTC',
    id='daily_archive',
    max_instances=1,
    misfire_grace_time=3600  # 容忍1小时延迟
)

if __name__ == "__main__":
    logger.info("Archive scheduler starting...")
    scheduler.start()
```

---

### 案例 2：分布式报表系统

**需求**：
- 每小时生成报表
- 报表生成耗时（5-10分钟）
- 多实例部署

**方案**：Celery Beat

```python
# tasks.py
from celery import Celery, chain
import logging

logger = logging.getLogger(__name__)

app = Celery('reports')
app.conf.update(
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/1',
)

@app.task(bind=True, max_retries=3)
def fetch_data(self):
    """获取数据"""
    try:
        logger.info("Fetching data...")
        data = query_database()
        logger.info(f"Fetched {len(data)} records")
        return data
    except Exception as e:
        logger.error(f"Fetch failed: {e}")
        raise self.retry(exc=e, countdown=60)

@app.task(bind=True)
def generate_report(self, data):
    """生成报表"""
    try:
        logger.info("Generating report...")
        report = create_report(data)
        logger.info("Report generated")
        return report
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise self.retry(exc=e, countdown=60)

@app.task
def send_report(report):
    """发送报表"""
    logger.info("Sending report...")
    email_report(report)
    logger.info("Report sent")
    return "Done"

@app.task
def cleanup():
    """清理资源"""
    logger.info("Cleaning up...")
    delete_temp_files()
    return "Cleaned"

# 创建报表生成流水线
@app.task
def create_report_pipeline():
    """创建报表流水线"""
    pipeline = chain(
        fetch_data.s(),
        generate_report.s(),
        send_report.s(),
        cleanup.s()
    )
    return pipeline()
```

**Beat配置**：

```python
# beat_config.py
from celery.schedules import crontab

beat_schedule = {
    'hourly-report': {
        'task': 'tasks.create_report_pipeline',
        'schedule': crontab(minute=0),  # 每小时
    },
}
```

---

## 📚 检查理解

1. **你的应用应该使用哪种模式？**
   - 提示：根据规模和需求

2. **为什么时区很重要？**
   - 提示：多服务器部署

3. **如何防止任务堆积？**
   - 提示：max_instances, coalesce

---

## 🚀 总结

### 关键要点

1. **选择合适的技术**：不是最复杂的就是最好的
2. **配置要规范**：时区、持久化、日志
3. **监控要到位**：执行时间、成功率、队列长度
4. **失败要处理**：重试、告警、降级
5. **测试要充分**：单元测试、集成测试

### 架构演进

```
个人项目 → APScheduler（嵌入式）
    ↓
团队项目 → APScheduler（独立进程）
    ↓
中型应用 → APScheduler + 分布式锁
    ↓
大型系统 → Celery Beat
```

---

## 🎓 下一步

恭喜你完成了定时任务模块的学习！

**建议**：
- 实现一个实际的定时任务
- 阅读官方文档
- 尝试不同的技术栈
- 分享你的经验

---

**记住：没有银弹，选择合适的工具！** 🚀
