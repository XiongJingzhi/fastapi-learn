# 04. 实现服务层 - Implementing the Service Layer

## 📍 在架构中的位置

**从 Level 1 到 Level 2：完整的三层架构**

```
┌─────────────────────────────────────────────────────────────┐
│          Level 1: 只有传输层（演示代码）                     │
└─────────────────────────────────────────────────────────────┘

@app.post("/users")
async def create_user(user: UserCreate):
    # ❌ 所有逻辑都在 endpoint
    hashed = hash_password(user.password)
    if db.exists(user.email):
        raise HTTPException(409, "Email exists")
    result = db.insert("...")
    return result

问题：
- 无法复用
- 难以测试
- 职责混乱

═══════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────┐
│          Level 2: 完整三层架构（生产代码）                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  传输层 (Transport Layer) - FastAPI Endpoints          │
│  @app.post("/users")                                   │
│  async def create_user(                                │
│      user: UserCreate,                                 │
│      service: UserService = Depends() ← 依赖注入       │
│  ):                                                    │
│      return await service.create_user(user)            │
│                                                         │
│  职责：协议适配                                          │
└─────────────────────────────────────────────────────────┘
                      │
                      │ 依赖注入
                      ▼
┌─────────────────────────────────────────────────────────┐
│  服务层 (Service Layer) - Business Logic                │
│  class UserService:                                     │
│      def __init__(self, repo: UserRepository):          │
│          self.repo = repo                               │
│                                                         │
│      async def create_user(self, user_data):           │
│          # ✅ 业务逻辑在这里                              │
│          if await self.repo.email_exists(...):          │
│              raise UserEmailExistsException()            │
│          user = User.create(user_data)                  │
│          return await self.repo.save(user)              │
│                                                         │
│  职责：用例编排、业务规则                                 │
└─────────────────────────────────────────────────────────┘
                      │
                      │ 依赖注入
                      ▼
┌─────────────────────────────────────────────────────────┐
│  基础设施层 (Infrastructure Layer) - Data Access        │
│  class SQLUserRepository(UserRepository):               │
│      def __init__(self, db: AsyncSession):             │
│          self.session = db                              │
│                                                         │
│      async def save(self, user: User):                 │
│          self.session.add(user)                         │
│          await self.session.commit()                    │
│          return user                                    │
│                                                         │
│  职责：数据持久化、外部集成                               │
└─────────────────────────────────────────────────────────┘
```

**🎯 你的学习目标**：实现完整的三层架构，真正理解职责分离。

---

## 🎯 什么是服务层？

### 服务层的定位

**类比：公司的管家**

```
┌─────────────────────────────────────────┐
│  前台（FastAPI Endpoint）               │
│  - 接待客人（接收 HTTP 请求）             │
│  - 不做决策（不处理业务逻辑）              │
│  - 转达给管家（调用 Service）            │
└─────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│  管家（Service Layer）                  │
│  - 协调各项工作（编排业务逻辑）           │
│  - 请专家（领域模型）                    │
│  - 请工人（基础设施）                    │
│  - 对前台负责（返回结果）                │
└─────────────────────────────────────────┘
              │
              ├─→ 专家（Domain Model）
              └─→ 工人（Infrastructure）
```

**服务层的核心职责**：

1. **用例编排** - 协调多个步骤完成一个用例
2. **业务规则** - 实现业务约束和验证
3. **事务边界** - 控制数据库事务的开始和结束
4. **领域事件** - 发布业务领域事件

---

## 🏗️ Repository 模式：数据访问抽象

### 什么是 Repository？

**类比：仓库管理员**

```python
# 你需要的："给我 id=123 的用户"
user = repository.find_by_id(123)

# 你不需要关心：
# - 数据是从哪来的？（PostgreSQL? MySQL? MongoDB?）
# - SQL 怎么写？
# - 连接怎么管理？
# - 缓存怎么处理？

# Repository 隐藏了所有数据访问细节
```

**Repository 接口定义**：

```python
from abc import ABC, abstractmethod
from typing import Optional

class UserRepository(ABC):
    """用户仓储接口（抽象）"""

    @abstractmethod
    async def save(self, user: User) -> User:
        """保存用户"""
        pass

    @abstractmethod
    async def find_by_id(self, user_id: int) -> Optional[User]:
        """根据 ID 查找用户"""
        pass

    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[User]:
        """根据邮箱查找用户"""
        pass

    @abstractmethod
    async def email_exists(self, email: str) -> bool:
        """检查邮箱是否已存在"""
        pass

    @abstractmethod
    async def delete(self, user_id: int) -> None:
        """删除用户"""
        pass
```

**SQL 实现**：

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

class SQLUserRepository(UserRepository):
    """SQL 实现（PostgreSQL/MySQL）"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, user: User) -> User:
        """保存用户到数据库"""
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def find_by_id(self, user_id: int) -> Optional[User]:
        """根据 ID 查找"""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def find_by_email(self, email: str) -> Optional[User]:
        """根据邮箱查找"""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def email_exists(self, email: str) -> bool:
        """检查邮箱是否存在"""
        result = await self.session.execute(
            select(func.count(User.id)).where(User.email == email)
        )
        count = result.scalar()
        return count > 0

    async def delete(self, user_id: int) -> None:
        """删除用户"""
        user = await self.find_by_id(user_id)
        if user:
            await self.session.delete(user)
            await self.session.commit()
```

**内存实现（用于测试）**：

```python
class InMemoryUserRepository(UserRepository):
    """内存实现（测试用）"""

    def __init__(self):
        self._users: dict[int, User] = {}
        self._next_id = 1

    async def save(self, user: User) -> User:
        if user.id is None:
            user.id = self._next_id
            self._next_id += 1
        self._users[user.id] = user
        return user

    async def find_by_id(self, user_id: int) -> Optional[User]:
        return self._users.get(user_id)

    async def find_by_email(self, email: str) -> Optional[User]:
        for user in self._users.values():
            if user.email == email:
                return user
        return None

    async def email_exists(self, email: str) -> bool:
        return await self.find_by_email(email) is not None

    async def delete(self, user_id: int) -> None:
        if user_id in self._users:
            del self._users[user_id]
```

---

## 💼 实现服务层

### UserService 设计

```python
from pydantic import BaseModel as PydanticModel

class UserCreate(PydanticModel):
    """创建用户的数据模型"""
    username: str
    email: str
    password: str

class UserUpdate(PydanticModel):
    """更新用户的数据模型"""
    username: str | None = None
    email: str | None = None

class UserService:
    """用户服务：编排用户相关的业务逻辑"""

    def __init__(self, repo: UserRepository):
        # 依赖仓储接口（不依赖具体实现）
        self.repo = repo

    async def create_user(self, user_data: UserCreate) -> User:
        """
        创建用户用例

        业务流程：
        1. 检查邮箱是否已存在
        2. 创建用户实体
        3. 哈希密码
        4. 保存到数据库
        5. 返回用户信息
        """
        # 1. 业务规则：邮箱必须唯一
        if await self.repo.email_exists(user_data.email):
            raise UserEmailExistsException(
                f"Email {user_data.email} already registered"
            )

        # 2. 创建用户实体
        user = User(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password  # 明文密码
        )

        # 3. 业务逻辑：哈希密码
        user.hash_password()

        # 4. 持久化
        saved_user = await self.repo.save(user)

        # 5. 返回（不包含密码）
        saved_user.password = None  # 清除密码
        return saved_user

    async def get_user(self, user_id: int) -> User:
        """获取用户"""
        user = await self.repo.find_by_id(user_id)
        if not user:
            raise UserNotFoundException(f"User {user_id} not found")
        return user

    async def update_user(self, user_id: int, user_data: UserUpdate) -> User:
        """更新用户"""
        user = await self.get_user(user_id)

        # 业务规则：如果更新邮箱，检查是否重复
        if user_data.email and user_data.email != user.email:
            if await self.repo.email_exists(user_data.email):
                raise UserEmailExistsException("Email already exists")
            user.email = user_data.email

        if user_data.username:
            user.username = user_data.username

        # 保存更新
        return await self.repo.save(user)

    async def delete_user(self, user_id: int) -> None:
        """删除用户"""
        user = await self.get_user(user_id)

        # 业务规则：不能删除自己
        #（如果有当前用户上下文）
        # if current_user.id == user_id:
        #     raise CannotDeleteSelfException()

        await self.repo.delete(user_id)
```

---

## 🔗 使用依赖注入组装

### 完整的三层架构实现

```python
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

app = FastAPI()

# ═══════════════════════════════════════════════════════════
# 1. 基础设施层：数据库配置
# ═══════════════════════════════════════════════════════════

engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/db")
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

def get_db() -> AsyncSession:
    """数据库会话（Request-scoped）"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

# ═══════════════════════════════════════════════════════════
# 2. 基础设施层：Repository 实现
# ═══════════════════════════════════════════════════════════

def get_user_repo(db: AsyncSession = Depends(get_db)) -> UserRepository:
    """用户仓储（依赖数据库）"""
    return SQLUserRepository(db)

# ═══════════════════════════════════════════════════════════
# 3. 服务层：Service 实现
# ═══════════════════════════════════════════════════════════

def get_user_service(
    repo: UserRepository = Depends(get_user_repo)
) -> UserService:
    """用户服务（依赖仓储）"""
    return UserService(repo)

# ═══════════════════════════════════════════════════════════
# 4. 传输层：FastAPI Endpoints
# ═══════════════════════════════════════════════════════════

@app.post("/users", response_model=UserResponse, status_code=201)
async def create_user(
    user: UserCreate,
    service: UserService = Depends(get_user_service)  # ← 依赖注入
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
    except UserEmailExistsException as e:
        raise HTTPException(status_code=409, detail=str(e))

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service)
):
    try:
        return await service.get_user(user_id)
    except UserNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user: UserUpdate,
    service: UserService = Depends(get_user_service)
):
    try:
        return await service.update_user(user_id, user)
    except UserNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except UserEmailExistsException as e:
        raise HTTPException(status_code=409, detail=str(e))

@app.delete("/users/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    service: UserService = Depends(get_user_service)
):
    try:
        await service.delete_user(user_id)
    except UserNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
```

---

## 📊 从 Level 1 到 Level 2：完整演进

### Level 1：演示代码（所有逻辑在 Endpoint）

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

# ❌ 没有分层
@app.post("/users")
async def create_user(user: UserCreate):
    # 直接在这里写所有逻辑

    # 1. 检查邮箱
    existing = await db.query(
        "SELECT * FROM users WHERE email = ?",
        user.email
    )
    if existing:
        raise HTTPException(409, "Email exists")

    # 2. 哈希密码
    import bcrypt
    hashed = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt())

    # 3. 插入数据库
    user_id = await db.insert(
        "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
        user.username, user.email, hashed
    )

    # 4. 返回
    return {"id": user_id, "username": user.username, "email": user.email}

# 问题：
# - 业务逻辑无法复用
# - 难以测试（必须启动 HTTP 服务器）
# - 职责混乱（HTTP + 业务 + 数据）
```

---

### Level 2：生产架构（完整三层）

```python
# ═══════════════════════════════════════════════════════════
# 传输层：只做协议适配
# ═══════════════════════════════════════════════════════════

@app.post("/users")
async def create_user(
    user: UserCreate,
    service: UserService = Depends(get_user_service)
):
    # ✅ 只做协议适配
    return await service.create_user(user)

# ═══════════════════════════════════════════════════════════
# 服务层：业务逻辑编排
# ═══════════════════════════════════════════════════════════

class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def create_user(self, user_data: UserCreate) -> User:
        # ✅ 业务逻辑在这里
        if await self.repo.email_exists(user_data.email):
            raise UserEmailExistsException()

        user = User.create(user_data)
        user.hash_password()
        return await self.repo.save(user)

# ═══════════════════════════════════════════════════════════
# 基础设施层：数据访问
# ═══════════════════════════════════════════════════════════

class SQLUserRepository(UserRepository):
    async def email_exists(self, email: str) -> bool:
        result = await self.session.execute(
            select(func.count(User.id)).where(User.email == email)
        )
        return result.scalar() > 0

    async def save(self, user: User) -> User:
        self.session.add(user)
        await self.session.commit()
        return user

# 好处：
# - 业务逻辑可复用（可以在 CLI/gRPC 中使用）
# - 易于测试（注入 Mock）
# - 职责清晰（每层知道自己的工作）
```

---

## 🧪 测试三层架构

### 测试 Service 层

```python
import pytest

async def test_create_user_success():
    """测试：成功创建用户"""
    # 1. 准备 Mock Repository
    mock_repo = InMemoryUserRepository()

    # 2. 创建 Service（注入 Mock）
    service = UserService(mock_repo)

    # 3. 执行操作
    user_data = UserCreate(
        username="alice",
        email="alice@example.com",
        password="secret123"
    )
    user = await service.create_user(user_data)

    # 4. 验证结果
    assert user.id is not None
    assert user.username == "alice"
    assert user.email == "alice@example.com"
    assert user.password is None  # 密码被清除
    assert user.password_hash is not None  # 密码被哈希

async def test_create_user_email_exists():
    """测试：邮箱已存在"""
    # 1. 准备 Mock Repository
    mock_repo = InMemoryUserRepository()
    await mock_repo.save(User(
        username="bob",
        email="alice@example.com",
        password="hash"
    ))

    # 2. 创建 Service
    service = UserService(mock_repo)

    # 3. 执行操作（预期失败）
    user_data = UserCreate(
        username="alice",
        email="alice@example.com",  # 重复邮箱
        password="secret123"
    )

    # 4. 验证抛出异常
    with pytest.raises(UserEmailExistsException):
        await service.create_user(user_data)
```

**关键点**：
- ✅ 不需要启动 HTTP 服务器
- ✅ 不需要连接真实数据库
- ✅ 测试速度快
- ✅ 可以测试边界情况

---

## 🎯 小实验：实现完整的 CRUD

### 目标：实现 TODO 应用的三层架构

```python
# ═══════════════════════════════════════════════════════════
# 1. 数据模型
# ═══════════════════════════════════════════════════════════

class TodoCreate(BaseModel):
    title: str
    description: str | None = None

class TodoUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    completed: bool | None = None

# ═══════════════════════════════════════════════════════════
# 2. Repository 接口
# ═══════════════════════════════════════════════════════════

class TodoRepository(ABC):
    @abstractmethod
    async def save(self, todo: Todo) -> Todo:
        pass

    @abstractmethod
    async def find_by_id(self, todo_id: int) -> Optional[Todo]:
        pass

    @abstractmethod
    async def list_all(self) -> list[Todo]:
        pass

    @abstractmethod
    async def delete(self, todo_id: int) -> None:
        pass

# ═══════════════════════════════════════════════════════════
# 3. Service 层
# ═══════════════════════════════════════════════════════════

class TodoService:
    def __init__(self, repo: TodoRepository):
        self.repo = repo

    async def create_todo(self, todo_data: TodoCreate) -> Todo:
        """创建 TODO"""
        # 业务规则：标题不能为空
        if not todo_data.title or todo_data.title.strip() == "":
            raise InvalidTodoException("Title cannot be empty")

        todo = Todo(
            title=todo_data.title,
            description=todo_data.description,
            completed=False
        )
        return await self.repo.save(todo)

    async def get_todo(self, todo_id: int) -> Todo:
        """获取 TODO"""
        todo = await self.repo.find_by_id(todo_id)
        if not todo:
            raise TodoNotFoundException(f"Todo {todo_id} not found")
        return todo

    async def list_todos(self) -> list[Todo]:
        """列出所有 TODO"""
        return await self.repo.list_all()

    async def update_todo(self, todo_id: int, todo_data: TodoUpdate) -> Todo:
        """更新 TODO"""
        todo = await self.get_todo(todo_id)

        if todo_data.title is not None:
            todo.title = todo_data.title
        if todo_data.description is not None:
            todo.description = todo_data.description
        if todo_data.completed is not None:
            todo.completed = todo_data.completed

        return await self.repo.save(todo)

    async def delete_todo(self, todo_id: int) -> None:
        """删除 TODO"""
        await self.get_todo(todo_id)  # 检查是否存在
        await self.repo.delete(todo_id)

# ═══════════════════════════════════════════════════════════
# 4. 依赖注入
# ═══════════════════════════════════════════════════════════

def get_todo_repo(db: AsyncSession = Depends(get_db)) -> TodoRepository:
    return SQLTodoRepository(db)

def get_todo_service(
    repo: TodoRepository = Depends(get_todo_repo)
) -> TodoService:
    return TodoService(repo)

# ═══════════════════════════════════════════════════════════
# 5. Endpoints
# ═══════════════════════════════════════════════════════════

@app.post("/todos", response_model=TodoResponse, status_code=201)
async def create_todo(
    todo: TodoCreate,
    service: TodoService = Depends(get_todo_service)
):
    return await service.create_todo(todo)

@app.get("/todos", response_model=list[TodoResponse])
async def list_todos(
    service: TodoService = Depends(get_todo_service)
):
    return await service.list_todos()

@app.get("/todos/{todo_id}", response_model=TodoResponse)
async def get_todo(
    todo_id: int,
    service: TodoService = Depends(get_todo_service)
):
    return await service.get_todo(todo_id)

@app.put("/todos/{todo_id}", response_model=TodoResponse)
async def update_todo(
    todo_id: int,
    todo: TodoUpdate,
    service: TodoService = Depends(get_todo_service)
):
    return await service.update_todo(todo_id, todo)

@app.delete("/todos/{todo_id}", status_code=204)
async def delete_todo(
    todo_id: int,
    service: TodoService = Depends(get_todo_service)
):
    await service.delete_todo(todo_id)
```

---

## 📚 检查理解

回答这些问题来测试你的理解：

1. **三层架构的职责划分？**
   - 提示：传输层（协议）、服务层（业务）、基础设施层（数据）

2. **为什么要用 Repository 模式？**
   - 提示：抽象数据访问、易于测试

3. **Service 层的职责是什么？**
   - 提示：用例编排、业务规则、事务边界

4. **如何测试 Service 层？**
   - 提示：注入 Mock Repository

5. **依赖注入如何让分层架构成为可能？**
   - 提示：Depends 自动解析依赖链

---

## 🚀 下一步

现在你已经实现了完整的三层架构，接下来：

1. **查看实际代码**：`examples/05_service_layer.py`
2. **学习下一课**：`notes/05_best_practices.md`（最佳实践）

**记住**：分层架构让代码清晰、可测试、可维护！

---

**费曼技巧总结**：
- ✅ 从 Level 1 到 Level 2 的完整演进
- ✅ Repository 模式的抽象
- ✅ Service 层的实现
- ✅ 依赖注入的组装
- ✅ 测试 Service 层
- ✅ 完整的 CRUD 示例
