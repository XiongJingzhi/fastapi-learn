"""
方案 2：任务 ID 哈希 + Redis 持久化（推荐用于生产）

这个示例展示如何处理 LangGraph 等长时间运行任务，
支持任务暂停、恢复、取消，以及断点恢复。

适用场景：
- LangGraph 图执行
- 数据处理流水线
- 长时间运行的异步任务
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import aioredis
import asyncio
import uuid
import time
import json
import os
from typing import Optional, Dict, Any
from datetime import datetime

app = FastAPI()

# 配置
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
SERVICE_NAME = os.getenv("SERVICE_NAME", "unknown")

# Redis 连接
redis_client = None

# 模拟 LangGraph 图定义
LANGGRAPH_GRAPHS = {
    "data_pipeline": {
        "nodes": ["fetch", "transform", "validate", "save"],
        "edges": [
            ("fetch", "transform"),
            ("transform", "validate"),
            ("validate", "save")
        ]
    },
    "ml_pipeline": {
        "nodes": ["load_data", "preprocess", "train", "evaluate"],
        "edges": [
            ("load_data", "preprocess"),
            ("preprocess", "train"),
            ("train", "evaluate")
        ]
    }
}

async def get_redis():
    """获取 Redis 连接"""
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
    initial_state: Dict[str, Any]

class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str

# 任务状态管理器
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
            86400,  # 24 小时过期
            json.dumps(state)
        )
        
        # 保存到任务列表
        await self.redis.sadd("tasks:all", task_id)
        await self.redis.expire("tasks:all", 86400)
    
    async def load_task_state(self, task_id: str) -> Optional[dict]:
        """从 Redis 加载任务状态"""
        key = f"task:{task_id}"
        data = await self.redis.get(key)
        if data:
            return json.loads(data)
        return None
    
    async def delete_task_state(self, task_id: str):
        """删除任务状态"""
        key = f"task:{task_id}"
        await self.redis.delete(key)
        await self.redis.srem("tasks:all", task_id)
    
    async def list_all_tasks(self) -> list:
        """列出所有任务"""
        task_ids = await self.redis.smembers("tasks:all")
        tasks = []
        for task_id in task_ids:
            state = await self.load_task_state(task_id)
            if state:
                tasks.append({
                    "task_id": state["task_id"],
                    "status": state["status"],
                    "progress": state["progress"],
                    "created_at": state["created_at"]
                })
        return tasks

# 任务状态管理器
task_manager = TaskStateManager()

# 模拟 LangGraph 节点执行
async def execute_node(
    task_id: str,
    node_name: str,
    state: dict,
    task_manager: TaskStateManager
) -> dict:
    """执行单个节点（模拟 LangGraph 节点）"""
    
    print(f"[{task_id}] Executing node: {node_name}")
    
    # 更新当前节点
    state["current_node"] = node_name
    await task_manager.save_task_state(task_id, state)
    
    # 模拟节点执行时间
    if node_name == "fetch":
        await asyncio.sleep(5)  # 5 秒
        state["state"]["data"] = f"fetched_data_{time.time()}"
        state["checkpoint"] = "fetch_completed"
    
    elif node_name == "transform":
        await asyncio.sleep(10)  # 10 秒
        state["state"]["transformed"] = f"transformed_{time.time()}"
        state["checkpoint"] = "transform_completed"
    
    elif node_name == "validate":
        await asyncio.sleep(3)  # 3 秒
        state["state"]["validated"] = True
        state["checkpoint"] = "validate_completed"
    
    elif node_name == "save":
        await asyncio.sleep(2)  # 2 秒
        state["state"]["saved"] = True
        state["checkpoint"] = "save_completed"
    
    elif node_name == "load_data":
        await asyncio.sleep(5)
        state["state"]["data"] = f"loaded_data_{time.time()}"
        state["checkpoint"] = "load_data_completed"
    
    elif node_name == "preprocess":
        await asyncio.sleep(8)
        state["state"]["preprocessed"] = f"preprocessed_{time.time()}"
        state["checkpoint"] = "preprocess_completed"
    
    elif node_name == "train":
        await asyncio.sleep(15)
        state["state"]["model"] = f"model_{time.time()}"
        state["checkpoint"] = "train_completed"
    
    elif node_name == "evaluate":
        await asyncio.sleep(5)
        state["state"]["accuracy"] = 0.95
        state["checkpoint"] = "evaluate_completed"
    
    # 更新进度
    progress_map = {
        "fetch": 10,
        "transform": 40,
        "validate": 60,
        "save": 80,
        "load_data": 10,
        "preprocess": 30,
        "train": 60,
        "evaluate": 90
    }
    state["progress"] = progress_map.get(node_name, 0)
    
    # 保存检查点
    await task_manager.save_task_state(task_id, state)
    
    print(f"[{task_id}] Node {node_name} completed")
    
    return state

async def execute_langgraph_task(
    task_id: str,
    request: TaskRequest,
    task_manager: TaskStateManager
):
    """执行 LangGraph 任务（支持断点恢复）"""
    
    try:
        # 1. 加载或初始化任务状态
        existing_state = await task_manager.load_task_state(task_id)
        
        if existing_state:
            # 从现有状态恢复
            state = existing_state
            print(f"[{task_id}] Resuming task from checkpoint: {state.get('checkpoint')}")
            
            # 如果任务已完成，直接返回
            if state["status"] == "completed":
                return
            
            # 如果任务失败了，从头开始
            if state["status"] == "failed":
                state = {
                    "task_id": task_id,
                    "status": "running",
                    "graph_name": request.graph_name,
                    "state": request.initial_state.copy(),
                    "progress": 0,
                    "current_node": "start",
                    "error": None,
                    "created_at": existing_state["created_at"],
                    "updated_at": time.time(),
                    "checkpoint": None
                }
        else:
            # 新任务
            state = {
                "task_id": task_id,
                "status": "running",
                "graph_name": request.graph_name,
                "state": request.initial_state.copy(),
                "progress": 0,
                "current_node": "start",
                "error": None,
                "created_at": time.time(),
                "updated_at": time.time(),
                "checkpoint": None
            }
        
        await task_manager.save_task_state(task_id, state)
        
        # 2. 获取图定义
        graph = LANGGRAPH_GRAPHS.get(request.graph_name)
        if not graph:
            raise ValueError(f"Unknown graph: {request.graph_name}")
        
        # 3. 确定起始节点（从检查点恢复）
        start_node = None
        if state.get("checkpoint"):
            # 从检查点继续
            checkpoint = state["checkpoint"]
            
            # 查找下一个节点
            for i, (from_node, to_node) in enumerate(graph["edges"]):
                if f"{from_node}_completed" == checkpoint:
                    start_node = to_node
                    break
            
            if not start_node:
                # 检查点已是最新的节点，从头开始
                start_node = graph["nodes"][0]
        else:
            # 从头开始
            start_node = graph["nodes"][0]
        
        print(f"[{task_id}] Starting from node: {start_node}")
        
        # 4. 执行图节点
        for node in graph["nodes"]:
            # 跳过已经完成的节点
            if state.get("checkpoint") and node != start_node:
                print(f"[{task_id}] Skipping completed node: {node}")
                continue
            
            # 检查是否需要暂停
            if state.get("status") == "paused":
                print(f"[{task_id}] Task paused at node: {node}")
                break
            
            # 执行节点
            state = await execute_node(task_id, node, state, task_manager)
        
        # 5. 任务完成
        if state["status"] == "running":
            state["status"] = "completed"
            state["progress"] = 100
            state["checkpoint"] = "completed"
            state["updated_at"] = time.time()
            await task_manager.save_task_state(task_id, state)
            print(f"[{task_id}] Task completed!")
        
    except Exception as e:
        # 6. 任务失败
        state["status"] = "failed"
        state["error"] = str(e)
        state["updated_at"] = time.time()
        await task_manager.save_task_state(task_id, state)
        print(f"[{task_id}] Task failed: {e}")

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    await task_manager.init()
    print(f"Task state manager initialized (Service: {SERVICE_NAME})")

# API 端点
@app.post("/api/tasks/execute")
async def create_task(
    request: TaskRequest,
    background_tasks: BackgroundTasks
) -> TaskResponse:
    """创建并执行 LangGraph 任务"""
    
    # 验证图名称
    if request.graph_name not in LANGGRAPH_GRAPHS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown graph name: {request.graph_name}. Available: {list(LANGGRAPH_GRAPHS.keys())}"
        )
    
    # 生成任务 ID
    task_id = f"task_{uuid.uuid4().hex[:8]}"
    
    # 启动后台任务
    background_tasks.add_task(
        execute_langgraph_task,
        task_id,
        request,
        task_manager
    )
    
    return TaskResponse(
        task_id=task_id,
        status="running",
        message=f"Task {task_id} started. Graph: {request.graph_name}"
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
        "checkpoint": state["checkpoint"],
        "error": state["error"],
        "state": state["state"],
        "created_at": state["created_at"],
        "updated_at": state["updated_at"],
        "node": SERVICE_NAME
    }

@app.post("/api/tasks/{task_id}/pause")
async def pause_task(task_id: str):
    """暂停任务"""
    
    state = await task_manager.load_task_state(task_id)
    
    if not state:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if state["status"] != "running":
        raise HTTPException(
            status_code=400,
            detail=f"Task is not running (status: {state['status']})"
        )
    
    state["status"] = "paused"
    state["updated_at"] = time.time()
    await task_manager.save_task_state(task_id, state)
    
    return {
        "message": f"Task {task_id} paused",
        "checkpoint": state["checkpoint"]
    }

@app.post("/api/tasks/{task_id}/resume")
async def resume_task(
    task_id: str,
    background_tasks: BackgroundTasks
):
    """恢复任务（从检查点继续）"""
    
    state = await task_manager.load_task_state(task_id)
    
    if not state:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if state["status"] not in ["paused", "failed"]:
        raise HTTPException(
            status_code=400,
            detail=f"Task cannot be resumed (status: {state['status']})"
        )
    
    # 恢复任务（从检查点继续）
    state["status"] = "running"
    state["error"] = None
    state["updated_at"] = time.time()
    await task_manager.save_task_state(task_id, state)
    
    # 重新启动后台任务（从断点继续）
    background_tasks.add_task(
        execute_langgraph_task,
        task_id,
        TaskRequest(
            graph_name=state["graph_name"],
            initial_state=state["state"]
        ),
        task_manager
    )
    
    return {
        "message": f"Task {task_id} resumed",
        "checkpoint": state["checkpoint"]
    }

@app.post("/api/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    """取消任务"""
    
    state = await task_manager.load_task_state(task_id)
    
    if not state:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if state["status"] not in ["running", "paused"]:
        raise HTTPException(
            status_code=400,
            detail=f"Task cannot be cancelled (status: {state['status']})"
        )
    
    state["status"] = "cancelled"
    state["updated_at"] = time.time()
    await task_manager.save_task_state(task_id, state)
    
    return {"message": f"Task {task_id} cancelled"}

@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str):
    """删除任务"""
    
    state = await task_manager.load_task_state(task_id)
    
    if not state:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if state["status"] == "running":
        raise HTTPException(
            status_code=400,
            detail="Cannot delete running task. Please cancel it first."
        )
    
    await task_manager.delete_task_state(task_id)
    
    return {"message": f"Task {task_id} deleted"}

@app.get("/api/tasks")
async def list_tasks():
    """列出所有任务"""
    
    tasks = await task_manager.list_all_tasks()
    
    return {"tasks": tasks}

@app.get("/api/graphs")
async def list_graphs():
    """列出可用的图"""
    
    return {
        "graphs": [
            {
                "name": graph_name,
                "nodes": graph["nodes"],
                "edges": graph["edges"]
            }
            for graph_name, graph in LANGGRAPH_GRAPHS.items()
        ]
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    
    try:
        redis = await get_redis()
        await redis.ping()
        
        # 统计活跃任务
        tasks = await task_manager.list_all_tasks()
        active_tasks = len([t for t in tasks if t["status"] == "running"])
        
        return {
            "status": "healthy",
            "service": SERVICE_NAME,
            "active_tasks": active_tasks,
            "total_tasks": len(tasks)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": SERVICE_NAME,
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
