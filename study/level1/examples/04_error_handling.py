"""
阶段 1.4: FastAPI 错误处理

学习目标:
1. 理解 HTTPException 的使用场景
2. 掌握如何自定义异常类
3. 学会使用全局异常处理器 (@app.exception_handler)
4. 了解不同场景下如何选择合适的状态码
5. 实现统一的错误响应格式

运行方式:
    uvicorn study.level1.examples.04_error_handling:app --reload
    访问: http://localhost:8000/docs
"""

from typing import Union, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, status, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError

# 创建 FastAPI 应用实例
app = FastAPI(
    title="FastAPI 错误处理示例",
    description="演示各种错误处理方式和最佳实践",
    version="1.0.0"
)


# ============================================================================
# 1. 基础错误处理 - HTTPException
# ============================================================================

"""
HTTPException 是 FastAPI 中最常用的异常类型

使用场景:
    - 资源不存在 (404)
    - 权限不足 (403)
    - 参数验证失败 (400)
    - 业务逻辑错误等
"""


@app.get("/items/{item_id}")
async def read_item(item_id: int):
    """
    基础异常示例 - 资源不存在

    ❌ 不好的做法:
        return {"error": "Item not found"}  # 状态码仍是 200

    ✅ 好的做法:
        raise HTTPException(404, detail="Item not found")
    """
    # 模拟数据库查询
    if item_id > 100:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"商品 ID {item_id} 不存在"
        )

    return {"item_id": item_id, "name": f"Item {item_id}"}


@app.get("/users/{user_id}")
async def read_user(user_id: int):
    """
    带头信息的异常示例

    可以在异常中添加自定义 HTTP 头
    """
    if user_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户 ID 必须大于 0",
            headers={
                "X-Error": "Invalid User ID",
                "X-Error-Code": "INVALID_ID"
            }
        )

    return {"user_id": user_id, "name": f"User {user_id}"}


# ============================================================================
# 2. 带详细信息的异常
# ============================================================================

@app.post("/items/")
async def create_item(item: dict):
    """
    业务逻辑错误示例

    验证失败时返回详细错误信息
    """
    # 检查必填字段
    if "name" not in item:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "Missing required field",
                "field": "name",
                "message": "商品名称不能为空"
            }
        )

    # 检查业务规则
    if len(item.get("name", "")) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Validation failed",
                "field": "name",
                "message": "商品名称至少需要3个字符",
                "received": item.get("name", "")
            }
        )

    return {"message": "商品创建成功", "item": item}


# ============================================================================
# 3. 自定义异常类
# ============================================================================

class APIError(Exception):
    """
    自定义基础异常类

    使用场景:
        - 需要更结构化的错误信息
        - 需要包含错误代码
        - 需要多语言支持
    """

    def __init__(
        self,
        message: str,
        code: str = "API_ERROR",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class UserNotFoundError(APIError):
    """用户不存在异常"""

    def __init__(self, user_id: int):
        super().__init__(
            message=f"用户 {user_id} 不存在",
            code="USER_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"user_id": user_id}
        )


class InsufficientPermissionError(APIError):
    """权限不足异常"""

    def __init__(self, required_permission: str):
        super().__init__(
            message="权限不足，无法执行此操作",
            code="INSUFFICIENT_PERMISSION",
            status_code=status.HTTP_403_FORBIDDEN,
            details={"required_permission": required_permission}
        )


class BusinessLogicError(APIError):
    """业务逻辑错误"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="BUSINESS_LOGIC_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


# ============================================================================
# 4. 全局异常处理器
# ============================================================================

# 处理自定义 APIError
@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """
    自定义异常处理器

    将所有 APIError 转换为统一的响应格式
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "code": exc.code,
            "message": exc.message,
            "details": exc.details,
            "path": str(request.url.path),
            "timestamp": None  # 实际应用中应该使用 datetime.now()
        }
    )


# 处理 ValidationError (Pydantic 验证错误)
@app.exception_handler(ValidationError)
async def validation_error_handler(
    request: Request,
    exc: ValidationError
) -> JSONResponse:
    """
    Pydantic 验证错误处理器

    FastAPI 默认返回 422 错误，这里自定义格式
    """
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": True,
            "code": "VALIDATION_ERROR",
            "message": "请求参数验证失败",
            "details": {"validation_errors": errors},
            "path": str(request.url.path)
        }
    )


# 处理 HTTPException (统一格式)
@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request,
    exc: HTTPException
) -> JSONResponse:
    """
    HTTPException 处理器

    将所有 HTTPException 转换为统一格式
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "code": f"HTTP_{exc.status_code}",
            "message": exc.detail,
            "details": exc.headers if exc.headers else {},
            "path": str(request.url.path)
        }
    )


# 处理所有未捕获的异常
@app.exception_handler(Exception)
async def general_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    全局异常处理器 - 捕获所有未处理的异常

    ⚠️ 重要: 生产环境中不要直接返回异常信息
       - 可能泄露敏感信息
       - 可能暴露系统架构
       - 应该记录日志并返回通用错误信息
    """
    import traceback

    # 在生产环境中，应该记录到日志系统
    # logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "code": "INTERNAL_SERVER_ERROR",
            "message": "服务器内部错误，请稍后重试",
            "details": {} if True else str(exc),  # 生产环境应该为空
            "path": str(request.url.path)
        }
    )


# ============================================================================
# 5. 使用自定义异常的端点
# ============================================================================

# 模拟数据库
fake_users_db = {
    1: {"id": 1, "name": "Alice", "role": "user"},
    2: {"id": 2, "name": "Bob", "role": "user"},
    3: {"id": 3, "name": "Admin", "role": "admin"}
}


@app.get("/api/users/{user_id}")
async def get_user(user_id: int):
    """
    使用自定义异常示例 - UserNotFoundError
    """
    if user_id not in fake_users_db:
        raise UserNotFoundError(user_id)

    return fake_users_db[user_id]


@app.delete("/api/users/{user_id}")
async def delete_user(user_id: int, requester_role: str = "user"):
    """
    使用自定义异常示例 - InsufficientPermissionError

    只有 admin 角色可以删除用户
    """
    if requester_role != "admin":
        raise InsufficientPermissionError("admin")

    if user_id not in fake_users_db:
        raise UserNotFoundError(user_id)

    # 模拟删除
    del fake_users_db[user_id]

    return {"message": f"用户 {user_id} 已删除"}


@app.post("/api/transfer")
async def transfer_money(
    from_account: int,
    to_account: int,
    amount: float
):
    """
    业务逻辑错误示例 - BusinessLogicError

    演示复杂的业务规则验证
    """
    # ❌ 不好的做法: 使用 HTTPException
    # if from_account == to_account:
    #     raise HTTPException(400, "不能转账给自己")

    # ✅ 好的做法: 使用自定义业务异常
    if from_account == to_account:
        raise BusinessLogicError(
            message="不能转账给自己",
            details={
                "from_account": from_account,
                "to_account": to_account
            }
        )

    if amount <= 0:
        raise BusinessLogicError(
            message="转账金额必须大于 0",
            details={"amount": amount}
        )

    if amount > 10000:
        raise BusinessLogicError(
            message="单笔转账不能超过 10000",
            details={
                "amount": amount,
                "max_amount": 10000
            }
        )

    return {
        "message": "转账成功",
        "from": from_account,
        "to": to_account,
        "amount": amount
    }


# ============================================================================
# 6. 请求体验证端点
# ============================================================================

class ItemCreate(BaseModel):
    """商品创建模型"""
    name: str = Field(..., min_length=3, max_length=50)
    price: float = Field(..., gt=0)
    quantity: int = Field(..., ge=0)

    class Config:
        # 设置示例值
        json_schema_extra = {
            "example": {
                "name": "Laptop",
                "price": 999.99,
                "quantity": 10
            }
        }


@app.post("/api/items")
async def create_item_validated(item: ItemCreate):
    """
    请求体验证示例

    FastAPI 会自动验证 Pydantic 模型
    如果验证失败，会触发 ValidationError 异常

    正常情况: {"name": "Laptop", "price": 999.99, "quantity": 10}
    错误情况1: {"name": "AB", "price": 999.99, "quantity": 10}  # name 太短
    错误情况2: {"name": "Laptop", "price": -10, "quantity": 10}  # price 为负
    错误情况3: {"name": "Laptop", "price": 999.99}  # 缺少 quantity
    """
    return {
        "message": "商品创建成功",
        "item": item
    }


# ============================================================================
# 7. 不同状态码的使用场景
# ============================================================================

@app.get("/error/400")
async def error_400():
    """
    400 Bad Request

    使用场景:
        - 请求参数错误
        - 请求格式不正确
        - 缺少必填参数
    """
    raise HTTPException(
        status_code=400,
        detail="请求参数错误"
    )


@app.get("/error/401")
async def error_401():
    """
    401 Unauthorized

    使用场景:
        - 未登录
        - Token 过期
        - 认证失败

    注意: 应该返回 WWW-Authenticate 头
    """
    raise HTTPException(
        status_code=401,
        detail="未授权，请先登录",
        headers={"WWW-Authenticate": "Bearer"}
    )


@app.get("/error/403")
async def error_403():
    """
    403 Forbidden

    使用场景:
        - 已登录但权限不足
        - 访问被禁止的资源
        - 超出配额限制

    与 401 的区别:
        401: 未认证（不知道你是谁）
        403: 已认证但无权限（知道你是谁但不允许访问）
    """
    raise HTTPException(
        status_code=403,
        detail="权限不足，无法访问此资源"
    )


@app.get("/error/404")
async def error_404(item_id: int):
    """
    404 Not Found

    使用场景:
        - 资源不存在
        - URL 路径错误
        - API 版本已废弃
    """
    raise HTTPException(
        status_code=404,
        detail=f"资源 {item_id} 不存在"
    )


@app.get("/error/409")
async def error_409():
    """
    409 Conflict

    使用场景:
        - 资源冲突（如用户名已存在）
        - 版本冲突（如更新冲突）
        - 状态冲突（如删除已删除的资源）
    """
    raise HTTPException(
        status_code=409,
        detail="资源冲突，用户名已被使用"
    )


@app.get("/error/422")
async def error_422():
    """
    422 Unprocessable Entity

    使用场景:
        - 请求格式正确但语义错误
        - 业务规则验证失败
        - 数据无法处理

    与 400 的区别:
        400: 请求格式错误（语法层面）
        422: 请求格式正确但无法处理（语义层面）
    """
    raise HTTPException(
        status_code=422,
        detail="无法处理的实体，业务规则验证失败"
    )


@app.get("/error/429")
async def error_429():
    """
    429 Too Many Requests

    使用场景:
        - 请求频率超限
        - 触发限流策略

    注意: 应该返回 Retry-After 头
    """
    raise HTTPException(
        status_code=429,
        detail="请求过于频繁，请稍后重试",
        headers={"Retry-After": "60"}  # 60秒后重试
    )


@app.get("/error/500")
async def error_500():
    """
    500 Internal Server Error

    使用场景:
        - 服务器内部错误
        - 未捕获的异常
        - 第三方服务不可用

    ⚠️ 注意: 不应该主动抛出 500 错误
        应该让全局异常处理器处理
    """
    # ❌ 不好的做法: 主动抛出 500
    # raise HTTPException(500, "服务器错误")

    # ✅ 好的做法: 抛出具体异常或自定义异常
    raise Exception("模拟服务器内部错误")


@app.get("/error/503")
async def error_503():
    """
    503 Service Unavailable

    使用场景:
        - 服务维护中
        - 服务过载
        - 依赖服务不可用

    注意: 应该返回 Retry-After 头
    """
    raise HTTPException(
        status_code=503,
        detail="服务暂时不可用，正在维护中",
        headers={"Retry-After": "3600"}  # 1小时后重试
    )


# ============================================================================
# 8. 根路径和文档
# ============================================================================

@app.get("/", summary="API 文档入口")
async def root():
    """根路径，返回 API 信息"""
    return {
        "name": "FastAPI 错误处理示例",
        "version": "1.0.0",
        "description": "演示各种错误处理方式和最佳实践",
        "endpoints": {
            "basic": "/items/{item_id}",
            "custom_exception": "/api/users/{user_id}",
            "business_logic": "/api/transfer",
            "validation": "/api/items",
            "status_codes": {
                "400": "/error/400",
                "401": "/error/401",
                "403": "/error/403",
                "404": "/error/404?item_id=999",
                "409": "/error/409",
                "422": "/error/422",
                "429": "/error/429",
                "500": "/error/500",
                "503": "/error/503"
            }
        },
        "docs": "/docs"
    }


# ============================================================================
# 9. 运行说明
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║           FastAPI 错误处理示例                             ║
    ╠════════════════════════════════════════════════════════════╣
    ║  启动服务...                                                ║
    ║  API 文档: http://localhost:8000/docs                      ║
    ╚════════════════════════════════════════════════════════════╝

    测试示例:

    1. 基础 404 错误:
       curl http://localhost:8000/items/999

    2. 自定义异常 - 用户不存在:
       curl http://localhost:8000/api/users/999

    3. 自定义异常 - 权限不足:
       curl -X DELETE "http://localhost:8000/api/users/1?requester_role=user"

    4. 业务逻辑错误:
       curl -X POST "http://localhost:8000/api/transfer?from_account=1&to_account=1&amount=100"

    5. 参数验证错误:
       curl -X POST http://localhost:8000/api/items \\
         -H "Content-Type: application/json" \\
         -d '{"name":"AB","price":-10,"quantity":5}'

    6. 不同状态码:
       curl http://localhost:8000/error/400
       curl http://localhost:8000/error/401
       curl http://localhost:8000/error/403
       curl http://localhost:8000/error/404?item_id=999
       curl http://localhost:8000/error/429
    """)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True
    )


# ============================================================================
# 10. 最佳实践总结
# ============================================================================

"""
【错误处理最佳实践】

1. ✅ 使用 HTTPException 处理标准错误
   - 资源不存在: 404
   - 权限不足: 403
   - 参数错误: 400

2. ✅ 创建自定义异常类
   - 继承自 Exception
   - 包含错误代码、消息、详情
   - 便于分类处理和国际化

3. ✅ 使用全局异常处理器
   - 统一错误响应格式
   - 避免重复代码
   - 记录错误日志
   - 不泄露敏感信息

4. ✅ 选择正确的 HTTP 状态码

   客户端错误 (4xx):
   - 400 Bad Request: 请求参数错误
   - 401 Unauthorized: 未认证
   - 403 Forbidden: 无权限
   - 404 Not Found: 资源不存在
   - 409 Conflict: 资源冲突
   - 422 Unprocessable Entity: 业务验证失败
   - 429 Too Many Requests: 请求超限

   服务器错误 (5xx):
   - 500 Internal Server Error: 内部错误
   - 503 Service Unavailable: 服务不可用

5. ✅ 错误信息要清晰有用
   - 说明问题原因
   - 提供解决方案
   - 包含相关字段信息
   - 不要暴露内部实现

6. ❌ 避免的陷阱:
   - 不要返回 200 状态码但包含错误信息
   - 不要在错误信息中暴露敏感数据
   - 不要直接返回异常堆栈（生产环境）
   - 不要使用不一致的错误格式
   - 不要忘记处理边界情况

7. ✅ 生产环境建议:
   - 使用日志系统记录所有错误
   - 监控错误率和错误类型
   - 设置告警规则
   - 定期审查错误日志
   - 为常见错误提供帮助文档
"""
