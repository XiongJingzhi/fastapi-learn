# 阶段 0.2: 事件循环 - 异步的"引擎"

## 🎯 核心概念（费曼简化版）

### 事件循环 = 一个超级高效的任务调度员

想象一个餐厅：

**事件循环** = 餐厅经理
- 📋 维护一个任务列表（谁在等餐）
- 🔄 不断检查任务状态（谁的餐好了）
- 📢 通知任务继续（叫号取餐）
- ⚡ 从不休息，一直循环（直到餐厅关门）

### 工作流程

```
┌─────────────────────────────────────┐
│         事件循环（Event Loop）         │
│                                     │
│  1. 查看任务列表                     │
│  2. 执行一个任务直到遇到 await       │
│  3. 任务暂停，记录"待办"             │
│  4. 切换到下一个任务                 │
│  5. 重复 1-4                        │
│  6. 所有任务完成后退出                │
└─────────────────────────────────────┘
```

---

## 🔑 关键概念

### 协程（Coroutine）

```python
async def my_function():
    return "结果"

# 调用协程函数
result = my_function()
print(type(result))  # <class 'coroutine'>
```

**协程是什么**：
- 一个"待执行的任务"
- 不会立即运行
- 需要被事件循环调度

**类比**：
- 协程 = 一个还没下锅的菜谱
- 事件循环 = 厨师
- await = 等待食材准备好

### 事件循环（Event Loop）

```python
# 创建事件循环并运行协程
asyncio.run(my_coroutine())
```

**事件循环做什么**：
1. 管理所有待执行的协程
2. 在遇到 `await` 时切换任务
3. 处理完成后的回调
4. 管理超时和异常

### await 的真面目

```python
async def example():
    print("步骤1")

    # await 做了什么：
    # 1. 暂停当前协程
    # 2. 把控制权还给事件循环
    # 3. 事件循环去执行其他任务
    # 4. 等待的操作完成后，恢复这里
    await asyncio.sleep(1)

    print("步骤2")
```

**await 的本质**：
- 不是一个普通的函数调用
- 是一个"暂停点"
- 允许事件循环切换到其他任务

---

## 📊 执行流程示例

```python
import asyncio

async def task(name, duration):
    print(f"[{name}] 开始")
    await asyncio.sleep(duration)
    print(f"[{name}] 完成")

async def main():
    print("=== 开始 ===")

    # 创建三个协程（还没运行）
    coro1 = task("A", 0.1)
    coro2 = task("B", 0.1)
    coro3 = task("C", 0.1)

    # 将协程包装成任务，加入事件循环
    task1 = asyncio.create_task(coro1)
    task2 = asyncio.create_task(coro2)
    task3 = asyncio.create_task(coro3)

    # 等待所有任务完成
    await asyncio.gather(task1, task2, task3)

    print("=== 结束 ===")

asyncio.run(main())
```

**执行过程**：

```
时间线：
0.000s === 开始 ===
0.001s [A] 开始     ← 任务A开始执行
0.002s [A] await    ← 任务A遇到await，暂停
0.003s [B] 开始     ← 事件循环切换到任务B
0.004s [B] await    ← 任务B遇到await，暂停
0.005s [C] 开始     ← 事件循环切换到任务C
0.006s [C] await    ← 任务C遇到await，暂停
        ... 事件循环等待，所有任务都在sleep ...
0.101s [A] 完成     ← 任务A的sleep完成，恢复执行
0.102s [B] 完成     ← 任务B的sleep完成，恢复执行
0.103s [C] 完成     ← 任务C的sleep完成，恢复执行
0.104s === 结束 ===
```

---

## 💡 核心要点

### 1. 事件循环是单线程的

```python
# 即使是"并发"，也是在同一个线程中
# 只是通过"切换"来模拟并发

async def task1():
    while True:
        print("任务1")
        await asyncio.sleep(0.001)  # 让出控制权

async def task2():
    while True:
        print("任务2")
        await asyncio.sleep(0.001)  # 让出控制权

# 这两个任务会交替执行，但都在同一个线程
```

### 2. await 必须在 async 函数中

```python
# ❌ 错误
def normal_function():
    await asyncio.sleep(1)  # SyntaxError

# ✅ 正确
async def async_function():
    await asyncio.sleep(1)
```

### 3. 协程需要被调度

```python
async def my_task():
    print("执行中")

# ❌ 错误：协程被创建但从未执行
coro = my_task()  # 什么都不会发生

# ✅ 正确：使用 asyncio.run
asyncio.run(my_task())

# ✅ 正确：使用 asyncio.gather
await asyncio.gather(my_task())
```

---

## 🧪 理解验证

### 问题1：为什么叫"事件循环"？

**答案**：
- **事件**：IO完成、定时器到期、任务完成等都是"事件"
- **循环**：不断重复"检查事件 → 处理事件"的过程

### 问题2：事件循环是多线程的吗？

**答案**：
- ❌ 不是！事件循环本身是单线程的
- ✅ 通过"快速切换"来模拟并发
- ✅ 真正的并行需要多进程（multiprocessing）

### 问题3：如果不 await 会怎样？

**答案**：
```python
async def bad_example():
    my_task()  # ❌ 忘记 await
    # 问题：my_task 被创建但从未执行！
```

---

## 📝 记忆口诀

```
事件循环：像个忙碌的经理，不断检查任务列表
协程：待执行的任务，需要经理调度
await：暂停点，让经理去做别的任务
asyncio.run：启动经理（事件循环）
create_task：把任务加入经理的列表
gather：等一组任务都完成
```

---

## 🔍 深入理解

### 事件循环的生命周期

```python
# 1. 创建事件循环
loop = asyncio.new_event_loop()

# 2. 设置为当前事件循环
asyncio.set_event_loop(loop)

# 3. 运行协程
loop.run_until_complete(my_coroutine())

# 4. 关闭循环
loop.close()
```

### 实际上 asyncio.run() 做了什么

```python
# asyncio.run(my_coroutine())
# 等价于：

loop = asyncio.new_event_loop()
try:
    loop.run_until_complete(my_coroutine())
finally:
    loop.close()
```

---

## 🚀 下一步

理解了事件循环后，让我们学习如何高效地并发执行多个任务：

**下一个主题**：并发执行 - 让任务真正"同时"运行

```bash
python -m app.examples.03_concurrency
```
