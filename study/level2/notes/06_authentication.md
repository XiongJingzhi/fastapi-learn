# 安全认证与授权 - FastAPI Security

## 🎯 为什么需要认证和授权？

想象你家的门：

```
没有门锁：
    任何人都能进入 → 危险！❌

有门锁：
    需要钥匙才能进 → 安全 ✅
    但钥匙丢了 → 任何人都可能进 ❌

有门锁 + 指纹锁：
    你自己才能进 → 很安全 ✅
    不同的人有不同的权限 → 更安全 ✅
```

**Web 应用的安全**：

1. **认证 (Authentication)**：你是谁？
   - 用户名/密码登录
   - JWT Token
   - OAuth2（第三方登录）

2. **授权 (Authorization)**：你能做什么？
   - 普通用户：只能看自己的数据
   - 管理员：可以管理所有数据
   - 访客：只能看公开内容

---

## 🔐 密码安全

### 为什么不能明文存储密码？

```python
# ❌ 危险：明文存储密码
users_db = {
    "alice": "password123",  # 数据库泄露 = 密码泄露！
    "bob": "secret456"
}

# ✅ 安全：存储密码哈希
users_db = {
    "alice": "2a10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy",  # bcrypt
    "bob": "2a10$e9X3...another_hash"
}
```

**密码哈希的特点**：
- ✅ 单向（不能从哈希还原密码）
- ✅ 唯一（相同密码不同哈希，因为有 salt）
- ✅ 慢（防止暴力破解）

### bcrypt 密码哈希

```python
from passlib.context import CryptContext

# 创建密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 哈希密码
def hash_password(password: str) -> str:
    """将明文密码转为哈希"""
    return pwd_context.hash(password)

# 验证密码
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码是否正确"""
    return pwd_context.verify(plain_password, hashed_password)

# 使用
password = "my_password_123"
hashed = hash_password(password)
# $2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW

# 验证
is_valid = verify_password("my_password_123", hashed)  # True
is_valid = verify_password("wrong_password", hashed)   # False
```

---

## 🎫 JWT (JSON Web Tokens)

### 什么是 JWT？

```
JWT 就像一张"临时通行证"

登录成功 → 服务器给你一张通行证（JWT）
以后访问 → 出示通行证
服务器检查 → 验证通行证是真的
通过 → 允许访问
```

**JWT 的结构**：

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c

├─ Header（算法信息）
├─ Payload（数据：用户ID、过期时间等）
└─ Signature（签名：防伪造）
```

### 创建和验证 JWT

```python
from datetime import datetime, timedelta
from jose import JWTError, jwt
from typing import Optional

# 密钥（生产环境应该从环境变量读取）
SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建 JWT token"""
    to_encode = data.copy()

    # 设置过期时间
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})

    # 编码 JWT
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """验证 JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

# 使用
# 创建 token
token = create_access_token(
    data={"sub": "alice"},
    expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
)
# eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# 验证 token
payload = verify_token(token)
# {"sub": "alice", "exp": 1704067200}
```

---

## 🔑 OAuth2 密码流

### FastAPI Security 工具

```python
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

app = FastAPI()

# OAuth2 密码流：标准化的认证方式
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Token(BaseModel):
    """Token 响应"""
    access_token: str
    token_type: str

class User(BaseModel):
    """用户"""
    username: str
    email: str | None = None
    full_name: str | None = None
```

### 登录端点

```python
@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 密码流登录端点

    - 接收 username 和 password
    - 验证用户
    - 返回 JWT token
    """
    # 1. 验证用户
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. 创建 token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    # 3. 返回 token
    return {"access_token": access_token, "token_type": "bearer"}
```

### 受保护的端点

```python
from fastapi import Depends

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    依赖：从 token 获取当前用户

    使用：
    @app.get("/users/me")
    async def read_users_me(current_user: User = Depends(get_current_user)):
        return current_user
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 验证 token
    payload = verify_token(token)
    if payload is None:
        raise credentials_exception

    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception

    # 获取用户
    user = get_user(fake_users_db, username=username)
    if user is None:
        raise credentials_exception

    return user

# 使用依赖
@app.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    """获取当前用户信息（需要认证）"""
    return current_user
```

---

## 👥 权限控制

### 基于角色的访问控制 (RBAC)

```python
from enum import Enum

class Role(str, Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"

class UserInDB(BaseModel):
    username: str
    email: str
    role: Role = Role.USER

def require_role(required_role: Role):
    """创建角色检查依赖"""
    def role_checker(current_user: UserInDB = Depends(get_current_user)):
        if current_user.role != required_role and current_user.role != Role.ADMIN:
            raise HTTPException(
                status_code=403,
                detail="权限不足"
            )
        return current_user
    return role_checker

# 使用
@app.get("/admin/dashboard")
async def admin_dashboard(
    current_user: UserInDB = Depends(require_role(Role.ADMIN))
):
    """只有管理员能访问"""
    return {"message": f"欢迎管理员 {current_user.username}"}

@app.get("/users/profile")
async def user_profile(
    current_user: UserInDB = Depends(require_role(Role.USER))
):
    """登录用户就能访问"""
    return {"username": current_user.username}
```

### 基于权限的访问控制

```python
class Permission(str, Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"

class UserInDB(BaseModel):
    username: str
    permissions: list[Permission] = []

def has_permission(permission: Permission):
    """检查权限"""
    def permission_checker(current_user: UserInDB = Depends(get_current_user)):
        if permission not in current_user.permissions:
            raise HTTPException(
                status_code=403,
                detail=f"需要 {permission.value} 权限"
            )
        return current_user
    return permission_checker

# 使用
@app.post("/posts")
async def create_post(
    current_user: UserInDB = Depends(has_permission(Permission.WRITE))
):
    """需要写权限"""
    return {"message": "创建成功"}
```

---

## 🌐 CORS（跨域资源共享）

### 什么是 CORS？

```
同源策略：浏览器限制
    https://example.com 的页面
    → 只能访问 https://example.com 的 API
    → 不能访问 https://api.com（不同域）

CORS：允许跨域访问
    服务器设置响应头：
    Access-Control-Allow-Origin: *
    → 允许其他域的页面访问
```

### FastAPI CORS 中间件

```python
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    # 允许的源（开发环境可以用 *）
    allow_origins=[
        "http://localhost:3000",
        "https://myapp.com",
    ],
    # 允许所有方法（GET, POST, PUT, DELETE等）
    allow_methods=["*"],
    # 允许所有请求头
    allow_headers=["*"],
    # 允许携带凭证（cookies）
    allow_credentials=True,
    # 预检请求缓存时间（秒）
    max_age=600,
)
```

### 生产环境配置

```python
import os

# 生产环境：指定允许的域名
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # 不要在生产环境用 *
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    allow_credentials=True,
)
```

---

## 🛡️ 安全最佳实践

### 1. HTTPS 生产环境必须使用

```python
# 生产环境强制 HTTPS
@app.get("/secure-data")
async def secure_data(request: Request):
    if request.url.scheme != "https":
        raise HTTPException(
            status_code=400,
            detail="必须使用 HTTPS"
        )
    return {"data": "sensitive"}
```

### 2. 安全的响应头

```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

# 只允许特定域名
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["example.com", "*.example.com"]
)

# 自动重定向到 HTTPS
# （注意：部署服务器时通常在反向代理层面处理）
# app.add_middleware(HTTPSRedirectMiddleware)
```

### 3. 限速（Rate Limiting）

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/api/users")
@limiter.limit("5/minute")  # 每分钟最多 5 次
async def get_users(request: Request):
    return {"users": []}
```

### 4. 输入验证和清理

```python
from pydantic import BaseModel, Field, field_validator

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    email: str

    @field_validator('username')
    @classmethod
    def username_alphanumeric(cls, v):
        if not v.isalnum():
            raise ValueError('用户名只能包含字母和数字')
        return v

    @field_validator('email')
    @classmethod
    def email_normalization(cls, v):
        # 清理输入：转小写、去除空格
        return v.strip().lower()
```

### 5. SQL 注入防护

```python
# ✅ 使用参数化查询（ORM 自动处理）
user = session.query(User).filter(User.username == username).first()

# ❌ 危险：不要拼接 SQL
# query = f"SELECT * FROM users WHERE username = '{username}'"
# 如果 username = "'; DROP TABLE users; --" 会导致 SQL 注入
```

### 6. XSS 防护

```python
from fastapi.responses import JSONResponse

# FastAPI 自动转义 JSON 中的特殊字符
@app.get("/search")
async def search(q: str):
    # 即使 q = "<script>alert('XSS')</script>"
    # 也会被正确转义为 JSON
    return {"query": q}  # 自动转义
```

---

## 🔐 完整认证示例

```python
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import timedelta
from typing import Optional

app = FastAPI()

# 配置
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# 模型
class Token(BaseModel):
    access_token: str
    token_type: str

class User(BaseModel):
    username: str
    email: str | None = None

class UserInDB(User):
    hashed_password: str

# 模拟数据库
fake_users_db = {
    "alice": {
        "username": "alice",
        "email": "alice@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"
    }
}

# 辅助函数
def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)
    return None

def verify_password(plain_password, hashed_password):
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(db, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    from datetime import datetime
    from jose import jwt

    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    from jose import JWTError
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        from jose import jwt
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user(fake_users_db, username=username)
    if user is None:
        raise credentials_exception
    return user

# 端点
@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
```

---

## 📚 安全检查清单

### 密码安全
- [ ] 使用 bcrypt 或类似算法哈希密码
- [ ] 不要明文存储密码
- [ ] 强制密码复杂度要求
- [ ] 实现密码重置流程

### Token 安全
- [ ] 使用 HTTPS 传输 token
- [ ] Token 设置合理的过期时间
- [ ] 实现 token 刷新机制
- [ ] 在服务端存储 token 黑名单（可选）

### API 安全
- [ ] 验证所有输入
- [ ] 使用 CORS 限制跨域访问
- [ ] 实现速率限制
- [ ] 记录安全相关日志
- [ ] 定期审计权限

---

## 🎯 总结

**认证授权核心要点**：

1. ✅ **永远不要明文存储密码**
2. ✅ **使用 HTTPS 传输敏感数据**
3. ✅ **Token 要有合理的过期时间**
4. ✅ **实现权限分级控制**
5. ✅ **记录安全相关日志**

**安全工具**：
- `passlib` - 密码哈希
- `python-jose` - JWT 处理
- `fastapi.security` - OAuth2 支持
- `slowapi` - 速率限制

**记住**：
- 安全是持续的过程，不是一次性的
- 永远不要信任用户输入
- 默认拒绝，显式允许
- 定期进行安全审计

**下一步**：学习 WebSocket 和测试

---

**安全是应用的基础！** 🔒
