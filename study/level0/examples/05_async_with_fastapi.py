"""
阶段 0.5: FastAPI中的异步 - 将基础应用到实际框架

学习目标：
1. 理解FastAPI中的 endpoint 函数何时应该用 async def
2. 理解路径操作函数中的异步操作
3. 理解依赖注入中的异步
4. 理解 Background Tasks

核心概念：
- async def endpoint：FastAPI会在线程池中运行
- def endpoint：直接运行（适用于阻塞操作）
- 依赖注入也可以是异步的
- BackgroundTasks 用于后台任务

⚠️  注意：这是一个演示文件，不需要实际运行服务器
"""

from fastapi import FastAPI, BackgroundTasks, Depends
from pydantic import BaseModel
import asyncio
import time


# ============ FastAPI 应用 ============

app = FastAPI(title="FastAPI 异步示例")


# ============ 数据模型 ============

class TaskRequest(BaseModel):
    task_id: str
    duration: float


class TaskResponse(BaseModel):
    task_id: str
    status: str
    result: str


# ============ 异步 Endpoint 示例 ============

@app.get("/")
async def read_root():
    """
    ✅ 正确：异步 endpoint
    FastAPI 会在线程池中运行这个函数
    """
    await asyncio.sleep(0.1)  # 模拟异步IO操作
    return {"message": "Hello, FastAPI!"}


@app.get("/sync")
def read_sync():
    """
    ⚠️  谨慎使用：同步 endpoint
    这个函数会直接运行，如果执行慢会阻塞整个请求
    适用于：
    - 非常快的操作（< 10ms）
    - 必须使用同步库的操作
    """
    time.sleep(0.1)  # 阻塞操作，会阻塞请求
    return {"message": "Sync endpoint"}


@app.post("/tasks", response_model=TaskResponse)
async def create_task(request: TaskRequest):
    """
    ✅ 正确：异步 endpoint 处理请求
    """
    # 模拟异步操作（如数据库查询）
    await asyncio.sleep(request.duration)

    return TaskResponse(
        task_id=request.task_id,
        status="completed",
        result=f"Task {request.task_id} finished"
    )


# ============ 并发请求处理演示 ============

@app.get("/demo/concurrent-requests")
async def demo_concurrent_requests():
    """
    演示：FastAPI 如何并发处理多个请求
    """
    results = await asyncio.gather(
        async_operation("请求1", 1),
        async_operation("请求2", 1),
        async_operation("请求3", 1),
    )
    return {"results": results}


async def async_operation(name: str, duration: float) -> str:
    """模拟异步操作"""
    await asyncio.sleep(duration)
    return f"{name}完成"


# ============ 异步依赖注入 ============

async def get_db():
    """
    异步依赖：获取数据库连接
    """
    # 模拟数据库连接
    await asyncio.sleep(0.1)
    return {"db_connection": "active"}


@app.get("/items/")
async def read_items(db: dict = Depends(get_db)):
    """
    使用异步依赖注入
    FastAPI 会自动 await 这个依赖
    """
    return {
        "message": "Items retrieved",
        "db_status": db["db_connection"]
    }


# ============ Background Tasks ============

def send_email(email: str, message: str):
    """
    后台任务：发送邮件
    注意：这是一个同步函数，会在后台线程池中执行
    """
    time.sleep(2)  # 模拟发送邮件的耗时操作
    print(f"📧 邮件已发送到 {email}: {message}")


@app.post("/notify/")
async def send_notification(
    email: str,
    message: str,
    background_tasks: BackgroundTasks
):
    """
    使用 BackgroundTasks 执行后台任务
    适用于：
    - 发送邮件
    - 写日志
    - 清理缓存
    - 其他不需要等待完成的操作
    """
    background_tasks.add_task(send_email, email, message)
    return {"message": "通知已加入后台任务队列"}


# ============ 异步生成器（Streaming） ============

@app.get("/stream")
async def stream_data():
    """
    演示：流式响应（Server-Sent Events）
    """
    async def generate():
        for i in range(5):
            await asyncio.sleep(0.5)
            yield f"data: 消息 {i}\n\n"

    return generate()


# ============ 关键要点总结 ============

@app.get("/guide")
async def async_guide():
    """
    FastAPI 中使用异步的指南
    """
    guide = {
        "title": "FastAPI 异步使用指南",
        "rules": [
            {
                "规则": "何时使用 async def",
                "说明": "当你的 endpoint 需要执行异步操作时（await）",
                "示例": "await asyncio.sleep(), await db.execute(), await client.get()"
            },
            {
                "规则": "何时使用 def",
                "说明": "当你的 endpoint 只执行快速操作，或必须使用阻塞的同步库时",
                "示例": "简单的计算、读取内存中的数据"
            },
            {
                "规则": "依赖注入",
                "说明": "依赖函数也可以是异步的，FastAPI 会自动处理",
                "示例": "async def get_db() -> Connection"
            },
            {
                "规则": "后台任务",
                "说明": "使用 BackgroundTasks 执行不需要立即完成的操作",
                "示例": "发送邮件、写日志、清理缓存"
            },
            {
                "规则": "避免阻塞",
                "说明": "在 async def 中避免使用阻塞操作",
                "正确": "await asyncio.sleep()",
                "错误": "time.sleep()"
            }
        ],
        "performance_tips": [
            "FastAPI 默认并发处理请求，异步操作不会互相阻塞",
            "使用 async def 可以让单个请求内的多个IO并发",
            "对于CPU密集型任务，考虑使用任务队列（Celery、RQ等）",
            "使用异步库：httpx（替代requests）、aiofiles（文件IO）"
        ]
    }
    return guide


# ============ 演示说明 ============

"""
🚀 如何运行这个示例：

1. 保存文件为 main.py
2. 安装依赖：pip install fastapi uvicorn
3. 启动服务器：
   uvicorn main:app --reload

4. 访问文档：http://localhost:8000/docs

5. 测试不同的端点：
   - GET /              # 异步 endpoint
   - GET /sync          # 同步 endpoint
   - POST /tasks        # 异步处理请求
   - GET /demo/concurrent-requests  # 并发请求演示

💡 观察要点：
- 异步 endpoint 可以并发处理多个请求
- 即使在单个请求内，也可以并发执行多个异步操作
- 异步依赖注入会被 FastAPI 自动处理
- BackgroundTasks 允许在响应返回后继续执行任务

⚠️  常见错误：
1. 在 async def 中使用 time.sleep()（阻塞）
2. 在 async def 中使用 requests（阻塞）
3. 忘记 await 异步函数
4. 在同步代码中直接调用协程函数
"""


def main():
    """打印使用说明"""
    print("\n" + "="*50)
    print("🎓 阶段 0.5: FastAPI中的异步")
    print("="*50)
    print("\n这是一个 FastAPI 应用的配置示例，包含多个异步 endpoint")
    print("\n🚀 运行方式：")
    print("  1. 安装依赖: pip install fastapi uvicorn")
    print("  2. 启动服务: uvicorn app.examples.05_async_with_fastapi:app --reload")
    print("  3. 访问文档: http://localhost:8000/docs")
    print("\n💡 这个文件演示了：")
    print("  - 异步 endpoint (async def)")
    print("  - 同步 endpoint (def)")
    print("  - 异步依赖注入")
    print("  - Background Tasks")
    print("  - 流式响应")
    print("="*50 + "\n")


if __name__ == "__main__":
    main()
