"""
FastAPI 响应处理示例

本文件演示了 FastAPI 中各种响应处理方式，包括：
1. JSON 响应和 response_model
2. FileResponse 和 StreamingResponse
3. 状态码处理
4. 响应头控制
5. WebSocket 基本示例

⚠️  架构说明：
这是 Level 1 - 传输层（Transport Layer）的代码。
按照分层架构原则，本文件只负责：
  - 接收 HTTP 请求
  - 参数校验（通过 Pydantic）
  - 调用服务层（Level 2 学习）
  - 返回 HTTP 响应

业务逻辑应该在 Service 层实现，为了演示方便，这里使用了简化的内存存储。
在真实项目中，这些逻辑会移到 UserService 等服务类中。

运行方式：
    uvicorn app.examples.02_response_handling:app --reload
"""

from typing import List, Optional
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, HTTPException, status, Response, WebSocket
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse, RedirectResponse
from pydantic import BaseModel, Field
import asyncio

app = FastAPI(
    title="FastAPI 响应处理示例",
    description="演示各种响应处理方式（Level 1 - 传输层）",
    version="1.0.0"
)


# ==================== 1. JSON 响应和 response_model ====================

class UserBase(BaseModel):
    """用户基础模型"""
    username: str = Field(..., min_length=3, max_length=20, description="用户名")
    email: str = Field(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", description="邮箱")


class UserCreate(UserBase):
    """用户创建模型（包含密码）"""
    password: str = Field(..., min_length=6, description="密码，至少6位")


class UserInDB(UserBase):
    """数据库中的用户模型（包含内部字段）"""
    id: int = Field(..., description="用户ID")
    hashed_password: str = Field(..., description="加密后的密码")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")


class UserResponse(UserBase):
    """用户响应模型（不包含敏感信息）"""
    id: int = Field(..., description="用户ID")
    created_at: datetime = Field(..., description="创建时间")


# ═══════════════════════════════════════════════════════════════
# 架构说明：这是传输层代码
# ═══════════════════════════════════════════════════════════════
#
# 在真实项目中，你应该这样组织代码：
#
# ┌─────────────────────────────────────────────────┐
# │ 传输层 (Transport Layer) - 当前文件             │
# │  @app.post("/api/users/")                       │
# │  async def create_user(user: UserCreate,        │
# │                      service: UserService):     │
# │      # 只做协议适配                              │
# │      return await service.create_user(user)     │
# └─────────────────────────────────────────────────┘
#                      ↓ 调用
# ┌─────────────────────────────────────────────────┐
# │ 服务层 (Service Layer) - Level 2 学习           │
# │  class UserService:                             │
# │      async def create_user(self, user_data):    │
# │          # 业务规则验证                          │
# │          # 编排领域操作                          │
# │          # 事务管理                              │
# └─────────────────────────────────────────────────┘
#
# 为了演示方便，下面的代码使用了简化的内存存储。
# Level 2 会学习如何正确实现服务层。
# ═══════════════════════════════════════════════════════════════

# 模拟数据库（仅用于演示）
fake_db: dict[int, UserInDB] = {}
user_id_counter = 1


@app.post(
    "/api/users/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建用户",
    description="创建新用户，自动过滤密码字段"
)
async def create_user(user: UserCreate) -> UserInDB:
    """
    创建用户示例

    🔍 架构要点：
    - response_model 确保只返回 UserResponse 中定义的字段
    - 即使返回 UserInDB， hashed_password 也会被自动过滤
    - 这是传输层的核心功能：协议适配和响应序列化

    ⚠️  注意：
    在真实项目中，这里的业务逻辑（检查重复、加密密码、保存到数据库）
    应该移到 UserService 中。Endpoint 只负责调用服务层和返回响应。
    """
    global user_id_counter

    # ⚠️ 这些业务逻辑应该在 Service 层
    # 这里为了演示 response_model 功能而保留
    for existing_user in fake_db.values():
        if existing_user.username == user.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )

    # 创建用户（模拟加密密码）
    user_in_db = UserInDB(
        id=user_id_counter,
        username=user.username,
        email=user.email,
        hashed_password=f"hashed_{user.password}",  # 实际应该使用 bcrypt 等算法
        created_at=datetime.now()
    )

    fake_db[user_id_counter] = user_in_db
    user_id_counter += 1

    # 返回 UserInDB，但 FastAPI 会根据 response_model 转换为 UserResponse
    # 这就是传输层的"协议适配"功能！
    return user_in_db


@app.get(
    "/api/users/{user_id}",
    response_model=UserResponse,
    summary="获取用户信息",
    responses={
        404: {"description": "用户未找到"}
    }
)
async def get_user(user_id: int) -> UserInDB:
    """
    获取用户信息，自动过滤敏感字段

    💡 最佳实践：
    - 使用 response_model 确保响应结构一致
    - 敏感字段（hashed_password）自动被过滤
    - 404 错误使用 HTTPException 统一处理
    """
    if user_id not in fake_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户 ID {user_id} 不存在"
        )
    return fake_db[user_id]


@app.get(
    "/api/users/",
    response_model=List[UserResponse],
    summary="获取所有用户"
)
async def get_users() -> List[UserInDB]:
    """
    获取所有用户列表

    💡 response_model 的威力：
    - 可以嵌套使用（List[UserResponse]）
    - 自动序列化每个元素
    - 自动过滤敏感字段
    """
    return list(fake_db.values())


# 使用 response_model_exclude 排除字段
@app.get(
    "/api/users/{user_id}/detail",
    response_model=UserInDB,
    response_model_exclude={"hashed_password"},
    summary="获取用户详细信息（排除密码）"
)
async def get_user_detail(user_id: int) -> UserInDB:
    """
    另一种排除敏感字段的方式

    💡 两种方式对比：
    1. 创建单独的 Response 模型（推荐，更明确）
    2. 使用 response_model_exclude（快速原型）

    生产环境建议使用方式 1，因为：
    - 更清晰地表达 API 契约
    - 便于维护和重构
    - 可以添加额外的响应字段
    """
    if user_id not in fake_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户 ID {user_id} 不存在"
        )
    return fake_db[user_id]


# ==================== 2. FileResponse 和 StreamingResponse ====================

@app.get(
    "/api/file/download",
    response_class=FileResponse,
    summary="下载文件"
)
async def download_file():
    """
    FileResponse 示例

    💡 使用场景：
    - CSV/Excel 报表导出
    - PDF 文件下载
    - 图片/视频文件
    - 日志文件打包下载

    ⚠️  注意：
    - 大文件应该使用流式传输
    - 生产环境注意文件路径安全
    - 考虑添加访问权限控制
    """
    # 创建一个示例文件（实际项目中应该从文件系统读取）
    file_path = Path("/tmp/example.txt")
    file_path.write_text("这是一个示例文件内容\nHello FastAPI!", encoding="utf-8")

    return FileResponse(
        path=str(file_path),
        filename="download.txt",  # 下载时显示的文件名
        media_type="text/plain",
        status_code=200
    )


@app.get(
    "/api/file/video",
    response_class=FileResponse,
    summary="流式传输视频"
)
async def stream_video():
    """
    视频文件流式传输示例

    💡 为什么要用 chunk_size？
    - 避免一次性加载大文件到内存
    - 支持视频的随机访问（拖动进度条）
    - 降低服务器内存压力

    🎯 适用场景：
    - 视频点播
    - 音频流媒体
    - 大文件下载
    """
    # 在实际项目中，这里应该是视频文件的路径
    file_path = Path("/tmp/sample_video.mp4")

    # 如果文件不存在，创建一个空文件
    if not file_path.exists():
        file_path.write_bytes(b"fake video content")

    return FileResponse(
        path=str(file_path),
        media_type="video/mp4",
        filename="video.mp4",
        chunk_size=1024 * 1024  # 1MB chunks
    )


async def generate_large_file():
    """
    生成器函数：模拟大文件流式生成

    💡 实际应用场景：
    - 数据库导出（逐行查询）
    - 日志实时推送
    - AI 模型流式输出（ChatGPT 式）
    - 实时数据监控

    ⚡ 性能优势：
    - 不需要一次性加载全部数据到内存
    - 客户端可以边收边处理
    - 降低延迟（首字节时间更短）
    """
    for i in range(100):
        yield f"数据行 {i}\n".encode("utf-8")
        await asyncio.sleep(0.1)  # 模拟耗时操作


@app.get(
    "/api/stream/data",
    response_class=StreamingResponse,
    summary="流式数据生成"
)
async def stream_data():
    """
    StreamingResponse 示例

    🎯 什么时候用 StreamingResponse？
    - 数据量大，不能一次性加载到内存
    - 需要实时推送数据
    - 想要降低首字节延迟

    📊 对比：
    - 普通响应：等所有数据准备好再返回
    - 流式响应：有数据就立即发送
    """
    return StreamingResponse(
        generate_large_file(),
        media_type="text/plain",
        headers={
            "Content-Disposition": "attachment; filename=data.txt"
        }
    )


async def generate_sse():
    """
    Server-Sent Events (SSE) 生成器

    💡 SSE vs WebSocket：
    - SSE: 单向（服务器 → 客户端），基于 HTTP
    - WebSocket: 双向，需要额外协议

    🎯 SSE 适用场景：
    - 股票价格推送
    - 实时通知
    - 进度条更新
    """
    for i in range(10):
        data = {
            "id": i,
            "message": f"更新 {i}",
            "timestamp": datetime.now().isoformat()
        }
        yield f"data: {data}\n\n"
        await asyncio.sleep(1)


@app.get(
    "/api/stream/events",
    response_class=StreamingResponse,
    summary="Server-Sent Events"
)
async def stream_events():
    """
    SSE (Server-Sent Events) 示例

    🔍 协议格式：
    data: {"message": "hello"}\n\n

    ⚡ 优势：
    - 自动重连（浏览器原生支持）
    - 实现简单（基于 HTTP）
    - 文本格式，易于调试
    """
    return StreamingResponse(
        generate_sse(),
        media_type="text/event-stream"
    )


# ==================== 3. 状态码处理 ====================

@app.get(
    "/api/status/ok",
    status_code=status.HTTP_200_OK,
    summary="正常响应"
)
async def ok_response():
    """
    200 OK - 请求成功

    💡 使用场景：
    - GET 请求成功
    - PUT/PATCH 更新成功
    """
    return {"status": "success", "message": "请求处理成功"}


@app.post(
    "/api/status/created",
    status_code=status.HTTP_201_CREATED,
    summary="资源创建"
)
async def created_response():
    """
    201 Created - 资源创建成功

    💡 使用场景：
    - POST 请求创建资源成功
    - 返回 Location 头指向新资源
    """
    return {"status": "success", "message": "资源创建成功"}


@app.post(
    "/api/status/no-content",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="无内容返回"
)
async def no_content_response():
    """
    204 No Content - 请求成功但无返回内容

    💡 使用场景：
    - DELETE 请求成功
    - PUT 更新成功但不需要返回内容
    - POST 操作成功但无需返回数据

    ⚠️ 注意：
    必须返回 Response 对象，不能返回字典
    """
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get(
    "/api/error/bad-request",
    summary="错误请求示例"
)
async def bad_request():
    """
    400 Bad Request 示例

    💡 使用场景：
    - 请求参数格式错误
    - 缺少必填字段
    - 参数值不符合业务规则
    """
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="请求参数不正确",
        headers={"X-Error": "Bad Request"}
    )


@app.get(
    "/api/error/unauthorized",
    summary="未授权示例"
)
async def unauthorized():
    """
    401 Unauthorized 示例

    💡 使用场景：
    - 未提供认证信息
    - Token 过期
    - 认证失败

    🔐 应该返回：
    WWW-Authenticate: Bearer
    """
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="未授权，请先登录",
        headers={"WWW-Authenticate": "Bearer"}
    )


@app.get(
    "/api/error/forbidden",
    summary="禁止访问示例"
)
async def forbidden():
    """
    403 Forbidden 示例

    💡 使用场景：
    - 已认证但权限不足
    - 访问了受保护的资源
    - 超出配额限制
    """
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="权限不足，无法访问此资源"
    )


@app.get(
    "/api/error/not-found",
    summary="资源未找到示例"
)
async def not_found():
    """
    404 Not Found 示例

    💡 使用场景：
    - 资源不存在
    - URL 路径错误
    - 资源已被删除
    """
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="请求的资源不存在"
    )


@app.get(
    "/api/error/validation",
    summary="验证错误示例"
)
async def validation_error():
    """
    422 Unprocessable Entity 示例

    💡 使用场景：
    - 请求格式正确但语义错误
    - 业务规则验证失败
    - FastAPI 会自动处理 Pydantic 验证错误

    🔍 FastAPI 特有：
    这是 FastAPI 默认的验证错误状态码
    """
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={
            "field": "email",
            "message": "邮箱格式不正确"
        }
    )


@app.get(
    "/api/error/server-error",
    summary="服务器错误示例"
)
async def server_error():
    """
    500 Internal Server Error 示例

    💡 使用场景：
    - 未捕获的异常
    - 数据库连接失败
    - 第三方服务不可用

    ⚠️  注意：
    实际应用中应该用 try-except 捕获异常
    不要直接抛出 500，让框架处理
    """
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="服务器内部错误，请稍后重试"
    )


# 自定义异常处理器
class CustomAPIError(Exception):
    """自定义 API 异常

    💡 为什么要自定义异常？
    - 业务逻辑相关的错误
    - 统一的错误格式
    - 便于异常处理器统一处理
    """
    def __init__(self, message: str, code: int = 400):
        self.message = message
        self.code = code


@app.exception_handler(CustomAPIError)
async def custom_api_error_handler(request, exc: CustomAPIError):
    """
    自定义异常处理器

    💡 好处：
    - 统一的错误响应格式
    - 可以添加日志、监控
    - 隐藏内部实现细节

    🎯 使用方式：
    raise CustomAPIError("用户不存在", code=404)
    """
    return JSONResponse(
        status_code=exc.code,
        content={
            "error": True,
            "message": exc.message,
            "code": exc.code
        }
    )


@app.get("/api/error/custom")
async def custom_error():
    """触发自定义异常"""
    raise CustomAPIError("这是一个自定义错误", code=400)


# ==================== 4. 响应头控制 ====================

@app.get(
    "/api/headers/basic",
    summary="设置响应头"
)
async def basic_headers():
    """
    基本响应头设置示例

    💡 FastAPI 自动设置的响应头：
    - Content-Type: 根据返回值自动设置
    - Content-Length: 自动计算
    - Date: 自动添加
    """
    return {
        "message": "响应示例",
        "timestamp": datetime.now().isoformat()
    }


@app.get(
    "/api/headers/custom",
    summary="自定义响应头"
)
async def custom_headers(response: Response):
    """
    通过 Response 对象设置自定义响应头

    💡 常用的自定义响应头：
    - X-Request-ID: 请求追踪
    - X-Response-Time: 性能监控
    - Cache-Control: 缓存策略
    - RateLimit-Remaining: 限流信息

    ⚠️  注意：
    自定义头通常以 X- 开头（约定俗成）
    """
    # 设置自定义响应头
    response.headers["X-Custom-Header"] = "Custom Value"
    response.headers["X-Request-ID"] = "req-12345"
    response.headers["X-Response-Time"] = "100ms"

    # 设置缓存头
    response.headers["Cache-Control"] = "max-age=3600"  # 缓存 1 小时
    response.headers["Expires"] = "Wed, 21 Oct 2025 07:28:00 GMT"

    return {
        "message": "自定义响应头示例",
        "headers": {
            "X-Custom-Header": response.headers.get("X-Custom-Header"),
            "Cache-Control": response.headers.get("Cache-Control")
        }
    }


@app.get(
    "/api/headers/cors",
    summary="CORS 响应头"
)
async def cors_headers(response: Response):
    """
    CORS (跨域资源共享) 响应头示例

    💡 CORS 解决了什么问题？
    浏览器的同源策略限制，允许跨域请求

    ⚠️  注意：
    生产环境建议使用 fastapi.middleware.cors.CORSMiddleware
    不要手动设置这些头，中间件会自动处理 OPTIONS 预检请求
    """
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Max-Age"] = "3600"

    return {"message": "CORS 响应头示例"}


@app.get(
    "/api/headers/download",
    summary="文件下载响应头"
)
async def download_headers():
    """
    文件下载相关的响应头设置

    💡 关键响应头：
    - Content-Disposition: attachment 触发浏览器下载
    - Content-Length: 文件大小（支持进度条）
    - Content-Type: MIME 类型

    🎯 两种模式：
    - inline: 浏览器尝试预览（PDF、图片）
    - attachment: 强制下载
    """
    content = "这是要下载的文件内容"

    return Response(
        content=content,
        media_type="text/plain",
        headers={
            "Content-Disposition": 'attachment; filename="example.txt"',
            "Content-Length": str(len(content)),
            "X-Download-Options": "noopen"
        }
    )


@app.get(
    "/api/redirect/old-url",
    response_class=RedirectResponse,
    status_code=307,
    summary="临时重定向"
)
async def redirect_old_url():
    """
    307 Temporary Redirect 示例

    💡 重定向状态码对比：
    - 301: 永久移动（SEO 会更新索引）
    - 302: 临时重定向（常见）
    - 307: 临时重定向（保持请求方法）
    - 308: 永久重定向（保持请求方法）

    🎯 使用场景：
    - URL 迁移
    - 短链接服务
    - 认证跳转
    """
    return "/api/headers/basic"


@app.get(
    "/api/redirect/moved",
    response_class=RedirectResponse,
    status_code=301,
    summary="永久移动"
)
async def redirect_permanent():
    """
    301 Moved Permanently 示例

    💡 SEO 影响：
    搜索引擎会更新索引到新 URL

    ⚠️  注意：
    确保新 URL 可用，避免死链
    """
    return "/api/users/"


# ==================== 5. WebSocket 基本示例 ====================

@app.websocket("/ws/echo")
async def websocket_echo(websocket: WebSocket):
    """
    WebSocket Echo 示例

    💡 WebSocket vs HTTP:
    - HTTP: 请求-响应（单向）
    - WebSocket: 全双工通信（双向）

    🎯 适用场景：
    - 聊天应用
    - 实时协作（在线文档）
    - 游戏服务器
    - 实时数据推送（股票、监控）

    🔍 连接生命周期：
    1. 客户端发起握手（HTTP Upgrade）
    2. 服务器接受连接（websocket.accept()）
    3. 双向收发消息
    4. 关闭连接（websocket.close()）
    """
    await websocket.accept()  # 接受连接

    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()

            # 处理消息
            response = f"Echo: {data}"

            # 发送响应
            await websocket.send_text(response)

    except Exception as e:
        # 连接关闭或出错
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket 聊天室示例

    💡 真实项目需要：
    - 连接管理器（管理所有在线连接）
    - 消息广播（发送给所有客户端）
    - 房间管理（分组聊天）
    - 心跳机制（检测断线）

    ⚠️  注意：
    这是简化示例，真实项目需要更复杂的状态管理
    """
    await websocket.accept()

    try:
        # 等待客户端发送用户名
        username = await websocket.receive_text()

        # 欢迎消息
        await websocket.send_text(f"欢迎 {username} 加入聊天室!")

        # 聊天循环
        while True:
            message = await websocket.receive_text()

            # 广播消息（实际应用中应该使用 WebSocket 连接管理器）
            formatted_msg = f"{username}: {message}"
            await websocket.send_text(formatted_msg)

    except Exception as e:
        print(f"Chat WebSocket error: {e}")
    finally:
        await websocket.close()


class NotificationMessage(BaseModel):
    """通知消息模型"""
    type: str  # 消息类型：info, warning, error
    title: str  # 标题
    content: str  # 内容


async def generate_notifications():
    """
    生成模拟通知消息

    💡 实际应用场景：
    - 系统监控告警（CPU、内存）
    - 业务事件通知（订单状态）
    - 用户活动通知（@、评论）
    - 实时数据更新（股票价格）

    🎯 技术选型：
    - 少量用户：WebSocket 全部推送
    - 大量用户：消息队列（Kafka、Redis）
    """
    notifications = [
        NotificationMessage(
            type="info",
            title="系统通知",
            content="系统将于今晚 22:00 进行维护"
        ),
        NotificationMessage(
            type="warning",
            title="资源警告",
            content="CPU 使用率达到 80%"
        ),
        NotificationMessage(
            type="error",
            title="错误报告",
            content="数据库连接失败"
        )
    ]

    for notification in notifications:
        yield notification.model_dump_json()
        await asyncio.sleep(2)


@app.websocket("/ws/notifications")
async def websocket_notifications(websocket: WebSocket):
    """
    WebSocket 推送通知示例

    💡 服务端推送模式：
    - 轮询：客户端定时请求（低效）
    - SSE: 单向推送（基于 HTTP）
    - WebSocket: 双向推送（实时性最好）

    🎯 这里演示的是服务端主动推送
    """
    await websocket.accept()

    try:
        # 发送欢迎消息
        await websocket.send_json({
            "type": "system",
            "content": "已连接到通知服务"
        })

        # 持续推送通知
        async for notification in generate_notifications():
            await websocket.send_json(notification)

    except Exception as e:
        print(f"Notifications WebSocket error: {e}")
    finally:
        await websocket.close()


# ==================== 主页面 ====================

@app.get("/", summary="API 文档入口")
async def root():
    """
    根路径，返回 API 信息

    💡 好的 API 设计：
    - 提供清晰的入口
    - 文档链接
    - 版本信息
    - 健康检查端点
    """
    return {
        "name": "FastAPI 响应处理示例",
        "version": "1.0.0",
        "level": "Level 1 - Transport Layer",
        "description": "演示传输层的协议适配功能",
        "endpoints": {
            "users": "/api/users/",
            "file_download": "/api/file/download",
            "streaming": "/api/stream/data",
            "status_codes": "/api/status/ok",
            "errors": "/api/error/not-found",
            "headers": "/api/headers/custom",
            "websocket": "/ws/echo"
        },
        "docs": "/docs",
        "redoc": "/redoc",
        "architecture_note": (
            "这是 Level 1 的传输层代码。"
            "在真实项目中，业务逻辑应该在 Service 层实现（Level 2 学习）。"
        )
    }


# ==================== 运行说明 ====================
"""
═══════════════════════════════════════════════════════════════
启动服务器
═══════════════════════════════════════════════════════════════

方式 1：使用 uvicorn 命令
    uvicorn app.examples.02_response_handling:app --reload

方式 2：指定 host 和 port
    uvicorn app.examples.02_response_handling:app --host 0.0.0.0 --port 8000

访问文档：
    Swagger UI: http://localhost:8000/docs
    ReDoc: http://localhost:8000/redoc

═══════════════════════════════════════════════════════════════
测试示例
═══════════════════════════════════════════════════════════════

1. 创建用户（演示 response_model）
curl -X POST "http://localhost:8000/api/users/" \\
  -H "Content-Type: application/json" \\
  -d '{"username": "testuser", "email": "test@example.com", "password": "password123"}'

2. 获取用户列表（演示自动过滤密码）
curl "http://localhost:8000/api/users/"

3. 下载文件（演示 FileResponse）
curl -O "http://localhost:8000/api/file/download"

4. 流式数据（演示 StreamingResponse）
curl "http://localhost:8000/api/stream/data"

5. 测试错误处理（演示 HTTPException）
curl "http://localhost:8000/api/error/not-found"

6. 测试自定义响应头
curl -I "http://localhost:8000/api/headers/custom"

7. WebSocket 测试（需要 websocat 或类似工具）
websocat ws://localhost:8000/ws/echo

═══════════════════════════════════════════════════════════════
最佳实践总结
═══════════════════════════════════════════════════════════════

✅ 传输层应该做的事：
   1. 使用 response_model 确保响应一致性
   2. 合理使用 HTTP 状态码
   3. 大文件使用 StreamingResponse
   4. 统一错误处理（HTTPException）
   5. 设置合适的响应头

❌ 传输层不应该做的事：
   1. ❌ 直接操作数据库
   2. ❌ 编写业务规则
   3. ❌ 调用外部 API（如发送邮件）
   4. ❌ 复杂的数据处理逻辑

这些应该交给 Service 层（Level 2 学习）！

═══════════════════════════════════════════════════════════════
架构演进
═══════════════════════════════════════════════════════════════

Level 1 (当前) → 传输层：协议适配
              ↓
Level 2 (下一步) → 服务层：业务逻辑编排
              ↓
Level 3 → 基础设施层：数据库、缓存、消息队列
              ↓
Level 4 → 生产就绪：监控、日志、限流
              ↓
Level 5 → 部署运维：Docker、K8s、CI/CD

═══════════════════════════════════════════════════════════════
"""
