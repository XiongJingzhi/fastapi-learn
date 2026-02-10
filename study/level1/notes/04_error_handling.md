# 04 错误处理 - 异常的分层处理策略

## 📖 为什么需要错误处理策略？

想象你在一家酒店：

```
❌ 没有错误处理：
客人：我要房间
前台：不知道，你自己去找（客人困惑）

❌ 错误的错误处理：
客人：我要房间
前台：系统出错了！（但客人不知道是什么问题）

✅ 正确的错误处理：
客人：我要房间
前台：抱歉，今天房间已满（404）
     或者：您的预订信息有误（400）
     或者：系统正在维护，请稍后再试（503）
```

**API 的错误处理也是一样**：
- 需要告诉客户端**具体**发生了什么问题
- 使用**标准**的 HTTP 状态码
- 提供**有用**的错误信息
- 保持**一致的**错误格式

---

## 🎯 核心概念

### 错误的两个维度

#### 维度 1：错误发生的层次

```
┌─────────────────────────────────────────────────────────┐
│                   传输层 (FastAPI)                        │
│                                                          │
│  错误类型：                                              │
│  • 400 Bad Request - 参数错误                            │
│  • 401 Unauthorized - 未认证                            │
│  • 403 Forbidden - 无权限                                │
│  • 404 Not Found - 资源不存在                            │
│  • 422 Unprocessable Entity - 验证失败                   │
└─────────────────────────────────────────────────────────┘
                          │
                          │ 触发
                          ▼
┌─────────────────────────────────────────────────────────┐
│                   服务层 (Service)                       │
│                                                          │
│  错误类型：                                              │
│  • 业务规则违反（如：余额不足）                           │
│  • 资源冲突（如：邮箱已存在）                             │
│  • 权限不足（业务层面）                                   │
└─────────────────────────────────────────────────────────┘
                          │
                          │ 触发
                          ▼
┌─────────────────────────────────────────────────────────┐
│                   领域层 (Domain)                        │
│                                                          │
│  错误类型：                                              │
│  • 值域错误（如：年龄不能为负）                           │
│  • 状态转换错误（如：已取消订单不能再次取消）             │
└─────────────────────────────────────────────────────────┘
                          │
                          │ 触发
                          ▼
┌─────────────────────────────────────────────────────────┐
│                 基础设施层 (Infrastructure)              │
│                                                          │
│  错误类型：                                              │
│  • 数据库连接失败                                        │
│  • 网络超时                                              │
│  • 外部 API 不可用                                       │
└─────────────────────────────────────────────────────────┘
```

#### 维度 2：错误如何传播

```
┌─────────────────────────────────────────────────────────┐
│                   错误传播流程                           │
└─────────────────────────────────────────────────────────┘

Domain 层抛出领域异常
    │
    ▼
Service 层捕获或转换
    │
    ▼
FastAPI 全局异常处理器
    │
    ▼
HTTP 响应（统一格式）
```

---

## 📊 HTTP 状态码的选择

### 常用状态码速查表

#### 2xx - 成功

| 状态码 | 含义 | 使用场景 |
|--------|------|----------|
| 200 | OK | 请求成功 |
| 201 | Created | 资源创建成功 |
| 204 | No Content | 删除成功（无返回内容） |

#### 4xx - 客户端错误

| 状态码 | 含义 | 使用场景 | 例子 |
|--------|------|----------|------|
| 400 | Bad Request | 请求参数错误 | 缺少必填字段 |
| 401 | Unauthorized | 未认证 | 缺少 Token |
| 403 | Forbidden | 无权限 | Token 有效但权限不足 |
| 404 | Not Found | 资源不存在 | 用户 ID 不存在 |
| 409 | Conflict | 资源冲突 | 邮箱已存在 |
| 422 | Unprocessable Entity | 验证失败 | Pydantic 校验失败 |
| 429 | Too Many Requests | 请求过于频繁 | 触发限流 |

#### 5xx - 服务器错误

| 状态码 | 含义 | 使用场景 | 例子 |
|--------|------|----------|------|
| 500 | Internal Server Error | 服务器内部错误 | 未捕获的异常 |
| 502 | Bad Gateway | 上游服务错误 | 数据库连接失败 |
| 503 | Service Unavailable | 服务不可用 | 系统维护中 |

### 选择状态码的原则

```
1. 4xx vs 5xx：
   - 客户端错误 → 4xx（参数错误、权限不足）
   - 服务器错误 → 5xx（数据库崩溃、网络故障）

2. 404 vs 400：
   - 资源不存在 → 404
   - 请求格式错误 → 400

3. 401 vs 403：
   - 未登录（没有 Token）→ 401
   - 已登录但无权限 → 403

4. 409 vs 400：
   - 资源冲突（如唯一约束）→ 409
   - 一般参数错误 → 400
```

---

## 🔧 FastAPI 错误处理实现

### 方式一：使用 HTTPException（基础）

FastAPI 内置的异常类：

```python
from fastapi import HTTPException, status

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    user = await get_user_from_db(user_id)

    if user is None:
        # 抛出 HTTP 异常
        raise HTTPException(
            status_code=404,
            detail="用户不存在",
            headers={"X-Error": "User not found"}  # 可选的自定义头
        )

    return user
```

**HTTPException 的字段**：
- `status_code`: HTTP 状态码
- `detail`: 错误详情（会放在响应的 detail 字段）
- `headers`: 可选的响应头

**问题**：
- ❌ 直接在 endpoint 中抛出 HTTP 异常（违反分层原则）
- ❌ Service 层需要知道 HTTP（不便于测试和复用）

### 方式二：自定义领域异常（推荐）

#### 步骤 1：定义领域异常

```python
# app/exceptions.py
class DomainException(Exception):
    """
    领域异常基类

    架构原则：
    - 领域异常不依赖 HTTP
    - 包含业务错误码和消息
    """
    def __init__(self, message: str, code: str = "DOMAIN_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class UserNotFoundException(DomainException):
    """用户不存在异常"""
    def __init__(self, user_id: int):
        super().__init__(
            message=f"用户 {user_id} 不存在",
            code="USER_NOT_FOUND"
        )
        self.user_id = user_id


class UserEmailExistsException(DomainException):
    """邮箱已存在异常"""
    def __init__(self, email: str):
        super().__init__(
            message=f"邮箱 {email} 已被使用",
            code="EMAIL_EXISTS"
        )
        self.email = email


class InsufficientBalanceException(DomainException):
    """余额不足异常"""
    def __init__(self, current: float, required: float):
        super().__init__(
            message=f"余额不足：当前 {current}，需要 {required}",
            code="INSUFFICIENT_BALANCE"
        )
        self.current = current
        self.required = required
```

#### 步骤 2：在 Service 层使用领域异常

```python
# app/services/user_service.py
class UserService:
    async def get_user(self, user_id: int) -> User:
        user = await self.repo.find_by_id(user_id)

        if user is None:
            # 抛出领域异常（不依赖 HTTP）
            raise UserNotFoundException(user_id)

        return user

    async def create_user(self, user_data: UserCreate) -> User:
        # 检查邮箱是否存在
        if await self.repo.email_exists(user_data.email):
            raise UserEmailExistsException(user_data.email)

        # 创建用户
        user = User.create(user_data)
        return await self.repo.save(user)
```

#### 步骤 3：创建全局异常处理器

```python
# app/exception_handlers.py
from fastapi import Request
from fastapi.responses import JSONResponse
from app.exceptions import DomainException

async def domain_exception_handler(
    request: Request,
    exc: DomainException
) -> JSONResponse:
    """
    领域异常处理器

    架构原则：
    - 在传输层捕获领域异常
    - 转换为 HTTP 响应
    - 使用统一的错误格式
    """
    # 映射到 HTTP 状态码
    status_code_map = {
        "USER_NOT_FOUND": 404,
        "EMAIL_EXISTS": 409,
        "INSUFFICIENT_BALANCE": 400,
        # ... 其他映射
    }

    status_code = status_code_map.get(exc.code, 400)

    return JSONResponse(
        status_code=status_code,
        content={
            "code": status_code,
            "message": exc.message,
            "data": {
                "error_code": exc.code,
                "detail": str(exc)
            },
            "timestamp": int(time.time())
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
            "timestamp": int(time.time())
        }
    )


async def general_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    通用异常处理器（捕获所有未处理的异常）

    安全原则：
    - 不暴露内部错误详情
    - 记录完整日志用于调试
    - 返回友好的错误消息
    """
    # 记录完整错误日志
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "服务器内部错误",
            "data": None,
            "timestamp": int(time.time())
        }
    )
```

#### 步骤 4：注册异常处理器

```python
# app/main.py
from fastapi import FastAPI
from app.exceptions import DomainException
from app.exception_handlers import (
    domain_exception_handler,
    http_exception_handler,
    general_exception_handler
)

app = FastAPI()

# 注册异常处理器
app.add_exception_handler(DomainException, domain_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)
```

#### 步骤 5：使用

```python
@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    service: UserService = Depends()
):
    # Service 抛出领域异常
    # 全局处理器自动转换为 HTTP 响应
    user = await service.get_user(user_id)
    return success_response(data=user)


# 输出示例（当用户不存在时）：
# {
#     "code": 404,
#     "message": "用户 123 不存在",
#     "data": {
#         "error_code": "USER_NOT_FOUND",
#         "detail": "用户 123 不存在"
#     },
#     "timestamp": 1739184000
# }
```

---

## 🎨 架构设计考量

### 1. 异常分层原则

```
❌ 错误：在 Service 层抛出 HTTPException
class UserService:
    def get_user(self, user_id: int):
        user = self.repo.find(user_id)
        if not user:
            raise HTTPException(status_code=404)  # ❌ 依赖 HTTP
        return user

✅ 正确：在 Service 层抛出领域异常
class UserService:
    def get_user(self, user_id: int):
        user = self.repo.find(user_id)
        if not user:
            raise UserNotFoundException(user_id)  # ✅ 领域异常
        return user
```

**为什么？**
- Service 层不应该知道 HTTP
- 领域异常可以在 CLI、gRPC 等其他场景复用
- 便于单元测试（不需要模拟 HTTP）

### 2. 异常映射策略

```
┌─────────────────────────────────────────────────────────┐
│              异常映射架构                                │
└─────────────────────────────────────────────────────────┘

Domain Exception (领域层)
    │
    │ 抛出
    ▼
Service Layer (服务层)
    │
    │ 捕获或传播
    ▼
FastAPI Exception Handler (传输层)
    │
    │ 映射: Domain Code → HTTP Status
    ▼
HTTP Response (统一格式)
```

**映射规则**：

```python
# 异常码映射表
EXCEPTION_CODE_MAP = {
    # 资源不存在 → 404
    "USER_NOT_FOUND": 404,
    "ORDER_NOT_FOUND": 404,
    "PRODUCT_NOT_FOUND": 404,

    # 资源冲突 → 409
    "EMAIL_EXISTS": 409,
    "USERNAME_EXISTS": 409,

    # 业务规则违反 → 400
    "INSUFFICIENT_BALANCE": 400,
    "INVALID_ORDER_STATUS": 400,

    # 权限不足 → 403
    "PERMISSION_DENIED": 403,
}
```

### 3. 错误信息的详细程度

```python
# 开发环境：返回详细错误
if settings.DEBUG:
    return {
        "code": 500,
        "message": "Internal Server Error",
        "data": {
            "error_type": type(exc).__name__,
            "error_detail": str(exc),
            "traceback": traceback.format_exc()
        }
    }

# 生产环境：返回友好消息
else:
    logger.error(f"Error: {exc}", exc_info=True)  # 记录详细日志
    return {
        "code": 500,
        "message": "服务器内部错误",
        "data": None
    }
```

---

## 💡 实战建议

### 1. 创建异常基类和工具

```python
# app/exceptions.py
from typing import Optional, Dict, Any

class DomainException(Exception):
    """领域异常基类"""

    def __init__(
        self,
        message: str,
        code: str = "DOMAIN_ERROR",
        http_status: int = 400,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.http_status = http_status  # 直接指定 HTTP 状态码
        self.details = details or {}
        super().__init__(self.message)


# 常用异常类
class NotFoundException(DomainException):
    """资源不存在"""
    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            message=f"{resource} {identifier} 不存在",
            code=f"{resource.upper()}_NOT_FOUND",
            http_status=404
        )


class ConflictException(DomainException):
    """资源冲突"""
    def __init__(self, resource: str, field: str, value: Any):
        super().__init__(
            message=f"{resource} 的 {field} '{value}' 已存在",
            code=f"{resource.upper()}_CONFLICT",
            http_status=409,
            details={"field": field, "value": value}
        )


class BusinessException(DomainException):
    """业务规则异常"""
    def __init__(self, message: str, code: str = "BUSINESS_ERROR"):
        super().__init__(
            message=message,
            code=code,
            http_status=400
        )
```

### 2. 简化的异常处理器

```python
# app/exception_handlers.py
from fastapi import Request
from fastapi.responses import JSONResponse
from app.exceptions import DomainException
import time
import logging

logger = logging.getLogger(__name__)


async def domain_exception_handler(
    request: Request,
    exc: DomainException
) -> JSONResponse:
    """领域异常处理器"""
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


async def general_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """通用异常处理器"""
    # 记录错误
    logger.error(
        f"Unhandled exception on {request.url}: {exc}",
        exc_info=True
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
```

### 3. 在 Service 中使用

```python
# app/services/user_service.py
from app.exceptions import NotFoundException, ConflictException

class UserService:
    async def get_user(self, user_id: int) -> User:
        user = await self.repo.find_by_id(user_id)

        if not user:
            # 使用通用异常类
            raise NotFoundException("User", user_id)

        return user

    async def create_user(self, data: UserCreate) -> User:
        if await self.repo.email_exists(data.email):
            raise ConflictException("User", "email", data.email)

        user = User.create(data)
        return await self.repo.save(user)
```

### 4. 测试异常处理

```python
# tests/test_users.py
import pytest
from app.exceptions import NotFoundException
from app.services.user_service import UserService

def test_get_user_not_found():
    """测试用户不存在异常"""
    service = UserService(mock_repo)

    with pytest.raises(NotFoundException) as exc_info:
        await service.get_user(999)

    assert exc_info.value.code == "USER_NOT_FOUND"
    assert "999" in exc_info.value.message
```

---

## ⚠️ 常见错误

### 错误 1：直接返回错误码 200

```python
# ❌ 错误：总是返回 200
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    user = await get_user(user_id)
    if not user:
        return {
            "code": 404,  # HTTP 状态码是 200，但业务码是 404
            "message": "用户不存在"
        }
    return {"code": 200, "data": user}

# ✅ 正确：使用正确的 HTTP 状态码
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    user = await get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user
```

### 错误 2：暴露内部错误

```python
# ❌ 错误：在生产环境暴露详细错误
@app.get("/users")
async def get_users():
    try:
        return await db.query("SELECT * FROM users")
    except Exception as e:
        return {
            "error": str(e),  # 可能暴露数据库结构！
            "traceback": traceback.format_exc()
        }

# ✅ 正确：记录日志但返回友好消息
@app.get("/users")
async def get_users():
    try:
        return await db.query("SELECT * FROM users")
    except Exception as e:
        logger.error(f"Database error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="服务器内部错误"
        )
```

### 错误 3：捕获所有异常

```python
# ❌ 错误：吞噬异常
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    try:
        return await get_user(user_id)
    except Exception:
        pass  # 错误被忽略！

# ✅ 正确：让异常传播或正确处理
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    return await get_user(user_id)  # 异常会被全局处理器捕获
```

---

## 🧪 理解验证

### 自我检查问题

1. **Service 层应该抛出什么类型的异常？**
   - A. HTTPException
   - B. 领域异常（DomainException）
   - C. ValueError
   - D. 不抛出异常，返回 None

2. **用户不存在应该返回什么状态码？**
   - A. 400
   - B. 401
   - C. 403
   - D. 404

3. **邮箱已存在应该返回什么状态码？**
   - A. 400
   - B. 404
   - C. 409
   - D. 500

4. **全局异常处理器在哪里注册？**
   - A. Service 层
   - B. FastAPI app 实例
   - C. Endpoint 函数
   - D. 不需要注册

5. **生产环境如何处理未捕获的异常？**
   - A. 返回详细错误信息
   - B. 返回堆栈跟踪
   - C. 记录日志并返回友好消息
   - D. 忽略异常

<details>
<summary>点击查看答案</summary>

1. ✅ B. 领域异常（DomainException）
2. ✅ D. 404
3. ✅ C. 409
4. ✅ B. FastAPI app 实例
5. ✅ C. 记录日志并返回友好消息

</details>

---

## 📝 记忆口诀

```
异常分层要记牢，
Service 抛出领域异常。
Handler 负责映射 HTTP，
统一格式返回给前端。

四零四找不见，
四零九有冲突。
四零零参数错，
五零零服务器。

生产环境不暴露，
详细日志后台存。
友好消息给用户，
调试开发分开整。
```

---

## 🔄 数据流程图

```
┌─────────────────────────────────────────────────────────┐
│                   Client Request                        │
│                  GET /users/123                         │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              FastAPI Endpoint                           │
│                                                          │
│  @app.get("/users/{id}")                                │
│  async def get_user(id: int, service: UserService):     │
│      user = await service.get_user(id)  # 可能抛出异常   │
│      return success_response(data=user)                 │
└─────────────────────────────────────────────────────────┘
                          │
                          │ (如果用户不存在)
                          ▼
┌─────────────────────────────────────────────────────────┐
│              Service Layer                              │
│                                                          │
│  async def get_user(self, user_id: int) -> User:        │
│      user = await self.repo.find_by_id(user_id)         │
│      if not user:                                       │
│          raise UserNotFoundException(user_id)  # 领域异常│
│      return user                                         │
└─────────────────────────────────────────────────────────┘
                          │
                          │ 异常向上传播
                          ▼
┌─────────────────────────────────────────────────────────┐
│         Global Exception Handler                        │
│                                                          │
│  async def domain_exception_handler(                    │
│      request, exc: DomainException                      │
│  ):                                                     │
│      # 映射: USER_NOT_FOUND → 404                       │
│      return JSONResponse(                               │
│          status_code=404,                               │
│          content={                                      │
│              "code": 404,                               │
│              "message": "用户 123 不存在",              │
│              "data": {                                  │
│                  "error_code": "USER_NOT_FOUND"         │
│              },                                         │
│              "timestamp": 1739184000                    │
│          }                                              │
│      )                                                  │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                   Client Response                       │
│                                                          │
│  HTTP 404 Not Found                                     │
│  {                                                     │
│    "code": 404,                                        │
│    "message": "用户 123 不存在",                       │
│    "data": {                                           │
│      "error_code": "USER_NOT_FOUND"                    │
│    },                                                  │
│    "timestamp": 1739184000                             │
│  }                                                     │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 下一步

现在你已经了解了错误处理的设计，可以：
1. 查看代码示例：`examples/04_error_handling.py`
2. 回顾统一响应格式：`notes/03_unified_response.md`
3. 进入 Level 2：学习依赖注入系统

**记住**：好的错误处理让 API 更可靠、更易用！

---

## 📚 延伸阅读

- [FastAPI Exception Handling](https://fastapi.tiangolo.com/tutorial/handling-errors/)
- [HTTP Status Codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)
- [REST API Error Handling Best Practices](https://restfulapi.net/http-status-codes/)

---

**让错误成为有用的信息，而不是谜题！** 🎯
