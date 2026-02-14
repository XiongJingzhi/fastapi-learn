# SQLAlchemy 基础 - Python ORM 实战指南

## 🎯 什么是 SQLAlchemy？

**SQLAlchemy 是 Python 最流行的 ORM（对象关系映射）框架**。

简单来说，它让你用 **Python 对象** 来操作数据库，而不是直接写 SQL 语句。

```python
# ❌ 传统方式：写原生 SQL
cursor.execute("SELECT * FROM users WHERE age > ?", (18,))
users = cursor.fetchall()

# ✅ SQLAlchemy：用 Python 对象
users = session.query(User).filter(User.age > 18).all()
```

---

## 💡 为什么使用 ORM？

### 对比：原生 SQL vs ORM

| 维度 | 原生 SQL | ORM (SQLAlchemy) |
|------|----------|------------------|
| **类型安全** | ❌ 运行时才发现错误 | ✅ 编译时类型检查 |
| **可维护性** | ❌ SQL 散落在代码各处 | ✅ 集中在 Model 定义 |
| **数据库移植** | ❌ 需要重写 SQL | ✅ 自动适配不同数据库 |
| **防止注入** | ❌ 需要手动转义 | ✅ 自动参数化查询 |
| **学习曲线** | ✅ 简单直接 | ⚠️ 需要学习框架 |
| **复杂查询** | ✅ SQL 更强大 | ⚠️ 复杂查询可能更复杂 |

**最佳实践**：
- 简单 CRUD → 使用 ORM
- 复杂查询 → 使用 ORM + Core (混合模式)
- 性能关键 → 使用原生 SQL + SQLAlchemy Core

---

## 🔑 SQLAlchemy 核心概念

### 1. 架构层次

SQLAlchemy 有两个主要部分：

```
┌─────────────────────────────────────────┐
│         ORM (对象关系映射)               │
│  ┌─────────────────────────────────┐   │
│  │  Session │  Query │  Model      │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
                  ↓ 使用
┌─────────────────────────────────────────┐
│         Core (SQL 表达式语言)            │
│  ┌─────────────────────────────────┐   │
│  │  Engine │  Connection │  Table │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
                  ↓ 连接
┌─────────────────────────────────────────┐
│            数据库 (DBAPI2)               │
│  (SQLite, PostgreSQL, MySQL, etc.)      │
└─────────────────────────────────────────┘
```

### 2. 核心组件

```python
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

# 1. Engine（引擎）- 数据库连接池
engine = create_engine("sqlite:///app.db")

# 2. Base（基类）- Model 的父类
Base = declarative_base()

# 3. Model（模型）- 数据库表的 Python 类
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)

# 4. Session（会话）- 数据库操作的句柄
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()
```

---

## 🎨 定义模型

### 基本模型定义

```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    """用户模型"""
    __tablename__ = "users"  # 数据库表名

    # 列定义
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"
```

### 关系定义

```python
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50))
    # 一对多关系
    posts = relationship("Post", back_populates="author")

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True)
    title = Column(String(100))
    user_id = Column(Integer, ForeignKey("users.id"))
    # 多对一关系
    author = relationship("User", back_populates="posts")
```

---

## 🔄 CRUD 操作

### Create（创建）

```python
# 方式 1：直接实例化
user = User(
    username="alice",
    email="alice@example.com",
    hashed_password="hashed_password_123"
)
session.add(user)
session.commit()

# 方式 2：使用 **dict
user_data = {
    "username": "bob",
    "email": "bob@example.com",
    "hashed_password": "hashed_password_456"
}
user = User(**user_data)
session.add(user)
session.commit()

# 方式 3：批量创建
users = [
    User(username=f"user{i}", email=f"user{i}@example.com")
    for i in range(10)
]
session.add_all(users)
session.commit()
```

### Read（读取）

```python
# 查询所有
users = session.query(User).all()

# 条件查询
user = session.query(User).filter(User.username == "alice").first()

# 多条件
users = session.query(User).filter(
    User.is_active == True,
    User.age > 18
).all()

# 使用 in_
users = session.query(User).filter(User.id.in_([1, 2, 3])).all()

# 使用 like
users = session.query(User).filter(User.username.like("%alice%")).all()

# 排序
users = session.query(User).order_by(User.created_at.desc()).all()

# 限制数量
users = session.query(User).limit(10).offset(20).all()

# 统计
count = session.query(User).count()
```

### Update（更新）

```python
# 方式 1：查询后修改
user = session.query(User).filter(User.id == 1).first()
user.username = "new_username"
session.commit()

# 方式 2：批量更新
session.query(User).filter(User.is_active == False).update(
    {"is_active": True},
    synchronize_session=False
)
session.commit()
```

### Delete（删除）

```python
# 删除单个
user = session.query(User).filter(User.id == 1).first()
session.delete(user)
session.commit()

# 批量删除
session.query(User).filter(User.is_active == False).delete()
session.commit()
```

---

## 🚀 异步 SQLAlchemy (FastAPI)

### 异步配置

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String

# 异步引擎（注意 URL 前缀是 +aiosqlite）
DATABASE_URL = "sqlite+aiosqlite:///./app.db"

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

# 异步依赖注入
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

### 异步 CRUD

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

async def create_user(session: AsyncSession, user_data: dict) -> User:
    """创建用户"""
    user = User(**user_data)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

async def get_user(session: AsyncSession, user_id: int) -> User | None:
    """获取用户"""
    result = await session.execute(
        select(User).filter(User.id == user_id)
    )
    return result.scalar_one_or_none()

async def get_users(session: AsyncSession, skip: int = 0, limit: int = 100):
    """获取用户列表"""
    result = await session.execute(
        select(User).offset(skip).limit(limit)
    )
    return result.scalars().all()

async def update_user(session: AsyncSession, user_id: int, user_data: dict):
    """更新用户"""
    result = await session.execute(
        select(User).filter(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if user:
        for key, value in user_data.items():
            setattr(user, key, value)
        await session.commit()
        await session.refresh(user)

    return user

async def delete_user(session: AsyncSession, user_id: int):
    """删除用户"""
    result = await session.execute(
        select(User).filter(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if user:
        await session.delete(user)
        await session.commit()

    return user
```

---

## 🔐 事务管理

### 基本事务

```python
async def transfer_money(
    session: AsyncSession,
    from_user_id: int,
    to_user_id: int,
    amount: float
):
    """转账 - 需要事务保证一致性"""
    try:
        # 开始事务
        async with session.begin():
            # 查询并锁定用户
            from_user = await session.get(User, from_user_id)
            to_user = await session.get(User, to_user_id)

            # 检查余额
            if from_user.balance < amount:
                raise ValueError("余额不足")

            # 转账
            from_user.balance -= amount
            to_user.balance += amount

        # 自动提交（如果成功）或回滚（如果失败）

    except Exception as e:
        # 事务自动回滚
        raise e
```

### 手动事务控制

```python
async def complex_operation(session: AsyncSession):
    """手动控制事务"""
    try:
        # 开始事务
        async with session.begin():
            # 操作 1
            user = User(username="alice")
            session.add(user)

            # 操作 2
            post = Post(title="First Post", user_id=user.id)
            session.add(post)

            # 如果任何操作失败，整个事务回滚

    except Exception as e:
        # 异常会触发回滚
        raise
```

---

## 🏗️ Repository 模式（推荐）

### 为什么使用 Repository 模式？

```
❌ 直接在 Service 层使用 SQLAlchemy：
class UserService:
    def get_user(self, user_id: int):
        user = session.query(User).filter(User.id == user_id).first()
        # 问题：Service 层依赖 SQLAlchemy

✅ 使用 Repository 模式：
class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def get_user(self, user_id: int):
        return self.user_repo.find_by_id(user_id)
        # 好处：Service 层只依赖接口，不依赖具体实现
```

### Repository 实现

```python
from typing import Generic, TypeVar, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

ModelType = TypeVar("ModelType")

class BaseRepository(Generic[ModelType]):
    """通用 Repository 基类"""

    def __init__(self, model: type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def find_by_id(self, id: int) -> Optional[ModelType]:
        """根据 ID 查找"""
        result = await self.session.execute(
            select(self.model).filter(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def find_all(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """查找所有"""
        result = await self.session.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def create(self, obj: ModelType) -> ModelType:
        """创建"""
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: ModelType) -> ModelType:
        """更新"""
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def delete(self, id: int) -> bool:
        """删除"""
        obj = await self.find_by_id(id)
        if obj:
            await self.session.delete(obj)
            await self.session.commit()
            return True
        return False

# 具体 Repository
class UserRepository(BaseRepository[User]):
    """用户 Repository"""

    async def find_by_username(self, username: str) -> Optional[User]:
        """根据用户名查找"""
        result = await self.session.execute(
            select(User).filter(User.username == username)
        )
        return result.scalar_one_or_none()

    async def find_active_users(self) -> List[User]:
        """查找活跃用户"""
        result = await self.session.execute(
            select(User).filter(User.is_active == True)
        )
        return result.scalars().all()

# 使用
async def example_usage(session: AsyncSession):
    user_repo = UserRepository(User, session)

    # 创建
    user = User(username="alice", email="alice@example.com")
    await user_repo.create(user)

    # 查询
    user = await user_repo.find_by_username("alice")
    users = await user_repo.find_active_users()

    # 更新
    user.is_active = False
    await user_repo.update(user)

    # 删除
    await user_repo.delete(user.id)
```

---

## ⚠️ 常见陷阱

### 陷阱 1：Session 线程安全

```python
# ❌ 错误：在多个线程共享同一个 Session
session = SessionLocal()
# 在不同线程中使用 session → 会导致问题

# ✅ 正确：每个线程/请求使用独立的 Session
def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
```

### 陷阱 2：忘记 refresh

```python
# ❌ 问题：修改数据库后，对象还是旧的
user = session.query(User).first()
# 在另一个地方修改了数据库
user_from_db = session.query(User).first()
print(user.username)  # 可能是旧值

# ✅ 正确：使用 refresh
user = session.query(User).first()
# 修改数据库后
session.refresh(user)
print(user.username)  # 最新的值
```

### 陷阱 3：N+1 查询问题

```python
# ❌ N+1 查询：每次访问关系都会查询数据库
users = session.query(User).all()
for user in users:
    print(user.posts)  # 每次都查询一次！

# ✅ 使用 eager loading
from sqlalchemy.orm import selectinload

users = session.query(User).options(
    selectinload(User.posts)
).all()
for user in users:
    print(user.posts)  # 不会额外查询
```

---

## 💡 最佳实践

### 1. 使用类型提示

```python
from typing import Optional, List

async def get_user(
    session: AsyncSession,
    user_id: int
) -> Optional[User]:
    """明确的返回类型"""
    ...
```

### 2. 连接池配置

```python
engine = create_async_engine(
    DATABASE_URL,
    echo=True,              # 开发环境打印 SQL
    pool_size=5,            # 连接池大小
    max_overflow=10,        # 最大溢出连接数
    pool_pre_ping=True,     # 连接前先测试
    pool_recycle=3600       # 1小时后回收连接
)
```

### 3. 使用 context manager

```python
async def with_session(func):
    """自动管理 Session 的装饰器"""
    async def wrapper(*args, **kwargs):
        async with AsyncSessionLocal() as session:
            try:
                return await func(session, *args, **kwargs)
            except Exception:
                await session.rollback()
                raise
    return wrapper
```

---

## 📚 快速参考

### 常用导入

```python
from sqlalchemy import (
    create_engine, Column, Integer, String,
    ForeignKey, DateTime, Boolean, select,
    update, delete, and_, or_, not_
)
from sqlalchemy.orm import (
    Session, sessionmaker, declarative_base,
    relationship, selectinload, joinedload
)
from sqlalchemy.ext.asyncio import (
    create_async_engine, AsyncSession,
    async_sessionmaker
)
```

### 查询模式

```python
# 同步
session.query(Model).filter(Model.field == value).first()

# 异步
result = await session.execute(
    select(Model).filter(Model.field == value)
)
model = result.scalar_one_or_none()
```

---

## 🎯 总结

**SQLAlchemy 核心要点**：

1. ✅ **ORM**：用 Python 对象操作数据库
2. ✅ **Core**：SQL 表达式语言（用于复杂查询）
3. ✅ **异步支持**：与 FastAPI 完美集成
4. ✅ **事务管理**：保证数据一致性
5. ✅ **Repository 模式**：解耦数据库层

**记住**：
- 定义 Model = 定义数据库表
- Session = 数据库操作的句柄
- 每个请求使用独立的 Session
- 使用 Repository 模式提高可维护性

**下一步**：学习 Alembic 数据库迁移（Level 3）

---

**SQLAlchemy 让数据库操作变得 Pythonic！** 🐍
