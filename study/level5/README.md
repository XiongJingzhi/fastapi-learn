# Level 5: 部署与运维 - Deployment & DevOps

## 🎯 学习目标

掌握将 FastAPI 应用部署到生产环境所需的技能，包括 Docker 容器化、Kubernetes 编排、CI/CD 流程、多环境配置等。

**核心目标**：
- Docker 容器化
- Docker Compose 多容器编排
- Kubernetes 部署
- CI/CD 流程
- 多环境配置管理
- 蓝绿部署和滚动更新

## 🎓 为什么需要部署与运维？

### 从 Level 4 到 Level 5 的演进

在 Level 4，我们学会了：
```python
# Level 4: 在开发环境运行
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# 问题：
# - 如何部署到服务器？
# - 如何管理依赖？
# - 如何保证环境一致性？
# - 如何自动化部署？
# - 如何实现零停机更新？
```

**Level 5 的解决方案**：
```python
# Level 5: 容器化 + 编排 + 自动化

# 1. Dockerfile（容器化）
FROM python:3.11-slim
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# 2. Kubernetes（编排）
kubectl apply -f deployment.yaml

# 3. CI/CD（自动化）
# Push code → GitHub Actions → Build → Test → Deploy
```

## 🏗️ Level 5 的核心主题

### 主题 1：Docker 容器化

**为什么需要 Docker？**

```
传统部署：
    开发环境：Python 3.11
    测试环境：Python 3.9
    生产环境：Python 3.10

    问题：
    - 版本不一致
    - 依赖冲突
    - "我本地能跑啊！"❌

Docker 部署：
    开发环境：容器（Python 3.11）
    测试环境：容器（Python 3.11）
    生产环境：容器（Python 3.11）

    好处：
    - 环境一致 ✅
    - 依赖隔离 ✅
    - "构建一次，到处运行" ✅
```

**内容**：
- Docker 基础概念
- 编写 Dockerfile
- 构建和运行容器
- 优化镜像大小

---

### 主题 2：Docker Compose

**为什么需要 Docker Compose？**

```
单容器部署：
    FastAPI 应用容器
    问题：数据库在哪？Redis 在哪？

多容器部署（Docker Compose）：
    FastAPI 应用容器
    PostgreSQL 容器
    Redis 容器
    Nginx 容器

    好处：
    - 一键启动整个系统 ✅
    - 容器间网络互通 ✅
    - 配置管理简单 ✅
```

**内容**：
- Docker Compose 基础
- 编写 docker-compose.yml
- 服务编排和依赖
- 数据持久化

---

### 主题 3：Kubernetes 编排

**为什么需要 Kubernetes？**

```
Docker（单机）：
    1 台服务器
    → 运行 10 个容器
    → 服务器挂了？所有服务挂了！❌

Kubernetes（集群）：
    3 台服务器
    → 运行 30 个容器（自动分散）
    → 1 台服务器挂了？
    → 容器自动迁移到其他服务器 ✅
    → 自动扩缩容 ✅
    → 自动故障恢复 ✅
```

**内容**：
- Kubernetes 基础概念
- Deployment、Service、Ingress
- ConfigMap 和 Secret
- 滚动更新和回滚

---

### 主题 4：CI/CD 流程

**为什么需要 CI/CD？**

```
手动部署：
    1. 本地测试
    2. 手动上传代码到服务器
    3. 手动安装依赖
    4. 手动重启服务
    5. 发现 bug！
    6. 重复步骤 2-5

    问题：慢、容易出错 ❌

自动化部署（CI/CD）：
    1. Push 代码到 Git
    2. GitHub Actions 自动触发
    3. 自动运行测试
    4. 自动构建 Docker 镜像
    5. 自动部署到生产环境
    6. 发现 bug？回滚（一键）

    好处：快、可靠、可追溯 ✅
```

**内容**：
- CI/CD 基础概念
- GitHub Actions 配置
- 自动化测试
- 自动化部署
- 环境变量管理

---

### 主题 5：多环境配置

**为什么需要多环境配置？**

```
单配置（错误做法）：
    生产环境数据库密码硬编码
    → 代码泄露？密码泄露！❌

多环境配置（正确做法）：
    开发环境：.env.development
    测试环境：.env.staging
    生产环境：.env.production（从密钥管理服务读取）

    好处：
    - 配置分离 ✅
    - 安全（密码不进代码库）✅
    - 灵活切换环境 ✅
```

**内容**：
- 环境变量管理
- pydantic-settings 配置
- ConfigMap 和 Secret
- 密钥管理最佳实践

---

### 主题 6：蓝绿部署和滚动更新

**为什么需要零停机部署？**

```
传统部署（停机更新）：
    1. 停止旧版本
    2. 部署新版本
    3. 启动新版本

    问题：停机时间（用户无法访问）❌

蓝绿部署（零停机）：
    1. 新版本部署到"绿环境"
    2. 测试绿环境
    3. 切换流量：蓝 → 绿
    4. 停止旧版本（蓝环境）

    好处：零停机、快速回滚 ✅
```

**内容**：
- 蓝绿部署策略
- 滚动更新策略
- 金丝雀发布
- Kubernetes 实现零停机部署

## 📁 目录结构

```
study/level5/
├── README.md                    # 本文件：学习概览
├── notes/                       # 学习笔记
│   ├── 01_docker_basics.md
│   ├── 02_docker_compose.md
│   ├── 03_kubernetes.md
│   ├── 04_cicd.md
│   ├── 05_multi_env.md
│   └── 06_deployment_strategies.md
├── examples/                    # 代码示例
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── k8s-deployment.yaml
│   ├── github-actions.yml
│   └── config.example.yml
└── exercises/                   # 练习题
    ├── 01_docker_exercises.md
    └── 02_k8s_exercises.md
```

## 🔗 与 Level 4 的关系

```
Level 4 (生产就绪)
├─ Redis 缓存 ✅
├─ 消息队列 ✅
├─ 外部 API 集成 ✅
└─ 监控、限流、熔断 ✅

        ↓ 加上部署和运维

Level 5 (部署与运维)
├─ Docker 容器化
├─ Kubernetes 编排
├─ CI/CD 自动化
└─ 多环境配置

        ↓ 能够

生产级 FastAPI 应用！
├─ 代码质量高（Level 1-3）
├─ 生产就绪（Level 4）
└─ 自动化部署（Level 5）
```

## 🎓 完成标准

当你完成以下所有项，就说明 Level 5 达标了：

- [ ] 理解 Docker 基础概念
- [ ] 能够编写 Dockerfile
- [ ] 能够使用 Docker Compose 编排多容器应用
- [ ] 理解 Kubernetes 基础概念
- [ ] 能够编写 Kubernetes 部署文件
- [ ] 能够配置 CI/CD 流程
- [ ] 理解多环境配置管理
- [ ] 掌握蓝绿部署和滚动更新
- [ ] 能够独立部署 FastAPI 应用到生产环境

## 🚀 恭喜！

完成 Level 5 后，你将掌握：

✅ **FastAPI 核心技能**（Level 1-3）
✅ **生产级能力**（Level 4）
✅ **部署和运维**（Level 5）

你将能够：
- 从零开始构建生产级 FastAPI 应用
- 使用 Docker 和 Kubernetes 部署
- 实现 CI/CD 自动化流程
- 管理多环境配置
- 实现零停机部署

**祝你学习愉快！记住：自动化部署让应用稳定、可靠、快速迭代！** 🚀
