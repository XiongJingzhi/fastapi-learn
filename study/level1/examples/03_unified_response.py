"""
阶段 1.3: FastAPI 统一响应格式

学习目标:
1. 理解为什么需要统一的响应格式
2. 掌握如何创建通用响应模型
3. 学会使用 response_model 声明响应类型
4. 实现分页响应格式
5. 过滤敏感字段（如密码、内部ID等）

运行方式:
    uvicorn study.level1.examples.03_unified_response:app --reload
    访问: http://localhost:8000/docs
"""

from typing import Generic, TypeVar, List, Optional, Any
from datetime import datetime
from fastapi import FastAPI, status
from pydantic import BaseModel, Field

# 创建 FastAPI 应用实例
app = FastAPI(
    title="FastAPI 统一响应格式示例",
    description="演示如何构建统一的API响应格式",
    version="1.0.0"
)


# ============================================================================
# 1. 为什么需要统一响应格式？
# ============================================================================

"""
❌ 不好的做法 - 响应格式不一致:

    # 成功时
    {"id": 1, "name": "Alice"}

    # 失败时
    {"error": "用户不存在"}

    # 分页时
    {"data": [...], "page": 1}

✅ 好的做法 - 统一响应格式:

    # 成功时
    {
        "code": 200,
        "message": "success",
        "data": {"id": 1, "name": "Alice"}
    }

    # 失败时
    {
        "code": 404,
        "message": "用户不存在",
        "data": null
    }

    # 分页时
    {
        "code": 200,
        "message": "success",
        "data": {
            "items": [...],
            "total": 100,
            "page": 1,
            "page_size": 10
        }
    }

优点:
    ✅ 前端可以统一处理响应
    ✅ 易于添加统一功能（如请求ID、时间戳）
    ✅ 方便日志记录和监控
    ✅ API 更易于维护和扩展
"""


# ============================================================================
# 2. 定义通用响应模型
# ============================================================================

# 定义泛型类型变量，支持任意数据类型
T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    """
    统一响应模型

    Generic[T] 使其可以包装任意类型的数据

    示例:
        ApiResponse[User]      # 单个用户
        ApiResponse[List[User]] # 用户列表
    """
    code: int = Field(
        default=200,
        description="业务状态码，200表示成功"
    )
    message: str = Field(
        default="success",
        description="响应消息，描述操作结果"
    )
    data: Optional[T] = Field(
        default=None,
        description="响应数据，可以是任意类型"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="响应时间戳"
    )

    class Config:
        # 使模型可以从 ORM 对象创建
        from_attributes = True


# ============================================================================
# 3. 分页响应模型
# ============================================================================

class PaginatedResponse(BaseModel, Generic[T]):
    """
    分页响应模型

    用于返回列表数据，包含分页信息

    示例:
        PaginatedResponse[User]  # 用户分页列表
    """
    code: int = Field(default=200, description="业务状态码")
    message: str = Field(default="success", description="响应消息")
    data: Optional[T] = Field(default=None, description="数据列表")
    pagination: Optional["PaginationInfo"] = Field(
        default=None,
        description="分页信息"
    )
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


class PaginationInfo(BaseModel):
    """分页元信息"""
    total: int = Field(..., description="总记录数")
    page: int = Field(..., ge=1, description="当前页码")
    page_size: int = Field(..., ge=1, le=100, description="每页记录数")
    total_pages: int = Field(..., ge=0, description="总页数")
    has_next: bool = Field(..., description="是否有下一页")
    has_prev: bool = Field(..., description="是否有上一页")


# ============================================================================
# 4. 定义业务模型
# ============================================================================

class UserBase(BaseModel):
    """用户基础模型"""
    username: str = Field(..., min_length=3, max_length=20)
    email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")


class UserCreate(UserBase):
    """创建用户时的模型"""
    password: str = Field(..., min_length=6, max_length=50)


class UserInDB(UserBase):
    """数据库中的用户模型（包含敏感字段）"""
    id: int
    hashed_password: str  # 加密后的密码
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True
    internal_notes: Optional[str] = None  # 内部备注


class UserResponse(BaseModel):
    """对外暴露的用户模型（过滤敏感字段）"""
    id: int
    username: str
    email: str
    created_at: datetime
    is_active: bool


# ============================================================================
# 5. 模拟数据库
# ============================================================================

fake_users_db = [
    UserInDB(
        id=1,
        username="alice",
        email="alice@example.com",
        hashed_password="hashed_alice123",
        created_at=datetime.now(),
        is_active=True,
        internal_notes="VIP客户，优先处理"
    ),
    UserInDB(
        id=2,
        username="bob",
        email="bob@example.com",
        hashed_password="hashed_bob456",
        created_at=datetime.now(),
        is_active=False,
        internal_notes="账号被冻结"
    ),
]


# ============================================================================
# 6. API 端点实现
# ============================================================================

# ===== 6.1 基础响应格式 =====

@app.get(
    "/api/hello",
    response_model=ApiResponse[str],
    summary="基础响应示例"
)
async def hello_world():
    """
    最简单的统一响应示例

    返回:
        ```json
        {
            "code": 200,
            "message": "success",
            "data": "Hello, World!",
            "timestamp": "2025-02-12T10:00:00"
        }
        ```
    """
    return ApiResponse[str](
        code=200,
        message="success",
        data="Hello, World!"
    )


@app.get(
    "/api/user/{user_id}",
    response_model=ApiResponse[UserResponse],
    summary="获取用户信息（统一响应）"
)
async def get_user(user_id: int):
    """
    获取用户信息，使用统一响应格式

    关键点:
        - response_model=ApiResponse[UserResponse] 声明响应类型
        - 自动过滤 hashed_password 和 internal_notes 等敏感字段
        - 即使返回 UserInDB，也只会序列化 UserResponse 中定义的字段
    """
    # 查找用户
    user = next((u for u in fake_users_db if u.id == user_id), None)

    if not user:
        # ❌ 错误做法：返回不一致的格式
        # return {"error": "用户不存在"}

        # ✅ 正确做法：使用统一格式
        return ApiResponse[UserResponse](
            code=404,
            message=f"用户 ID {user_id} 不存在",
            data=None
        )

    # 返回用户信息（UserInDB 会被自动转换为 UserResponse）
    return ApiResponse[UserResponse](
        code=200,
        message="获取用户信息成功",
        data=user  # FastAPI 会根据 UserResponse 自动过滤敏感字段
    )


@app.post(
    "/api/users",
    response_model=ApiResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="创建用户（统一响应）"
)
async def create_user(user: UserCreate):
    """
    创建用户，使用统一响应格式

    关键点:
        - 创建时使用 UserCreate（需要密码）
        - 返回时使用 UserResponse（过滤密码）
        - 响应格式统一为 ApiResponse
    """
    # 检查用户名是否已存在
    if any(u.username == user.username for u in fake_users_db):
        return ApiResponse[UserResponse](
            code=400,
            message="用户名已存在",
            data=None
        )

    # 创建新用户（模拟）
    new_user = UserInDB(
        id=len(fake_users_db) + 1,
        username=user.username,
        email=user.email,
        hashed_password=f"hashed_{user.password}",  # 实际应该用 bcrypt
        created_at=datetime.now(),
        is_active=True,
        internal_notes="新用户"
    )
    fake_users_db.append(new_user)

    return ApiResponse[UserResponse](
        code=201,
        message="用户创建成功",
        data=new_user  # 自动过滤敏感字段
    )


# ===== 6.2 分页响应格式 =====

@app.get(
    "/api/users",
    response_model=PaginatedResponse[List[UserResponse]],
    summary="获取用户列表（分页）"
)
async def get_users(
    page: int = 1,
    page_size: int = 10,
    active_only: bool = True
):
    """
    获取用户列表，带分页功能

    参数:
        - page: 页码，从1开始
        - page_size: 每页记录数
        - active_only: 是否只返回激活用户

    返回格式:
        ```json
        {
            "code": 200,
            "message": "success",
            "data": [...],
            "pagination": {
                "total": 100,
                "page": 1,
                "page_size": 10,
                "total_pages": 10,
                "has_next": true,
                "has_prev": false
            },
            "timestamp": "2025-02-12T10:00:00"
        }
        ```
    """
    # 过滤用户
    filtered_users = fake_users_db
    if active_only:
        filtered_users = [u for u in filtered_users if u.is_active]

    # 计算分页
    total = len(filtered_users)
    total_pages = (total + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size
    users = filtered_users[start:end]

    # 构建分页信息
    pagination = PaginationInfo(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1
    )

    return PaginatedResponse[List[UserResponse]](
        code=200,
        message="获取用户列表成功",
        data=users,
        pagination=pagination
    )


# ===== 6.3 使用 response_model_exclude 过滤字段 =====

@app.get(
    "/api/user/{user_id}/admin",
    response_model=ApiResponse[UserInDB],
    response_model_exclude={"hashed_password", "internal_notes"},
    summary="获取用户详细信息（管理员视图）"
)
async def get_user_admin(user_id: int):
    """
    管理员查看用户详细信息

    使用 response_model_exclude 而不是创建新模型

    ❌ 不好的做法：
        为每个权限级别创建不同的响应模型

    ✅ 好的做法：
        使用 response_model_exclude 动态排除字段
    """
    user = next((u for u in fake_users_db if u.id == user_id), None)

    if not user:
        return ApiResponse[UserInDB](
            code=404,
            message="用户不存在",
            data=None
        )

    return ApiResponse[UserInDB](
        code=200,
        message="获取用户详情成功",
        data=user
    )
    # hashed_password 和 internal_notes 会被自动排除


# ===== 6.4 使用 response_model_include 只包含指定字段 =====

@app.get(
    "/api/user/{user_id}/brief",
    response_model=ApiResponse[UserResponse],
    response_model_include={"id", "username"},
    summary="获取用户简要信息"
)
async def get_user_brief(user_id: int):
    """
    获取用户简要信息，只包含部分字段

    使用 response_model_include 只返回指定字段

    返回:
        ```json
        {
            "code": 200,
            "message": "success",
            "data": {
                "id": 1,
                "username": "alice"
            }
        }
        ```
    """
    user = next((u for u in fake_users_db if u.id == user_id), None)

    if not user:
        return ApiResponse[UserResponse](
            code=404,
            message="用户不存在",
            data=None
        )

    return ApiResponse[UserResponse](
        code=200,
        message="success",
        data=user
    )
    # 只会返回 id 和 username 字段


# ============================================================================
# 7. 根路径和文档
# ============================================================================

@app.get("/", summary="API 文档入口")
async def root():
    """根路径，返回 API 信息"""
    return {
        "name": "FastAPI 统一响应格式示例",
        "version": "1.0.0",
        "description": "演示如何构建统一的 API 响应格式",
        "endpoints": {
            "hello": "/api/hello",
            "get_user": "/api/user/{user_id}",
            "create_user": "/api/users",
            "list_users": "/api/users?page=1&page_size=10",
            "user_admin": "/api/user/{user_id}/admin",
            "user_brief": "/api/user/{user_id}/brief"
        },
        "docs": "/docs",
        "redoc": "/redoc"
    }


# ============================================================================
# 8. 运行说明
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║         FastAPI 统一响应格式示例                            ║
    ╠════════════════════════════════════════════════════════════╣
    ║  启动服务...                                                ║
    ║  API 文档: http://localhost:8000/docs                      ║
    ║  ReDoc:   http://localhost:8000/redoc                     ║
    ╚════════════════════════════════════════════════════════════╝

    测试示例:

    1. 基础响应:
       curl http://localhost:8000/api/hello

    2. 获取用户信息:
       curl http://localhost:8000/api/user/1

    3. 创建用户:
       curl -X POST http://localhost:8000/api/users \\
         -H "Content-Type: application/json" \\
         -d '{"username":"charlie","email":"charlie@example.com","password":"pass123"}'

    4. 获取用户列表（分页）:
       curl "http://localhost:8000/api/users?page=1&page_size=10&active_only=true"

    5. 管理员查看用户详情:
       curl http://localhost:8000/api/user/1/admin

    6. 获取用户简要信息:
       curl http://localhost:8000/api/user/1/brief
    """)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True
    )


# ============================================================================
# 9. 最佳实践总结
# ============================================================================

"""
【统一响应格式最佳实践】

1. ✅ 使用 Generic 创建可复用的响应模型
   - ApiResponse[T] 支持任意数据类型
   - 避免为每个接口重复定义响应结构

2. ✅ 始终使用 response_model 声明响应类型
   - FastAPI 会自动验证返回数据
   - OpenAPI 文档会自动生成正确的 schema

3. ✅ 自动过滤敏感字段
   - 使用不同的模型进行输入和输出
   - UserCreate（输入）vs UserResponse（输出）
   - 避免密码、内部ID等泄露

4. ✅ 分页响应包含完整信息
   - 总记录数、当前页、每页大小
   - 总页数、是否有下一页
   - 方便前端构建分页组件

5. ✅ 状态码和业务状态码分离
   - HTTP 状态码：表示协议层面的成功/失败
   - 业务状态码(code)：表示业务逻辑的结果
   - 例如：HTTP 200，但 code=404 表示用户不存在

6. ✅ 使用 response_model_exclude/include 灵活控制输出
   - exclude: 排除特定字段（如密码）
   - include: 只包含特定字段（如简要信息）
   - 避免创建过多的模型类

7. ❌ 避免的陷阱:
   - 不要返回不一致的响应格式
   - 不要在响应中包含敏感信息
   - 不要忘记设置 response_model
   - 不要在响应中暴露内部实现细节
"""
