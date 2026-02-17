"""
方案 1：Nginx IP Hash 负载均衡

这个示例展示如何使用 Nginx 的 ip_hash 指令实现会话保持。
"""

from fastapi import FastAPI, Request
import os

app = FastAPI()

# 每个节点配置自己的服务名称
SERVICE_NAME = os.getenv("SERVICE_NAME", "unknown")

# 模拟本地会话存储（每个节点独立）
local_sessions = {}

@app.get("/")
async def root(request: Request):
    """根路径，显示当前节点"""
    return {
        "message": f"Hello from {SERVICE_NAME}",
        "service": SERVICE_NAME,
        "client_ip": request.client.host
    }

@app.get("/load-balancer-test")
async def load_balancer_test(request: Request):
    """负载均衡测试端点"""
    return {
        "service": SERVICE_NAME,
        "client_ip": request.client.host,
        "timestamp": __import__("time").time()
    }

@app.post("/api/login")
async def login(username: str, password: str, request: Request):
    """用户登录（模拟）"""
    # 模拟验证
    if username != "admin" or password != "admin":
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # 存储在本地会话
    session_id = request.client.host  # 使用 IP 作为会话 ID
    local_sessions[session_id] = {
        "username": username,
        "login_time": __import__("time").time()
    }
    
    return {
        "message": "Login successful",
        "service": SERVICE_NAME,
        "session_id": session_id
    }

@app.get("/api/session")
async def get_session(request: Request):
    """获取会话数据"""
    session_id = request.client.host
    session_data = local_sessions.get(session_id)
    
    if not session_data:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "service": SERVICE_NAME,
        "session_id": session_id,
        "session": session_data
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": SERVICE_NAME
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
