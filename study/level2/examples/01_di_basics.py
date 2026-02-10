"""
阶段 2.1: FastAPI 依赖注入基础

学习目标:
1. 理解什么是依赖注入（DI）
2. 掌握 FastAPI 的 Depends() 基本用法
3. 学会定义函数依赖
4. 理解依赖链的自动解析
5. 对比"没有 DI"和"有 DI"的代码差异

架构演进:
    Level 1 (无 DI) → Level 2 (有 DI)
    传输层混逻辑 → 分层架构

运行方式:
    uvicorn study.level2.examples.01_di_basics:app --reload
    访问: http://localhost:8000/docs
"""

from typing import Optional
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, Field

app = FastAPI(
    title="FastAPI 依赖注入基础",
    description="演示依赖注入的基本概念和用法",
    version="2.0.0"
)


# ==================== 场景 0: 问题演示 - 没有 DI 的代码 ====================

# ══════════════════════════════════════════════════════════════
# ❌ Level 1 的问题：没有依赖注入
# ══════════════════════════════════════════════════════════════

# 模拟的"数据库"
fake_db_level1 = {
    1: {"id": 1, "name": "Alice", "email": "alice@example.com"},
    2: {"id": 2, "name": "Bob", "email": "bob@example.com"},
}


@app.get("/level1/users/{user_id}")
async def get_user_level1(user_id: int):
    """
    ❌ Level 1 的典型问题：没有依赖注入

    问题分析：
    1. Endpoint 直接操作"数据库"（fake_db_level1）
    2. 无法在 CLI 工具中复用这个逻辑
    3. 难以测试（必须启动 HTTP 服务器）
    4. 业务逻辑混在传输层

    实际项目中的问题：
    - 如果换数据库，需要修改所有 endpoint
    - 无法写单元测试（被 HTTP 绑定）
    - 代码重复（多个 endpoint 都要写类似的 DB 操作）
    """
    # ❌ 直接依赖 fake_db（硬编码）
    if user_id not in fake_db_level1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # ❌ 业务逻辑在 endpoint 中
    user = fake_db_level1[user_id]

    # ❌ 数据处理逻辑也在 endpoint 中
    user["last_accessed"] = datetime.now().isoformat()

    return user


# ══════════════════════════════════════════════════════════════
# ✅ Level 2 的改进：使用依赖注入
# ══════════════════════════════════════════════════════════════

# ==================== 场景 1: 最简单的依赖注入 ====================

def common_parameters(
    skip: int = 0,
    limit: int = 100,
    debug: bool = False
):
    """
    场景 1: 最简单的依赖 - 公共参数

    💡 使用场景：
    - 多个 endpoint 需要相同的查询参数
    - 避免在每个 endpoint 中重复定义
    - 统一参数验证逻辑

    🎯 优势：
    - 代码复用
    - 统一管理
    - 易于维护
    """
    return {"skip": skip, "limit": limit, "debug": debug}


@app.get("/items/")
async def read_items(
    commons: dict = Depends(common_parameters)
):
    """
    使用依赖注入获取公共参数

    ✅ 改进：
    - 不需要重复定义 skip/limit/debug
    - FastAPI 自动调用 common_parameters
    - 参数验证逻辑统一管理
    """
    return {
        "message": "获取商品列表",
        "params": commons,
        "items": [
            {"id": 1, "name": "商品A"},
            {"id": 2, "name": "商品B"},
        ][commons["skip"]:commons["skip"] + commons["limit"]]
    }


@app.get("/users/")
async def read_users(
    commons: dict = Depends(common_parameters)
):
    """
    复用相同的依赖

    ✅ 复用性：
    - common_parameters 在多个 endpoint 间共享
    - 修改一次，所有 endpoint 都生效
    """
    return {
        "message": "获取用户列表",
        "params": commons,
        "users": [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ][commons["skip"]:commons["skip"] + commons["limit"]]
    }


# ==================== 场景 2: 带类型提示的依赖 ====================

class CommonParams(BaseModel):
    """公共参数模型（使用 Pydantic 验证）"""

    skip: int = Field(0, ge=0, description="跳过的记录数")
    limit: int = Field(100, ge=1, le=100, description="返回的记录数")
    debug: bool = Field(False, description="调试模式")


def get_common_params(
    skip: int = 0,
    limit: int = 100,
    debug: bool = False
) -> CommonParams:
    """
    场景 2: 带类型提示的依赖

    💡 返回类型提示的好处：
    - IDE 自动补全
    - 类型检查
    - 文档自动生成
    """
    return CommonParams(skip=skip, limit=limit, debug=debug)


@app.get("/products/")
async def read_products(
    commons: CommonParams = Depends(get_common_params)
):
    """
    使用带类型的依赖

    ✅ IDE 支持：
    - commons.skip 会自动补全
    - commons.limit 有类型提示
    - 文档中会显示参数说明
    """
    return {
        "message": "获取产品列表",
        "skip": commons.skip,
        "limit": commons.limit,
        "debug": commons.debug,
        "products": [
            {"id": i, "name": f"产品{i}"}
            for i in range(commons.skip, commons.skip + commons.limit)
        ]
    }


# ==================== 场景 3: 依赖链（嵌套依赖）====================

# ══════════════════════════════════════════════════════════════
# 依赖链示意图
# ══════════════════════════════════════════════════════════════
#
# query_params
#   ↓
#   ↓ 依赖
#   ↓
# db_connection
#   ↓
#   ↓ 依赖
#   ↓
# repository
#   ↓
#   ↓ 依赖
#   ↓
# service
# ══════════════════════════════════════════════════════════════


def get_query_params(
    debug: bool = False,
    verbose: bool = False
) -> dict:
    """第 1 层：查询参数"""
    return {"debug": debug, "verbose": verbose}


def get_db_connection(
    params: dict = Depends(get_query_params)
) -> dict:
    """
    第 2 层：数据库连接（依赖查询参数）

    💡 依赖链：
    get_db_connection 依赖 get_query_params
    FastAPI 会先调用 get_query_params，再调用 get_db_connection
    """
    # 模拟数据库连接
    return {
        "connection": "fake_db_connection",
        "params": params,
        "connected_at": datetime.now().isoformat()
    }


def get_repository(
    db: dict = Depends(get_db_connection)
) -> dict:
    """
    第 3 层：仓储（依赖数据库连接）

    💡 依赖链继续延伸：
    endpoint → get_repository → get_db_connection → get_query_params
    """
    # 模拟仓储
    return {
        "repository": "fake_repository",
        "db": db,
        "data": [
            {"id": 1, "name": "数据1"},
            {"id": 2, "name": "数据2"},
        ]
    }


@app.get("/chain/items/")
async def read_items_with_chain(
    repo: dict = Depends(get_repository)
):
    """
    使用依赖链

    🔍 FastAPI 自动解析整个依赖链：
    1. 调用 get_query_params()
    2. 将结果传给 get_db_connection(params)
    3. 将结果传给 get_repository(db)
    4. 将结果传给 endpoint(repo)

    ✅ 好处：
    - 不需要手动管理依赖关系
    - 依赖自动按顺序创建
    - 代码清晰，层次分明
    """
    return {
        "message": "使用依赖链获取数据",
        "repository": repo["repository"],
        "db_connection": repo["db"]["connection"],
        "params": repo["db"]["params"],
        "data": repo["data"]
    }


# ==================== 场景 4: 真实场景 - 用户服务 ====================

# ══════════════════════════════════════════════════════════════
# 架构说明：这是一个简化的分层架构示例
# ══════════════════════════════════════════════════════════════
#
# ┌─────────────────────────────────────────────────┐
# │ 传输层 (Transport Layer)                         │
# │  @app.get("/users/{user_id}")                   │
# │  async def get_user(                            │
# │      service: UserService = Depends(...)       │
# │  ):                                             │
# │      return await service.get_user(user_id)    │
# └─────────────────────────────────────────────────┘
#                      ↓ 依赖注入
# ┌─────────────────────────────────────────────────┐
# │ 服务层 (Service Layer)                           │
# │  class UserService:                             │
# │      def __init__(self, repo: UserRepository)  │
# │      async def get_user(self, user_id)         │
# └─────────────────────────────────────────────────┘
#                      ↓ 依赖注入
# ┌─────────────────────────────────────────────────┐
# │ 基础设施层 (Infrastructure Layer)                │
# │  class UserRepository:                          │
# │      def __init__(self, db: Database)          │
# │      async def find_by_id(self, user_id)       │
# └─────────────────────────────────────────────────┘
# ══════════════════════════════════════════════════════════════

# 模拟数据库
fake_db = {
    1: {"id": 1, "name": "Alice", "email": "alice@example.com"},
    2: {"id": 2, "name": "Bob", "email": "bob@example.com"},
    3: {"id": 3, "name": "Charlie", "email": "charlie@example.com"},
}


# ---- 基础设施层 ----

class Database:
    """模拟数据库连接"""

    def __init__(self):
        self.data = fake_db
        print(f"[DB] 数据库连接已建立")


def get_database() -> Database:
    """
    获取数据库连接（依赖）

    💡 这是依赖注入的起点
    """
    return Database()


class UserRepository:
    """用户仓储 - 数据访问层"""

    def __init__(self, db: Database):
        """
        ✅ 构造函数注入

        💡 关键点：
        - db 不是在内部创建的
        - 而是通过参数传入的
        - 这就是依赖注入！
        """
        self.db = db
        print(f"[Repo] UserRepository 创建完成，依赖: {db}")

    async def find_by_id(self, user_id: int) -> Optional[dict]:
        """根据 ID 查找用户"""
        return self.db.data.get(user_id)

    async def find_all(self) -> list:
        """获取所有用户"""
        return list(self.db.data.values())


def get_user_repository(
    db: Database = Depends(get_database)
) -> UserRepository:
    """
    获取用户仓储（依赖数据库）

    💡 依赖注入的关键函数
    - FastAPI 会自动调用这个函数
    - 自动解析 db 依赖
    - 创建 UserRepository 实例
    """
    return UserRepository(db)


# ---- 服务层 ----

class UserService:
    """用户服务 - 业务逻辑层"""

    def __init__(self, repo: UserRepository):
        """
        ✅ 构造函数注入（第二次）

        💡 依赖链：
        UserService → UserRepository → Database
        """
        self.repo = repo
        print(f"[Service] UserService 创建完成，依赖: {repo}")

    async def get_user(self, user_id: int) -> Optional[dict]:
        """获取用户（包含业务逻辑）"""
        user = await self.repo.find_by_id(user_id)

        if not user:
            return None

        # 业务逻辑：添加访问时间
        user["last_accessed"] = datetime.now().isoformat()

        return user

    async def list_users(self) -> list:
        """列出所有用户"""
        return await self.repo.find_all()


def get_user_service(
    repo: UserRepository = Depends(get_user_repository)
) -> UserService:
    """
    获取用户服务（依赖仓储）

    💡 完整的依赖链：
    get_user_service
      → get_user_repository
        → get_database
    """
    return UserService(repo)


# ---- 传输层 ----

@app.get("/level2/users/{user_id}")
async def get_user_level2(
    user_id: int,
    service: UserService = Depends(get_user_service)
):
    """
    ✅ Level 2 的改进：使用依赖注入

    🔍 依赖注入的威力：

    1. **Endpoint 变薄了**：
       - 不再直接操作数据库
       - 只负责协议适配
       - 业务逻辑在 Service 层

    2. **可测试性**：
       - 可以注入 Mock 的 service
       - 不需要启动 HTTP 服务器
       - 单元测试变得简单

    3. **可复用性**：
       - UserService 可以在 CLI 工具中使用
       - 可以在 gRPC 服务中使用
       - 不被 HTTP 层绑定

    4. **可维护性**：
       - 各层职责清晰
       - 修改数据库实现不影响 Service
       - 修改业务逻辑不影响 Endpoint
    """
    user = await service.get_user(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户 {user_id} 不存在"
        )

    return user


@app.get("/level2/users/")
async def list_users_level2(
    service: UserService = Depends(get_user_service)
):
    """
    获取用户列表

    ✅ 代码复用：
    - 相同的 service 依赖
    - FastAPI 自动缓存
    - 不会重复创建
    """
    users = await service.list_users()
    return {
        "count": len(users),
        "users": users
    }


# ==================== 场景 5: 依赖缓存 ====================

@app.get("/cache/demo/{user_id}")
async def demo_dependency_cache(
    user_id: int,
    service1: UserService = Depends(get_user_service),
    service2: UserService = Depends(get_user_service),
    service3: UserService = Depends(get_user_service)
):
    """
    演示依赖缓存

    💡 FastAPI 的优化：
    - 同一个请求中使用 Depends(get_user_service)
    - 只会创建一次 UserService 实例
    - service1, service2, service3 是同一个对象

    🔍 为什么这很重要？
    - 性能优化（避免重复创建）
    - 状态共享（同一个请求使用同一个连接）
    - 事务管理（确保同一个请求使用同一个数据库会话）
    """
    # 验证：它们是同一个对象
    is_same = (
        service1 is service2 and
        service2 is service3
    )

    return {
        "user_id": user_id,
        "cache_demo": {
            "service1_is_service2": service1 is service2,
            "service2_is_service3": service2 is service3,
            "all_same": is_same,
            "service_id": id(service1)
        },
        "user": await service1.get_user(user_id)
    }


# ==================== 场景 6: 对比总结 ====================

@app.get("/compare/level1-vs-level2")
async def compare_levels():
    """
    Level 1 vs Level 2 对比总结

    ══════════════════════════════════════════════════════════════
    Level 1 (没有依赖注入)
    ══════════════════════════════════════════════════════════════

    @app.get("/users/{user_id}")
    async def get_user(user_id: int):
        if user_id not in fake_db:
            raise HTTPException(404)
        user = fake_db[user_id]
        user["last_accessed"] = datetime.now().isoformat()
        return user

    ❌ 问题：
    1. Endpoint 直接操作数据库
    2. 业务逻辑混在传输层
    3. 无法复用（CLI、gRPC 无法使用）
    4. 难以测试（必须启动 HTTP 服务器）
    5. 代码重复（多个 endpoint 写类似逻辑）

    ══════════════════════════════════════════════════════════════
    Level 2 (使用依赖注入)
    ══════════════════════════════════════════════════════════════

    @app.get("/users/{user_id}")
    async def get_user(
        user_id: int,
        service: UserService = Depends(get_user_service)
    ):
        return await service.get_user(user_id)

    ✅ 优势：
    1. Endpoint 只负责协议适配
    2. 业务逻辑在 Service 层
    3. 可以复用（CLI、gRPC 都能用）
    4. 易于测试（注入 Mock）
    5. 代码清晰，职责分明

    ══════════════════════════════════════════════════════════════
    """
    return {
        "level1_no_di": {
            "description": "没有依赖注入",
            "characteristics": [
                "Endpoint 直接操作数据库",
                "业务逻辑混在传输层",
                "难以测试和复用",
                "代码重复",
                "违反单一职责原则"
            ],
            "example_url": "/level1/users/1"
        },
        "level2_with_di": {
            "description": "使用依赖注入",
            "characteristics": [
                "Endpoint 只做协议适配",
                "业务逻辑在 Service 层",
                "易于测试和复用",
                "代码清晰，职责分明",
                "符合分层架构原则"
            ],
            "example_url": "/level2/users/1",
            "architecture": {
                "transport_layer": "传输层 - 协议适配",
                "service_layer": "服务层 - 业务逻辑",
                "infrastructure_layer": "基础设施层 - 数据访问"
            }
        },
        "key_improvements": [
            "依赖注入让分层架构成为可能",
            "各层可以独立测试和演进",
            "代码变得可复用、可维护",
            "符合 SOLID 原则"
        ]
    }


# ==================== 根路径和健康检查 ====================

@app.get("/")
async def root():
    """根路径 - API 信息"""
    return {
        "name": "FastAPI 依赖注入基础示例",
        "version": "2.0.0",
        "level": "Level 2 - 依赖注入",
        "description": "演示依赖注入的基本概念和用法",
        "endpoints": {
            "level1_example": "/level1/users/1",
            "level2_example": "/level2/users/1",
            "common_params": "/items/",
            "dependency_chain": "/chain/items/",
            "cache_demo": "/cache/demo/1",
            "comparison": "/compare/level1-vs-level2"
        },
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "FastAPI DI Basics Demo",
        "architecture": "Layered Architecture with DI"
    }


# ==================== 运行说明 ====================
"""
═══════════════════════════════════════════════════════════════
启动服务器
═══════════════════════════════════════════════════════════════

uvicorn study.level2.examples.01_di_basics:app --reload

═══════════════════════════════════════════════════════════════
测试示例
═══════════════════════════════════════════════════════════════

1. Level 1 (没有 DI)
curl http://localhost:8000/level1/users/1

2. Level 2 (有 DI)
curl http://localhost:8000/level2/users/1

3. 公共参数（演示代码复用）
curl http://localhost:8000/items/?skip=0&limit=10&debug=true
curl http://localhost:8000/users/?skip=0&limit=5&debug=true

4. 依赖链
curl http://localhost:8000/chain/items/?debug=true&verbose=true

5. 依赖缓存
curl http://localhost:8000/cache/demo/1

6. 对比总结
curl http://localhost:8000/compare/level1-vs-level2

═══════════════════════════════════════════════════════════════
核心概念
═══════════════════════════════════════════════════════════════

1. 依赖注入 (Dependency Injection, DI)
   - 把依赖的创建交给外部
   - 对象只负责使用，不负责创建

2. FastAPI 的 Depends()
   - 自动解析依赖
   - 自动管理依赖的生命周期
   - 支持依赖链

3. 依赖链
   endpoint → service → repo → db
   FastAPI 会自动按顺序创建

4. 依赖缓存
   - 同一个请求中，相同的依赖只创建一次
   - 提高性能，确保状态一致性

═══════════════════════════════════════════════════════════════
Level 1 → Level 2 的关键改进
═══════════════════════════════════════════════════════════════

❌ Level 1: 传输层包含业务逻辑
    → 难以测试
    → 无法复用
    → 违反架构原则

✅ Level 2: 使用依赖注入实现分层
    → 易于测试
    → 可以复用
    → 符合架构原则
    → 各层独立演化

═══════════════════════════════════════════════════════════════
下一步学习
═══════════════════════════════════════════════════════════════

Level 2.2: 类依赖 vs 函数依赖
Level 2.3: 依赖的生命周期
Level 2.4: 实现完整的服务层

"""
