# 00 架构总览 - FastAPI 的分层设计

## 📖 为什么需要理解架构？

在深入学习 FastAPI 的具体功能之前，我们需要从架构高度理解 FastAPI 在整个系统中的位置。这能帮助我们：

1. **理解职责边界** - 知道什么该在 FastAPI 层做，什么不该做
2. **设计可扩展的系统** - 为后续 Level 2-5 的演进打好基础
3. **避免常见陷阱** - 比如在 endpoint 中写业务逻辑
4. **做出正确的技术决策** - 知道何时用 FastAPI，何时用其他工具

---

## 🏗️ FastAPI 整体分层架构

### 系统分层视图

```
┌─────────────────────────────────────────────────────────────┐
│                        客户端层                              │
│                   (Web/Mobile/API)                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   【传输层 / Transport Layer】                │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              FastAPI 应用 (协议适配)                   │   │
│  │  • 路由匹配      → @app.get("/users/{id}")            │   │
│  │  • 参数校验      → Pydantic Models                    │   │
│  │  • 响应序列化    → JSON/HTML/File                     │   │
│  │  • 错误处理      → HTTPException                      │   │
│  │  • 认证授权      → Depends(get_current_user)          │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  职责: "把 HTTP 协议翻译成 Python 对象"                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   【服务层 / Service Layer】                  │
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │  UserService     │  │  OrderService    │                │
│  │  • create_user() │  │  • place_order() │                │
│  │  • get_user()    │  │  • cancel()      │                │
│  │  • update_user() │  │  • list_orders() │                │
│  └──────────────────┘  └──────────────────┘                │
│                                                              │
│  职责: "编排业务逻辑，不关心 HTTP 细节"                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   【领域层 / Domain Layer】                   │
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │  User (实体)     │  │  Order (实体)    │                │
│  │  • 属性验证      │  │  • 状态转换      │                │
│  │  • 业务规则      │  │  • 业务规则      │                │
│  │  • 领域事件      │  │  • 领域事件      │                │
│  └──────────────────┘  └──────────────────┘                │
│                                                              │
│  职责: "核心业务逻辑，与框架无关"                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│               【基础设施层 / Infrastructure Layer】            │
│                                                              │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │
│  │Database │ │  Redis  │ │  Kafka  │ │  Email  │          │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘          │
│                                                              │
│  职责: "提供技术能力，实现仓储接口"                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 每层的关键职责

### 传输层 (Transport Layer) - FastAPI 的领地

**为什么叫"传输层"？**

因为这层负责处理数据传输的协议细节（HTTP），让上层不需要关心网络通信。

**FastAPI 在这里做什么？**

```python
# ✅ 传输层应该做的事
@app.post("/users")                                  # 路由匹配
async def create_user(                              # 协议适配
    user: UserCreate,                               # 请求校验
    service: UserService = Depends()                # 依赖注入
):
    result = await service.create_user(user)        # 调用服务层
    return {"code": 200, "data": result}            # 响应序列化
```

**核心职责**：
1. **路由匹配** - 将 URL 映射到处理函数
2. **参数校验** - 验证请求参数的合法性
3. **协议转换** - HTTP 请求 ←→ Python 对象
4. **响应格式化** - Python 对象 ←→ HTTP 响应
5. **错误映射** - 异常 ←→ HTTP 状态码

**❌ 不应该做的事**：
- ❌ 直接操作数据库
- ❌ 编写业务规则（如"用户余额不能小于0"）
- ❌ 调用外部 API（如发送邮件）
- ❌ 复杂的数据处理逻辑

**为什么？**
- 违反单一职责原则
- 难以测试（需要模拟 HTTP 请求）
- 难以复用（业务逻辑被绑在 HTTP 层）
- 难以演进（如添加 gRPC 接口）

---

### 服务层 (Service Layer) - 业务逻辑的编排者

```python
# ✅ 服务层应该做的事
class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def create_user(self, user_data: UserCreate):
        # 1. 业务规则验证
        if await self.user_repo.exists_by_email(user_data.email):
            raise ValueError("Email already exists")

        # 2. 编排领域操作
        user = User.create(user_data)
        user.hash_password()  # 领域逻辑

        # 3. 持久化
        await self.user_repo.save(user)

        # 4. 触发副作用（通过领域事件）
        user.publish_event(UserCreated(user_id=user.id))

        return user
```

**核心职责**：
1. **编排业务流程** - 协调多个领域对象
2. **事务边界** - 控制数据库事务的起止
3. **领域事件触发** - 发布业务事件
4. **用例实现** - 对应用户的具体操作

---

### 领域层 (Domain Layer) - 核心业务逻辑

```python
# ✅ 领域层应该做的事
class User:
    def __init__(self, name: str, email: str, password: str):
        self.name = name
        self.email = email
        self.password = password
        self._events = []

    def hash_password(self):
        """核心业务逻辑，与框架无关"""
        if not self.password:
            raise ValueError("Password is required")
        self.password = bcrypt.hash(self.password)

    def verify_password(self, raw: str) -> bool:
        """核心业务逻辑"""
        return bcrypt.verify(raw, self.password)

    def change_email(self, new_email: str):
        """业务规则：邮件必须唯一"""
        if not self.is_valid_email(new_email):
            raise ValueError("Invalid email")
        self.email = new_email
        self._events.append(UserEmailChanged(self.id, new_email))
```

**核心职责**：
1. **实体行为** - 对象的状态转换规则
2. **业务规则** - 不变的业务约束
3. **领域事件** - 业务中发生的重要事情

**关键特点**：
- **不依赖任何框架** - 可以独立于 FastAPI 运行
- **可单独测试** - 不需要 HTTP 环境
- **业务语言** - 代码使用业务术语

---

### 基础设施层 (Infrastructure Layer)

```python
# ✅ 基础设施层应该做的事
class UserRepository(abc.ABC):
    """仓储接口（在领域层定义）"""

    @abc.abstractmethod
    async def save(self, user: User) -> User:
        pass

    @abc.abstractmethod
    async def find_by_id(self, user_id: int) -> Optional[User]:
        pass


class SQLUserRepository(UserRepository):
    """SQL 实现（在基础设施层实现）"""

    def __init__(self, db_session: AsyncSession):
        self.session = db_session

    async def save(self, user: User) -> User:
        self.session.add(user)
        await self.session.commit()
        return user

    async def find_by_id(self, user_id: int) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
```

**核心职责**：
1. **持久化** - 数据库操作
2. **外部集成** - 调用第三方 API
3. **技术支持** - 缓存、消息队列等

---

## 🔄 层次组装与协调 - 由下而上的视角

前面的内容是从"由上而下"的视角（客户端 → 传输层 → 服务层），现在我们换个角度，从"由下而上"理解各层如何组装和协调。

### 系统的"骨骼"与"肌肉"

```
如果把系统比作一个人：

┌─────────────────────────────────────────────────────────────┐
│  皮肤和感官      ← 传输层 (FastAPI)                         │
│  • 接触外界（接收请求）                                       │
│  • 表达自己（返回响应）                                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  大脑            ← 服务层 (Service)                         │
│  • 协调行动（编排业务流程）                                   │
│  • 做决策（应用业务规则）                                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  知识和经验    ← 领域层 (Domain)                            │
│  • 核心能力（业务逻辑）                                       │
│  • 行为模式（实体规则）                                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  记忆和工具      ← 基础设施层 (Infrastructure)               │
│  • 存储信息（数据库）                                         │
│  • 使用工具（外部服务）                                       │
└─────────────────────────────────────────────────────────────┘
```

### 从数据库开始：由下而上的构建

让我们从最底层开始，看系统是如何一层层构建起来的。

#### 第 0 步：基础设施层 - 准备技术能力

```python
# 1. 数据库连接
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

engine = create_async_engine("postgresql+asyncpg://...")
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# 2. 仓储实现（基础设施层）
class SQLUserRepository(UserRepository):  # 实现领域定义的接口
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, user: User) -> User:
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def find_by_id(self, user_id: int) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
```

**这一层的价值**：
- 提供"技术能力"（SQL、网络调用等）
- 实现"接口约定"（由 Domain 层定义的 Repository 接口）
- 可以随时替换（如从 PostgreSQL 换到 MySQL）

---

#### 第 1 步：领域层 - 定义核心业务

```python
# 1. 领域接口（在领域层定义）
from abc import ABC, abstractmethod
from typing import Optional

class UserRepository(ABC):
    """用户仓储接口（由领域层定义，由基础设施层实现）"""

    @abstractmethod
    async def save(self, user: User) -> User:
        pass

    @abstractmethod
    async def find_by_id(self, user_id: int) -> Optional[User]:
        pass

# 2. 领域实体（核心业务逻辑）
class User:
    """用户实体（包含业务规则）"""

    def __init__(self, name: str, email: str, password: str):
        self.id = None
        self.name = name
        self.email = email
        self.password = password
        self._events = []  # 领域事件

    def hash_password(self):
        """业务规则：密码必须哈希"""
        if not self.password:
            raise ValueError("Password is required")
        self.password = bcrypt.hash(self.password)

    def verify_password(self, raw: str) -> bool:
        """业务规则：验证密码"""
        return bcrypt.verify(raw, self.password)

    def change_email(self, new_email: str):
        """业务规则：邮箱变更需要验证"""
        if not self.is_valid_email(new_email):
            raise ValueError("Invalid email format")
        old_email = self.email
        self.email = new_email
        self._events.append(UserEmailChanged(self.id, old_email, new_email))
```

**这一层的价值**：
- **不依赖任何框架** - 可以独立运行和测试
- **包含核心业务逻辑** - 密码哈希、邮箱验证等
- **定义接口契约** - UserRepository 接口

---

#### 第 2 步：服务层 - 编排业务流程

```python
# 依赖注入：组装依赖
def get_user_service() -> UserService:
    """创建 UserService 实例（由下而上组装）"""
    # 1. 获取数据库会话（基础设施）
    session = Depends(get_db)

    # 2. 创建仓储（基础设施实现）
    repo = SQLUserRepository(session)

    # 3. 创建服务（依赖仓储）
    return UserService(repo)


class UserService:
    """用户服务（编排业务逻辑）"""

    def __init__(self, user_repo: UserRepository):
        # 依赖抽象，不依赖具体实现
        self.user_repo = user_repo

    async def create_user(self, user_data: UserCreate) -> User:
        """创建用户（编排业务流程）"""
        # 1. 业务规则：检查邮箱是否唯一
        existing = await self.user_repo.find_by_email(user_data.email)
        if existing:
            raise UserEmailExistsException(user_data.email)

        # 2. 创建领域对象
        user = User(
            name=user_data.name,
            email=user_data.email,
            password=user_data.password
        )

        # 3. 执行领域逻辑
        user.hash_password()  # 领域对象的行为

        # 4. 持久化（通过仓储接口）
        saved_user = await self.user_repo.save(user)

        # 5. 发布领域事件
        for event in user._events:
            await self.event_publisher.publish(event)

        return saved_user
```

**这一层的价值**：
- **编排多个领域对象** - 协调 User、EmailValidator 等
- **事务边界** - 控制数据库事务的起止
- **用例实现** - 对应用户的具体操作（创建用户）

---

#### 第 3 步：传输层 - 对外暴露接口

```python
from fastapi import FastAPI, Depends, HTTPException

app = FastAPI()

@app.post("/users")
async def create_user(
    user_data: UserCreate,
    service: UserService = Depends(get_user_service)  # 自动注入
):
    """
    创建用户端点

    职责：协议适配
    1. 接收 HTTP 请求
    2. 校验参数（Pydantic 自动完成）
    3. 调用服务
    4. 返回 HTTP 响应
    """
    try:
        # 调用服务层
        user = await service.create_user(user_data)

        # 返回响应
        return {
            "code": 201,
            "message": "创建成功",
            "data": {
                "id": user.id,
                "name": user.name,
                "email": user.email
            }
        }
    except UserEmailExistsException as e:
        # 捕获领域异常，转换为 HTTP 响应
        raise HTTPException(status_code=409, detail=str(e))
```

**这一层的价值**：
- **协议适配** - HTTP ↔ Python 对象
- **参数校验** - Pydantic 自动完成
- **响应格式化** - 统一的 JSON 格式

---

### 完整的数据流动图

```
┌─────────────────────────────────────────────────────────────────┐
│                     HTTP Request                                │
│              POST /users {"name": "张三", "email": "..."}       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              FastAPI Endpoint (传输层)                           │
│                                                                  │
│  1. 接收 HTTP 请求                                               │
│  2. Pydantic 校验参数自动完成                                    │
│  3. Depends(get_user_service) 自动注入依赖                      │
│     ┌──────────────────────────────────────────────┐            │
│     │  FastAPI 的依赖注入链：                       │            │
│     │                                                │            │
│     │  get_db()                                     │            │
│     │    ↓ (提供数据库会话)                          │            │
│     │  SQLUserRepository(session)                   │            │
│     │    ↓ (创建仓储)                                │            │
│     │  UserRepository(repo)                         │            │
│     │    ↓ (创建服务)                                │            │
│     │  UserService ──────────────┐                  │            │
│     └────────────────────────────┼──────────────────┘            │
│                                  │                               │
│  4. service.create_user(user) ───┘ (调用服务层)                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              UserService (服务层)                                │
│                                                                  │
│  1. 接收 UserCreate 数据                                        │
│  2. 调用 self.user_repo.find_by_email() ────┐                  │
│  3. 创建 User 领域对象                       │                  │
│  4. 调用 user.hash_password() (领域逻辑)      │                  │
│  5. 调用 self.user_repo.save(user) ───────────┤                  │
│  6. 发布领域事件                             │                  │
│                                             │                  │
│  (通过 UserRepository 接口调用基础设施层) ────┘                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              SQLUserRepository (基础设施层)                      │
│                                                                  │
│  1. 执行 SQL: SELECT * FROM users WHERE email = ?              │
│  2. 执行 SQL: INSERT INTO users (...) VALUES (...)             │
│  3. 返回 User 对象                                              │
│                                                                  │
│  (与 PostgreSQL 数据库通信)                                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              Database (PostgreSQL)                               │
│                                                                  │
│  • 存储用户数据                                                  │
│  • 执行 SQL 语句                                                │
│  • 返回查询结果                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▲ (数据开始返回)
                              │
┌─────────────────────────────────────────────────────────────────┐
│              SQLUserRepository 返回 User 对象                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              UserService 返回 User 对象                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              FastAPI Endpoint                                   │
│                                                                  │
│  1. 接收 User 对象                                              │
│  2. 序列化为 JSON: {                                             │
│       "code": 201,                                               │
│       "message": "创建成功",                                     │
│       "data": {"id": 1, "name": "张三", "email": "..."}         │
│     }                                                           │
│  3. 返回 HTTP Response (Status 201)                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              HTTP Response                                      │
│     Status: 201 Created                                         │
│     Body: {"code": 201, "message": "创建成功", "data": {...}}   │
└─────────────────────────────────────────────────────────────────┘
```

### 层次间的依赖关系

```
┌─────────────────────────────────────────────────────────────────┐
│                    依赖关系总结                                  │
└─────────────────────────────────────────────────────────────────┘

FastAPI (传输层)
    │  依赖：UserService 接口
    │  不需要知道：User 如何创建、数据如何存储
    ▼
UserService (服务层)
    │  依赖：UserRepository 接口、User 领域对象
    │  不需要知道：具体是 SQL 还是 NoSQL
    ▼
UserRepository (接口)
    │  定义在：Domain 层
    │  实现在：Infrastructure 层
    ▼
Domain (领域层)
    │  核心：User 实体、业务规则
    │  不依赖：任何框架或基础设施
    ▲
    │ 实现
    │
SQLUserRepository (基础设施层)
    │  依赖：数据库驱动
    │  职责：SQL 语句、数据库连接
    ▼
Database (数据库)
```

### 关键设计原则

#### 1. 依赖倒置 (Dependency Inversion)

```python
# ❌ 错误：高层依赖低层
class UserService:
    def __init__(self):
        self.repo = SQLUserRepository()  # 依赖具体实现

# ✅ 正确：高层依赖抽象
class UserService:
    def __init__(self, repo: UserRepository):  # 依赖接口
        self.repo = repo
```

#### 2. 接口隔离 (Interface Segregation)

```python
# Domain 层定义接口
class UserRepository(ABC):
    @abstractmethod
    async def save(self, user: User) -> User: ...

# Infrastructure 层实现接口
class SQLUserRepository(UserRepository):
    async def save(self, user: User) -> User:
        # SQL 实现...

# 也可以有其他实现
class MongoUserRepository(UserRepository):
    async def save(self, user: User) -> User:
        # MongoDB 实现...
```

#### 3. 单一职责 (Single Responsibility)

```
每层只做一件事：

FastAPI      → 协议适配 (HTTP ↔ Python)
Service      → 编排业务 (协调多个领域对象)
Domain       → 业务逻辑 (实体行为和规则)
Repository   → 数据持久化 (SQL 执行)
```

---

## 🎨 传输层深度解析

### 传输层的本质：协议适配

**什么是协议适配？**

协议适配就是把"外部的协议"翻译成"内部的对象"。

```
外部世界（HTTP）          内部世界（Python）
┌─────────────┐          ┌─────────────┐
│ HTTP 请求    │   翻译   │ Python 对象  │
│             │  ────→   │             │
│ • URL       │          │ • 函数参数   │
│ • Header    │          │ • Pydantic  │
│ • Body      │          │ • 字典      │
└─────────────┘          └─────────────┘

内部世界（Python）          外部世界（HTTP）
┌─────────────┐          ┌─────────────┐
│ Python 对象  │   翻译   │ HTTP 响应    │
│             │  ────→   │             │
│ • 数据模型   │          │ • JSON      │
│ • 字典      │          │ • 状态码    │
│ • 异常      │          │ • Header    │
└─────────────┘          └─────────────┘
```

**类比**：就像翻译官
- 客户说英语（HTTP）
- 翻译官翻译成中文（Python）
- 业务部门处理（Service）
- 翻译官再把中文翻译回英语（HTTP）

---

### FastAPI 在技术栈中的位置

```
┌─────────────────────────────────────────────────────────────┐
│                       应用层                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Your Code (Service/Domain)               │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Web 框架层                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              FastAPI                                  │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐     │   │
│  │  │ Starlette  │  │  Pydantic  │  │ Routing    │     │   │
│  │  │ (ASGI)     │  │ (校验)     │  │ OpenAPI    │     │   │
│  │  └────────────┘  └────────────┘  └────────────┘     │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      服务器层                                │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │  Uvicorn   │  │  Gunicorn  │  │   Hypercorn│           │
│  │ (ASGI)     │  │  (Worker)  │  │   (ASGI)   │           │
│  └────────────┘  └────────────┘  └────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

**FastAPI 依赖的核心库**：

1. **Starlette** - Web 框架基础
   - 路由系统
   - 请求/响应处理
   - ASGI 支持
   - WebSocket 支持

2. **Pydantic** - 数据校验
   - 类型注解
   - 数据验证
   - 序列化/反序列化
   - JSON Schema 生成

**FastAPI 的价值**：
- 整合 Starlette + Pydantic
- 自动生成 OpenAPI 文档
- 依赖注入系统
- 类型提示友好

---

### 传输层的设计原则

#### 原则 1：薄协议层 (Thin Protocol Layer)

**目标**：传输层应该尽可能"薄"，只做协议转换，不做业务逻辑。

```python
# ❌ 错误：厚的传输层（包含业务逻辑）
@app.post("/users")
async def create_user(user: UserCreate):
    # 业务逻辑混在传输层
    if await db.query("SELECT * FROM users WHERE email = ?", user.email):
        raise HTTPException(409, "Email exists")

    hashed = bcrypt.hash(user.password)
    user_id = await db.insert("INSERT INTO users ...")
    send_welcome_email(user.email)

    return {"id": user_id, **user.dict()}

# ✅ 正确：薄的传输层（只做协议适配）
@app.post("/users")
async def create_user(
    user: UserCreate,                # 1. 接收参数（Pydantic 自动校验）
    service: UserService = Depends() # 2. 注入依赖
):
    user = await service.create_user(user)  # 3. 调用服务
    return success_response(data=user)      # 4. 返回响应
```

**为什么薄的传输层更好？**
- ✅ 业务逻辑可以复用（CLI、gRPC 等）
- ✅ 易于测试（Service 可以单独测试）
- ✅ 职责清晰（协议适配 vs 业务逻辑）

---

#### 原则 2：无业务逻辑 (No Business Logic)

**传输层不应该包含的业务逻辑**：
- ❌ 数据验证的业务规则（如：邮箱是否唯一）
- ❌ 数据转换（如：密码哈希）
- ❌ 业务流程编排（如：创建用户 → 发送邮件）
- ❌ 事务管理（如：数据库事务）

**传输层应该做的事**：
- ✅ HTTP 参数校验（格式、类型）
- ✅ 调用服务层
- ✅ 格式化响应
- ✅ HTTP 异常处理

```python
# ❌ 错误：在传输层实现业务规则
@app.post("/users")
async def create_user(user: UserCreate):
    # 业务规则：密码强度检查
    if len(user.password) < 8:
        raise HTTPException(400, "Password too weak")

    # 业务规则：年龄限制
    if user.age < 18:
        raise HTTPException(400, "Must be 18+")

    # ... 更多业务规则

# ✅ 正确：业务规则在 Domain 层
class User:
    def validate_password(self, password: str):
        if len(password) < 8:
            raise ValueError("Password too weak")

    def validate_age(self, age: int):
        if age < 18:
            raise ValueError("Must be 18+")

@app.post("/users")
async def create_user(user: UserCreate, service: UserService = Depends()):
    return await service.create_user(user)
```

---

#### 原则 3：边界清晰 (Clear Boundaries)

**传输层的边界在哪里？**

```
┌─────────────────────────────────────────────────────────────┐
│                        边界                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              传输层边界                               │   │
│  │                                                        │   │
│  │  输入边界：                                            │   │
│  │  • HTTP 请求                                           │   │
│  │  • Query 参数                                          │   │
│  │  • Path 参数                                           │   │
│  │  • Body (JSON)                                         │   │
│  │  • Header                                              │   │
│  │  • Cookie                                              │   │
│  │                                                        │   │
│  │  输出边界：                                            │   │
│  │  • HTTP 响应                                           │   │
│  │  • JSON 数据                                           │   │
│  │  • 状态码                                              │   │
│  │  • Response Header                                     │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**跨边界的数据格式**：

```python
# 输入：HTTP → Python
{
    "name": "张三",           # JSON 字符串
    "email": "test@test.com", # JSON 字符串
    "age": 25                 # JSON 数字
}
    ↓ Pydantic 反序列化
UserCreate(
    name: str,   # Python str
    email: str,  # Python str
    age: int     # Python int
)

# 输出：Python → HTTP
User(
    id=1,
    name="张三",
    email="test@test.com"
)
    ↓ Pydantic 序列化
{
    "id": 1,
    "name": "张三",
    "email": "test@test.com"
}  # JSON 对象
```

---

### 与其他层次的交互

#### 传输层 ↔ 服务层

```python
# 传输层调用服务层
@app.get("/users/{user_id}")
async def get_user(user_id: int, service: UserService = Depends()):
    # 1. 传输层提供简单的数据类型
    user = await service.get_user(user_id)

    # 2. 服务层返回领域对象
    # 3. 传输层将其序列化为 JSON
    return success_response(data=user)
```

**关键点**：
- 传输层不知道 Service 如何工作
- Service 不知道 HTTP 的存在
- 通过"接口"解耦

---

#### 传输层 ↔ 异常处理

```python
# 领域异常 → HTTP 状态码
@app.exception_handler(DomainException)
async def domain_exception_handler(request, exc: DomainException):
    # 传输层的职责：将领域异常映射为 HTTP 响应
    return JSONResponse(
        status_code=exc.http_status,
        content={
            "code": exc.http_status,
            "message": exc.message,
            "error_code": exc.code
        }
    )
```

**异常映射表**：
```
Domain Exception        → HTTP Status
UserNotFoundException    → 404 Not Found
EmailExistsException    → 409 Conflict
BusinessException       → 400 Bad Request
```

---

### 传输层的边界测试

**如何判断代码是否违反了传输层原则？**

#### 测试 1：能否在 CLI 中复用？

```python
# 如果业务逻辑在传输层，CLI 无法复用
@app.post("/users")
async def create_user(user: UserCreate):
    hashed = hash_password(user.password)  # ❌ 业务逻辑
    db.save(user)

# CLI 无法调用 HTTP endpoint！

# 正确：业务逻辑在 Service
class UserService:
    async def create_user(self, user_data: UserCreate):
        user = User.create(user_data)
        user.hash_password()  # ✅ 业务逻辑
        self.repo.save(user)

# HTTP API
@app.post("/users")
async def create_user(user: UserCreate, service: UserService = Depends()):
    return await service.create_user(user)

# CLI 工具
async def cli_create_user(name: str, email: str, password: str):
    service = UserService(repo)
    user = await service.create_user(UserCreate(name, email, password))
    print(f"User created: {user.id}")
```

#### 测试 2：能否独立测试 Service？

```python
# 如果传输层包含业务逻辑，Service 测试需要 HTTP 环境

# ❌ 错误：Service 依赖 HTTP
class UserService:
    def __init__(self):
        self.http_client = HTTPClient()  # 依赖 HTTP

    async def get_user(self, user_id: int):
        response = await self.http_client.get(f"/users/{user_id}")
        return response.json()

# 测试需要启动 HTTP 服务器！

# ✅ 正确：Service 不依赖 HTTP
class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo  # 依赖抽象

    async def get_user(self, user_id: int):
        return await self.repo.find_by_id(user_id)

# 测试可以注入 Mock Repository
async def test_get_user():
    mock_repo = Mock(spec=UserRepository)
    mock_repo.find_by_id.return_value = User(id=1, name="Test")
    service = UserService(mock_repo)
    user = await service.get_user(1)
    assert user.id == 1
```

#### 测试 3：切换协议是否困难？

```python
# 如果业务逻辑在传输层，添加 gRPC 接口需要重写

# ❌ 错误：HTTP 和业务逻辑混在一起
@app.post("/users")
async def create_user(user: UserCreate):
    # 业务逻辑
    hashed = hash_password(user.password)
    db.save(user)
    return {"id": user.id}

# 添加 gRPC 需要重写所有逻辑！

# ✅ 正确：Service 可以被多种协议复用
class UserService:
    async def create_user(self, user_data: UserCreate):
        # 业务逻辑（与协议无关）
        user = User.create(user_data)
        user.hash_password()
        self.repo.save(user)
        return user

# HTTP API
@app.post("/users")
async def create_user_http(user: UserCreate, service: UserService = Depends()):
    return await service.create_user(user)

# gRPC API
class UserServiceGRPC(user_service_pb2_grpc.UserServiceServicer):
    async def CreateUser(self, request, context):
        service = UserService(repo)
        user = await service.create_user(UserCreate.from_proto(request))
        return user.to_proto()
```

---

## 🔄 与 MVC 架构的对比

### 传统 MVC 架构

```
┌─────┐   请求   ┌──────────┐
│ View │ ──────→ │  Controller │
└─────┘           └──────────┘
                       │
                       ▼
                  ┌─────────┐
                  │  Model  │
                  └─────────┘
```

**MVC 的问题**：
1. **Controller 和 Model 职责模糊** - 业务逻辑该放哪？
2. **Model 变成贫血模型** - 只有 getter/setter，没有行为
3. **难以应对复杂业务** - 跨多个实体的操作放哪？

### FastAPI 推荐的分层架构

```
┌──────────────┐
│   FastAPI    │  ← 协议适配层（轻量级）
└──────────────┘
       │
       ▼
┌──────────────┐
│   Service    │  ← 用例编排层（可测试）
└──────────────┘
       │
       ▼
┌──────────────┐
│   Domain     │  ← 业务逻辑层（核心价值）
└──────────────┘
       │
       ▼
┌──────────────┐
│Infrastructure│  ← 技术实现层（可替换）
└──────────────┘
```

**分层架构的优势**：
1. **职责清晰** - 每层知道自己该做什么
2. **易于测试** - 每层可独立测试
3. **灵活替换** - 换数据库只改基础设施层
4. **符合 DDD** - 领域驱动设计的思想

---

## 🔗 依赖关系与依赖注入

### 依赖方向原则

```
     ┌──────────────┐
     │  FastAPI     │  ← 依赖 Service 接口
     └──────────────┘
            │
            ▼
     ┌──────────────┐
     │   Service    │  ← 依赖 Domain（实体 + 仓储接口）
     └──────────────┘
            │
            ▼
     ┌──────────────┐
     │   Domain     │  ← 不依赖任何层（核心）
     └──────────────┘
            ▲
            │
     ┌──────────────┐
     │Infrastructure│  ← 实现 Domain 定义的接口
     └──────────────┘
```

**核心原则**：
- **依赖倒置** - 高层不依赖低层，都依赖抽象
- **领域独立** - Domain 层不依赖任何框架
- **接口隔离** - Service 定义接口，Infrastructure 实现接口

### FastAPI 的依赖注入

```python
# FastAPI 自动管理依赖关系

# 1. 定义依赖（可以嵌套）
def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session

def get_user_repo(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return SQLUserRepository(db)

def get_user_service(
    repo: UserRepository = Depends(get_user_repo)
) -> UserService:
    return UserService(repo)

# 2. 使用依赖（FastAPI 自动解析）
@app.post("/users")
async def create_user(
    user: UserCreate,
    service: UserService = Depends(get_user_service)  # 自动注入
):
    return await service.create_user(user)
```

**依赖注入的好处**：
1. **解耦** - Endpoint 不需要知道如何创建 Service
2. **可测试** - 测试时可以注入 Mock 对象
3. **可复用** - 依赖可以在多个 endpoint 间共享
4. **生命周期管理** - FastAPI 自动管理资源的创建和销毁

---

## 📊 Level 1-5 的演进路径

### 演进全景图

```
Level 0: 异步基础
├─ 事件循环
├─ async/await
└─ 并发执行
         │
         ▼
Level 1: 传输层协议 ← 当前阶段
├─ 请求校验 (Path/Query/Body)
├─ 响应处理 (JSON/File/Streaming)
├─ 错误处理 (HTTPException)
└─ RESTful 设计
         │
         ▼
Level 2: 依赖注入系统
├─ Depends 高级用法
├─ 类依赖 vs 函数依赖
├─ request-scoped/app-scoped
└─ 应用生命周期 (lifespan)
         │
         ▼
Level 3: 外部系统集成
├─ 数据库 (SQLAlchemy + Alembic)
├─ 缓存 (Redis)
├─ 消息队列 (Kafka/RabbitMQ)
└─ 连接池/超时/重试
         │
         ▼
Level 4: 生产就绪
├─ 结构化日志 (JSON)
├─ Prometheus 指标
├─ 分布式追踪 (OpenTelemetry)
└─ 限流/熔断/降级
         │
         ▼
Level 5: 部署与运维
├─ Docker 多阶段构建
├─ 多环境配置
├─ CI/CD 流程
└─ 蓝绿部署/金丝雀发布
```

### 为什么要按这个顺序学习？

```
理解顺序 (自下而上):
Level 0 → 异步基础 ─┐
                   ├─→ Level 1 → 能处理 HTTP 请求了
Level 1 → HTTP 协议 ─┘
                   │
                   ├─→ Level 2 → 能组织代码了
Level 2 → 依赖注入 ─┘
                   │
                   ├─→ Level 3 → 能连接外部系统了
Level 3 → 外部集成 ─┘
                   │
                   ├─→ Level 4 → 能监控了
Level 4 → 可观测性 ─┘
                   │
                   ├─→ Level 5 → 能部署了
Level 5 → 运维部署 ─┘
```

**设计哲学**：
- **渐进式复杂度** - 每个 Level 建立在前一个基础上
- **实用主义** - 先学用的最多的，后学优化项
- **架构驱动** - 每个阶段都在完善架构能力

---

## 🎯 Level 1 的具体目标

### 你将学会什么

```
完成 Level 1 后，你能够：

✅ 正确处理各种类型的请求参数
   - /users/123        (Path)
   - /users?page=1     (Query)
   - POST /users       (Body)
   - Header 中的 Token
   - Cookie 中的 Session

✅ 返回各种类型的响应
   - JSON 数据
   - 文件下载
   - 流式数据（大文件）
   - WebSocket 实时通信

✅ 设计统一的 API 格式
   {
     "code": 200,
     "message": "success",
     "data": {...},
     "timestamp": 1234567890
   }

✅ 正确处理错误
   - 400: 参数错误
   - 401: 未认证
   - 403: 无权限
   - 404: 资源不存在
   - 500: 服务器错误

✅ 设计 RESTful API
   GET    /users          # 列表
   GET    /users/123      # 详情
   POST   /users          # 创建
   PUT    /users/123      # 更新
   DELETE /users/123      # 删除
```

### 架构约束（Level 1 必须遵守）

```python
# ❌ Level 1 禁止这样写
@app.post("/users")
async def create_user(user: UserCreate):
    # 禁止：在 endpoint 中写业务逻辑
    hashed = hash_password(user.password)
    result = db.execute("INSERT INTO users...")
    send_email(user.email)
    return result

# ✅ Level 1 应该这样写
@app.post("/users")
async def create_user(
    user: UserCreate,
    service: UserService = Depends()
):
    # Endpoint 只负责：参数校验 → 调用服务 → 返回响应
    return await service.create_user(user)
```

**为什么这样约束？**
1. **保持专注** - Level 1 只学协议层，不引入业务逻辑复杂性
2. **建立习惯** - 从一开始就养成正确的分层习惯
3. **便于演进** - 到 Level 2 再学如何实现 Service 层

---

## 💡 架构设计的"为什么"

### Q1: 为什么 FastAPI 叫"协议适配层"？

**类比**：想象你是公司的前台

```
客户（HTTP 请求）
    │
    ▼
前台（FastAPI）
    │  "您好，请问有什么可以帮您？"  (路由)
    │  "请出示您的证件"              (校验)
    │  "好的，请稍等"                (转发)
    ▼
业务部门（Service）
    │  处理具体业务
    ▼
前台（FastAPI）
    │  "您的业务已办理完成"          (响应)
    ▼
客户（HTTP 响应）
```

前台不办理业务，只负责：
- 接待客户（接收请求）
- 核对证件（参数校验）
- 转达信息（调用服务）
- 反馈结果（返回响应）

这就是 FastAPI 的角色 —— **协议适配**。

---

### Q2: 为什么不能在 endpoint 中写业务逻辑？

**现实案例**：用户注册

```python
# ❌ 在 endpoint 中写业务逻辑的问题
@app.post("/register")
async def register(user: UserCreate):
    # 问题1: 业务逻辑被绑在 HTTP 层
    hashed = bcrypt.hash(user.password)

    # 问题2: 无法单元测试（必须启动 HTTP 服务器）
    result = db.query("INSERT INTO users...")

    # 问题3: 难以复用（如 CLI 工具也需要注册功能）
    send_email(user.email)

    # 问题4: 事务边界不清晰
    return result
```

**如果能拆分**：

```python
# ✅ 拆分后的好处
@app.post("/register")                          # HTTP 层
async def register(user: UserCreate, service: UserService = Depends()):
    return await service.register(user)         # 只做协议适配

# Service 层
class UserService:
    async def register(self, user_data: UserCreate):
        user = User.create(user_data)           # 业务逻辑
        await self.repo.save(user)              # 持久化
        user.publish_event(UserRegistered())    # 副作用

# 好处:
# 1. Service 可以独立测试（不需要 HTTP）
# 2. Service 可以在 CLI、gRPC 等多处复用
# 3. 事务边界清晰（在 Service 层）
# 4. 业务逻辑与框架解耦
```

---

### Q3: 为什么要分层？不麻烦吗？

**短期看**：分层确实增加了代码量和复杂度

**长期看**：分层带来的收益远大于成本

```
场景对比：

简单场景（个人博客）
├─ 不分层: 1个文件搞定 ✅
└─ 分层:    5个文件，过度设计 ❌

复杂场景（电商系统）
├─ 不分层: 100个 endpoint，逻辑混乱 ❌
│         - 修改价格逻辑要改 10 处
│         - 测试要启动整个 HTTP 服务器
│         - 无法添加 gRPC 接口
│
└─ 分层:    职责清晰，易于扩展 ✅
           - 业务逻辑集中在 Service
           - Service 可单独测试
           - 可以添加多种接口（HTTP/gRPC/CLI）
```

**结论**：
- 小项目（PoC）→ 可以不分层，快速验证
- 中项目（生产）→ 简单分层（FastAPI + Service）
- 大项目（企业）→ 完整分层（DDD 架构）

**Level 1-5 的目标**：让你掌握完整分层的知识，根据项目规模灵活选择。

---

### Q4: 依赖注入是什么？为什么要用它？

**生活类比**：组装电脑

```python
# ❌ 硬编码依赖（自己买零件）
class Computer:
    def __init__(self):
        self.cpu = IntelCPU()          # 硬编码
        self.gpu = NvidiaGPU()          # 硬编码
        self.ram = SamsungRAM()        # 硬编码

# 问题：想换 AMD GPU？必须改代码

# ✅ 依赖注入（别人提供零件）
class Computer:
    def __init__(self, cpu: CPU, gpu: GPU, ram: RAM):  # 依赖抽象
        self.cpu = cpu
        self.gpu = gpu
        self.ram = ram

# 好处：可以灵活组装
computer1 = Computer(IntelCPU(), NvidiaGPU(), SamsungRAM())
computer2 = Computer(AMDCPU(), AMDGPU(), KingstonRAM())
```

**FastAPI 中的依赖注入**：

```python
# FastAPI 自动为你"组装"依赖
def get_user_service(
    db: AsyncSession = Depends(get_db),          # 自动提供数据库
    cache: Redis = Depends(get_redis)            # 自动提供缓存
) -> UserService:
    return UserService(db, cache)                # 组装服务

@app.get("/users/{id}")
async def get_user(
    id: int,
    service: UserService = Depends(get_user_service)  # 自动注入
):
    return await service.get_user(id)
```

**核心价值**：
1. **解耦** - Endpoint 不需要知道如何创建 Service
2. **可测试** - 测试时注入 Mock 对象
3. **灵活** - 不同环境可以注入不同实现

---

## 🧐 理解验证

### 自我检查问题

1. **传输层的核心职责是什么？**
   - A. 编写业务逻辑
   - B. 协议适配（HTTP ↔ Python 对象）
   - C. 数据库操作
   - D. 发送邮件

2. **为什么不能在 endpoint 中直接操作数据库？**
   - A. 因为 FastAPI 不支持
   - B. 因为会导致代码难以测试和复用
   - C. 因为会降低性能
   - D. 没有原因，可以这样做

3. **依赖注入的主要好处是？**
   - A. 让代码更复杂
   - B. 让代码运行更快
   - C. 让代码更解耦、可测试
   - D. 减少代码量

4. **以下哪个是正确的分层顺序？**
   - A. Domain → Service → FastAPI → Infrastructure
   - B. FastAPI → Service → Domain → Infrastructure
   - C. Infrastructure → Domain → Service → FastAPI
   - D. Service → FastAPI → Domain → Infrastructure

5. **RESTful API 的设计原则是什么？**
   - A. URL 中包含动词
   - B. 使用 HTTP 方法的语义（GET/POST/PUT/DELETE）
   - C. 所有请求都用 POST
   - D. 不关心 HTTP 状态码

<details>
<summary>点击查看答案</summary>

1. ✅ B. 协议适配
2. ✅ B. 代码难以测试和复用
3. ✅ C. 更解耦、可测试
4. ✅ B. FastAPI → Service → Domain → Infrastructure
5. ✅ B. HTTP 方法的语义

</details>

---

## 📝 记忆口诀

### 分层口诀

```
FastAPI 做前台，迎来送往
Service 做管家，统筹安排
Domain 做专家，专注业务
Infrastructure 做工人，干脏活累活
```

### 依赖注入口诀

```
不要自己找依赖，
让别人提供给你。
测试时换假的，
生产时换真的。
```

### 架构演进口诀

```
Level 0 先打基础（异步）
Level 1 学会对话（HTTP）
Level 2 学会组织（依赖）
Level 3 学会交友（外部）
Level 4 学会体检（监控）
Level 5 学会上线（部署）
```

---

## 🚀 下一步

现在你已经理解了 FastAPI 的整体架构，可以开始学习 Level 1 的具体内容：

1. **请求参数校验** → `notes/01_request_validation.md`
2. **响应处理** → `notes/02_response_handling.md`
3. **统一响应格式** → `notes/03_unified_response.md`
4. **错误处理** → `notes/04_error_handling.md`
5. **HTTP 语义** → `notes/05_http_semantics.md`

记住：**架构是骨架，细节是血肉**。先理解骨架，再填充血肉！

---

## 📚 延伸阅读

- [Clean Architecture by Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Domain-Driven Design by Eric Evans](https://www.domainlanguage.com/ddd/)
- [FastAPI 官方文档 - Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [RESTful API 设计指南](https://restfulapi.net/)

---

**保持好奇心，理解"为什么"比记住"怎么做"更重要！** 🎓
