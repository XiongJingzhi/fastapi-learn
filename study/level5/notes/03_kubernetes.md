# 03. Kubernetes 编排 - Kubernetes Orchestration

## 📍 在架构中的位置

**从"单机部署"到"集群编排"**

```
┌─────────────────────────────────────────────────────────────┐
│          Docker Compose（单机）                              │
└─────────────────────────────────────────────────────────────┘

单台服务器：
    └─ 运行 10 个容器

    问题：
    - 服务器挂了？所有服务挂了！❌
    - 无法自动扩展
    - 无法自动故障恢复

═══════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────┐
│          Kubernetes（集群）                                  │
└─────────────────────────────────────────────────────────────┘

集群（3 台服务器）：
    Node 1: 10 个容器
    Node 2: 10 个容器
    Node 3: 10 个容器

    好处：
    - Node 1 挂了？容器自动迁移到 Node 2、3 ✅
    - 自动扩展（流量增加？自动加容器）✅
    - 自动故障恢复 ✅
```

**🎯 你的学习目标**：掌握 Kubernetes 基础，能够将 FastAPI 应用部署到 K8s 集群。

---

## 🎯 什么是 Kubernetes？

### 生活类比：交通指挥系统

**十字路口（没有红绿灯）**：

```
问题：
- 所有车辆争抢道路
- 容易堵车
- 容易事故
- 效率低 ❌
```

**红绿灯（有交通指挥）**：

```
好处：
- 车辆有序通行
- 避免事故
- 提高效率 ✅
```

**Kubernetes = 容器编排的"交通指挥系统"**：

```
功能：
- 自动调度（容器分配到哪台服务器）
- 自动扩展（根据负载自动增减容器）
- 自动恢复（容器挂了自动重启）
- 滚动更新（零停机部署）
- 服务发现（自动注册和发现）
```

---

## 🔧 Kubernetes 核心概念

### 集群架构

```
┌─────────────────────────────────────────────────────────────┐
│                  Kubernetes 集群架构                         │
└─────────────────────────────────────────────────────────────┘

Control Plane（控制平面）：
├─ API Server：集群入口（所有请求都通过它）
├─ Scheduler：调度器（决定 Pod 运行在哪个 Node）
├─ Controller Manager：控制器（维护集群状态）
└─ etcd：键值存储（存储集群配置）

Worker Nodes（工作节点）：
├─ Node 1：
│   ├─ Kubelet：节点代理（与 Master 通信）
│   ├─ Container Runtime：容器运行时（Docker）
│   └─ Pods：运行容器
├─ Node 2：
│   └─ ...
└─ Node 3：
    └─ ...
```

---

### 核心资源

```
1. Pod（容器组）
   └─ 最小部署单元
   └─ 一个或多个容器
   └─ 共享网络和存储

2. Deployment（部署）
   └─ 管理 Pod
   └─ 声明式配置
   └─ 自动扩缩容

3. Service（服务）
   └─ Pod 的稳定访问入口
   └─ 负载均衡
   └─ 服务发现

4. ConfigMap（配置）
   └─ 存储配置数据
   └─ 不敏感的配置

5. Secret（密钥）
   └─ 存储敏感数据
   └─ 加密存储
```

---

## 📝 Kubernetes 部署文件

### Deployment（部署）

**fastapi-deployment.yaml**：

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-app
  labels:
    app: fastapi
spec:
  # 副本数（运行 3 个 Pod）
  replicas: 3

  # 选择器（选择要管理的 Pod）
  selector:
    matchLabels:
      app: fastapi

  # Pod 模板
  template:
    metadata:
      labels:
        app: fastapi
    spec:
      containers:
      - name: fastapi
        image: fastapi-app:v1.0
        ports:
        - containerPort: 8000

        # 环境变量
        env:
        - name: DATABASE_URL
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: database_url
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: app-secret
              key: secret_key

        # 资源限制
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"

        # 健康检查
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10

        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

---

### Service（服务）

**fastapi-service.yaml**：

```yaml
apiVersion: v1
kind: Service
metadata:
  name: fastapi-service
spec:
  # 服务类型
  type: LoadBalancer  # ClusterIP, NodePort, LoadBalancer

  # 选择器（选择要暴露的 Pod）
  selector:
    app: fastapi

  # 端口映射
  ports:
  - protocol: TCP
    port: 80        # 服务端口
    targetPort: 8000 # Pod 端口
```

---

### ConfigMap（配置）

**fastapi-configmap.yaml**：

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  database_url: "postgresql://postgres:password@postgres-service:5432/mydb"
  redis_url: "redis://redis-service:6379"
  debug: "false"
  log_level: "info"
```

---

### Secret（密钥）

**fastapi-secret.yaml**：

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secret
type: Opaque
data:
  # Base64 编码的值
  secret_key: c2VjcmV0X2tleV9iYXNlNjQ=
  database_password: cGFzc3dvcmQ=
```

**创建 Secret（命令行）**：

```bash
# 从字面值创建
kubectl create secret generic app-secret \
  --from-literal=secret_key='my_secret_key' \
  --from-literal=database_password='my_password'

# 从文件创建
kubectl create secret generic app-secret \
  --from-file=secret_key=./secret.txt \
  --from-file=database_password=./password.txt
```

---

## 🚀 Kubernetes 命令

### 基本命令

```bash
# ═══════════════════════════════════════════════════════════
# 应用配置
# ═══════════════════════════════════════════════════════════

# 创建资源
kubectl apply -f fastapi-deployment.yaml
kubectl apply -f fastapi-service.yaml

# 一次应用多个文件
kubectl apply -f k8s/

# ═══════════════════════════════════════════════════════════
# 查看资源
# ═══════════════════════════════════════════════════════════

# 查看 Pod
kubectl get pods

# 查看 Deployment
kubectl get deployments

# 查看 Service
kubectl get services

# 查看所有资源
kubectl get all

# 查看详细信息
kubectl describe pod fastapi-app-xxx

# ═══════════════════════════════════════════════════════════
# 查看日志
# ═══════════════════════════════════════════════════════════

# 查看 Pod 日志
kubectl logs fastapi-app-xxx

# 实时跟踪日志
kubectl logs -f fastapi-app-xxx

# 查看多个 Pod 的日志
kubectl logs -l app=fastapi

# ═══════════════════════════════════════════════════════════
# 执行命令
# ═══════════════════════════════════════════════════════════

# 在 Pod 中执行命令
kubectl exec -it fastapi-app-xxx -- bash

# 运行一次性命令
kubectl exec fastapi-app-xxx -- python -m pytest

# ═══════════════════════════════════════════════════════════
# 扩缩容
# ═══════════════════════════════════════════════════════════

# 手动扩展到 5 个副本
kubectl scale deployment fastapi-app --replicas=5

# 自动扩缩容（HPA）
kubectl autoscale deployment fastapi-app --min=2 --max=10 --cpu-percent=80

# ═══════════════════════════════════════════════════════════
# 更新和回滚
# ═══════════════════════════════════════════════════════════

# 更新镜像
kubectl set image deployment/fastapi-app fastapi=fastapi-app:v2.0

# 查看更新状态
kubectl rollout status deployment/fastapi-app

# 查看更新历史
kubectl rollout history deployment/fastapi-app

# 回滚到上一个版本
kubectl rollout undo deployment/fastapi-app

# 回滚到指定版本
kubectl rollout undo deployment/fastapi-app --to-revision=2

# ═══════════════════════════════════════════════════════════
# 删除资源
# ═══════════════════════════════════════════════════════════

# 删除 Pod（会自动重建）
kubectl delete pod fastapi-app-xxx

# 删除 Deployment
kubectl delete deployment fastapi-app

# 从文件删除
kubectl delete -f fastapi-deployment.yaml
```

---

## 🎨 Ingress（入口）

### 什么是 Ingress？

**Ingress = HTTP(S) 路由规则**：

```
没有 Ingress：
    Service: LoadBalancer
    → 每个服务都需要一个公网 IP
    → 成本高、管理复杂

有 Ingress：
    Ingress: 1 个公网 IP
    → 根据路径/域名路由到不同服务
    → /api/v1 → Service A
    → /api/v2 → Service B
    → 成本低、管理简单
```

---

### Ingress 配置

**fastapi-ingress.yaml**：

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: fastapi-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
  # 基于路径的路由
  - host: api.example.com
    http:
      paths:
      - path: /v1
        pathType: Prefix
        backend:
          service:
            name: fastapi-v1-service
            port:
              number: 80
      - path: /v2
        pathType: Prefix
        backend:
          service:
            name: fastapi-v2-service
            port:
              number: 80

  # 基于域名的路由
  - host: admin.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: admin-service
            port:
              number: 80
```

---

## 🎯 小实验：自己动手

### 实验 1：部署第一个应用

```yaml
# fastapi-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hello-k8s
spec:
  replicas: 2
  selector:
    matchLabels:
      app: hello
  template:
    metadata:
      labels:
        app: hello
    spec:
      containers:
      - name: hello
        image: fastapi-app:v1.0
        ports:
        - containerPort: 8000

---
apiVersion: v1
kind: Service
metadata:
  name: hello-service
spec:
  selector:
    app: hello
  ports:
  - port: 80
    targetPort: 8000
```

```bash
# 部署
kubectl apply -f fastapi-deployment.yaml

# 查看
kubectl get pods
kubectl get services

# 端口转发（本地访问）
kubectl port-forward service/hello-service 8080:80

# 访问 http://localhost:8080
```

---

## 📚 检查理解

回答这些问题来测试你的理解：

1. **什么是 Kubernetes？**
   - 提示：容器编排平台

2. **Pod 和 Deployment 的区别？**
   - 提示：Pod 是容器组，Deployment 管理 Pod

3. **Service 的作用？**
   - 提示：负载均衡、服务发现

4. **ConfigMap 和 Secret 的区别？**
   - 提示：敏感 vs 非敏感配置

5. **什么是滚动更新？**
   - 提示：零停机部署

---

## 🚀 下一步

现在你已经掌握了 Kubernetes 基础，接下来：

1. **学习 CI/CD**：`notes/04_cicd.md`
2. **查看实际代码**：`examples/k8s/`

**记住**：Kubernetes 让应用具备高可用、自动扩展、自动恢复的能力！**

---

**费曼技巧总结**：
- ✅ 交通指挥系统类比
- ✅ 集群架构图
- ✅ 完整的 K8s 部署文件
- ✅ 常用 kubectl 命令
- ✅ Ingress 路由配置
