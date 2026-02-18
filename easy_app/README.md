# FastAPI 学习应用

一个功能完整的 FastAPI 学习应用，涵盖 Python Web 开发的核心概念和现代最佳实践。

## 功能特性

- **用户管理系统**：注册、登录、JWT认证
- **待办事项管理**：完整的CRUD操作，支持分页和过滤
- **数据库集成**：SQLAlchemy 2.0 + Alembic迁移
- **API文档**：自动生成Swagger文档
- **测试覆盖**：单元测试和集成测试
- **中间件**：CORS、日志、错误处理
- **现代Python**：异步编程、类型注解、Pydantic v2

## 技术栈

- **Web框架**: FastAPI 0.104.1
- **ORM**: SQLAlchemy 2.0 (异步支持)
- **数据库**: SQLite (学习用，易于设置)
- **认证**: JWT (python-jose)
- **密码加密**: Passlib (bcrypt)
- **配置管理**: Pydantic Settings
- **测试**: pytest + pytest-asyncio
- **代码质量**: Black, Ruff

## 项目结构

```
fastapi-learning-app/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI应用入口
│   ├── database.py          # 数据库连接
│   ├── models/              # SQLAlchemy模型
│   │   ├── user.py          # 用户模型
│   │   └── todo.py          # 待办事项模型
│   ├── schemas/             # Pydantic模式
│   │   ├── user.py          # 用户模式
│   │   ├── todo.py          # 待办事项模式
│   │   └── token.py         # 令牌模式
│   ├── api/                 # API路由
│   │   ├── deps.py          # 依赖注入
│   │   └── v1/
│   │       ├── api.py       # 路由聚合
│   │       └── endpoints/
│   │           ├── auth.py  # 认证端点
│   │           ├── users.py # 用户管理
│   │           └── todos.py # 待办事项管理
│   ├── core/
│   │   ├── config.py        # 配置管理
│   │   └── security.py      # 安全工具
│   ├── crud/                # CRUD操作
│   │   ├── base.py          # 基础CRUD类
│   │   ├── user.py          # 用户CRUD
│   │   └── todo.py          # 待办事项CRUD
│   └── utils/               # 辅助函数
├── alembic/                 # 数据库迁移
├── tests/                   # 测试文件
├── requirements.txt         # 生产依赖
├── requirements-dev.txt     # 开发依赖
├── .env.example            # 环境变量示例
└── README.md               # 项目说明
```

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd fastapi-learning-app

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，修改必要的配置
# 至少需要修改 SECRET_KEY
```

### 3. 运行应用

```bash
# 开发模式运行
uvicorn app.main:app --reload

# 或者直接运行
python -m app.main
```

访问 http://localhost:8000 查看应用
访问 http://localhost:8000/api/v1/docs 查看API文档

### 4. 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_auth.py

# 运行测试并显示覆盖率
pytest --cov=app tests/
```

## API 使用示例

### 用户注册

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "testuser",
    "password": "password123"
  }'
```

### 用户登录

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=password123"
```

### 创建待办事项

```bash
curl -X POST "http://localhost:8000/api/v1/todos/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "学习 FastAPI",
    "description": "完成 FastAPI 学习项目"
  }'
```

### 获取待办事项列表

```bash
curl -X GET "http://localhost:8000/api/v1/todos/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 学习要点

### Python 基础概念

- **类型注解**：理解 Python 的类型系统
- **异步编程**：async/await 模式
- **面向对象**：类、继承、多态
- **装饰器模式**：函数装饰器的使用
- **上下文管理器**：with 语句和 async with

### FastAPI 核心概念

- **路由系统**：API 端点的定义和组织
- **依赖注入**：FastAPI 的核心特性
- **请求/响应模型**：Pydantic 的使用
- **自动文档生成**：OpenAPI/Swagger 集成
- **中间件系统**：请求处理流程

### Web 开发概念

- **RESTful API**：REST 原则和实践
- **HTTP 状态码**：正确使用状态码
- **JWT 认证**：无状态认证机制
- **CORS 原理**：跨域资源共享
- **数据库 ORM**：对象关系映射

### 最佳实践

- **代码组织**：模块化和分层架构
- **错误处理**：统一错误响应格式
- **测试策略**：单元测试和集成测试
- **配置管理**：环境变量和设置
- **安全性**：常见安全威胁和防护

## 开发指南

### 代码格式化

```bash
# 格式化代码
black app/ tests/

# 代码检查
ruff check app/ tests/

# 修复代码
ruff check --fix app/ tests/
```

### 数据库迁移

```bash
# 生成迁移文件
alembic revision --autogenerate -m "描述"

# 应用迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

### 添加新的API端点

1. 在 `app/models/` 中定义 SQLAlchemy 模型
2. 在 `app/schemas/` 中定义 Pydantic 模式
3. 在 `app/crud/` 中实现 CRUD 操作
4. 在 `app/api/v1/endpoints/` 中创建端点
5. 在 `app/api/v1/api.py` 中注册路由
6. 在 `tests/` 中添加测试

## 常见问题

### Q: 如何切换到 PostgreSQL？

A: 修改 `.env` 文件中的 `DATABASE_URL`：
```
DATABASE_URL="postgresql+asyncpg://user:password@localhost/dbname"
```
并安装 PostgreSQL 驱动：`pip install asyncpg`

### Q: 如何添加用户角色？

A: 扩展 User 模型，添加 role 字段，并在依赖项中检查权限。

### Q: 如何实现文件上传？

A: 使用 FastAPI 的 `UploadFile` 和 `File` 类型。

### Q: 如何添加 WebSocket？

A: 使用 FastAPI 的 WebSocket 支持，创建端点处理实时通信。

## 扩展功能

- [ ] 文件上传功能
- [ ] WebSocket 实时通信
- [ ] 缓存实现 (Redis)
- [ ] 消息队列 (Celery)
- [ ] API 版本控制
- [ ] GraphQL 支持
- [ ] Docker 部署
- [ ] CI/CD 配置

## 参考资源

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [SQLAlchemy 文档](https://docs.sqlalchemy.org/)
- [Pydantic 文档](https://docs.pydantic.dev/)
- [pytest 文档](https://docs.pytest.org/)

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License