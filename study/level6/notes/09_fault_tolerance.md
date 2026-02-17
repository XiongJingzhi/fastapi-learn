# 09. 容错模式 - Fault Tolerance Patterns

## 📍 在架构中的位置

**从"一个服务挂了，整个系统挂"到"故障隔离"**

```
┌─────────────────────────────────────────────────────────────┐
│          没有容错保护                                        │
└─────────────────────────────────────────────────────────────┘

客户端 → API 网关 → 订单服务 → 用户服务（挂了）
                     ↓
                  等待超时
                     ↓
                  线程池耗尽
                     ↓
                  订单服务也挂了
                     ↓
                  级联故障，整个系统崩溃 ❌

═══════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────┐
│          有容错保护                                          │
└─────────────────────────────────────────────────────────────┘

客户端 → API 网关 → 订单服务 → 用户服务（挂了）
                     ↓
                  熔断器检测到故障
                     ↓
                  熔断器打开，返回降级数据
                     ↓
                  订单服务正常运行 ✅
```

**🎯 你的学习目标**：掌握微服务架构中的容错模式，包括熔断、降级、限流、超时、重试等。

---

## 🎯 为什么需要容错模式？

### 分布式系统的现实

```
墨菲定律：
    "凡是可能出错的事，就一定会出错"

在微服务中：
    - 网络会失败
    - 服务会崩溃
    - 数据库会不可用
    - 响应会很慢
    - 依赖会失效

如果没有容错保护：
    一个服务的问题 → 级联故障 → 整个系统崩溃
```

### 生活类比：电梯安全

```
没有安全措施：
    电梯故障 → 自由落体 → 人员伤亡

有安全措施：
    电梯故障
    → 限速器（防止速度过快）
    → 安全钳（夹住导轨）
    → 缓冲器（减少冲击）
    → 人员安全

微服务的容错模式 = 电梯的安全措施
```

---

## 🔌 模式 1：熔断器（Circuit Breaker）

### 概念

```
熔断器就像电路的保险丝：
    - 电流过大（故障率过高）
    → 熔断器打开（断开电路）
    → 保护整个系统（防止级联故障）
    → 一段时间后尝试恢复（半开状态）
```

### 三种状态

```
关闭（Closed）：
    - 正常状态
    - 请求正常通过
    - 统计故障率

打开（Open）：
    - 故障率超过阈值
    - 熔断器打开
    - 直接返回错误或降级数据
    - 不再调用后端服务

半开（Half-Open）：
    - 熔断器打开一段时间后
    - 允许少量请求通过
    - 测试服务是否恢复
    → 成功 → 熔断器关闭
    → 失败 → 熔断器继续打开
```

### 实现

```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
async def call_user_service(user_id: int):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://user-service:8001/users/{user_id}")
        response.raise_for_status()
        return response.json()

# 使用
@app.get("/orders/{order_id}")
async def get_order(order_id: int):
    try:
        user = await call_user_service(user_id)
    except CircuitBreakerError:
        # 熔断器打开，返回降级数据
        user = {"id": user_id, "name": "Unknown"}
    return {"user": user}
```

### 配置参数

```python
@circuit(
    failure_threshold=5,      # 失败多少次后打开熔断器
    recovery_timeout=60,      # 熔断器打开后多久尝试恢复（秒）
    expected_exception=ConnectionError  # 哪些异常计入失败
)
async def call_service():
    pass
```

---

## ⬇️ 模式 2：降级（Fallback）

### 概念

```
当服务不可用时，返回备选方案
    - 返回缓存数据
    - 返回默认值
    - 返回推荐数据
```

### 降级策略

```python
from functools import wraps

def fallback(cache_key: str, default_value: any):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except (CircuitBreakerError, TimeoutException):
                # 1. 尝试从缓存获取
                cached = await cache.get(cache_key)
                if cached:
                    return cached

                # 2. 返回默认值
                return default_value
        return wrapper
    return decorator

@fallback(cache_key="user:123", default_value={"id": 123, "name": "Unknown"})
async def get_user(user_id: int):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://user-service:8001/users/{user_id}")
        return response.json()
```

### 降级示例

```python
# 电商系统降级策略

@app.get("/products/{product_id}")
async def get_product(product_id: int):
    try:
        # 正常调用产品服务
        product = await product_service.get_product(product_id)
    except Exception:
        # 降级：返回缓存的产品数据
        product = await cache.get(f"product:{product_id}")
        if not product:
            # 降级：返回默认产品信息
            product = {
                "id": product_id,
                "name": "Temporarily Unavailable",
                "price": 0
            }
    return product

@app.get("/recommendations/{user_id}")
async def get_recommendations(user_id: int):
    try:
        # 正常调用推荐服务
        recommendations = await recommendation_service.get(user_id)
    except Exception:
        # 降级：返回热门商品
        recommendations = await get_hot_products()
    return recommendations
```

---

## 🚦 模式 3：限流（Rate Limiting）

### 概念

```
限制请求速率，防止系统过载
    - 用户级别限流（防止某个用户过度使用）
    - IP 级别限流（防止 DDoS 攻击）
    - 服务级别限流（保护后端服务）
```

### 实现方式

```python
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# 全局限流
@app.get("/api/products")
@limiter.limit("100/minute")  # 每分钟 100 次
async def get_products(request: Request):
    pass

# 不同接口不同限流
@app.get("/api/public")
@limiter.limit("1000/minute")  # 公开接口：高限流
async def public_endpoint(request: Request):
    pass

@app.post("/api/heavy-computation")
@limiter.limit("10/minute")  # 昂贵操作：低限流
async def heavy_computation(request: Request):
    pass

# 用户级别限流
@app.get("/api/users/{user_id}")
@limiter.limit("60/minute", key_func=lambda r: f"user:{r.path_params['user_id']}")
async def get_user(request: Request, user_id: int):
    pass
```

### 限流算法

```
1. 固定窗口（Fixed Window）
   → 每分钟固定次数
   → 问题：边界突刺（一分钟末尾 + 下一分钟开头 = 2倍请求）

2. 滑动窗口（Sliding Window Log）
   → 记录每个请求的时间戳
   → 滑动窗口内统计请求数
   → 更精确，但内存占用大

3. 令牌桶（Token Bucket）
   → 以固定速率向桶中放入令牌
   → 请求消耗令牌
   → 允许突发流量

4. 漏桶（Leaky Bucket）
   → 请求进入漏桶
   → 以固定速率处理
   → 平滑流量
```

---

## ⏱️ 模式 4：超时（Timeout）

### 概念

```
设置超时时间，防止无限等待
    - 连接超时（建立连接的最长时间）
    - 读取超时（读取数据的最长时间）
    - 总超时（整个请求的最长时间）
```

### 实现

```python
import httpx
from httpx import TimeoutException

# 设置超时
timeout = httpx.Timeout(
    connect=2.0,   # 连接超时 2 秒
    read=5.0,      # 读取超时 5 秒
    write=5.0,     # 写入超时 5 秒
    pool=10.0      # 连接池超时 10 秒
)

async def call_service():
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get("http://user-service:8001/users/1")
            return response.json()
    except TimeoutException:
        # 超时处理
        raise HTTPException(status_code=504, detail="Service timeout")
```

### 超时策略

```python
# 不同操作不同超时
timeout_config = {
    "fast_query": Timeout(1.0),      # 快速查询：1 秒
    "normal_query": Timeout(5.0),    # 普通查询：5 秒
    "slow_query": Timeout(30.0),     # 慢查询：30 秒
}

async def query_user(user_id: int):
    timeout = timeout_config["fast_query"]
    async with httpx.AsyncClient(timeout=timeout) as client:
        return await client.get(f"/users/{user_id}")
```

---

## 🔄 模式 5：重试（Retry）

### 概念

```
请求失败时自动重试
    - 瞬时故障（网络抖动）
    → 重试可能成功
    - 持久故障（服务下线）
    → 重试无意义，快速失败
```

### 实现

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

# 指数退避重试
@retry(
    stop=stop_after_attempt(3),  # 最多重试 3 次
    wait=wait_exponential(multiplier=1, min=1, max=10),  # 指数退避：1s, 2s, 4s, ...
    retry=retry_if_exception_type(httpx.NetworkError),  # 只重试网络错误
    reraise=True  # 重试失败后重新抛出异常
)
async def call_service():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://user-service:8001/users/1")
        response.raise_for_status()
        return response.json()

# 使用
try:
    user = await call_service()
except httpx.HTTPError:
    # 重试失败，返回降级数据
    user = {"id": 1, "name": "Unknown"}
```

### 重试策略

```python
# 1. 固定延迟重试
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
async def retry_fixed_delay():
    pass

# 2. 线性退避重试
@retry(stop=stop_after_attempt(3), wait=wait_incrementing(start=1, increment=2))
async def retry_linear_backoff():
    pass

# 3. 随机抖动重试（避免惊群效应）
@retry(stop=stop_after_attempt(3), wait=wait_random_exponential(multiplier=1, max=10))
async def retry_random_jitter():
    pass

# 4. 只重试特定异常
@retry(retry=retry_if_exception_type(ConnectionError))
async def retry_specific_exceptions():
    pass
```

### 幂等性

```python
# 重试要求操作幂等（多次执行结果相同）
# 幂等操作：GET、PUT、DELETE
# 非幂等操作：POST

@retry(stop=stop_after_attempt(3))
async def create_order(order_data: dict):
    # 非幂等操作！不要重试！
    pass

@retry(stop=stop_after_attempt(3))
async def update_order(order_id: int, order_data: dict):
    # 幂等操作，可以重试
    pass

# 生成幂等键
import uuid

@app.post("/orders")
async def create_order(order_data: dict, idempotency_key: str = None):
    if not idempotency_key:
        idempotency_key = str(uuid.uuid4())

    # 检查是否已处理
    existing = await cache.get(f"idempotency:{idempotency_key}")
    if existing:
        return existing  # 返回之前的结果

    # 创建订单
    order = await create_order_in_db(order_data)

    # 缓存结果
    await cache.set(f"idempotency:{idempotency_key}", order, expire=3600)

    return order
```

---

## 🚢 模式 6：舱壁隔离（Bulkhead）

### 概念

```
将资源隔离，防止一个服务的故障影响其他服务
    - 线程池隔离
    - 信号量隔离
```

### 实现

```python
from concurrent.futures import ThreadPoolExecutor
import asyncio

# 为不同的服务创建独立的线程池
user_service_executor = ThreadPoolExecutor(max_workers=10)
order_service_executor = ThreadPoolExecutor(max_workers=20)

async def call_user_service(user_id: int):
    loop = asyncio.get_event_loop()
    # 使用独立的线程池
    return await loop.run_in_executor(
        user_service_executor,
        lambda: requests.get(f"http://user-service:8001/users/{user_id}")
    )

async def call_order_service(order_id: int):
    loop = asyncio.get_event_loop()
    # 使用独立的线程池
    return await loop.run_in_executor(
        order_service_executor,
        lambda: requests.get(f"http://order-service:8002/orders/{order_id}")
    )
```

### 信号量隔离

```python
import asyncio

# 为不同的服务设置并发限制
user_service_semaphore = asyncio.Semaphore(10)
order_service_semaphore = asyncio.Semaphore(20)

async def call_user_service(user_id: int):
    async with user_service_semaphore:
        # 最多 10 个并发请求
        async with httpx.AsyncClient() as client:
            return await client.get(f"http://user-service:8001/users/{user_id}")

async def call_order_service(order_id: int):
    async with order_service_semaphore:
        # 最多 20 个并发请求
        async with httpx.AsyncClient() as client:
            return await client.get(f"http://order-service:8002/orders/{order_id}")
```

---

## 🎯 组合使用

### 完整的容错策略

```python
from tenacity import retry, stop_after_attempt, wait_exponential
from circuitbreaker import circuit
from httpx import Timeout, TimeoutException
import asyncio

# 组合使用：超时 + 重试 + 熔断 + 降级
@circuit(failure_threshold=5, recovery_timeout=60)
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(TimeoutException)
)
async def call_user_service_with_circuit_breaker(user_id: int):
    timeout = Timeout(connect=2.0, read=5.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(f"http://user-service:8001/users/{user_id}")
        response.raise_for_status()
        return response.json()

# 使用
@app.get("/orders/{order_id}")
async def get_order(order_id: int):
    try:
        user = await call_user_service_with_circuit_breaker(user_id)
    except Exception:
        # 所有容错措施都失败，返回降级数据
        user = {"id": user_id, "name": "Unknown"}
    return {"user": user}
```

---

## 📊 监控容错

### 监控指标

```python
from prometheus_client import Counter, Histogram

# 熔断器状态
circuit_breaker_open = Counter(
    'circuit_breaker_open_total',
    'Circuit breaker opened',
    ['service']
)

# 降级次数
fallback_calls = Counter(
    'fallback_calls_total',
    'Fallback calls',
    ['service', 'reason']
)

# 重试次数
retry_attempts = Counter(
    'retry_attempts_total',
    'Retry attempts',
    ['service']
)

# 超时次数
timeout_errors = Counter(
    'timeout_errors_total',
    'Timeout errors',
    ['service']
)

# 使用
@app.get("/orders/{order_id}")
async def get_order(order_id: int):
    try:
        user = await call_user_service(user_id)
    except CircuitBreakerError:
        circuit_breaker_open.labels(service='user-service').inc()
        user = {"id": user_id, "name": "Unknown"}
    except TimeoutException:
        timeout_errors.labels(service='user-service').inc()
        user = {"id": user_id, "name": "Unknown"}
    return user
```

---

## ⚠️ 常见陷阱

### 陷阱 1：过度重试

```
问题：
    重试次数过多
    → 加重后端服务负担
    → 延迟增加

解决：
    - 限制重试次数（最多 3 次）
    - 使用指数退避
    - 只对瞬时错误重试
```

### 陷阱 2：超时设置过长

```
问题：
    超时设置过长
    → 客户端等待时间过长
    → 资源被占用

解决：
    - 根据业务设置合理的超时
    - 快速失败优于慢速响应
```

### 陷阱 3：降级逻辑简单

```
问题：
    降级返回空数据或错误数据
    → 用户体验差

解决：
    - 降级返回有意义的备选数据
    - 降级返回缓存数据
    - 降级返回推荐数据
```

---

## 🎯 小实验：容错模式

### 实验：实现熔断器

```python
from datetime import datetime, timedelta
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, failure_threshold: int, recovery_timeout: int):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        self.opened_at = None

    def call(self, func):
        async def wrapper(*args, **kwargs):
            # 检查熔断器状态
            if self.state == CircuitState.OPEN:
                if datetime.now() - self.opened_at > timedelta(seconds=self.recovery_timeout):
                    self.state = CircuitState.HALF_OPEN
                else:
                    raise Exception("Circuit breaker is open")

            try:
                result = await func(*args, **kwargs)
                # 成功，重置失败计数
                self.failure_count = 0
                if self.state == CircuitState.HALF_OPEN:
                    self.state = CircuitState.CLOSED
                return result
            except Exception as e:
                self.failure_count += 1
                if self.failure_count >= self.failure_threshold:
                    self.state = CircuitState.OPEN
                    self.opened_at = datetime.now()
                raise e
        return wrapper

# 使用
circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)

@circuit_breaker.call
async def call_user_service(user_id: int):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://user-service:8001/users/{user_id}")
        response.raise_for_status()
        return response.json()
```

---

## 📚 检查理解

回答这些问题来测试你的理解：

1. **为什么需要容错模式？**
   - 提示：防止级联故障

2. **熔断器的工作原理？**
   - 提示：关闭、打开、半开三种状态

3. **降级的策略有哪些？**
   - 提示：缓存数据、默认值、推荐数据

4. **限流的算法有哪些？**
   - 提示：固定窗口、滑动窗口、令牌桶、漏桶

5. **如何组合使用容错模式？**
   - 提示：超时 + 重试 + 熔断 + 降级

---

## 🚀 下一步

现在你已经了解了容错模式，接下来：

1. **学习分布式追踪**：`notes/10_distributed_tracing.md`
2. **查看实际代码**：`examples/`

**记住：在分布式系统中，故障是常态，要为故障做好准备！**
