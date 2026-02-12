"""
示例 3.1: 数据库基础 - Database Basics

学习目标:
1. 理解数据库连接的基本概念
2. 掌握基本的 CRUD 操作
3. 学习如何使用 Context Manager 管理连接
4. 理解连接池的作用
5. 学习如何安全地处理数据库操作

架构演进:
    Level 2 (内存存储) → Level 3 (真实数据库)

运行方式:
    # 1. 启动 PostgreSQL (使用 Docker)
    docker run --name fastapi-db -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=fastapi -p 5432:5432 -d postgres:16

    # 2. 运行示例
    python study/level3/examples/01_database_basics.py

测试方式:
    # API 端点测试
    curl http://localhost:8000/docs
"""

from typing import Optional, List
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy import text, select, insert, update, delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import String, Boolean, DateTime

# ══════════════════════════════════════════════════════════════════════════
# 架构说明: 为什么需要理解数据库基础？
# ══════════════════════════════════════════════════════════════════════════
#
# 在学习 SQLAlchemy 之前，我们需要理解数据库的基本概念：
#
# 1. 连接管理 - 如何建立和管理数据库连接
# 2. CRUD 操作 - 增删改查的基本操作
# 3. 事务管理 - 保证数据一致性
# 4. 连接池 - 提高性能的关键
#
# ══════════════════════════════════════════════════════════════════════════


# ==================== 数据库配置 ====================

# ══════════════════════════════════════════════════════════════════════════
# 数据库 URL 格式说明
# ══════════════════════════════════════════════════════════════════════════
#
# PostgreSQL (asyncpg):
#   postgresql+asyncpg://user:password@host:port/database
#
# SQLite (aiosqlite):
#   sqlite+aiosqlite:///path/to/database.db
#
# MySQL (asyncmy):
#   mysql+asyncmy://user:password@host:port/database
#
# ══════════════════════════════════════════════════════════════════════════

# 使用 SQLite (简单、无需额外安装)
DATABASE_URL = "sqlite+aiosqlite:///../fastapi.db"

# 或使用 PostgreSQL (生产环境推荐)
# DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/fastapi"


# ══════════════════════════════════════════════════════════════════════════
# 创建异步引擎 (Create Async Engine)
# ══════════════════════════════════════════════════════════════════════════
#
# 引擎负责:
# 1. 管理数据库连接池
# 2. 处理数据库连接的创建和销毁
# 3. 提供 SQL 执行接口
#
# 关键配置参数:
# - echo: 是否打印 SQL (开发时设为 True，生产环境设为 False)
# - pool_size: 连接池大小
# - max_overflow: 最大溢出连接数
#
# ══════════════════════════════════════════════════════════════════════════

engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # 打印 SQL 语句（学习时很有用）

    # 连接池配置
    pool_size=5,  # 池中保持的连接数
    max_overflow=10,  # 最大溢出连接数

    # SQLite 特殊配置
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# 创建会话工厂
async_session = async_sessionmaker(
    engine,
    expire_on_commit=False  # 避免访问过期对象
)


# ==================== 模型定义 ====================

# ══════════════════════════════════════════════════════════════════════════
# SQLAlchemy 模型定义 (Model Definition)
# ══════════════════════════════════════════════════════════════════════════
#
# 模型 (Model) = 数据库表 (Table) 的 Python 表示
#
# 关键概念:
# 1. __tablename__: 数据库表名
# 2. Mapped[type]: 类型注解（IDE 提示友好）
# 3. mapped_column: 列定义
# 4. primary_key: 主键（唯一标识）
#
# ══════════════════════════════════════════════════════════════════════════

class Base(DeclarativeBase):
    """所有模型的基类"""
    pass


class User(Base):
    """
    用户模型

    对应的 SQL 表:
    CREATE TABLE users (
        id INTEGER PRIMARY KEY,
        username VARCHAR(50) NOT NULL,
        email VARCHAR(100) NOT NULL UNIQUE,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    __tablename__ = "users"

    # ═══════════════════════════════════════════════════════════════════
    # 主键 (Primary Key)
    # ═══════════════════════════════════════════════════════════════════
    #
    # 主键的作用:
    # 1. 唯一标识表中的每一行
    # 2. 用于建立表之间的关联（外键）
    # 3. 加速查询（自动创建索引）
    #
    # ═══════════════════════════════════════════════════════════════════

    id: Mapped[int] = mapped_column(primary_key=True)

    # ═══════════════════════════════════════════════════════════════════
    # 字段定义 (Field Definition)
    # ═══════════════════════════════════════════════════════════════════
    #
    # Mapped[type] - Python 3.12+ 的类型注解方式
    # mapped_column - 列配置
    #
    # 常用参数:
    # - nullable: 是否可为空
    # - unique: 是否唯一
    # - default: 默认值
    # - index: 是否创建索引
    #
    # ═══════════════════════════════════════════════════════════════════

    username: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(100), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"


# ==================== 数据库操作 ====================

# ══════════════════════════════════════════════════════════════════════════
# CRUD 操作示例 (Create, Read, Update, Delete)
# ══════════════════════════════════════════════════════════════════════════
#
# CRUD 是数据库操作的四个基本操作:
# - Create: 创建新记录
# - Read: 读取记录
# - Update: 更新记录
# - Delete: 删除记录
#
# ══════════════════════════════════════════════════════════════════════════

@asynccontextmanager
async def get_db():
    """
    获取数据库会话 (Context Manager)

    💡 为什么使用 Context Manager?
    1. 自动管理连接的创建和销毁
    2. 确保异常时也能正确关闭连接
    3. 代码更简洁

    ══════════════════════════════════════════════════════════════════════════
    资源管理对比
    ══════════════════════════════════════════════════════════════════════════

    ❌ 错误方式 (容易泄露连接):
    async def create_user():
        session = async_session()
        user = User(username="alice")
        session.add(user)
        await session.commit()
        # 如果这里抛出异常，session 永远不会关闭！

    ✅ 正确方式 (使用 Context Manager):
    async def create_user():
        async with async_session() as session:
            user = User(username="alice")
            session.add(user)
            await session.commit()
        # 无论是否异常，session 都会自动关闭

    ══════════════════════════════════════════════════════════════════════════
    """
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


# ══════════════════════════════════════════════════════════════════════════
# CREATE - 创建记录
# ══════════════════════════════════════════════════════════════════════════

async def create_user(session: AsyncSession, username: str, email: str) -> User:
    """
    创建用户 (Create)

    方式 1: 使用 ORM (推荐)
    ══════════════════════════════════════════════════════════════════════════

    ✅ 优势:
    - 类型安全
    - IDE 自动补全
    - 自动处理类型转换
    """

    # 1. 创建 Python 对象
    user = User(
        username=username,
        email=email,
        is_active=True
    )

    # 2. 添加到会话
    session.add(user)

    # 3. 提交事务
    await session.commit()

    # 4. 刷新对象（获取数据库生成的 id）
    await session.refresh(user)

    return user


async def create_user_with_raw_sql(session: AsyncSession, username: str, email: str) -> User:
    """
    创建用户 (使用原始 SQL)

    方式 2: 使用 Core (接近原始 SQL)

    ✅ 优势:
    - 性能更好
    - 更灵活（可以使用数据库特定功能）

    ❌ 劣势:
    - 不够类型安全
    - 需要手动处理类型
    """

    # 使用 insert 语句
    stmt = insert(User).values(
        username=username,
        email=email,
        is_active=True
    )

    # 执行并返回
    result = await session.execute(stmt)
    await session.commit()

    # 获取插入的 ID (SQLite)
    user_id = result.lastrowid

    # 查询新创建的用户
    user = await session.get(User, user_id)
    return user


# ══════════════════════════════════════════════════════════════════════════
# READ - 读取记录
# ══════════════════════════════════════════════════════════════════════════

async def get_user_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
    """
    根据 ID 获取用户 (Read)

    方式 1: 使用 session.get() (简单查询)
    """
    return await session.get(User, user_id)


async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
    """
    根据邮箱获取用户

    方式 2: 使用 select() (复杂查询)
    """
    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_all_users(session: AsyncSession) -> List[User]:
    """
    获取所有用户
    """
    stmt = select(User).order_by(User.created_at.desc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def search_users(session: AsyncSession, keyword: str) -> List[User]:
    """
    搜索用户 (模糊匹配)
    """
    stmt = select(User).where(
        User.username.contains(keyword)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


# ══════════════════════════════════════════════════════════════════════════
# UPDATE - 更新记录
# ══════════════════════════════════════════════════════════════════════════

async def update_user(
    session: AsyncSession,
    user_id: int,
    **kwargs
) -> Optional[User]:
    """
    更新用户 (Update)

    方式 1: 使用 ORM 对象 (推荐)
    """
    # 1. 获取用户
    user = await session.get(User, user_id)
    if not user:
        return None

    # 2. 修改字段
    for key, value in kwargs.items():
        if hasattr(user, key):
            setattr(user, key, value)

    # 3. 提交变更
    await session.commit()

    # 4. 刷新对象
    await session.refresh(user)

    return user


async def update_user_with_statement(
    session: AsyncSession,
    user_id: int,
    username: str
) -> Optional[User]:
    """
    更新用户 (使用 update 语句)

    方式 2: 使用 update() (批量更新更高效)
    """
    stmt = (
        update(User)
        .where(User.id == user_id)
        .values(username=username)
        .returning(User)  # PostgreSQL 特性
    )

    result = await session.execute(stmt)
    await session.commit()

    return result.scalar_one_or_none()


# ══════════════════════════════════════════════════════════════════════════
# DELETE - 删除记录
# ══════════════════════════════════════════════════════════════════════════

async def delete_user(session: AsyncSession, user_id: int) -> bool:
    """
    删除用户 (Delete)

    方式 1: 使用 session.delete()
    """
    user = await session.get(User, user_id)
    if not user:
        return False

    await session.delete(user)
    await session.commit()

    return True


async def delete_user_with_statement(session: AsyncSession, user_id: int) -> bool:
    """
    删除用户 (使用 delete 语句)

    方式 2: 使用 delete() (批量删除更高效)
    """
    stmt = delete(User).where(User.id == user_id)

    result = await session.execute(stmt)
    await session.commit()

    # affected_rows > 0 表示删除成功
    return result.rowcount > 0


# ==================== 初始化数据库 ====================

async def init_database():
    """
    初始化数据库

    创建所有表
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("✅ Database initialized successfully!")


# ==================== FastAPI 应用 ====================

app = FastAPI(
    title="数据库基础示例",
    description="演示基本的数据库连接和 CRUD 操作",
    version="1.0.0"
)


# ══════════════════════════════════════════════════════════════════════════
# 启动事件
# ══════════════════════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库"""
    await init_database()


# ══════════════════════════════════════════════════════════════════════════
# Pydantic 模型 (用于 API)
# ══════════════════════════════════════════════════════════════════════════

class UserCreate(BaseModel):
    """创建用户请求"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr


class UserUpdate(BaseModel):
    """更新用户请求"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """用户响应"""
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ══════════════════════════════════════════════════════════════════════════
# API Endpoints
# ══════════════════════════════════════════════════════════════════════════

@app.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user_endpoint(user_data: UserCreate):
    """
    创建用户

    ══════════════════════════════════════════════════════════════════════════
    依赖注入说明 (Dependency Injection)
    ══════════════════════════════════════════════════════════════════════════

    FastAPI 的 Depends() 会:
    1. 调用 get_db() 获取数据库会话
    2. 传递给 endpoint 函数
    3. endpoint 结束后自动关闭会话

    💡 注意: 实际项目中应该使用 Depends(get_db)
    这里为了演示简化，直接在函数中获取
    ══════════════════════════════════════════════════════════════════════════
    """
    async with get_db() as db:
        try:
            user = await create_user(
                db,
                user_data.username,
                user_data.email
            )
            return user

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create user: {str(e)}"
            )


@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user_endpoint(user_id: int):
    """获取用户"""
    async with get_db() as db:
        user = await get_user_by_id(db, user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )

        return user


@app.get("/users", response_model=List[UserResponse])
async def list_users_endpoint(keyword: Optional[str] = None):
    """列出用户"""
    async with get_db() as db:
        if keyword:
            users = await search_users(db, keyword)
        else:
            users = await get_all_users(db)

        return users


@app.put("/users/{user_id}", response_model=UserResponse)
async def update_user_endpoint(user_id: int, user_data: UserUpdate):
    """更新用户"""
    async with get_db() as db:
        # 过滤 None 值
        update_data = {k: v for k, v in user_data.dict().items() if v is not None}

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )

        user = await update_user(db, user_id, **update_data)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )

        return user


@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_endpoint(user_id: int):
    """删除用户"""
    async with get_db() as db:
        success = await delete_user(db, user_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "数据库基础示例",
        "version": "1.0.0",
        "endpoints": {
            "create_user": "POST /users",
            "get_user": "GET /users/{user_id}",
            "list_users": "GET /users",
            "update_user": "PUT /users/{user_id}",
            "delete_user": "DELETE /users/{user_id}"
        },
        "docs": "/docs"
    }


# ==================== 运行说明 ====================
"""
═══════════════════════════════════════════════════════════════════════════
数据库基础总结
═══════════════════════════════════════════════════════════════════════════

1. 数据库连接 (Database Connection)
   - 使用 create_async_engine() 创建引擎
   - 引擎管理连接池
   - 使用 async_sessionmaker() 创建会话工厂

2. CRUD 操作 (Create, Read, Update, Delete)
   - Create: session.add() + session.commit()
   - Read: select() + session.execute()
   - Update: 修改对象属性 + session.commit()
   - Delete: session.delete() + session.commit()

3. Context Manager (上下文管理器)
   - async with session: 自动管理连接
   - 确保异常时也能正确关闭
   - 推荐使用方式

4. 连接池 (Connection Pool)
   - 复用连接，提高性能
   - pool_size: 池中保持的连接数
   - max_overflow: 最大溢出连接数

═══════════════════════════════════════════════════════════════════════════
测试示例
═══════════════════════════════════════════════════════════════════════════

# 1. 创建用户
curl -X POST "http://localhost:8000/users" \\
      -H "Content-Type: application/json" \\
      -d '{"username": "alice", "email": "alice@example.com"}'

# 2. 获取用户
curl "http://localhost:8000/users/1"

# 3. 列出所有用户
curl "http://localhost:8000/users"

# 4. 搜索用户
curl "http://localhost:8000/users?keyword=alice"

# 5. 更新用户
curl -X PUT "http://localhost:8000/users/1" \\
      -H "Content-Type: application/json" \\
      -d '{"is_active": false}'

# 6. 删除用户
curl -X DELETE "http://localhost:8000/users/1"

═══════════════════════════════════════════════════════════════════════════
下一步学习
═══════════════════════════════════════════════════════════════════════════

掌握了基础后，继续学习:
1. SQLAlchemy 高级特性 → examples/02_sqlalchemy_basics.py
2. Repository 模式 → examples/03_repository_pattern.py
3. 事务管理 → examples/04_transactions.py

═══════════════════════════════════════════════════════════════════════════
"""
