# Level 6 Examples Summary

## 📁 示例代码总结

本目录包含了微服务架构的完整示例代码，涵盖了从基础服务搭建到高级特性的实现。

---

## 🚀 快速开始

### 使用 Docker Compose

```bash
cd examples
docker-compose up -d

# 测试服务
curl http://localhost:8000/api/users/1       # 通过网关调用用户服务
curl http://localhost:8000/api/products      # 通过网关调用产品服务
curl http://localhost:8000/api/orders        # 通过网关调用订单服务
```

### 使用 Kubernetes

```bash
kubectl apply -f kubernetes/

# 查看状态
kubectl get pods,svc
```

---

## 📦 服务列表

### 1. 用户服务 (User Service)

**目录**: `user-service/`

**端口**: 8001

**功能**:
- 用户管理
- 用户查询

**API**:
- `GET /health` - 健康检查
- `GET /users` - 获取所有用户
- `GET /users/{user_id}` - 获取单个用户
- `POST /users` - 创建用户
- `PUT /users/{user_id}` - 更新用户

**技术要点**:
- RESTful API 设计
- Pydantic 数据校验
- 模拟数据库存储

---

### 2. 产品服务 (Product Service)

**目录**: `product-service/`

**端口**: 8003

**功能**:
- 产品管理
- 产品查询

**API**:
- `GET /health` - 健康检查
- `GET /products` - 获取所有产品
- `GET /products/{product_id}` - 获取单个产品

**技术要点**:
- RESTful API 设计
- 产品数据模型

---

### 3. 订单服务 (Order Service)

**目录**: `order-service/`

**端口**: 8002

**功能**:
- 订单管理
- 服务间通信

**API**:
- `GET /health` - 健康检查
- `GET /orders` - 获取所有订单
- `GET /orders/{order_id}` - 获取单个订单
- `POST /orders` - 创建订单（调用用户服务和产品服务）

**技术要点**:
- 服务间 HTTP 通信（使用 httpx）
- 异步请求
- 错误处理

---

### 4. API 网关 (API Gateway)

**目录**: `api-gateway/`

**端口**: 8000

**功能**:
- 统一入口
- 路由转发

**API**:
- `GET /health` - 健康检查
- `/api/users/*` - 路由到用户服务
- `/api/orders/*` - 路由到订单服务
- `/api/products/*` - 路由到产品服务

**技术要点**:
- 动态路由
- 请求代理
- CORS 支持

---

## 🏗️ 架构设计

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        客户端                                │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      API 网关 (:8000)                         │
│                   (统一入口、路由转发)                         │
└─────────────────────────────────────────────────────────────┘
          ↓              ↓              ↓
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │用户服务   │   │订单服务   │   │产品服务   │
    │(:8001)   │   │(:8002)   │   │(:8003)   │
    └──────────┘   └──────────┘   └──────────┘
```

### 服务间通信

```
订单服务 → 用户服务 (HTTP)
订单服务 → 产品服务 (HTTP)
客户端 → API 网关 → 后端服务 (HTTP)
```

---

## 📚 学习路径

### 阶段 1：理解基础服务

**目标**: 理解单个服务的结构

**步骤**:
1. 阅读 `user-service/main.py`
2. 运行用户服务
3. 测试用户服务 API

**命令**:
```bash
cd user-service
python main.py
curl http://localhost:8001/users
```

---

### 阶段 2：理解服务间通信

**目标**: 理解服务间如何调用

**步骤**:
1. 阅读 `order-service/main.py`
2. 启动用户服务和产品服务
3. 启动订单服务
4. 创建订单（观察日志）

**命令**:
```bash
# 终端 1
cd user-service && python main.py

# 终端 2
cd product-service && python main.py

# 终端 3
cd order-service && python main.py

# 终端 4
curl -X POST http://localhost:8002/orders \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "product_id": 1, "quantity": 2}'
```

---

### 阶段 3：理解 API 网关

**目标**: 理解网关如何路由请求

**步骤**:
1. 启动所有服务
2. 启动 API 网关
3. 通过网关访问所有服务

**命令**:
```bash
# 使用 Docker Compose
docker-compose up -d

# 通过网关访问
curl http://localhost:8000/api/users/1
curl http://localhost:8000/api/products
```

---

## 🎯 核心概念

### 1. 服务独立部署

每个服务是一个独立的 FastAPI 应用，可以单独运行和部署。

```python
# user-service/main.py
from fastapi import FastAPI

app = FastAPI(title="User Service")

@app.get("/users")
def get_users():
    return {"users": [...]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
```

### 2. 服务间通信

使用 httpx 进行异步 HTTP 调用。

```python
# order-service/main.py
import httpx

async def create_order(order: OrderCreate):
    # 调用用户服务
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{USER_SERVICE_URL}/users/{order.user_id}")
        user = response.json()
    return user
```

### 3. API 网关路由

网关根据路径前缀路由请求到不同的服务。

```python
# api-gateway/main.py
services = {
    "users": "http://user-service:8000",
    "orders": "http://order-service:8000",
}

@app.api_route("/api/{service}/{path:path}")
async def proxy_request(service: str, path: str, request: Request):
    service_url = services[service]
    url = f"{service_url}/{path}"
    # 转发请求...
```

---

## 🛠️ 扩展练习

### 练习 1：添加熔断器

为订单服务调用用户服务和产品服务添加熔断器。

```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
async def call_user_service(user_id: int):
    # 调用用户服务...
    pass
```

### 练习 2：添加限流

为 API 网关添加限流功能。

```python
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@app.api_route("/api/{service}/{path:path}")
@limiter.limit("100/minute")
async def proxy_request(...):
    # 代理请求...
```

### 练习 3：添加缓存

为用户服务添加 Redis 缓存。

```python
import redis

r = redis.Redis(host='redis', port=6379)

@app.get("/users/{user_id}")
def get_user(user_id: int):
    # 尝试从缓存获取
    cached = r.get(f"user:{user_id}")
    if cached:
        return json.loads(cached)

    # 从数据库获取
    user = get_user_from_db(user_id)

    # 写入缓存
    r.setex(f"user:{user_id}", 60, json.dumps(user))

    return user
```

---

## 📊 性能指标

### 目标性能

- API 响应时间: < 100ms (P95)
- 服务间调用: < 50ms (P95)
- 吞吐量: > 1000 QPS

### 优化建议

1. **使用连接池**: 复用 HTTP 连接
2. **并行调用**: 使用 `asyncio.gather` 并行调用多个服务
3. **添加缓存**: 缓存热点数据
4. **压缩响应**: 启用 gzip 压缩

---

## 🐛 常见问题

### 问题 1：服务无法启动

**原因**: 端口被占用

**解决**:
```bash
# 查看端口占用
lsof -i :8001

# 杀掉占用进程
kill -9 <PID>
```

### 问题 2：服务间通信失败

**原因**: 服务地址配置错误

**解决**:
```bash
# 检查服务地址
echo $USER_SERVICE_URL

# 使用 docker-compose 时使用服务名
USER_SERVICE_URL=http://user-service:8000
```

### 问题 3：网关路由失败

**原因**: 后端服务未启动

**解决**:
```bash
# 检查服务健康状态
curl http://user-service:8001/health
curl http://order-service:8002/health
curl http://product-service:8003/health
```

---

## 📚 进阶资源

### 扩展阅读

1. **服务发现**
   - [Consul](https://www.consul.io/)
   - [Etcd](https://etcd.io/)

2. **API 网关**
   - [Kong](https://konghq.com/)
   - [Traefik](https://traefik.io/)

3. **服务网格**
   - [Istio](https://istio.io/)
   - [Linkerd](https://linkerd.io/)

### 参考项目

- [Microservices Example](https://github.com/kubernetes/kubernetes/tree/master/examples)
- [Spring PetClinic Microservices](https://github.com/spring-petclinic/spring-petclinic-microservices)

---

**记住：微服务架构的核心是服务间的协作，理解通信模式是关键！** 🚀
