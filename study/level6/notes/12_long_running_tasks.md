# 12. 长时间运行任务的会话保持

## 🎯 场景描述

### 问题：LangGraph 长时间运行任务的上下文保持

```
用户发起请求
    ↓
节点 A: 执行任务（保存上下文到内存）
    ↓
节点 A: 继续执行...
    ↓
节点 A: 挂了 / 超时 / 用户断开连接
    ↓
用户重新请求
    ↓
❌ 如果路由到节点 B → 丢失之前的上下文
✅ 如果路由到节点 A → 可以恢复上下文继续执行
```

### 实际案例

**LangGraph 图执行场景**：

```python
# 伪代码：LangGraph 图执行
graph = StateGraph()

# 节点 1: 数据准备
@graph.add_node("prepare")
async def prepare_data(state):
    # 可能需要 10 秒
    state["data"] = fetch_large_dataset()
    return state

# 节点 2: 数据处理
@graph.add_node("process")
async def process_data(state):
    # 可能需要 30 秒
    state["processed"] = process_large_dataset(state["data"])
    return state

# 节点 3: 生成报告
@graph.add_node("generate")
async def generate_report(state):
    # 可能需要 20 秒
    state["report"] = generate_report(state["processed"])
    return state

# 执行图
result = await graph.execute(initial_state)

# 问题：如果在节点 2 执行时节点挂了，状态丢失！
```

**用户请求流程**：

```
T0: 用户发起任务 → 节点 A 开始执行
T1: 节点 A 执行到"数据准备"完成
T2: 节点 A 执行到"数据处理"进行中...
T3: 节点 A 挂了 / 超时 / 网络断开
T4: 用户重试请求

需求：
- 请求应该路由到节点 A（之前的上下文在节点 A）
- 或者路由到任意节点，但能从持久化存储恢复上下文
```

---

## 📚 解决方案

### 方案 1：任务 ID 一致性哈希（推荐）

#### 原理

使用任务 ID（Task ID）或会话 ID（Session ID）作为哈希键，确保同一个任务的所有请求都路由到同一个节点。

```
任务 ID: task_12345
    ↓
一致性哈希
    ↓
目标节点: api-1
    ↓
所有关于 task_12345 的请求都路由到 api-1
```

#### Nginx 配置

```nginx
upstream langgraph_backend {
    # 使用任务 ID 进行一致性哈希
    hash $arg_task_id consistent;
    
    server api-1:8000;
    server api-2:8000;
    server api-3:8000;
}

upstream api_backend {
    # 普通 API 使用轮询
    server api-1:8000;
    server api-2:8000;
    server api-3:8000;
}

server {
    listen 80;
    
    # LangGraph 任务执行端点（需要会话保持）
    location /api/tasks/execute/ {
        proxy_pass http://langgraph_backend;
        proxy_set_header Host $host;
    }
    
    # 查询任务状态（需要会话保持）
    location /api/tasks/ {
        proxy_pass http://langgraph_backend;
        proxy_set_header Host $host;
    }
    
    # 普通 API（不需要会话保持）
    location /api/ {
        proxy_pass http://api_backend;
        proxy_set_header Host $host;
    }
}
```

#### FastAPI 实现

```python
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import asyncio
from typing import Dict, Optional
import uuid
import time

app = FastAPI()

# 任务状态存储（内存中）
# 生产环境应该使用 Redis + 持久化
tasks: Dict[str, dict] = {}

class TaskRequest(BaseModel):
    graph_name: str
    initial_state: dict

class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str

async def execute_langgraph_task(task_id: str, request: TaskRequest):
    """执行 LangGraph 任务（模拟）"""
    
    try:
        # 1. 初始化任务状态
        tasks[task_id] = {
            "task_id": task_id,
            "status": "running",
            "graph_name": request.graph_name,
            "state": request.initial_state.copy(),
            "progress": 0,
            "current_node": "start",
            "error": None,
            "created_at": time.time(),
            "updated_at": time.time()
        }
        
        # 2. 模拟节点 1：数据准备
        print(f"[{task_id}] Starting data preparation...")
        tasks[task_id]["current_node"] = "prepare"
        tasks[task_id]["progress"] = 10
        await asyncio.sleep(10)  # 模拟耗时操作
        
        tasks[task_id]["state"]["data"] = "prepared_data"
        tasks[task_id]["progress"] = 30
        
        # 3. 模拟节点 2：数据处理
        print(f"[{task_id}] Starting data processing...")
        tasks[task_id]["current_node"] = "process"
        tasks[task_id]["progress"] = 40
        await asyncio.sleep(15)  # 模拟耗时操作
        
        tasks[task_id]["state"]["processed"] = "processed_data"
        tasks[task_id]["progress"] = 60
        
        # 4. 模拟节点 3：生成报告
        print(f"[{task_id}] Starting report generation...")
        tasks[task_id]["current_node"] = "generate"
        tasks[task_id]["progress"] = 70
        await asyncio.sleep(10)  # 模拟耗时操作
        
        tasks[task_id]["state"]["report"] = "generated_report"
        tasks[task_id]["progress"] = 100
        
        # 5. 任务完成
        tasks[task_id]["status"] = "completed"
        tasks[task_id]["updated_at"] = time.time()
        print(f"[{task_id}] Task completed!")
        
    except Exception as e:
        # 6. 任务失败
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["error"] = str(e)
        tasks[task_id]["updated_at"] = time.time()
        print(f"[{task_id}] Task failed: {e}")

@app.post("/api/tasks/execute")
async def create_task(
    request: TaskRequest,
    background_tasks: BackgroundTasks
) -> TaskResponse:
    """创建并执行 LangGraph 任务"""
    
    # 生成任务 ID
    task_id = f"task_{uuid.uuid4().hex[:8]}"
    
    # 启动后台任务
    background_tasks.add_task(execute_langgraph_task, task_id, request)
    
    return TaskResponse(
        task_id=task_id,
        status="running",
        message=f"Task {task_id} started"
    )

@app.get("/api/tasks/{task_id}")
async def get_task_status(task_id: str):
    """获取任务状态"""
    
    task = tasks.get(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "task_id": task["task_id"],
        "status": task["status"],
        "progress": task["progress"],
        "current_node": task["current_node"],
        "error": task["error"],
        "state": task["state"],
        "node": "current"  # 当前节点名称
    }

@app.post("/api/tasks/{task_id}/pause")
async def pause_task(task_id: str):
    """暂停任务"""
    
    task = tasks.get(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task["status"] != "running":
        raise HTTPException(
            status_code=400,
            detail=f"Task is not running (status: {task['status']})"
        )
    
    task["status"] = "paused"
    task["updated_at"] = time.time()
    
    return {"message": f"Task {task_id} paused"}

@app.post("/api/tasks/{task_id}/resume")
async def resume_task(task_id: str, background_tasks: BackgroundTasks):
    """恢复任务"""
    
    task = tasks.get(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task["status"] != "paused":
        raise HTTPException(
            status_code=400,
            detail=f"Task is not paused (status: {task['status']})"
        )
    
    # 恢复任务（从当前状态继续）
    task["status"] = "running"
    task["updated_at"] = time.time()
    
    # 重新启动后台任务（从断点继续）
    background_tasks.add_task(
        execute_langgraph_task,
        task_id,
        TaskRequest(
            graph_name=task["graph_name"],
            initial_state=task["state"]
        )
    )
    
    return {"message": f"Task {task_id} resumed"}

@app.post("/api/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    """取消任务"""
    
    task = tasks.get(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task["status"] not in ["running", "paused"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel task in status {task['status']}"
        )
    
    task["status"] = "cancelled"
    task["updated_at"] = time.time()
    
    return {"message": f"Task {task_id} cancelled"}

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "node": "current",
        "active_tasks": len([t for t in tasks.values() if t["status"] == "running"])
    }
```

#### 测试

```bash
# 1. 创建任务
curl -X POST http://localhost:8000/api/tasks/execute \
  -H "Content-Type: application/json" \
  -d '{
    "graph_name": "data_pipeline",
    "initial_state": {"input": "test_data"}
  }'

# 返回: {"task_id": "task_abc123", "status": "running", ...}

# 2. 查询任务状态（使用 task_id 确保路由到同一节点）
curl http://localhost:8000/api/tasks/task_abc123

# 返回: {"task_id": "task_abc123", "status": "running", "progress": 40, ...}

# 3. 暂停任务
curl -X POST http://localhost:8000/api/tasks/task_abc123/pause

# 4. 恢复任务（仍路由到同一节点，从断点继续）
curl -X POST http://localhost:8000/api/tasks/task_abc123/resume

# 5. 取消任务
curl -X POST http://localhost:8000/api/tasks/task_abc123/cancel
```

---

### 方案 2：Redis 持久化 + 会话保持（推荐用于生产）

#### 原理

将任务状态持久化到 Redis，同时使用任务 ID 进行哈希路由。即使节点挂了，新节点也能从 Redis 恢复状态。

```
任务执行 → 更新 Redis 状态
    ↓
节点挂了
    ↓
用户重试 → 一致性哈希路由到新节点
    ↓
新节点从 Redis 恢复状态 → 继续执行
```

#### 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                     负载均衡 (Nginx)                    │
│         hash $arg_task_id consistent                   │
└─────────────────────────────────────────────────────────┘
                    ↓
    ┌───────────┬───────────┬───────────┐
    │  API-1    │  API-2    │  API-3    │
    └─────┬─────┴─────┬─────┴─────┬─────┘
          │           │           │
          └───────────┼───────────┘
                      ↓
              ┌───────────────┐
              │    Redis      │
              │  (持久化状态)  │
              └───────────────┘
```

#### FastAPI 实现

```python
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import aioredis
import asyncio
import uuid
import time
import json
from typing import Optional

app = FastAPI()

# Redis 配置
REDIS_HOST = "redis"
REDIS_PORT = 6379

# Redis 连接
redis_client = None

async def get_redis():
    global redis_client
    if redis_client is None:
        redis_client = await aioredis.from_url(
            f"redis://{REDIS_HOST}:{REDIS_PORT}",
            encoding="utf-8",
            decode_responses=True
        )
    return redis_client

# 数据模型
class TaskRequest(BaseModel):
    graph_name: str
    initial_state: dict

class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str

# 任务状态管理
class TaskStateManager:
    """任务状态管理器（Redis 持久化）"""
    
    def __init__(self):
        self.redis = None
    
    async def init(self):
        """初始化 Redis 连接"""
        self.redis = await get_redis()
    
    async def save_task_state(self, task_id: str, state: dict):
        """保存任务状态到 Redis"""
        key = f"task:{task_id}"
        await self.redis.setex(
            key,
            3600,  # 1 小时过期
            json.dumps(state)
        )
        
        # 保存到列表（便于查询所有任务）
        await self.redis.sadd("tasks:all", task_id)
        await self.redis.expire("tasks:all", 3600)
    
    async def load_task_state(self, task_id: str) -> Optional[dict]:
        """从 Redis 加载任务状态"""
        key = f"task:{task_id}"
        data = await self.redis.get(key)
        if data:
            return json.loads(data)
        return None
    
    async def update_task_progress(self, task_id: str, progress: int):
        """更新任务进度"""
        state = await self.load_task_state(task_id)
        if state:
            state["progress"] = progress
            state["updated_at"] = time.time()
            await self.save_task_state(task_id, state)
    
    async def delete_task_state(self, task_id: str):
        """删除任务状态"""
        key = f"task:{task_id}"
        await self.redis.delete(key)
        await self.redis.srem("tasks:all", task_id)

# 任务状态管理器
task_manager = TaskStateManager()

async def execute_langgraph_task(task_id: str, request: TaskRequest):
    """执行 LangGraph 任务（支持断点恢复）"""
    
    try:
        # 1. 初始化任务状态
        initial_state = {
            "task_id": task_id,
            "status": "running",
            "graph_name": request.graph_name,
            "state": request.initial_state.copy(),
            "progress": 0,
            "current_node": "start",
            "error": None,
            "created_at": time.time(),
            "updated_at": time.time(),
            "checkpoint": None  # 检查点
        }
        
        await task_manager.save_task_state(task_id, initial_state)
        
        # 2. 从检查点恢复（如果有）
        state = await task_manager.load_task_state(task_id)
        if state.get("checkpoint"):
            print(f"[{task_id}] Resuming from checkpoint: {state['checkpoint']}")
            # 从检查点继续执行...
        
        # 3. 模拟节点 1：数据准备
        print(f"[{task_id}] Starting data preparation...")
        state["current_node"] = "prepare"
        await task_manager.update_task_progress(task_id, 10)
        await asyncio.sleep(10)
        
        # 保存检查点
        state["state"]["data"] = "prepared_data"
        state["checkpoint"] = "data_prepared"
        await task_manager.save_task_state(task_id, state)
        
        await task_manager.update_task_progress(task_id, 30)
        
        # 4. 模拟节点 2：数据处理
        print(f"[{task_id}] Starting data processing...")
        state["current_node"] = "process"
        await task_manager.update_task_progress(task_id, 40)
        await asyncio.sleep(15)
        
        # 保存检查点
        state["state"]["processed"] = "processed_data"
        state["checkpoint"] = "data_processed"
        await task_manager.save_task_state(task_id, state)
        
        await task_manager.update_task_progress(task_id, 60)
        
        # 5. 模拟节点 3：生成报告
        print(f"[{task_id}] Starting report generation...")
        state["current_node"] = "generate"
        await task_manager.update_task_progress(task_id, 70)
        await asyncio.sleep(10)
        
        state["state"]["report"] = "generated_report"
        await task_manager.save_task_state(task_id, state)
        
        await task_manager.update_task_progress(task_id, 100)
        
        # 6. 任务完成
        state["status"] = "completed"
        state["checkpoint"] = "completed"
        await task_manager.save_task_state(task_id, state)
        print(f"[{task_id}] Task completed!")
        
    except Exception as e:
        # 7. 任务失败
        state = await task_manager.load_task_state(task_id)
        state["status"] = "failed"
        state["error"] = str(e)
        state["updated_at"] = time.time()
        await task_manager.save_task_state(task_id, state)
        print(f"[{task_id}] Task failed: {e}")

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    await task_manager.init()
    print("Task state manager initialized")

@app.post("/api/tasks/execute")
async def create_task(
    request: TaskRequest,
    background_tasks: BackgroundTasks
) -> TaskResponse:
    """创建并执行 LangGraph 任务"""
    
    # 生成任务 ID
    task_id = f"task_{uuid.uuid4().hex[:8]}"
    
    # 启动后台任务
    background_tasks.add_task(execute_langgraph_task, task_id, request)
    
    return TaskResponse(
        task_id=task_id,
        status="running",
        message=f"Task {task_id} started"
    )

@app.get("/api/tasks/{task_id}")
async def get_task_status(task_id: str):
    """获取任务状态"""
    
    state = await task_manager.load_task_state(task_id)
    
    if not state:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "task_id": state["task_id"],
        "status": state["status"],
        "progress": state["progress"],
        "current_node": state["current_node"],
        "error": state["error"],
        "state": state["state"],
        "checkpoint": state["checkpoint"],
        "node": os.getenv("SERVICE_NAME", "unknown")
    }

@app.post("/api/tasks/{task_id}/resume")
async def resume_task(task_id: str, background_tasks: BackgroundTasks):
    """恢复任务（从 Redis 恢复状态）"""
    
    state = await task_manager.load_task_state(task_id)
    
    if not state:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if state["status"] != "paused":
        raise HTTPException(
            status_code=400,
            detail=f"Task is not paused (status: {state['status']})"
        )
    
    # 恢复任务（从 Redis 中的状态继续）
    state["status"] = "running"
    state["updated_at"] = time.time()
    await task_manager.save_task_state(task_id, state)
    
    # 重新启动后台任务（从断点继续）
    background_tasks.add_task(
        execute_langgraph_task,
        task_id,
        TaskRequest(
            graph_name=state["graph_name"],
            initial_state=state["state"]
        )
    )
    
    return {
        "message": f"Task {task_id} resumed",
        "checkpoint": state["checkpoint"]
    }

@app.get("/api/tasks")
async def list_tasks():
    """列出所有任务"""
    redis = await get_redis()
    task_ids = await redis.smembers("tasks:all")
    
    tasks = []
    for task_id in task_ids:
        state = await task_manager.load_task_state(task_id)
        if state:
            tasks.append({
                "task_id": state["task_id"],
                "status": state["status"],
                "progress": state["progress"],
                "created_at": state["created_at"]
            })
    
    return {"tasks": tasks}

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "node": os.getenv("SERVICE_NAME", "unknown")
    }
```

---

### 方案 3：WebSocket + 任务队列（推荐用于实时交互）

#### 原理

使用 WebSocket 保持长连接，任务执行过程中实时推送进度。如果连接断开，可以通过任务 ID 重新连接。

#### 架构设计

```
用户连接 WebSocket (携带 task_id)
    ↓
一致性哈希路由到特定节点
    ↓
节点保持 WebSocket 连接
    ↓
任务执行 → 实时推送进度
    ↓
连接断开
    ↓
用户使用 task_id 重新连接
    ↓
路由到同一节点 → 恢复连接 → 继续推送
```

#### FastAPI 实现

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
import asyncio
import uuid
import time
import json
from typing import Dict, Set

app = FastAPI()

# WebSocket 连接管理
class ConnectionManager:
    """WebSocket 连接管理器"""
    
    def __init__(self):
        # 每个节点的活跃连接
        self.active_connections: Dict[str, WebSocket] = {}
        
        # 任务对应的连接
        self.task_connections: Dict[str, str] = {}  # task_id -> connection_id
    
    async def connect(self, websocket: WebSocket, connection_id: str):
        """接受连接"""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
    
    def disconnect(self, connection_id: str):
        """断开连接"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        # 清理任务关联
        tasks_to_remove = [
            task_id for task_id, conn_id in self.task_connections.items()
            if conn_id == connection_id
        ]
        for task_id in tasks_to_remove:
            del self.task_connections[task_id]
    
    async def send_personal_message(self, message: dict, connection_id: str):
        """发送消息给特定连接"""
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            await websocket.send_json(message)
    
    async def broadcast_to_task(self, message: dict, task_id: str):
        """广播消息给任务相关的连接"""
        connection_id = self.task_connections.get(task_id)
        if connection_id:
            await self.send_personal_message(message, connection_id)
    
    async def connect_task(self, connection_id: str, task_id: str):
        """连接任务"""
        self.task_connections[task_id] = connection_id

# 连接管理器
manager = ConnectionManager()

# 任务状态
tasks: Dict[str, dict] = {}

async def execute_langgraph_task(
    task_id: str,
    graph_name: str,
    initial_state: dict
):
    """执行 LangGraph 任务（实时推送进度）"""
    
    try:
        # 1. 初始化任务
        tasks[task_id] = {
            "task_id": task_id,
            "status": "running",
            "graph_name": graph_name,
            "state": initial_state.copy(),
            "progress": 0,
            "current_node": "start",
            "error": None,
            "created_at": time.time(),
            "updated_at": time.time()
        }
        
        # 推送开始消息
        await manager.broadcast_to_task({
            "type": "task_started",
            "task_id": task_id,
            "status": "running"
        }, task_id)
        
        # 2. 模拟节点 1：数据准备
        print(f"[{task_id}] Starting data preparation...")
        tasks[task_id]["current_node"] = "prepare"
        
        await manager.broadcast_to_task({
            "type": "progress",
            "task_id": task_id,
            "progress": 10,
            "message": "Preparing data...",
            "current_node": "prepare"
        }, task_id)
        
        await asyncio.sleep(10)
        
        tasks[task_id]["state"]["data"] = "prepared_data"
        await manager.broadcast_to_task({
            "type": "progress",
            "task_id": task_id,
            "progress": 30,
            "message": "Data prepared",
            "current_node": "prepare"
        }, task_id)
        
        # 3. 模拟节点 2：数据处理
        print(f"[{task_id}] Starting data processing...")
        tasks[task_id]["current_node"] = "process"
        
        await manager.broadcast_to_task({
            "type": "progress",
            "task_id": task_id,
            "progress": 40,
            "message": "Processing data...",
            "current_node": "process"
        }, task_id)
        
        await asyncio.sleep(15)
        
        tasks[task_id]["state"]["processed"] = "processed_data"
        await manager.broadcast_to_task({
            "type": "progress",
            "task_id": task_id,
            "progress": 60,
            "message": "Data processed",
            "current_node": "process"
        }, task_id)
        
        # 4. 模拟节点 3：生成报告
        print(f"[{task_id}] Starting report generation...")
        tasks[task_id]["current_node"] = "generate"
        
        await manager.broadcast_to_task({
            "type": "progress",
            "task_id": task_id,
            "progress": 70,
            "message": "Generating report...",
            "current_node": "generate"
        }, task_id)
        
        await asyncio.sleep(10)
        
        tasks[task_id]["state"]["report"] = "generated_report"
        
        # 5. 任务完成
        tasks[task_id]["status"] = "completed"
        tasks[task_id]["progress"] = 100
        
        await manager.broadcast_to_task({
            "type": "task_completed",
            "task_id": task_id,
            "status": "completed",
            "progress": 100,
            "result": tasks[task_id]["state"]
        }, task_id)
        
        print(f"[{task_id}] Task completed!")
        
    except Exception as e:
        # 6. 任务失败
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["error"] = str(e)
        
        await manager.broadcast_to_task({
            "type": "task_failed",
            "task_id": task_id,
            "status": "failed",
            "error": str(e)
        }, task_id)
        
        print(f"[{task_id}] Task failed: {e}")

@app.websocket("/ws/tasks/{task_id}")
async def websocket_task_endpoint(
    websocket: WebSocket,
    task_id: str
):
    """WebSocket 任务端点"""
    
    # 生成连接 ID
    connection_id = f"conn_{uuid.uuid4().hex[:8]}"
    
    # 接受连接
    await manager.connect(websocket, connection_id)
    
    # 关联任务
    await manager.connect_task(connection_id, task_id)
    
    try:
        # 检查任务是否存在
        if task_id not in tasks:
            # 创建新任务
            await manager.send_personal_message({
                "type": "error",
                "message": "Task not found. Please create task first."
            }, connection_id)
            return
        
        # 发送当前任务状态
        if tasks[task_id]["status"] == "running":
            await manager.send_personal_message({
                "type": "task_status",
                "task_id": task_id,
                "status": tasks[task_id]["status"],
                "progress": tasks[task_id]["progress"],
                "current_node": tasks[task_id]["current_node"]
            }, connection_id)
        
        # 保持连接，接收消息
        while True:
            data = await websocket.receive_json()
            
            # 处理客户端消息
            if data.get("type") == "pause":
                # 暂停任务
                if tasks[task_id]["status"] == "running":
                    tasks[task_id]["status"] = "paused"
                    await manager.send_personal_message({
                        "type": "task_paused",
                        "task_id": task_id
                    }, connection_id)
            
            elif data.get("type") == "resume":
                # 恢复任务
                if tasks[task_id]["status"] == "paused":
                    tasks[task_id]["status"] = "running"
                    await manager.send_personal_message({
                        "type": "task_resumed",
                        "task_id": task_id
                    }, connection_id)
    
    except WebSocketDisconnect:
        # 连接断开
        manager.disconnect(connection_id)
        print(f"Client {connection_id} disconnected")
    
    except Exception as e:
        # 发生错误
        manager.disconnect(connection_id)
        print(f"Client {connection_id} error: {e}")

@app.post("/api/tasks/execute")
async def create_task(
    graph_name: str,
    initial_state: dict,
    background_tasks: BackgroundTasks
):
    """创建并执行 LangGraph 任务"""
    
    # 生成任务 ID
    task_id = f"task_{uuid.uuid4().hex[:8]}"
    
    # 启动后台任务
    background_tasks.add_task(
        execute_langgraph_task,
        task_id,
        graph_name,
        initial_state
    )
    
    return {
        "task_id": task_id,
        "status": "running",
        "ws_url": f"ws://localhost:8000/ws/tasks/{task_id}",
        "message": f"Task {task_id} started. Connect to WebSocket for real-time updates."
    }

@app.get("/api/tasks/{task_id}")
async def get_task_status(task_id: str):
    """获取任务状态（HTTP API）"""
    
    task = tasks.get(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "task_id": task["task_id"],
        "status": task["status"],
        "progress": task["progress"],
        "current_node": task["current_node"],
        "error": task["error"],
        "state": task["state"]
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "node": os.getenv("SERVICE_NAME", "unknown"),
        "active_connections": len(manager.active_connections)
    }
```

#### 客户端示例

```html
<!DOCTYPE html>
<html>
<head>
    <title>LangGraph Task Monitor</title>
</head>
<body>
    <h1>LangGraph Task Monitor</h1>
    
    <div>
        <label>Task ID:</label>
        <input type="text" id="taskId" placeholder="task_abc123">
        <button onclick="connect()">Connect</button>
        <button onclick="disconnect()">Disconnect</button>
    </div>
    
    <div id="output">
        <h2>Task Status</h2>
        <pre id="status"></pre>
        
        <h2>Messages</h2>
        <ul id="messages"></ul>
    </div>
    
    <script>
        let ws = null;
        const taskIdInput = document.getElementById('taskId');
        const statusOutput = document.getElementById('status');
        const messagesOutput = document.getElementById('messages');
        
        function connect() {
            const taskId = taskIdInput.value;
            if (!taskId) {
                alert('Please enter a task ID');
                return;
            }
            
            ws = new WebSocket(`ws://localhost:8000/ws/tasks/${taskId}`);
            
            ws.onopen = function() {
                addMessage('Connected to task: ' + taskId);
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                
                if (data.type === 'progress' || 
                    data.type === 'task_status' ||
                    data.type === 'task_completed') {
                    statusOutput.textContent = JSON.stringify(data, null, 2);
                }
                
                addMessage(`${data.type}: ${JSON.stringify(data)}`);
            };
            
            ws.onclose = function() {
                addMessage('Disconnected');
                ws = null;
            };
            
            ws.onerror = function(error) {
                addMessage('Error: ' + error);
            };
        }
        
        function disconnect() {
            if (ws) {
                ws.close();
            }
        }
        
        function addMessage(message) {
            const li = document.createElement('li');
            li.textContent = new Date().toISOString() + ' - ' + message;
            messagesOutput.appendChild(li);
        }
    </script>
</body>
</html>
```

---

## 📊 方案对比

| 方案 | 适用场景 | 优点 | 缺点 |
|------|----------|------|------|
| **任务 ID 哈希** | 长时间任务 | 简单，自动路由 | 节点挂了丢失状态 |
| **Redis 持久化** | 生产环境 | 支持断点恢复 | 依赖 Redis |
| **WebSocket** | 实时交互 | 实时进度推送 | 长连接开销大 |

---

## 🎯 推荐方案

### 对于 LangGraph 长时间运行任务：

**最佳组合：任务 ID 哈希 + Redis 持久化**

```
Nginx: hash $arg_task_id consistent
FastAPI: Redis 持久化任务状态
```

**原因**：
1. ✅ 同一任务路由到同一节点（减少状态传输）
2. ✅ Redis 持久化（节点挂了可以恢复）
3. ✅ 支持断点继续
4. ✅ 支持人工介入和干预

---

## 🚀 总结

### 关键要点

1. **任务 ID 是关键**：使用 task_id 进行哈希路由
2. **持久化是必须的**：Redis 保存任务状态
3. **检查点机制**：定期保存执行进度
4. **支持断点恢复**：从中断点继续执行
5. **人工干预接口**：暂停/恢复/取消

### 实施步骤

1. Nginx 配置：`hash $arg_task_id consistent`
2. FastAPI 实现：任务状态管理器（Redis）
3. 检查点机制：定期保存执行状态
4. 恢复机制：从检查点继续执行
5. API 设计：创建/查询/暂停/恢复/取消

---

**记住：对于长时间运行的任务，会话保持 + 状态持久化是必须的！** 🚀
