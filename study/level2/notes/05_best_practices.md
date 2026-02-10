# 05. 最佳实践 - Best Practices

## 📍 在架构中的位置

**从会用到用好：掌握生产环境的最佳实践**

```
┌─────────────────────────────────────────────────────────────┐
│          之前的学习：依赖注入的基本用法                        │
└─────────────────────────────────────────────────────────────┘

✅ 知道什么是依赖注入
✅ 知道如何使用 Depends
✅ 知道如何实现三层架构

问题：
- 如何避免常见的陷阱？
- 如何在测试中使用依赖注入？
- 如何优化性能？
- 生产环境需要注意什么？

═══════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────┐
│          这一课：生产环境的最佳实践                          │
└─────────────────────────────────────────────────────────────┘

反模式 → 正确模式
测试 → Mock 注入
性能 → 依赖缓存
安全 → 依赖验证

从会用到用好！
```

**🎯 你的学习目标**：掌握生产环境的依赖注入最佳实践。

---

## ⚠️ 常见反模式及避免方法

### 反模式 1：服务定位器 (Service Locator)

**❌ 反模式**：

```python
from fastapi import FastAPI, Request

app = FastAPI()

# 全局容器（服务定位器）
service_container = {
    "user_service": UserService(),
    "order_service": OrderService(),
}

@app.get("/users/{user_id}")
async def get_user(user_id: int, request: Request):
    # ❌ 主动获取依赖（隐式依赖）
    user_service = request.app.service_container["user_service"]
    return await user_service.get_user(user_id)

# 问题：
# 1. 依赖关系不明确（看函数签名不知道需要什么）
# 2. 难以测试（需要设置全局容器）
# 3. 违反依赖注入原则（应该是"被动接收"）
```

**✅ 正确模式**：

```python
from fastapi import Depends

@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service)  # ← 显式依赖
):
    return await service.get_user(user_id)

# 好处：
# 1. 依赖明确（看函数签名就知道需要什么）
# 2. 易于测试（可以注入 Mock）
# 3. 符合依赖注入原则（被动接收）
```

---

### 反模式 2：全局可变状态

**❌ 反模式**：

```python
from fastapi import FastAPI

app = FastAPI()

# ❌ 全局可变状态（线程不安全！）
current_request_id = None
request_counter = 0

def set_request_context(request_id: int):
    global current_request_id, request_counter
    current_request_id = request_id
    request_counter = 0

@app.get("/test/{request_id}")
async def test(request_id: int):
    set_request_context(request_id)

    # 问题：多个请求会互相干扰！
    global request_counter
    request_counter += 1
    return {"request_id": current_request_id, "count": request_counter}

# 场景：
# 请求 1: GET /test/1 → {"request_id": 1, "count": 1}
# 请求 2: GET /test/2 → {"request_id": 2, "count": 2}  ← 干扰请求 1！
```

**✅ 正确模式**：

```python
from fastapi import FastAPI, Depends

app = FastAPI()

class RequestContext:
    """请求上下文（每个请求独立）"""

    def __init__(self, request_id: int):
        self.request_id = request_id
        self.counter = 0

def get_request_context(request_id: int) -> RequestContext:
    """每个请求创建独立的上下文"""
    return RequestContext(request_id)

@app.get("/test/{request_id}")
async def test(
    request_id: int,
    ctx: RequestContext = Depends(get_request_context)  # ← 每个请求独立
):
    ctx.counter += 1
    return {"request_id": ctx.request_id, "count": ctx.counter}

# 好处：
# - 每个请求有独立的上下文
# - 不会互相干扰
# - 线程安全
```

---

### 反模式 3：过度注入

**❌ 反模式**：

```python
class UserService:
    def __init__(
        self,
        user_repo: UserRepository,
        order_repo: OrderRepository,      # ← 为什么 UserService 需要 OrderRepo？
        product_repo: ProductRepository,  # ← 不相关
        email_service: EmailService,
        sms_service: SMSService,          # ← 太多依赖
        notification_service: NotificationService,
        logger: Logger,
        cache: Cache,
        event_bus: EventBus,
    ):
        # ❌ 太多依赖！职责不清

# 问题：
# 1. 难以维护（构造函数太长）
# 2. 职责混乱（为什么需要这么多服务？）
# 3. 难以测试（需要 Mock 很多依赖）
```

**✅ 正确模式**：

```python
class UserService:
    def __init__(
        self,
        user_repo: UserRepository,
        notification: NotificationService  # ← 聚合相关服务
    ):
        # ✅ 只注入真正需要的依赖
        self.user_repo = user_repo
        self.notification = notification

    async def create_user(self, user_data: UserCreate) -> User:
        user = await self.user_repo.save(user_data)
        await self.notification.send_welcome(user.email)
        return user

# 好处：
# 1. 依赖少而精
# 2. 职责清晰
# 3. 易于测试
```

---

### 反模式 4：在依赖中做 HTTP 请求

**❌ 反模式**：

```python
def get_current_user(token: str = Header(...)) -> User:
    """❌ 在依赖中发起 HTTP 请求"""
    # 阻塞的 HTTP 请求！
    response = requests.get(f"https://auth-api/verify?token={token}")
    if response.status_code != 200:
        raise HTTPException(401, "Invalid token")
    return User(**response.json())

@app.get("/profile")
async def get_profile(
    user: User = Depends(get_current_user)  # ← 阻塞！
):
    return user

# 问题：
# 1. 阻塞事件循环（requests 是同步的）
# 2. 性能差（每个请求都等待外部 API）
# 3. 不可靠（外部 API 故障会导致所有请求失败）
```

**✅ 正确模式**：

```python
async def get_current_user(
    token: str = Header(...),
    http_client: httpx.AsyncClient = Depends(get_http_client)  # ← 异步客户端
) -> User:
    """✅ 异步 HTTP 请求"""
    try:
        response = await http_client.get(
            f"https://auth-api/verify",
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code != 200:
            raise HTTPException(401, "Invalid token")
        return User(**response.json())
    except httpx.RequestError as e:
        raise HTTPException(503, "Auth service unavailable")

# 好处：
# 1. 异步非阻塞
# 2. 性能好
# 3. 错误处理完善
```

---

## 🧪 测试中的依赖注入

### 测试 Best Practice 1：使用 Mock Repository

```python
import pytest
from unittest.mock import Mock

# ═══════════════════════════════════════════════════════════
# 真实代码
# ═══════════════════════════════════════════════════════════

class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def create_user(self, user_data: UserCreate) -> User:
        if await self.repo.email_exists(user_data.email):
            raise UserEmailExistsException()
        user = User.create(user_data)
        return await self.repo.save(user)

# ═══════════════════════════════════════════════════════════
# 测试代码
# ═══════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_create_user_success():
    # 1. 创建 Mock Repository
    mock_repo = Mock(spec=UserRepository)
    mock_repo.email_exists.return_value = False  # 邮箱不存在
    mock_repo.save.return_value = User(id=1, username="alice", email="alice@example.com")

    # 2. 创建 Service（注入 Mock）
    service = UserService(mock_repo)

    # 3. 执行操作
    user_data = UserCreate(username="alice", email="alice@example.com", password="secret")
    result = await service.create_user(user_data)

    # 4. 验证结果
    assert result.id == 1
    assert result.username == "alice"

    # 5. 验证 Mock 被正确调用
    mock_repo.email_exists.assert_called_once_with("alice@example.com")
    mock_repo.save.assert_called_once()

@pytest.mark.asyncio
async def test_create_user_email_exists():
    # 1. 创建 Mock Repository
    mock_repo = Mock(spec=UserRepository)
    mock_repo.email_exists.return_value = True  # 邮箱已存在

    # 2. 创建 Service
    service = UserService(mock_repo)

    # 3. 执行操作（预期失败）
    user_data = UserCreate(username="alice", email="alice@example.com", password="secret")

    # 4. 验证抛出异常
    with pytest.raises(UserEmailExistsException):
        await service.create_user(user_data)

    # 5. 验证 save 没有被调用
    mock_repo.save.assert_not_called()
```

---

### 测试 Best Practice 2：Override 依赖

```python
from fastapi.testclient import TestClient
from unittest.mock import Mock

# ═══════════════════════════════════════════════════════════
# 真实代码
# ═══════════════════════════════════════════════════════════

app = FastAPI()

def get_user_service() -> UserService:
    """真实的服务（连接真实数据库）"""
    db = get_db()
    repo = SQLUserRepository(db)
    return UserService(repo)

@app.post("/users")
async def create_user(
    user: UserCreate,
    service: UserService = Depends(get_user_service)
):
    return await service.create_user(user)

# ═══════════════════════════════════════════════════════════
# 测试代码
# ═══════════════════════════════════════════════════════════

client = TestClient(app)

def test_create_user_with_mock():
    """使用 Mock 测试 Endpoint"""

    # 1. 创建 Mock Service
    mock_service = Mock(spec=UserService)
    mock_service.create_user.return_value = User(
        id=1, username="alice", email="alice@example.com"
    )

    # 2. Override 依赖
    app.dependency_overrides[get_user_service] = lambda: mock_service

    try:
        # 3. 测试 Endpoint
        response = client.post(
            "/users",
            json={"username": "alice", "email": "alice@example.com", "password": "secret"}
        )

        # 4. 验证响应
        assert response.status_code == 201
        assert response.json()["username"] == "alice"

        # 5. 验证 Mock 被调用
        mock_service.create_user.assert_called_once()

    finally:
        # 6. 清理 Override
        app.dependency_overrides = {}
```

---

### 测试 Best Practice 3：使用 Fixture

```python
import pytest
from fastapi.testclient import TestClient

# ═══════════════════════════════════════════════════════════
# Pytest Fixture
# ═══════════════════════════════════════════════════════════

@pytest.fixture
def mock_user_service():
    """Fixture: Mock UserService"""
    mock = Mock(spec=UserService)
    mock.get_user.return_value = User(
        id=1, username="alice", email="alice@example.com"
    )
    return mock

@pytest.fixture
def client_with_mock(mock_user_service):
    """Fixture: TestClient with Mock Service"""
    # Override 依赖
    app.dependency_overrides[get_user_service] = lambda: mock_user_service
    client = TestClient(app)
    yield client
    # 清理
    app.dependency_overrides = {}

# ═══════════════════════════════════════════════════════════
# 测试代码
# ═══════════════════════════════════════════════════════════

def test_get_user(client_with_mock):
    """测试 GET /users/1"""
    response = client_with_mock.get("/users/1")

    assert response.status_code == 200
    assert response.json()["username"] == "alice"
```

---

## ⚡ 性能优化建议

### 优化 1：使用 Application-scoped 缓存

**❌ 每次请求都创建**：

```python
def get_http_client() -> httpx.AsyncClient:
    """❌ 每次请求都创建新的 HTTP 客户端"""
    return httpx.AsyncClient()

@app.get("/external-api")
async def call_external_api(
    client: httpx.AsyncClient = Depends(get_http_client)
):
    response = await client.get("https://api.example.com/data")
    return response.json()

# 问题：
# - 每个请求都创建新客户端（浪费）
# - 无法复用连接池
```

**✅ 全局复用**：

```python
from fastapi import FastAPI

app = FastAPI()

# Application-scoped: 全局 HTTP 客户端
http_client = httpx.AsyncClient(timeout=30.0)

def get_http_client() -> httpx.AsyncClient:
    """✅ 返回全局客户端"""
    return http_client

@app.get("/external-api")
async def call_external_api(
    client: httpx.AsyncClient = Depends(get_http_client)
):
    response = await client.get("https://api.example.com/data")
    return response.json()

# 好处：
# - 复用连接池
# - 性能更好
```

---

### 优化 2：利用依赖缓存

```python
from fastapi import Depends

class ExpensiveOperation:
    """昂贵的操作（如加载大模型）"""

    def __init__(self):
        print("⏳ 加载模型...")
        self.model = load_large_model()  # 耗时操作
        print("✅ 模型加载完成")

def get_model():
    """❌ 每次都重新加载"""
    return ExpensiveOperation()

# 同一个请求中多次使用
@app.post("/predict")
async def predict(
    model1: ExpensiveOperation = Depends(get_model),
    model2: ExpensiveOperation = Depends(get_model),  # 重新加载！
):
    # ❌ 会打印两次 "⏳ 加载模型..."
    return {"result": "ok"}

# ═══════════════════════════════════════════════════════════

# ✅ 正确：利用缓存

@app.post("/predict")
async def predict(
    model: ExpensiveOperation = Depends(get_model)
):
    # ✅ 同一个请求内，model1 和 model2 是同一个实例
    return {"result": "ok"}
```

---

### 优化 3：惰性初始化

```python
from fastapi import FastAPI, Depends

app = FastAPI()

class LazyCache:
    """惰性初始化的缓存"""

    def __init__(self):
        self._cache = None

    def __call__(self) -> Cache:
        if self._cache is None:
            print("📦 首次创建缓存")
            self._cache = Cache()
        return self._cache

# Application-scoped: 惰性初始化
cache_provider = LazyCache()

def get_cache() -> Cache:
    """返回缓存（首次使用时才创建）"""
    return cache_provider()

# 特点：
# - 应用启动时不创建缓存
# - 第一次请求时才创建
# - 后续请求复用
```

---

## 🔒 安全考虑

### 安全 1：验证依赖参数

```python
from fastapi import Depends, Header

def get_current_user(
    authorization: str = Header(...)  # ← 必须提供
) -> User:
    """验证认证 Token"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Invalid authorization format")

    token = authorization.split(" ")[1]
    if not token:
        raise HTTPException(401, "Missing token")

    # 验证 token
    user = verify_token(token)
    if not user:
        raise HTTPException(401, "Invalid token")

    return user

@app.get("/profile")
async def get_profile(
    user: User = Depends(get_current_user)  # ← 自动验证
):
    return user
```

---

### 安全 2：限制敏感操作

```python
from fastapi import Depends

def require_admin(user: User = Depends(get_current_user)) -> User:
    """要求管理员权限"""
    if not user.is_admin:
        raise HTTPException(403, "Admin access required")
    return user

@app.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    admin: User = Depends(require_admin)  # ← 必须是管理员
):
    await delete_user_from_db(user_id)
    return {"message": "User deleted"}
```

---

## 🎯 生产环境检查清单

### 部署前检查

- [ ] **依赖测试**：所有 Service 都有单元测试
- [ ] **Mock 测试**：使用 Mock Repository 进行测试
- [ ] **异常处理**：所有依赖都有异常处理
- [ ] **资源清理**：使用 `yield` 的依赖都有 `finally` 块
- [ ] **生命周期**：正确选择 Request-scoped vs Application-scoped
- [ ] **性能测试**：测试依赖创建的性能
- [ ] **文档**：复杂依赖都有文档说明

### 代码审查检查

- [ ] **职责清晰**：每个依赖只做一件事
- [ ] **依赖最少**：Service 的依赖数量合理（< 5 个）
- [ ] **接口抽象**：依赖接口而不是具体实现
- [ ] **无全局状态**：没有全局可变状态
- [ ] **异步正确**：所有 I/O 操作都是异步的
- [ ] **错误处理**：所有异常都被正确处理

---

## 📚 检查理解

回答这些问题来测试你的理解：

1. **什么是服务定位器反模式？**
   - 提示：主动获取依赖 vs 被动接收

2. **如何测试 Service 层？**
   - 提示：注入 Mock Repository

3. **如何 Override 依赖进行测试？**
   - 提示：`app.dependency_overrides`

4. **什么时候使用 Application-scoped？**
   - 提示：需要全局共享时

5. **如何避免全局可变状态？**
   - 提示：使用 Request-scoped 依赖

---

## 🚀 Level 2 总结

恭喜你完成了 Level 2 的学习！

**你已经掌握**：
- ✅ 依赖注入的基本概念
- ✅ 函数依赖 vs 类依赖
- ✅ Request-scoped vs Application-scoped
- ✅ 完整的三层架构实现
- ✅ 最佳实践和常见陷阱

**下一步**：
- 📖 学习 **Level 3**：外部系统集成
- 📖 学习 **数据库**：SQLAlchemy + Alembic
- 📖 学习 **缓存**：Redis 集成

记住：**依赖注入是生产架构的核心，掌握它让代码变得清晰、可测试、可维护！**

---

**费曼技巧总结**：
- ✅ 常见反模式对比
- ✅ 测试最佳实践
- ✅ 性能优化建议
- ✅ 安全考虑
- ✅ 生产环境检查清单
