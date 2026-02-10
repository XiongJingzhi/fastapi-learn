# 01. 依赖注入基础 - Dependency Injection Basics

## 📍 在架构中的位置

**从 Level 1 到 Level 2：架构演进的关键一步**

```
┌─────────────────────────────────────────────────────────────┐
│              Level 1: 演示代码（没有依赖注入）                │
└─────────────────────────────────────────────────────────────┘

@app.post("/users")
async def create_user(user: UserCreate):
    # ❌ 所有逻辑都在 endpoint
    hashed = hash_password(user.password)
    result = db.insert("...", ...)
    return result

问题：
- 代码无法复用
- 难以测试
- 违反分层原则

═══════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────┐
│            Level 2: 生产架构（使用依赖注入）                  │
└─────────────────────────────────────────────────────────────┘

@app.post("/users")
async def create_user(
    user: UserCreate,
    service: UserService = Depends(get_user_service) ← 关键！
):
    # ✅ 只做协议适配
    return await service.create_user(user)

好处：
- 业务逻辑在 Service 层（可复用）
- 易于测试（注入 Mock）
- 符合分层架构
```

**🎯 你的学习目标**：掌握 `Depends` 的使用，理解它是如何让分层架构成为可能。

**⚠️ 架构意义**：这是**从演示代码到生产代码的关键转变**！

---

## 🎯 什么是依赖注入？

### 生活类比：点外卖

**场景 1：自己做饭（没有依赖注入）**

```python
# ❌ 你自己创建所有东西
class Person:
    def __init__(self):
        # 你需要自己做饭
        self.kitchen = Kitchen()      # 买厨房
        self.ingredients = Buy()      # 买菜
        self.cooking_skills = Learn()  # 学习厨艺

    def eat_lunch(self):
        # 自己做饭（麻烦！）
        return self.kitchen.cook(self.ingredients)

# 使用
alice = Person()  # 必须创建厨房、买菜、学习
alice.eat_lunch()
```

**问题**：
- 你必须知道如何创建厨房
- 你必须知道如何买菜
- 如果要换菜谱，必须重新学习

---

**场景 2：点外卖（使用依赖注入）**

```python
# ✅ 别人做好送来
class Person:
    def __init__(self, food_service: FoodDelivery):
        # 只需要知道"有外卖服务"
        self.food_service = food_service

    def eat_lunch(self):
        # 直接吃（简单！）
        return self.food_service.deliver_lunch()

# 外面有人负责准备
food_service = FoodDelivery(kitchen, ingredients, chef)
alice = Person(food_service)  # 注入外卖服务
alice.eat_lunch()
```

**好处**：
- 你不需要知道饭怎么做
- 你可以换不同的外卖服务
- 测试时可以注入"模拟外卖"（如预制菜）

---

### 代码中的"依赖"是什么？

**依赖 (Dependency)**：一个对象需要另一个对象才能完成工作。

```python
# UserService 依赖 UserRepository
class UserService:
    def __init__(self):
        # ❌ 自己创建依赖
        self.repo = UserRepository()

# 问题：UserService 必须知道如何创建 UserRepository
```

**依赖注入 (Dependency Injection, DI)**：
- 不自己创建依赖
- 让别人提供给你
- 你只负责使用

```python
# ✅ 使用依赖注入
class UserService:
    def __init__(self, repo: UserRepository):
        # 依赖作为参数传入（别人提供）
        self.repo = repo

# 外部负责创建和注入
repo = UserRepository()
service = UserService(repo)  # 注入依赖
```

---

## 🤔 为什么需要依赖注入？

### 三大核心好处

#### 1. 解耦 - 不关心如何创建

```python
# ❌ 紧耦合
class UserService:
    def __init__(self):
        # 必须知道如何创建 PostgreSQL 连接
        self.db = PostgreSQL(
            host="localhost",
            port=5432,
            user="alice",
            password="secret"
        )

# 问题：想换数据库？必须改 UserService 代码！
```

```python
# ✅ 解耦
class UserService:
    def __init__(self, db: Database):
        # 只关心接口，不关心具体实现
        self.db = db

# 好处：可以注入 PostgreSQL、MySQL、MongoDB...
pg_db = PostgreSQL(...)
service1 = UserService(pg_db)

mysql_db = MySQL(...)
service2 = UserService(mysql_db)
```

---

#### 2. 可测试 - 注入 Mock 对象

```python
# ❌ 难以测试
class UserService:
    def __init__(self):
        self.db = PostgreSQL()  # 必须连接真实数据库

    async def get_user(self, user_id: int):
        return await self.db.query(f"SELECT * FROM users WHERE id = {user_id}")

# 测试时必须启动真实的 PostgreSQL！（慢、复杂）
async def test_get_user():
    service = UserService()  # 需要数据库连接！
    user = await service.get_user(1)
    assert user.name == "Alice"
```

```python
# ✅ 易于测试
class UserService:
    def __init__(self, db: Database):
        self.db = db

    async def get_user(self, user_id: int):
        return await self.db.find_by_id(user_id)

# 测试时注入 Mock（不需要数据库！）
class MockDatabase(Database):
    def __init__(self):
        self.users = {
            1: User(id=1, name="Alice"),
            2: User(id=2, name="Bob"),
        }

    async def find_by_id(self, user_id: int):
        return self.users.get(user_id)

# 测试（快速、简单）
async def test_get_user():
    mock_db = MockDatabase()
    service = UserService(mock_db)  # 注入 Mock
    user = await service.get_user(1)
    assert user.name == "Alice"  # ✅ 测试通过
```

---

#### 3. 可复用 - 多处使用同一个逻辑

```python
# ✅ 业务逻辑在 Service 层，可以多处复用

class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def create_user(self, user_data: UserCreate) -> User:
        # 业务逻辑：检查邮箱是否已存在
        if await self.repo.email_exists(user_data.email):
            raise ValueError("Email already exists")

        # 业务逻辑：创建用户
        user = User.create(user_data)
        return await self.repo.save(user)

# 处处可以复用！

# HTTP API
@app.post("/users")
async def http_create_user(
    user: UserCreate,
    service: UserService = Depends(get_user_service)
):
    return await service.create_user(user)

# CLI 工具
async def cli_create_user(username: str, email: str):
    service = get_user_service()  # 同样的 Service
    return await service.create_user(UserCreate(username=username, email=email))

# gRPC 接口
async def grpc_create_user(request, context):
    service = get_user_service()  # 同样的 Service
    return await service.create_user(UserCreate(**request.dict()))
```

---

## 📦 FastAPI 的 Depends：如何使用？

### 基本语法

```python
from fastapi import FastAPI, Depends

app = FastAPI()

# 1️⃣ 定义依赖（一个函数）
def get_user_service():
    """这个函数负责创建 UserService"""
    db = get_db()
    repo = UserRepository(db)
    return UserService(repo)

# 2️⃣ 使用依赖（在 endpoint 中）
@app.post("/users")
async def create_user(
    user: UserCreate,
    service: UserService = Depends(get_user_service)  # ← 关键！
):
    # FastAPI 会自动调用 get_user_service()
    # 并把返回值注入到 service 参数
    return await service.create_user(user)
```

**工作流程**：

```
HTTP 请求到达
    │
    ▼
FastAPI 看到：service: UserService = Depends(get_user_service)
    │
    ▼
FastAPI 自动调用：get_user_service()
    │
    ├─→ 创建 Database
    ├─→ 创建 UserRepository
    └─→ 返回 UserService
    │
    ▼
FastAPI 把 UserService 注入到 endpoint
    │
    ▼
Endpoint 执行：await service.create_user(user)
```

---

### 对比：没有 DI vs 有 DI

#### ❌ 没有 DI（Level 1 风格）

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

@app.post("/users")
async def create_user(user: UserCreate):
    # ❌ 所有逻辑都在 endpoint

    # 1. 校验业务规则
    existing = db.query("SELECT * FROM users WHERE email = ?", user.email)
    if existing:
        raise HTTPException(400, "Email already exists")

    # 2. 处理数据
    hashed = hash_password(user.password)

    # 3. 保存到数据库
    user_id = db.insert(
        "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
        user.username, user.email, hashed
    )

    # 4. 返回结果
    return {"id": user_id, "username": user.username}

# 问题：
# - 代码无法复用（CLI 工具需要重写）
# - 难以测试（必须启动 HTTP 服务器和数据库）
# - 职责混乱（HTTP + 业务 + 数据库混在一起）
```

---

#### ✅ 使用 DI（Level 2 风格）

```python
from fastapi import FastAPI, Depends
from pydantic import BaseModel

app = FastAPI()

# ═══════════════════════════════════════════════════════════
# 1. 定义依赖
# ═══════════════════════════════════════════════════════════

def get_db():
    """数据库连接"""
    return Database()

def get_user_repo(db: Database = Depends(get_db)):
    """用户仓储"""
    return UserRepository(db)

def get_user_service(repo: UserRepository = Depends(get_user_repo)):
    """用户服务（业务逻辑在这里！）"""
    return UserService(repo)

# ═══════════════════════════════════════════════════════════
# 2. Service 层：业务逻辑
# ═══════════════════════════════════════════════════════════

class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def create_user(self, user_data: UserCreate) -> User:
        # ✅ 业务逻辑在这里

        # 1. 校验业务规则
        if await self.repo.email_exists(user_data.email):
            raise ValueError("Email already exists")

        # 2. 创建用户
        user = User.create(user_data)
        user.hash_password()

        # 3. 保存
        return await self.repo.save(user)

# ═══════════════════════════════════════════════════════════
# 3. Endpoint：只做协议适配
# ═══════════════════════════════════════════════════════════

@app.post("/users")
async def create_user(
    user: UserCreate,
    service: UserService = Depends(get_user_service)  # ← 注入依赖
):
    # ✅ 只做协议适配
    return await service.create_user(user)

# 好处：
# - 代码可复用（Service 可以在 CLI/gRPC 中使用）
# - 易于测试（注入 Mock，不需要数据库）
# - 职责清晰（HTTP 层只做适配，业务逻辑在 Service）
```

---

## 🔗 依赖链：Depends 可以嵌套

### 简单的依赖链

```python
# ═══════════════════════════════════════════════════════════
# 依赖 1：数据库连接
# ═══════════════════════════════════════════════════════════

def get_db() -> Database:
    """创建数据库连接"""
    return Database(host="localhost", port=5432)

# ═══════════════════════════════════════════════════════════
# 依赖 2：仓储（依赖数据库）
# ═══════════════════════════════════════════════════════════

def get_user_repo(db: Database = Depends(get_db)) -> UserRepository:
    """
    创建用户仓储
    - FastAPI 看到这个函数需要 db
    - 自动调用 get_db()
    - 把 db 注入到这个函数
    """
    return UserRepository(db)

# ═══════════════════════════════════════════════════════════
# 依赖 3：服务（依赖仓储）
# ═══════════════════════════════════════════════════════════

def get_user_service(
    repo: UserRepository = Depends(get_user_repo)
) -> UserService:
    """
    创建用户服务
    - FastAPI 看到这个函数需要 repo
    - 自动调用 get_user_repo()
    - get_user_repo() 又需要 db
    - 自动调用 get_db()
    - 整个依赖链自动解析！
    """
    return UserService(repo)

# ═══════════════════════════════════════════════════════════
# 使用：Endpoint
# ═══════════════════════════════════════════════════════════

@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service)  # ← 顶层依赖
):
    # FastAPI 自动解析整个依赖链：
    # service → repo → db
    return await service.get_user(user_id)
```

**依赖链示意图**：

```
Endpoint: get_user
    │
    │ Depends(get_user_service)
    ▼
Service: get_user_service
    │
    │ Depends(get_user_repo)
    ▼
Repo: get_user_repo
    │
    │ Depends(get_db)
    ▼
DB: get_db
    │
    └─→ 返回 Database
         │
         └─→ 返回 UserRepository
              │
              └─→ 返回 UserService
                   │
                   └─→ 注入到 Endpoint
```

---

### 依赖链的好处

**1. 自动管理创建顺序**

```python
# FastAPI 自动按顺序创建：
# 1. get_db() → Database
# 2. get_user_repo(db) → UserRepository
# 3. get_user_service(repo) → UserService

# 你不需要手动写：
db = get_db()
repo = get_user_repo(db)
service = get_user_service(repo)
```

**2. 自动缓存（同一个请求中）**

```python
@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    service1: UserService = Depends(get_user_service),
    service2: UserService = Depends(get_user_service),
):
    # service1 和 service2 是同一个实例！
    assert service1 is service2  # True

# FastAPI 不会重复创建，而是复用
```

**3. 依赖可复用**

```python
# 多个 endpoint 可以复用同一个依赖

@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service)  # 复用
):
    return await service.get_user(user_id)

@app.post("/users")
async def create_user(
    user: UserCreate,
    service: UserService = Depends(get_user_service)  # 复用
):
    return await service.create_user(user)

@app.put("/users/{user_id}")
async def update_user(
    user_id: int,
    user: UserUpdate,
    service: UserService = Depends(get_user_service)  # 复用
):
    return await service.update_user(user_id, user)
```

---

## 🎨 实际例子：完整的用户注册

### 让我们看一个完整的例子

```python
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, EmailStr

app = FastAPI()

# ═══════════════════════════════════════════════════════════
# 1. 数据模型
# ═══════════════════════════════════════════════════════════

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str

# ═══════════════════════════════════════════════════════════
# 2. 模拟数据库
# ═══════════════════════════════════════════════════════════

class FakeDatabase:
    def __init__(self):
        self.users = {}
        self.next_id = 1

    def save_user(self, username: str, email: str, password: str) -> int:
        user_id = self.next_id
        self.users[user_id] = {
            "id": user_id,
            "username": username,
            "email": email,
            "password": password
        }
        self.next_id += 1
        return user_id

    def email_exists(self, email: str) -> bool:
        return any(u["email"] == email for u in self.users.values())

# ═══════════════════════════════════════════════════════════
# 3. Service 层：业务逻辑
# ═══════════════════════════════════════════════════════════

class UserService:
    def __init__(self, db: FakeDatabase):
        self.db = db

    async def create_user(self, user_data: UserCreate) -> dict:
        """创建用户的业务逻辑"""

        # 1. 业务规则：检查邮箱是否已存在
        if self.db.email_exists(user_data.email):
            raise ValueError("Email already registered")

        # 2. 业务逻辑：创建用户
        user_id = self.db.save_user(
            username=user_data.username,
            email=user_data.email,
            password=hash_password(user_data.password)  # 哈希密码
        )

        # 3. 返回用户信息
        return {
            "id": user_id,
            "username": user_data.username,
            "email": user_data.email
        }

# ═══════════════════════════════════════════════════════════
# 4. 依赖注入：组装依赖
# ═══════════════════════════════════════════════════════════

def get_database() -> FakeDatabase:
    """依赖：数据库连接"""
    return FakeDatabase()

def get_user_service(
    db: FakeDatabase = Depends(get_database)
) -> UserService:
    """
    依赖：用户服务
    - FastAPI 自动调用 get_database()
    - 把 db 注入到这里
    - 返回 UserService(db)
    """
    return UserService(db)

# ═══════════════════════════════════════════════════════════
# 5. Endpoint：只做协议适配
# ═══════════════════════════════════════════════════════════

@app.post("/users", response_model=UserResponse, status_code=201)
async def create_user(
    user: UserCreate,
    service: UserService = Depends(get_user_service)  # ← 注入依赖
):
    """
    创建用户

    Endpoint 只负责：
    1. 接收 HTTP 请求（FastAPI 自动）
    2. 校验请求格式（Pydantic 自动）
    3. 调用 Service（依赖注入自动）
    4. 返回 HTTP 响应（FastAPI 自动）
    """
    try:
        result = await service.create_user(user)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

**测试一下**：

```bash
# 测试 1：正常注册
curl -X POST "http://localhost:8000/users" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "email": "alice@example.com",
    "password": "secret123"
  }'

# 响应：
# {
#   "id": 1,
#   "username": "alice",
#   "email": "alice@example.com"
# }

# 测试 2：邮箱重复
curl -X POST "http://localhost:8000/users" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "bob",
    "email": "alice@example.com",
    "password": "secret456"
  }'

# 响应：
# {
#   "detail": "Email already registered"
# }
```

---

## 🔍 依赖注入让代码变简洁？

### 对比代码量

```python
# ❌ 没有 DI：每个 endpoint 都要重复创建依赖

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    db = get_db()  # 重复
    repo = UserRepository(db)  # 重复
    service = UserService(repo)  # 重复
    return await service.get_user(user_id)

@app.post("/users")
async def create_user(user: UserCreate):
    db = get_db()  # 重复
    repo = UserRepository(db)  # 重复
    service = UserService(repo)  # 重复
    return await service.create_user(user)

@app.put("/users/{user_id}")
async def update_user(user_id: int, user: UserUpdate):
    db = get_db()  # 重复
    repo = UserRepository(db)  # 重复
    service = UserService(repo)  # 重复
    return await service.update_user(user_id, user)

# 问题：每个 endpoint 都有相同的"样板代码"


# ✅ 使用 DI：依赖定义一次，到处复用

def get_user_service(
    db: Database = Depends(get_db),
    repo: UserRepository = Depends(get_user_repo)
) -> UserService:
    return UserService(repo)

@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service)  # 一行搞定
):
    return await service.get_user(user_id)

@app.post("/users")
async def create_user(
    user: UserCreate,
    service: UserService = Depends(get_user_service)  # 复用
):
    return await service.create_user(user)

@app.put("/users/{user_id}")
async def update_user(
    user_id: int,
    user: UserUpdate,
    service: UserService = Depends(get_user_service)  # 复用
):
    return await service.update_user(user_id, user)

# 好处：
# - 依赖定义一次，到处复用
# - Endpoint 代码简洁清晰
# - 没有重复的"样板代码"
```

---

## 🎯 小实验：自己动手

### 实验 1：创建简单的依赖

**目标**：创建一个返回当前时间的依赖

```python
from fastapi import FastAPI, Depends
from datetime import datetime
from pydantic import BaseModel

app = FastAPI()

class InfoResponse(BaseModel):
    message: str
    current_time: str

# 1. 定义依赖：返回当前时间
def get_current_time() -> str:
    """返回当前时间"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 2. 使用依赖
@app.get("/info", response_model=InfoResponse)
async def get_info(
    current_time: str = Depends(get_current_time)  # ← 注入时间
):
    return {
        "message": "Hello!",
        "current_time": current_time
    }
```

**测试**：
```bash
curl "http://localhost:8000/info"
# 返回：
# {
#   "message": "Hello!",
#   "current_time": "2024-01-15 10:30:45"
# }
```

---

### 实验 2：依赖链

**目标**：创建一个依赖链

```python
from fastapi import FastAPI, Depends
from pydantic import BaseModel

app = FastAPI()

# 1. 依赖 1：返回配置
def get_config() -> dict:
    """返回配置"""
    return {
        "app_name": "My API",
        "version": "1.0.0",
        "debug": True
    }

# 2. 依赖 2：依赖配置
def get_app_info(config: dict = Depends(get_config)) -> str:
    """依赖配置，返回应用信息"""
    return f"{config['app_name']} v{config['version']}"

# 3. Endpoint：使用依赖 2
@app.get("/about")
async def about(
    app_info: str = Depends(get_app_info)  # ← 自动解析依赖链
):
    # FastAPI 自动：
    # 1. 调用 get_config()
    # 2. 调用 get_app_info(config)
    # 3. 把 app_info 注入到这里
    return {"app_info": app_info}
```

**测试**：
```bash
curl "http://localhost:8000/about"
# 返回：
# {
#   "app_info": "My API v1.0.0"
# }
```

---

### 实验 3：带参数的依赖

**目标**：创建一个需要参数的依赖

```python
from fastapi import FastAPI, Depends
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float

# 依赖：检查权限
def check_permission(user_id: int):
    """检查用户权限"""
    if user_id < 1:
        raise HTTPException(403, "Forbidden")

    # 返回用户信息
    return {
        "user_id": user_id,
        "is_admin": user_id == 1
    }

@app.get("/items/{item_id}")
async def get_item(
    item_id: int,
    user: dict = Depends(check_permission)  # ← 需要传入 user_id
):
    return {
        "item_id": item_id,
        "user": user
    }

# 问题：user_id 从哪里来？
```

**思考**：如何传入 `user_id`？

<details>
<summary>点击查看答案</summary>

```python
# 方案 1：从 Path 参数获取
@app.get("/items/{item_id}/users/{user_id}")
async def get_item(
    item_id: int,
    user_id: int,  # Path 参数
    user: dict = Depends(check_permission)  # FastAPI 自动注入 user_id
):
    return {"item_id": item_id, "user": user}

# 方案 2：使用可调用对象（下节课学习）
```

</details>

---

## 📚 检查理解

回答这些问题来测试你的理解：

1. **什么是依赖？**
   - 提示：一个对象需要另一个对象才能工作

2. **什么是依赖注入？**
   - 提示：不自己创建，让别人提供

3. **FastAPI 中如何使用依赖注入？**
   - 提示：使用 `Depends()` 函数

4. **依赖注入有什么好处？**
   - 提示：解耦、可测试、可复用

5. **什么是依赖链？**
   - 提示：Depends 可以嵌套，A 依赖 B，B 依赖 C

---

## 🚀 下一步

现在你已经理解了依赖注入的基本概念，接下来：

1. **查看实际代码**：`examples/02_di_basics.py`
2. **运行并测试**：观察依赖注入的工作流程
3. **学习下一课**：`notes/02_class_vs_function.md`（类依赖 vs 函数依赖）

**记住**：依赖注入是从演示代码到生产架构的关键一步！

---

**费曼技巧总结**：
- ✅ 用简单的类比（点外卖）
- ✅ 对比没有 DI vs 有 DI
- ✅ 展示依赖链的工作原理
- ✅ 提供可运行的完整例子
- ✅ 小实验巩固理解
