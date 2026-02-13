"""
Level 1 - Example 04: 错误处理 (Error Handling)

本示例展示 FastAPI 的错误处理机制：
1. 使用 HTTPException 抛出 HTTP 错误
2. 自定义领域异常 (Domain Exception)
3. 全局异常处理器 (Global Exception Handler)
4. 异常码到 HTTP 状态码的映射

运行方式:
    uvicorn study.level1.examples.04_error_handling:app --reload
"""

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime
import logging

app = FastAPI(title="Level 1 - Error Handling")

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ========== 自定义领域异常 ==========

class DomainException(Exception):
    """
    领域异常基类

    架构原则：
    - 领域异常不依赖 HTTP
    - 包含业务错误码和消息
    - 可以在 Service 层使用，不耦合 FastAPI
    """

    def __init__(
        self,
        message: str,
        code: str = "DOMAIN_ERROR",
        http_status: int = 400,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.http_status = http_status  # 映射的 HTTP 状态码
        self.details = details or {}
        super().__init__(self.message)


class NotFoundException(DomainException):
    """资源不存在异常"""

    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            message=f"{resource} {identifier} 不存在",
            code=f"{resource.upper()}_NOT_FOUND",
            http_status=404,
            details={"resource": resource, "identifier": str(identifier)}
        )


class ConflictException(DomainException):
    """资源冲突异常（如：邮箱已存在）"""

    def __init__(self, resource: str, field: str, value: Any):
        super().__init__(
            message=f"{resource} 的 {field} '{value}' 已存在",
            code=f"{resource.upper()}_CONFLICT",
            http_status=409,
            details={"resource": resource, "field": field, "value": str(value)}
        )


class BusinessException(DomainException):
    """业务规则违反异常"""

    def __init__(self, message: str, code: str = "BUSINESS_ERROR"):
        super().__init__(
            message=message,
            code=code,
            http_status=400
        )


class PermissionDeniedException(DomainException):
    """权限不足异常"""

    def __init__(self, message: str = "权限不足"):
        super().__init__(
            message=message,
            code="PERMISSION_DENIED",
            http_status=403
        )


# ========== 数据模型 ==========

class UserCreate(BaseModel):
    """创建用户的请求模型"""
    username: str = Field(..., min_length=3, max_length=20)
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = Field(None, max_length=50)


class UserResponse(BaseModel):
    """用户响应模型"""
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    created_at: datetime


# ========== 模拟数据库 ==========

fake_users_db: Dict[int, UserResponse] = {
    1: UserResponse(
        id=1,
        username="alice",
        email="alice@example.com",
        full_name="Alice Johnson",
        created_at=datetime(2024, 1, 10, 8, 0, 0)
    ),
    2: UserResponse(
        id=2,
        username="bob",
        email="bob@example.com",
        full_name="Bob Smith",
        created_at=datetime(2024, 1, 11, 9, 30, 0)
    )
}

user_id_counter = 3


# ========== 全局异常处理器 ==========

async def domain_exception_handler(
    request: Request,
    exc: DomainException
) -> JSONResponse:
    """
    领域异常处理器

    将领域异常转换为统一格式的 HTTP 响应
    """
    return JSONResponse(
        status_code=exc.http_status,
        content={
            "code": exc.http_status,
            "message": exc.message,
            "data": {
                "error_code": exc.code,
                **exc.details
            } if exc.details else None,
            "timestamp": int(datetime.now().timestamp())
        }
    )


async def http_exception_handler(
    request: Request,
    exc: HTTPException
) -> JSONResponse:
    """
    HTTP 异常处理器（统一格式）
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "message": exc.detail,
            "data": None,
            "timestamp": int(datetime.now().timestamp())
        }
    )


async def general_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    通用异常处理器（捕获所有未处理的异常）

    安全原则：
    - 不暴露内部错误详情给客户端
    - 记录完整日志用于调试
    - 返回友好的错误消息
    """
    # 记录完整错误日志
    logger.error(
        f"Unhandled exception on {request.url}: {exc}",
        exc_info=True,
        extra={"path": request.url.path, "method": request.method}
    )

    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "服务器内部错误",
            "data": None,
            "timestamp": int(datetime.now().timestamp())
        }
    )


# 注册异常处理器
app.add_exception_handler(DomainException, domain_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)


# ========== API 端点 ==========

@app.get("/")
async def root():
    """根端点"""
    return {
        "message": "Error Handling Demo",
        "endpoints": {
            "users": "/users",
            "users_with_id": "/users/{user_id}",
            "trigger_error": "/error/{type}"
        }
    }


# ========== 示例 1：抛出领域异常 ==========

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    """
    获取用户 - 使用领域异常

    如果用户不存在，抛出 NotFoundException（领域异常）
    全局处理器会自动将其转换为 404 HTTP 响应
    """
    user = fake_users_db.get(user_id)

    if not user:
        # 抛出领域异常（不依赖 HTTP）
        raise NotFoundException("User", user_id)

    return user


@app.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    """
    创建用户 - 使用领域异常

    可能抛出的异常：
    - ConflictException: 邮箱已存在 (409)
    - BusinessException: 业务规则违反 (400)
    """
    global user_id_counter

    # 检查邮箱是否已存在
    for existing_user in fake_users_db.values():
        if existing_user.email == user.email:
            # 抛出领域异常
            raise ConflictException("User", "email", user.email)

    # 创建用户
    new_user = UserResponse(
        id=user_id_counter,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        created_at=datetime.now()
    )

    fake_users_db[user_id_counter] = new_user
    user_id_counter += 1

    return new_user


# ========== 示例 2：直接使用 HTTPException ==========

@app.get("/items/{item_id}")
async def get_item(item_id: int):
    """
    获取商品 - 使用 HTTPException

    简单场景可以直接使用 HTTPException
    """
    # 模拟商品不存在
    if item_id != 1:
        raise HTTPException(
            status_code=404,
            detail=f"商品 {item_id} 不存在"
        )

    return {
        "id": item_id,
        "name": "Sample Item"
    }


# ========== 示例 3：自定义验证错误 ==========

class SpecialUserCreate(BaseModel):
    """带自定义验证的用户创建模型"""

    username: str

    @validator('username')
    def username_must_contain_number(cls, v):
        """用户名必须包含数字"""
        if not any(c.isdigit() for c in v):
            raise BusinessException("用户名必须包含至少一个数字", "USERNAME_NO_NUMBER")
        return v


@app.post("/users/special")
async def create_special_user(user: SpecialUserCreate):
    """创建特殊用户 - 使用自定义验证异常"""
    # Pydantic 验证会自动调用 validator
    # 如果验证失败，会抛出 BusinessException

    return {
        "message": f"用户 {user.username} 创建成功",
        "username": user.username
    }


# ========== 示例 4：错误演示端点 ==========

@app.get("/error/{error_type}")
async def trigger_error(error_type: str):
    """
    触发各种类型的错误（用于测试）

    Types:
    - not_found: 资源不存在
    - conflict: 资源冲突
    - business: 业务规则违反
    - permission: 权限不足
    - http: 直接 HTTPException
    - general: 未捕获的异常
    """
    if error_type == "not_found":
        raise NotFoundException("Product", 123)

    elif error_type == "conflict":
        raise ConflictException("Order", "order_id", "ORD-2024-001")

    elif error_type == "business":
        raise BusinessException("余额不足", "INSUFFICIENT_BALANCE")

    elif error_type == "permission":
        raise PermissionDeniedException("您没有权限访问此资源")

    elif error_type == "http":
        raise HTTPException(
            status_code=400,
            detail="直接使用 HTTPException"
        )

    elif error_type == "general":
        # 触发通用异常（被 general_exception_handler 捕获）
        1 / 0  # ZeroDivisionError

    else:
        raise HTTPException(
            status_code=400,
            detail=f"未知错误类型: {error_type}"
        )


# ========== 示例 5：多级错误处理 ==========

@app.get("/users/{user_id}/profile/{section}")
async def get_user_profile_section(user_id: int, section: str):
    """
    获取用户资料的特定部分

    演示多级错误处理：
    1. 用户不存在 (404)
    2. 资料部分不存在 (404)
    3. 权限不足 (403)
    """
    # 1. 检查用户是否存在
    user = fake_users_db.get(user_id)
    if not user:
        raise NotFoundException("User", user_id)

    # 2. 检查资料部分是否有效
    valid_sections = ["basic", "contact", "preferences"]
    if section not in valid_sections:
        raise BusinessException(
            message=f"无效的资料部分: {section}. 有效值: {', '.join(valid_sections)}",
            code="INVALID_SECTION"
        )

    # 3. 模拟权限检查
    if section == "preferences" and user_id == 1:
        raise PermissionDeniedException("您无权访问此用户的偏好设置")

    # 返回资料数据
    return {
        "user_id": user_id,
        "section": section,
        "data": f"Sample data for {section} section"
    }


# ========== 示例 6：错误响应对比 ==========

@app.get("/compare/{use_domain_exception}")
async def compare_error_handling(use_domain_exception: bool, user_id: int = 999):
    """
    对比两种错误处理方式

    - use_domain_exception=true: 使用领域异常（推荐）
    - use_domain_exception=false: 使用 HTTPException（不推荐）

    访问：/compare/true 或 /compare/false
    """
    if use_domain_exception:
        # ✅ 推荐：使用领域异常
        # 优点：
        # 1. Service 层不依赖 HTTP
        # 2. 可以在其他场景复用（如 CLI、gRPC）
        # 3. 便于单元测试
        raise NotFoundException("User", user_id)

    else:
        # ❌ 不推荐：直接使用 HTTPException
        # 缺点：
        # 1. 如果在 Service 层使用，会耦合 HTTP
        # 2. 难以在其他场景复用
        # 3. 测试时需要模拟 HTTP
        raise HTTPException(
            status_code=404,
            detail=f"用户 {user_id} 不存在"
        )


# ========== 主程序入口 ==========

if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("FastAPI Error Handling Demo")
    print("=" * 60)
    print()
    print("测试端点：")
    print("  正常请求：")
    print("    curl http://localhost:8000/users/1")
    print()
    print("  资源不存在（领域异常）：")
    print("    curl http://localhost:8000/users/999")
    print()
    print("  资源冲突：")
    print("    curl -X POST http://localhost:8000/users \\")
    print("      -H 'Content-Type: application/json' \\")
    print("      -d '{\"username\": \"test\", \"email\": \"alice@example.com\", \"password\": \"password123\"}'")
    print()
    print("  错误类型测试：")
    print("    curl http://localhost:8000/error/not_found")
    print("    curl http://localhost:8000/error/conflict")
    print("    curl http://localhost:8000/error/business")
    print("    curl http://localhost:8000/error/permission")
    print("    curl http://localhost:8000/error/general")
    print()
    print("  对比两种错误处理方式：")
    print("    curl http://localhost:8000/compare/true/999")
    print("    curl http://localhost:8000/compare/false/999")
    print()
    print("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
