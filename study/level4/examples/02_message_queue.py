"""
02. 消息队列集成 - Message Queue Integration
=============================================

这个示例展示了如何在 FastAPI 中集成消息队列（Kafka/RabbitMQ）

架构原则：
- 生产者-消费者模式：解耦服务
- 异步处理：提升响应速度
- 消息可靠性：确保消息不丢失
- 错误处理：重试机制
- 死信队列：处理失败消息

运行要求：
- pip install aiokafka aio-pika
- Kafka 运行在 localhost:9092（或使用 RabbitMQ）

注意：本示例使用 mock 消息队列来演示概念
"""

import asyncio
import json
import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable

from fastapi import FastAPI, HTTPException, BackgroundTasks, status
from pydantic import BaseModel, Field, ConfigDict, field_validator

# ═══════════════════════════════════════════════════════════════════
# 日志配置
# ═══════════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════
# Mock 消息队列（用于演示）
# ═══════════════════════════════════════════════════════════════════


class InMemoryMessageQueue:
    """
    内存消息队列（Mock 实现）

    真实环境中应该使用：
    - Kafka（aiokafka）：高吞吐量、分布式
    - RabbitMQ（aio-pika）：企业级、复杂路由

    这个 mock 用于演示概念，无需外部依赖
    """

    def __init__(self):
        self._queues: Dict[str, List[Dict]] = {}
        self._consumers: Dict[str, List[Callable]] = {}
        self._dead_letter_queue: List[Dict] = []

    async def publish(self, topic: str, message: Dict) -> str:
        """
        发布消息

        返回：消息 ID
        """
        if topic not in self._queues:
            self._queues[topic] = []

        msg_id = str(uuid.uuid4())
        envelope = {
            "id": msg_id,
            "topic": topic,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "attempts": 0,
        }

        self._queues[topic].append(envelope)
        logger.info(f"[MQ] 发布消息: {topic} -> {msg_id}")
        logger.debug(f"[MQ] 消息内容: {message}")

        # 触发消费者
        if topic in self._consumers:
            for consumer in self._consumers[topic]:
                asyncio.create_task(consumer(envelope))

        return msg_id

    async def consume(
        self,
        topic: str,
        handler: Callable,
        group_id: Optional[str] = None,
    ):
        """
        注册消费者

        真实环境中的参数：
        - group_id: 消费者组 ID，用于负载均衡
        """
        if topic not in self._consumers:
            self._consumers[topic] = []

        self._consumers[topic].append(handler)
        logger.info(f"[MQ] 注册消费者: {topic} (group: {group_id})")

    async def acknowledge(self, topic: str, message_id: str):
        """
        确认消息处理成功

        在真实队列中，这会提交 offset
        """
        logger.debug(f"[MQ] 消息已确认: {message_id}")

    async def retry(self, topic: str, message_id: str, delay: int = 5):
        """
        重试消息

        实际实现：延迟队列
        """
        logger.info(f"[MQ] 消息重试: {message_id} (delay: {delay}s)")

    async def dead_letter(self, topic: str, envelope: Dict):
        """
        发送到死信队列

        用于处理无法处理的消息
        """
        self._dead_letter_queue.append(envelope)
        logger.error(f"[MQ] 消息进入死信队列: {envelope['id']}")


mock_mq = InMemoryMessageQueue()

# ═══════════════════════════════════════════════════════════════════
# 事件模型
# ═══════════════════════════════════════════════════════════════════


class EventType(str, Enum):
    """事件类型"""
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    EMAIL_SENT = "email.sent"
    EMAIL_FAILED = "email.failed"
    ORDER_CREATED = "order.created"
    PAYMENT_SUCCESS = "payment.success"
    PAYMENT_FAILED = "payment.failed"


class BaseEvent(BaseModel):
    """基础事件"""
    event_type: EventType
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any]

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
        }
    )


class UserCreatedEvent(BaseEvent):
    """用户创建事件"""
    event_type: EventType = EventType.USER_CREATED


class EmailEvent(BaseEvent):
    """邮件事件"""
    event_type: EventType
    data: Dict[str, Any]

    @field_validator("data")
    @classmethod
    def validate_email_data(cls, v):
        required = ["to", "subject", "body"]
        for field in required:
            if field not in v:
                raise ValueError(f"Missing required field: {field}")
        return v


class OrderEvent(BaseEvent):
    """订单事件"""
    event_type: EventType
    data: Dict[str, Any]

    @field_validator("data")
    @classmethod
    def validate_order_data(cls, v):
        required = ["order_id", "user_id", "amount"]
        for field in required:
            if field not in v:
                raise ValueError(f"Missing required field: {field}")
        return v


# ═══════════════════════════════════════════════════════════════════
# 生产者（Publisher）
# ═══════════════════════════════════════════════════════════════════


class EventPublisher:
    """
    事件发布器

    职责：
        - 发布领域事件到消息队列
        - 确保消息格式正确
        - 处理发布失败
    """

    def __init__(self, mq: InMemoryMessageQueue):
        self.mq = mq

    async def publish(self, topic: str, event: BaseEvent) -> str:
        """
        发布事件

        流程：
            1. 验证事件
            2. 序列化
            3. 发布到 MQ
            4. 返回消息 ID

        可靠性保证：
            - 真实环境中配置 acks=all
            - 启用重试
            - 幂等性 ID
        """
        try:
            # 验证
            event_dict = event.model_dump()

            # 发布
            msg_id = await self.mq.publish(topic, event_dict)

            logger.info(f"[Publisher] 事件已发布: {event.event_type} -> {msg_id}")
            return msg_id

        except Exception as e:
            logger.error(f"[Publisher] 发布失败: {e}")
            # 真实环境中应该重试
            raise


# ═══════════════════════════════════════════════════════════════════
# 消费者（Consumer）
# ═══════════════════════════════════════════════════════════════════


class MessageProcessor:
    """
    消息处理器

    职责：
        - 处理消息
        - 错误处理和重试
        - 死信队列
    """

    def __init__(self, mq: InMemoryMessageQueue):
        self.mq = mq
        self.max_retries = 3

    async def process_with_retry(
        self,
        envelope: Dict,
        handler: Callable,
    ):
        """
        带重试的消息处理

        流程：
            1. 执行处理器
            2. 成功则确认
            3. 失败则重试
            4. 达到最大重试次数则进入死信队列
        """
        topic = envelope["topic"]
        message = envelope["message"]
        msg_id = envelope["id"]
        attempts = envelope.get("attempts", 0)

        try:
            # 执行处理器
            await handler(message)

            # 成功：确认消息
            await self.mq.acknowledge(topic, msg_id)
            logger.info(f"[Processor] 消息处理成功: {msg_id}")

        except Exception as e:
            logger.error(f"[Processor] 消息处理失败: {msg_id}, 错误: {e}")

            attempts += 1

            # 判断是否重试
            if attempts < self.max_retries:
                # 重试
                envelope["attempts"] = attempts
                await asyncio.sleep(2 ** attempts)  # 指数退避
                await self.mq.retry(topic, msg_id)

                # 递归重试
                await self.process_with_retry(envelope, handler)
            else:
                # 达到最大重试次数，进入死信队列
                logger.error(f"[Processor] 消息进入死信队列: {msg_id}")
                await self.mq.dead_letter(topic, envelope)


class EventConsumer:
    """
    事件消费者

    职责：
        - 订阅主题
        - 调用处理器
        - 错误处理
    """

    def __init__(self, mq: InMemoryMessageQueue, processor: MessageProcessor):
        self.mq = mq
        self.processor = processor

    async def subscribe(
        self,
        topic: str,
        handler: Callable,
        group_id: Optional[str] = None,
    ):
        """
        订阅主题

        参数：
            topic: 主题名称
            handler: 消息处理函数
            group_id: 消费者组 ID
        """
        async def wrapper(envelope: Dict):
            await self.processor.process_with_retry(envelope, handler)

        await self.mq.consume(topic, wrapper, group_id)


# ═══════════════════════════════════════════════════════════════════
# 业务处理器
# ═══════════════════════════════════════════════════════════════════


class EmailHandler:
    """
    邮件处理器

    展示场景：
        - 发送欢迎邮件
        - 发送订单确认邮件
        - 错误处理和重试
    """

    def __init__(self):
        self.email_queue = []

    async def send_welcome_email(self, event_data: Dict):
        """
        发送欢迎邮件

        模拟邮件发送（2 秒）
        """
        username = event_data.get("username")
        email = event_data.get("email")

        logger.info(f"[Email] 准备发送欢迎邮件: {username} <{email}>")

        # 模拟发送延迟
        await asyncio.sleep(2)

        # 模拟 10% 失败率
        import random
        if random.random() < 0.1:
            raise Exception("SMTP 服务器暂时不可用")

        # 成功
        logger.info(f"[Email] ✓ 欢迎邮件已发送: {email}")
        self.email_queue.append({
            "to": email,
            "subject": "欢迎！",
            "body": f"欢迎 {username}！",
            "sent_at": datetime.utcnow().isoformat(),
        })

    async def send_order_confirmation(self, event_data: Dict):
        """
        发送订单确认邮件
        """
        order_id = event_data.get("order_id")
        user_id = event_data.get("user_id")
        amount = event_data.get("amount")

        logger.info(f"[Email] 发送订单确认邮件: 订单 {order_id}")

        await asyncio.sleep(1)

        logger.info(f"[Email] ✓ 订单确认邮件已发送: 用户 {user_id}")


class AnalyticsHandler:
    """
    数据分析处理器

    展示场景：
        - 更新用户统计
        - 计算订单指标
        - 数据聚合
    """

    def __init__(self):
        self.metrics = {
            "users_created": 0,
            "orders_created": 0,
            "total_revenue": 0.0,
        }

    async def update_user_stats(self, event_data: Dict):
        """
        更新用户统计
        """
        user_id = event_data.get("user_id")
        self.metrics["users_created"] += 1

        logger.info(f"[Analytics] 用户统计已更新: {user_id}")
        logger.info(f"[Analytics] 当前指标: {self.metrics}")

    async def update_order_metrics(self, event_data: Dict):
        """
        更新订单指标
        """
        order_id = event_data.get("order_id")
        amount = event_data.get("amount", 0)

        self.metrics["orders_created"] += 1
        self.metrics["total_revenue"] += amount

        logger.info(f"[Analytics] 订单指标已更新: {order_id}")
        logger.info(f"[Analytics] 当前指标: {self.metrics}")


class NotificationHandler:
    """
    通知处理器

    展示场景：
        - 推送通知
        - 短信通知
        - 应用内通知
    """

    async def send_push_notification(self, event_data: Dict):
        """
        发送推送通知
        """
        user_id = event_data.get("user_id")
        title = event_data.get("title", "新通知")
        body = event_data.get("body", "")

        logger.info(f"[Notification] 发送推送通知: 用户 {user_id}")
        logger.info(f"[Notification] 标题: {title}, 内容: {body}")

        await asyncio.sleep(0.5)

        logger.info(f"[Notification] ✓ 推送通知已发送")


# ═══════════════════════════════════════════════════════════════════
# FastAPI 应用
# ═══════════════════════════════════════════════════════════════════


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动：启动消费者
    logger.info("[App] 启动消费者...")

    processor = MessageProcessor(mock_mq)
    consumer = EventConsumer(mock_mq, processor)

    # 邮件处理器
    email_handler = EmailHandler()
    await consumer.subscribe(
        "emails",
        email_handler.send_welcome_email,
        group_id="email-senders",
    )

    # 分析处理器
    analytics_handler = AnalyticsHandler()
    await consumer.subscribe(
        "analytics",
        analytics_handler.update_user_stats,
        group_id="analytics-processors",
    )

    # 通知处理器
    notification_handler = NotificationHandler()
    await consumer.subscribe(
        "notifications",
        notification_handler.send_push_notification,
        group_id="notification-senders",
    )

    # 存储到 app state
    app.state.publisher = EventPublisher(mock_mq)
    app.state.email_handler = email_handler
    app.state.analytics_handler = analytics_handler

    logger.info("[App] 消费者已启动")
    yield

    # 关闭
    logger.info("[App] 应用关闭")


app = FastAPI(
    title="消息队列示例",
    description="展示消息队列集成的最佳实践",
    version="1.0.0",
    lifespan=lifespan,
)

# ═══════════════════════════════════════════════════════════════════
# 请求/响应模型
# ═══════════════════════════════════════════════════════════════════


class CreateUserRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    age: int = Field(..., ge=18, le=120)


class CreateOrderRequest(BaseModel):
    user_id: int
    product_id: int
    quantity: int = Field(..., ge=1)
    amount: float = Field(..., gt=0)


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    age: int
    created_at: datetime


class OrderResponse(BaseModel):
    id: int
    user_id: int
    amount: float
    status: str
    created_at: datetime


class MessageResponse(BaseModel):
    """异步任务响应"""
    message: str
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: str = "pending"


# ═══════════════════════════════════════════════════════════════════
# API 端点
# ═══════════════════════════════════════════════════════════════════


@app.get("/")
async def root():
    """健康检查"""
    return {
        "message": "消息队列示例",
        "status": "running",
    }


@app.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(request: CreateUserRequest):
    """
    创建用户（同步 + 异步）

    流程：
        1. 创建用户（同步，100ms）
        2. 发布事件到消息队列（1ms）
        3. 返回响应（总耗时 ~100ms）

    后台任务（异步）：
        - 邮件服务发送欢迎邮件（2000ms）
        - 分析服务更新统计（50ms）

    对比同步模式：
        同步模式总耗时：100 + 2000 = 2100ms
        异步模式总耗时：100ms（快 21 倍！）
    """
    # 1. 创建用户（模拟数据库操作）
    import time
    start = time.perf_counter()

    user_id = random.randint(1000, 9999)
    user = UserResponse(
        id=user_id,
        username=request.username,
        email=request.email,
        age=request.age,
        created_at=datetime.utcnow(),
    )

    # 模拟数据库延迟
    await asyncio.sleep(0.1)

    db_time = (time.perf_counter() - start) * 1000

    # 2. 发布事件
    publisher: EventPublisher = app.state.publisher

    # 发布欢迎邮件事件
    email_event = EmailEvent(
        event_type=EventType.EMAIL_SENT,
        data={
            "to": user.email,
            "subject": "欢迎！",
            "body": f"欢迎 {user.username}！",
            "username": user.username,
            "email": user.email,
        },
    )
    await publisher.publish("emails", email_event)

    # 发布用户统计事件
    analytics_event = BaseEvent(
        event_type=EventType.USER_CREATED,
        data={
            "user_id": user.id,
            "username": user.username,
            "created_at": user.created_at.isoformat(),
        },
    )
    await publisher.publish("analytics", analytics_event)

    # 3. 发送推送通知
    notification_event = BaseEvent(
        event_type=EventType.USER_CREATED,
        data={
            "user_id": user.id,
            "title": "欢迎加入！",
            "body": f"{user.username}，欢迎注册我们的平台！",
        },
    )
    await publisher.publish("notifications", notification_event)

    total_time = (time.perf_counter() - start) * 1000

    logger.info(f"[API] 用户创建完成: {user_id}, 耗时: {total_time:.2f}ms (DB: {db_time:.2f}ms)")

    return user


@app.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(request: CreateOrderRequest):
    """
    创建订单

    事件流程：
        1. 创建订单
        2. 发布订单创建事件
        3. 邮件服务发送确认邮件
        4. 分析服务更新指标
        5. 库存服务扣减库存
    """
    # 1. 创建订单
    order_id = random.randint(10000, 99999)
    order = OrderResponse(
        id=order_id,
        user_id=request.user_id,
        amount=request.amount,
        status="pending",
        created_at=datetime.utcnow(),
    )

    await asyncio.sleep(0.05)  # 模拟数据库操作

    # 2. 发布事件
    publisher: EventPublisher = app.state.publisher

    # 订单创建事件
    order_event = OrderEvent(
        event_type=EventType.ORDER_CREATED,
        data={
            "order_id": order.id,
            "user_id": order.user_id,
            "amount": order.amount,
            "status": order.status,
        },
    )
    await publisher.publish("orders", order_event)

    # 3. 发布分析事件
    analytics_event = BaseEvent(
        event_type=EventType.ORDER_CREATED,
        data={
            "order_id": order.id,
            "user_id": order.user_id,
            "amount": order.amount,
        },
    )
    await publisher.publish("analytics", analytics_event)

    logger.info(f"[API] 订单已创建: {order_id}")

    return order


@app.get("/emails/sent")
async def get_sent_emails():
    """查看已发送的邮件"""
    email_handler: EmailHandler = app.state.email_handler
    return {
        "count": len(email_handler.email_queue),
        "emails": email_handler.email_queue,
    }


@app.get("/analytics/metrics")
async def get_analytics_metrics():
    """查看分析指标"""
    analytics_handler: AnalyticsHandler = app.state.analytics_handler
    return analytics_handler.metrics


@app.get("/mq/dead-letter-queue")
async def get_dead_letter_queue():
    """查看死信队列"""
    return {
        "count": len(mock_mq._dead_letter_queue),
        "messages": mock_mq._dead_letter_queue,
    }


# ═══════════════════════════════════════════════════════════════════
# 演示和测试
# ═══════════════════════════════════════════════════════════════════


async def demo_basic_messaging():
    """演示基本消息传递"""
    print("\n" + "="*60)
    print("演示 1: 基本消息传递")
    print("="*60)

    publisher = EventPublisher(mock_mq)

    # 发布事件
    event = UserCreatedEvent(
        data={"username": "alice", "email": "alice@example.com"},
    )
    msg_id = await publisher.publish("users", event)
    print(f"✓ 事件已发布: {msg_id}")

    await asyncio.sleep(0.5)


async def demo_event_driven_architecture():
    """演示事件驱动架构"""
    print("\n" + "="*60)
    print("演示 2: 事件驱动架构")
    print("="*60)

    publisher = EventPublisher(mock_mq)

    # 1. 发布用户创建事件
    print("\n1. 发布用户创建事件")
    user_event = UserCreatedEvent(
        data={
            "user_id": 1,
            "username": "bob",
            "email": "bob@example.com",
        },
    )
    await publisher.publish("users", user_event)

    # 2. 邮件服务消费事件（发送欢迎邮件）
    print("\n2. 邮件服务处理事件")
    email_handler = EmailHandler()
    await email_handler.send_welcome_email(user_event.data)

    # 3. 分析服务消费事件（更新统计）
    print("\n3. 分析服务处理事件")
    analytics_handler = AnalyticsHandler()
    await analytics_handler.update_user_stats(user_event.data)

    await asyncio.sleep(0.5)


async def demo_retry_mechanism():
    """演示重试机制"""
    print("\n" + "="*60)
    print("演示 3: 消息重试机制")
    print("="*60)

    processor = MessageProcessor(mock_mq)

    # 创建一个会失败的消息
    envelope = {
        "id": "msg-123",
        "topic": "test",
        "message": {"test": "data"},
        "attempts": 0,
    }

    async def failing_handler(msg):
        raise Exception("模拟失败")

    print("\n尝试处理消息（会失败并重试）")
    await processor.process_with_retry(envelope, failing_handler)

    await asyncio.sleep(1)


async def demo_performance_comparison():
    """演示性能对比"""
    print("\n" + "="*60)
    print("演示 4: 同步 vs 异步性能对比")
    print("="*60)

    # 同步模式（模拟）
    print("\n同步模式（发送邮件）:")
    start = asyncio.get_event_loop().time()

    # 创建用户
    await asyncio.sleep(0.1)

    # 同步发送邮件（阻塞）
    await asyncio.sleep(2.0)

    sync_time = (asyncio.get_event_loop().time() - start) * 1000
    print(f"  总耗时: {sync_time:.2f}ms")

    # 异步模式
    print("\n异步模式（消息队列）:")
    start = asyncio.get_event_loop().time()

    # 创建用户
    await asyncio.sleep(0.1)

    # 发布到消息队列（非阻塞）
    await asyncio.sleep(0.001)

    # 后台发送邮件（异步）
    async def send_email_background():
        await asyncio.sleep(2.0)

    asyncio.create_task(send_email_background())

    async_time = (asyncio.get_event_loop().time() - start) * 1000
    print(f"  总耗时: {async_time:.2f}ms")
    print(f"  性能提升: {sync_time / async_time:.1f} 倍")

    await asyncio.sleep(0.5)


async def main():
    """运行所有演示"""
    print("\n🚀 消息队列集成示例")

    try:
        await demo_basic_messaging()
        await demo_event_driven_architecture()
        await demo_retry_mechanism()
        await demo_performance_comparison()

        print("\n" + "="*60)
        print("✅ 所有演示完成！")
        print("="*60)
        print("\n提示：运行 FastAPI 应用体验完整功能：")
        print("  uvicorn study.level4.examples.02_message_queue:app --reload")
        print("\nAPI 端点：")
        print("  POST   /users                    # 创建用户（触发多个事件）")
        print("  POST   /orders                   # 创建订单")
        print("  GET    /emails/sent              # 查看已发送邮件")
        print("  GET    /analytics/metrics        # 查看分析指标")
        print("  GET    /mq/dead-letter-queue     # 查看死信队列")

    except Exception as e:
        logger.error(f"演示失败: {e}")
        print(f"\n❌ 错误: {e}")


import random


if __name__ == "__main__":
    asyncio.run(main())
