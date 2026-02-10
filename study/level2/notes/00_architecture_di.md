# 00 依赖注入架构设计 - 分层架构的粘合剂

## 📖 为什么需要理解依赖注入？

在深入学习 FastAPI 的依赖注入系统之前，我们需要理解：**依赖注入是实现分层架构的关键技术。**

如果没有依赖注入：
- ❌ 无法真正实现分层架构
- ❌ 代码难以测试
- ❌ 业务逻辑被绑在 HTTP 层
- ❌ 无法复用

有了依赖注入：
- ✅ 真正的分层架构成为可能
- ✅ 代码变得可测试、可复用
- ✅ 各层清晰分离
- ✅ 易于维护和演进

---

## 🏗️ 依赖注入在分层架构中的位置

### Level 1 vs Level 2 的架构演进

```
┌─────────────────────────────────────────────────────────────┐
│                  Level 1: 传输层（没有依赖注入）              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              FastAPI Endpoint                               │
│  @app.post("/users")                                       │
│  async def create_user(user: UserCreate):                  │
│      # ❌ 业务逻辑混在传输层                                │
│      if await db.query("..."):                             │
│          raise HTTPException(409)                          │
│      hashed = hash_password(user.password)                 │
│      user_id = await db.insert("...")                      │
│      return {"id": user_id}                                │
└─────────────────────────────────────────────────────────────┘

问题：
- 业务逻辑无法复用（CLI、gRPC 无法使用）
- 难以测试（必须启动 HTTP 服务器）
- 违反分层架构原则

═══════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────┐
│            Level 2: 分层架构（使用依赖注入）                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              FastAPI Endpoint (传输层)                      │
│  @app.post("/users")                                       │
│  async def create_user(                                    │
│      user: UserCreate,                                     │
│      service: UserService = Depends(get_user_service) ← DI │
│  ):                                                        │
│      # ✅ 只做协议适配                                      │
│      return await service.create_user(user)                │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ 依赖注入
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              UserService (服务层)                           │
│  class UserService:                                        │
│      def __init__(self, repo: UserRepository): ← 依赖抽象   │
│          self.repo = repo                                  │
│                                                          │
│      async def create_user(self, user_data):              │
│          # ✅ 业务逻辑在这里                                │
│          if await self.repo.email_exists(...):            │
│              raise UserEmailExistsException()              │
│          user = User.create(user_data)                     │
│          return await self.repo.save(user)                │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ 依赖注入
                          ▼
┌─────────────────────────────────────────────────────────────┐
│           UserRepository (基础设施层)                       │
│  class SQLUserRepository(UserRepository):                 │
│      def __init__(self, db: AsyncSession): ← 依赖抽象       │
│          self.session = db                                │
│                                                          │
│      async def save(self, user: User) -> User:            │
│          # ✅ 数据持久化在这里                              │
│          self.session.add(user)                           │
│          await self.session.commit()                      │
│          return user                                      │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ 依赖注入
                          ▼
┌─────────────────────────────────────────────────────────────┐
│           Database (PostgreSQL)                            │
└─────────────────────────────────────────────────────────────┘
```

**演进的关键**：依赖注入让各层可以**解耦**和**独立演化**。

---

## 🎯 依赖注入的本质

### 什么是依赖？

**依赖 (Dependency)**：一个对象需要另一个对象才能完成工作。

```python
class UserService:
    def __init__(self):
        self.db = Database()  # UserService 依赖 Database
```

**问题**：`UserService` 必须知道如何创建 `Database`，这导致：
- ❌ 紧耦合（无法换数据库）
- ❌ 难以测试（无法用 Mock 替换）
- ❌ 职责混乱（创建 + 使用）

### 什么是依赖注入？

**依赖注入 (Dependency Injection, DI)**：把依赖的创建交给外部，对象只负责使用。

```python
# ✅ 使用依赖注入
class UserService:
    def __init__(self, db: Database):  # 依赖作为参数传入
        self.db = db  # 只负责使用，不负责创建

# 外部负责创建和注入
db = Database()
user_service = UserService(db)  # 注入依赖
```

**优势**：
- ✅ 解耦（不知道如何创建，只知道如何使用）
- ✅ 可测试（测试时注入 Mock）
- ✅ 可复用（可以在不同场景注入不同实现）

### 依赖注入的三种方式

#### 1. 构造函数注入（推荐）

```python
class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo  # 通过构造函数注入

# 优点：
# ✅ 依赖明确（看构造函数就知道需要什么）
# ✅ 不可变（初始化后不能改变）
# ✅ 易于测试
```

#### 2. Setter 注入

```python
class UserService:
    def set_repo(self, repo: UserRepository):
        self.repo = repo  # 通过 setter 注入

# 缺点：
# ❌ 依赖不明确（不知道何时设置了依赖）
# ❌ 可变（依赖可以在运行时改变）
# ❌ 容易忘记注入
```

#### 3. 接口注入

```python
class UserService(Injectable):
    def inject_dependencies(self, repo: UserRepository):
        self.repo = repo  # 通过接口方法注入

# 缺点：
# ❌ 需要额外的接口
# ❌ 不够直观
```

**FastAPI 使用构造函数注入（通过 `Depends`）**。

---

## 🔧 FastAPI 的依赖注入系统

### FastAPI DI 的核心概念

```python
from fastapi import Depends

# 1. 定义依赖（可调用对象）
def get_user_service() -> UserService:
    """依赖提供者"""
    db = get_db()
    repo = UserRepository(db)
    return UserService(repo)

# 2. 使用依赖（FastAPI 自动注入）
@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service)  # 自动注入
):
    return await service.get_user(user_id)
```

### FastAPI DI 的工作流程

```
HTTP Request: GET /users/123
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│ FastAPI 依赖注入引擎                                    │
│                                                         │
│ 1. 解析依赖：                                           │
│    service: UserService = Depends(get_user_service)    │
│                                                         │
│ 2. 解析依赖链：                                         │
│    get_user_service()                                  │
│      → get_db()  (get_user_service 的依赖)             │
│      → get_db() 返回 AsyncSession                       │
│      → UserRepository(db)                              │
│      → UserService(repo)                               │
│      → 返回 UserService 实例                            │
│                                                         │
│ 3. 注入依赖：                                           │
│    调用 endpoint 函数                                   │
│    service = get_user_service()  # 自动执行            │
│    get_user(123, service)                              │
│                                                         │
│ 4. 缓存依赖：                                           │
│    同一个请求中再次使用 Depends(get_user_service)      │
│    → 不会重新创建，使用缓存的实例                       │
└─────────────────────────────────────────────────────────┘
    │
    ▼
HTTP Response
```

### FastAPI DI 的优势

#### 1. 自动管理依赖

```python
# ❌ 手动管理（繁琐）
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    # 手动创建依赖
    db = create_db_connection()
    repo = UserRepository(db)
    service = UserService(repo)
    # 使用依赖
    return await service.get_user(user_id)

# ✅ 自动管理（简洁）
@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service)  # 自动
):
    return await service.get_user(user_id)
```

#### 2. 依赖缓存

```python
@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    service1: UserService = Depends(get_user_service),
    service2: UserService = Depends(get_user_service)  # 不会重新创建
):
    # service1 和 service2 是同一个实例
    assert service1 is service2  # True
```

#### 3. 嵌套依赖

```python
def get_db() -> AsyncSession:
    """数据库连接"""
    return async_session()

def get_repo(db: AsyncSession = Depends(get_db)) -> UserRepository:
    """仓储（依赖 db）"""
    return UserRepository(db)

def get_service(repo: UserRepository = Depends(get_repo)) -> UserService:
    """服务（依赖 repo）"""
    return UserService(repo)

@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    service: UserService = Depends(get_service)  # 自动解析整个依赖链
):
    return await service.get_user(user_id)
```

**依赖链**：
```
get_user
  → Depends(get_service)
    → Depends(get_repo)
      → Depends(get_db)
```

---

## 🎨 分层架构中的依赖注入

### 依赖倒置原则

**核心思想**：高层不应依赖低层，都应依赖抽象。

```
┌─────────────────────────────────────────────────────────────┐
│              错误的依赖方向（高层依赖低层）                  │
└─────────────────────────────────────────────────────────────┘

Endpoint (高层)
    │ 依赖
    ▼
Service (中层)
    │ 依赖具体实现
    ▼
SQLUserRepository (低层)
    │ 依赖
    ▼
Database

问题：
- Service 被绑死在 SQL 实现
- 无法换数据库（如从 PostgreSQL 换到 MongoDB）
- 无法测试（无法用 Mock 替换）

═══════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────┐
│              正确的依赖方向（依赖倒置）                      │
└─────────────────────────────────────────────────────────────┘

Endpoint (高层)
    │ 依赖接口
    ▼
Service (中层)
    │ 依赖接口
    ▼
UserRepository (抽象接口 - 在 Domain 层定义)
    ▲
    │ 实现接口
    │
SQLUserRepository (具体实现 - 在 Infrastructure 层)
    │ 依赖
    ▼
Database

优势：
- Service 只依赖接口，不依赖具体实现
- 可以轻松换数据库
- 测试时注入 Mock
```

### 分层架构的依赖关系

```python
# ══════════════════════════════════════════════════════════════
# 领域层 (Domain Layer) - 定义接口
# ══════════════════════════════════════════════════════════════

from abc import ABC, abstractmethod

class UserRepository(ABC):
    """用户仓储接口（抽象）"""

    @abstractmethod
    async def save(self, user: User) -> User:
        pass

    @abstractmethod
    async def find_by_id(self, user_id: int) -> Optional[User]:
        pass

# ══════════════════════════════════════════════════════════════
# 基础设施层 (Infrastructure Layer) - 实现接口
# ══════════════════════════════════════════════════════════════

class SQLUserRepository(UserRepository):
    """SQL 实现（具体）"""

    def __init__(self, db: AsyncSession):
        self.session = db

    async def save(self, user: User) -> User:
        self.session.add(user)
        await self.session.commit()
        return user

    async def find_by_id(self, user_id: int) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

# ══════════════════════════════════════════════════════════════
# 服务层 (Service Layer) - 依赖接口
# ══════════════════════════════════════════════════════════════

class UserService:
    """用户服务（依赖抽象，不依赖具体）"""

    def __init__(self, repo: UserRepository):  # ← 依赖接口
        self.repo = repo

    async def create_user(self, user_data: UserCreate) -> User:
        # 业务逻辑
        user = User.create(user_data)
        return await self.repo.save(user)

# ══════════════════════════════════════════════════════════════
# 传输层 (Transport Layer) - 使用依赖注入
# ══════════════════════════════════════════════════════════════

from fastapi import Depends

def get_db() -> AsyncSession:
    """数据库会话（依赖）"""
    return async_session()

def get_user_repo(db: AsyncSession = Depends(get_db)) -> UserRepository:
    """仓储（依赖 db，返回接口的具体实现）"""
    return SQLUserRepository(db)

def get_user_service(
    repo: UserRepository = Depends(get_user_repo)
) -> UserService:
    """服务（依赖 repo）"""
    return UserService(repo)

@app.post("/users")
async def create_user(
    user: UserCreate,
    service: UserService = Depends(get_user_service)  # ← 自动注入
):
    """Endpoint（依赖 service）"""
    return await service.create_user(user)
```

**关键点**：
1. `UserService` 依赖 `UserRepository` **接口**，不依赖具体实现
2. `get_user_service()` 负责组装具体实现
3. FastAPI 自动解析依赖链

---

## 🔄 依赖注入让代码可测试

### 没有依赖注入的测试（困难）

```python
# ❌ 代码紧耦合，难以测试
class UserService:
    def __init__(self):
        self.db = PostgreSQL()  # 硬编码

    async def get_user(self, user_id: int):
        return await self.db.query(f"SELECT * FROM users WHERE id = {user_id}")

# 测试时必须启动真实的数据库
async def test_get_user():
    service = UserService()  # 需要 PostgreSQL 连接！
    user = await service.get_user(1)
    assert user.name == "Alice"
```

### 使用依赖注入的测试（简单）

```python
# ✅ 代码解耦，易于测试
class UserService:
    def __init__(self, repo: UserRepository):  # 依赖接口
        self.repo = repo

    async def get_user(self, user_id: int):
        return await self.repo.find_by_id(user_id)

# 测试时注入 Mock
class MockUserRepository(UserRepository):
    """Mock 仓储（不需要数据库）"""
    def __init__(self):
        self.users = {
            1: User(id=1, name="Alice"),
            2: User(id=2, name="Bob"),
        }

    async def find_by_id(self, user_id: int) -> Optional[User]:
        return self.users.get(user_id)

    async def save(self, user: User) -> User:
        pass

# 测试（不需要数据库）
async def test_get_user():
    mock_repo = MockUserRepository()
    service = UserService(mock_repo)  # 注入 Mock
    user = await service.get_user(1)
    assert user.name == "Alice"  # ✅ 测试通过
```

---

## 💡 依赖注入的设计模式

### 工厂模式（Factory Pattern）

```python
class UserServiceFactory:
    """服务工厂（负责创建服务）"""

    @staticmethod
    def create_user_service() -> UserService:
        db = create_db_connection()
        repo = UserRepository(db)
        return UserService(repo)

# 使用
service = UserServiceFactory.create_user_service()
```

### 容器模式（Container Pattern）

```python
class DIContainer:
    """依赖注入容器（管理所有依赖）"""

    def __init__(self):
        self._singletons = {}  # 单例缓存
        self._factories = {}   # 工厂方法

    def register_singleton(self, key: str, factory):
        """注册单例"""
        self._factories[key] = factory

    def get(self, key: str):
        """获取实例"""
        if key not in self._singletons:
            self._singletons[key] = self._factories[key]()
        return self._singletons[key]

# 使用
container = DIContainer()
container.register_singleton("db", lambda: create_db())
container.register_singleton("user_service", lambda: UserService(container.get("db")))

service = container.get("user_service")
```

**FastAPI 的内置容器**：
- FastAPI 有自己的 DI 容器
- `Depends` 就是从容器中获取依赖
- 不需要手动管理容器

---

## ⚠️ 常见的 DI 反模式

### 反模式 1：服务定位器 (Service Locator)

```python
# ❌ 反模式：服务定位器
class UserService:
    def __init__(self):
        self.repo = ServiceLocator.get("user_repo")  # 主动获取

# 问题：
# - 依赖关系不明确（看构造函数不知道需要什么）
# - 难以测试（需要设置 ServiceLocator）
# - 隐式依赖（依赖被隐藏）

# ✅ 正确：依赖注入
class UserService:
    def __init__(self, repo: UserRepository):  # 依赖明确
        self.repo = repo
```

### 反模式 2：紧耦合的工厂

```python
# ❌ 反模式：工厂紧耦合具体实现
class UserServiceFactory:
    @staticmethod
    def create() -> UserService:
        db = PostgreSQL()  # 硬编码
        repo = SQLUserRepository(db)
        return UserService(repo)

# 问题：无法换数据库

# ✅ 正确：工厂接受配置
class UserServiceFactory:
    @staticmethod
    def create(db: Database) -> UserService:
        repo = SQLUserRepository(db)
        return UserService(repo)
```

### 反模式 3：过度注入

```python
# ❌ 反模式：注入过多依赖
class UserService:
    def __init__(
        self,
        user_repo: UserRepository,
        order_repo: OrderRepository,
        product_repo: ProductRepository,
        email_service: EmailService,
        sms_service: SMSService,
        notification_service: NotificationService,
        logger: Logger,
        cache: Cache,
    ):
        # 太多依赖！

# ✅ 正确：拆分服务
class UserService:
    def __init__(self, user_repo: UserRepository, notification: NotificationService):
        self.user_repo = user_repo
        self.notification = notification
```

---

## 🧐 理解验证

### 自我检查问题

1. **依赖注入的核心思想是？**
   - A. 自己创建依赖
   - B. 让别人提供依赖
   - C. 使用工厂模式
   - D. 使用单例模式

2. **FastAPI 中如何使用依赖注入？**
   - A. 使用 `@Inject` 装饰器
   - B. 使用 `Depends()` 函数
   - C. 手动创建依赖
   - D. 使用全局变量

3. **依赖倒置原则的意思是？**
   - A. 高层依赖低层
   - B. 低层依赖高层
   - C. 都依赖抽象
   - D. 不依赖任何东西

4. **为什么依赖注入让代码更可测试？**
   - A. 代码运行更快
   - B. 可以注入 Mock 对象
   - C. 减少代码量
   - D. 自动生成测试

5. **以下哪个是正确的依赖注入方式？**
   - A. 构造函数注入
   - B. Setter 注入
   - C. 全局变量
   - D. 单例模式

<details>
<summary>点击查看答案</summary>

1. ✅ B. 让别人提供依赖
2. ✅ B. 使用 `Depends()` 函数
3. ✅ C. 都依赖抽象
4. ✅ B. 可以注入 Mock 对象
5. ✅ A. 构造函数注入

</details>

---

## 📝 记忆口诀

```
依赖注入记心间，
不要自己找依赖。
别人提供给你用，
测试复用都方便。

构造函数来注入，
依赖明确不隐藏。
依赖倒置是核心，
高层不把低层赖。

FastAPI 的 Depends，
自动解析依赖链。
缓存优化性能好，
分层架构靠它连。
```

---

## 🚀 下一步

现在你已经理解了依赖注入的架构设计，可以开始学习 Level 2 的具体内容：

1. **依赖基础** → `notes/01_dependency_basics.md`
2. **类依赖 vs 函数依赖** → `notes/02_class_vs_function.md`
3. **依赖的生命周期** → `notes/03_dependency_lifecycle.md`
4. **实现服务层** → `notes/04_service_layer.md`
5. **最佳实践** → `notes/05_best_practices.md`

记住：**依赖注入是实现分层架构的关键技术！**

---

## 📚 延伸阅读

- [FastAPI Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [Dependency Inversion Principle](https://en.wikipedia.org/wiki/Dependency_inversion_principle)
- [Inversion of Control](https://en.wikipedia.org/wiki/Inversion_of_control)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

---

**掌握依赖注入，你的代码将变得清晰、可测试、可维护！** 🎯
