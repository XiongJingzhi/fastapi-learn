# Level 1: FastAPI 作为协议适配层 - 学习记录

## 📚 学习目标

掌握 FastAPI 作为 HTTP 协议适配层的核心功能，学会正确处理请求和响应，理解 Web API 的设计原则。

## 核心原则

**⚠️ 重要约束**: 不在 endpoint 中写业务逻辑！

Endpoint 只负责：
- 接收请求 → 参数校验 → 调用服务层 → 返回响应

## 🎯 核心概念

1. **请求参数校验** - Query / Path / Body / Header / Cookie
2. **响应处理** - JSON / 文件 / Streaming / WebSocket
3. **统一响应格式** - 标准化 API 响应结构
4. **错误模型** - HTTP 状态码与异常处理
5. **RESTful 设计** - 资源命名与语义化

## 📁 本目录内容

```
study/level1/
├── README.md                  # 本文件：学习概览
├── notes/                     # 学习笔记和费曼讲解
│   ├── 01_request_validation.md
│   ├── 02_response_handling.md
│   ├── 03_unified_response.md
│   ├── 04_error_handling.md
│   └── 05_http_semantics.md
├── examples/                  # 代码示例
│   ├── 01_request_validation.py
│   ├── 02_response_handling.py
│   ├── 03_unified_response.py
│   ├── 04_error_handling.py
│   └── 05_restful_api.py
└── exercises/                 # 练习题和实验
    ├── 01_basic_exercises.md
    ├── 02_intermediate_exercises.md
    └── 03_challenge_projects.md
```

## 📖 学习路径

### 阶段 1.1: 请求参数校验

**学习时间**: 30-40分钟
**核心概念**: Pydantic 模型, 类型注解, 自动校验

**学习材料**:
- 笔记: `notes/01_request_validation.md`
- 示例: `examples/01_request_validation.py`
- 运行: `uvicorn app.examples.01_request_validation:app --reload`

**完成标准**:
- [ ] 理解 Path/Query/Body/Header/Cookie 参数的区别
- [ ] 能够使用 Pydantic 模型校验请求体
- [ ] 掌握参数类型转换和默认值
- [ ] 理解必填 vs 可选参数

**关键知识点**:
```python
# Path 参数
@app.get("/items/{item_id}")
async def read_item(item_id: int)

# Query 参数
@app.get("/items/")
async def read_items(skip: int = 0, limit: int = 10)

# Body 参数
class Item(BaseModel):
    name: str
    price: float

@app.post("/items/")
async def create_item(item: Item)
```

---

### 阶段 1.2: 响应处理

**学习时间**: 30-40分钟
**核心概念**: JSONResponse, FileResponse, StreamingResponse

**学习材料**:
- 笔记: `notes/02_response_handling.md`
- 示例: `examples/02_response_handling.py`

**完成标准**:
- [ ] 理解 FastAPI 默认的 JSON 序列化
- [ ] 能够返回文件响应
- [ ] 掌握流式响应（如大文件下载）
- [ ] 理解 WebSocket 基本用法

**关键知识点**:
```python
# JSON 响应（默认）
@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id, "name": "Foo"}

# 文件响应
from fastapi.responses import FileResponse
@app.get("/download")
async def download_file():
    return FileResponse("path/to/file")

# 流式响应
from fastapi.responses import StreamingResponse
async def generate():
    yield b"chunk1"
    yield b"chunk2"

@app.get("/stream")
async def stream_data():
    return StreamingResponse(generate())
```

---

### 阶段 1.3: 统一响应格式

**学习时间**: 25-30分钟
**核心概念**: 响应模型, Response Model, 数据封装

**学习材料**:
- 笔记: `notes/03_unified_response.md`
- 示例: `examples/03_unified_response.py`

**完成标准**:
- [ ] 设计统一的 API 响应格式
- [ ] 使用 `response_model` 声明响应类型
- [ ] 理解如何过滤敏感字段
- [ ] 掌握分页响应格式

**推荐响应格式**:
```json
{
  "code": 200,
  "message": "success",
  "data": {...},
  "timestamp": 1234567890
}
```

---

### 阶段 1.4: 错误处理

**学习时间**: 25-30分钟
**核心概念**: HTTPException, 异常处理器, 状态码

**学习材料**:
- 笔记: `notes/04_error_handling.md`
- 示例: `examples/04_error_handling.py`

**完成标准**:
- [ ] 理解常用 HTTP 状态码
- [ ] 能够抛出合适的 HTTPException
- [ ] 掌握全局异常处理器
- [ ] 理解如何返回错误详情

**关键知识点**:
```python
from fastapi import HTTPException

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")
    return items[item_id]

# 全局异常处理
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"message": str(exc)}
    )
```

---

### 阶段 1.5: HTTP 语义与 RESTful 设计

**学习时间**: 30-40分钟
**核心概念**: RESTful, HTTP 方法, 资源命名

**学习材料**:
- 笔记: `notes/05_http_semantics.md`
- 示例: `examples/05_restful_api.py`

**完成标准**:
- [ ] 理解 RESTful 设计原则
- [ ] 掌握 HTTP 方法的语义（GET/POST/PUT/DELETE）
- [ ] 学会设计资源 URL
- [ ] 理解幂等性和安全性

**RESTful 设计示例**:
```
GET    /users          # 列表
GET    /users/123      # 详情
POST   /users          # 创建
PUT    /users/123      # 更新
DELETE /users/123      # 删除
```

---

## 🧪 验证理解

运行测试验证你的理解：

```bash
pytest tests/test_fastapi_basics.py -v
```

**测试覆盖**:
- ✅ 请求参数校验
- ✅ 响应格式化
- ✅ 错误处理
- ✅ 状态码使用
- ✅ RESTful 设计

---

## 💡 学习建议

### 架构原则

**❌ 错误做法**:
```python
@app.post("/users")
async def create_user(user: User):
    # 直接在 endpoint 中写业务逻辑
    hashed_password = hash_password(user.password)
    db_user = db.save(user)
    send_email(user.email)
    return db_user
```

**✅ 正确做法**:
```python
@app.post("/users")
async def create_user(user: User, service: UserService = Depends()):
    # Endpoint 只负责协议适配
    return await service.create_user(user)
```

### 思考问题
- 为什么 FastAPI 使用 Pydantic 进行校验？
- 什么时候应该使用 4xx 错误，什么时候使用 5xx？
- 如何设计一个用户友好的错误响应？
- RESTful API 的 URL 设计原则是什么？

### 常见误区
- ❌ 在 endpoint 中直接操作数据库
- ✅ 通过服务层（Service Layer）处理业务逻辑

- ❌ 返回 200 错误码但消息中说明错误
- ✅ 使用正确的 HTTP 状态码

- ❌ 使用 GET 方法修改数据
- ✅ GET 方法应该是幂等的

---

## 🎓 完成标准

当你完成以下所有项，就说明 Level 1 达标了：

- [ ] 理解并实践所有 5 种参数类型（Path/Query/Body/Header/Cookie）
- [ ] 能够设计统一的响应格式
- [ ] 掌握常用 HTTP 状态码的使用场景
- [ ] 理解 RESTful 设计原则
- [ ] 通过所有测试
- [ ] 完成一个简单的 RESTful API（如 TODO API）
- [ ] 理解为什么不在 endpoint 中写业务逻辑

---

## 🚀 下一步

完成 Level 1 后，你将准备好进入 **Level 2: 依赖注入系统**！

Level 2 将学习：
- FastAPI 的依赖注入机制
- 如何组织可测试的代码
- 数据库连接管理
- 认证与授权

---

## 📝 学习记录

### 我的笔记
- 学习日期: _____________
- 完成阶段: _____________
- 遇到的问题: _____________
- 我的理解: _____________

### 我的实验
- 尝试过的修改: _____________
- 发现的有趣现象: _____________
- 仍然不理解的: _____________

---

**祝你学习愉快！记住：API 设计的第一要务是清晰！** 🚀
