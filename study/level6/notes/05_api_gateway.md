# 05. API 网关 - API Gateway

## 📍 在架构中的位置

**从"客户端直接调用多个服务"到"统一入口"**

```
┌─────────────────────────────────────────────────────────────┐
│          没有 API 网关                                       │
└─────────────────────────────────────────────────────────────┘

客户端 → 用户服务 (http://api.example.com:8001)
       → 订单服务 (http://api.example.com:8002)
       → 产品服务 (http://api.example.com:8003)
       → 支付服务 (http://api.example.com:8004)

问题：
    - 客户端需要知道每个服务的地址
    - 客户端需要处理认证、限流等逻辑
    - 跨域问题（CORS）
    - 无法统一监控和日志

═══════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────┐
│          有 API 网关                                         │
└─────────────────────────────────────────────────────────────┘

客户端 → API 网关 (http://api.example.com)
         → 后端服务（客户端不需要知道具体服务地址）

好处：
    - 统一入口
    - 认证、授权在网关处理
    - 限流、熔断在网关处理
    - 聚合多个服务的响应
    - 协议转换（HTTP → gRPC）
    - 统一监控和日志
```

**🎯 你的学习目标**：理解 API 网关的作用、实现方式和最佳实践。

---

## 🎯 什么是 API 网关？

### 定义

**API 网关**是微服务架构中的服务器，是系统的统一入口，处理所有客户端请求并将其路由到适当的后端服务。

### 生活类比：酒店前台

```
没有前台：
    客户 → 直接找客房服务（打扫房间）
         → 直接找餐厅服务（点餐）
         → 直接找健身房服务（预约）
    → 客户需要知道每个服务在哪里
    → 客户需要分别付费

有前台（API 网关）：
    客户 → 前台
         → 前台联系客房服务
         → 前台联系餐厅服务
         → 前台联系健身房服务
    → 客户只需要找前台
    → 前台统一处理认证（登记入住）
    → 前台统一处理付费（结账）
```

---

## 🏗️ API 网关的核心功能

### 功能 1：路由转发

```yaml
# 路由规则
/api/users/*    → user-service:8001
/api/orders/*   → order-service:8002
/api/products/* → product-service:8003
/api/payments/* → payment-service:8004
```

```python
# FastAPI 实现简单路由
from fastapi import FastAPI, Request
import httpx

app = FastAPI()
services = {
    "users": "http://user-service:8001",
    "orders": "http://order-service:8002",
    "products": "http://product-service:8003",
}

@app.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_request(service: str, path: str, request: Request):
    if service not in services:
        raise HTTPException(status_code=404, detail="Service not found")

    url = f"{services[service]}/{path}"
    body = await request.body()

    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=request.method,
            url=url,
            headers=request.headers,
            content=body
        )
    return response.json()
```

### 功能 2：认证与授权

```python
from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # 白名单路径（不需要认证）
    if request.url.path in ["/health", "/docs"]:
        return await call_next(request)

    # 验证 Token
    try:
        auth_header = request.headers["Authorization"]
        token = auth_header.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        request.state.user = payload
    except (KeyError, IndexError, jwt.PyJWTError):
        raise HTTPException(status_code=401, detail="Invalid token")

    # 继续处理请求
    response = await call_next(request)
    return response

# 将用户信息传递给后端服务
@app.api_route("/{service}/{path:path}")
async def proxy_request(service: str, path: str, request: Request):
    headers = dict(request.headers)
    headers["X-User-ID"] = str(request.state.user["user_id"])
    # 调用后端服务...
```

### 功能 3：限流

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# 全局限流：每分钟 100 次请求
@app.api_route("/{service}/{path:path}")
@limiter.limit("100/minute")
async def proxy_request(request: Request):
    # 处理请求...
    pass

# 不同接口不同限流策略
@app.api_route("/api/public/{path:path}")
@limiter.limit("1000/minute")  # 公开接口：每分钟 1000 次
async def proxy_public_request(request: Request):
    pass

@app.api_route("/api/expensive/{path:path}")
@limiter.limit("10/minute")  # 昂贵操作：每分钟 10 次
async def proxy_expensive_request(request: Request):
    pass
```

### 功能 4：熔断器

```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
async def call_service(service_url: str, path: str, request: Request):
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=request.method,
            url=f"{service_url}/{path}",
            headers=request.headers,
            content=await request.body()
        )
        response.raise_for_status()
        return response.json()

@app.api_route("/{service}/{path:path}")
async def proxy_request(service: str, path: str, request: Request):
    if service not in services:
        raise HTTPException(status_code=404, detail="Service not found")

    try:
        return await call_service(services[service], path, request)
    except CircuitBreakerError:
        # 熔断器打开，返回降级响应
        return {"error": "Service temporarily unavailable"}
    except httpx.HTTPError as e:
        raise HTTPException(status_code=503, detail=str(e))
```

### 功能 5：响应聚合

```python
import asyncio

@app.get("/api/orders/{order_id}")
async def get_order_detail(order_id: int):
    # 并行调用多个服务
    order, user, products = await asyncio.gather(
        call_service("order-service", f"orders/{order_id}", request),
        call_service("user-service", "users/{user_id}", request),
        call_service("product-service", "products", request)
    )

    # 聚合响应
    return {
        "order": order,
        "user": user,
        "products": products
    }
```

### 功能 6：协议转换

```python
# 客户端使用 HTTP，后端服务使用 gRPC

@app.get("/api/users/{user_id}")
async def get_user(user_id: int):
    # HTTP 请求
    # 转换为 gRPC 调用
    async with grpc.aio.insecure_channel('user-service:50051') as channel:
        stub = user_pb2_grpc.UserServiceStub(channel)
        request = user_pb2.GetUserRequest(user_id=user_id)
        response = await stub.GetUser(request)
        # 将 gRPC 响应转换为 JSON
        return {
            "id": response.id,
            "name": response.name,
            "email": response.email
        }
```

### 功能 7：负载均衡

```python
from random import choice

services = {
    "user-service": [
        "http://user-service-1:8001",
        "http://user-service-2:8001",
        "http://user-service-3:8001",
    ]
}

async def get_service_instance(service_name: str) -> str:
    # 随机选择一个实例（简单负载均衡）
    instances = services.get(service_name, [])
    if not instances:
        raise HTTPException(status_code=503, detail="Service unavailable")
    return choice(instances)

@app.api_route("/{service}/{path:path}")
async def proxy_request(service: str, path: str, request: Request):
    # 获取服务实例
    service_url = await get_service_instance(service)
    # 调用服务...
```

---

## 🔧 API 网关实现

### 方案 1：使用 FastAPI 自建

```python
# gateway/main.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
from circuitbreaker import circuit
from slowapi import Limiter
from slowapi.util import get_remote_address

app = FastAPI(title="API Gateway")

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 服务注册表
services = {
    "users": "http://user-service:8001",
    "orders": "http://order-service:8002",
    "products": "http://product-service:8003",
}

# 限流器
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# 健康检查
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# 代理所有请求
@app.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit("100/minute")
@circuit(failure_threshold=5, recovery_timeout=60)
async def proxy_request(service: str, path: str, request: Request):
    if service not in services:
        raise HTTPException(status_code=404, detail="Service not found")

    url = f"{services[service]}/{path}"

    # 转发请求
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=request.method,
            url=url,
            headers=request.headers,
            content=await request.body(),
            timeout=30.0
        )
        return response.json()

# 聚合请求示例
@app.get("/api/orders/{order_id}/detail")
async def get_order_detail(order_id: int, request: Request):
    # 并行调用多个服务
    order, user, products = await asyncio.gather(
        call_service("orders", f"orders/{order_id}", request),
        call_service("users", "users", request),
        call_service("products", "products", request)
    )

    return {
        "order": order,
        "user": user,
        "products": products
    }
```

### 方案 2：使用 Kong

```yaml
# docker-compose.yml
version: '3.8'

services:
  kong:
    image: kong:latest
    ports:
      - "8000:8000"  # Proxy
      - "8443:8443"  # Proxy SSL
      - "8001:8001"  # Admin
    environment:
      KONG_DATABASE: "off"
      KONG_PROXY_ACCESS_LOG: /dev/stdout
      KONG_ADMIN_ACCESS_LOG: /dev/stdout
      KONG_PROXY_ERROR_LOG: /dev/stderr
      KONG_ADMIN_ERROR_LOG: /dev/stderr

  # 配置 Kong
  kong-config:
    image: curlimages/curl
    depends_on:
      - kong
    command: |
      sh -c "
      sleep 5 &&
      curl -i -X POST http://kong:8001/services \
        --data name=user-service \
        --data url=http://user-service:8001 &&
      curl -i -X POST http://kong:8001/services/user-service/routes \
        --data paths[]=/api/users &&
      echo 'Kong configured'
      "
```

### 方案 3：使用 Traefik

```yaml
# docker-compose.yml
version: '3.8'

services:
  traefik:
    image: traefik:v2.10
    ports:
      - "80:80"
      - "8080:8080"  # Dashboard
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./traefik.yml:/etc/traefik/traefik.yml
    command:
      - "--api.insecure=true"
      - "--providers.docker=true"

  user-service:
    image: user-service:latest
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.user-service.rule=PathPrefix(`/api/users`)"
      - "traefik.http.services.user-service.loadbalancer.server.port=8001"

  order-service:
    image: order-service:latest
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.order-service.rule=PathPrefix(`/api/orders`)"
      - "traefik.http.services.order-service.loadbalancer.server.port=8002"
```

### 方案 4：使用 Kubernetes Ingress

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-gateway
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  rules:
    - host: api.example.com
      http:
        paths:
          - path: /api/users
            pathType: Prefix
            backend:
              service:
                name: user-service
                port:
                  number: 8001
          - path: /api/orders
            pathType: Prefix
            backend:
              service:
                name: order-service
                port:
                  number: 8002
```

---

## 📋 API 网关选型

### 对比表格

| 特性 | FastAPI 自建 | Kong | Traefik | AWS API Gateway |
|------|--------------|------|---------|-----------------|
| **灵活性** | 高（完全可控） | 中 | 中 | 低 |
| **学习曲线** | 低 | 中 | 中 | 中 |
| **性能** | 中 | 高 | 高 | 高 |
| **功能丰富度** | 低 | 高 | 高 | 高 |
| **运维成本** | 高 | 中 | 低 | 低（托管） |
| **成本** | 无 | 开源版免费 | 开源免费 | 按调用计费 |
| **适合场景** | 简单场景 | 复杂场景 | Kubernetes | 云原生 |

---

## ⚠️ API 网关的陷阱

### 陷阱 1：单点故障

```
问题：
    API 网关挂了 → 整个系统不可用

解决：
    - 部署多个网关实例
    - 使用负载均衡
    - 健康检查和自动故障转移
```

### 陷阱 2：性能瓶颈

```
问题：
    所有流量都经过网关 → 网关成为瓶颈

解决：
    - 网关只处理轻量级逻辑
    - 避免在网关中做复杂计算
    - 使用高性能网关（Kong、Traefik）
```

### 陷阱 3：网关逻辑过重

```
问题：
    在网关中实现太多业务逻辑
    → 网关变得复杂、难以维护

解决：
    - 网关只处理横切关注点（认证、限流、路由）
    - 业务逻辑放在后端服务
```

---

## 🎯 小实验：API 网关

### 实验：实现简单的 API 网关

```python
# gateway/main.py
from fastapi import FastAPI, Request
import httpx

app = FastAPI()

services = {
    "users": "http://user-service:8001",
    "orders": "http://order-service:8002",
}

@app.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy(service: str, path: str, request: Request):
    if service not in services:
        return {"error": "Service not found"}, 404

    url = f"{services[service]}/{path}"
    body = await request.body()

    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=request.method,
            url=url,
            headers=request.headers,
            content=body
        )
    return response.json()

# 运行：uvicorn gateway:app --port 8000
```

---

## 📚 检查理解

回答这些问题来测试你的理解：

1. **什么是 API 网关？**
   - 提示：微服务的统一入口

2. **API 网关的核心功能有哪些？**
   - 提示：路由、认证、限流、熔断、聚合

3. **API 网关的实现方案有哪些？**
   - 提示：自建、Kong、Traefik、云服务

4. **如何避免 API 网关成为单点故障？**
   - 提示：多实例、负载均衡

5. **API 网关 vs 服务网格（Service Mesh）？**
   - 提示：网关处理南北流量，服务网格处理东西流量

---

## 🚀 下一步

现在你已经了解了 API 网关，接下来：

1. **学习服务发现**：`notes/06_service_discovery.md`
2. **学习容错模式**：`notes/09_fault_tolerance.md`

**记住：API 网关是微服务的统一入口，但不要在其中实现业务逻辑！**
