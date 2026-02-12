"""
Level 3 Examples - 数据库与持久化示例代码

本目录包含 Level 3 的所有代码示例，用于演示如何将真实数据库集成到分层架构中。

## 示例列表

1. **01_database_basics.py** - 数据库基础
   - 展示如何连接数据库
   - 基本的 CRUD 操作
   - 使用 Context Manager 管理连接
   - 连接池配置

2. **02_sqlalchemy_basics.py** - SQLAlchemy 核心
   - SQLAlchemy 模型定义
   - Session 管理
   - 基本查询操作
   - 关系映射（一对一、一对多、多对多）
   - Eager Loading（避免 N+1 查询）

3. **03_repository_pattern.py** - Repository 模式
   - 定义 Repository 抽象接口
   - 实现 SQLAlchemyRepository
   - 展示如何通过依赖注入使用 Repository
   - Mock Repository 实现（用于测试）

4. **04_transactions.py** - 事务管理
   - 事务的 begin/commit/rollback
   - 处理事务失败
   - 嵌套事务
   - 并发控制（锁）

5. **05_migrations.py** - Alembic 迁移
   - 展示迁移脚本的编写
   - 升级和降级操作
   - 数据迁移策略

## 运行示例

每个示例都可以独立运行:

```bash
# 启动 PostgreSQL (使用 Docker)
docker run --name fastapi-db -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=fastapi -p 5432:5432 -d postgres:16

# 运行示例
python study/level3/examples/01_database_basics.py
python study/level3/examples/02_sqlalchemy_basics.py
python study/level3/examples/03_repository_pattern.py
python study/level3/examples/04_transactions.py
python study/level3/examples/05_migrations.py
```

## 学习建议

1. **按顺序学习** - 示例之间有递进关系
2. **动手实践** - 运行每个示例并测试 API
3. **阅读代码注释** - 注释中包含大量架构说明
4. **对比学习** - 观察每个示例如何演进

## 端口分配

为了避免端口冲突，每个示例使用不同的端口:

- Example 01: http://localhost:8000
- Example 02: http://localhost:8001
- Example 03: http://localhost:8002
- Example 04: http://localhost:8003
- Example 05: http://localhost:8004

## 相关资源

- 笔记: `../notes/`
- 练习: `../exercises/`
- FastAPI 文档: https://fastapi.tiangolo.com/
- SQLAlchemy 文档: https://docs.sqlalchemy.org/
"""

__version__ = "1.0.0"
