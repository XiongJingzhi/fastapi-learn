# Level 0 基础练习题

## 🎯 练习目标

通过实际编写代码，巩固 Level 0 学到的异步编程基础知识。

---

## 练习1: 同步 vs 异步

### 题目

编写一个程序，比较同步和异步下载3个文件的性能差异。

### 要求

1. 创建一个同步版本的下载函数 `download_file_sync()`
2. 创建一个异步版本的下载函数 `download_file_async()`
3. 分别测量并打印两种方式的总耗时
4. 解释为什么异步版本更快

### 提示

```python
import asyncio
import time

# 你的代码在这里

def main():
    print("同步版本：")
    # 运行同步版本

    print("\n异步版本：")
    # 运行异步版本

if __name__ == "__main__":
    main()
```

### 预期输出

```
同步版本：
开始下载 file1.txt...
下载完成 file1.txt，耗时 1.00秒
开始下载 file2.txt...
下载完成 file2.txt，耗时 1.00秒
开始下载 file3.txt...
下载完成 file3.txt，耗时 1.00秒
总耗时: 3.01秒

异步版本：
开始下载 file1.txt...
开始下载 file2.txt...
开始下载 file3.txt...
下载完成 file1.txt，耗时 1.00秒
下载完成 file2.txt，耗时 1.00秒
下载完成 file3.txt，耗时 1.00秒
总耗时: 1.01秒
```

---

## 练习2: 使用 asyncio.gather()

### 题目

编写一个程序，使用 `asyncio.gather()` 并发获取3个用户的信息。

### 要求

1. 创建 `fetch_user(user_id)` 异步函数，模拟获取用户信息
2. 使用 `asyncio.gather()` 并发获取 user_id 为 1, 2, 3 的用户
3. 打印所有用户信息
4. 测量总耗时

### 提示

```python
import asyncio
import time

async def fetch_user(user_id: int) -> dict:
    """模拟获取用户信息"""
    await asyncio.sleep(1)  # 模拟网络请求
    return {
        "user_id": user_id,
        "name": f"User{user_id}",
        "email": f"user{user_id}@example.com"
    }

async def main():
    # 你的代码在这里

if __name__ == "__main__":
    asyncio.run(main())
```

### 预期输出

```
开始获取用户信息...
所有用户获取完成！
用户1: {'user_id': 1, 'name': 'User1', 'email': 'user1@example.com'}
用户2: {'user_id': 2, 'name': 'User2', 'email': 'user2@example.com'}
用户3: {'user_id': 3, 'name': 'User3', 'email': 'user3@example.com'}
总耗时: 1.01秒
```

---

## 练习3: 创建和使用任务

### 题目

编写一个程序，使用 `asyncio.create_task()` 手动管理任务。

### 要求

1. 创建3个异步任务，分别模拟不同的操作（下载、上传、处理）
2. 使用 `asyncio.create_task()` 创建任务
3. 打印每个任务的开始和结束时间
4. 等待所有任务完成

### 提示

```python
import asyncio
import time

async def download():
    print(f"[{time.strftime('%H:%M:%S')}] 开始下载...")
    await asyncio.sleep(2)
    print(f"[{time.strftime('%H:%M:%S')}] 下载完成")

async def upload():
    print(f"[{time.strftime('%H:%M:%S')}] 开始上传...")
    await asyncio.sleep(1)
    print(f"[{time.strftime('%H:%M:%S')}] 上传完成")

async def process():
    print(f"[{time.strftime('%H:%M:%S')}] 开始处理...")
    await asyncio.sleep(1.5)
    print(f"[{time.strftime('%H:%M:%S')}] 处理完成")

async def main():
    # 你的代码在这里

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 练习4: 识别阻塞操作

### 题目

找出下面代码中的阻塞操作，并修复它们。

### 问题代码

```python
import asyncio
import time
import requests

async def fetch_data(url):
    """获取数据"""
    response = requests.get(url)  # ❌ 阻塞
    return response.json()

async def process_data(data):
    """处理数据"""
    time.sleep(1)  # ❌ 阻塞
    return {"processed": data}

async def main():
    data = await fetch_data("https://api.example.com/data")
    result = await process_data(data)
    print(result)

asyncio.run(main())
```

### 要求

1. 识别所有的阻塞操作
2. 将它们替换为非阻塞的版本
3. 解释为什么这样修改

### 修复后的代码框架

```python
import asyncio
import httpx  # 使用异步的HTTP库

async def fetch_data(url):
    """获取数据（非阻塞）"""
    # 你的代码

async def process_data(data):
    """处理数据（非阻塞）"""
    # 你的代码

async def main():
    # 你的代码

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 练习5: 错误处理

### 题目

编写一个程序，正确处理异步任务中的错误。

### 要求

1. 创建3个异步任务，其中第2个任务会抛出异常
2. 使用 `return_exceptions=True` 让所有任务都能完成
3. 检查哪些任务成功，哪些失败
4. 打印结果和错误信息

### 提示

```python
import asyncio

async def task_a():
    await asyncio.sleep(0.1)
    return "任务A成功"

async def task_b():
    await asyncio.sleep(0.1)
    raise ValueError("任务B失败")

async def task_c():
    await asyncio.sleep(0.1)
    return "任务C成功"

async def main():
    # 使用 return_exceptions=True
    results = await asyncio.gather(
        task_a(),
        task_b(),
        task_c(),
        return_exceptions=True  # 关键参数
    )

    # 你的代码：检查结果

if __name__ == "__main__":
    asyncio.run(main())
```

### 预期输出

```
任务A成功: 任务A成功
任务B失败: 任务B失败
任务C成功: 任务C成功
```

---

## 练习6: 综合应用

### 题目

编写一个简单的异步批量处理程序。

### 场景

你需要处理100个订单：
1. 从数据库获取订单信息
2. 调用支付网关验证支付
3. 更新订单状态

### 要求

1. 创建异步函数模拟数据库查询
2. 创建异步函数模拟支付验证
3. 并发处理10个订单（使用 Semaphore 限制并发数）
4. 打印处理进度和总耗时

### 提示

```python
import asyncio
import time

async def fetch_order(order_id: int) -> dict:
    """从数据库获取订单"""
    await asyncio.sleep(0.1)  # 模拟数据库查询
    return {
        "order_id": order_id,
        "amount": order_id * 100,
        "status": "pending"
    }

async def verify_payment(order: dict) -> bool:
    """验证支付"""
    await asyncio.sleep(0.2)  # 模拟支付网关调用
    return order["amount"] > 0

async def update_order(order: dict, payment_verified: bool):
    """更新订单状态"""
    await asyncio.sleep(0.05)  # 模拟数据库更新
    order["status"] = "verified" if payment_verified else "failed"

async def process_order(order_id: int, semaphore: asyncio.Semaphore):
    """处理单个订单"""
    async with semaphore:  # 限制并发数
        # 你的代码

async def main():
    order_ids = list(range(1, 101))  # 100个订单
    semaphore = asyncio.Semaphore(10)  # 最多10个并发

    # 你的代码

if __name__ == "__main__":
    asyncio.run(main())
```

---

## ✅ 检查清单

完成所有练习后，检查你是否能够：

- [ ] 编写和使用异步函数
- [ ] 使用 `asyncio.gather()` 并发执行多个任务
- [ ] 使用 `asyncio.create_task()` 手动创建任务
- [ ] 识别和避免阻塞操作
- [ ] 正确处理异步任务中的错误
- [ ] 使用 Semaphore 限制并发数
- [ ] 解释异步代码的性能优势

---

## 💡 学习建议

1. **先理解，再编码**
   - 确保理解每个练习的目标
   - 思考需要用到哪些概念

2. **先运行，再优化**
   - 先让代码跑起来
   - 再考虑优化和改进

3. **添加打印语句**
   - 观察执行顺序
   - 理解并发行为

4. **测试边界情况**
   - 空列表
   - 单个任务
   - 失败的任务

5. **记录你的发现**
   - 哪些容易理解
   - 哪些比较困难
   - 有什么疑问

---

**祝你练习愉快！记住：实践是最好的学习方式！** 🚀
