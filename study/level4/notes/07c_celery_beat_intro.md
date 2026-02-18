# 07c. Celery Beat 基础

## 🎯 学习目标

理解Celery Beat的架构，能够实现基本的分布式定时任务。

---

## 🎓 为什么需要Celery Beat？

### APScheduler的痛点

```
APScheduler：
    单机运行 ✅
    多实例部署 ❌（每个实例都会执行）
    任务持久化 ✅（需要额外配置）
    分布式 ❌（需要额外方案）
```

**问题场景**：
```
你有3个服务器实例
每个都运行APScheduler
→ 任务会执行3次！❌
```

---

### Celery Beat的优势

```
Celery Beat：
    单个Beat进程 ✅（只调度一次）
    多个Worker进程 ✅（谁空闲谁执行）
    任务持久化 ✅（Broker）
    分布式 ✅（原生支持）
```

**解决方案**：
```
1个Beat进程（调度器）
→ 发送任务到Broker
→ 多个Worker竞争执行
→ 只有1个Worker执行 ✅
```

---

## 🏗️ Celery架构

### 四个核心组件

```
┌─────────────────────────────────────────────────────────────┐
│                    Celery 架构                              │
└─────────────────────────────────────────────────────────────┘

1. Beat（调度器）
   └─ 像公司前台
   └─ 有任务清单（schedule）
   └─ 到点发送任务到Broker

2. Broker（消息队列）
   └─ 像任务公告栏
   └─ Beat发布任务到这里
   └─ Worker从这里取任务

3. Worker（执行器）
   └─ 像员工
   └─ 从Broker取任务
   └─ 执行任务

4. Backend（结果存储）
   └─ 像任务档案
   └─ 存储任务执行结果
```

---

### 费曼技巧：餐厅类比

**Celery Beat 就像餐厅**：

```
Beat（前台）：
   收到订单
   → 放到订单队列（Broker）

Chef（Worker）：
   从订单队列取订单
   → 做菜（执行任务）
   → 菜做好了（结果）

结果记录（Backend）：
   记录哪个订单完成了
```

---

## 🎨 Hello World

### 步骤 1：安装依赖

```bash
pip install celery redis
```

### 步骤 2：定义任务

```python
# tasks.py
from celery import Celery

# 创建Celery应用
app = Celery('tasks')

# 配置
app.conf.update(
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/1',
)

# 定义任务
@app.task
def add(x, y):
    result = x + y
    print(f"Adding {x} + {y} = {result}")
    return result

@app.task
def send_email(to, subject):
    print(f"Sending email to {to}: {subject}")
    return {"status": "sent"}
```

---

### 步骤 3：配置Beat

```python
# beat_config.py
from celery.schedules import crontab

beat_schedule = {
    'add-every-30-seconds': {
        'task': 'tasks.add',
        'schedule': 30.0,  # 每30秒
        'args': (16, 16)
    },
    'send-daily-email': {
        'task': 'tasks.send_email',
        'schedule': crontab(hour=9, minute=0),  # 每天上午9点
        'args': ("user@example.com", "Daily Report")
    },
}
```

---

### 步骤 4：启动Worker

```bash
celery -A tasks worker --loglevel=info
```

**输出**：
```
-------------- celery@xxx v5.x.x
---- **** -----
--- * ***  * -- Linux-x.x.x-x
-- * - **** ---
- ** ---------- [config]
- ** ---------- .> app:         tasks:0x...
- ** ---------- .> transport:   redis://localhost:6379/0
- ** ---------- .> results:     redis://localhost:6379/1
- *** --- * --- .> concurrency: 8 (prefork)
-- ******* ---- .> task events: OFF
--- ***** -----
 -------------- [queues]
                .> celery           exchange=celery(direct) key=celery

[tasks]
  . tasks.add
  . tasks.send_email

[INFO] Ready to accept tasks!
```

---

### 步骤 5：启动Beat

```bash
celery -A beat_config beat --loglevel=info
```

**输出**：
```
celery beat v5.x.x is starting.
__    -    ... [node]
LocalTime -> 2025-02-18 10:00:00
Configuration ->
    . broker -> redis://localhost:6379/0
    . loader -> celery.loaders.app.AppLoader
    . scheduler -> celery.beat.PersistentScheduler
    . logfile -> [stderr]@%INFO
    . maxinterval -> 5.00 seconds (5s)
[INFO] Scheduler: Sending due task add-every-30-seconds
[INFO] Scheduler: Sending due task add-every-30-seconds
```

---

## 📅 Schedule配置

### interval（固定间隔）

```python
beat_schedule = {
    'task-every-30-seconds': {
        'task': 'tasks.my_task',
        'schedule': 30.0,  # 30秒
    },
    'task-every-hour': {
        'task': 'tasks.my_task',
        'schedule': 3600.0,  # 1小时
    },
}
```

---

### crontab（复杂规则）

```python
from celery.schedules import crontab

beat_schedule = {
    # 每天上午9点
    'daily-task': {
        'task': 'tasks.my_task',
        'schedule': crontab(hour=9, minute=0),
    },

    # 每周一上午9点
    'weekly-task': {
        'task': 'tasks.my_task',
        'schedule': crontab(day_of_week='mon', hour=9, minute=0),
    },

    # 每月1号凌晨
    'monthly-task': {
        'task': 'tasks.my_task',
        'schedule': crontab(day=1, hour=0, minute=0),
    },

    # 每5分钟
    'frequent-task': {
        'task': 'tasks.my_task',
        'schedule': crontab(minute='*/5'),
    },
}
```

---

### countdown倒计时

```python
@app.task
def process_data(data):
    return f"Processed {data}"

# 10秒后执行
process_data.apply_async(args=[123], countdown=10)
```

---

## 🎯 完整示例

### 任务定义

```python
# tasks.py
from celery import Celery

app = Celery('myapp')
app.conf.update(
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/1',
)

@app.task
def generate_report(report_type):
    print(f"Generating {report_type} report...")
    # 模拟耗时操作
    import time
    time.sleep(2)
    return f"{report_type} report done"

@app.task
def cleanup_database():
    print("Cleaning up database...")
    import time
    time.sleep(1)
    return "Database cleaned"
```

### Beat配置

```python
# beat_config.py
from celery.schedules import crontab

beat_schedule = {
    'daily-report': {
        'task': 'tasks.generate_report',
        'schedule': crontab(hour=8, minute=0),
        'args': ('daily',)
    },
    'weekly-cleanup': {
        'task': 'tasks.cleanup_database',
        'schedule': crontab(day_of_week='sun', hour=2, minute=0),
    },
}
```

### 启动脚本

```bash
# 启动Redis
docker run -d -p 6379:6379 redis:alpine

# 启动Worker
celery -A tasks worker --loglevel=info

# 启动Beat（新终端）
celery -A beat_config beat --loglevel=info
```

---

## 🎯 小实验

### 实验 1：手动触发任务

```python
from tasks import add

# 同步调用
result = add.delay(4, 6)
print(f"Task ID: {result.id}")

# 等待结果
print(f"Result: {result.get()}")
```

---

### 实验 2：定时任务

```python
# beat_config.py
from celery.schedules import crontab

beat_schedule = {
    'test-task': {
        'task': 'tasks.add',
        'schedule': crontab(minute='*/1'),  # 每分钟
        'args': (1, 1)
    },
}
```

**观察**：每分钟Worker输出 "Adding 1 + 1 = 2"

---

## 📚 检查理解

1. **Celery的四个组件是什么？**
   - 提示：Beat, Broker, Worker, Backend

2. **为什么Celery适合分布式？**
   - 提示：单个Beat，多个Worker

3. **如何配置每天上午10点执行？**
   - 提示：crontab(hour=10, minute=0)

---

## 🚀 下一步

- 学习Celery高级特性 → `notes/07d_celery_beat_advanced.md`
- 查看完整示例 → `examples/07_scheduled_tasks/celery_beat/`

---

**记住：Celery Beat = 分布式定时任务的王者！** 🚀
