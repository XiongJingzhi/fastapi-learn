# asyncio 和事件循环：深入理解

> **基于你的 Node.js 背景，用最简单的方式解释**

---

## 🎯 三个核心问题

1. **Python 的 asyncio 异步库的作用是什么？**
2. **单线程事件循环的机制是如何工作的？**
3. **如何处理同步的任务？同步的任务和异步任务都在一个循环里吗？**

让我们逐个击破！

---

## 问题 1：asyncio 的作用是什么？

### 最简单的答案

**asyncio = Python 版的 Node.js 事件循环 + 异步工具箱**

在 Node.js 中，事件循环是内置的，你感觉不到它的存在。

在 Python 中，你需要 **显式使用** asyncio 库来管理事件循环和异步操作。

---

### 对比理解

#### Node.js（隐式事件循环）
```javascript
// JavaScript - 事件循环自动运行
console.log('Start');

setTimeout(() => {
    console.log('Timeout');
}, 1000);

console.log('End');

// 你不需要写任何代码来启动事件循环
// 它一直在后台运行
```

#### Python（显式事件循环）
```python
import asyncio

# Python - 需要显式启动事件循环
async def main():
    print('Start')
    await asyncio.sleep(1)  # 类似 setTimeout
    print('Timeout')
    print('End')

asyncio.run(main())  # 显式启动事件循环
```

**关键差异**：
- Node.js：事件循环一直运行（隐式）
- Python：需要用 `asyncio.run()` 启动（显式）

---

### asyncio 的三大核心功能

#### 1. 事件循环管理
```python
import asyncio

# 启动事件循环
asyncio.run(main())

# 或者更底层的写法
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(main())
```

**类比**：
- Node.js 的事件循环像**自动挡汽车**（自动管理）
- Python 的 asyncio 像**手动挡汽车**（你需要操作）

---

#### 2. 协程（Coroutine）支持
```python
import asyncio

async def fetch_data():
    # async 定义一个协程
    await asyncio.sleep(1)  # await 等待异步操作
    return {"data": "success"}

# 运行协程
result = asyncio.run(fetch_data())
```

**对比 JavaScript**：
```javascript
// JavaScript
async function fetchData() {
    await new Promise(r => setTimeout(r, 1000));
    return { data: "success" }
}
```

**关键字完全相同**：`async` 和 `await`！

---

#### 3. 异步工具集
```python
import asyncio

# 并发执行多个任务
async def task1():
    await asyncio.sleep(1)
    return "Task 1 done"

async def task2():
    await asyncio.sleep(1)
    return "Task 2 done"

async def main():
    # 同时运行两个任务（类似 Promise.all）
    results = await asyncio.gather(task1(), task2())
    print(results)

asyncio.run(main())
```

**asyncio 工具箱包含**：
- `asyncio.sleep()` - 延迟执行（类似 `setTimeout`）
- `asyncio.gather()` - 并发执行（类似 `Promise.all`）
- `asyncio.create_task()` - 创建任务（类似 `process.nextTick`）
- `asyncio.Queue()` - 异步队列
- `asyncio.Lock()` - 异步锁

---

## 问题 2：单线程事件循环如何工作？

### 最简单的解释

**事件循环 = 一个永远在运行的 while 循环**

它的核心逻辑：
```python
while True:
    # 1. 检查是否有任务准备执行
    task = get_next_ready_task()

    if task:
        # 2. 执行任务，直到遇到 await
        task.run()

        # 3. 如果遇到 await，暂停任务
        if task.is_waiting():
            pause_task(task)

    # 4. 等待 I/O 事件（网络请求、文件读写等）
    wait_for_io_events()

    # 5. 如果有 I/O 完成，恢复对应的任务
    resume_completed_tasks()
```

---

### 详细工作流程

让我用一个实际例子说明：

```python
import asyncio
import time

async def fetch_user(user_id):
    print(f"开始获取用户 {user_id}")
    await asyncio.sleep(2)  # 模拟网络请求（阻塞 2 秒）
    print(f"用户 {user_id} 获取完成")
    return f"User-{user_id}"

async def main():
    start = time.time()

    # 并发获取 3 个用户
    results = await asyncio.gather(
        fetch_user(1),
        fetch_user(2),
        fetch_user(3)
    )

    print(f"结果: {results}")
    print(f"总时间: {time.time() - start:.2f} 秒")

asyncio.run(main())
```

**输出**：
```
开始获取用户 1
开始获取用户 2
开始获取用户 3
用户 1 获取完成
用户 2 获取完成
用户 3 获取完成
结果: ['User-1', 'User-2', 'User-3']
总时间: 2.00 秒  # 不是 6 秒！
```

---

### 事件循环的时间线

让我们看看事件循环内部发生了什么：

```
时刻 0.0s:
├─ 启动 fetch_user(1)
│  └─ 执行到 await asyncio.sleep(2) → 暂停，设置 2s 后唤醒
├─ 启动 fetch_user(2)
│  └─ 执行到 await asyncio.sleep(2) → 暂停，设置 2s 后唤醒
├─ 启动 fetch_user(3)
│  └─ 执行到 await asyncio.sleep(2) → 暂停，设置 2s 后唤醒
└─ 所有任务都在等待，事件循环进入休眠

时刻 0.0s ~ 2.0s:
└─ 事件循环在等待，CPU 可以处理其他事情（如果有的话）

时刻 2.0s:
├─ fetch_user(1) 的 sleep 完成 → 恢复执行 → 打印"用户 1 获取完成"
├─ fetch_user(2) 的 sleep 完成 → 恢复执行 → 打印"用户 2 获取完成"
├─ fetch_user(3) 的 sleep 完成 → 恢复执行 → 打印"用户 3 获取完成"
└─ main() 的 gather 完成 → 打印结果

总时间：2 秒（并发执行，不是串行的 6 秒）
```

---

### 对比 Node.js 的事件循环

Node.js 的事件循环阶段（简化版）：
```
┌───────────────────────────┐
│   timers (setTimeout)     │
├───────────────────────────┤
│   pending callbacks       │
├───────────────────────────┤
│   idle, prepare           │
├───────────────────────────┤
│   poll (新的 I/O 事件)    │
├───────────────────────────┤
│   check (setImmediate)    │
├───────────────────────────┤
│   close callbacks         │
└───────────────────────────┘
```

Python 的事件循环（简化版）：
```
while True:
    1. 运行准备好的任务
    2. 等待 I/O 事件
    3. 处理完成的 I/O
    4. 重复
```

**关键相似点**：
- ✅ 都是单线程
- ✅ 都用非阻塞 I/O
- ✅ 都在 I/O 等待时切换任务

**关键差异**：
- Node.js 有多个阶段，更复杂
- Python 更简单，一个循环搞定

---

## 问题 3：同步任务如何处理？会阻塞吗？

### ⚠️ 这是最重要的问题！

**答案：同步任务会阻塞整个事件循环！**

---

### 什么是同步任务？

**同步任务 = 阻塞任务 = 不使用 await 的耗时操作**

```python
import asyncio
import time  # ⚠️ 这是同步的！

async def bad_example():
    print("开始")

    # ⚠️ 这是同步的！会阻塞整个事件循环
    time.sleep(3)  # 不是 await asyncio.sleep()

    print("结束")

asyncio.run(bad_example())
```

**问题**：
- `time.sleep(3)` 是同步的
- 它会让**整个事件循环停止 3 秒**
- 在这 3 秒内，其他任务都无法执行

---

### 为什么会阻塞？

让我用图示说明：

#### 正确的异步（非阻塞）
```python
async def good_example():
    print("开始任务 1")
    await asyncio.sleep(2)  # ✅ 异步，不阻塞
    print("任务 1 完成")

async def main():
    # 同时运行两个任务
    await asyncio.gather(
        good_example(),
        good_example()
    )

# 结果：两个任务并发执行，总时间 2 秒
```

**时间线**：
```
任务 1: ───await───→ 完成
任务 2: ───await───→ 完成
总时间: 2 秒（并发）
```

---

#### 错误的同步（阻塞）
```python
import time

def bad_example():  # ⚠️ 不是 async
    print("开始任务 1")
    time.sleep(2)  # ❌ 同步，阻塞！
    print("任务 1 完成")

async def main():
    # 即使在 async 函数中调用
    bad_example()  # ❌ 整个事件循环被阻塞

# 结果：任务串行执行，总时间 4 秒
```

**时间线**：
```
任务 1: ───阻塞整个循环───→ 完成
                        （任务 2 无法开始）
任务 2:                    ───阻塞整个循环───→ 完成
总时间: 4 秒（串行）
```

---

### 同步 vs 异步任务对比

| 特性 | 同步任务 | 异步任务 |
|------|---------|---------|
| **关键字** | 无特殊关键字 | `async` / `await` |
| **是否阻塞** | ✅ 阻塞事件循环 | ❌ 不阻塞 |
| **其他任务** | 无法运行 | 可以并发运行 |
| **示例** | `time.sleep()` | `asyncio.sleep()` |
| **示例** | `requests.get()` | `aiohttp.get()` |

---

### 实际例子：Web 爬虫

#### ❌ 错误：使用同步库
```python
import requests
import asyncio

async def fetch_url(url):
    # ⚠️ requests 是同步的！
    response = requests.get(url)  # 阻塞整个事件循环
    return response.text

async def main():
    urls = ['url1', 'url2', 'url3']

    # 即使用 asyncio.gather，还是串行执行
    results = await asyncio.gather(*[
        fetch_url(url) for url in urls
    ])

# 问题：每个请求都会阻塞，没有并发优势
```

**时间线**：
```
请求 1: ───阻塞───→ 完成
请求 2:            ───阻塞───→ 完成
请求 3:                      ───阻塞───→ 完成
总时间: 15 秒（假设每个 5 秒）
```

---

#### ✅ 正确：使用异步库
```python
import aiohttp
import asyncio

async def fetch_url(session, url):
    # ✅ aiohttp 是异步的
    async with session.get(url) as response:
        return await response.text()

async def main():
    urls = ['url1', 'url2', 'url3']

    async with aiohttp.ClientSession() as session:
        # 真正的并发执行
        results = await asyncio.gather(*[
            fetch_url(session, url) for url in urls
        ])

# 结果：3 个请求同时发出
```

**时间线**：
```
请求 1: ───await───→ 完成
请求 2: ───await───→ 完成
请求 3: ───await───→ 完成
总时间: 5 秒（并发）
```

---

### 混合使用：同步 + 异步

**问题**：如果我必须使用同步库怎么办？

**答案 1：在线程池中运行**（不完美，但可用）
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor
import requests

def sync_fetch(url):
    return requests.get(url).text

async def async_fetch(url):
    loop = asyncio.get_event_loop()

    # 在线程池中运行同步代码
    result = await loop.run_in_executor(
        ThreadPoolExecutor(),
        sync_fetch,
        url
    )
    return result

async def main():
    results = await asyncio.gather(
        async_fetch('url1'),
        async_fetch('url2')
    )

# 这样可以部分并发，但不如纯异步高效
```

**答案 2：直接用异步库**（推荐）
```python
# 找对应的异步库
# requests → aiohttp
# sqlalchemy → asyncpg (PostgreSQL)
# redis → aioredis
# pymongo → motor (MongoDB)
```

---

## 🎯 总结

### 问题 1：asyncio 的作用？
- 管理事件循环
- 提供 async/await 语法
- 提供异步工具集（sleep, gather, queue 等）

### 问题 2：事件循环如何工作？
- 一个永不停止的 while 循环
- 执行任务 → 遇到 await → 暂停 → 等待 I/O → 恢复执行
- 类似 Node.js，但更简单

### 问题 3：同步任务会阻塞吗？
- **会！同步任务会阻塞整个事件循环**
- 必须使用异步库（aiohttp, asyncpg 等）
- 不能在异步代码中直接用 requests、time 等

---

## ⚠️ 核心要点

> **在异步代码中，任何阻塞操作都会阻塞整个事件循环！**

这意味着：
- ❌ `time.sleep()` → 用 `asyncio.sleep()`
- ❌ `requests.get()` → 用 `aiohttp.get()`
- ❌ 长时间计算 → 用 `run_in_executor()` 移到线程池

---

## 📝 验证理解

### 测试 1：找出错误

这段代码有什么问题？

```python
import asyncio
import time

async def task(name):
    print(f"{name} 开始")
    time.sleep(2)  # 同步睡眠
    print(f"{name} 完成")

async def main():
    await asyncio.gather(
        task("A"),
        task("B"),
        task("C")
    )

asyncio.run(main())
```

<details>
<summary>查看答案</summary>

**问题**：`time.sleep(2)` 是同步的，会阻塞事件循环。

**修复**：改用 `await asyncio.sleep(2)`

```python
async def task(name):
    print(f"{name} 开始")
    await asyncio.sleep(2)  # ✅ 异步睡眠
    print(f"{name} 完成")
```

**效果对比**：
- 错误版本：总时间 6 秒（串行）
- 正确版本：总时间 2 秒（并发）
</details>

---

### 测试 2：选择正确的库

你应该用哪个库来发送 HTTP 请求？

A. `requests`
B. `aiohttp`
C. `httpx`（支持同步和异步）

<details>
<summary>查看答案</summary>

**答案**：B 或 C

- ❌ `requests` - 同步库，会阻塞
- ✅ `aiohttp` - 纯异步库
- ✅ `httpx` - 同时支持同步和异步

**在 FastAPI 中推荐**：使用 `httpx.AsyncClient()`
</details>

---

## 🚀 下一步

现在你已经理解了事件循环的机制，让我们进入阶段 0.3：

**编写你的第一个异步程序，对比同步和异步的性能差异！**

准备好了吗？告诉我"准备好了"，我们继续！
