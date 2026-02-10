# Level 2: 依赖注入系统 - 学习记录

## 🎯 学习目标

掌握 FastAPI 的依赖注入系统，理解如何通过依赖注入实现真正的分层架构，让代码变得可测试、可复用、可维护。

**核心目标**：
- 从 Level 1 的"薄 endpoint"演进到完整的分层架构
- 理解依赖注入如何解耦各个层次
- 掌握服务层（Service Layer）的实现
- 学会管理依赖的生命周期

## 🎓 为什么需要依赖注入？

### 从 Level 1 的局限说起

在 Level 1，我们学到了：
- ✅ Endpoint 应该保持"薄"（只做协议适配）
- ✅ 业务逻辑应该在 Service 层
- ✅ 但我们还没有真正实现 Service 层！

**Level 1 的问题**：
```python
# Level 1 的代码（为了演示，业务逻辑混在 endpoint）
@app.post("/users/")
async def create_user(user: UserCreate):
    # ❌ 业务逻辑在传输层（违反架构原则）
    if await db.query("SELECT * FROM users WHERE email = ?", user.email):
        raise HTTPException(409, "Email exists")

    hashed = hash_password(user.password)
    user_id = await db.insert("INSERT INTO users ...")

    return {"id": user_id}
```

**Level 2 的解决方案**：
```python
# Level 2 的代码（使用依赖注入实现分层架构）
class UserService:
    """服务层 - 包含业务逻辑"""
    def __init__(self, repo: UserRepository):
        self.repo = repo  # 依赖抽象

    async def create_user(self, user_data: UserCreate):
        # ✅ 业务逻辑在服务层
        if await self.repo.email_exists(user_data.email):
            raise UserEmailExistsException(user_data.email)

        user = User.create(user_data)
        return await self.repo.save(user)

# 依赖注入：FastAPI 自动组装依赖
@app.post("/users/")
async def create_user(
    user: UserCreate,
    service: UserService = Depends(get_user_service)  # 依赖注入
):
    # ✅ Endpoint 只做协议适配
    return await service.create_user(user)
```

## 🏗️ Level 2 的核心主题

### 依赖注入的本质

**什么是依赖注入？**

简单来说：**不要自己找依赖，让别人提供给你。**

```
❌ 硬编码依赖（自己创建）：
class UserService:
    def __init__(self):
        self.db = Database()  # 自己创建依赖

✅ 依赖注入（别人提供）：
class UserService:
    def __init__(self, db: Database):  # 依赖抽象
        self.db = db  # 别人注入的依赖
```

**为什么需要依赖注入？**

1. **解耦** - 类不需要知道如何创建依赖
2. **可测试** - 测试时可以注入 Mock 对象
3. **可复用** - 同一个 Service 可以用在 HTTP、CLI、gRPC 等场景

### FastAPI 的依赖注入系统

FastAPI 提供了强大的依赖注入系统：

```python
from fastapi import Depends

# 1. 定义依赖
def get_user_service() -> UserService:
    db = get_db()
    repo = UserRepository(db)
    return UserService(repo)

# 2. 使用依赖（FastAPI 自动注入）
@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service)
):
    return await service.get_user(user_id)
```

**FastAPI DI 的优势**：
- ✅ 自动管理依赖的创建和销毁
- ✅ 支持嵌套依赖
- ✅ 自动缓存（同一请求中的多次使用只创建一次）
- ✅ 集成到 OpenAPI 文档

## 📚 学习路径

### 阶段 2.1: 依赖基础

**学习目标**：理解 `Depends` 的基本使用

**内容**：
- 什么是依赖注入？
- `Depends` 的基本语法
- 函数依赖的定义和使用
- 简单的依赖链

**学习材料**：
- 笔记：`notes/01_dependency_basics.md`
- 示例：`examples/01_dependency_basics.py`

**完成标准**：
- [ ] 理解依赖注入的概念
- [ ] 能够使用 `Depends` 注入简单依赖
- [ ] 理解依赖的自动解析过程

---

### 阶段 2.2: 类依赖 vs 函数依赖

**学习目标**：掌握不同形式依赖的使用场景

**内容**：
- 函数依赖（简单场景）
- 类依赖（有状态、需要初始化）
- 依赖类 vs 可调用对象
- 如何选择合适的形式

**学习材料**：
- 笔记：`notes/02_class_vs_function.md`
- 示例：`examples/02_class_vs_function.py`

**完成标准**：
- [ ] 知道何时用函数依赖，何时用类依赖
- [ ] 理解类依赖的优势（状态管理、复用）
- [ ] 能够实现复杂的依赖关系

---

### 阶段 2.3: 依赖的生命周期

**学习目标**：理解依赖的创建和销毁时机

**内容**：
- Request-scoped 依赖（每个请求创建一次）
- Application-scoped 依赖（全局共享）
- 依赖的缓存机制
- `yield` 依赖（资源清理）

**学习材料**：
- 笔记：`notes/03_dependency_lifecycle.md`
- 示例：`examples/03_dependency_lifecycle.py`

**完成标准**：
- [ ] 理解 request-scoped vs app-scoped
- [ ] 掌握使用 `yield` 管理资源（如数据库连接）
- [ ] 理解依赖的缓存机制

---

### 阶段 2.4: 实现服务层

**学习目标**：通过依赖注入实现真正的分层架构

**内容**：
- Service 层的设计
- Repository 模式
- 依赖倒置原则
- 从 Level 1 演进到 Level 2

**学习材料**：
- 笔记：`notes/04_service_layer.md`
- 示例：`examples/04_service_layer.py`

**完成标准**：
- [ ] 能够设计并实现 Service 层
- [ ] 理解依赖倒置原则
- [ ] 实现 Endpoint → Service → Repository 的分层架构

---

### 阶段 2.5: 依赖注入的最佳实践

**学习目标**：掌握生产级的依赖注入模式

**内容**：
- 依赖注入的反模式
- 循环依赖的解决方案
- 测试中的依赖注入
- 性能优化建议

**学习材料**：
- 笔记：`notes/05_best_practices.md`
- 示例：`examples/05_best_practices.py`

**完成标准**：
- [ ] 能够识别和避免常见的 DI 陷阱
- [ ] 掌握测试中如何注入 Mock 对象
- [ ] 理解依赖注入的性能影响

---

## 🎯 Level 2 的核心成果

完成 Level 2 后，你将能够：

### 1. 从 Level 1 演进到真正的分层架构

```
Level 1 (传输层)
├─ Endpoint 包含业务逻辑（为了演示）
└─ 使用简单的内存存储

        ↓ 演进

Level 2 (分层架构)
├─ Endpoint (薄，只做协议适配)
├─ Service (业务逻辑编排)
└─ Repository (数据持久化)
```

### 2. 编写可测试、可复用的代码

```python
# ✅ Service 可以独立测试
def test_user_service():
    mock_repo = Mock(spec=UserRepository)
    service = UserService(mock_repo)
    user = service.create_user(UserCreate(...))
    assert user.id is not None

# ✅ Service 可以在多处复用
# HTTP API
@app.post("/users")
async def create_user_http(service: UserService = Depends()):
    return await service.create_user(...)

# CLI 工具
async def create_user_cli(name, email):
    service = UserService(repo)
    user = await service.create_user(...)
    print(f"User created: {user.id}")
```

### 3. 理解依赖注入的设计哲学

- **控制反转** (IoC) - 不自己创建依赖
- **依赖倒置** - 依赖抽象而非具体
- **单一职责** - 每个类只做一件事

## 📁 目录结构

```
study/level2/
├── README.md                  # 本文件：学习概览
├── notes/                     # 学习笔记
│   ├── 00_architecture_di.md  # 依赖注入架构设计
│   ├── 01_dependency_basics.md
│   ├── 02_class_vs_function.md
│   ├── 03_dependency_lifecycle.md
│   ├── 04_service_layer.md
│   └── 05_best_practices.md
├── examples/                  # 代码示例
│   ├── 01_dependency_basics.py
│   ├── 02_class_vs_function.py
│   ├── 03_dependency_lifecycle.py
│   ├── 04_service_layer.py
│   └── 05_best_practices.py
└── exercises/                 # 练习题
    ├── 01_basic_exercises.md
    ├── 02_intermediate_exercises.md
    └── 03_challenge_projects.md
```

## 🔗 与 Level 1 的关系

```
Level 1 (传输层)
├─ 请求参数校验 ✅
├─ 响应处理 ✅
├─ 统一响应格式 ✅
└─ 错误处理 ✅

        ↓ 加上

Level 2 (依赖注入)
├─ Service 层实现
├─ Repository 模式
├─ 依赖注入系统
└─ 分层架构完成

        ↓ 能够

Level 3 (外部系统集成)
├─ 数据库集成
├─ 缓存集成
└─ 消息队列集成
```

**Level 2 的关键作用**：
- 将 Level 1 学到的"薄 endpoint"原则真正落地
- 为 Level 3 的外部系统集成提供清晰的分层架构
- 让代码变得可测试、可复用

## ⚠️ 架构约束（Level 2 必须遵守）

```python
# ❌ 禁止：硬编码依赖
class UserService:
    def __init__(self):
        self.db = Database()  # 硬编码

# ✅ 正确：依赖注入
class UserService:
    def __init__(self, db: Database):
        self.db = db  # 注入的依赖

# ❌ 禁止：在 Service 中使用 HTTPException
class UserService:
    async def get_user(self, user_id: int):
        if not user:
            raise HTTPException(404)  # Service 不应该知道 HTTP

# ✅ 正确：抛出领域异常
class UserService:
    async def get_user(self, user_id: int):
        if not user:
            raise UserNotFoundException(user_id)  # 领域异常
```

## 📝 记录建议

### 学习笔记（notes/）

每个学习笔记应包含：
1. 核心概念（费曼简化版）
2. 生活化类比
3. 代码示例（❌ 错误 vs ✅ 正确）
4. 架构说明（为什么这样设计）
5. 理解验证问题

### 示例代码（examples/）

每个代码示例应包含：
1. 完整的分层架构（Endpoint → Service → Repository）
2. 使用依赖注入连接各层
3. 架构说明注释
4. 可直接运行

## 🎓 完成标准

当你完成以下所有项，就说明 Level 2 达标了：

- [ ] 理解依赖注入的概念和价值
- [ ] 掌握 `Depends` 的各种用法
- [ ] 能够设计和实现 Service 层
- [ ] 能够使用依赖注入连接各层
- [ ] 理解依赖的生命周期
- [ ] 能够编写可测试的代码
- [ ] 实现一个完整的分层架构示例

## 🚀 下一步

完成 Level 2 后，你将准备好进入 **Level 3: 外部系统集成**！

Level 3 将学习：
- 数据库集成（SQLAlchemy + Alembic）
- 缓存集成（Redis）
- 消息队列（Kafka/RabbitMQ）
- 连接池、超时、重试

---

**祝你学习愉快！记住：依赖注入是实现分层架构的关键！** 🚀
