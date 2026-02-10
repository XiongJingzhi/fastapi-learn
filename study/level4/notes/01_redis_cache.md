# 01. Redis 缓存 - Redis Caching

## 📍 在架构中的位置

**从数据库直接查询到缓存加速**

```
┌─────────────────────────────────────────────────────────────┐
│          Level 3: 直接查询数据库（每次请求）                   │
└─────────────────────────────────────────────────────────────┘

class UserService:
    async def get_user(self, user_id: int) -> User:
        # ❌ 每次都查数据库（慢）
        return await self.repo.find_by_id(user_id)

性能问题：
- 数据库压力大
- 响应慢（10-50ms per query）
- 无法支持高并发
- 成本高（数据库资源昂贵）

═══════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────┐
│          Level 4: 使用 Redis 缓存                               │
└─────────────────────────────────────────────────────────────┘

class UserService:
    async def get_user(self, user_id: int) -> User:
        # 1. 先查缓存（快）
        user = await self.cache.get(f"user:{user_id}")
        if user:
            return user

        # 2. 缓存未命中，查数据库
        user = await self.repo.find_by_id(user_id)

        # 3. 写入缓存（供下次使用）
        await self.cache.set(f"user:{user_id}", user, ex=300)

        return user

性能提升：
- 响应时间：10ms → 1ms（10 倍提升）
- 并发能力：1000 QPS → 10000 QPS（10 倍提升）
- 数据库压力：降低 90%（大部分请求命中缓存）
```

**🎯 你的学习目标**：掌握 Redis 缓存集成，提升应用性能。

---

## 🎯 什么是 Redis？

### Redis vs 数据库

**类比**：

```
数据库 = 仓库（存所有东西）
├─ 慢：硬盘 I/O
├─ 适合：持久化存储
└─ 数据量大

Redis = 办公桌（放常用的东西）
├─ 快：内存操作
├─ 适合：临时存储
└─ 容量小但快
```

**对比表格**：

| 特性 | Redis | PostgreSQL |
|------|-------|------------|
| **存储介质** | 内存 | 磁盘 |
| **速度** | 极快（亚毫秒） | 慢（毫秒到秒） |
| **容量** | 小（GB 级别） | 大（TB 级别） |
| **数据类型** | String, Hash, List, Set | 表、行、列 |
| **持久化** | 可选（RDB/AOF） | 总是持久化 |
| **适用场景** | 缓存、会话、计数器 | 持久化数据 |

---

### Redis 数据类型

**5 种基本类型**：

```
1. String（字符串）
   └─ 用途：缓存对象、计数器、分布式锁

2. Hash（哈希表）
   └─ 用途：对象存储（如用户信息）

3. List（列表）
   └─ 用途：消息队列、时间线

4. Set（集合）
   └─ 用途：标签、关注关系

5. ZSet（有序集合）
   └─ 用途：排行榜、优先级队列
```

---

## 🔧 Redis 基础操作

### String 类型

```python
import redis.asyncio as redis

# 连接 Redis
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

# SET/GET
await redis_client.set('name', 'Alice')
name = await redis_client.get('name')  # 'Alice'

# 带过期时间（30 秒）
await redis_client.set('session:abc123', 'user_data', ex=30)

# 计数器
await redis_client.incr('counter')  # 自增
await redis_client.incrby('counter', 10)  # 增加 10

# 删除
await redis_client.delete('name')
```

---

### Hash 类型

```python
# HSET/HGET
await redis_client.hset('user:1', 'username', 'alice')
await redis_client.hset('user:1', 'email', 'alice@example.com')

username = await redis_client.hget('user:1', 'username')  # 'alice'

# HMGET（一次获取多个字段）
user_info = await redis_client.hmget('user:1', 'username', 'email')

# HGETALL（获取所有字段）
user_data = await redis_client.hgetall('user:1')
# {'username': 'alice', 'email': 'alice@example.com'}

# HDEL
await redis_client.hdel('user:1', 'email')
```

---

## 🎨 缓存模式

### Cache-Aside 模式（推荐）

**流程**：

```
┌─────────────────────────────────────────────────────────────┐
│                    Cache-Aside 模式                          │
└─────────────────────────────────────────────────────────────┘

读取数据：
    1. 应用查询缓存
    2. 命中？→ 返回数据 ✅
    3. 未命中？→ 查询数据库
    4. 写入缓存（供下次使用）
    5. 返回数据

写入数据：
    1. 更新数据库
    2. 删除缓存（或更新缓存）
```

**代码实现**：

```python
from redis import asyncio as aioredis

class CacheUserRepository:
    """带缓存的用户仓储"""

    def __init__(self, repo: UserRepository, redis: aioredis.Redis):
        self.repo = repo
        self.redis = redis

    async def find_by_id(self, user_id: int) -> User | None:
        """查找用户（先查缓存）"""
        cache_key = f"user:{user_id}"

        # 1. 查缓存
        cached_user = await self.redis.get(cache_key)
        if cached_user:
            # 命中缓存，反序列化
            return User.parse_raw(cached_user)

        # 2. 缓存未命中，查数据库
        user = await self.repo.find_by_id(user_id)
        if not user:
            return None

        # 3. 写入缓存（30 分钟过期）
        await self.redis.setex(
            cache_key,
            1800,  # 30 分钟
            user.model_dump_json()
        )

        return user

    async def update_user(self, user: User) -> User:
        """更新用户"""
        # 1. 更新数据库
        user = await self.repo.save(user)

        # 2. 删除缓存（下次读取时会重新缓存）
        cache_key = f"user:{user.id}"
        await self.redis.delete(cache_key)

        return user

    async def delete_user(self, user_id: int) -> None:
        """删除用户"""
        # 1. 删除数据库
        await self.repo.delete(user_id)

        # 2. 删除缓存
        cache_key = f"user:{user_id}"
        await self.redis.delete(cache_key)
```

---

## 🚀 FastAPI + Redis 集成

### 配置 Redis 客户端

```python
from fastapi import FastAPI
from redis.asyncio import Redis
from typing import Optional

app = FastAPI()

# ═══════════════════════════════════════════════════════════
# Application-scoped: 全局 Redis 客户端
# ═══════════════════════════════════════════════════════════

redis_client = Redis(
    host='localhost',
    port=6379,
    decode_responses=True,  # 自动解码字节为字符串
    db=0  # 使用数据库 0
)

def get_redis() -> Redis:
    """返回 Redis 客户端"""
    return redis_client
```

---

### 使用缓存装饰器

```python
from functools import wraps
import json
import hashlib

def cache_result(expire: int = 300):
    """缓存装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 1. 生成缓存键
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            cache_key = hashlib.md5(cache_key.encode()).hexdigest()

            # 2. 查缓存
            cached = await redis_client.get(cache_key)
            if cached:
                return json.loads(cached)

            # 3. 执行函数
            result = await func(*args, **kwargs)

            # 4. 写缓存
            await redis_client.setex(
                cache_key,
                expire,
                json.dumps(result)
            )

            return result

        return wrapper
    return decorator

# 使用
@cache_result(expire=60)
async def get_user_stats(user_id: int):
    # 这个函数的结果会被缓存 60 秒
    return await calculate_user_stats(user_id)
```

---

## 🔄 缓存更新策略

### 写策略对比

**Write-Through（直写）**：

```python
async def update_user(user: User):
    # 1. 更新数据库
    user = await db.save(user)

    # 2. 同时更新缓存
    await cache.set(f"user:{user.id}", user, ex=300)

    return user

# 好处：缓存和数据库保持一致
# 坏处：每次写操作都要更新缓存（性能开销）
```

---

**Write-Behind（延迟写）**：

```python
async def update_user(user: User):
    # 1. 只更新数据库
    user = await db.save(user)

    # 2. 删除缓存（下次读取时更新）
    await cache.delete(f"user:{user.id}")

    return user

# 好处：写操作快（不更新缓存）
# 坏处：缓存未命中时第一个请求慢
```

---

## 🎨 实际场景：用户会话管理

### Redis 存储会话

```python
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
import secrets

app = FastAPI()
redis_client = Redis(host='localhost', port=6379)

class SessionCreate(BaseModel):
    username: str
    password: str

class SessionResponse(BaseModel):
    token: str
    username: str

@app.post("/session", response_model=SessionResponse)
async def create_session(credentials: SessionCreate):
    """创建会话"""

    # 1. 验证用户
    user = await authenticate_user(credentials.username, credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # 2. 生成会话 token
    token = secrets.token_urlsafe(32)

    # 3. 存储到 Redis（1 小时过期）
    await redis_client.setex(
        f"session:{token}",
        3600,
        user.model_dump_json()
    )

    return SessionResponse(token=token, username=user.username)

@app.get("/profile")
async def get_profile(
    token: str = Header(...),
    redis: Redis = Depends(get_redis)
):
    """获取当前用户信息"""

    # 从 Redis 获取会话
    session_data = await redis_client.get(f"session:{token}")
    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = User.parse_raw(session_data)
    return user
```

---

## 🎯 分布式锁

### Redis 分布式锁

```python
import asyncio

class DistributedLock:
    """分布式锁"""

    def __init__(self, redis: Redis, lock_name: str, expire: int = 10):
        self.redis = redis
        self.lock_name = f"lock:{lock_name}"
        self.expire = expire

    async def __aenter__(self):
        """获取锁"""
        while True:
            # 尝试获取锁
            acquired = await self.redis.set(
                self.lock_name,
                "locked",
                nx=True,  # 只有不存在的键才设置
                ex=self.expire
            )

            if acquired:
                return self

            # 等待 100ms 后重试
            await asyncio.sleep(0.1)

    async def __aexit__(self, exc_type, exc_val, tb):
        """释放锁"""
        await redis_client.delete(self.lock_name)

# 使用
async def transfer_money_with_lock(
    user_id_from: int,
    user_id_to: int,
    amount: int
):
    """转账（使用分布式锁）"""

    lock = DistributedLock(
        redis_client,
        f"transfer:{user_id_from}",
        expire=10  # 10 秒后自动释放
    )

    async with lock:
        # 只有一个请求能执行到这里
        # 其他请求会等待锁释放
        await perform_transfer(user_id_from, user_id_to, amount)
```

---

## 🎯 小实验：自己动手

### 实验 1：基本缓存

```python
import redis.asyncio as redis

async def basic_cache():
    # 连接
    r = redis.Redis(host='localhost', port=6379)

    # SET/GET
    await r.set('key', 'value')
    value = await r.get('key')
    print(value)  # 'value'

    # 带过期时间
    await r.setex('session:abc', 3600, 'user_data')
```

---

### 实验 2：Hash 缓存

```python
async def hash_cache():
    r = redis.Redis(host='localhost', port=6379)

    # HSET/HGET
    await r.hset('user:1', 'username', 'alice')
    await r.hset('user:1', 'email', 'alice@example.com')

    # HGETALL
    user = await r.hgetall('user:1')
    print(user)  # {'username': 'alice', 'email': 'alice@example.com'}
```

---

## 📚 检查理解

回答这些问题来测试你的理解：

1. **Redis 和数据库的区别？**
   - 提示：Redis 快但容量小，数据库慢但容量大

2. **什么是 Cache-Aside 模式？**
   - 提示：先查缓存，未命中再查数据库

3. **为什么需要分布式锁？**
   - 提示：防止并发修改

4. **如何实现会话管理？**
   - 提示：token → Redis

5. **Write-Through 和 Write-Behind 的区别？**
   - 提示：直写 vs 延迟写

---

## 🚀 下一步

现在你已经掌握了 Redis 缓存，接下来：

1. **学习消息队列**：`notes/02_message_queue.md`
2. **查看实际代码**：`examples/01_redis_cache.py`

**记住**：缓存是提升性能最有效的方法之一，Redis 是最快的缓存系统！**

---

**费曼技巧总结**：
- ✅ 仓库 vs 办公桌类比
- ✅ 详细的对比表格
- ✅ Cache-Aside 模式流程图
- ✅ 完整的代码示例
- ✅ 分布式锁实现
- ✅ 会话管理示例
