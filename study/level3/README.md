# Level 3: 数据库与持久化 - 学习记录

## 🎯 学习目标

掌握在分层架构中集成数据库和外部系统，理解如何通过 Repository 模式将持久化逻辑隔离在基础设施层。

**核心目标**：
- 实现 Repository 模式完成分层架构
- 掌握 SQLAlchemy 的集成
- 理解事务管理和连接池
- 学会数据库迁移（Alembic）

## 🎓 为什么需要数据库集成？

### 从 Level 2 到 Level 3 的演进

在 Level 2，我们学会了依赖注入，实现了：

```python
# Level 2: 使用依赖注入，但 Repository 还是空的
class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

class MockUserRepository(UserRepository):
    """Mock 实现（使用内存）"""
    def __init__(self):
        self.users = {}

    async def save(self, user: User) -> User:
        self.users[user.id] = user
        return user
```

**Level 2 的问题**：
- ❌ Repository 使用内存存储（数据不持久）
- ❌ 无法处理并发
- ❌ 没有事务管理
- ❌ 无法支持复杂查询

**Level 3 的解决方案**：
```python
# Level 3: 真实的数据库集成
class SQLUserRepository(UserRepository):
    """SQL 实现（使用 PostgreSQL）"""
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, user: User) -> User:
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
```

### 为什么需要 Repository 模式？

**直接在 Service 中使用 SQLAlchemy 的问题**：

```python
# ❌ 错误：Service 直接依赖 SQLAlchemy
class UserService:
    async def create_user(self, user_data: UserCreate):
        async with AsyncSession() as session:
            user = User(**user_data.dict())
            session.add(user)
            await session.commit()

# 问题：
# - Service 被绑死在 SQLAlchemy
# - 无法换数据库（如从 PostgreSQL 换到 MongoDB）
# - 难以测试（必须启动数据库）
# - SQL 逻辑散落在 Service 中
```

**使用 Repository 模式的优势**：

```python
# ✅ 正确：Service 依赖 Repository 接口
class UserService:
    def __init__(self, repo: UserRepository):  # 依赖接口
        self.repo = repo

# 好处：
# - Service 不知道底层是 SQL 还是 NoSQL
# - 可以轻松换数据库实现
# - 测试时注入 Mock Repository
# - 所有持久化逻辑集中在 Repository
```

## 🏗️ Level 3 的核心主题

### Repository 模式

**什么是 Repository 模式？**

Repository 模式是一种数据访问模式，它将数据持久化逻辑封装在单独的层中。

```
┌─────────────────────────────────────────────────────────────┐
│              Repository 模式的架构位置                       │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐      依赖接口      ┌──────────────┐
│   Service    │ ───────────────→  │ Repository   │
│  (业务逻辑)   │                    │  (数据访问)   │
└──────────────┘                    └──────────────┘
                                          │
                                          │ 实现接口
                                          ▼
                                   ┌──────────────┐
                                   │   Database   │
                                   │  (PostgreSQL) │
                                   └──────────────┘
```

**Repository 的核心价值**：
1. **抽象** - 隐藏数据访问细节
2. **解耦** - Service 不依赖具体实现
3. **可测试** - 可以注入 Mock
4. **可复用** - 数据访问逻辑集中管理

### SQLAlchemy 集成

**为什么选择 SQLAlchemy？**

- ✅ Python 最流行的 ORM
- ✅ 支持 async/await
- ✅ 类型提示友好
- ✅ 自动生成表结构
- ✅ 数据库无关（支持 PostgreSQL/MySQL/SQLite）

**核心概念**：
```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

# 1. 定义模型（映射到数据库表）
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(100))

# 2. 创建异步引擎
engine = create_async_engine("postgresql+asyncpg://...")
async_session = sessionmaker(engine, class_=AsyncSession)

# 3. 在 Repository 中使用
class SQLUserRepository(UserRepository):
    async def save(self, user: User) -> User:
        async with async_session() as session:
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user
```

### 事务管理

**什么是事务？**

事务是数据库操作的逻辑单元，要么全部成功，要么全部失败。

**事务的 ACID 特性**：
- **A**tomicity - 原子性（全部成功或全部失败）
- **C**onsistency - 一致性（数据始终一致）
- **I**solation - 隔离性（并发事务互不影响）
- **D**urability - 持久性（提交后永久保存）

**FastAPI 中的事务管理**：
```python
from fastapi import Depends

async def get_db() -> AsyncSession:
    """请求级别的数据库会话"""
    async with async_session() as session:
        yield session

@app.post("/users")
async def create_user(
    user: UserCreate,
    service: UserService = Depends(),
    db: AsyncSession = Depends(get_db)  # 事务边界
):
    try:
        user = await service.create_user(user)
        await db.commit()  # 提交事务
    except Exception as e:
        await db.rollback()  # 回滚事务
        raise
```

### 数据库迁移（Alembic）

**什么是数据库迁移？**

迁移是数据库结构的版本控制，用于管理表结构的变化。

**Alembic 的工作流程**：
```
1. 修改 SQLAlchemy 模型
2. 生成迁移脚本: alembic revision --autogenerate -m "add user table"
3. 查看迁移脚本
4. 应用迁移: alembic upgrade head
5. 数据库表结构更新
```

## 📚 学习路径

### 阶段 3.1: 数据库基础

**学习目标**：理解关系型数据库和基本概念

**内容**：
- 关系型数据库基础
- 表、行、列
- 主键、外键
- 索引
- SQL 基础查询

**学习材料**：
- 笔记：`notes/01_database_basics.md`
- 示例：`examples/01_database_basics.py`

**完成标准**：
- [ ] 理解关系型数据库的基本概念
- [ ] 掌握基本的 SQL 查询
- [ ] 理解主键和外键的作用

---

### 阶段 3.2: SQLAlchemy 入门

**学习目标**：掌握 SQLAlchemy 的基本用法

**内容**：
- SQLAlchemy 架构（Core vs ORM）
- 定义模型（映射到表）
- CRUD 操作（增删改查）
- 关系（一对一、一对多、多对多）

**学习材料**：
- 笔记：`notes/02_sqlalchemy_basics.md`
- 示例：`examples/02_sqlalchemy_basics.py`

**完成标准**：
- [ ] 能够定义 SQLAlchemy 模型
- [ ] 掌握基本的 CRUD 操作
- [ ] 理解如何定义模型关系

---

### 阶段 3.3: Repository 模式

**学习目标**：实现 Repository 模式完成分层架构

**内容**：
- Repository 接口定义
- SQL 实现
- 使用依赖注入集成
- 复杂查询的处理

**学习材料**：
- 笔记：`notes/03_repository_pattern.md`
- 示例：`examples/03_repository_pattern.py`

**完成标准**：
- [ ] 理解 Repository 模式的价值
- [ ] 能够设计 Repository 接口
- [ ] 实现完整的 SQL Repository

---

### 阶段 3.4: 事务与连接池

**学习目标**：掌握事务管理和连接池配置

**内容**：
- 事务边界
- 连接池原理
- 并发控制
- 死锁处理

**学习材料**：
- 笔记：`notes/04_transactions.md`
- 示例：`examples/04_transactions.py`

**完成标准**：
- [ ] 理解事务的 ACID 特性
- [ ] 掌握 FastAPI 中的事务管理
- [ ] 配置和优化连接池

---

### 阶段 3.5: 数据库迁移

**学习目标**：使用 Alembic 管理数据库变化

**内容**：
- Alembic 基础
- 生成迁移脚本
- 版本管理
- 数据迁移策略

**学习材料**：
- 笔记：`notes/05_migrations.md`
- 示例：`examples/05_migrations.py`

**完成标准**：
- [ ] 理解数据库迁移的作用
- [ ] 掌握 Alembic 的基本使用
- [ ] 能够安全地执行数据迁移

## 🎯 Level 3 的核心成果

完成 Level 3 后，你将能够：

### 1. 实现完整的分层架构

```
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Endpoint (传输层)                      │
│  @app.post("/users")                                       │
│  async def create_user(                                    │
│      user: UserCreate,                                     │
│      service: UserService = Depends()                      │
│  ):                                                        │
│      return await service.create_user(user)                │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ 依赖注入
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              UserService (服务层)                           │
│  async def create_user(self, user_data: UserCreate):       │
│      if await self.repo.email_exists(user_data.email):     │
│          raise UserEmailExistsException()                  │
│      user = User.create(user_data)                         │
│      return await self.repo.save(user)                     │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ 依赖接口
                          ▼
┌─────────────────────────────────────────────────────────────┐
│         SQLUserRepository (基础设施层)                      │
│  async def save(self, user: User) -> User:                 │
│      self.session.add(user)                                │
│      await self.session.commit()                           │
│      return user                                            │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ SQLAlchemy
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              PostgreSQL (数据库)                            │
└─────────────────────────────────────────────────────────────┘
```

### 2. 编写可维护的数据访问代码

```python
# ✅ 数据访问逻辑集中在 Repository
class SQLUserRepository(UserRepository):
    async def find_by_email(self, email: str) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def find_active_users(self) -> List[User]:
        result = await self.session.execute(
            select(User).where(User.is_active == True)
        )
        return result.scalars().all()
```

### 3. 管理数据库变化

```bash
# 生成迁移
alembic revision --autogenerate -m "add user table"

# 查看迁移
cat alembic/versions/001_add_user_table.py

# 应用迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

## 📁 目录结构

```
study/level3/
├── README.md                      # 本文件：学习概览
├── notes/                         # 学习笔记
│   ├── 00_architecture_db.md      # 数据库架构设计
│   ├── 01_database_basics.md
│   ├── 02_sqlalchemy_basics.md
│   ├── 03_repository_pattern.md
│   ├── 04_transactions.md
│   └── 05_migrations.md
├── examples/                      # 代码示例
│   ├── 01_database_basics.py
│   ├── 02_sqlalchemy_basics.py
│   ├── 03_repository_pattern.py
│   ├── 04_transactions.py
│   └── 05_migrations.py
└── exercises/                     # 练习题
    ├── 01_basic_exercises.md
    ├── 02_intermediate_exercises.md
    └── 03_challenge_projects.md
```

## 🔗 与 Level 2 的关系

```
Level 2 (依赖注入)
├─ Depends 的基本用法 ✅
├─ 类依赖 vs 函数依赖 ✅
├─ 依赖的生命周期 ✅
└─ Service 层实现（使用 Mock Repository）

        ↓ 加上真实的数据库

Level 3 (数据库与持久化)
├─ Repository 模式的真实实现
├─ SQLAlchemy 集成
├─ 事务管理
└─ 数据库迁移

        ↓ 能够

Level 4 (生产就绪)
├─ 缓存集成（Redis）
├─ 消息队列（Kafka）
└─ 外部 API 集成
```

**Level 3 的关键作用**：
- 将 Level 2 的 Mock Repository 替换为真实实现
- 完成分层架构的最后一块拼图
- 为 Level 4 的外部系统集成建立基础

## ⚠️ 架构约束（Level 3 必须遵守）

```python
# ❌ 禁止：Service 直接使用 SQLAlchemy
class UserService:
    async def create_user(self, user_data: UserCreate):
        async with AsyncSession() as session:
            session.add(User(**user_data.dict()))
            await session.commit()

# ✅ 正确：Service 通过 Repository 访问数据库
class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def create_user(self, user_data: UserCreate):
        user = User.create(user_data)
        return await self.repo.save(user)

# ❌ 禁止：在 Repository 中编写业务逻辑
class SQLUserRepository(UserRepository):
    async def create_user(self, user_data: UserCreate):
        # ❌ 业务规则：检查密码强度
        if len(user_data.password) < 8:
            raise ValueError("Password too weak")
        ...

# ✅ 正确：Repository 只负责数据访问
class SQLUserRepository(UserRepository):
    async def save(self, user: User) -> User:
        self.session.add(user)
        await self.session.commit()
        return user
```

## 🎓 完成标准

当你完成以下所有项，就说明 Level 3 达标了：

- [ ] 理解关系型数据库的基本概念
- [ ] 掌握 SQLAlchemy 的基本用法
- [ ] 能够实现 Repository 模式
- [ ] 理解事务管理和连接池
- [ ] 掌握 Alembic 数据库迁移
- [ ] 实现一个完整的分层架构应用
- [ ] 能够处理复杂的查询和关系

## 🚀 下一步

完成 Level 3 后，你将准备好进入 **Level 4: 生产就绪**！

Level 4 将学习：
- 缓存集成（Redis）
- 消息队列（Kafka/RabbitMQ）
- 外部 API 集成
- 连接池、超时、重试
- 限流、熔断、降级

---

**祝你学习愉快！记住：Repository 模式是数据访问的最佳实践！** 🚀
