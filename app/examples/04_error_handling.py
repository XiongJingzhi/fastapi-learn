"""
FastAPI 错误处理示例

本示例演示如何实现分层的错误处理策略，包括：
1. 定义领域异常（DomainException）
2. 在 Service 层使用领域异常
3. 创建全局异常处理器
4. 统一的错误响应格式
5. HTTP 状态码的正确使用

运行命令：
    uvicorn app.examples.04_error_handling:app --reload

访问文档：
    http://localhost:8000/docs
"""

from fastapi import FastAPI, APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, EmailStr
from typing import Generic, TypeVar, Optional, List, Dict, Any
import logging
import time

# 创建应用实例
app = FastAPI(
    title="错误处理示例",
    description="演示如何实现分层的错误处理策略",
    version="1.0.0"
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# WARNING: 以下 users_db / orders_db 使用进程内共享可变状态，仅用于教学演示。
# WARNING: 这会导致并发请求下的数据竞争、跨请求污染、重启丢失，生产环境必须使用真实数据库。
users_db = [
    {"id": 1, "name": "张三", "email": "zhangsan@example.com", "password": "hash1", "balance": 100.0},
    {"id": 2, "name": "李四", "email": "lisi@example.com", "password": "hash2", "balance": 50.0},
]
orders_db: List[Dict[str, Any]] = []


# ==========================================
# 第一部分：领域异常定义
# ==========================================

class DomainException(Exception):
    """
    领域异常基类

    架构原则：
    - 领域异常不依赖 HTTP
    - 包含业务错误码、消息和 HTTP 状态码
    - 可以携带额外的详细信息
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
        self.http_status = http_status
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于日志）"""
        return {
            "code": self.code,
            "message": self.message,
            "http_status": self.http_status,
            "details": self.details
        }


class NotFoundException(DomainException):
    """
    资源不存在异常

    使用场景：查询的资源不存在
    HTTP 状态码：404
    """

    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            message=f"{resource} {identifier} 不存在",
            code=f"{resource.upper()}_NOT_FOUND",
            http_status=404,
            details={"resource": resource, "identifier": str(identifier)}
        )
        self.resource = resource
        self.identifier = identifier


class ConflictException(DomainException):
    """
    资源冲突异常

    使用场景：唯一约束冲突（如邮箱、用户名已存在）
    HTTP 状态码：409
    """

    def __init__(self, resource: str, field: str, value: Any):
        super().__init__(
            message=f"{resource} 的 {field} '{value}' 已存在",
            code=f"{resource.upper()}_CONFLICT",
            http_status=409,
            details={"resource": resource, "field": field, "value": str(value)}
        )
        self.resource = resource
        self.field = field
        self.value = value


class BusinessException(DomainException):
    """
    业务规则异常

    使用场景：违反业务规则（如余额不足、订单状态不允许操作）
    HTTP 状态码：400
    """

    def __init__(self, message: str, code: str = "BUSINESS_ERROR", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            code=code,
            http_status=400,
            details=details or {}
        )


class AuthenticationException(DomainException):
    """
    认证异常

    使用场景：未登录或 Token 无效
    HTTP 状态码：401
    """

    def __init__(self, message: str = "未认证"):
        super().__init__(
            message=message,
            code="AUTHENTICATION_FAILED",
            http_status=401
        )


class AuthorizationException(DomainException):
    """
    授权异常

    使用场景：已登录但权限不足
    HTTP 状态码：403
    """

    def __init__(self, message: str = "权限不足"):
        super().__init__(
            message=message,
            code="AUTHORIZATION_FAILED",
            http_status=403
        )


# ==========================================
# 第二部分：全局异常处理器
# ==========================================

async def domain_exception_handler(
    request: Any,
    exc: DomainException
) -> JSONResponse:
    """
    领域异常处理器

    架构原则：
    - 在传输层捕获领域异常
    - 转换为统一格式的 HTTP 响应
    - 使用异常中定义的 HTTP 状态码
    """
    logger.info(
        f"Domain exception: {exc.code} - {exc.message}",
        extra={"exception_details": exc.to_dict()}
    )

    return JSONResponse(
        status_code=exc.http_status,
        content={
            "code": exc.http_status,
            "message": exc.message,
            "data": {
                "error_code": exc.code,
                **exc.details
            } if exc.details else None,
            "timestamp": int(time.time())
        }
    )


async def http_exception_handler(
    request: Any,
    exc: HTTPException
) -> JSONResponse:
    """
    HTTP 异常处理器（统一格式）

    FastAPI 内置的 HTTPException 也使用统一格式
    """
    logger.info(f"HTTP exception: {exc.status_code} - {exc.detail}")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "message": str(exc.detail),
            "data": None,
            "timestamp": int(time.time())
        }
    )


async def general_exception_handler(
    request: Any,
    exc: Exception
) -> JSONResponse:
    """
    通用异常处理器（捕获所有未处理的异常）

    安全原则：
    - 不暴露内部错误详情给客户端
    - 记录完整的错误日志用于调试
    - 返回友好的错误消息
    """
    # 记录完整的错误信息和堆栈
    logger.error(
        f"Unhandled exception: {type(exc).__name__} - {str(exc)}",
        exc_info=True,
        extra={"path": getattr(request, 'url', 'unknown')}
    )

    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "服务器内部错误",
            "data": None,
            "timestamp": int(time.time())
        }
    )


# 注册全局异常处理器
app.add_exception_handler(DomainException, domain_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)


# ==========================================
# 第三部分：数据模型
# ==========================================

class UserCreate(BaseModel):
    """创建用户请求模型"""
    name: str = Field(..., min_length=1, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    password: str = Field(..., min_length=6, max_length=50, description="密码")


class UserResponse(BaseModel):
    """用户响应模型"""
    id: int
    name: str
    email: str
    balance: float = Field(0.0, description="账户余额")


class OrderCreate(BaseModel):
    """创建订单请求模型"""
    user_id: int
    product_id: int
    amount: float = Field(..., gt=0, description="订单金额")


# ==========================================
# 第四部分：Service 层（模拟）
# ==========================================

class MockDatabase:
    """模拟数据库"""

    def __init__(self):
        self.users = users_db
        self.orders = orders_db

    def find_user_by_id(self, user_id: int) -> Optional[dict]:
        """根据 ID 查找用户"""
        for user in self.users:
            if user["id"] == user_id:
                return user
        return None

    def find_user_by_email(self, email: str) -> Optional[dict]:
        """根据邮箱查找用户"""
        for user in self.users:
            if user["email"] == email:
                return user
        return None

    def email_exists(self, email: str) -> bool:
        """检查邮箱是否存在"""
        return self.find_user_by_email(email) is not None

    def create_user(self, user_data: dict) -> dict:
        """创建用户"""
        new_user = {
            "id": max((user["id"] for user in self.users), default=0) + 1,
            "name": user_data["name"],
            "email": user_data["email"],
            "password": f"hash_{user_data['password']}",  # 模拟密码哈希
            "balance": 0.0
        }
        self.users.append(new_user)
        return new_user

    def update_balance(self, user_id: int, amount: float) -> dict:
        """更新用户余额"""
        user = self.find_user_by_id(user_id)
        if user:
            user["balance"] += amount
        return user

    def create_order(self, order_data: dict) -> dict:
        """创建订单"""
        order = {
            "id": max((existing_order["id"] for existing_order in self.orders), default=0) + 1,
            **order_data,
            "status": "pending",
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.orders.append(order)
        return order


class UserService:
    """
    用户服务

    架构原则：
    - 抛出领域异常，不抛出 HTTPException
    - 实现业务逻辑和规则
    - 返回领域对象，不返回响应格式
    """

    def __init__(self):
        self.db = MockDatabase()

    async def get_user(self, user_id: int) -> dict:
        """获取用户"""
        user = self.db.find_user_by_id(user_id)

        if not user:
            # 抛出领域异常（不是 HTTPException）
            raise NotFoundException("User", user_id)

        return user

    async def create_user(self, user_data: UserCreate) -> dict:
        """创建用户"""
        # 业务规则：检查邮箱是否已存在
        if self.db.email_exists(user_data.email):
            raise ConflictException("User", "email", user_data.email)

        # 创建用户
        user = self.db.create_user(user_data.dict())
        return user

    async def decrease_balance(self, user_id: int, amount: float) -> dict:
        """扣减余额"""
        user = await self.get_user(user_id)

        # 业务规则：检查余额是否足够
        if user["balance"] < amount:
            raise BusinessException(
                message=f"余额不足：当前 {user['balance']:.2f}，需要 {amount:.2f}",
                code="INSUFFICIENT_BALANCE",
                details={
                    "current_balance": user["balance"],
                    "required_amount": amount
                }
            )

        # 扣减余额
        user = self.db.update_balance(user_id, -amount)
        return user


class OrderService:
    """订单服务"""

    def __init__(self):
        self.db = MockDatabase()

    async def create_order(self, user_id: int, product_id: int, amount: float) -> dict:
        """创建订单"""
        # 模拟业务规则：订单金额不能超过 10000
        if amount > 10000:
            raise BusinessException(
                message=f"订单金额不能超过 10000",
                code="ORDER_AMOUNT_EXCEEDED",
                details={"max_amount": 10000, "actual_amount": amount}
            )

        order = self.db.create_order({
            "user_id": user_id,
            "product_id": product_id,
            "amount": amount
        })
        return order


# 依赖注入
def get_user_service() -> UserService:
    return UserService()


def get_order_service() -> OrderService:
    return OrderService()


# ==========================================
# 第五部分：API 端点
# ==========================================

router = APIRouter(prefix="/api", tags=["用户和订单"])


@router.get(
    "/users/{user_id}",
    response_model=dict,
    summary="获取用户",
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
    获取用户信息

    错误处理演示：
    - 用户不存在 → 404 Not Found
    """
    user = await service.get_user(user_id)

    # 成功响应
    return {
        "code": 200,
        "message": "查询成功",
        "data": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "balance": user["balance"]
        },
        "timestamp": int(time.time())
    }


@router.post(
    "/users",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="创建用户",
    responses={
        201: {"description": "创建成功"},
        409: {"description": "邮箱已存在"},
        422: {"description": "参数验证失败"}
    }
)
async def create_user(
    user_data: UserCreate,
    service: UserService = Depends(get_user_service)
):
    """
    创建用户

    错误处理演示：
    - 邮箱已存在 → 409 Conflict
    - 参数验证失败 → 422 Unprocessable Entity（FastAPI 自动处理）
    """
    user = await service.create_user(user_data)

    return {
        "code": 201,
        "message": "创建成功",
        "data": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"]
        },
        "timestamp": int(time.time())
    }


@router.post(
    "/users/{user_id}/decrease-balance",
    response_model=dict,
    summary="扣减余额",
    responses={
        200: {"description": "操作成功"},
        404: {"description": "用户不存在"},
        400: {"description": "余额不足"}
    }
)
async def decrease_balance(
    user_id: int,
    amount: float = Field(..., gt=0, description="扣减金额"),
    service: UserService = Depends(get_user_service)
):
    """
    扣减用户余额

    错误处理演示：
    - 用户不存在 → 404 Not Found
    - 余额不足 → 400 Bad Request（业务规则违反）
    """
    user = await service.decrease_balance(user_id, amount)

    return {
        "code": 200,
        "message": "扣减成功",
        "data": {
            "id": user["id"],
            "balance": user["balance"]
        },
        "timestamp": int(time.time())
    }


@router.post(
    "/orders",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="创建订单",
    responses={
        201: {"description": "创建成功"},
        400: {"description": "业务规则违反"}
    }
)
async def create_order(
    order_data: OrderCreate,
    user_service: UserService = Depends(get_user_service),
    order_service: OrderService = Depends(get_order_service)
):
    """
    创建订单

    错误处理演示：
    - 订单金额超过限制 → 400 Bad Request（业务规则违反）
    """
    # 先验证用户存在
    await user_service.get_user(order_data.user_id)

    # 创建订单
    order = await order_service.create_order(
        order_data.user_id,
        order_data.product_id,
        order_data.amount
    )

    return {
        "code": 201,
        "message": "订单创建成功",
        "data": order,
        "timestamp": int(time.time())
    }


# ==========================================
# 第六部分：对比示例 - 错误 vs 正确
# ==========================================

comparison_router = APIRouter(prefix="/api/comparison", tags=["错误处理对比"])


# ❌ 错误示例：在 Service 层抛出 HTTPException
class BadUserService:
    """错误的 Service 实现"""

    async def get_user_bad(self, user_id: int):
        """错误：Service 抛出 HTTPException"""
        db = MockDatabase()
        user = db.find_user_by_id(user_id)

        if not user:
            # ❌ Service 不应该知道 HTTP！
            raise HTTPException(
                status_code=404,
                detail="用户不存在"
            )

        return user


@comparison_router.get("/bad/users/{user_id}")
async def bad_get_user(user_id: int):
    """错误示例：Service 抛出 HTTP 异常"""
    service = BadUserService()
    return await service.get_user_bad(user_id)


# ✅ 正确示例：Service 抛出领域异常
@comparison_router.get("/good/users/{user_id}")
async def good_get_user(user_id: int, service: UserService = Depends(get_user_service)):
    """
    正确示例：Service 抛出领域异常

    优点：
    1. Service 不依赖 HTTP
    2. 可以在其他场景复用（如 CLI）
    3. 便于单元测试
    """
    user = await service.get_user(user_id)
    return {
        "code": 200,
        "message": "查询成功",
        "data": user,
        "timestamp": int(time.time())
    }


# ❌ 错误示例：忽略异常
@comparison_router.get("/bad/silent/{user_id}")
async def bad_silent_error(user_id: int):
    """错误示例：忽略异常"""
    try:
        service = UserService()
        user = await service.get_user(user_id)
        return {"user": user}
    except Exception:
        # ❌ 吞噬异常，返回空数据
        return {"user": None}


# ✅ 正确示例：让异常传播
@comparison_router.get("/good/propagate/{user_id}")
async def good_propagate_error(user_id: int, service: UserService = Depends(get_user_service)):
    """
    正确示例：让异常传播到全局处理器

    优点：
    1. 统一的错误处理
    2. 不会遗漏错误
    """
    user = await service.get_user(user_id)
    return {
        "code": 200,
        "message": "查询成功",
        "data": user,
        "timestamp": int(time.time())
    }


app.include_router(router)
app.include_router(comparison_router)


# ==========================================
# 启动和测试说明
# ==========================================

@app.get("/", summary="API 信息")
async def root():
    """根路径，返回 API 信息"""
    return {
        "message": "错误处理示例 API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "用户和订单": {
                "GET /api/users/{id}": "获取用户（可能返回 404）",
                "POST /api/users": "创建用户（可能返回 409）",
                "POST /api/users/{id}/decrease-balance": "扣减余额（可能返回 400）",
                "POST /api/orders": "创建订单"
            },
            "错误处理对比": {
                "GET /api/comparison/bad/users/{id}": "错误示例",
                "GET /api/comparison/good/users/{id}": "正确示例",
                "GET /api/comparison/bad/silent/{id}": "忽略异常（错误）",
                "GET /api/comparison/good/propagate/{id}": "传播异常（正确）"
            }
        },
        "test_cases": {
            "404_错误": "GET /api/users/999",
            "409_错误": 'POST /api/users {"name": "张三", "email": "zhangsan@example.com", "password": "123456"}',
            "400_错误（余额不足）": "POST /api/users/1/decrease-balance?amount=200",
            "400_错误（订单金额超限）": 'POST /api/orders {"user_id": 1, "product_id": 1, "amount": 20000}'
        }
    }


if __name__ == "__main__":
    import uvicorn

    print("""
    ╔═══════════════════════════════════════════════════════╗
    ║            FastAPI 错误处理示例                        ║
    ╠═══════════════════════════════════════════════════════╣
    ║  API 文档: http://localhost:8000/docs                  ║
    ║                                                         ║
    ║  测试端点（演示错误处理）：                              ║
    ║  1. 404 Not Found:                                     ║
    ║     GET /api/users/999                                 ║
    ║                                                         ║
    ║  2. 409 Conflict (邮箱已存在):                          ║
    ║     POST /api/users                                    ║
    ║     {"name": "张三", "email": "zhangsan@example.com",  ║
    ║      "password": "123456"}                             ║
    ║                                                         ║
    ║  3. 400 Bad Request (余额不足):                         ║
    ║     POST /api/users/1/decrease-balance?amount=200      ║
    ║                                                         ║
    ║  4. 对比示例:                                          ║
    ║     GET /api/comparison/good/users/1  (正确)           ║
    ║     GET /api/comparison/bad/users/1   (错误)           ║
    ╚═══════════════════════════════════════════════════════╝
    """)

    uvicorn.run(
        "app.examples.04_error_handling:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
