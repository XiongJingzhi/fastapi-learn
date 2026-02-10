# 02. 类依赖 vs 函数依赖 - Class vs Function Dependencies

## 📍 在架构中的位置

**深入理解依赖注入的形式选择**

```
┌─────────────────────────────────────────────────────────────┐
│          上一课：Depends 的基本用法                          │
└─────────────────────────────────────────────────────────────┘

def get_user_service(repo: UserRepository = Depends(get_repo)):
    return UserService(repo)

@app.get("/users/{id}")
async def get_user(
    service: UserService = Depends(get_user_service)  # 函数依赖
):
    return await service.get_user(id)

问题：
- 函数依赖可以吗？可以！
- 那为什么要学类依赖？
- 什么时候用哪种？

═══════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────┐
│          这一课：两种依赖形式的对比                          │
└─────────────────────────────────────────────────────────────┘

函数依赖 vs 类依赖
├─ 函数依赖：简单、轻量
└─ 类依赖：强大、灵活

学会根据场景选择！
```

**🎯 你的学习目标**：掌握两种依赖形式，知道何时使用哪种。

---

## 🎯 两种依赖形式对比

### 形式 1：函数依赖（简单场景）

**基本语法**：

```python
from fastapi import Depends

def get_user_service() -> UserService:
    """函数依赖：返回服务实例"""
    db = get_db()
    repo = UserRepository(db)
    return UserService(repo)

@app.get("/users/{id}")
async def get_user(
    service: UserService = Depends(get_user_service)  # ← 函数依赖
):
    return await service.get_user(id)
```

**特点**：
- ✅ 简单直观
- ✅ 适合无状态逻辑
- ✅ 轻量级

**适用场景**：
- 简单的依赖创建
- 无状态的操作
- 一次性返回结果

---

### 形式 2：类依赖（复杂场景）

**基本语法**：

```python
from fastapi import Depends

class UserServiceProvider:
    """类依赖：可以管理状态和复杂逻辑"""

    def __init__(self, repo: UserRepository = Depends(get_repo)):
        # 构造函数可以接受依赖
        self.repo = repo

    def __call__(self) -> UserService:
        # __call__ 方法让类实例可调用
        return UserService(self.repo)

@app.get("/users/{id}")
async def get_user(
    service: UserService = Depends(UserServiceProvider())  # ← 类依赖
):
    return await service.get_user(id)
```

**特点**：
- ✅ 可以管理状态
- ✅ 可以有多个方法
- ✅ 更灵活强大

**适用场景**：
- 需要管理状态
- 复杂的初始化逻辑
- 需要多个相关方法

---

## 🤔 为什么需要类依赖？

### 场景对比：简单 vs 复杂

#### 场景 1：简单依赖（函数依赖就够）

```python
# ✅ 简单场景：函数依赖

def get_current_user(token: str = Header(...)) -> User:
    """从 token 获取当前用户"""
    payload = decode_jwt(token)
    user_id = payload["user_id"]
    return get_user_from_db(user_id)

@app.get("/profile")
async def get_profile(
    user: User = Depends(get_current_user)  # 简单直接
):
    return user

# 为什么够用？
# - 逻辑简单：解码 token → 获取用户
# - 无状态：不需要记住之前的状态
# - 一次性：每次返回新用户对象
```

---

#### 场景 2：复杂依赖（类依赖更合适）

```python
# ✅ 复杂场景：类依赖

class AuthProvider:
    """认证提供者（管理复杂的认证逻辑）"""

    def __init__(self):
        # 状态：缓存认证结果
        self._cache = {}

    def __call__(self, token: str = Header(...)) -> User:
        """主要方法：验证并返回用户"""
        # 1. 检查缓存（状态管理）
        if token in self._cache:
            return self._cache[token]

        # 2. 验证 token
        user = self._verify_token(token)

        # 3. 缓存结果（状态管理）
        self._cache[token] = user

        return user

    def _verify_token(self, token: str) -> User:
        """辅助方法：验证 token"""
        payload = decode_jwt(token)
        return get_user_from_db(payload["user_id"])

    def invalidate(self, token: str):
        """辅助方法：让 token 失效"""
        if token in self._cache:
            del self._cache[token]

@app.get("/profile")
async def get_profile(
    user: User = Depends(AuthProvider())  # 类依赖
):
    return user

# 为什么需要类？
# - 需要状态：缓存已验证的用户
# - 复杂逻辑：验证、缓存、失效
# - 多个方法：__call__, _verify_token, invalidate
```

---

## 📊 详细对比

### 对比表格

| 特性 | 函数依赖 | 类依赖 |
|------|---------|--------|
| **语法** | `def func()` | `class Cls: def __call__()` |
| **状态管理** | ❌ 无状态 | ✅ 可以有状态 |
| **复杂度** | 简单 | 复杂 |
| **可维护性** | 小型场景好 | 大型场景好 |
| **测试难度** | 容易 | 稍复杂 |
| **适用场景** | 简单依赖 | 复杂依赖 |
| **内存占用** | 低 | 稍高（有状态时） |

---

### 实际例子对比

#### 例子 1：获取配置（函数依赖）

```python
from fastapi import Depends
from pydantic import BaseModel

class Config(BaseModel):
    app_name: str
    debug: bool

# 函数依赖：简单直接
def get_config() -> Config:
    """返回配置"""
    return Config(
        app_name="My API",
        debug=True
    )

@app.get("/info")
async def get_info(
    config: Config = Depends(get_config)  # ← 简单
):
    return {
        "app_name": config.app_name,
        "debug": config.debug
    }

# 为什么用函数依赖？
# - 逻辑简单：返回配置对象
# - 无状态：不需要记忆
# - 一次性的：每次返回新配置
```

---

#### 例子 2：数据库连接池（类依赖）

```python
from fastapi import Depends

class DatabasePool:
    """数据库连接池（管理状态）"""

    def __init__(self, max_connections: int = 10):
        # 状态：连接池
        self.max_connections = max_connections
        self._connections = []
        self._created = 0

    def __call__(self) -> Database:
        """返回一个数据库连接"""
        # 状态管理：检查是否达到最大连接数
        if len(self._connections) >= self.max_connections:
            raise Exception("Too many connections")

        # 状态管理：创建或复用连接
        if self._connections:
            return self._connections.pop()

        # 创建新连接
        db = self._create_connection()
        self._created += 1
        return db

    def return_connection(self, db: Database):
        """归还连接到池（状态管理）"""
        self._connections.append(db)

    def _create_connection(self) -> Database:
        """辅助方法：创建连接"""
        return Database(host="localhost", port=5432)

    def stats(self) -> dict:
        """辅助方法：统计信息"""
        return {
            "created": self._created,
            "available": len(self._connections),
            "max": self.max_connections
        }

@app.get("/users")
async def list_users(
    db: Database = Depends(DatabasePool(max_connections=5))  # ← 类依赖
):
    users = await db.query("SELECT * FROM users")
    return users

# 为什么用类依赖？
# - 需要状态：管理连接池（_connections, _created）
# - 复杂逻辑：创建、复用、归还连接
# - 多个方法：__call__, return_connection, stats
```

---

## 🔧 可调用对象作为依赖

### 理解 `__call__` 方法

**什么是可调用对象？**

```python
# 函数是可调用的
def func():
    pass

func()  # ✅ 可以调用

# 类实例也可以是可调用的（如果实现了 __call__）
class CallableClass:
    def __call__(self):
        print("我被调用了！")

obj = CallableClass()
obj()  # ✅ 也可以调用（因为实现了 __call__）
```

**FastAPI 如何使用可调用对象？**

```python
from fastapi import Depends

class MyDependency:
    """可调用对象：作为依赖"""

    def __init__(self, prefix: str = "MSG"):
        # 构造函数：只在创建时调用一次
        self.prefix = prefix
        self.counter = 0

    def __call__(self) -> str:
        # __call__：每次请求时调用
        self.counter += 1
        return f"{self.prefix} #{self.counter}"

# 使用
my_dep = MyDependency(prefix="LOG")

@app.get("/test1")
async def test1(
    msg: str = Depends(my_dep)  # ← 类实例作为依赖
):
    # FastAPI 调用 my_dep.__call__()
    return {"message": msg}

@app.get("/test2")
async def test2(
    msg: str = Depends(my_dep)  # ← 同一个实例
):
    # FastAPI 再次调用 my_dep.__call__()
    return {"message": msg}

# 访问 /test1 → {"message": "LOG #1"}
# 访问 /test2 → {"message": "LOG #2"}
# counter 状态被保留！
```

**工作原理**：

```
1. 启动应用时
   └─→ 创建 MyDependency(prefix="LOG")
      └─→ __init__ 被调用
      └─→ self.counter = 0

2. 第一次请求 /test1
   └─→ FastAPI 调用 my_dep.__call__()
      └─→ self.counter = 1
      └─→ 返回 "LOG #1"

3. 第二次请求 /test2
   └─→ FastAPI 调用 my_dep.__call__()
      └─→ self.counter = 2
      └─→ 返回 "LOG #2"

注意：my_dep 实例在应用生命周期内只有一个
```

---

## 🎨 实际场景：认证系统

### 函数依赖：简单的 Token 认证

```python
from fastapi import Depends, Header
from pydantic import BaseModel

class User(BaseModel):
    id: int
    username: str

def get_current_user(token: str = Header(...)) -> User:
    """函数依赖：简单的 token 认证"""
    try:
        payload = decode_jwt(token)
        user_id = payload["user_id"]
        return get_user_from_db(user_id)
    except:
        raise HTTPException(401, "Invalid token")

@app.get("/profile")
async def get_profile(
    user: User = Depends(get_current_user)
):
    return user

# 为什么用函数依赖？
# - 逻辑简单：解码 token → 获取用户
# - 无状态：不需要缓存
# - 一次性的：每次重新验证
```

---

### 类依赖：带缓存的认证系统

```python
from fastapi import Depends, Header
from typing import Dict

class CachedAuthProvider:
    """类依赖：带缓存的认证系统"""

    def __init__(self, cache_ttl: int = 300):
        # 状态：缓存配置
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, tuple] = {}  # {token: (user, timestamp)}

    def __call__(self, token: str = Header(...)) -> User:
        """验证 token（带缓存）"""

        # 1. 检查缓存（状态管理）
        if token in self._cache:
            user, timestamp = self._cache[token]
            if time.time() - timestamp < self.cache_ttl:
                return user  # 缓存命中

        # 2. 验证 token
        user = self._verify_token(token)

        # 3. 更新缓存（状态管理）
        self._cache[token] = (user, time.time())

        return user

    def _verify_token(self, token: str) -> User:
        """辅助方法：验证 token"""
        try:
            payload = decode_jwt(token)
            return get_user_from_db(payload["user_id"])
        except:
            raise HTTPException(401, "Invalid token")

    def logout(self, token: str):
        """辅助方法：登出（清除缓存）"""
        if token in self._cache:
            del self._cache[token]

    def clear_expired(self):
        """辅助方法：清除过期缓存"""
        now = time.time()
        expired = [
            token for token, (_, timestamp) in self._cache.items()
            if now - timestamp >= self.cache_ttl
        ]
        for token in expired:
            del self._cache[token]

# 使用
auth_provider = CachedAuthProvider(cache_ttl=300)

@app.get("/profile")
async def get_profile(
    user: User = Depends(auth_provider)
):
    return user

@app.post("/logout")
async def logout(
    token: str = Header(...),
    auth: CachedAuthProvider = Depends(auth_provider)
):
    auth.logout(token)
    return {"message": "Logged out"}

# 为什么用类依赖？
# - 需要状态：缓存已验证的用户
# - 复杂逻辑：验证、缓存、过期清理
# - 多个方法：__call__, logout, clear_expired
```

---

## 🎯 小实验：自己动手

### 实验 1：函数依赖 - 简单计数器

**目标**：创建一个每次返回递增数字的函数依赖

```python
from fastapi import FastAPI, Depends

app = FastAPI()

counter = 0

def get_next_id() -> int:
    """返回下一个 ID"""
    global counter
    counter += 1
    return counter

@app.get("/items/{item_id}")
async def get_item(
    item_id: int,
    request_id: int = Depends(get_next_id)  # ← 函数依赖
):
    return {
        "item_id": item_id,
        "request_id": request_id
    }

# 测试：
# GET /items/1 → {"item_id": 1, "request_id": 1}
# GET /items/2 → {"item_id": 2, "request_id": 2}

# 问题：counter 是全局变量，多个 endpoint 会互相影响！
```

---

### 实验 2：类依赖 - 独立计数器

**目标**：使用类依赖，每个 endpoint 有独立的计数器

```python
from fastapi import FastAPI, Depends

app = FastAPI()

class Counter:
    """计数器类（管理状态）"""

    def __init__(self):
        self._count = 0

    def __call__(self) -> int:
        """返回下一个 ID"""
        self._count += 1
        return self._count

# 为不同 endpoint 创建独立的计数器
items_counter = Counter()
users_counter = Counter()

@app.get("/items/{item_id}")
async def get_item(
    item_id: int,
    request_id: int = Depends(items_counter)  # ← 独立计数器
):
    return {
        "item_id": item_id,
        "request_id": request_id
    }

@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    request_id: int = Depends(users_counter)  # ← 独立计数器
):
    return {
        "user_id": user_id,
        "request_id": request_id
    }

# 测试：
# GET /items/1 → {"item_id": 1, "request_id": 1}
# GET /items/2 → {"item_id": 2, "request_id": 2}
# GET /users/1 → {"user_id": 1, "request_id": 1}  ← 独立计数！
# GET /users/2 → {"user_id": 2, "request_id": 2}

# 好处：每个 endpoint 有独立的状态
```

---

### 实验 3：带参数的类依赖

**目标**：创建一个可以自定义初始值的计数器

```python
from fastapi import FastAPI, Depends

app = FastAPI()

class Counter:
    """计数器类（可配置初始值）"""

    def __init__(self, start: int = 0):
        self._count = start

    def __call__(self) -> int:
        self._count += 1
        return self._count

# 创建不同初始值的计数器
counter_from_0 = Counter(start=0)
counter_from_100 = Counter(start=100)

@app.get("/items/{item_id}")
async def get_item(
    item_id: int,
    request_id: int = Depends(counter_from_0)  # 从 0 开始
):
    return {"item_id": item_id, "request_id": request_id}

@app.get("/orders/{order_id}")
async def get_order(
    order_id: int,
    request_id: int = Depends(counter_from_100)  # 从 100 开始
):
    return {"order_id": order_id, "request_id": request_id}

# 测试：
# GET /items/1 → {"item_id": 1, "request_id": 1}
# GET /orders/1 → {"order_id": 1, "request_id": 101}  ← 从 100 开始！
```

---

## 📚 检查理解

回答这些问题来测试你的理解：

1. **函数依赖和类依赖的主要区别？**
   - 提示：状态管理、复杂度

2. **什么时候用函数依赖？**
   - 提示：简单场景、无状态

3. **什么时候用类依赖？**
   - 提示：需要状态、复杂逻辑

4. **什么是可调用对象？**
   - 提示：实现了 `__call__` 方法的类

5. **`__init__` 和 `__call__` 的区别？**
   - 提示：`__init__` 只调用一次，`__call__` 每次请求都调用

---

## 🚀 下一步

现在你已经理解了函数依赖和类依赖的区别，接下来：

1. **查看实际代码**：`examples/03_class_vs_function.py`
2. **学习下一课**：`notes/03_dependency_lifecycle.md`（依赖的生命周期）

**记住**：根据场景选择合适的形式，简单用函数，复杂用类！

---

**费曼技巧总结**：
- ✅ 对比表格（清晰展示区别）
- ✅ 实际场景（简单 vs 复杂）
- ✅ 可调用对象解释（`__call__` 原理）
- ✅ 完整例子（认证系统）
- ✅ 小实验（独立计数器）
