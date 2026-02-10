# Level 1 基础练习题

## 🎯 练习说明

这些练习题帮助你巩固 **请求参数校验** 和 **响应处理** 的知识。

**练习原则**：
- ✅ **i+1 难度** - 每个练习都是略高于当前水平的挑战
- ✅ **循序渐进** - 从简单到复杂，逐步提升
- ✅ **真实场景** - 模拟实际项目中的常见需求
- ✅ **自我验证** - 提供答案和检查方法

**练习结构**：
- 📝 **目标** - 这个练习要达到什么目的
- 💡 **提示** - 关键思路（需要时再看）
- ✅ **答案** - 参考实现
- 🔍 **自检** - 如何验证你的答案

---

## 🟢 基础练习 - 单个概念巩固

### 练习 1：用户注册接口（Body 参数 + 响应模型）

#### 📝 目标
创建一个用户注册接口，要求：
1. 使用 Pydantic 模型校验请求数据
2. 密码必须至少 8 个字符
3. 邮箱必须是有效格式
4. 使用响应模型，**不返回密码字段**
5. 注册成功返回 201 状态码

#### 💡 提示
- 创建两个 Pydantic 模型：`UserCreate` 和 `UserResponse`
- 使用 `Field()` 设置密码长度限制
- 使用 `EmailStr` 类型校验邮箱
- 在路由装饰器中使用 `response_model` 参数

#### ✅ 答案

```python
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime

app = FastAPI()

# 数据模型
class UserCreate(BaseModel):
    """创建用户的请求模型"""
    username: str = Field(..., min_length=3, max_length=20)
    email: EmailStr  # 自动校验邮箱格式
    password: str = Field(..., min_length=8)  # 至少 8 个字符
    full_name: str | None = Field(None, max_length=50)

class UserResponse(BaseModel):
    """返回给前端的用户模型（不包含密码）"""
    id: int
    username: str
    email: str
    full_name: str | None
    created_at: datetime

# 模拟数据库
fake_db: dict[int, UserResponse] = {}
user_id_counter = 1

@app.post(
    "/users/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
async def register_user(user: UserCreate):
    global user_id_counter

    # 检查用户名是否已存在
    for existing_user in fake_db.values():
        if existing_user.username == user.username:
            raise HTTPException(
                status_code=400,
                detail="Username already exists"
            )

    # 创建新用户
    new_user = UserResponse(
        id=user_id_counter,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        created_at=datetime.now()
    )

    fake_db[user_id_counter] = new_user
    user_id_counter += 1

    return new_user
```

#### 🔍 自检
1. **测试正常注册**：
   ```bash
   curl -X POST "http://localhost:8000/users/register" \
     -H "Content-Type: application/json" \
     -d '{
       "username": "alice",
       "email": "alice@example.com",
       "password": "password123"
     }'
   ```
   预期：返回用户信息，**不包含密码**，状态码 201

2. **测试密码太短**：
   ```bash
   curl -X POST "http://localhost:8000/users/register" \
     -H "Content-Type: application/json" \
     -d '{"username": "bob", "email": "bob@example.com", "password": "123"}'
   ```
   预期：返回 422 错误，提示密码至少 8 个字符

3. **测试无效邮箱**：
   ```bash
   curl -X POST "http://localhost:8000/users/register" \
     -H "Content-Type: application/json" \
     -d '{"username": "charlie", "email": "invalid-email", "password": "password123"}'
   ```
   预期：返回 422 错误，提示邮箱格式无效

---

### 练习 2：博客文章列表（Query 参数 + 分页）

#### 📝 目标
创建一个获取文章列表的接口，要求：
1. 使用 Query 参数实现分页
2. `page` 默认为 1，必须 ≥ 1
3. `per_page` 默认为 10，必须在 1-50 之间
4. 可选的 `category` 筛选参数
5. 返回文章列表和总数

#### 💡 提示
- 使用 `Query()` 函数设置参数约束
- 使用 `ge` (greater than or equal) 和 `le` (less than or equal)
- 返回一个字典，包含 `items` 和 `total` 两个字段

#### ✅ 答案

```python
from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

class Article(BaseModel):
    id: int
    title: str
    content: str
    category: str
    author: str

# 模拟数据库
fake_articles = [
    Article(id=i, title=f"Article {i}", content="...", category=f"cat{i%3}", author="alice")
    for i in range(1, 101)  # 100 篇文章
]

@app.get("/articles")
async def list_articles(
    page: int = Query(1, ge=1, description="页码，从 1 开始"),
    per_page: int = Query(10, ge=1, le=50, description="每页数量，最多 50"),
    category: Optional[str] = Query(None, description="按类别筛选")
):
    # 筛选
    articles = fake_articles
    if category:
        articles = [a for a in articles if a.category == category]

    # 分页
    total = len(articles)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_articles = articles[start:end]

    return {
        "items": paginated_articles,
        "total": total,
        "page": page,
        "per_page": per_page
    }
```

#### 🔍 自检
1. **测试默认分页**：
   ```bash
   curl "http://localhost:8000/articles"
   ```
   预期：返回第 1 页，10 篇文章，total=100

2. **测试指定页码**：
   ```bash
   curl "http://localhost:8000/articles?page=2&per_page=20"
   ```
   预期：返回第 2 页，20 篇文章

3. **测试类别筛选**：
   ```bash
   curl "http://localhost:8000/articles?category=cat1"
   ```
   预期：只返回 cat1 类别的文章

4. **测试无效参数**：
   ```bash
   curl "http://localhost:8000/articles?page=0"
   ```
   预期：返回 422 错误，page 必须 ≥ 1

---

### 练习 3：商品详情（Path 参数 + 404 处理）

#### 📝 目标
创建一个获取商品详情的接口，要求：
1. 使用 Path 参数获取商品 ID
2. 如果商品不存在，返回 404 错误
3. 如果商品存在，返回详细信息
4. 使用响应模型隐藏成本价字段

#### 💡 提示
- 使用 `Path()` 函数定义路径参数
- 使用 `HTTPException` 抛出 404 错误
- 创建两个模型：`ItemInDB`（包含成本价）和 `ItemResponse`（不包含）

#### ✅ 答案

```python
from fastapi import FastAPI, HTTPException, Path, status
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

class ItemInDB(BaseModel):
    """数据库中的商品（包含敏感信息）"""
    id: int
    name: str
    price: float
    cost: float  # 成本价（敏感信息）
    description: Optional[str] = None
    in_stock: bool = True

class ItemResponse(BaseModel):
    """返回给前端的商品（不包含成本价）"""
    id: int
    name: str
    price: float
    description: Optional[str] = None
    in_stock: bool = True

# 模拟数据库
fake_items_db: dict[int, ItemInDB] = {
    1: ItemInDB(id=1, name="Laptop", price=999.99, cost=600.00, description="Good laptop"),
    2: ItemInDB(id=2, name="Mouse", price=29.99, cost=5.00),
    3: ItemInDB(id=3, name="Keyboard", price=79.99, cost=20.00, in_stock=False)
}

@app.get("/items/{item_id}", response_model=ItemResponse)
async def get_item(
    item_id: int = Path(..., ge=1, description="商品 ID")
):
    # 查找商品
    item = fake_items_db.get(item_id)

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {item_id} not found"
        )

    # 自动过滤 cost 字段
    return item
```

#### 🔍 自检
1. **测试存在的商品**：
   ```bash
   curl "http://localhost:8000/items/1"
   ```
   预期：返回商品信息，**不包含 cost**，状态码 200

2. **测试不存在的商品**：
   ```bash
   curl "http://localhost:8000/items/999"
   ```
   预期：返回 404 错误

3. **测试无效 ID**：
   ```bash
   curl "http://localhost:8000/items/abc"
   ```
   预期：返回 422 错误，提示必须是整数

---

### 练习 4：导出用户数据（FileResponse）

#### 📝 目标
创建一个导出用户数据的接口，要求：
1. 生成 CSV 格式的用户列表
2. 包含字段：id, username, email, created_at
3. 使用 FileResponse 或 StreamingResponse 返回
4. 文件名为 `users_YYYYMMDD.csv`

#### 💡 提示
- 使用 Python 的 `csv` 模块或手动生成 CSV
- 使用 `datetime.now()` 获取当前日期
- 在响应头中设置 `Content-Disposition`

#### ✅ 答案

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from datetime import datetime
import io

app = FastAPI()

class User(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

# 模拟数据库
fake_users = [
    User(id=1, username="alice", email="alice@example.com", created_at=datetime.now()),
    User(id=2, username="bob", email="bob@example.com", created_at=datetime.now()),
]

@app.get("/users/export")
async def export_users():
    # 生成 CSV 内容
    output = io.StringIO()

    # 写入表头
    output.write("id,username,email,created_at\n")

    # 写入数据
    for user in fake_users:
        created_at_str = user.created_at.strftime("%Y-%m-%d %H:%M:%S")
        output.write(f"{user.id},{user.username},{user.email},{created_at_str}\n")

    # 生成文件名
    today = datetime.now().strftime("%Y%m%d")
    filename = f"users_{today}.csv"

    # 返回 CSV 文件
    return StreamingResponse(
        content=iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
```

#### 🔍 自检
1. **测试导出**：
   ```bash
   curl "http://localhost:8000/users/export" -o users.csv
   cat users.csv
   ```
   预期：下载成功，CSV 格式正确

2. **检查文件名**：
   预期：文件名格式为 `users_20240115.csv`（日期会变化）

---

## 🟡 综合练习 - 多概念组合

### 练习 5：完整的 TODO API（CRUD）

#### 📝 目标
创建一个完整的 TODO 应用 API，包含：

**1. 创建 TODO** - `POST /todos`
- 必填字段：`title`（1-100 字符）
- 可选字段：`description`（最多 500 字符）、`completed`（默认 False）
- 返回 201 状态码

**2. 获取 TODO 列表** - `GET /todos`
- 支持分页（`page` 和 `per_page`）
- 可选筛选：`completed`（true/false）
- 返回列表和总数

**3. 获取单个 TODO** - `GET /todos/{todo_id}`
- 如果不存在，返回 404

**4. 更新 TODO** - `PUT /todos/{todo_id}`
- 可以更新 `title`、`description`、`completed`
- 如果不存在，返回 404

**5. 删除 TODO** - `DELETE /todos/{todo_id}`
- 如果不存在，返回 404
- 删除成功返回 204

#### 💡 提示
- 创建多个 Pydantic 模型：`TodoCreate`、`TodoUpdate`、`TodoResponse`
- 使用 `fake_db` 字典模拟数据库
- 更新接口的 `TodoUpdate` 模型中所有字段都应该是可选的

#### ✅ 答案

```python
from fastapi import FastAPI, HTTPException, Path, Query, status
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

app = FastAPI()

# ========== 数据模型 ==========

class TodoBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

class TodoCreate(TodoBase):
    """创建 TODO 的请求模型"""
    completed: bool = False

class TodoUpdate(BaseModel):
    """更新 TODO 的请求模型（所有字段可选）"""
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    completed: Optional[bool] = None

class TodoResponse(TodoBase):
    """返回给前端的 TODO 模型"""
    id: int
    completed: bool
    created_at: datetime

# ========== 模拟数据库 ==========

fake_db: dict[int, TodoResponse] = {}
todo_id_counter = 1

# ========== CRUD 接口 ==========

@app.post("/todos", response_model=TodoResponse, status_code=201)
async def create_todo(todo: TodoCreate):
    """创建 TODO"""
    global todo_id_counter

    new_todo = TodoResponse(
        id=todo_id_counter,
        title=todo.title,
        description=todo.description,
        completed=todo.completed,
        created_at=datetime.now()
    )

    fake_db[todo_id_counter] = new_todo
    todo_id_counter += 1

    return new_todo

@app.get("/todos")
async def list_todos(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    completed: Optional[bool] = None
):
    """获取 TODO 列表"""
    # 筛选
    todos = list(fake_db.values())
    if completed is not None:
        todos = [t for t in todos if t.completed == completed]

    # 排序（最新的在前）
    todos.sort(key=lambda x: x.id, reverse=True)

    # 分页
    total = len(todos)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_todos = todos[start:end]

    return {
        "items": paginated_todos,
        "total": total,
        "page": page,
        "per_page": per_page
    }

@app.get("/todos/{todo_id}", response_model=TodoResponse)
async def get_todo(todo_id: int = Path(..., ge=1)):
    """获取单个 TODO"""
    todo = fake_db.get(todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="TODO not found")
    return todo

@app.put("/todos/{todo_id}", response_model=TodoResponse)
async def update_todo(todo_id: int = Path(..., ge=1), todo_update: TodoUpdate = None):
    """更新 TODO"""
    todo = fake_db.get(todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="TODO not found")

    # 只更新提供的字段
    update_data = todo_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(todo, field, value)

    return todo

@app.delete("/todos/{todo_id}", status_code=204)
async def delete_todo(todo_id: int = Path(..., ge=1)):
    """删除 TODO"""
    if todo_id not in fake_db:
        raise HTTPException(status_code=404, detail="TODO not found")

    del fake_db[todo_id]
    return None  # 204 状态码不返回内容
```

#### 🔍 自检
1. **测试创建 TODO**：
   ```bash
   curl -X POST "http://localhost:8000/todos" \
     -H "Content-Type: application/json" \
     -d '{"title": "学习 FastAPI", "description": "完成 Level 1 练习"}'
   ```

2. **测试获取列表**：
   ```bash
   curl "http://localhost:8000/todos?page=1&per_page=5&completed=false"
   ```

3. **测试更新**：
   ```bash
   curl -X PUT "http://localhost:8000/todos/1" \
     -H "Content-Type: application/json" \
     -d '{"completed": true}'
   ```

4. **测试删除**：
   ```bash
   curl -X DELETE "http://localhost:8000/todos/1"
   ```

---

### 练习 6：商品搜索 API（综合查询）

#### 📝 目标
创建一个类似淘宝的商品搜索接口：

**`POST /products/search`**

**Path 参数**：
- `category`：商品类别（如 electronics, books, clothing）

**Query 参数**：
- `q`：搜索关键词（在标题和描述中搜索）
- `sort_by`：排序字段（price_asc, price_desc, popularity）
- `page` 和 `per_page`：分页

**Body 参数**（使用 Pydantic 模型）：
- `price_range`：价格范围 `{min: float, max: float}`
- `brands`：品牌列表（如 ["Apple", "Samsung"]）
- `in_stock`：是否只显示有货商品

**响应**：
- 返回符合条件的商品列表
- 包含搜索结果总数
- 包含当前筛选条件摘要

#### 💡 提示
- 使用多个 Pydantic 模型处理不同类型的参数
- 搜索逻辑：遍历所有商品，检查是否满足所有条件
- 排序逻辑：根据 `sort_by` 参数对结果排序

#### ✅ 答案

```python
from fastapi import FastAPI, Path, Query
from pydantic import BaseModel, Field
from typing import Optional, List

app = FastAPI()

# ========== 数据模型 ==========

class PriceRange(BaseModel):
    """价格范围"""
    min: Optional[float] = Field(None, ge=0)
    max: Optional[float] = Field(None, ge=0)

class SearchFilter(BaseModel):
    """搜索筛选条件（请求体）"""
    price_range: Optional[PriceRange] = None
    brands: Optional[List[str]] = Field(default_factory=list)
    in_stock: Optional[bool] = None

class Product(BaseModel):
    """商品"""
    id: int
    title: str
    description: str
    price: float
    category: str
    brand: str
    in_stock: bool
    popularity: int  # 人气值

class SearchResponse(BaseModel):
    """搜索响应"""
    items: List[Product]
    total: int
    page: int
    per_page: int
    filters_applied: dict

# ========== 模拟数据库 ==========

fake_products = [
    Product(
        id=1,
        title="iPhone 15",
        description="最新款苹果手机",
        price=7999.0,
        category="electronics",
        brand="Apple",
        in_stock=True,
        popularity=95
    ),
    Product(
        id=2,
        title="Galaxy S24",
        description="三星旗舰手机",
        price=6999.0,
        category="electronics",
        brand="Samsung",
        in_stock=True,
        popularity=88
    ),
    Product(
        id=3,
        title="MacBook Pro",
        description="苹果笔记本电脑",
        price=15999.0,
        category="electronics",
        brand="Apple",
        in_stock=False,
        popularity=92
    ),
    Product(
        id=4,
        title="Python 编程",
        description="从入门到精通",
        price=89.0,
        category="books",
        brand="Unknown",
        in_stock=True,
        popularity=75
    ),
]

# ========== 搜索接口 ==========

@app.post("/products/search/{category}", response_model=SearchResponse)
async def search_products(
    category: str = Path(..., description="商品类别"),
    q: Optional[str] = Query(None, description="搜索关键词"),
    sort_by: str = Query("popularity", description="排序字段"),
    page: int = Query(1, ge=1, description="页码"),
    per_page: int = Query(10, ge=1, le=50, description="每页数量"),
    filters: Optional[SearchFilter] = None
):
    # 1. 类别筛选
    products = [p for p in fake_products if p.category == category]

    # 2. 关键词搜索
    if q:
        q_lower = q.lower()
        products = [
            p for p in products
            if q_lower in p.title.lower() or q_lower in p.description.lower()
        ]

    # 3. 价格筛选
    if filters and filters.price_range:
        if filters.price_range.min is not None:
            products = [p for p in products if p.price >= filters.price_range.min]
        if filters.price_range.max is not None:
            products = [p for p in products if p.price <= filters.price_range.max]

    # 4. 品牌筛选
    if filters and filters.brands:
        products = [p for p in products if p.brand in filters.brands]

    # 5. 库存筛选
    if filters and filters.in_stock is not None:
        products = [p for p in products if p.in_stock == filters.in_stock]

    # 6. 排序
    if sort_by == "price_asc":
        products.sort(key=lambda x: x.price)
    elif sort_by == "price_desc":
        products.sort(key=lambda x: x.price, reverse=True)
    elif sort_by == "popularity":
        products.sort(key=lambda x: x.popularity, reverse=True)

    # 7. 分页
    total = len(products)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_products = products[start:end]

    # 8. 筛选条件摘要
    filters_applied = {
        "category": category,
        "q": q,
        "sort_by": sort_by,
        "filters": filters.dict() if filters else None
    }

    return SearchResponse(
        items=paginated_products,
        total=total,
        page=page,
        per_page=per_page,
        filters_applied=filters_applied
    )
```

#### 🔍 自检
1. **简单搜索**：
   ```bash
   curl -X POST "http://localhost:8000/products/search/electronics?q=手机" \
     -H "Content-Type: application/json" \
     -d '{}'
   ```

2. **价格筛选**：
   ```bash
   curl -X POST "http://localhost:8000/products/search/electronics?sort_by=price_asc" \
     -H "Content-Type: application/json" \
     -d '{"price_range": {"min": 5000, "max": 10000}}'
   ```

3. **品牌筛选**：
   ```bash
   curl -X POST "http://localhost:8000/products/search/electronics" \
     -H "Content-Type: application/json" \
     -d '{"brands": ["Apple"], "in_stock": true}'
   ```

---

## 🔴 挑战练习 - 真实项目场景

### 练习 7：用户认证系统

#### 📝 目标
创建一个用户认证系统，包含：

**1. 注册** - `POST /auth/register`
- 用户名：3-20 字符，只能包含字母、数字、下划线
- 邮箱：必须是有效格式
- 密码：至少 8 个字符，必须包含字母和数字
- 确认密码：必须与密码一致

**2. 登录** - `POST /auth/login`
- 使用 Header 传递认证信息
- 返回 JWT token（模拟，不需要真实的 JWT）

**3. 获取当前用户** - `GET /auth/me`
- 从 Header 中读取 token
- 返回当前用户信息

#### 💡 提示
- 使用 Pydantic 的 `validator` 实现自定义校验
- 使用 `@root_validator` 实现密码确认校验
- 使用 `Header()` 函数从请求头中获取数据

#### ✅ 答案

```python
from fastapi import FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field, validator, root_validator
import re

app = FastAPI()

# ========== 数据模型 ==========

class UserRegister(BaseModel):
    """用户注册"""
    username: str = Field(..., min_length=3, max_length=20)
    email: str
    password: str = Field(..., min_length=8)
    password_confirm: str

    @validator('username')
    def username_alphanumeric(cls, v):
        """用户名只能包含字母、数字、下划线"""
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username can only contain letters, numbers, and underscores')
        return v

    @validator('password')
    def password_strength(cls, v):
        """密码必须包含字母和数字"""
        if not any(c.isalpha() for c in v):
            raise ValueError('Password must contain at least one letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v

    @root_validator
    def passwords_match(cls, values):
        """密码和确认密码必须一致"""
        password = values.get('password')
        password_confirm = values.get('password_confirm')
        if password != password_confirm:
            raise ValueError('Passwords do not match')
        return values

class UserLogin(BaseModel):
    """用户登录"""
    username: str
    password: str

class UserResponse(BaseModel):
    """用户响应"""
    id: int
    username: str
    email: str

class TokenResponse(BaseModel):
    """Token 响应"""
    access_token: str
    token_type: str = "bearer"

# ========== 模拟数据库和 Token 系统 ==========

fake_users_db: dict[str, dict] = {}
fake_tokens_db: dict[str, dict] = {}
user_id_counter = 1

def create_token(user_id: int) -> str:
    """创建模拟 token"""
    token = f"fake_token_{user_id}_{user_id_counter}"
    fake_tokens_db[token] = {"user_id": user_id}
    return token

def verify_token(token: str) -> dict | None:
    """验证 token"""
    return fake_tokens_db.get(token)

# ========== 认证接口 ==========

@app.post("/auth/register", response_model=UserResponse, status_code=201)
async def register(user: UserRegister):
    """用户注册"""
    global user_id_counter

    # 检查用户名是否已存在
    if user.username in fake_users_db:
        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )

    # 创建用户
    new_user = {
        "id": user_id_counter,
        "username": user.username,
        "email": user.email,
        "password": user.password  # 实际应用中应该哈希密码
    }

    fake_users_db[user.username] = new_user
    user_id_counter += 1

    return UserResponse(
        id=new_user["id"],
        username=new_user["username"],
        email=new_user["email"]
    )

@app.post("/auth/login", response_model=TokenResponse)
async def login(user: UserLogin, authorization: str = Header(None)):
    """用户登录"""
    # 验证用户名和密码
    db_user = fake_users_db.get(user.username)
    if not db_user or db_user["password"] != user.password:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    # 生成 token
    token = create_token(db_user["id"])

    return TokenResponse(access_token=token)

@app.get("/auth/me", response_model=UserResponse)
async def get_current_user(authorization: str = Header(...)):
    """获取当前用户"""
    # 提取 token
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format"
        )

    token = authorization.split(" ")[1]

    # 验证 token
    token_data = verify_token(token)
    if not token_data:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    # 查找用户
    user_id = token_data["user_id"]
    for username, user_data in fake_users_db.items():
        if user_data["id"] == user_id:
            return UserResponse(
                id=user_data["id"],
                username=user_data["username"],
                email=user_data["email"]
            )

    raise HTTPException(status_code=404, detail="User not found")
```

#### 🔍 自检
1. **测试注册**：
   ```bash
   curl -X POST "http://localhost:8000/auth/register" \
     -H "Content-Type: application/json" \
     -d '{
       "username": "alice",
       "email": "alice@example.com",
       "password": "password123",
       "password_confirm": "password123"
     }'
   ```

2. **测试登录**：
   ```bash
   curl -X POST "http://localhost:8000/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"username": "alice", "password": "password123"}'
   ```

3. **测试获取当前用户**：
   ```bash
   curl "http://localhost:8000/auth/me" \
     -H "Authorization: Bearer fake_token_1_1"
   ```

---

### 练习 8：日志流式输出（StreamingResponse）

#### 📝 目标
创建一个实时日志查看接口：

**`GET /logs/stream`**

**Query 参数**：
- `level`：日志级别（DEBUG, INFO, WARNING, ERROR）
- `tail`：只显示最后 N 行

**功能**：
1. 模拟实时生成日志
2. 使用 Server-Sent Events (SSE) 格式返回
3. 每秒生成一条日志
4. 最多返回 10 条日志后自动关闭

#### 💡 提示
- 使用异步生成器函数
- SSE 格式：`data: {json}\n\n`
- 使用 `asyncio.sleep()` 模拟延迟

#### ✅ 答案

```python
from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
import asyncio
import json
from datetime import datetime
from enum import Enum

app = FastAPI()

class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"

async def generate_logs(level: LogLevel, max_logs: int = 10):
    """生成日志流"""
    log_messages = [
        (LogLevel.INFO, "Application started"),
        (LogLevel.DEBUG, "Loading configuration"),
        (LogLevel.INFO, "Connecting to database"),
        (LogLevel.WARNING, "High memory usage detected"),
        (LogLevel.ERROR, "Failed to connect to cache"),
        (LogLevel.INFO, "Retrying connection"),
        (LogLevel.DEBUG, "Cache connection established"),
        (LogLevel.INFO, "Server ready to accept requests"),
        (LogLevel.WARNING, "Slow query detected"),
        (LogLevel.INFO, "Request processed successfully"),
    ]

    count = 0
    for log_level, message in log_messages:
        if count >= max_logs:
            break

        # 只返回指定级别及以上的日志
        level_order = {LogLevel.DEBUG: 0, LogLevel.INFO: 1, LogLevel.WARNING: 2, LogLevel.ERROR: 3}
        if level_order[log_level] >= level_order[level]:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "level": log_level,
                "message": message
            }

            # SSE 格式
            yield f"data: {json.dumps(log_entry)}\n\n"
            count += 1

        # 模拟实时生成
        await asyncio.sleep(1)

@app.get("/logs/stream")
async def stream_logs(
    level: LogLevel = Query(LogLevel.INFO, description="日志级别"),
    tail: int = Query(10, ge=1, le=50, description="最多返回行数")
):
    """流式返回日志"""
    return StreamingResponse(
        generate_logs(level, tail),
        media_type="text/event-stream"
    )
```

#### 🔍 自检
```bash
curl -N "http://localhost:8000/logs/stream?level=INFO&tail=5"
```
预期：看到实时生成的日志流

---

## 🎓 学习检验

完成所有练习后，回答以下问题来检验你的理解：

### 1. 概念理解
1. 什么时候使用 Path 参数，什么时候使用 Query 参数？
2. response_model 的作用是什么？为什么不直接返回数据库对象？
3. StreamingResponse 和普通 Response 有什么区别？
4. 如何在 Pydantic 模型中实现自定义校验？
5. HTTP 状态码 200、201、204、404、422 分别表示什么？

### 2. 实践能力
1. 你能独立实现一个完整的 CRUD API 吗？
2. 你知道如何处理文件上传和下载吗？
3. 你能设计安全的 API 响应结构吗？
4. 你知道如何实现数据验证和错误处理吗？

### 3. 进阶思考
1. 如果用户数据量很大（百万级），如何优化分页查询？
2. 如何设计 API 的版本控制？
3. 如何处理并发请求和数据一致性？

---

## 🚀 下一步

恭喜你完成了 Level 1 的所有练习！

**你已经掌握**：
- ✅ 请求参数校验（Path、Query、Body、Header、Cookie）
- ✅ 响应处理（JSON、Response Model、File、Streaming）
- ✅ HTTP 状态码和错误处理
- ✅ 完整的 CRUD API 设计

**接下来**：
- 📖 学习 **依赖注入系统**（Level 2）
- 📖 学习 **数据库集成**（Level 3）
- 📖 学习 **认证和授权**（Level 4）

继续加油！💪
