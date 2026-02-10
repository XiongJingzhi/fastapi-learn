# 03. Repository 模式 - Repository Pattern

## 📍 在架构中的位置

**完成分层架构的最后一块拼图**

```
┌─────────────────────────────────────────────────────────────┐
│          Level 2: Service 使用 Mock Repository              │
└─────────────────────────────────────────────────────────────┘

class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

# 使用 Mock（内存）
mock_repo = InMemoryUserRepository()
service = UserService(mock_repo)

问题：
- 数据存在内存中（重启丢失）
- 无法支持并发
- 没有事务
- 无法支持复杂查询

═══════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────┐
│          Level 3: Service 使用 SQL Repository               │
└─────────────────────────────────────────────────────────────┘

class UserService:
    def __init__(self, repo: UserRepository):  # 不变！
        self.repo = repo

# 使用真实数据库
sql_repo = SQLUserRepository(session)
service = UserService(sql_repo)  # 代码不需要改！

好处：
- Service 层代码完全不变
- 只需更换 Repository 实现
- 数据持久化
- 支持事务和并发
```

**🎯 你的学习目标**：实现 Repository 模式，完成完整的三层架构。

---

## 🎯 什么是 Repository 模式？

### 生活类比：仓库管理员

**想象一个公司的仓库**：

```
┌─────────────────────────────────────────────────────────────┐
│                    仓库系统                                  │
└─────────────────────────────────────────────────────────────┘

部门经理（Service）
    │ 需要：5 个笔记本电脑
    ▼
仓库管理员（Repository）
    │ 职责：
    │ - 查找库存
    │ - 入库/出库
    │ - 管理货架
    │ - （部门经理不需要知道东西放在哪个货架）
    ▼
仓库货架（Database）
    │ 实际存储：
    │ - 货架 A1: 笔记本电脑
    │ - 货架 B2: 鼠标
    └─ ...
```

**关键点**：
- **部门经理**只关心"我要 5 个电脑"，不关心从哪个货架拿
- **仓库管理员**知道东西在哪，如何高效取货
- **仓库货架**是实际存储的地方

**对应到代码**：

```python
# Service = 部门经理
class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo  # 依赖仓库管理员

    async def create_user(self, user_data: UserCreate):
        # 业务逻辑
        user = User.create(user_data)
        # 让 Repository 负责存储
        return await self.repo.save(user)  # 不关心怎么存

# Repository = 仓库管理员
class SQLUserRepository(UserRepository):
    async def save(self, user: User) -> User:
        # 数据访问逻辑
        self.session.add(user)
        await self.session.commit()
        return user  # 实际存储细节
```

---

## 🏗️ Repository 模式的架构

### 架构层次

```
┌─────────────────────────────────────────────────────────────┐
│              Service Layer (服务层)                          │
│                                                              │
│  class UserService:                                         │
│      def __init__(self, repo: UserRepository):  ← 依赖接口     │
│          self.repo = repo                                   │
│                                                              │
│      async def create_user(self, user_data):               │
│          # 业务规则验证                                       │
│          if await self.repo.email_exists(...):              │
│              raise EmailExistsException()                   │
│                                                              │
│          # 创建用户实体                                       │
│          user = User.create(user_data)                       │
│                                                              │
│          # 调用 Repository 存储数据                           │
│          return await self.repo.save(user)                   │
│                                                              │
│  职责：业务逻辑、用例编排                                      │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ 依赖接口（抽象）
                          ▼
┌─────────────────────────────────────────────────────────────┐
│          Repository Interface (仓储接口)                     │
│                                                              │
│  class UserRepository(ABC):                                 │
│      @abstractmethod                                        │
│      async def save(self, user: User) -> User:             │
│          pass                                               │
│                                                              │
│      @abstractmethod                                        │
│      async def find_by_id(self, user_id: int) -> User:     │
│          pass                                               │
│                                                              │
│      @abstractmethod                                        │
│      async def email_exists(self, email: str) -> bool:     │
│          pass                                               │
│                                                              │
│  职责：定义数据访问契约（在 Domain 层定义）                      │
└─────────────────────────────────────────────────────────────┘
                          ▲
                          │ 实现接口
                          │
          ┌───────────────┴───────────────┐
          │                               │
┌──────────────────────┐     ┌──────────────────────┐
│ SQL Implementation    │     │  Mock Implementation │
│  (生产环境)            │     │  (测试环境)           │
├──────────────────────┤     ├──────────────────────┤
│ class SQLUserRepo     │     │ class MockUserRepo    │
│   (UserRepository):   │     │   (UserRepository):   │
│                       │     │                       │
│   async def save(...): │     │   async def save(...): │
│       session.add(u)   │     │       self.users[...] │
│       await commit()   │     │                       │
└──────────────────────┘     └──────────────────────┘

│ 职责：具体的数据访问逻辑（在 Infrastructure 层实现）            │
```

---

## 📦 定义 Repository 接口

### 接口定义

```python
from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import User

# ═══════════════════════════════════════════════════════════
# Repository 接口（在 Domain 层定义）
# ═══════════════════════════════════════════════════════════

class UserRepository(ABC):
    """用户仓储接口（抽象）"""

    @abstractmethod
    async def save(self, user: User) -> User:
        """
        保存用户

        如果是新用户：插入
        如果是已存在用户：更新
        """
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
    async def find_all(self) -> List[User]:
        """查找所有用户"""
        pass

    @abstractmethod
    async def email_exists(self, email: str) -> bool:
        """检查邮箱是否存在"""
        pass

    @abstractmethod
    async def delete(self, user_id: int) -> None:
        """删除用户"""
        pass

    @abstractmethod
    async def exists_by_id(self, user_id: int) -> bool:
        """检查用户是否存在"""
        pass

    @abstractmethod
    async def count(self) -> int:
        """统计用户数量"""
        pass
```

---

## 🔧 SQL 实现

### 完整的 SQL Repository

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional, List

# ═══════════════════════════════════════════════════════════
# SQL 实现（在 Infrastructure 层实现）
# ═══════════════════════════════════════════════════════════

class SQLUserRepository(UserRepository):
    """SQL 实现的 UserRepository（生产环境）"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, user: User) -> User:
        """保存用户（插入或更新）"""
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def find_by_id(self, user_id: int) -> Optional[User]:
        """根据 ID 查找"""
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_email(self, email: str) -> Optional[User]:
        """根据邮箱查找"""
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_all(self) -> List[User]:
        """查找所有用户"""
        stmt = select(User).order_by(User.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def email_exists(self, email: str) -> bool:
        """检查邮箱是否存在"""
        # 方法 1：使用 exists
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

        # 方法 2：使用 count（更高效）
        # stmt = select(func.count(User.id)).where(User.email == email)
        # result = await self.session.execute(stmt)
        # return result.scalar() > 0

    async def delete(self, user_id: int) -> None:
        """删除用户"""
        user = await self.find_by_id(user_id)
        if user:
            await self.session.delete(user)
            await self.session.commit()

    async def exists_by_id(self, user_id: int) -> bool:
        """检查用户是否存在"""
        stmt = select(func.count(User.id)).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar() > 0

    async def count(self) -> int:
        """统计用户数量"""
        stmt = select(func.count(User.id))
        result = await self.session.execute(stmt)
        return result.scalar()

    # ═══════════════════════════════════════════════════════════
    # 额外的复杂查询方法
    # ═══════════════════════════════════════════════════════════

    async def search(self, keyword: str) -> List[User]:
        """搜索用户（用户名或邮箱）"""
        stmt = select(User).where(
            or_(
                User.username.contains(keyword),
                User.email.contains(keyword)
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def find_active_users(self) -> List[User]:
        """查找活跃用户"""
        stmt = select(User).where(
            User.is_active == True
        ).order_by(User.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def find_by_ids(self, user_ids: List[int]) -> List[User]:
        """根据 ID 列表查找用户"""
        stmt = select(User).where(User.id.in_(user_ids))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def paginate(self, offset: int, limit: int) -> List[User]:
        """分页查询"""
        stmt = select(User).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
```

---

## 🧪 Mock 实现（用于测试）

### InMemory Repository

```python
# ═══════════════════════════════════════════════════════════
# Mock 实现（用于测试）
# ═══════════════════════════════════════════════════════════

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

    async def find_all(self) -> List[User]:
        return list(self._users.values())

    async def email_exists(self, email: str) -> bool:
        return await self.find_by_email(email) is not None

    async def delete(self, user_id: int) -> None:
        if user_id in self._users:
            del self._users[user_id]

    async def exists_by_id(self, user_id: int) -> bool:
        return user_id in self._users

    async def count(self) -> int:
        return len(self._users)

    # 额外方法
    async def clear(self):
        """清空所有数据（测试用）"""
        self._users.clear()
        self._next_id = 1
```

---

## 🔗 使用依赖注入集成

### 完整的依赖注入链

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# ═══════════════════════════════════════════════════════════
# 1. 数据库配置
# ═══════════════════════════════════════════════════════════

engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/db")
async_session = sessionmaker(engine, class_=AsyncSession)

def get_db() -> AsyncSession:
    """数据库会话依赖（Request-scoped）"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

# ═══════════════════════════════════════════════════════════
# 2. Repository 依赖
# ═══════════════════════════════════════════════════════════

def get_user_repo(
    db: AsyncSession = Depends(get_db)
) -> UserRepository:
    """用户仓储依赖"""
    return SQLUserRepository(db)

# ═══════════════════════════════════════════════════════════
# 3. Service 依赖
# ═══════════════════════════════════════════════════════════

def get_user_service(
    repo: UserRepository = Depends(get_user_repo)
) -> UserService:
    """用户服务依赖"""
    return UserService(repo)

# ═══════════════════════════════════════════════════════════
# 4. Endpoints
# ═══════════════════════════════════════════════════════════

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

@app.post("/users", status_code=201)
async def create_user(
    user: UserCreate,
    service: UserService = Depends(get_user_service)  # ← 注入
):
    """创建用户"""
    try:
        result = await service.create_user(user)
        return result
    except UserEmailExistsException as e:
        raise HTTPException(status_code=409, detail=str(e))

@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service)
):
    """获取用户"""
    user = await service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/users")
async def list_users(
    service: UserService = Depends(get_user_service)
):
    """列出所有用户"""
    return await service.list_users()
```

---

## 🎨 完整示例：TODO 应用的 Repository

### 定义 TODO Repository

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

# ═══════════════════════════════════════════════════════════
# 1. 模型
# ═══════════════════════════════════════════════════════════

class Todo(Base):
    """TODO 模型"""
    __tablename__ = "todos"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

# ═══════════════════════════════════════════════════════════
# 2. Repository 接口
# ═══════════════════════════════════════════════════════════

class TodoRepository(ABC):
    """TODO 仓储接口"""

    @abstractmethod
    async def save(self, todo: Todo) -> Todo:
        pass

    @abstractmethod
    async def find_by_id(self, todo_id: int) -> Optional[Todo]:
        pass

    @abstractmethod
    async def find_all(self) -> List[Todo]:
        pass

    @abstractmethod
    async def find_completed(self, completed: bool) -> List[Todo]:
        pass

    @abstractmethod
    async def delete(self, todo_id: int) -> None:
        pass

# ═══════════════════════════════════════════════════════════
# 3. SQL 实现
# ═══════════════════════════════════════════════════════════

class SQLTodoRepository(TodoRepository):
    """SQL 实现"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, todo: Todo) -> Todo:
        self.session.add(todo)
        await self.session.commit()
        await self.session.refresh(todo)
        return todo

    async def find_by_id(self, todo_id: int) -> Optional[Todo]:
        stmt = select(Todo).where(Todo.id == todo_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_all(self) -> List[Todo]:
        stmt = select(Todo).order_by(Todo.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def find_completed(self, completed: bool) -> List[Todo]:
        stmt = select(Todo).where(
            Todo.completed == completed
        ).order_by(Todo.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete(self, todo_id: int) -> None:
        todo = await self.find_by_id(todo_id)
        if todo:
            await self.session.delete(todo)
            await self.session.commit()

# ═══════════════════════════════════════════════════════════
# 4. Service 层
# ═══════════════════════════════════════════════════════════

class TodoService:
    """TODO 服务"""

    def __init__(self, repo: TodoRepository):
        self.repo = repo

    async def create_todo(self, title: str, description: str = None) -> Todo:
        """创建 TODO"""
        if not title or title.strip() == "":
            raise InvalidTodoException("Title cannot be empty")

        todo = Todo(title=title, description=description)
        return await self.repo.save(todo)

    async def complete_todo(self, todo_id: int) -> Todo:
        """完成 TODO"""
        todo = await self.repo.find_by_id(todo_id)
        if not todo:
            raise TodoNotFoundException(f"Todo {todo_id} not found")

        todo.completed = True
        return await self.repo.save(todo)

    async def list_todos(self, completed: bool | None = None) -> List[Todo]:
        """列出 TODO"""
        if completed is None:
            return await self.repo.find_all()
        return await self.repo.find_completed(completed)

# ═══════════════════════════════════════════════════════════
# 5. 依赖注入
# ═══════════════════════════════════════════════════════════

def get_todo_repo(db: AsyncSession = Depends(get_db)) -> TodoRepository:
    return SQLTodoRepository(db)

def get_todo_service(repo: TodoRepository = Depends(get_todo_repo)) -> TodoService:
    return TodoService(repo)

# ═══════════════════════════════════════════════════════════
# 6. Endpoints
# ═══════════════════════════════════════════════════════════

@app.post("/todos", status_code=201)
async def create_todo(
    title: str,
    description: str = None,
    service: TodoService = Depends(get_todo_service)
):
    return await service.create_todo(title, description)

@app.get("/todos")
async def list_todos(
    completed: bool | None = None,
    service: TodoService = Depends(get_todo_service)
):
    return await service.list_todos(completed)

@app.put("/todos/{todo_id}/complete")
async def complete_todo(
    todo_id: int,
    service: TodoService = Depends(get_todo_service)
):
    return await service.complete_todo(todo_id)
```

---

## 🎯 Repository 设计原则

### 原则 1：接口在 Domain 层定义

```python
# ✅ 正确：接口在 Domain 层定义
# domain/repositories.py

class UserRepository(ABC):
    """在 Domain 层定义（不依赖具体技术）"""
    @abstractmethod
    async def save(self, user: User) -> User:
        pass

# infrastructure/repositories.py

class SQLUserRepository(UserRepository):
    """在 Infrastructure 层实现（依赖 SQLAlchemy）"""
    async def save(self, user: User) -> User:
        # 具体的 SQLAlchemy 代码
        pass
```

**为什么？**
- Domain 层不依赖任何技术
- Infrastructure 层实现 Domain 层定义的接口
- 符合依赖倒置原则

---

### 原则 2：Repository 只做数据访问

```python
# ❌ 错误：在 Repository 中写业务逻辑

class SQLUserRepository(UserRepository):
    async def create_user(self, user_data: UserCreate) -> User:
        # ❌ 业务规则：检查密码强度
        if len(user_data.password) < 8:
            raise ValueError("Password too weak")

        # ❌ 业务逻辑：哈希密码
        user = User(
            username=user_data.username,
            password_hash=hash_password(user_data.password)
        )

        self.session.add(user)
        await self.session.commit()
        return user

# ✅ 正确：Repository 只做数据访问

class SQLUserRepository(UserRepository):
    async def save(self, user: User) -> User:
        # ✅ 只负责保存数据
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

# 业务逻辑在 Service 层
class UserService:
    async def create_user(self, user_data: UserCreate) -> User:
        # ✅ 业务规则：检查密码强度
        if len(user_data.password) < 8:
            raise InvalidPasswordException()

        # ✅ 业务逻辑：创建用户实体
        user = User.create(user_data)

        # ✅ 调用 Repository 保存
        return await self.repo.save(user)
```

---

### 原则 3：方法名要表达意图

```python
# ✅ 好的方法名（表达业务意图）

async def find_by_email(self, email: str) -> Optional[User]:
    """根据邮箱查找"""
    pass

async def email_exists(self, email: str) -> bool:
    """检查邮箱是否存在"""
    pass

async def find_active_users(self) -> List[User]:
    """查找活跃用户"""
    pass

# ❌ 不好的方法名（技术导向）

async def get_by_email(self, email: str):
    pass  # 和 find_by_email 有什么区别？

async def check_email(self, email: str):
    pass  # check 什么？存在？格式？

async def query_users_where_active_is_true(self):
    pass  # 太长，不直观
```

---

## 🎯 小实验：实现完整的 Repository

### 实验：用户管理 Repository

```python
# 1. 定义接口
class UserRepository(ABC):
    @abstractmethod
    async def save(self, user: User) -> User: pass

    @abstractmethod
    async def find_by_id(self, user_id: int) -> Optional[User]: pass

# 2. 实现 SQL Repository
class SQLUserRepository(UserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, user: User) -> User:
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def find_by_id(self, user_id: int) -> Optional[User]:
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

# 3. 集成到 FastAPI
def get_user_repo(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return SQLUserRepository(db)

@app.post("/users")
async def create_user(
    user: UserCreate,
    repo: UserRepository = Depends(get_user_repo)
):
    # 使用 Repository
    return await repo.create_user(user)
```

---

## 📚 检查理解

回答这些问题来测试你的理解：

1. **Repository 模式的作用是什么？**
   - 提示：抽象数据访问逻辑

2. **为什么 Repository 要定义接口？**
   - 提示：依赖倒置、可测试

3. **Repository 和 Service 的职责边界？**
   - 提示：Repository 只做数据访问，Service 做业务逻辑

4. **如何测试 Service 层？**
   - 提示：注入 Mock Repository

5. **依赖注入如何组装 Repository？**
   - 提示：get_db() → get_repo() → get_service()

---

## 🚀 下一步

现在你已经掌握了 Repository 模式，接下来：

1. **学习事务管理**：`notes/04_transactions.md`
2. **查看实际代码**：`examples/03_repository_pattern.py`

**记住**：Repository 模式是数据访问的最佳实践，它让数据访问逻辑集中、可测试、可维护！

---

**费曼技巧总结**：
- ✅ 仓库管理员类比
- ✅ 完整的架构层次图
- ✅ 接口定义 + SQL 实现 + Mock 实现
- ✅ 完整的 TODO 应用示例
- ✅ Repository 设计原则
