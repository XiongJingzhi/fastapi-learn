"""
阶段 2.3: 依赖的生命周期

学习目标:
1. 理解 Request-scoped vs Application-scoped
2. 掌握使用 yield 管理资源
3. 理解依赖缓存机制
4. 学习如何控制依赖的创建和销毁
5. 了解不同生命周期的影响

运行方式:
    uvicorn study.level2.examples.03_dependency_lifecycle:app --reload
"""

from typing import Dict
from datetime import datetime
from fastapi import FastAPI, Depends
from pydantic import BaseModel

app = FastAPI(
    title="依赖的生命周期",
    description="演示依赖的不同生命周期和资源管理",
    version="2.0.0"
)


# ==================== 场景 1: Request-scoped（默认）====================

# ══════════════════════════════════════════════════════════════
# Request-scoped: 每个请求创建新实例
# ══════════════════════════════════════════════════════════════

class RequestCounter:
    """
    场景 1: Request-scoped 计数器

    💡 FastAPI 的默认行为：
    - 每个请求创建新的依赖实例
    - 请求结束后实例被销毁
    - 不同请求之间不共享状态

    🎯 适用场景：
    - 请求特定的数据
    - 需要隔离状态的场景
    - 大多数业务逻辑
    """

    def __init__(self):
        self.created_at = datetime.now()
        self.request_id = id(self)
        self.call_count = 0

    def increment(self):
        self.call_count += 1
        return self.call_count


def get_request_counter() -> RequestCounter:
    """
    获取 Request-scoped 计数器

    💡 每次调用都返回新实例
    """
    return RequestCounter()


@app.get("/request/count")
async def request_count(
    counter: RequestCounter = Depends(get_request_counter)
):
    """
    Request-scoped 示例

    🔍 行为：
    - 每次请求都创建新的 RequestCounter
    - counter.call_count 总是从 0 开始
    - 不同请求的 counter 是不同的对象
    """
    counter.increment()
    counter.increment()

    return {
        "type": "Request-scoped",
        "request_id": counter.request_id,
        "created_at": counter.created_at.isoformat(),
        "call_count": counter.call_count,
        "note": "每次请求都创建新实例"
    }


# ==================== 场景 2: Application-scoped（全局单例）====================

# ══════════════════════════════════════════════════════════════
# Application-scoped: 全应用共享一个实例
# ══════════════════════════════════════════════════════════════

class AppState:
    """
    场景 2: Application-scoped 状态

    💡 使用模块级变量实现单例：
    - 应用启动时创建
    - 所有请求共享同一个实例
    - 状态在请求间持久化

    ⚠️  注意：
    - 不是线程安全的！
    - 需要考虑并发访问
    - 适合只读数据或使用锁

    🎯 适用场景：
    - 配置信息
    - 全局缓存（需加锁）
    - 连接池管理
    - 统计信息
    """

    def __init__(self):
        self.created_at = datetime.now()
        self.request_count = 0
        self.last_request_time = None


# 模块级变量（应用启动时创建）
app_state = AppState()


def get_app_state() -> AppState:
    """
    获取 Application-scoped 状态

    💡 每次都返回同一个实例
    """
    global app_state
    app_state.request_count += 1
    app_state.last_request_time = datetime.now()
    return app_state


@app.get("/app/stats")
async def app_stats(
    state: AppState = Depends(get_app_state)
):
    """
    Application-scoped 示例

    🔍 行为：
    - 所有请求共享同一个 AppState
    - state.request_count 会累加
    - state.last_request_time 会更新

    ✅ 可以用来做：
    - 请求计数
    - 全局统计
    - 配置管理
    """
    return {
        "type": "Application-scoped",
        "created_at": state.created_at.isoformat(),
        "request_count": state.request_count,
        "last_request": state.last_request_time.isoformat(),
        "note": "所有请求共享同一个实例"
    }


# ==================== 场景 3: 使用 yield 管理资源 ====================

# ══════════════════════════════════════════════════════════════
# yield: 自动管理资源的创建和销毁
# ══════════════════════════════════════════════════════════════

class DatabaseConnection:
    """模拟数据库连接"""

    def __init__(self, db_name: str):
        self.db_name = db_name
        self.connected_at = datetime.now()
        print(f"[DB] 连接到数据库: {db_name}")

    def query(self, sql: str) -> str:
        """执行查询"""
        return f"查询结果: {sql}"

    def close(self):
        """关闭连接"""
        print(f"[DB] 关闭数据库连接: {self.db_name}")
        self.closed_at = datetime.now()


def get_db_connection(db_name: str = "test_db"):
    """
    场景 3: 使用 yield 管理资源

    💡 yield 的魔法：
    yield 之前的代码：在 endpoint 之前执行（创建资源）
    yield 返回的值：注入到 endpoint
    yield 之后的代码：在 endpoint 之后执行（清理资源）

    🔍 工作流程：
    1. FastAPI 调用 get_db_connection()
    2. 执行 yield 之前的代码（创建连接）
    3. 将连接对象注入到 endpoint
    4. endpoint 执行业务逻辑
    5. endpoint 返回响应后
    6. 执行 yield 之后的代码（关闭连接）

    ✅ 优势：
    - 自动资源管理
    - 确保资源被正确释放
    - 即使发生异常也会执行清理代码
    """
    # yield 之前：创建资源
    db = DatabaseConnection(db_name)

    try:
        # 将资源交给 FastAPI
        yield db
    finally:
        # yield 之后：清理资源
        # 即使 endpoint 抛出异常，这里也会执行
        db.close()


@app.get("/db/query")
async def query_database(
    db: DatabaseConnection = Depends(get_db_connection)
):
    """
    使用 yield 管理的数据库连接

    🔍 执行流程：
    1. get_db_connection() 被调用
    2. 创建 DatabaseConnection（打印"连接"）
    3. db 对象注入到这里
    4. 执行查询逻辑
    5. 返回响应
    6. 执行 db.close()（打印"关闭"）

    ✅ 无论是否出错，连接都会被正确关闭！
    """
    result = db.query("SELECT * FROM users")

    return {
        "db_name": db.db_name,
        "connected_at": db.connected_at.isoformat(),
        "result": result,
        "note": "响应后连接会自动关闭"
    }


# ==================== 场景 4: yield 的异常处理 ====================

class TransactionManager:
    """事务管理器"""

    def __init__(self):
        self.started_at = datetime.now()
        print("[TX] 事务开始")

    def commit(self):
        """提交事务"""
        print("[TX] 事务提交")
        self.committed_at = datetime.now()

    def rollback(self):
        """回滚事务"""
        print("[TX] 事务回滚")
        self.rolled_back_at = datetime.now()


def get_transaction():
    """
    场景 4: yield 的异常处理

    💡 使用 try-finally 确保清理：

    即使 endpoint 抛出异常：
    1. finally 块仍然会执行
    2. 可以在这里回滚事务
    3. 确保数据一致性
    """
    transaction = TransactionManager()

    try:
        yield transaction
        # 如果正常到达这里，提交事务
        transaction.commit()
    except Exception as e:
        # 如果发生异常，回滚事务
        print(f"[TX] 检测到异常: {e}")
        transaction.rollback()
        raise


@app.get("/tx/success")
async def successful_transaction(
    tx: TransactionManager = Depends(get_transaction)
):
    """
    成功的事务

    🔍 执行流程：
    1. 创建事务（打印"事务开始"）
    2. 执行业务逻辑
    3. 返回响应
    4. 执行 tx.commit()（打印"事务提交"）
    """
    return {
        "status": "success",
        "started_at": tx.started_at.isoformat(),
        "committed": hasattr(tx, 'committed_at')
    }


@app.get("/tx/fail")
async def failed_transaction(
    tx: TransactionManager = Depends(get_transaction)
):
    """
    失败的事务

    🔍 执行流程：
    1. 创建事务（打印"事务开始"）
    2. 抛出异常
    3. 执行 tx.rollback()（打印"事务回滚"）
    4. 异常继续传播
    """
    raise ValueError("模拟业务错误")


# ==================== 场景 5: 依赖缓存机制演示 ====================

# ══════════════════════════════════════════════════════════════
# 依赖缓存：同一个请求中，相同的依赖只创建一次
# ══════════════════════════════════════════════════════════════

def get_expensive_resource():
    """
    场景 5: 昂贵的资源

    💡 模拟一个创建成本很高的对象
    - 需要初始化
    - 需要连接远程服务
    - 需要加载大量数据

    ✅ FastAPI 的缓存机制：
    - 同一个请求中
    - 即使多次使用 Depends(get_expensive_resource)
    - 也只会创建一次
    """
    print("[Resource] 创建昂贵资源（这行应该只打印一次）")
    return {
        "created_at": datetime.now(),
        "data": "大量数据...",
        "instance_id": id(get_expensive_resource)
    }


@app.get("/cache/demo")
async def demo_cache(
    resource1: dict = Depends(get_expensive_resource),
    resource2: dict = Depends(get_expensive_resource),
    resource3: dict = Depends(get_expensive_resource)
):
    """
    依赖缓存演示

    🔍 观察：
    - 查看控制台输出
    - "创建昂贵资源" 只打印一次
    - resource1, resource2, resource3 是同一个对象

    ✅ 性能优化：
    - 避免重复创建
    - 节省资源
    - 提高性能
    """
    is_same = (
        resource1 is resource2 and
        resource2 is resource3
    )

    return {
        "cached": is_same,
        "resource1_id": id(resource1),
        "resource2_id": id(resource2),
        "resource3_id": id(resource3),
        "note": "控制台应该只看到一次'创建昂贵资源'"
    }


# ==================== 场景 6: 禁用缓存（使用 use_cache）====================

def get_non_cached_resource():
    """
    场景 6: 禁用缓存的资源

    💡 默认情况下，依赖会被缓存
    使用 use_cache=False 可以禁用
    """
    return {
        "created_at": datetime.now(),
        "instance_id": id(get_non_cached_resource)
    }


from fastapi import Depends as _Depends


def CustomDepends(dependency, *, use_cache=True):
    """自定义 Depends 支持 use_cache 参数"""
    return _Depends(dependency, use_cache=use_cache)


@app.get("/cache/disabled")
async def demo_no_cache(
    resource1: dict = CustomDepends(get_non_cached_resource, use_cache=False),
    resource2: dict = CustomDepends(get_non_cached_resource, use_cache=False),
):
    """
    禁用缓存演示

    🔍 行为：
    - 每次使用都创建新实例
    - resource1 和 resource2 是不同的对象

    💡 使用场景：
    - 需要每次都获取新数据
    - 不希望缓存
    - 特殊需求
    """
    return {
        "cached": resource1 is resource2,
        "resource1_id": id(resource1),
        "resource2_id": id(resource2),
        "note": "两个对象应该不同"
    }


# ==================== 场景 7: 生命周期对比总结 ====================

@app.get("/lifecycle/compare")
async def compare_lifecycles():
    """
    生命周期对比总结

    ══════════════════════════════════════════════════════════════
    Request-scoped（默认）
    ══════════════════════════════════════════════════════════════

    def get_data() -> Data:
        return Data()  # 每次创建新实例

    @app.get("/data")
    async def use_data(
        data: Data = Depends(get_data)
    ):
        return data

    特点：
    - 每个请求创建新实例
    - 请求结束销毁实例
    - 不同请求不共享状态
    - FastAPI 默认行为

    适用场景：
    ✅ 大多数业务逻辑
    ✅ 请求特定数据
    ✅ 需要状态隔离

    ══════════════════════════════════════════════════════════════
    Application-scoped（全局单例）
    ══════════════════════════════════════════════════════════════

    app_state = AppState()  # 模块级变量

    def get_state() -> AppState:
        return app_state  # 始终返回同一个实例

    @app.get("/state")
    async def use_state(
        state: AppState = Depends(get_state)
    ):
        return state

    特点：
    - 应用启动时创建
    - 所有请求共享实例
    - 状态持久化
    - 需要考虑并发安全

    适用场景：
    ✅ 配置信息（只读）
    ✅ 全局统计（需加锁）
    ✅ 连接池
    ✅ 缓存（需加锁）

    ══════════════════════════════════════════════════════════════
    使用 yield 管理资源
    ══════════════════════════════════════════════════════════════

    def get_db():
        db = Database()
        try:
            yield db  # 注入到 endpoint
        finally:
            db.close()  # 清理资源

    @app.get("/query")
    async def query(
        db: Database = Depends(get_db)
    ):
        return db.query("...")

    特点：
    - 自动管理资源
    - 确保清理代码执行
    - 即使异常也会清理
    - 类似 Python 的 with 语句

    适用场景：
    ✅ 数据库连接
    ✅ 文件句柄
    ✅ 网络连接
    ✅ 任何需要清理的资源

    ══════════════════════════════════════════════════════════════
    """
    return {
        "request_scoped": {
            "description": "每个请求创建新实例",
            "lifecycle": "请求创建 → 请求销毁",
            "state_sharing": "不共享",
            "use_cases": [
                "大多数业务逻辑",
                "请求特定数据",
                "需要状态隔离"
            ],
            "example": "/request/count"
        },
        "application_scoped": {
            "description": "全局共享单例",
            "lifecycle": "应用启动 → 应用关闭",
            "state_sharing": "全局共享",
            "use_cases": [
                "配置信息",
                "全局统计",
                "连接池",
                "缓存（需加锁）"
            ],
            "example": "/app/stats",
            "warning": "注意并发安全"
        },
        "yield_resource": {
            "description": "使用 yield 管理资源",
            "lifecycle": "创建 → 使用 → 自动清理",
            "state_sharing": "Request-scoped",
            "use_cases": [
                "数据库连接",
                "文件句柄",
                "网络连接",
                "事务管理"
            ],
            "example": "/db/query",
            "benefit": "自动清理，异常安全"
        }
    }


# ==================== 根路径 ====================

@app.get("/")
async def root():
    return {
        "name": "依赖的生命周期示例",
        "version": "2.0.0",
        "endpoints": {
            "request_scoped": "/request/count",
            "app_scoped": "/app/stats",
            "yield_resource": "/db/query",
            "tx_success": "/tx/success",
            "tx_fail": "/tx/fail",
            "cache_demo": "/cache/demo",
            "comparison": "/lifecycle/compare"
        },
        "docs": "/docs"
    }


# ==================== 运行说明 ====================
"""
═══════════════════════════════════════════════════════════════
生命周期总结
═══════════════════════════════════════════════════════════════

Request-scoped（默认）:
    - 每个请求创建新实例
    - 请求结束销毁
    - 不共享状态

Application-scoped:
    - 全局单例
    - 应用启动创建
    - 所有请求共享
    - 注意并发安全

yield 资源管理:
    - 自动创建和清理
    - yield 前创建
    - yield 后清理
    - 异常安全

═══════════════════════════════════════════════════════════════
测试命令
═══════════════════════════════════════════════════════════════

# Request-scoped：每次都创建新实例
curl http://localhost:8000/request/count
curl http://localhost:8000/request/count

# Application-scoped：共享同一个实例
curl http://localhost:8000/app/stats
curl http://localhost:8000/app/stats

# yield 资源管理（查看控制台）
curl http://localhost:8000/db/query

# 事务管理
curl http://localhost:8000/tx/success
curl http://localhost:8000/tx/fail

# 依赖缓存（查看控制台）
curl http://localhost:8000/cache/demo

═══════════════════════════════════════════════════════════════
"""
