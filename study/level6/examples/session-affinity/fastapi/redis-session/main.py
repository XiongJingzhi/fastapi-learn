"""
方案 4：Redis 共享会话

这个示例展示如何使用 Redis 存储会话，实现多节点间会话共享。
"""

from fastapi import FastAPI, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel
import aioredis
import uuid
import json
from typing import Optional, Dict
import os

app = FastAPI()

# Redis 配置
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
SESSION_EXPIRE_SECONDS = 3600  # 1 小时

# Redis 连接
redis_client = None

async def get_redis():
    """获取 Redis 连接"""
    global redis_client
    if redis_client is None:
        if REDIS_PASSWORD:
            redis_client = await aioredis.from_url(
                f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}",
                encoding="utf-8",
                decode_responses=True
            )
        else:
            redis_client = await aioredis.from_url(
                f"redis://{REDIS_HOST}:{REDIS_PORT}",
                encoding="utf-8",
                decode_responses=True
            )
    return redis_client

# Session 中间件
@app.middleware("http")
async def session_middleware(request: Request, call_next):
    """Session 管理中间件"""
    redis = await get_redis()
    
    # 获取或创建 Session ID
    session_id = request.cookies.get("session_id")
    
    if not session_id:
        # 创建新 Session
        session_id = str(uuid.uuid4())
        request.state.session = {}
        request.state.is_new_session = True
    else:
        # 加载现有 Session
        session_data = await redis.get(f"session:{session_id}")
        if session_data:
            try:
                request.state.session = json.loads(session_data)
            except json.JSONDecodeError:
                request.state.session = {}
        else:
            request.state.session = {}
        request.state.is_new_session = False
    
    # 处理请求
    response = await call_next(request)
    
    # 保存 Session
    if request.state.session:
        await redis.setex(
            f"session:{session_id}",
            SESSION_EXPIRE_SECONDS,
            json.dumps(request.state.session)
        )
    
    # 设置 Cookie
    if request.state.is_new_session:
        response.set_cookie(
            key="session_id",
            value=session_id,
            max_age=SESSION_EXPIRE_SECONDS,
            httponly=True,
            secure=False,  # 生产环境应为 True
            samesite="lax"
        )
    
    return response

def get_session(request: Request) -> dict:
    """依赖注入：获取 Session"""
    return request.state.session

# 数据模型
class LoginRequest(BaseModel):
    username: str
    password: str

class SessionItem(BaseModel):
    key: str
    value: str

# API 端点
@app.post("/api/login")
async def login(
    request_data: LoginRequest,
    session: dict = Depends(get_session)
):
    """用户登录"""
    # 模拟验证
    if request_data.username != "admin" or request_data.password != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # 在 Session 中存储用户信息
    session["user_id"] = "1"
    session["username"] = request_data.username
    session["login_time"] = datetime.now().isoformat()
    
    return {
        "message": "Login successful",
        "session": session,
        "service": os.getenv("SERVICE_NAME", "unknown")
    }

@app.get("/api/session")
async def get_session_data(session: dict = Depends(get_session)):
    """获取 Session 数据"""
    return {
        "session": session,
        "service": os.getenv("SERVICE_NAME", "unknown")
    }

@app.post("/api/session")
async def set_session_data(
    item: SessionItem,
    session: dict = Depends(get_session)
):
    """设置 Session 数据"""
    session[item.key] = item.value
    
    return {
        "message": "Session updated",
        "key": item.key,
        "value": item.value,
        "service": os.getenv("SERVICE_NAME", "unknown")
    }

@app.delete("/api/session")
async def clear_session(
    request: Request,
    session: dict = Depends(get_session)
):
    """清空 Session"""
    session.clear()
    
    # 删除 Redis 中的 Session
    session_id = request.cookies.get("session_id")
    if session_id:
        redis = await get_redis()
        await redis.delete(f"session:{session_id}")
    
    return {
        "message": "Session cleared",
        "service": os.getenv("SERVICE_NAME", "unknown")
    }

@app.post("/api/logout")
async def logout(
    request: Request,
    session: dict = Depends(get_session)
):
    """用户登出"""
    # 清空 Session
    session.clear()
    
    # 删除 Redis 中的 Session
    session_id = request.cookies.get("session_id")
    if session_id:
        redis = await get_redis()
        await redis.delete(f"session:{session_id}")
    
    response = {"message": "Logout successful"}
    
    # 清除 Cookie
    from fastapi.responses import JSONResponse
    json_response = JSONResponse(content=response)
    json_response.delete_cookie("session_id")
    
    return json_response

@app.get("/api/users/me")
async def get_current_user(session: dict = Depends(get_session)):
    """获取当前用户信息"""
    user_id = session.get("user_id")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    return {
        "user_id": user_id,
        "username": session.get("username"),
        "login_time": session.get("login_time"),
        "service": os.getenv("SERVICE_NAME", "unknown")
    }

@app.get("/api/users/{user_id}/data")
async def get_user_data(user_id: str, session: dict = Depends(get_session)):
    """获取用户数据（使用 Redis 缓存）"""
    redis = await get_redis()
    cache_key = f"user:{user_id}:data"
    
    # 从 Redis 获取数据
    data = await redis.get(cache_key)
    
    if data:
        return {
            "data": json.loads(data),
            "cache_level": "redis",
            "service": os.getenv("SERVICE_NAME", "unknown")
        }
    
    # 缓存未命中，模拟从数据库获取
    data = {
        "user_id": user_id,
        "timestamp": datetime.now().isoformat(),
        "data": "some_data"
    }
    
    # 写入 Redis 缓存
    await redis.setex(cache_key, 300, json.dumps(data))
    
    return {
        "data": data,
        "cache_level": "database",
        "service": os.getenv("SERVICE_NAME", "unknown")
    }

@app.get("/api/stats")
async def get_stats():
    """获取统计信息"""
    redis = await get_redis()
    
    # 获取所有 Session 键
    session_keys = await redis.keys("session:*")
    session_count = len(session_keys)
    
    return {
        "total_sessions": session_count,
        "service": os.getenv("SERVICE_NAME", "unknown")
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    try:
        redis = await get_redis()
        await redis.ping()
        return {
            "status": "healthy",
            "service": os.getenv("SERVICE_NAME", "unknown")
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": os.getenv("SERVICE_NAME", "unknown"),
            "error": str(e)
        }

if __name__ == "__main__":
    from datetime import datetime
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
