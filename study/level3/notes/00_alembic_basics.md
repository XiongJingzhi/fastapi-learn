# Alembic 基础 - 数据库迁移的架构设计

## 🎯 什么是 Alembic？

**Alembic 是 SQLAlchemy 作者开发的数据库迁移工具**。

想象你在建造一个房子：

```
没有迁移工具：
    房子建好了 → 想加个房间 → 拆掉重建？ ❌

有迁移工具（Alembic）：
    房子 v1.0 → 设计图纸记录
    加个房间 → 生成变更图纸 v1.1 → 施工 ✅
    不满意？回滚到 v1.0 → 拆除新房间 ✅
    清楚知道每个版本的房子长什么样 ✅
```

**Alembic 的核心价值**：

1. **版本控制**：记录数据库结构的历史
2. **增量变更**：只变更必要的部分
3. **可回滚**：可以撤销变更
4. **团队协作**：所有人同步数据库结构
5. **自动化**：自动生成迁移脚本

---

## 💡 为什么需要数据库迁移？

### 传统方式的问题

```python
# ❌ 传统方式：手动管理数据库
# 开发者 A
CREATE TABLE users (
    id INT PRIMARY KEY,
    name VARCHAR(50)
);

# 开发者 B
# 不知道 A 已经创建了表，又创建了一遍
CREATE TABLE users (
    id INT PRIMARY KEY,
    username VARCHAR(50)  # 字段名还不一致！
);

# 生产环境
# 如何同步？手工执行 SQL？容易出错！
```

### 使用 Alembic 后

```bash
# ✅ 版本化的数据库变更
alembic revision --autogenerate -m "add email column to users"
# 生成迁移脚本：versions/001_add_email.py

# 应用到开发环境
alembic upgrade head

# 应用到生产环境
alembic upgrade head

# 需要回滚？
alembic downgrade -1
```

---

## 🏗️ Alembic 架构

### 核心组件

```
┌─────────────────────────────────────────────────────┐
│                  Alembic Environment                │
│  ┌──────────────────────────────────────────────┐  │
│  │  Migration Scripts (迁移脚本)                │  │
│  │  versions/                                  │  │
│  │  ├── 001_initial_schema.py                  │  │
│  │  ├── 002_add_users_table.py                 │  │
│  │  ├── 003_add_email_column.py                │  │
│  │  └── ...                                    │  │
│  └──────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────┐  │
│  │  alembic.ini (配置文件)                      │  │
│  └──────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────┐  │
│  │  env.py (环境配置)                           │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────┐
│              alembic_version table                  │
│  记录当前数据库的版本（迁移历史）                    │
└─────────────────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────┐
│               你的数据库表                           │
│  users, posts, comments, ...                       │
└─────────────────────────────────────────────────────┘
```

### 迁移脚本结构

```python
"""add email column to users

Revision ID: 003_add_email
Revises: 002_add_users_table
Create Date: 2024-01-15 10:30:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003_add_email'           # 这个迁移的 ID
down_revision = '002_add_users_table' # 基于哪个迁移
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级：应用变更"""
    op.add_column('users', sa.Column('email', sa.String(100), nullable=True))


def downgrade() -> None:
    """降级：撤销变更"""
    op.drop_column('users', 'email')
```

---

## 🔄 迁移工作流程

### 完整流程

```
1. 修改 SQLAlchemy Model
   ↓
2. 生成迁移脚本
   alembic revision --autogenerate -m "描述"
   ↓
3. 检查生成的脚本（重要！）
   cat versions/xxx_migration.py
   ↓
4. 应用到数据库
   alembic upgrade head
   ↓
5. 验证变更
   检查数据库结构是否符合预期
```

### 初始化 Alembic

```bash
# 1. 安装
pip install alembic

# 2. 初始化
alembic init alembic
# 生成目录结构：
# alembic/
#   ├── versions/     # 迁移脚本目录
#   ├── env.py        # 环境配置
#   ├── script.py.mako # 模板
# alembic.ini         # 配置文件

# 3. 配置 alembic.ini
# sqlalchemy.url = driver://user:pass@localhost/dbname

# 4. 配置 env.py（导入你的 Base）
# target_metadata = Base.metadata
```

---

## 🎨 迁移策略对比

### 策略 1：自动生成（autogenerate）

```bash
# 自动检测 Model 变化并生成迁移脚本
alembic revision --autogenerate -m "add email column"
```

**优点**：
- ✅ 快速、方便
- ✅ 适合简单变更

**缺点**：
- ❌ 可能生成不完美的脚本
- ❌ 需要人工检查

**示例**：
```python
# Model 变更
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50))
    email = Column(String(100))  # 新增字段

# 自动生成的迁移
def upgrade() -> None:
    op.add_column('users', sa.Column('email', sa.String(100), nullable=True))
```

### 策略 2：手动编写

```python
# 手动创建迁移脚本
alembic revision -m "custom migration"

# 手动编写 upgrade 和 downgrade
def upgrade() -> None:
    # 自定义逻辑
    op.execute("CREATE INDEX idx_users_email ON users (email)")

    # 数据迁移
    op.execute("""
        UPDATE users
        SET email = username || '@example.com'
        WHERE email IS NULL
    """)

def downgrade() -> None:
    op.execute("DROP INDEX idx_users_email")
```

**优点**：
- ✅ 完全控制
- ✅ 可以做复杂的数据迁移

**缺点**：
- ❌ 需要更多时间
- ❌ 需要更深入的了解

### 策略 3：混合模式（推荐）

```bash
# 1. 自动生成
alembic revision --autogenerate -m "add email"

# 2. 检查并手动调整
vim versions/001_add_email.py

# 3. 如果需要，添加自定义逻辑
def upgrade() -> None:
    # 自动生成的基础变更
    op.add_column('users', sa.Column('email', sa.String(100), nullable=True))

    # 手动添加的额外逻辑
    op.execute("UPDATE users SET email = username || '@temp.com' WHERE email IS NULL")
    op.alter_column('users', 'email', nullable=False)

# 4. 应用
alembic upgrade head
```

---

## 🔐 生产环境最佳实践

### 1. 永远不要在生产环境直接使用 autogenerate

```bash
# ❌ 危险
在生产服务器上：
alembic revision --autogenerate -m "quick fix"
alembic upgrade head

# ✅ 安全
在开发环境：
1. 编写并测试迁移脚本
2. 在测试环境验证
3. 代码审查
4. 在生产环境应用已验证的脚本
```

### 2. 迁移脚本的原子性

```python
# ✅ 好的做法：每个迁移脚本做一件事
def upgrade() -> None:
    op.add_column('users', sa.Column('email', sa.String(100), nullable=True))

# ❌ 不好的做法：一个脚本做太多事
def upgrade() -> None:
    op.add_column('users', sa.Column('email', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('phone', sa.String(20), nullable=True))
    op.add_column('users', sa.Column('address', sa.String(200), nullable=True))
    op.create_table('posts', ...)
    op.create_table('comments', ...)
    # 如果中途失败，难以回滚
```

### 3. 数据迁移与结构迁移分离

```python
# ✅ 分离结构迁移和数据迁移

# 版本 001: 添加新字段（结构迁移）
def upgrade() -> None:
    op.add_column('users', sa.Column('email', sa.String(100), nullable=True))

# 版本 002: 填充数据（数据迁移）
def upgrade() -> None:
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=op.get_bind())
    session = Session()

    # 批量更新（使用分批避免内存问题）
    batch_size = 1000
    offset = 0
    while True:
        users = session.query(User).offset(offset).limit(batch_size).all()
        if not users:
            break
        for user in users:
            user.email = f"{user.username}@example.com"
        session.commit()
        offset += batch_size

    # 然后设置非空
    op.alter_column('users', 'email', nullable=False)
```

### 4. 回滚策略

```python
# ✅ 总是编写 downgrade
def upgrade() -> None:
    # 可逆操作
    op.add_column('users', sa.Column('email', sa.String(100), nullable=True))

def downgrade() -> None:
    # 撤销操作
    op.drop_column('users', 'email')

# ⚠️ 难以回滚的操作（数据丢失）
def upgrade() -> None:
    op.drop_column('users', 'temp_field')

def downgrade() -> None:
    # 数据已经丢失，无法完全恢复
    # 只能重建字段（但数据没了）
    op.add_column('users', sa.Column('temp_field', sa.String(100)))
```

---

## 🚨 常见问题与解决方案

### 问题 1：迁移冲突

```python
# 场景：两个开发者同时创建迁移

# 开发者 A：版本 002_add_posts_table.py
down_revision = '001_initial_schema'

# 开发者 B：版本 002_add_comments_table.py
down_revision = '001_initial_schema'

# ❌ 冲突：两个版本号相同

# ✅ 解决方案：重新编号
# 开发者 B 修改为：
# version = '003_add_comments_table'
# down_revision = '002_add_posts_table'
```

### 问题 2：autogenerate 检测不到变更

```python
# 常见原因：
# 1. Model 没有正确导入到 env.py
# env.py
target_metadata = Base.metadata  # 确保导入所有 Model

# 2. 使用了不支持的功能（如某些数据库特性）
# 需要手动编写迁移
```

### 问题 3：迁移历史丢失

```python
# 场景：删除了 alembic_version 表或 versions 目录

# ✅ 解决方案：重建基线
alembic revision --autogenerate -m "baseline"
# 手动修改，设置为当前数据库状态
# 然后标记为基线版本
alembic stamp head
```

---

## 💡 FastAPI 集成

### 项目结构

```
project/
├── alembic/
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
├── app/
│   ├── models/
│   │   ├── user.py
│   │   └── post.py
│   ├── database.py
│   └── main.py
├── alembic.ini
└── requirements.txt
```

### env.py 配置

```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# 导入你的 Base 和所有 Model
from app.database import Base
from app.models import *  # 导入所有模型

# Alembic Config 对象
config = context.config

# 设置数据库 URL（可以从环境变量读取）
config.set_main_option("sqlalchemy.url", "sqlite+aiosqlite:///./app.db")

# 解释模型的元数据
target_metadata = Base.metadata

# ... 其他配置
```

### 异步支持

```python
# alembic/env.py
from asyncio import run
from sqlalchemy.ext.asyncio import async_engine_from_config

def run_migrations_online() -> None:
    """异步模式下运行迁移"""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async def do_run_migrations():
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations_sync)

    run(do_run_migrations())
```

---

## 📚 迁移命令速查

```bash
# 初始化
alembic init alembic

# 创建迁移
alembic revision -m "description"              # 手动创建
alembic revision --autogenerate -m "description" # 自动生成

# 应用迁移
alembic upgrade head                            # 应用到最新版本
alembic upgrade +1                             # 应用下一个版本
alembic downgrade -1                           # 回退一个版本
alembic downgrade base                          # 回退到初始状态

# 查看状态
alembic current                                # 当前版本
alembic history                                # 迁移历史
alembic heads                                  # 最新版本

# 调试
alembic upgrade head --sql                     # 只生成 SQL，不执行
alembic upgrade head --sql > migration.sql     # 导出 SQL 文件

# 标记版本（不执行迁移）
alembic stamp head                             # 标记为最新版本
alembic stamp 001_initial_schema               # 标记为指定版本
```

---

## 🎯 总结

**Alembic 核心价值**：

1. ✅ **版本控制**：数据库结构的 Git
2. ✅ **团队协作**：所有人同步数据库结构
3. ✅ **可回滚**：出现问题时可以撤销
4. ✅ **自动化**：自动生成迁移脚本
5. ✅ **安全**：在生产环境应用已验证的变更

**最佳实践**：

- 在开发环境测试迁移脚本
- 每个迁移做一件事
- 总是编写 downgrade
- 不要在生产环境使用 autogenerate
- 数据迁移与结构迁移分离

**记住**：
- 迁移脚本代码的一部分，需要版本控制
- 检查自动生成的脚本
- 保留回滚能力
- 在测试环境验证后再应用到生产

**下一步**：学习数据库集成（Level 3）

---

**Alembic 让数据库迁移变得安全而有序！** 🔄
