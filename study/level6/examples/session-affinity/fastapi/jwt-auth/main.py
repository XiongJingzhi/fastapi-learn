"""
方案 3：JWT + 本地缓存

这个示例展示如何使用 JWT 实现无状态认证，并结合本地缓存优化性能。
"""

from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import jwt
import hashlib
from typing import Optional, Dict
from datetime import datetime, timedelta
import json

app = FastAPI()

# JWT 配置
SECRET_KEY = "your-secret-key-change-this-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 模拟用户数据库
users_db = {
    "1": {"id": "1", "username": "admin", "email": "admin@example.com"},
    "2": {"id": "2", "username": "user", "email": "user@example.com"}
}

# 本地缓存（每个节点独立）
# key: user_id:resource, value: data_dict
local_cache: Dict[str, dict] = {}

class LoginRequest(BaseModel):
    username: str
    password: str

class CacheItem(BaseModel):
    key: str
    value: dict
    ttl: int = 300  # 默认 5 分钟

# JWT 认证
security = HTTPBearer()

def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """验证 JWT Token"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # 检查过期时间
        exp = payload.get("exp")
        if exp and exp < datetime.utcnow().timestamp():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )
        
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

def create_access_token(data: dict) -> str:
    """创建 JWT Token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_cache_key(user_id: str, resource: str) -> str:
    """生成缓存键"""
    return f"{user_id}:{resource}"

# API 端点
@app.post("/api/login")
async def login(request_data: LoginRequest):
    """用户登录"""
    # 验证用户名密码
    user = None
    for uid, user_data in users_db.items():
        if user_data["username"] == request_data.username:
            user = user_data
            break
    
    if not user or request_data.password != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # 生成 JWT
    access_token = create_access_token(
        data={
            "sub": user["id"],
            "username": user["username"],
            "email": user["email"]
        }
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@app.get("/api/users/me")
async def get_current_user(
    request: Request,
    payload: dict = Depends(verify_token)
):
    """获取当前用户信息"""
    user_id = payload.get("sub")
    user = users_db.get(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "user": user,
        "service": os.getenv("SERVICE_NAME", "unknown"),
        "cache_level": "none"
    }

@app.get("/api/users/{user_id}/data")
async def get_user_data(
    user_id: str,
    resource: str,
    payload: dict = Depends(verify_token)
):
    """获取用户数据（支持本地缓存）"""
    cache_key = get_cache_key(user_id, resource)
    
    # 检查本地缓存
    if cache_key in local_cache:
        print(f"Local cache hit: {cache_key}")
        return {
            "data": local_cache[cache_key],
            "cache_level": "local",
            "service": os.getenv("SERVICE_NAME", "unknown")
        }
    
    # 缓存未命中，模拟从数据库获取
    print(f"Cache miss: {cache_key}, fetching from database")
    data = {
        "user_id": user_id,
        "resource": resource,
        "timestamp": datetime.now().isoformat(),
        "data": "some_data"
    }
    
    # 写入本地缓存
    local_cache[cache_key] = data
    
    return {
        "data": data,
        "cache_level": "database",
        "service": os.getenv("SERVICE_NAME", "unknown")
    }

@app.post("/api/users/{user_id}/cache")
async def set_user_cache(
    user_id: str,
    item: CacheItem,
    payload: dict = Depends(verify_token)
):
    """设置用户缓存数据"""
    cache_key = get_cache_key(user_id, item.key)
    local_cache[cache_key] = item.value
    
    # 这里可以设置 TTL（简单实现）
    # 生产环境应该使用专门的缓存库
    
    return {
        "message": "Cache updated",
        "cache_key": cache_key,
        "service": os.getenv("SERVICE_NAME", "unknown")
    }

@app.delete("/api/users/{user_id}/cache")
async def clear_user_cache(
    user_id: str,
    key: Optional[str] = None,
    payload: dict = Depends(verify_token)
):
    """清除用户缓存"""
    if key:
        # 清除特定缓存
        cache_key = get_cache_key(user_id, key)
        if cache_key in local_cache:
            del local_cache[cache_key]
    else:
        # 清除用户所有缓存
        prefix = f"{user_id}:"
        keys_to_delete = [k for k in local_cache.keys() if k.startswith(prefix)]
        for k in keys_to_delete:
            del local_cache[k]
    
    return {
        "message": "Cache cleared",
        "service": os.getenv("SERVICE_NAME", "unknown")
    }

@app.get("/api/cache/stats")
async def get_cache_stats():
    """获取缓存统计"""
    return {
        "total_keys": len(local_cache),
        "keys": list(local_cache.keys()),
        "service": os.getenv("SERVICE_NAME", "unknown")
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": os.getenv("SERVICE_NAME", "unknown")
    }

if __name__ == "__main__":
    import os
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
