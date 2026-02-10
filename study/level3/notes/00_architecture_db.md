# 00 数据库架构设计 - 持久化层的分层实现

## 📖 为什么需要理解数据库架构设计？

在深入学习数据库集成之前，我们需要理解：**数据库集成不是简单地添加 SQL 代码，而是通过 Repository 模式将持久化逻辑隔离在专门的层中。**

如果没有正确的架构：
- ❌ Service 被绑死在具体的数据库实现
- ❌ 数据访问逻辑散落在各处
- ❌ 无法进行单元测试
- ❌ 难以切换数据库

有了正确的架构：
- ✅ Service 只依赖 Repository 接口
- ✅ 所有数据访问逻辑集中在 Repository
- ✅ 可以注入 Mock 进行单元测试
- ✅ 可以轻松切换数据库实现

---

## 🏗️ 数据库在分层架构中的位置

### 数据持久化层架构

```
┌─────────────────────────────────────────────────────────────┐
│              分层架构中的数据库集成                          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              FastAPI Endpoint (传输层)                      │
│  @app.post("/users")                                       │
│  async def create_user(                                    │
│      user: UserCreate,                                     │
│      service: UserService = Depends(get_user_service)      │
│  ):                                                        │
│      # ✅ 只做协议适配                                      │
│      return await service.create_user(user)                │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ 调用服务层
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              UserService (服务层)                           │
│  class UserService:                                        │
│      def __init__(self, repo: UserRepository):            │
│          self.repo = repo  # ← 依赖接口（抽象）            │
│                                                          │
│      async def create_user(self, user_data: UserCreate):   │
│          # ✅ 业务逻辑                                      │
│          if await self.repo.email_exists(user_data.email): │
│              raise UserEmailExistsException()              │
│          user = User.create(user_data)                     │
│          return await self.repo.save(user)                │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ 依赖接口
                          ▼
┌─────────────────────────────────────────────────────────────┐
│         UserRepository (领域层定义接口)                     │
│  class UserRepository(ABC):                                │
│      @abstractmethod                                      │
│      async def save(self, user: User) -> User: ...        │
│                                                          │
│      @abstractmethod                                      │
│      async def find_by_email(self, email: str) -> ...     │
└─────────────────────────────────────────────────────────────┘
                          ▲
                          │ 实现接口
                          │
┌─────────────────────────────────────────────────────────────┐
│      SQLUserRepository (基础设施层 - SQL 实现)             │
│  class SQLUserRepository(UserRepository):                 │
│      def __init__(self, session: AsyncSession):            │
│          self.session = session  # ← 依赖抽象             │
│                                                          │
│      async def save(self, user: User) -> User:            │
│          # ✅ 数据持久化逻辑                                │
│          self.session.add(user)                           │
│          await self.session.commit()                      │
│          return user                                      │
│                                                          │
│      async def find_by_email(self, email: str):          │
│          # ✅ SQL 查询逻辑                                 │
│          result = await self.session.execute(             │
│              select(User).where(User.email == email)       │
│          )                                               │
│          return result.scalar_one_or_none()                │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ SQLAlchemy ORM
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Database (PostgreSQL/MySQL)                    │
└─────────────────────────────────────────────────────────────┘
```

**关键点**：
1. **Service 只依赖接口** - 不知道底层是 SQL 还是 NoSQL
2. **Repository 封装数据访问** - 所有 SQL 逻辑都在这里
3. **依赖注入连接各层** - FastAPI 自动组装依赖链

---

## 🎯 Repository 模式深度解析

### 为什么需要 Repository 模式？

#### 问题：直接在 Service 中使用数据库

```python
# ❌ 错误示例：Service 直接使用 SQLAlchemy
from sqlalchemy.ext.asyncio import AsyncSession

class UserService:
    async def create_user(self, user_data: UserCreate, session: AsyncSession):
        # 问题 1: Service 被绑死在 SQLAlchemy
        user = User(**user_data.dict())
        session.add(user)
        await session.commit()

        # 问题 2: 无法切换数据库（如从 PostgreSQL 换到 MongoDB）
        # 问题 3: 难以测试（必须启动数据库）
        # 问题 4: 数据访问逻辑散落在 Service 中
```

**问题分析**：
- ❌ **紧耦合** - Service 被绑死在 SQLAlchemy
- ❌ **难以测试** - 必须启动真实数据库
- ❌ **逻辑混乱** - 业务逻辑和数据访问混在一起
- ❌ **无法复用** - 数据访问逻辑无法在其他场景使用

#### 解决方案：Repository 模式

```python
# ✅ 正确示例：使用 Repository 模式

# 1. 在领域层定义接口（Level 3 开始）
class UserRepository(ABC):
    """用户仓储接口（抽象）"""

    @abstractmethod
    async def save(self, user: User) -> User:
        pass

    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[User]:
        pass

# 2. 在基础设施层实现（Level 3）
class SQLUserRepository(UserRepository):
    """SQL 实现（具体）"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, user: User) -> User:
        self.session.add(user)
        await self.session.commit()
        return user

    async def find_by_email(self, email: str) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

# 3. 在服务层使用（Level 2）
class UserService:
    def __init__(self, repo: UserRepository):  # ← 依赖接口
        self.repo = repo

    async def create_user(self, user_data: UserCreate) -> User:
        # ✅ 业务逻辑
        if await self.repo.email_exists(user_data.email):
            raise UserEmailExistsException(user_data.email)

        user = User.create(user_data)
        return await self.repo.save(user)  # ← 调用接口
```

**优势**：
- ✅ **解耦** - Service 只依赖接口，不依赖具体实现
- ✅ **可测试** - 可以注入 Mock Repository
- ✅ **可切换** - 可以轻松换数据库实现
- ✅ **职责清晰** - 数据访问逻辑集中在 Repository

### Repository 的职责边界

```
┌─────────────────────────────────────────────────────────────┐
│              Repository 的职责边界                           │
└─────────────────────────────────────────────────────────────┘

✅ Repository 应该做的事：
   1. CRUD 操作（增删改查）
   2. SQL 查询
   3. 数据映射（ORM 对象 ↔ 数据库行）
   4. 连接管理

❌ Repository 不应该做的事：
   1. 业务规则验证（如：密码强度、余额是否足够）
   2. 事务管理（事务边界在 Service 层）
   3. 调用外部服务（如：发送邮件）
   4. 复杂的数据处理（应该在 Domain 层）
```

**示例对比**：

```python
# ❌ 错误：Repository 包含业务逻辑
class SQLUserRepository(UserRepository):
    async def create_user(self, user_data: UserCreate) -> User:
        # ❌ 业务规则：检查密码强度
        if len(user_data.password) < 8:
            raise ValueError("Password too weak")

        # ❌ 业务逻辑：发送欢迎邮件
        send_welcome_email(user_data.email)

        # ✅ 数据持久化（这是 Repository 该做的）
        user = User(**user_data.dict())
        self.session.add(user)
        await self.session.commit()
        return user

# ✅ 正确：Repository 只负责数据访问
class SQLUserRepository(UserRepository):
    async def save(self, user: User) -> User:
        # ✅ 只做数据持久化
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

# 业务逻辑在 Service 层
class UserService:
    async def create_user(self, user_data: UserCreate) -> User:
        # ✅ 业务规则验证
        if not self.is_password_strong(user_data.password):
            raise WeakPasswordException()

        # ✅ 创建领域对象
        user = User.create(user_data)

        # ✅ 调用 Repository 保存
        saved_user = await self.repo.save(user)

        # ✅ 副作用（通过领域事件）
        user.publish_event(UserCreated(saved_user.id))

        return saved_user
```

---

## 🔧 SQLAlchemy 集成架构

### SQLAlchemy 的两种用法

#### Core vs ORM

```
┌─────────────────────────────────────────────────────────────┐
│              SQLAlchemy Core (SQL 表达式)                    │
└─────────────────────────────────────────────────────────────┘

from sqlalchemy import insert, select

# 使用 Core（接近原始 SQL）
stmt = insert(User).values(name="Alice", email="alice@example.com")
result = await session.execute(stmt)

优势：
- ✅ 性能更好（接近原生 SQL）
- ✅ 更灵活（可以使用数据库特定功能）
- ✅ 适合复杂查询

劣势：
- ❌ 不够类型安全
- ❌ 需要手动处理映射
- ❌ 代码冗长

═══════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────┐
│              SQLAlchemy ORM (对象关系映射)                  │
└─────────────────────────────────────────────────────────────┘

from sqlalchemy.orm import select

# 使用 ORM（面向对象）
user = User(name="Alice", email="alice@example.com")
session.add(user)
await session.commit()

优势：
- ✅ 类型安全
- ✅ 面向对象（更 Pythonic）
- ✅ 自动映射
- ✅ 关系管理

劣势：
- ❌ 性能略低（有开销）
- ❌ 学习曲线
```

**Level 3 的选择**：
- 主要使用 **ORM**（更符合分层架构）
- 复杂查询使用 **Core**（性能优化）

### SQLAlchemy 架构设计

```python
# ══════════════════════════════════════════════════════════════
# 1. 模型定义（Domain/Infrastructure 边界）
# ══════════════════════════════════════════════════════════════

from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    """所有模型的基类"""
    pass

class User(Base):
    """用户模型（映射到数据库表）"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # ══════════════════════════════════════════════════════════════
    # 架构说明：Model vs Entity
    # ══════════════════════════════════════════════════════════════
    #
    # SQLAlchemy Model（这里）：
    # - 负责数据库映射
    # - 字段定义、关系定义
    # - 表结构
    #
    # Domain Entity（在领域层）：
    # - 包含业务逻辑
    # - 行为方法
    # - 业务规则
    #
    # ══════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════
# 2. 数据库引擎配置（基础设施层）
# ══════════════════════════════════════════════════════════════

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# 创建异步引擎
engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost/dbname",
    echo=False,  # 生产环境设为 False
    pool_size=5,  # 连接池大小
    max_overflow=10  # 最大溢出连接数
)

# 创建会话工厂
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False  # 避免访问过期对象
)

# ══════════════════════════════════════════════════════════════
# 3. 依赖注入配置（传输层）
# ══════════════════════════════════════════════════════════════

from fastapi import Depends

async def get_db() -> AsyncSession:
    """
    获取数据库会话（依赖）

    架构说明：
    - Request-scoped：每个请求创建新会话
    - 自动管理连接：请求结束自动关闭
    - 事务边界：在 Service 层控制
    """
    async with async_session() as session:
        yield session

# ══════════════════════════════════════════════════════════════
# 4. Repository 实现（基础设施层）
# ══════════════════════════════════════════════════════════════

class SQLUserRepository(UserRepository):
    """
    SQL 用户仓储（具体实现）

    架构职责：
    - 封装 SQLAlchemy 操作
    - 实现数据访问逻辑
    - 不包含业务规则
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, user: User) -> User:
        """保存用户（插入或更新）"""
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def find_by_id(self, user_id: int) -> Optional[User]:
        """根据 ID 查询用户"""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def find_by_email(self, email: str) -> Optional[User]:
        """根据邮箱查询用户"""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def find_all(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """查询所有用户（分页）"""
        result = await self.session.execute(
            select(User)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

# ══════════════════════════════════════════════════════════════
# 5. 依赖注入链（传输层）
# ══════════════════════════════════════════════════════════════

def get_user_repo(db: AsyncSession = Depends(get_db)) -> UserRepository:
    """
    获取用户仓储（依赖）

    依赖链：
    get_user_repo
      → Depends(get_db)
      → 返回 SQLUserRepository(db)
    """
    return SQLUserRepository(db)

def get_user_service(
    repo: UserRepository = Depends(get_user_repo)
) -> UserService:
    """
    获取用户服务（依赖）

    依赖链：
    get_user_service
      → Depends(get_user_repo)
      → Depends(get_db)
      → 返回 UserService(repo)
    """
    return UserService(repo)

# ══════════════════════════════════════════════════════════════
# 6. Endpoint 使用（传输层）
# ══════════════════════════════════════════════════════════════

@app.post("/users")
async def create_user(
    user: UserCreate,
    service: UserService = Depends(get_user_service)  # ← 自动注入
):
    """
    创建用户（Endpoint）

    依赖注入流程：
    1. FastAPI 看到 Depends(get_user_service)
    2. 解析依赖链：
       get_user_service
         → get_user_repo
           → get_db
             → async_session()  ← 创建会话
       → SQLUserRepository(db)
       → UserService(repo)
    3. 调用 endpoint：create_user(..., service)
    4. service.create_user() 完成业务逻辑
    5. 请求结束，会话自动关闭
    """
    return await service.create_user(user)
```

---

## 🔄 事务管理架构

### 事务边界的设计

```
┌─────────────────────────────────────────────────────────────┐
│              事务边界应该在 Service 层                      │
└─────────────────────────────────────────────────────────────┘

@app.post("/orders")
async def create_order(
    order_data: OrderCreate,
    service: OrderService = Depends(),
    db: AsyncSession = Depends(get_db)  # ← 事务会话
):
    """
    创建订单（事务边界示例）

    架构原则：
    - Service 层控制事务的起止
    - 多个 Repository 操作在一个事务中
    - 成功则 commit，失败则 rollback
    """
    try:
        # 开始事务（隐式）
        order = await service.create_order(order_data)

        # 提交事务
        await db.commit()

        return order
    except Exception as e:
        # 回滚事务
        await db.rollback()
        raise
```

### Service 层的事务管理

```python
class OrderService:
    """订单服务（演示事务管理）"""

    async def create_order(
        self,
        order_data: OrderCreate,
        user_repo: UserRepository,
        product_repo: ProductRepository,
        order_repo: OrderRepository
    ) -> Order:
        """
        创建订单（涉及多个 Repository）

        事务说明：
        - 所有数据库操作在一个事务中
        - 任何步骤失败，整个操作回滚
        - 保证数据一致性
        """
        # 1. 查询用户（读操作）
        user = await user_repo.find_by_id(order_data.user_id)
        if not user:
            raise UserNotFoundException(order_data.user_id)

        # 2. 查询商品（读操作）
        product = await product_repo.find_by_id(order_data.product_id)
        if not product:
            raise ProductNotFoundException(order_data.product_id)

        # 3. 检查库存（业务规则）
        if product.stock < order_data.quantity:
            raise InsufficientStockException()

        # 4. 创建订单（写操作）
        order = Order.create(
            user_id=user.id,
            product_id=product.id,
            quantity=order_data.quantity
        )

        # 5. 扣减库存（写操作）
        product.decrease_stock(order_data.quantity)

        # 6. 保存订单和商品（在同一事务中）
        saved_order = await order_repo.save(order)
        await product_repo.save(product)

        return saved_order
        # 如果任何步骤抛出异常，FastAPI 会自动 rollback
```

---

## 🎨 从 Level 2 到 Level 3 的演进

### Level 2: Mock Repository

```python
# Level 2: 使用内存存储（为了演示依赖注入）

class MockUserRepository(UserRepository):
    """Mock 仓储（内存实现）"""

    def __init__(self):
        self.users: Dict[int, User] = {}

    async def save(self, user: User) -> User:
        self.users[user.id] = user
        return user

    async def find_by_email(self, email: str) -> Optional[User]:
        for user in self.users.values():
            if user.email == email:
                return user
        return None

# 优势：
# ✅ 不需要数据库
# ✅ 可以演示依赖注入
# ✅ 可以运行单元测试

# 问题：
# ❌ 数据不持久
# ❌ 无法处理并发
# ❌ 无法演示事务
```

### Level 3: SQL Repository

```python
# Level 3: 使用真实数据库

class SQLUserRepository(UserRepository):
    """SQL 仓储（PostgreSQL 实现）"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, user: User) -> User:
        self.session.add(user)
        await self.session.commit()
        return user

    async def find_by_email(self, email: str) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

# 优势：
# ✅ 数据持久化
# ✅ 支持并发
# ✅ 完整的事务支持
# ✅ 生产级代码

# 关键：
# ✅ Service 层代码不需要修改！
# ✅ 只需要更换 Repository 实现
```

**演进的关键**：
- Service 层代码保持不变
- 只需要更换 Repository 实现
- 这就是依赖倒置原则的价值

---

## ⚠️ 常见的数据库集成反模式

### 反模式 1：Service 直接使用 SQLAlchemy

```python
# ❌ 反模式
class UserService:
    async def create_user(self, user_data: UserCreate):
        async with AsyncSession() as session:
            user = User(**user_data.dict())
            session.add(user)
            await session.commit()

# ✅ 正确
class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def create_user(self, user_data: UserCreate):
        user = User.create(user_data)
        return await self.repo.save(user)
```

### 反模式 2：Repository 包含业务逻辑

```python
# ❌ 反模式
class SQLUserRepository(UserRepository):
    async def create_user(self, user_data: UserCreate):
        # ❌ 业务规则验证
        if len(user_data.password) < 8:
            raise ValueError("Password too weak")

        # ✅ 数据持久化
        user = User(**user_data.dict())
        self.session.add(user)
        await self.session.commit()

# ✅ 正确
class SQLUserRepository(UserRepository):
    async def save(self, user: User) -> User:
        # ✅ 只做数据持久化
        self.session.add(user)
        await self.session.commit()
        return user

# 业务逻辑在 Service 层
class UserService:
    async def create_user(self, user_data: UserCreate):
        # ✅ 业务规则验证
        if not self.is_password_strong(user_data.password):
            raise WeakPasswordException()

        user = User.create(user_data)
        return await self.repo.save(user)
```

### 反模式 3：Repository 返回 DTO

```python
# ❌ 反模式：Repository 返回数据传输对象
class SQLUserRepository(UserRepository):
    async def find_by_id(self, user_id: int) -> UserDTO:
        result = await self.session.execute(...)
        return UserDTO.from_orm(result)  # ❌ Repository 不负责转换

# ✅ 正确：Repository 返回领域对象
class SQLUserRepository(UserRepository):
    async def find_by_id(self, user_id: int) -> User:
        result = await self.session.execute(...)
        return result.scalar_one_or_none()  # ✅ 返回 ORM 对象
```

---

## 🧐 理解验证

### 自我检查问题

1. **Repository 模式的核心价值是？**
   - A. 提高性能
   - B. 封装数据访问逻辑，解耦 Service 和数据库
   - C. 减少代码量
   - D. 自动生成 SQL

2. **Service 应该依赖什么？**
   - A. 具体的 Repository 实现
   - B. SQLAlchemy Session
   - C. Repository 接口
   - D. 数据库连接

3. **事务边界应该在哪一层？**
   - A. Repository 层
   - B. Service 层
   - C. Endpoint 层
   - D. 数据库层

4. **为什么不能在 Repository 中写业务逻辑？**
   - A. 会影响性能
   - B. 违反单一职责原则，难以复用和测试
   - C. 代码太多
   - D. 没有原因，可以写

5. **从 Level 2 到 Level 3，Service 层代码需要修改吗？**
   - A. 需要大量修改
   - B. 只需要更换 Repository 实现
   - C. 完全重写
   - D. 不需要修改

<details>
<summary>点击查看答案</summary>

1. ✅ B. 封装数据访问逻辑，解耦 Service 和数据库
2. ✅ C. Repository 接口
3. ✅ B. Service 层
4. ✅ B. 违反单一职责原则，难以复用和测试
5. ✅ B. 只需要更换 Repository 实现

</details>

---

## 📝 记忆口诀

```
Repository 模式记心间，
数据访问它负责。
Service 只依赖接口，
具体实现可替换。

SQLAlchemy 很强大，
ORM 映射最常用。
会话管理用依赖，
请求结束自动关。

事务边界在 Service，
提交回滚要分明。
数据一致最重要，
ACID 特性要保证。
```

---

## 🚀 下一步

现在你已经理解了数据库集成的架构设计，可以开始学习 Level 3 的具体内容：

1. **数据库基础** → `notes/01_database_basics.md`
2. **SQLAlchemy 入门** → `notes/02_sqlalchemy_basics.md`
3. **Repository 模式** → `notes/03_repository_pattern.md`
4. **事务与连接池** → `notes/04_transactions.md`
5. **数据库迁移** → `notes/05_migrations.md`

记住：**Repository 模式是数据访问的最佳实践！**

---

## 📚 延伸阅读

- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Repository Pattern by Martin Fowler](https://martinfowler.com/eaaCatalog/repository.html)
- [Patterns of Enterprise Application Architecture](https://www.martinfowler.com/books/eaa.html)

---

**掌握数据库集成，让你的应用能够持久化数据！** 🎯
