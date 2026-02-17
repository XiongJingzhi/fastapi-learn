"""
04. 监控与指标 - Monitoring and Metrics
=======================================

这个示例展示了如何在 FastAPI 中实现监控和指标收集。

架构原则：
- 可观测性三大支柱：Logs、Metrics、Traces
- 结构化日志：JSON 格式，便于查询
- Prometheus 指标：Counter、Gauge、Histogram、Summary
- 分布式追踪：OpenTelemetry
- 健康检查：liveness 和 readiness

运行要求：
- pip install prometheus-fastapi-instrumentator opentelemetry-api
- Prometheus 服务器（可选）

生产环境建议：
- 使用集中式日志系统（ELK、Loki）
- 配置 Prometheus 抓取
- 使用 Grafana 仪表盘
- 启用分布式追踪
- 设置告警规则
"""

import asyncio
import logging
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request, status, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from prometheus_client import Counter, Gauge, Histogram, Summary, Info

# ═══════════════════════════════════════════════════════════════════
# 结构化日志配置
# ═══════════════════════════════════════════════════════════════════


class StructuredLogger:
    """
    结构化日志

    对比传统日志：
        传统：logger.info(f"User {user_id} logged in")
        结构化：logger.info("User logged in", extra={"user_id": user_id})

    优点：
        - 结构化数据，易于查询
        - 支持日志聚合工具
        - 便于分析
    """

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # JSON 格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # 控制台输出
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def _log(self, level: str, message: str, **context):
        """记录日志"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "message": message,
            "level": level,
            **context,
        }

        # 添加请求 ID（如果存在）
        if "request_id" not in log_entry:
            log_entry["request_id"] = str(uuid.uuid4())

        # 记录
        getattr(self.logger, level.lower())(
            f"{message} - {context}"
        )

        return log_entry

    def info(self, message: str, **context):
        """信息日志"""
        return self._log("INFO", message, **context)

    def warning(self, message: str, **context):
        """警告日志"""
        return self._log("WARNING", message, **context)

    def error(self, message: str, **context):
        """错误日志"""
        return self._log("ERROR", message, **context)

    def debug(self, message: str, **context):
        """调试日志"""
        return self._log("DEBUG", message, **context)


logger = StructuredLogger(__name__)

# ═══════════════════════════════════════════════════════════════════
# Prometheus 指标
# ═══════════════════════════════════════════════════════════════════


class MetricsCollector:
    """
    Prometheus 指标收集器

    四种指标类型：
        1. Counter（计数器）：只增不减
           用途：请求数、错误数
           示例：http_requests_total

        2. Gauge（仪表盘）：可增可减
           用途：当前连接数、内存使用
           示例：active_connections

        3. Histogram（直方图）：可配置的桶
           用途：请求延迟分布
           示例：http_request_duration_seconds

        4. Summary（摘要）：统计信息
           用途：平均延迟、P95、P99
           示例：http_request_duration_seconds_summary
    """

    def __init__(self):
        # Counter：HTTP 请求总数
        self.http_requests_total = Counter(
            "http_requests_total",
            "Total HTTP requests",
            ["method", "endpoint", "status"]
        )

        # Counter：HTTP 错误总数
        self.http_errors_total = Counter(
            "http_errors_total",
            "Total HTTP errors",
            ["method", "endpoint", "error_type"]
        )

        # Gauge：当前活跃请求数
        self.http_requests_active = Gauge(
            "http_requests_active",
            "Active HTTP requests"
        )

        # Gauge：数据库连接数
        self.db_connections = Gauge(
            "db_connections",
            "Database connections",
            ["database", "state"]  # state: active, idle
        )

        # Histogram：请求延迟（分桶）
        self.http_request_duration_seconds = Histogram(
            "http_request_duration_seconds",
            "HTTP request latency",
            ["method", "endpoint"],
            buckets=[0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0]
        )

        # Summary：请求延迟（统计）
        self.http_request_duration_summary = Summary(
            "http_request_duration_summary",
            "HTTP request latency summary",
            ["method", "endpoint"]
        )

        # Counter：业务指标
        self.user_registrations_total = Counter(
            "user_registrations_total",
            "Total user registrations"
        )

        self.orders_created_total = Counter(
            "orders_created_total",
            "Total orders created"
        )

        self.orders_amount_total = Counter(
            "orders_amount_total",
            "Total order amount",
            ["currency"]
        )

        # Gauge：系统指标
        self.system_memory_usage = Gauge(
            "system_memory_usage_bytes",
            "System memory usage"
        )

        # Info：应用信息
        self.app_info = Info(
            "app_info",
            "Application information"
        )

        # 初始化应用信息
        self.app_info.info({
            "version": "1.0.0",
            "environment": "production",
        })

    def record_request(
        self,
        method: str,
        endpoint: str,
        status: int,
        duration: float,
    ):
        """记录请求"""
        self.http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=status
        ).inc()

        self.http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)

        self.http_request_duration_summary.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)

    def record_error(
        self,
        method: str,
        endpoint: str,
        error_type: str,
    ):
        """记录错误"""
        self.http_errors_total.labels(
            method=method,
            endpoint=endpoint,
            error_type=error_type
        ).inc()

    def record_user_registration(self):
        """记录用户注册"""
        self.user_registrations_total.inc()

    def record_order(self, amount: float, currency: str = "USD"):
        """记录订单"""
        self.orders_created_total.inc()
        self.orders_amount_total.labels(currency=currency).inc(amount)


metrics = MetricsCollector()


# ═══════════════════════════════════════════════════════════════════
# 分布式追踪（简化版）
# ═══════════════════════════════════════════════════════════════════


class TraceContext:
    """追踪上下文"""

    def __init__(
        self,
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
    ):
        self.trace_id = trace_id or str(uuid.uuid4())
        self.span_id = span_id or str(uuid.uuid4())[:16]
        self.parent_span_id = parent_span_id

    def to_dict(self) -> Dict:
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
        }


class Span:
    """
    Span（追踪段）

    分布式追踪概念：
        Trace（追踪）：一个完整的请求链路
        Span（段）：链路中的一个步骤

    示例：
        Trace: 用户请求 → API → 数据库 → 缓存 → 响应
        Span 1: 用户请求
        Span 2: API 处理（父：Span 1）
        Span 3: 数据库查询（父：Span 2）
        Span 4: 缓存查询（父：Span 2）
    """

    def __init__(
        self,
        name: str,
        parent_span: Optional["Span"] = None,
        context: Optional[TraceContext] = None,
    ):
        self.name = name
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.parent_span = parent_span
        self.context = context or TraceContext(
            parent_span_id=parent_span.context.span_id if parent_span else None
        )
        self.tags: Dict[str, Any] = {}
        self.events: List[Dict] = []

    def set_tag(self, key: str, value: Any):
        """设置标签"""
        self.tags[key] = value
        return self

    def add_event(self, name: str, **attributes):
        """添加事件"""
        self.events.append({
            "name": name,
            "timestamp": time.time(),
            "attributes": attributes,
        })
        return self

    def finish(self):
        """结束 span"""
        self.end_time = time.time()
        duration = self.end_time - self.start_time

        logger.info(
            f"Span 完成: {self.name}",
            duration=duration,
            **self.context.to_dict(),
            tags=self.tags,
            events_count=len(self.events),
        )

        return duration

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, tb):
        if exc_type:
            self.set_tag("error", True)
            self.add_event("error", message=str(exc_val))
        self.finish()


class Tracer:
    """追踪器"""

    def __init__(self, service_name: str):
        self.service_name = service_name

    def start_span(
        self,
        name: str,
        parent_span: Optional[Span] = None,
    ) -> Span:
        """开始一个 span"""
        span = Span(name, parent_span)
        logger.info(
            f"Span 开始: {name}",
            **span.context.to_dict(),
        )
        return span


tracer = Tracer("fastapi-service")

# ═══════════════════════════════════════════════════════════════════
# 中间件
# ═══════════════════════════════════════════════════════════════════


async def logging_middleware(request: Request, call_next):
    """
    日志中间件

    记录：
        - 请求信息
        - 响应信息
        - 延迟
        - 追踪 ID
    """
    # 生成请求 ID
    request_id = str(uuid.uuid4())

    # 开始 span
    with tracer.start_span(f"{request.method} {request.url.path}") as span:
        span.set_tag("http.method", request.method)
        span.set_tag("http.url", str(request.url))
        span.set_tag("http.request_id", request_id)

        # 记录请求
        logger.info(
            "请求开始",
            method=request.method,
            path=request.url.path,
            request_id=request_id,
        )

        # 增加活跃请求
        metrics.http_requests_active.inc()

        # 计时
        start_time = time.time()

        try:
            # 处理请求
            response = await call_next(request)

            # 计算延迟
            duration = time.time() - start_time

            # 记录响应
            logger.info(
                "请求完成",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration=duration,
                request_id=request_id,
            )

            # 记录指标
            metrics.record_request(
                method=request.method,
                endpoint=request.url.path,
                status=response.status_code,
                duration=duration,
            )

            span.set_tag("http.status_code", response.status_code)

            # 添加响应头
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Trace-ID"] = span.context.trace_id

            return response

        except Exception as e:
            # 计算延迟
            duration = time.time() - start_time

            # 记录错误
            logger.error(
                "请求失败",
                method=request.method,
                path=request.url.path,
                error=str(e),
                duration=duration,
                request_id=request_id,
            )

            # 记录错误指标
            metrics.record_error(
                method=request.method,
                endpoint=request.url.path,
                error_type=type(e).__name__,
            )

            span.set_tag("error", True)
            span.add_event("error", message=str(e))

            raise

        finally:
            # 减少活跃请求
            metrics.http_requests_active.dec()


# ═══════════════════════════════════════════════════════════════════
# 健康检查
# ═══════════════════════════════════════════════════════════════════


class HealthStatus(str, Enum):
    """健康状态"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class HealthCheckResult(BaseModel):
    """健康检查结果"""
    status: HealthStatus
    version: str
    timestamp: datetime
    checks: Dict[str, Dict[str, Any]]


class HealthChecker:
    """
    健康检查器

    Kubernetes 健康探针：
        - Liveness：应用是否存活（重启失败的）
        - Readiness：应用是否就绪（暂时不接收请求）

    检查项：
        - 数据库连接
        - Redis 连接
        - 外部服务可用性
        - 磁盘空间
    """

    def __init__(self):
        self.checks = {
            "database": self._check_database,
            "redis": self._check_redis,
            "disk": self._check_disk,
        }

    async def _check_database(self) -> Dict[str, Any]:
        """检查数据库连接"""
        try:
            # 模拟数据库检查
            await asyncio.sleep(0.01)

            return {
                "status": "healthy",
                "latency_ms": 10,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
            }

    async def _check_redis(self) -> Dict[str, Any]:
        """检查 Redis 连接"""
        try:
            # 模拟 Redis 检查
            await asyncio.sleep(0.005)

            return {
                "status": "healthy",
                "latency_ms": 5,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
            }

    async def _check_disk(self) -> Dict[str, Any]:
        """检查磁盘空间"""
        import shutil

        # 模拟磁盘检查
        usage = shutil.disk_usage("/")

        # 使用率超过 80% 警告
        if usage.percent > 80:
            return {
                "status": "degraded",
                "usage_percent": usage.percent,
                "free_gb": usage.free / (1024**3),
            }

        return {
            "status": "healthy",
            "usage_percent": usage.percent,
            "free_gb": usage.free / (1024**3),
        }

    async def check(self) -> HealthCheckResult:
        """执行所有检查"""
        results = {}

        for name, check_func in self.checks.items():
            try:
                results[name] = await check_func()
            except Exception as e:
                results[name] = {
                    "status": "unhealthy",
                    "error": str(e),
                }

        # 计算总体状态
        statuses = [r["status"] for r in results.values()]

        if "unhealthy" in statuses:
            overall_status = HealthStatus.UNHEALTHY
        elif "degraded" in statuses:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY

        return HealthCheckResult(
            status=overall_status,
            version="1.0.0",
            timestamp=datetime.utcnow(),
            checks=results,
        )


health_checker = HealthChecker()

# ═══════════════════════════════════════════════════════════════════
# 业务模型
# ═══════════════════════════════════════════════════════════════════


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime


class OrderCreate(BaseModel):
    user_id: int
    amount: float = Field(..., gt=0)
    currency: str = Field(default="USD", pattern="^[A-Z]{3}$")


class OrderResponse(BaseModel):
    id: int
    user_id: int
    amount: float
    status: str
    created_at: datetime

# ═══════════════════════════════════════════════════════════════════
# 业务服务
# ═══════════════════════════════════════════════════════════════════


class UserService:
    """用户服务（带监控）"""

    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """创建用户（带追踪）"""
        with tracer.start_span("UserService.create_user") as span:
            span.set_tag("username", user_data.username)

            # 模拟数据库操作
            await asyncio.sleep(0.01)

            user = UserResponse(
                id=random.randint(1000, 9999),
                username=user_data.username,
                email=user_data.email,
                created_at=datetime.utcnow(),
            )

            span.add_event("user_created", user_id=user.id)

            # 记录业务指标
            metrics.record_user_registration()

            logger.info(
                "用户创建成功",
                user_id=user.id,
                username=user.username,
            )

            return user


class OrderService:
    """订单服务（带监控）"""

    async def create_order(self, order_data: OrderCreate) -> OrderResponse:
        """创建订单（带追踪）"""
        with tracer.start_span("OrderService.create_order") as span:
            span.set_tag("amount", order_data.amount)
            span.set_tag("currency", order_data.currency)

            # 模拟数据库操作
            await asyncio.sleep(0.02)

            order = OrderResponse(
                id=random.randint(10000, 99999),
                user_id=order_data.user_id,
                amount=order_data.amount,
                status="pending",
                created_at=datetime.utcnow(),
            )

            span.add_event("order_created", order_id=order.id)

            # 记录业务指标
            metrics.record_order(order_data.amount, order_data.currency)

            logger.info(
                "订单创建成功",
                order_id=order.id,
                user_id=order.user_id,
                amount=order_data.amount,
            )

            return order

# ═══════════════════════════════════════════════════════════════════
# FastAPI 应用
# ═══════════════════════════════════════════════════════════════════


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动
    logger.info("应用启动", version="1.0.0")
    yield
    # 关闭
    logger.info("应用关闭")


app = FastAPI(
    title="监控与指标示例",
    description="展示监控和指标收集的最佳实践",
    version="1.0.0",
    lifespan=lifespan,
)

# 添加中间件
app.middleware("http")(logging_middleware)

# 服务实例
user_service = UserService()
order_service = OrderService()

# ═══════════════════════════════════════════════════════════════════
# API 端点
# ═══════════════════════════════════════════════════════════════════


@app.get("/")
async def root():
    """根端点"""
    return {
        "message": "监控与指标示例",
        "version": "1.0.0",
    }


@app.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate):
    """创建用户（带监控）"""
    return await user_service.create_user(user_data)


@app.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(order_data: OrderCreate):
    """创建订单（带监控）"""
    return await order_service.create_order(order_data)


@app.get("/health")
async def health_check():
    """
    健康检查（Readiness Probe）

    Kubernetes 使用：
        - Readiness Probe: 检查应用是否准备好接收请求
        - 失败时：从 Service 中移除，不接收新请求
    """
    result = await health_checker.check()

    # 根据状态返回不同的 HTTP 状态码
    if result.status == HealthStatus.UNHEALTHY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=result.model_dump(),
        )

    return result


@app.get("/health/live")
async def liveness():
    """
    存活检查（Liveness Probe）

    Kubernetes 使用：
        - Liveness Probe: 检查应用是否存活
        - 失败时：重启容器
    """
    return {"status": "alive"}


@app.get("/metrics")
async def metrics_endpoint():
    """
    Prometheus 指标端点

    Prometheus 配置：
        scrape_configs:
          - job_name: 'fastapi'
            static_configs:
              - targets: ['localhost:8000']
            metrics_path: /metrics
    """
    from prometheus_client import generate_latest

    return Response(
        content=generate_latest(),
        media_type="text/plain",
    )


@app.get("/debug/traces")
async def get_traces():
    """获取最近的追踪记录（调试用）"""
    return {
        "message": "在生产环境中，使用 OpenTelemetry + Jaeger/Zipkin",
        "hint": "这个端点仅用于演示",
    }


import random


from fastapi import Response


# ═══════════════════════════════════════════════════════════════════
# 演示和测试
# ═══════════════════════════════════════════════════════════════════


async def demo_structured_logging():
    """演示结构化日志"""
    print("\n" + "="*60)
    print("演示 1: 结构化日志")
    print("="*60)

    logger.info(
        "用户登录",
        user_id=123,
        username="alice",
        ip_address="192.168.1.1",
    )

    logger.warning(
        "磁盘空间不足",
        usage_percent=85,
        free_gb=15,
    )

    logger.error(
        "支付失败",
        order_id=456,
        error="支付服务超时",
        amount=99.99,
    )


async def demo_prometheus_metrics():
    """演示 Prometheus 指标"""
    print("\n" + "="*60)
    print("演示 2: Prometheus 指标")
    print("="*60)

    # 模拟请求
    for i in range(10):
        metrics.record_request(
            method="GET",
            endpoint="/api/users",
            status=200,
            duration=random.uniform(0.01, 0.5),
        )

    # 模拟错误
    metrics.record_error(
        method="POST",
        endpoint="/api/payments",
        error_type="TimeoutError",
    )

    # 业务指标
    metrics.record_user_registration()
    metrics.record_order(99.99, "USD")

    print("✓ 指标已记录")
    print("  访问 http://localhost:8000/metrics 查看 Prometheus 指标")


async def demo_distributed_tracing():
    """演示分布式追踪"""
    print("\n" + "="*60)
    print("演示 3: 分布式追踪")
    print("="*60)

    # 主 span
    with tracer.start_span("HandleUserRequest") as parent_span:
        parent_span.set_tag("user_id", 123)

        # 子 span 1：数据库查询
        with tracer.start_span("QueryDatabase", parent_span) as db_span:
            await asyncio.sleep(0.01)
            db_span.set_tag("db.query", "SELECT * FROM users WHERE id = 123")

        # 子 span 2：缓存查询
        with tracer.start_span("QueryCache", parent_span) as cache_span:
            await asyncio.sleep(0.005)
            cache_span.set_tag("cache.hit", True)

        # 子 span 3：外部 API 调用
        with tracer.start_span("CallPaymentAPI", parent_span) as api_span:
            await asyncio.sleep(0.02)
            api_span.set_tag("external.api", "payment-service")


async def demo_health_checks():
    """演示健康检查"""
    print("\n" + "="*60)
    print("演示 4: 健康检查")
    print("="*60)

    result = await health_checker.check()

    print(f"\n总体状态: {result.status}")
    print("\n检查项:")
    for name, check in result.checks.items():
        status_symbol = "✓" if check["status"] == "healthy" else "✗"
        print(f"  {status_symbol} {name}: {check['status']}")
        if "error" in check:
            print(f"      错误: {check['error']}")


async def main():
    """运行所有演示"""
    print("\n🚀 监控与指标示例")

    try:
        await demo_structured_logging()
        await demo_prometheus_metrics()
        await demo_distributed_tracing()
        await demo_health_checks()

        print("\n" + "="*60)
        print("✅ 所有演示完成！")
        print("="*60)
        print("\n提示：运行 FastAPI 应用体验完整功能：")
        print("  uvicorn study.level4.examples.04_monitoring:app --reload")
        print("\nAPI 端点：")
        print("  POST   /users                        # 创建用户（记录指标）")
        print("  POST   /orders                       # 创建订单（记录指标）")
        print("  GET    /health                       # 健康检查（Readiness）")
        print("  GET    /health/live                  # 存活检查（Liveness）")
        print("  GET    /metrics                      # Prometheus 指标")
        print("\nPrometheus 配置：")
        print("  scrape_configs:")
        print("    - job_name: 'fastapi'")
        print("      static_configs:")
        print("        - targets: ['localhost:8000']")
        print("      metrics_path: /metrics")

    except Exception as e:
        logger.error(f"演示失败: {e}")
        print(f"\n❌ 错误: {e}")


if __name__ == "__main__":
    asyncio.run(main())
