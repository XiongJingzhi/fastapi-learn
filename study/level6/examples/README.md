# Level 6 Examples - 微服务架构

## 📁 目录结构

```
examples/
├── user-service/              # 用户服务
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── order-service/             # 订单服务
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── product-service/           # 产品服务
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── api-gateway/               # API 网关
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml         # 服务编排
├── kubernetes/                # Kubernetes 配置
│   ├── user-service.yaml
│   ├── order-service.yaml
│   ├── product-service.yaml
│   └── api-gateway.yaml
└── README.md                  # 本文件
```

---

## 🚀 快速开始

### 使用 Docker Compose

```bash
# 启动所有服务
cd examples
docker-compose up -d

# 查看日志
docker-compose logs -f

# 测试服务
curl http://localhost:8000/api/users/1       # 通过网关调用用户服务
curl http://localhost:8000/api/orders/1      # 通过网关调用订单服务
curl http://localhost:8000/api/products      # 通过网关调用产品服务

# 停止服务
docker-compose down
```

### 使用 Kubernetes

```bash
# 部署到 Kubernetes
kubectl apply -f kubernetes/

# 查看状态
kubectl get pods,svc

# 测试服务
curl http://api-gateway/api/users/1
```

---

## 📝 服务说明

### 用户服务 (User Service)

端口：8001

功能：
- 创建用户
- 获取用户信息
- 更新用户信息

API：
- `POST /users` - 创建用户
- `GET /users/{user_id}` - 获取用户信息
- `PUT /users/{user_id}` - 更新用户信息

### 订单服务 (Order Service)

端口：8002

功能：
- 创建订单
- 获取订单信息
- 调用用户服务和产品服务

API：
- `POST /orders` - 创建订单
- `GET /orders/{order_id}` - 获取订单信息

### 产品服务 (Product Service)

端口：8003

功能：
- 获取产品列表
- 获取产品详情

API：
- `GET /products` - 获取产品列表
- `GET /products/{product_id}` - 获取产品详情

### API 网关 (API Gateway)

端口：8000

功能：
- 路由请求到后端服务
- 认证和授权
- 限流和熔断

API：
- `/api/users/*` → user-service
- `/api/orders/*` → order-service
- `/api/products/*` → product-service

---

## 🎯 学习路径

1. **基础阶段**：启动单个服务
   - 运行用户服务
   - 测试 API

2. **进阶阶段**：启动多个服务
   - 使用 Docker Compose 启动所有服务
   - 测试服务间通信

3. **高级阶段**：添加容错
   - 实现熔断器
   - 实现降级
   - 实现限流

4. **专家阶段**：部署到 Kubernetes
   - 编写 Kubernetes 配置
   - 部署到集群
   - 配置服务发现

---

**记住：微服务的核心是服务间的协作，理解通信模式是关键！** 🚀
