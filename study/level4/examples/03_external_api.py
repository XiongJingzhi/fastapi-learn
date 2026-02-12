"""
03. 外部 API 调用 - External API Integration
=============================================

这个示例展示了如何在 FastAPI 中调用外部 API，包括：

架构原则：
- 超时控制：快速失败
- 重试策略：指数退避
- 熔断器：防止级联故障
- 速率限制：保护下游服务
- 幂等性：安全重试

运行要求：
- pip install httpx
- 外部 API（本示例使用 mock）

生产环境建议：
- 使用连接池
- 配置合理的超时
- 启用重试和熔断
- 监控 API 调用
"""

import asyncio
import logging
import random
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import httpx
from fastapi import FastAPI, HTTPException, status, Depends
from pydantic import BaseModel, Field

# ═══════════════════════════════════════════════════════════════════
# 日志配置
# ═══════════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════
# 熔断器模式
# ═══════════════════════════════════════════════════════════════════


class CircuitState(str, Enum):
    """熔断器状态"""
    CLOSED = "closed"      # 正常状态
    OPEN = "open"          # 熔断状态
    HALF_OPEN = "half_open"  # 半开状态（试探）


@dataclass
class CircuitBreakerConfig:
    """熔断器配置"""
    failure_threshold: int = 5      # 失败阈值
    success_threshold: int = 2       # 恢复阈值
    timeout: int = 60               # 熔断超时（秒）
    expected_exception: Exception = Exception


class CircuitBreakerError(Exception):
    """熔断器异常"""
    pass


class CircuitBreaker:
    """
    熔断器

    场景：
        下游服务故障时，快速失败而非一直等待

        故障场景：
        1. 外部 API 响应慢（每个请求 30 秒）
        2. 不使用熔断：1000 请求 × 30 秒 = 系统挂起
        3. 使用熔断：前 5 个请求失败后，直接返回错误

    状态转换：
        CLOSED（正常）
            → 失败数达到阈值 → OPEN（熔断）
        OPEN（熔断）
            → 超时后 → HALF_OPEN（试探）
        HALF_OPEN（试探）
            → 成功数达到阈值 → CLOSED（恢复）
            → 失败 → OPEN（再次熔断）

    使用示例：
        @circuit_breaker(failure_threshold=5, timeout=60)
        async def call_external_api():
            return await httpx.get("https://api.example.com")
    """

    def __init__(
        self,
        config: CircuitBreakerConfig,
        name: str = "default",
    ):
        self.config = config
        self.name = name

        # 状态
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.opened_at: Optional[datetime] = None

    async def __aenter__(self):
        """进入熔断器"""
        if not self._can_execute():
            raise CircuitBreakerError(
                f"Circuit breaker '{self.name}' is {self.state.value}"
            )
        return self

    async def __aexit__(self, exc_type, exc_val, tb):
        """退出熔断器"""
        if exc_type is not None:
            # 执行失败
            self._on_failure()
        else:
            # 执行成功
            self._on_success()

    def _can_execute(self) -> bool:
        """检查是否可以执行"""
        if self.state == CircuitState.CLOSED:
            return True

        elif self.state == CircuitState.OPEN:
            # 检查是否超时
            if self.opened_at and datetime.utcnow() > self.opened_at + timedelta(seconds=self.config.timeout):
                logger.info(f"[CircuitBreaker] {self.name}: 超时，进入半开状态")
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                return True
            return False

        elif self.state == CircuitState.HALF_OPEN:
            return True

        return False

    def _on_failure(self):
        """处理失败"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        if self.state == CircuitState.HALF_OPEN:
            # 半开状态失败，重新进入熔断
            logger.warning(f"[CircuitBreaker] {self.name}: 半开状态失败，重新熔断")
            self.state = CircuitState.OPEN
            self.opened_at = datetime.utcnow()

        elif self.failure_count >= self.config.failure_threshold:
            # 达到失败阈值，进入熔断
            logger.error(
                f"[CircuitBreaker] {self.name}: 失败数 {self.failure_count}，"
                f"达到阈值 {self.config.failure_threshold}，触发熔断"
            )
            self.state = CircuitState.OPEN
            self.opened_at = datetime.utcnow()

    def _on_success(self):
        """处理成功"""
        self.failure_count = 0
        self.last_failure_time = None

        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1

            if self.success_count >= self.config.success_threshold:
                # 达到成功阈值，恢复
                logger.info(f"[CircuitBreaker] {self.name}: 成功数 {self.success_count}，恢复")
                self.state = CircuitState.CLOSED

    def get_state(self) -> Dict[str, Any]:
        """获取当前状态"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
        }


def circuit_breaker(
    failure_threshold: int = 5,
    success_threshold: int = 2,
    timeout: int = 60,
    name: str = "default",
):
    """
    熔断器装饰器

    参数：
        failure_threshold: 失败阈值
        success_threshold: 成功阈值（用于恢复）
        timeout: 熔断超时（秒）
        name: 熔断器名称
    """
    config = CircuitBreakerConfig(
        failure_threshold=failure_threshold,
        success_threshold=success_threshold,
        timeout=timeout,
    )
    breaker = CircuitBreaker(config, name)

    def decorator(func):
        async def wrapper(*args, **kwargs):
            async with breaker:
                return await func(*args, **kwargs)
        return wrapper

    # 附加熔断器实例到装饰器，便于查询状态
    decorator.breaker = breaker
    return decorator


# ═══════════════════════════════════════════════════════════════════
# 重试策略
# ═══════════════════════════════════════════════════════════════════


class RetryStrategy:
    """
    重试策略

    场景：
        临时性故障（网络抖动、服务重启）

    策略：
        - 指数退避：2^0, 2^1, 2^2, 2^3 秒
        - 最大重试次数
        - 只重试幂等操作

    注意事项：
        - 非幂等操作不应该重试
        - 要有合理的超时限制
    """

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter  # 添加随机抖动，避免雷鸣羊群效应

    async def execute(self, func, *args, **kwargs):
        """
        执行带重试的函数

        流程：
            1. 尝试执行函数
            2. 失败则计算延迟
            3. 等待延迟
            4. 重试
            5. 达到最大重试次数则抛出异常
        """
        last_exception = None

        for attempt in range(self.max_attempts):
            try:
                # 执行函数
                result = await func(*args, **kwargs)

                # 成功
                if attempt > 0:
                    logger.info(f"[Retry] 第 {attempt + 1} 次尝试成功")

                return result

            except Exception as e:
                last_exception = e

                # 是否还有重试机会
                if attempt < self.max_attempts - 1:
                    # 计算延迟
                    delay = self._calculate_delay(attempt)

                    logger.warning(
                        f"[Retry] 第 {attempt + 1} 次尝试失败: {e}, "
                        f"{delay:.2f} 秒后重试"
                    )

                    # 等待后重试
                    await asyncio.sleep(delay)
                else:
                    # 达到最大重试次数
                    logger.error(
                        f"[Retry] 已达到最大重试次数 {self.max_attempts}，放弃"
                    )
                    raise last_exception

    def _calculate_delay(self, attempt: int) -> float:
        """
        计算延迟时间（指数退避 + 抖动）

        公式：
            delay = min(base_delay * exponential_base ^ attempt, max_delay)

        抖动（±25%）：
            避免多个请求同时重试，造成雷鸣羊群效应
        """
        delay = min(
            self.base_delay * (self.exponential_base ** attempt),
            self.max_delay
        )

        if self.jitter:
            # 添加 ±25% 的随机抖动
            import random
            delay = delay * random.uniform(0.75, 1.25)

        return delay


# ═══════════════════════════════════════════════════════════════════
# 速率限制器
# ═══════════════════════════════════════════════════════════════════


class RateLimiter:
    """
    速率限制器

    场景：
        保护下游服务不被打爆

    算法：
        令牌桶算法

    参数：
        rate: 每秒请求数
        burst: 突发容量
    """

    def __init__(self, rate: float = 10.0, burst: int = 20):
        self.rate = rate
        self.burst = burst
        self.tokens = burst
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> bool:
        """
        获取令牌

        返回：
            True: 成功获取
            False: 令牌不足
        """
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_update

            # 补充令牌
            self.tokens = min(
                self.burst,
                self.tokens + elapsed * self.rate
            )
            self.last_update = now

            # 检查令牌
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    async def wait(self, tokens: int = 1):
        """
        等待令牌（阻塞）
        """
        while not await self.acquire(tokens):
            await asyncio.sleep(0.1)


# ═══════════════════════════════════════════════════════════════════
# Mock 外部 API
# ═══════════════════════════════════════════════════════════════════


class MockExternalAPI:
    """
    模拟外部 API

    模拟场景：
        - 正常响应
        - 超时
        - 服务器错误
        - 速率限制
    """

    def __init__(self, failure_rate: float = 0.2):
        self.failure_rate = failure_rate
        self.request_count = 0

    async def call(
        self,
        endpoint: str,
        method: str = "GET",
        data: Optional[Dict] = None,
    ) -> Dict:
        """模拟 API 调用"""
        self.request_count += 1

        # 模拟延迟
        await asyncio.sleep(random.uniform(0.1, 0.5))

        # 模拟失败
        if random.random() < self.failure_rate:
            # 随机失败
            failure_type = random.choice(["timeout", "500", "429"])

            if failure_type == "timeout":
                raise TimeoutError("Request timeout")

            elif failure_type == "500":
                raise HTTPException(status_code=500, detail="Internal server error")

            elif failure_type == "429":
                raise HTTPException(status_code=429, detail="Rate limit exceeded")

        # 成功响应
        return {
            "endpoint": endpoint,
            "method": method,
            "data": data,
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
        }


mock_api = MockExternalAPI(failure_rate=0.3)

# ═══════════════════════════════════════════════════════════════════
# HTTP 客户端（带弹性）
# ═══════════════════════════════════════════════════════════════════


class ResilientHTTPClient:
    """
    弹性 HTTP 客户端

    特性：
        - 超时控制
        - 重试策略
        - 熔断器
        - 速率限制
        - 连接池
    """

    def __init__(
        self,
        base_url: str,
        timeout: float = 10.0,
        max_retries: int = 3,
        rate_limit: float = 10.0,
    ):
        self.base_url = base_url
        self.timeout = timeout

        # httpx 客户端（带连接池）
        self.client = httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(
                max_connections=100,
                max_keepalive_connections=20,
            ),
        )

        # 重试策略
        self.retry_strategy = RetryStrategy(
            max_attempts=max_retries,
            base_delay=1.0,
        )

        # 速率限制器
        self.rate_limiter = RateLimiter(rate=rate_limit)

        # 熔断器
        self.circuit_breaker = CircuitBreaker(
            config=CircuitBreakerConfig(
                failure_threshold=5,
                success_threshold=2,
                timeout=60,
            ),
            name=base_url,
        )

    async def get(self, endpoint: str, **kwargs) -> Dict:
        """GET 请求（带弹性）"""
        return await self._request("GET", endpoint, **kwargs)

    async def post(self, endpoint: str, **kwargs) -> Dict:
        """POST 请求（带弹性）"""
        return await self._request("POST", endpoint, **kwargs)

    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """
        发送请求（带弹性）

        流程：
            1. 速率限制检查
            2. 熔断器检查
            3. 重试执行
        """
        # 1. 速率限制
        await self.rate_limiter.wait()

        # 2. 熔断器
        async def do_request():
            response = await self.client.request(method, endpoint, **kwargs)
            response.raise_for_status()
            return response.json()

        # 3. 重试 + 熔断
        async with self.circuit_breaker:
            result = await self.retry_strategy.execute(do_request)
            return result

    async def close(self):
        """关闭客户端"""
        await self.client.aclose()


# ═══════════════════════════════════════════════════════════════════
# 业务模型
# ═══════════════════════════════════════════════════════════════════


class PaymentRequest(BaseModel):
    """支付请求"""
    amount: float = Field(..., gt=0)
    currency: str = Field(default="USD", pattern="^[A-Z]{3}$")
    user_id: int
    order_id: int


class PaymentResponse(BaseModel):
    """支付响应"""
    payment_id: str
    status: str
    amount: float
    currency: str
    processed_at: datetime


class WeatherRequest(BaseModel):
    """天气查询请求"""
    city: str
    country: str = Field(default="US", min_length=2, max_length=2)


class WeatherResponse(BaseModel):
    """天气响应"""
    city: str
    temperature: float
    condition: str
    humidity: int
    timestamp: datetime


# ═══════════════════════════════════════════════════════════════════
# API 服务（集成外部 API）
# ═══════════════════════════════════════════════════════════════════


class PaymentService:
    """
    支付服务（调用外部支付 API）

    展示：
        - 超时控制
        - 重试策略
        - 幂等性
    """

    def __init__(self):
        self.retry_strategy = RetryStrategy(
            max_attempts=3,
            base_delay=1.0,
        )

    async def process_payment(self, request: PaymentRequest) -> PaymentResponse:
        """
        处理支付

        外部 API 可能失败，需要重试

        注意：
            支付操作必须是幂等的（重复调用不重复扣款）
        """
        logger.info(f"[Payment] 处理支付: 订单 {request.order_id}, 金额 {request.amount}")

        async def do_payment():
            # 调用外部支付 API
            result = await mock_api.call(
                f"/payments",
                method="POST",
                data=request.dict(),
            )

            return PaymentResponse(
                payment_id=str(random.randint(100000, 999999)),
                status="completed",
                amount=request.amount,
                currency=request.currency,
                processed_at=datetime.utcnow(),
            )

        # 带重试执行
        try:
            response = await self.retry_strategy.execute(do_payment)
            logger.info(f"[Payment] ✓ 支付成功: {response.payment_id}")
            return response

        except Exception as e:
            logger.error(f"[Payment] ✗ 支付失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"支付服务暂时不可用: {str(e)}",
            )


class WeatherService:
    """
    天气服务（调用外部天气 API）

    展示：
        - 熔断器
        - 缓存
        - 降级
    """

    def __init__(self):
        # 创建熔断器
        self.circuit_breaker = CircuitBreaker(
            config=CircuitBreakerConfig(
                failure_threshold=3,
                success_threshold=2,
                timeout=30,
            ),
            name="weather_api",
        )

        # 缓存
        self._cache: Dict[str, tuple] = {}

    async def get_weather(self, request: WeatherRequest) -> WeatherResponse:
        """
        获取天气

        策略：
            1. 先查缓存
            2. 缓存未命中则调用 API（带熔断）
            3. API 失败则返回降级数据
        """
        cache_key = f"{request.city},{request.country}"

        # 1. 查缓存
        if cache_key in self._cache:
            cached_data, cached_at = self._cache[cache_key]
            age = (datetime.utcnow() - cached_at).total_seconds()

            if age < 600:  # 10 分钟缓存
                logger.info(f"[Weather] 缓存命中: {cache_key}")
                return cached_data

        # 2. 调用外部 API（带熔断）
        try:
            async with self.circuit_breaker:
                logger.info(f"[Weather] 调用 API: {cache_key}")

                result = await mock_api.call(
                    f"/weather?city={request.city}&country={request.country}",
                )

                response = WeatherResponse(
                    city=request.city,
                    temperature=random.uniform(10, 30),
                    condition=random.choice(["Sunny", "Cloudy", "Rainy"]),
                    humidity=random.randint(40, 80),
                    timestamp=datetime.utcnow(),
                )

                # 写入缓存
                self._cache[cache_key] = (response, datetime.utcnow())

                return response

        except CircuitBreakerError:
            logger.warning(f"[Weather] 熔断器打开，使用降级数据")
            # 降级：返回缓存的旧数据或默认值
            if cache_key in self._cache:
                cached_data, _ = self._cache[cache_key]
                return cached_data

            return WeatherResponse(
                city=request.city,
                temperature=20.0,
                condition="Unknown",
                humidity=50,
                timestamp=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"[Weather] API 调用失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="天气服务暂时不可用",
            )


# ═══════════════════════════════════════════════════════════════════
# FastAPI 应用
# ═══════════════════════════════════════════════════════════════════


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动
    logger.info("[App] 应用启动")
    yield
    # 关闭
    logger.info("[App] 应用关闭")


app = FastAPI(
    title="外部 API 集成示例",
    description="展示外部 API 调用的最佳实践",
    version="1.0.0",
    lifespan=lifespan,
)

# 服务实例
payment_service = PaymentService()
weather_service = WeatherService()

# ═══════════════════════════════════════════════════════════════════
# API 端点
# ═══════════════════════════════════════════════════════════════════


@app.get("/")
async def root():
    """健康检查"""
    return {
        "message": "外部 API 集成示例",
        "status": "running",
    }


@app.post("/payments", response_model=PaymentResponse)
async def create_payment(request: PaymentRequest):
    """
    创建支付

    特性：
        - 重试策略
        - 超时控制
        - 幂等性保证
    """
    return await payment_service.process_payment(request)


@app.get("/weather", response_model=WeatherResponse)
async def get_weather(request: WeatherRequest):
    """
    获取天气

    特性：
        - 熔断器
        - 缓存
        - 服务降级
    """
    return await weather_service.get_weather(request)


@app.get("/circuit-breaker/state")
async def get_circuit_breaker_state():
    """获取熔断器状态"""
    return weather_service.circuit_breaker.get_state()


@app.post("/circuit-breaker/reset")
async def reset_circuit_breaker():
    """重置熔断器"""
    weather_service.circuit_breaker.state = CircuitState.CLOSED
    weather_service.circuit_breaker.failure_count = 0
    weather_service.circuit_breaker.opened_at = None
    return {"message": "熔断器已重置"}


# ═══════════════════════════════════════════════════════════════════
# 演示和测试
# ═══════════════════════════════════════════════════════════════════


async def demo_retry_strategy():
    """演示重试策略"""
    print("\n" + "="*60)
    print("演示 1: 重试策略")
    print("="*60)

    async def failing_operation():
        """会失败的操作"""
        if random.random() < 0.5:
            raise Exception("随机失败")
        return "成功！"

    retry = RetryStrategy(max_attempts=5)

    try:
        result = await retry.execute(failing_operation)
        print(f"✓ 操作成功: {result}")
    except Exception as e:
        print(f"✗ 操作失败（已达最大重试次数）: {e}")


async def demo_circuit_breaker():
    """演示熔断器"""
    print("\n" + "="*60)
    print("演示 2: 熔断器")
    print("="*60)

    breaker = CircuitBreaker(
        config=CircuitBreakerConfig(
            failure_threshold=3,
            success_threshold=2,
            timeout=5,
        ),
        name="demo",
    )

    async def failing_operation():
        """会失败的操作"""
        raise Exception("操作失败")

    print("\n1. 前 3 次失败（触发熔断）")
    for i in range(3):
        try:
            async with breaker:
                await failing_operation()
        except CircuitBreakerError:
            print(f"   第 {i+1} 次: 熔断器已打开")
        except Exception:
            print(f"   第 {i+1} 次: 操作失败")

    print(f"\n熔断器状态: {breaker.get_state()}")

    print("\n2. 第 4 次尝试（熔断中，直接拒绝）")
    try:
        async with breaker:
            await failing_operation()
    except CircuitBreakerError as e:
        print(f"   第 4 次: {e}")

    print("\n3. 等待超时后重试")
    await asyncio.sleep(6)

    print("\n4. 第 5 次尝试（半开状态）")
    try:
        async with breaker:
            print("   操作成功！")
    except Exception as e:
        print(f"   失败: {e}")

    print(f"\n熔断器状态: {breaker.get_state()}")


async def demo_rate_limiter():
    """演示速率限制"""
    print("\n" + "="*60)
    print("演示 3: 速率限制")
    print("="*60)

    limiter = RateLimiter(rate=5.0, burst=10)

    print("\n尝试发送 20 个请求（速率限制 5/秒）")
    start = time.monotonic()

    for i in range(20):
        await limiter.wait()
        elapsed = time.monotonic() - start
        print(f"   请求 {i+1}: {elapsed:.2f}s")

    total_time = time.monotonic() - start
    print(f"\n总耗时: {total_time:.2f}s")
    print(f"平均速率: {20/total_time:.2f} 请求/秒")


async def demo_external_api_integration():
    """演示外部 API 集成"""
    print("\n" + "="*60)
    print("演示 4: 外部 API 集成")
    print("="*60)

    service = PaymentService()

    # 成功的支付
    print("\n1. 创建支付（会重试）")
    request = PaymentRequest(
        amount=100.0,
        currency="USD",
        user_id=1,
        order_id=1001,
    )

    try:
        response = await service.process_payment(request)
        print(f"✓ 支付成功: {response.payment_id}")
    except HTTPException as e:
        print(f"✗ 支付失败: {e.detail}")


async def main():
    """运行所有演示"""
    print("\n🚀 外部 API 集成示例")

    try:
        await demo_retry_strategy()
        await demo_circuit_breaker()
        await demo_rate_limiter()
        await demo_external_api_integration()

        print("\n" + "="*60)
        print("✅ 所有演示完成！")
        print("="*60)
        print("\n提示：运行 FastAPI 应用体验完整功能：")
        print("  uvicorn study.level4.examples.03_external_api:app --reload")
        print("\nAPI 端点：")
        print("  POST   /payments                    # 创建支付（带重试）")
        print("  GET    /weather                     # 获取天气（带熔断和缓存）")
        print("  GET    /circuit-breaker/state       # 查看熔断器状态")
        print("  POST   /circuit-breaker/reset       # 重置熔断器")

    except Exception as e:
        logger.error(f"演示失败: {e}")
        print(f"\n❌ 错误: {e}")


if __name__ == "__main__":
    asyncio.run(main())
