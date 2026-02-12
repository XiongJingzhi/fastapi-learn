"""
示例 3.2: SQLAlchemy 核心 - SQLAlchemy Core & ORM

学习目标:
1. 理解 SQLAlchemy 的架构（Core vs ORM）
2. 掌握模型定义和关系映射
3. 学习各种查询方式
4. 理解关系类型（一对一、一对多、多对多）
5. 掌握高级查询技巧

运行方式:
    # 1. 启动 PostgreSQL
    docker run --name fastapi-db -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=fastapi -p 5432:5432 -d postgres:16

    # 2. 运行示例
    python study/level3/examples/02_sqlalchemy_basics.py

测试方式:
    curl http://localhost:8001/docs
"""

from typing import List, Optional
from datetime import datetime
from enum import Enum

from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy import (
    String, Boolean, DateTime, Integer, Text, Float, ForeignKey,
    select, insert, update, delete, func, and_, or_, desc
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, mapped_column,
    relationship, joinedload, selectinload
)
from sqlalchemy.types import Enum as SQLEnum

# ══════════════════════════════════════════════════════════════════════════
# SQLAlchemy 架构说明
# ══════════════════════════════════════════════════════════════════════════
#
# SQLAlchemy 有两层:
#
# ┌─────────────────────────────────────────────────────────────────┐
# │                     SQLAlchemy 架构                             │
# └─────────────────────────────────────────────────────────────────┘
#
# ┌─────────────────────────────────────────────────────────────────┐
# │ ORM (对象关系映射)                                            │
# │                                                              │
# │  class User(Base):                                           │
# │      __tablename__ = "users"                                  │
# │      id = Column(Integer, primary_key=True)                    │
# │                                                              │
# │  user = User(name="Alice")                                    │
# │  session.add(user)                                           │
# │                                                              │
# │  ✅ 面向对象，类型安全，自动映射                             │
# └─────────────────────────────────────────────────────────────────┘
#                          │
#                          │ 建立在 Core 之上
#                          ▼
# ┌─────────────────────────────────────────────────────────────────┐
# │ Core (SQL 表达式语言)                                         │
# │                                                              │
# │  stmt = insert(User).values(name="Alice")                      │
# │  await session.execute(stmt)                                  │
# │                                                              │
# │  ✅ 接近原生 SQL，性能更好，更灵活                            │
# └─────────────────────────────────────────────────────────────────┘
#
# ══════════════════════════════════════════════════════════════════════════


# ==================== 数据库配置 ====================

DATABASE_URL = "sqlite+aiosqlite:///../fastapi_orm.db"

engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # 打印 SQL
    connect_args={"check_same_thread": False}
)

async_session = async_sessionmaker(
    engine,
    expire_on_commit=False
)


# ==================== 模型定义 ====================

class Base(DeclarativeBase):
    """所有模型的基类"""
    pass


# ══════════════════════════════════════════════════════════════════════════
# 1. 枚举类型定义
# ══════════════════════════════════════════════════════════════════════════

class OrderStatus(str, Enum):
    """订单状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


# ══════════════════════════════════════════════════════════════════════════
# 2. 用户模型 (User Model)
# ══════════════════════════════════════════════════════════════════════════

class User(Base):
    """
    用户模型

    对应 SQL:
    CREATE TABLE users (
        id INTEGER PRIMARY KEY,
        username VARCHAR(50) NOT NULL UNIQUE,
        email VARCHAR(100) NOT NULL UNIQUE,
        full_name VARCHAR(100),
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    __tablename__ = "users"

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # 基本字段
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True  # 创建索引（加速查询）
    )
    email: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True
    )
    full_name: Mapped[Optional[str]] = mapped_column(String(100))

    # 状态字段
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    # ═══════════════════════════════════════════════════════════════════
    # 关系定义 (Relationships)
    # ═══════════════════════════════════════════════════════════════════
    #
    # relationship() 定义模型之间的关联
    #
    # 参数说明:
    # - back_populates: 反向关系字段名
    # - uselist: 是否返回列表 (一对一=False, 一对多=True)
    # - cascade: 级联操作 (删除用户时是否删除关联数据)
    #
    # ═══════════════════════════════════════════════════════════════════

    # 一对多: 一个用户有多个订单
    orders: Mapped[List["Order"]] = relationship(
        "Order",
        back_populates="user",
        cascade="all, delete-orphan"  # 删除用户时删除订单
    )

    # 一对一: 一个用户有一个资料卡
    profile: Mapped[Optional["UserProfile"]] = relationship(
        "UserProfile",
        back_populates="user",
        uselist=False,  # 一对一
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username})>"


# ══════════════════════════════════════════════════════════════════════════
# 3. 用户资料模型 (一对一关系)
# ══════════════════════════════════════════════════════════════════════════

class UserProfile(Base):
    """
    用户资料模型 (一对一)

    对应 SQL:
    CREATE TABLE user_profiles (
        id INTEGER PRIMARY KEY,
        user_id INTEGER UNIQUE,
        bio TEXT,
        avatar_url VARCHAR(255),
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    """

    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # 外键 (唯一 → 一对一)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        unique=True  # UNIQUE 保证一对一
    )

    # 资料字段
    bio: Mapped[Optional[str]] = mapped_column(Text)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(255))

    # 反向关系: 指向 User
    user: Mapped[User] = relationship(
        "User",
        back_populates="profile"
    )

    def __repr__(self) -> str:
        return f"<UserProfile(id={self.id}, user_id={self.user_id})>"


# ══════════════════════════════════════════════════════════════════════════
# 4. 产品模型 (多对多关系的一方)
# ══════════════════════════════════════════════════════════════════════════

class Product(Base):
    """
    产品模型

    对应 SQL:
    CREATE TABLE products (
        id INTEGER PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        description TEXT,
        price DECIMAL(10, 2) NOT NULL,
        stock INTEGER DEFAULT 0
    );
    """

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text)
    price: Mapped[float] = mapped_column(Float)
    stock: Mapped[int] = mapped_column(Integer, default=0)

    # 多对多: 一个产品可以在多个订单中
    # 通过 OrderItem 关联表
    order_items: Mapped[List["OrderItem"]] = relationship(
        "OrderItem",
        back_populates="product"
    )

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, name={self.name}, price={self.price})>"


# ══════════════════════════════════════════════════════════════════════════
# 5. 订单模型 (一对多关系的一端)
# ══════════════════════════════════════════════════════════════════════════

class Order(Base):
    """
    订单模型

    对应 SQL:
    CREATE TABLE orders (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        status VARCHAR(20) DEFAULT 'pending',
        total_price DECIMAL(10, 2),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    """

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # 外键 → User (一对多)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id")
    )

    # 订单字段
    status: Mapped[OrderStatus] = mapped_column(
        SQLEnum(OrderStatus),
        default=OrderStatus.PENDING
    )
    total_price: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    # 关系
    user: Mapped[User] = relationship(
        "User",
        back_populates="orders"
    )

    # 一对多: 一个订单有多个订单项
    items: Mapped[List["OrderItem"]] = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Order(id={self.id}, user_id={self.user_id}, status={self.status})>"


# ══════════════════════════════════════════════════════════════════════════
# 6. 订单项模型 (关联表 - 多对多)
# ══════════════════════════════════════════════════════════════════════════

class OrderItem(Base):
    """
    订单项模型 (关联表)

    对应 SQL:
    CREATE TABLE order_items (
        id INTEGER PRIMARY KEY,
        order_id INTEGER,
        product_id INTEGER,
        quantity INTEGER NOT NULL,
        price DECIMAL(10, 2) NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    );
    """

    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # 外键
    order_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("orders.id")
    )
    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.id")
    )

    # 字段
    quantity: Mapped[int] = mapped_column(Integer)
    price: Mapped[float] = mapped_column(Float)

    # 关系
    order: Mapped[Order] = relationship(
        "Order",
        back_populates="items"
    )
    product: Mapped[Product] = relationship(
        "Product",
        back_populates="order_items"
    )

    def __repr__(self) -> str:
        return f"<OrderItem(id={self.id}, order_id={self.order_id}, product_id={self.product_id})>"


# ==================== 数据库操作 ====================

async def init_database():
    """初始化数据库"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database initialized successfully!")


# ══════════════════════════════════════════════════════════════════════════
# 基础 CRUD 操作 (使用 ORM)
# ══════════════════════════════════════════════════════════════════════════

async def create_user(
    session: AsyncSession,
    username: str,
    email: str,
    full_name: Optional[str] = None
) -> User:
    """创建用户"""
    user = User(
        username=username,
        email=email,
        full_name=full_name
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def get_user_with_profile(session: AsyncSession, user_id: int) -> Optional[User]:
    """
    获取用户及其资料 (Eager Loading)

    ══════════════════════════════════════════════════════════════════════════
    预加载策略 (Eager Loading Strategies)
    ══════════════════════════════════════════════════════════════════════════

    问题: N+1 查询
    ───────────────────────────────────────────────────────────────────────────────
    # ❌ 懒加载 (Lazy Loading) - 会导致 N+1 查询
    users = await session.execute(select(User))
    for user in users.scalars():
        print(user.profile.bio)  # 每次访问 profile 都会查询数据库！

    解决方案: 使用预加载
    ───────────────────────────────────────────────────────────────────────────────

    1. joinedload() - 使用 JOIN 查询 (一对一、一对多推荐)
    ══════════════════════════════════════════════════════════════════════════
    优点: 一次查询获取所有数据
    缺点: JOIN 可能导致重复数据
    适用: 一对一、一对多关系
    """
    stmt = (
        select(User)
        .where(User.id == user_id)
        .options(joinedload(User.profile))  # JOIN 查询
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

    """
    2. selectinload() - 使用单独的查询 (多对多推荐)
    ══════════════════════════════════════════════════════════════════════════
    优点: 避免 JOIN 导致的重复
    缺点: 需要两次查询
    适用: 多对多关系
    """
    stmt = (
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.orders))  # 单独查询
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_order(
    session: AsyncSession,
    user_id: int,
    items: List[dict]
) -> Order:
    """
    创建订单 (演示事务)

    ══════════════════════════════════════════════════════════════════════════
    事务说明
    ══════════════════════════════════════════════════════════════════════════
    所有操作在一个事务中:
    - 创建订单
    - 创建订单项
    - 更新库存
    全部成功或全部失败！
    """
    try:
        # 1. 创建订单
        order = Order(user_id=user_id, status=OrderStatus.PENDING)
        session.add(order)

        # 2. 创建订单项并计算总价
        total_price = 0.0
        for item_data in items:
            # 查询产品
            product = await session.get(Product, item_data["product_id"])
            if not product:
                raise ValueError(f"Product {item_data['product_id']} not found")

            # 检查库存
            if product.stock < item_data["quantity"]:
                raise ValueError(f"Insufficient stock for {product.name}")

            # 创建订单项
            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=item_data["quantity"],
                price=product.price
            )
            session.add(order_item)

            # 更新库存
            product.stock -= item_data["quantity"]

            total_price += product.price * item_data["quantity"]

        # 3. 更新订单总价
        order.total_price = total_price

        # 4. 提交事务
        await session.commit()
        await session.refresh(order)

        return order

    except Exception as e:
        await session.rollback()
        raise e


# ══════════════════════════════════════════════════════════════════════════
# 复杂查询 (Advanced Queries)
# ══════════════════════════════════════════════════════════════════════════

async def search_users(
    session: AsyncSession,
    keyword: str,
    is_active: Optional[bool] = None
) -> List[User]:
    """
    搜索用户 (多条件查询)

    ══════════════════════════════════════════════════════════════════════════
    使用 and_(), or_() 组合条件
    ══════════════════════════════════════════════════════════════════════════
    """
    conditions = []

    # 用户名或邮箱包含关键词
    conditions.append(
        or_(
            User.username.contains(keyword),
            User.email.contains(keyword)
        )
    )

    # 可选: 只查询活跃用户
    if is_active is not None:
        conditions.append(User.is_active == is_active)

    # 组合所有条件
    stmt = select(User).where(and_(*conditions))

    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_user_statistics(session: AsyncSession) -> dict:
    """
    获取用户统计 (使用聚合函数)

    ══════════════════════════════════════════════════════════════════════════
    聚合函数 (Aggregate Functions)
    ══════════════════════════════════════════════════════════════════════════
    - func.count(): 计数
    - func.sum(): 求和
    - func.avg(): 平均值
    - func.max()/func.min(): 最大值/最小值
    """
    # 总用户数
    count_stmt = select(func.count(User.id))
    total_result = await session.execute(count_stmt)
    total_count = total_result.scalar()

    # 活跃用户数
    active_stmt = select(func.count(User.id)).where(User.is_active == True)
    active_result = await session.execute(active_stmt)
    active_count = active_result.scalar()

    return {
        "total_users": total_count,
        "active_users": active_count,
        "inactive_users": total_count - active_count
    }


async def get_orders_with_items(
    session: AsyncSession,
    user_id: int
) -> List[Order]:
    """
    获取用户订单及其订单项 (多级预加载)

    ══════════════════════════════════════════════════════════════════════════
    多级关系加载
    ══════════════════════════════════════════════════════════════════════════
    Order → OrderItem → Product (三级关系)
    """
    stmt = (
        select(Order)
        .where(Order.user_id == user_id)
        .options(
            joinedload(Order.items),  # 加载订单项
            joinedload(Order.items).joinedload(OrderItem.product)  # 加载产品
        )
        .order_by(desc(Order.created_at))
    )

    result = await session.execute(stmt)
    return list(result.scalars().all())


# ══════════════════════════════════════════════════════════════════════════
# 使用 Core (SQL 表达式)
# ══════════════════════════════════════════════════════════════════════════

async def bulk_create_products(
    session: AsyncSession,
    products_data: List[dict]
) -> int:
    """
    批量插入产品 (使用 Core)

    ══════════════════════════════════════════════════════════════════════════
    ORM vs Core 性能对比
    ══════════════════════════════════════════════════════════════════════════

    ORM 方式 (慢):
    for data in products_data:
        product = Product(**data)
        session.add(product)
    # 1000 条数据需要 1000 次 INSERT

    Core 方式 (快):
    stmt = insert(Product).values(products_data)
    await session.execute(stmt)
    # 1000 条数据只需要 1 次 INSERT
    """
    stmt = insert(Product).values(products_data)

    result = await session.execute(stmt)
    await session.commit()

    return result.rowcount


async def update_user_status_batch(
    session: AsyncSession,
    user_ids: List[int],
    is_active: bool
) -> int:
    """
    批量更新用户状态

    使用 Core 的 update() 语句，性能更好
    """
    stmt = (
        update(User)
        .where(User.id.in_(user_ids))
        .values(is_active=is_active)
    )

    result = await session.execute(stmt)
    await session.commit()

    return result.rowcount


# ==================== FastAPI 应用 ====================

app = FastAPI(
    title="SQLAlchemy 核心",
    description="演示 SQLAlchemy 的 ORM 和 Core 用法",
    version="2.0.0"
)


@app.on_event("startup")
async def startup_event():
    await init_database()


# ══════════════════════════════════════════════════════════════════════════
# Pydantic 模型
# ══════════════════════════════════════════════════════════════════════════

class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    stock: int = 0


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int


class OrderCreate(BaseModel):
    user_id: int
    items: List[OrderItemCreate]


# ══════════════════════════════════════════════════════════════════════════
# Endpoints
# ══════════════════════════════════════════════════════════════════════════

@app.post("/users")
async def create_user_endpoint(
    username: str,
    email: str,
    full_name: Optional[str] = None
):
    """创建用户"""
    async with async_session() as session:
        user = await create_user(session, username, email, full_name)
        return user


@app.get("/users/{user_id}")
async def get_user_endpoint(user_id: int):
    """获取用户（带资料卡）"""
    async with async_session() as session:
        user = await get_user_with_profile(session, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user


@app.post("/orders")
async def create_order_endpoint(order_data: OrderCreate):
    """创建订单（演示事务）"""
    async with async_session() as session:
        try:
            order = await create_order(
                session,
                order_data.user_id,
                [item.dict() for item in order_data.items]
            )
            return order
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))


@app.get("/users/{user_id}/orders")
async def get_user_orders_endpoint(user_id: int):
    """获取用户订单（带订单项和产品）"""
    async with async_session() as session:
        orders = await get_orders_with_items(session, user_id)
        return orders


@app.get("/statistics")
async def get_statistics_endpoint():
    """获取统计信息"""
    async with async_session() as session:
        return await get_user_statistics(session)


@app.post("/products/bulk")
async def bulk_create_products_endpoint(products: List[ProductCreate]):
    """批量创建产品"""
    async with async_session() as session:
        products_data = [p.dict() for p in products]
        count = await bulk_create_products(session, products_data)
        return {"created": count}


@app.get("/")
async def root():
    return {
        "name": "SQLAlchemy 核心",
        "version": "2.0.0",
        "features": [
            "ORM 模型定义",
            "关系映射 (一对一、一对多、多对多)",
            "Eager Loading (joinedload, selectinload)",
            "复杂查询",
            "批量操作 (Core)"
        ],
        "docs": "/docs"
    }


# ==================== 运行说明 ====================
"""
═══════════════════════════════════════════════════════════════════════════
SQLAlchemy 核心总结
═══════════════════════════════════════════════════════════════════════════

1. SQLAlchemy 两层架构
   - ORM: 面向对象，类型安全
   - Core: 接近原生 SQL，性能更好

2. 模型定义
   - Mapped[type]: 类型注解
   - mapped_column(): 列定义
   - relationship(): 关系定义

3. 关系类型
   - 一对一: UserProfile → User
   - 一对多: User → Orders
   - 多对多: Orders ↔ Products (through OrderItem)

4. Eager Loading (避免 N+1 查询)
   - joinedload(): JOIN 查询
   - selectinload(): 单独查询

5. 批量操作
   - ORM: 适合少量数据
   - Core: 适合大量数据

═══════════════════════════════════════════════════════════════════════════
测试示例
═══════════════════════════════════════════════════════════════════════════

# 1. 创建用户
curl -X POST "http://localhost:8001/users?username=alice&email=alice@example.com"

# 2. 创建订单
curl -X POST "http://localhost:8001/orders" \\
      -H "Content-Type: application/json" \\
      -d '{
        "user_id": 1,
        "items": [
          {"product_id": 1, "quantity": 2},
          {"product_id": 2, "quantity": 1}
        ]
      }'

# 3. 获取用户订单（带预加载）
curl "http://localhost:8001/users/1/orders"

# 4. 获取统计信息
curl "http://localhost:8001/statistics"

═══════════════════════════════════════════════════════════════════════════
下一步学习
═══════════════════════════════════════════════════════════════════════════

掌握了 SQLAlchemy 基础后，继续学习:
1. Repository 模式 → examples/03_repository_pattern.py
2. 事务管理 → examples/04_transactions.py

═══════════════════════════════════════════════════════════════════════════
"""
