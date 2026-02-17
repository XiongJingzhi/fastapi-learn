# 02. 服务拆分设计 - Service Design

## 📍 在架构中的位置

**从"一个巨大的服务"到"多个合理的服务"**

```
┌─────────────────────────────────────────────────────────────┐
│          错误的拆分方式                                      │
└─────────────────────────────────────────────────────────────┘

按技术层拆分：
├── user-controller-service/     # 用户控制器服务
├── user-service-service/        # 用户业务逻辑服务
├── user-repository-service/     # 用户数据访问服务
├── order-controller-service/    # 订单控制器服务
├── order-service-service/       # 订单业务逻辑服务
└── order-repository-service/    # 订单数据访问服务

问题：
- 一个业务的代码分散在多个服务
- 服务间频繁调用
- 高耦合、低内聚 ❌

═══════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────┐
│          正确的拆分方式                                      │
└─────────────────────────────────────────────────────────────┘

按业务能力拆分：
├── user-service/        # 用户服务（完整的用户管理功能）
├── order-service/       # 订单服务（完整的订单管理功能）
├── product-service/     # 产品服务（完整的产品管理功能）
└── payment-service/     # 支付服务（完整的支付处理功能）

好处：
- 一个业务的代码集中在一个服务
- 高内聚、低耦合 ✅
- 服务独立性强
```

**🎯 你的学习目标**：掌握如何合理地拆分微服务，定义清晰的服务边界。

---

## 🎯 服务拆分原则

### 原则 1：单一职责原则（Single Responsibility Principle）

```
每个服务只负责一个业务能力

反例：
    order-service/
    ├── 订单管理
    ├── 支付处理        # 应该独立为 payment-service
    ├── 库存管理        # 应该独立为 inventory-service
    └── 物流跟踪        # 应该独立为 shipping-service

正例：
    order-service/      # 只负责订单管理
    ├── 创建订单
    ├── 查询订单
    ├── 取消订单
    └── 订单状态更新
```

### 原则 2：高内聚、低耦合（High Cohesion, Low Coupling）

```
高内聚：
    一个服务内的功能紧密相关
    → 订单服务包含订单相关的所有功能

低耦合：
    服务间依赖最小化
    → 订单服务通过 API 调用库存服务，而不是直接访问其数据库
```

### 原则 3：独立数据存储（Database per Service）

```
错误做法：
    多个服务共享一个数据库
    → 数据耦合严重
    → 无法独立部署和扩展

正确做法：
    每个服务有独立的数据库
    → 数据隔离
    → 可选择最适合的数据库类型

示例：
    user-service    → PostgreSQL (关系型)
    product-service → MongoDB (文档型)
    cache-service   → Redis (键值型)
    search-service  → Elasticsearch (搜索引擎)
```

### 原则 4：按业务边界拆分（Domain-Driven Design）

```
使用领域驱动设计（DDD）识别业务边界

核心概念：
    - 领域（Domain）：问题空间
    - 子域（Subdomain）：问题的子集
    - 限界上下文（Bounded Context）：特定模型的边界

电商系统示例：
    用户域（User Domain）
        → 用户服务（User Service）

    商品域（Product Domain）
        → 产品服务（Product Service）

    订单域（Order Domain）
        → 订单服务（Order Service）

    支付域（Payment Domain）
        → 支付服务（Payment Service）
```

---

## 🎨 服务拆分策略

### 策略 1：按业务能力拆分

```
示例：电商系统

业务能力 → 服务

用户管理   → user-service
商品管理   → product-service
订单管理   → order-service
库存管理   → inventory-service
支付处理   → payment-service
物流跟踪   → shipping-service
通知服务   → notification-service
推荐系统   → recommendation-service

优点：
    - 符合业务语言
    - 易于理解和沟通
    - 团队自治（一个团队负责一个业务能力）
```

### 策略 2：按数据拆分

```
基于数据的读写模式和一致性要求拆分

读多写少：
    → 产品服务（Product Service）
    → 大量查询，少量更新
    → 使用缓存优化

读写分离：
    → 订单服务（Order Service）
    → 写库：PostgreSQL
    → 读库：PostgreSQL Read Replica

数据量大：
    → 日志服务（Log Service）
    → 使用时序数据库或 Elasticsearch

实时性要求高：
    → 库存服务（Inventory Service）
    → 使用 Redis + MySQL
```

### 策略 3：按扩展性需求拆分

```

根据流量和资源需求拆分

高流量服务：
    → 产品服务（大量浏览）
    → 推荐服务（实时推荐）
    → 多部署实例，独立扩展

计算密集型：
    → 推荐服务（机器学习计算）
    → 图片服务（图片处理）
    → 使用更强大的服务器

IO 密集型：
    → 文件服务（文件上传下载）
    → 使用 SSD 存储
```

---

## 📐 服务边界识别

### 方法 1：事件风暴（Event Storming）

```
步骤：
    1. 召集领域专家和开发人员
    2. 在墙上贴出领域事件
    3. 识别事件之间的关系
    4. 划分限界上下文

示例：订单系统

事件：
    - OrderCreated
    - OrderPaid
    - OrderShipped
    - OrderCompleted
    - OrderCancelled

聚合：
    - 所有 Order 事件 → 订单服务

边界：
    - OrderCreated → 触发库存扣减（库存服务）
    - OrderPaid → 触发支付确认（支付服务）
    - OrderShipped → 触发物流通知（物流服务）
```

### 方法 2：业务流程分析

```
分析业务流程，识别独立的业务单元

用户下单流程：
    1. 浏览商品（产品服务）
    2. 加入购物车（购物车服务）
    3. 创建订单（订单服务）
    4. 支付（支付服务）
    5. 扣减库存（库存服务）
    6. 发货（物流服务）
    7. 通知（通知服务）

每个步骤对应一个或多个服务
```

### 方法 3：数据所有权分析

```
分析数据的创建和修改来源

数据：用户信息
    → 由用户服务创建和维护
    → 其他服务只读（通过 API）
    → 用户服务拥有数据所有权

数据：订单信息
    → 由订单服务创建和维护
    → 库存服务、支付服务等只读
    → 订单服务拥有数据所有权
```

---

## ⚖️ 服务粒度控制

### 拆分太细

```
纳米服务（过度拆分）：
    user-authentication-service/    # 用户认证
    user-authorization-service/     # 用户授权
    user-profile-service/           # 用户资料
    user-preference-service/        # 用户偏好
    user-avatar-service/            # 用户头像

问题：
    - 管理复杂度高
    - 网络开销大
    - 调试困难
    - 资源浪费（每个服务都需要监控、日志等）
```

### 拆分太粗

```
单体服务（拆分不足）：
    business-service/    # 包含所有业务功能
    ├── 用户
    ├── 订单
    ├── 产品
    ├── 支付
    ├── 库存
    └── 物流

问题：
    - 违背微服务初衷
    - 无法独立部署和扩展
    - 团队协作困难
```

### 合理粒度

```
原则：
    - 一个服务可以由一个小团队（2-5 人）维护
    - 一个服务可以在一周内重写
    - 服务间调用频率不过高
    - 服务有明确的业务价值

示例：
    user-service/        # 用户服务（2 人团队）
    order-service/       # 订单服务（3 人团队）
    product-service/     # 产品服务（2 人团队）
    payment-service/     # 支付服务（2 人团队）
```

---

## 🔄 拆分步骤

### 步骤 1：分析现有系统

```
如果从单体应用拆分：

1. 代码分析
   - 识别模块依赖
   - 识别数据依赖
   - 识别业务边界

2. 数据库分析
   - 识别表之间的关系
   - 识别跨表查询
   - 规划数据库拆分方案

3. 接口分析
   - 识别前端调用的接口
   - 识别接口之间的依赖
   - 规划接口迁移方案
```

### 步骤 2：制定拆分计划

```
拆分顺序：
    1. 优先拆分变化最频繁的模块
    2. 优先拆分资源需求差异大的模块
    3. 最后拆分核心业务模块

示例：
    第一阶段：通知服务（独立性强，拆分风险低）
    第二阶段：推荐服务（计算密集，需要独立扩展）
    第三阶段：订单服务（核心业务，需要谨慎拆分）
```

### 步骤 3：绞杀者模式（Strangler Pattern）

```
逐步替换单体应用：

1. 在单体应用前面设置 API 网关
2. 将特定功能拆分为微服务
3. API 网关将请求路由到微服务
4. 逐步将更多功能拆分为微服务
5. 最终单体应用被"绞杀"，只保留微服务

示例：
    原有：
        客户端 → 单体应用

    第一阶段：
        客户端 → API 网关 → 单体应用

    第二阶段：
        客户端 → API 网关 → 微服务（通知）
                          → 单体应用（其他）

    第三阶段：
        客户端 → API 网关 → 微服务（通知）
                          → 微服务（推荐）
                          → 单体应用（其他）

    最终：
        客户端 → API 网关 → 微服务（通知）
                          → 微服务（推荐）
                          → 微服务（订单）
                          → 微服务（用户）
```

### 步骤 4：数据迁移

```

数据迁移策略：

1. 双写（Double Write）
    - 新数据同时写入单体数据库和微服务数据库
    - 旧数据逐步迁移
    - 切换读流量到微服务

2. 增量同步
    - 使用 CDC（Change Data Capture）同步数据
    - 例如：Debezium + Kafka

3. 读切换
    - 先切换读流量
    - 验证数据一致性
    - 再切换写流量

4. 逐步停止单体数据库的写入
    - 只保留微服务数据库
```

---

## 🎯 拆分示例：电商系统

### 原始单体应用

```
e-commerce-monolith/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models/
│   │   ├── user.py
│   │   ├── product.py
│   │   ├── order.py
│   │   └── payment.py
│   ├── routes/
│   │   ├── user_routes.py
│   │   ├── product_routes.py
│   │   ├── order_routes.py
│   │   └── payment_routes.py
│   └── services/
│       ├── user_service.py
│       ├── product_service.py
│       ├── order_service.py
│       └── payment_service.py
└── database.py
```

### 拆分为微服务

```
services/
├── user-service/
│   ├── main.py
│   ├── models/
│   │   └── user.py
│   ├── routes/
│   │   └── user_routes.py
│   ├── services/
│   │   └── user_service.py
│   └── database.py
│
├── product-service/
│   ├── main.py
│   ├── models/
│   │   └── product.py
│   ├── routes/
│   │   └── product_routes.py
│   ├── services/
│   │   └── product_service.py
│   └── database.py
│
├── order-service/
│   ├── main.py
│   ├── models/
│   │   └── order.py
│   ├── routes/
│   │   └── order_routes.py
│   ├── services/
│   │   └── order_service.py
│   ├── clients/
│   │   ├── user_client.py     # 调用用户服务
│   │   ├── product_client.py  # 调用产品服务
│   │   └── payment_client.py  # 调用支付服务
│   └── database.py
│
└── payment-service/
    ├── main.py
    ├── models/
    │   └── payment.py
    ├── routes/
    │   └── payment_routes.py
    ├── services/
    │   └── payment_service.py
    └── database.py
```

---

## 🔧 服务拆分工具

### 1. 领域驱动设计（DDD）

```
核心概念：
    - 领域（Domain）
    - 子域（Subdomain）
    - 限界上下文（Bounded Context）
    - 聚合（Aggregate）
    - 实体（Entity）
    - 值对象（Value Object）

工具：
    - 事件风暴（Event Storming）
    - 建模工作坊
```

### 2. 代码分析工具

```
工具：
    - 依赖分析：pydeps
    - 代码复杂度：radon
    - 代码覆盖率：pytest-cov

示例：
    pydeps app --max-bacon=3 --cluster
    # 生成依赖图，识别模块依赖关系
```

### 3. 数据库分析工具

```

工具：
    - 表依赖分析：查询外键关系
    - 查询分析：慢查询日志
    - 数据访问模式：ORM 日志
```

---

## ⚠️ 常见陷阱

### 陷阱 1：共享数据库

```
错误：
    user-service 和 order-service 共享数据库
    → 违背了数据库私有原则

正确：
    user-service 有自己的数据库
    order-service 有自己的数据库
    → 通过 API 访问数据
```

### 陷阱 2：分布式单体

```
错误：
    多个服务，但高度耦合
    → 修改一个功能需要同时修改多个服务

正确：
    服务独立部署
    → 通过 API 通信
    → 故障隔离
```

### 陷阱 3：过度拆分

```
错误：
    拆分为几十个甚至上百个微服务
    → 管理复杂度超过收益

正确：
    根据业务合理拆分
    → 一个服务由 2-5 人团队维护
```

---

## 🎯 小实验：服务拆分

### 实验：拆分用户和订单服务

```python
# 原始单体应用
# monolith/main.py
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

app = FastAPI()

@app.post("/orders")
def create_order(
    user_id: int,
    product_id: int,
    db: Session = Depends(get_db)
):
    # 查询用户（在同一数据库）
    user = db.query(User).filter(User.id == user_id).first()
    # 创建订单
    order = Order(user_id=user_id, product_id=product_id)
    db.add(order)
    db.commit()
    return order

# 拆分为微服务
# user_service/main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/users/{user_id}")
def get_user(user_id: int):
    return {"id": user_id, "name": "John"}

# order_service/main.py
from fastapi import FastAPI
import httpx

app = FastAPI()

@app.post("/orders")
async def create_order(user_id: int, product_id: int):
    # 调用用户服务获取用户信息
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://user-service:8001/users/{user_id}")
        user = response.json()

    # 创建订单
    order = {"user_id": user_id, "product_id": product_id}
    return order
```

---

## 📚 检查理解

回答这些问题来测试你的理解：

1. **服务拆分的核心原则是什么？**
   - 提示：单一职责、高内聚低耦合、独立数据存储

2. **如何识别服务边界？**
   - 提示：业务能力、数据所有权、事件风暴

3. **什么是绞杀者模式？**
   - 提示：逐步替换单体应用

4. **服务粒度如何控制？**
   - 提示：不要过度拆分，也不要拆分不足

5. **数据迁移的策略有哪些？**
   - 提示：双写、增量同步、CDC

---

## 🚀 下一步

现在你已经了解了服务拆分设计，接下来：

1. **学习服务间通信**：`notes/03_service_communication_sync.md`
2. **查看实际代码**：`examples/`

**记住：服务拆分是渐进式的，不要一开始就追求完美的拆分！**
