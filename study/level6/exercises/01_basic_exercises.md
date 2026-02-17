# Level 6 基础练习题

## 🎯 练习目标

通过实战练习，掌握微服务基础架构，包括服务拆分、服务间通信、API 网关等。

---

## 练习 1: 从单体应用拆分为微服务

### 题目

将一个单体应用拆分为多个微服务。

### 要求

1. 创建用户服务（User Service）
2. 创建订单服务（Order Service）
3. 创建产品服务（Product Service）
4. 实现服务间通信

### 单体应用代码

`monolith/main.py`:

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# 模拟数据库
users = {
    1: {"id": 1, "name": "Alice", "email": "alice@example.com"},
}

products = {
    1: {"id": 1, "name": "Laptop", "price": 999.99},
}

orders = []

class OrderCreate(BaseModel):
    user_id: int
    product_id: int
    quantity: int

@app.post("/orders")
def create_order(order: OrderCreate):
    # 验证用户
    if order.user_id not in users:
        return {"error": "User not found"}

    # 验证产品
    if order.product_id not in products:
        return {"error": "Product not found"}

    # 创建订单
    new_order = {
        "id": len(orders) + 1,
        "user": users[order.user_id],
        "product": products[order.product_id],
        "quantity": order.quantity
    }
    orders.append(new_order)
    return new_order
```

### 任务

1. 拆分为三个独立的服务
2. 订单服务需要调用用户服务和产品服务
3. 使用 httpx 进行服务间通信

### 检查清单

- [ ] 用户服务独立运行
- [ ] 产品服务独立运行
- [ ] 订单服务独立运行
- [ ] 订单服务成功调用用户服务
- [ ] 订单服务成功调用产品服务

---

## 练习 2: 实现 API 网关

### 题目

实现一个简单的 API 网关，统一管理所有服务的路由。

### 要求

1. 创建 API 网关服务
2. 实现路由转发
3. 测试所有服务通过网关访问

### 提示

```python
from fastapi import FastAPI, Request, HTTPException
import httpx

app = FastAPI()

services = {
    "users": "http://user-service:8001",
    "orders": "http://order-service:8002",
    "products": "http://product-service:8003",
}

@app.api_route("/api/{service}/{path:path}")
async def proxy_request(service: str, path: str, request: Request):
    # 转发请求到对应服务
    pass
```

### 检查清单

- [ ] API 网关成功路由用户服务请求
- [ ] API 网关成功路由订单服务请求
- [ ] API 网关成功路由产品服务请求
- [ ] 客户端只需知道网关地址

---

## 练习 3: 使用 Docker Compose 编排服务

### 题目

使用 Docker Compose 编排所有微服务。

### 要求

1. 为每个服务创建 Dockerfile
2. 编写 docker-compose.yml
3. 使用 `docker-compose up` 启动所有服务

### 提示

```yaml
version: '3.8'

services:
  user-service:
    build: ./user-service
    ports:
      - "8001:8000"

  order-service:
    build: ./order-service
    ports:
      - "8002:8000"
    depends_on:
      - user-service
      - product-service

  product-service:
    build: ./product-service
    ports:
      - "8003:8000"

  api-gateway:
    build: ./api-gateway
    ports:
      - "8000:8000"
    depends_on:
      - user-service
      - order-service
      - product-service
```

### 检查清单

- [ ] 所有服务成功启动
- [ ] 服务间可以互相通信
- [ ] 通过网关可以访问所有服务
- [ ] 服务健康检查正常

---

## 练习 4: 添加服务健康检查

### 题目

为每个服务添加健康检查端点。

### 要求

1. 每个服务添加 `/health` 端点
2. 返回服务名称和状态
3. API 网关聚合所有服务的健康状态

### 提示

```python
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "user-service"
    }
```

### 检查清单

- [ ] 每个服务都有健康检查端点
- [ ] API 网关有聚合健康检查端点
- [ ] 健康检查返回服务状态
- [ ] 健康检查可以用于负载均衡

---

## 练习 5: 服务间认证

### 题目

实现简单的服务间认证机制。

### 要求

1. 使用共享密钥（API Key）进行服务间认证
2. API 网关验证客户端请求
3. 后端服务验证网关请求

### 提示

```python
from fastapi import Header, HTTPException

API_KEY = "shared-secret-key"

@app.post("/orders")
async def create_order(order: OrderCreate, x_api_key: str = Header()):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    # 创建订单...
```

### 检查清单

- [ ] 服务间使用 API Key 认证
- [ ] 未认证的请求被拒绝
- [ ] API Key 安全存储（环境变量）
- [ ] API 网关添加认证头

---

## ✅ 完成标准

完成所有练习后，你应该能够：

- [ ] 理解微服务架构的基本概念
- [ ] 能够拆分单体应用为微服务
- [ ] 能够实现服务间 HTTP 通信
- [ ] 能够实现简单的 API 网关
- [ ] 能够使用 Docker Compose 编排服务
- [ ] 理解服务健康检查的重要性
- [ ] 理解服务间认证的基本方法

---

## 💡 学习建议

1. **循序渐进**
   - 先运行单个服务
   - 再运行多个服务
   - 最后添加 API 网关

2. **观察日志**
   - 查看每个服务的日志
   - 理解服务间调用流程
   - 调试通信问题

3. **使用 Postman**
   - 测试每个服务的 API
   - 测试 API 网关
   - 验证服务间通信

---

**祝你练习愉快！记住：微服务架构的核心是服务间的协作！** 🚀
