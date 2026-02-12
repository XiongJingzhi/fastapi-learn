# Level 5 进阶练习题

## 🎯 练习目标

通过实战练习，掌握多环境配置、Kubernetes 部署和 CI/CD 流程。

---

## 练习 1: 多环境配置管理

### 题目

实现多环境配置系统，支持开发、预发、生产三个环境。

### 要求

1. 创建基础配置类 `config/base.py`
2. 创建开发环境配置 `config/development.py`
3. 创建预发环境配置 `config/staging.py`
4. 创建生产环境配置 `config/production.py`
5. 根据环境变量自动选择配置

### 示例代码

`config/__init__.py`:

```python
import os
from config.development import DevelopmentSettings
from config.staging import StagingSettings
from config.production import ProductionSettings

def get_settings():
    """根据环境变量获取配置"""
    env = os.getenv("ENVIRONMENT", "development")

    if env == "production":
        return ProductionSettings()
    elif env == "staging":
        return StagingSettings()
    else:
        return DevelopmentSettings()

settings = get_settings()
```

`main.py`:

```python
from fastapi import FastAPI
from config import settings

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
)

@app.get("/config")
def read_config():
    return {
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "database_url": settings.DATABASE_URL[:20] + "...",  # 隐藏完整 URL
    }
```

### 测试不同环境

```bash
# 开发环境
ENVIRONMENT=development python main.py

# 预发环境
ENVIRONMENT=staging python main.py

# 生产环境
ENVIRONMENT=production python main.py
```

### 检查清单

- [ ] 不同环境加载不同配置
- [ ] 开发环境启用调试和详细日志
- [ ] 生产环境关闭调试和文档
- [ ] 敏感信息从环境变量读取

---

## 练习 2: Kubernetes Deployment

### 题目

为 FastAPI 应用创建 Kubernetes Deployment 配置。

### 要求

1. 创建 `k8s/deployment.yaml`
2. 配置副本数、资源限制
3. 配置健康检查（Liveness 和 Readiness）
4. 配置环境变量和 ConfigMap

### 示例代码

`k8s/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-app
spec:
  replicas: 3  # 你的代码在这里

  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0

  selector:
    matchLabels:
      app: fastapi-app

  template:
    metadata:
      labels:
        app: fastapi-app
    spec:
      containers:
      - name: fastapi-app
        image: fastapi-app:latest
        ports:
        - containerPort: 8000

        # 环境变量从 ConfigMap 读取
        envFrom:
        - configMapRef:
            name: fastapi-config

        # 敏感信息从 Secret 读取
        env:
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: fastapi-secret
              key: secret-key

        # 资源限制
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"

        # 健康检查（你的代码）
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10

        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
```

`main.py` (添加健康检查端点):

```python
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

### 检查清单

- [ ] 部署到 Kubernetes 集群
- [ ] Pod 正常运行
- [ ] 健康检查通过
- [ ] 可以扩缩容

### 命令

```bash
# 部署
kubectl apply -f k8s/deployment.yaml

# 查看 Pod
kubectl get pods -l app=fastapi-app

# 查看 Deployment
kubectl get deployment fastapi-app

# 扩缩容
kubectl scale deployment fastapi-app --replicas=5

# 查看日志
kubectl logs -l app=fastapi-app --all-containers=true
```

---

## 练习 3: Kubernetes Service 和 Ingress

### 题目

创建 Kubernetes Service 和 Ingress，暴露应用。

### 要求

1. 创建 `k8s/service.yaml`
2. 创建 `k8s/ingress.yaml`
3. 配置域名和路由
4. 配置 TLS（HTTPS）

### 示例代码

`k8s/service.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: fastapi-service
spec:
  type: ClusterIP
  selector:
    app: fastapi-app
  ports:
  - port: 80
    targetPort: 8000
```

`k8s/ingress.yaml`:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: fastapi-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - fastapi.example.com
    secretName: fastapi-tls
  rules:
  - host: fastapi.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: fastapi-service
            port:
              number: 80
```

### 检查清单

- [ ] Service 可以访问 Pod
- [ ] Ingress 可以访问 Service
- [ ] 域名解析正确
- [ ] HTTPS 正常工作

---

## 练习 4: ConfigMap 和 Secret

### 题目

创建 ConfigMap 和 Secret 管理配置。

### 要求

1. 创建 `k8s/configmap.yaml`
2. 创建 `k8s/secret.yaml`
3. 在 Deployment 中使用 ConfigMap 和 Secret
4. 验证配置正确加载

### 示例代码

`k8s/configmap.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fastapi-config
data:
  ENVIRONMENT: "production"
  DEBUG: "false"
  LOG_LEVEL: "info"
  DATABASE_HOST: "postgres-service"
  DATABASE_PORT: "5432"
```

`k8s/secret.yaml`:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: fastapi-secret
type: Opaque
data:
  database-url: cG9zdGdyZXNxbDovL3VzZXI6cGFzc0BkYjo1NDMyL2FwcGRi  # base64 编码
  secret-key: eW91ci1zZWNyZXQta2V5  # base64 编码
```

### 创建 Secret

```bash
# 方式 1: 从字面值创建
kubectl create secret generic fastapi-secret \
  --from-literal=database-url='postgresql://user:pass@db:5432/appdb' \
  --from-literal=secret-key='your-secret-key'

# 方式 2: 从文件创建
kubectl create secret generic fastapi-secret \
  --from-file=database-url=./db-url.txt \
  --from-file=secret-key=./secret-key.txt

# 方式 3: 从 env 文件创建
kubectl create secret generic fastapi-secret \
  --from-env-file=.env
```

### 检查清单

- [ ] ConfigMap 正确加载
- [ ] Secret 正确加载
- [ ] 敏感信息不在日志中显示
- [ ] 配置更新后 Pod 能重新加载

---

## 练习 5: 滚动更新和回滚

### 题目

实践 Kubernetes 的滚动更新和回滚功能。

### 要求

1. 部署 v1 版本
2. 更新到 v2 版本（观察滚动更新）
3. 检查更新状态
4. 如果有问题，回滚到 v1

### 示例流程

```bash
# 1. 部署 v1
kubectl set image deployment/fastapi-app fastapi-app=fastapi-app:v1

# 2. 等待就绪
kubectl rollout status deployment/fastapi-app

# 3. 查看当前版本
kubectl get pods -l app=fastapi-app -o jsonpath='{.items[0].spec.containers[0].image}'

# 4. 更新到 v2
kubectl set image deployment/fastapi-app fastapi-app=fastapi-app:v2

# 5. 观察滚动更新
watch kubectl get pods -l app=fastapi-app

# 6. 查看更新历史
kubectl rollout history deployment/fastapi-app

# 7. 如果有问题，回滚
kubectl rollout undo deployment/fastapi-app

# 8. 回滚到指定版本
kubectl rollout undo deployment/fastapi-app --to-revision=2
```

### 监控更新

```bash
# 实时查看 Pod 状态
watch kubectl get pods -l app=fastapi-app

# 查看事件
kubectl get events --sort-by=.metadata.creationTimestamp

# 查看详细信息
kubectl describe deployment fastapi-app
```

### 检查清单

- [ ] 滚动更新正常进行
- [ ] 更新过程中服务不中断
- [ ] 可以查看更新历史
- [ ] 回滚功能正常

---

## 练习 6: 水平自动扩缩容（HPA）

### 题目

配置 Horizontal Pod Autoscaler，根据负载自动扩缩容。

### 要求

1. 安装 Metrics Server
2. 创建 HPA 配置
3. 生成负载测试扩缩容
4. 观察自动扩缩容

### 示例代码

`k8s/hpa.yaml`:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: fastapi-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: fastapi-app
  minReplicas: 2  # 最小 2 个副本
  maxReplicas: 10  # 最大 10 个副本
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70  # CPU 使用率超过 70% 时扩容
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80  # 内存使用率超过 80% 时扩容
```

### 安装 Metrics Server

```bash
# 安装 Metrics Server（如果还没安装）
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# 验证安装
kubectl get apiservice v1beta1.metrics.k8s.io

# 查看资源使用
kubectl top nodes
kubectl top pods
```

### 测试扩缩容

```bash
# 1. 创建 HPA
kubectl apply -f k8s/hpa.yaml

# 2. 查看 HPA 状态
kubectl get hpa

# 3. 生成负载（使用 ab 或 wrk）
kubectl run -i --tty load-generator --image=busybox /bin/sh

# 在 load-generator 容器中：
ab -n 100000 -c 100 http://fastapi-service/

# 4. 观察 HPA 和 Pod 数量变化
watch kubectl get hpa,pods

# 5. 停止负载后，观察自动缩容
```

### 检查清单

- [ ] Metrics Server 正常运行
- [ ] HPA 正常创建
- [ ] 负载增加时自动扩容
- [ ] 负载减少时自动缩容

---

## 练习 7: CI/CD 基础

### 题目

创建一个简单的 GitHub Actions 工作流。

### 要求

1. 创建 `.github/workflows/ci.yml`
2. 配置代码检查（Lint）
3. 配置自动化测试
4. 配置 Docker 镜像构建

### 示例代码

`.github/workflows/ci.yml`:

```yaml
name: CI Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  lint:
    name: Code Quality
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install ruff
          pip install -r requirements.txt

      - name: Run Ruff
        run: ruff check .

  test:
    name: Run Tests
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install pytest pytest-asyncio httpx
          pip install -r requirements.txt

      - name: Run tests
        run: pytest tests/ -v

  build:
    name: Build Docker Image
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ghcr.io/${{ github.repository }}/fastapi-app:latest
```

### 检查清单

- [ ] 代码检查正常工作
- [ ] 测试自动运行
- [ ] Docker 镜像自动构建
- [ ] 在 GitHub Actions 页面查看运行状态

---

## 练习 8: 完整的 CI/CD 流程

### 题目

创建完整的 CI/CD 流程，包含自动部署。

### 要求

1. 代码检查
2. 自动化测试
3. 构建 Docker 镜像
4. 推送到镜像仓库
5. 自动部署到 Kubernetes

### 示例代码

`.github/workflows/ci-cd.yml`:

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main ]

jobs:
  test:
    name: Test
    runs-on: ubuntu-latest
    steps:
      # ... 测试步骤 ...

  build:
    name: Build
    runs-on: ubuntu-latest
    needs: test
    steps:
      # ... 构建步骤 ...

  deploy:
    name: Deploy to Kubernetes
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up kubectl
        uses: azure/setup-kubectl@v4

      - name: Configure Kubernetes
        run: |
          echo "${{ secrets.KUBECONFIG }}" | base64 -d > kubeconfig.yaml
          export KUBECONFIG=kubeconfig.yaml

      - name: Update Deployment
        run: |
          export KUBECONFIG=kubeconfig.yaml
          kubectl set image deployment/fastapi-app \
            fastapi-app=ghcr.io/${{ github.repository }}/fastapi-app:latest

      - name: Verify deployment
        run: |
          export KUBECONFIG=kubeconfig.yaml
          kubectl rollout status deployment/fastapi-app
```

### 检查清单

- [ ] CI 流程正常工作
- [ ] CD 自动部署到 Kubernetes
- [ ] 可以通过 GitHub Actions 触发部署
- [ ] 部署失败时有告警

---

## ✅ 完成标准

完成所有练习后，你应该能够：

- [ ] 管理多环境配置
- [ ] 部署应用到 Kubernetes
- [ ] 配置 Service 和 Ingress
- [ ] 使用 ConfigMap 和 Secret
- [ ] 执行滚动更新和回滚
- [ ] 配置水平自动扩缩容
- [ ] 创建 CI/CD 流程
- [ ] 自动化部署

---

## 💡 学习建议

1. **循序渐进**
   - 先掌握 Kubernetes 基础
   - 再学习 CI/CD
   - 最后实践完整流程

2. **本地测试**
   - 使用 Minikube 或 Kind
   - 在本地充分测试
   - 再部署到真实集群

3. **监控和日志**
   - 查看容器日志
   - 监控资源使用
   - 分析问题原因

4. **文档记录**
   - 记录部署流程
   - 记录常见问题
   - 总结最佳实践

---

**祝你练习愉快！记住：Kubernetes 和 CI/CD 是现代部署的核心技能！** 🚀
