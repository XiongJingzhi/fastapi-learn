# 03 统一响应格式 - API 的一致性保障

## 📖 为什么需要统一响应格式？

想象你在一家餐厅点餐：

```
❌ 没有统一格式：
服务员A：给你端上来一盘菜（直接给食物）
服务员B：给你一个菜单 + 食物（格式不同）
服务员C：给你一个号码牌，让你等（又一种格式）

✅ 统一格式：
所有服务员：
1. "您好，这是您的订单号" (code)
2. "您的餐点已经准备好了" (message)
3. 端上食物 (data)
4. "祝您用餐愉快" (timestamp)
```

**API 的响应格式也是一样**：
- 前端（移动端/Web）需要统一的格式来处理响应
- 统一格式让前端可以封装通用的处理逻辑
- 便于添加全局功能（如统一错误提示、Loading 状态）

---

## 🎯 核心概念

### 什么是统一响应格式？

**定义**：整个 API 中所有端点都使用相同的响应结构

**典型结构**：
```json
{
    "code": 200,              // 业务状态码
    "message": "success",     // 用户友好的消息
    "data": {...},            // 实际数据
    "timestamp": 1234567890   // 时间戳
}
```

**为什么要这样设计？**

1. **前端友好** - 可以封装统一的响应处理逻辑
2. **易于调试** - 时间戳帮助追踪请求
3. **国际化** - message 可以根据语言切换
4. **日志友好** - 统一格式便于日志分析

---

## 📊 响应格式设计

### 1. 基础响应格式

#### 成功响应

```json
{
    "code": 200,
    "message": "操作成功",
    "data": {
        "id": 1,
        "name": "张三",
        "email": "zhangsan@example.com"
    },
    "timestamp": 1739184000
}
```

#### 失败响应

```json
{
    "code": 400,
    "message": "参数验证失败",
    "data": {
        "detail": [
            {
                "field": "email",
                "message": "邮箱格式不正确"
            }
        ]
    },
    "timestamp": 1739184000
}
```

### 2. 分页响应格式

当返回列表数据时，需要包含分页信息：

```json
{
    "code": 200,
    "message": "查询成功",
    "data": {
        "items": [
            {"id": 1, "name": "张三"},
            {"id": 2, "name": "李四"}
        ],
        "pagination": {
            "total": 100,          // 总记录数
            "page": 1,             // 当前页码
            "page_size": 10,       // 每页大小
            "pages": 10            // 总页数
        }
    },
    "timestamp": 1739184000
}
```

**为什么需要分页信息？**

1. **性能** - 避免一次返回大量数据
2. **用户体验** - 前端可以显示"加载更多"或分页器
3. **可预测性** - 前端知道还有多少数据

### 3. 无数据响应

当操作成功但不需要返回数据时：

```json
{
    "code": 200,
    "message": "删除成功",
    "data": null,
    "timestamp": 1739184000
}
```

**或者**（如果不需要 data 字段）：

```json
{
    "code": 200,
    "message": "删除成功",
    "timestamp": 1739184000
}
```

---

## 🔧 FastAPI 实现统一响应

### 方案一：使用 Pydantic 模型（推荐）

#### 步骤 1：定义响应模型

```python
from typing import Generic, TypeVar, Optional
from pydantic import BaseModel, Field

# 泛型类型，用于 data 字段
T = TypeVar('T')

class ApiResponse(BaseModel, Generic[T]):
    """统一响应格式"""
    code: int = Field(200, description="业务状态码")
    message: str = Field("success", description="响应消息")
    data: Optional[T] = Field(None, description="响应数据")
    timestamp: int = Field(default_factory=lambda: int(time.time()))

    class Config:
        json_schema_extra = {
            "example": {
                "code": 200,
                "message": "操作成功",
                "data": {"id": 1},
                "timestamp": 1739184000
            }
        }

# 分页数据模型
class PaginatedData(BaseModel, Generic[T]):
    """分页数据"""
    items: list[T] = Field(..., description="数据列表")
    pagination: dict = Field(..., description="分页信息")

# 使用示例
class UserResponse(BaseModel):
    id: int
    name: str
    email: str
```

#### 步骤 2：创建响应辅助函数

```python
from typing import Any
import time

def success_response(
    data: Any = None,
    message: str = "操作成功",
    code: int = 200
) -> ApiResponse:
    """创建成功响应"""
    return ApiResponse(
        code=code,
        message=message,
        data=data,
        timestamp=int(time.time())
    )

def paginated_response(
    items: list[Any],
    total: int,
    page: int,
    page_size: int,
    message: str = "查询成功"
) -> ApiResponse:
    """创建分页响应"""
    paginated_data = PaginatedData(
        items=items,
        pagination={
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size
        }
    )
    return ApiResponse(
        code=200,
        message=message,
        data=paginated_data,
        timestamp=int(time.time())
    )
```

#### 步骤 3：在 Endpoint 中使用

```python
from fastapi import APIRouter, Query
from typing import List

router = APIRouter()

@router.get("/users/{user_id}", response_model=ApiResponse[UserResponse])
async def get_user(user_id: int):
    """获取单个用户"""
    # 模拟数据库查询
    user = {
        "id": user_id,
        "name": "张三",
        "email": "zhangsan@example.com"
    }
    return success_response(data=user, message="查询成功")


@router.get("/users", response_model=ApiResponse[PaginatedData[UserResponse]])
async def list_users(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页大小")
):
    """获取用户列表（分页）"""
    # 模拟数据库查询
    users = [
        {"id": i, "name": f"用户{i}", "email": f"user{i@example.com}"}
        for i in range(1, page_size + 1)
    ]
    total = 100  # 模拟总数

    return paginated_response(
        items=users,
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/users", response_model=ApiResponse[UserResponse], status_code=201)
async def create_user(user_data: dict):
    """创建用户"""
    # 模拟创建用户
    new_user = {
        "id": 1,
        "name": user_data["name"],
        "email": user_data["email"]
    }
    return success_response(
        data=new_user,
        message="创建成功",
        code=201
    )
```

### 方案二：使用响应包装器（高级）

#### 创建响应包装类

```python
from fastapi.responses import JSONResponse
from typing import Any, Optional
import time

class ResponseWrapper:
    """响应包装器 - 自动包装所有响应"""

    @staticmethod
    def success(
        data: Any = None,
        message: str = "操作成功",
        code: int = 200,
        status_code: int = 200
    ) -> JSONResponse:
        """成功响应"""
        content = {
            "code": code,
            "message": message,
            "data": data,
            "timestamp": int(time.time())
        }
        return JSONResponse(content=content, status_code=status_code)

    @staticmethod
    def error(
        message: str = "操作失败",
        code: int = 500,
        data: Any = None,
        status_code: int = 400
    ) -> JSONResponse:
        """错误响应"""
        content = {
            "code": code,
            "message": message,
            "data": data,
            "timestamp": int(time.time())
        }
        return JSONResponse(content=content, status_code=status_code)

    @staticmethod
    def paginated(
        items: list[Any],
        total: int,
        page: int,
        page_size: int,
        message: str = "查询成功"
    ) -> JSONResponse:
        """分页响应"""
        content = {
            "code": 200,
            "message": message,
            "data": {
                "items": items,
                "pagination": {
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "pages": (total + page_size - 1) // page_size
                }
            },
            "timestamp": int(time.time())
        }
        return JSONResponse(content=content)
```

#### 使用包装器

```python
@router.get("/users/{user_id}")
async def get_user(user_id: int):
    """获取单个用户"""
    user = await get_user_from_db(user_id)

    if not user:
        return ResponseWrapper.error(
            message="用户不存在",
            code=404,
            status_code=404
        )

    return ResponseWrapper.success(
        data=user,
        message="查询成功"
    )
```

---

## 🎨 架构设计考量

### 1. 响应格式放哪一层？

```
❌ 错误：在 Service 层返回 ApiResponse
class UserService:
    def get_user(self, user_id: int) -> ApiResponse:
        # 问题：Service 层不应该知道 HTTP 响应格式
        ...

✅ 正确：在 Endpoint 层包装响应
@router.get("/users/{user_id}")
async def get_user(user_id: int, service: UserService = Depends()):
    user = await service.get_user(user_id)
    return success_response(data=user)  # 在传输层包装
```

**原因**：
- **职责分离** - Service 返回领域对象，Endpoint 负责序列化
- **可复用性** - Service 可以被 CLI、gRPC 等其他接口复用
- **可测试性** - Service 不依赖响应格式

### 2. 响应模型 vs 领域模型

```python
# ❌ 混淆：直接返回领域模型（可能包含敏感信息）
class User(BaseModel):
    id: int
    name: str
    email: str
    password_hash: str  # 敏感字段！

@router.get("/users/{id}", response_model=User)
async def get_user(id: int):
    return user  # 密码泄露！

# ✅ 正确：定义响应模型
class UserInDB(BaseModel):
    """领域模型（包含所有字段）"""
    id: int
    name: str
    email: str
    password_hash: str

class UserResponse(BaseModel):
    """响应模型（只包含可公开的字段）"""
    id: int
    name: str
    email: str

    class Config:
        from_attributes = True  # 可以从 ORM 对象创建

@router.get("/users/{id}", response_model=UserResponse)
async def get_user(id: int):
    user: UserInDB = await get_user_from_db(id)
    return user  # 自动过滤 password_hash
```

**FastAPI 的自动过滤**：
```python
# 使用 response_model 的 exclude 参数
@router.get(
    "/users/{id}",
    response_model=UserResponse,
    response_model_exclude={"password_hash"}  # 排除敏感字段
)
```

### 3. 分页逻辑应该在哪？

```
❌ 错误：在 Endpoint 中实现分页逻辑
@router.get("/users")
async def list_users(page: int, page_size: int):
    # 问题：分页逻辑应该在 Service 层
    all_users = await db.query("SELECT * FROM users")
    start = (page - 1) * page_size
    end = start + page_size
    return all_users[start:end]  # 性能差！

✅ 正确：在 Service 层实现分页
class UserService:
    async def list_users(
        self,
        page: int,
        page_size: int
    ) -> PaginatedResult[User]:
        # 在数据库层面分页（使用 LIMIT/OFFSET）
        users = await self.db.query(
            "SELECT * FROM users LIMIT ? OFFSET ?",
            page_size,
            (page - 1) * page_size
        )
        total = await self.db.query("SELECT COUNT(*) FROM users")

        return PaginatedResult(
            items=users,
            total=total,
            page=page,
            page_size=page_size
        )

@router.get("/users")
async def list_users(
    page: int = Query(1),
    page_size: int = Query(10),
    service: UserService = Depends()
):
    result = await service.list_users(page, page_size)
    return paginated_response(
        items=result.items,
        total=result.total,
        page=result.page,
        page_size=result.page_size
    )
```

---

## 🔄 数据流程图

```
┌─────────────────────────────────────────────────────────┐
│                  Client (前端/移动端)                    │
└─────────────────────────────────────────────────────────┘
                          │
                          │ HTTP GET /users/123
                          ▼
┌─────────────────────────────────────────────────────────┐
│              FastAPI Endpoint (传输层)                   │
│                                                          │
│  @app.get("/users/{id}")                                │
│  async def get_user(id: int, service: UserService):     │
│      # 1. 参数校验（自动）                               │
│      # 2. 调用 Service                                  │
│      user = await service.get_user(id)                  │
│      # 3. 包装响应                                       │
│      return success_response(data=user)                 │
└─────────────────────────────────────────────────────────┘
                          │
                          │ 调用服务层
                          ▼
┌─────────────────────────────────────────────────────────┐
│              UserService (服务层)                        │
│                                                          │
│  async def get_user(self, user_id: int) -> User:        │
│      # 1. 查询数据库                                     │
│      user = await self.repo.find_by_id(user_id)         │
│      # 2. 业务规则                                       │
│      if not user:                                       │
│          raise UserNotFound()                           │
│      # 3. 返回领域对象                                   │
│      return user                                         │
└─────────────────────────────────────────────────────────┘
                          │
                          │ 查询数据
                          ▼
┌─────────────────────────────────────────────────────────┐
│          UserRepository (基础设施层)                     │
│                                                          │
│  async def find_by_id(self, id: int) -> Optional[User]: │
│      result = await db.execute(                         │
│          "SELECT * FROM users WHERE id = ?", id         │
│      )                                                  │
│      return User.from_row(result)                       │
└─────────────────────────────────────────────────────────┘
                          │
                          │ 返回领域对象
                          ▼
┌─────────────────────────────────────────────────────────┐
│              FastAPI 自动序列化                          │
│                                                          │
│  User → {                                               │
│    "code": 200,                                         │
│    "message": "success",                                │
│    "data": {"id": 123, "name": "张三"},                 │
│    "timestamp": 1739184000                              │
│  } → JSON Response                                      │
└─────────────────────────────────────────────────────────┘
                          │
                          │ HTTP Response
                          ▼
┌─────────────────────────────────────────────────────────┐
│                  Client (前端/移动端)                    │
│                                                          │
│  // 统一的响应处理                                       │
│  function handleResponse(response) {                    │
│    if (response.code === 200) {                         │
│      showSuccess(response.message);                     │
│      return response.data;                              │
│    } else {                                             │
│      showError(response.message);                       │
│    }                                                    │
│  }                                                      │
└─────────────────────────────────────────────────────────┘
```

---

## 💡 实战建议

### 1. 创建响应工具模块

```python
# app/common/response.py
from typing import Any, Generic, TypeVar, Optional, List
from pydantic import BaseModel, Field
import time

T = TypeVar('T')

class ApiResponse(BaseModel, Generic[T]):
    """统一响应格式"""
    code: int = Field(200, description="业务状态码")
    message: str = Field("success", description="响应消息")
    data: Optional[T] = Field(None, description="响应数据")
    timestamp: int = Field(default_factory=lambda: int(time.time()))

class PaginationMeta(BaseModel):
    """分页元数据"""
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")
    pages: int = Field(..., description="总页数")

class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应"""
    items: List[T] = Field(..., description="数据列表")
    pagination: PaginationMeta

def success(data: Any = None, message: str = "操作成功", code: int = 200) -> dict:
    """成功响应"""
    return {
        "code": code,
        "message": message,
        "data": data,
        "timestamp": int(time.time())
    }

def paginated(
    items: List[Any],
    total: int,
    page: int,
    page_size: int,
    message: str = "查询成功"
) -> dict:
    """分页响应"""
    return {
        "code": 200,
        "message": message,
        "data": {
            "items": items,
            "pagination": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "pages": (total + page_size - 1) // page_size
            }
        },
        "timestamp": int(time.time())
    }
```

### 2. 在路由中使用

```python
from fastapi import APIRouter, Depends, Query
from app.common.response import ApiResponse, success, paginated
from app.schemas.user import UserResponse, UserCreate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["用户"])

@router.get("/{user_id}", response_model=ApiResponse[UserResponse])
async def get_user(
    user_id: int,
    service: UserService = Depends()
):
    """获取用户详情"""
    user = await service.get_user(user_id)
    return success(data=user, message="查询成功")


@router.get("", response_model=ApiResponse[dict])
async def list_users(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页大小"),
    service: UserService = Depends()
):
    """获取用户列表"""
    result = await service.list_users(page, page_size)
    return paginated(
        items=result.items,
        total=result.total,
        page=page,
        page_size=page_size
    )


@router.post("", response_model=ApiResponse[UserResponse], status_code=201)
async def create_user(
    user_data: UserCreate,
    service: UserService = Depends()
):
    """创建用户"""
    user = await service.create_user(user_data)
    return success(data=user, message="创建成功", code=201)
```

### 3. 前端使用示例

```typescript
// TypeScript 前端代码
interface ApiResponse<T> {
    code: number;
    message: string;
    data: T;
    timestamp: number;
}

interface User {
    id: number;
    name: string;
    email: string;
}

// 统一的 API 调用函数
async function apiCall<T>(url: string): Promise<T> {
    const response = await fetch(url);
    const result: ApiResponse<T> = await response.json();

    if (result.code !== 200) {
        throw new Error(result.message);
    }

    return result.data;
}

// 使用示例
async function getUser(id: number): Promise<User> {
    return apiCall<User>(`/api/users/${id}`);
}

async function listUsers(page: number): Promise<PaginatedUsers> {
    return apiCall<PaginatedUsers>(`/api/users?page=${page}`);
}
```

---

## ⚠️ 常见错误

### 错误 1：在 Service 层返回 ApiResponse

```python
# ❌ 错误
class UserService:
    async def get_user(self, user_id: int) -> ApiResponse:
        user = await self.repo.find_by_id(user_id)
        return ApiResponse(data=user)  # Service 不应该知道响应格式

# ✅ 正确
class UserService:
    async def get_user(self, user_id: int) -> User:
        user = await self.repo.find_by_id(user_id)
        return user  # 返回领域对象
```

### 错误 2：不一致的响应格式

```python
# ❌ 错误：不同端点返回不同格式
@app.get("/users/1")
return {"id": 1, "name": "张三"}  # 格式A

@app.get("/orders/1")
return {"data": {...}, "status": "ok"}  # 格式B

# ✅ 正确：统一格式
@app.get("/users/1")
return success_response(data=user)

@app.get("/orders/1")
return success_response(data=order)
```

### 错误 3：返回所有字段（包括敏感信息）

```python
# ❌ 错误
class User(BaseModel):
    id: int
    name: str
    email: str
    password_hash: str  # 敏感！

@app.get("/users/{id}", response_model=User)
async def get_user(id: int):
    return user  # 密码泄露

# ✅ 正确：定义响应模型
class UserResponse(BaseModel):
    id: int
    name: str
    email: str

@app.get("/users/{id}", response_model=UserResponse)
async def get_user(id: int):
    return user  # FastAPI 自动过滤
```

---

## 🧪 理解验证

### 自我检查问题

1. **统一响应格式的主要目的是什么？**
   - A. 让响应看起来更专业
   - B. 便于前端统一处理响应
   - C. 减少响应大小
   - D. 提高性能

2. **响应格式应该在哪个层定义？**
   - A. Domain 层
   - B. Service 层
   - C. Endpoint/传输层
   - D. Infrastructure 层

3. **如何避免返回敏感字段？**
   - A. 在 Service 层删除敏感字段
   - B. 使用 response_model 或定义响应模型
   - C. 在数据库查询时排除
   - D. 手动构建返回字典

4. **分页逻辑应该在哪实现？**
   - A. Endpoint 层
   - B. Service 层（数据库层面分页）
   - C. 前端
   - D. 不需要分页

5. **为什么要包含 timestamp 字段？**
   - A. 看起来更专业
   - B. 便于调试和追踪请求
   - C. HTTP 协议要求
   - D. 没有特别原因

<details>
<summary>点击查看答案</summary>

1. ✅ B. 便于前端统一处理响应
2. ✅ C. Endpoint/传输层
3. ✅ B. 使用 response_model 或定义响应模型
4. ✅ B. Service 层（数据库层面分页）
5. ✅ B. 便于调试和追踪请求

</details>

---

## 📝 记忆口诀

```
响应格式要统一，
前端处理不头疼。
code message 和 data，
timestamp 也要紧跟。

分页数据有元信息，
total page 不能少。
响应模型分开定，
敏感信息保护牢。

Service 返回领域对象，
Endpoint 包装响应格式。
职责分离要记住，
架构清晰好维护。
```

---

## 🚀 下一步

现在你已经了解了统一响应格式的设计，可以：
1. 查看代码示例：`examples/03_unified_response.py`
2. 学习错误处理：`notes/04_error_handling.md`
3. 尝试设计自己的响应格式

**记住**：统一响应格式是生产级 API 的基础，值得花时间设计好！

---

## 📚 延伸阅读

- [FastAPI Response Model](https://fastapi.tiangolo.com/tutorial/response-model/)
- [Pydantic Generic Models](https://docs.pydantic.dev/latest/concepts/models/#generic-models)
- [REST API Response Format Best Practices](https://restfulapi.net/response-format/)

---

**保持一致性，让你的 API 更易用！** 🎯
