# 如何定制国际化 Pydantic 异常处理

> **学习目标**: 掌握如何将 Pydantic 异常消息国际化，支持多语言错误提示  
> **难度**: ⭐⭐ 中等  
> **预计时间**: 30 分钟

---

## 📖 为什么需要国际化异常处理？

### 问题场景

**场景 1：中文用户**

```python
# 默认的 Pydantic 异常
UserCreate(name="", age=-1)

# 错误信息
{
    "detail": [
        {
            "loc": ["body", "name"],
            "msg": "ensure this value has at least 1 characters",
            "type": "value_error.any_str.min_length"
        },
        {
            "loc": ["body", "age"],
            "msg": "ensure this value is greater than or equal to 0",
            "type": "value_error.number.not_ge"
        }
    ]
}
```

**问题**: 错误信息是英文，中文用户看不懂

---

**场景 2：英文用户**

```python
# 假设你已经将错误信息翻译成中文
UserCreate(name="", age=-1)

# 错误信息
{
    "detail": [
        {
            "loc": ["body", "name"],
            "msg": "确保此值至少包含 1 个字符",
            "type": "value_error.any_str.min_length"
        },
        {
            "loc": ["body", "age"],
            "msg": "确保此值大于或等于 0",
            "type": "value_error.number.not_ge"
        }
    ]
}
```

**问题**: 英文用户看不懂中文错误信息

---

**理想场景**

```python
# 中文用户
UserCreate(name="", age=-1)
# 错误信息（中文）
{
    "detail": [
        {
            "loc": ["body", "name"],
            "msg": "姓名不能为空",
            "type": "value_error.any_str.min_length"
        },
        {
            "loc": ["body", "age"],
            "msg": "年龄不能小于 0",
            "type": "value_error.number.not_ge"
        }
    ]
}

# 英文用户
UserCreate(name="", age=-1)
# 错误信息（英文）
{
    "detail": [
        {
            "loc": ["body", "name"],
            "msg": "Name cannot be empty",
            "type": "value_error.any_str.min_length"
        },
        {
            "loc": ["body", "age"],
            "msg": "Age cannot be less than 0",
            "type": "value_error.number.not_ge"
        }
    ]
}
```

---

## 🎯 核心概念

### 1. Pydantic 的国际化支持

Pydantic v2 支持通过自定义错误消息来实现国际化。

**关键点**:
- ✅ **自定义错误消息**: 可以在每个字段上定义自定义错误消息
- ✅ **动态错误消息**: 可以使用函数动态生成错误消息
- ✅ **多语言支持**: 可以根据用户的语言设置返回不同的错误消息

---

### 2. FastAPI 的语言检测

FastAPI 可以通过以下方式检测用户的语言偏好：

**方法 1**: 通过 HTTP Header（推荐）
```python
from fastapi import FastAPI, Request

app = FastAPI()

@app.get("/items/{item_id}")
async def read_item(request: Request, item_id: int):
    # 获取 Accept-Language header
    accept_language = request.headers.get("accept-language", "en")
    # 提取主要语言（如：zh-CN → zh）
    lang = accept_language.split(",")[0].split("-")[0]
    return {"lang": lang, "item_id": item_id}
```

**方法 2**: 通过查询参数
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/items/{item_id}")
async def read_item(item_id: int, lang: str = "en"):
    return {"lang": lang, "item_id": item_id}
```

**方法 3**: 通过 JWT Token（推荐用于认证用户）
```python
from fastapi import FastAPI, Depends

app = FastAPI()

async def get_current_lang(token: str = Depends(get_current_user)):
    # 从 Token 中读取用户的语言设置
    user = decode_token(token)
    return user.lang
```

---

## 🔧 实现方案

### 方案 1: 使用 `pydantic.ValidationError` 自定义（推荐）

**优点**:
- ✅ 简单直接
- ✅ 性能好
- ✅ 易于维护

**缺点**:
- ⚠️ 需要为每个字段定义错误消息

---

#### 步骤 1: 创建国际化字典

```python
# app/i18n/errors.py

ERROR_MESSAGES = {
    "en": {
        "name": {
            "required": "Name is required",
            "min_length": "Name must be at least 1 character",
            "max_length": "Name must be at most 50 characters",
            "pattern": "Name must contain only letters and spaces",
        },
        "age": {
            "required": "Age is required",
            "ge": "Age must be greater than or equal to 0",
            "le": "Age must be less than or equal to 120",
        },
    },
    "zh": {
        "name": {
            "required": "姓名不能为空",
            "min_length": "姓名至少包含 1 个字符",
            "max_length": "姓名最多包含 50 个字符",
            "pattern": "姓名只能包含字母和空格",
        },
        "age": {
            "required": "年龄不能为空",
            "ge": "年龄不能小于 0",
            "le": "年龄不能大于 120",
        },
    },
}
```

---

#### 步骤 2: 创建自定义 Pydantic 模型

```python
# app/models/user.py

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from app.i18n.errors import ERROR_MESSAGES

class UserCreate(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        pattern=r"^[a-zA-Z\s]+$",
    )
    age: int = Field(
        ...,
        ge=0,
        le=120,
    )
    email: Optional[str] = None

    # 自定义错误消息（英文默认）
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "John Doe",
                    "age": 30,
                    "email": "john@example.com"
                }
            ]
        }
    }
```

---

#### 步骤 3: 创建全局异常处理器

```python
# app/exceptions/i18n_handler.py

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from typing import List, Dict, Any
from app.i18n.errors import ERROR_MESSAGES

def translate_error_message(
    msg: str,
    field_name: str,
    lang: str = "en"
) -> str:
    """翻译错误消息"""
    # 默认语言为英文
    lang = lang if lang in ERROR_MESSAGES else "en"
    
    # 尝试匹配错误消息
    error_messages = ERROR_MESSAGES[lang].get(field_name, {})
    
    # 如果找到对应的错误消息，返回翻译后的消息
    for key, value in error_messages.items():
        if key in msg.lower():
            return value
    
    # 如果没有找到，返回原始消息
    return msg

async def i18n_validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """国际化验证异常处理器"""
    # 获取用户的语言偏好
    lang = request.headers.get("accept-language", "en")
    lang = lang.split(",")[0].split("-")[0]  # 提取主要语言
    
    # 转换错误消息
    errors: List[Dict[str, Any]] = []
    for error in exc.errors():
        # 获取字段名
        field_name = error["loc"][-1] if error["loc"] else "unknown"
        
        # 翻译错误消息
        translated_msg = translate_error_message(
            error["msg"],
            str(field_name),
            lang
        )
        
        errors.append({
            "loc": error["loc"],
            "msg": translated_msg,
            "type": error["type"],
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": errors},
    )
```

---

#### 步骤 4: 注册异常处理器

```python
# app/main.py

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from app.exceptions.i18n_handler import i18n_validation_exception_handler

app = FastAPI()

# 注册全局异常处理器
app.add_exception_handler(
    RequestValidationError,
    i18n_validation_exception_handler
)

# 测试路由
from app.models.user import UserCreate

@app.post("/users")
async def create_user(user: UserCreate):
    return user
```

---

#### 步骤 5: 测试国际化异常处理

```python
# 测试中文用户
# Request Headers: accept-language: zh-CN
POST /users
Content-Type: application/json
Accept-Language: zh-CN

{
    "name": "",
    "age": -1
}

# Response
{
    "detail": [
        {
            "loc": ["body", "name"],
            "msg": "姓名至少包含 1 个字符",
            "type": "value_error.any_str.min_length"
        },
        {
            "loc": ["body", "age"],
            "msg": "年龄不能小于 0",
            "type": "value_error.number.not_ge"
        }
    ]
}

# 测试英文用户
# Request Headers: accept-language: en-US
POST /users
Content-Type: application/json
Accept-Language: en-US

{
    "name": "",
    "age": -1
}

# Response
{
    "detail": [
        {
            "loc": ["body", "name"],
            "msg": "Name must be at least 1 character",
            "type": "value_error.any_str.min_length"
        },
        {
            "loc": ["body", "age"],
            "msg": "Age must be greater than or equal to 0",
            "type": "value_error.number.not_ge"
        }
    ]
}
```

---

### 方案 2: 使用 `pydantic-translations` 库

**优点**:
- ✅ 功能强大
- ✅ 支持多种国际化框架
- ✅ 社区支持好

**缺点**:
- ⚠️ 需要安装额外的库
- ⚠️ 学习成本较高

---

#### 安装库

```bash
pip install pydantic-translations
```

---

#### 使用示例

```python
# app/i18n/translations.py

from pydantic_translations import PydanticI18n

# 初始化国际化
i18n = PydanticI18n(
    default_locale="en",
    locales={
        "en": {
            "name": {
                "required": "Name is required",
                "min_length": "Name must be at least 1 character",
            },
            "age": {
                "required": "Age is required",
                "ge": "Age must be greater than or equal to 0",
            },
        },
        "zh": {
            "name": {
                "required": "姓名不能为空",
                "min_length": "姓名至少包含 1 个字符",
            },
            "age": {
                "required": "年龄不能为空",
                "ge": "年龄不能小于 0",
            },
        },
    },
)

# 使用国际化
class UserCreate(BaseModel):
    name: str
    age: int

# 翻译验证错误
error_messages = i18n.translate_validation_errors(
    validation_error,
    locale="zh"
)
```

---

### 方案 3: 使用 FastAPI 的依赖注入（推荐）

**优点**:
- ✅ 灵活
- ✅ 可以访问请求上下文
- ✅ 易于测试

**缺点**:
- ⚠️ 需要为每个模型添加依赖

---

#### 实现示例

```python
# app/dependencies/i18n.py

from fastapi import Depends, Request, Header
from typing import Optional

async def get_lang(
    request: Request,
    accept_language: Optional[str] = Header(None)
) -> str:
    """获取用户的语言偏好"""
    # 优先级：1. Accept-Language Header > 2. 查询参数 > 3. 默认值
    
    # 1. 从 Header 获取
    if accept_language:
        return accept_language.split(",")[0].split("-")[0]
    
    # 2. 从查询参数获取
    lang = request.query_params.get("lang")
    if lang:
        return lang
    
    # 3. 默认值
    return "en"
```

---

#### 使用示例

```python
# app/main.py

from fastapi import FastAPI, Depends, Request
from app.models.user import UserCreate
from app.dependencies.i18n import get_lang
from app.exceptions.i18n_handler import i18n_validation_exception_handler

app = FastAPI()

# 注册全局异常处理器
app.add_exception_handler(
    RequestValidationError,
    i18n_validation_exception_handler
)

@app.post("/users")
async def create_user(
    user: UserCreate,
    lang: str = Depends(get_lang)
):
    # lang 会在异常处理器中使用
    return user
```

---

## 🎯 完整示例

### 项目结构

```
app/
├── i18n/
│   └── errors.py          # 国际化错误消息字典
├── models/
│   └── user.py           # Pydantic 模型
├── exceptions/
│   └── i18n_handler.py   # 国际化异常处理器
├── dependencies/
│   └── i18n.py          # 语言依赖
└── main.py              # FastAPI 应用
```

---

### 完整代码

```python
# app/i18n/errors.py

ERROR_MESSAGES = {
    "en": {
        "name": {
            "required": "Name is required",
            "min_length": "Name must be at least 1 character",
            "max_length": "Name must be at most 50 characters",
            "pattern": "Name must contain only letters and spaces",
        },
        "age": {
            "required": "Age is required",
            "ge": "Age must be greater than or equal to 0",
            "le": "Age must be less than or equal to 120",
        },
        "email": {
            "email": "Invalid email format",
        },
    },
    "zh": {
        "name": {
            "required": "姓名不能为空",
            "min_length": "姓名至少包含 1 个字符",
            "max_length": "姓名最多包含 50 个字符",
            "pattern": "姓名只能包含字母和空格",
        },
        "age": {
            "required": "年龄不能为空",
            "ge": "年龄不能小于 0",
            "le": "年龄不能大于 120",
        },
        "email": {
            "email": "邮箱格式不正确",
        },
    },
}
```

---

```python
# app/models/user.py

from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional

class UserCreate(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        pattern=r"^[a-zA-Z\u4e00-\u9fa5\s]+$",  # 支持中文
        description="用户姓名"
    )
    age: int = Field(
        ...,
        ge=0,
        le=120,
        description="用户年龄"
    )
    email: Optional[EmailStr] = Field(
        None,
        description="用户邮箱"
    )

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name.required")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "张三",
                    "age": 30,
                    "email": "zhangsan@example.com"
                }
            ]
        }
    }


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    age: Optional[int] = Field(None, ge=0, le=120)
    email: Optional[EmailStr] = None
```

---

```python
# app/exceptions/i18n_handler.py

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from typing import List, Dict, Any
from app.i18n.errors import ERROR_MESSAGES

def translate_error_message(
    msg: str,
    field_name: str,
    lang: str = "en"
) -> str:
    """翻译错误消息"""
    lang = lang if lang in ERROR_MESSAGES else "en"
    
    error_messages = ERROR_MESSAGES[lang].get(field_name, {})
    
    # 匹配错误消息
    if "required" in msg.lower() or "field required" in msg.lower():
        return error_messages.get("required", msg)
    elif "min_length" in msg.lower():
        return error_messages.get("min_length", msg)
    elif "max_length" in msg.lower():
        return error_messages.get("max_length", msg)
    elif "pattern" in msg.lower():
        return error_messages.get("pattern", msg)
    elif "ge" in msg.lower():
        return error_messages.get("ge", msg)
    elif "le" in msg.lower():
        return error_messages.get("le", msg)
    elif "email" in msg.lower():
        return error_messages.get("email", msg)
    
    return msg

async def i18n_validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """国际化验证异常处理器"""
    lang = request.headers.get("accept-language", "en")
    lang = lang.split(",")[0].split("-")[0]
    
    errors: List[Dict[str, Any]] = []
    for error in exc.errors():
        field_name = error["loc"][-1] if error["loc"] else "unknown"
        
        translated_msg = translate_error_message(
            error["msg"],
            str(field_name),
            lang
        )
        
        errors.append({
            "loc": error["loc"],
            "msg": translated_msg,
            "type": error["type"],
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": errors},
    )
```

---

```python
# app/main.py

from fastapi import FastAPI, Depends, Header
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.models.user import UserCreate, UserUpdate
from app.exceptions.i18n_handler import i18n_validation_exception_handler

app = FastAPI(
    title="User API",
    description="用户管理 API，支持国际化错误处理"
)

# 注册全局异常处理器
app.add_exception_handler(
    RequestValidationError,
    i18n_validation_exception_handler
)

# 语言依赖
async def get_lang(accept_language: Optional[str] = Header(None)) -> str:
    """获取用户的语言偏好"""
    if accept_language:
        return accept_language.split(",")[0].split("-")[0]
    return "en"

@app.post("/users", response_model=UserCreate)
async def create_user(
    user: UserCreate,
    lang: str = Depends(get_lang)
):
    """创建用户"""
    return user

@app.put("/users/{user_id}", response_model=UserUpdate)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    lang: str = Depends(get_lang)
):
    """更新用户"""
    return user_update

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok"}
```

---

## 🧪 测试

### 测试中文用户

```bash
# 测试中文用户
curl -X POST "http://localhost:8000/users" \
  -H "Content-Type: application/json" \
  -H "Accept-Language: zh-CN" \
  -d '{
    "name": "",
    "age": -1,
    "email": "invalid-email"
  }'

# Response
{
  "detail": [
    {
      "loc": ["body", "age"],
      "msg": "年龄不能小于 0",
      "type": "value_error.number.not_ge"
    },
    {
      "loc": ["body", "name"],
      "msg": "姓名不能为空",
      "type": "value_error.missing"
    },
    {
      "loc": ["body", "email"],
      "msg": "邮箱格式不正确",
      "type": "value_error.email"
    }
  ]
}
```

---

### 测试英文用户

```bash
# 测试英文用户
curl -X POST "http://localhost:8000/users" \
  -H "Content-Type: application/json" \
  -H "Accept-Language: en-US" \
  -d '{
    "name": "",
    "age": -1,
    "email": "invalid-email"
  }'

# Response
{
  "detail": [
    {
      "loc": ["body", "age"],
      "msg": "Age must be greater than or equal to 0",
      "type": "value_error.number.not_ge"
    },
    {
      "loc": ["body", "name"],
      "msg": "Name is required",
      "type": "value_error.missing"
    },
    {
      "loc": ["body", "email"],
      "msg": "Invalid email format",
      "type": "value_error.email"
    }
  ]
}
```

---

## 🎯 最佳实践

### 1. 使用标准 HTTP Header

**推荐**: 使用 `Accept-Language` Header

```python
# 客户端设置语言
fetch('/users', {
    headers: {
        'Accept-Language': 'zh-CN'
    }
})

# 服务端读取语言
lang = request.headers.get("accept-language", "en")
```

---

### 2. 支持语言回退

**推荐**: 支持语言回退（如：zh-CN → zh → en）

```python
def get_lang_with_fallback(lang: str) -> str:
    """获取语言，支持回退"""
    # 尝试完整语言代码（如：zh-CN）
    if lang in ERROR_MESSAGES:
        return lang
    
    # 尝试主语言（如：zh）
    main_lang = lang.split("-")[0]
    if main_lang in ERROR_MESSAGES:
        return main_lang
    
    # 回退到默认语言
    return "en"
```

---

### 3. 缓存翻译结果

**推荐**: 缓存翻译结果以提高性能

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def translate_error_message_cached(msg: str, field_name: str, lang: str) -> str:
    """翻译错误消息（带缓存）"""
    return translate_error_message(msg, field_name, lang)
```

---

### 4. 使用专业的国际化框架

**推荐**: 对于复杂项目，使用专业的国际化框架

**推荐框架**:
- `Babel` - Python 国际化框架
- `gettext` - 标准 Python 国际化框架
- `fastapi-i18n` - FastAPI 专用国际化框架

---

## 📊 总结

### 核心要点

1. **Pydantic 支持国际化**: Pydantic v2 支持自定义错误消息
2. **FastAPI 语言检测**: 可以通过 HTTP Header、查询参数等方式检测语言
3. **全局异常处理器**: 使用全局异常处理器统一处理验证错误
4. **翻译函数**: 使用翻译函数将英文错误消息翻译成目标语言

### 实现步骤

1. ✅ 创建国际化字典（`ERROR_MESSAGES`）
2. ✅ 创建 Pydantic 模型（定义字段和验证规则）
3. ✅ 创建全局异常处理器（翻译错误消息）
4. ✅ 注册全局异常处理器（`app.add_exception_handler`）
5. ✅ 测试国际化异常处理

### 适用场景

- 🌍 **国际化应用**: 需要支持多语言的 API
- 🎯 **用户体验**: 需要提供友好的错误提示
- 🔄 **动态语言**: 需要根据用户的语言设置返回不同的错误消息

---

**完成！** 🎉 你现在可以定制国际化的 Pydantic 异常处理了！
