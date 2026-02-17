# Pydantic 基础 - 数据验证的"守门员"

## 🎯 什么是 Pydantic？

想象你是一家高级餐厅的**门口守门员**：

```
没有守门员（没有 Pydantic）：
    顾客穿拖鞋进来 → 店里才发现不符合要求 → 尴尬！
    顾客带宠物进来 → 其他客人投诉 → 麻烦！
    顾客预订了10人只来2人 → 浪费桌子 → 损失！

有守门员（使用 Pydantic）：
    顾客到门口 → 守门员检查着装、人数、预约
    ✅ 符合要求 → 请进
    ❌ 不符合 → 礼貌拒绝，说明原因
    店里秩序井然，大家都很开心！
```

**Pydantic 就是 FastAPI 的"守门员"**：

- 在数据进入你的程序**之前**检查它
- 不符合规则的数据**直接拒绝**
- 符合规则的数据**转换成正确的格式**
- **自动生成**错误提示，告诉用户哪里错了

---

## 💡 为什么需要数据验证？

### 真实世界的问题

假设你写了一个用户注册接口：

```python
# ❌ 没有数据验证
@app.post("/users")
async def register_user(username: str, email: str, age: int):
    # 直接保存到数据库
    db.save(username, email, age)

问题：
1. 用户名可以是空字符串 ""
2. 邮箱可以是 "invalid-email"（不是有效邮箱）
3. 年龄可以是 -5（负数！）或 2000（不合理）
4. 保存后才发现问题 → 数据库被污染
```

### 使用 Pydantic 后

```python
# ✅ 有数据验证
from pydantic import BaseModel, Field, EmailStr, field_validator

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    email: EmailStr  # 自动验证邮箱格式
    age: int = Field(..., ge=0, le=150)  # 0-150岁

@app.post("/users")
async def register_user(user: UserCreate):
    # 数据已经被验证过了，放心使用
    db.save(user.username, user.email, user.age)
```

**好处**：
1. ✅ 用户名必须 3-20 个字符
2. ✅ 邮箱格式自动验证
3. ✅ 年龄必须在 0-150 之间
4. ✅ 不符合规则的数据**根本进不来**
5. ✅ 用户立即收到友好的错误提示

---

## 🔑 核心概念

### 1. BaseModel（基础模型）

就像一个**产品说明书**，规定了数据应该长什么样：

```python
from pydantic import BaseModel

class User(BaseModel):
    """用户模型"""
    id: int
    name: str
    email: str
    age: int

# 使用：自动验证和转换
user = User(
    id="123",      # 字符串 → 自动转为整数
    name="Alice",
    email="alice@example.com",
    age=25
)

print(user.id)    # 123 (int)
print(user.name)  # "Alice" (str)
```

**关键特点**：
- ✅ **类型声明**：告诉 Pydantic 每个字段应该是什么类型
- ✅ **自动转换**：尝试把输入转换成正确的类型
- ✅ **自动验证**：转换失败就报错
- ✅ **点号访问**：像对象一样访问数据 (`user.name`)

---

### 2. Field（字段配置）

**Field 就像更详细的"产品规格说明"**：

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    username: str = Field(
        ...,
        min_length=3,
        max_length=20,
        description="用户名"
    )
    email: str = Field(..., regex=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    age: int = Field(..., ge=0, le=150, description="年龄")
    is_active: bool = Field(True, description="是否激活")
```

**常用的 Field 参数**：

| 参数 | 含义 | 示例 |
|------|------|------|
| `...` | 必填字段 | `name: str = Field(...)` |
| `default` | 默认值 | `age: int = Field(18)` |
| `ge` | 大于等于 | `age: int = Field(..., ge=0)` |
| `le` | 小于等于 | `age: int = Field(..., le=150)` |
| `gt` | 大于 | `price: float = Field(..., gt=0)` |
| `lt` | 小于 | `discount: float = Field(..., lt=1)` |
| `min_length` | 最小长度 | `name: str = Field(..., min_length=3)` |
| `max_length` | 最大长度 | `name: str = Field(..., max_length=20)` |
| `regex` | 正则表达式 | `phone: str = Field(..., regex=r"^1\d{10}$")` |

---

### 3. validator（验证器）

**validator 就像"特种检查员"**，做更复杂的验证：

```python
from pydantic import BaseModel, field_validator

class UserCreate(BaseModel):
    username: str
    password: str

    @field_validator('username')
    @classmethod
    def username_must_not_contain_space(cls, v):
        """用户名不能包含空格"""
        if ' ' in v:
            raise ValueError('用户名不能包含空格')
        return v

    @field_validator('password')
    @classmethod
    def password_must_be_strong(cls, v):
        """密码必须足够强"""
        if len(v) < 8:
            raise ValueError('密码至少8位')
        if not any(c.isupper() for c in v):
            raise ValueError('密码必须包含大写字母')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含数字')
        return v
```

**工作原理**：
1. Pydantic 先做基础类型检查
2. 然后调用 `@field_validator` 装饰的函数
3. 验证失败就抛出 `ValueError`

---

### 4. root_validator（根验证器）

**root_validator 就像"最终审核员"**，检查**多个字段之间的关系**：

```python
from pydantic import BaseModel, model_validator

class Payment(BaseModel):
    amount: float
    currency: str
    account_balance: float

    @model_validator(mode='after')
    @classmethod
    def check_sufficient_balance(cls, data):
        """检查余额是否充足"""
        if data.amount and data.account_balance and data.amount > data.account_balance:
            raise ValueError('余额不足，无法完成支付')

        return data
```

**使用场景**：
- 检查两个字段之间的关系（如：开始时间 < 结束时间）
- 需要访问多个字段才能做的验证
- 根据一个字段的值验证另一个字段

---

## 🎨 常用类型

### 基础类型

```python
from pydantic import BaseModel
from typing import Optional, List

class Item(BaseModel):
    # 基础类型
    id: int
    name: str
    price: float
    is_available: bool

    # 可选字段（可以是 None）
    description: Optional[str] = None

    # 默认值
    tags: List[str] = []

    # 嵌套模型
    class Category(BaseModel):
        id: int
        name: str

    category: Category
```

### 特殊类型

```python
from pydantic import BaseModel, EmailStr, HttpUrl, Field, field_validator
from datetime import datetime
from decimal import Decimal

class User(BaseModel):
    # EmailStr - 自动验证邮箱格式
    email: EmailStr

    # HttpUrl - 自动验证 URL
    website: HttpUrl

    # datetime - 自动解析日期时间
    created_at: datetime

    # Decimal - 精确的十进制数（用于货币）
    balance: Decimal
```

---

## 🔄 与 FastAPI 的集成

### FastAPI 自动使用 Pydantic

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class UserCreate(BaseModel):
    username: str
    email: str
    age: int

@app.post("/users")
async def create_user(user: UserCreate):
    """
    FastAPI 自动：
    1. 验证请求数据
    2. 转换成 UserCreate 对象
    3. 验证失败自动返回 422 错误
    """
    # 直接使用，数据已经验证过了
    return {
        "username": user.username,
        "email": user.email,
        "age": user.age
    }
```

### 请求示例

```bash
# ✅ 成功的请求
curl -X POST "http://localhost:8000/users" \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "email": "alice@example.com", "age": 25}'

# ❌ 验证失败的请求
curl -X POST "http://localhost:8000/users" \
  -H "Content-Type: application/json" \
  -d '{"username": "a", "email": "invalid", "age": -5}'

# 响应：
# {
#   "detail": [
#     {
#       "loc": ["body", "username"],
#       "msg": "ensure this value has at least 3 characters",
#       "type": "value_error.any_str.min_length"
#     },
#     {
#       "loc": ["body", "email"],
#       "msg": "value is not a valid email address",
#       "type": "value_error.email"
#     },
#     {
#       "loc": ["body", "age"],
#       "msg": "ensure this value is greater than or equal to 0",
#       "type": "value_error.number.not_ge"
#     }
#   ]
# }
```

---

## ⚠️ 常见陷阱

### 陷阱 1：混淆 None 和可选字段

```python
# ❌ 错误
class Item(BaseModel):
    name: str = None  # 类型不匹配：str 不是 None

# ✅ 正确
from typing import Optional
class Item(BaseModel):
    name: Optional[str] = None  # 可以是 str 或 None
```

### 陷阱 2：修改验证后的数据

```python
# ❌ 错误：Pydantic 模型默认是不可变的
user = User(id=1, name="Alice")
user.name = "Bob"  # 报错！

# ✅ 正确：使用 .model_dump() 或 .copy()
user_dict = user.model_dump()
user_dict["name"] = "Bob"  # 可以修改

# 或者配置模型为可变的
from pydantic import ConfigDict

class User(BaseModel):
    name: str

    model_config = ConfigDict(validate_assignment=True)  # 允许修改后重新验证
```

### 陷阱 3：忘记处理数据类型转换

```python
# ⚠️ 注意：Pydantic 会自动转换类型
class Item(BaseModel):
    price: float

item = Item(price="99.99")  # 字符串 → float
print(item.price)  # 99.99 (float)

# 如果不需要自动转换，使用 StrictStr
from pydantic import StrictStr

class Item(BaseModel):
    price: StrictStr  # 必须是字符串，不转换

item = Item(price="99.99")  # ✅
item = Item(price=99.99)    # ❌ 报错：必须是字符串
```

---

## 💡 最佳实践

### 1. 分层定义模型

```python
# ✅ 推荐：分离输入、输出、数据库模型

class UserBase(BaseModel):
    """基础字段"""
    username: str
    email: str

class UserCreate(UserBase):
    """创建用户时的输入"""
    password: str

class UserInDB(UserBase):
    """数据库中的完整用户"""
    id: int
    password_hash: str
    created_at: datetime

class UserResponse(UserBase):
    """返回给客户端的数据（不包含密码）"""
    id: int
    created_at: datetime
```

### 2. 使用 ConfigDict 配置模型

```python
from pydantic import ConfigDict

class User(BaseModel):
    username: str
    email: str

    model_config = ConfigDict(
        from_attributes=True,        # 允许从 ORM 对象创建
        populate_by_name=True,       # 字段别名（使用 camelCase）
        validate_assignment=True,    # 验证赋值
        use_enum_values=True         # 使用枚举值而不是名称
    )
```

### 3. 提供有意义的错误信息

```python
from pydantic import BaseModel, Field, field_validator

class UserCreate(BaseModel):
    password: str = Field(..., min_length=8)

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('密码至少需要8个字符')
        # 提供具体的改进建议
        if not any(c.isupper() for c in v):
            raise ValueError('密码必须包含至少一个大写字母')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含至少一个数字')
        return v
```

---

## 📚 快速参考

### 常用导入

```python
from pydantic import BaseModel, Field, field_validator, root_validator
from pydantic import EmailStr, HttpUrl, ValidationError
from typing import Optional, List, Dict
from datetime import datetime
from decimal import Decimal
```

### 验证数据

```python
try:
    user = User(**data)
except ValidationError as e:
    print(e)  # 打印详细的错误信息
```

### 导出数据

```python
user = User(id=1, name="Alice")

# 转为字典
user_dict = user.model_dump()

# 转为 JSON
user_json = user.model_dump_json()

# 排除某些字段
user_dict = user.dict(exclude={"password"})

# 只包含某些字段
user_dict = user.dict(include={"id", "name"})
```

---

## 🎯 总结

**Pydantic 的核心价值**：

1. ✅ **提前发现错误**：数据进入程序前就验证
2. ✅ **自动转换类型**：把字符串 "123" 转为整数 123
3. ✅ **清晰的定义**：用代码定义数据应该长什么样
4. ✅ **友好的错误**：自动生成详细的错误提示
5. ✅ **与 FastAPI 无缝集成**：开箱即用

**记住**：
- Pydantic 就像一个"守门员"，保护你的程序
- 使用 BaseModel 定义数据模型
- 使用 Field 设置字段约束
- 使用 validator 做复杂验证
- 使用 root_validator 验证多个字段的关系

**下一步**：学习如何在 FastAPI 中使用 Pydantic（Level 1）

---

**Pydantic 让数据验证变得简单而强大！** 🛡️
