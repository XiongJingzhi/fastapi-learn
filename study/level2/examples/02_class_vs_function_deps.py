"""
阶段 2.2: 类依赖 vs 函数依赖

学习目标:
1. 理解函数依赖的使用场景
2. 掌握类依赖的定义和使用
3. 学习带初始化参数的类依赖
4. 对比类依赖和函数依赖的优劣
5. 了解可调用对象作为依赖

运行方式:
    uvicorn study.level2.examples.02_class_vs_function_deps:app --reload
"""

from typing import Optional
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, Field

app = FastAPI(
    title="类依赖 vs 函数依赖",
    description="演示不同类型的依赖注入方式",
    version="2.0.0"
)


# ==================== 场景 1: 函数依赖 ====================

# ══════════════════════════════════════════════════════════════
# 函数依赖：最简单的方式
# ══════════════════════════════════════════════════════════════

def get_user_agent(user_agent: Optional[str] = None):
    """
    场景 1: 函数依赖

    💡 使用场景：
    - 简单的依赖（不需要状态）
    - 纯函数计算
    - 参数转换和验证

    ✅ 优势：
    - 简单直观
    - 易于理解
    - 适合简单逻辑

    ⚠️  限制：
    - 无法保存状态（每次调用都是新的）
    - 无法持有资源（如数据库连接）
    """
    return user_agent or "Unknown"


@app.get("/func/agent")
async def check_agent(
    agent: str = Depends(get_user_agent)
):
    """使用函数依赖"""
    return {
        "message": "使用函数依赖",
        "user_agent": agent,
        "type": "function_dependency"
    }


# ==================== 场景 2: 类依赖（基础）====================

# ══════════════════════════════════════════════════════════════
# 类依赖：FastAPI 的"魔法"
# ══════════════════════════════════════════════════════════════

class CommonQueryParams:
    """
    场景 2: 类依赖（基础）

    💡 FastAPI 的特殊处理：
    - 类的 __init__ 参数会被自动从请求中提取
    - 就像 endpoint 函数的参数一样
    - 不需要手动调用 Depends()

    🎯 关键点：
    1. __init__ 的参数名就是查询参数名
    2. 可以使用 Field() 进行验证
    3. 可以设置默认值

    ✅ 优势：
    - 可以保存状态
    - 可以有多个方法
    - 更符合 OOP 思想
    """

    def __init__(
        self,
        skip: int = 0,
        limit: int = 100,
        debug: bool = False
    ):
        """
        FastAPI 会自动调用 __init__
        并从请求中提取参数
        """
        self.skip = skip
        self.limit = limit
        self.debug = debug
        self.timestamp = datetime.now()

    def get_range(self) -> tuple:
        """方法：计算范围"""
        return (self.skip, self.skip + self.limit)

    def is_debug(self) -> bool:
        """方法：是否调试模式"""
        return self.debug


@app.get("/class/items")
async def read_items(
    commons: CommonQueryParams = Depends(CommonQueryParams)
):
    """
    使用类依赖

    🔍 FastAPI 的魔法：
    1. 看到依赖是 CommonQueryParams 类
    2. 自动调用 CommonQueryParams(skip=0, limit=100)
    3. 参数从请求中自动提取
    4. 返回的实例注入到 endpoint
    """
    start, end = commons.get_range()

    return {
        "message": "使用类依赖",
        "skip": commons.skip,
        "limit": commons.limit,
        "debug": commons.is_debug(),
        "range": (start, end),
        "timestamp": commons.timestamp.isoformat(),
        "type": "class_dependency"
    }


# ==================== 场景 3: 带初始化参数的类 ====================

class DatabaseConnection:
    """
    场景 3: 带初始化参数的类

    💡 这种类依赖的特点：
    - 需要在创建时传入配置参数
    - 通常用于数据库连接、API 客户端等
    - 初始化参数不是从请求中获取的

    ⚠️  注意：
    - __init__ 的参数需要提供默认值
    - 或者使用工厂函数
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "mydb"
    ):
        """
        初始化数据库连接

        ⚠️  这些参数不是从请求中获取的
        而是配置参数
        """
        self.host = host
        self.port = port
        self.database = database
        self.connected_at = datetime.now()

    def connect(self):
        """连接数据库"""
        return f"Connected to {self.host}:{self.port}/{self.database}"

    def query(self, sql: str):
        """执行查询"""
        return f"Executing: {sql}"


# 方式 1: 直接使用类（参数使用默认值）
@app.get("/db/default")
async def use_default_db(
    db: DatabaseConnection = Depends(DatabaseConnection)
):
    """
    使用默认配置的数据库连接

    💡 FastAPI 会调用 DatabaseConnection()
    使用所有默认参数
    """
    return {
        "message": "使用默认配置",
        "connection": db.connect(),
        "connected_at": db.connected_at.isoformat()
    }


# 方式 2: 使用工厂函数（自定义参数）
def get_custom_db() -> DatabaseConnection:
    """
    工厂函数：创建自定义配置的数据库连接

    💡 使用场景：
    - 需要自定义配置
    - 从环境变量读取配置
    - 创建单例连接
    """
    return DatabaseConnection(
        host="custom-host",
        port=3306,
        database="customdb"
    )


@app.get("/db/custom")
async def use_custom_db(
    db: DatabaseConnection = Depends(get_custom_db)
):
    """
    使用自定义配置的数据库连接

    💡 使用工厂函数的好处：
    - 可以读取配置文件
    - 可以进行初始化逻辑
    - 可以创建单例
    """
    return {
        "message": "使用自定义配置",
        "connection": db.connect(),
        "connected_at": db.connected_at.isoformat()
    }


# ==================== 场景 4: 可调用对象（__call__）====================

class RequestCounter:
    """
    场景 4: 可调用对象作为依赖

    💡 Python 的 __call__ 魔法方法：
    - 让对象可以像函数一样调用
    - FastAPI 支持这种依赖

    🎯 使用场景：
    - 需要对象的状态（计数器、缓存等）
    - 又希望像函数一样简单调用
    """

    def __init__(self):
        """初始化计数器"""
        self.count = 0

    def __call__(self) -> int:
        """
        让对象可调用

        💡 FastAPI 会调用这个方法
        """
        self.count += 1
        return self.count


@app.get("/counter/func")
async def use_counter_func(
    count: int = Depends(RequestCounter())
):
    """
    使用可调用对象

    🔍 工作原理：
    1. RequestCounter() 创建实例
    2. FastAPI 调用实例的 __call__() 方法
    3. 返回值注入到 endpoint

    ⚠️  注意：
    每次请求都会创建新实例
    """
    return {
        "message": "使用可调用对象",
        "count": count,
        "type": "callable_object"
    }


# ==================== 场景 5: 类依赖 vs 函数依赖对比 ====================

# ══════════════════════════════════════════════════════════════
# 对比示例：相同功能的不同实现
# ══════════════════════════════════════════════════════════════

# ---- 函数依赖版本 ----

def func_format_date(
    date_format: str = "%Y-%m-%d"
) -> str:
    """
    函数依赖：格式化日期
    """
    return datetime.now().strftime(date_format)


@app.get("/format/func")
async def format_with_func(
    formatted: str = Depends(func_format_date)
):
    """使用函数依赖"""
    return {"date": formatted, "type": "function"}


# ---- 类依赖版本 ----

class DateFormatter:
    """
    类依赖：格式化日期
    可以支持更多功能
    """

    def __init__(
        self,
        date_format: str = "%Y-%m-%d",
        timezone: str = "UTC"
    ):
        self.date_format = date_format
        self.timezone = timezone
        self.call_count = 0

    def format(self) -> str:
        """格式化日期"""
        self.call_count += 1
        return datetime.now().strftime(self.date_format)

    def get_call_count(self) -> int:
        """获取调用次数"""
        return self.call_count


@app.get("/format/class")
async def format_with_class(
    formatter: DateFormatter = Depends(DateFormatter)
):
    """使用类依赖"""
    return {
        "date": formatter.format(),
        "timezone": formatter.timezone,
        "call_count": formatter.get_call_count(),
        "type": "class"
    }


# ==================== 场景 6: 何时使用类依赖 ====================

class UserService:
    """
    场景 6: 复杂业务逻辑使用类依赖

    💡 类依赖的优势在这里体现：

    1. **状态管理**
       - 可以持有配置
       - 可以缓存数据
       - 可以管理连接

    2. **多方法**
       - 一个类提供多个相关方法
       - 避免创建多个函数依赖

    3. **可测试性**
       - 可以注入 Mock
       - 可以替换实现

    4. **面向对象**
       - 封装相关逻辑
       - 继承和多态
    """

    def __init__(
        self,
        cache_enabled: bool = True,
        max_cache_size: int = 100
    ):
        """
        初始化服务

        💡 这些不是从请求中获取的
        而是服务配置
        """
        self.cache_enabled = cache_enabled
        self.max_cache_size = max_cache_size
        self._cache = {}

    def get_user(self, user_id: int) -> dict:
        """获取用户（带缓存）"""
        if self.cache_enabled and user_id in self._cache:
            return {
                "data": self._cache[user_id],
                "cached": True
            }

        # 模拟数据库查询
        user = {
            "id": user_id,
            "name": f"User{user_id}",
            "email": f"user{user_id}@example.com"
        }

        if self.cache_enabled:
            self._cache[user_id] = user

        return {"data": user, "cached": False}

    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()

    def get_cache_info(self) -> dict:
        """获取缓存信息"""
        return {
            "enabled": self.cache_enabled,
            "size": len(self._cache),
            "max_size": self.max_cache_size
        }


def get_user_service() -> UserService:
    """
    创建用户服务

    💡 可以在这里读取配置
    """
    return UserService(
        cache_enabled=True,
        max_cache_size=1000
    )


@app.get("/service/users/{user_id}")
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service)
):
    """
    使用类依赖实现复杂逻辑

    ✅ 类依赖的优势：
    - 可以管理状态（缓存）
    - 可以提供多个方法
    - 代码组织更清晰
    """
    result = service.get_user(user_id)

    return {
        "user": result["data"],
        "cached": result["cached"],
        "cache_info": service.get_cache_info()
    }


@app.get("/service/cache/clear")
async def clear_cache(
    service: UserService = Depends(get_user_service)
):
    """清空缓存"""
    service.clear_cache()
    return {
        "message": "缓存已清空",
        "cache_info": service.get_cache_info()
    }


# ==================== 场景 7: 综合对比总结 ====================

@app.get("/compare/summary")
async def compare_summary():
    """
    函数依赖 vs 类依赖 - 总结对比

    ══════════════════════════════════════════════════════════════
    函数依赖
    ══════════════════════════════════════════════════════════════

    def get_data(x: int, y: int) -> dict:
        return {"x": x, "y": y, "sum": x + y}

    @app.get("/data")
    async def use_data(
        data: dict = Depends(get_data)
    ):
        return data

    ✅ 优势：
    - 简单直观
    - 易于理解
    - 适合简单逻辑
    - 函数式编程风格

    ⚠️  限制：
    - 无法保存状态
    - 每次调用都是新的
    - 不适合复杂逻辑

    💡 使用场景：
    - 参数转换
    - 简单验证
    - 纯计算逻辑
    - 不需要状态的场景

    ══════════════════════════════════════════════════════════════
    类依赖
    ══════════════════════════════════════════════════════════════

    class DataProcessor:
        def __init__(self, x: int, y: int):
            self.x = x
            self.y = y
            self.call_count = 0

        def process(self) -> dict:
            self.call_count += 1
            return {
                "x": self.x,
                "y": self.y,
                "sum": self.x + self.y,
                "calls": self.call_count
            }

    @app.get("/process")
    async def use_processor(
        processor: DataProcessor = Depends(DataProcessor)
    ):
        return processor.process()

    ✅ 优势：
    - 可以保存状态
    - 可以提供多个方法
    - 更符合 OOP
    - 适合复杂逻辑
    - 易于扩展

    ⚠️  限制：
    - 相对复杂
    - 需要理解类和对象

    💡 使用场景：
    - 需要状态管理（缓存、计数器）
    - 复杂业务逻辑
    - 需要多个相关方法
    - 面向对象设计

    ══════════════════════════════════════════════════════════════
    选择建议
    ══════════════════════════════════════════════════════════════

    使用函数依赖，当：
    ✅ 逻辑简单（< 10 行）
    ✅ 不需要状态
    ✅ 纯计算或转换
    ✅ 参数验证

    使用类依赖，当：
    ✅ 需要状态（缓存、连接）
    ✅ 逻辑复杂（> 10 行）
    ✅ 需要多个方法
    ✅ 面向对象设计
    ✅ 需要继承或扩展

    ══════════════════════════════════════════════════════════════
    """
    return {
        "function_dependency": {
            "description": "函数依赖",
            "pros": [
                "简单直观",
                "易于理解",
                "适合简单逻辑",
                "函数式编程风格"
            ],
            "cons": [
                "无法保存状态",
                "每次都是新的",
                "不适合复杂逻辑"
            ],
            "use_cases": [
                "参数转换",
                "简单验证",
                "纯计算",
                "不需要状态"
            ],
            "example": "/format/func"
        },
        "class_dependency": {
            "description": "类依赖",
            "pros": [
                "可以保存状态",
                "可以提供多个方法",
                "更符合 OOP",
                "适合复杂逻辑",
                "易于扩展"
            ],
            "cons": [
                "相对复杂",
                "需要理解类和对象"
            ],
            "use_cases": [
                "需要状态管理",
                "复杂业务逻辑",
                "需要多个方法",
                "面向对象设计"
            ],
            "example": "/format/class"
        },
        "recommendation": {
            "simple": "简单场景 → 函数依赖",
            "complex": "复杂场景 → 类依赖",
            "principle": "KISS 原则：保持简单"
        }
    }


# ==================== 根路径 ====================

@app.get("/")
async def root():
    return {
        "name": "类依赖 vs 函数依赖示例",
        "version": "2.0.0",
        "endpoints": {
            "function_dep": "/func/agent",
            "class_dep": "/class/items",
            "db_default": "/db/default",
            "db_custom": "/db/custom",
            "counter": "/counter/func",
            "format_func": "/format/func",
            "format_class": "/format/class",
            "service": "/service/users/1",
            "summary": "/compare/summary"
        },
        "docs": "/docs"
    }


# ==================== 运行说明 ====================
"""
═══════════════════════════════════════════════════════════════
核心对比
═══════════════════════════════════════════════════════════════

函数依赖：
    def get_data(x: int, y: int):
        return {"sum": x + y}

    ✅ 简单
    ❌ 无状态

类依赖：
    class DataProcessor:
        def __init__(self, x: int, y: int):
            self.call_count = 0

        def process(self):
            self.call_count += 1
            return {"count": self.call_count}

    ✅ 有状态
    ✅ 多方法
    ⚠️  相对复杂

═══════════════════════════════════════════════════════════════
选择原则
═══════════════════════════════════════════════════════════════

简单场景 → 函数依赖
    - 参数转换
    - 简单验证
    - 纯计算

复杂场景 → 类依赖
    - 需要状态
    - 多个方法
    - 业务逻辑

═══════════════════════════════════════════════════════════════
"""
