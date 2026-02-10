"""
FastAPI 统一响应格式示例

本示例演示如何实现和使用统一的 API 响应格式，包括：
1. 标准响应格式（code/message/data/timestamp）
2. 分页响应格式
3. 响应模型过滤（防止泄露敏感信息）
4. 可复用的响应辅助函数

运行命令：
    uvicorn app.examples.03_unified_response:app --reload

访问文档：
    http://localhost:8000/docs
"""

from fastapi import FastAPI, APIRouter, Depends, Query, HTTPException, status
from typing import Generic, TypeVar, Optional, List, Any
from pydantic import BaseModel, Field
import time

# 创建应用实例
app = FastAPI(
    title="统一响应格式示例",
    description="演示如何实现统一的 API 响应格式",
    version="1.0.0"
)

# ==========================================
# 第一部分：响应模型定义
# ==========================================

# 泛型类型，用于 data 字段
T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    """
    统一响应格式

    设计原则：
    - code: 业务状态码（与 HTTP 状态码可能不同）
    - message: 用户友好的消息
    - data: 实际数据（可选）
    - timestamp: 时间戳，便于调试
    """
    code: int = Field(
        default=200,
        description="业务状态码",
        examples=[200, 201, 400, 404]
    )
    message: str = Field(
        default="success",
        description="响应消息",
        examples=["操作成功", "查询成功", "创建成功"]
    )
    data: Optional[T] = Field(
        default=None,
        description="响应数据"
    )
    timestamp: int = Field(
        default_factory=lambda: int(time.time()),
        description="时间戳"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "code": 200,
                "message": "操作成功",
                "data": {"id": 1, "name": "张三"},
                "timestamp": 1739184000
            }
        }


class PaginationMeta(BaseModel):
    """分页元数据"""
    total: int = Field(..., description="总记录数", example=100)
    page: int = Field(..., ge=1, description="当前页码", example=1)
    page_size: int = Field(..., ge=1, description="每页大小", example=10)
    pages: int = Field(..., ge=0, description="总页数", example=10)


class PaginatedData(BaseModel, Generic[T]):
    """分页数据结构"""
    items: List[T] = Field(..., description="数据列表")
    pagination: PaginationMeta = Field(..., description="分页信息")


# ==========================================
# 第二部分：领域模型和响应模型
# ==========================================

class UserInDB(BaseModel):
    """
    用户领域模型（包含所有字段）

    注意：这个模型包含敏感信息（password_hash）
    不能直接作为响应模型！
    """
    id: int
    name: str
    email: str
    password_hash: str = Field(..., description="密码哈希（敏感）")
    created_at: str

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "张三",
                "email": "zhangsan@example.com",
                "password_hash": "hashed_password_here",
                "created_at": "2024-01-01T00:00:00Z"
            }
        }


class UserResponse(BaseModel):
    """
    用户响应模型（只包含可公开的字段）

    架构原则：响应模型应该过滤敏感信息
    """
    id: int
    name: str
    email: str
    created_at: str

    class Config:
        from_attributes = True  # 可以从 ORM 对象创建
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "张三",
                "email": "zhangsan@example.com",
                "created_at": "2024-01-01T00:00:00Z"
            }
        }


class UserCreate(BaseModel):
    """创建用户的请求模型"""
    name: str = Field(..., min_length=1, max_length=50)
    email: str = Field(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    password: str = Field(..., min_length=6, max_length=50)


# ==========================================
# 第三部分：响应辅助函数
# ==========================================

def success_response(
    data: Any = None,
    message: str = "操作成功",
    code: int = 200
) -> dict:
    """
    创建成功响应

    架构原则：辅助函数返回字典，FastAPI 自动序列化
    """
    return {
        "code": code,
        "message": message,
        "data": data,
        "timestamp": int(time.time())
    }


def paginated_response(
    items: List[Any],
    total: int,
    page: int,
    page_size: int,
    message: str = "查询成功"
) -> dict:
    """
    创建分页响应

    注意：分页计算在 Service 层完成
    这里只负责包装响应
    """
    pages = (total + page_size - 1) // page_size

    return {
        "code": 200,
        "message": message,
        "data": {
            "items": items,
            "pagination": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "pages": pages
            }
        },
        "timestamp": int(time.time())
    }


# ==========================================
# 第四部分：模拟 Service 层
# ==========================================

class UserService:
    """
    用户服务（模拟）

    架构原则：
    - Service 返回领域对象，不返回响应格式
    - 分页逻辑在 Service 层实现（数据库层面）
    - 业务规则在这里实现
    """

    # 模拟数据库
    _fake_db: List[UserInDB] = [
        UserInDB(
            id=i,
            name=f"用户{i}",
            email=f"user{i}@example.com",
            password_hash=f"hash_{i}",
            created_at="2024-01-01T00:00:00Z"
        )
        for i in range(1, 101)  # 100 个模拟用户
    ]

    async def get_user(self, user_id: int) -> Optional[UserInDB]:
        """获取单个用户"""
        for user in self._fake_db:
            if user.id == user_id:
                return user
        return None

    async def list_users(
        self,
        page: int,
        page_size: int
    ) -> tuple[List[UserInDB], int]:
        """
        获取用户列表（分页）

        返回：(用户列表, 总数)

        注意：在实际应用中，分页应该在数据库层面实现
        使用 LIMIT/OFFSET 而不是加载所有数据
        """
        total = len(self._fake_db)
        start = (page - 1) * page_size
        end = start + page_size

        items = self._fake_db[start:end]
        return items, total

    async def create_user(self, user_data: UserCreate) -> UserInDB:
        """创建用户"""
        new_id = len(self._fake_db) + 1

        # 模拟密码哈希（实际应该用 bcrypt）
        password_hash = f"hash_{user_data.password}"

        new_user = UserInDB(
            id=new_id,
            name=user_data.name,
            email=user_data.email,
            password_hash=password_hash,
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ")
        )

        self._fake_db.append(new_user)
        return new_user


# 依赖注入函数
def get_user_service() -> UserService:
    """获取 UserService 实例"""
    return UserService()


# ==========================================
# 第五部分：API 端点
# ==========================================

router = APIRouter(prefix="/api/users", tags=["用户管理"])


@router.get(
    "/{user_id}",
    response_model=ApiResponse[UserResponse],
    summary="获取用户详情",
    responses={
        200: {"description": "查询成功"},
        404: {"description": "用户不存在"}
    }
)
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service)
):
    """
    获取单个用户

    架构原则：
    1. Endpoint 参数校验（自动）
    2. 调用 Service 获取领域对象
    3. 使用 response_model 自动过滤敏感字段
    4. 包装统一响应格式
    """
    # 调用 Service 层
    user = await service.get_user(user_id)

    # 业务规则：用户不存在
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 返回成功响应
    # 注意：response_model 会自动过滤 password_hash
    return success_response(
        data=user,
        message="查询成功"
    )


@router.get(
    "",
    response_model=ApiResponse[PaginatedData[UserResponse]],
    summary="获取用户列表",
    responses={
        200: {"description": "查询成功"}
    }
)
async def list_users(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页大小"),
    service: UserService = Depends(get_user_service)
):
    """
    获取用户列表（分页）

    架构原则：
    1. 分页参数在 Endpoint 层接收
    2. Service 层实现分页逻辑
    3. Endpoint 层包装分页响应
    """
    # 调用 Service 层（分页逻辑在 Service）
    items, total = await service.list_users(page, page_size)

    # 返回分页响应
    return paginated_response(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.post(
    "",
    response_model=ApiResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="创建用户",
    responses={
        201: {"description": "创建成功"},
        400: {"description": "参数验证失败"}
    }
)
async def create_user(
    user_data: UserCreate,
    service: UserService = Depends(get_user_service)
):
    """
    创建用户

    架构原则：
    1. Pydantic 自动校验请求参数
    2. Service 处理业务逻辑
    3. 返回 201 状态码
    4. 响应模型自动过滤密码
    """
    # 调用 Service 创建用户
    new_user = await service.create_user(user_data)

    # 返回成功响应（201 Created）
    return success_response(
        data=new_user,
        message="创建成功",
        code=201
    )


@router.delete(
    "/{user_id}",
    response_model=ApiResponse[None],
    summary="删除用户",
    responses={
        200: {"description": "删除成功"},
        404: {"description": "用户不存在"}
    }
)
async def delete_user(
    user_id: int,
    service: UserService = Depends(get_user_service)
):
    """
    删除用户（示例）

    注意：成功但无数据时，data 为 null
    """
    user = await service.get_user(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 实际应用中这里会调用 service.delete_user(user_id)

    # 返回成功响应（无数据）
    return success_response(
        data=None,
        message="删除成功"
    )


# 注册路由
app.include_router(router)


# ==========================================
# 第六部分：对比示例 - 错误 vs 正确
# ==========================================

comparison_router = APIRouter(
    prefix="/api/comparison",
    tags=["架构对比示例"]
)


# ❌ 错误示例：不统一的响应格式
@comparison_router.get("/bad/users/{user_id}")
async def bad_get_user(user_id: int):
    """
    错误示例：不统一的响应格式

    问题：
    1. 直接返回对象，没有包装
    2. 没有统一的响应结构
    3. 前端无法统一处理
    """
    service = UserService()
    user = await service.get_user(user_id)

    if user is None:
        return {"error": "not found"}  # 错误格式！

    # 直接返回用户对象 - 格式不一致！
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email
    }


# ✅ 正确示例：统一的响应格式
@comparison_router.get("/good/users/{user_id}", response_model=ApiResponse[UserResponse])
async def good_get_user(user_id: int, service: UserService = Depends(get_user_service)):
    """
    正确示例：统一的响应格式

    优点：
    1. 使用统一的 ApiResponse 包装
    2. 前端可以统一处理
    3. 自动过滤敏感字段
    """
    user = await service.get_user(user_id)

    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")

    return success_response(data=user)


# ❌ 错误示例：在 Service 层返回响应格式
class BadUserService:
    """错误的 Service 实现"""

    async def get_user_with_response(self, user_id: int) -> dict:
        """错误：Service 返回响应格式"""
        user = await UserService().get_user(user_id)

        # ❌ Service 不应该知道响应格式！
        return {
            "code": 200,
            "message": "success",
            "data": user,
            "timestamp": int(time.time())
        }


# ✅ 正确示例：Service 返回领域对象
class GoodUserService:
    """正确的 Service 实现"""

    async def get_user(self, user_id: int) -> Optional[UserInDB]:
        """正确：Service 返回领域对象"""
        # 业务逻辑
        return await UserService().get_user(user_id)


app.include_router(comparison_router)


# ==========================================
# 启动和测试说明
# ==========================================

@app.get("/", summary="API 信息")
async def root():
    """根路径，返回 API 信息"""
    return {
        "message": "统一响应格式示例 API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "用户管理": "/api/users",
            "架构对比": "/api/comparison"
        }
    }


if __name__ == "__main__":
    import uvicorn

    print("""
    ╔═══════════════════════════════════════════════════════╗
    ║       FastAPI 统一响应格式示例                         ║
    ╠═══════════════════════════════════════════════════════╣
    ║  API 文档: http://localhost:8000/docs                  ║
    ║  测试端点:                                              ║
    ║    - GET  /api/users/1          (获取用户)            ║
    ║    - GET  /api/users             (用户列表)            ║
    ║    - POST /api/users             (创建用户)            ║
    ║    - GET  /api/comparison/good/users/1  (正确示例)    ║
    ║    - GET  /api/comparison/bad/users/1   (错误示例)    ║
    ╚═══════════════════════════════════════════════════════╝
    """)

    uvicorn.run(
        "app.examples.03_unified_response:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
