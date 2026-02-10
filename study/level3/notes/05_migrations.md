# 05. 数据库迁移 - Database Migrations

## 📍 在架构中的位置

**管理数据库结构变化的版本控制**

```
┌─────────────────────────────────────────────────────────────┐
│          没有 Migration 的问题                                │
└─────────────────────────────────────────────────────────────┘

开发流程：

开发人员 A：
    - 添加了 'phone' 字段到 users 表
    - 手动执行 SQL: ALTER TABLE users ADD COLUMN phone VARCHAR(20);

开发人员 B：
    - 不知道 A 的改动
    - 删除了本地数据库，重新创建
    - 表结构丢失了 'phone' 字段！❌

生产环境：
    - 需要部署新版本
    - 不知道数据库需要哪些改动
    - 手动执行 SQL（容易出错）❌

═══════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────┐
│          使用 Alembic Migration                              │
└─────────────────────────────────────────────────────────────┘

开发流程：

1. 修改 SQLAlchemy 模型
2. 生成迁移脚本: alembic revision --autogenerate -m "add phone field"
3. 查看迁移脚本
4. 应用迁移: alembic upgrade head
5. 所有环境的数据库结构一致！

好处：
- 版本控制（知道每个版本做了什么改动）
- 自动化（不需要手动写 SQL）
- 可回滚（出错了可以恢复）
- 团队协作（所有开发者同步）
```

**🎯 你的学习目标**：掌握 Alembic 的基本使用，安全地管理数据库结构变化。

---

## 🎯 什么是数据库迁移？

### 生活类比：建筑图纸的版本控制

**想象建造一个房子**：

```
版本 1（初始图纸）：
    - 客厅
    - 卧室
    - 厨房

版本 2（添加车库）：
    - 保留原有的房间
    - 新增：车库

版本 3（扩建客厅）：
    - 保留其他房间
    - 扩大客厅

每个版本都记录了：
- 做了什么改动
- 改动前后的对比
- 如何回滚到上一个版本
```

**数据库迁移也是同样的道理**：

```
版本 1（初始表）：
    CREATE TABLE users (
        id INTEGER PRIMARY KEY,
        username VARCHAR(50)
    );

版本 2（添加 email 字段）：
    ALTER TABLE users ADD COLUMN email VARCHAR(100);

版本 3（添加索引）：
    CREATE INDEX idx_users_username ON users(username);
```

---

## 🔧 Alembic 基础

### 安装 Alembic

```bash
# 安装 Alembic
pip install alembic

# 初始化 Alembic
alembic init alembic

# 生成配置文件
# alembic/
# ├── env.py           # 环境配置
# ├── script.py.mako   # 迁移脚本模板
# └── versions/        # 迁移脚本目录
```

---

### 配置 Alembic

**修改 `alembic/env.py`**：

```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# ═══════════════════════════════════════════════════════════
# 关键配置：添加模型的 MetaData
# ═══════════════════════════════════════════════════════════
from myapp.models import Base  # ← 导入你的 Base
target_metadata = Base.metadata  # ← 设置 target_metadata

# ═══════════════════════════════════════════════════════════
# 配置数据库连接
# ═══════════════════════════════════════════════════════════

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

# 创建异步引擎（如果是异步模式）
# 同步模式：
# sqlalchemy.engine.url = driver://user:pass@localhost/dbname

# 异步模式（自定义 run_migrations_online）
import asyncio
from myapp.database import get_database_url

def run_migrations_online():
    """运行迁移（在线模式）"""
    connectable = create_async_engine(get_database_url())

    def do_run_migrations(connection):
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()

    asyncio.run(connectable.connect(do_run_migrations))


# ... 其他配置保持不变
```

---

## 📝 生成迁移脚本

### 基本工作流

**步骤 1：修改 SQLAlchemy 模型**

```python
from sqlalchemy import String, Boolean, Column
from sqlalchemy.orm import Mapped, mapped_column

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(100))

    # 新增字段
    phone: Mapped[str | None] = mapped_column(String(20))  # ← 新增
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)  # ← 新增
    created_at: Mapped[datetime] = mapped_column(DateTime)  # ← 新增
```

---

**步骤 2：生成迁移脚本**

```bash
# 自动生成迁移脚本
alembic revision --autogenerate -m "add phone and is_active fields"

# 输出：
# INFO  [alembic.autogenerate] Generating /path/to/migrations/001_add_phone_and_is_active_fields.py
# ...done
```

**生成的迁移脚本**（`alembic/versions/001_add_phone_and_is_active_fields.py`）：

```python
"""add phone and is_active fields

Revision ID: 001_add_phone_and_is_active_fields
Revises:
Create Date: 2024-01-15 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_add_phone_and_is_active_fields'
down_revision = None  # ← 这是第一个迁移（没有父级）
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级操作（应用变更）"""
    # 添加新列
    op.add_column('users', sa.Column('phone', sa.String(length=20), nullable=True))
    op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=True))
    op.add_column('users', sa.Column('created_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """降级操作（撤销变更）"""
    # 删除列
    op.drop_column('users', 'created_at')
    op.drop_column('users', 'is_active')
    op.drop_column('users', 'phone')
```

---

**步骤 3：查看迁移脚本**

```bash
# 查看迁移历史
alembic history

# 输出：
# Rev: 001_add_phone_and_is_active_fields (head)
#
# 查看迁移详情
alembic show 001_add_phone_and_is_active_fields
```

---

**步骤 4：应用迁移**

```bash
# 升级到最新版本
alembic upgrade head

# 输出：
# INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
# INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
# INFO  [sqlalchemy.engine.base.Engine] ...
# INFO  [alembic.runtime.migration] Running upgrade 001_add_phone_and_is_active_fields ->
# INFO  [alembic.runtime.migration] ... done
```

---

**步骤 5：验证结果**

```bash
# 连接数据库查看表结构
\d users

# 输出：
# Column    | Type                | Collation | Nullable | Default
# ----------+---------------------+-----------+----------+---------
# id        | integer             |           | not null |
# username  | character varying(50)|           | not null |
# email     | character varying(100)|           | not null |
# phone     | character varying(20)|           | yes      |
# is_active | boolean             |           | yes      | true
# created_at| timestamp without time zone |       | yes      |
```

---

## 🔄 迁移操作

### 常见的迁移类型

#### 1. 添加字段

```python
def upgrade() -> None:
    op.add_column(
        'users',
        'phone',
        sa.String(length=20),
        nullable=True  # 允许为 NULL（重要：避免破坏现有数据）
    )

def downgrade() -> None:
    op.drop_column('users', 'phone')
```

---

#### 2. 修改字段

```python
def upgrade() -> None:
    # 修改字段长度
    op.alter_column(
        'users',
        'username',
        existing_type=String(50),
        type_=String(100)  # 从 50 改为 100
    )

def downgrade() -> None:
    op.alter_column(
        'users',
        'username',
        existing_type=String(100),
        type_=String(50)
    )
```

---

#### 3. 创建表

```python
def upgrade() -> None:
    op.create_table(
        'posts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ),
        sa.Column('created_at', sa.DateTime(), nullable=False)
    )

def downgrade() -> None:
    op.drop_table('posts')
```

---

#### 4. 添加索引

```python
def upgrade() -> None:
    op.create_index(
        'idx_users_email',
        'users',
        ['email']
    )

def downgrade() -> None:
    op.drop_index('idx_users_email')
```

---

#### 5. 添加外键

```python
def upgrade() -> None:
    op.create_foreign_key(
        'fk_posts_author_id_users',
        'posts',
        'author_id',
        'users',
        'id'
    )

def downgrade() -> None:
    op.drop_constraint('fk_posts_author_id_users', 'posts', 'author_id')
```

---

## 🎨 实际场景：博客系统迁移

### 场景 1：初始迁移

```python
# 001_initial_tables.py

def upgrade() -> None:
    """创建初始表"""
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('username', sa.String(50), nullable=False),
        sa.Column('email', sa.String(100), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    )

    op.create_table(
        'posts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], name='fk_posts_author')
    )

    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_posts_author', 'posts', ['author_id'])

def downgrade() -> None:
    op.drop_table('posts')
    op.drop_table('users')
```

---

### 场景 2：添加标签功能

```python
# 002_add_tags.py

def upgrade() -> None:
    # 1. 创建 tags 表
    op.create_table(
        'tags',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(50), nullable=False, unique=True)
    )

    # 2. 创建中间表（多对多）
    op.create_table(
        'post_tags',
        sa.Column('post_id', sa.Integer(), primary_key=True),
        sa.Column('tag_id', sa.Integer(), primary_key=True),
        sa.ForeignKeyConstraint(['post_id'], ['posts.id'], name='fk_post_tags_post'),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], name='fk_post_tags_tag')
    )

def downgrade() -> None:
    op.drop_table('post_tags')
    op.drop_table('tags')
```

---

### 场景 3：添加软删除

```python
# 003_add_soft_delete.py

def upgrade() -> None:
    # 添加 deleted_at 列
    op.add_column('posts', sa.Column('deleted_at', sa.DateTime(), nullable=True))

    # 创建索引（加速查询未删除的文章）
    op.create_index('idx_posts_deleted_at', 'posts', ['deleted_at'])

def downgrade() -> None:
    op.drop_index('idx_posts_deleted_at')
    op.drop_column('posts', 'deleted_at')
```

---

## 🛡️ 安全迁移策略

### 数据迁移

**场景**：迁移已有数据

```python
# 004_migrate_user_data.py

from alembic import op
import sqlalchemy as sa
from datetime import datetime

def upgrade() -> None:
    # 1. 添加新列
    op.add_column('users', 'full_name', sa.String(100), nullable=True)

    # 2. 迁移数据（从 username 填充 full_name）
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "UPDATE users SET full_name = username WHERE full_name IS NULL"
        )
    )

    # 3. 现在设置为 NOT NULL
    op.alter_column('users', 'full_name', nullable=False)

def downgrade() -> None:
    op.drop_column('users', 'full_name')
```

---

### 分步迁移（安全）

**场景**：重大结构变更

```python
# 策略：分多个迁移完成

# 004_split_username_step1_add_full_name.py
def upgrade():
    # 步骤 1：添加新列（允许 NULL）
    op.add_column('users', 'full_name', sa.String(100), nullable=True)

def downgrade():
    op.drop_column('users', 'full_name')


# 005_split_username_step2_migrate_data.py
def upgrade():
    # 步骤 2：迁移数据
    conn = op.get_bind()
    conn.execute(
        sa.text("UPDATE users SET full_name = username WHERE full_name IS NULL")
    )

def downgrade():
    # 无法简单回滚（保留数据即可）
    pass


# 006_split_username_step3_make_required.py
def upgrade():
    # 步骤 3：填充 NULL 值
    conn = op.get_bind()
    conn.execute(
        sa.text("UPDATE users SET full_name = 'Unknown' WHERE full_name IS NULL")
    )

    # 步骤 4：设置为 NOT NULL
    op.alter_column('users', 'full_name', nullable=False)

def downgrade():
    op.alter_column('users', 'full_name', nullable=True)


# 007_split_username_step4_remove_username.py
def upgrade():
    # 步骤 5：删除旧列
    op.drop_column('users', 'username')

def downgrade():
    # 回滚：恢复旧列
    op.add_column('users', 'username', sa.String(50), nullable=False)
    conn = op.get_bind()
    conn.execute(
        sa.text("UPDATE users SET username = full_name")
    )
```

---

## 🎯 小实验：自己动手

### 实验 1：创建初始迁移

```bash
# 1. 初始化 Alembic
alembic init alembic

# 2. 配置 alembic/env.py（添加 Base.metadata）

# 3. 生成迁移
alembic revision --autogenerate -m "initial tables"

# 4. 应用迁移
alembic upgrade head
```

---

### 实验 2：添加新字段

```python
# 1. 修改模型
class User(Base):
    # ... 现有字段
    phone: Mapped[str | None] = mapped_column(String(20))

# 2. 生成迁移
alembic revision --autogenerate -m "add phone field"

# 3. 应用迁移
alembic upgrade head
```

---

### 实验 3：回滚迁移

```bash
# 查看当前版本
alembic current

# 回滚一个版本
alembic downgrade -1

# 回滚到指定版本
alembic downgrade 001_add_phone_and_is_active_fields

# 回滚到初始状态
alembic downgrade base
```

---

## 📚 检查理解

回答这些问题来测试你的理解：

1. **什么是数据库迁移？**
   - 提示：管理数据库结构变化的版本控制

2. **Alembic 的作用是什么？**
   - 提示：自动生成和应用 SQL 变更

3. `--autogenerate` 的作用？
   - 提示：根据模型变化自动生成迁移脚本

4. `upgrade` 和 `downgrade` 的区别？
   - 提示：upgrade 应用变更，downgrade 撤销变更

5. **为什么需要分步迁移？**
   - 提示：安全性，避免数据丢失

---

## 🚀 下一步

现在你已经掌握了数据库迁移，Level 3 完成！

**Level 3 总结**：
- ✅ 数据库基础（表、主键、外键）
- ✅ SQLAlchemy ORM（模型定义、CRUD）
- ✅ Repository 模式（接口 + 实现）
- ✅ 事务管理（ACID、并发控制）
- ✅ 数据库迁移（Alembic）

**接下来**：
- 📖 学习 **Level 4**：生产就绪
- 📖 学习 **缓存集成**（Redis）
- 📖 学习 **消息队列**（Kafka）

记住：**Alembic 让数据库迁移变得安全、简单、可版本控制！**

---

**费曼技巧总结**：
- ✅ 建筑图纸版本控制类比
- ✅ 完整的工作流程
- ✅ 常见的迁移类型
- ✅ 实际场景（博客系统）
- ✅ 安全迁移策略
- ✅ 小实验
