# 长时间运行任务示例（LangGraph 场景）

本目录包含专门针对 LangGraph 等长时间运行任务的会话保持实现。

---

## 🎯 场景说明

### LangGraph 长时间运行任务的特点

1. **执行时间长**：可能需要几分钟甚至几小时
2. **状态复杂**：需要保持图执行的中间状态
3. **可中断**：用户可能需要暂停、恢复、取消
4. **需要人工介入**：某些节点可能需要人工确认
5. **断点恢复**：从断点继续执行，而不是从头开始

### 问题场景

```
用户发起 LangGraph 任务
    ↓
任务开始执行
    ↓
执行到节点 3（数据确认）
    ↓
❌ 节点挂了 / 用户断开连接
    ↓
用户重新连接
    ↓
需要：
1. 路由到同一节点（如果内存中还有状态）
2. 或从持久化存储恢复状态
3. 从节点 3 继续，而不是从头开始
```

---

## 🚀 快速开始

### 方案 1：任务 ID 哈希 + 内存状态

```bash
cd long-running-tasks

# 启动服务
docker-compose -f docker-compose-task-hash.yml up -d

# 创建任务
curl -X POST http://localhost:8000/api/tasks/execute \
  -H "Content-Type: application/json" \
  -d '{
    "graph_name": "data_pipeline",
    "initial_state": {"input": "test_data"}
  }'

# 返回: {"task_id": "task_abc123", "status": "running", ...}

# 查询任务状态（使用 task_id 自动路由到同一节点）
curl http://localhost:8000/api/tasks/task_abc123

# 暂停任务
curl -X POST http://localhost:8000/api/tasks/task_abc123/pause

# 恢复任务
curl -X POST http://localhost:8000/api/tasks/task_abc123/resume
```

### 方案 2：任务 ID 哈希 + Redis 持久化

```bash
# 启动服务（包含 Redis）
docker-compose -f docker-compose-redis-persist.yml up -d

# 创建任务
curl -X POST http://localhost:8000/api/tasks/execute \
  -H "Content-Type: application/json" \
  -d '{
    "graph_name": "data_pipeline",
    "initial_state": {"input": "test_data"}
  }'

# 查询任务状态
curl http://localhost:8000/api/tasks/task_abc123

# 暂停任务
curl -X POST http://localhost:8000/api/tasks/task_abc123/pause

# 恢复任务（从 Redis 恢复状态）
curl -X POST http://localhost:8000/api/tasks/task_abc123/resume
```

### 方案 3：WebSocket 实时监控

```bash
# 启动服务
docker-compose -f docker-compose-websocket.yml up -d

# 创建任务
curl -X POST http://localhost:8000/api/tasks/execute \
  -H "Content-Type: application/json" \
  -d '{
    "graph_name": "data_pipeline",
    "initial_state": {"input": "test_data"}
  }'

# 使用 WebSocket 客户端连接
# 打开 frontend/index.html
# 输入 task_id，连接 WebSocket

# 或者使用 wscat
wscat -c "ws://localhost:8000/ws/tasks/task_abc123"
```

---

## 📁 目录结构

```
long-running-tasks/
├── task-hash/                    # 方案 1：任务 ID 哈希
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── redis-persist/                # 方案 2：Redis 持久化
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── websocket/                     # 方案 3：WebSocket
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                      # WebSocket 客户端
│   └── index.html
├── nginx/
│   ├── task-hash.conf            # 方案 1 配置
│   ├── redis-persist.conf        # 方案 2 配置
│   └── websocket.conf            # 方案 3 配置
├── docker-compose-task-hash.yml  # 方案 1 编排
├── docker-compose-redis-persist.yml  # 方案 2 编排
├── docker-compose-websocket.yml      # 方案 3 编排
└── README.md                      # 本文件
```

---

## 🔧 核心功能

### 1. 任务管理 API

```python
# 创建任务
POST /api/tasks/execute
{
    "graph_name": "data_pipeline",
    "initial_state": {"input": "test_data"}
}
→ {"task_id": "task_abc123", "status": "running", ...}

# 查询任务
GET /api/tasks/{task_id}
→ {"task_id": "task_abc123", "status": "running", "progress": 40, ...}

# 暂停任务
POST /api/tasks/{task_id}/pause
→ {"message": "Task task_abc123 paused"}

# 恢复任务
POST /api/tasks/{task_id}/resume
→ {"message": "Task task_abc123 resumed", "checkpoint": "data_processed"}

# 取消任务
POST /api/tasks/{task_id}/cancel
→ {"message": "Task task_abc123 cancelled"}

# 列出所有任务
GET /api/tasks
→ {"tasks": [{"task_id": "task_abc123", "status": "running", ...}, ...]}
```

### 2. 检查点机制

```python
# 任务执行过程中定期保存检查点
state["checkpoint"] = "data_prepared"
await task_manager.save_task_state(task_id, state)

# 恢复时从检查点继续
state = await task_manager.load_task_state(task_id)
if state.get("checkpoint") == "data_prepared":
    # 从检查点继续执行
    execute_from_checkpoint(state)
```

### 3. WebSocket 实时推送

```javascript
// 连接 WebSocket
ws = new WebSocket(`ws://localhost:8000/ws/tasks/${taskId}`);

// 接收实时进度
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    if (data.type === 'progress') {
        console.log(`Progress: ${data.progress}%`);
    }
};

// 发送控制消息
ws.send(JSON.stringify({
    "type": "pause"
}));
```

---

## 📊 性能测试

### 并发任务测试

```bash
# 创建 100 个并发任务
for i in {1..100}; do
  curl -X POST http://localhost:8000/api/tasks/execute \
    -H "Content-Type: application/json" \
    -d "{\"graph_name\": \"task_$i\", \"initial_state\": {\"input\": \"$i\"}}" &
done

wait

# 查询所有任务
curl http://localhost:8000/api/tasks | jq '.tasks | length'
```

### 任务恢复测试

```bash
# 创建任务
TASK_ID=$(curl -X POST http://localhost:8000/api/tasks/execute \
  -H "Content-Type: application/json" \
  -d '{"graph_name": "test", "initial_state": {}}' \
  -s | jq -r '.task_id')

# 等待 5 秒
sleep 5

# 暂停任务
curl -X POST http://localhost:8000/api/tasks/$TASK_ID/pause

# 停止节点（模拟故障）
docker-compose stop api-1

# 重启节点
docker-compose start api-1

# 恢复任务
curl -X POST http://localhost:8000/api/tasks/$TASK_ID/resume

# 检查是否从断点继续
curl http://localhost:8000/api/tasks/$TASK_ID | jq '.checkpoint'
```

---

## 🎯 最佳实践

### 1. 检查点频率

```python
# ✅ 推荐：在每个关键节点保存检查点
@graph.add_node("process_data")
async def process_data(state):
    # 处理数据
    processed = await process(state["data"])
    
    # 保存检查点
    state["processed"] = processed
    state["checkpoint"] = "data_processed"
    await task_manager.save_task_state(task_id, state)
    
    return state

# ❌ 不推荐：检查点过于频繁
@graph.add_node("process_item")
async def process_item(state):
    for item in items:
        # 处理每个项目
        result = await process(item)
        
        # 每个项目都保存检查点（太频繁了）
        state["checkpoint"] = f"item_{item.id}"
        await task_manager.save_task_state(task_id, state)
```

### 2. 状态大小控制

```python
# ✅ 推荐：只保存必要的状态
state = {
    "task_id": task_id,
    "status": "running",
    "checkpoint": "data_processed",
    "state": {
        # 只保存必要的中间状态
        "processed_data": data_summary,
        "metadata": metadata
    }
}

# ❌ 不推荐：保存所有中间数据
state = {
    "task_id": task_id,
    "status": "running",
    "checkpoint": "data_processed",
    "state": {
        # 保存所有原始数据（太大了）
        "raw_data": huge_dataset,
        "intermediate_results": all_intermediate_results
    }
}
```

### 3. 错误处理

```python
# ✅ 推荐：详细的错误处理
try:
    result = await execute_node(state)
except TimeoutError:
    state["status"] = "paused"
    state["error"] = "Node timeout"
    state["checkpoint"] = "node_timeout"
    await task_manager.save_task_state(task_id, state)
    
    # 通知用户
    await manager.broadcast_to_task({
        "type": "task_paused",
        "task_id": task_id,
        "reason": "Node timeout",
        "action_required": "resume_or_cancel"
    }, task_id)
except Exception as e:
    state["status"] = "failed"
    state["error"] = str(e)
    await task_manager.save_task_state(task_id, state)

# ❌ 不推荐：忽略错误
try:
    result = await execute_node(state)
except:
    pass  # 忽略所有错误
```

---

## 🚀 总结

### 关键要点

1. **任务 ID 是路由键**：使用 task_id 进行一致性哈希
2. **持久化是必须的**：Redis 保存任务状态和检查点
3. **检查点机制**：定期保存执行进度
4. **断点恢复**：从检查点继续执行
5. **实时监控**：WebSocket 推送任务进度
6. **人工干预**：暂停/恢复/取消接口

### 推荐方案

**生产环境最佳组合**：
```
Nginx: hash $arg_task_id consistent
FastAPI: Redis 持久化 + 检查点机制
前端: WebSocket 实时监控
```

---

**记住：对于长时间运行的任务，会话保持 + 状态持久化是必须的！** 🚀
