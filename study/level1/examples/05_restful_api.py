"""
阶段 1.5: FastAPI RESTful API 设计

学习目标:
1. 理解 RESTful API 设计原则
2. 掌握 CRUD 操作的标准实现
3. 学会设计合理的 URL 结构
4. 理解幂等性和安全性
5. 掌握状态码的正确使用
6. 学习如何保持 endpoint "薄"（只做协议适配）

运行方式:
    uvicorn study.level1.examples.05_restful_api:app --reload
    访问: http://localhost:8000/docs
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import FastAPI, HTTPException, status, Query, Path
from pydantic import BaseModel, Field, EmailStr, field_validator

# 创建 FastAPI 应用实例
app = FastAPI(
    title="FastAPI RESTful API 示例",
    description="演示完整的 RESTful API 设计和最佳实践",
    version="1.0.0"
)


# ============================================================================
# 1. RESTful API 设计原则
# ============================================================================

"""
【RESTful API 核心原则】

1. 资源导向
   - URL 表示资源（名词），不是动作
   - ✅ /users/     (用户列表)
   - ❌ /getUsers/  (包含动作)

2. HTTP 方法表示操作
   - GET:    获取资源（安全、幂等）
   - POST:   创建资源（非幂等）
   - PUT:    完整更新资源（幂等）
   - PATCH:  部分更新资源（非幂等）
   - DELETE: 删除资源（幂等）

3. 使用合适的 HTTP 状态码
   - 200 OK: 请求成功
   - 201 Created: 资源创建成功
   - 204 No Content: 删除成功（无返回内容）
   - 400 Bad Request: 请求参数错误
   - 404 Not Found: 资源不存在
   - 409 Conflict: 资源冲突

4. 版本控制
   - URL 版本: /api/v1/users/
   - Header 版本: Accept: application/vnd.api.v1+json

5. 过滤、排序、分页
   - GET /users/?page=1&limit=10&sort=name&order=desc
   - GET /users/?status=active&role=admin
"""


# ============================================================================
# 2. 定义数据模型
# ============================================================================

class UserBase(BaseModel):
    """用户基础模型"""
    username: str = Field(..., min_length=3, max_length=20, description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")
    full_name: Optional[str] = Field(None, max_length=50, description="全名")
    bio: Optional[str] = Field(None, max_length=500, description="个人简介")


class UserCreate(UserBase):
    """创建用户模型"""
    password: str = Field(..., min_length=6, max_length=50, description="密码")

    @field_validator('username')
    @classmethod
    def username_alphanumeric(cls, v):
        """验证用户名只包含字母数字下划线"""
        if not v.replace('_', '').isalnum():
            raise ValueError('用户名只能包含字母、数字和下划线')
        return v


class UserUpdate(BaseModel):
    """更新用户模型（所有字段可选）"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=50)
    bio: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None

    class Config:
        # 允许部分更新
        extra = "forbid"


class UserInDB(UserBase):
    """数据库中的用户模型"""
    id: int
    hashed_password: str
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None


class UserResponse(UserBase):
    """用户响应模型（不包含敏感信息）"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


# ============================================================================
# 3. 模拟数据库和业务逻辑层
# ============================================================================

# 注意：实际应用中，这些应该放在独立的 service/repository 层
# endpoint 应该保持"薄"，只做协议适配


class UserService:
    """
    用户服务层 - 业务逻辑

    ✅ 好的架构:
        - Endpoint (Thin Layer): 只做协议适配
        - Service Layer: 业务逻辑
        - Repository Layer: 数据访问

    这样可以:
        - 复用业务逻辑
        - 便于单元测试
        - 降低耦合
    """

    _fake_db: Dict[int, UserInDB] = {}
    _id_counter = 1

    @classmethod
    def create(cls, user_data: UserCreate) -> UserInDB:
        """创建用户"""
        # 检查用户名是否已存在
        for user in cls._fake_db.values():
            if user.username == user_data.username:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"用户名 '{user_data.username}' 已存在"
                )

        # 检查邮箱是否已存在
        for user in cls._fake_db.values():
            if user.email == user_data.email:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"邮箱 '{user_data.email}' 已被注册"
                )

        # 创建用户
        user = UserInDB(
            id=cls._id_counter,
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            bio=user_data.bio,
            hashed_password=f"hashed_{user_data.password}",  # 实际应该用 bcrypt
            is_active=True,
            created_at=datetime.now()
        )

        cls._fake_db[cls._id_counter] = user
        cls._id_counter += 1

        return user

    @classmethod
    def get_by_id(cls, user_id: int) -> UserInDB:
        """根据 ID 获取用户"""
        if user_id not in cls._fake_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"用户 ID {user_id} 不存在"
            )
        return cls._fake_db[user_id]

    @classmethod
    def list_all(
        cls,
        skip: int = 0,
        limit: int = 10,
        active_only: bool = False
    ) -> List[UserInDB]:
        """获取用户列表"""
        users = list(cls._fake_db.values())

        if active_only:
            users = [u for u in users if u.is_active]

        # 排序：按 ID 降序
        users = sorted(users, key=lambda u: u.id, reverse=True)

        # 分页
        return users[skip:skip + limit]

    @classmethod
    def update(cls, user_id: int, update_data: UserUpdate) -> UserInDB:
        """更新用户"""
        user = cls.get_by_id(user_id)

        # 只更新提供的字段
        update_dict = update_data.model_dump(exclude_unset=True)

        if not update_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="没有提供任何要更新的字段"
            )

        # 更新字段
        for field, value in update_dict.items():
            setattr(user, field, value)

        user.updated_at = datetime.now()

        return user

    @classmethod
    def delete(cls, user_id: int) -> None:
        """删除用户"""
        if user_id not in cls._fake_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"用户 ID {user_id} 不存在"
            )

        del cls._fake_db[user_id]

    @classmethod
    def count(cls) -> int:
        """获取用户总数"""
        return len(cls._fake_db)


# 初始化一些测试数据
UserService._fake_db = {
    1: UserInDB(
        id=1,
        username="alice",
        email="alice@example.com",
        full_name="Alice Smith",
        bio="Software Engineer",
        hashed_password="hashed_alice123",
        is_active=True,
        created_at=datetime.now()
    ),
    2: UserInDB(
        id=2,
        username="bob",
        email="bob@example.com",
        full_name="Bob Johnson",
        bio="Product Manager",
        hashed_password="hashed_bob456",
        is_active=True,
        created_at=datetime.now()
    ),
    3: UserInDB(
        id=3,
        username="charlie",
        email="charlie@example.com",
        full_name="Charlie Brown",
        bio="Designer",
        hashed_password="hashed_charlie789",
        is_active=False,
        created_at=datetime.now()
    )
}
UserService._id_counter = 4


# ============================================================================
# 4. RESTful API 端点实现
# ============================================================================

# ==================== 4.1 CREATE - 创建资源 ====================

@app.post(
    "/api/v1/users/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建用户",
    description="创建新用户，返回用户信息",
    responses={
        201: {"description": "用户创建成功"},
        409: {"description": "用户名或邮箱已存在"},
        422: {"description": "请求体验证失败"}
    },
    tags=["Users"]
)
async def create_user(user: UserCreate) -> UserInDB:
    """
    创建新用户 (POST /api/v1/users/)

    RESTful 原则:
        - 使用 POST 方法创建资源
        - URL 是集合路径 /users/
        - 返回 201 Created 状态码
        - 返回完整的资源信息

    幂等性: ❌ 非幂等（多次请求会创建多个资源）
    安全性: ❌ 不安全（修改服务器状态）
    """
    # ❌ 不好的做法: 在 endpoint 中直接写业务逻辑
    # if any(u.username == user.username for u in fake_db.values()):
    #     raise HTTPException(409, "用户名已存在")
    # new_user = UserInDB(...)
    # fake_db[new_user.id] = new_user
    # return new_user

    # ✅ 好的做法: 调用 Service 层处理业务逻辑
    # Endpoint 只做协议适配
    user_created = UserService.create(user)
    return user_created


# ==================== 4.2 READ - 读取资源 ====================

@app.get(
    "/api/v1/users/{user_id}",
    response_model=UserResponse,
    summary="获取用户详情",
    description="根据用户 ID 获取用户信息",
    responses={
        200: {"description": "成功获取用户信息"},
        404: {"description": "用户不存在"}
    },
    tags=["Users"]
)
async def get_user(
    user_id: int = Path(..., gt=0, description="用户 ID")
) -> UserInDB:
    """
    获取单个用户 (GET /api/v1/users/{user_id})

    RESTful 原则:
        - 使用 GET 方法读取资源
        - URL 包含资源 ID
        - 返回 200 OK
        - 返回完整的资源表示

    幂等性: ✅ 幂等（多次请求结果相同）
    安全性: ✅ 安全（不修改服务器状态）
    """
    user = UserService.get_by_id(user_id)
    return user


@app.get(
    "/api/v1/users/",
    response_model=List[UserResponse],
    summary="获取用户列表",
    description="获取用户列表，支持分页和过滤",
    tags=["Users"]
)
async def list_users(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(10, ge=1, le=100, description="返回的记录数"),
    active_only: bool = Query(False, description="只返回激活用户")
) -> List[UserInDB]:
    """
    获取用户列表 (GET /api/v1/users/)

    RESTful 原则:
        - 使用 GET 方法读取资源集合
        - 使用 Query 参数过滤、分页
        - 返回 200 OK
        - 返回资源列表

    分页参数:
        - skip: 跳过的记录数（默认 0）
        - limit: 返回的记录数（默认 10，最大 100）
        - active_only: 是否只返回激活用户

    幂等性: ✅ 幂等
    安全性: ✅ 安全

    扩展: 可以添加更多过滤参数
        - GET /api/v1/users/?status=active&role=admin
        - GET /api/v1/users/?sort=name&order=desc
    """
    users = UserService.list_all(skip, limit, active_only)

    # 可以在响应头中添加分页信息
    total = UserService.count()

    return users


# ==================== 4.3 UPDATE - 更新资源 ====================

@app.put(
    "/api/v1/users/{user_id}",
    response_model=UserResponse,
    summary="完整更新用户",
    description="更新用户的所有字段，未提供的字段会设置为默认值",
    responses={
        200: {"description": "用户更新成功"},
        404: {"description": "用户不存在"},
        422: {"description": "请求体验证失败"}
    },
    tags=["Users"]
)
async def update_user(
    user_id: int = Path(..., gt=0),
    user: UserBase = None
) -> UserInDB:
    """
    完整更新用户 (PUT /api/v1/users/{user_id})

    RESTful 原则:
        - 使用 PUT 方法完整更新资源
        - 请求体包含完整的资源表示
        - 返回 200 OK 和更新后的资源

    PUT vs PATCH:
        - PUT: 完整更新（替换整个资源）
        - PATCH: 部分更新（只更新提供的字段）

    示例请求体:
        {
            "username": "alice_new",
            "email": "alice_new@example.com",
            "full_name": "Alice Smith Jr.",
            "bio": "Senior Software Engineer"
        }

    幂等性: ✅ 幂等（多次相同的请求结果相同）
    安全性: ❌ 不安全

    ⚠️ 注意: 此示例中实际使用了部分更新逻辑
         完整的 PUT 实现应该替换所有字段
    """
    # 转换为 UserUpdate (实际应用中应该有专门的 PUT 模型)
    update_data = UserUpdate(**user.model_dump())
    updated_user = UserService.update(user_id, update_data)
    return updated_user


@app.patch(
    "/api/v1/users/{user_id}",
    response_model=UserResponse,
    summary="部分更新用户",
    description="只更新提供的字段，其他字段保持不变",
    responses={
        200: {"description": "用户更新成功"},
        404: {"description": "用户不存在"},
        400: {"description": "没有提供要更新的字段"}
    },
    tags=["Users"]
)
async def partial_update_user(
    user_id: int = Path(..., gt=0),
    user: UserUpdate = None
) -> UserInDB:
    """
    部分更新用户 (PATCH /api/v1/users/{user_id})

    RESTful 原则:
        - 使用 PATCH 方法部分更新资源
        - 只更新提供的字段
        - 未提供的字段保持不变

    示例请求体（只更新 email）:
        {
            "email": "newemail@example.com"
        }

    示例请求体（只更新状态）:
        {
            "is_active": false
        }

    幂等性: ❌ 非幂等（取决于具体操作）
    安全性: ❌ 不安全

    最佳实践:
        - PATCH 比 PUT 更灵活
        - 推荐使用 PATCH 进行更新
    """
    updated_user = UserService.update(user_id, user)
    return updated_user


# ==================== 4.4 DELETE - 删除资源 ====================

@app.delete(
    "/api/v1/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除用户",
    description="根据用户 ID 删除用户",
    responses={
        204: {"description": "用户删除成功"},
        404: {"description": "用户不存在"}
    },
    tags=["Users"]
)
async def delete_user(
    user_id: int = Path(..., gt=0, description="用户 ID")
):
    """
    删除用户 (DELETE /api/v1/users/{user_id})

    RESTful 原则:
        - 使用 DELETE 方法删除资源
        - 返回 204 No Content（无响应体）
        - 如果返回内容，使用 200 OK

    为什么是 204 而不是 200?
        - 204 表示请求成功但无返回内容
        - 删除操作通常不需要返回内容
        - 更节省带宽

    幂等性: ✅ 幂等（删除不存在的资源返回相同结果）
    安全性: ❌ 不安全

    软删除 vs 硬删除:
        - 软删除: 设置 is_active=False（推荐）
        - 硬删除: 从数据库中删除（数据丢失）

    实际应用建议:
        - 优先使用软删除
        - 记录删除时间和操作人
        - 提供恢复功能
    """
    UserService.delete(user_id)
    # 不返回任何内容，FastAPI 会自动返回 204


# ==================== 4.5 其他常用端点 ====================

@app.get(
    "/api/v1/users/{user_id}/posts/",
    response_model=List[dict],
    summary="获取用户的文章列表",
    description="获取指定用户的所有文章",
    tags=["Users"]
)
async def get_user_posts(user_id: int):
    """
    获取用户的子资源 (GET /api/v1/users/{user_id}/posts/)

    RESTful 设计 - 子资源:
        - URL 结构反映资源关系
        - /users/{id}/posts/  表示用户的文章
        - /posts/?user_id={id}  表示按用户过滤文章

    两种方式都可以，选择一种保持一致
    """
    # 确认用户存在
    UserService.get_by_id(user_id)

    # 返回模拟数据
    return [
        {"id": 1, "title": "First Post", "user_id": user_id},
        {"id": 2, "title": "Second Post", "user_id": user_id}
    ]


@app.post(
    "/api/v1/users/{user_id}/activate/",
    response_model=UserResponse,
    summary="激活用户",
    description="激活已禁用的用户账号",
    tags=["Users"]
)
async def activate_user(user_id: int):
    """
    激活用户 (POST /api/v1/users/{user_id}/activate/)

    这是一个动作端点，不是资源操作

    什么时候使用动作端点?
        - 操作不适合用 CRUD 表示
        - 需要执行特定动作
        - 如：激活、禁用、重置密码等

    RESTful 设计建议:
        - 优先使用资源操作（PUT/PATCH）
        - 避免过多的动作端点
        - 保持 URL 的一致性
    """
    user = UserService.get_by_id(user_id)

    # 使用 PATCH 更新状态更符合 RESTful
    update_data = UserUpdate(is_active=True)
    updated_user = UserService.update(user_id, update_data)

    return updated_user


# ============================================================================
# 5. 根路径和文档
# ============================================================================

@app.get("/", summary="API 文档入口")
async def root():
    """根路径，返回 API 信息"""
    return {
        "name": "FastAPI RESTful API 示例",
        "version": "1.0.0",
        "description": "演示完整的 RESTful API 设计和最佳实践",
        "endpoints": {
            "create_user": "POST /api/v1/users/",
            "get_user": "GET /api/v1/users/{user_id}",
            "list_users": "GET /api/v1/users/",
            "update_user": "PUT /api/v1/users/{user_id}",
            "partial_update": "PATCH /api/v1/users/{user_id}",
            "delete_user": "DELETE /api/v1/users/{user_id}",
            "user_posts": "GET /api/v1/users/{user_id}/posts/",
            "activate_user": "POST /api/v1/users/{user_id}/activate/"
        },
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health", summary="健康检查")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "RESTful API Demo",
        "version": "1.0.0"
    }


# ============================================================================
# 6. 运行说明
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║         FastAPI RESTful API 设计示例                       ║
    ╠════════════════════════════════════════════════════════════╣
    ║  启动服务...                                                ║
    ║  API 文档: http://localhost:8000/docs                      ║
    ║  ReDoc:   http://localhost:8000/redoc                     ║
    ╚════════════════════════════════════════════════════════════╝

    测试示例:

    1. 创建用户 (POST):
       curl -X POST http://localhost:8000/api/v1/users/ \\
         -H "Content-Type: application/json" \\
         -d '{
           "username": "david",
           "email": "david@example.com",
           "full_name": "David Lee",
           "bio": "Developer",
           "password": "password123"
         }'

    2. 获取用户列表 (GET):
       curl "http://localhost:8000/api/v1/users/?skip=0&limit=10&active_only=true"

    3. 获取单个用户 (GET):
       curl http://localhost:8000/api/v1/users/1

    4. 完整更新用户 (PUT):
       curl -X PUT http://localhost:8000/api/v1/users/1 \\
         -H "Content-Type: application/json" \\
         -d '{
           "username": "alice_updated",
           "email": "alice_updated@example.com",
           "full_name": "Alice Smith Jr.",
           "bio": "Senior Engineer"
         }'

    5. 部分更新用户 (PATCH):
       curl -X PATCH http://localhost:8000/api/v1/users/1 \\
         -H "Content-Type: application/json" \\
         -d '{"bio": "Updated bio"}'

    6. 删除用户 (DELETE):
       curl -X DELETE http://localhost:8000/api/v1/users/1

    7. 激活用户 (POST):
       curl -X POST http://localhost:8000/api/v1/users/3/activate/
    """)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True
    )


# ============================================================================
# 7. 最佳实践总结
# ============================================================================

"""
【RESTful API 设计最佳实践】

1. ✅ URL 设计
   - 使用名词表示资源: /users/
   - 使用复数形式: /users/ 而不是 /user/
   - 层级结构清晰: /users/{id}/posts/
   - 小写字母，连字符分隔: /api/v1/user-groups/

2. ✅ HTTP 方法的正确使用
   - GET:    获取资源（安全、幂等）
   - POST:   创建资源（非幂等）
   - PUT:    完整更新（幂等）
   - PATCH:  部分更新（非幂等）
   - DELETE: 删除资源（幂等）

3. ✅ 状态码规范
   - 200 OK: 成功
   - 201 Created: 创建成功
   - 204 No Content: 删除成功
   - 400 Bad Request: 请求错误
   - 404 Not Found: 资源不存在
   - 409 Conflict: 资源冲突

4. ✅ 架构分层
   - Endpoint (Thin Layer): 只做协议适配
   - Service Layer: 业务逻辑
   - Repository Layer: 数据访问

   ❌ 不好的做法:
       @app.post("/users/")
       async def create_user(user: UserCreate):
           # 直接在 endpoint 中写业务逻辑
           if exists(user.username):
               raise HTTPException(409)
           new_user = db.insert(user)
           return new_user

   ✅ 好的做法:
       @app.post("/users/")
       async def create_user(user: UserCreate):
           # 只做协议适配，业务逻辑在 Service 层
           return UserService.create(user)

5. ✅ 过滤、排序、分页
   - GET /users/?page=1&limit=10
   - GET /users/?status=active
   - GET /users/?sort=name&order=desc

6. ✅ 版本控制
   - URL 版本: /api/v1/users/ (推荐)
   - Header 版本: Accept: application/vnd.api.v1+json

7. ✅ 响应格式
   - 返回完整的资源表示
   - 使用统一的响应格式
   - 自动过滤敏感字段

8. ✅ 幂等性和安全性
   - GET、PUT、DELETE: 幂等
   - GET: 安全
   - POST、PUT、PATCH、DELETE: 不安全

9. ❌ 避免的陷阱
   - 不要在 URL 中使用动词: /getUsers/
   - 不要返回不一致的格式
   - 不要忽略幂等性
   - 不要在 endpoint 中写重业务逻辑
   - 不要忘记处理错误情况

10. ✅ 扩展性考虑
    - 预留版本号: /api/v1/users/
    - 支持过滤和搜索
    - 支持字段选择（部分响应）
    - 支持批量操作
    - 速率限制

参考资源:
    - RESTful API 设计指南: https://restfulapi.net/
    - HTTP 状态码: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status
    - JSON API 规范: https://jsonapi.org/
"""
