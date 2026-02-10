# 04. 事务与连接池 - Transactions & Connection Pool

## 📍 在架构中的位置

**理解数据一致性和性能优化的关键**

```
┌─────────────────────────────────────────────────────────────┐
│          没有事务管理的问题                                   │
└─────────────────────────────────────────────────────────────┘

async def transfer_money(user_id_from: int, user_id_to: int, amount: int):
    # 1. 扣钱
    await db.execute("UPDATE users SET balance = balance - $1 WHERE id = $2", amount, user_id_from)

    # ❌ 如果这里崩溃？钱扣了但没到账！

    # 2. 加钱
    await db.execute("UPDATE users SET balance = balance + $1 WHERE id = $2", amount, user_id_to)

问题：
- 数据不一致（钱扣了但没到账）
- 无法回滚
- 并发问题

═══════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────┐
│          使用事务管理                                          │
└─────────────────────────────────────────────────────────────┘

async def transfer_money(user_id_from: int, user_id_to: int, amount: int):
    async with db.begin():  # ← 开始事务
        try:
            # 1. 扣钱
            await db.execute("UPDATE users SET balance = balance - $1 WHERE id = $2", amount, user_id_from)

            # 2. 加钱
            await db.execute("UPDATE users SET balance = balance + $1 WHERE id = $2", amount, user_id_to)

            # 3. 提交事务
            await db.commit()  # ← 两个操作要么都成功，要么都失败

        except Exception as e:
            # 4. 回滚事务
            await db.rollback()  # ← 撤销所有操作
            raise

好处：
- 数据一致性（ACID）
- 原子性（全部成功或全部失败）
- 并发安全
```

**🎯 你的学习目标**：掌握事务管理和连接池配置，确保数据一致性和高性能。

---

## 🎯 什么是事务？

### 生活类比：银行转账

**场景**：Alice 给 Bob 转 100 元

**没有事务的情况**：

```
步骤 1: 银行从 Alice 账户扣 100 元
         Alice 账户: 1000 → 900 ✅

步骤 2: 系统崩溃！💥

步骤 3: 银行给 Bob 账户加 100 元
         ← 没执行！

结果：
- Alice 损失了 100 元
- Bob 没收到 100 元
- 100 元凭空消失！❌
```

**有事务的情况**：

```
开始事务:
    步骤 1: 银行从 Alice 账户扣 100 元
             Alice 账户: 1000 → 900 ✅

    步骤 2: 系统崩溃！💥

    回滚事务:
        Alice 账户: 900 → 1000 ✅（恢复）
        Bob 账户不变

结果：
- Alice 没有损失
- Bob 没有收到
- 但数据一致！✅
```

---

### 事务的 ACID 特性

**ACID** 是事务的四个核心特性：

```
┌─────────────────────────────────────────────────────────────┐
│                     A - Atomicity (原子性)                   │
│                                                             │
│  事务中的操作要么全部成功，要么全部失败                     │
│                                                             │
│  例子：转账                                                │
│  - 扣钱 + 加钱 = 一个原子                                 │
│  - 要么都成功，要么都失败                                  │
│  - 不会出现"扣了钱但没加钱"的情况                          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                     C - Consistency (一致性)                   │
│                                                             │
│  事务前后，数据库始终保持一致状态                             │
│                                                             │
│  例子：转账                                                │
│  - 转账前：Alice 1000 + Bob 500 = 1500                  │
│  - 转账后：Alice 900 + Bob 600 = 1500                    │
│  - 总金额不变（一致）                                     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                     I - Isolation (隔离性)                   │
│                                                             │
│  并发事务之间互相隔离，不会互相干扰                          │
│                                                             │
│  例子：两个同时进行的转账                                   │
│  - 事务 A：Alice → Bob (100 元)                           │
│  - 事务 B：Bob → Charlie (50 元)                          │
│  - 隔离性保证：两个事务看到的是一致的数据                  │
│  - 不会出现"余额检查-更新"的竞态条件                        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                     D - Durability (持久性)                   │
│                                                             │
│  事务一旦提交，结果永久保存，即使系统崩溃也不会丢失           │
│                                                             │
│  例子：转账成功                                            │
│  - 事务提交                                               │
│  - 数据写入磁盘                                          │
│  - 即使系统立即崩溃，数据也不会丢失                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 FastAPI 中的事务管理

### 基本事务模式

**模式 1：手动管理事务**

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

async def transfer_money(
    user_id_from: int,
    user_id_to: int,
    amount: int,
    db: AsyncSession = Depends(get_db)
):
    """转账"""

    # 1. 开始事务（隐式）
    try:
        # 2. 执行操作
        await db.execute(
            "UPDATE users SET balance = balance - $1 WHERE id = $2",
            amount, user_id_from
        )

        await db.execute(
            "UPDATE users SET balance = balance + $1 WHERE id = $2",
            amount, user_id_to
        )

        # 3. 提交事务
        await db.commit()

    except Exception as e:
        # 4. 回滚事务
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Transfer failed: {str(e)}"
        )
```

---

**模式 2：使用 `async with`（推荐）**

```python
async def transfer_money(
    user_id_from: int,
    user_id_to: int,
    amount: int,
    db: AsyncSession = Depends(get_db)
):
    """转账（使用 with 自动管理事务）"""

    async with db.begin():  # ← 自动提交或回滚
        try:
            # 扣钱
            await db.execute(
                "UPDATE users SET balance = balance - $1 WHERE id = $2",
                amount, user_id_from
            )

            # 加钱
            await db.execute(
                "UPDATE users SET balance = balance + $1 WHERE id = $2",
                amount, user_id_to
            )

        except Exception as e:
            # 自动回滚
            raise HTTPException(
                status_code=500,
                detail=f"Transfer failed: {str(e)}"
            )

    # with 块结束时自动提交（如果没有异常）
```

---

### 依赖注入中的事务

**在 `get_db()` 中使用 `yield`**：

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

engine = create_async_engine("postgresql+asyncpg://...")
async_session = sessionmaker(engine, class_=AsyncSession)

def get_db() -> AsyncSession:
    """数据库会话依赖（自动管理事务）"""

    async with async_session() as session:
        try:
            yield session  # ← 提供给 endpoint 使用

        finally:
            # 自动清理
            await session.close()

# 使用
@app.post("/transfer")
async def transfer(
    user_id_from: int,
    user_id_to: int,
    amount: int,
    db: AsyncSession = Depends(get_db)  # ← 事务由 get_db() 管理
):
    async with db.begin():  # ← 子事务
        # 执行转账操作
        await db.execute(...)
        await db.execute(...)
```

---

## 🎨 实际场景：订单创建

### 完整的事务处理

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

class OrderService:
    """订单服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_order(
        self,
        user_id: int,
        items: List[OrderItem]
    ) -> Order:
        """
        创建订单（使用事务）

        业务流程：
        1. 检查用户是否存在
        2. 检查商品库存
        3. 扣减库存
        4. 创建订单
        5. 计算总价
        全部成功或全部失败！
        """

        async with self.db.begin():  # ← 开始事务
            try:
                # 1. 检查用户
                user = await self._get_user(user_id)
                if not user:
                    raise UserNotFoundException(f"User {user_id} not found")

                # 2. 检查库存并扣减
                total_price = 0
                for item in items:
                    product = await self._get_product(item.product_id)
                    if not product:
                        raise ProductNotFoundException(f"Product {item.product_id} not found")

                    if product.stock < item.quantity:
                        raise InsufficientStockException(
                            f"Product {product.name} only has {product.stock} in stock"
                        )

                    # 扣减库存
                    product.stock -= item.quantity
                    await self.db.execute(
                        "UPDATE products SET stock = $1 WHERE id = $2",
                        product.stock, product.id
                    )

                    total_price += product.price * item.quantity

                # 3. 创建订单
                order = Order(
                    user_id=user_id,
                    total_price=total_price
                )
                self.db.add(order)

                # 4. 创建订单项
                for item in items:
                    order_item = OrderItem(
                        order_id=order.id,
                        product_id=item.product_id,
                        quantity=item.quantity,
                        price=item.price
                    )
                    self.db.add(order_item)

                # 5. 提交事务（所有操作持久化）
                # await self.db.commit()  # with 块结束时自动提交

                return order

            except Exception as e:
                # 回滚事务（撤销所有操作）
                # await self.db.rollback()  # with 块结束时自动回滚
                raise

    async def _get_user(self, user_id: int) -> Optional[User]:
        """获取用户"""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_product(self, product_id: int) -> Optional[Product]:
        """获取商品"""
        stmt = select(Product).where(Product.id == product_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
```

---

## 🔄 并发控制

### 隔离级别

**隔离级别**：控制并发事务之间的隔离程度。

```python
from sqlalchemy import text

async def demonstrate_isolation_levels(db: AsyncSession):
    """演示不同的隔离级别"""

    # Read Uncommitted（读未提交）- 最低隔离
    async with db.begin():
        await db.execute(text("SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED"))
        # 可以读取未提交的数据（脏读）

    # Read Committed（读已提交）- 默认级别
    async with db.begin():
        await db.execute(text("SET TRANSACTION ISOLATION LEVEL READ COMMITTED"))
        # 只能读取已提交的数据（避免脏读）

    # Repeatable Read（可重复读）- 推荐
    async with db.begin():
        await db.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ"))
        # 同一事务中多次读取结果一致

    # Serializable（可串行化）- 最高隔离
    async with db.begin():
        await db.execute(text("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE"))
        # 完全隔离（最安全但最慢）
```

**对比表**：

| 隔离级别 | 脏读 | 不可重复读 | 幻读 | 性能 |
|---------|-----|-----------|-----|------|
| Read Uncommitted | ✅ 可能 | ✅ 可能 | ✅ 可能 | 最高 |
| Read Committed | ❌ 避免 | ✅ 可能 | ✅ 可能 | 高 |
| Repeatable Read | ❌ 避免 | ❌ 避免 | ✅ 可能 | 中 |
| Serializable | ❌ 避免 | ❌ 避免 | ❌ 避免 | 最低 |

---

### 锁

**乐观锁（Optimistic Locking）**：

```python
from sqlalchemy import select, update

class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    stock: Mapped[int] = mapped_column(Integer)
    version: Mapped[int] = mapped_column(Integer, default=0)  # 版本号

async def update_product_with_optimistic_lock(
    db: AsyncSession,
    product_id: int,
    new_stock: int
):
    """使用乐观锁更新商品"""

    # 1. 读取商品（获取版本号）
    product = await db.get(Product, product_id)
    if not product:
        raise ProductNotFoundException()

    old_version = product.version

    # 2. 更新商品（检查版本号）
    result = await db.execute(
        update(Product)
        .where(Product.id == product_id)
        .where(Product.version == old_version)  # 版本号必须一致
        .values(stock=new_stock, version=old_version + 1)
        .returning(Product)
    )

    updated_product = result.scalar_one_or_none()

    if not updated_product:
        raise ConcurrentModificationException(
            "Product was modified by another transaction"
        )

    # 3. 提交
    await db.commit()

    return updated_product
```

---

## 🌐 连接池

### 什么是连接池？

**类比**：餐厅的服务员

```
┌─────────────────────────────────────────────────────────────┐
│                    数据库连接池                              │
└─────────────────────────────────────────────────────────────┘

没有连接池：
    每次请求都创建新连接
    └─→ 连接数据库（慢：建立 TCP 连接）
    └─→ 执行查询
    └─→ 关闭连接（慢）
    问题：频繁创建/销毁连接，性能差

有连接池：
    启动时创建 10 个连接
    └─→ 请求 1：从池中获取连接 1（快）
    └─→ 执行查询
    └─→ 归还连接 1 到池
    └─→ 请求 2：从池中获取连接 1（快）
    好处：复用连接，性能好
```

---

### 配置连接池

```python
from sqlalchemy.ext.asyncio import create_async_engine

# 创建引擎（配置连接池）
engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost/db",

    # 连接池配置
    pool_size=10,          # 池中保持的连接数
    max_overflow=20,        # 最大溢出连接数（总共 30 个）
    pool_timeout=30,        # 获取连接的超时时间（秒）
    pool_recycle=3600,      # 连接回收时间（秒）
    pool_pre_ping=True,     # 连接前检查可用性

    # 性能配置
    echo=False,             # 不打印 SQL（生产环境）
    echo_pool=False,        # 不打印连接池日志

    # SQLite 配置
    # connect_args={"check_same_thread": False}  # SQLite 线程安全
)
```

**参数说明**：

| 参数 | 说明 | 推荐值 |
|------|------|--------|
| `pool_size` | 池中保持的连接数 | 5-20 |
| `max_overflow` | 最大溢出连接数 | 10-40 |
| `pool_timeout` | 获取连接超时 | 30 秒 |
| `pool_recycle` | 连接回收时间 | 3600 秒 |
| `pool_pre_ping` | 连接前检查 | True（生产） |

---

### 连接池监控

```python
async def check_pool_status():
    """检查连接池状态"""

    pool = engine.pool

    print(f"Pool size: {pool.size()}")
    print(f"Checked out connections: {pool.checkedout()}")
    print(f"Overflow: {pool.overflow()}")
    print(f"Invalid connections: {pool.invalid()}")

# 在生产环境中，可以定期检查
# 并发送到监控系统（如 Prometheus）
```

---

## 🎨 实际场景：高并发订单系统

### 完整的事务 + 连接池配置

```python
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# ═══════════════════════════════════════════════════════════
# 1. 配置连接池（生产环境）
# ═══════════════════════════════════════════════════════════

engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost/db",
    pool_size=20,          # 高并发：20 个连接
    max_overflow=40,        # 最多 60 个连接
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True,
)

async_session = sessionmaker(engine, class_=AsyncSession)

# ═══════════════════════════════════════════════════════════
# 2. 依赖注入
# ═══════════════════════════════════════════════════════════

def get_db() -> AsyncSession:
    """获取数据库会话"""
    async with async_session() as session:
        yield session

# ═══════════════════════════════════════════════════════════
# 3. 服务层（事务管理）
# ═══════════════════════════════════════════════════════════

class OrderService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_order(self, user_id: int, items: List[OrderItem]) -> Order:
        """创建订单（高并发环境）"""

        async with self.db.begin():
            # 设置隔离级别（避免脏读）
            await self.db.execute(
                text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
            )

            try:
                # 使用 FOR UPDATE 锁定行（悲观锁）
                for item in items:
                    # 锁定商品行（防止并发修改）
                    product = await self.db.execute(
                        select(Product)
                        .where(Product.id == item.product_id)
                        .with_for_update()  # ← 加锁
                    )
                    product = result.scalar_one()

                    if not product:
                        raise ProductNotFoundException()

                    if product.stock < item.quantity:
                        raise InsufficientStockException()

                    # 扣减库存
                    product.stock -= item.quantity

                # 创建订单
                order = Order(user_id=user_id, total_price=total)
                self.db.add(order)

                return order

            except Exception as e:
                # 自动回滚
                raise

# ═══════════════════════════════════════════════════════════
# 4. Endpoint
# ═══════════════════════════════════════════════════════════

@app.post("/orders")
async def create_order(
    user_id: int,
    items: List[OrderItem],
    db: AsyncSession = Depends(get_db)
):
    service = OrderService(db)
    return await service.create_order(user_id, items)
```

---

## 🎯 小实验：事务处理

### 实验 1：简单事务

```python
async def simple_transaction(db: AsyncSession):
    """简单的事务示例"""
    async with db.begin():
        # 插入用户
        user = User(username="alice", email="alice@example.com")
        db.add(user)

        # 查询用户
        stmt = select(User).where(User.username == "alice")
        result = await db.execute(stmt)
        found_user = result.scalar_one()

        print(f"Found user: {found_user.username}")

    # 事务自动提交
```

---

### 实验 2：回滚事务

```python
async def rollback_transaction(db: AsyncSession):
    """演示事务回滚"""
    try:
        async with db.begin():
            # 插入用户
            user = User(username="bob", email="bob@example.com")
            db.add(user)

            # 故意抛出异常
            raise Exception("Something went wrong!")

    except Exception:
        print("Transaction rolled back")

    # 验证：用户应该不存在
    stmt = select(User).where(User.username == "bob")
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    print(f"User exists: {user is not None}")  # False
```

---

## 📚 检查理解

回答这些问题来测试你的理解：

1. **事务的 ACID 特性是什么？**
   - 提示：Atomicity, Consistency, Isolation, Durability

2. **为什么需要事务管理？**
   - 提示：数据一致性

3. **如何使用 `async with db.begin()`？**
   - 提示：自动提交或回滚

4. **连接池有什么好处？**
   - 提示：复用连接，提高性能

5. **什么是隔离级别？**
   - 提示：控制并发事务的隔离程度

---

## 🚀 下一步

现在你已经掌握了事务管理和连接池，接下来：

1. **学习数据库迁移**：`notes/05_migrations.md`
2. **查看实际代码**：`examples/04_transactions.py`

**记住**：事务管理保证数据一致性，连接池优化性能，两者缺一不可！

---

**费曼技巧总结**：
- ✅ 银行转账类比
- ✅ ACID 特性详解
- ✅ 完整的订单创建示例
- ✅ 隔离级别和锁
- ✅ 连接池配置
- ✅ 高并发场景示例
