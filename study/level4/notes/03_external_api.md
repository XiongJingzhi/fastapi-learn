# 03. 外部 API 集成 - External API Integration

## 📍 在架构中的位置

**从内部数据库到外部服务调用**

```
┌─────────────────────────────────────────────────────────────┐
│          Level 3: 只使用内部数据库                           │
└─────────────────────────────────────────────────────────────┘

用户请求：
    用户下单
    → 查询本地数据库（商品信息）
    → 创建订单（100ms）
    → 返回响应

问题：
- 无法调用外部服务（支付、物流、邮件）
- 无法获取第三方数据（天气、汇率、地图）
- 业务受限
═══════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────┐
│          Level 4: 集成外部 API                               │
└─────────────────────────────────────────────────────────────┘

用户请求：
    用户下单
    → 查询本地数据库（商品信息）
    → 调用支付 API（外部服务）
    → 调用物流 API（外部服务）
    → 创建订单（100ms）
    → 返回响应

能力：
- 支付集成（Stripe、支付宝）
- 物流查询（FedEx、顺丰）
- 数据获取（天气、地图、AI 服务）
- 消息推送（短信、邮件、通知）
```

**🎯 你的学习目标**：掌握外部 API 集成的最佳实践，包括超时、重试、熔断等容错机制。

---

## 🎯 为什么需要外部 API 集成？

### 生活类比：餐厅的供应商

**内部数据库 = 餐厅自己的仓库**：
```
餐厅仓库：
├─ 自己的食材
├─ 快速获取（厨房内）
└─ 完全控制
```

**外部 API = 外部供应商**：
```
供应商：
├─ 新鲜食材（蔬菜配送）
├─ 专业服务（酒水供应商）
└─ 第三方服务（清洁服务）

问题：
- 可能延迟（配送堵车）
- 可能失败（供应商缺货）
- 需要容错方案（备用供应商）
```

---

## 🔧 HTTP 客户端（httpx）

### 为什么用 httpx 而不是 requests？

**对比表格**：

| 特性 | requests | httpx |
|------|----------|-------|
| **异步支持** | ❌ 不支持 | ✅ 原生支持 |
| **HTTP/2** | ❌ 不支持 | ✅ 支持 |
| **连接池** | ✅ 支持 | ✅ 更好 |
| **超时控制** | ✅ 基础 | ✅ 高级 |
| **类型提示** | ❌ 无 | ✅ 完整 |

**结论**：FastAPI 是异步框架，必须使用异步 HTTP 客户端！

---

### 安装和基本使用

**安装**：

```bash
pip install httpx
```

**基本 GET 请求**：

```python
import httpx

async def get_user(user_id: int):
    """调用外部 API 获取用户信息"""

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.example.com/users/{user_id}"
        )

        # 检查状态码
        if response.status_code == 200:
            return response.json()
        else:
            return None
```

---

### 带参数和请求头的请求

```python
import httpx

async def search_users(
    query: str,
    limit: int = 10,
    api_key: str = "your-api-key"
):
    """搜索用户（带查询参数和请求头）"""

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.example.com/users/search",
            params={
                "q": query,
                "limit": limit
            },
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
        )

        return response.json()
```

---

### POST 请求（发送数据）

```python
from pydantic import BaseModel

class PaymentRequest(BaseModel):
    amount: float
    currency: str
    payment_method: str

async def create_payment(payment: PaymentRequest):
    """创建支付（POST 请求）"""

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.stripe.com/v1/payments",
            json={
                "amount": payment.amount,
                "currency": payment.currency,
                "payment_method": payment.payment_method
            },
            headers={
                "Authorization": f"Bearer {STRIPE_API_KEY}"
            }
        )

        return response.json()
```

---

## ⏱️ 超时控制

### 为什么需要超时？

**没有超时的问题**：

```
用户请求 → 调用外部 API
    → 外部 API 挂了（无响应）
    → 我们的请求一直等待
    → 连接池耗尽
    → 整个应用崩溃！❌
```

**有超时的保护**：

```
用户请求 → 调用外部 API（超时 5 秒）
    → 外部 API 5 秒内没响应
    → 抛出 Timeout 异常
    → 捕获异常，返回友好错误
    → 应用继续运行 ✅
```

---

### 配置超时

```python
import httpx
from httpx import Timeout

# ═══════════════════════════════════════════════════════════
# 1. 全局超时配置
# ═══════════════════════════════════════════════════════════

timeout = Timeout(
    connect=5.0,    # 连接超时：5 秒
    read=10.0,      # 读取超时：10 秒
    write=5.0,      # 写入超时：5 秒
    pool=5.0        # 连接池获取超时：5 秒
)

async def call_with_timeout():
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get("https://api.example.com/slow")
        return response.json()

# ═══════════════════════════════════════════════════════════
# 2. 单个请求超时配置
# ═══════════════════════════════════════════════════════════

async def call_with_specific_timeout():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.example.com/slow",
            timeout=5.0  # 这个请求超时 5 秒
        )
        return response.json()
```

---

### 处理超时异常

```python
import httpx
from httpx import TimeoutException

async def safe_call_with_timeout(url: str):
    """安全调用外部 API（处理超时）"""

    timeout = Timeout(5.0)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
            return response.json()

    except TimeoutException:
        # 超时处理
        print(f"请求超时：{url}")
        return {"error": "请求超时，请稍后重试"}

    except httpx.HTTPError as e:
        # 其他 HTTP 错误
        print(f"HTTP 错误：{e}")
        return {"error": "请求失败"}
```

---

## 🔄 重试策略

### 为什么需要重试？

**网络不稳定的场景**：

```
第一次请求：网络抖动 → 失败
第二次请求：网络恢复 → 成功 ✅

如果没有重试：
    第一次失败 → 直接返回错误 → 用户体验差
```

**何时应该重试**：
- 网络错误（连接超时、DNS 解析失败）
- 5xx 服务器错误（500, 502, 503, 504）
- 429 速率限制（Too Many Requests）

**何时不应该重试**：
- 4xx 客户端错误（400, 401, 403, 404）
- 这些错误重试也没用（参数错误、权限不足）

---

### 基本重试实现

```python
import asyncio
import httpx

async def call_with_retry(
    url: str,
    max_retries: int = 3,
    retry_delay: float = 1.0
):
    """调用外部 API（带重试）"""

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)

                # 成功
                if response.status_code == 200:
                    return response.json()

                # 5xx 错误（重试）
                if 500 <= response.status_code < 600:
                    print(f"服务器错误 {response.status_code}，重试 {attempt + 1}/{max_retries}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay)
                        continue

                # 4xx 错误（不重试）
                return {"error": f"客户端错误 {response.status_code}"}

        except httpx.TimeoutException:
            print(f"请求超时，重试 {attempt + 1}/{max_retries}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
                continue

        except httpx.HTTPError as e:
            print(f"HTTP 错误：{e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
                continue

    # 所有重试都失败
    return {"error": "请求失败，已达到最大重试次数"}
```

---

### 指数退避重试

```python
import asyncio
import httpx

async def call_with_exponential_backoff(
    url: str,
    max_retries: int = 3,
    initial_delay: float = 1.0
):
    """指数退避重试（避免服务器压力）"""

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)

                if response.status_code == 200:
                    return response.json()

                # 5xx 错误
                if 500 <= response.status_code < 600:
                    if attempt < max_retries - 1:
                        # 指数退避：1s, 2s, 4s, 8s...
                        delay = initial_delay * (2 ** attempt)
                        print(f"重试 {attempt + 1}/{max_retries}，等待 {delay}s")
                        await asyncio.sleep(delay)
                        continue

                return {"error": f"错误 {response.status_code}"}

        except httpx.TimeoutException:
            if attempt < max_retries - 1:
                delay = initial_delay * (2 ** attempt)
                print(f"超时重试 {attempt + 1}/{max_retries}，等待 {delay}s")
                await asyncio.sleep(delay)
                continue

    return {"error": "请求失败"}
```

---

## 🔌 熔断器模式

### 什么是熔断器？

**生活类比：电路熔断器**

```
正常情况：
    电流正常流动 → 熔断器闭合 → 电器工作

异常情况：
    电流过大 → 熔断器跳闸 → 断开电路
    → 保护电器不被烧坏

恢复情况：
    等待一段时间 → 熔断器复位 → 重新通电
```

**软件熔断器**：

```
正常情况：
    外部 API 正常 → 请求正常通过

异常情况：
    外部 API 持续失败 → 熔断器打开
    → 直接返回错误（不再请求外部 API）
    → 保护我们的应用不被拖垮

恢复情况：
    等待一段时间 → 熔断器半开
    → 尝试发送一个请求
    → 成功？→ 熔断器关闭
    → 失败？→ 熔断器继续打开
```

---

### 熔断器实现

```python
import asyncio
import httpx
from datetime import datetime, timedelta
from typing import Optional

class CircuitBreaker:
    """熔断器"""

    def __init__(
        self,
        failure_threshold: int = 5,      # 失败阈值
        recovery_timeout: int = 60,      # 恢复超时（秒）
        expected_exception: Exception = httpx.HTTPError
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0            # 失败计数
        self.last_failure_time: Optional[datetime] = None  # 上次失败时间
        self.state = "CLOSED"             # 状态：CLOSED, OPEN, HALF_OPEN

    def __call__(self, func):
        """装饰器"""
        async def wrapper(*args, **kwargs):
            # 1. 检查熔断器状态
            if self.state == "OPEN":
                # 检查是否可以尝试恢复
                if self._should_attempt_reset():
                    self.state = "HALF_OPEN"
                else:
                    raise Exception("熔断器打开，请求被拒绝")

            # 2. 执行函数
            try:
                result = await func(*args, **kwargs)

                # 成功：重置计数器
                if self.state == "HALF_OPEN":
                    self.state = "CLOSED"
                    self.failure_count = 0

                return result

            except self.expected_exception as e:
                # 失败：增加计数
                self.failure_count += 1
                self.last_failure_time = datetime.now()

                # 检查是否达到阈值
                if self.failure_count >= self.failure_threshold:
                    self.state = "OPEN"

                raise e

        return wrapper

    def _should_attempt_reset(self) -> bool:
        """是否应该尝试重置熔断器"""
        if self.last_failure_time is None:
            return True

        time_since_last_failure = (
            datetime.now() - self.last_failure_time
        ).total_seconds()

        return time_since_last_failure >= self.recovery_timeout


# ═══════════════════════════════════════════════════════════
# 使用熔断器
# ═══════════════════════════════════════════════════════════

# 创建熔断器（5 次失败后打开，60 秒后尝试恢复）
circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60
)

@circuit_breaker
async def call_external_api(url: str):
    """调用外部 API（受熔断器保护）"""
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()


# 使用
try:
    result = await call_external_api("https://api.example.com/data")
except Exception as e:
    print(f"请求失败：{e}")
    # 熔断器打开时，返回缓存数据或默认值
    result = get_cached_data()
```

---

## 🚨 速率限制

### 为什么需要速率限制？

**场景**：调用第三方 API

```
第三方 API 限制：
    - 每分钟 100 次请求
    - 超过限制？→ 返回 429 Too Many Requests
    - 严重超限？→ API 密钥被封禁！❌

没有速率限制：
    我们的请求 → 1000 次/分钟
    → 第三方 API 限制触发
    → 所有请求失败

有速率限制：
    我们的请求 → 100 次/分钟（自动控制）
    → 所有请求成功 ✅
```

---

### 简单的速率限制器

```python
import asyncio
import time
from collections import deque

class RateLimiter:
    """速率限制器（令牌桶算法）"""

    def __init__(self, rate: int, per: float = 60.0):
        """
        rate: 速率（多少次请求）
        per: 时间窗口（秒）
        例如：rate=100, per=60 表示每分钟 100 次请求
        """
        self.rate = rate
        self.per = per
        self.allowance = rate  # 当前允许的请求数
        self.last_check = time.time()

    async def acquire(self):
        """获取令牌（阻塞直到有可用令牌）"""
        while True:
            # 计算时间差
            now = time.time()
            time_passed = now - self.last_check

            # 补充令牌
            self.allowance += time_passed * (self.rate / self.per)

            # 限制最大令牌数
            if self.allowance > self.rate:
                self.allowance = self.rate

            # 更新最后检查时间
            self.last_check = now

            # 检查是否有可用令牌
            if self.allowance >= 1.0:
                self.allowance -= 1.0
                return

            # 没有令牌，等待
            sleep_time = (1.0 - self.allowance) / (self.rate / self.per)
            await asyncio.sleep(sleep_time)


# ═══════════════════════════════════════════════════════════
# 使用速率限制器
# ═══════════════════════════════════════════════════════════

# 创建速率限制器（每分钟 100 次请求）
limiter = RateLimiter(rate=100, per=60.0)

async def call_with_rate_limit(url: str):
    """调用外部 API（受速率限制）"""

    # 等待令牌
    await limiter.acquire()

    # 发送请求
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(url)
        return response.json()


# 批量请求（自动限制速率）
async def batch_requests(urls: list[str]):
    """批量请求（自动速率限制）"""
    tasks = [call_with_rate_limit(url) for url in urls]
    return await asyncio.gather(*tasks)
```

---

## 🎨 FastAPI 集成外部 API

### 完整示例：天气查询服务

```python
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import httpx
from typing import Optional

app = FastAPI()

# ═══════════════════════════════════════════════════════════
# 1. 定义模型
# ═══════════════════════════════════════════════════════════

class WeatherRequest(BaseModel):
    city: str
    country: Optional[str] = None

class WeatherResponse(BaseModel):
    city: str
    temperature: float
    description: str
    humidity: int

# ═══════════════════════════════════════════════════════════
# 2. 外部 API 客户端（Application-scoped）
# ═══════════════════════════════════════════════════════════

class WeatherAPIClient:
    """天气 API 客户端"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.client: Optional[httpx.AsyncClient] = None

    async def start(self):
        """启动客户端"""
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )

    async def stop(self):
        """停止客户端"""
        if self.client:
            await self.client.aclose()

    async def get_weather(self, city: str, country: Optional[str] = None) -> dict:
        """获取天气信息"""

        # 构建查询参数
        query = city
        if country:
            query = f"{city},{country}"

        # 调用外部 API
        response = await self.client.get(
            f"{self.base_url}/weather",
            params={
                "q": query,
                "appid": self.api_key,
                "units": "metric"
            }
        )

        # 检查响应
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"天气 API 错误：{response.text}"
            )

        data = response.json()

        # 解析响应
        return {
            "city": data["name"],
            "temperature": data["main"]["temp"],
            "description": data["weather"][0]["description"],
            "humidity": data["main"]["humidity"]
        }

# 创建全局客户端实例
weather_client = WeatherAPIClient(api_key="your-api-key")

# ═══════════════════════════════════════════════════════════
# 3. 应用生命周期管理
# ═══════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    await weather_client.start()

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理"""
    await weather_client.stop()

# ═══════════════════════════════════════════════════════════
# 4. 依赖注入
# ═══════════════════════════════════════════════════════════

def get_weather_client() -> WeatherAPIClient:
    """获取天气 API 客户端"""
    return weather_client

# ═══════════════════════════════════════════════════════════
# 5. Endpoints
# ═══════════════════════════════════════════════════════════

@app.post("/weather", response_model=WeatherResponse)
async def get_weather(
    request: WeatherRequest,
    client: WeatherAPIClient = Depends(get_weather_client)
):
    """获取天气信息"""

    try:
        weather_data = await client.get_weather(
            city=request.city,
            country=request.country
        )
        return WeatherResponse(**weather_data)

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="请求超时")
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"外部 API 错误：{e}")
```

---

## 🔐 API 密钥管理

### 环境变量存储密钥

```python
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """应用配置"""

    # 外部 API 密钥
    WEATHER_API_KEY: str
    STRIPE_API_KEY: str
    SENDGRID_API_KEY: str

    class Config:
        env_file = ".env"

# 加载配置
settings = Settings()

# 使用
weather_client = WeatherAPIClient(api_key=settings.WEATHER_API_KEY)
```

---

## 🎯 小实验：自己动手

### 实验 1：基本 HTTP 请求

```python
import httpx

async def basic_request():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.github.com/users/python")
        print(response.json())

asyncio.run(basic_request())
```

---

### 实验 2：超时和重试

```python
import httpx
import asyncio

async def request_with_timeout_and_retry():
    timeout = httpx.Timeout(5.0)

    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get("https://httpbin.org/delay/10")
                return response.json()

        except httpx.TimeoutException:
            print(f"超时，重试 {attempt + 1}/3")
            await asyncio.sleep(1)

    return {"error": "请求失败"}

asyncio.run(request_with_timeout_and_retry())
```

---

## 📚 检查理解

回答这些问题来测试你的理解：

1. **为什么用 httpx 而不是 requests？**
   - 提示：异步支持、HTTP/2

2. **为什么需要超时控制？**
   - 提示：防止请求一直等待，保护应用

3. **何时应该重试请求？**
   - 提示：5xx 错误、超时、网络错误

4. **什么是熔断器模式？**
   - 提示：保护应用不被外部故障拖垮

5. **为什么需要速率限制？**
   - 提示：遵守第三方 API 限制

---

## 🚀 下一步

现在你已经掌握了外部 API 集成，接下来：

1. **学习监控和日志**：`notes/04_monitoring.md`
2. **查看实际代码**：`examples/03_external_api.py`

**记住**：外部 API 调用必须做好容错处理（超时、重试、熔断），否则会成为系统的短板！**

---

**费曼技巧总结**：
- ✅ 餐厅供应商类比
- ✅ 超时控制的重要性
- ✅ 重试策略（固定延迟、指数退避）
- ✅ 熔断器模式（电路熔断器类比）
- ✅ 速率限制器（令牌桶算法）
- ✅ 完整的 FastAPI 集成示例
