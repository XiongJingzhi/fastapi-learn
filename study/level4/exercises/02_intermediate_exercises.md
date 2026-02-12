# Level 4 - 进阶练习

## 📚 练习目标

掌握生产环境的复杂场景和最佳实践。

---

## 练习 1: 多级缓存架构

### 目标
实现多级缓存（Redis + 内存）提升性能

### 任务
1. 实现内存缓存（LRU）
2. 实现二级缓存（内存 → Redis）
3. 实现缓存预热

### 要求
```python
# multi_level_cache.py

from functools import lru_cache
from redis.asyncio import Redis

class MultiLevelCache:
    """
    两级缓存：
    - L1: 内存缓存（极快，但容量小）
    - L2: Redis 缓存（快，容量大）
    - L3: 数据库（慢，但全量）
    """

    def __init__(self, redis: Redis):
        self.redis = redis

    async def get_user(self, user_id: int) -> User | None:
        """
        TODO: 实现两级缓存

        查询顺序：
        1. L1 内存缓存（使用 @lru_cache）
        2. L2 Redis 缓存
        3. L3 数据库

        更新顺序：
        - 写入 L1 和 L2
        """
        pass

    async def warmup_cache(self, user_ids: List[int]):
        """
        TODO: 缓存预热

        批量加载热点数据到缓存
        """
        pass

    async def invalidate_user(self, user_id: int):
        """
        TODO: 缓存失效

        同时清除 L1 和 L2 缓存
        """
        pass
```

### 验证
- L1 缓存命中率 > 80%
- L2 缓存命中率 > 15%
- 数据库查询 < 5%
- 缓存预热完成时间 < 1 秒（100 个用户）

### 提示
- 使用 `@lru_cache(maxsize=1000)` 装饰器
- L1 缓存 TTL：5 分钟
- L2 缓存 TTL：30 分钟
- 使用 `asyncio.gather()` 并行预热

---

## 练习 2: 消息队列可靠性保证

### 目标
确保消息不丢失、不重复

### 任务
1. 实现消息确认机制
2. 实现死信队列
3. 实现幂等性处理

### 要求
```python
# reliable_mq.py

class ReliableConsumer:
    """
    可靠的消息消费者
    """

    async def consume_with_ack(self, queue: str):
        """
        TODO: 消费消息（带确认）

        流程：
        1. 从队列拉取消息
        2. 处理消息
        3. 成功则确认（ack）
        4. 失败则重试（nack）
        5. 达到最大重试次数则进入死信队列
        """
        pass

    async def send_to_dead_letter(
        self,
        message: dict,
        error: Exception
    ):
        """
        TODO: 发送到死信队列

        死信消息包含：
        - 原始消息
        - 错误信息
        - 重试次数
        - 时间戳
        """
        pass

class IdempotentHandler:
    """
    幂等处理器
    """

    async def handle_payment(self, event: dict) -> dict:
        """
        TODO: 幂等支付处理

        使用幂等键确保：
        - 相同的事件返回相同结果
        - 重复处理不会重复扣款
        """
        pass
```

### 验证
- 消息不丢失（模拟进程重启）
- 消息不重复处理（使用幂等键）
- 失败消息进入死信队列
- 死信消息可以重试

### 提示
- 使用 Redis 存储幂等键（TTL: 24 小时）
- 幂等键格式：`payment:{order_id}`
- 死信队列：`{queue}_dlq`

---

## 练习 3: API 速率限制

### 目标
实现多维度速率限制

### 任务
1. 实现 IP 级别限制
2. 实现用户级别限制
3. 实现 API 级别限制

### 要求
```python
# rate_limiter.py

class RateLimiter:
    """
    多维度速率限制器

    算法：令牌桶
    """

    def __init__(self, redis: Redis):
        self.redis = redis

    async def check_rate_limit(
        self,
        identifier: str,
        limit: int,
        window: int
    ) -> bool:
        """
        TODO: 检查速率限制

        使用滑动窗口算法：
        - 限制：limit 次请求
        - 时间窗口：window 秒

        返回：
        - True: 允许请求
        - False: 超出限制
        """
        pass

    async def get_limit_info(
        self,
        identifier: str
    ) -> dict:
        """
        TODO: 获取限制信息

        返回：
        {
            "remaining": 95,  # 剩余请求数
            "reset_at": "...",  # 重置时间
            "limit": 100
        }
        """
        pass

# FastAPI 依赖
async def rate_limit_by_ip(request: Request):
    """IP 级别限制：100 请求/分钟"""
    pass

async def rate_limit_by_user(user_id: int):
    """用户级别限制：1000 请求/小时"""
    pass
```

### 验证
- IP 限制：100 请求/分钟
- 用户限制：1000 请求/小时
- API 限制：每个端点独立限制
- 超出限制返回 429 状态码
- 响应头包含限制信息

### 提示
- 使用 Redis Sorted Set 实现滑动窗口
- 分数 = 时间戳
- 删除窗口外的记录
- 计数 = 集合大小

---

## 练习 4: 分布式追踪集成

### 目标
实现完整的分布式追踪

### 任务
1. 集成 OpenTelemetry
2. 追踪跨服务调用
3. 记录 Span 和事件

### 要求
```python
# tracing.py

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

class DistributedTracer:
    """
    分布式追踪器
    """

    def __init__(self, service_name: str):
        # TODO: 初始化 OpenTelemetry
        pass

    async def trace_http_request(
        self,
        request: Request,
        handler: Callable
    ):
        """
        TODO: 追踪 HTTP 请求

        创建 Span：
        - 名称："{method} {path}"
        - 标签：method、path、user_id
        - 事件：start、end
        """
        pass

    async def trace_external_call(
        self,
        service: str,
        operation: str,
        func: Callable
    ):
        """
        TODO: 追踪外部服务调用

        创建子 Span
        """
        pass

    def inject_trace_headers(
        self,
        headers: dict
    ) -> dict:
        """
        TODO: 注入追踪头

        添加：
        - traceparent
        - tracestate
        """
        pass

    def extract_trace_context(
        self,
        headers: dict
    ):
        """
        TODO: 提取追踪上下文

        从传入的请求头中提取
        """
        pass
```

### 验证
- 所有请求都有 trace ID
- 跨服务调用保持同一个 trace ID
- Span 包含正确的父子关系
- 可以导出到 Jaeger/Zipkin

### 提示
- 使用 `opentelemetry-fastapi` 中间件
- 使用 `httpx.AsyncClient` 发送追踪数据
- 环境变量：`OTEL_EXPORTER_OTLP_ENDPOINT`

---

## 练习 5: 服务降级策略

### 目标
实现多级服务降级

### 任务
1. 定义降级级别
2. 实现降级决策器
3. 实现降级处理器

### 要求
```python
# degradation.py

from enum import Enum

class DegradationLevel(Enum):
    NORMAL = "normal"        # 正常
    DEGRADED = "degraded"   # 部分降级
    MINIMAL = "minimal"     # 最小服务

class DegradationManager:
    """
    降级管理器
    """

    def __init__(self):
        self.level = DegradationLevel.NORMAL
        # TODO: 初始化依赖服务状态

    async def check_health(self) -> DegradationLevel:
        """
        TODO: 检查健康状态

        检查项：
        - 数据库连接
        - Redis 连接
        - 外部 API 可用性

        决策规则：
        - 所有正常：NORMAL
        - 部分异常：DEGRADED
        - 核心异常：MINIMAL
        """
        pass

    async def handle_with_degradation(
        self,
        feature: str,
        normal_handler: Callable,
        degraded_handler: Callable = None,
        minimal_handler: Callable = None
    ):
        """
        TODO: 根据降级级别处理请求

        NORMAL -> normal_handler
        DEGRADED -> degraded_handler
        MINIMAL -> minimal_handler
        """
        pass

# 示例：推荐服务
class RecommendationService:
    async def get_recommendations(self, user_id: int):
        return await degradation_manager.handle_with_degradation(
            feature="recommendations",
            normal_handler=self._personalized_recommendations,
            degraded_handler=self._popular_recommendations,
            minimal_handler=self._empty_recommendations
        )
```

### 验证
- 健康检查准确反映系统状态
- 降级级别自动调整
- 降级时返回合理的数据
- 降级恢复后自动切换回正常

### 提示
- 使用超时判断服务健康
- 设置成功率阈值
- 记录降级事件日志
- 使用 Prometheus 指标监控

---

## 🎯 完成标准

完成所有练习后，你应该能够：

- ✅ 实现多级缓存
- ✅ 确保消息队列可靠性
- ✅ 实现速率限制
- ✅ 集成分布式追踪
- ✅ 实现服务降级

## 📝 提交检查清单

- [ ] 代码可运行
- [ ] 有单元测试
- [ ] 有集成测试
- [ ] 有性能测试
- [ ] 有文档说明

---

**下一步**: 完成 `03_challenge_projects.md`
