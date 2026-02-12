"""
05. 弹性设计 - Resilience Patterns
===================================

这个示例展示了生产环境中的弹性设计模式。

架构原则：
- 失败是常态：假设所有外部依赖都可能失败
- 快速失败：超时优于挂起
- 优雅降级：部分功能可用总比全部不可用好
- 幂等性：安全重试

关键模式：
    1. 重试：指数退避
    2. 超时：防止挂起
    3. 熔断：防止级联故障
    4. 降级：提供备选方案
    5. 隔离：舱壁隔离
    6. 幂等：安全重试

运行要求：
- 无特殊依赖（使用 mock）

生产环境建议：
- 使用 Hystrix、Resilience4j 等库
- 配置合理的超时和重试
- 实现多级降级
- 监控弹性指标
"""

import asyncio
import random
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional, TypeVar

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

# ═══════════════════════════════════════════════════════════════════
# 日志配置
# ═══════════════════════════════════════════════════════════════════

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════
# 舱壁隔离（Bulkhead Pattern）
# ═══════════════════════════════════════════════════════════════════


class BulkheadIsolationError(Exception):
    """舱壁隔离异常：信号量已满"""
    pass


class Bulkhead:
    """
    舱壁隔离（Bulkhead Isolation）

    场景：
        防止一个慢服务拖累整个应用

        问题场景：
        - 数据库查询慢（5 秒）
        - 不使用隔离：100 个并发请求全部挂起，应用无响应
        - 使用隔离：最多 10 个并发查询数据库，其他请求快速失败

    实现：
        使用信号量限制并发数

    类比：
        泰坦尼克号：船舱分隔，一个漏水不会沉没整艘船
    """

    def __init__(self, max_concurrent: int, name: str = "default"):
        self.max_concurrent = max_concurrent
        self.name = name
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.active_count = 0
        self.rejected_count = 0

    async def __aenter__(self):
        """进入隔离区"""
        acquired = await self.semaphore.acquire()

        if not acquired:
            self.rejected_count += 1
            logger.warning(f"[Bulkhead] {self.name}: 并发数已满，拒绝请求")
            raise BulkheadIsolationError(f"并发数已达上限 {self.max_concurrent}")

        self.active_count += 1
        logger.debug(f"[Bulkhead] {self.name}: 活跃数 {self.active_count}/{self.max_concurrent}")

        return self

    async def __aexit__(self, exc_type, exc_val, tb):
        """退出隔离区"""
        self.active_count -= 1
        self.semaphore.release()
        logger.debug(f"[Bulkhead] {self.name}: 活跃数 {self.active_count}/{self.max_concurrent}")

    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "name": self.name,
            "max_concurrent": self.max_concurrent,
            "active_count": self.active_count,
            "rejected_count": self.rejected_count,
        }


# ═══════════════════════════════════════════════════════════════════
# 超时控制
# ═══════════════════════════════════════════════════════════════════


class TimeoutError(Exception):
    """超时异常"""
    pass


async def with_timeout(coro: Awaitable, timeout: float) -> Any:
    """
    超时控制

    场景：
        防止请求挂起

    问题场景：
        - 外部 API 无响应
        - 不设置超时：请求永远挂起
        - 设置超时：3 秒后返回错误

    原则：
        快速失败优于挂起
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        raise TimeoutError(f"操作超时（{timeout}秒）")


# ═══════════════════════════════════════════════════════════════════
# 重试策略（指数退避）
# ═══════════════════════════════════════════════════════════════════


T = TypeVar("T")


class RetryPolicy:
    """
    重试策略

    算法：
        指数退避（Exponential Backoff）

        延迟公式：
            delay = base_delay * (backoff_factor ^ attempt)

        示例：
            attempt 0: 1s
            attempt 1: 2s
            attempt 2: 4s
            attempt 3: 8s

    添加抖动（Jitter）：
        避免雷鸣羊群效应

        问题：多个请求同时失败，同时重试，造成新的冲击
        解决：添加随机偏移（±25%）
    """

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        jitter: bool = True,
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter

    async def execute(self, func: Callable[[], Awaitable[T]]) -> T:
        """执行带重试的函数"""
        last_exception = None

        for attempt in range(self.max_attempts):
            try:
                # 执行函数
                result = await func()

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
                        f"{delay:.2f}秒后重试"
                    )

                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"[Retry] 已达最大重试次数 {self.max_attempts}，放弃"
                    )

        raise last_exception

    def _calculate_delay(self, attempt: int) -> float:
        """计算延迟时间（指数退避 + 抖动）"""
        delay = min(
            self.base_delay * (self.backoff_factor ** attempt),
            self.max_delay
        )

        if self.jitter:
            # 添加 ±25% 的随机抖动
            delay = delay * random.uniform(0.75, 1.25)

        return delay


# ═══════════════════════════════════════════════════════════════════
# 服务降级
# ═══════════════════════════════════════════════════════════════════


class DegradationLevel(str, Enum):
    """降级级别"""
    NORMAL = "normal"          # 正常
    DEGRADED = "degraded"      # 部分降级
    MINIMAL = "minimal"        # 最小服务
    OFFLINE = "offline"        # 完全离线


class FallbackResult:
    """
    降级结果

    场景：
        外部服务不可用时，提供备选方案

    降级策略：
        1. 使用缓存数据
        2. 返回默认值
        3. 返回简化数据
        4. 返回错误提示
    """

    def __init__(
        self,
        data: Any,
        is_fallback: bool = True,
        reason: str = "",
    ):
        self.data = data
        self.is_fallback = is_fallback
        self.reason = reason

    def __repr__(self):
        if self.is_fallback:
            return f"FallbackResult(data={self.data}, reason='{self.reason}')"
        return f"Result(data={self.data})"


async def with_fallback(
    primary: Callable[[], Awaitable[T]],
    fallback: Callable[[], Awaitable[T]],
    exceptions: tuple = (Exception,),
) -> T:
    """
    带降级的执行

    流程：
        1. 尝试执行主逻辑
        2. 失败则执行降级逻辑
    """
    try:
        return await primary()
    except exceptions as e:
        logger.warning(f"[Fallback] 主逻辑失败: {e}，使用降级方案")
        return await fallback()


# ═══════════════════════════════════════════════════════════════════
# 幂等性保证
# ═══════════════════════════════════════════════════════════════════


class IdempotencyKey:
    """
    幂等性键

    场景：
        确保重试不会重复执行

    问题：
        客户端请求超时，不确定是否成功
        - 不使用幂等：重试导致重复扣款
        - 使用幂等：重试返回之前的结果

    实现：
        使用幂等键记录请求结果
    """

    def __init__(self):
        self._store: Dict[str, Any] = {}

    async def process(
        self,
        key: str,
        func: Callable[[], Awaitable[T]],
        expire_seconds: int = 3600,
    ) -> T:
        """
        幂等处理

        流程：
            1. 检查幂等键是否存在
            2. 存在则返回之前的结果
            3. 不存在则执行函数并缓存结果
        """
        # 1. 检查是否已处理
        if key in self._store:
            logger.info(f"[Idempotency] 幂等键已存在: {key}")
            result = self._store[key]
            return result["data"]

        # 2. 执行函数
        logger.info(f"[Idempotency] 首次处理: {key}")
        result = await func()

        # 3. 缓存结果
        self._store[key] = {
            "data": result,
            "timestamp": datetime.utcnow(),
        }

        # 4. 设置过期（可选）
        # 真实环境应使用 Redis

        return result

    def clear(self):
        """清除所有幂等键"""
        self._store.clear()


idempotency_store = IdempotencyKey()


# ═══════════════════════════════════════════════════════════════════
# Mock 外部服务
# ═══════════════════════════════════════════════════════════════════


class ExternalService:
    """
    外部服务（模拟）

    模拟场景：
        - 正常响应
        - 延迟
        - 错误
        - 超时
    """

    def __init__(self, failure_rate: float = 0.3):
        self.failure_rate = failure_rate
        self.request_count = 0

    async def call(self, operation: str) -> Dict:
        """调用服务"""
        self.request_count += 1

        # 模拟网络延迟
        await asyncio.sleep(random.uniform(0.1, 0.5))

        # 模拟失败
        if random.random() < self.failure_rate:
            failure_type = random.choice(["timeout", "error", "slow"])

            if failure_type == "timeout":
                # 模拟超时（慢响应）
                await asyncio.sleep(5.0)
                return {"status": "timeout"}

            elif failure_type == "error":
                raise Exception("服务暂时不可用")

            elif failure_type == "slow":
                # 模拟慢响应（2 秒）
                await asyncio.sleep(2.0)

        # 正常响应
        return {
            "operation": operation,
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
        }


external_service = ExternalService(failure_rate=0.3)

# ═══════════════════════════════════════════════════════════════════
# 弹性装饰器组合
# ═══════════════════════════════════════════════════════════════════


def resilient(
    timeout: Optional[float] = None,
    max_retries: int = 3,
    bulkhead_max: Optional[int] = None,
    fallback_func: Optional[Callable] = None,
):
    """
    弹性装饰器（组合多种模式）

    参数：
        timeout: 超时时间（秒）
        max_retries: 最大重试次数
        bulkhead_max: 并发限制
        fallback_func: 降级函数

    使用示例：
        @resilient(timeout=3.0, max_retries=3, bulkhead_max=10)
        async def call_external_api():
            return await external_service.call("test")
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 1. 舱壁隔离
            if bulkhead_max:
                bulkhead = Bulkhead(bulkhead_max, func.__name__)

            # 2. 重试策略
            retry_policy = RetryPolicy(max_attempts=max_retries)

            # 定义执行逻辑
            async def execute():
                # 超时控制
                if timeout:
                    return await with_timeout(func(*args, **kwargs), timeout)
                else:
                    return await func(*args, **kwargs)

            # 3. 执行（带重试）
            try:
                if bulkhead_max:
                    async with bulkhead:
                        result = await retry_policy.execute(execute)
                else:
                    result = await retry_policy.execute(execute)

                return result

            except Exception as e:
                # 4. 降级
                if fallback_func:
                    logger.warning(f"[Resilient] 主逻辑失败，使用降级: {e}")
                    return await fallback_func(*args, **kwargs)
                raise

        return wrapper
    return decorator


# ═══════════════════════════════════════════════════════════════════
# 业务服务
# ═══════════════════════════════════════════════════════════════════


class ProductService:
    """
    产品服务（带弹性）

    展示：
        - 舱壁隔离
        - 超时控制
        - 重试策略
        - 服务降级
    """

    def __init__(self):
        self.bulkhead = Bulkhead(max_concurrent=10, name="product_service")
        self.retry_policy = RetryPolicy(max_attempts=3)
        self._cache = {
            1: {"id": 1, "name": "Laptop", "price": 999.99, "in_stock": True},
            2: {"id": 2, "name": "Mouse", "price": 29.99, "in_stock": True},
        }

    async def get_product(self, product_id: int) -> Dict:
        """
        获取产品（带弹性）

        弹性策略：
            1. 先查缓存（降级）
            2. 缓存未命中则调用外部服务
            3. 使用舱壁隔离
            4. 设置超时
            5. 失败则返回缓存数据
        """
        logger.info(f"[ProductService] 获取产品: {product_id}")

        # 1. 先查缓存
        if product_id in self._cache:
            logger.info(f"[ProductService] 缓存命中: {product_id}")
            return self._cache[product_id]

        # 2. 调用外部服务（带弹性）
        async with self.bulkhead:
            try:
                result = await with_timeout(
                    external_service.call(f"product_{product_id}"),
                    timeout=2.0
                )
                return result

            except TimeoutError:
                logger.warning(f"[ProductService] 外部服务超时，使用降级")
                # 降级：返回默认产品
                return {
                    "id": product_id,
                    "name": "Unknown Product",
                    "price": 0.0,
                    "in_stock": False,
                    "_degraded": True,
                }

            except Exception as e:
                logger.error(f"[ProductService] 外部服务失败: {e}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="产品服务暂时不可用",
                )

    async def get_product_with_retry(self, product_id: int) -> Dict:
        """获取产品（带重试）"""
        return await self.retry_policy.execute(
            lambda: self.get_product(product_id)
        )


class OrderService:
    """
    订单服务（带幂等性）

    展示：
        - 幂等性保证
        - 重试安全
    """

    def __init__(self):
        self.idempotency = IdempotencyKey()

    async def create_order(
        self,
        user_id: int,
        product_id: int,
        amount: float,
        idempotency_key: str,
    ) -> Dict:
        """
        创建订单（幂等）

        幂等性保证：
            - 相同的幂等键返回相同结果
            - 重试不会重复扣款
        """
        logger.info(
            f"[OrderService] 创建订单: user={user_id}, "
            f"product={product_id}, key={idempotency_key}"
        )

        # 幂等处理
        async def do_create():
            # 模拟订单创建
            order_id = random.randint(10000, 99999)

            # 模拟支付（可能失败）
            if random.random() < 0.3:
                raise Exception("支付失败")

            return {
                "order_id": order_id,
                "user_id": user_id,
                "product_id": product_id,
                "amount": amount,
                "status": "completed",
                "created_at": datetime.utcnow().isoformat(),
            }

        return await self.idempotency.process(
            idempotency_key,
            do_create,
            expire_seconds=3600,
        )


class RecommendationService:
    """
    推荐服务（多级降级）

    展示：
        - 多级降级策略
    """

    def __init__(self):
        self._user_recommendations = {
            1: ["Product A", "Product B", "Product C"],
            2: ["Product D", "Product E"],
        }

    async def get_recommendations(self, user_id: int) -> List[str]:
        """
        获取推荐（多级降级）

        降级级别：
            1. 正常：个性化推荐
            2. 一级降级：热门推荐
            3. 二级降级：空列表
        """
        logger.info(f"[RecommendationService] 获取推荐: user={user_id}")

        # 正常：个性化推荐
        if user_id in self._user_recommendations:
            try:
                # 模拟外部推荐服务
                result = await external_service.call(f"recommend_{user_id}")
                return self._user_recommendations[user_id]
            except Exception as e:
                logger.warning(f"[RecommendationService] 个性化推荐失败: {e}")

        # 一级降级：热门推荐
        logger.info(f"[RecommendationService] 使用热门推荐（降级）")
        return ["Popular Product 1", "Popular Product 2", "Popular Product 3"]


# ═══════════════════════════════════════════════════════════════════
# 业务模型
# ═══════════════════════════════════════════════════════════════════


class CreateOrderRequest(BaseModel):
    """创建订单请求"""
    user_id: int = Field(..., gt=0)
    product_id: int = Field(..., gt=0)
    amount: float = Field(..., gt=0)
    idempotency_key: str = Field(..., min_length=1)


class CreateOrderResponse(BaseModel):
    """创建订单响应"""
    order_id: int
    status: str
    created_at: datetime


class ProductResponse(BaseModel):
    """产品响应"""
    id: int
    name: str
    price: float
    in_stock: bool


# ═══════════════════════════════════════════════════════════════════
# FastAPI 应用
# ═══════════════════════════════════════════════════════════════════


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("[App] 应用启动")
    yield
    logger.info("[App] 应用关闭")


app = FastAPI(
    title="弹性设计示例",
    description="展示弹性设计的最佳实践",
    version="1.0.0",
    lifespan=lifespan,
)

# 服务实例
product_service = ProductService()
order_service = OrderService()
recommendation_service = RecommendationService()

# ═══════════════════════════════════════════════════════════════════
# API 端点
# ═══════════════════════════════════════════════════════════════════


@app.get("/")
async def root():
    """根端点"""
    return {
        "message": "弹性设计示例",
        "status": "running",
    }


@app.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int):
    """
    获取产品（带弹性）

    特性：
        - 舱壁隔离
        - 超时控制
        - 服务降级
    """
    product = await product_service.get_product(product_id)
    return ProductResponse(**product)


@app.post("/orders", response_model=CreateOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(request: CreateOrderRequest):
    """
    创建订单（幂等）

    特性：
        - 幂等性保证
        - 安全重试

    使用幂等键：
        - 客户端生成唯一键（UUID）
        - 相同的键返回相同结果
        - 超时重试安全
    """
    order = await order_service.create_order(
        user_id=request.user_id,
        product_id=request.product_id,
        amount=request.amount,
        idempotency_key=request.idempotency_key,
    )
    return CreateOrderResponse(**order)


@app.get("/users/{user_id}/recommendations")
async def get_recommendations(user_id: int):
    """
    获取推荐（多级降级）

    特性：
        - 多级降级策略
        - 优雅降级
    """
    recommendations = await recommendation_service.get_recommendations(user_id)
    return {"user_id": user_id, "recommendations": recommendations}


@app.get("/stats/bulkhead")
async def get_bulkhead_stats():
    """获取舱壁隔离统计"""
    return product_service.bulkhead.get_stats()


# ═══════════════════════════════════════════════════════════════════
# 演示和测试
# ═══════════════════════════════════════════════════════════════════


async def demo_timeout():
    """演示超时控制"""
    print("\n" + "="*60)
    print("演示 1: 超时控制")
    print("="*60)

    async def slow_operation():
        await asyncio.sleep(5.0)
        return "完成"

    # 不设置超时（会挂起 5 秒）
    print("\n不设置超时：")
    start = time.time()
    try:
        result = await asyncio.wait_for(slow_operation(), timeout=1.0)
        print(f"  结果: {result}")
    except asyncio.TimeoutError:
        elapsed = time.time() - start
        print(f"  ✓ 1 秒后超时（实际等待 {elapsed:.2f}秒）")


async def demo_retry():
    """演示重试策略"""
    print("\n" + "="*60)
    print("演示 2: 重试策略（指数退避）")
    print("="*60)

    attempt_count = 0

    async def failing_operation():
        nonlocal attempt_count
        attempt_count += 1
        print(f"\n  尝试 #{attempt_count}")

        if attempt_count < 3:
            raise Exception("模拟失败")

        print("  ✓ 成功！")
        return "成功"

    retry_policy = RetryPolicy(max_attempts=5)
    result = await retry_policy.execute(failing_operation)

    print(f"\n最终结果: {result}")


async def demo_bulkhead():
    """演示舱壁隔离"""
    print("\n" + "="*60)
    print("演示 3: 舱壁隔离")
    print("="*60)

    bulkhead = Bulkhead(max_concurrent=2, name="demo")

    async def task(name: str, duration: float):
        try:
            async with bulkhead:
                print(f"  {name}: 开始")
                await asyncio.sleep(duration)
                print(f"  {name}: 完成")
        except BulkheadIsolationError as e:
            print(f"  {name}: 被拒绝 - {e}")

    # 5 个任务，但最多 2 个并发
    print("\n启动 5 个任务（最多 2 个并发）:")
    tasks = [
        task(f"Task-{i}", random.uniform(0.5, 1.0))
        for i in range(5)
    ]

    await asyncio.gather(*tasks)

    print(f"\n统计: {bulkhead.get_stats()}")


async def demo_fallback():
    """演示服务降级"""
    print("\n" + "="*60)
    print("演示 4: 服务降级")
    print("="*60)

    async def primary_service():
        """主服务（会失败）"""
        raise Exception("主服务不可用")

    async def fallback_service():
        """降级服务"""
        return {"data": "降级数据", "_fallback": True}

    print("\n尝试调用主服务（会失败并降级）:")
    result = await with_fallback(
        primary_service,
        fallback_service,
    )

    print(f"  结果: {result}")


async def demo_idempotency():
    """演示幂等性"""
    print("\n" + "="*60)
    print("演示 5: 幂等性保证")
    print("="*60)

    idempotency = IdempotencyKey()
    key = "test-order-123"

    async def create_order():
        print("  创建订单...")
        await asyncio.sleep(0.1)
        return {"order_id": 999, "status": "created"}

    # 第一次调用（执行）
    print("\n第一次调用:")
    result1 = await idempotency.process(key, create_order)
    print(f"  结果: {result1}")

    # 第二次调用（返回缓存）
    print("\n第二次调用（相同幂等键）:")
    result2 = await idempotency.process(key, create_order)
    print(f"  结果: {result2}")
    print(f"  ✓ 返回缓存结果（未重复执行）")


async def demo_resilient_decorator():
    """演示弹性装饰器"""
    print("\n" + "="*60)
    print("演示 6: 弹性装饰器（组合模式）")
    print("="*60)

    @resilient(
        timeout=2.0,
        max_retries=3,
        bulkhead_max=5,
    )
    async def call_external_service():
        """调用外部服务"""
        return await external_service.call("test")

    print("\n调用外部服务（带弹性保护）:")
    try:
        result = await call_external_service()
        print(f"  ✓ 成功: {result}")
    except Exception as e:
        print(f"  ✗ 失败: {e}")


async def main():
    """运行所有演示"""
    print("\n🚀 弹性设计示例")

    try:
        await demo_timeout()
        await demo_retry()
        await demo_bulkhead()
        await demo_fallback()
        await demo_idempotency()
        await demo_resilient_decorator()

        print("\n" + "="*60)
        print("✅ 所有演示完成！")
        print("="*60)
        print("\n提示：运行 FastAPI 应用体验完整功能：")
        print("  uvicorn study.level4.examples.05_resilience:app --reload")
        print("\nAPI 端点：")
        print("  GET    /products/{id}                # 获取产品（带降级）")
        print("  POST   /orders                       # 创建订单（幂等）")
        print("  GET    /users/{id}/recommendations  # 获取推荐（多级降级）")
        print("  GET    /stats/bulkhead              # 舱壁隔离统计")

    except Exception as e:
        logger.error(f"演示失败: {e}")
        print(f"\n❌ 错误: {e}")


if __name__ == "__main__":
    asyncio.run(main())
