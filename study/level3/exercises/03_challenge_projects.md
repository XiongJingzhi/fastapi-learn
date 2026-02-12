# Level 3 综合项目 - Challenge Projects

## 📋 项目概述

这些综合项目帮助你将 Level 3 的所有知识整合到真实场景中。

## 🎯 项目目标

完成这些项目后，你将能够：
- ✅ 设计完整的数据库架构
- ✅ 实现生产级的 Repository 层
- ✅ 处理复杂的事务场景
- ✅ 管理数据库迁移

---

## 项目 1: 博客系统

### 功能需求

实现一个完整的博客系统 API。

#### 1.1 用户管理

**功能**：
- 用户注册、登录
- 个人资料管理
- 用户权限（普通用户/管理员）

**数据模型**：
```python
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="user")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)
```

**Repository 方法**：
- `create_user()`
- `find_by_email()`
- `find_by_username()`
- `update_password()`

#### 1.2 文章管理

**功能**：
- 创建、编辑、删除文章
- 文章状态（草稿/发布）
- 文章分类
- 文章标签

**数据模型**：
```python
class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    slug: Mapped[str] = mapped_column(String(200), unique=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id"))
    status: Mapped[str] = mapped_column(String(20), default="draft")
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)

    # 关系
    author: Mapped["User"] = relationship("User", back_populates="posts")
    category: Mapped[Optional["Category"]] = relationship("Category")
    tags: Mapped[List["Tag"]] = relationship(
        "PostTag", back_populates="post"
    )
```

**Repository 方法**：
- `create_post()`
- `find_published()`
- `find_by_slug()`
- `search_posts()`
- `increment_view_count()`
- `add_tag()`, `remove_tag()`

#### 1.3 评论系统

**功能**：
- 发表评论
- 评论审核
- 评论回复（嵌套评论）

**数据模型**：
```python
class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"))
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("comments.id"))
    content: Mapped[str] = mapped_column(Text)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime)

    # 关系
    post: Mapped["Post"] = relationship("Post")
    author: Mapped["User"] = relationship("User")
    parent: Mapped[Optional["Comment"]] = relationship("Comment", remote_side=[id])
    replies: Mapped[List["Comment"]] = relationship("Comment")
```

**Repository 方法**：
- `create_comment()`
- `find_approved_comments()`
- `find_replies()`
- `approve_comment()`

### 技术挑战

#### 挑战 1: 生成唯一 Slug

实现自动生成文章 URL slug（英文标题转 URL 友好格式）。

```python
def generate_slug(title: str) -> str:
    """
    生成 slug

    示例:
    "Hello World!" → "hello-world"
    "Python & FastAPI" → "python-fastapi"
    """
    # TODO: 实现
    pass
```

**要求**：
- 转小写
- 特殊字符转连字符
- 去除重复连字符
- 检查唯一性（如有重复添加数字后缀）

#### 挑战 2: 嵌套评论查询

查询评论树（递归结构）。

```python
async def get_comment_tree(post_id: int) -> List[dict]:
    """
    获取评论树

    Returns:
        [
            {
                "id": 1,
                "content": "Great post!",
                "replies": [
                    {"id": 2, "content": "Thanks!", "replies": []}
                ]
            }
        ]
    """
    pass
```

**方案选择**：
1. 递归查询（多次数库查询）
2. 一次性查询后构建树（推荐）
3. 使用数据库递归 CTE（高级）

#### 挑战 3: 文章搜索

实现全文搜索（标题和内容）。

```python
async def search_posts(
    keyword: str,
    category_id: Optional[int] = None,
    tag_ids: Optional[List[int]] = None
) -> List[Post]:
    """
    搜索文章

    支持关键词、分类、标签组合查询
    """
    pass
```

### API Endpoints

```python
# 用户
POST   /api/register
POST   /api/login
GET    /api/users/me
PUT    /api/users/me

# 文章
POST   /api/posts
GET    /api/posts
GET    /api/posts/{slug}
PUT    /api/posts/{id}
DELETE /api/posts/{id}

# 分类
POST   /api/categories
GET    /api/categories

# 标签
POST   /api/tags
GET    /api/tags

# 评论
POST   /api/posts/{post_id}/comments
GET    /api/posts/{post_id}/comments
```

---

## 项目 2: 电商订单系统

### 功能需求

实现一个电商订单系统，重点演示事务管理。

#### 2.1 商品管理

**数据模型**：
```python
class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text)
    price: Mapped[float] = mapped_column(Float)
    stock: Mapped[int] = mapped_column(Integer, default=0)
    sku: Mapped[str] = mapped_column(String(50), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)
```

#### 2.2 订单管理

**数据模型**：
```python
class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    total_amount: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)

    # 关系
    items: Mapped[List["OrderItem"]] = relationship(
        "OrderItem", back_populates="order"
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[float] = mapped_column(Float)
    total_price: Mapped[float] = mapped_column(Float)

    # 关系
    order: Mapped["Order"] = relationship("Order", back_populates="items")
    product: Mapped["Product"] = relationship("Product")
```

### 核心事务场景

#### 场景 1: 创建订单（库存扣减）

```python
async def create_order(
    user_id: int,
    items: List[dict]  # [{"product_id": 1, "quantity": 2}]
) -> Order:
    """
    创建订单（原子操作）

    事务步骤:
    1. 查询所有商品
    2. 检查库存
    3. 扣减库存
    4. 创建订单
    5. 创建订单项
    6. 计算总价

    任何步骤失败 → 全部回滚
    """
    async with session.begin():
        # TODO: 实现
        pass
```

**挑战**：
- 使用 `with_for_update()` 锁定商品行（防止并发超卖）
- 实现库存不足时的部分库存处理

#### 场景 2: 订单支付

```python
async def process_payment(
    order_id: int,
    payment_method: str,
    amount: float
) -> dict:
    """
    处理支付

    事务步骤:
    1. 查询订单
    2. 调用支付网关（模拟）
    3. 更新订单状态
    4. 记录支付日志
    """
    async with session.begin():
        # TODO: 实现
        pass
```

**挑战**：
- 支付失败时回滚
- 幂等性（防止重复支付）

#### 场景 3: 订单退款

```python
async def refund_order(
    order_id: int,
    reason: str
) -> bool:
    """
    订单退款

    事务步骤:
    1. 查询订单
    2. 恢复库存
    3. 更新订单状态
    4. 记录退款日志
    """
    async with session.begin():
        # TODO: 实现
        pass
```

### 并发控制

#### 问题场景

```
时刻 1: 用户 A 查询商品 (stock=1)
时刻 2: 用户 B 查询商品 (stock=1)
时刻 3: 用户 A 下单 (stock=0)
时刻 4: 用户 B 下单 (stock=-1) ← 问题！
```

#### 解决方案

使用悲观锁：

```python
async def create_order_with_lock(
    user_id: int,
    items: List[dict]
) -> Order:
    async with session.begin():
        for item in items:
            # 锁定商品行
            stmt = (
                select(Product)
                .where(Product.id == item["product_id"])
                .with_for_update()  # ← 加锁
            )
            result = await session.execute(stmt)
            product = result.scalar_one()

            # 检查库存（此时其他事务无法修改）
            if product.stock < item["quantity"]:
                raise InsufficientStockException(...)

            # 扣减库存
            product.stock -= item["quantity"]

        # ... 创建订单
```

### API Endpoints

```python
# 商品
POST   /api/products
GET    /api/products
GET    /api/products/{id}
PUT    /api/products/{id}

# 订单
POST   /api/orders
GET    /api/orders
GET    /api/orders/{id}
POST   /api/orders/{id}/pay
POST   /api/orders/{id}/refund

# 库存
POST   /api/products/{id}/stock
GET    /api/products/low-stock  # 库存预警
```

---

## 项目 3: 数据迁移实战

### 需求描述

模拟真实项目的数据库迁移场景。

#### 场景 1: 表结构演进

**版本 1 - 初始版本**
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(50),
    email VARCHAR(100)
);
```

**版本 2 - 添加字段**
```sql
ALTER TABLE users ADD COLUMN created_at TIMESTAMP;
ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT TRUE;
```

**版本 3 - 修改字段**
```sql
ALTER TABLE users ALTER COLUMN username TYPE VARCHAR(100);
```

**版本 4 - 添加索引**
```sql
CREATE INDEX idx_users_email ON users(email);
CREATE UNIQUE INDEX idx_users_username ON users(username);
```

**任务**：
- 为每个版本创建 Alembic 迁移脚本
- 实现 upgrade() 和 downgrade()
- 测试升级和降级

#### 场景 2: 数据迁移

**迁移任务**：将 `full_name` 字段拆分为 `first_name` 和 `last_name`

```python
# migration: split_full_name.py

def upgrade() -> None:
    # 1. 添加新列
    op.add_column('users', sa.Column('first_name', sa.String(50)))
    op.add_column('users', sa.Column('last_name', sa.String(50)))

    # 2. 迁移数据
    connection = op.get_bind()
    # TODO: 执行数据迁移

    # 3. 删除旧列
    op.drop_column('users', 'full_name')


def downgrade() -> None:
    # 1. 恢复旧列
    op.add_column('users', sa.Column('full_name', sa.String(100)))

    # 2. 合并数据
    # TODO: 实现

    # 3. 删除新列
    op.drop_column('users', 'first_name')
    op.drop_column('users', 'last_name')
```

**要求**：
- 使用批量处理（避免内存问题）
- 处理异常情况（如 NULL 值）
- 提供回滚方案

#### 场景 3: 大表迁移

**问题**：users 表有 1000 万条数据，如何安全迁移？

**方案 1: 分批迁移**
```python
def upgrade_large_table():
    batch_size = 10000
    offset = 0

    while True:
        # 查询一批
        result = session.execute(
            "SELECT id FROM users LIMIT :limit OFFSET :offset",
            {"limit": batch_size, "offset": offset}
        )

        rows = result.fetchall()
        if not rows:
            break

        # 处理这批
        for row in rows:
            # TODO: 处理
            pass

        offset += batch_size
```

**方案 2: 使用新表**
```python
def upgrade_with_new_table():
    # 1. 创建新表
    op.create_table('users_new', ...)

    # 2. 分批复制数据
    # TODO: 实现分批复制

    # 3. 重命名表
    op.rename_table('users', 'users_old')
    op.rename_table('users_new', 'users')

    # 4. 删除旧表（在后续迁移中）
```

---

## 🎯 评分标准

### 功能完整性 (40%)

- [ ] 所有核心功能实现
- [ ] Repository 接口完整
- [ ] Service 层业务逻辑清晰
- [ ] API 端点可访问

### 架构设计 (30%)

- [ ] 正确使用 Repository 模式
- [ ] 依赖注入配置正确
- [ ] 事务边界合理
- [ ] 代码分层清晰

### 代码质量 (20%)

- [ ] 类型提示完整
- [ ] 文档字符串完整
- [ ] 错误处理完善
- [ ] 代码风格一致

### 测试覆盖 (10%)

- [ ] 单元测试（Repository）
- [ ] 集成测试（Service）
- [ ] API 测试（Endpoints）

---

## 📚 参考资源

- 示例代码: `../examples/`
- 笔记: `../notes/`
- SQLAlchemy 文档: https://docs.sqlalchemy.org/
- Alembic 文档: https://alembic.sqlalchemy.org/

---

## 🚀 提交检查

完成项目后，确保：

### 代码仓库
- [ ] 使用 Git 版本控制
- [ ] 提交信息清晰
- [ ] Alembic 迁移脚本纳入版本控制

### 文档
- [ ] README.md 说明如何运行
- [ ] API 文档（Swagger/OpenAPI）
- [ ] 数据库模型文档
- [ ] 迁移说明

### 部署
- [ ] 提供 docker-compose.yml
- [ ] 环境变量配置文件示例
- [ ] 迁移脚本可执行

---

## 🎊 恭喜！

完成 Level 3 的所有学习内容！你已经掌握：

- ✅ 数据库集成
- ✅ Repository 模式
- ✅ 事务管理
- ✅ 数据迁移
- ✅ 生产级代码

**准备好进入 Level 4: 生产就绪！** 🚀

下一个 Level 将学习：
- 缓存集成（Redis）
- 消息队列（Kafka/RabbitMQ）
- 外部 API 集成
- 连接池、超时、重试
- 限流、熔断、降级

**继续加油！** 💪
