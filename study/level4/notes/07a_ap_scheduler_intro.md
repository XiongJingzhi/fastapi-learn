# 07a. APScheduler 基础

## 🎯 学习目标

掌握APScheduler的基本用法，能够实现简单的定时任务。

---

## 🎓 什么是APScheduler？

### 费曼技巧：像给5岁孩子解释

**APScheduler 就像手机上的闹钟应用**：

```
手机闹钟：
1. 你设置闹钟（添加任务）
2. 到时间了手机响（触发器触发）
3. 你听到闹钟声（执行任务）
4. 你可以删除闹钟（删除任务）

APScheduler：
1. 你添加定时任务（add_job）
2. 时间到了（trigger触发）
3. 执行你的代码（执行job）
4. 你可以删除任务（remove_job）
```

---

## 🏗️ 核心组件

### 1. Scheduler（调度器）

**作用**：总指挥，管理所有任务

```python
from apscheduler.schedulers.blocking import BlockingScheduler

# 创建调度器（阻塞式）
scheduler = BlockingScheduler()

# 或者（异步式）
from apscheduler.schedulers.asyncio import AsyncIOScheduler
scheduler = AsyncIOScheduler()
```

**类比**：
- `BlockingScheduler` = 专注做一件事的员工
- `AsyncIOScheduler` = 可以同时做多件事的员工

---

### 2. Trigger（触发器）

**作用**：什么时候执行？

#### 三种Trigger

**1. date - 一次性任务**

```python
from datetime import datetime, timedelta

# 明天中午12点执行
scheduler.add_job(
    my_function,
    'date',
    run_date=datetime.now() + timedelta(days=1, hours=12)
)
```

**类比**：设置一次性的提醒（如：明天下午2点去看牙医）

---

**2. interval - 固定间隔**

```python
# 每5秒执行一次
scheduler.add_job(
    my_function,
    'interval',
    seconds=5
)

# 每2小时执行一次
scheduler.add_job(
    my_function,
    'interval',
    hours=2
)
```

**类比**：设置重复提醒（如：每30分钟喝杯水）

---

**3. cron - 复杂规则**

```python
# 每天上午10点执行
scheduler.add_job(
    my_function,
    'cron',
    hour=10,
    minute=0
)

# 每周一上午9点执行
scheduler.add_job(
    my_function,
    'cron',
    day_of_week='mon',
    hour=9,
    minute=0
)

# 每月1号凌晨执行
scheduler.add_job(
    my_function,
    'cron',
    day=1,
    hour=0,
    minute=0
)
```

**类比**：设置复杂的重复提醒（如：每周一到周五早上7点叫醒我）

---

### 3. Job（任务）

**作用**：做什么？

```python
def my_task():
    print("Executing scheduled task...")

# 添加任务
scheduler.add_job(my_task, 'interval', seconds=10)
```

**任务可以带参数**：

```python
def send_email(to, subject):
    print(f"Sending email to {to}: {subject}")

scheduler.add_job(
    send_email,
    'interval',
    hours=1,
    args=['user@example.com', 'Daily Report']
)
```

---

## 🎨 Hello World示例

### 最简单的定时任务

```python
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime

# 创建调度器
scheduler = BlockingScheduler()

# 定义任务
def print_hello():
    print(f"[{datetime.now()}] Hello, Scheduler!")

# 添加任务：每3秒执行一次
scheduler.add_job(print_hello, 'interval', seconds=3)

print("Scheduler started. Press Ctrl+C to exit.")

# 启动调度器
try:
    scheduler.start()
except (KeyboardInterrupt, SystemExit):
    print("Scheduler stopped.")
```

**运行**：
```bash
python your_file.py
```

**预期输出**：
```
Scheduler started. Press Ctrl+C to exit.
[2025-02-18 10:00:00] Hello, Scheduler!
[2025-02-18 10:00:03] Hello, Scheduler!
[2025-02-18 10:00:06] Hello, Scheduler!
...
```

---

## 🔗 与FastAPI集成

### 嵌入模式

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时
    scheduler.start()
    yield
    # 关闭时
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

async def my_task():
    print("Task executed")

# 添加任务
scheduler.add_job(my_task, 'interval', minutes=5)
```

---

## 🎯 小实验

### 实验 1：每5秒打印当前时间

```python
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime

scheduler = BlockingScheduler()

def print_time():
    print(f"Current time: {datetime.now()}")

scheduler.add_job(print_time, 'interval', seconds=5)

scheduler.start()
```

**预期**：每5秒打印当前时间

---

### 实验 2：明天中午12点执行

```python
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime, timedelta

scheduler = BlockingScheduler()

def tomorrow_noon():
    print("It's noon tomorrow!")

# 计算明天中午12点
tomorrow = datetime.now() + timedelta(days=1)
tomorrow_noon = tomorrow.replace(hour=12, minute=0, second=0, microsecond=0)

scheduler.add_job(tomorrow_noon, 'date', run_date=tomorrow_noon)

scheduler.start()
```

---

### 实验 3：每天上午10点执行

```python
from apscheduler.schedulers.blocking import BlockingScheduler

scheduler = BlockingScheduler()

def daily_task():
    print("Daily task at 10 AM")

scheduler.add_job(daily_task, 'cron', hour=10, minute=0)

scheduler.start()
```

---

## 📚 检查理解

回答这些问题：

1. **Scheduler的作用是什么？**
   - 提示：总指挥

2. **三种Trigger的区别？**
   - 提示：一次性、固定间隔、复杂规则

3. **如何创建一个每分钟执行的任务？**
   - 提示：interval trigger

4. **BlockingScheduler和AsyncIOScheduler的区别？**
   - 提示：阻塞 vs 异步

---

## 🚀 下一步

- 学习APScheduler高级特性 → `notes/07b_ap_scheduler_advanced.md`
- 查看实际代码示例 → `examples/07_scheduled_tasks/level1_simple_timer.py`

---

**记住：APScheduler就像闹钟，简单直接！** 🚀
