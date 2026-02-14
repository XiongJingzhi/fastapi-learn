# FastAPI 测试完全指南

## 🎯 为什么需要测试？

想象你在建造一座桥：

```
没有测试：
    建好桥 → 让车过去 → 桥塌了 → 太晚了！❌

有测试：
    建桥前 → 用模型测试承重 → 发现问题 → 修复 → 再测试
    建好桥 → 放心使用 ✅
```

**测试的价值**：

1. **提前发现 bug**：在生产环境之前发现问题
2. **重构的信心**：改代码时不怕破坏功能
3. **活的文档**：测试代码展示了代码如何使用
4. **开发效率**：自动化测试比手动测试快得多
5. **质量保证**：确保软件质量稳定

---

## 📚 测试类型金字塔

```
              /\
             /  \
            / E2E \        ← 端到端测试（少）
           /--------\
          / 集成测试 \      ← 集成测试（中）
         /------------\
        /   单元测试    \    ← 单元测试（多）
       /----------------\
```

### 单元测试

**定义**：测试单个函数或类，隔离其他依赖

```python
def test_add_user():
    """测试单个函数"""
    user = User(username="alice", email="alice@example.com")
    assert user.username == "alice"
    assert user.email == "alice@example.com"
```

**特点**：
- ✅ 快速（毫秒级）
- ✅ 隔离（不依赖数据库、网络）
- ✅ 可靠（不会因为外部因素失败）
- ✅ 数量多（应该占测试的 70%+）

### 集成测试

**定义**：测试多个组件如何协作

```python
def test_create_and_get_user():
    """测试 API + 数据库"""
    # 创建用户（通过 API）
    response = client.post("/users", json={"username": "alice"})
    assert response.status_code == 200

    # 获取用户（通过 API）
    response = client.get("/users/1")
    assert response.status_code == 200
    assert response.json()["username"] == "alice"
```

**特点**：
- ⚠️ 较慢（需要启动数据库等）
- ⚠️ 依赖外部服务
- ✅ 测试真实场景
- ✅ 数量适中（占 20-30%）

### 端到端测试

**定义**：测试完整用户流程

```python
def test_user_registration_flow():
    """测试用户注册流程"""
    # 1. 访问注册页面
    # 2. 填写表单
    # 3. 提交
    # 4. 检查邮箱
    # 5. 点击验证链接
    # 6. 登录
```

**特点**：
- ❌ 最慢（需要完整环境）
- ❌ 最脆弱（容易因各种原因失败）
- ✅ 最接近真实用户场景
- ✅ 数量最少（占 5-10%）

---

## 🛠️ FastAPI 测试工具

### TestClient

**FastAPI 自带的测试客户端**：

```python
from fastapi.testclient import TestClient
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello"}

# 创建测试客户端
client = TestClient(app)

# 使用
def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello"}
```

**TestClient 的特点**：
- ✅ 同步 API（不需要 async/await）
- ✅ 自动处理请求和响应
- ✅ 不启动真实服务器（更快）
- ✅ 支持 FastAPI 的所有功能

---

## 📦 pytest 配置

### 安装依赖

```bash
# requirements-test.txt
pytest==7.4.0
pytest-asyncio==0.21.0
httpx==0.24.0  # 异步测试需要
```

### pytest.ini

```ini
[pytest]
# 测试文件模式
python_files = test_*.py
# 测试类模式
python_classes = Test*
# 测试函数模式
python_functions = test_*
# 异步测试模式
asyncio_mode = auto
# 输出选项
addopts =
    -v
    --strict-markers
    --disable-warnings
    --tb=short
```

---

## 🎨 测试 Fixtures

### 基础 Fixture

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

# 测试数据库
TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    # 创建表
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # 清理
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db_session):
    """创建测试客户端"""
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    # 覆盖依赖
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    # 清理
    app.dependency_overrides.clear()
```

### 使用 Fixture

```python
def test_create_user(client):
    """使用 client fixture"""
    response = client.post(
        "/users",
        json={"username": "alice", "email": "alice@example.com"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "alice"
```

---

## 🧪 测试示例

### 1. 测试 API 端点

```python
def test_read_user(client):
    """测试获取用户"""
    # 先创建用户
    client.post("/users", json={"username": "alice"})

    # 测试获取
    response = client.get("/users/1")
    assert response.status_code == 200
    assert response.json()["username"] == "alice"

def test_read_user_not_found(client):
    """测试用户不存在"""
    response = client.get("/users/999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
```

### 2. 测试请求验证

```python
def test_create_user_validation_error(client):
    """测试参数验证"""
    response = client.post(
        "/users",
        json={"username": "a"}  # 太短
    )
    assert response.status_code == 422
    data = response.json()
    assert "username" in str(data)
```

### 3. 测试依赖注入

```python
from unittest.mock import Mock

def test_with_mock_dependency(client):
    """使用 mock 依赖"""
    # Mock 服务
    mock_service = Mock()
    mock_service.get_user.return_value = {"id": 1, "name": "Alice"}

    # 覆盖依赖
    app.dependency_overrides[get_user_service] = lambda: mock_service

    response = client.get("/users/1")
    assert response.status_code == 200

    # 验证 mock 被调用
    mock_service.get_user.assert_called_once_with(1)
```

### 4. 异步测试

```python
import pytest

@pytest.mark.asyncio
async def test_async_endpoint():
    """测试异步端点"""
    from app.main import app
    from httpx import AsyncClient

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/users")
        assert response.status_code == 200
```

### 5. 测试文件上传

```python
def test_upload_file(client):
    """测试文件上传"""
    file_content = b"Hello, World!"
    files = {"file": ("test.txt", file_content, "text/plain")}

    response = client.post("/upload", files=files)
    assert response.status_code == 200
    assert response.json()["filename"] == "test.txt"
```

### 6. 测试 WebSocket

```python
from fastapi.testclient import TestClient
from fastapi import FastAPI, WebSocket

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_json({"msg": "Hello"})
    await websocket.close()

def test_websocket(client):
    """测试 WebSocket"""
    with client.websocket_connect("/ws") as websocket:
        data = websocket.receive_json()
        assert data == {"msg": "Hello"}
```

---

## 🎭 Mock 和 Patch

### 为什么需要 Mock？

```python
# ❌ 没有 Mock：测试依赖外部服务
def test_send_email():
    user = create_user()
    send_welcome_email(user.email)  # 真的发邮件！
    # 问题：慢、不可靠、可能发垃圾邮件

# ✅ 使用 Mock：隔离外部依赖
from unittest.mock import patch, Mock

@patch("app.tasks.send_welcome_email")
def test_send_email_mock(mock_send):
    user = create_user()
    send_welcome_email(user.email)  # 被 Mock 了
    # 验证函数被调用
    mock_send.assert_called_once_with(user.email)
```

### Mock 常用技巧

```python
from unittest.mock import Mock, patch, MagicMock

# 1. Mock 返回值
mock_service = Mock()
mock_service.get_user.return_value = {"id": 1, "name": "Alice"}
result = mock_service.get_user(1)
assert result == {"id": 1, "name": "Alice"}

# 2. Mock 异常
mock_service.get_user.side_effect = ValueError("User not found")
with pytest.raises(ValueError):
    mock_service.get_user(1)

# 3. Patch 类方法
with patch("app.services.UserService.get_user") as mock_get:
    mock_get.return_value = user
    response = client.get("/users/1")
    mock_get.assert_called_once()

# 4. 检查调用
mock_service.get_user.assert_called()
mock_service.get_user.assert_called_with(1)
mock_service.get_user.assert_called_once()
assert mock_service.get_user.call_count == 3
```

---

## 📊 测试覆盖率

### 安装 coverage

```bash
pip install pytest-cov
```

### 运行覆盖率测试

```bash
# 生成覆盖率报告
pytest --cov=app --cov-report=html

# 在浏览器中查看
open htmlcov/index.html
```

### coverage.conf

```ini
[run]
source = app
omit =
    */tests/*
    */migrations/*
    */__init__.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
    @abstractmethod
```

### 目标覆盖率

| 组件 | 目标覆盖率 |
|------|-----------|
| 核心业务逻辑 | 90%+ |
| API 端点 | 80%+ |
| 工具函数 | 95%+ |
| 配置文件 | 50%+ |

---

## 💡 测试最佳实践

### 1. 测试命名

```python
# ✅ 好的命名
def test_user_creation_success():
    pass

def test_user_creation_with_invalid_email_fails():
    pass

# ❌ 不好的命名
def test_user():
    pass

def test1():
    pass
```

### 2. AAA 模式

```python
def test_create_user():
    # Arrange（准备）
    user_data = {"username": "alice", "email": "alice@example.com"}

    # Act（执行）
    response = client.post("/users", json=user_data)

    # Assert（断言）
    assert response.status_code == 200
    assert response.json()["username"] == "alice"
```

### 3. 一个测试只验证一件事

```python
# ❌ 不好：测试太多东西
def test_user():
    user = create_user()
    assert user.username == "alice"
    assert user.email == "alice@example.com"
    assert user.age == 25
    assert user.is_active == True
    # 如果这里失败，不知道是哪个字段的问题

# ✅ 好：每个测试独立
def test_user_has_correct_username():
    user = create_user(username="alice")
    assert user.username == "alice"

def test_user_has_correct_email():
    user = create_user(email="alice@example.com")
    assert user.email == "alice@example.com"
```

### 4. 使用描述性断言

```python
# ❌ 不好
assert user.age == 25

# ✅ 好（失败时会显示消息）
assert user.age == 25, f"Expected 25, got {user.age}"

# ✅ 更好
assert user.age >= 18, "User must be 18 or older"
```

### 5. 测试边界条件

```python
@pytest.mark.parametrize("age,expected", [
    (0, False),      # 最小边界
    (17, False),     # 边界下
    (18, True),      # 边界
    (19, True),      # 边界上
    (150, True),     # 最大边界
    (151, False),    # 超出边界
])
def test_user_age_validation(age, expected):
    user = User(age=age)
    assert user.is_adult() == expected
```

### 6. 测试异常

```python
def test_division_by_zero():
    with pytest.raises(ZeroDivisionError):
        1 / 0

def test_user_not_found():
    with pytest.raises(HTTPException) as exc_info:
        get_user(999)
    assert exc_info.value.status_code == 404
```

### 7. 使用 Markers 分组测试

```python
import pytest

@pytest.mark.unit
def test_calculate_total():
    pass

@pytest.mark.integration
def test_database_connection():
    pass

@pytest.mark.slow
def test_long_running_task():
    pass

# 运行特定标记
# pytest -m unit
# pytest -m "not slow"
```

---

## 🚀 运行测试

### 基本命令

```bash
# 运行所有测试
pytest

# 运行特定文件
pytest tests/test_users.py

# 运行特定测试
pytest tests/test_users.py::test_create_user

# 显示详细输出
pytest -v

# 只显示失败的测试
pytest --tb=no -q

# 失败时停止
pytest -x

# 失败时进入 pdb 调试
pytest --pdb
```

### 并行运行

```bash
pip install pytest-xdist

# 使用所有 CPU
pytest -n auto

# 使用 4 个进程
pytest -n 4
```

### 监视模式

```bash
pip install pytest-watch

# 文件变化时自动运行测试
ptw
```

---

## 📁 项目结构

```
project/
├── app/
│   ├── main.py
│   ├── models/
│   ├── routers/
│   └── services/
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # 共享 fixtures
│   ├── test_routes/
│   │   ├── __init__.py
│   │   ├── test_users.py
│   │   └── test_posts.py
│   ├── test_services/
│   │   ├── __init__.py
│   │   └── test_user_service.py
│   └── test_utils/
│       ├── __init__.py
│       └── test_helpers.py
├── pytest.ini
└── requirements-test.txt
```

---

## 🎯 测试检查清单

### 单元测试
- [ ] 测试所有公共方法
- [ ] 测试边界条件
- [ ] 测试异常情况
- [ ] 使用 Mock 隔离依赖

### 集成测试
- [ ] 测试 API 端点
- [ ] 测试数据库操作
- [ ] 测试外部服务集成
- [ ] 使用测试数据库

### 测试质量
- [ ] 测试命名清晰
- [ ] 遵循 AAA 模式
- [ ] 一个测试只验证一件事
- [ ] 覆盖率达到目标

---

## 📚 快速参考

### 常用断言

```python
# 相等性
assert a == b
assert a != b

# 布尔
assert True
assert False
assert x is True
assert x is False

# 比较
assert a > b
assert a >= b
assert a < b
assert a <= b

# 包含
assert x in [1, 2, 3]
assert "hello" in "hello world"

# 类型
assert isinstance(x, int)

# 异常
with pytest.raises(ValueError):
    raise ValueError

# 近似（浮点数）
assert a == pytest.approx(b, rel=1e-3)
```

### 常用 fixtures

```python
@pytest.fixture
def temp_file():
    """临时文件"""
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False) as f:
        yield f.name
    os.unlink(f.name)

@pytest.fixture
def mock_db():
    """Mock 数据库"""
    db = Mock()
    db.query.return_value.all.return_value = []
    return db

@pytest.fixture(scope="session")
def db_engine():
    """会话级别的 fixture（只创建一次）"""
    engine = create_engine("...")
    yield engine
    engine.dispose()
```

---

## 🎯 总结

**测试核心原则**：

1. ✅ **测试金字塔**：多单元测试，少 E2E 测试
2. ✅ **隔离性**：测试之间不互相依赖
3. ✅ **快速**：单元测试应该很快
4. ✅ **可靠**：测试应该稳定，不 flaky
5. ✅ **可维护**：测试代码也应该整洁

**记住**：
- 测试是代码的一部分，不是可选项
- 好的测试让重构变得安全
- 测试覆盖率不是唯一目标，测试质量更重要
- TDD（测试驱动开发）可以提高代码质量

**下一步**：实践编写测试！

---

**测试是软件质量的保障！** 🛡️
