# 阶段 0.3: 并发执行 - 让任务真正"同时"运行

## 🎯 核心概念（费曼简化版）

### 并发（Concurrency）= 一个CPU，快速切换

想象一个厨师同时做3道菜：

**并发模式**：
1. 开始做菜A（切菜）
2. 菜A需要炖煮10分钟 → **切换到菜B**
3. 开始做菜B（切菜）
4. 菜B需要炖煮10分钟 → **切换到菜C**
5. 开始做菜C（切菜）
6. 菜C需要炖煮10分钟 → **检查菜A**
7. 菜A好了 → 继续菜A
8. ...

**关键**：不是真的"同时"，而是通过切换来"看起来同时"

**时间对比**：
- 顺序：30分钟（10+10+10）
- 并发：约12分钟（因为有等待时间可以利用）

---

## 🔑 并发工具

### 1. asyncio.gather() - 最常用的并发方式

```python
import asyncio

async def task(name, duration):
    print(f"{name} 开始")
    await asyncio.sleep(duration)
    print(f"{name} 完成")
    return f"{name}的结果"

async def main():
    # 同时启动3个任务，等待全部完成
    results = await asyncio.gather(
        task("A", 2),
        task("B", 2),
        task("C", 2),
    )

    print(results)  # ['A的结果', 'B的结果', 'C的结果']

asyncio.run(main())
```

**gather() 的特点**：
- ✅ 同时启动所有任务
- ✅ 等待所有任务完成
- ✅ 按传入顺序返回结果
- ✅ 任何一个任务失败，会立即取消其他任务（除非 `return_exceptions=True`）

### 2. asyncio.create_task() - 手动创建任务

```python
async def main():
    # 创建任务（立即开始执行）
    task1 = asyncio.create_task(task("A", 2))
    task2 = asyncio.create_task(task("B", 2))
    task3 = asyncio.create_task(task("C", 2))

    # 此时3个任务都在运行，我们可以做其他事
    print("任务都已启动，正在运行...")

    # 等待所有任务完成
    await asyncio.gather(task1, task2, task3)

asyncio.run(main())
```

**create_task() 的特点**：
- ✅ 立即调度任务执行
- ✅ 返回一个 Task 对象
- ✅ 可以在之后等待
- ✅ 更灵活，可以手动管理任务生命周期

### 3. asyncio.TaskGroup() - Python 3.11+ 推荐

```python
async def main():
    # TaskGroup 自动管理任务
    async with asyncio.TaskGroup() as tg:
        task1 = tg.create_task(task("A", 2))
        task2 = tg.create_task(task("B", 2))
        task3 = tg.create_task(task("C", 2))

    # 退出 with 块时，所有任务都已完成

asyncio.run(main())
```

**TaskGroup 的特点**：
- ✅ 自动等待所有任务完成
- ✅ 自动处理异常
- ✅ 更安全的并发管理
- ⚠️ 需要 Python 3.11+

---

## 📊 并发 vs 顺序

### 顺序执行

```python
async def sequential():
    start = time.time()

    result1 = await fetch_data("api1")
    result2 = await fetch_data("api2")
    result3 = await fetch_data("api3")

    # 时间：1s + 1s + 1s = 3s
```

### 并发执行

```python
async def concurrent():
    start = time.time()

    results = await asyncio.gather(
        fetch_data("api1"),
        fetch_data("api2"),
        fetch_data("api3"),
    )

    # 时间：约1s（3个请求同时发出）
```

---

## 💡 实际应用场景

### 场景1：并发调用多个API

```python
import httpx

async def fetch_user(user_id: int):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"/api/users/{user_id}")
        return response.json()

async def main():
    # 并发获取多个用户信息
    users = await asyncio.gather(
        fetch_user(1),
        fetch_user(2),
        fetch_user(3),
        fetch_user(4),
        fetch_user(5),
    )

    print(users)

asyncio.run(main())
```

### 场景2：并发查询数据库

```python
async def get_user_orders(user_id: int):
    async with database.transaction():
        orders = await database.fetch_all(
            "SELECT * FROM orders WHERE user_id = $1",
            user_id
        )
        return orders

async def get_user_profile(user_id: int):
    async with database.transaction():
        profile = await database.fetch_one(
            "SELECT * FROM profiles WHERE user_id = $1",
            user_id
        )
        return profile

async def get_user_data(user_id: int):
    # 并发获取订单和个人资料
    orders, profile = await asyncio.gather(
        get_user_orders(user_id),
        get_user_profile(user_id),
    )

    return {"orders": orders, "profile": profile}
```

### 场景3：批量处理

```python
async def process_item(item_id: int):
    # 模拟处理单个项目
    await asyncio.sleep(0.1)
    return f"项目{item_id}已处理"

async def process_batch(item_ids: list[int]):
    # 并发处理一批项目
    results = await asyncio.gather(
        *[process_item(id) for id in item_ids]
    )
    return results

# 使用
async def main():
    item_ids = list(range(100))  # 100个项目
    results = await process_batch(item_ids)
    # 时间：约0.1秒（而不是10秒）

asyncio.run(main())
```

---

## 🎯 何时使用并发

### ✅ 适合并发

1. **多个独立的IO操作**
   - 调用多个API
   - 查询多个数据库表
   - 读写多个文件

2. **任务之间没有依赖**
   - 获取用户信息和获取用户订单
   - 处理队列中的多个任务

3. **IO密集型**
   - 大量等待时间
   - 网络请求、数据库操作

### ❌ 不适合并发

1. **任务有依赖关系**
   ```python
   # ❌ 不能并发
   user_id = await create_user(data)
   orders = await get_orders(user_id)  # 需要 user_id
   ```

2. **CPU密集型**
   - 数据计算
   - 图像处理
   - 应该用多进程（multiprocessing）

3. **需要严格顺序**
   - 事务操作
   - 有先后逻辑要求的业务

---

## 🧪 理解验证

### 问题1：gather() 和 create_task() 有什么区别？

**答案**：
- `gather()`: 一次性启动多个任务，简单直接
- `create_task()`: 更灵活，可以手动控制任务生命周期

### 问题2：并发会更快吗？

**答案**：
- ✅ 多个IO操作并发 → 是的
- ✅ IO等待时间长 → 是的
- ❌ CPU密集型 → 不是（应该用多进程）
- ❌ 单个任务 → 不是（没有并发优势）

### 问题3：如何控制并发数量？

**答案**：
```python
import asyncio

async def process_with_limit(items, limit=10):
    semaphore = asyncio.Semaphore(limit)

    async def process(item):
        async with semaphore:
            return await process_item(item)

    results = await asyncio.gather(
        *[process(item) for item in items]
    )
    return results
```

---

## 📝 记忆口诀

```
gather：同时启动多个任务，简单直接
create_task：手动创建任务，更灵活
TaskGroup：自动管理任务，更安全（Python 3.11+）

并发适用：多个IO操作，无依赖
并发不适用：CPU密集，有依赖

记住：并发不是并行，是快速切换
```

---

## 🚀 下一步

学会了并发执行，让我们了解异步编程的最大陷阱：

**下一个主题**：阻塞操作 - 异步编程的"敌人"

```bash
python -m app.examples.04_blocking_operations
```
