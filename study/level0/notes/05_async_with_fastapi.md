# 阶段 0.5: FastAPI 中的异步 - 理论到实践

## 🎯 核心概念（费曼简化版）

### FastAPI 如何处理请求

想象一个餐厅：

**同步模式（传统框架）**：
- 每个服务员（线程）服务一桌客人
- 如果需要等待厨房，服务员就站在那里等
- 10个服务员 = 最多服务10桌客人

**异步模式（FastAPI）**：
- 所有服务员共享一个队伍
- 点餐后，服务员立即去服务下一桌
- 厨房准备好后，通过叫号通知
- 1个服务员可以同时服务很多桌客人

---

## 🔑 核心概念

### 1. 何时使用 async def

```python
from fastapi import FastAPI
import asyncio

app = FastAPI()

# ✅ 使用 async def：endpoint 中有 IO 操作
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    # 模拟数据库查询
    await asyncio.sleep(0.1)  # 数据库IO
    return {"user_id": user_id, "name": "Alice"}
```

**使用 async def 的场景**：
- 需要查询数据库
- 需要调用外部API
- 需要读写文件
- 需要 `await` 任何异步操作

### 2. 何时使用 def

```python
from fastapi import FastAPI

app = FastAPI()

# ✅ 使用 def：endpoint 只是简单计算
@app.get("/add")
def add_numbers(a: int, b: int):
    # 简单的CPU计算，不需要IO
    result = a + b
    return {"result": result}

# ✅ 使用 def：必须使用同步库
@app.get("/process-image")
def process_image():
    # 图像处理库是同步的，没有异步版本
    from PIL import Image
    img = Image.open("image.jpg")
    img.rotate(45).save("rotated.jpg")
    return {"status": "ok"}
```

**使用 def 的场景**：
- 非常快的操作（< 10ms）
- 简单的计算或逻辑
- 必须使用没有异步版本的库

### 3. FastAPI 的并发处理

```python
from fastapi import FastAPI
import asyncio

app = FastAPI()

@app.get("/slow")
async def slow_endpoint():
    """模拟一个慢操作"""
    await asyncio.sleep(5)
    return {"message": "完成"}

# FastAPI 可以同时处理多个这样的请求
# 因为它们是异步的，不会互相阻塞
```

**FastAPI 如何工作**：
1. 收到请求A → 启动 endpoint A
2. endpoint A 遇到 await → 暂停
3. 收到请求B → 启动 endpoint B
4. endpoint B 遇到 await → 暂停
5. 收到请求C → 启动 endpoint C
6. ...
7. endpoint A 的等待完成 → 恢复执行
8. endpoint A 返回响应

**关键**：
- 单个请求内的多个操作可以并发
- 多个请求可以并发处理
- 不需要为每个请求创建线程

---

## 📊 实际示例

### 示例1：并发调用多个API

```python
from fastapi import FastAPI, HTTPException
import httpx

app = FastAPI()

async def fetch_github_user(username: str):
    """调用 GitHub API"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.github.com/users/{username}")
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="User not found")
        return response.json()

@app.get("/users/{username}")
async def get_user(username: str):
    """获取用户信息"""
    user = await fetch_github_user(username)
    return {
        "login": user["login"],
        "name": user["name"],
        "followers": user["followers"],
    }

@app.get("/users")
async def get_multiple_users(usernames: str):
    """获取多个用户的信息（并发）"""
    username_list = usernames.split(",")

    # 并发调用多个 API
    users = await asyncio.gather(
        *[fetch_github_user(name) for name in username_list]
    )

    return {"users": users}
```

### 示例2：异步依赖注入

```python
from fastapi import FastAPI, Depends
import asyncio

app = FastAPI()

async def get_db():
    """异步依赖：获取数据库连接"""
    # 模拟连接数据库
    await asyncio.sleep(0.1)
    return {"connection": "active"}

async def get_current_user(db: dict = Depends(get_db)):
    """异步依赖：获取当前用户"""
    # 模拟查询用户
    await asyncio.sleep(0.1)
    return {"user_id": 1, "name": "Alice"}

@app.get("/profile")
async def get_profile(user: dict = Depends(get_current_user)):
    """使用异步依赖"""
    return {
        "user": user,
        "message": "Profile fetched"
    }
```

**依赖注入的工作原理**：
```python
# 请求到达 /profile
# ↓
# FastAPI 调用 get_db()
# ↓
# await asyncio.sleep(0.1) - 可以处理其他请求
# ↓
# get_db() 返回 db
# ↓
# FastAPI 调用 get_current_user(db)
# ↓
# await asyncio.sleep(0.1) - 可以处理其他请求
# ↓
# get_current_user() 返回 user
# ↓
# FastAPI 调用 get_profile(user)
# ↓
# 返回响应
```

### 示例3：Background Tasks

```python
from fastapi import FastAPI, BackgroundTasks
import time

app = FastAPI()

def send_email(email: str, message: str):
    """发送邮件（同步函数）"""
    time.sleep(2)  # 模拟发送邮件的耗时
    print(f"邮件已发送到 {email}: {message}")

@app.post("/notify")
async def send_notification(
    email: str,
    message: str,
    background_tasks: BackgroundTasks
):
    """
    发送通知

    使用 BackgroundTasks：
    - 响应立即返回
    - 邮件在后台发送
    - 不阻塞请求
    """
    background_tasks.add_task(send_email, email, message)

    return {
        "message": "通知已加入队列",
        "email": email
    }
```

**BackgroundTasks 的特点**：
- ✅ 不阻塞请求
- ✅ 在响应返回后执行
- ✅ 适合轻量级后台任务
- ❌ 不适合需要可靠性的任务（应用重启会丢失）

### 示例4：流式响应

```python
from fastapi import FastAPI
import asyncio

app = FastAPI()

@app.get("/stream")
async def stream_data():
    """
    流式响应（Server-Sent Events）

    适用场景：
    - 实时数据推送
    - 大文件传输
    - 进度更新
    """
    async def generate():
        for i in range(10):
            await asyncio.sleep(1)
            yield f"data: 消息 {i}\n\n"

    return generate()
```

---

## 💡 性能优化建议

### 1. 使用异步的数据库驱动

```python
# ❌ 错误：使用同步的 sqlalchemy
from sqlalchemy import create_engine
engine = create_engine("postgresql://...")

# ✅ 正确：使用异步的数据库驱动
from sqlalchemy.ext.asyncio import create_async_engine
engine = create_async_engine("postgresql+asyncpg://...")
```

### 2. 使用异步的HTTP客户端

```python
# ❌ 错误：使用同步的 requests
import requests
response = requests.get("https://api.example.com")

# ✅ 正确：使用异步的 httpx
import httpx
async with httpx.AsyncClient() as client:
    response = await client.get("https://api.example.com")
```

### 3. 并发执行独立的IO操作

```python
@app.get("/dashboard")
async def dashboard(user_id: int):
    """仪表板：需要获取多种数据"""

    # ✅ 并发获取所有数据
    profile, orders, notifications = await asyncio.gather(
        fetch_user_profile(user_id),
        fetch_user_orders(user_id),
        fetch_user_notifications(user_id),
    )

    return {
        "profile": profile,
        "orders": orders,
        "notifications": notifications,
    }
```

### 4. 避免在 endpoint 中写业务逻辑

```python
# ❌ 错误：业务逻辑写在 endpoint 中
@app.post("/users")
async def create_user(user: UserCreate):
    # 验证
    if not user.email:
        raise HTTPException(400, "Email required")

    # 处理
    user_data = user.model_dump()
    user_data["hashed_password"] = hash_password(user.password)

    # 保存
    new_user = await db.users.insert(user_data)

    return new_user

# ✅ 正确：业务逻辑在服务层
@app.post("/users")
async def create_user(user: UserCreate, user_service: UserService = Depends()):
    """endpoint 只处理HTTP协议相关的事务"""
    # 参数校验
    # 调用服务层
    # 返回响应
    return await user_service.create_user(user)
```

---

## 🧪 理解验证

### 问题1：FastAPI 的并发是怎么实现的？

**答案**：
- FastAPI 基于 Starlette（异步框架）
- 使用事件循环处理多个请求
- 单个请求遇到 await 时，可以处理其他请求
- 不需要为每个请求创建线程

### 问题2：什么时候用 async def，什么时候用 def？

**答案**：
- **async def**：有 IO 操作（数据库、API、文件）
- **def**：纯计算或必须使用同步库
- **如果不确定**：用 async def（FastAPI 会优化）

### 问题3：BackgroundTasks 和异步操作有什么区别？

**答案**：
- **异步操作（await）**：等待完成后返回响应
- **BackgroundTasks**：立即返回响应，后台执行

---

## 📝 记忆口诀

```
async def：有IO操作就用
def：纯计算或必须用同步库

FastAPI 并发：事件循环 + await
一个请求等待，处理其他请求

依赖注入：也可以是异步的
BackgroundTasks：不阻塞响应

记住：endpoint 只处理协议，业务逻辑在服务层
```

---

## 🎓 Level 0 总结

恭喜你完成了 Level 0 的学习！

### 你已经掌握了：

1. ✅ 同步 vs 异步的执行模式
2. ✅ 事件循环的工作原理
3. ✅ 并发执行的优势和工具
4. ✅ 阻塞操作的识别和避免
5. ✅ FastAPI 中的异步应用

### 下一步：Level 1

**Level 1: FastAPI 作为协议适配层**

你将学习：
- 请求参数校验（Query / Path / Body / Header / Cookie）
- 响应处理（JSON / 文件 / Streaming / WebSocket）
- 统一响应格式与错误模型
- HTTP 状态码与语义

**核心约束**：不在 endpoint 中写业务逻辑

---

**准备好进入 Level 1 了吗？** 🚀
