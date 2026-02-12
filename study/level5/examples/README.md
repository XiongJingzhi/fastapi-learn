# Level 5 Examples - 部署与运维

## 📁 目录结构

```
examples/
├── Dockerfile                      # Docker 多阶段构建配置
├── docker-compose.yml              # 本地开发环境编排
├── .dockerignore                   # Docker 构建排除文件
├── .env.example                    # 环境变量示例
├── main.py                         # FastAPI 应用示例
├── requirements.txt                # Python 依赖
├── kubernetes/                     # Kubernetes 配置
│   ├── deployment.yaml             # Deployment 部署配置
│   ├── service.yaml                # Service 服务配置
│   ├── ingress.yaml                # Ingress 入口配置
│   ├── configmap.yaml              # ConfigMap 配置
│   └── secret.yaml                 # Secret 敏感信息
├── config/                         # 多环境配置
│   ├── base.py                     # 基础配置
│   ├── development.py              # 开发环境
│   ├── staging.py                  # 预发环境
│   └── production.py               # 生产环境
├── .github/workflows/              # CI/CD 配置
│   └── ci.yml                      # GitHub Actions
└── deployment_strategies.md        # 部署策略说明
```

---

## 🚀 快速开始

### 1. 本地 Docker 运行

```bash
# 构建镜像
docker build -t fastapi-app .

# 运行容器
docker run -d -p 8000:8000 fastapi-app

# 访问应用
curl http://localhost:8000/health
```

### 2. Docker Compose（推荐）

```bash
# 复制环境变量文件
cp .env.example .env

# 编辑 .env 文件（可选）

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 3. Kubernetes 部署

```bash
# 创建 ConfigMap 和 Secret
kubectl apply -f kubernetes/configmap.yaml
kubectl apply -f kubernetes/secret.yaml

# 部署应用
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/service.yaml

# 配置 Ingress（可选）
kubectl apply -f kubernetes/ingress.yaml

# 查看状态
kubectl get pods,svc,ingress
```

---

## 📝 配置说明

### Dockerfile 特性

- ✅ 多阶段构建（减小镜像大小）
- ✅ 非 root 用户运行（安全）
- ✅ 健康检查
- ✅ 依赖缓存优化

### docker-compose.yml 包含

- FastAPI 应用
- PostgreSQL 数据库
- Redis 缓存
- 数据持久化
- 健康检查

### Kubernetes 配置

- Deployment：3 副本，滚动更新
- Service：ClusterIP 类型
- Ingress：域名路由，TLS 支持
- ConfigMap：非敏感配置
- Secret：敏感信息（base64 编码）

---

## 🔧 环境配置

### 开发环境

```bash
export ENVIRONMENT=development
python main.py
```

### 预发环境

```bash
export ENVIRONMENT=staging
python main.py
```

### 生产环境

```bash
export ENVIRONMENT=production
python main.py
```

---

## 📚 学习路径

1. **基础阶段**：学习 Docker 基础
   - 阅读 `Dockerfile`
   - 运行本地容器
   - 练习基础练习

2. **进阶阶段**：多容器编排
   - 学习 `docker-compose.yml`
   - 理解服务依赖
   - 练习进阶练习

3. **高级阶段**：Kubernetes 部署
   - 学习 Kubernetes 配置文件
   - 部署到集群
   - 练习高级练习

4. **专家阶段**：CI/CD 和监控
   - 学习 CI/CD 配置
   - 配置监控告警
   - 完成挑战项目

---

## 🎯 练习指南

1. 从 `exercises/01_basic_exercises.md` 开始
2. 完成基础练习后，进入进阶练习
3. 最后完成综合项目

---

## 📖 推荐阅读顺序

1. `Dockerfile` - 了解容器化
2. `docker-compose.yml` - 了解服务编排
3. `kubernetes/deployment.yaml` - 了解 K8s 部署
4. `kubernetes/service.yaml` - 了解服务发现
5. `kubernetes/ingress.yaml` - 了解外部访问
6. `.github/workflows/ci.yml` - 了解 CI/CD
7. `deployment_strategies.md` - 了解部署策略

---

**记住：代码写好只是完成了一半，能部署出去才是真正的完整！** 🚀
