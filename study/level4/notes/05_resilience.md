# 05. 限流、熔断、降级 - Rate Limiting, Circuit Breaking, Degradation

## 📍 在架构中的位置

**从"毫无防备"到"铜墙铁壁"**

```
┌─────────────────────────────────────────────────────────────┐
│          没有保护机制                                         │
└─────────────────────────────────────────────────────────────┘

正常情况：
    100 用户/秒 → API 正常响应

异常情况：
    恶意攻击：10000 请求/秒
    → 数据库：10000 连接/秒
    → 数据库：崩溃（处理不了）❌
    → 正常用户：无法访问 ❌

    外部服务故障：
    → 调用外部 API（超时、重试、超时、重试...）
    → 我们的连接池耗尽
    → 整个应用崩溃 ❌

    高峰流量：
    → 流量暴增 10 倍
    → 服务器资源耗尽
    → 所有请求失败 ❌

═══════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────┐
│          有保护机制                                           │
└─────────────────────────────────────────────────────────────┘

异常情况 1：恶意攻击
    限流：每个 IP 最多 100 请求/分钟
    → 恶意流量：被拦截 ✅
    → 正常用户：正常访问 ✅

异常情况 2：外部服务故障
    熔断器：检测到外部服务持续失败
    → 熔断器打开：快速失败 ✅
    → 降级：返回缓存数据 ✅
    → 我们的应用：继续运行 ✅

异常情况 3：高峰流量
    降级：关闭非核心功能
    → 推荐服务：暂停（节省资源）✅
    → 核心功能：正常运行 ✅
```

**🎯 你的学习目标**：掌握限流、熔断、降级三大保护机制，让应用具备生产级韧性。

---

## 🚦 限流（Rate Limiting）

### 为什么需要限流？

**生活类比：餐厅限流**

```
没有限流：
    1000 顾客同时涌入餐厅
    → 服务员忙不过来
    → 厨房瘫痪
    → 所有顾客：等待 2 小时
    → 体验极差 ❌

有限流：
    门口排队：每次进 50 人
    → 餐厅内：井然有序
    → 服务质量：保证
    → 等待时间：可预期 ✅
```

---

### 限流算法

#### 1. 固定窗口（Fixed Window）

**原理**：

```
时间窗口：1 分钟
限制：100 次请求

10:00:00 - 10:00:59：100 次 ✅
10:01:00 - 10:01:59：重新计数，100 次 ✅

问题：
- 突刺问题（边界）
- 10:00:59：100 次
- 10:01:00：100 次
- 1 秒内 200 次（突刺）❌
```

**代码实现**：

```python
import time
from collections import defaultdict

class FixedWindowRateLimiter:
    """固定窗口限流器"""

    def __init__(self, rate: int, window: int):
        """
        rate: 限制次数
        window: 时间窗口（秒）
        """
        self.rate = rate
        self.window = window
        self.requests = defaultdict(int)  # {user_id: count}
        self.window_start = defaultdict(int)  # {user_id: start_time}

    def is_allowed(self, user_id: int) -> bool:
        """检查是否允许请求"""

        now = int(time.time())

        # 检查窗口是否重置
        if now - self.window_start[user_id] >= self.window:
            self.requests[user_id] = 0
            self.window_start[user_id] = now

        # 检查是否超过限制
        if self.requests[user_id] >= self.rate:
            return False

        self.requests[user_id] += 1
        return True


# 使用
limiter = FixedWindowRateLimiter(rate=100, window=60)

if limiter.is_allowed(user_id=123):
    # 处理请求
    pass
else:
    # 返回 429 Too Many Requests
    pass
```

---

#### 2. 滑动窗口（Sliding Window）

**原理**：

```
时间窗口：1 分钟（滑动）
限制：100 次请求

10:00:30：查看过去 1 分钟（09:59:30 - 10:00:30）
10:00:30：查看过去 1 分钟（09:59:31 - 10:00:31）
...

好处：
- 平滑限流
- 没有突刺问题 ✅
```

**代码实现**：

```python
import time
from collections import deque

class SlidingWindowRateLimiter:
    """滑动窗口限流器"""

    def __init__(self, rate: int, window: int):
        self.rate = rate
        self.window = window
        self.requests = defaultdict(deque)  # {user_id: deque([timestamp1, timestamp2, ...])}

    def is_allowed(self, user_id: int) -> bool:
        """检查是否允许请求"""

        now = time.time()
        user_requests = self.requests[user_id]

        # 移除窗口外的旧请求
        while user_requests and user_requests[0] <= now - self.window:
            user_requests.popleft()

        # 检查是否超过限制
        if len(user_requests) >= self.rate:
            return False

        # 记录当前请求
        user_requests.append(now)
        return True
```

---

#### 3. 令牌桶（Token Bucket）

**原理**：

```
桶：容量 100 个令牌
速率：每秒补充 10 个令牌

请求：
- 消耗 1 个令牌
- 有令牌？→ 允许 ✅
- 无令牌？→ 拒绝 ❌

特点：
- 允许突发（桶内令牌可积累）
- 平滑限流
```

**代码实现**：

```python
import time
import asyncio

class TokenBucketRateLimiter:
    """令牌桶限流器"""

    def __init__(self, rate: float, capacity: int):
        """
        rate: 令牌补充速率（个/秒）
        capacity: 桶容量
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity  # 当前令牌数
        self.last_refill = time.time()

    async def acquire(self, tokens: int = 1):
        """获取令牌（阻塞直到有足够令牌）"""

        while True:
            now = time.time()

            # 补充令牌
            elapsed = now - self.last_refill
            refill_amount = elapsed * self.rate
            self.tokens = min(self.capacity, self.tokens + refill_amount)
            self.last_refill = now

            # 检查是否有足够令牌
            if self.tokens >= tokens:
                self.tokens -= tokens
                return

            # 等待
            wait_time = (tokens - self.tokens) / self.rate
            await asyncio.sleep(wait_time)

    def is_allowed(self, tokens: int = 1) -> bool:
        """非阻塞检查是否允许"""

        now = time.time()

        # 补充令牌
        elapsed = now - self.last_refill
        refill_amount = elapsed * self.rate
        self.tokens = min(self.capacity, self.tokens + refill_amount)
        self.last_refill = now

        # 检查是否有足够令牌
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True

        return False
```

---

### FastAPI 集成限流

**基于 IP 的限流**：

```python
from fastapi import FastAPI, Request, HTTPException, Depends
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

app = FastAPI()

# ═══════════════════════════════════════════════════════════
# 1. 配置限流器（使用 slowapi）
# ═══════════════════════════════════════════════════════════

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ═══════════════════════════════════════════════════════════
# 2. 使用限流装饰器
# ═══════════════════════════════════════════════════════════

@app.get("/users")
@limiter.limit("10/minute")  # 每分钟 10 次请求
async def get_users(request: Request):
    """获取用户列表（限流）"""
    return {"users": []}

@app.post("/orders")
@limiter.limit("5/minute")  # 每分钟 5 次请求
async def create_order(request: Request):
    """创建订单（限流）"""
    return {"order_id": 123}
```

---

**基于用户的限流**：

```python
from fastapi import Depends, HTTPException, Header
from typing import Dict

# ═══════════════════════════════════════════════════════════
# 令牌桶限流器（按用户）
# ═══════════════════════════════════════════════════════════

user_limiters: Dict[int, TokenBucketRateLimiter] = {}

def get_user_limiter(user_id: int) -> TokenBucketRateLimiter:
    """获取用户限流器"""

    if user_id not in user_limiters:
        user_limiters[user_id] = TokenBucketRateLimiter(
            rate=10.0,      # 每秒 10 个令牌
            capacity=100    # 桶容量 100
        )

    return user_limiters[user_id]

async def check_rate_limit(user_id: int):
    """检查用户速率限制"""

    limiter = get_user_limiter(user_id)

    if not limiter.is_allowed():
        raise HTTPException(
            status_code=429,
            detail="Too many requests, please try again later"
        )

# ═══════════════════════════════════════════════════════════
# 使用限流
# ═══════════════════════════════════════════════════════════

@app.get("/api/users")
async def get_users(user_id: int = Header(...)):
    """获取用户（按用户限流）"""

    await check_rate_limit(user_id)

    return {"users": []}
```

---

## 🔌 熔断器（Circuit Breaker）

### 熔断器状态

**三种状态**：

```
┌─────────────────────────────────────────────────────────────┐
│                    熔断器状态机                              │
└─────────────────────────────────────────────────────────────┘

CLOSED（闭合）→ 正常状态
    │
    │ 失败次数达到阈值
    ↓
OPEN（打开）→ 熔断状态（拒绝请求）
    │
    │ 等待超时时间
    ↓
HALF_OPEN（半开）→ 尝试恢复
    │
    │ 成功？→ CLOSED（恢复）
    │ 失败？→ OPEN（继续熔断）
```

---

### 使用 pybreaker 实现熔断器

**安装**：

```bash
pip install pybreaker
```

---

**基本使用**：

```python
from pybreaker import CircuitBreaker
import httpx

# ═══════════════════════════════════════════════════════════
# 1. 创建熔断器
# ═══════════════════════════════════════════════════════════

external_api_breaker = CircuitBreaker(
    fail_max=5,           # 失败阈值：5 次
    timeout_duration=60   # 超时时间：60 秒
)

# ═══════════════════════════════════════════════════════════
# 2. 使用熔断器保护函数
# ═══════════════════════════════════════════════════════════

@external_api_breaker
async def call_external_api(url: str):
    """调用外部 API（受熔断器保护）"""

    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()

# ═══════════════════════════════════════════════════════════
# 3. 使用
# ═══════════════════════════════════════════════════════════

try:
    result = await call_external_api("https://api.example.com/data")
except external_api_breaker.CircuitBreakerError:
    # 熔断器打开，返回降级数据
    result = get_fallback_data()
```

---

### FastAPI 集成熔断器

**完整示例**：

```python
from fastapi import FastAPI, HTTPException
from pybreaker import CircuitBreaker
import httpx

app = FastAPI()

# ═══════════════════════════════════════════════════════════
# 1. 创建多个熔断器（针对不同服务）
# ═══════════════════════════════════════════════════════════

payment_breaker = CircuitBreaker(
    fail_max=3,
    timeout_duration=30
)

shipping_breaker = CircuitBreaker(
    fail_max=5,
    timeout_duration=60
)

# ═══════════════════════════════════════════════════════════
# 2. 熔断的函数
# ═══════════════════════════════════════════════════════════

@payment_breaker
async def call_payment_api(amount: float):
    """调用支付 API"""

    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.post(
            "https://api.payment.com/charge",
            json={"amount": amount}
        )
        response.raise_for_status()
        return response.json()

@shipping_breaker
async def call_shipping_api(address: str):
    """调用物流 API"""

    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.post(
            "https://api.shipping.com/create",
            json={"address": address}
        )
        response.raise_for_status()
        return response.json()

# ═══════════════════════════════════════════════════════════
# 3. 业务端点
# ═══════════════════════════════════════════════════════════

@app.post("/orders")
async def create_order(amount: float, address: str):
    """创建订单"""

    try:
        # 调用支付 API
        payment = await call_payment_api(amount)

    except payment_breaker.CircuitBreakerError:
        # 支付服务熔断，返回错误
        raise HTTPException(
            status_code=503,
            detail="Payment service unavailable, please try again later"
        )

    try:
        # 调用物流 API
        shipping = await call_shipping_api(address)

    except shipping_breaker.CircuitBreakerError:
        # 物流服务熔断，使用降级方案（稍后重试）
        shipping = {"message": "Shipping will be arranged later"}

    return {
        "payment": payment,
        "shipping": shipping
    }
```

---

## 🔄 服务降级（Service Degradation）

### 什么是降级？

**生活类比：餐厅降级**

```
正常情况：
    └─ 完整菜单：50 道菜
    └─ 完整服务：迎宾、点餐、上菜、送客

高峰期（资源不足）：
    └─ 简化菜单：10 道热销菜（推荐功能暂停）✅
    └─ 核心服务：点餐、上菜（迎宾暂停）✅

极端情况（厨师病了）：
    └─ 只有预做菜（半成品）✅
    └─ 保证：不关门，有东西卖 ✅
```

**降级策略**：

```
1. 关闭非核心功能
   - 推荐系统（可暂停）
   - 搜索功能（可降级为简单搜索）
   - 数据分析（可暂停）

2. 返回默认值
   - 用户头像：返回默认头像
   - 排行榜：返回缓存排行榜
   - 评论数：显示"数万+"

3. 返回缓存数据
   - 商品详情：返回 1 小时前的缓存
   - 用户信息：返回 5 分钟前的缓存
   - 统计数据：返回昨天的数据

4. 延迟处理
   - 邮件发送：稍后重试
   - 数据同步：稍后同步
   - 日志记录：批量写入
```

---

### 降级实现

**装饰器实现**：

```python
from functools import wraps
import asyncio
from typing import Callable, Any

def fallback_on_error(fallback_func: Callable):
    """错误时降级装饰器"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                print(f"Error in {func.__name__}: {e}, using fallback")
                return await fallback_func(*args, **kwargs)
        return wrapper
    return decorator


# ═══════════════════════════════════════════════════════════
# 使用
# ═══════════════════════════════════════════════════════════

async def get_recommended_products_fallback(user_id: int):
    """推荐系统降级：返回热门商品"""
    return await get_hot_products()

@fallback_on_error(get_recommended_products_fallback)
async def get_recommended_products(user_id: int):
    """获取推荐商品（可能失败）"""
    return await recommendation_service.get_recommendations(user_id)

# 使用
products = await get_recommended_products(user_id=123)
# 如果推荐服务挂了，自动返回热门商品
```

---

**FastAPI 集成降级**：

```python
from fastapi import FastAPI, HTTPException
import httpx

app = FastAPI()

# ═══════════════════════════════════════════════════════════
# 1. 降级函数
# ═══════════════════════════════════════════════════════════

async def get_recommendations_fallback():
    """推荐系统降级：返回热门商品"""

    # 返回缓存的热门商品
    return {
        "products": [
            {"id": 1, "name": "Hot Product 1"},
            {"id": 2, "name": "Hot Product 2"}
        ],
        "source": "fallback"  # 标记为降级数据
    }

async def get_user_stats_fallback():
    """统计服务降级：返回默认值"""

    return {
        "views": "N/A",
        "likes": "N/A",
        "source": "fallback"
    }

# ═══════════════════════════════════════════════════════════
# 2. 业务函数（带降级）
# ═══════════════════════════════════════════════════════════

async def get_recommendations(user_id: int):
    """获取推荐商品"""

    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(
                f"https://api.recommendation.com/users/{user_id}/recommendations"
            )
            response.raise_for_status()
            return response.json()

    except (httpx.TimeoutException, httpx.HTTPError):
        # 失败时降级
        return await get_recommendations_fallback()

async def get_user_stats(user_id: int):
    """获取用户统计"""

    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(
                f"https://api.stats.com/users/{user_id}"
            )
            response.raise_for_status()
            return response.json()

    except (httpx.TimeoutException, httpx.HTTPError):
        # 失败时降级
        return await get_user_stats_fallback()

# ═══════════════════════════════════════════════════════════
# 3. Endpoints
# ═══════════════════════════════════════════════════════════

@app.get("/users/{user_id}/recommendations")
async def user_recommendations(user_id: int):
    """获取用户推荐"""

    recommendations = await get_recommendations(user_id)

    # 检查是否为降级数据
    if recommendations.get("source") == "fallback":
        # 可以添加告警
        log_warning("Recommendation service failed, using fallback")

    return recommendations

@app.get("/users/{user_id}/stats")
async def user_stats(user_id: int):
    """获取用户统计"""

    stats = await get_user_stats(user_id)
    return stats
```

---

## 🎨 完整示例：电商系统

### 限流 + 熔断 + 降级

```python
from fastapi import FastAPI, HTTPException, Request, Header
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pybreaker import CircuitBreaker
import httpx

app = FastAPI()

# ═══════════════════════════════════════════════════════════
# 1. 限流配置
# ═══════════════════════════════════════════════════════════

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ═══════════════════════════════════════════════════════════
# 2. 熔断器配置
# ═══════════════════════════════════════════════════════════

payment_breaker = CircuitBreaker(fail_max=3, timeout_duration=30)
inventory_breaker = CircuitBreaker(fail_max=5, timeout_duration=60)
recommendation_breaker = CircuitBreaker(fail_max=5, timeout_duration=60)

# ═══════════════════════════════════════════════════════════
# 3. 服务调用（带熔断）
# ═══════════════════════════════════════════════════════════

@payment_breaker
async def call_payment_service(order_id: int, amount: float):
    """调用支付服务"""

    async with httpx.AsyncClient(timeout=3.0) as client:
        response = await client.post(
            "https://api.payment.com/charge",
            json={"order_id": order_id, "amount": amount}
        )
        response.raise_for_status()
        return response.json()

@inventory_breaker
async def call_inventory_service(product_id: int, quantity: int):
    """调用库存服务"""

    async with httpx.AsyncClient(timeout=3.0) as client:
        response = await client.post(
            f"https://api.inventory.com/products/{product_id}/reserve",
            json={"quantity": quantity}
        )
        response.raise_for_status()
        return response.json()

@recommendation_breaker
async def call_recommendation_service(user_id: int):
    """调用推荐服务"""

    async with httpx.AsyncClient(timeout=2.0) as client:
        response = await client.get(
            f"https://api.recommendation.com/users/{user_id}"
        )
        response.raise_for_status()
        return response.json()

# ═══════════════════════════════════════════════════════════
# 4. 降级函数
# ═══════════════════════════════════════════════════════════

async def get_recommendations_fallback():
    """推荐服务降级"""
    return {
        "products": get_hot_products_from_cache(),
        "source": "fallback"
    }

async def get_recommendations_with_fallback(user_id: int):
    """获取推荐（带降级）"""

    try:
        return await call_recommendation_service(user_id)
    except (recommendation_breaker.CircuitBreakerError, httpx.HTTPError):
        return await get_recommendations_fallback()

# ═══════════════════════════════════════════════════════════
# 5. Endpoints
# ═══════════════════════════════════════════════════════════

@app.get("/products/{product_id}/recommendations")
@limiter.limit("100/minute")  # 限流
async def product_recommendations(product_id: int, request: Request):
    """获取商品推荐（限流 + 熔断 + 降级）"""

    recommendations = await get_recommendations_with_fallback(product_id)
    return recommendations

@app.post("/orders")
@limiter.limit("10/minute")  # 限流（更严格）
async def create_order(request: Request, order: OrderCreate):
    """创建订单（限流 + 熔断）"""

    # 1. 扣库存（带熔断）
    try:
        inventory = await call_inventory_service(
            order.product_id,
            order.quantity
        )
    except inventory_breaker.CircuitBreakerError:
        raise HTTPException(
            status_code=503,
            detail="Inventory service unavailable, please try again later"
        )

    # 2. 支付（带熔断）
    try:
        payment = await call_payment_service(
            order.id,
            order.amount
        )
    except payment_breaker.CircuitBreakerError:
        # 支付服务失败，需要回滚库存
        await rollback_inventory(order.product_id, order.quantity)

        raise HTTPException(
            status_code=503,
            detail="Payment service unavailable, please try again later"
        )

    return {
        "order_id": order.id,
        "payment": payment,
        "inventory": inventory
    }
```

---

## 🎯 小实验：自己动手

### 实验 1：令牌桶限流

```python
import asyncio

limiter = TokenBucketRateLimiter(rate=10.0, capacity=100)

async def test_limiter():
    for i in range(105):
        if limiter.is_allowed():
            print(f"Request {i}: Allowed")
        else:
            print(f"Request {i}: Denied")

asyncio.run(test_limiter())
```

---

### 实验 2：熔断器

```python
from pybreaker import CircuitBreaker

breaker = CircuitBreaker(fail_max=2, timeout_duration=5)

@breaker
async def failing_function():
    raise Exception("Service unavailable")

async def test_breaker():
    for i in range(5):
        try:
            await failing_function()
        except Exception as e:
            print(f"Attempt {i}: {e}")

asyncio.run(test_breaker())
```

---

## 📚 检查理解

回答这些问题来测试你的理解：

1. **为什么需要限流？**
   - 提示：防止恶意攻击、保护系统

2. **固定窗口和滑动窗口的区别？**
   - 提示：突刺问题、平滑限流

3. **令牌桶算法的优点？**
   - 提示：允许突发、平滑限流

4. **熔断器的三种状态？**
   - 提示：CLOSED、OPEN、HALF_OPEN

5. **什么是服务降级？**
   - 提示：核心功能保持、非核心功能暂停

---

## 🚀 下一步

恭喜！现在你已经掌握了 Level 4 的所有内容！

**Level 4 总结**：
- ✅ Redis 缓存集成
- ✅ 消息队列（Kafka/RabbitMQ）
- ✅ 外部 API 集成（超时、重试、熔断）
- ✅ 监控和日志（Prometheus、结构化日志）
- ✅ 限流、熔断、降级

**接下来**：
- 📖 学习 **Level 5**：部署与运维
- 📖 学习 **Docker 容器化**
- 📖 学习 **Kubernetes 编排**

**记住**：限流、熔断、降级是生产环境的三大保护机制，缺一不可！**

---

**费曼技巧总结**：
- ✅ 餐厅限流类比
- ✅ 三种限流算法（固定窗口、滑动窗口、令牌桶）
- ✅ 熔断器状态机
- ✅ 服务降级策略
- ✅ 完整的电商系统示例（限流+熔断+降级）
