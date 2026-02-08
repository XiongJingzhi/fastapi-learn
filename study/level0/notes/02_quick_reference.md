# asyncio 快速参考卡片

> **基于你的 Node.js 背景**

---

## 🎯 核心概念对比

| 概念 | Node.js | Python asyncio |
|------|---------|----------------|
| **异步函数** | `async function()` | `async def func():` |
| **等待异步** | `await promise` | `await coroutine` |
| **并发执行** | `Promise.all([p1, p2])` | `await asyncio.gather(c1, c2)` |
| **延迟执行** | `setTimeout(cb, ms)` | `await asyncio.sleep(sec)` |
| **事件循环** | 隐式（自动运行） | 显式（`asyncio.run()`） |

---

## 📚 常用模式对照表

### 1. 定义异步函数

**Node.js**:
```javascript
async function fetchData() {
    const response = await fetch(url);
    return response.json();
}
```

**Python**:
```python
async def fetch_data():
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
```

---

### 2. 并发执行多个任务

**Node.js**:
```javascript
const results = await Promise.all([
    fetch(url1),
    fetch(url2),
    fetch(url3)
]);
```

**Python**:
```python
results = await asyncio.gather(
    fetch(url1),
    fetch(url2),
    fetch(url3)
)
```

---

### 3. 延迟执行

**Node.js**:
```javascript
await new Promise(r => setTimeout(r, 1000));
```

**Python**:
```python
await asyncio.sleep(1)
```

---

### 4. 创建任务（fire and forget）

**Node.js**:
```javascript
// 不等待完成
fetch(url).catch(console.error);
```

**Python**:
```python
# 不等待完成
task = asyncio.create_task(fetch(url))
# 或者
asyncio.ensure_future(fetch(url))
```

---

## ⚠️ 阻塞 vs 非阻塞

### 阻塞操作（不要用！）

| 操作 | 阻塞版本 | 异步版本 |
|------|---------|---------|
| **睡眠** | `time.sleep()` | `asyncio.sleep()` |
| **HTTP** | `requests.get()` | `aiohttp.get()` |
| **文件** | `open().read()` | `aiofiles.open()` |
| **数据库** | `sqlite3` | `aiosqlite` |

**规则**：在 `async def` 中，**所有** I/O 都要用异步版本！

---

## 🔧 常用 asyncio 函数

```python
import asyncio

# 1. 运行异步程序
asyncio.run(main())

# 2. 并发执行
results = await asyncio.gather(task1(), task2())

# 3. 超时控制
result = await asyncio.wait_for(task(), timeout=5.0)

# 4. 创建任务（不等待）
task = asyncio.create_task(coroutine())

# 5. 等待任意一个完成
done, pending = await asyncio.wait(
    [task1, task2],
    return_when=asyncio.FIRST_COMPLETED
)

# 6. 异步队列
queue = asyncio.Queue()
await queue.put(item)
item = await queue.get()

# 7. 异步锁
lock = asyncio.Lock()
async with lock:
    # 临界区代码
    pass
```

---

## 🐛 常见错误

### 错误 1：在 async 函数中使用同步代码

```python
async def bad():
    time.sleep(1)  # ❌ 阻塞！

async def good():
    await asyncio.sleep(1)  # ✅ 非阻塞
```

### 错误 2：忘记 await

```python
async def bad():
    result = fetch_data()  # ❌ 返回协程对象，不是结果

async def good():
    result = await fetch_data()  # ✅ 等待完成
```

### 错误 3：在同步函数中调用异步

```python
def bad():
    await something()  # ❌ 语法错误

def good():
    asyncio.run(something())  # ✅ 创建新的事件循环
```

### 错误 4：用同步库

```python
async def bad():
    data = requests.get(url)  # ❌ 阻塞

async def good():
    async with aiohttp.ClientSession() as session:
        data = await session.get(url)  # ✅ 非阻塞
```

---

## 📊 性能对比

### 场景：100 个 HTTP 请求

| 方法 | 时间 | 说明 |
|------|------|------|
| **同步（串行）** | ~100 秒 | 一个接一个 |
| **多线程** | ~10 秒 | 受 GIL 限制 |
| **异步（asyncio）** | ~1 秒 | 真正并发 |

---

## 🎯 最佳实践

### 1. 所有 I/O 都用异步
```python
✅ async def process():
✅     data = await fetch_async()
✅     await save_to_db_async(data)

❌ def process():
❌     data = fetch_sync()  # 阻塞
❌     save_to_db_sync(data)  # 阻塞
```

### 2. 最小化 await 之间的同步代码
```python
✅ async def good():
✅     data = await fetch()
✅     result = process(data)  # 快速计算
✅     await save(result)

❌ async def bad():
❌     data = await fetch()
❌     heavy_computation()  # 阻塞！
❌     await save(data)
```

### 3. 使用异步上下文管理器
```python
✅ async with aiohttp.ClientSession() as session:
✅     async with session.get(url) as response:
✅         return await response.text()

❌ session = aiohttp.ClientSession()
❌ response = await session.get(url)
❌ # 忘记关闭 session
```

---

## 🔄 迁移检查清单

从 Node.js 迁移到 Python 时：

- [ ] 把 `async function` 改成 `async def`
- [ ] 把 `Promise.all` 改成 `asyncio.gather`
- [ ] 把 `setTimeout` 改成 `asyncio.sleep`
- [ ] 把 `fetch` 改成 `aiohttp` 或 `httpx.AsyncClient`
- [ ] 添加 `asyncio.run()` 启动事件循环
- [ ] 检查所有 I/O 操作，使用异步版本
- [ ] 移除所有 `time.sleep()`，改用 `await asyncio.sleep()`

---

## 📝 快速测试

**测试你的理解**：

以下代码会输出什么？执行时间多久？

```python
import asyncio

async def foo(n):
    print(f"foo{n} start")
    await asyncio.sleep(n)
    print(f"foo{n} end")

async def bar(n):
    print(f"bar{n} start")
    await asyncio.sleep(n)
    print(f"bar{n} end")

async def main():
    await asyncio.gather(
        foo(2),
        bar(1),
        foo(1)
    )

asyncio.run(main())
```

<details>
<summary>查看答案</summary>

**输出**：
```
foo2 start
bar1 start
foo1 start
bar1 end      # 1 秒后
foo1 end      # 1 秒后
foo2 end      # 2 秒后
```

**总时间**：2 秒

**原因**：
- 所有任务几乎同时开始
- bar(1) 和 foo(1) 在 1 秒后完成
- foo(2) 在 2 秒后完成
- 最长的任务决定总时间
</details>

---

## 🚀 下一步

现在你可以：
1. ✅ 理解 asyncio 的基本概念
2. ✅ 知道如何避免阻塞
3. ✅ 掌握常用模式

**接下来**：编写你的第一个异步程序！

---

**记住**：asyncio 和 Node.js 的异步模型非常相似，只要你理解了事件循环，迁移就很容易！
