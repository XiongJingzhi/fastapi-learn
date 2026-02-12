# Level 5 综合项目

## 🎯 项目目标

通过完整的实战项目，掌握从开发到生产的完整 CI/CD 流程。

---

## 项目 1: 完整的电商 API 部署

### 背景

构建一个电商后端 API，包含商品、订单、用户管理，并实现完整的 CI/CD 流程。

### 功能要求

#### 核心功能

1. **用户管理**
   - 用户注册和登录（JWT）
   - 个人信息管理
   - 密码重置

2. **商品管理**
   - 商品列表（分页、搜索、筛选）
   - 商品详情
   - 库存管理

3. **订单管理**
   - 创建订单
   - 订单支付（模拟）
   - 订单查询
   - 订单状态更新

4. **缓存和性能优化**
   - Redis 缓存热门商品
   - 数据库连接池
   - 分页查询

5. **监控和日志**
   - 健康检查端点
   - Prometheus metrics
   - 结构化日志

### 技术栈

- **后端框架**: FastAPI
- **数据库**: PostgreSQL
- **缓存**: Redis
- **容器**: Docker
- **编排**: Docker Compose (本地), Kubernetes (生产)
- **CI/CD**: GitHub Actions
- **监控**: Prometheus + Grafana (可选)

### 项目结构

```
ecommerce-api/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── models.py
│   ├── schemas.py
│   ├── database.py
│   ├── auth.py
│   ├── api/
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── users.py
│   │   │   ├── products.py
│   │   │   └── orders.py
│   └── utils/
│       ├── cache.py
│       └── logger.py
├── tests/
│   ├── test_users.py
│   ├── test_products.py
│   └── test_orders.py
├── alembic/
├── k8s/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── configmap.yaml
│   └── secret.yaml
├── .github/
│   └── workflows/
│       └── ci-cd.yml
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── requirements.txt
└── README.md
```

### 任务清单

#### Phase 1: 开发环境搭建

- [ ] 创建 FastAPI 项目
- [ ] 配置 PostgreSQL 数据库
- [ ] 配置 Redis 缓存
- [ ] 编写数据模型（用户、商品、订单）
- [ ] 实现基础 CRUD 操作
- [ ] 添加 JWT 认证

#### Phase 2: Docker 容器化

- [ ] 编写 Dockerfile（多阶段构建）
- [ ] 编写 docker-compose.yml
- [ ] 配置数据持久化
- [ ] 本地测试容器化应用
- [ ] 优化镜像大小

#### Phase 3: Kubernetes 部署

- [ ] 创建 Deployment 配置
- [ ] 创建 Service 配置
- [ ] 创建 Ingress 配置
- [ ] 创建 ConfigMap 和 Secret
- [ ] 部署到 Minikube/Kind（本地测试）
- [ ] 配置健康检查和探针

#### Phase 4: CI/CD 流程

- [ ] 配置代码检查（Ruff, Mypy）
- [ ] 编写单元测试
- [ ] 配置 GitHub Actions
- [ ] 自动构建 Docker 镜像
- [ ] 自动部署到 Kubernetes
- [ ] 配置自动回滚

#### Phase 5: 监控和优化

- [ ] 添加 Prometheus metrics
- [ ] 配置日志聚合
- [ ] 性能测试（使用 locust 或 ab）
- [ ] 优化数据库查询
- [ ] 优化缓存策略

### 验收标准

1. **功能完整性**
   - [ ] 所有核心功能正常工作
   - [ ] API 文档完整（OpenAPI）
   - [ ] 错误处理完善

2. **代码质量**
   - [ ] 代码检查通过（无警告）
   - [ ] 类型检查通过
   - [ ] 测试覆盖率 > 70%

3. **容器化**
   - [ ] Docker 镜像大小 < 200MB
   - [ ] 非 root 用户运行
   - [ ] 健康检查正常

4. **部署**
   - [ ] 可以一键部署到 Kubernetes
   - [ ] 滚动更新正常
   - [ ] 可以快速回滚

5. **CI/CD**
   - [ ] Push 代码自动触发 CI
   - [ ] 测试失败阻止部署
   - [ ] 部署到生产环境自动触发

6. **监控**
   - [ ] 健康检查端点正常
   - [ ] 可以查询 metrics
   - [ ] 日志结构化

### 提示

```python
# main.py 示例
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from config import settings
from database import engine, Base
from api.v1 import users, products, orders

app = FastAPI(
    title="Ecommerce API",
    version="1.0.0",
    debug=settings.DEBUG,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(products.router, prefix="/api/v1/products", tags=["products"])
app.include_router(orders.router, prefix="/api/v1/orders", tags=["orders"])

# 启动事件
@app.on_event("startup")
async def startup():
    # 创建数据库表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 配置 Prometheus metrics
    Instrumentator().instrument(app).expose(app)

# 健康检查
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/ready")
async def readiness_check():
    # 检查数据库连接
    # 检查 Redis 连接
    return {"status": "ready"}
```

---

## 项目 2: 蓝绿部署实践

### 背景

实现一个蓝绿部署的完整流程，包括自动切换和回滚。

### 功能要求

1. **版本管理**
   - v1.0 版本（当前生产）
   - v2.0 版本（新版本）

2. **部署策略**
   - 蓝环境：v1.0
   - 绿环境：v2.0
   - 流量切换脚本
   - 自动回滚脚本

3. **健康检查**
   - 端点实现
   - 自动化检查脚本

### 任务清单

- [ ] 实现两个版本的 FastAPI 应用
- [ ] 编写蓝绿部署脚本
- [ ] 编写健康检查脚本
- [ ] 实现自动回滚机制
- [ ] 测试完整流程

### 示例脚本

`deploy-blue-green.sh`:

```bash
#!/bin/bash

set -e

BLUE_VERSION="v1.0"
GREEN_VERSION="v2.0"
NAMESPACE="production"

echo "🚀 开始蓝绿部署..."

# 1. 部署绿环境
echo "📦 部署绿环境 ($GREEN_VERSION)..."
kubectl apply -f k8s/deployment-green.yaml -n $NAMESPACE

# 2. 等待绿环境就绪
echo "⏳ 等待绿环境就绪..."
kubectl rollout status deployment/fastapi-app-green -n $NAMESPACE

# 3. 健康检查
echo "🏥 运行健康检查..."
GREEN_POD=$(kubectl get pods -n $NAMESPACE -l version=$GREEN_VERSION -o jsonpath='{.items[0].metadata.name}')
HEALTH_CHECK=$(kubectl exec -n $NAMESPACE $GREEN_POD -- curl -s http://localhost:8000/health)

if [[ $HEALTH_CHECK != *"healthy"* ]]; then
    echo "❌ 健康检查失败，停止部署"
    exit 1
fi

echo "✅ 健康检查通过"

# 4. 切换流量
echo "🔄 切换流量到绿环境..."
kubectl patch service fastapi-service -n $NAMESPACE -p '{"spec":{"selector":{"version":"'$GREEN_VERSION'"}}}'

# 5. 验证
echo "🔍 验证部署..."
sleep 10
EXTERNAL_URL="https://api.example.com"
VERIFY=$(curl -s $EXTERNAL_URL/health)

if [[ $VERIFY != *"healthy"* ]]; then
    echo "❌ 验证失败，回滚到蓝环境"
    kubectl patch service fastapi-service -n $NAMESPACE -p '{"spec":{"selector":{"version":"'$BLUE_VERSION'"}}}'
    exit 1
fi

echo "✅ 部署成功！"

# 6. 清理（可选）
# kubectl delete deployment fastapi-app-blue -n $NAMESPACE
```

---

## 项目 3: 金丝雀发布实践

### 背景

实现金丝雀发布流程，逐步将流量切换到新版本。

### 功能要求

1. **版本管理**
   - 稳定版（v1.0）
   - 金丝雀版（v2.0）

2. **流量控制**
   - 5% → 25% → 50% → 100%
   - 基于错误率自动回滚
   - 监控指标收集

### 任务清单

- [ ] 部署金丝雀版本
- [ ] 配置流量分流（Istio 或 NGINX Ingress）
- [ ] 编写流量切换脚本
- [ ] 编写监控脚本
- [ ] 实现自动回滚
- [ ] 测试完整流程

### 示例脚本

`canary-deployment.sh`:

```bash
#!/bin/bash

set -e

CANARY_VERSION="v2.0"
NAMESPACE="production"

# 流量权重（逐步增加）
WEIGHTS=(5 25 50 100)
CHECK_INTERVAL=300  # 5 分钟

echo "🐤 开始金丝雀发布..."

# 1. 部署金丝雀版本
echo "📦 部署金丝雀版本 ($CANARY_VERSION)..."
kubectl apply -f k8s/deployment-canary.yaml -n $NAMESPACE

# 2. 等待金丝雀就绪
echo "⏳ 等待金丝雀就绪..."
kubectl rollout status deployment/fastapi-app-canary -n $NAMESPACE

# 3. 逐步增加流量
for weight in "${WEIGHTS[@]}"; do
    echo "📊 设置金丝雀流量权重: $weight%"

    # 更新 Ingress 注解
    kubectl annotate ingress fastapi-ingress \
        nginx.ingress.kubernetes.io/canary-weight="$weight" \
        -n $NAMESPACE --overwrite

    # 等待并检查
    echo "⏳ 等待 $CHECK_INTERVAL 秒..."
    sleep $CHECK_INTERVAL

    # 检查错误率
    ERROR_RATE=$(curl -s 'http://prometheus:9090/api/v1/query?query=rate(http_requests_total{status=~"5.."}[5m])' | jq '.data.result[0].value[1]')

    if (( $(echo "$ERROR_RATE > 0.05" | bc -l) )); then
        echo "❌ 错误率过高 ($ERROR_RATE)，回滚"
        kubectl annotate ingress fastapi-ingress \
            nginx.ingress.kubernetes.io/canary-weight="0" \
            -n $NAMESPACE --overwrite
        exit 1
    fi

    echo "✅ $weight% 流量正常"
done

echo "✅ 金丝雀发布完成！"
```

---

## 项目 4: 监控和告警系统

### 背景

构建完整的监控和告警系统。

### 功能要求

1. **应用监控**
   - Prometheus metrics
   - 自定义指标

2. **告警规则**
   - 高错误率
   - 高延迟
   - 高 CPU/内存

3. **可视化**
   - Grafana Dashboard
   - 实时监控

### 任务清单

- [ ] 集成 Prometheus
- [ ] 定义业务指标
- [ ] 配置告警规则
- [ ] 创建 Grafana Dashboard
- [ ] 配置告警通知（钉钉/Slack）
- [ ] 测试告警

### 示例代码

`metrics.py`:

```python
from prometheus_client import Counter, Histogram, Gauge
from functools import wraps

# 定义指标
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

active_users = Gauge(
    'active_users',
    'Number of active users'
)

# 中间件
def prometheus_middleware(app):
    @wraps(app)
    async def wrapper(request, call_next):
        # 记录请求开始
        import time
        start_time = time.time()

        # 处理请求
        response = await call_next(request)

        # 记录指标
        duration = time.time() - start_time
        http_requests_total.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        http_request_duration.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)

        return response
    return wrapper
```

---

## 项目 5: 性能优化和压测

### 背景

对应用进行性能优化和压力测试。

### 功能要求

1. **性能优化**
   - 数据库查询优化
   - 缓存优化
   - 异步优化

2. **压力测试**
   - 使用 Locust 或 k6
   - 并发测试
   - 性能报告

### 任务清单

- [ ] 分析当前性能瓶颈
- [ ] 优化数据库查询
- [ ] 优化缓存策略
- [ ] 编写压力测试脚本
- [ ] 执行压力测试
- [ ] 生成性能报告

### 示例压测脚本

`locustfile.py`:

```python
from locust import HttpUser, task, between

class FastAPIUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def get_products(self):
        self.client.get("/api/v1/products")

    @task(2)
    def get_product_detail(self):
        self.client.get("/api/v1/products/1")

    @task(1)
    def create_order(self):
        self.client.post("/api/v1/orders", json={
            "product_id": 1,
            "quantity": 2
        })
```

运行压测：

```bash
locust -f locustfile.py --host=http://localhost:8000 --users=100 --spawn-rate=10
```

---

## ✅ 项目验收标准

完成项目后，确认你可以：

- [ ] 从零构建完整的 FastAPI 应用
- [ ] 容器化应用（Docker）
- [ ] 编排多容器应用（Docker Compose）
- [ ] 部署到 Kubernetes
- [ ] 实现 CI/CD 流程
- [ ] 执行蓝绿部署
- [ ] 执行金丝雀发布
- [ ] 配置监控和告警
- [ ] 进行性能优化

---

## 💡 学习建议

1. **选择合适的项目**
   - 从简单的项目 1 开始
   - 逐步挑战更复杂的项目
   - 每个项目都完整实现

2. **循序渐进**
   - Phase 1 → Phase 2 → Phase 3
   - 每个 Phase 都测试通过
   - 不要跳过步骤

3. **文档记录**
   - 记录部署流程
   - 记录遇到的问题
   - 编写 README

4. **代码质量**
   - 遵循最佳实践
   - 编写测试
   - 代码审查

---

**祝你项目愉快！记住：完整的 CI/CD 流程是 DevOps 的核心能力！** 🚀
