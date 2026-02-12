"""
示例 3.4: 事务管理 - Transaction Management

学习目标:
1. 理解事务的 ACID 特性
2. 掌握 FastAPI 中的事务管理
3. 学习如何处理事务失败和回滚
4. 理解嵌套事务
5. 学习并发控制（锁、隔离级别）

运行方式:
    # 1. 启动 PostgreSQL
    docker run --name fastapi-db -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=fastapi -p 5432:5432 -d postgres:16

    # 2. 运行示例
    python study/level3/examples/04_transactions.py

测试方式:
    curl http://localhost:8003/docs
"""

from typing import List, Optional
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, update, text, and_
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import String, Boolean, DateTime, Integer, Float

# ══════════════════════════════════════════════════════════════════════════
# 架构说明: 为什么需要事务管理？
# ══════════════════════════════════════════════════════════════════════════
#
# 没有事务的问题 (数据不一致):
# ────────────────────────────────────────────────────────────────────────────────────────
#
# 场景: 银行转账
#
# async def transfer_money(user_id_from: int, user_id_to: int, amount: int):
#     # 1. 扣钱
#     await db.execute(
#         "UPDATE users SET balance = balance - $1 WHERE id = $2",
#         amount, user_id_from
#     )
#
#     # ❌ 如果这里崩溃？
#     # 钱扣了但没到账！
#
#     # 2. 加钱
#     await db.execute(
#         "UPDATE users SET balance = balance + $1 WHERE id = $2",
#         amount, user_id_to
#     )
#
# 问题: 数据不一致 (钱凭空消失)
#
# ══════════════════════════════════════════════════════════════════════════
# 解决方案: 使用事务 (保证一致性)
# ══════════════════════════════════════════════════════════════════════════
#
# async def transfer_money(user_id_from: int, user_id_to: int, amount: int):
#     async with db.begin():  # ← 开始事务
#         # 1. 扣钱
#         await db.execute(...)
#
#         # 2. 加钱
#         await db.execute(...)
#
#         # 3. 提交事务 (自动)
#         # await db.commit()
#
#     # 如果任何步骤失败，自动回滚！
#
# 好处: 全部成功或全部失败 (数据一致)
#
# ══════════════════════════════════════════════════════════════════════════


# ==================== 数据库配置 ====================

DATABASE_URL = "sqlite+aiosqlite:///../fastapi_transactions.db"

engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # 打印 SQL (观察事务)
    connect_args={"check_same_thread": False}
)

async_session = async_sessionmaker(
    engine,
    expire_on_commit=False
)


# ==================== 模型定义 ====================

class Base(DeclarativeBase):
    pass


class Account(Base):
    """
    账户模型

    用于演示转账事务
    """
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner: Mapped[str] = mapped_column(String(50))
    balance: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Account(id={self.id}, owner={self.owner}, balance={self.balance})>"


class Product(Base):
    """
    产品模型

    用于演示库存管理事务
    """
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    stock: Mapped[int] = mapped_column(Integer, default=0)
    price: Mapped[float] = mapped_column(Float)

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, name={self.name}, stock={self.stock})>"


class Order(Base):
    """
    订单模型

    用于演示复杂事务 (多个操作)
    """
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(Integer)
    quantity: Mapped[int] = mapped_column(Integer)
    total_price: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Order(id={self.id}, product_id={self.product_id}, quantity={self.quantity})>"


# ==================== 数据库操作 ====================

async def init_database():
    """初始化数据库"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # 初始化测试数据
        await conn.execute(
            text("""
                INSERT OR IGNORE INTO accounts (id, owner, balance) VALUES
                (1, 'Alice', 1000.0),
                (2, 'Bob', 500.0)
            """)
        )
        await conn.execute(
            text("""
                INSERT OR IGNORE INTO products (id, name, stock, price) VALUES
                (1, 'Laptop', 10, 1000.0),
                (2, 'Mouse', 50, 50.0)
            """)
        )

    print("✅ Database initialized successfully!")


# ══════════════════════════════════════════════════════════════════════════
# 事务管理示例
# ══════════════════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════════════════
# 1. 手动管理事务 (Manual Transaction Management)
# ══════════════════════════════════════════════════════════════════════════

async def transfer_money_manual(
    session: AsyncSession,
    from_id: int,
    to_id: int,
    amount: float
) -> bool:
    """
    转账 (手动管理事务)

    ══════════════════════════════════════════════════════════════════════════
    手动事务流程
    ══════════════════════════════════════════════════════════════════════════
    1. 执行操作 (session 默认在事务中)
    2. 成功: session.commit()
    3. 失败: session.rollback()
    ══════════════════════════════════════════════════════════════════════════
    """
    try:
        # 1. 扣钱
        from_account = await session.get(Account, from_id)
        if not from_account or from_account.balance < amount:
            raise ValueError("Insufficient balance")

        from_account.balance -= amount

        # 2. 加钱
        to_account = await session.get(Account, to_id)
        if not to_account:
            raise ValueError("Recipient account not found")

        to_account.balance += amount

        # 3. 提交事务
        await session.commit()

        print(f"✅ Transferred {amount} from {from_account.owner} to {to_account.owner}")
        return True

    except Exception as e:
        # 4. 回滚事务
        await session.rollback()
        print(f"❌ Transfer failed: {e}, transaction rolled back")
        raise e


# ══════════════════════════════════════════════════════════════════════════
# 2. 使用 Context Manager (推荐)
# ══════════════════════════════════════════════════════════════════════════

async def transfer_money_auto(
    session: AsyncSession,
    from_id: int,
    to_id: int,
    amount: float
) -> bool:
    """
    转账 (使用 Context Manager)

    ══════════════════════════════════════════════════════════════════════════
    async with session.begin() 的行为
    ══════════════════════════════════════════════════════════════════════════
    - 进入 with 块: 自动开始事务
    - 正常退出: 自动提交 (commit)
    - 异常退出: 自动回滚 (rollback)

    ✅ 推荐: 更简洁，不容易出错
    ══════════════════════════════════════════════════════════════════════════
    """
    try:
        async with session.begin():  # ← 自动管理事务
            # 1. 扣钱
            from_account = await session.get(Account, from_id)
            if not from_account or from_account.balance < amount:
                raise ValueError("Insufficient balance")

            from_account.balance -= amount

            # 2. 加钱
            to_account = await session.get(Account, to_id)
            if not to_account:
                raise ValueError("Recipient account not found")

            to_account.balance += amount

            # 3. 自动提交 (with 块结束时)
            print(f"✅ Transferred {amount} from {from_account.owner} to {to_account.owner}")
            return True

    except Exception as e:
        # 自动回滚
        print(f"❌ Transfer failed: {e}, transaction rolled back")
        raise e


# ══════════════════════════════════════════════════════════════════════════
# 3. 复杂事务 (多个操作)
# ══════════════════════════════════════════════════════════════════════════

async def create_order(
    session: AsyncSession,
    product_id: int,
    quantity: int
) -> Order:
    """
    创建订单 (复杂事务)

    ══════════════════════════════════════════════════════════════════════════
    事务操作流程
    ══════════════════════════════════════════════════════════════════════════
    1. 查询产品
    2. 检查库存
    3. 扣减库存
    4. 创建订单
    5. 计算总价
    全部成功或全部失败！
    ══════════════════════════════════════════════════════════════════════════
    """
    async with session.begin():
        # 1. 查询产品
        product = await session.get(Product, product_id)
        if not product:
            raise ValueError(f"Product {product_id} not found")

        # 2. 检查库存
        if product.stock < quantity:
            raise ValueError(
                f"Insufficient stock. Only {product.stock} available, requested {quantity}"
            )

        # 3. 扣减库存
        product.stock -= quantity

        # 4. 创建订单
        order = Order(
            product_id=product_id,
            quantity=quantity,
            total_price=product.price * quantity,
            status="confirmed"
        )
        session.add(order)

        # 5. 自动提交
        print(f"✅ Order created: {order.id}, product stock updated: {product.stock}")
        return order


# ══════════════════════════════════════════════════════════════════════════
# 4. 嵌套事务 (Nested Transactions / Savepoints)
# ══════════════════════════════════════════════════════════════════════════

async def create_order_with_logging(
    session: AsyncSession,
    product_id: int,
    quantity: int
) -> Order:
    """
    创建订单 (带日志记录)

    ══════════════════════════════════════════════════════════════════════════
    嵌套事务说明
    ══════════════════════════════════════════════════════════════════════════
    - 外层事务: 创建订单、扣减库存
    - 内层事务: 记录日志

    如果内层失败，不影响外层事务
    (使用 SAVEPOINT)

    注意: SQLite 不完全支持嵌套事务，PostgreSQL 完全支持
    ══════════════════════════════════════════════════════════════════════════
    """
    async with session.begin():
        # 外层事务: 创建订单
        product = await session.get(Product, product_id)
        if not product or product.stock < quantity:
            raise ValueError("Product not available")

        product.stock -= quantity

        order = Order(
            product_id=product_id,
            quantity=quantity,
            total_price=product.price * quantity
        )
        session.add(order)

        # 内层事务: 记录日志
        # 注意: 这里使用 nested() 创建保存点
        # async with session.begin_nested():
        #     # 记录日志
        #     log = OrderLog(order_id=order.id, message="Order created")
        #     session.add(log)

        return order


# ══════════════════════════════════════════════════════════════════════════
# 5. 并发控制 (锁)
# ══════════════════════════════════════════════════════════════════════════

async def create_order_with_lock(
    session: AsyncSession,
    product_id: int,
    quantity: int
) -> Order:
    """
    创建订单 (使用锁)

    ══════════════════════════════════════════════════════════════════════════
    并发问题
    ══════════════════════════════════════════════════════════════════════════
    场景: 两个用户同时购买最后一件商品

    用户 A: 查询库存 (stock=1)
    用户 B: 查询库存 (stock=1)
    用户 A: 扣减库存 (stock=0)
    用户 B: 扣减库存 (stock=-1) ← 问题！

    解决方案: 使用悲观锁
    ══════════════════════════════════════════════════════════════════════════
    """
    async with session.begin():
        # 使用 FOR UPDATE 锁定行
        stmt = select(Product).where(
            Product.id == product_id
        ).with_for_update()  # ← 加锁

        result = await session.execute(stmt)
        product = result.scalar_one_or_none()

        if not product:
            raise ValueError(f"Product {product_id} not found")

        if product.stock < quantity:
            raise ValueError(f"Only {product.stock} items available")

        # 其他事务必须等待锁释放才能继续
        product.stock -= quantity

        order = Order(
            product_id=product_id,
            quantity=quantity,
            total_price=product.price * quantity
        )
        session.add(order)

        return order


# ══════════════════════════════════════════════════════════════════════════
# 依赖注入 (Transaction-aware Dependency Injection)
# ══════════════════════════════════════════════════════════════════════════

@asynccontextmanager
async def get_db():
    """
    获取数据库会话

    ══════════════════════════════════════════════════════════════════════════
    事务边界设计
    ══════════════════════════════════════════════════════════════════════════
    方式 1: 在 get_db() 中管理事务
    ────────────────────────────────────────────────────────────────────────────────────────
    async def get_db():
        async with async_session() as session:
            async with session.begin():
                yield session
                # 自动提交

    问题: Endpoint 无法控制事务 (例如: 需要多步操作)

    方式 2: 在 Service 层管理事务 (推荐)
    ────────────────────────────────────────────────────────────────────────────────────────
    async def get_db():
        async with async_session() as session:
            yield session
            # Service 层使用 async with session.begin()

    ✅ 推荐: Service 层控制事务边界
    ══════════════════════════════════════════════════════════════════════════
    """
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


# ==================== 服务层 ====================

class TransactionService:
    """事务服务 (演示不同的事务模式)"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def transfer_money(
        self,
        from_id: int,
        to_id: int,
        amount: float
    ) -> bool:
        """转账 (使用自动事务管理)"""
        return await transfer_money_auto(self.db, from_id, to_id, amount)

    async def create_order(
        self,
        product_id: int,
        quantity: int
    ) -> Order:
        """创建订单 (复杂事务)"""
        return await create_order(self.db, product_id, quantity)

    async def create_order_safe(
        self,
        product_id: int,
        quantity: int
    ) -> Order:
        """创建订单 (带锁，防止并发问题)"""
        return await create_order_with_lock(self.db, product_id, quantity)


# ==================== FastAPI 应用 ====================

app = FastAPI(
    title="事务管理示例",
    description="演示事务管理、并发控制和回滚",
    version="4.0.0"
)


@app.on_event("startup")
async def startup_event():
    await init_database()


# ══════════════════════════════════════════════════════════════════════════
# Pydantic 模型
# ══════════════════════════════════════════════════════════════════════════

class TransferRequest(BaseModel):
    from_id: int = Field(..., gt=0)
    to_id: int = Field(..., gt=0)
    amount: float = Field(..., gt=0)

    class Config:
        json_schema_extra = {
            "example": {
                "from_id": 1,
                "to_id": 2,
                "amount": 100.0
            }
        }


class OrderCreate(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0, le=100)


# ══════════════════════════════════════════════════════════════════════════
# Endpoints
# ══════════════════════════════════════════════════════════════════════════

@app.post("/transfer")
async def transfer(
    request: TransferRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    转账 (演示事务)

    ══════════════════════════════════════════════════════════════════════════
    ACID 特性演示
    ══════════════════════════════════════════════════════════════════════════
    A - Atomicity (原子性):
        扣钱和加钱要么都成功，要么都失败

    C - Consistency (一致性):
        转账前后总金额不变

    I - Isolation (隔离性):
        并发转账互不影响

    D - Durability (持久性):
        提交后永久保存
    ══════════════════════════════════════════════════════════════════════════
    """
    service = TransactionService(db)
    try:
        await service.transfer_money(
            request.from_id,
            request.to_id,
            request.amount
        )
        return {
            "success": True,
            "message": f"Transferred {request.amount} from account {request.from_id} to {request.to_id}"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.post("/orders")
async def create_order_endpoint(
    order_data: OrderCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    创建订单 (演示复杂事务)

    事务操作:
    1. 查询产品
    2. 检查库存
    3. 扣减库存
    4. 创建订单
    全部成功或全部失败！
    """
    service = TransactionService(db)
    try:
        order = await service.create_order(
            order_data.product_id,
            order_data.quantity
        )
        return {
            "success": True,
            "order_id": order.id,
            "total_price": order.total_price,
            "remaining_stock": order.quantity
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.post("/orders/safe")
async def create_order_safe_endpoint(
    order_data: OrderCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    创建订单 (演示并发控制)

    使用悲观锁防止并发问题:
    - with_for_update() 锁定产品行
    - 其他事务必须等待
    """
    service = TransactionService(db)
    try:
        order = await service.create_order_safe(
            order_data.product_id,
            order_data.quantity
        )
        return {
            "success": True,
            "order_id": order.id,
            "message": "Order created with lock protection"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.get("/accounts")
async def list_accounts(db: AsyncSession = Depends(get_db)):
    """查看所有账户余额"""
    stmt = select(Account)
    result = await db.execute(stmt)
    accounts = result.scalars().all()
    return {
        "accounts": [
            {"id": a.id, "owner": a.owner, "balance": a.balance}
            for a in accounts
        ],
        "total_balance": sum(a.balance for a in accounts)
    }


@app.get("/products")
async def list_products(db: AsyncSession = Depends(get_db)):
    """查看所有产品库存"""
    stmt = select(Product)
    result = await db.execute(stmt)
    products = result.scalars().all()
    return {
        "products": [
            {
                "id": p.id,
                "name": p.name,
                "stock": p.stock,
                "price": p.price
            }
            for p in products
        ]
    }


@app.get("/")
async def root():
    return {
        "name": "事务管理示例",
        "version": "4.0.0",
        "features": [
            "手动事务管理",
            "自动事务管理 (Context Manager)",
            "复杂事务 (多个操作)",
            "嵌套事务 (Savepoints)",
            "并发控制 (锁)"
        ],
        "acid_properties": {
            "A": "Atomicity - 原子性",
            "C": "Consistency - 一致性",
            "I": "Isolation - 隔离性",
            "D": "Durability - 持久性"
        },
        "endpoints": {
            "transfer": "POST /transfer",
            "create_order": "POST /orders",
            "create_order_safe": "POST /orders/safe",
            "list_accounts": "GET /accounts",
            "list_products": "GET /products"
        },
        "docs": "/docs"
    }


# ==================== 运行说明 ====================
"""
═══════════════════════════════════════════════════════════════════════════
事务管理总结
═══════════════════════════════════════════════════════════════════════════

1. ACID 特性
   A - Atomicity (原子性): 全部成功或全部失败
   C - Consistency (一致性): 数据始终一致
   I - Isolation (隔离性): 并发事务互不影响
   D - Durability (持久性): 提交后永久保存

2. 事务管理方式
   - 手动: session.commit() / session.rollback()
   - 自动: async with session.begin() (推荐)

3. 事务边界设计
   - Repository 层: 不管理事务
   - Service 层: 控制事务边界
   - Endpoint 层: 调用 Service

4. 并发控制
   - 悲观锁: with_for_update() (锁定行)
   - 乐观锁: 版本号 (检查冲突)

═══════════════════════════════════════════════════════════════════════════
测试示例
═══════════════════════════════════════════════════════════════════════════

# 1. 查看账户余额
curl "http://localhost:8003/accounts"

# 2. 转账 (成功)
curl -X POST "http://localhost:8003/transfer" \\
      -H "Content-Type: application/json" \\
      -d '{"from_id": 1, "to_id": 2, "amount": 100.0}'

# 3. 转账 (失败 - 余额不足)
curl -X POST "http://localhost:8003/transfer" \\
      -H "Content-Type: application/json" \\
      -d '{"from_id": 1, "to_id": 2, "amount": 10000.0}'

# 4. 查看产品库存
curl "http://localhost:8003/products"

# 5. 创建订单 (成功)
curl -X POST "http://localhost:8003/orders" \\
      -H "Content-Type: application/json" \\
      -d '{"product_id": 1, "quantity": 2}'

# 6. 创建订单 (失败 - 库存不足)
curl -X POST "http://localhost:8003/orders" \\
      -H "Content-Type: application/json" \\
      -d '{"product_id": 1, "quantity": 100}'

# 7. 再次查看账户/产品 (验证数据一致性)
curl "http://localhost:8003/accounts"
curl "http://localhost:8003/products"

═══════════════════════════════════════════════════════════════════════════
下一步学习
═══════════════════════════════════════════════════════════════════════════

掌握了事务管理后，继续学习:
1. 数据库迁移 → examples/05_migrations.py

═══════════════════════════════════════════════════════════════════════════
"""
