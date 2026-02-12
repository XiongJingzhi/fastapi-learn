"""
01. Redis 缓存集成 - Redis Cache Integration
=============================================

这个示例展示了如何在 FastAPI 中集成 Redis 缓存来提升性能。

架构原则：
- Cache-Aside 模式：先查缓存，未命中再查数据库
- 缓存过期策略：设置合理的 TTL
- 缓存更新：写操作时删除缓存
- 防止缓存穿透：查询不存在的数据时缓存空值
- 防止缓存雪崩：设置随机 TTL 偏移
- 防止缓存击穿：使用分布式锁

运行要求：
- pip install redis
- Redis 服务器运行在 localhost:6379
"""

import asyncio
import json
import logging
import random
from contextlib import asynccontextmanager
from datetime import timedelta
from functools import wraps
from typing import Any, Optional, TypeVar, Generic

import redis.asyncio as aioredis
from fastapi import FastAPI, HTTPException, Depends, Header, status
from pydantic import BaseModel, Field

# ═══════════════════════════════════════════════════════════════════
# 日志配置
# ═══════════════════════════════════════════════════════════════════

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════
# Mock 数据库（生产环境中应该是真实的数据库）
# ═══════════════════════════════════════════════════════════════════


class MockDatabase:
    """模拟数据库"""

    def __init__(self):
        self._users = {
            1: {"id": 1, "username": "alice", "email": "alice@example.com", "age": 25},
            2: {"id": 2, "username": "bob", "email": "bob@example.com", "age": 30},
            3: {"id": 3, "username": "charlie", "email": "charlie@example.com", "age": 35},
        }
        self._products = {
            1: {"id": 1, "name": "Laptop", "price": 999.99, "stock": 10},
            2: {"id": 2, "name": "Mouse", "price": 29.99, "stock": 50},
            3: {"id": 3, "name": "Keyboard", "price": 79.99, "stock": 30},
        }

    async def get_user(self, user_id: int) -> Optional[dict]:
        """获取用户（模拟数据库查询，10ms）"""
        logger.info(f"[DB] 查询用户: {user_id}")
        await asyncio.sleep(0.01)  # 模拟数据库延迟
        return self._users.get(user_id)

    async def create_user(self, user_data: dict) -> dict:
        """创建用户"""
        logger.info(f"[DB] 创建用户: {user_data['username']}")
        await asyncio.sleep(0.01)
        new_id = max(self._users.keys()) + 1
        user_data["id"] = new_id
        self._users[new_id] = user_data
        return user_data

    async def update_user(self, user_id: int, user_data: dict) -> Optional[dict]:
        """更新用户"""
        logger.info(f"[DB] 更新用户: {user_id}")
        await asyncio.sleep(0.01)
        if user_id in self._users:
            self._users[user_id].update(user_data)
            return self._users[user_id]
        return None

    async def delete_user(self, user_id: int) -> bool:
        """删除用户"""
        logger.info(f"[DB] 删除用户: {user_id}")
        await asyncio.sleep(0.01)
        if user_id in self._users:
            del self._users[user_id]
            return True
        return False

    async def get_product(self, product_id: int) -> Optional[dict]:
        """获取产品"""
        logger.info(f"[DB] 查询产品: {product_id}")
        await asyncio.sleep(0.01)
        return self._products.get(product_id)


mock_db = MockDatabase()

# ═══════════════════════════════════════════════════════════════════
# Redis 连接管理
# ═══════════════════════════════════════════════════════════════════


class RedisManager:
    """
    Redis 连接管理器

    最佳实践：
    - 使用连接池管理连接
    - 应用启动时初始化，关闭时清理
    - 使用 decode_responses=True 自动解码字节
    """

    def __init__(self, url: str = "redis://localhost:6379"):
        self.url = url
        self._redis: Optional[aioredis.Redis] = None

    async def connect(self):
        """建立连接"""
        self._redis = await aioredis.from_url(
            self.url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=50,  # 连接池大小
        )
        logger.info("[Redis] 连接已建立")

    async def disconnect(self):
        """关闭连接"""
        if self._redis:
            await self._redis.close()
            logger.info("[Redis] 连接已关闭")

    @property
    def client(self) -> aioredis.Redis:
        """获取 Redis 客户端"""
        if not self._redis:
            raise RuntimeError("Redis 未连接")
        return self._redis


redis_manager = RedisManager()


# ═══════════════════════════════════════════════════════════════════
# 缓存装饰器
# ═══════════════════════════════════════════════════════════════════

T = TypeVar("T")


def cached(
    key_prefix: str,
    expire: int = 300,
    key_builder: Optional[callable] = None,
):
    """
    缓存装饰器

    参数：
        key_prefix: 缓存键前缀
        expire: 过期时间（秒），默认 5 分钟
        key_builder: 自定义键生成函数

    使用场景：
        - 缓存数据库查询结果
        - 缓存 API 调用结果
        - 缓存计算密集型操作

    示例：
        @cached("user", expire=600)
        async def get_user(user_id: int):
            return await db.get_user(user_id)
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            redis = redis_manager.client

            # 1. 生成缓存键
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # 默认键生成策略
                key_parts = [key_prefix]
                if args:
                    key_parts.extend(str(arg) for arg in args)
                if kwargs:
                    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = ":".join(key_parts)

            # 2. 尝试从缓存获取
            try:
                cached_value = await redis.get(cache_key)
                if cached_value:
                    logger.debug(f"[Cache] 命中: {cache_key}")
                    return json.loads(cached_value)
            except Exception as e:
                logger.error(f"[Cache] 读取失败: {e}")

            # 3. 缓存未命中，执行函数
            logger.debug(f"[Cache] 未命中: {cache_key}")
            result = await func(*args, **kwargs)

            # 4. 写入缓存
            if result is not None:
                try:
                    await redis.setex(
                        cache_key,
                        expire,
                        json.dumps(result, default=str)
                    )
                    logger.debug(f"[Cache] 已写入: {cache_key}")
                except Exception as e:
                    logger.error(f"[Cache] 写入失败: {e}")

            return result

        return wrapper

    return decorator


# ═══════════════════════════════════════════════════════════════════
# Cache-Aside 模式实现
# ═══════════════════════════════════════════════════════════════════


class CacheAsideRepository(Generic[T]):
    """
    Cache-Aside 缓存模式

    读取流程：
        1. 先查缓存
        2. 命中则返回
        3. 未命中则查数据库
        4. 写入缓存
        5. 返回数据

    写入流程：
        1. 更新数据库
        2. 删除缓存（而非更新，避免缓存脏数据）

    优点：
        - 简单直观
        - 缓存失效时自动从数据库加载
        - 适合读多写少的场景

    注意事项：
        - 防止缓存雪崩：添加随机 TTL 偏移
        - 防止缓存穿透：缓存空值
        - 防止缓存击穿：使用分布式锁
    """

    def __init__(
        self,
        redis: aioredis.Redis,
        key_prefix: str,
        default_ttl: int = 300,
    ):
        self.redis = redis
        self.key_prefix = key_prefix
        self.default_ttl = default_ttl

    def _make_key(self, identifier: Any) -> str:
        """生成缓存键"""
        return f"{self.key_prefix}:{identifier}"

    def _make_ttl(self, ttl: Optional[int] = None) -> int:
        """
        生成 TTL（添加随机偏移防止缓存雪崩）

        雪崩场景：大量缓存同时过期，导致数据库压力突增
        解决方案：在 TTL 基础上添加 ±10% 的随机偏移
        """
        if ttl:
            # 添加 ±10% 的随机偏移
            offset = int(ttl * 0.1)
            return ttl + random.randint(-offset, offset)
        return self.default_ttl

    async def get(
        self,
        identifier: Any,
        db_getter: callable,
        ttl: Optional[int] = None,
    ) -> Optional[T]:
        """
        获取数据（Cache-Aside）

        参数：
            identifier: 数据标识符
            db_getter: 数据库查询函数
            ttl: 过期时间（秒）

        返回：
            数据或 None
        """
        cache_key = self._make_key(identifier)

        # 1. 查缓存
        try:
            cached = await self.redis.get(cache_key)
            if cached:
                logger.info(f"[Cache] 命中: {cache_key}")
                return json.loads(cached)
        except Exception as e:
            logger.error(f"[Cache] 读取失败: {e}")

        # 2. 缓存未命中，查数据库
        logger.info(f"[Cache] 未命中: {cache_key}")
        data = await db_getter(identifier)

        if data is None:
            # 防止缓存穿透：缓存空值（TTL 较短）
            # 穿透场景：恶意查询不存在的数据，每次都查数据库
            # 解决方案：缓存空值，TTL 设置较短（如 60 秒）
            try:
                await self.redis.setex(cache_key, 60, json.dumps(None))
            except Exception as e:
                logger.error(f"[Cache] 写入空值失败: {e}")
            return None

        # 3. 写入缓存
        try:
            await self.redis.setex(
                cache_key,
                self._make_ttl(ttl),
                json.dumps(data, default=str)
            )
            logger.info(f"[Cache] 已写入: {cache_key}")
        except Exception as e:
            logger.error(f"[Cache] 写入失败: {e}")

        return data

    async def set(self, identifier: Any, data: Any, ttl: Optional[int] = None):
        """
        直接设置缓存

        使用场景：
            - 预热缓存
            - 更新缓存
        """
        cache_key = self._make_key(identifier)
        try:
            await self.redis.setex(
                cache_key,
                self._make_ttl(ttl),
                json.dumps(data, default=str)
            )
            logger.info(f"[Cache] 已设置: {cache_key}")
        except Exception as e:
            logger.error(f"[Cache] 设置失败: {e}")

    async def delete(self, identifier: Any):
        """
        删除缓存

        注意：写操作后删除缓存，而非更新
        原因：避免并发写导致缓存和数据库不一致
        """
        cache_key = self._make_key(identifier)
        try:
            await self.redis.delete(cache_key)
            logger.info(f"[Cache] 已删除: {cache_key}")
        except Exception as e:
            logger.error(f"[Cache] 删除失败: {e}")

    async def invalidate_pattern(self, pattern: str):
        """
        批量删除缓存（模糊匹配）

        使用场景：
            - 删除用户的所有相关缓存
            - 清空特定前缀的缓存

        示例：
            await repo.invalidate_pattern("user:*")  # 删除所有用户缓存
        """
        try:
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                await self.redis.delete(*keys)
                logger.info(f"[Cache] 批量删除: {len(keys)} 个键")
        except Exception as e:
            logger.error(f"[Cache] 批量删除失败: {e}")


# ═══════════════════════════════════════════════════════════════════
# 分布式锁
# ═══════════════════════════════════════════════════════════════════


class DistributedLock:
    """
    Redis 分布式锁

    使用场景：
        - 防止缓存击穿：热点数据过期时，只允许一个请求查数据库
        - 防止重复任务：确保同一时间只有一个任务执行
        - 资源互斥：保护临界资源

    击穿场景：
        热点数据过期瞬间，大量请求同时查询数据库
        例如：秒杀活动开始时，商品详情缓存过期

    实现原理：
        1. SET NX（只在键不存在时设置）
        2. 设置过期时间（防止死锁）
        3. 释放时检查锁是否属于自己

    注意：
        - 这是简化实现，生产环境建议使用 Redisson 或 redlock
    """

    def __init__(
        self,
        redis: aioredis.Redis,
        lock_name: str,
        expire: int = 10,
        auto_renewal: bool = False,
    ):
        self.redis = redis
        self.lock_key = f"lock:{lock_name}"
        self.expire = expire
        self.auto_renewal = auto_renewal
        self._lock_value: Optional[str] = None
        self._renewal_task: Optional[asyncio.Task] = None

    async def __aenter__(self):
        """获取锁"""
        import uuid

        self._lock_value = str(uuid.uuid4())

        while True:
            # 尝试获取锁
            acquired = await self.redis.set(
                self.lock_key,
                self._lock_value,
                nx=True,  # 只在键不存在时设置
                ex=self.expire,
            )

            if acquired:
                logger.info(f"[Lock] 获取锁成功: {self.lock_key}")

                # 自动续期（看门狗）
                if self.auto_renewal:
                    self._renewal_task = asyncio.create_task(
                        self._auto_renew()
                    )

                return self

            # 锁已被占用，等待重试
            logger.info(f"[Lock] 锁被占用，等待: {self.lock_key}")
            await asyncio.sleep(0.1)

    async def __aexit__(self, exc_type, exc_val, tb):
        """释放锁"""
        # 停止自动续期
        if self._renewal_task:
            self._renewal_task.cancel()
            try:
                await self._renewal_task
            except asyncio.CancelledError:
                pass

        # 检查锁是否属于自己，避免误删
        script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        try:
            result = await self.redis.eval(
                script,
                1,
                self.lock_key,
                self._lock_value,
            )
            if result:
                logger.info(f"[Lock] 释放锁成功: {self.lock_key}")
            else:
                logger.warning(f"[Lock] 锁不属于自己: {self.lock_key}")
        except Exception as e:
            logger.error(f"[Lock] 释放锁失败: {e}")

    async def _auto_renew(self):
        """自动续期（看门狗）"""
        while True:
            await asyncio.sleep(self.expire / 2)  # 每隔一半时间续期

            script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("expire", KEYS[1], ARGV[2])
            else
                return 0
            end
            """

            try:
                await self.redis.eval(
                    script,
                    1,
                    self.lock_key,
                    self._lock_value,
                    self.expire,
                )
                logger.debug(f"[Lock] 自动续期: {self.lock_key}")
            except Exception as e:
                logger.error(f"[Lock] 自动续期失败: {e}")
                break


# ═══════════════════════════════════════════════════════════════════
# 业务模型
# ═══════════════════════════════════════════════════════════════════


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    age: int = Field(..., ge=18, le=120)


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    age: int


class UserStats(BaseModel):
    """用户统计信息（计算密集型）"""
    user_id: int
    total_orders: int
    total_spent: float
    avg_order_value: float
    favorite_category: str


# ═══════════════════════════════════════════════════════════════════
# 用户服务（带缓存）
# ═══════════════════════════════════════════════════════════════════


class UserService:
    """
    用户服务（使用 Cache-Aside 模式）

    展示场景：
        1. 读取缓存（热点数据）
        2. 写入删除缓存
        3. 缓存装饰器
        4. 防止缓存击穿
    """

    def __init__(self, redis: aioredis.Redis):
        self.redis = redis
        self.user_cache = CacheAsideRepository(redis, "user", default_ttl=300)
        self.stats_cache = CacheAsideRepository(redis, "stats", default_ttl=600)

    async def get_user(self, user_id: int) -> Optional[UserResponse]:
        """
        获取用户（使用缓存）

        缓存策略：Cache-Aside
        TTL: 5 分钟
        """
        user = await self.user_cache.get(
            user_id,
            lambda uid: mock_db.get_user(uid),
            ttl=300,
        )

        if user:
            return UserResponse(**user)
        return None

    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """
        创建用户

        缓存策略：创建后不需要缓存（下次查询时缓存）
        """
        user = await mock_db.create_user(user_data.model_dump())
        logger.info(f"[Service] 用户已创建: {user['id']}")
        return UserResponse(**user)

    async def update_user(
        self,
        user_id: int,
        user_data: dict,
    ) -> Optional[UserResponse]:
        """
        更新用户

        缓存策略：更新后删除缓存（而非更新）
        原因：避免并发更新导致缓存脏数据
        """
        user = await mock_db.update_user(user_id, user_data)

        if user:
            # 删除缓存
            await self.user_cache.delete(user_id)
            logger.info(f"[Service] 用户已更新，缓存已删除: {user_id}")
            return UserResponse(**user)

        return None

    async def delete_user(self, user_id: int) -> bool:
        """
        删除用户

        缓存策略：删除后删除缓存
        """
        success = await mock_db.delete_user(user_id)

        if success:
            # 删除缓存
            await self.user_cache.delete(user_id)
            # 删除相关缓存（如统计信息）
            await self.stats_cache.delete(user_id)
            logger.info(f"[Service] 用户已删除，缓存已清除: {user_id}")

        return success

    @cached("user_stats", expire=600)
    async def get_user_stats(self, user_id: int) -> UserStats:
        """
        获取用户统计（使用缓存装饰器）

        这是计算密集型操作，适合缓存
        TTL: 10 分钟
        """
        logger.info(f"[Service] 计算用户统计: {user_id}")

        # 模拟复杂计算（100ms）
        await asyncio.sleep(0.1)

        # 模拟统计数据
        stats = UserStats(
            user_id=user_id,
            total_orders=random.randint(10, 100),
            total_spent=random.uniform(500, 5000),
            avg_order_value=random.uniform(30, 100),
            favorite_category=random.choice(["Electronics", "Books", "Clothing"]),
        )

        return stats

    async def get_user_with_lock(self, user_id: int) -> Optional[UserResponse]:
        """
        获取用户（防止缓存击穿）

        场景：热点数据（如 VIP 用户）缓存过期瞬间，
        大量并发请求会同时查询数据库

        解决：使用分布式锁，只允许一个请求查数据库，
        其他请求等待缓存更新完成
        """
        cache_key = f"user:{user_id}"

        # 1. 先尝试从缓存获取
        cached = await self.redis.get(cache_key)
        if cached:
            return UserResponse(**json.loads(cached))

        # 2. 缓存未命中，使用分布式锁
        lock = DistributedLock(
            self.redis,
            f"cache_load:{user_id}",
            expire=10,
        )

        async with lock:
            # 3. 获取锁后，再次检查缓存（双重检查）
            cached = await self.redis.get(cache_key)
            if cached:
                return UserResponse(**json.loads(cached))

            # 4. 查询数据库
            logger.info(f"[Service] 使用锁查询数据库: {user_id}")
            user = await mock_db.get_user(user_id)

            if user:
                # 5. 写入缓存
                await self.user_cache.set(user_id, user, ttl=300)
                return UserResponse(**user)

        return None


# ═══════════════════════════════════════════════════════════════════
# FastAPI 应用
# ═══════════════════════════════════════════════════════════════════


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动
    await redis_manager.connect()
    yield
    # 关闭
    await redis_manager.disconnect()


app = FastAPI(
    title="Redis 缓存示例",
    description="展示 Redis 缓存集成的最佳实践",
    version="1.0.0",
    lifespan=lifespan,
)

# 全局服务实例
user_service: Optional[UserService] = None


def get_user_service() -> UserService:
    """获取用户服务（依赖注入）"""
    redis = redis_manager.client
    return UserService(redis)


# ═══════════════════════════════════════════════════════════════════
# API 端点
# ═══════════════════════════════════════════════════════════════════


@app.get("/")
async def root():
    """健康检查"""
    return {
        "message": "Redis 缓存示例",
        "status": "running",
    }


@app.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    service: UserService = Depends(get_user_service),
):
    """
    创建用户

    缓存策略：创建后不缓存（懒加载）
    """
    return await service.create_user(user_data)


@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
):
    """
    获取用户（使用缓存）

    性能对比：
        - 缓存命中：~1ms
        - 缓存未命中：~10ms（数据库查询）
        - 提升：10 倍

    缓存策略：Cache-Aside
    TTL: 5 分钟
    """
    user = await service.get_user(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户 {user_id} 不存在",
        )

    return user


@app.get("/users/{user_id}/stats", response_model=UserStats)
async def get_user_stats(
    user_id: int,
    service: UserService = Depends(get_user_service),
):
    """
    获取用户统计（使用缓存装饰器）

    这是计算密集型操作（100ms），非常适合缓存

    缓存策略：装饰器缓存
    TTL: 10 分钟
    """
    return await service.get_user_stats(user_id)


@app.get("/users/{user_id}/with-lock", response_model=UserResponse)
async def get_user_with_lock(
    user_id: int,
    service: UserService = Depends(get_user_service),
):
    """
    获取用户（防止缓存击穿）

    适用场景：
        - 热点数据（如 VIP 用户）
        - 缓存过期瞬间高并发

    实现方式：分布式锁
    """
    user = await service.get_user_with_lock(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户 {user_id} 不存在",
        )

    return user


@app.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: dict,
    service: UserService = Depends(get_user_service),
):
    """
    更新用户

    缓存策略：更新后删除缓存

    为什么删除而不是更新缓存？
        - 避免并发更新导致缓存脏数据
        - 删除后下次查询会自动加载最新数据
        - 简单且可靠
    """
    user = await service.update_user(user_id, user_data)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户 {user_id} 不存在",
        )

    return user


@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
):
    """
    删除用户

    缓存策略：删除后清除所有相关缓存
    """
    success = await service.delete_user(user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户 {user_id} 不存在",
        )


@app.post("/cache/warmup")
async def warmup_cache(service: UserService = Depends(get_user_service)):
    """
    缓存预热

    场景：应用启动时或定时任务中，预先加载热点数据到缓存

    好处：
        - 避免启动初期大量缓存未命中
        - 提升首屏性能
    """
    # 预热用户数据
    for user_id in [1, 2, 3]:
        user = await mock_db.get_user(user_id)
        if user:
            await service.user_cache.set(user_id, user, ttl=600)

    return {"message": "缓存预热完成", "count": 3}


@app.post("/cache/clear")
async def clear_cache(
    pattern: str = "user:*",
    service: UserService = Depends(get_user_service),
):
    """
    清除缓存（批量）

    使用场景：
        - 批量更新后清除相关缓存
        - 紧急下线时清空所有缓存

    示例：
        POST /cache/clear?pattern=user:*
        POST /cache/clear?pattern=stats:*
    """
    await service.user_cache.invalidate_pattern(pattern)

    return {
        "message": f"已清除匹配 '{pattern}' 的缓存",
    }


# ═══════════════════════════════════════════════════════════════════
# 演示和测试
# ═══════════════════════════════════════════════════════════════════


async def demo_basic_usage():
    """演示基本使用"""
    print("\n" + "="*60)
    print("演示 1: 基本 Redis 操作")
    print("="*60)

    await redis_manager.connect()
    redis = redis_manager.client

    # 基本操作
    await redis.set("demo:key1", "value1")
    value = await redis.get("demo:key1")
    print(f"✓ SET/GET: {value}")

    # 带过期时间
    await redis.setex("demo:key2", 5, "value2")
    ttl = await redis.ttl("demo:key2")
    print(f"✓ SETEX with TTL: {ttl} 秒")

    # 删除
    await redis.delete("demo:key1")
    exists = await redis.exists("demo:key1")
    print(f"✓ DELETE: 存在? {exists}")

    # Hash 操作
    await redis.hset("demo:user:1", "username", "alice")
    await redis.hset("demo:user:1", "email", "alice@example.com")
    user = await redis.hgetall("demo:user:1")
    print(f"✓ HGETALL: {user}")

    await redis_manager.disconnect()


async def demo_cache_performance():
    """演示缓存性能"""
    print("\n" + "="*60)
    print("演示 2: 缓存性能对比")
    print("="*60)

    await redis_manager.connect()
    service = UserService(redis_manager.client)

    # 第一次查询（缓存未命中）
    print("\n第一次查询（缓存未命中）：")
    import time
    start = time.perf_counter()
    await service.get_user(1)
    elapsed1 = (time.perf_counter() - start) * 1000
    print(f"  耗时: {elapsed1:.2f}ms (数据库查询)")

    # 第二次查询（缓存命中）
    print("\n第二次查询（缓存命中）：")
    start = time.perf_counter()
    await service.get_user(1)
    elapsed2 = (time.perf_counter() - start) * 1000
    print(f"  耗时: {elapsed2:.2f}ms (缓存读取)")

    # 性能提升
    speedup = elapsed1 / elapsed2
    print(f"\n✓ 性能提升: {speedup:.1f} 倍")

    await redis_manager.disconnect()


async def demo_cache_aside():
    """演示 Cache-Aside 模式"""
    print("\n" + "="*60)
    print("演示 3: Cache-Aside 模式")
    print("="*60)

    await redis_manager.connect()
    redis = redis_manager.client
    cache = CacheAsideRepository(redis, "demo_user", default_ttl=60)

    # 第一次读取（缓存未命中）
    print("\n第一次读取（缓存未命中）：")
    user = await cache.get(1, lambda uid: mock_db.get_user(uid))
    print(f"  结果: {user}")

    # 第二次读取（缓存命中）
    print("\n第二次读取（缓存命中）：")
    user = await cache.get(1, lambda uid: mock_db.get_user(uid))
    print(f"  结果: {user}")

    # 更新后删除缓存
    print("\n更新用户（删除缓存）：")
    await cache.delete(1)
    print("  ✓ 缓存已删除")

    # 再次读取（缓存未命中）
    print("\n再次读取（重新缓存）：")
    user = await cache.get(1, lambda uid: mock_db.get_user(uid))
    print(f"  结果: {user}")

    await redis_manager.disconnect()


async def main():
    """运行所有演示"""
    print("\n🚀 Redis 缓存集成示例")

    try:
        await demo_basic_usage()
        await demo_cache_performance()
        await demo_cache_aside()

        print("\n" + "="*60)
        print("✅ 所有演示完成！")
        print("="*60)
        print("\n提示：运行 FastAPI 应用体验完整功能：")
        print("  uvicorn study.level4.examples.01_redis_cache:app --reload")
        print("\nAPI 端点：")
        print("  GET    /users/{id}              # 获取用户（缓存）")
        print("  POST   /users                   # 创建用户")
        print("  GET    /users/{id}/stats        # 获取统计（缓存装饰器）")
        print("  GET    /users/{id}/with-lock    # 获取用户（防击穿）")
        print("  PUT    /users/{id}              # 更新用户（删除缓存）")
        print("  DELETE /users/{id}              # 删除用户（清除缓存）")
        print("  POST   /cache/warmup            # 缓存预热")
        print("  POST   /cache/clear             # 清除缓存")

    except Exception as e:
        logger.error(f"演示失败: {e}")
        print(f"\n❌ 错误: {e}")
        print("\n请确保 Redis 服务运行在 localhost:6379")


if __name__ == "__main__":
    asyncio.run(main())
