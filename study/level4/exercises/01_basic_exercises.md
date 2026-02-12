# Level 4 - 基础练习

## 📚 练习目标

巩固生产就绪的基础概念和基本实现。

---

## 练习 1: Redis 缓存基本操作

### 目标
实现基本的 Redis 缓存操作

### 任务
1. 创建一个用户服务，使用 Redis 缓存用户数据
2. 实现读取时的 Cache-Aside 模式
3. 实现写入时删除缓存
4. 为缓存设置合理的 TTL

### 要求
```python
# user_service.py

from redis.asyncio import Redis
from pydantic import BaseModel

class User(BaseModel):
    id: int
    username: str
    email: str

class UserService:
    def __init__(self, redis: Redis):
        self.redis = redis
        # TODO: 初始化

    async def get_user(self, user_id: int) -> User | None:
        """
        TODO: 实现 Cache-Aside 模式

        步骤：
        1. 先查 Redis 缓存
        2. 缓存命中则返回
        3. 缓存未命中则查数据库
        4. 写入缓存（TTL: 5 分钟）
        5. 返回数据
        """
        pass

    async def update_user(self, user: User) -> User:
        """
        TODO: 更新用户

        步骤：
        1. 更新数据库
        2. 删除缓存（注意：是删除而非更新）
        """
        pass
```

### 验证
- 缓存命中时响应时间 < 5ms
- 缓存未命中时更新缓存
- 写入后缓存被删除

### 提示
- 使用 `redis.get()` 和 `redis.setex()`
- TTL 建议 300 秒（5 分钟）
- 缓存键格式：`user:{user_id}`

---

## 练习 2: 消息队列基本用法

### 目标
实现基本的生产者-消费者模式

### 任务
1. 创建一个用户注册事件发布者
2. 创建一个邮件发送消费者
3. 实现异步处理

### 要求
```python
# event_publisher.py

class UserEventPublisher:
    async def publish_user_created(self, user: User):
        """
        TODO: 发布用户创建事件

        事件格式：
        {
            "event_type": "user.created",
            "user_id": 123,
            "username": "alice",
            "timestamp": "2024-01-01T00:00:00Z"
        }
        """
        pass

# email_consumer.py

class EmailConsumer:
    async def handle_user_created(self, event: dict):
        """
        TODO: 处理用户创建事件

        1. 解析事件
        2. 发送欢迎邮件
        3. 记录日志
        """
        pass
```

### 验证
- 用户注册后邮件被发送
- 事件处理是异步的（不阻塞响应）
- 消息不丢失（使用 ack）

### 提示
- 使用 `asyncio.create_task()` 后台处理
- 模拟邮件发送：`await asyncio.sleep(2)`

---

## 练习 3: HTTP 客户端超时和重试

### 目标
为外部 API 调用添加超时和重试

### 任务
1. 创建一个 HTTP 客户端
2. 添加超时控制
3. 添加重试机制（指数退避）

### 要求
```python
# api_client.py

import httpx

class WeatherAPIClient:
    def __init__(self):
        # TODO: 配置超时
        self.client = httpx.AsyncClient(
            timeout=???
        )

    async def get_weather(self, city: str) -> dict:
        """
        TODO: 添加重试机制

        重试策略：
        - 最大重试 3 次
        - 指数退避：1s, 2s, 4s
        - 只重试网络错误和超时
        """
        pass

    async def _do_get_weather(self, city: str) -> dict:
        """实际的 API 调用"""
        response = await self.client.get(
            f"https://api.weather.com/{city}"
        )
        response.raise_for_status()
        return response.json()
```

### 验证
- 超时时间 < 5 秒
- 网络错误时自动重试
- 重试延迟遵循指数退避

### 提示
- 使用 `asyncio.sleep()` 实现延迟
- 使用 `try-except` 捕获异常
- 计算延迟：`2 ** attempt`

---

## 练习 4: 结构化日志

### 目标
实现结构化日志记录

### 任务
1. 创建一个日志工具类
2. 记录请求和响应
3. 添加追踪 ID

### 要求
```python
# logger.py

import logging
import uuid

class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def log_request(
        self,
        method: str,
        path: str,
        user_id: int = None
    ):
        """
        TODO: 记录请求日志

        日志格式（JSON）：
        {
            "timestamp": "2024-01-01T00:00:00Z",
            "level": "INFO",
            "message": "Request received",
            "method": "GET",
            "path": "/api/users",
            "user_id": 123,
            "trace_id": "abc-123"
        }
        """
        pass

    def log_error(
        self,
        error: Exception,
        context: dict
    ):
        """
        TODO: 记录错误日志

        包含错误类型、消息和上下文
        """
        pass
```

### 验证
- 日志包含时间戳
- 日志包含追踪 ID
- 错误日志包含堆栈信息

### 提示
- 使用 `datetime.utcnow()` 获取时间
- 使用 `uuid.uuid4()` 生成追踪 ID
- 使用 `logger.exception()` 记录异常

---

## 练习 5: 熔断器基本实现

### 目标
实现一个简单的熔断器

### 任务
1. 定义熔断器状态（CLOSED, OPEN, HALF_OPEN）
2. 实现状态转换逻辑
3. 实现熔断器装饰器

### 要求
```python
# circuit_breaker.py

from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"      # 正常
    OPEN = "open"          # 熔断
    HALF_OPEN = "half_open"  # 半开

class SimpleCircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: int = 60
    ):
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        # TODO: 初始化其他属性

    async def call(self, func, *args, **kwargs):
        """
        TODO: 实现熔断逻辑

        1. 检查状态
        2. OPEN 状态：检查是否超时，超时则转为 HALF_OPEN
        3. CLOSED/ HALF_OPEN 状态：执行函数
        4. 成功：重置失败计数（HALF_OPEN 转为 CLOSED）
        5. 失败：增加失败计数，达到阈值则 OPEN
        """
        pass
```

### 验证
- 失败 5 次后触发熔断
- 熔断期间拒绝请求
- 超时后进入半开状态
- 半开状态成功后恢复

### 提示
- 使用 `time.time()` 记录时间戳
- 状态转换时要记录日志
- 使用异常表示熔断状态

---

## 🎯 完成标准

完成所有练习后，你应该能够：

- ✅ 实现基本的 Redis 缓存
- ✅ 使用消息队列进行异步处理
- ✅ 为外部 API 添加超时和重试
- ✅ 记录结构化日志
- ✅ 实现简单的熔断器

## 📝 提交检查清单

- [ ] 所有代码可运行
- [ ] 没有硬编码（使用配置）
- [ ] 有适当的错误处理
- [ ] 有日志记录
- [ ] 代码有注释

---

**下一步**: 完成 `02_intermediate_exercises.md`
