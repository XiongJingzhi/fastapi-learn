# 02. SQLAlchemy 入门 - SQLAlchemy Basics

## 📍 在架构中的位置

**从 SQL 到 ORM：用 Python 对象操作数据库**

```
┌─────────────────────────────────────────────────────────────┐
│          纯 SQL 方式（繁琐、易错）                           │
└─────────────────────────────────────────────────────────────┘

async def get_user(user_id: int):
    # ❌ 手动写 SQL
    query = "SELECT * FROM users WHERE id = $1"
    result = await db.execute(query, user_id)
    return result.fetchone()

问题：
- 容易出现 SQL 注入
- 类型不安全
- 代码重复
- 难以维护

═══════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────┐
│          ORM 方式（SQLAlchemy）                              │
└─────────────────────────────────────────────────────────────┘

async def get_user(user_id: int):
    # ✅ 使用 Python 对象
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()

好处：
- 类型安全
- 防止 SQL 注入
- 代码简洁
- 易于维护
```

**🎯 你的学习目标**：掌握 SQLAlchemy 的基本用法，用 Python 对象操作数据库。

---

## 🎯 什么是 SQLAlchemy？

**SQLAlchemy** 是 Python 最流行的 ORM（对象关系映射）框架。

### ORM 的概念

**ORM (Object-Relational Mapping)**：将 Python 对象映射到数据库表。

**类比**：翻译官

```
Python 对象          ORM           数据库表
   User    ───────► SQLAlchemy ◄──────  users
     │                            ┌────┬────────────┬──────────┐
     ├─ id                      │ id │ username    │ email    │
     ├─ username                ├────┼────────────┼──────────┤
     └─ email                  │ 1  │ alice       │ alice@.. │
                             └────┴────────────┴──────────┘
```

**核心思想**：
- 操作 Python 对象 = 操作数据库表
- 不需要直接写 SQL
- SQLAlchemy 自动生成 SQL

---

## 🏗️ SQLAlchemy 架构

### 两层架构

```
┌─────────────────────────────────────────────────────────────┐
│              SQLAlchemy 架构                                 │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│          ORM 层（你主要使用的部分）                          │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │    Model     │  │  Session     │  │  Query       │      │
│  │  (映射到表)   │  │ (事务管理)   │  │  (查询构建)   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ 自动转换
                          ▼
┌─────────────────────────────────────────────────────────────┐
│          Core 层（SQL 生成和执行）                           │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Engine     │  │  Connection  │  │  Expression  │      │
│  │  (连接池)     │  │  (数据库连接) │  │  (SQL 表达式) │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ 执行
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    数据库 (PostgreSQL)                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 定义模型（映射到表）

### 基本模型定义

```python
from sqlalchemy import String, Integer, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

# ═══════════════════════════════════════════════════════════
# 定义模型基类
# ═══════════════════════════════════════════════════════════

from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """所有模型的基类"""
    pass

# ═══════════════════════════════════════════════════════════
# 定义 User 模型
# ═══════════════════════════════════════════════════════════

class User(Base):
    """用户模型（映射到 users 表）"""

    __tablename__ = "users"

    # Mapped[类型] = mapped_column(配置)
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}')>"
```

**对应生成的 SQL**：

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP
);
```

---

### 字段类型映射

| Python 类型 | SQLAlchemy 类型 | SQL 类型 | 说明 |
|-------------|-----------------|----------|------|
| `int` | `Integer` | `INTEGER` | 整数 |
| `str` | `String(50)` | `VARCHAR(50)` | 字符串（长度限制） |
| `str` | `Text` | `TEXT` | 长文本 |
| `bool` | `Boolean` | `BOOLEAN` | 布尔值 |
| `float` | `Float` | `FLOAT` | 浮点数 |
| `Decimal` | `Numeric(10, 2)` | `NUMERIC(10,2)` | 精确小数（金额） |
| `datetime` | `DateTime` | `TIMESTAMP` | 日期时间 |
| `bytes` | `LargeBinary` | `BLOB` | 二进制数据 |
| `list` (JSON) | `JSON` | `JSON` | JSON 数据 |

---

## 🔧 配置数据库连接

### 创建异步引擎

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# ═══════════════════════════════════════════════════════════
# 1. 创建异步引擎
# ═══════════════════════════════════════════════════════════

# PostgreSQL
DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/dbname"

# SQLite（开发用）
# DATABASE_URL = "sqlite+aiosqlite:///./app.db"

engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # 打印 SQL（开发时用）
    pool_pre_ping=True,  # 连接前检查可用性
    pool_size=10,  # 连接池大小
)

# ═══════════════════════════════════════════════════════════
# 2. 创建 Session 工厂
# ═══════════════════════════════════════════════════════════

async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # 提交后不过期对象
)

# ═══════════════════════════════════════════════════════════
# 3. 创建表（如果不存在）
# ═══════════════════════════════════════════════════════════

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# 运行
# import asyncio
# asyncio.run(create_tables())
```

---

## 💾 CRUD 操作

### 1. Create（创建）

```python
async def create_user(
    session: AsyncSession,
    username: str,
    email: str,
    password: str
) -> User:
    """创建用户"""

    # 1. 创建 Python 对象
    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password)  # 哈希密码
    )

    # 2. 添加到会话
    session.add(user)

    # 3. 提交事务
    await session.commit()

    # 4. 刷新对象（获取数据库生成的 id）
    await session.refresh(user)

    return user

# 使用
async with async_session() as session:
    user = await create_user(session, "alice", "alice@example.com", "secret")
    print(f"Created user with id={user.id}")
```

**对应的 SQL**：
```sql
INSERT INTO users (username, email, password_hash, is_active, created_at)
VALUES ('alice', 'alice@example.com', '...', TRUE, '2024-01-15 10:30:00');
```

---

### 2. Read（读取）

```python
from sqlalchemy import select

async def get_user_by_id(
    session: AsyncSession,
    user_id: int
) -> User | None:
    """根据 ID 获取用户"""

    # 1. 构建查询
    stmt = select(User).where(User.id == user_id)

    # 2. 执行查询
    result = await session.execute(stmt)

    # 3. 获取结果
    user = result.scalar_one_or_none()

    return user

async def get_all_users(session: AsyncSession) -> list[User]:
    """获取所有用户"""

    stmt = select(User).order_by(User.created_at.desc())
    result = await session.execute(stmt)
    return list(result.scalars().all())

async def search_users(
    session: AsyncSession,
    keyword: str
) -> list[User]:
    """搜索用户"""

    stmt = select(User).where(
        User.username.contains(keyword)  # LIKE %keyword%
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())
```

---

### 3. Update（更新）

```python
async def update_user(
    session: AsyncSession,
    user_id: int,
    username: str | None = None,
    email: str | None = None
) -> User | None:
    """更新用户"""

    # 1. 获取用户
    user = await get_user_by_id(session, user_id)
    if not user:
        return None

    # 2. 修改属性
    if username is not None:
        user.username = username
    if email is not None:
        user.email = email

    # 3. 提交（SQLAlchemy 自动检测变化并生成 UPDATE）
    await session.commit()

    # 4. 刷新
    await session.refresh(user)

    return user
```

**对应的 SQL**：
```sql
UPDATE users
SET username = 'alice2', email = 'alice2@example.com'
WHERE id = 1;
```

---

### 4. Delete（删除）

```python
async def delete_user(session: AsyncSession, user_id: int) -> bool:
    """删除用户"""

    # 1. 获取用户
    user = await get_user_by_id(session, user_id)
    if not user:
        return False

    # 2. 删除
    await session.delete(user)

    # 3. 提交
    await session.commit()

    return True
```

**对应的 SQL**：
```sql
DELETE FROM users WHERE id = 1;
```

---

## 🔗 定义关系

### 一对一关系

**场景**：用户和用户资料

```python
class User(Base):
    """用户"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50))

    # 一对一关系
    profile: Mapped["UserProfile"] = relationship(
        back_populates="user"
    )

class UserProfile(Base):
    """用户资料"""
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    bio: Mapped[str] = mapped_column(Text)

    # 一对一关系
    user: Mapped["User"] = relationship(
        back_populates="profile"
    )

# 使用
async def create_user_with_profile(session: AsyncSession):
    user = User(username="alice")
    user.profile = UserProfile(bio="Developer")

    session.add(user)
    await session.commit()

    # 访问
    print(user.profile.bio)  # "Developer"
    print(user.profile.user.username)  # "alice"
```

---

### 一对多关系

**场景**：用户和订单

```python
class User(Base):
    """用户"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50))

    # 一对多关系
    orders: Mapped[list["Order"]] = relationship(
        back_populates="user"
    )

class Order(Base):
    """订单"""
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    product: Mapped[str] = mapped_column(String(100))

    # 多对一关系
    user: Mapped["User"] = relationship(
        back_populates="orders"
    )

# 使用
async def get_user_with_orders(session: AsyncSession, user_id: int):
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one()

    # 访问订单（自动加载）
    for order in user.orders:
        print(f"Order: {order.product}")

# 联合查询（Eager Loading）
from sqlalchemy.orm import selectinload

async def get_user_with_orders_eager(session: AsyncSession, user_id: int):
    stmt = select(User).where(User.id == user_id).options(
        selectinload(User.orders)  # 自动加载关联
    )
    result = await session.execute(stmt)
    user = result.scalar_one()

    # 订单已经加载（不会触发额外查询）
    print(user.orders[0].product)
```

---

### 多对多关系

**场景**：文章和标签

```python
# ═══════════════════════════════════════════════════════════
# 中间表（关联表）
# ═══════════════════════════════════════════════════════════

from sqlalchemy import Table

post_tags = Table(
    "post_tags",
    Base.metadata,
    Column("post_id", ForeignKey("posts.id"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True)
)

# ═══════════════════════════════════════════════════════════
# 模型
# ═══════════════════════════════════════════════════════════

class Post(Base):
    """文章"""
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))

    # 多对多关系
    tags: Mapped[list["Tag"]] = relationship(
        "Tag",
        secondary=post_tags,  # 中间表
        back_populates="posts"
    )

class Tag(Base):
    """标签"""
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))

    # 多对多关系
    posts: Mapped[list["Post"]] = relationship(
        "Post",
        secondary=post_tags,
        back_populates="tags"
    )

# 使用
async def add_post_with_tags(session: AsyncSession):
    # 创建文章
    post = Post(title="FastAPI Tutorial")

    # 创建标签
    python_tag = Tag(name="Python")
    web_tag = Tag(name="Web")

    # 添加标签
    post.tags.append(python_tag)
    post.tags.append(web_tag)

    session.add(post)
    await session.commit()

    # 查询
    for tag in post.tags:
        print(f"Tag: {tag.name}")
```

---

## 🎨 完整示例：博客系统

```python
from sqlalchemy import (
    create_async_engine, AsyncSession, String,
    Integer, Text, DateTime, ForeignKey, select, func
)
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, mapped_column,
    relationship, sessionmaker
)
from datetime import datetime

# ═══════════════════════════════════════════════════════════
# 1. 基类
# ═══════════════════════════════════════════════════════════

class Base(DeclarativeBase):
    pass

# ═══════════════════════════════════════════════════════════
# 2. 模型
# ═══════════════════════════════════════════════════════════

class User(Base):
    """用户"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(100))

    # 关系：用户写的文章
    posts: Mapped[list["Post"]] = relationship(
        back_populates="author"
    )

class Post(Base):
    """文章"""
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    # 关系：文章作者
    author: Mapped["User"] = relationship(
        back_populates="posts"
    )

    # 关系：文章评论
    comments: Mapped[list["Comment"]] = relationship(
        back_populates="post"
    )

class Comment(Base):
    """评论"""
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column(Text)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"))
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # 关系：所属文章
    post: Mapped["Post"] = relationship(
        back_populates="comments"
    )

# ═══════════════════════════════════════════════════════════
# 3. 数据库配置
# ═══════════════════════════════════════════════════════════

engine = create_async_engine("sqlite+aiosqlite:///./blog.db")
async_session = sessionmaker(engine, class_=AsyncSession)

# ═══════════════════════════════════════════════════════════
# 4. CRUD 操作
# ═══════════════════════════════════════════════════════════

async def create_post(
    session: AsyncSession,
    title: str,
    content: str,
    author_id: int
) -> Post:
    """创建文章"""
    post = Post(title=title, content=content, author_id=author_id)
    session.add(post)
    await session.commit()
    await session.refresh(post)
    return post

async def get_post_with_author(
    session: AsyncSession,
    post_id: int
) -> Post | None:
    """获取文章（包含作者信息）"""
    stmt = select(Post).where(Post.id == post_id).options(
        selectinload(Post.author)  # 自动加载作者
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def get_recent_posts(
    session: AsyncSession,
    limit: int = 10
) -> list[Post]:
    """获取最近的文章"""
    stmt = select(Post).order_by(
        Post.created_at.desc()
    ).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())

# ═══════════════════════════════════════════════════════════
# 5. 使用示例
# ═══════════════════════════════════════════════════════════

async def main():
    # 创建表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 使用会话
    async with async_session() as session:
        # 创建文章
        post = await create_post(
            session,
            title="My First Post",
            content="Hello World!",
            author_id=1
        )

        # 查询文章（包含作者）
        post = await get_post_with_author(session, post.id)
        print(f"Post: {post.title} by {post.author.username}")

        # 查询最近的文章
        posts = await get_recent_posts(session, limit=5)
        for post in posts:
            print(f"- {post.title}")
```

---

## 🎯 小实验：自己动手

### 实验 1：定义模型

```python
# 定义一个 Todo 模型
class Todo(Base):
    __tablename__ = "todos"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

---

### 实验 2：CRUD 操作

```python
# Create
async def create_todo(session: AsyncSession, title: str):
    todo = Todo(title=title)
    session.add(todo)
    await session.commit()
    return todo

# Read
async def get_todo(session: AsyncSession, todo_id: int):
    stmt = select(Todo).where(Todo.id == todo_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

# Update
async def complete_todo(session: AsyncSession, todo_id: int):
    todo = await get_todo(session, todo_id)
    if todo:
        todo.completed = True
        await session.commit()
    return todo

# Delete
async def delete_todo(session: AsyncSession, todo_id: int):
    todo = await get_todo(session, todo_id)
    if todo:
        await session.delete(todo)
        await session.commit()
    return True
```

---

## 📚 检查理解

回答这些问题来测试你的理解：

1. **什么是 ORM？它有什么好处？**
   - 提示：用 Python 对象操作数据库

2. **如何定义一个 SQLAlchemy 模型？**
   - 提示：继承 Base，使用 __tablename__

3. **如何插入一条记录？**
   - 提示：session.add(), session.commit()

4. **如何查询数据？**
   - 提示：select().where()

5. **一对多关系如何定义？**
   - 提示：relationship(), ForeignKey

---

## 🚀 下一步

现在你已经掌握了 SQLAlchemy 的基本用法，接下来：

1. **学习 Repository 模式**：`notes/03_repository_pattern.md`
2. **查看实际代码**：`examples/02_sqlalchemy_basics.py`

**记住**：SQLAlchemy 是 Python 生态最强大的 ORM，掌握它将让你的数据库操作变得简单而优雅！

---

**费曼技巧总结**：
- ✅ 翻译官类比
- ✅ 详细的类型映射表
- ✅ 完整的 CRUD 示例
- ✅ 三种关系类型
- ✅ 实际博客系统示例
