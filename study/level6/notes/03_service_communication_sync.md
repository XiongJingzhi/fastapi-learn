# 03. 同步通信 - Synchronous Communication

## 📍 在架构中的位置

**从"函数调用"到"网络调用"**

```
┌─────────────────────────────────────────────────────────────┐
│          单体应用（函数调用）                                 │
└─────────────────────────────────────────────────────────────┘

订单服务调用用户服务：
    # 同一个进程内
    user = get_user(user_id)  # 函数调用
    order = create_order(user)

特点：
    - 快速（内存访问）
    - 可靠（无网络问题）
    - 简单（无需处理网络故障）

═══════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────┐
│          微服务（HTTP 调用）                                  │
└─────────────────────────────────────────────────────────────┘

订单服务调用用户服务：
    # 不同进程，网络通信
    response = httpx.get("http://user-service:8001/users/{user_id}")
    user = response.json()
    order = create_order(user)

特点：
    - 较慢（网络延迟）
    - 不可靠（网络可能失败）
    - 复杂（需要处理超时、重试、熔断）
```

**🎯 你的学习目标**：掌握微服务间同步通信的方式、协议和最佳实践。

---

## 🎯 同步通信概述

### 什么是同步通信？

```
定义：
    服务 A 调用服务 B
    → 服务 A 等待服务 B 的响应
    → 服务 A 收到响应后继续处理

特点：
    - 简单直观
    - 实时响应
    - 强耦合（服务 B 挂了，服务 A 也失败）
```

### 生活类比：电话通话

```
同步通信 = 电话通话

你：
    "你好，请问图书馆今天开吗？"

图书馆：
    "开的，9 点到 18 点。"

你：
    "好的，谢谢！"

特点：
    - 实时交互
    - 必须双方同时在线
    - 一方挂断，通信中断
```

---

## 🔌 通信协议

### HTTP/REST

```
特点：
    - 通用、简单
    - 无状态
    - 基于 JSON（通常）
    - 工具生态丰富

示例：
    # 订单服务调用用户服务
    import httpx

    async def get_user(user_id: int):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://user-service:8001/users/{user_id}",
                timeout=5.0
            )
            return response.json()

优点：
    ✅ 简单易用
    ✅ 通用标准
    ✅ 工具丰富

缺点：
    ❌ 性能较低（文本协议）
    ❌ 数据包较大（JSON）
    ❌ 无类型安全
```

### gRPC

```
特点：
    - 高性能（二进制协议）
    - 基于 Protocol Buffers
    - 强类型（代码生成）
    - 支持双向流

示例：

    # user.proto
    syntax = "proto3";

    service UserService {
        rpc GetUser(GetUserRequest) returns (User);
    }

    message GetUserRequest {
        int32 user_id = 1;
    }

    message User {
        int32 id = 1;
        string name = 2;
        string email = 3;
    }

    # 生成的 Python 代码
    import grpc

    async def get_user(user_id: int):
        async with grpc.aio.insecure_channel('user-service:50051') as channel:
            stub = user_pb2_grpc.UserServiceStub(channel)
            request = user_pb2.GetUserRequest(user_id=user_id)
            response = await stub.GetUser(request)
            return response

优点：
    ✅ 高性能
    ✅ 强类型
    ✅ 支持流式传输

缺点：
    ❌ 学习曲线陡峭
    ❌ 工具较少
    ❌ 调试困难（二进制协议）
```

### GraphQL

```
特点：
    - 按需查询
    - 单个端点
    - 强类型 Schema

示例：
    # 订单服务 GraphQL 查询
    query {
        order(id: 123) {
            id
            total
            user {
                id
                name
            }
            products {
                id
                name
                price
            }
        }
    }

优点：
    ✅ 按需获取数据（避免 over-fetching）
    ✅ 单个请求获取多个资源
    ✅ 强类型

缺点：
    ❌ 复杂度高
    ❌ 缓存困难
    ❌ N+1 查询问题
```

---

## 📡 通信模式

### 模式 1：一对一同步

```
服务 A → 服务 B

示例：
    订单服务 → 用户服务
    → 获取用户信息

    @app.post("/orders")
    async def create_order(order_data: OrderCreate):
        # 调用用户服务
        user = await user_client.get_user(order_data.user_id)
        # 创建订单
        order = create_order(user, order_data)
        return order

优点：
    - 简单直接
    - 实时响应

缺点：
    - 强耦合
    - 性能受最慢的服务影响
```

### 模式 2：聚合（Aggregator）

```
API 网关 → 服务 A
         → 服务 B
         → 服务 C
         → 聚合响应

示例：
    @app.get("/orders/{order_id}")
    async def get_order_detail(order_id: int):
        # 并行调用多个服务
        order, user, products = await asyncio.gather(
            order_client.get_order(order_id),
            user_client.get_user(user_id),
            product_client.get_products(product_ids)
        )

        # 聚合响应
        return {
            "order": order,
            "user": user,
            "products": products
        }

优点：
    - 客户端一次请求获取所有数据
    - 减少客户端复杂度

缺点：
    - 响应时间取决于最慢的服务
```

### 模式 3：链式调用（Chain of Responsibility）

```
客户端 → 服务 A → 服务 B → 服务 C

示例：
    下单流程：
    订单服务 → 库存服务（扣减库存）
             → 支付服务（处理支付）
             → 物流服务（创建物流单）

缺点：
    - 链路长，性能差
    - 任何一个服务失败，整个流程失败
    - 不推荐使用
```

---

## 🔐 服务间认证

### 方式 1：共享密钥（API Key）

```python
# 服务间使用共享密钥
API_KEY = "shared-secret-key"

# 调用方
headers = {"X-API-Key": API_KEY}
response = await client.get("http://user-service/users/1", headers=headers)

# 被调用方
@app.get("/users/{user_id}")
async def get_user(user_id: int, x_api_key: str = Header()):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return get_user_from_db(user_id)
```

### 方式 2：JWT Token

```python
# 使用 JWT 进行服务间认证
import jwt

# 生成 JWT
def generate_service_token():
    payload = {
        "service": "order-service",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

# 验证 JWT
def verify_service_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload["service"]
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# 调用方
headers = {"Authorization": f"Bearer {generate_service_token()}"}
response = await client.get("http://user-service/users/1", headers=headers)
```

### 方式 3：mTLS（双向认证）

```yaml
# Kubernetes 使用 mTLS
# Linkerd 或 Istio 服务网格自动处理
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: user-service
spec:
  host: user-service
  trafficPolicy:
    tls:
      mode: ISTIO_MUTUAL
```

---

## ⚡ 性能优化

### 优化 1：连接池

```python
import httpx
# 使用连接池复用连接
client = httpx.AsyncClient(
    base_url="http://user-service:8001",
    limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
    timeout=5.0
)

@app.post("/orders")
async def create_order(order_data: OrderCreate):
    # 复用连接
    user = await client.get(f"/users/{order_data.user_id}")
    return user
```

### 优化 2：并行调用

```python
import asyncio

@app.get("/orders/{order_id}")
async def get_order_detail(order_id: int):
    # 并行调用多个服务
    order, user, products = await asyncio.gather(
        order_client.get_order(order_id),
        user_client.get_user(user_id),
        product_client.get_products(product_ids)
    )
    return {"order": order, "user": user, "products": products}
```

### 优化 3：数据压缩

```python
# 启用 gzip 压缩
client = httpx.AsyncClient(
    base_url="http://user-service:8001",
    headers={"Accept-Encoding": "gzip"}
)
```

### 优化 4：缓存

```python
from functools import lru_cache
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

@app.get("/users/{user_id}")
@cache(expire=60)  # 缓存 60 秒
async def get_user(user_id: int):
    return get_user_from_db(user_id)
```

---

## 🛡️ 容错处理

### 容错 1：超时控制

```python
from httpx import TimeoutException

@app.post("/orders")
async def create_order(order_data: OrderCreate):
    try:
        # 设置超时
        user = await user_client.get_user(
            order_data.user_id,
            timeout=Timeout(5.0, connect=2.0)  # 总超时 5 秒，连接超时 2 秒
        )
    except TimeoutException:
        # 超时处理
        raise HTTPException(status_code=504, detail="User service timeout")
```

### 容错 2：重试机制

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),  # 最多重试 3 次
    wait=wait_exponential(multiplier=1, min=1, max=10)  # 指数退避
)
async def call_user_service(user_id: int):
    response = await user_client.get_user(user_id)
    return response

@app.post("/orders")
async def create_order(order_data: OrderCreate):
    try:
        user = await call_user_service(order_data.user_id)
    except RetryError:
        raise HTTPException(status_code=503, detail="User service unavailable")
```

### 容错 3：熔断器

```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
async def call_user_service(user_id: int):
    response = await user_client.get_user(user_id)
    return response

@app.post("/orders")
async def create_order(order_data: OrderCreate):
    try:
        user = await call_user_service(order_data.user_id)
    except CircuitBreakerError:
        # 熔断器打开，返回降级数据
        user = {"id": order_data.user_id, "name": "Unknown"}
    return create_order_with_user(user, order_data)
```

---

## 📊 监控与追踪

### 分布式追踪

```python
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.propagate import inject

# 初始化追踪
FastAPIInstrumentor.instrument_app(app)

@app.post("/orders")
async def create_order(order_data: OrderCreate):
    # 获取当前 trace
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("call_user_service"):
        # 调用用户服务（自动传播 trace context）
        headers = {}
        inject(headers)  # 注入 trace context 到 headers
        user = await user_client.get_user(
            order_data.user_id,
            headers=headers
        )
    return user
```

### 监控指标

```python
from prometheus_client import Counter, Histogram

# 定义指标
user_service_calls = Counter(
    'user_service_calls_total',
    'Total calls to user service',
    ['service', 'status']
)

user_service_latency = Histogram(
    'user_service_latency_seconds',
    'Latency of user service calls'
)

@app.post("/orders")
async def create_order(order_data: OrderCreate):
    start = time.time()
    try:
        user = await user_client.get_user(order_data.user_id)
        user_service_calls.labels(service='order', status='success').inc()
        return user
    except Exception as e:
        user_service_calls.labels(service='order', status='error').inc()
        raise
    finally:
        user_service_latency.observe(time.time() - start)
```

---

## ⚠️ 常见陷阱

### 陷阱 1：级联故障

```
问题：
    服务 A 调用服务 B
    服务 B 调用服务 C
    服务 C 挂了
    → 服务 B 等待超时
    → 服务 A 也等待超时
    → 线程池耗尽
    → 整个系统崩溃

解决：
    - 使用熔断器
    - 设置超时
    - 降级处理
```

### 陷阱 2：N+1 查询

```
问题：
    获取订单列表（10 个订单）
    → 循环调用用户服务 10 次（获取每个订单的用户）

解决：
    # 批量查询
    user_ids = [order.user_id for order in orders]
    users = await user_client.get_users(user_ids)  # 一次调用
```

### 陷阱 3：过度同步调用

```
问题：
    订单创建后
    → 同步调用通知服务（发送邮件）
    → 同步调用推荐服务（更新推荐）
    → 响应慢

解决：
    # 改为异步通信（消息队列）
    await message_queue.publish("OrderCreated", order_data)
```

---

## 🎯 小实验：同步通信

### 实验：实现服务间 HTTP 调用

```python
# user_service/main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/users/{user_id}")
def get_user(user_id: int):
    return {"id": user_id, "name": "Alice", "email": "alice@example.com"}

# order_service/main.py
from fastapi import FastAPI
import httpx

app = FastAPI()
user_client = httpx.AsyncClient(base_url="http://user-service:8001")

@app.post("/orders")
async def create_order(user_id: int, product_id: int):
    # 调用用户服务
    response = await user_client.get(f"/users/{user_id}")
    user = response.json()

    # 创建订单
    order = {
        "id": 1,
        "user": user,
        "product_id": product_id
    }
    return order
```

---

## 📚 检查理解

回答这些问题来测试你的理解：

1. **同步通信的优缺点？**
   - 提示：简单直观 vs 强耦合、性能问题

2. **HTTP vs gRPC 的区别？**
   - 提示：性能、类型安全、工具生态

3. **如何处理服务间认证？**
   - 提示：API Key、JWT、mTLS

4. **如何优化同步通信性能？**
   - 提示：连接池、并行调用、缓存

5. **如何避免级联故障？**
   - 提示：熔断器、超时、降级

---

## 🚀 下一步

现在你已经了解了同步通信，接下来：

1. **学习异步通信**：`notes/04_service_communication_async.md`
2. **学习 API 网关**：`notes/05_api_gateway.md`

**记住：同步通信简单直接，但要注意容错和性能！**
