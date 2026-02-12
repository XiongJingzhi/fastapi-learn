# Level 2 综合挑战项目：实战应用

## 🎯 项目目标

通过三个真实场景的综合项目，将依赖注入、分层架构、生命周期管理等知识融会贯通，实现生产级别的代码。

---

## 挑战项目 1: 构建完整的博客系统

### 🎯 项目描述

实现一个功能完整的博客系统后端，包含用户管理、文章管理、评论系统。要求使用标准的分层架构（Repository → Service → Endpoint），并应用依赖注入最佳实践。

### 💡 费曼类比：建设图书馆

```
构建博客系统就像建设图书馆：

Repository 层 = 书库管理
- 负责存储和检索书籍
- 管理书架空间

Service 层 = 图书管理员
- 提供借阅服务（业务逻辑）
- 验证读者资格
- 处理特殊请求

Endpoint 层 = 前台服务
- 接待读者（HTTP 请求）
- 引导到相应服务
- 返回结果

依赖注入 = 内部协调系统
- 自动将读者的请求路由到正确的部门
- 确保每个部门有需要的资源
```

### 📋 需求列表

#### 基础功能
1. **用户模块**
   - [ ] 用户注册（验证邮箱唯一性）
   - [ ] 用户登录（返回 token）
   - [ ] 获取用户信息

2. **文章模块**
   - [ ] 创建文章（需要认证）
   - [ ] 获取文章列表（分页）
   - [ ] 获取单篇文章
   - [ ] 更新文章（作者权限验证）
   - [ ] 删除文章（作者权限验证）

3. **评论模块**
   - [ ] 发表评论（需要认证）
   - [ ] 获取文章的评论列表
   - [ ] 删除评论（作者或管理员）

#### 高级功能
4. **缓存系统**
   - [ ] 热门文章缓存（Application-scoped）
   - [ ] 使用 TTL 自动过期

5. **限流保护**
   - [ ] API 限流（每用户每分钟 10 次）

6. **日志审计**
   - [ ] 记录所有写操作（Request-scoped + yield）

### 🏗️ 架构设计

```python
# ═══════════════════════════════════════════════════════════
# 分层架构
# ═══════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────┐
│  Endpoint Layer (HTTP Layer)                      │
│  - 接收 HTTP 请求                                   │
│  - 参数验证（Pydantic）                             │
│  - 调用 Service 层                                 │
│  - 返回 HTTP 响应                                  │
│  - 处理异常                                        │
└─────────────────────────────────────────────────────┘
                      │ Depends
                      ▼
┌─────────────────────────────────────────────────────┐
│  Service Layer (Business Logic)                   │
│  - 实现业务规则                                    │
│  - 权限验证                                        │
│  - 调用 Repository 层                              │
│  - 事务管理                                        │
└─────────────────────────────────────────────────────┘
                      │ Depends
                      ▼
┌─────────────────────────────────────────────────────┐
│  Repository Layer (Data Access)                   │
│  - CRUD 操作                                        │
│  - 数据库查询                                      │
│  - 缓存操作                                        │
└─────────────────────────────────────────────────────┘
```

### 📝 实现任务

#### 任务 1: 基础结构搭建

```python
# blog_project/models.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class User(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

class ArticleCreate(BaseModel):
    title: str
    content: str

class Article(BaseModel):
    id: int
    title: str
    content: str
    author_id: int
    author_name: str
    created_at: datetime

class CommentCreate(BaseModel):
    content: str

class Comment(BaseModel):
    id: int
    article_id: int
    author_id: int
    author_name: str
    content: str
    created_at: datetime

# TODO: 完成所有需要的模型定义
```

```python
# blog_project/repositories.py
from typing import Optional, List
from blog_project.models import User, Article, Comment

class UserRepository:
    """用户仓储"""

    def __init__(self):
        # TODO: 初始化数据存储
        pass

    async def email_exists(self, email: str) -> bool:
        """检查邮箱是否存在"""
        # TODO: 实现逻辑
        pass

    async def username_exists(self, username: str) -> bool:
        """检查用户名是否存在"""
        # TODO: 实现逻辑
        pass

    async def save(self, user: User) -> User:
        """保存用户"""
        # TODO: 实现逻辑
        pass

    async def find_by_email(self, email: str) -> Optional[User]:
        """根据邮箱查找用户"""
        # TODO: 实现逻辑
        pass

    async def find_by_id(self, user_id: int) -> Optional[User]:
        """根据 ID 查找用户"""
        # TODO: 实现逻辑
        pass

class ArticleRepository:
    """文章仓储"""

    # TODO: 实现 ArticleRepository 的所有方法
    pass

class CommentRepository:
    """评论仓储"""

    # TODO: 实现 CommentRepository 的所有方法
    pass
```

```python
# blog_project/services.py
from blog_project.models import User, Article, Comment
from blog_project.repositories import UserRepository, ArticleRepository, CommentRepository

class UserService:
    """用户服务"""

    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def register(self, user_data) -> User:
        """
        注册用户

        业务规则：
        1. 邮箱必须唯一
        2. 用户名必须唯一
        3. 密码需要加密（模拟）
        """
        # TODO: 实现注册逻辑
        pass

    async def login(self, email: str, password: str) -> str:
        """
        用户登录

        返回 token
        """
        # TODO: 实现登录逻辑
        pass

class ArticleService:
    """文章服务"""

    # TODO: 实现 ArticleService 的所有业务逻辑
    pass

class CommentService:
    """评论服务"""

    # TODO: 实现 CommentService 的所有业务逻辑
    pass
```

```python
# blog_project/dependencies.py
from fastapi import Depends
from blog_project.repositories import UserRepository, ArticleRepository, CommentRepository
from blog_project.services import UserService, ArticleService, CommentService

# TODO: 实现 Repository 依赖
def get_user_repo() -> UserRepository:
    pass

def get_article_repo() -> ArticleRepository:
    pass

def get_comment_repo() -> CommentRepository:
    pass

# TODO: 实现 Service 依赖
def get_user_service(
    repo: UserRepository = Depends(get_user_repo)
) -> UserService:
    pass

def get_article_service(
    repo: ArticleRepository = Depends(get_article_repo)
) -> ArticleService:
    pass

def get_comment_service(
    repo: CommentRepository = Depends(get_comment_repo)
) -> CommentService:
    pass
```

```python
# blog_project/main.py
from fastapi import FastAPI, Depends, HTTPException
from blog_project.models import *
from blog_project.dependencies import *

app = FastAPI(title="Blog API")

# TODO: 实现 Endpoints

@app.post("/users/register", status_code=201)
async def register(
    user_data: UserCreate,
    service: UserService = Depends(get_user_service)
):
    """用户注册"""
    # TODO: 实现逻辑
    pass

@app.post("/users/login")
async def login(
    # TODO: 实现登录
):
    pass

@app.get("/users/{user_id}")
async def get_user(
    # TODO: 实现获取用户信息
):
    pass

@app.post("/articles", status_code=201)
async def create_article(
    # TODO: 实现创建文章
):
    pass

@app.get("/articles")
async def list_articles(
    # TODO: 实现获取文章列表（支持分页）
):
    pass

@app.get("/articles/{article_id}")
async def get_article(
    # TODO: 实现获取单篇文章
):
    pass

# TODO: 实现更多的 endpoints...
```

#### 任务 2: 添加缓存系统

```python
# blog_project/cache.py
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import time

class CacheService:
    """缓存服务（Application-scoped）"""

    def __init__(self, default_ttl: int = 300):
        """
        default_ttl: 默认过期时间（秒）
        """
        self.default_ttl = default_ttl
        self._cache: Dict[str, tuple] = {}  # {key: (value, expire_time)}

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        # TODO: 实现获取逻辑
        pass

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """设置缓存"""
        # TODO: 实现设置逻辑
        pass

    def delete(self, key: str):
        """删除缓存"""
        # TODO: 实现删除逻辑
        pass

    def clear(self):
        """清空所有缓存"""
        # TODO: 实现清空逻辑
        pass

# TODO: 创建全局缓存实例
```

```python
# 在 ArticleService 中使用缓存

class ArticleService:
    def __init__(self, repo: ArticleRepository, cache: CacheService):
        self.repo = repo
        self.cache = cache

    async def get_popular_articles(self) -> List[Article]:
        """获取热门文章（使用缓存）"""

        # 1. 尝试从缓存获取
        cache_key = "popular_articles"
        cached = self.cache.get(cache_key)

        if cached:
            return cached

        # 2. 缓存未命中，从数据库获取
        articles = await self.repo.find_popular()

        # 3. 更新缓存（TTL 5 分钟）
        self.cache.set(cache_key, articles, ttl=300)

        return articles

# TODO: 修改 dependencies.py，注入 cache 到 service
```

#### 任务 3: 添加限流保护

```python
# blog_project/rate_limit.py
from typing import Dict
import time

class RateLimiter:
    """限流器（Application-scoped）"""

    def __init__(self, max_requests: int = 10, window: int = 60):
        self.max_requests = max_requests
        self.window = window
        self._requests: Dict[str, list] = {}

    def is_allowed(self, identifier: str) -> bool:
        """
        检查是否允许请求

        返回 (allowed: bool, retry_after: Optional[int])
        """
        # TODO: 实现限流逻辑
        pass

# TODO: 创建全局限流器实例

# TODO: 实现依赖函数 check_rate_limit
def check_rate_limit(
    # 需要从请求中获取用户标识（IP 或 user_id）
    # 检查限流
    # 如果超过限制，抛出 HTTPException(429)
):
    pass
```

#### 任务 4: 添加审计日志

```python
# blog_project/audit.py
from typing import List, Dict
from datetime import datetime

class AuditLogger:
    """审计日志记录器（Request-scoped + yield）"""

    def __init__(self):
        self.actions: List[Dict] = []

    def log(self, action: str, resource: str, resource_id: int = None):
        """记录一个操作"""
        self.actions.append({
            "action": action,
            "resource": resource,
            "resource_id": resource_id,
            "timestamp": datetime.now().isoformat()
        })

    def get_summary(self) -> List[Dict]:
        """获取审计摘要"""
        return self.actions

# TODO: 实现 get_audit_logger 依赖（使用 yield）
# 在请求结束时，可以将日志保存到数据库或文件
def get_audit_logger():
    pass

# TODO: 在需要审计的 endpoints 中注入 audit_logger
# 例如：创建文章、删除文章等
```

### ✅ 完成标准

**基础功能**：
- [ ] 用户可以注册和登录
- [ ] 用户可以创建、查看、更新、删除文章
- [ ] 用户可以发表和删除评论
- [ ] 权限验证正确（只能修改自己的内容）

**高级功能**：
- [ ] 热门文章有缓存（第二次访问更快）
- [ ] API 限流生效（超过限制返回 429）
- [ ] 所有写操作有审计日志

**代码质量**：
- [ ] 分层架构清晰（Repository → Service → Endpoint）
- [ ] 依赖注入正确使用
- [ ] 生命周期管理合理
- [ ] 异常处理完善

### 💡 提示

1. **分层原则**：
   - Repository 层：只做数据操作
   - Service 层：只做业务逻辑
   - Endpoint 层：只做 HTTP 协议适配

2. **依赖注入**：
   - Repository → Service：使用 Depends
   - Service → Endpoint：使用 Depends
   - 全局资源（Cache、RateLimiter）：直接创建

3. **生命周期**：
   - Cache、RateLimiter：Application-scoped
   - AuditLogger：Request-scoped（使用 yield）

4. **测试顺序**：
   - 先实现基础 CRUD
   - 再添加权限验证
   - 最后添加缓存、限流、日志

### 🧪 扩展挑战

如果基础功能完成了，可以尝试：

1. **添加标签系统**
   - 文章可以有多个标签
   - 支持按标签筛选文章

2. **添加搜索功能**
   - 全文搜索文章标题和内容
   - 搜索结果缓存

3. **添加统计功能**
   - 文章浏览量统计
   - 用户活跃度统计

4. **性能优化**
   - 批量查询优化
   - 分页查询优化

---

## 挑战项目 2: 电商订单系统

### 🎯 项目描述

实现一个电商订单系统，包含商品管理、购物车、订单处理。重点关注事务管理和一致性保证。

### 💡 费曼类比：餐厅点餐系统

```
电商订单系统就像餐厅点餐：

商品管理 = 菜单管理
- 显示所有菜品
- 菜品详情

购物车 = 预点菜
- 客人可以先选好菜品
- 还可以修改

订单处理 = 正式下单
- 确认订单（事务开始）
- 检查库存
- 扣减库存
- 创建订单
- 支付（事务提交）
- 如果失败，回滚所有操作
```

### 📋 需求列表

#### 核心功能
1. **商品模块**
   - [ ] 商品列表
   - [ ] 商品详情
   - [ ] 库存管理

2. **购物车模块**
   - [ ] 添加商品到购物车
   - [ ] 查看购物车
   - [ ] 更新数量
   - [ ] 删除商品

3. **订单模块**
   - [ ] 创建订单（关键：事务管理）
   - [ ] 订单支付
   - [ ] 订单状态查询
   - [ ] 订单取消（回滚库存）

### 🏗️ 架构重点

**事务管理**：
```python
class OrderService:
    def create_order(self, user_id: int, items: List[OrderItem]) -> Order:
        """
        创建订单（使用事务）

        步骤：
        1. 开始事务
        2. 检查所有商品的库存
        3. 扣减库存
        4. 创建订单
        5. 提交事务
        6. 如果任何步骤失败，回滚事务
        """
```

### 📝 实现任务

```python
# ecommerce/models.py
from pydantic import BaseModel
from typing import List
from datetime import datetime
from enum import Enum

class ProductStatus(str, Enum):
    AVAILABLE = "available"
    OUT_OF_STOCK = "out_of_stock"
    DISCONTINUED = "discontinued"

class Product(BaseModel):
    id: int
    name: str
    price: float
    stock: int
    status: ProductStatus

class CartItem(BaseModel):
    product_id: int
    quantity: int

class OrderStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class OrderItem(BaseModel):
    product_id: int
    product_name: str
    price: float
    quantity: int

class Order(BaseModel):
    id: int
    user_id: int
    items: List[OrderItem]
    total_amount: float
    status: OrderStatus
    created_at: datetime

# TODO: 定义所有需要的模型
```

```python
# ecommerce/services.py
from typing import List
from ecommerce.models import Product, Cart, Order

class OrderService:
    """订单服务（重点：事务管理）"""

    def __init__(self, order_repo, product_repo, cart_repo):
        self.order_repo = order_repo
        self.product_repo = product_repo
        self.cart_repo = cart_repo

    async def create_order(
        self,
        user_id: int,
        cart_id: int
    ) -> Order:
        """
        创建订单（事务管理）

        TODO: 实现以下流程

        1. 获取购物车
        2. 检查所有商品的库存
        3. 如果库存不足，抛出异常
        4. 扣减库存
        5. 清空购物车
        6. 创建订单
        7. 如果任何步骤失败，回滚所有操作
        """
        # TODO: 实现事务逻辑
        pass

    async def cancel_order(self, order_id: int) -> Order:
        """
        取消订单（回滚库存）

        TODO: 实现以下流程

        1. 获取订单
        2. 检查订单状态（只有 pending 状态可以取消）
        3. 恢复库存
        4. 更新订单状态为 cancelled
        """
        pass

# TODO: 实现 ProductService（商品管理）
# TODO: 实现 CartService（购物车管理）
```

### ✅ 完成标准

- [ ] 商品可以添加到购物车
- [ ] 购物车可以结算创建订单
- [ ] 创建订单时库存会正确扣减
- [ ] 库存不足时无法创建订单
- [ ] 取消订单时库存会恢复
- [ ] 所有操作使用事务保证一致性

### 💡 事务管理提示

**使用 yield 管理事务**：
```python
def get_db_transaction():
    """获取数据库事务（使用 yield）"""
    db = Database()
    try:
        db.begin()
        yield db
        db.commit()  # 没有异常，提交
    except Exception:
        db.rollback()  # 有异常，回滚
        raise
    finally:
        db.close()
```

**在 Service 中使用事务**：
```python
@app.post("/orders")
async def create_order(
    user_id: int,
    cart_id: int,
    db: Database = Depends(get_db_transaction),  # 自动管理事务
    service: OrderService = Depends(get_order_service),
):
    # 如果 service.create_order 抛出异常
    # 事务会自动回滚
    return await service.create_order(user_id, cart_id)
```

---

## 挑战项目 3: 任务队列系统

### 🎯 项目描述

实现一个异步任务队列系统，支持任务提交、执行、取消、重试。重点关注长时间运行任务的管理。

### 💡 费曼类比：快递配送系统

```
任务队列就像快递配送：

任务提交 = 下单
- 客户提交配送请求
- 系统分配任务编号

任务执行 = 配送中
- 快递员正在配送
- 可以查询进度

任务取消 = 取消订单
- 客户取消配送
- 停止配送

任务重试 = 配送失败重试
- 第一次没送到
- 重新配送
```

### 📋 需求列表

#### 核心功能
1. **任务管理**
   - [ ] 提交任务
   - [ ] 查询任务状态
   - [ ] 取消任务
   - [ ] 获取任务结果

2. **任务执行**
   - [ ] 异步执行任务
   - [ ] 进度更新
   - [ ] 失败重试

3. **统计监控**
   - [ ] 任务统计（总数、成功、失败、进行中）
   - [ ] 执行时间统计

### 🏗️ 架构设计

```python
# task_queue/models.py
from pydantic import BaseModel
from datetime import datetime
from enum import Enum
from typing import Optional, Any, Dict

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Task(BaseModel):
    id: str
    name: str
    status: TaskStatus
    progress: float  # 0.0 到 1.0
    result: Optional[Any]
    error: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    retry_count: int

class TaskCreate(BaseModel):
    name: str
    params: Dict[str, Any]
    max_retries: int = 3
```

```python
# task_queue/service.py
import asyncio
import uuid
from typing import Dict
from task_queue.models import Task, TaskStatus

class TaskQueueService:
    """任务队列服务"""

    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}

    async def submit(
        self,
        name: str,
        func: callable,
        params: dict,
        max_retries: int = 3
    ) -> str:
        """
        提交任务

        TODO: 实现逻辑
        1. 生成任务 ID
        2. 创建 Task 对象
        3. 保存到 self.tasks
        4. 异步执行任务
        5. 返回任务 ID
        """
        pass

    async def get_status(self, task_id: str) -> Optional[Task]:
        """获取任务状态"""
        # TODO: 实现逻辑
        pass

    async def cancel(self, task_id: str) -> bool:
        """
        取消任务

        TODO: 实现逻辑
        1. 检查任务状态
        2. 如果是 PENDING 或 RUNNING，取消
        3. 如果是 async task，调用 cancel()
        4. 更新任务状态
        """
        pass

    async def get_result(self, task_id: str) -> Optional[Any]:
        """获取任务结果"""
        # TODO: 实现逻辑
        pass

    def get_statistics(self) -> dict:
        """
        获取统计信息

        TODO: 返回
        - 总任务数
        - 各状态任务数
        - 平均执行时间
        """
        pass
```

### ✅ 完成标准

- [ ] 可以提交任务并获取任务 ID
- [ ] 可以查询任务状态和进度
- [ ] 可以取消正在执行的任务
- [ ] 任务失败后可以自动重试
- [ ] 可以获取任务统计信息
- [ ] 使用 Application-scoped 管理任务队列

### 💡 异步任务提示

**使用 asyncio 异步执行**：
```python
async def _run_task(self, task_id: str, func: callable, params: dict, max_retries: int):
    """
    内部方法：运行任务

    使用 asyncio.create_task() 异步执行
    """
    task = self.tasks[task_id]

    # 更新状态为 RUNNING
    task.status = TaskStatus.RUNNING
    task.started_at = datetime.now()

    try:
        # 执行任务
        result = await func(**params)

        # 更新状态为 COMPLETED
        task.status = TaskStatus.COMPLETED
        task.result = result
        task.completed_at = datetime.now()

    except Exception as e:
        # 任务失败
        if task.retry_count < max_retries:
            # 重试
            task.retry_count += 1
            await asyncio.sleep(2 ** task.retry_count)  # 指数退避
            await self._run_task(task_id, func, params, max_retries)
        else:
            # 超过重试次数，标记为 FAILED
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now()
```

---

## ✅ 总结检查清单

完成所有挑战项目后，检查你是否能够：

### 技术能力
- [ ] 设计并实现完整的分层架构
- [ ] 正确使用依赖注入解耦各层
- [ ] 合理选择依赖的生命周期
- [ ] 使用 yield 管理资源和事务
- [ ] 实现带重试和错误处理的异步任务
- [ ] 实现缓存和限流等横切关注点

### 架构理解
- [ ] 理解为什么要分层架构
- [ ] 理解依赖倒置原则
- [ ] 理解单一职责原则
- [ ] 理解开闭原则（对扩展开放，对修改关闭）

### 实践经验
- [ ] 能够独立设计 RESTful API
- [ ] 能够处理复杂业务逻辑
- [ ] 能够保证数据一致性
- [ ] 能够优化性能（缓存、限流）
- [ ] 能够编写可测试的代码

---

## 💡 学习建议

1. **循序渐进**
   - 先完成基础功能
   - 再添加高级功能
   - 最后优化性能

2. **测试驱动**
   - 为每个 Service 编写测试
   - Mock Repository 层
   - 验证业务逻辑

3. **文档先行**
   - 先设计 API 接口
   - 再实现内部逻辑
   - 最后编写文档

4. **代码审查**
   - 检查分层是否清晰
   - 检查依赖是否合理
   - 检查异常是否处理

5. **性能优化**
   - 使用缓存减少数据库查询
   - 使用限流保护 API
   - 使用异步提高并发

---

## 🎓 完成奖励

如果你完成了这三个挑战项目，恭喜你！

**你已经掌握了**：
- ✅ 完整的分层架构设计
- ✅ 依赖注入的最佳实践
- ✅ 事务管理和一致性保证
- ✅ 异步任务和队列系统
- ✅ 性能优化技巧（缓存、限流）
- ✅ 生产级代码的组织方式

**你已经可以**：
- 🚀 设计和实现生产级别的 FastAPI 应用
- 🚀 编写可维护、可测试的代码
- 🚀 处理复杂的业务逻辑
- 🚀 优化系统性能

**下一步**：
- 📚 学习 Level 3：数据库集成（SQLAlchemy、Alembic）
- 📚 学习 Level 4：认证授权（JWT、OAuth2）
- 📚 学习 Level 5：部署运维（Docker、K8s）

---

**记住：最好的学习方式就是实践！**

选择一个你最感兴趣的项目，开始动手吧！ 💪
