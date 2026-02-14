# WebSocket 实时通信 - 构建实时应用

## 🎯 什么是 WebSocket？

### HTTP vs WebSocket

```
HTTP（传统）：
客户端 → 请求 → 服务器
         ← 响应
    （客户端必须不断询问：有新消息吗？）

WebSocket（实时）：
客户端 ←→ 服务器（持续连接）
    服务器主动推送消息给客户端
    像打电话：双向、实时、持续
```

### 类比理解

```
HTTP = 发邮件
    你：发邮件问"有新消息吗？"
    服务器：回复"有"或"没有"
    你：收到，再发一封...

WebSocket = 打电话
    你：拨打电话建立连接
    对方：随时可以说话
    双方：可以同时说话（全双工）
```

### WebSocket 优势

| 场景 | HTTP | WebSocket |
|------|------|-----------|
| **实时聊天** | ❌ 需要轮询 | ✅ 即时推送 |
| **实时通知** | ❌ 延迟高 | ✅ 即时送达 |
| **股票行情** | ❌ 资源消耗大 | ✅ 高效推送 |
| **多人协作** | ❌ 同步困难 | ✅ 实时同步 |
| **游戏** | ❌ 延迟高 | ✅ 低延迟 |

---

## 🔑 核心概念

### WebSocket 生命周期

```
1. 握手（Handshake）
   客户端 → HTTP Upgrade 请求 → 服务器
   服务器 → HTTP 101 响应 → 客户端
   （连接升级为 WebSocket）

2. 数据传输
   客户端 ←→ 服务器
   （双向实时通信）

3. 关闭（Close）
   任一方发送 Close 帧
   连接关闭
```

### 消息类型

```python
# 文本消息（最常用）
await websocket.send_json({"msg": "Hello"})
await websocket.receive_json()

# 二进制消息
await websocket.send_bytes(b"binary data")
await websocket.receive_bytes()

# 文本消息
await websocket.send_text("plain text")
await websocket.receive_text()
```

---

## 🎨 FastAPI WebSocket 实现

### 基础 WebSocket

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List

app = FastAPI()

class ConnectionManager:
    """连接管理器"""

    def __init__(self):
        # 存储所有活跃连接
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """接受连接"""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """断开连接"""
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """发送个人消息"""
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        """广播消息给所有连接"""
        for connection in self.active_connections:
            await connection.send_text(message)

# 创建管理器实例
manager = ConnectionManager()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    """
    WebSocket 端点

    客户端连接示例：
    const ws = new WebSocket('ws://localhost:8000/ws/123');
    ws.onmessage = (event) => console.log(event.data);
    ws.send('Hello Server');
    """
    await manager.connect(websocket)
    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()
            print(f"Client {client_id}: {data}")

            # 回复消息
            await manager.send_personal_message(
                f"You sent: {data}",
                websocket
            )

            # 广播给所有人
            await manager.broadcast(
                f"Client {client_id} says: {data}"
            )
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client {client_id} left")
```

### WebSocket 路由参数

```python
@app.websocket("/ws/{room_id}/{user_id}")
async def chat_websocket(
    websocket: WebSocket,
    room_id: str,
    user_id: str
):
    await websocket.accept()
    await websocket.send_text(
        f"Welcome to room {room_id}, user {user_id}!"
    )

    while True:
        data = await websocket.receive_text()
        # 处理消息
        response = f"{user_id} in {room_id}: {data}"
        await websocket.send_text(response)
```

---

## 💬 实战：实时聊天室

### 完整聊天室实现

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from pydantic import BaseModel
from typing import Dict, Set
from datetime import datetime

app = FastAPI()

# ========== 数据模型 ==========

class ChatMessage(BaseModel):
    """聊天消息"""
    room_id: str
    user_id: str
    username: str
    message: str
    timestamp: datetime

# ========== 聊天室管理 ==========

class ChatRoom:
    """聊天室"""

    def __init__(self, room_id: str):
        self.room_id = room_id
        # 存储房间内的所有 WebSocket 连接
        self.connections: Dict[str, WebSocket] = {}
        # 消息历史（可选）
        self.message_history: list[ChatMessage] = []

    async def connect(self, websocket: WebSocket, user_id: str, username: str):
        """用户加入房间"""
        await websocket.accept()
        self.connections[user_id] = websocket

        # 发送欢迎消息
        await websocket.send_json({
            "type": "system",
            "message": f"欢迎 {username} 加入房间 {self.room_id}",
            "timestamp": datetime.now().isoformat()
        })

        # 通知其他人
        await self.broadcast({
            "type": "user_joined",
            "username": username,
            "message": f"{username} 加入了聊天室",
            "timestamp": datetime.now().isoformat()
        }, exclude_user_id=user_id)

    def disconnect(self, user_id: str, username: str):
        """用户离开房间"""
        if user_id in self.connections:
            del self.connections[user_id]

    async def broadcast(self, message: dict, exclude_user_id: str = None):
        """广播消息给房间内的所有人"""
        for user_id, connection in self.connections.items():
            # 排除发送者（可选）
            if user_id != exclude_user_id:
                try:
                    await connection.send_json(message)
                except:
                    # 连接可能已断开
                    self.disconnect(user_id, "")

# ========== 聊天室管理器 ==========

class ChatRoomManager:
    """管理所有聊天室"""

    def __init__(self):
        self.rooms: Dict[str, ChatRoom] = {}

    def get_or_create_room(self, room_id: str) -> ChatRoom:
        """获取或创建聊天室"""
        if room_id not in self.rooms:
            self.rooms[room_id] = ChatRoom(room_id)
        return self.rooms[room_id]

# 全局聊天室管理器
room_manager = ChatRoomManager()

# ========== WebSocket 端点 ==========

@app.websocket("/ws/chat/{room_id}")
async def chat_websocket(
    websocket: WebSocket,
    room_id: str,
    user_id: str,
    username: str
):
    """
    聊天室 WebSocket 端点

    客户端连接示例：
    const ws = new WebSocket(
      'ws://localhost:8000/ws/chat/general?user_id=123&username=Alice'
    );

    ws.onopen = () => {
      console.log('Connected to chat room');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('Received:', data);
    };

    ws.send(JSON.stringify({
      type: 'message',
      message: 'Hello everyone!'
    }));
    """

    # 获取或创建聊天室
    room = room_manager.get_or_create_room(room_id)

    # 连接
    await room.connect(websocket, user_id, username)

    try:
        while True:
            # 接收消息
            data = await websocket.receive_json()

            # 处理不同类型的消息
            if data.get("type") == "message":
                # 创建聊天消息
                chat_message = ChatMessage(
                    room_id=room_id,
                    user_id=user_id,
                    username=username,
                    message=data["message"],
                    timestamp=datetime.now()
                )

                # 广播给房间内的所有人
                await room.broadcast({
                    "type": "message",
                    "user_id": user_id,
                    "username": username,
                    "message": data["message"],
                    "timestamp": chat_message.timestamp.isoformat()
                })

            elif data.get("type") == "typing":
                # 广播"正在输入"状态
                await room.broadcast({
                    "type": "typing",
                    "user_id": user_id,
                    "username": username
                }, exclude_user_id=user_id)

    except WebSocketDisconnect:
        # 用户断开连接
        room.disconnect(user_id, username)
        await room.broadcast({
            "type": "user_left",
            "username": username,
            "message": f"{username} 离开了聊天室",
            "timestamp": datetime.now().isoformat()
        })

# ========== REST API（补充） ==========

@app.get("/rooms/{room_id}/users")
async def get_room_users(room_id: str):
    """获取聊天室在线用户"""
    room = room_manager.get_or_create_room(room_id)
    return {
        "room_id": room_id,
        "online_users": list(room.connections.keys()),
        "count": len(room.connections)
    }
```

### 客户端实现

```html
<!DOCTYPE html>
<html>
<head>
    <title>WebSocket 聊天室</title>
</head>
<body>
    <h1>聊天室</h1>
    <div id="messages"></div>
    <input type="text" id="messageInput" placeholder="输入消息...">
    <button onclick="sendMessage()">发送</button>

    <script>
        const room_id = "general";
        const user_id = "user_" + Math.random().toString(36).substr(2, 9);
        const username = "Alice";

        // 连接 WebSocket
        const ws = new WebSocket(
            `ws://localhost:8000/ws/chat/${room_id}?user_id=${user_id}&username=${username}`
        );

        // 连接打开
        ws.onopen = () => {
            console.log("Connected to chat room");
            addMessage("系统", "已连接到聊天室");
        };

        // 接收消息
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);

            if (data.type === "message") {
                addMessage(data.username, data.message);
            } else if (data.type === "user_joined") {
                addMessage("系统", data.message);
            }
        };

        // 连接关闭
        ws.onclose = () => {
            addMessage("系统", "已断开连接");
        };

        // 发送消息
        function sendMessage() {
            const input = document.getElementById("messageInput");
            const message = input.value;

            if (message.trim()) {
                ws.send(JSON.stringify({
                    type: "message",
                    message: message
                }));
                input.value = "";
            }
        }

        // 添加消息到界面
        function addMessage(username, message) {
            const messagesDiv = document.getElementById("messages");
            const messageDiv = document.createElement("div");
            messageDiv.textContent = `${username}: ${message}`;
            messagesDiv.appendChild(messageDiv);
        }

        // 回车发送
        document.getElementById("messageInput").addEventListener("keypress", (e) => {
            if (e.key === "Enter") {
                sendMessage();
            }
        });
    </script>
</body>
</html>
```

---

## 🔄 高级功能

### 1. 心跳和重连

```python
import asyncio

@app.websocket("/ws")
async def websocket_with_heartbeat(websocket: WebSocket):
    await websocket.accept()

    # 心跳任务
    async def send_heartbeat():
        while True:
            await asyncio.sleep(30)  # 每30秒
            try:
                await websocket.send_json({"type": "ping"})
            except:
                break

    # 启动心跳任务
    heartbeat_task = asyncio.create_task(send_heartbeat())

    try:
        while True:
            data = await websocket.receive_json()

            # 响应心跳
            if data.get("type") == "pong":
                continue

            # 处理其他消息
            await websocket.send_json({"type": "echo", "data": data})
    finally:
        heartbeat_task.cancel()
```

### 客户端自动重连

```javascript
class WebSocketClient {
    constructor(url) {
        this.url = url;
        this.ws = null;
        this.reconnectDelay = 1000;
        this.maxReconnectDelay = 30000;
    }

    connect() {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
            console.log("Connected");
            this.reconnectDelay = 1000;  // 重置延迟
        };

        this.ws.onclose = () => {
            console.log("Disconnected, reconnecting...");
            setTimeout(() => this.connect(), this.reconnectDelay);
            this.reconnectDelay = Math.min(
                this.reconnectDelay * 2,
                this.maxReconnectDelay
            );
        };

        this.ws.onmessage = (event) => {
            this.handleMessage(event.data);
        };
    }

    handleMessage(data) {
        const message = JSON.parse(data);

        if (message.type === "ping") {
            // 响应心跳
            this.ws.send(JSON.stringify({type: "pong"}));
        } else {
            console.log("Received:", message);
        }
    }

    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        }
    }
}

// 使用
const client = new WebSocketClient("ws://localhost:8000/ws");
client.connect();
```

### 2. 私有频道

```python
class PrivateChannelManager:
    """私有频道管理"""

    def __init__(self):
        # user_id -> room_id -> WebSocket
        self.user_rooms: Dict[str, Dict[str, WebSocket]] = {}

    async def join_private_channel(
        self,
        websocket: WebSocket,
        user_id: str,
        room_id: str
    ):
        """加入私有频道"""
        if user_id not in self.user_rooms:
            self.user_rooms[user_id] = {}

        self.user_rooms[user_id][room_id] = websocket
        await websocket.send_json({
            "type": "joined",
            "channel": room_id
        })

    async def send_to_user(self, user_id: str, room_id: str, message: dict):
        """发送消息到特定用户的特定频道"""
        if user_id in self.user_rooms and room_id in self.user_rooms[user_id]:
            websocket = self.user_rooms[user_id][room_id]
            await websocket.send_json(message)
```

### 3. 广播优化（避免阻塞）

```python
import asyncio

async def broadcast_message(message: dict, connections: list[WebSocket]):
    """并发广播（避免串行等待）"""
    tasks = []
    for connection in connections:
        tasks.append(connection.send_json(message))

    # 并发执行所有发送任务
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 处理失败的连接
    for result, connection in zip(results, connections):
        if isinstance(result, Exception):
            # 连接可能已断开，移除它
            connections.remove(connection)
```

---

## 🛡️ 安全考虑

### 1. 验证 WebSocket 连接

```python
from fastapi import Query, Header

@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),  # 查询参数验证
    user_agent: str = Header(None)  # 头部验证
):
    await websocket.accept()

    # 验证 token
    user = verify_token(token)
    if not user:
        await websocket.close(code=1008, reason="Unauthorized")
        return

    # 继续...
```

### 2. 限制连接数

```python
class ConnectionLimiter:
    """连接限制器"""

    def __init__(self, max_connections: int):
        self.max_connections = max_connections
        self.current_connections = 0

    def can_connect(self) -> bool:
        if self.current_connections >= self.max_connections:
            return False
        self.current_connections += 1
        return True

    def disconnect(self):
        self.current_connections -= 1

limiter = ConnectionLimiter(max_connections=100)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    if not limiter.can_connect():
        await websocket.close(code=1013, reason="Too many connections")
        return

    await websocket.accept()

    try:
        # ...
        pass
    finally:
        limiter.disconnect()
```

---

## 📊 性能优化

### 1. 消息队列

```python
import asyncio
from collections import deque

class BufferedWebSocket:
    """缓冲 WebSocket 连接"""

    def __init__(self, websocket: WebSocket, buffer_size: int = 100):
        self.websocket = websocket
        self.buffer = deque(maxlen=buffer_size)
        self.send_task = None

    async def send(self, message: dict):
        """添加到缓冲区"""
        self.buffer.append(message)

        # 如果发送任务没有运行，启动它
        if self.send_task is None or self.send_task.done():
            self.send_task = asyncio.create_task(self._send_buffer())

    async def _send_buffer(self):
        """批量发送缓冲区的消息"""
        while self.buffer:
            message = self.buffer.popleft()
            try:
                await self.websocket.send_json(message)
            except:
                break
```

### 2. 使用 Redis 实现分布式

```python
import redis

# 发布消息到 Redis（某个频道）
redis_client = redis.Redis()

@app.post("/broadcast/{room_id}")
async def broadcast_to_room(room_id: str, message: dict):
    """通过 Redis 广播"""
    redis_client.publish(
        f"room:{room_id}",
        json.dumps(message)
    )
    return {"status": "sent"}

# 在 WebSocket 中订阅
@app.websocket("/ws/{room_id}")
async def websocket_websocket(websocket: WebSocket, room_id: str):
    await websocket.accept()

    # 订阅 Redis 频道
    pubsub = redis_client.pubsub()
    pubsub.subscribe(f"room:{room_id}")

    try:
        for message in pubsub.listen():
            if message["type"] == "message":
                data = json.loads(message["data"])
                await websocket.send_json(data)
    finally:
        pubsub.unsubscribe()
```

---

## 🎯 总结

**WebSocket 核心要点**：

1. ✅ **实时双向通信**：服务器可以主动推送
2. ✅ **持久连接**：建立连接后持续通信
3. ✅ **低延迟**：比 HTTP 轮询快得多
4. ✅ **适合场景**：聊天、通知、游戏、协作

**最佳实践**：
- 实现心跳和重连机制
- 处理连接断开
- 限制连接数
- 验证连接权限
- 优化广播性能

**使用场景**：
- ✅ 实时聊天
- ✅ 实时通知
- ✅ 协作编辑
- ✅ 多人游戏
- ❌ 简单的 CRUD（用 HTTP）

**下一步**：学习测试和部署

---

**WebSocket 让实时应用成为可能！** 💬
