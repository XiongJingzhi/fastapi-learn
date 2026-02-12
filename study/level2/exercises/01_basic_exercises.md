# Level 2 基础练习题：依赖注入入门

## 🎯 练习目标

通过实际编写代码，掌握 FastAPI 依赖注入的基础用法，理解依赖注入如何让代码更清晰、更易测试。

---

## 练习 1: 创建你的第一个依赖

### 🎯 学习目标
理解依赖注入的基本概念和工作流程

### 💡 费曼类比：餐厅点餐

想象你在餐厅吃饭：

**没有依赖注入（自己做饭）**：
```
你（endpoint）需要：
1. 自己买食材（创建依赖）
2. 自己做饭（处理业务逻辑）
3. 自己洗碗（清理资源）

问题：太累了！每次都要重复这些工作
```

**有依赖注入（点餐）**：
```
你（endpoint）只需要：
1. 看菜单（声明需要什么）
2. 点菜（Depends 告诉 FastAPI）
3. 等菜上桌（使用注入的依赖）

服务员（Depends）会帮你：
- 找厨师（创建依赖）
- 端菜上来（注入到 endpoint）
- 收盘子（清理资源）

好处：你只管吃，不用管怎么做！
```

### 📝 任务

创建一个简单的 FastAPI 应用，使用依赖注入获取当前时间：

```python
from fastapi import FastAPI, Depends
from datetime import datetime
from pydantic import BaseModel

app = FastAPI()

class InfoResponse(BaseModel):
    message: str
    current_time: str
    app_name: str

# TODO 1: 定义一个依赖函数，返回当前时间
# 提示：使用 datetime.now()

def get_current_time() -> str:
    """返回当前时间的字符串"""
    # 你的代码在这里
    pass

# TODO 2: 定义一个依赖函数，返回应用名称
def get_app_name() -> str:
    """返回应用名称"""
    # 返回 "My FastAPI App"
    pass

# TODO 3: 在 endpoint 中使用这两个依赖
@app.get("/info", response_model=InfoResponse)
async def get_info(
    # 在这里使用 Depends 注入上面的两个依赖
):
    return {
        "message": "Welcome to the API!",
        # 使用注入的依赖
    }
```

### ✅ 完成标准

- [ ] 代码可以正常运行（使用 `uvicorn` 启动）
- [ ] 访问 `/info` 返回包含当前时间和应用名称的 JSON
- [ ] 理解依赖函数的执行时机（什么时候被调用）

### 💡 提示

如果遇到困难，思考这些问题：
1. `Depends()` 的参数应该是什么？
2. 依赖函数的返回值如何进入 endpoint 参数？
3. endpoint 的参数名和依赖函数的返回值有什么关系？

### 🧪 验证理解

如果让你给同事讲解"什么是依赖注入"，你会用什么类比？

<details>
<summary>参考答案（先自己思考）</summary>

**我的答案**：就像网购。
- 你（endpoint）在淘宝下单（声明依赖）
- 快递员（Depends）负责把包裹送到你家（注入依赖）
- 你只需要签收使用（在 endpoint 中使用）
- 你不需要知道包裹是怎么运输的（不关心依赖如何创建）

**另一个类比**：就像用手机充电。
- 你（endpoint）需要充电
- 你插上充电器（Depends）
- 电（依赖）自动从充电宝流向你的手机
- 你不需要知道电是怎么产生的（不关心发电厂）
</details>

---

## 练习 2: 依赖链 - 理解嵌套依赖

### 🎯 学习目标
理解依赖可以依赖其他依赖，形成依赖链

### 💡 费曼类比：组装电脑

```
依赖链就像组装电脑的层次关系：

CPU 依赖
    ↓
主板依赖（需要 CPU）
    ↓
完整电脑（需要主板）
    ↓
你使用电脑（endpoint）

每一层只需要关心直接依赖的下一层！
```

### 📝 任务

创建一个依赖链，展示如何嵌套依赖：

```python
from fastapi import FastAPI, Depends
from pydantic import BaseModel

app = FastAPI()

# 数据模型
class DatabaseConfig(BaseModel):
    host: str
    port: int
    database: str

class Database:
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.connected = False

    def connect(self):
        self.connected = True
        return f"Connected to {self.config.host}:{self.config.port}"

class Repository:
    def __init__(self, db: Database):
        self.db = db

    def get_status(self) -> str:
        if self.db.connected:
            return f"Repository ready on {self.db.config.database}"
        return "Repository not connected"

# TODO 1: 定义依赖 1 - 获取数据库配置
def get_db_config() -> DatabaseConfig:
    """返回数据库配置"""
    return DatabaseConfig(
        host="localhost",
        port=5432,
        database="myapp"
    )

# TODO 2: 定义依赖 2 - 依赖配置，创建数据库连接
def get_database(
    # 使用 Depends 注入配置依赖
) -> Database:
    """创建数据库连接"""
    pass

# TODO 3: 定义依赖 3 - 依赖数据库，创建仓储
def get_repository(
    # 使用 Depends 注入数据库依赖
) -> Repository:
    """创建仓储"""
    pass

# TODO 4: 在 endpoint 中使用最终的依赖
@app.get("/status")
async def check_status(
    # 注入最终的依赖
):
    # 返回仓储的状态
    pass
```

### ✅ 完成标准

- [ ] 代码可以正常运行
- [ ] 访问 `/status` 返回类似 `"Repository ready on myapp"` 的消息
- [ ] 理解依赖链的执行顺序（哪个依赖先被调用？）

### 💡 提示

思考依赖的执行顺序：
1. 当你访问 `/status` 时，FastAPI 看到 `Depends(get_repository)`
2. `get_repository` 需要 `db: Database = Depends(get_database)`
3. `get_database` 需要 `config: DatabaseConfig = Depends(get_db_config)`
4. FastAPI 会自动按什么顺序调用这些函数？

### 🧪 验证理解

如果依赖链是 A → B → C（A 依赖 B，B 依赖 C），执行顺序是什么？

<details>
<summary>参考答案</summary>

执行顺序：C → B → A（从最底层的依赖开始）

1. FastAPI 解析 A 依赖 B
2. FastAPI 解析 B 依赖 C
3. FastAPI 先调用 C（最底层）
4. C 的返回值注入到 B
5. B 的返回值注入到 A
6. A 的返回值注入到 endpoint

就像盖房子：
- 先打地基（C）
- 再砌墙（B）
- 最后盖屋顶（A）
</details>

---

## 练习 3: 简单的用户注册服务

### 🎯 学习目标
将业务逻辑从 endpoint 移到 Service 层，使用依赖注入

### 💡 费曼类比：医院看病

```
没有分层（Level 1）：
挂号员（endpoint）既要挂号，又要看病，还要开药
→ 太乱了！

有分层（Level 2）：
挂号员（endpoint）只负责引导
医生（Service）负责看病
药房（Repository）负责发药
→ 职责清晰！
```

### 📝 任务

重构一个用户注册的 endpoint，使用依赖注入：

```python
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Dict

app = FastAPI()

# ═══════════════════════════════════════════════════════════
# 数据模型
# ═══════════════════════════════════════════════════════════

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class User(BaseModel):
    id: int
    username: str
    email: str

# ═══════════════════════════════════════════════════════════
# Repository 层：数据访问（模拟）
# ═══════════════════════════════════════════════════════════

class UserRepository:
    """用户仓储：负责数据操作"""

    def __init__(self):
        # 模拟数据库
        self.users: Dict[int, User] = {}
        self.next_id = 1

    def email_exists(self, email: str) -> bool:
        """检查邮箱是否已存在"""
        return any(u.email == email for u in self.users.values())

    def save(self, user: User) -> User:
        """保存用户"""
        user.id = self.next_id
        self.users[user.id] = user
        self.next_id += 1
        return user

# ═══════════════════════════════════════════════════════════
# Service 层：业务逻辑（需要你完成）
# ═══════════════════════════════════════════════════════════

class UserService:
    """用户服务：负责业务逻辑"""

    def __init__(self, repo: UserRepository):
        # TODO: 保存 repo 到实例变量
        pass

    def create_user(self, user_data: UserCreate) -> User:
        """
        创建用户的业务逻辑

        业务规则：
        1. 检查邮箱是否已存在（使用 repo.email_exists）
        2. 如果存在，抛出 ValueError("Email already registered")
        3. 创建用户对象（使用 User 模型）
        4. 保存用户（使用 repo.save）
        5. 返回保存的用户
        """
        # TODO: 实现业务逻辑
        pass

# ═══════════════════════════════════════════════════════════
# 依赖注入（需要你完成）
# ═══════════════════════════════════════════════════════════

# TODO: 定义 get_user_repo 依赖
def get_user_repo() -> UserRepository:
    """创建并返回 UserRepository 实例"""
    pass

# TODO: 定义 get_user_service 依赖
# 提示：这个函数需要依赖 get_user_repo
def get_user_service(
    # 使用 Depends 注入 repo
) -> UserService:
    """创建并返回 UserService 实例"""
    pass

# ═══════════════════════════════════════════════════════════
# Endpoint：只做协议适配（需要你完成）
# ═══════════════════════════════════════════════════════════

@app.post("/users", status_code=201)
async def create_user(
    user: UserCreate,
    # TODO: 使用 Depends 注入 service
):
    """
    创建用户

    Endpoint 只负责：
    1. 接收请求（FastAPI 自动）
    2. 调用 Service
    3. 返回响应
    4. 处理异常（转换 ValueError 为 HTTPException）
    """
    try:
        # TODO: 调用 service.create_user
        pass
    except ValueError as e:
        # 转换业务异常为 HTTP 异常
        raise HTTPException(status_code=400, detail=str(e))
```

### ✅ 完成标准

- [ ] 代码可以正常运行
- [ ] 成功创建第一个用户（返回 201 状态码）
- [ ] 尝试用相同邮箱创建第二个用户（返回 400 错误）
- [ ] 理解为什么业务逻辑应该在 Service 层，而不是 endpoint

### 💡 提示

1. Service 层的 `__init__` 需要接收 repo 参数
2. `get_user_service` 函数需要声明 `repo: UserRepository = Depends(get_user_repo)`
3. endpoint 需要 `service: UserService = Depends(get_user_service)`

### 🧪 验证理解

为什么要把业务逻辑放在 Service 层，而不是直接写在 endpoint 里？

<details>
<summary>参考答案</summary>

**可复用性**：
```
❌ 业务逻辑在 endpoint：
- HTTP API 可以用
- CLI 工具无法复用（需要重写）
- 定时任务无法复用（需要重写）
- 测试困难（需要启动 HTTP 服务器）

✅ 业务逻辑在 Service：
- HTTP API 调用 Service
- CLI 工具也调用同一个 Service
- 定时任务也调用同一个 Service
- 测试简单（直接测试 Service，不需要 HTTP）
```

**职责分离**：
- Endpoint：负责 HTTP 协议相关的事（接收请求、返回响应）
- Service：负责业务逻辑（验证规则、数据处理）
- Repository：负责数据访问（SQL 查询、缓存操作）

就像餐厅：
- 服务员（endpoint）：只负责点菜、上菜
- 厨师（service）：负责做菜（业务逻辑）
- 采购（repository）：负责买菜（数据访问）
</details>

---

## 练习 4: 验证依赖的缓存机制

### 🎯 学习目标
理解同一个请求内，相同的依赖只会被创建一次

### 💡 费曼类比：共享出租车

```
同一个请求（一次出行）：
- 你（endpoint）需要去两个地方
- 第一个地方：打车（调用依赖）
- 第二个地方：还是同一趟行程（复用依赖）

FastAPI 不会给你叫两辆出租车！
而是让你在同一辆车上完成两件事
```

### 📝 任务

验证依赖的缓存机制：

```python
from fastapi import FastAPI, Depends

app = FastAPI()

# 全局计数器
call_count = 0

def get_dependency():
    """一个简单的依赖"""
    global call_count
    call_count += 1
    print(f"依赖被调用：第 {call_count} 次")
    return {"count": call_count}

@app.get("/test-single")
async def test_single_use(
    dep: dict = Depends(get_dependency)
):
    """
    只使用一次依赖
    预期：依赖被调用 1 次
    """
    return {
        "message": "Single use",
        "dep_count": dep["count"]
    }

# TODO: 创建一个 endpoint，在同一个请求中使用两次相同的依赖
@app.get("/test-double")
async def test_double_use(
    # 在参数列表中使用两次 Depends(get_dependency)
    # 提示：参数名要不同，比如 dep1 和 dep2
):
    """
    使用两次相同的依赖
    预期：依赖只被调用 1 次（因为会被缓存）
    """
    # 检查 dep1 和 dep2 是否是同一个对象
    # 提示：使用 `is` 操作符
    pass
```

### ✅ 完成标准

- [ ] 实现 `test_double_use` endpoint
- [ ] 验证 `dep1 is dep2` 返回 True
- [ ] 理解为什么依赖只被调用一次

### 💡 提示

在同一个请求内：
```python
@app.get("/test")
async def test(
    dep1: Dict = Depends(get_dep),
    dep2: Dict = Depends(get_dep),  # 同一个依赖
):
    # dep1 和 dep2 是同一个对象！
    assert dep1 is dep2  # True
```

### 🧪 验证理解

为什么同一个请求内，相同的依赖会被缓存？

<details>
<summary>参考答案</summary>

**性能考虑**：
- 创建依赖可能很昂贵（数据库连接、网络请求等）
- 同一个请求不需要多次创建

**状态一致性**：
- 如果每次都创建新实例，可能导致状态不一致
- 例如：两次获取数据库连接，应该是同一个事务

**实际例子**：
```python
@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    db1: Database = Depends(get_db),
    db2: Database = Depends(get_db),  # 同一个请求
    service: UserService = Depends(get_service),  # 内部也用 get_db
):
    # db1, db2, service.db 都是同一个 Database 实例
    # 这样可以保证整个请求使用同一个数据库事务
```
</details>

---

## 练习 5: 综合练习 - 完整的博客文章 API

### 🎯 学习目标
将所有知识点整合，实现一个简单的博客文章 API

### 💡 费曼类比：搭建完整的服务流程

```
就像开一家餐馆：
1. 采购（Repository）：管理食材
2. 厨师（Service）：烹饪菜肴
3. 服务员（Endpoint）：接待客人
4. 依赖注入（Depends）：让各部门协作
```

### 📝 任务

实现一个博客文章 API，包含以下功能：
1. 创建文章
2. 获取所有文章
3. 获取单篇文章

```python
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

app = FastAPI()

# ═══════════════════════════════════════════════════════════
# 数据模型
# ═══════════════════════════════════════════════════════════

class PostCreate(BaseModel):
    title: str
    content: str
    author: str

class Post(BaseModel):
    id: int
    title: str
    content: str
    author: str
    created_at: str

# ═══════════════════════════════════════════════════════════
# Repository 层
# ═══════════════════════════════════════════════════════════

class PostRepository:
    """文章仓储"""

    def __init__(self):
        self.posts: Dict[int, Post] = {}
        self.next_id = 1

    def save(self, post: Post) -> Post:
        """保存文章"""
        # TODO: 实现保存逻辑
        pass

    def find_all(self) -> List[Post]:
        """获取所有文章"""
        # TODO: 返回所有文章
        pass

    def find_by_id(self, post_id: int) -> Optional[Post]:
        """根据 ID 获取文章"""
        # TODO: 根据 ID 查找文章，不存在返回 None
        pass

# ═══════════════════════════════════════════════════════════
# Service 层
# ═══════════════════════════════════════════════════════════

class PostService:
    """文章服务"""

    def __init__(self, repo: PostRepository):
        self.repo = repo

    def create_post(self, post_data: PostCreate) -> Post:
        """
        创建文章

        业务规则：
        1. 标题不能为空
        2. 创建时间设为当前时间（ISO 格式）
        3. 调用 repo.save 保存
        """
        # TODO: 实现业务逻辑
        pass

    def list_posts(self) -> List[Post]:
        """列出所有文章"""
        # TODO: 调用 repo
        pass

    def get_post(self, post_id: int) -> Post:
        """
        获取单篇文章

        如果文章不存在，抛出 ValueError("Post not found")
        """
        # TODO: 实现业务逻辑
        pass

# ═══════════════════════════════════════════════════════════
# 依赖注入
# ═══════════════════════════════════════════════════════════

# TODO: 定义 get_post_repo 依赖
def get_post_repo() -> PostRepository:
    pass

# TODO: 定义 get_post_service 依赖
def get_post_service(
    # 依赖 repo
) -> PostService:
    pass

# ═══════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════

# TODO: 实现 POST /posts endpoint
@app.post("/posts", status_code=201)
async def create_post(
    post: PostCreate,
    # 注入 service
):
    pass

# TODO: 实现 GET /posts endpoint
@app.get("/posts")
async def list_posts(
    # 注入 service
):
    pass

# TODO: 实现 GET /posts/{post_id} endpoint
@app.get("/posts/{post_id}")
async def get_post(
    post_id: int,
    # 注入 service
):
    # 捕获 ValueError，转换为 HTTPException(404)
    pass
```

### ✅ 完成标准

- [ ] 可以创建文章（POST /posts）
- [ ] 可以列出所有文章（GET /posts）
- [ ] 可以获取单篇文章（GET /posts/{id}）
- [ ] 获取不存在的文章返回 404
- [ ] 代码结构清晰（Repository → Service → Endpoint）

### 💡 提示

1. 按照分层结构完成代码：
   - 先完成 Repository 层（数据操作）
   - 再完成 Service 层（业务逻辑）
   - 最后完成 Endpoint（HTTP 适配）

2. 依赖注入的顺序：
   - `get_post_service` 依赖 `get_post_repo`
   - endpoint 依赖 `get_post_service`

3. 异常处理：
   - Service 层抛出 `ValueError`
   - Endpoint 捕获并转换为 `HTTPException`

### 🧪 验证理解

为什么需要分 Repository、Service、Endpoint 三层？不能只写一层？

<details>
<summary>参考答案</summary>

**单层的问题**：
```
❌ 只有 Endpoint：
@app.post("/posts")
async def create_post(post: PostCreate):
    # 1. 数据验证
    # 2. 业务逻辑
    # 3. 数据存储
    # 4. HTTP 响应

问题：
- 代码太长，难以维护
- 业务逻辑无法复用（CLI、定时任务无法使用）
- 测试困难（必须启动 HTTP 服务器）
- 职责混乱
```

**三层的好处**：
```
✅ Repository（数据层）：
- 只负责数据操作（CRUD）
- 可以切换数据库（MySQL → PostgreSQL）
- 可以添加缓存（Redis）

✅ Service（业务层）：
- 只负责业务逻辑（验证规则、计算）
- 可以在多处复用（HTTP、CLI、gRPC）
- 易于测试（Mock Repository）

✅ Endpoint（接口层）：
- 只负责 HTTP 协议
- 代码简洁清晰
- 易于替换（HTTP → WebSocket）
```

**类比**：
- Repository = 图书管理员（管理书籍）
- Service = 老师（传授知识）
- Endpoint = 前台接待（接待访客）
</details>

---

## ✅ 总结检查清单

完成所有练习后，检查你是否能够：

- [ ] 解释什么是依赖注入
- [ ] 使用 `Depends()` 创建简单的依赖
- [ ] 理解依赖链的执行顺序
- [ ] 将业务逻辑从 endpoint 移到 Service 层
- [ ] 理解为什么同一个请求内依赖会被缓存
- [ ] 实现完整的 Repository → Service → Endpoint 三层架构
- [ ] 用生活化的类比给别人讲解依赖注入

---

## 💡 学习建议

1. **先理解，再编码**
   - 确保理解每个练习的目标
   - 思考依赖的执行流程
   - 画出依赖关系图

2. **逐步实现**
   - 先完成最简单的功能
   - 再逐步添加复杂逻辑
   - 每完成一步就测试

3. **观察日志**
   - 在依赖函数中添加 `print()` 语句
   - 观察函数的调用顺序
   - 验证自己的理解

4. **画图辅助理解**
   - 画出依赖关系图
   - 标注执行顺序
   - 标注数据流向

5. **写注释**
   - 在代码中写清楚每一步的作用
   - 解释为什么要这样设计
   - 记录你的思考过程

---

**恭喜你完成基础练习！现在你已经掌握了依赖注入的核心用法。**

**下一步：尝试进阶练习（02_intermediate_exercises.md）**
