"""
示例 3.3: Repository 模式 - Repository Pattern

学习目标:
1. 理解 Repository 模式的价值和设计原理
2. 掌握如何定义 Repository 接口
3. 实现完整的 SQLAlchemy Repository
4. 学习如何通过依赖注入集成 Repository
5. 理解如何使用 Mock Repository 进行测试

运行方式:
    # 1. 启动 PostgreSQL
    docker run --name fastapi-db -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=fastapi -p 5432:5432 -d postgres:16

    # 2. 运行示例
    python study/level3/examples/03_repository_pattern.py

测试方式:
    curl http://localhost:8002/docs
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import String, Boolean, DateTime

# ══════════════════════════════════════════════════════════════════════════
# 架构说明: Repository 模式的价值
# ══════════════════════════════════════════════════════════════════════════
#
# 为什么需要 Repository 模式?
#
# ══════════════════════════════════════════════════════════════════════════
# 问题: Service 直接使用 SQLAlchemy (紧耦合)
# ══════════════════════════════════════════════════════════════════════════
#
# ❌ 错误示例:
# class UserService:
#     def __init__(self, session: AsyncSession):
#         self.session = session  # ← 被绑死在 SQLAlchemy
#
#     async def create_user(self, user_data: UserCreate):
#         user = User(**user_data.model_dump())
#         self.session.add(user)
#         await self.session.commit()
#
# 问题:
# 1. Service 被绑死在 SQLAlchemy (无法换数据库)
# 2. 难以测试 (必须启动真实数据库)
# 3. SQL 逻辑散落在 Service 中 (无法复用)
# 4. 违反单一职责原则 (Service 既做业务逻辑又做数据访问)
#
# ══════════════════════════════════════════════════════════════════════════
# 解决方案: Repository 模式 (解耦)
# ══════════════════════════════════════════════════════════════════════════
#
# ✅ 正确示例:
# class UserRepository(ABC):
#     @abstractmethod
#     async def save(self, user: User) -> User: pass
#
# class SQLUserRepository(UserRepository):
#     async def save(self, user: User) -> User:
#         self.session.add(user)
#         await self.session.commit()
#         return user
#
# class UserService:
#     def __init__(self, repo: UserRepository):  # ← 依赖接口
#         self.repo = repo
#
#     async def create_user(self, user_data: UserCreate):
#         user = User.create(user_data)
#         return await self.repo.save(user)  # ← 调用接口
#
# 好处:
# 1. Service 只依赖接口 (不依赖具体实现)
# 2. 可以轻松换数据库 (PostgreSQL → MongoDB)
# 3. 可以注入 Mock Repository (易于测试)
# 4. 数据访问逻辑集中在 Repository (易于维护)
#
# ══════════════════════════════════════════════════════════════════════════


# ==================== 数据库配置 ====================

DATABASE_URL = "sqlite+aiosqlite:///../fastapi_repo.db"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}
)

async_session = async_sessionmaker(
    engine,
    expire_on_commit=False
)


# ==================== 领域层 (Domain Layer) ====================

# ══════════════════════════════════════════════════════════════════════════
# 领域层: 定义业务实体和接口
# ══════════════════════════════════════════════════════════════════════════
#
# 领域层不依赖任何框架 (FastAPI, SQLAlchemy)
# 只定义业务实体和行为
#
# ══════════════════════════════════════════════════════════════════════════

class Base(DeclarativeBase):
    """模型基类"""
    pass


class User(Base):
    """
    用户实体 (Domain Entity)

    ══════════════════════════════════════════════════════════════════════════
    领域实体 vs 数据模型
    ══════════════════════════════════════════════════════════════════════════

    领域实体 (这里):
    - 包含数据 (字段)
    - 包含行为 (方法)
    - 业务规则封装

    数据模型 (在 SQLAlchemy 中):
    - 只包含数据 (贫血模型)
    - 不包含业务逻辑

    💡 充血模型 vs 贫血模型
    - 充血模型: 领域实体包含业务逻辑 (推荐)
    - 贫血模型: 领域实体只有数据，逻辑在 Service 中
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # ═══════════════════════════════════════════════════════════════════
    # 领域行为 (Domain Behavior)
    # ═══════════════════════════════════════════════════════════════════

    def update_email(self, new_email: str) -> None:
        """
        更新邮箱 (包含业务规则)

        💡 业务规则应该在领域对象中
        而不是散落在各处
        """
        if "@" not in new_email:
            raise ValueError("Invalid email format")

        self.email = new_email

    def deactivate(self) -> None:
        """停用用户"""
        self.is_active = False

    def activate(self) -> None:
        """激活用户"""
        self.is_active = True

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username})>"


# ══════════════════════════════════════════════════════════════════════════
# 依赖倒置原则 (Dependency Inversion Principle)
# ══════════════════════════════════════════════════════════════════════════
#
# 定义: 高层模块不应依赖低层模块，都应依赖抽象
#
# 在这里:
# - 高层模块: Service (业务逻辑)
# - 低层模块: Repository (数据访问)
# - 抽象: UserRepository (接口)
#
# ══════════════════════════════════════════════════════════════════════════


class IUserRepository(ABC):
    """
    用户仓储接口 (Repository Interface)

    ══════════════════════════════════════════════════════════════════════════
    接口定义原则
    ══════════════════════════════════════════════════════════════════════════

    1. 在 Domain 层定义 (不依赖具体技术)
    2. 方法定义要表达业务意图
    3. 方法名要清晰 (find_by_*, exists_*, count_*)
    4. 返回类型要明确
    """

    @abstractmethod
    async def save(self, user: User) -> User:
        """
        保存用户

        如果是新用户: 插入
        如果是已存在用户: 更新
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
    async def find_by_username(self, username: str) -> Optional[User]:
        """根据用户名查找用户"""
        pass

    @abstractmethod
    async def find_all(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """查找所有用户（分页）"""
        pass

    @abstractmethod
    async def search(self, keyword: str) -> List[User]:
        """
        搜索用户

        搜索用户名或邮箱包含关键词的用户
        """
        pass

    @abstractmethod
    async def email_exists(self, email: str) -> bool:
        """检查邮箱是否存在"""
        pass

    @abstractmethod
    async def username_exists(self, username: str) -> bool:
        """检查用户名是否存在"""
        pass

    @abstractmethod
    async def count(self) -> int:
        """统计用户数量"""
        pass

    @abstractmethod
    async def delete(self, user_id: int) -> bool:
        """
        删除用户

        Returns:
            bool: 是否删除成功
        """
        pass


# ==================== 基础设施层 (Infrastructure Layer) ====================

# ══════════════════════════════════════════════════════════════════════════
# SQL 实现 (SQL Implementation)
# ══════════════════════════════════════════════════════════════════════════
#
# 实现 Domain 层定义的接口
# 负责具体的数据访问逻辑
#
# ══════════════════════════════════════════════════════════════════════════

class SQLUserRepository(IUserRepository):
    """
    SQL 用户仓储 (SQL Repository)

    ══════════════════════════════════════════════════════════════════════════
    Repository 的职责
    ══════════════════════════════════════════════════════════════════════════

    ✅ Repository 应该做的事:
    - CRUD 操作 (增删改查)
    - SQL 查询
    - 数据映射 (ORM 对象 ↔ 数据库行)
    - 连接管理

    ❌ Repository 不应该做的事:
    - 业务规则验证 (如：密码强度、余额是否足够)
    - 事务管理 (事务边界在 Service 层)
    - 调用外部服务 (如：发送邮件)
    - 复杂的数据处理 (应该在 Domain 层)
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, user: User) -> User:
        """
        保存用户

        ══════════════════════════════════════════════════════════════════════════
        SQLAlchemy 的 session.add() 行为
        ══════════════════════════════════════════════════════════════════════════
        - 如果 user.id 为 None: 执行 INSERT
        - 如果 user.id 已存在: 执行 UPDATE
        """
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def find_by_id(self, user_id: int) -> Optional[User]:
        """根据 ID 查找"""
        return await self.session.get(User, user_id)

    async def find_by_email(self, email: str) -> Optional[User]:
        """根据邮箱查找"""
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_username(self, username: str) -> Optional[User]:
        """根据用户名查找"""
        stmt = select(User).where(User.username == username)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_all(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """
        查找所有用户（分页）

        ══════════════════════════════════════════════════════════════════════════
        分页说明
        ══════════════════════════════════════════════════════════════════════════
        skip: 跳过多少条记录 (offset)
        limit: 返回多少条记录

        示例:
        skip=0, limit=10  → 第 1-10 条
        skip=10, limit=10 → 第 11-20 条
        """
        stmt = (
            select(User)
            .offset(skip)
            .limit(limit)
            .order_by(User.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def search(self, keyword: str) -> List[User]:
        """
        搜索用户

        ══════════════════════════════════════════════════════════════════════════
        使用 or_() 组合条件
        ══════════════════════════════════════════════════════════════════════════
        """
        stmt = select(User).where(
            or_(
                User.username.contains(keyword),
                User.email.contains(keyword)
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def email_exists(self, email: str) -> bool:
        """
        检查邮箱是否存在

        ══════════════════════════════════════════════════════════════════════════
        性能优化: 使用 count() 而不是 find_by_email()
        ══════════════════════════════════════════════════════════════════════════
        原因: count() 只需要返回数字，不需要加载整个对象
        """
        stmt = select(func.count(User.id)).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar() > 0

    async def username_exists(self, username: str) -> bool:
        """检查用户名是否存在"""
        stmt = select(func.count(User.id)).where(User.username == username)
        result = await self.session.execute(stmt)
        return result.scalar() > 0

    async def count(self) -> int:
        """统计用户数量"""
        stmt = select(func.count(User.id))
        result = await self.session.execute(stmt)
        return result.scalar()

    async def delete(self, user_id: int) -> bool:
        """删除用户"""
        user = await self.find_by_id(user_id)
        if not user:
            return False

        await self.session.delete(user)
        await self.session.commit()

        return True


# ══════════════════════════════════════════════════════════════════════════
# Mock 实现 (用于测试)
# ══════════════════════════════════════════════════════════════════════════

class InMemoryUserRepository(IUserRepository):
    """
    内存用户仓储 (Mock Repository)

    ══════════════════════════════════════════════════════════════════════════
    Mock Repository 的用途
    ══════════════════════════════════════════════════════════════════════════
    1. 单元测试: 不需要启动真实数据库
    2. 快速开发: 不需要等待数据库操作
    3. 演示教学: 清晰展示 Repository 模式的价值

    💡 Mock 实现和 SQL 实现可以互换！
    因为它们都实现了同一个接口 (IUserRepository)
    """

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

    async def find_by_username(self, username: str) -> Optional[User]:
        for user in self._users.values():
            if user.username == username:
                return user
        return None

    async def find_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        users = list(self._users.values())
        return users[skip:skip + limit]

    async def search(self, keyword: str) -> List[User]:
        result = []
        for user in self._users.values():
            if keyword in user.username or keyword in user.email:
                result.append(user)
        return result

    async def email_exists(self, email: str) -> bool:
        return await self.find_by_email(email) is not None

    async def username_exists(self, username: str) -> bool:
        return await self.find_by_username(username) is not None

    async def count(self) -> int:
        return len(self._users)

    async def delete(self, user_id: int) -> bool:
        if user_id in self._users:
            del self._users[user_id]
            return True
        return False


# ==================== 服务层 (Service Layer) ====================

# ══════════════════════════════════════════════════════════════════════════
# 服务层: 业务逻辑编排
# ══════════════════════════════════════════════════════════════════════════
#
# 服务层依赖 Repository 接口，不依赖具体实现
# 这样可以轻松切换数据库实现
#
# ══════════════════════════════════════════════════════════════════════════


class UserEmailExistsException(Exception):
    """邮箱已存在异常"""
    pass


class UserUsernameExistsException(Exception):
    """用户名已存在异常"""
    pass


class UserNotFoundException(Exception):
    """用户不存在异常"""
    pass


class UserService:
    """
    用户服务

    ══════════════════════════════════════════════════════════════════════════
    服务层的职责
    ══════════════════════════════════════════════════════════════════════════

    ✅ 服务层应该做的事:
    - 业务规则验证
    - 编排领域操作
    - 异常转换
    - 事务控制

    ❌ 服务层不应该做的事:
    - 数据访问逻辑 (在 Repository 中)
    - HTTP 协议处理 (在 Endpoint 中)
    """

    def __init__(self, repo: IUserRepository):
        """
        构造函数注入

        💡 依赖倒置: 依赖接口，不依赖具体实现
        """
        self.repo = repo

    async def create_user(
        self,
        username: str,
        email: str
    ) -> User:
        """
        创建用户 (业务逻辑)

        ══════════════════════════════════════════════════════════════════════════
        业务流程
        ══════════════════════════════════════════════════════════════════════════
        1. 业务规则验证 (邮箱/用户名是否存在)
        2. 创建领域对象
        3. 执行领域逻辑
        4. 持久化

        💡 所有业务逻辑都在这里
        而不是散落在 endpoint 中
        """
        # 1. 业务规则验证
        if await self.repo.email_exists(email):
            raise UserEmailExistsException(f"邮箱 {email} 已被使用")

        if await self.repo.username_exists(username):
            raise UserUsernameExistsException(f"用户名 {username} 已被使用")

        # 2. 创建领域对象
        user = User(
            username=username,
            email=email
        )

        # 3. 持久化
        saved_user = await self.repo.save(user)

        return saved_user

    async def get_user(self, user_id: int) -> User:
        """获取用户"""
        user = await self.repo.find_by_id(user_id)
        if not user:
            raise UserNotFoundException(f"用户 {user_id} 不存在")
        return user

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """列出所有用户"""
        return await self.repo.find_all(skip, limit)

    async def update_user_email(
        self,
        user_id: int,
        new_email: str
    ) -> User:
        """
        更新用户邮箱 (业务逻辑)

        ══════════════════════════════════════════════════════════════════════════
        业务逻辑
        ══════════════════════════════════════════════════════════════════════════
        1. 检查用户是否存在
        2. 检查新邮箱是否已被使用
        3. 调用领域对象的方法 (update_email)
        4. 保存
        """
        # 1. 检查用户是否存在
        user = await self.get_user(user_id)

        # 2. 检查新邮箱
        existing = await self.repo.find_by_email(new_email)
        if existing and existing.id != user_id:
            raise UserEmailExistsException(f"邮箱 {new_email} 已被使用")

        # 3. 更新 (领域逻辑)
        user.update_email(new_email)

        # 4. 保存
        return await self.repo.save(user)

    async def deactivate_user(self, user_id: int) -> User:
        """停用用户"""
        user = await self.get_user(user_id)
        user.deactivate()
        return await self.repo.save(user)

    async def delete_user(self, user_id: int) -> bool:
        """删除用户"""
        # 先检查用户是否存在
        await self.get_user(user_id)

        # 执行删除
        return await self.repo.delete(user_id)

    async def search_users(self, keyword: str) -> List[User]:
        """搜索用户"""
        return await self.repo.search(keyword)


# ==================== 依赖注入配置 ====================

# ══════════════════════════════════════════════════════════════════════════
# 依赖注入链 (Dependency Injection Chain)
# ══════════════════════════════════════════════════════════════════════════
#
# get_user_service
#   → get_user_repository
#     → get_db
#       → SQLUserRepository
#
# FastAPI 自动解析依赖链！
# ══════════════════════════════════════════════════════════════════════════


async def get_db() -> AsyncSession:
    """数据库会话依赖"""
    async with async_session() as session:
        yield session


def get_user_repository(
    db: AsyncSession = Depends(get_db)
) -> IUserRepository:
    """
    获取用户仓储

    💡 可以根据环境返回不同实现
    """
    # 生产环境: 使用 SQL Repository
    return SQLUserRepository(db)

    # 测试环境: 可以返回 Mock Repository
    # return InMemoryUserRepository()


def get_user_service(
    repo: IUserRepository = Depends(get_user_repository)
) -> UserService:
    """
    获取用户服务

    ══════════════════════════════════════════════════════════════════════════
    依赖注入流程
    ══════════════════════════════════════════════════════════════════════════
    1. FastAPI 看到 Depends(get_user_service)
    2. 解析依赖:
       get_user_service
         → Depends(get_user_repository)
           → Depends(get_db)
             → async_session()  ← 创建会话
           → SQLUserRepository(db)
         → UserService(repo)
    3. 调用 endpoint
    4. 请求结束，会话自动关闭
    """
    return UserService(repo)


# ==================== FastAPI 应用 ====================

app = FastAPI(
    title="Repository 模式示例",
    description="演示 Repository 模式的实现和价值",
    version="3.0.0"
)


@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# ══════════════════════════════════════════════════════════════════════════
# Pydantic 模型
# ══════════════════════════════════════════════════════════════════════════

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ══════════════════════════════════════════════════════════════════════════
# Endpoints
# ══════════════════════════════════════════════════════════════════════════

@app.post("/users", response_model=UserResponse, status_code=201)
async def create_user(
    user_data: UserCreate,
    service: UserService = Depends(get_user_service)
):
    """
    创建用户

    ══════════════════════════════════════════════════════════════════════════
    Endpoint 的职责
    ══════════════════════════════════════════════════════════════════════════
    ✅ Endpoint 只做:
    - 接收请求
    - 参数校验 (Pydantic)
    - 调用服务层
    - 返回响应
    - 异常处理

    ❌ Endpoint 不做:
    - 业务逻辑 (在 Service 中)
    - 数据访问 (在 Repository 中)
    """
    try:
        return await service.create_user(
            user_data.username,
            user_data.email
        )
    except (UserEmailExistsException, UserUsernameExistsException) as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service)
):
    """获取用户"""
    try:
        return await service.get_user(user_id)
    except UserNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@app.get("/users", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    service: UserService = Depends(get_user_service)
):
    """列出所有用户"""
    return await service.list_users(skip, limit)


@app.put("/users/{user_id}/email", response_model=UserResponse)
async def update_user_email(
    user_id: int,
    new_email: EmailStr,
    service: UserService = Depends(get_user_service)
):
    """更新用户邮箱"""
    try:
        return await service.update_user_email(user_id, new_email)
    except (UserNotFoundException, UserEmailExistsException) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    service: UserService = Depends(get_user_service)
):
    """删除用户"""
    try:
        await service.delete_user(user_id)
    except UserNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@app.get("/")
async def root():
    return {
        "name": "Repository 模式示例",
        "version": "3.0.0",
        "architecture": "Endpoint → Service → Repository → Database",
        "benefits": [
            "Service 只依赖接口 (不依赖具体实现)",
            "可以轻松换数据库 (PostgreSQL → MongoDB)",
            "可以注入 Mock Repository (易于测试)",
            "数据访问逻辑集中在 Repository (易于维护)"
        ],
        "docs": "/docs"
    }


# ==================== 运行说明 ====================
"""
═══════════════════════════════════════════════════════════════════════════
Repository 模式总结
═══════════════════════════════════════════════════════════════════════════

1. Repository 模式的价值
   - 抽象数据访问逻辑
   - 解耦 Service 和数据库
   - 易于测试 (可以注入 Mock)
   - 可以轻松换数据库实现

2. 接口定义原则
   - 在 Domain 层定义 (不依赖具体技术)
   - 方法定义要表达业务意图
   - 方法名要清晰

3. Repository 职责边界
   - ✅ 做: CRUD、SQL 查询、数据映射
   - ❌ 不做: 业务规则验证、事务管理、调用外部服务

4. 依赖注入
   - get_db() → get_repository() → get_service()
   - FastAPI 自动解析依赖链

═══════════════════════════════════════════════════════════════════════════
测试示例
═══════════════════════════════════════════════════════════════════════════

# 1. 创建用户
curl -X POST "http://localhost:8002/users" \\
      -H "Content-Type: application/json" \\
      -d '{"username": "alice", "email": "alice@example.com"}'

# 2. 获取用户
curl "http://localhost:8002/users/1"

# 3. 列出用户 (分页)
curl "http://localhost:8002/users?skip=0&limit=10"

# 4. 更新邮箱
curl -X PUT "http://localhost:8002/users/1/email?new_email=newalice@example.com"

# 5. 删除用户
curl -X DELETE "http://localhost:8002/users/1"

═══════════════════════════════════════════════════════════════════════════
下一步学习
═══════════════════════════════════════════════════════════════════════════

掌握了 Repository 模式后，继续学习:
1. 事务管理 → examples/04_transactions.py
2. 数据库迁移 → examples/05_migrations.py

═══════════════════════════════════════════════════════════════════════════
"""
