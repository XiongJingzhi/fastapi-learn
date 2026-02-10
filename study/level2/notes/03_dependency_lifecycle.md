# 03. 依赖的生命周期 - Dependency Lifecycle

## 📍 在架构中的位置

**理解依赖的创建和销毁时机**

```
┌─────────────────────────────────────────────────────────────┐
│          上一课：函数依赖 vs 类依赖                           │
└─────────────────────────────────────────────────────────────┘

def get_service() -> UserService:
    return UserService(repo)

@app.get("/users")
async def get_users(
    service: UserService = Depends(get_service)
):
    return await service.list_users()

问题：
- get_service() 什么时候被调用？
- service 实例是每次新建还是复用？
- 如何管理资源（如数据库连接）？

═══════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────┐
│          这一课：依赖的生命周期管理                          │
└─────────────────────────────────────────────────────────────┘

Request-scoped（请求范围）
└─ 每个请求创建一次（默认）

Application-scoped（应用范围）
└─ 应用启动时创建，全局共享

学会根据资源类型选择合适的生命周期！
```

**🎯 你的学习目标**：理解依赖的创建和销毁时机，正确管理资源。

---

## 🎯 两种生命周期模式

### 模式 1：Request-scoped（请求范围，默认）

**定义**：每个 HTTP 请求创建一个新的依赖实例。

```python
from fastapi import Depends

def get_db() -> Database:
    """每次请求都创建新连接"""
    print("创建新的数据库连接")
    return Database()

@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    db: Database = Depends(get_db)  # ← 每次请求都会调用
):
    return await db.query(f"SELECT * FROM users WHERE id = {user_id}")
```

**工作流程**：

```
请求 1: GET /users/1
    │
    ├─→ Depends(get_db)
    │   └─→ 调用 get_db()
    │       └─→ 创建 Database 实例 1
    │
    └─→ Endpoint 执行
        └─→ 使用 Database 实例 1
    └─→ 请求结束
        └─→ Database 实例 1 被销毁

请求 2: GET /users/2
    │
    ├─→ Depends(get_db)
    │   └─→ 调用 get_db()
    │       └─→ 创建 Database 实例 2  ← 新实例！
    │
    └─→ Endpoint 执行
        └─→ 使用 Database 实例 2
    └─→ 请求结束
        └─→ Database 实例 2 被销毁
```

**特点**：
- ✅ 每个请求独立
- ✅ 无状态（不会互相影响）
- ✅ 自动清理（请求结束销毁）

**适用场景**：
- 数据库连接（使用 `yield` 管理）
- 请求特定的资源
- 无状态的服务

---

### 模式 2：Application-scoped（应用范围）

**定义**：应用启动时创建一次，所有请求共享同一个实例。

```python
from fastapi import FastAPI, Depends

app = FastAPI()

# 创建单例实例
cache = Cache()  # 应用启动时创建

def get_cache() -> Cache:
    """返回全局缓存实例"""
    return cache  # 总是返回同一个实例

@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    cache: Cache = Depends(get_cache)  # ← 全局共享
):
    # 所有请求使用同一个 cache 实例
    return cache.get(f"user:{user_id}")
```

**工作流程**：

```
应用启动
    │
    └─→ 创建 Cache 实例（全局唯一）
        └─→ cache = Cache()

请求 1: GET /users/1
    │
    ├─→ Depends(get_cache)
    │   └─→ 调用 get_cache()
    │       └─→ 返回 Cache 实例  ← 全局唯一
    │
    └─→ Endpoint 执行
        └─→ 使用 Cache 实例
    └─→ 请求结束
        └─→ Cache 实例保留（不销毁）

请求 2: GET /users/2
    │
    ├─→ Depends(get_cache)
    │   └─→ 调用 get_cache()
    │       └─→ 返回同一个 Cache 实例
    │
    └─→ Endpoint 执行
        └─→ 使用同一个 Cache 实例
    └─→ 请求结束
        └─→ Cache 实例继续保留
```

**特点**：
- ✅ 全局共享
- ✅ 有状态（可以累积数据）
- ✅ 生命周期长（应用启动到关闭）

**适用场景**：
- 缓存
- 配置对象
- 连接池（管理多个连接）

---

## 🔄 Request-scoped 的详细机制

### 依赖缓存（同一请求内）

**关键概念**：同一个请求内，相同的依赖只创建一次！

```python
from fastapi import Depends

def get_db() -> Database:
    print("创建数据库连接")
    return Database()

@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    db1: Database = Depends(get_db),  # ← 第一次
    db2: Database = Depends(get_db),  # ← 第二次（同一个请求）
):
    # db1 和 db2 是同一个实例！
    assert db1 is db2  # True
    return await db1.query(f"SELECT * FROM users WHERE id = {user_id}")
```

**日志输出**：

```
GET /users/1
    创建数据库连接  ← 只打印一次！

GET /users/2
    创建数据库连接  ← 新请求，重新创建
```

**工作原理**：

```
请求开始
    │
    ├─→ 第一次遇到 Depends(get_db)
    │   └─→ 调用 get_db()
    │       └─→ 创建 Database 实例
    │       └─→ 缓存实例（请求级别的缓存）
    │
    ├─→ 第二次遇到 Depends(get_db)
    │   └─→ 从缓存获取（不重新创建）
    │
    └─→ 请求结束
        └─→ 清空缓存（所有依赖被销毁）
```

**实际场景**：

```python
@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    db: Database = Depends(get_db),  # ← 第一次创建
    service: UserService = Depends(get_user_service),  # ← 内部也用 db
):
    # get_user_service 内部也 Depends(get_db)
    # 但不会重新创建 db，而是复用！
    return await service.get_user(user_id)
```

---

### 使用 `yield` 管理资源

**问题**：如何确保请求结束后关闭数据库连接？

**方案**：使用 `yield` 关键字！

```python
from fastapi import Depends

def get_db():
    """使用 yield 管理数据库连接"""
    # 1. 创建连接（请求开始时）
    db = Database(host="localhost", port=5432)
    print("✅ 数据库连接已打开")

    try:
        yield db  # ← 交给 endpoint 使用

    finally:
        # 2. 关闭连接（请求结束时）
        db.close()
        print("❌ 数据库连接已关闭")

@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    db: Database = Depends(get_db)  # ← 使用 yield 的依赖
):
    return await db.query(f"SELECT * FROM users WHERE id = {user_id}")

# 执行流程：
# 1. 请求到达 → 调用 get_db() → 打开连接 → yield db
# 2. Endpoint 使用 db
# 3. 请求结束 → 执行 finally → 关闭连接
```

**工作流程**：

```
GET /users/1
    │
    ├─→ Depends(get_db)
    │   ├─→ 调用 get_db()
    │   ├─→ 创建 Database 实例
    │   ├─→ 打开连接 ✅
    │   ├─→ yield db（暂停在这里）
    │   │
    │   └─→ Endpoint 使用 db
    │       └─→ 执行查询
    │   │
    │   └─→ Endpoint 返回
    │
    └─→ 请求结束
        └─→ 继续 get_db()（从 yield 后继续）
            └─→ finally 块
                └─→ 关闭连接 ❌
```

**实际例子：数据库事务**

```python
def get_db():
    """管理数据库事务"""
    db = Database()

    try:
        # 开始事务
        db.begin()
        yield db
        # 提交事务（如果没有异常）
        db.commit()
        print("✅ 事务已提交")

    except Exception as e:
        # 回滚事务（如果有异常）
        db.rollback()
        print(f"❌ 事务已回滚: {e}")
        raise

    finally:
        # 关闭连接
        db.close()
        print("🔌 连接已关闭")

@app.post("/users")
async def create_user(
    user: UserCreate,
    db: Database = Depends(get_db)  # ← 自动管理事务
):
    # 如果这里抛出异常，事务会自动回滚！
    user_id = await db.insert("INSERT INTO users ...")
    return {"id": user_id}
```

---

## 🌐 Application-scoped 的详细机制

### 创建全局单例

**方法 1：直接创建（最简单）**

```python
from fastapi import FastAPI, Depends

app = FastAPI()

# 应用启动时创建（全局唯一）
cache = Cache()

def get_cache() -> Cache:
    """返回全局缓存"""
    return cache

@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    cache: Cache = Depends(get_cache)
):
    return cache.get(f"user:{user_id}")

# 特点：
# - 简单直接
# - cache 在应用启动时创建
# - 所有请求共享同一个实例
```

---

**方法 2：使用类依赖**

```python
from fastapi import FastAPI, Depends

app = FastAPI()

class CacheProvider:
    """缓存提供者（应用范围）"""

    def __init__(self):
        # __init__ 只在应用启动时调用一次
        self._cache = {}
        print("📦 创建全局缓存")

    def __call__(self) -> Cache:
        """每次请求返回同一个缓存实例"""
        return self._cache

# 创建全局实例
cache_provider = CacheProvider()

@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    cache: Cache = Depends(cache_provider)  # ← 全局共享
):
    return cache.get(f"user:{user_id}")

# 特点：
# - cache_provider.__init__() 只调用一次
# - 所有请求共享同一个 _cache 字典
```

---

**方法 3：使用 `lifespan`（推荐用于复杂场景）**

```python
from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    print("🚀 应用启动")
    cache = Cache()
    # 可以将 cache 存储在 app.state
    app.state.cache = cache

    yield

    # 关闭时执行
    print("🛑 应用关闭")
    # 清理资源
    app.state.cache.clear()

app = FastAPI(lifespan=lifespan)

def get_cache(request: Request) -> Cache:
    """从 app.state 获取缓存"""
    return request.app.state.cache

@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    cache: Cache = Depends(get_cache)
):
    return cache.get(f"user:{user_id}")

# 特点：
# - 使用 lifespan 管理应用生命周期
# - 启动时创建，关闭时清理
# - 通过 app.state 共享
```

---

## 🎨 实际场景对比

### 场景 1：数据库连接（Request-scoped）

```python
def get_db():
    """每个请求独立的数据库连接"""
    db = Database()
    try:
        yield db
    finally:
        db.close()

@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    db: Database = Depends(get_db)  # ← Request-scoped
):
    return await db.query(f"SELECT * FROM users WHERE id = {user_id}")

# 为什么用 Request-scoped？
# - 每个请求需要独立的连接
# - 请求结束要关闭连接
# - 避免连接泄漏
```

---

### 场景 2：Redis 缓存（Application-scoped）

```python
from fastapi import FastAPI, Depends

app = FastAPI()

# 应用启动时创建 Redis 连接
redis = Redis(host="localhost", port=6379)
print("📦 创建全局 Redis 连接")

def get_redis() -> Redis:
    """返回全局 Redis 实例"""
    return redis

@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    redis: Redis = Depends(get_redis)  # ← Application-scoped
):
    # 从缓存获取
    cached = redis.get(f"user:{user_id}")
    if cached:
        return cached

    # 缓存未命中，从数据库获取
    user = await db.get_user(user_id)
    redis.set(f"user:{user_id}", user, ex=300)
    return user

# 为什么用 Application-scoped？
# - Redis 连接是昂贵的资源
# - 可以在多个请求间共享
# - 连接池本身就是设计来共享的
```

---

### 场景 3：混合使用

```python
from fastapi import FastAPI, Depends

app = FastAPI()

# Application-scoped: 全局资源
cache = Cache()
redis = Redis()

def get_cache() -> Cache:
    return cache

def get_redis() -> Redis:
    return redis

# Request-scoped: 请求特定资源
def get_db():
    db = Database()
    try:
        yield db
    finally:
        db.close()

@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    db: Database = Depends(get_db),      # ← 每个请求新连接
    cache: Cache = Depends(get_cache),   # ← 全局共享
    redis: Redis = Depends(get_redis),   # ← 全局共享
):
    # 1. 先查本地缓存
    cached = cache.get(f"user:{user_id}")
    if cached:
        return cached

    # 2. 再查 Redis 缓存
    cached = redis.get(f"user:{user_id}")
    if cached:
        cache.set(f"user:{user_id}", cached)
        return cached

    # 3. 最后查数据库
    user = await db.get_user(user_id)

    # 4. 更新缓存
    cache.set(f"user:{user_id}", user)
    redis.set(f"user:{user_id}", user, ex=300)

    return user

# 混合使用的好处：
# - 数据库连接：每个请求独立，避免干扰
# - 本地缓存：全局共享，提高性能
# - Redis：全局共享，利用连接池
```

---

## 🎯 选择指南

### 对比表格

| 场景 | 生命周期 | 原因 |
|------|---------|------|
| **数据库连接** | Request-scoped (`yield`) | 每个请求独立连接，用完关闭 |
| **数据库事务** | Request-scoped (`yield`) | 请求结束提交或回滚 |
| **Redis 连接** | Application-scoped | 连接池设计来共享 |
| **本地缓存** | Application-scoped | 全局共享提高性能 |
| **配置对象** | Application-scoped | 配置不会改变 |
| **Logger** | Application-scoped | 全局共享日志实例 |
| **请求上下文** | Request-scoped | 每个请求独立 |
| **临时文件** | Request-scoped (`yield`) | 用完删除 |

---

### 决策流程图

```
需要依赖？
    │
    ├─→ 资源需要清理吗？（连接、文件等）
    │   ├─→ 是 → Request-scoped (使用 yield)
    │   └─→ 否 → 继续
    │
    ├─→ 资源可以在多个请求间共享吗？
    │   ├─→ 是 → Application-scoped
    │   └─→ 否 → Request-scoped
    │
    └─→ 资源是请求特定的吗？
        ├─→ 是 → Request-scoped
        └─→ 否 → Application-scoped
```

---

## 🎯 小实验：自己动手

### 实验 1：Request-scoped 计数器

**目标**：观察依赖的创建和销毁

```python
from fastapi import FastAPI, Depends

app = FastAPI()

def get_counter():
    """每个请求独立的计数器"""
    print("📝 创建新的计数器")
    counter = {"count": 0}
    try:
        yield counter
    finally:
        print(f"🗑️ 销毁计数器（最终值: {counter['count']}）")

@app.get("/test")
async def test(
    counter: dict = Depends(get_counter)
):
    counter["count"] += 1
    return {"count": counter["count"]}

# 测试：
# 第一次请求 /test
#   📝 创建新的计数器
#   🗑️ 销毁计数器（最终值: 1）
#
# 第二次请求 /test
#   📝 创建新的计数器  ← 重新创建！
#   🗑️ 销毁计数器（最终值: 1）
```

---

### 实验 2：Application-scoped 计数器

**目标**：观察全局状态的累积

```python
from fastapi import FastAPI, Depends

app = FastAPI()

# 全局计数器
counter = {"count": 0}
print("📦 创建全局计数器")

def get_counter() -> dict:
    """返回全局计数器"""
    return counter

@app.get("/test")
async def test(
    counter: dict = Depends(get_counter)  # ← 全局共享
):
    counter["count"] += 1
    return {"count": counter["count"]}

# 测试：
# 第一次请求 /test → {"count": 1}
# 第二次请求 /test → {"count": 2}  ← 累积！
# 第三次请求 /test → {"count": 3}
```

---

### 实验 3：对比两种生命周期

**目标**：同时使用两种生命周期

```python
from fastapi import FastAPI, Depends

app = FastAPI()

# Application-scoped: 全局计数器
global_counter = {"count": 0}

def get_global_counter() -> dict:
    return global_counter

# Request-scoped: 请求计数器
def get_request_counter():
    counter = {"count": 0}
    try:
        yield counter
    finally:
        pass

@app.get("/test")
async def test(
    global_count: dict = Depends(get_global_counter),     # ← 全局
    request_count: dict = Depends(get_request_counter)    # ← 请求
):
    global_count["count"] += 1
    request_count["count"] += 1
    return {
        "global": global_count["count"],   # 持续累积
        "request": request_count["count"]  # 每次请求重置
    }

# 测试：
# 第一次请求 /test → {"global": 1, "request": 1}
# 第二次请求 /test → {"global": 2, "request": 1}  ← request 重置
# 第三次请求 /test → {"global": 3, "request": 1}
```

---

## 📚 检查理解

回答这些问题来测试你的理解：

1. **Request-scoped 和 Application-scoped 的区别？**
   - 提示：创建时机、生命周期

2. **什么时候使用 `yield`？**
   - 提示：需要清理资源时

3. **同一个请求内，相同的依赖会创建几次？**
   - 提示：只创建一次（缓存）

4. **数据库连接应该用什么生命周期？**
   - 提示：Request-scoped with yield

5. **Redis 连接应该用什么生命周期？**
   - 提示：Application-scoped（连接池）

---

## 🚀 下一步

现在你已经理解了依赖的生命周期，接下来：

1. **查看实际代码**：`examples/04_lifecycle.py`
2. **学习下一课**：`notes/04_service_layer.md`（实现服务层）

**记住**：根据资源特性选择合适的生命周期，正确管理资源！

---

**费曼技巧总结**：
- ✅ 两种生命周期对比
- ✅ 工作流程可视化
- ✅ `yield` 的详细解释
- ✅ 实际场景选择指南
- ✅ 小实验观察行为
