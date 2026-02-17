# 11. 会话保持（Session Affinity）

## 🎯 问题背景

在多节点部署中，默认的负载均衡策略（轮询）会将请求随机分发到不同的实例：

```
用户 A 的请求 1 → API-1
用户 A 的请求 2 → API-2  ❌ 不同节点，会话数据丢失
用户 A 的请求 3 → API-3  ❌ 缓存未命中
```

这会导致的问题：
- ❌ 会话数据无法共享
- ❌ 本地缓存失效
- ❌ 需要分布式存储会话（性能开销大）

**目标：让同一个用户的请求始终路由到同一个节点**

```
用户 A 的所有请求 → API-1  ✅ 会话保持
用户 B 的所有请求 → API-2  ✅ 会话保持
用户 C 的所有请求 → API-3  ✅ 会话保持
```

---

## 📚 解决方案对比

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **IP Hash** | 简单，无需额外配置 | 用户 IP 变化会失效 | 内网、固定 IP |
| **Cookie 路由** | 精确，支持 IP 变化 | 需要客户端支持 Cookie | Web 应用 |
| **JWT + 无状态** | 天然支持多节点 | Token 体积大 | RESTful API |
| **Redis 共享会话** | 灵活，支持节点扩容 | 依赖外部存储 | 大规模系统 |
| **一致性哈希** | 平滑扩容，数据局部性好 | 实现复杂 | 自定义路由 |

---

## 🔧 方案 1：Nginx IP Hash（推荐用于内网）

### 原理

使用客户端 IP 地址的哈希值决定路由目标。

```nginx
upstream fastapi_backend {
    # IP 哈希策略
    ip_hash;
    
    server api-1:8000;
    server api-2:8000;
    server api-3:8000;
}
```

### 配置示例

```nginx
upstream fastapi_backend {
    # IP 哈希策略
    ip_hash;
    
    server api-1:8000 max_fails=3 fail_timeout=30s;
    server api-2:8000 max_fails=3 fail_timeout=30s;
    server api-3:8000 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    
    location / {
        proxy_pass http://fastapi_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### 优点
- ✅ 配置简单，一行代码即可
- ✅ 无需客户端支持
- ✅ 自动保持会话

### 缺点
- ❌ 用户 IP 变化会失效（如 NAT 环境、移动网络）
- ❌ 新增/删除节点会导致大量用户重新路由
- ❌ 不适合大规模节点数（哈希分布不均）

### 测试

```bash
# 使用 curl -J 模拟同一 IP 的多个请求
curl http://localhost:8000/load-balancer-test
curl http://localhost:8000/load-balancer-test
curl http://localhost:8000/load-balancer-test

# 观察返回的 service_name 是否一致
```

---

## 🔧 方案 2：Cookie-based 路由（推荐用于 Web 应用）

### 原理

在用户第一次请求时，在 Cookie 中写入目标节点标识。后续请求根据 Cookie 路由。

### Nginx 配置

```nginx
upstream fastapi_backend {
    server api-1:8000;
    server api-2:8000;
    server api-3:8000;
}

# 负载均衡器需要第三方模块：ngx_http_upstream_module
# 或者使用 nginx-sticky-module

# 方式 1：使用 sticky module（推荐）
upstream fastapi_backend {
    sticky cookie srv_id expires=1h domain=.example.com path=/;
    
    server api-1:8000 srv_id=api1;
    server api-2:8000 srv_id=api2;
    server api-3:8000 srv_id=api3;
}

# 方式 2：使用 hash + map（无第三方模块）
map $cookie_backend $backend_server {
    default $upstream;
    "api1"  "api-1:8000";
    "api2"  "api-2:8000";
    "api3"  "api-3:8000";
}

server {
    listen 80;
    
    location / {
        # 如果 Cookie 存在，直接路由
        if ($cookie_backend) {
            proxy_pass http://$backend_server;
        }
        
        # 否则使用默认负载均衡
        proxy_pass http://fastapi_backend;
        
        # 设置 Cookie（由后端处理）
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### FastAPI 设置 Cookie

```python
from fastapi import FastAPI, Response
import random

app = FastAPI()

SERVER_NODES = ["api1", "api2", "api3"]
CURRENT_NODE = "api1"  # 每个节点配置自己的 ID

@app.get("/")
async def root(response: Response):
    # 设置路由 Cookie
    response.set_cookie(
        key="backend",
        value=CURRENT_NODE,
        max_age=3600,  # 1 小时
        httponly=True,
        secure=False,  # 生产环境应为 True
        samesite="lax"
    )
    
    return {
        "message": f"Hello from {CURRENT_NODE}",
        "node": CURRENT_NODE
    }
```

### 安装 Nginx Sticky Module

```bash
# Ubuntu/Debian
sudo apt-get install libnginx-mod-http-sticky

# CentOS/RHEL
sudo yum install nginx-module-sticky

# 或从源码编译
wget https://bitbucket.org/nginx-goodies/nginx-sticky-module-ng/get/master.tar.gz
tar -xzvf master.tar.gz
cd nginx-1.x.x
./configure --add-module=/path/to/nginx-sticky-module-ng
make && make install
```

### 优点
- ✅ 精确控制路由
- ✅ 用户 IP 变化不影响
- ✅ 可以手动切换节点

### 缺点
- ❌ 需要客户端支持 Cookie
- ❌ 需要第三方 Nginx 模块（sticky module）
- ❌ Cookie 泄露风险（需要 secure 和 httponly）

---

## 🔧 方案 3：JWT + 本地缓存（推荐用于 API）

### 原理

使用 JWT 无状态认证，同时在每个节点维护本地缓存。虽然 JWT 可以跨节点使用，但通过缓存优化性能。

### 架构设计

```
用户请求 → Nginx（轮询）→ 任意节点
                           ↓
                        验证 JWT
                           ↓
        ┌──────────────────┴──────────────────┐
        ↓                  ↓                  ↓
    检查本地缓存        检查本地缓存        检查本地缓存
        ↓                  ↓                  ↓
    缓存命中？          缓存命中？          缓存命中？
        ↓                  ↓                  ↓
    返回数据            返回数据            返回数据
        ↓                  ↓                  ↓
    更新缓存            更新缓存            更新缓存
```

### 实现

```python
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import aioredis
from typing import Optional
import hashlib
from datetime import datetime, timedelta

app = FastAPI()

# JWT 配置
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 本地缓存（内存 + Redis）
local_cache: dict = {}

# Redis 连接
redis_client = None

async def get_redis():
    global redis_client
    if redis_client is None:
        redis_client = await aioredis.from_url(
            "redis://redis:6379",
            encoding="utf-8",
            decode_responses=True
        )
    return redis_client

# JWT 认证
security = HTTPBearer()

async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# 一致性哈希路由
def get_cache_key(user_id: int, resource: str) -> str:
    """生成缓存键，确保同一用户在同一节点上的缓存键一致"""
    return f"user:{user_id}:{resource}"

# 两级缓存：本地缓存 + Redis
async def get_user_data(user_id: int, resource: str) -> Optional[dict]:
    """获取用户数据（本地缓存 + Redis）"""
    cache_key = get_cache_key(user_id, resource)
    
    # 1. 检查本地缓存
    if cache_key in local_cache:
        print(f"Local cache hit: {cache_key}")
        return local_cache[cache_key]
    
    # 2. 检查 Redis
    redis = await get_redis()
    data = await redis.get(cache_key)
    
    if data:
        print(f"Redis cache hit: {cache_key}")
        data_dict = eval(data)
        # 更新本地缓存
        local_cache[cache_key] = data_dict
        return data_dict
    
    # 3. 缓存未命中，从数据库获取
    print(f"Cache miss: {cache_key}, fetching from database")
    data = await fetch_from_database(user_id, resource)
    
    # 4. 写入缓存
    local_cache[cache_key] = data
    await redis.setex(cache_key, 300, str(data))  # 5 分钟过期
    
    return data

async def fetch_from_database(user_id: int, resource: str) -> dict:
    """模拟从数据库获取数据"""
    # 这里应该是实际的数据库查询
    return {"user_id": user_id, resource: "data", "timestamp": datetime.now().isoformat()}

# API 端点
@app.get("/api/users/me")
async def get_current_user(
    request: Request,
    payload: dict = Depends(verify_token)
):
    """获取当前用户信息"""
    user_id = payload.get("sub")
    
    # 获取用户数据（两级缓存）
    user_data = await get_user_data(user_id, "profile")
    
    return {
        "user": user_data,
        "node": request.headers.get("X-Service-Name", "unknown"),
        "cache_level": "local"
    }

@app.post("/api/login")
async def login(username: str, password: str, response: Response):
    """用户登录"""
    # 验证用户名密码
    if username != "admin" or password != "password":
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # 生成 JWT
    access_token = jwt.encode(
        {
            "sub": "1",  # user_id
            "username": username,
            "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        },
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    
    # 清空该用户的缓存
    user_id = 1
    for key in list(local_cache.keys()):
        if key.startswith(f"user:{user_id}"):
            del local_cache[key]
    
    redis = await get_redis()
    await redis.delete(*[f"user:{user_id}:*"])
    
    return {"access_token": access_token, "token_type": "bearer"}
```

### 优点
- ✅ JWT 天然支持多节点
- ✅ 两级缓存（本地 + Redis）提升性能
- ✅ 无状态，易于扩展
- ✅ 不依赖会话保持

### 缺点
- ❌ Token 体积大
- ❌ 无法主动撤销 Token（需要黑名单）
- ❌ 本地缓存可能导致数据不一致

---

## 🔧 方案 4：Redis 共享会话（推荐用于传统 Web 应用）

### 原理

将所有会话数据存储在 Redis 中，所有节点共享同一个会话存储。

### 实现

```python
from fastapi import FastAPI, Request, Response
import uuid
import aioredis
import json
from datetime import datetime, timedelta

app = FastAPI()

# Redis 配置
redis_client = None
SESSION_EXPIRE_SECONDS = 3600  # 1 小时

async def get_redis():
    global redis_client
    if redis_client is None:
        redis_client = await aioredis.from_url(
            "redis://redis:6379",
            encoding="utf-8",
            decode_responses=True
        )
    return redis_client

# Session 中间件
@app.middleware("http")
async def session_middleware(request: Request, call_next):
    """Session 管理中间件"""
    
    # 获取或创建 Session ID
    session_id = request.cookies.get("session_id")
    
    if not session_id:
        # 创建新 Session
        session_id = str(uuid.uuid4())
        request.state.session = {}
        request.state.is_new_session = True
    else:
        # 加载现有 Session
        redis = await get_redis()
        session_data = await redis.get(f"session:{session_id}")
        request.state.session = json.loads(session_data) if session_data else {}
        request.state.is_new_session = False
    
    # 处理请求
    response = await call_next(request)
    
    # 保存 Session
    redis = await get_redis()
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

# 获取 Session
def get_session(request: Request) -> dict:
    return request.state.session

# API 端点
@app.get("/api/session")
async def get_session_data(session: dict = Depends(get_session)):
    """获取 Session 数据"""
    return {"session": session}

@app.post("/api/session")
async def set_session_data(
    key: str,
    value: str,
    session: dict = Depends(get_session)
):
    """设置 Session 数据"""
    session[key] = value
    return {"message": "Session updated", "key": key, "value": value}

@app.delete("/api/session")
async def clear_session(request: Request, session: dict = Depends(get_session)):
    """清空 Session"""
    session.clear()
    return {"message": "Session cleared"}

@app.post("/api/login")
async def login(username: str, password: str, session: dict = Depends(get_session)):
    """用户登录"""
    if username != "admin" or password != "admin":
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # 在 Session 中存储用户信息
    session["user_id"] = "1"
    session["username"] = username
    session["login_time"] = datetime.now().isoformat()
    
    return {"message": "Login successful", "session": session}

@app.post("/api/logout")
async def logout(request: Request, session: dict = Depends(get_session)):
    """用户登出"""
    session.clear()
    
    # 删除 Redis 中的 Session
    session_id = request.cookies.get("session_id")
    if session_id:
        redis = await get_redis()
        await redis.delete(f"session:{session_id}")
    
    return {"message": "Logout successful"}
```

### 优点
- ✅ 所有节点共享会话数据
- ✅ 支持节点动态扩缩容
- ✅ Session 持久化
- ✅ 易于实现

### 缺点
- ❌ 依赖外部存储（Redis）
- ❌ 网络开销（每次请求都需要访问 Redis）
- ❌ Redis 故障会影响所有会话

---

## 🔧 方案 5：一致性哈希（推荐用于自定义路由）

### 原理

使用一致性哈希算法，根据用户 ID 或其他标识符计算目标节点。新加入或删除节点时，只需重新路由少量用户。

### 实现

```python
import hashlib
from typing import List, Dict

class ConsistentHashing:
    """一致性哈希路由器"""
    
    def __init__(self, nodes: List[str], virtual_nodes: int = 150):
        """
        初始化一致性哈希
        
        Args:
            nodes: 节点列表
            virtual_nodes: 每个节点的虚拟节点数（越多分布越均匀）
        """
        self.nodes = nodes
        self.virtual_nodes = virtual_nodes
        self.ring: Dict[int, str] = {}
        self.sorted_keys: List[int] = []
        
        self._build_ring()
    
    def _hash(self, key: str) -> int:
        """计算哈希值"""
        return int(hashlib.md5(key.encode()).hexdigest(), 16)
    
    def _build_ring(self):
        """构建哈希环"""
        self.ring.clear()
        self.sorted_keys.clear()
        
        for node in self.nodes:
            # 为每个节点创建虚拟节点
            for i in range(self.virtual_nodes):
                virtual_node_key = f"{node}:{i}"
                hash_value = self._hash(virtual_node_key)
                self.ring[hash_value] = node
                self.sorted_keys.append(hash_value)
        
        # 排序哈希键
        self.sorted_keys.sort()
    
    def get_node(self, key: str) -> str:
        """根据键获取目标节点"""
        if not self.ring:
            return None
        
        hash_value = self._hash(key)
        
        # 找到第一个大于等于 hash_value 的节点
        for ring_key in self.sorted_keys:
            if ring_key >= hash_value:
                return self.ring[ring_key]
        
        # 如果没找到，返回第一个节点（环形）
        return self.ring[self.sorted_keys[0]]
    
    def add_node(self, node: str):
        """添加节点"""
        self.nodes.append(node)
        self._build_ring()
    
    def remove_node(self, node: str):
        """删除节点"""
        if node in self.nodes:
            self.nodes.remove(node)
            self._build_ring()


# 使用示例
class SessionRouter:
    """会话路由器"""
    
    def __init__(self):
        self.hasher = ConsistentHashing(
            nodes=["api-1:8000", "api-2:8000", "api-3:8000"],
            virtual_nodes=150
        )
    
    def get_node_for_user(self, user_id: str) -> str:
        """根据用户 ID 获取目标节点"""
        return self.hasher.get_node(f"user:{user_id}")
    
    def get_node_for_session(self, session_id: str) -> str:
        """根据 Session ID 获取目标节点"""
        return self.hasher.get_node(f"session:{session_id}")


# FastAPI 中使用
from fastapi import FastAPI, HTTPException
import httpx

app = FastAPI()
router = SessionRouter()

@app.get("/api/users/{user_id}")
async def get_user(user_id: str):
    """获取用户信息（路由到特定节点）"""
    # 获取目标节点
    target_node = router.get_node_for_user(user_id)
    
    # 调用目标节点
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://{target_node}/internal/users/{user_id}")
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Service unavailable")
        return response.json()

# 每个 FastAPI 节点提供内部 API
@app.get("/internal/users/{user_id}")
async def internal_get_user(user_id: str):
    """内部 API：获取用户数据"""
    # 这里访问本地数据库或缓存
    return {"user_id": user_id, "node": "current_node"}
```

### Nginx 配合一致性哈希

```nginx
upstream fastapi_backend {
    # 使用 hash 指令实现一致性哈希
    hash $arg_user_id consistent;
    
    server api-1:8000;
    server api-2:8000;
    server api-3:8000;
}

server {
    listen 80;
    
    location /api/users/ {
        proxy_pass http://fastapi_backend;
        proxy_set_header Host $host;
    }
}
```

### 优点
- ✅ 平滑扩容（新增节点只需迁移少量数据）
- ✅ 数据局部性好（相同用户的数据在同一节点）
- ✅ 易于实现
- ✅ 不依赖外部存储

### 缺点
- ❌ 需要客户端传递用户标识符
- ❌ 节点故障时需要重新路由
- ❌ 不适合所有场景

---

## 📊 方案选择指南

### 根据场景选择

| 场景 | 推荐方案 | 原因 |
|------|----------|------|
| **内网固定 IP** | IP Hash | 简单高效 |
| **传统 Web 应用** | Cookie + Redis 共享会话 | 兼容性好 |
| **RESTful API** | JWT + 本地缓存 | 无状态，易扩展 |
| **需要精确路由** | 一致性哈希 | 数据局部性好 |
| **混合场景** | Cookie + 一致性哈希 | 灵活可控 |

### 混合方案示例

```python
from fastapi import FastAPI, Depends, Request
from fastapi.security import HTTPBearer
import jwt
from typing import Optional

app = FastAPI()

# 方案 1：JWT 认证（无状态）
async def verify_jwt(request: Request):
    token = request.headers.get("Authorization")
    if token:
        # 验证 JWT
        pass
    return None

# 方案 2：Cookie 会话（有状态）
async def get_session(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id:
        # 从 Redis 加载会话
        pass
    return None

# 方案 3：根据用户类型选择策略
@app.get("/api/data")
async def get_data(
    request: Request,
    jwt_user: Optional[dict] = Depends(verify_jwt),
    session_user: Optional[dict] = Depends(get_session)
):
    if jwt_user:
        # JWT 用户：使用无状态方案
        return await handle_jwt_user(jwt_user)
    elif session_user:
        # Cookie 用户：使用会话方案
        return await handle_session_user(session_user)
    else:
        # 匿名用户：使用临时会话
        return await handle_anonymous_user(request)
```

---

## 🎯 最佳实践

### 1. 优先选择无状态方案

```python
# ✅ 推荐：JWT + 无状态
@app.get("/api/users/me")
async def get_current_user(token: str = Depends(verify_jwt)):
    return {"user_id": token["sub"]}

# ❌ 不推荐：依赖会话状态
@app.get("/api/users/me")
async def get_current_user(session_id: str):
    user = await redis.get(f"session:{session_id}")
    return user
```

### 2. 使用两级缓存

```python
# ✅ 推荐：本地缓存 + Redis
async def get_user_data(user_id: int):
    # 1. 检查本地缓存
    if user_id in local_cache:
        return local_cache[user_id]
    
    # 2. 检查 Redis
    data = await redis.get(f"user:{user_id}")
    if data:
        local_cache[user_id] = data
        return data
    
    # 3. 查询数据库
    data = await fetch_from_db(user_id)
    local_cache[user_id] = data
    await redis.setex(f"user:{user_id}", 300, data)
    return data
```

### 3. 设置合理的过期时间

```python
# ✅ 推荐：短过期时间
SESSION_EXPIRE = 3600  # 1 小时
CACHE_EXPIRE = 300     # 5 分钟

# ❌ 不推荐：长过期时间
SESSION_EXPIRE = 86400  # 24 小时
CACHE_EXPIRE = 3600    # 1 小时
```

### 4. 处理节点故障

```python
# ✅ 推荐：故障时降级到其他节点
async def call_user_service(user_id: int):
    target_node = router.get_node_for_user(user_id)
    
    try:
        return await httpx.get(f"http://{target_node}/users/{user_id}")
    except Exception:
        # 节点故障，尝试其他节点
        backup_nodes = router.get_backup_nodes(user_id)
        for node in backup_nodes:
            try:
                return await httpx.get(f"http://{node}/users/{user_id}")
            except:
                continue
        raise HTTPException(status_code=503, detail="Service unavailable")
```

---

## 🚀 总结

### 关键要点

1. **无状态优先**：JWT 是微服务的最佳选择
2. **会话保持是备选**：只有在必要时才使用
3. **两级缓存**：本地缓存 + Redis 提升性能
4. **故障容错**：节点故障时能够自动切换
5. **平滑扩容**：一致性哈希支持动态扩容

### 推荐组合

**小型项目（< 10K 用户）**：
- Nginx 轮询 + Redis 共享会话

**中型项目（10K - 1M 用户）**：
- Nginx IP Hash + JWT + 本地缓存

**大型项目（> 1M 用户）**：
- 一致性哈希 + JWT + 两级缓存

---

**记住：会话保持是手段，不是目的。无状态才是微服务的王道！** 🚀
