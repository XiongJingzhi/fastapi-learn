# 04. 监控和日志 - Monitoring and Logging

## 📍 在架构中的位置

**从"盲人摸象"到"一目了然"**

```
┌─────────────────────────────────────────────────────────────┐
│          没有监控和日志                                       │
└─────────────────────────────────────────────────────────────┘

生产环境出问题了：

用户反馈：
    "网站很慢！"
    "无法登录！"
    "订单提交失败！"

开发者：
    "哪里出问题了？不知道。" ❌
    "数据库慢？还是 API 慢？" ❌
    "怎么排查？瞎猜。" ❌

问题：
- 无法快速定位问题
- 无法了解系统健康状况
- 无法优化性能

═══════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────┐
│          有监控和日志                                         │
└─────────────────────────────────────────────────────────────┘

生产环境出问题了：

Grafana 仪表盘显示：
    📊 数据库连接池：100% 使用（异常！）
    📊 Redis 响应时间：500ms（正常 < 1ms）
    📊 /api/orders 错误率：15%（异常！）

日志显示：
    ERROR: Database connection timeout
    ERROR: Out of connection pool

开发者：
    "问题定位：数据库连接池满了！" ✅
    "解决方案：增加连接池大小或优化查询" ✅
    "修复时间：5 分钟" ✅

好处：
- 快速定位问题
- 实时了解系统状况
- 数据驱动优化
```

**🎯 你的学习目标**：掌握监控和日志的基本配置，让系统可观测、可调试。

---

## 🎯 什么是可观测性？

### 三大支柱

**可观测性（Observability）的三大支柱**：

```
┌─────────────────────────────────────────────────────────────┐
│                    可观测性三大支柱                          │
└─────────────────────────────────────────────────────────────┘

1. 日志（Logs）
   └─ 离散的事件记录
   └─ "什么时间发生了什么"
   └─ 例：ERROR: User login failed at 10:30:15

2. 指标（Metrics）
   └─ 数值化的测量数据
   └─ "系统状态如何"
   └─ 例：CPU 使用率：75%，请求数：1000/秒

3. 追踪（Traces）
   └─ 请求的完整路径
   └─ "请求经过了哪些服务"
   └─ 例：API Gateway → Service A → Service B → Database
```

---

### 生活类比：汽车仪表盘

**日志 = 汽车的黑匣子**：
```
记录事件：
- "2024-01-15 10:30:15 发动机启动"
- "2024-01-15 10:35:20 超速警告"
- "2024-01-15 10:40:00 刹车故障"

用途：事后分析
```

**指标 = 汽车的仪表盘**：
```
实时显示：
- 速度表：120 km/h
- 转速表：3000 RPM
- 油量：剩余 50%
- 水温：90°C

用途：实时监控
```

**追踪 = 导航路线**：
```
显示路径：
起点 → 高速 → 城市 → 终点

每个路段的时间：
- 起点-高速：10 分钟
- 高速-城市：30 分钟
- 城市-终点：15 分钟

用途：性能分析
```

---

## 📝 结构化日志

### 为什么需要结构化日志？

**传统日志（非结构化）**：

```python
# ❌ 不好的日志格式
print(f"User {user_id} logged in at {time}")
print(f"Order created: {order_id} by user {user_id}")
print(f"ERROR: Failed to send email to {email}")
```

**问题**：
- 无法搜索（"查找所有 user_id=123 的日志"）
- 无法过滤（"只看 ERROR 级别的日志"）
- 无法分析（"统计登录失败率"）

---

**结构化日志（JSON 格式）**：

```python
# ✅ 好的日志格式
import json
from datetime import datetime

log_entry = {
    "timestamp": datetime.utcnow().isoformat(),
    "level": "INFO",
    "event": "user_login",
    "user_id": 123,
    "ip": "192.168.1.1"
}
print(json.dumps(log_entry))

# 输出：
# {"timestamp": "2024-01-15T10:30:15", "level": "INFO", "event": "user_login", "user_id": 123, "ip": "192.168.1.1"}
```

**好处**：
- 可搜索（`event="user_login" AND user_id=123`）
- 可过滤（`level="ERROR"`）
- 可分析（统计 `event="user_login"` 的数量）

---

### Python 日志配置

**基本配置**：

```python
import logging
import json
from datetime import datetime

# ═══════════════════════════════════════════════════════════
# 1. 自定义 JSON 格式化器
# ═══════════════════════════════════════════════════════════

class JSONFormatter(logging.Formatter):
    """JSON 格式化器"""

    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        # 添加额外的字段
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id

        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id

        # 异常信息
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)

# ═══════════════════════════════════════════════════════════
# 2. 配置日志
# ═══════════════════════════════════════════════════════════

def setup_logging():
    """配置日志"""

    # 创建 logger
    logger = logging.getLogger("myapp")
    logger.setLevel(logging.INFO)

    # 创建处理器（控制台）
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)

    # 设置格式化器
    formatter = JSONFormatter()
    handler.setFormatter(formatter)

    # 添加处理器
    logger.addHandler(handler)

    return logger

# ═══════════════════════════════════════════════════════════
# 3. 使用日志
# ═══════════════════════════════════════════════════════════

logger = setup_logging()

# 基本日志
logger.info("Application started")

# 带额外字段的日志
logger.info("User logged in", extra={"user_id": 123, "ip": "192.168.1.1"})

# 错误日志
try:
    1 / 0
except Exception as e:
    logger.error("Division by zero", exc_info=True)
```

---

### FastAPI 集成日志

**请求 ID 日志**：

```python
from fastapi import FastAPI, Request
import uuid
import logging

app = FastAPI()
logger = logging.getLogger("myapp")

# ═══════════════════════════════════════════════════════════
# 中间件：为每个请求生成唯一 ID
# ═══════════════════════════════════════════════════════════

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录所有请求"""

    # 生成请求 ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    # 记录请求开始
    logger.info(
        "Request started",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path
        }
    )

    # 处理请求
    try:
        response = await call_next(request)

        # 记录请求完成
        logger.info(
            "Request completed",
            extra={
                "request_id": request_id,
                "status_code": response.status_code
            }
        )

        return response

    except Exception as e:
        # 记录请求失败
        logger.error(
            "Request failed",
            extra={
                "request_id": request_id,
                "error": str(e)
            },
            exc_info=True
        )
        raise

# ═══════════════════════════════════════════════════════════
# 使用请求 ID
# ═══════════════════════════════════════════════════════════

@app.get("/users/{user_id}")
async def get_user(user_id: int, request: Request):
    """获取用户信息"""

    request_id = request.state.request_id

    logger.info(
        "Fetching user",
        extra={
            "request_id": request_id,
            "user_id": user_id
        }
    )

    user = await fetch_user(user_id)

    return user
```

---

## 📊 Prometheus 指标

### 什么是 Prometheus？

**Prometheus = 时序数据库**：

```
特点：
- 专门存储指标数据（数值、时间戳）
- 高效的存储和查询
- 强大的数据采集能力
- 丰富的可视化工具（Grafana）
```

**核心概念**：

```
1. Metric（指标）
   └─ 一个可测量的数值
   └─ 例：http_requests_total（总请求数）

2. Label（标签）
   └─ 指标的维度
   └─ 例：method="GET", status="200"

3. Sample（样本）
   └─ 时间戳 + 数值
   └─ 例：1689600000, 100（在时间戳 1689600000，值是 100）
```

---

### 安装 prometheus-client

```bash
pip install prometheus-client
```

---

### 基本指标类型

**Counter（计数器）**：

```python
from prometheus_client import Counter

# 创建计数器
request_count = Counter(
    'http_requests_total',           # 指标名称
    'Total HTTP requests',           # 帮助文本
    ['method', 'endpoint', 'status'] # 标签
)

# 使用：记录请求
request_count.labels(
    method='GET',
    endpoint='/users',
    status='200'
).inc()

# 输出（Prometheus 格式）：
# http_requests_total{method="GET",endpoint="/users",status="200"} 123
```

---

**Histogram（直方图）**：

```python
from prometheus_client import Histogram

# 创建直方图（记录分布）
request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

# 使用：记录请求耗时
import time

start = time.time()
# ... 处理请求 ...
duration = time.time() - start

request_duration.labels(
    method='GET',
    endpoint='/users'
).observe(duration)

# 输出：
# http_request_duration_seconds_bucket{method="GET",endpoint="/users",le="0.005"} 100
# http_request_duration_seconds_bucket{method="GET",endpoint="/users",le="0.01"} 200
# ...
```

---

**Gauge（仪表）**：

```python
from prometheus_client import Gauge

# 创建仪表（记录当前值）
active_connections = Gauge(
    'db_active_connections',
    'Active database connections'
)

# 使用：设置当前连接数
active_connections.set(10)

# 增加/减少
active_connections.inc()   # +1
active_connections.dec(5)  # -5

# 输出：
# db_active_connections 11
```

---

### FastAPI 集成 Prometheus

```python
from fastapi import FastAPI, Request
from prometheus_client import Counter, Histogram, generate_latest
from prometheus_client import CONTENT_TYPE_LATEST
import time

app = FastAPI()

# ═══════════════════════════════════════════════════════════
# 1. 定义指标
# ═══════════════════════════════════════════════════════════

# 请求计数器
request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

# 请求耗时直方图
request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

# 当前活跃请求
active_requests = Gauge(
    'http_active_requests',
    'Active HTTP requests'
)

# ═══════════════════════════════════════════════════════════
# 2. 中间件：自动记录指标
# ═══════════════════════════════════════════════════════════

@app.middleware("http")
async def track_requests(request: Request, call_next):
    """跟踪所有请求"""

    # 增加活跃请求
    active_requests.inc()

    # 记录开始时间
    start_time = time.time()

    # 处理请求
    response = await call_next(request)

    # 计算耗时
    duration = time.time() - start_time

    # 记录指标
    request_count.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()

    request_duration.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)

    # 减少活跃请求
    active_requests.dec()

    return response

# ═══════════════════════════════════════════════════════════
# 3. 指标端点（供 Prometheus 抓取）
# ═══════════════════════════════════════════════════════════

@app.get("/metrics")
async def metrics():
    """Prometheus 指标端点"""
    return generate_latest()
```

---

## 🔍 分布式追踪

### 什么是分布式追踪？

**场景：微服务调用链**：

```
用户请求 → API Gateway → Service A → Service B → Database
            (100ms)        (200ms)      (150ms)     (50ms)
            总计：500ms

问题：
- 整个请求慢（500ms）
- 哪个服务慢？不知道！
```

**有追踪**：

```
Trace ID: abc123
├─ Span 1: API Gateway (100ms)
├─ Span 2: Service A (200ms)
│   ├─ Span 2.1: Service B (150ms)
│   │   └─ Span 2.1.1: Database (50ms)
└─ 总计：500ms

发现问题：
- Service A 慢（200ms）
- Service B 也慢（150ms）
- Database 正常（50ms）
```

---

### OpenTelemetry 基础

**安装**：

```bash
pip install opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation-fastapi
```

---

**基本使用**：

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.export import ConsoleSpanExporter

# ═══════════════════════════════════════════════════════════
# 1. 配置 Tracer
# ═══════════════════════════════════════════════════════════

# 创建 Tracer Provider
trace.set_tracer_provider(TracerProvider())

# 添加导出器（输出到控制台）
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(ConsoleSpanExporter())
)

# 获取 Tracer
tracer = trace.get_tracer(__name__)

# ═══════════════════════════════════════════════════════════
# 2. 创建 Span
# ═══════════════════════════════════════════════════════════

async def process_order(order_id: int):
    """处理订单"""

    # 创建 Span
    with tracer.start_as_current_span("process_order") as span:
        # 设置属性
        span.set_attribute("order_id", order_id)

        # 创建子 Span
        with tracer.start_as_current_span("validate_order"):
            await validate_order(order_id)

        with tracer.start_as_current_span("save_to_database"):
            await save_order_to_db(order_id)
```

---

## 📈 Grafana 仪表盘

### 什么是 Grafana？

**Grafana = 可视化工具**：

```
功能：
- 从 Prometheus 读取指标
- 创建仪表盘和图表
- 设置告警规则
- 美观的 UI
```

---

### 常用面板类型

**1. Graph（折线图）**：
```
用途：显示趋势
例：请求速率、响应时间
```

**2. Stat（数值）**：
```
用途：显示当前值
例：当前在线用户、错误率
```

**3. Table（表格）**：
```
用途：显示详细数据
例：按接口统计的请求数
```

**4. Heatmap（热力图）**：
```
用途：显示分布
例：请求耗时的分布
```

---

### 常用 PromQL 查询

```promql
# 1. 请求速率（每秒请求数）
rate(http_requests_total[5m])

# 2. 按 HTTP 状态码分组
sum(rate(http_requests_total[5m])) by (status)

# 3. 错误率
sum(rate(http_requests_total{status=~"5.."}[5m])) /
sum(rate(http_requests_total[5m]))

# 4. P95 响应时间
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# 5. 当前活跃请求
http_active_requests
```

---

## 🎨 实际场景：完整的监控系统

### FastAPI + Prometheus + Grafana

**架构图**：

```
┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│   FastAPI   │────▶│ Prometheus  │────▶│   Grafana    │
│             │     │  (抓取指标)  │     │  (可视化)    │
│ /metrics    │     └─────────────┘     └──────────────┘
└─────────────┘
```

---

**FastAPI 应用**：

```python
from fastapi import FastAPI
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import time

app = FastAPI()

# 指标定义
request_count = Counter('http_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
request_duration = Histogram('http_request_duration_seconds', 'Request duration', ['method', 'endpoint'])
active_connections = Gauge('db_active_connections', 'DB connections')

# 中间件
@app.middleware("http")
async def metrics_middleware(request, call_next):
    start = time.time()
    active_connections.inc()

    response = await call_next(request)

    duration = time.time() - start
    request_count.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    request_duration.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)

    active_connections.dec()
    return response

# 指标端点
@app.get("/metrics")
async def metrics():
    return generate_latest()

# 业务端点
@app.get("/api/users")
async def get_users():
    return {"users": []}
```

---

**Prometheus 配置（prometheus.yml）**：

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'fastapi'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

---

**启动**：

```bash
# 启动 FastAPI
uvicorn main:app --port 8000

# 启动 Prometheus
prometheus --config.file=prometheus.yml

# 启动 Grafana
grafana-server

# 访问
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000
```

---

## 🎯 小实验：自己动手

### 实验 1：基本日志

```python
import logging
import json

from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage()
        })

logger = logging.getLogger("myapp")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)

logger.info("Hello, logging!")
# 输出：{"timestamp": "2024-01-15T10:30:15", "level": "INFO", "message": "Hello, logging!"}
```

---

### 实验 2：Prometheus 指标

```python
from prometheus_client import Counter

request_count = Counter('test_requests_total', 'Test requests')

request_count.inc()
request_count.inc()

print(generate_latest())
```

---

## 📚 检查理解

回答这些问题来测试你的理解：

1. **什么是结构化日志？**
   - 提示：JSON 格式、可搜索、可过滤

2. **可观测性的三大支柱是什么？**
   - 提示：日志、指标、追踪

3. **为什么需要 Prometheus？**
   - 提示：存储和查询指标数据

4. **Counter、Histogram、Gauge 的区别？**
   - 提示：计数器、分布、当前值

5. **什么是分布式追踪？**
   - 提示：跟踪请求在微服务间的完整路径

---

## 🚀 下一步

现在你已经掌握了监控和日志，接下来：

1. **学习限流、熔断、降级**：`notes/05_resilience.md`
2. **查看实际代码**：`examples/04_monitoring.py`

**记住**：没有监控的系统就是"盲人摸象"，可观测性让系统问题一目了然！**

---

**费曼技巧总结**：
- ✅ 汽车仪表盘类比
- ✅ 结构化日志（JSON 格式）
- ✅ Prometheus 指标（Counter、Histogram、Gauge）
- ✅ FastAPI 集成示例
- ✅ 分布式追踪概念
- ✅ Prometheus + Grafana 架构
