"""
示例 3.5: 数据库迁移 - Alembic Migrations

学习目标:
1. 理解为什么需要数据库迁移
2. 掌握 Alembic 的基本使用
3. 学习如何生成迁移脚本
4. 理解升级和降级操作
5. 学习数据迁移的最佳实践

前置条件:
    # 1. 安装 Alembic
    pip install alembic

    # 2. 启动 PostgreSQL
    docker run --name fastapi-db -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=fastapi -p 5432:5432 -d postgres:16

配置方式:
    # 1. 初始化 Alembic
    alembic init alembic

    # 2. 配置 alembic/env.py (见下方示例)

    # 3. 生成迁移
    alembic revision --autogenerate -m "Initial migration"

    # 4. 应用迁移
    alembic upgrade head

测试方式:
    # 查看迁移历史
    alembic history

    # 回滚迁移
    alembic downgrade -1
"""

# ══════════════════════════════════════════════════════════════════════════
# 为什么需要数据库迁移？
# ══════════════════════════════════════════════════════════════════════════
#
# 问题场景:
# ────────────────────────────────────────────────────────────────────────────────────────
#
# 开发初期:
#   CREATE TABLE users (
#       id INTEGER PRIMARY KEY,
#       username VARCHAR(50)
#   );
#
# 需求变更 (需要添加邮箱字段):
#   # ❌ 直接修改数据库 (不推荐)
#   ALTER TABLE users ADD COLUMN email VARCHAR(100);
#
# 问题:
#   1. 无法回滚
#   2. 无法追踪变更历史
#   3. 团队成员的数据库结构不一致
#   4. 生产环境升级困难
#
# ══════════════════════════════════════════════════════════════════════════
# 解决方案: 使用 Alembic 管理迁移
# ══════════════════════════════════════════════════════════════════════════
#
# Alembic 提供的功能:
#   1. 版本控制: 记录每次数据库变更
#   2. 自动升级: alembic upgrade head
#   3. 安全回滚: alembic downgrade base
#   4. 自动生成: 根据模型变更生成迁移脚本
#
# ══════════════════════════════════════════════════════════════════════════


# ==================== Alembic 配置示例 ====================

# ══════════════════════════════════════════════════════════════════════════
# alembic.ini 配置文件
# ══════════════════════════════════════════════════════════════════════════
"""
# Alembic 配置文件 (alembic.ini)

[alembic]
# 迁移脚本存放路径
script_location = alembic

# 迁移脚本命名格式
# 使用 %%
file_template = %%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d_%%(rev)s_%%(slug)s

# 数据库连接 URL (会被 env.py 中的配置覆盖)
# sqlalchemy.url = postgresql+asyncpg://user:pass@localhost/dbname

# 时区设置
timezone = UTC

# ...
"""

# ══════════════════════════════════════════════════════════════════════════
# alembic/env.py 配置文件
# ══════════════════════════════════════════════════════════════════════════
"""
# Alembic 环境配置 (alembic/env.py)

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import sys
import os

# 导入你的模型
# sys.path.append(os.getcwd())
# from myapp.models import Base  # ← 导入你的 Base
# from myapp.models import User, Product  # ← 导入所有模型

# Alembic Config 对象
config = context.config

# 解释日志配置
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 添加模型的 MetaData
# target_metadata = Base.metadata  # ← SQLAlchemy 模型的 metadata
target_metadata = None


# ══════════════════════════════════════════════════════════════════════════
# 数据库 URL 配置
# ══════════════════════════════════════════════════════════════════════════

def get_database_url():
    """获取数据库 URL"""
    # 从环境变量读取
    # url = os.getenv("DATABASE_URL")

    # 或者硬编码 (开发环境)
    url = "postgresql+asyncpg://postgres:postgres@localhost/fastapi"

    return url


def run_migrations_offline() -> None:
    """
    离线模式运行迁移

    使用场景: 不需要连接数据库，生成 SQL 脚本
    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """执行迁移"""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,  # 比较列类型
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    """
    异步模式运行迁移 (推荐)

    ══════════════════════════════════════════════════════════════════════════
    注意: Alembic 默认是同步的
    使用 AsyncEngine 需要特殊配置
    ══════════════════════════════════════════════════════════════════════════
    """
    from sqlalchemy.ext.asyncio import async_engine_from_config

    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_database_url()

    connectable = await async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """在线模式运行迁移"""
    asyncio.run(run_async_migrations())


# 根据上下文选择运行模式
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
"""


# ══════════════════════════════════════════════════════════════════════════
# 迁移脚本示例
# ══════════════════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════════════════
# 迁移 1: 初始表结构
# ══════════════════════════════════════════════════════════════════════════
"""
# alembic/versions/20240101_0001_initial.py

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = '0001'
down_revision = None  # 第一个迁移
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    升级操作 (应用迁移)

    ══════════════════════════════════════════════════════════════════════════
    这个函数的内容会被应用到数据库
    将数据库从旧版本升级到新版本
    ══════════════════════════════════════════════════════════════════════════
    """
    # 创建用户表
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # 创建索引
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_username', 'users', ['username'])
    op.create_index('ix_users_email', 'users', ['email'], unique=True)


def downgrade() -> None:
    """
    降级操作 (回滚迁移)

    ══════════════════════════════════════════════════════════════════════════
    这个函数的内容用于回滚
    将数据库从新版本恢复到旧版本
    必须是 upgrade() 的逆向操作
    ══════════════════════════════════════════════════════════════════════════
    """
    # 删除索引
    op.drop_index('ix_users_email', table_name='users')
    op.drop_index('ix_users_username', table_name='users')
    op.drop_index('ix_users_id', table_name='users')

    # 删除表
    op.drop_table('users')
"""


# ══════════════════════════════════════════════════════════════════════════
# 迁移 2: 添加用户资料表
# ══════════════════════════════════════════════════════════════════════════
"""
# alembic/versions/20240102_0002_add_user_profile.py

from alembic import op
import sqlalchemy as sa

revision = '0002'
down_revision = '0001'  # 依赖之前的迁移
branch_labels = None
depends_on = None


def upgrade() -> None:
    """添加用户资料表"""

    # 创建用户资料表
    op.create_table(
        'user_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('avatar_url', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['users.id'],
            name='fk_user_profile_user'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')  # 一对一关系
    )


def downgrade() -> None:
    """删除用户资料表"""
    op.drop_table('user_profiles')
"""


# ══════════════════════════════════════════════════════════════════════════
# 迁移 3: 数据迁移 (Data Migration)
# ══════════════════════════════════════════════════════════════════════════
"""
# alembic/versions/20240103_0003_migrate_data.py

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column

# 定义表对象 (用于数据操作)
users_table = table('users',
    column('id', sa.Integer),
    column('username', sa.String),
    column('email', sa.String)
)

revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    数据迁移示例

    场景: 将 full_name 从 users 表移到 user_profiles 表
    """

    # 1. 添加新列
    op.add_column('users', sa.Column('full_name', sa.String(length=100), nullable=True))

    # 2. 迁移数据 (使用批量操作)
    from sqlalchemy.orm import Session
    bind = op.get_bind()
    session = Session(bind=bind)

    try:
        # 分批处理 (避免内存问题)
        batch_size = 1000
        offset = 0

        while True:
            # 查询一批数据
            result = session.execute(
                sa.text("SELECT id, username FROM users LIMIT :limit OFFSET :offset"),
                {"limit": batch_size, "offset": offset}
            )

            rows = result.fetchall()
            if not rows:
                break

            # 更新数据
            for row in rows:
                session.execute(
                    sa.text("UPDATE users SET full_name = :name WHERE id = :id"),
                    {"name": f"Full Name of {row[1]}", "id": row[0]}
                )

            session.commit()
            offset += batch_size

    finally:
        session.close()


def downgrade() -> None:
    """回滚: 删除 full_name 列"""
    op.drop_column('users', 'full_name')
"""


# ══════════════════════════════════════════════════════════════════════════
# 迁移 4: 修改列类型
# ══════════════════════════════════════════════════════════════════════════
"""
# alembic/versions/20240104_0004_alter_column.py

from alembic import op
import sqlalchemy as sa

revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    修改列类型

    ══════════════════════════════════════════════════════════════════════════
    注意: PostgreSQL 支持无数据丢失的类型转换
    但某些操作可能导致数据丢失，需要小心！
    ══════════════════════════════════════════════════════════════════════════
    """

    # 方式 1: 使用 alter_column (简单类型)
    op.alter_column(
        'users',
        'username',
        type_=sa.String(100),  # 从 VARCHAR(50) 改为 VARCHAR(100)
        existing_type=sa.String(50),
        nullable=False
    )

    # 方式 2: 批量修改 (复杂场景)
    # with op.batch_alter_table('users') as batch_op:
    #     batch_op.alter_column('username', type_=sa.String(100))
    #     batch_op.alter_column('email', type_=sa.String(200))


def downgrade() -> None:
    """回滚: 恢复原类型"""
    op.alter_column(
        'users',
        'username',
        type_=sa.String(50),
        existing_type=sa.String(100),
        nullable=False
    )
"""


# ==================== Alembic 命令行工具 ====================

# ══════════════════════════════════════════════════════════════════════════
# 常用命令
# ══════════════════════════════════════════════════════════════════════════

"""
═══════════════════════════════════════════════════════════════════════════
Alembic 常用命令
═══════════════════════════════════════════════════════════════════════════

1. 初始化 Alembic
───────────────────────────────────────────────────────────────────────────────────────
alembic init alembic
创建:
  - alembic/              (迁移脚本目录)
  - alembic.ini           (配置文件)
  - alembic/env.py        (环境配置)

2. 生成迁移脚本
───────────────────────────────────────────────────────────────────────────────────────
# 自动生成 (根据模型变化)
alembic revision --autogenerate -m "Add user profile table"

# 手动创建 (空白模板)
alembic revision -m "Custom migration"

3. 查看迁移状态
───────────────────────────────────────────────────────────────────────────────────────
# 查看当前版本
alembic current

# 查看迁移历史
alembic history

# 查看待执行的迁移
alembic heads

4. 执行迁移
───────────────────────────────────────────────────────────────────────────────────────
# 升级到最新版本
alembic upgrade head

# 升级到指定版本
alembic upgrade 0002

# 升级一步
alembic upgrade +1

5. 回滚迁移
───────────────────────────────────────────────────────────────────────────────────────
# 降级到基础版本 (删除所有表)
alembic downgrade base

# 降级到指定版本
alembic downgrade 0002

# 降级一步
alembic downgrade -1

6. 生成 SQL 脚本 (不执行)
───────────────────────────────────────────────────────────────────────────────────────
# 生成升级 SQL
alembic upgrade head --sql > upgrade.sql

# 生成降级 SQL
alembic downgrade base --sql > downgrade.sql

═══════════════════════════════════════════════════════════════════════════
"""


# ==================== 完整示例代码 ====================

from fastapi import FastAPI
from sqlalchemy import create_engine, Column, Integer, String, Boolean

# 创建测试引擎
engine = create_engine("sqlite:///./test_migrations.db")


# 定义模型 (用于演示)
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False)
    email = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)


# ==================== FastAPI 应用 ====================

app = FastAPI(
    title="数据库迁移示例",
    description="演示如何使用 Alembic 管理数据库迁移",
    version="5.0.0"
)


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "数据库迁移示例",
        "version": "5.0.0",
        "description": "演示 Alembic 的使用和最佳实践",
        "alembic_commands": {
            "init": "alembic init alembic",
            "generate": "alembic revision --autogenerate -m 'message'",
            "upgrade": "alembic upgrade head",
            "downgrade": "alembic downgrade -1",
            "current": "alembic current",
            "history": "alembic history"
        },
        "migration_workflow": [
            "1. 修改 SQLAlchemy 模型",
            "2. 生成迁移: alembic revision --autogenerate -m 'description'",
            "3. 查看迁移脚本",
            "4. 测试迁移: alembic upgrade head",
            "5. 如有问题: alembic downgrade -1",
            "6. 提交迁移脚本到版本控制"
        ],
        "best_practices": [
            "始终检查自动生成的迁移脚本",
            "不要修改已应用的迁移",
            "保持迁移脚本幂等性",
            "数据迁移使用批量操作",
            "生产环境前在测试环境验证",
            "保留所有迁移脚本 (不要删除)"
        ],
        "docs": "https://alembic.sqlalchemy.org/"
    }


# ==================== 运行说明 ====================
"""
═══════════════════════════════════════════════════════════════════════════
数据库迁移总结
═══════════════════════════════════════════════════════════════════════════

1. 为什么需要迁移?
   - 版本控制数据库结构
   - 安全升级和回滚
   - 团队协作
   - 生产环境部署

2. Alembic 工作流程
   修改模型 → 生成迁移 → 检查脚本 → 应用迁移

3. 迁移命令
   - 生成: alembic revision --autogenerate -m 'message'
   - 升级: alembic upgrade head
   - 降级: alembic downgrade -1

4. 最佳实践
   - 始终检查自动生成的脚本
   - 数据迁移使用批量操作
   - 保留所有迁移脚本
   - 生产环境前测试

═══════════════════════════════════════════════════════════════════════════
实际操作步骤
═══════════════════════════════════════════════════════════════════════════

# 1. 初始化 Alembic (首次)
alembic init alembic

# 2. 配置 alembic/env.py
#    - 设置数据库 URL
#    - 导入你的模型 Base

# 3. 生成初始迁移
alembic revision --autogenerate -m "Initial migration"

# 4. 查看生成的脚本
cat alembic/versions/xxxxx_initial_migration.py

# 5. 应用迁移
alembic upgrade head

# 6. 修改模型 (例如添加字段)

# 7. 生成新迁移
alembic revision --autogenerate -m "Add full_name field"

# 8. 检查迁移脚本
cat alembic/versions/yyyyy_add_full_name_field.py

# 9. 应用迁移
alembic upgrade head

# 10. 如有问题，回滚
alembic downgrade -1

═══════════════════════════════════════════════════════════════════════════
团队协作建议
═══════════════════════════════════════════════════════════════════════════

1. 提交迁移脚本
   - 迁移脚本应该纳入版本控制
   - 每个人生成的迁移脚本可能不同

2. 合并冲突处理
   - 如果多人生成迁移，可能产生冲突
   - 解决: 保留第一个迁移，其他人重新生成

3. 数据库状态一致性
   - 每个开发者的数据库应该保持一致
   - 使用 alembic upgrade head 同步

═══════════════════════════════════════════════════════════════════════════
"""
