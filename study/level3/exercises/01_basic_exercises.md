# Level 3 基础练习 - Basic Exercises

## 📋 练习概述

这些练习帮助你巩固 Level 3 的基础概念：
- 数据库连接和 CRUD 操作
- SQLAlchemy 模型定义
- 基本的查询操作

## 🎯 练习目标

完成这些练习后，你将能够：
- ✅ 独立创建数据库连接
- ✅ 定义 SQLAlchemy 模型
- ✅ 实现基本的 CRUD 操作
- ✅ 使用事务管理数据一致性

---

## 练习 1: 创建 TODO 应用数据库

### 需求描述

创建一个 TODO 应用的数据库集成，包含以下功能：

#### 1.1 定义模型

创建 `Todo` 模型，包含字段：
- `id`: 主键
- `title`: 标题（必填，最大 200 字符）
- `description`: 描述（可选）
- `completed`: 是否完成（默认 False）
- `created_at`: 创建时间（自动生成）
- `updated_at`: 更新时间（自动更新）

**提示**：
```python
from sqlalchemy import DateTime, func

# 自动更新时间戳
updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

#### 1.2 实现 CRUD 操作

创建以下函数：
- `create_todo()` - 创建 TODO
- `get_todo_by_id()` - 根据 ID 获取 TODO
- `list_todos()` - 列出所有 TODO
- `update_todo()` - 更新 TODO
- `delete_todo()` - 删除 TODO
- `mark_completed()` - 标记完成

#### 1.3 创建 FastAPI Endpoints

- `POST /todos` - 创建 TODO
- `GET /todos/{id}` - 获取 TODO
- `GET /todos` - 列出 TODO（支持 `?completed=true/false` 过滤）
- `PUT /todos/{id}` - 更新 TODO
- `DELETE /todos/{id}` - 删除 TODO
- `PATCH /todos/{id}/complete` - 标记完成

### 验收标准

- [ ] 模型定义正确，包含所有字段
- [ ] CRUD 操作完整
- [ ] API 端点可访问
- [ ] 支持按完成状态过滤
- [ ] 使用事务管理

### 参考代码结构

```python
# models.py
class Todo(Base):
    __tablename__ = "todos"
    # TODO: 定义字段

# repository.py
class TodoRepository:
    async def create(self, todo: Todo) -> Todo:
        # TODO: 实现创建
        pass

# main.py
@app.post("/todos")
async def create_todo(todo_data: TodoCreate):
    # TODO: 实现 endpoint
    pass
```

---

## 练习 2: 实现分页查询

### 需求描述

为 TODO 列表添加分页功能。

#### 2.1 修改查询函数

修改 `list_todos()` 函数，支持：
- `skip`: 跳过多少条（默认 0）
- `limit`: 返回多少条（默认 20，最大 100）

```python
async def list_todos(
    skip: int = 0,
    limit: int = 20
) -> List[Todo]:
    # TODO: 实现分页查询
    pass
```

#### 2.2 添加总数统计

创建函数 `count_todos()` 返回 TODO 总数。

#### 2.3 返回分页信息

API 响应包含：
- `items`: TODO 列表
- `total`: 总数
- `skip`: 跳过数
- `limit`: 返回数

```python
{
    "items": [...],
    "total": 100,
    "skip": 0,
    "limit": 20
}
```

### 验收标准

- [ ] 分页参数生效
- [ ] limit 最大值限制为 100
- [ ] 返回总数统计
- [ ] 响应格式正确

---

## 练习 3: 添加搜索功能

### 需求描述

为 TODO 添加搜索功能。

#### 3.1 实现关键词搜索

搜索标题和描述中包含关键词的 TODO：

```python
async def search_todos(keyword: str) -> List[Todo]:
    """
    搜索标题或描述包含关键词的 TODO

    提示: 使用 or_() 和 contains()
    """
    pass
```

#### 3.2 添加搜索 Endpoint

```
GET /todos/search?keyword=work
```

#### 3.3 组合过滤

支持同时使用：
- 搜索关键词
- 完成状态过滤
- 分页

```
GET /todos/search?keyword=work&completed=false&skip=0&limit=10
```

### 验收标准

- [ ] 搜索标题和描述
- [ ] 大小写不敏感
- [ ] 可与其他过滤组合
- [ ] 分页在搜索中生效

---

## 练习 4: 数据验证

### 需求描述

在 TODO 创建和更新时添加数据验证。

#### 4.1 Pydantic 模型验证

```python
class TodoCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)

    # TODO: 添加更多验证规则
    pass
```

#### 4.2 业务规则验证

在创建/更新时检查：
- 标题不能为空
- 标题不能全是空格
- 描述最大 1000 字符

**提示**：在 Service 层实现业务规则验证。

### 验收标准

- [ ] Pydantic 验证生效
- [ ] 业务规则验证实现
- [ ] 返回清晰的错误信息
- [ ] 输入被正确清理

---

## 练习 5: 连接池配置

### 需求描述

配置数据库连接池。

#### 5.1 配置连接池参数

```python
engine = create_async_engine(
    DATABASE_URL,
    # TODO: 配置连接池
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True
)
```

#### 5.2 添加连接池监控

创建 endpoint 查看连接池状态：

```python
@app.get("/debug/pool")
async def pool_status():
    # TODO: 返回连接池状态
    pass
```

返回：
```json
{
    "pool_size": 5,
    "checked_out": 2,
    "overflow": 0,
    "invalid": 0
}
```

### 验收标准

- [ ] 连接池参数配置正确
- [ ] 可以查看连接池状态
- [ ] 连接复用生效
- [ ] 长时间连接被正确回收

---

## 🎯 提交检查

完成所有练习后，确保：

### 代码质量
- [ ] 所有函数有类型提示
- [ ] 所有函数有文档字符串
- [ ] 代码遵循 PEP 8
- [ ] 没有硬编码的配置

### 功能完整
- [ ] 所有 CRUD 操作正常
- [ ] 分页功能正常
- [ ] 搜索功能正常
- [ ] 验证规则生效

### 测试覆盖
- [ ] 创建 TODO 测试
- [ ] 更新 TODO 测试
- [ ] 删除 TODO 测试
- [ ] 分页查询测试
- [ ] 搜索功能测试

---

## 📚 参考资源

- SQLAlchemy 文档: https://docs.sqlalchemy.org/
- FastAPI 文档: https://fastapi.tiangolo.com/
- 示例代码: `../examples/01_database_basics.py`
- 笔记: `../notes/01_database_basics.md`

---

## 🚀 下一步

完成基础练习后，继续：
1. **进阶练习** → `02_intermediate_exercises.md`
2. **Repository 模式** → `../examples/03_repository_pattern.py`

**祝你学习愉快！** 🎯
