# 02. 响应处理 - Response Handling

## 📍 在架构中的位置

**传输层 (Transport Layer)** - 继续在 FastAPI 的领地！

```
┌─────────────┐
│   客户端    │  ← 期待收到 HTTP 响应
└─────────────┘
      ▲
      │
┌─────────────────────────────┐
│      【传输层 / FastAPI】    │
│                             │
│  1️⃣ 接收请求                  │
│  2️⃣ 校验参数  ← 上节课学习      │
│  3️⃣ 调用服务层                │
│  4️⃣ 返回响应  ← 你在这里学习   │
└─────────────────────────────┘
      ▲
      │
┌─────────────┐
│  服务层     │  ← 返回业务结果
└─────────────┘
```

**🎯 你的学习目标**：掌握"协议适配"的最后一步 —— 把 Python 对象转换成 HTTP 响应。

**⚠️ 架构约束**：响应处理只负责**格式化输出**，不包含业务逻辑。

---

## 🎯 什么是响应处理？

继续我们的餐厅类比：

**上节课学的是**：顾客如何点菜（请求校验）- 传输层输入
**这节课学的是**：服务员如何上菜并给账单（响应处理）- 传输层输出

### 餐厅账单的类比

想象你在餐厅用餐后的三个场景：

**场景 1：简单账单**（JSON 响应）
```
服务员递给你一张纸：
"总计：¥128"
```

**场景 2：详细账单**（结构化 JSON）
```
菜品      数量   单价   小计
宫保鸡丁   1     ¥38    ¥38
米饭      2     ¥2     ¥4
汤        1     ¥18    ¥18
------------------------
总计：¥60
```

**场景 3：下载菜单文件**（文件响应）
```
服务员：这是我们店的完整菜单，可以带回家
（递给你一个 PDF 文件）
```

**场景 4：边做边上菜**（流式响应）
```
服务员：大菜需要等一会儿，我先给您上开胃菜...
然后上汤...
然后是主菜...
（一道一道地上）
```

在 FastAPI 中，**响应处理**就是"服务员给顾客账单"这个过程——把服务器处理结果以合适的方式返回给客户端。

**架构视角**：响应处理是传输层的另一核心职责 —— **协议适配的最后一步**。

---

## 💡 架构提示：响应处理的职责边界

### 传输层应该/不应该做的事

```
┌─────────────────────────────────────────┐
│  ❌ 不在传输层做的事（Level 1 禁止）      │
│  - 业务逻辑转换（如"计算订单总价"）       │
│  - 数据处理（如"数据统计分析"）          │
│  - 数据库查询                            │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  ✅ 在传输层做的事（Level 1 学习）        │
│  - 数据格式转换（Python 对象 → JSON）    │
│  - 字段过滤（如"隐藏密码字段"）          │
│  - 响应格式化（如"添加元数据"）          │
│  - 状态码设置（如"201 Created"）        │
└─────────────────────────────────────────┘
```

**为什么这样区分？**

```python
# ❌ 错误示例：在 endpoint 中做业务逻辑
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    user = db.query("SELECT * FROM users WHERE id = ?", user_id)
    # 问题1: 直接操作数据库（应该在 Service/Repository 层）
    # 问题2: 业务逻辑混在 HTTP 层

    # 在 endpoint 中计算
    user["full_name"] = f"{user['first_name']} {user['last_name']}"
    # 问题3: 数据转换应该在 Service 层

    return user

# ✅ 正确示例：endpoint 只做协议适配
@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    service: UserService = Depends()  # Level 2 学习
):
    # Endpoint 只负责：调用服务 → 过滤字段 → 返回
    return await service.get_user(user_id)
    # response_model 自动过滤敏感字段
```

---

## 🤔 为什么响应处理很重要？

### 真实世界的问题

假设你有一个获取用户信息的接口：

**不好的响应设计**：
```json
{
  "status": "success",
  "data": {
    "user": {
      "id": 123,
      "name": "Alice"
    },
    "timestamp": "2024-01-15T10:30:00Z"
  },
  "code": 200,
  "message": "User retrieved successfully"
}
```

问题：每次都要解析 `data.user`，太啰嗦了！

**好的响应设计**：
```json
{
  "id": 123,
  "name": "Alice",
  "email": "alice@example.com",
  "created_at": "2024-01-10T08:00:00Z"
}
```

清晰、直接、易用！

### 三大好处

1. **一致性**：所有接口返回相同格式的数据
2. **可预测性**：前端开发者知道每个字段的意思
3. **自文档化**：响应结构本身就是最好的文档

**架构价值**：良好的响应设计让**传输层保持轻量**，业务逻辑集中在 Service 层。

---

## 📦 FastAPI 的四种响应类型

### 类型 1：基本 JSON 响应

**类比**：简单账单

**最简单的情况**：
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/hello")
async def say_hello():
    return {"message": "Hello, World!"}
    # FastAPI 自动转换为 JSON，并设置 Content-Type: application/json
```

**自动类型转换**：
```python
@app.get("/items/{item_id}")
async def get_item(item_id: int):
    # FastAPI 自动把这些转换为 JSON
    return {
        "id": item_id,
        "name": "Laptop",
        "price": 999.99,
        "in_stock": True,
        "tags": ["electronics", "computers"],
        "specs": {
            "cpu": "Intel i7",
            "ram": "16GB"
        }
    }
```

**FastAPI 会自动处理**：
- `dict` → JSON 对象
- `list` → JSON 数组
- `str` → JSON 字符串
- `int/float` → JSON 数字
- `bool` → JSON 布尔值
- `None` → JSON null
- `datetime` → ISO 8601 字符串

---

### 类型 2：使用响应模型（Response Model）

**类比**：标准化的账单格式

**问题场景**：
```python
# ❌ 不好的做法：返回了不该返回的数据
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    # 从数据库获取用户
    user = db.get_user(user_id)
    return user
    # 可能返回了：id, name, email, password_hash, secret_key...
    # 危险！密码哈希不应该暴露给前端！
```

**✅ 使用响应模型**：
```python
from pydantic import BaseModel

class UserInDB(BaseModel):
    """数据库中的完整用户信息"""
    id: int
    username: str
    email: str
    password_hash: str      # 密码哈希
    secret_key: str         # 密钥
    created_at: datetime

class UserResponse(BaseModel):
    """返回给前端的安全信息"""
    id: int
    username: str
    email: str
    created_at: datetime
    # 注意：没有 password_hash 和 secret_key！

@app.get("/users/{user_id}")
async def get_user(user_id: int, response: Response):
    # 1. 从数据库获取完整用户信息
    user_db = db.get_user(user_id)

    # 2. 只返回 response_model 中定义的字段
    return user_db
```

**response_model 参数**：
```python
from fastapi import FastAPI, Response

app = FastAPI()

@app.get(
    "/users/{user_id}",
    response_model=UserResponse,
    # FastAPI 自动过滤，只返回 UserResponse 中的字段
)
async def get_user(user_id: int):
    user_db = db.get_user(item_id)
    return user_db  # 自动过滤敏感字段！
```

**response_model_exclude 参数**（更灵活）：
```python
@app.get(
    "/users/{user_id}",
    response_model=UserInDB,
    response_model_exclude={"password_hash", "secret_key"},
    # 排除这些字段
)
async def get_user(item_id: int):
    return db.get_user(item_id)
```

**实际场景示例**：
```python
from pydantic import BaseModel
from datetime import datetime

class ItemBase(BaseModel):
    name: str
    description: str | None = None
    price: float

class ItemCreate(ItemBase):
    """创建商品时需要的字段"""
    pass

class ItemInDB(ItemBase):
    """数据库中的商品"""
    id: int
    created_at: datetime
    updated_at: datetime

class ItemResponse(ItemBase):
    """返回给前端的商品"""
    id: int
    created_at: datetime
    # 注意：没有 updated_at，前端不需要

@app.post("/items", response_model=ItemResponse)
async def create_item(item: ItemCreate):
    # 1. 创建商品（保存到数据库）
    item_db = ItemInDB(
        **item.model_dump(),
        id=1,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db.save(item_db)

    # 2. 只返回 ItemResponse 中定义的字段
    return item_db
```

---

### 类型 3：文件响应

**类比**：下载菜单 PDF

**返回文本文件**：
```python
from fastapi import FastAPI
from fastapi.responses import FileResponse

app = FastAPI()

@app.get("/download-menu")
async def download_menu():
    return FileResponse(
        path="menu.pdf",
        filename="restaurant_menu.pdf",
        media_type="application/pdf"
    )
```

**动态生成文件**：
```python
from fastapi.responses import Response, PlainTextResponse

@app.get("/export-csv")
async def export_users_to_csv():
    # 1. 从数据库获取数据
    users = db.get_all_users()

    # 2. 生成 CSV 内容
    csv_content = "id,name,email\n"
    for user in users:
        csv_content += f"{user.id},{user.name},{user.email}\n"

    # 3. 返回文件响应
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=users.csv"
        }
    )

# 更简洁的方式：
@app.get("/export-csv-v2")
async def export_users_to_csv_v2():
    users = db.get_all_users()
    csv_content = generate_csv(users)

    return PlainTextResponse(
        content=csv_content,
        headers={
            "Content-Disposition": "attachment; filename=users.csv"
        }
    )
```

**返回图片**：
```python
from fastapi.responses import Response
import io
from PIL import Image

@app.get("/generate-chart")
async def generate_chart():
    # 1. 生成图表（使用 matplotlib 或其他库）
    img = create_chart_image()

    # 2. 转换为字节
    img_io = io.BytesIO()
    img.save(img_io, format='PNG')
    img_bytes = img_io.getvalue()

    # 3. 返回图片
    return Response(
        content=img_bytes,
        media_type="image/png"
    )
```

**实际场景**：
- 导出数据：CSV、Excel、JSON 文件
- 生成报告：PDF、Word 文档
- 返回图片：验证码、二维码、图表
- 下载附件：用户上传的文件

---

### 类型 4：流式响应

**类比**：边做边上菜

**理解流式响应**：

普通响应 vs 流式响应：
```
普通响应：
[等待...等待...等待...] → [一次性返回所有数据]

流式响应：
[返回数据块1] → [返回数据块2] → [返回数据块3] → ...
```

**生成器函数**：
```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

def generate_large_file():
    """生成大文件的生成器"""
    for i in range(100):
        yield f"Line {i}\n"
        # 每次生成一行，不是一次性生成所有行

@app.get("/download-large-file")
async def download_large_file():
    return StreamingResponse(
        content=generate_large_file(),
        media_type="text/plain"
    )
```

**实时数据流**：
```python
import asyncio
from fastapi.responses import StreamingResponse

async def generate_realtime_data():
    """模拟实时数据流"""
    for i in range(10):
        await asyncio.sleep(1)  # 模拟延迟
        yield f"data: {i}\n\n"

@app.get("/realtime-data")
async def realtime_data():
    return StreamingResponse(
        content=generate_realtime_data(),
        media_type="text/event-stream"
    )
```

**大文件下载**：
```python
def read_file_in_chunks(file_path: str, chunk_size: int = 8192):
    """分块读取文件，避免内存溢出"""
    with open(file_path, mode='rb') as file:
        while chunk := file.read(chunk_size):
            yield chunk

@app.get("/download-video")
async def download_video():
    video_path = "large_video.mp4"
    return StreamingResponse(
        content=read_file_in_chunks(video_path),
        media_type="video/mp4"
    )
```

**实际场景**：
- 大文件下载：视频、大文档
- 实时数据：股票行情、聊天消息
- AI 生成内容：ChatGPT 逐字返回
- 日志流：实时查看服务器日志

---

## 🎨 响应状态码

**HTTP 状态码类比**：
- `200 OK`：服务员微笑着说"好的，马上来"
- `201 Created`：服务员说"新菜品已添加"
- `400 Bad Request`：服务员说"对不起，您的菜单填写有误"
- `404 Not Found`：服务员说"对不起，找不到这道菜"
- `422 Unprocessable Entity`：服务员说"您的订单格式不对"
- `500 Internal Server Error`：厨师说"哎呀，厨房出问题了"

**设置状态码**：
```python
from fastapi import FastAPI, status

app = FastAPI()

@app.post("/items", status_code=status.HTTP_201_CREATED)
async def create_item(item: Item):
    # 创建成功，返回 201 状态码
    return {"id": 1, **item.model_dump()}

@app.get("/items/{item_id}")
async def get_item(item_id: int):
    item = db.get_item(item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    return item
```

---

## 🔥 实战示例：完整的用户管理 API

**⚠️ 架构提醒**：以下示例专注于展示传输层的响应处理技巧。在生产环境中，业务逻辑应该在 Service 层实现（Level 2 学习）。

```python
# 注意：这是 Level 1 的简化示例
# 生产环境应该使用依赖注入（Level 2 学习）

```python
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
import csv

app = FastAPI()

# ========== 数据模型 ==========

class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str | None = None

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    id: int
    created_at: datetime
    is_active: bool = True

class UserResponse(UserBase):
    id: int
    created_at: datetime
    is_active: bool
    # 注意：没有 password！

# ========== 响应模型映射 ==========
# 根据不同情况返回不同的响应模型

@app.post("/users", response_model=UserResponse, status_code=201)
async def create_user(user: UserCreate):
    """创建用户"""
    # 1. 检查用户名是否已存在
    if db.user_exists(user.username):
        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )

    # 2. 创建用户（保存到数据库）
    user_db = UserInDB(
        id=1,
        **user.dict(exclude={"password"}),
        created_at=datetime.now(),
        password_hash=hash_password(user.password)  # 哈希密码
    )
    db.save_user(user_db)

    # 3. 只返回 UserResponse 中定义的字段
    return user_db

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    """获取用户"""
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    return user

@app.get("/users", response_model=list[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 10
):
    """获取用户列表"""
    users = db.get_users(skip=skip, limit=limit)
    return users  # 自动过滤每个用户的敏感字段

@app.get("/users/{user_id}/profile")
async def get_user_profile(user_id: int):
    """获取用户完整资料（返回文件）"""
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 生成 PDF 资料卡
    pdf_path = generate_profile_pdf(user)

    return FileResponse(
        path=pdf_path,
        filename=f"profile_{user_id}.pdf",
        media_type="application/pdf"
    )

@app.get("/users/export")
async def export_users():
    """导出所有用户为 CSV"""
    users = db.get_all_users()

    # 生成 CSV
    def generate_csv():
        output = io.StringIO()
        writer = csv.writer(output)

        # 写入表头
        writer.writerow(["id", "username", "email", "created_at"])

        # 写入数据
        for user in users:
            writer.writerow([
                user.id,
                user.username,
                user.email,
                user.created_at
            ])

        # 生成内容
        csv_content = output.getvalue()
        yield csv_content

    return StreamingResponse(
        content=generate_csv(),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=users.csv"
        }
    )
```

---

## 🚨 常见错误与调试

### 错误 1：返回了不该返回的数据

```python
# ❌ 错误：暴露了密码哈希
@app.post("/login")
async def login(username: str, password: str):
    user = db.authenticate(username, password)
    return user  # 包含 password_hash！

# ✅ 正确：使用响应模型
@app.post("/login", response_model=UserResponse)
async def login(username: str, password: str):
    user = db.authenticate(username, password)
    return user  # 自动过滤 password_hash
```

### 错误 2：忘记设置 Content-Type

```python
# ❌ 错误：可能无法正确显示
@app.get("/data")
async def get_data():
    return Response(content="some data")

# ✅ 正确：明确指定类型
@app.get("/data")
async def get_data():
    return Response(
        content="some data",
        media_type="text/plain"
    )
```

### 错误 3：流式响应没有异步生成

```python
# ❌ 错误：阻塞事件循环
def generate_data():
    time.sleep(1)  # 阻塞！
    return "data"

# ✅ 正确：使用异步
async def generate_data():
    await asyncio.sleep(1)  # 非阻塞
    return "data"
```

---

## 🎯 练习：自己动手

**⚠️ 重要提醒**：这些练习专注于传输层的响应处理，使用简化的数据结构。**不要在练习中编写业务逻辑或直接操作数据库**。

### 练习 1：商品列表 API

创建一个商品列表接口：
- 使用 `response_model` 确保不暴露成本价
- 支持分页（`page` 和 `per_page` 参数）
- 返回状态码 200

### 练习 2：导出订单

创建一个导出订单接口：
- 根据日期范围筛选订单
- 生成 CSV 文件
- 使用 `StreamingResponse` 返回

### 练习 3：实时通知

创建一个实时通知接口：
- 使用生成器函数模拟实时消息
- 每 2 秒返回一条通知
- 使用 `StreamingResponse` 返回

---

## 📚 检查理解

回答这些问题来测试你的理解：

1. **什么时候需要使用 response_model？**
   - 提示：需要过滤敏感字段时

2. **StreamingResponse 和普通 Response 有什么区别？**
   - 提示：一次性返回 vs 分块返回

3. **如何返回一个文件下载？**
   - 提示：FileResponse 或 StreamingResponse

4. **状态码 201 和 200 有什么区别？**
   - 提示：201 用于资源创建

5. **响应处理属于架构中的哪一层？**
   - 提示：这是传输层（Transport Layer）的职责

6. **如何确保响应中不包含密码字段？**
   - 提示：response_model 或 response_model_exclude

7. **为什么不在 endpoint 中做数据转换？**
   - 提示：业务逻辑应该在 Service 层

---
   - 提示：需要过滤敏感字段时

2. **StreamingResponse 和普通 Response 有什么区别？**
   - 提示：一次性返回 vs 分块返回

3. **如何返回一个文件下载？**
   - 提示：FileResponse 或 StreamingResponse

4. **状态码 201 和 200 有什么区别？**
   - 提示：201 用于资源创建

5. **如何确保响应中不包含密码字段？**
   - 提示：response_model 或 response_model_exclude

---

## 🚀 下一步

现在你已经理解了响应处理的基本概念，接下来：

1. **查看实际代码**：`examples/02_response_handling.py`
2. **运行并测试**：尝试不同的响应类型
3. **完成练习**：在 `exercises/02_response_exercises.md` 中有更多练习

记住：**好的响应设计让 API 易用、安全、高效！**

**架构视角回顾**：
- ✅ 你学会了：传输层的响应处理职责
- ✅ 你掌握了：JSON、文件、流式响应
- ⏭️ 下一步：统一响应格式和错误处理
- 🎯 最终目标：成为合格的"协议适配"专家

**Level 1 总结**：完成这两个课程后，你已经掌握了传输层的核心职责 —— **协议适配的输入和输出**！

---

---

**费曼技巧总结**：
- ✅ 用简单的类比（餐厅账单）
- ✅ 循序渐进（JSON → 模型 → 文件 → 流式）
- ✅ 用具体的例子（完整的用户管理 API）
- ✅ 展示常见的错误
- ✅ 提供可运行的代码
- ✅ 包含练习题检验理解
