# 07d. Celery Beat 高级特性

## 🎯 学习目标

掌握Celery Beat的高级用法，包括任务链、任务监控、失败处理。

---

## 🎓 分布式任务

### 多Worker部署

```
1个Beat进程
    ↓
发送任务到Broker
    ↓
┌─────────┬─────────┬─────────┐
│ Worker1 │ Worker2 │ Worker3 │
└─────────┴─────────┴─────────┘
    ↓         ↓         ↓
竞争获取任务
    ↓
只有1个Worker执行
```

**启动多个Worker**：

```bash
# Worker 1
celery -A tasks worker --loglevel=info -n worker1@%h

# Worker 2（新终端）
celery -A tasks worker --loglevel=info -n worker2@%h

# Worker 3（新终端）
celery -A tasks worker --loglevel=info -n worker3@%h
```

---

### 任务路由

```python
# tasks.py
from celery import Celery

app = Celery('myapp')
app.conf.update(
    broker_url='redis://localhost:6379/0',
    task_routes = {
        'tasks.heavy_task': {
            'queue': 'heavy_tasks',
        },
        'tasks.light_task': {
            'queue': 'light_tasks',
        },
    },
)

@app.task
def heavy_task():
    # 耗时任务
    import time
    time.sleep(10)
    return "Heavy task done"

@app.task
def light_task():
    # 轻量任务
    return "Light task done"
```

**启动Worker监听特定队列**：

```bash
# 处理重任务的Worker
celery -A tasks worker --loglevel=info -Q heavy_tasks

# 处理轻任务的Worker
celery -A tasks worker --loglevel=info -Q light_tasks
```

---

## 🔗 高级特性

### 1. 任务链（Chain）

**场景**：A完成后再执行B

```python
from celery import chain

# 定义任务
@app.task
def task_a():
    print("Task A")
    return "A's result"

@app.task
def task_b(previous_result):
    print(f"Task B, got {previous_result}")
    return "B's result"

@app.task
def task_c(previous_result):
    print(f"Task C, got {previous_result}")
    return "C's result"

# 创建任务链
result = chain(
    task_a.s(),
    task_b.s(),
    task_c.s()
)()

# 输出：
# Task A
# Task B, got A's result
# Task C, got B's result
```

**费曼技巧**：
- 就像流水线
- A传给B，B传给C
- 一步接一步

---

### 2. 任务组（Group）

**场景**：并行执行多个任务

```python
from celery import group

@app.task
def task_1():
    return "Task 1 done"

@app.task
def task_2():
    return "Task 2 done"

@app.task
def task_3():
    return "Task 3 done"

# 并行执行
result = group(
    task_1.s(),
    task_2.s(),
    task_3.s()
)()

# 所有任务并行执行
```

**费曼技巧**：
- 就像雇佣3个工人
- 同时工作
- 谁先完成谁先结束

---

### 3. 任务回调（Callback）

**场景**：任务完成后通知

```python
@app.task
def main_task():
    result = do_something()
    return result

@app.task
def callback_task(previous_result):
    print(f"Main task completed with: {previous_result}")
    send_notification(previous_result)

# 主任务完成后执行回调
main_task.apply_async(link=callback_task.s())
```

---

## 📊 任务监控

### Flower监控界面

**安装**：

```bash
pip install flower
```

**启动**：

```bash
celery -A tasks flower
```

**访问**：http://localhost:5555

**功能**：
- 查看任务执行状态
- 查看Worker状态
- 查看任务执行时间
- 查看任务失败原因

---

### 任务状态追踪

```python
@app.task(bind=True)
def long_task(self):
    # self是任务实例
    print(f"Task ID: {self.request.id}")
    print(f"Task State: {self.state}")

    # 更新状态
    self.update_state(state='PROGRESS', meta={'progress': 50})

    # 执行任务
    result = do_work()

    return result
```

---

## ⚠️ 失败处理

### 自动重试

```python
@app.task(bind=True, max_retries=3)
def flaky_task(self):
    try:
        # 可能失败的操作
        result = risky_operation()
        return result
    except Exception as e:
        # 重试，指数退避
        raise self.retry(exc=e, countdown=2 ** self.request.retries)
```

**费曼技巧**：
- 就像快递寄不出去
- 再寄一次
- 如果还是失败，等待更长时间再试

---

### 超时控制

```python
@app.task(time_limit=60, soft_time_limit=50)
def timeout_task():
    """
    time_limit: 硬超时（60秒后强制终止）
    soft_time_limit: 软超时（50秒后抛出异常）
    """
    import time
    time.sleep(70)  # 超时！
```

---

### 速率限制

```python
@app.task(rate_limit='10/m')
def rate_limited_task():
    """
    每分钟最多执行10次
    """
    print("Task executed")
```

---

## 🎯 完整示例

### 数据处理流水线

```python
from celery import Celery, chain, group
import time

app = Celery('pipeline')
app.conf.update(
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/1',
)

@app.task
def fetch_data():
    """获取数据"""
    print("Fetching data...")
    time.sleep(1)
    return [1, 2, 3, 4, 5]

@app.task
def process_item(item):
    """处理单个数据项"""
    print(f"Processing item {item}")
    time.sleep(0.5)
    return item * 2

@app.task
def save_results(results):
    """保存结果"""
    print(f"Saving results: {results}")
    time.sleep(1)
    return "Saved"

@app.task
def send_notification():
    """发送通知"""
    print("Sending notification...")
    return "Notification sent"

# 创建流水线
def create_pipeline():
    # 1. 获取数据
    fetch_job = fetch_data.s()

    # 2. 并行处理每个数据项
    def process_results(data):
        return group(process_item.s(i) for i in data)()

    process_job = process_results

    # 3. 保存结果
    save_job = save_results.s()

    # 4. 发送通知
    notify_job = send_notification.s()

    # 组装流水线
    pipeline = chain(
        fetch_job,
        process_job,
        save_job,
        notify_job
    )

    return pipeline()

# 执行流水线
if __name__ == "__main__":
    result = create_pipeline()
    print(f"Pipeline started: {result.id}")
```

---

## 🎯 小实验

### 实验 1：任务链

```python
from celery import Celery, chain

app = Celery('experiments')
app.conf.update(broker_url='redis://localhost:6379/0')

@app.task
def add(x, y):
    result = x + y
    print(f"{x} + {y} = {result}")
    return result

# 创建链：((1+2) + 3) + 4
pipeline = chain(
    add.s(1, 2),
    add.s(3),
    add.s(4)
)

result = pipeline()
print(f"Final result: {result.get()}")
# 输出：1+2=3, 3+3=6, 6+4=10
# Final result: 10
```

---

### 实验 2：任务组

```python
from celery import Celery, group

app = Celery('experiments')
app.conf.update(broker_url='redis://localhost:6379/0')

@app.task
def multiply(x, y):
    result = x * y
    print(f"{x} * {y} = {result}")
    return result

# 并行执行
job = group(
    multiply.s(2, 3),
    multiply.s(4, 5),
    multiply.s(6, 7)
)

result = job()
print(f"Results: {result.get()}")
# 输出：[6, 20, 42]
```

---

## 📚 检查理解

1. **Chain和Group的区别？**
   - 提示：串行 vs 并行

2. **如何处理任务失败？**
   - 提示：retry

3. **Flower的作用？**
   - 提示：监控

---

## 🚀 下一步

- 学习最佳实践 → `notes/07e_best_practices.md`
- 查看完整示例 → `examples/07_scheduled_tasks/celery_beat/`

---

**记住：Celery的高级特性让你的任务更强大！** 🚀
