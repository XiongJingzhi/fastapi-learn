# Level 3 进阶练习 - Intermediate Exercises

## 📋 练习概述

这些练习帮助你掌握 Level 3 的进阶概念：
- Repository 模式实现
- 复杂查询和关系映射
- 事务管理和并发控制

## 🎯 练习目标

完成这些练习后，你将能够：
- ✅ 设计和实现 Repository 模式
- ✅ 处理一对一、一对多、多对多关系
- ✅ 管理复杂事务
- ✅ 理解并发控制

---

## 练习 1: 实现 Repository 模式

### 需求描述

将 TODO 应用重构为使用 Repository 模式。

#### 1.1 定义 Repository 接口

在领域层定义接口：

```python
# domain/repositories.py
from abc import ABC, abstractmethod
from typing import List, Optional

class ITodoRepository(ABC):
    """TODO 仓储接口"""

    @abstractmethod
    async def save(self, todo: Todo) -> Todo:
        pass

    @abstractmethod
    async def find_by_id(self, todo_id: int) -> Optional[Todo]:
        pass

    @abstractmethod
    async def find_all(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[Todo]:
        pass

    # TODO: 定义其他方法
```

#### 1.2 实现 SQL Repository

```python
# infrastructure/sql_todo_repository.py
class SQLTodoRepository(ITodoRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, todo: Todo) -> Todo:
        # TODO: 实现保存
        pass

    # TODO: 实现其他方法
```

#### 1.3 实现 Mock Repository（用于测试）

```python
# infrastructure/mock_todo_repository.py
class InMemoryTodoRepository(ITodoRepository):
    def __init__(self):
        self._todos: dict[int, Todo] = {}
        self._next_id = 1

    # TODO: 实现所有接口方法
```

#### 1.4 通过依赖注入集成

```python
# dependencies.py
def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session

def get_todo_repo(
    db: AsyncSession = Depends(get_db)
) -> ITodoRepository:
    return SQLTodoRepository(db)

# 测试时可以使用 Mock
# def get_todo_repo() -> ITodoRepository:
#     return InMemoryTodoRepository()
```

### 验收标准

- [ ] Repository 接口定义完整
- [ ] SQL Repository 实现正确
- [ ] Mock Repository 可互换使用
- [ ] 依赖注入配置正确
- [ ] Service 层只依赖接口

### 架构检查

回答以下问题：
1. **为什么需要 Repository 接口？**
   - 提示：依赖倒置、可测试性

2. **Repository 和 Service 的职责边界？**
   - 提示：Repository 只做数据访问

3. **如何测试 Service 层？**
   - 提示：注入 Mock Repository

---

## 练习 2: 实现一对多关系

### 需求描述

扩展 TODO 应用，添加**分类（Category）**功能。

#### 2.1 定义模型

创建 `Category` 模型：

```python
class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    description: Mapped[Optional[str]] = mapped_column(Text)
```

扩展 `Todo` 模型，添加外键：

```python
class Todo(Base):
    # ... 现有字段

    category_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("categories.id")
    )

    # 关系定义
    category: Mapped[Optional["Category"]] = relationship(
        "Category",
        back_populates="todos"
    )
```

#### 2.2 定义反向关系

```python
class Category(Base):
    # ... 字段定义

    # 一个分类有多个 TODO
    todos: Mapped[List["Todo"]] = relationship(
        "Todo",
        back_populates="category"
    )
```

#### 2.3 创建 Category Repository

实现 `ICategoryRepository` 和 `SQLCategoryRepository`。

方法：
- `create_category()` - 创建分类
- `list_categories()` - 列出所有分类
- `get_category_with_todos()` - 获取分类及其 TODO（预加载）

#### 2.4 创建 API Endpoints

- `POST /categories` - 创建分类
- `GET /categories` - 列出分类
- `GET /categories/{id}` - 获取分类（带 TODO）
- `PUT /todos/{id}/category` - 为 TODO 设置分类

### 验收标准

- [ ] 一对多关系定义正确
- [ ] 外键约束生效
- [ ] 可以查询分类及其 TODO
- [ ] 使用 Eager Loading 避免查询

### 挑战

1. **删除分类时怎么办？**
   - 选项 1: 级联删除（删除分类也删除其 TODO）
   - 选项 2: 设置 NULL（TODO 的 category_id 设为 NULL）
   - 选项 3: 禁止删除（如果有关联的 TODO）

   实现哪种策略？为什么？

2. **如何查询未分类的 TODO？**
   ```python
   async def find_uncategorized() -> List[Todo]:
       # TODO: 实现
       pass
   ```

---

## 练习 3: 实现多对多关系

### 需求描述

为 TODO 添加**标签（Tag）**功能（多对多关系）。

#### 3.1 定义关联表

```python
class TodoTag(Base):
    """TODO-标签 关联表"""
    __tablename__ = "todo_tags"

    todo_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("todos.id"),
        primary_key=True
    )
    tag_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tags.id"),
        primary_key=True
    )

    # 关系
    todo: Mapped["Todo"] = relationship("Todo", back_populates="tags")
    tag: Mapped["Tag"] = relationship("Tag", back_populates="todos")
```

#### 3.2 定义 Tag 模型

```python
class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30), unique=True)
    color: Mapped[Optional[str]] = mapped_column(String(7))  # 十六进制颜色

    # 多对多关系
    todos: Mapped[List["Todo"]] = relationship(
        "TodoTag",
        back_populates="tag"
    )
```

#### 3.3 扩展 Todo 模型

```python
class Todo(Base):
    # ... 现有字段

    # 多对多关系
    tags: Mapped[List["Tag"]] = relationship(
        "TodoTag",
        back_populates="todo"
    )
```

#### 3.4 实现功能

- `add_tag_to_todo()` - 为 TODO 添加标签
- `remove_tag_from_todo()` - 移除标签
- `list_todos_by_tag()` - 根据标签查询 TODO
- `get_popular_tags()` - 获取热门标签（使用最多的）

#### 3.5 API Endpoints

- `POST /tags` - 创建标签
- `POST /todos/{id}/tags` - 为 TODO 添加标签
- `DELETE /todos/{id}/tags/{tag_id}` - 移除标签
- `GET /tags` - 列出所有标签
- `GET /tags/{id}/todos` - 获取标签下的所有 TODO

### 验收标准

- [ ] 多对多关系定义正确
- [ ] 关联表正确配置
- [ ] 可以添加/移除标签
- [ ] 可以根据标签查询
- [ ] 热门标签统计正确

---

## 练习 4: 事务管理

### 需求描述

实现一个需要多步骤操作的功能，演示事务管理。

#### 4.1 场景：批量更新 TODO 状态

创建功能：批量标记多个 TODO 为完成。

**要求**：
- 所有更新在一个事务中
- 如果任何一个失败，全部回滚
- 返回成功和失败的数量

```python
async def batch_mark_completed(
    todo_ids: List[int]
) -> dict:
    """
    批量标记完成

    Returns:
        {
            "success": 5,  # 成功数量
            "failed": 2,   # 失败数量
            "errors": [...]  # 错误信息
        }
    """
    async with session.begin():
        # TODO: 实现
        pass
```

#### 4.2 场景：创建模板 TODO

创建功能：从模板创建 TODO。

**流程**：
1. 查询模板 TODO
2. 创建新的 TODO（标题加 "[副本]"）
3. 复制所有标签
4. 复制分类

**要求**：所有操作在一个事务中。

```python
async def create_todo_from_template(
    template_id: int,
    new_title: str
) -> Todo:
    async with session.begin():
        # TODO: 实现多步骤操作
        pass
```

### 验收标准

- [ ] 批量操作使用事务
- [ ] 失败时正确回滚
- [ ] 返回详细的操作结果
- [ ] 多步骤操作原子性保证

### 挑战

**并发问题**：
- 两个用户同时批量更新同一批 TODO
- 会发生什么？
- 如何避免？

**提示**：使用锁或乐观锁。

---

## 练习 5: 复杂查询

### 需求描述

实现几个复杂查询场景。

#### 5.1 统计查询

创建统计 API：

```python
@app.get("/statistics")
async def get_statistics():
    return {
        "total_todos": 0,
        "completed_todos": 0,
        "pending_todos": 0,
        "todos_per_category": {},
        "todos_per_tag": {},
        "average_completion_time": 0.0
    }
```

**提示**：使用 `func.count()`, `func.avg()` 等聚合函数。

#### 5.2 时间范围查询

查询指定时间范围内创建的 TODO：

```python
async def find_todos_by_date_range(
    start_date: datetime,
    end_date: datetime
) -> List[Todo]:
    """
    查询时间范围内的 TODO

    提示: 使用 Todo.created_at >= start_date
    """
    pass
```

#### 5.3 全文搜索

实现更强大的搜索：

- 搜索标题、描述
- 支持多个关键词（AND/OR）
- 高亮匹配结果

```python
async def advanced_search(
    keywords: List[str],
    match_all: bool = True  # True=AND, False=OR
) -> List[Todo]:
    """
    高级搜索

    示例:
    keywords=["work", "urgent"], match_all=True
    → 查询同时包含 "work" 和 "urgent" 的 TODO

    keywords=["work", "urgent"], match_all=False
    → 查询包含 "work" 或 "urgent" 的 TODO
    """
    pass
```

### 验收标准

- [ ] 统计查询正确
- [ ] 时间范围查询正确
- [ ] 高级搜索功能正常
- [ ] 查询性能可接受（添加索引）

---

## 🎯 综合项目：完整的 TODO 管理 API

### 需求描述

将前面所有练习整合，创建一个完整的 TODO 管理 API。

#### 功能要求

1. **基础 CRUD**
   - 创建、查询、更新、删除 TODO

2. **分类管理**
   - 创建分类
   - 为 TODO 设置分类
   - 按分类查询

3. **标签管理**
   - 创建标签
   - 为 TODO 添加标签
   - 按标签查询

4. **高级功能**
   - 分页查询
   - 搜索
   - 统计
   - 批量操作

5. **事务管理**
   - 批量更新
   - 模板创建

6. **数据验证**
   - Pydantic 模型验证
   - 业务规则验证

#### 架构要求

```
┌─────────────────────────────────────────────────────────────┐
│                FastAPI Endpoints                       │
│  @app.post("/todos")                                  │
│  @app.get("/todos/search")                             │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ 依赖注入
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              TodoService (Service Layer)                 │
│  - 业务规则验证                                         │
│  - 编排操作                                             │
│  - 事务控制                                             │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ 依赖接口
                          ▼
┌─────────────────────────────────────────────────────────────┐
│         ITodoRepository (Repository Interface)            │
└─────────────────────────────────────────────────────────────┘
                          ▲
                          │ 实现
                          │
          ┌───────────────┴───────────────┐
          │                               │
┌──────────────────────┐     ┌──────────────────────┐
│ SQLTodoRepository     │     │ MockTodoRepository   │
│  (生产环境)           │     │  (测试环境)           │
└──────────────────────┘     └──────────────────────┘
```

### 验收标准

#### 功能完整
- [ ] 所有 CRUD 功能正常
- [ ] 分类和标签功能正常
- [ ] 搜索和分页正常
- [ ] 批量操作正常
- [ ] 统计功能正常

#### 架构清晰
- [ ] 使用 Repository 模式
- [ ] Service 层业务逻辑清晰
- [ ] 依赖注入配置正确
- [ ] 事务边界正确

#### 代码质量
- [ ] 类型提示完整
- [ ] 文档字符串完整
- [ ] 错误处理完善
- [ ] 代码结构清晰

#### 测试覆盖
- [ ] 单元测试（Repository）
- [ ] 集成测试（Service）
- [ ] API 测试（Endpoints）

---

## 📚 参考资源

- Repository 模式: `../examples/03_repository_pattern.py`
- 事务管理: `../examples/04_transactions.py`
- SQLAlchemy 查询: `../examples/02_sqlalchemy_basics.py`
- 架构笔记: `../notes/00_architecture_db.md`

---

## 🚀 下一步

完成进阶练习后，继续：
1. **综合项目** → `03_challenge_projects.md`
2. **生产就绪** → Level 4

**恭喜完成进阶练习！** 🎯
