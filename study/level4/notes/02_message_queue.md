# 02. 消息队列 - Message Queue (Kafka/RabbitMQ)

## 📍 在架构中的位置

**从同步到异步：提升系统响应速度**

```
┌─────────────────────────────────────────────────────────────┐
│          同步操作（阻塞）                                     │
└─────────────────────────────────────────────────────────────┘

用户注册：
    用户点击"注册"按钮
    → 创建用户账户（100ms）
    → 发送欢迎邮件（2000ms）❌ 慢！
    → 返回响应（2100ms）

用户体验：慢！
- 用户等待 2 秒
- 如果邮件服务挂了？注册失败！

═══════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────┐
│          异步操作（消息队列）                                │
└─────────────────────────────────────────────────────────────┘

用户注册：
    用户点击"注册"按钮
    → 创建用户账户（100ms）
    → 写入消息队列（1ms）
    → 返回响应（101ms）✅ 快！

后台任务：
    消费者从队列读取消息
    → 发送欢迎邮件（2000ms，异步）

用户体验：快！
- 用户只等待 100ms
- 邮件服务挂了？注册仍然成功！
```

**🎯 你的学习目标**：掌握消息队列集成，实现异步处理。

---

## 🎯 什么是消息队列？

### 生活类比：餐厅点餐

**同步模式（没有消息队列）**：

```
顾客 → 服务员 → 厨房 → 厨师 → 做菜 → 服务员 → 顾客

问题：
- 服务员一直在厨房等待（无法服务其他顾客）
- 厨师忙碌时，顾客必须等待
- 无法处理高并发
```

**异步模式（有消息队列）**：

```
顾客 → 服务员 → 点菜单（订单单） → 订单队列

厨房：
    厨师从订单队列取单
    → 做菜
    → 菜做好了

好处：
- 服务员不用在厨房等待（可以服务更多顾客）
- 厨师可以按自己的节奏做菜
- 订单不会丢失（在队列中排队）
```

---

### 消息队列核心概念

```
┌─────────────────────────────────────────────────────────────┐
│                  消息队列架构                                │
└─────────────────────────────────────────────────────────────┘

生产者（Producer）                  消费者（Consumer）
     │                                    │
     ├─ 用户注册                           ├─ 邮件发送服务
     ├─ 订单创建                           ├─ 数据分析服务
     ├─ 文件上传                           ├─ 日志处理服务
     └─ ...                               └─ ...

     │                                    │
     ▼                                    ▼
┌─────────────────────────────────────────────────────────────┐
│                    消息队列                                 │
│                                                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐      │
│  │ Queue 1 │  │ Queue 2 │  │ Queue 3 │  │ Queue 4 │      │
│  │ 邮件队列 │  │ 订单队列 │  │ 日志队列 │  │ ...    │      │
│  └─────────┘  └─────────┘  └─────────└  └─────────┘      │
│                                                             │
│  特性：                                                       │
│  - FIFO（先进先出）                                            │
│  - 持久化（消息不丢失）                                        │
│  - 解耦（生产者和消费者独立）                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Kafka vs RabbitMQ

### 对比表格

| 特性 | Kafka | RabbitMQ |
|------|-------|-----------|
| **吞吐量** | 极高（百万级/秒） | 高（万级/秒） |
| **延迟** | 低（毫秒级） | 稍高（毫秒级） |
| **复杂度** | 简单 | 复杂 |
| **路由** | 简单（topic） | 复杂（exchange） |
| **持久化** | 磁盘 | 内存/磁盘 |
| **适用场景** | 大数据、日志 | 企业消息、复杂路由 |
| **社区** | 非常活跃 | 成熟稳定 |

---

## 🔧 Kafka 基础

### 安装和启动

**安装 Kafka**：

```bash
# 下载 Kafka
wget https://downloads.apache.org/kafka/3.6.0/kafka_2.13-3.6.0.tgz
tar -xzf kafka_2.13-3.6.0.tgz
cd kafka_2.13-3.6.0

# 启动 Zookeeper
bin/zookeeper-server-start.sh

# 启动 Kafka
bin/kafka-server-start.sh

# 创建主题
bin/kafka-topics.sh --create --topic users --bootstrap-server localhost:9092
```

---

### Python 客户端（aiokafka）

**安装**：

```bash
pip install aiokafka
```

**生产者**：

```python
from aiokafka import AIOKafkaProducer
import asyncio

async def send_message(topic: str, message: dict):
    """发送消息到 Kafka"""

    producer = AIOKafkaProducer(
        bootstrap_servers="localhost:9092"
    )

    # 序列化消息
    import json
    value = json.dumps(message).encode('utf-8')

    # 发送消息
    await producer.send_and_wait(
        topic=topic,
        value=value
    )

    await producer.stop()

# 使用
asyncio.run(send_message("users", {"user_id": 1, "action": "created"}))
```

---

**消费者**：

```python
from aiokafka import AIOKafkaConsumer
import asyncio

async def consume_messages(topic: str):
    """消费 Kafka 消息"""

    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers="localhost:9092",
        group_id="my-group"  # 消费者组
        auto_offset_reset='earliest'  # 从最早的消息开始
    )

    await consumer.start()

    try:
        async for msg in consumer:
            # 解析消息
            import json
            message = json.loads(msg.value)
            print(f"Received: {message}")

            # 处理消息
            await process_message(message)

    finally:
        await consumer.stop()

# 使用
asyncio.run(consume_messages("users"))
```

---

## 🎨 FastAPI 集成 Kafka

### 异步后台任务

```python
from fastapi import FastAPI, BackgroundTasks, Depends
from aiokafka import AIOKafkaProducer
import json

app = FastAPI()

# ═══════════════════════════════════════════════════════════
# 1. 定义后台任务
# ═══════════════════════════════════════════════════════════

background_tasks = BackgroundTasks()

def get_kafka_producer() -> AIOKafkaProducer:
    """获取 Kafka 生产者（全局单例）"""
    return background_tasks.state["kafka_producer"]

# ═══════════════════════════════════════════════════════════
# 2. 应用启动时创建生产者
# ═══════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    # 创建 Kafka 生产者
    producer = AIOKafkaProducer(
        bootstrap_servers="localhost:9092"
    )
    await producer.start()

    # 存储到后台任务状态
    background_tasks.state["kafka_producer"] = producer

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理"""
    producer = background_tasks.state.get("kafka_producer")
    if producer:
        await producer.stop()

# ═══════════════════════════════════════════════════════════
# 3. 发送消息的辅助函数
# ═══════════════════════════════════════════════════════════

async def publish_event(topic: str, event: dict):
    """发布事件到 Kafka"""
    producer = get_kafka_producer()
    value = json.dumps(event).encode('utf-8')

    await producer.send_and_wait(
        topic,
        value=value
    )

# ═══════════════════════════════════════════════════════════
# 4. Endpoints
# ═══════════════════════════════════════════════════════════

@app.post("/users")
async def create_user(user: UserCreate):
    """创建用户（发送事件）"""
    # 1. 创建用户
    user = await service.create_user(user)

    # 2. 发布事件（异步）
    await publish_event("users", {
        "action": "user.created",
        "user_id": user.id,
        "username": user.username
    })

    return user
```

---

## 🔁 实际场景：邮件发送

### 异步邮件发送

```python
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

# ═══════════════════════════════════════════════════════════
# 1. 定义邮件事件
# ═══════════════════════════════════════════════════════════

class EmailEvent(BaseModel):
    to: str
    subject: str
    body: str

# ═══════════════════════════════════════════════════════════
# 2. Kafka 消费者（邮件发送服务）
# ═══════════════════════════════════════════════════════════

class EmailConsumer:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.smtp_username = "your-email@gmail.com"
        self.smtp_password = "your-app-password"

    async def start_consuming(self):
        """开始消费邮件队列"""
        consumer = AIOKafkaConsumer(
            "emails",
            bootstrap_servers="localhost:9092",
            group_id="email-senders"
        )

        await consumer.start()

        try:
            async for msg in consumer:
                # 解析邮件事件
                email_event = EmailEvent(**json.loads(msg.value))

                # 发送邮件
                await self.send_email(email_event)

        finally:
            await consumer.stop()

    async def send_email(self, event: EmailEvent):
        """发送邮件"""
        message = MIMEMultipart()
        message['From'] = self.smtp_username
        message['To'] = event.to
        message['Subject'] = event.subject

        message.attach(MIMEText(event.body))

        # 连接 SMTP 服务器
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(message)

# ═══════════════════════════════════════════════════════════
# 3. FastAPI Endpoint
# ═══════════════════════════════════════════════════════════

@app.post("/users")
async def create_user(user: UserCreate):
    """创建用户（发送欢迎邮件）"""
    # 1. 创建用户（100ms）
    user = await service.create_user(user)

    # 2. 发送欢迎邮件到队列（1ms）
    await publish_event("emails", {
        "to": user.email,
        "subject": "Welcome!",
        "body": f"Welcome {user.username}!"
    })

    # 3. 立即返回（总耗时 101ms）
    return user

# 后台：邮件发送服务消费队列（2000ms，异步）
```

---

## 🎯 消息模式

### 1. 工作队列（Work Queue）

**场景**：处理耗时任务

```python
# 生产者：创建任务
@app.post("/process-video")
async def process_video(video_id: int):
    """提交视频处理任务"""

    # 发送到任务队列
    await publish_event("video-processing", {
        "video_id": video_id,
        "status": "pending"
    })

    return {"message": "Video submitted for processing"}

# 消费者：处理任务
class VideoProcessor:
    async def start_consuming(self):
        consumer = AIOKafkaConsumer(
            "video-processing",
            bootstrap_servers="localhost:9092",
            group_id="video-processors"
        )

        await consumer.start()

        async for msg in consumer:
            task = json.loads(msg.value)

            # 处理视频（耗时）
            await process_video(task["video_id"])

            # 更新状态
            await publish_event("video-processed", {
                "video_id": task["video_id"],
                "status": "completed"
            })
```

---

### 2. 发布-订阅（Pub/Sub）

**场景**：事件广播

```python
# 发布者：发布文章
@app.post("/posts")
async def create_post(post: PostCreate):
    post = await service.create_post(post)

    # 发布事件（多个消费者订阅）
    await publish_event("posts", {
        "action": "post.created",
        "post_id": post.id,
        "title": post.title
    })

    return post

# 消费者 1：缓存失效
class CacheInvalidator:
    async def start_consuming():
        consumer = AIOKafkaConsumer("posts", ...)

        async for msg in consumer:
            event = json.loads(msg.value)

            # 删除相关缓存
            await cache.delete(f"post:{event['post_id']}")

# 消费者 2：通知订阅者
class Notifier:
    async def start_consuming():
        consumer = AOCafkaConsumer("posts", ...)

        async for msg in consumer:
            event = json.loads(msg.value)

            # 发送通知
            await send_notification(event['title'])
```

---

## 🔐 消息可靠性

### 确保消息不丢失

**配置 Kafka**：

```python
# 生产者配置
producer = AIOKafkaProducer(
    bootstrap_servers="localhost:9092",
    # 可靠性配置
    ack='all',              # 等待所有副本确认
    retries=3,              # 重试 3 次
    max_in_flight=1,        # 同时只发送 1 条消息
    enable_idempotence=True  # 幂等性（去重）
)
```

**消费者配置**：

```python
# 消费者配置
consumer = AIOKafkaConsumer(
    "emails",
    bootstrap_servers="localhost:9092",
    group_id="email-senders",
    # 可靠性配置
    auto_offset_reset='earliest',  # 从最早的消息开始
    enable_auto_commit=False,     # 手动提交 offset
    max_poll_records=10,          # 每次最多拉取 10 条
    session_timeout_ms=30000       # 30 秒会话超时
)

await consumer.start()

try:
    async for msg in consumer:
        # 处理消息
        await process_message(msg)

        # 手动提交 offset（确认处理成功）
        await consumer.commit()

finally:
    await consumer.stop()
```

---

## 🎯 小实验：自己动手

### 实验 1：基本消息发送

```python
# 发送简单消息
import asyncio
from aiokafka import AIOKafkaProducer

async def send_message():
    producer = AIOKafkaProducer(bootstrap_servers="localhost:9092")
    await producer.start()

    try:
        await producer.send_and_wait(
            "test-topic",
            b"Hello Kafka!"
        )
    finally:
        await producer.stop()

asyncio.run(send_message())
```

---

### 实验 2：消费消息

```python
# 消费消息
async def consume_messages():
    consumer = AIOKafkaConsumer(
        "test-topic",
        bootstrap_servers="localhost:9092",
        group_id="test-group"
    )

    await consumer.start()

    try:
        async for msg in consumer:
            print(f"Received: {msg.value.decode()}")
            await consumer.commit()

    finally:
        await consumer.stop()

asyncio.run(consume_messages())
```

---

## 📚 检查理解

回答这些问题来测试你的理解：

1. **为什么需要消息队列？**
   - 提示：异步处理、解耦、削峰填谷

2. **Kafka 和 RabbitMQ 的区别？**
   - 提示：吞吐量、复杂度

3. **什么是生产者和消费者？**
   - 提示：发送消息、处理消息

4. **如何确保消息不丢失？**
   - 提示：ack、retries、手动提交

5. **什么是工作队列模式？**
   - 提示：异步处理耗时任务

---

## 🚀 下一步

现在你已经掌握了消息队列基础，接下来：

1. **学习外部 API 集成**：`notes/03_external_api.md`
2. **查看实际代码**：`examples/02_message_queue.py`

**记住**：消息队列让应用解耦、异步、高可靠！**

---

**费曼技巧总结**：
- ✅ 餐厅点餐类比
- ✅ 同步 vs 异步对比
- ✅ Kafka vs RabbitMQ 对比
- ✅ 完整的代码示例
- ✅ 实际场景（邮件发送）
- ✅ 消息模式（工作队列、发布订阅）
- ✅ 可靠性配置
