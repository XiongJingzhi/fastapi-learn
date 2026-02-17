# Level 6 进阶练习题

## 🎯 练习目标

通过实战练习，掌握微服务架构中的容错、限流、熔断、降级等高级特性。

---

## 练习 1: 实现熔断器

### 题目

为服务间调用实现熔断器模式。

### 要求

1. 使用 `circuitbreaker` 库
2. 配置熔断器参数（失败阈值、恢复时间）
3. 模拟服务故障，观察熔断器行为

### 提示

```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
async def call_user_service(user_id: int):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://user-service:8001/users/{user_id}")
        response.raise_for_status()
        return response.json()

@app.post("/orders")
async def create_order(order: OrderCreate):
    try:
        user = await call_user_service(order.user_id)
    except CircuitBreakerError:
        user = {"id": order.user_id, "name": "Unknown"}
    return user
```

### 测试场景

1. 正常情况：服务正常，熔断器关闭
2. 故障情况：服务挂了，熔断器打开
3. 恢复情况：服务恢复，熔断器半开→关闭

### 检查清单

- [ ] 熔断器正常工作
- [ ] 熔断器打开后返回降级数据
- [ ] 熔断器一段时间后尝试恢复
- [ ] 服务恢复后熔断器关闭

---

## 练习 2: 实现降级策略

### 题目

为关键接口实现降级策略。

### 要求

1. 用户服务不可用时，返回缓存数据
2. 产品服务不可用时，返回默认数据
3. 推荐服务不可用时，返回热门商品

### 提示

```python
from functools import wraps
import asyncio

cache = {}

def fallback(cache_key: str, default_value: any):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
                # 缓存结果
                cache[cache_key] = result
                return result
            except Exception:
                # 返回缓存或默认值
                return cache.get(cache_key, default_value)
        return wrapper
    return decorator

@fallback(cache_key="user:123", default_value={"id": 123, "name": "Unknown"})
async def get_user(user_id: int):
    # 调用用户服务...
    pass
```

### 检查清单

- [ ] 服务不可用时返回缓存数据
- [ ] 缓存为空时返回默认值
- [ ] 降级逻辑不影响其他功能
- [ ] 降级数据对用户有意义

---

## 练习 3: 实现限流

### 题目

使用 Redis 实现分布式限流。

### 要求

1. 使用 Redis 存储请求计数
2. 实现滑动窗口限流算法
3. 不同接口不同限流策略

### 提示

```python
import redis
import time

r = redis.Redis(host='redis', port=6379, decode_responses=True)

async def rate_limit(user_id: int, limit: int, window: int) -> bool:
    """滑动窗口限流"""
    now = time.time()
    key = f"rate_limit:{user_id}"

    # 移除窗口外的记录
    r.zremrangebyscore(key, 0, now - window)

    # 添加当前请求
    r.zadd(key, {str(now): now})

    # 统计窗口内请求数
    count = r.zcard(key)

    return count <= limit

@app.post("/orders")
async def create_order(order: OrderCreate, user_id: int):
    if not await rate_limit(user_id, limit=10, window=60):
        raise HTTPException(status_code=429, detail="Too many requests")
    # 创建订单...
```

### 检查清单

- [ ] 限流正常工作
- [ ] 超过限制返回 429 状态码
- [ ] 限流算法精确
- [ ] 限流配置灵活可调

---

## 练习 4: 实现重试机制

### 题目

为服务间调用实现智能重试。

### 要求

1. 使用 `tenacity` 库
2. 指数退避重试
3. 只对瞬时错误重试

### 提示

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(httpx.ConnectError)
)
async def call_service_with_retry(url: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()
```

### 检查清单

- [ ] 重试机制正常工作
- [ ] 瞬时错误重试成功
- [ ] 持久错误快速失败
- [ ] 重试不加重后端负担

---

## 练习 5: 实现超时控制

### 题目

为服务间调用添加超时控制。

### 要求

1. 设置连接超时
2. 设置读取超时
3. 超时后返回友好错误

### 提示

```python
import httpx
from httpx import TimeoutException

timeout = httpx.Timeout(
    connect=2.0,  # 连接超时 2 秒
    read=5.0,     # 读取超时 5 秒
    write=5.0,    # 写入超时 5 秒
    pool=10.0     # 连接池超时 10 秒
)

async def call_service_with_timeout(url: str):
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
            return response.json()
    except TimeoutException:
        raise HTTPException(status_code=504, detail="Service timeout")
```

### 检查清单

- [ ] 超时控制正常工作
- [ ] 连接超时正确触发
- [ ] 读取超时正确触发
- [ ] 超时后返回友好错误

---

## 练习 6: 实现分布式配置

### 题目

使用 Redis 实现简单的分布式配置中心。

### 要求

1. 配置存储在 Redis 中
2. 服务启动时从 Redis 加载配置
3. 配置更新后服务热加载

### 提示

```python
import redis
import json

r = redis.Redis(host='redis', port=6379, decode_responses=True)

class Config:
    def __init__(self):
        self.load_config()

    def load_config(self):
        config_str = r.get("app:config")
        if config_str:
            config = json.loads(config_str)
            self.debug = config.get("debug", False)
            self.log_level = config.get("log_level", "INFO")

    def reload_config(self):
        self.load_config()

config = Config()

@app.post("/admin/reload-config")
def reload_config():
    config.reload_config()
    return {"status": "config reloaded"}
```

### 检查清单

- [ ] 配置存储在 Redis 中
- [ ] 服务启动时加载配置
- [ ] 配置可以热更新
- [ ] 配置更新不影响服务运行

---

## 练习 7: 实现分布式追踪

### 题目

使用 OpenTelemetry 实现分布式追踪。

### 要求

1. 为每个服务添加追踪
2. 传播 trace context
3. 导出追踪数据到 Jaeger

### 提示

```python
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.propagate import inject

# 初始化追踪
FastAPIInstrumentor.instrument_app(app)

@app.post("/orders")
async def create_order(order: OrderCreate):
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("call_user_service"):
        headers = {}
        inject(headers)
        user = await call_user_service(order.user_id, headers=headers)
    return user
```

### 检查清单

- [ ] 每个服务都有追踪
- [ ] Trace context 正确传播
- [ ] 追踪数据导出到 Jaeger
- [ ] 可以在 Jaeger UI 中查看调用链

---

## ✅ 完成标准

完成所有练习后，你应该能够：

- [ ] 理解和实现熔断器模式
- [ ] 理解和实现降级策略
- [ ] 理解和实现限流
- [ ] 理解和实现重试机制
- [ ] 理解和实现超时控制
- [ ] 理解和实现分布式配置
- [ ] 理解和实现分布式追踪

---

## 💡 学习建议

1. **逐个实现**
   - 不要一次性实现所有功能
   - 一个一个地添加容错特性
   - 理解每个特性的作用

2. **测试故障场景**
   - 故意制造服务故障
   - 观察容错机制是否生效
   - 验证系统稳定性

3. **监控指标**
   - 监控熔断器状态
   - 监控降级次数
   - 监控重试次数

---

**祝你练习愉快！记住：在分布式系统中，故障是常态，要为故障做好准备！** 🚀
