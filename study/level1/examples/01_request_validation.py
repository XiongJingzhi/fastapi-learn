"""
阶段 1.1: FastAPI 请求参数校验

学习目标:
1. 理解 Path/Query/Body/Header/Cookie 参数的区别和使用场景
2. 掌握 Pydantic 模型进行请求体验证
3. 理解参数类型转换、默认值和必填/可选参数
4. 学习如何添加参数验证规则

运行方式:
    uvicorn study.level1.examples.01_request_validation:app --reload
    访问: http://localhost:8000/docs
"""
from typing import Optional, List, Set
from datetime import datetime
from fastapi import FastAPI, Path, Query, Body, Header, Cookie, Depends, HTTPException, status, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator, EmailStr, ConfigDict

# 创建 FastAPI 应用实例
app = FastAPI(
    title="FastAPI 请求参数校验示例",
    description="演示 Path/Query/Body/Header/Cookie 参数的各种用法",
    version="1.0.0"
)


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    """
    统一处理请求参数校验错误（Pydantic -> FastAPI）。

    对外返回稳定结构，便于调用方按 code + errors 解析。
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "code": "VALIDATION_ERROR",
            "message": "请求参数校验失败",
            "path": request.url.path,
            "errors": exc.errors(),
        },
    )


# ============================================================================
# 1. Path 参数 - URL 路径中的参数
# ============================================================================

@app.get("/items/{item_id}")
async def read_item(
    item_id: int = Path(
        ...,
        description="商品ID",
        gt=0,  # 必须大于0
        le=1000  # 小于等于1000
    )
):
    """
    Path 参数示例 - 从URL路径中获取参数

    示例:
        GET /items/42

    参数验证:
        - item_id 必须是整数
        - item_id 必须大于0
        - item_id 必须小于等于1000
    """
    return {
        "item_id": item_id,
        "message": f"获取商品 {item_id} 的信息"
    }


@app.get("/files/{file_path:path}")
async def read_file(file_path: str):
    """
    Path 参数示例 - 匹配任意路径

    示例:
        GET /files/home/user/documents/file.txt

    使用 :path 可以匹配包含 / 的路径
    """
    return {
        "file_path": file_path,
        "message": f"读取文件: {file_path}"
    }


# ============================================================================
# 2. Query 参数 - URL 查询字符串中的参数
# ============================================================================

@app.get("/items/")
async def list_items(
    skip: int = Query(
        0,
        ge=0,  # 大于等于0
        description="跳过的记录数"
    ),
    limit: int = Query(
        10,
        ge=1,
        le=100,  # 小于等于100
        description="返回的记录数"
    ),
    keyword: Optional[str] = Query(
        None,
        min_length=1,
        max_length=50,
        description="搜索关键词"
    )
):
    """
    Query 参数示例 - 从URL查询字符串获取参数

    示例:
        GET /items/?skip=0&limit=10&keyword=phone

    参数验证:
        - skip: 默认0，必须 >= 0
        - limit: 默认10，必须在 1-100 之间
        - keyword: 可选，如果提供则长度在 1-50 之间
    """
    return {
        "skip": skip,
        "limit": limit,
        "keyword": keyword,
        "message": f"跳过 {skip} 条，返回 {limit} 条记录"
    }


@app.get("/search/")
async def search_items(
    q: List[str] = Query(
        [],
        description="搜索关键词列表，可以多次传递"
    )
):
    """
    Query 参数示例 - 多值参数

    示例:
        GET /search/?q=phone&q=laptop&q=tablet

    可以接收多个同名参数，自动转换为列表
    """
    return {
        "query": q,
        "count": len(q),
        "message": f"搜索关键词: {', '.join(q)}"
    }


# ============================================================================
# 3. Body 参数 - 请求体中的 JSON 数据
# ============================================================================

class ItemBase(BaseModel):
    """商品基础模型"""
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="商品名称"
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="商品描述"
    )
    price: float = Field(
        ...,
        gt=0,
        description="商品价格，必须大于0"
    )
    tax: Optional[float] = Field(
        None,
        ge=0,
        description="税率"
    )


class ItemCreate(ItemBase):
    """创建商品时的模型"""
    tags: List[str] = Field(
        default_factory=list,
        description="商品标签列表"
    )


class ItemResponse(BaseModel):
    """商品响应模型"""
    item_id: int
    name: str
    price: float
    with_tax: float
    tags: List[str] = Field(default_factory=list)
    # Pydantic v2 写法（替代 class Config）
    model_config = ConfigDict(from_attributes=True)


@app.post("/items/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(item: ItemCreate):
    """
    Body 参数示例 - 使用 Pydantic 模型验证请求体

    示例请求体:
    {
        "name": "iPhone 15",
        "description": "最新款苹果手机",
        "price": 7999.0,
        "tax": 0.13,
        "tags": ["电子产品", "手机"]
    }

    验证规则:
        - name: 必填，长度 1-100
        - description: 可选，最长500字符
        - price: 必填，必须大于0
        - tax: 可选，必须 >= 0
        - tags: 可选，字符串列表
    """
    # 计算含税价格
    item_dict = item.model_dump()
    item_dict["item_id"] = 1  # 模拟数据库生成的ID
    item_dict["with_tax"] = item.price * (1 + (item.tax or 0))

    return item_dict


# ============================================================================
# Body 参数 - 请求体中的 JSON 数据（推荐写法）
# ============================================================================

class ItemUpdate(BaseModel):
    """商品更新模型 - 统一的请求结构（推荐）"""
    name: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0)
    description: Optional[str] = Field(None, max_length=500)
    tags: List[str] = Field(default_factory=list)


@app.put("/items/{item_id}/recommended")
async def update_item_recommended(
    item_id: int = Path(..., gt=0, description="商品ID"),
    item: ItemUpdate = Body(..., description="商品数据")
):
    """
    ✅ 推荐写法：使用统一的 Pydantic 模型

    优点:
        - 清晰明确，IDE 有完整提示
        - 自动验证整个请求体
        - 客户端知道确切的数据结构
        - 易于维护和扩展

    示例请求体:
    {
        "name": "MacBook Pro",
        "price": 15999.0,
        "description": "高性能笔记本",
        "tags": ["电子产品", "电脑"]
    }

    注意:
        - item_id 来自 Path 参数
        - item 是整个请求体（Pydantic 模型）
    """
    return {
        "item_id": item_id,
        "item": item,
        "message": "✅ 商品已更新（推荐写法）"
    }


# ============================================================================
# Body 参数 - 多个参数场景（高级用法）
# ============================================================================

class ItemUpdateWithMeta(BaseModel):
    """商品更新模型（包含元数据）"""
    name: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0)
    description: Optional[str] = Field(None, max_length=500)
    tags: List[str] = Field(default_factory=list)


class ItemUpdateRequest(BaseModel):
    """
    完整的更新请求模型

    当需要同时传递商品数据和元数据时使用
    """
    item: ItemUpdateWithMeta
    user_id: int = Field(..., description="操作用户ID")
    priority: int = Field(10, ge=1, le=10, description="优先级")


@app.put("/items/{item_id}/with-meta")
async def update_item_with_metadata(
    item_id: int = Path(..., gt=0),
    request: ItemUpdateRequest = Body(...)
):
    """
    ✅ 高级场景：商品数据 + 元数据

    当请求体结构复杂时，将其封装为一个完整的模型

    优点:
        - 清晰的数据结构
        - 所有验证规则集中定义
        - 易于版本控制

    示例请求体:
    {
        "item": {
            "name": "MacBook Pro",
            "price": 15999.0,
            "tags": ["电子产品"]
        },
        "user_id": 123,
        "priority": 5
    }

    说明:
        - item_id 来自 URL 路径
        - request 是完整的请求体模型
        - user_id 是操作者ID（实际应用中应从 token 获取）
    """
    return {
        "item_id": item_id,
        "item": request.item,
        "user_id": request.user_id,
        "priority": request.priority,
        "message": "✅ 商品已更新（高级写法）"
    }


# ============================================================================
# 实际应用场景：用户认证 + 资源更新（最佳实践示例）
# ============================================================================

# 模拟：从认证 token 获取当前用户 ID
async def get_current_user_id() -> int:
    """
    依赖函数：从认证 token 获取用户 ID

    实际应用中：
    - 解析 JWT token
    - 验证 token 有效性
    - 返回用户 ID
    """
    # 这里只是模拟，返回固定值
    return 999


class ItemUpdate(BaseModel):
    """简化的更新模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    price: Optional[float] = Field(None, gt=0)


@app.put("/items/{item_id}/real-world")
async def update_item_real_world(
    item_id: int = Path(..., gt=0),
    item: ItemUpdate = Body(...),
    current_user_id: int = Depends(get_current_user_id),
    priority: int = Query(10, ge=1, le=10)
):
    """
    ✅ 生产环境推荐写法

    参数来源:
        - item_id: Path (URL 路径)
        - item: Body (请求体 - 商品数据)
        - current_user_id: Depends (从认证 token 获取)
        - priority: Query (URL 查询参数)

    示例请求:
        PUT /items/123?priority=5
        Headers: Authorization: Bearer <token>
        Body:
        {
            "name": "MacBook Pro",
            "price": 15999.0
        }

    优点:
        - 用户 ID 不由客户端指定（安全！）
        - 优先级使用 Query 参数（符合 RESTful）
        - 清晰的职责分离
    """
    return {
        "item_id": item_id,
        "item": item,
        "current_user_id": current_user_id,
        "priority": priority,
        "message": "✅ 商品已更新（生产环境写法）"
    }


# ============================================================================
# 4. Header 参数 - HTTP 请求头
# ============================================================================

@app.get("/headers/")
async def read_headers(
    user_agent: Optional[str] = Header(None),
    accept_language: Optional[str] = Header(None),
    x_token: Optional[str] = Header(
        None,
        description="自定义认证令牌"
    )
):
    """
    Header 参数示例 - 从 HTTP 请求头获取参数

    注意:
        - Header 参数会自动将下划线转换为连字符
        - x_token -> X-Token

    示例请求头:
        X-Token: your-secret-token
        Accept-Language: zh-CN
    """
    return {
        "user_agent": user_agent,
        "accept_language": accept_language,
        "x_token": x_token,
        "message": "读取请求头信息"
    }


@app.get("/auth/")
async def check_auth(
    authorization: str = Header(
        ...,
        description="Bearer token"
    )
):
    """
    Header 参数示例 - 必填的认证头

    示例请求头:
        Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证格式，应为 'Bearer <token>'"
        )

    token = authorization[7:]  # 去掉 "Bearer " 前缀
    return {
        "token": token[:20] + "...",  # 只显示前20个字符
        "status": "authenticated",
        "message": "认证成功"
    }


@app.get("/headers/response")
async def set_response_headers(response: Response):
    """
    Header 参数扩展示例 - 设置响应头

    说明:
        - 通过 Response 对象设置响应头
        - 常用于链路追踪、版本标识、缓存控制
    """
    response.headers["X-Request-Id"] = "demo-request-001"
    response.headers["X-Service-Version"] = "1.0.0"
    response.headers["Cache-Control"] = "no-store"

    return {
        "message": "已设置响应头",
        "headers_set": [
            "X-Request-Id",
            "X-Service-Version",
            "Cache-Control"
        ]
    }


# ============================================================================
# 5. Cookie 参数 - HTTP Cookie
# ============================================================================

@app.get("/cookies/")
async def read_cookies(
    session_id: Optional[str] = Cookie(
        None,
        description="会话ID"
    ),
    user_preference: Optional[str] = Cookie(
        None,
        description="用户偏好设置"
    )
):
    """
    Cookie 参数示例 - 从 HTTP Cookie 获取参数

    测试方法:
        1. 使用浏览器开发者工具设置 Cookie
        2. 或使用 curl:
           curl --cookie "session_id=abc123;user_preference=dark" \
                http://localhost:8000/cookies/
    """
    return {
        "session_id": session_id,
        "user_preference": user_preference,
        "message": "读取 Cookie 信息"
    }


@app.post("/login/")
async def login(
    response: Response,
    username: str = Body(...),
    password: str = Body(...)
):
    """
    模拟登录并设置 Cookie 的端点

    演示:
        - 接收登录凭证
        - 通过 Set-Cookie 响应头设置 Cookie
    """
    # 实际应用中这里应该验证密码哈希
    if username.strip() and password.strip():
        response.set_cookie(
            key="session_id",
            value=f"session-{username.lower()}-demo",
            max_age=3600,  # 1 小时
            httponly=True,
            samesite="lax"
        )
        response.set_cookie(
            key="user_preference",
            value="light",
            max_age=7 * 24 * 3600,  # 7 天
            httponly=False,
            samesite="lax"
        )

        return {
            "message": "登录成功",
            "username": username,
            "note": "响应已通过 Set-Cookie 写入 session_id 和 user_preference"
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码不能为空"
        )


# ============================================================================
# 6. 高级验证 - 自定义验证器和复杂模型
# ============================================================================

class UserCreate(BaseModel):
    """用户创建模型 - 演示高级验证"""
    username: str = Field(
        ...,
        min_length=3,
        max_length=20,
        pattern="^[a-zA-Z0-9_]+$",  # 只允许字母、数字、下划线
        description="用户名"
    )
    email: EmailStr = Field(
        ...,
        description="邮箱地址"
    )
    age: int = Field(
        ...,
        ge=18,
        le=120,
        description="年龄，必须成年"
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=50,
        description="密码"
    )
    confirm_password: str = Field(
        ...,
        description="确认密码"
    )
    interests: Set[str] = Field(
        default_factory=set,
        description="兴趣标签（自动去重）"
    )

    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v, info):
        """自定义验证器：确保两次密码一致"""
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('密码不匹配')
        return v

    @field_validator('username')
    @classmethod
    def username_not_admin(cls, v):
        """自定义验证器：禁止使用保留用户名"""
        if v.lower() in ['admin', 'root', 'system']:
            raise ValueError(f'"{v}" 是保留用户名')
        return v


@app.post("/users/", status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    """
    高级验证示例 - 自定义验证器和复杂模型

    示例请求体:
    {
        "username": "john_doe",
        "email": "john@example.com",
        "age": 25,
        "password": "securepass123",
        "confirm_password": "securepass123",
        "interests": ["编程", "音乐", "编程"]
    }

    验证规则:
        - username: 3-20字符，只允许字母数字下划线，不能是保留词
        - email: 必须是有效的邮箱格式
        - age: 必须在 18-120 之间
        - password: 最少8字符
        - confirm_password: 必须与 password 一致
        - interests: 自动去重（使用 Set）
    """
    # 实际应用中这里应该:
    # 1. 哈希密码
    # 2. 保存到数据库
    # 3. 返回用户信息（不包含密码）

    user_dict = user.model_dump()
    user_dict.pop('password')
    user_dict.pop('confirm_password')

    return {
        **user_dict,
        "user_id": 123,
        "created_at": datetime.now().isoformat(),
        "message": "用户创建成功"
    }


# ============================================================================
# 7. 综合示例 - 混合使用多种参数类型
# ============================================================================

@app.post("/orders/{order_id}/items/{item_id}")
async def add_order_item(
    # Path 参数
    order_id: int = Path(..., gt=0),
    item_id: int = Path(..., gt=0),

    # Query 参数
    discount: float = Query(0, ge=0, le=1),

    # Body 参数
    quantity: int = Body(..., ge=1, le=100),

    # Header 参数
    x_user_id: int = Header(..., alias="X-User-Id"),

    # Cookie 参数
    session_token: Optional[str] = Cookie(None)
):
    """
    综合示例 - 同时使用多种参数类型

    示例请求:
        POST /orders/123/items/456?discount=0.1
        Headers: X-User-Id: 789
        Cookie: session_token=abc123
        Body: {"quantity": 2}

    参数说明:
        - order_id, item_id: 来自 URL 路径
        - discount: 来自 URL 查询参数
        - quantity: 来自请求体
        - X-User-Id: 来自请求头
        - session_token: 来自 Cookie
    """
    return {
        "order_id": order_id,
        "item_id": item_id,
        "quantity": quantity,
        "discount": discount,
        "user_id": x_user_id,
        "session_token": session_token[:10] + "..." if session_token else None,
        "message": "商品已添加到订单"
    }


# ============================================================================
# 根路径和健康检查
# ============================================================================

@app.get("/")
async def root():
    """根路径 - 欢迎页面"""
    return {
        "message": "FastAPI 请求参数校验示例",
        "docs": "/docs",
        "endpoints": {
            "path": "/items/{item_id}",
            "query": "/items/",
            "body": "/items/",
            "header": "/headers/",
            "cookie": "/cookies/",
            "advanced": "/users/",
            "combined": "/orders/{order_id}/items/{item_id}"
        }
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "FastAPI Request Validation Demo"
    }


# ============================================================================
# 运行说明
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║           FastAPI 请求参数校验示例                         ║
    ╠════════════════════════════════════════════════════════════╣
    ║  启动服务...                                                ║
    ║  API 文档: http://localhost:8000/docs                      ║
    ║  健康检查: http://localhost:8000/health                    ║
    ╚════════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        # 直接 `python file.py` 运行时不要启用 reload，否则会提示必须传 import string
        reload=False
    )
