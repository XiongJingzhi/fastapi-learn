# 01. 请求参数校验 - Request Validation

## 📍 在架构中的位置

**传输层 (Transport Layer)** - 这是 FastAPI 的核心领地！

```
┌─────────────┐
│   客户端    │  ← 发送 HTTP 请求
└─────────────┘
      │
      ▼
┌─────────────────────────────┐
│      【传输层 / FastAPI】    │
│                             │
│  1️⃣ 接收请求                  │
│  2️⃣ 校验参数  ← 你在这里学习   │
│  3️⃣ 调用服务层                │
│  4️⃣ 返回响应                  │
└─────────────────────────────┘
      │
      ▼
┌─────────────┐
│  服务层     │  ← 业务逻辑（Level 2+ 学习）
└─────────────┘
```

**🎯 你的学习目标**：掌握"协议适配"的第一步 —— 把 HTTP 请求数据转换成 Python 对象。

**⚠️ 架构约束**：在 Level 1，我们只学习传输层的职责，**不在 endpoint 中编写业务逻辑**。

---

## 🎯 什么是请求校验？

想象你开了一家餐厅：

**没有校验的情况**：
- 顾客点菜时说"我要一份...嗯...那个东西"
- 顾客给你一张白纸当菜单
- 顾客说"我要 -5 个汉堡"

你的服务员会非常困惑，不知道该做什么！

**有校验的情况**：
- 顾客必须清楚地说明：菜名、数量、桌号
- 如果顾客说错了，服务员会礼貌地指出："对不起，请提供完整的菜名"
- 如果顾客说"我要 5 个汉堡"，服务员会说"好的，5 个汉堡"

在 FastAPI 中，**请求校验**就是这个"服务员"——它确保发到服务器的数据是完整、正确、可用的。

**架构视角**：请求校验是传输层的核心职责之一 —— **协议适配的第一步**。

---

## 💡 架构提示：为什么校验如此重要？

### 传输层的职责边界

```
┌─────────────────────────────────────────┐
│  ❌ 不在传输层做的事（Level 1 禁止）      │
│  - 业务逻辑验证（如"用户余额是否足够"）   │
│  - 数据库操作                            │
│  - 调用外部 API                          │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  ✅ 在传输层做的事（Level 1 学习）        │
│  - 数据格式验证（如"邮箱格式是否正确"）   │
│  - 数据类型转换（如"字符串→整数"）        │
│  - 必填字段检查（如"是否缺少 username"）  │
└─────────────────────────────────────────┘
```

**为什么这样区分？**

```python
# ❌ 错误示例：在 endpoint 中做业务逻辑
@app.post("/orders")
async def create_order(order: OrderCreate):
    # 问题：业务逻辑被绑在 HTTP 层
    if order.quantity > 100:
        # 这应该在 Service 层！
        raise HTTPException(400, "库存不足")
    result = db.create_order(order)  # 不应该直接操作数据库
    return result

# ✅ 正确示例：endpoint 只做协议适配
@app.post("/orders")
async def create_order(
    order: OrderCreate,
    service: OrderService = Depends()  # Level 2 学习
):
    # Endpoint 只负责：校验 → 调用服务 → 返回
    return await service.create_order(order)
```

---

## 🤔 为什么需要请求校验？

### 真实世界的问题

假设你有一个用户注册接口，期望收到：
```json
{
  "username": "alice",
  "email": "alice@example.com",
  "age": 25
}
```

但如果用户发送：
```json
{
  "username": "bob"
  // 忘记了 email
  // age 是负数？
}
```

**没有校验**：你的代码会崩溃，或者存入错误的数据到数据库
**有校验**：FastAPI 自动拦截，告诉用户"缺少必填字段 email"

### 三大好处

1. **保护你的代码**：不会因为错误数据而崩溃
2. **保护你的数据**：不会把垃圾数据存入数据库
3. **帮助用户**：清楚地告诉用户哪里出错了

---

## 📦 FastAPI 的五种参数类型

FastAPI 把"从客户端获取数据"这个任务分成了五种方式，就像餐厅有五种接收订单的方式：

### 1. Path Parameters（路径参数）

**类比**：就像快递单号，直接写在地址上

```
GET /users/123
         ^^^
         这个 123 就是路径参数
```

**代码示例**：
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    # FastAPI 自动确保 user_id 是整数
    # 如果访问 /users/abc，会返回 422 错误
    return {"user_id": user_id}
```

**关键点**：
- 用 `{}` 在 URL 中定义占位符
- FastAPI 自动转换类型（字符串 → 整数）
- 如果类型不对，自动返回错误

**实际场景**：
- `/items/42` → 获取 ID 为 42 的商品
- `/posts/2024/01/15` → 获取 2024年1月15日的文章
- `/files/cat.jpg` → 获取名为 cat.jpg 的文件

---

### 2. Query Parameters（查询参数）

**类比**：就像网购时的筛选条件

```
GET /products?category=electronics&sort=price
                    ^^^^^^^^^^^^^^^^ ^^^^^^^^^^^
                    这些都是查询参数
```

**代码示例**：
```python
@app.get("/products")
async def get_products(
    category: str = "all",      # 默认值 "all"
    sort: str = "relevance",
    limit: int = 10
):
    return {
        "category": category,
        "sort": sort,
        "limit": limit
    }
```

**访问示例**：
- `/products` → 使用所有默认值
- `/products?category=books` → 只指定 category
- `/products?category=books&limit=20` → 指定多个参数
- `/products?limit=abc` → 错误！limit 必须是整数

**关键点**：
- `?` 后面开始是查询参数
- 用 `&` 分隔多个参数
- 可以设置默认值
- FastAPI 自动类型转换

**实际场景**：
- 搜索：`/search?q=python&page=2`
- 筛选：`/users?role=admin&active=true`
- 排序：`/items?sort_by=price&order=desc`

---

### 3. Body Parameters（请求体参数）

**类比**：就像填写一张详细的表单

```
POST /users
Content-Type: application/json

{
  "name": "Alice",
  "email": "alice@example.com",
  "age": 25
}
```

**代码示例**：
```python
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    name: str                    # 必填
    email: EmailStr              # 必填，且必须是邮箱格式
    age: int | None = None       # 可选，默认 None
    address: str = "Unknown"     # 可选，默认 "Unknown"

@app.post("/users")
async def create_user(user: UserCreate):
    # FastAPI 自动校验：
    # 1. name 必须存在
    # 2. email 必须是有效邮箱
    # 3. age 必须是整数（如果提供）
    # 4. address 默认是 "Unknown"
    return {"message": f"Created user: {user.name}"}
```

**Pydantic 模型的力量**：

```python
from pydantic import BaseModel, Field

class Item(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    # "..." 表示必填
    # 名字长度必须在 1-50 之间

    price: float = Field(..., gt=0)
    # 价格必须大于 0

    description: str | None = Field(None, max_length=500)
    # 描述可选，最多 500 字符

    tags: list[str] = []
    # 标签列表，默认为空列表
```

**发送错误的请求**：
```json
{
  "name": "",              // ❌ 太短了
  "price": -10,            // ❌ 不能是负数
  "description": "a" * 600 // ❌ 太长了
}
```

**FastAPI 的响应**：
```json
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "ensure this value has at least 1 characters",
      "type": "value_error.any_str.min_length"
    },
    {
      "loc": ["body", "price"],
      "msg": "ensure this value is greater than 0",
      "type": "value_error.number.not_gt"
    }
  ]
}
```

**实际场景**：
- 创建资源：POST /users（注册新用户）
- 更新资源：PUT /items/123（更新商品信息）
- 提交表单：POST /orders（提交订单）

---

### 4. Header Parameters（请求头参数）

**类比**：就像信封上的寄信人信息

```python
from fastapi import Header

@app.get("/items")
async def get_items(
    user_agent: str = Header(...),
    authorization: str | None = Header(None)
):
    return {
        "user_agent": user_agent,
        "authorization": authorization
    }
```

**关键点**：
- 自动从 HTTP 请求头中提取
- 常用于认证、版本控制
- 参数名会自动转换（User-Agent → user_agent）

**实际场景**：
- 认证令牌：`Authorization: Bearer abc123`
- API 版本：`API-Version: v2`
- 客户端信息：`User-Agent: MyApp/1.0`

---

### 5. Cookie Parameters（Cookie 参数）

**类比**：就像会员卡，你带着它，商家就认得你

```python
from fastapi import Cookie

@app.get("/profile")
async def get_profile(
    session_id: str | None = Cookie(None)
):
    if not session_id:
        return {"message": "Not logged in"}
    return {"session_id": session_id}
```

**实际场景**：
- 会话管理：`session_id=abc123`
- 用户偏好：`theme=dark`
- 追踪标识：`user_token=xyz789`

---

## 🎓 类型注解的重要性

FastAPI 使用 Python 的**类型注解**来知道如何校验数据：

```python
# 基本类型
age: int                # 必须是整数
name: str               # 必须是字符串
price: float            # 必须是浮点数

# 可选类型
nickname: str | None    # 可以是字符串或 None
middle_name: Optional[str] = None  # 同上（旧写法）

# 默认值
limit: int = 10         # 默认 10，如果不提供的话

# 列表类型
tags: list[str]         # 必须是字符串列表
scores: list[int]       # 必须是整数列表
```

**FastAPI 看到这些注解后**：
1. 自动生成 API 文档（Swagger UI）
2. 自动校验传入数据
3. 自动转换数据类型
4. 自动返回友好的错误信息

---

## 🔥 实战示例：完整的商品搜索 API

```python
from fastapi import FastAPI, Query, Path
from pydantic import BaseModel, Field
from typing import Optional

app = FastAPI()

class ProductFilter(BaseModel):
    """商品筛选条件（请求体）"""
    min_price: float | None = Field(None, ge=0)
    # ge=0 表示 greater than or equal to 0（≥0）

    max_price: float | None = Field(None, ge=0)

    brands: list[str] = []
    # 品牌列表

    in_stock: bool | None = None
    # 是否只显示有货商品

@app.post("/products/{category}")
async def search_products(
    # Path: 商品类别（必填）
    category: str = Path(..., description="商品类别"),

    # Query: 分页参数（有默认值）
    page: int = Query(1, ge=1, description="页码，从 1 开始"),
    per_page: int = Query(10, ge=1, le=100, description="每页数量，最多 100"),

    # Body: 筛选条件（可选）
    filters: ProductFilter = None,

    # Header: 用户语言偏好
    accept_language: str = Query("zh-CN", description="语言设置")
):
    """
    搜索商品

    FastAPI 会自动校验：
    - category 必须提供
    - page 必须 ≥ 1
    - per_page 必须 1-100 之间
    - filters.min_price 和 max_price 必须 ≥ 0
    """

    return {
        "category": category,
        "page": page,
        "per_page": per_page,
        "filters": filters,
        "language": accept_language
    }
```

**请求示例**：

```bash
# 完整请求
curl -X POST "http://localhost:8000/products/electronics?page=2&per_page=20" \
  -H "Accept-Language: en-US" \
  -d '{
    "min_price": 100,
    "max_price": 1000,
    "brands": ["Apple", "Samsung"],
    "in_stock": true
  }'

# 最简请求（使用所有默认值）
curl -X POST "http://localhost:8000/products/books"
```

---

## 🚨 常见错误与调试

### 错误 1：混淆 Path 和 Query

```python
# ❌ 错误：想用 Query 但定义成了 Path
@app.get("/items")
async def get_items(item_id: int = Path(...)):
    # /items?item_id=123 → 找不到这个路径！
    pass

# ✅ 正确
@app.get("/items/{item_id}")
async def get_items(item_id: int = Path(...)):
    # /items/123 → 正确！
    pass
```

### 错误 2：忘记导入 Query 或 Path

```python
# ❌ 错误
@app.get("/items")
async def get_items(limit: int = Query(10)):
    # NameError: name 'Query' is not defined
    pass

# ✅ 正确
from fastapi import Query

@app.get("/items")
async def get_items(limit: int = Query(10)):
    pass
```

### 错误 3：必填参数设置了默认值

```python
# ❌ 错误逻辑
@app.get("/items")
async def get_items(item_id: int = None):
    # 想必填，但给了默认值，变成可选了！
    pass

# ✅ 正确
@app.get("/items")
async def get_items(item_id: int = Query(...)):
    # ... 表示必填
    pass
```

### 错误 4：Pydantic 模型字段顺序问题

```python
# ⚠️ 潜在问题
class Item(BaseModel):
    name: str
    price: float
    description: str  # 如果前端先发 description，会报错

# ✅ 更好的设计
class Item(BaseModel):
    name: str
    description: str | None = None  # 可选字段放后面
    price: float
```

---

## 🎯 练习：自己动手

**⚠️ 重要提醒**：这些练习专注于传输层的参数校验，**不涉及业务逻辑和数据库操作**。

### 练习 1：用户搜索 API

创建一个用户搜索接口：
- Path: `user_type`（用户类型：admin/user）
- Query: `page`（页码，默认 1）
- Query: `status`（状态：active/inactive，可选）
- Body: `UserFilter` 模型（包含 age_min, age_max）
- Header: `X-Request-ID`（追踪 ID）

### 练习 2：订单创建 API

创建一个订单接口：
- 使用 Pydantic 模型定义订单结构
- 包含字段：product_id（必填）、quantity（≥1）、note（可选）
- 如果 quantity > 100，需要 special_approval 字段

### 练习 3：调试错误信息

故意发送错误的请求，观察 FastAPI 的错误响应，理解错误信息的结构。

---

## 📚 检查理解

回答这些问题来测试你的理解：

1. **什么时候用 Path，什么时候用 Query？**
   - 提示：Path 是 URL 的一部分，Query 是 `?` 后面的参数

2. **为什么需要 Pydantic 模型，而不是直接用字典？**
   - 提示：自动校验、类型转换、API 文档

3. **请求校验属于架构中的哪一层？**
   - 提示：这是传输层（Transport Layer）的职责

4. **为什么不在 endpoint 中编写业务逻辑？**
   - 提示：违反单一职责原则，难以测试和复用

5. **`Query(...)` 中的 `...` 是什么意思？**
   - 提示：表示"必填"

6. **FastAPI 如何知道一个参数是 Path、Query 还是 Body？**
   - 提示：看函数签名中的类型和默认值

---
   - 提示：Path 是 URL 的一部分，Query 是 `?` 后面的参数

2. **为什么需要 Pydantic 模型，而不是直接用字典？**
   - 提示：自动校验、类型转换、API 文档

3. **如何让一个参数可选？**
   - 提示：使用 `| None` 或 `Optional[...]` 并设置默认值 `None`

4. **`Query(...)` 中的 `...` 是什么意思？**
   - 提示：表示"必填"

5. **FastAPI 如何知道一个参数是 Path、Query 还是 Body？**
   - 提示：看函数签名中的类型和默认值

---

## 🚀 下一步

现在你已经理解了请求校验的基本概念，接下来：

1. **查看实际代码**：`examples/01_request_validation.py`
2. **运行并测试**：尝试发送各种请求，观察校验效果
3. **完成练习**：在 `exercises/01_basic_exercises.md` 中有更多练习

记住：**请求校验是传输层的核心职责，是协议适配的第一步！**

**架构视角回顾**：
- ✅ 你学会了：传输层的参数校验职责
- ⏭️ 下一步：响应处理（传输层的另一核心职责）
- 🎯 最终目标：成为合格的"协议适配"专家

---

---

**费曼技巧总结**：
- ✅ 用简单的类比（餐厅服务员）
- ✅ 用具体的例子（JSON 请求/响应）
- ✅ 展示常见的错误
- ✅ 提供可运行的代码
- ✅ 包含练习题检验理解
