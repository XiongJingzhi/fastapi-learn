# 阶段 0.1: 同步 vs 异步

## 🎯 核心概念（费曼简化版）

### 同步（Synchronous）= 排队等候

想象你在餐厅点餐：

**同步模式**：
1. 你点餐
2. **站在柜台前等**（什么都不做，只是等）
3. 厨师做餐
4. 你拿到餐，离开
5. 下一个人才能开始点餐

**问题**：如果每个人都需要等5分钟，3个人就要等15分钟。

```python
# 同步代码示例
def task(name):
    print(f"{name} 开始")
    time.sleep(5)  # 站在那里等5秒，不能做其他事
    print(f"{name} 完成")

# 执行：任务A → 任务B → 任务C（排队）
task("A")
task("B")
task("C")
# 总时间：5 + 5 + 5 = 15秒
```

### 异步（Asynchronous）= 取号等待

**异步模式**：
1. 你点餐
2. **拿到一个号码牌**（可以去做其他事）
3. 去刷手机、聊天、喝饮料
4. 听到叫号时，去取餐
5. 多个人可以同时点餐，都在等自己的号码

**优势**：3个人几乎同时点餐，都在等，总时间约等于一个人的等待时间。

```python
# 异步代码示例
async def task(name):
    print(f"{name} 开始")
    await asyncio.sleep(5)  # 拿到号码牌，去做其他事
    print(f"{name} 完成")

# 执行：任务A、B、C 同时开始
await asyncio.gather(
    task("A"),
    task("B"),
    task("C")
)
# 总时间：约5秒（并发执行）
```

---

## 🔑 关键字解释

### `async def` - 定义"可暂停"的函数

```python
# 这是一个普通函数（同步）
def normal_function():
    return "结果"

# 这是一个协程函数（异步）
async def async_function():
    return "结果"
```

**区别**：
- 调用 `normal_function()` 立即执行并返回结果
- 调用 `async_function()` 返回一个**协程对象**（像一个"待执行的任务"）

### `await` - "暂停这里，去做其他事"

```python
async def example():
    print("开始")

    # await 的意思是：
    # "这个操作需要等待，但我不会傻等，先去做其他任务"
    await asyncio.sleep(2)

    print("结束")
```

**await 的作用**：
1. 暂停当前函数的执行
2. 让出控制权给事件循环
3. 事件循环可以去执行其他任务
4. 等待的操作完成后，恢复执行

---

## 📊 实际对比

### 同步版本

```python
import time

def download_file(url):
    print(f"开始下载 {url}")
    time.sleep(2)  # 模拟下载，阻塞2秒
    print(f"下载完成 {url}")

start = time.time()
download_file("file1.txt")
download_file("file2.txt")
download_file("file3.txt")
print(f"总耗时: {time.time() - start} 秒")
```

**输出**：
```
开始下载 file1.txt
下载完成 file1.txt
开始下载 file2.txt
下载完成 file2.txt
开始下载 file3.txt
下载完成 file3.txt
总耗时: 6.01 秒
```

### 异步版本

```python
import asyncio

async def download_file(url):
    print(f"开始下载 {url}")
    await asyncio.sleep(2)  # 模拟下载，非阻塞
    print(f"下载完成 {url}")

async def main():
    start = asyncio.get_event_loop().time()

    await asyncio.gather(
        download_file("file1.txt"),
        download_file("file2.txt"),
        download_file("file3.txt"),
    )

    print(f"总耗时: {asyncio.get_event_loop().time() - start} 秒")

asyncio.run(main())
```

**输出**：
```
开始下载 file1.txt
开始下载 file2.txt
开始下载 file3.txt
下载完成 file1.txt
下载完成 file2.txt
下载完成 file3.txt
总耗时: 2.00 秒
```

---

## 💡 核心要点

1. **同步**：一个接一个执行，前一个没完成后一个不能开始
2. **异步**：多个任务可以"同时"进行（并发）
3. **`async def`**：定义可以被暂停的函数
4. **`await`**：暂停当前函数，让出控制权
5. **性能差异**：异步可以将多个IO操作的时间从"相加"变成"取最大值"

---

## 🧪 理解验证

### 问题1：为什么异步版本更快？

**答案**：
- 同步：任务A、B、C 顺序执行，总时间 = A+B+C
- 异步：任务A、B、C 并发执行，总时间 ≈ max(A, B, C)

### 问题2：什么情况下应该用异步？

**答案**：
- ✅ IO密集型：网络请求、数据库查询、文件读写
- ❌ CPU密集型：数据计算、图像处理（用多进程更好）

### 问题3：异步一定比同步快吗？

**答案**：不一定！
- 如果只有一个任务，异步和同步差不多
- 如果是CPU密集型任务，异步没优势
- 异步的优势体现在**多个IO操作并发**时

---

## 📝 记忆口诀

```
同步：一个接一个，排队等
异步：同时进行，拿号等

async def：这是个可以暂停的函数
await：暂停这里，去做别的

异步好在哪里：IO操作并发，时间从相加变成取最大
```

---

## 🚀 下一步

理解了同步和异步的区别后，让我们深入了解：

**下一个主题**：事件循环 - 异步的"引擎"

```bash
python -m app.examples.02_event_loop
```
