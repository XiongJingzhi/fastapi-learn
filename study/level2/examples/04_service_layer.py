"""
阶段 2.4: 实现服务层 - 真正的三层架构

学习目标:
1. 理解服务层在架构中的位置
2. 掌握 Repository 模式的实现
3. 学习如何组织业务逻辑
4. 理解依赖倒置原则
5. 实现完整的用户管理系统

架构演进:
    Level 1 (传输层混逻辑) → Level 2 (真正的分层)

运行方式:
    uvicorn study.level2.examples.04_service_layer:app --reload
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, Field, EmailStr

app = FastAPI(
    title="实现服务层",
    description="演示真正的三层架构：传输层 → 服务层 → 基础设施层",
    version="2.0.0"
)


# ══════════════════════════════════════════════════════════════════════════
# 架构总览
# ══════════════════════════════════════════════════════════════════════════
#
# ┌─────────────────────────────────────────────────────────────────────┐
# │ 传输层 (Transport Layer) - FastAPI Endpoints                       │
# │                                                                     │
# │  职责：协议适配                                                     │
# │  - 接收 HTTP 请求                                                   │
# │  - 参数校验（Pydantic）                                              │
# │  - 调用服务层                                                       │
# │  - 返回 HTTP 响应                                                   │
# └─────────────────────────────────────────────────────────────────────┘
#                               ↓ 依赖注入
# ┌─────────────────────────────────────────────────────────────────────┐
# │ 服务层 (Service Layer) - Business Logic                            │
# │                                                                     │
# │  职责：业务逻辑编排                                                 │
# │  - 业务规则验证                                                     │
# │  - 编排领域操作                                                     │
# │  - 事务边界控制                                                     │
# │  - 异常转换                                                         │
# └─────────────────────────────────────────────────────────────────────┘
#                               ↓ 依赖注入
# ┌─────────────────────────────────────────────────────────────────────┐
# │ 基础设施层 (Infrastructure Layer) - Data Access                    │
# │                                                                     │
# │  职责：数据持久化                                                   │
# │  - 数据库操作                                                       │
# │  - 缓存管理                                                         │
# │  - 外部 API 调用                                                    │
# └─────────────────────────────────────────────────────────────────────┘
# ══════════════════════════════════════════════════════════════════════════


# ==================== 领域层 (Domain Layer) ====================

# ══════════════════════════════════════════════════════════════════════════
# 领域层：定义业务实体和接口
# 这是架构的核心，不依赖任何框架
# ══════════════════════════════════════════════════════════════════════════


class User:
    """
    用户实体（领域模型）

    💡 领域模型 vs 数据模型：
    - 数据模型：只包含数据（贫血模型）
    - 领域模型：包含数据 + 行为（充血模型）

    ✅ 优势：
    - 业务逻辑集中管理
    - 不依赖框架
    - 易于测试
    """

    def __init__(
        self,
        id: Optional[int],
        username: str,
        email: str,
        password: str
    ):
        self.id = id
        self.username = username
        self.email = email
        self.password = password
        self.created_at = datetime.now()

    def hash_password(self):
        """
        业务逻辑：密码加密

        💡 领域逻辑应该在这里
        而不是散落在各处
        """
        if not self.password:
            raise ValueError("Password is required")
        # 实际应该使用 bcrypt
        self.password = f"hashed_{self.password}"

    def verify_password(self, raw_password: str) -> bool:
        """验证密码"""
        return self.password == f"hashed_{raw_password}"

    def update_email(self, new_email: str):
        """
        业务逻辑：更新邮箱

        💡 业务规则可以封装在领域对象中
        """
        if "@" not in new_email:
            raise ValueError("Invalid email format")
        self.email = new_email


class UserDuplicateError(Exception):
    """用户重复异常"""
    pass


class UserNotFoundError(Exception):
    """用户不存在异常"""
    pass


# ══════════════════════════════════════════════════════════════════════════
# 依赖倒置原则：定义抽象接口
# ══════════════════════════════════════════════════════════════════════════

class IUserRepository(ABC):
    """
    用户仓储接口（抽象）

    💡 为什么需要接口？
    1. 依赖倒置：高层不依赖低层，都依赖抽象
    2. 易于测试：可以注入 Mock
    3. 灵活替换：可以换不同的存储实现

    🎯 关键点：
    - 在领域层定义
    - 基础设施层实现
    - 服务层依赖接口，不依赖具体实现
    """

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
    async def find_all(self) -> List[User]:
        """查找所有用户"""
        pass

    @abstractmethod
    async def exists_by_email(self, email: str) -> bool:
        """检查邮箱是否存在"""
        pass

    @abstractmethod
    async def delete(self, user_id: int) -> bool:
        """删除用户"""
        pass


# ==================== 基础设施层 (Infrastructure Layer) ====================

# ══════════════════════════════════════════════════════════════════════════
# 基础设施层：实现接口
# ══════════════════════════════════════════════════════════════════════════


class InMemoryUserRepository(IUserRepository):
    """
    内存用户仓储（实现）

    💡 实现 IUserRepository 接口
    - 使用内存存储（演示用）
    - 生产环境应该用 SQLUserRepository

    ✅ 好处：
    - 可以随时替换实现
    - 不影响服务层代码
    - 易于测试
    """

    def __init__(self):
        self._users: dict[int, User] = {}
        self._next_id = 1

    async def save(self, user: User) -> User:
        """保存用户"""
        if user.id is None:
            user.id = self._next_id
            self._next_id += 1

        self._users[user.id] = user
        return user

    async def find_by_id(self, user_id: int) -> Optional[User]:
        """根据 ID 查找用户"""
        return self._users.get(user_id)

    async def find_by_email(self, email: str) -> Optional[User]:
        """根据邮箱查找用户"""
        for user in self._users.values():
            if user.email == email:
                return user
        return None

    async def find_all(self) -> List[User]:
        """查找所有用户"""
        return list(self._users.values())

    async def exists_by_email(self, email: str) -> bool:
        """检查邮箱是否存在"""
        return await self.find_by_email(email) is not None

    async def delete(self, user_id: int) -> bool:
        """删除用户"""
        if user_id in self._users:
            del self._users[user_id]
            return True
        return False


# ==================== 服务层 (Service Layer) ====================

# ══════════════════════════════════════════════════════════════════════════
# 服务层：业务逻辑编排
# ══════════════════════════════════════════════════════════════════════════


class UserService:
    """
    用户服务

    💡 服务层的职责：
    1. 业务规则验证
    2. 编排领域操作
    3. 事务边界控制
    4. 异常转换

    🔍 关键点：
    - 依赖 IUserRepository 接口，不依赖具体实现
    - 可以独立测试（注入 Mock）
    - 业务逻辑集中管理
    """

    def __init__(self, repo: IUserRepository):
        """
        构造函数注入

        💡 依赖倒置：
        - 依赖接口（IUserRepository）
        - 不依赖具体实现（InMemoryUserRepository）
        """
        self.repo = repo

    async def create_user(
        self,
        username: str,
        email: str,
        password: str
    ) -> User:
        """
        创建用户（业务逻辑）

        🔍 业务流程：
        1. 业务规则验证（邮箱是否已存在）
        2. 创建领域对象
        3. 执行领域逻辑（密码加密）
        4. 持久化

        💡 所有业务逻辑都在这里
        而不是散落在 endpoint 中
        """
        # 1. 业务规则验证
        if await self.repo.exists_by_email(email):
            raise UserDuplicateError(f"邮箱 {email} 已被使用")

        # 2. 创建领域对象
        user = User(
            id=None,
            username=username,
            email=email,
            password=password
        )

        # 3. 执行领域逻辑
        user.hash_password()

        # 4. 持久化
        saved_user = await self.repo.save(user)

        return saved_user

    async def get_user(self, user_id: int) -> User:
        """获取用户"""
        user = await self.repo.find_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"用户 {user_id} 不存在")
        return user

    async def list_users(self) -> List[User]:
        """列出所有用户"""
        return await self.repo.find_all()

    async def update_user_email(
        self,
        user_id: int,
        new_email: str
    ) -> User:
        """
        更新用户邮箱

        🔍 业务逻辑：
        1. 检查用户是否存在
        2. 检查新邮箱是否已被使用
        3. 更新邮箱（包含业务规则验证）
        """
        # 1. 检查用户是否存在
        user = await self.get_user(user_id)

        # 2. 检查新邮箱
        existing = await self.repo.find_by_email(new_email)
        if existing and existing.id != user_id:
            raise UserDuplicateError(f"邮箱 {new_email} 已被使用")

        # 3. 更新（领域逻辑）
        user.update_email(new_email)

        # 4. 保存
        return await self.repo.save(user)

    async def delete_user(self, user_id: int) -> bool:
        """删除用户"""
        # 先检查用户是否存在
        await self.get_user(user_id)

        # 执行删除
        return await self.repo.delete(user_id)


# ==================== 依赖注入配置 ====================

# ══════════════════════════════════════════════════════════════════════════
# 依赖注入配置：组装依赖
# ══════════════════════════════════════════════════════════════════════════


def get_user_repository() -> IUserRepository:
    """
    获取用户仓储（依赖提供者）

    💡 依赖注入的起点：
    - FastAPI 调用这个函数
    - 返回仓储实例
    - 可以根据环境返回不同实现
    """
    # 生产环境：
    # return SQLUserRepository(get_db_session())

    # 开发/测试环境：
    return InMemoryUserRepository()


def get_user_service(
    repo: IUserRepository = Depends(get_user_repository)
) -> UserService:
    """
    获取用户服务（依赖提供者）

    💡 依赖链：
    get_user_service
      → get_user_repository
        → InMemoryUserRepository

    ✅ FastAPI 自动解析依赖链
    """
    return UserService(repo)


# ==================== 传输层 (Transport Layer) ====================

# ══════════════════════════════════════════════════════════════════════════
# 传输层：FastAPI Endpoints
# ══════════════════════════════════════════════════════════════════════════


# ---- Pydantic 模型（用于 API）----

class UserCreate(BaseModel):
    """创建用户请求模型"""
    username: str = Field(..., min_length=3, max_length=20)
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserResponse(BaseModel):
    """用户响应模型"""
    id: int
    username: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


class ErrorDetail(BaseModel):
    """错误详情"""
    error: str
    message: str


# ---- Endpoints ----


@app.post("/api/users", response_model=UserResponse, status_code=201)
async def create_user(
    user_data: UserCreate,
    service: UserService = Depends(get_user_service)
):
    """
    创建用户

    ══════════════════════════════════════════════════════════════════════════
    传输层职责（只有这些）：
    ══════════════════════════════════════════════════════════════════════════

    ✅ 接收请求
    ✅ 参数校验（Pydantic）
    ✅ 调用服务层
    ✅ 返回响应
    ✅ 异常处理（将领域异常转为 HTTP 响应）

    ❌ 不包含业务逻辑
    ❌ 不直接操作数据库
    ❌ 不包含业务规则

    ══════════════════════════════════════════════════════════════════════════
    """
    try:
        # 调用服务层（所有业务逻辑在那里）
        user = await service.create_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password
        )
        return user

    except UserDuplicateError as e:
        # 业务异常 → HTTP 400
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.get("/api/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service)
):
    """获取用户"""
    try:
        return await service.get_user(user_id)
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@app.get("/api/users", response_model=List[UserResponse])
async def list_users(
    service: UserService = Depends(get_user_service)
):
    """列出所有用户"""
    users = await service.list_users()
    return users


@app.put("/api/users/{user_id}/email", response_model=UserResponse)
async def update_user_email(
    user_id: int,
    new_email: EmailStr,
    service: UserService = Depends(get_user_service)
):
    """更新用户邮箱"""
    try:
        return await service.update_user_email(user_id, new_email)
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except UserDuplicateError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.delete("/api/users/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    service: UserService = Depends(get_user_service)
):
    """删除用户"""
    try:
        await service.delete_user(user_id)
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ==================== 架构对比 ====================

@app.get("/architecture/comparison")
async def compare_architectures():
    """
    架构对比总结

    ══════════════════════════════════════════════════════════════════════════
    Level 1: 没有分层（问题）
    ══════════════════════════════════════════════════════════════════════════

    @app.post("/users")
    async def create_user(user_data: UserCreate):
        # ❌ 业务逻辑在 endpoint 中
        if await db.query("SELECT * FROM users WHERE email = ?", user_data.email):
            raise HTTPException(400, "Email exists")

        # ❌ 直接操作数据库
        hashed = hash_password(user_data.password)
        user_id = await db.insert("INSERT INTO users ...")

        return {"id": user_id}

    问题：
    - Endpoint 包含业务逻辑
    - 无法复用（CLI、gRPC 都用不了）
    - 难以测试（必须启动 HTTP）
    - 代码重复（多个 endpoint 写类似逻辑）

    ══════════════════════════════════════════════════════════════════════════
    Level 2: 三层架构（解决）
    ══════════════════════════════════════════════════════════════════════════

    # Endpoint（传输层）
    @app.post("/users")
    async def create_user(
        user_data: UserCreate,
        service: UserService = Depends(get_user_service)
    ):
        # ✅ 只做协议适配
        return await service.create_user(...)

    # Service（服务层）
    class UserService:
        async def create_user(self, ...):
            # ✅ 业务逻辑在这里
            if await self.repo.exists_by_email(email):
                raise UserDuplicateError()
            user = User.create(...)
            return await self.repo.save(user)

    # Repository（基础设施层）
    class InMemoryUserRepository:
        async def save(self, user: User):
            # ✅ 数据持久化
            ...

    优势：
    - Endpoint 只做协议适配
    - 业务逻辑可复用、可测试
    - 代码清晰、职责分明
    - 易于维护和扩展

    ══════════════════════════════════════════════════════════════════════════
    """
    return {
        "level_1_no_layering": {
            "description": "没有分层",
            "problems": [
                "业务逻辑在 endpoint",
                "无法复用",
                "难以测试",
                "代码重复"
            ]
        },
        "level_2_layered_architecture": {
            "description": "三层架构",
            "layers": {
                "transport": "传输层 - 协议适配",
                "service": "服务层 - 业务逻辑",
                "infrastructure": "基础设施层 - 数据访问"
            },
            "benefits": [
                "职责清晰",
                "易于测试",
                "可以复用",
                "易于维护"
            ]
        },
        "key_principle": "依赖注入让分层架构成为可能"
    }


# ==================== 根路径 ====================

@app.get("/")
async def root():
    return {
        "name": "真正的三层架构示例",
        "version": "2.0.0",
        "architecture": "Transport → Service → Infrastructure",
        "endpoints": {
            "create_user": "POST /api/users",
            "get_user": "GET /api/users/{user_id}",
            "list_users": "GET /api/users",
            "update_email": "PUT /api/users/{user_id}/email",
            "delete_user": "DELETE /api/users/{user_id}",
            "comparison": "/architecture/comparison"
        },
        "docs": "/docs"
    }


# ==================== 运行说明 ====================
"""
═══════════════════════════════════════════════════════════════════════════
三层架构总结
═══════════════════════════════════════════════════════════════════════════

传输层 (Transport Layer):
    - 职责：协议适配
    - 内容：接收请求、校验参数、调用服务、返回响应
    - 不包含：业务逻辑、数据库操作

服务层 (Service Layer):
    - 职责：业务逻辑编排
    - 内容：业务规则验证、编排领域操作、事务控制
    - 依赖：依赖接口，不依赖具体实现

基础设施层 (Infrastructure Layer):
    - 职责：数据持久化
    - 内容：数据库操作、缓存、外部 API
    - 实现：实现领域层定义的接口

═══════════════════════════════════════════════════════════════════════════
测试示例
═══════════════════════════════════════════════════════════════════════════

# 1. 创建用户
curl -X POST "http://localhost:8000/api/users" \\
      -H "Content-Type: application/json" \\
      -d '{"username": "alice", "email": "alice@example.com", "password": "password123"}'

# 2. 获取用户
curl "http://localhost:8000/api/users/1"

# 3. 列出所有用户
curl "http://localhost:8000/api/users"

# 4. 更新邮箱
curl -X PUT "http://localhost:8000/api/users/1/email?new_email=newalice@example.com"

# 5. 删除用户
curl -X DELETE "http://localhost:8000/api/users/1"

# 6. 架构对比
curl "http://localhost:8000/architecture/comparison"

═══════════════════════════════════════════════════════════════════════════
关键点
═══════════════════════════════════════════════════════════════════════════

1. 依赖倒置：
   - 服务层依赖接口（IUserRepository）
   - 不依赖具体实现（InMemoryUserRepository）
   - 可以随时替换实现

2. 单一职责：
   - 每层只做自己的事
   - 不越界、不混杂

3. 易于测试：
   - 服务层可以单独测试
   - 注入 Mock 仓储即可

4. 易于复用：
   - 服务层不依赖 FastAPI
   - 可以在 CLI、gRPC 中使用

═══════════════════════════════════════════════════════════════════════════
"""
