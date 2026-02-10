"""
FastAPI 响应处理示例

本文件演示了 FastAPI 中各种响应处理方式，包括：
1. JSON 响应和 response_model
2. FileResponse 和 StreamingResponse
3. 状态码处理
4. 响应头控制
5. WebSocket 基本示例

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
    description="演示各种响应处理方式",
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


# 模拟数据库
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

    - response_model 确保只返回 UserResponse 中定义的字段
    - 即使返回 UserInDB， hashed_password 也会被自动过滤
    """
    global user_id_counter

    # 检查用户名是否已存在
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
    """获取用户信息，自动过滤敏感字段"""
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
    """获取所有用户列表"""
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
    使用 response_model_exclude 而不是创建新的模型
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

    返回一个静态文件供下载
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

    使用 FileResponse 的 chunk_size 参数控制流式传输
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

    在实际应用中，这可以是：
    - 从数据库流式读取数据
    - 实时生成的日志
    - AI 模型的流式输出
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

    使用生成器函数流式返回数据
    适合大文件或实时数据
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

    用于服务器到客户端的单向实时推送
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
    """200 OK - 请求成功"""
    return {"status": "success", "message": "请求处理成功"}


@app.post(
    "/api/status/created",
    status_code=status.HTTP_201_CREATED,
    summary="资源创建"
)
async def created_response():
    """201 Created - 资源创建成功"""
    return {"status": "success", "message": "资源创建成功"}


@app.post(
    "/api/status/no-content",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="无内容返回"
)
async def no_content_response():
    """
    204 No Content - 请求成功但无返回内容

    常用于 DELETE 操作
    """
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get(
    "/api/error/bad-request",
    summary="错误请求示例"
)
async def bad_request():
    """
    400 Bad Request 示例

    客户端请求参数错误
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

    需要身份认证
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

    已认证但无权限访问
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

    请求的资源不存在
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

    请求格式正确但语义错误（FastAPI 会自动处理）
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

    服务器内部错误（实际应用中应该用 try-except 捕获）
    """
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="服务器内部错误，请稍后重试"
    )


# 自定义异常处理器
class CustomAPIError(Exception):
    """自定义 API 异常"""
    def __init__(self, message: str, code: int = 400):
        self.message = message
        self.code = code


@app.exception_handler(CustomAPIError)
async def custom_api_error_handler(request, exc: CustomAPIError):
    """自定义异常处理器"""
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

    在返回字典或使用 Response 对象时设置自定义头
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

    可以设置缓存、CORS 等各种头信息
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

    注意：生产环境建议使用 fastapi.middleware.cors.CORSMiddleware
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

    Content-Disposition: attachment 触发浏览器下载
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
    summary="永久重定向"
)
async def redirect_old_url():
    """
    307 Temporary Redirect 示例

    将旧 URL 重定向到新 URL
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

    资源已永久移动到新位置
    """
    return "/api/users/"


# ==================== 5. WebSocket 基本示例 ====================

@app.websocket("/ws/echo")
async def websocket_echo(websocket: WebSocket):
    """
    WebSocket Echo 示例

    接收客户端消息并原样返回
    适合测试 WebSocket 连接
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

    模拟简单的聊天室功能
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

    在实际应用中，这可能是：
    - 系统监控告警
    - 实时数据更新
    - 用户活动通知
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

    服务端主动推送消息给客户端
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
    """
    return {
        "name": "FastAPI 响应处理示例",
        "version": "1.0.0",
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
        "redoc": "/redoc"
    }


# ==================== 运行说明 ====================
"""
启动服务器：

    # 方式 1：使用 uvicorn 命令
    uvicorn app.examples.02_response_handling:app --reload --host 0.0.0.0 --port 8000

    # 方式 2：使用 Python 模块方式
    python -m uvicorn app.examples.02_response_handling:app --reload

测试示例：

    # 1. 创建用户
    curl -X POST "http://localhost:8000/api/users/" \
      -H "Content-Type: application/json" \
      -d '{"username": "testuser", "email": "test@example.com", "password": "password123"}'

    # 2. 获取用户列表
    curl "http://localhost:8000/api/users/"

    # 3. 下载文件
    curl -O "http://localhost:8000/api/file/download"

    # 4. 流式数据
    curl "http://localhost:8000/api/stream/data"

    # 5. 测试错误处理
    curl "http://localhost:8000/api/error/not-found"

    # 6. 测试自定义响应头
    curl -I "http://localhost:8000/api/headers/custom"

    # 7. WebSocket 测试（需要 websocat 或类似工具）
    websocat ws://localhost:8000/ws/echo

访问文档：
    - Swagger UI: http://localhost:8000/docs
    - ReDoc: http://localhost:8000/redoc

最佳实践：
    1. 始终使用 response_model 来确保 API 响应的一致性
    2. 合理使用 HTTP 状态码，遵循 RESTful 规范
    3. 对于大文件或实时数据，优先使用 StreamingResponse
    4. 使用 HTTPException 处理错误，提供清晰的错误信息
    5. 响应头设置要考虑安全性和性能（如 CORS、缓存等）
    6. WebSocket 适用于需要实时双向通信的场景
    7. 生产环境应添加日志、监控和错误追踪
"""
