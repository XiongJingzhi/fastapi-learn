# 阶段 0.4: 阻塞操作 - 异步编程的"敌人"

## 🎯 核心概念（费曼简化版）

### 阻塞操作 = 卡住整个队伍

想象你在排队办理业务：

**阻塞操作**：
1. 你到柜台
2. 办理员开始处理
3. 办理员发现需要等待某个文件（比如10分钟）
4. **整个队伍停下了** - 所有人都要等
5. 10分钟后，继续办理
6. 下一个人才能开始

**问题**：一个人等待，所有人都被阻塞

---

## 🔍 什么是阻塞操作

### 阻塞操作的特征

```python
# 这些操作会阻塞整个事件循环

# 1. time.sleep() - 阻塞式等待
import time
time.sleep(5)  # ❌ 整个程序停止5秒

# 2. 同步文件IO
with open("large_file.txt") as f:
    content = f.read()  # ❌ 读取时阻塞

# 3. 同步HTTP请求
import requests
response = requests.get("https://api.example.com")  # ❌ 等待响应

# 4. 同步数据库操作
import sqlite3
cursor.execute("SELECT * FROM large_table")  # ❌ 查询时阻塞

# 5. CPU密集型计算
result = sum(range(1000000000))  # ❌ 计算时阻塞
```

### 为什么阻塞是问题

```python
import asyncio
import time

async def bad_task(name):
    print(f"{name} 开始")
    time.sleep(2)  # ❌ 阻塞！整个事件循环停止
    print(f"{name} 完成")

async def main():
    # 即使用了异步，但因为有 time.sleep()
    # 任务仍然会顺序执行！
    await asyncio.gather(
        bad_task("A"),
        bad_task("B"),
        bad_task("C"),
    )
    # 总时间：6秒（2+2+2），而不是2秒

asyncio.run(main())
```

**问题**：
- 虽然用了 `async`/`await`
- 但 `time.sleep()` 阻塞了整个事件循环
- 其他任务无法执行
- 失去了异步的优势

---

## ✅ 非阻塞的替代方案

### 1. 等待操作

```python
# ❌ 阻塞
import time
time.sleep(5)

# ✅ 非阻塞
import asyncio
await asyncio.sleep(5)
```

### 2. 文件IO

```python
# ❌ 阻塞
with open("file.txt") as f:
    content = f.read()

# ✅ 非阻塞
import aiofiles
async with aiofiles.open("file.txt") as f:
    content = await f.read()
```

### 3. HTTP请求

```python
# ❌ 阻塞
import requests
response = requests.get("https://api.example.com")

# ✅ 非阻塞
import httpx
async with httpx.AsyncClient() as client:
    response = await client.get("https://api.example.com")
```

### 4. 数据库操作

```python
# ❌ 阻塞
import sqlite3
conn = sqlite3.connect("database.db")
cursor = conn.cursor()
cursor.execute("SELECT * FROM users")

# ✅ 非阻塞
import aiosqlite
async with aiosqlite.connect("database.db") as db:
    cursor = await db.execute("SELECT * FROM users")
    rows = await cursor.fetchall()
```

---

## 🔧 处理无法避免的阻塞操作

### 使用 run_in_executor()

当必须使用同步库时，可以在线程池中运行：

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

def blocking_function(n: int) -> int:
    """一个阻塞的CPU密集型函数"""
    result = 1
    for i in range(1, n + 1):
        result *= i
    return result

async def main():
    loop = asyncio.get_event_loop()

    # 在线程池中运行阻塞函数
    with ThreadPoolExecutor() as executor:
        result = await loop.run_in_executor(
            executor,
            blocking_function,
            1000
        )

    print(result)

asyncio.run(main())
```

**run_in_executor() 的作用**：
- 在单独的线程中运行阻塞函数
- 不阻塞事件循环
- 其他任务可以继续执行

### 对于CPU密集型任务

```python
from concurrent.futures import ProcessPoolExecutor

def cpu_bound_task(n: int):
    """CPU密集型任务"""
    # 大量计算
    return sum(range(n))

async def main():
    loop = asyncio.get_event_loop()

    # 使用进程池（而不是线程池）
    with ProcessPoolExecutor() as executor:
        result = await loop.run_in_executor(
            executor,
            cpu_bound_task,
            1000000000
        )

    print(result)

asyncio.run(main())
```

**为什么用 ProcessPoolExecutor**：
- CPU密集型任务不适合线程池（GIL限制）
- 进程池可以真正并行执行
- 适合纯计算任务

---

## 📊 常见阻塞操作对照表

| 操作 | ❌ 阻塞版本 | ✅ 异步版本 |
|------|-----------|-----------|
| 等待 | `time.sleep(1)` | `await asyncio.sleep(1)` |
| 文件读 | `open().read()` | `aiofiles.open().read()` |
| HTTP GET | `requests.get()` | `httpx.AsyncClient().get()` |
| 数据库 | `sqlite3` | `aiosqlite`, `asyncpg` |
| 子进程 | `subprocess.run()` | `asyncio.create_subprocess_exec()` |

---

## 💡 实际案例

### 案例1：错误的异步代码

```python
import asyncio
import time
import requests

async def fetch_user(user_id: int):
    # ❌ 使用了阻塞的 requests.get()
    response = requests.get(f"https://api.example.com/users/{user_id}")
    return response.json()

async def main():
    users = await asyncio.gather(
        fetch_user(1),
        fetch_user(2),
        fetch_user(3),
    )
    print(users)

# 问题：虽然是异步，但 requests.get() 会阻塞
# 结果：任务仍然是顺序执行
asyncio.run(main())
```

### 案例2：正确的异步代码

```python
import asyncio
import httpx

async def fetch_user(user_id: int):
    # ✅ 使用异步的 httpx
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.example.com/users/{user_id}")
        return response.json()

async def main():
    users = await asyncio.gather(
        fetch_user(1),
        fetch_user(2),
        fetch_user(3),
    )
    print(users)

# 结果：真正的并发执行
asyncio.run(main())
```

### 案例3：使用 run_in_executor

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor
import requests  # 同步库

def fetch_user_sync(user_id: int):
    """同步的HTTP请求"""
    response = requests.get(f"https://api.example.com/users/{user_id}")
    return response.json()

async def fetch_user_async(user_id: int):
    """包装同步函数为异步"""
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        result = await loop.run_in_executor(
            executor,
            fetch_user_sync,
            user_id
        )
    return result

async def main():
    # 即使使用同步库，也能并发执行
    users = await asyncio.gather(
        fetch_user_async(1),
        fetch_user_async(2),
        fetch_user_async(3),
    )
    print(users)

asyncio.run(main())
```

---

## 🧪 理解验证

### 问题1：如何判断一个操作是否阻塞？

**答案**：
- 看是否有 `await` 关键字
- 看文档说明（ synchronous / asynchronous ）
- 测试：在 async 函数中使用，观察是否阻塞其他任务

### 问题2：所有阻塞操作都要避免吗？

**答案**：
- ❌ 不是！如果操作很快（< 10ms），可以接受
- ❌ 如果没有异步版本，可以使用 `run_in_executor()`
- ✅ 主要避免长时间阻塞（网络请求、文件IO、计算）

### 问题3：为什么 time.sleep() 不能在异步中使用？

**答案**：
- `time.sleep()` 会阻塞整个线程
- 事件循环在同一個线程中运行
- 所以事件循环也被阻塞了
- 应该用 `await asyncio.sleep()`

---

## 📝 记忆口诀

```
阻塞操作：卡住整个队伍，别人都得等
识别方法：看有没有 await，查文档

替代方案：
- 等待：asyncio.sleep()
- 文件：aiofiles
- HTTP：httpx
- 数据库：asyncpg, aiosqlite

无法避免：用 run_in_executor() 放到线程池

记住：异步代码中的阻塞操作 = 失去异步优势
```

---

## 🚀 下一步

理解了阻塞操作后，让我们学习如何在 FastAPI 中应用异步知识：

**下一个主题**：FastAPI 中的异步

```bash
uvicorn app.examples.05_async_with_fastapi:app --reload
```
