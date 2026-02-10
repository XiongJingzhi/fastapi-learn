# 04. CI/CD 流程 - CI/CD Pipeline

## 📍 在架构中的位置

**从"手动部署"到"自动化流水线"**

```
┌─────────────────────────────────────────────────────────────┐
│          手动部署（传统方式）                                 │
└─────────────────────────────────────────────────────────────┘

部署流程：
    1. 本地写代码
    2. 本地测试（可能跳过）❌
    3. 手动上传代码到服务器（SCP/FTP）
    4. 手动安装依赖
    5. 手动重启服务
    6. 发现 bug！❌
    7. 重复步骤 2-6

    问题：
    - 慢（30 分钟+）❌
    - 容易出错（忘记安装依赖）❌
    - 无法追溯（谁部署的？什么版本？）❌
    - 回滚困难 ❌

═══════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────┐
│          CI/CD（自动化流水线）                                │
└─────────────────────────────────────────────────────────────┘

自动化流程：
    1. Push 代码到 Git
    2. GitHub Actions 自动触发 ✅
    3. 自动运行测试 ✅
    4. 自动构建 Docker 镜像 ✅
    5. 自动部署到测试环境 ✅
    6. 自动运行集成测试 ✅
    7. 自动部署到生产环境 ✅
    8. 发现 bug？一键回滚 ✅

    好处：
    - 快（5 分钟）✅
    - 可靠（自动化，不会遗漏步骤）✅
    - 可追溯（完整的部署历史）✅
    - 回滚简单 ✅
```

**🎯 你的学习目标**：掌握 CI/CD 流程，能够实现 FastAPI 应用的自动化部署。

---

## 🎯 什么是 CI/CD？

### 两大概念

**CI（Continuous Integration）持续集成**：

```
含义：
    频繁地（每天多次）将代码集成到主干

流程：
    开发者提交代码
    → 自动运行测试
    → 自动构建
    → 快速反馈（是否通过）

好处：
    - 及早发现 bug
    - 减少集成冲突
    - 提高代码质量
```

---

**CD（Continuous Deployment/Continuous Delivery）**：

```
Continuous Delivery（持续交付）：
    自动部署到测试环境
    → 人工批准后部署到生产环境

Continuous Deployment（持续部署）：
    完全自动化
    → 通过测试后自动部署到生产环境

好处：
    - 快速交付
    - 降低风险
    - 用户快速获得新功能
```

---

### 生活类比：汽车生产线

**手工造车（没有自动化）**：

```
流程：
    1. 工人 A 安装引擎
    2. 工人 B 安装轮胎
    3. 工人 C 安装座椅
    4. 工人 D 测试
    5. 发现问题？手动回溯

    问题：慢、容易出错、质量不稳定 ❌
```

**自动化生产线（有 CI/CD）**：

```
流程：
    1. 传送带（自动流转）
    2. 机器人（自动安装）
    3. 自动检测（质量检查）
    4. 发现问题？自动停线

    好处：快、质量高、可追溯 ✅
```

---

## 🔧 GitHub Actions 基础

### Workflow 文件

**`.github/workflows/ci-cd.yml`**：

```yaml
# 工作流名称
name: CI/CD Pipeline

# 触发条件
on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

# 环境变量
env:
  DOCKER_REGISTRY: ghcr.io
  IMAGE_NAME: fastapi-app

# ═══════════════════════════════════════════════════════════
# Jobs（任务）
# ═══════════════════════════════════════════════════════════

jobs:
  # Job 1: 运行测试
  test:
    name: Run Tests
    runs-on: ubuntu-latest

    steps:
    # 1. 检出代码
    - name: Checkout code
      uses: actions/checkout@v3

    # 2. 设置 Python
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    # 3. 安装依赖
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov

    # 4. 运行测试
    - name: Run tests
      run: |
        pytest --cov=app tests/

    # 5. 上传覆盖率报告
    - name: Upload coverage
      uses: codecov/codecov-action@v3

  # Job 2: 构建和推送镜像
  build:
    name: Build Docker Image
    runs-on: ubuntu-latest
    needs: test  # 依赖 test 任务

    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2

    - name: Login to Docker Registry
      uses: docker/login-action@v2
      with:
        registry: ${{ env.DOCKER_REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - name: Build and push
      uses: docker/build-push-action@v4
      with:
        context: .
        push: true
        tags: |
          ${{ env.DOCKER_REGISTRY }}/${{ github.repository }}:latest
          ${{ env.DOCKER_REGISTRY }}/${{ github.repository }}:${{ github.sha }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

  # Job 3: 部署到测试环境
  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/develop'
    environment:
      name: staging
      url: https://staging.example.com

    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Deploy to Kubernetes
      uses: azure/k8s-deploy@v4
      with:
        manifests: |
          k8s/staging/deployment.yaml
          k8s/staging/service.yaml
        images: |
          ${{ env.DOCKER_REGISTRY }}/${{ github.repository }}:${{ github.sha }}

  # Job 4: 部署到生产环境
  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main'
    environment:
      name: production
      url: https://example.com

    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Deploy to Kubernetes
      uses: azure/k8s-deploy@v4
      with:
        manifests: |
          k8s/production/deployment.yaml
          k8s/production/service.yaml
        images: |
          ${{ env.DOCKER_REGISTRY }}/${{ github.repository }}:${{ github.sha }}
```

---

## 🎨 完整的 CI/CD 流程

### 1. 代码质量检查

**Lint 和 Format 检查**：

```yaml
jobs:
  lint:
    name: Code Quality Check
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install ruff black isort mypy

    - name: Run ruff (linter)
      run: ruff check .

    - name: Run black (formatter check)
      run: black --check .

    - name: Run isort (import sort check)
      run: isort --check-only .

    - name: Run mypy (type check)
      run: mypy app/
```

---

### 2. 安全扫描

**依赖漏洞扫描**：

```yaml
jobs:
  security:
    name: Security Scan
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        scan-type: 'fs'
        scan-ref: '.'
        format: 'sarif'
        output: 'trivy-results.sarif'

    - name: Upload Trivy results to GitHub Security tab
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: 'trivy-results.sarif'
```

---

### 3. 多环境部署

**环境配置**：

```yaml
deploy-staging:
  environment:
    name: staging
    url: https://staging.example.com

  steps:
  - name: Configure kubectl
    run: |
      echo "${{ secrets.KUBE_CONFIG }}" | base64 -d > kubeconfig
      export KUBECONFIG=kubeconfig

  - name: Deploy to staging
    run: |
      kubectl set image deployment/fastapi-app \
        fastapi=ghcr.io/${{ github.repository }}:${{ github.sha }} \
        -n staging

deploy-production:
  environment:
    name: production
    url: https://example.com

  steps:
  - name: Deploy to production
    run: |
      # 同上，但使用 production namespace
```

---

### 4. 自动化测试

**单元测试 + 集成测试**：

```yaml
test:
  steps:
  # 单元测试
  - name: Unit tests
    run: pytest tests/unit/ -v

  # 集成测试（需要数据库）
  - name: Integration tests
    run: |
      docker-compose up -d db redis
      pytest tests/integration/ -v
      docker-compose down

  # E2E 测试
  - name: E2E tests
    run: |
      npm install -g cypress
      cypress run
```

---

## 🔄 Git Flow 策略

### 分支策略

```
main（生产分支）
├─ 稳定版本
├─ 保护分支（需要 PR）
└─ 触发生产部署

develop（开发分支）
├─ 最新开发版本
├─ 触发测试部署
└─ 合并到 main 前需要测试

feature/*（功能分支）
├─ feature/new-api
├─ feature/fix-bug
└─ 完成后合并到 develop

hotfix/*（紧急修复分支）
├─ hotfix/critical-bug
├─ 直接从 main 分支创建
└─ 修复后合并回 main 和 develop
```

---

### 工作流程

```
1. 开发新功能
   git checkout -b feature/new-api
   # ... 写代码 ...
   git commit -m "Add new API"

2. 推送到远程
   git push origin feature/new-api

3. 创建 PR
   # 在 GitHub 上创建 PR: feature/new-api → develop

4. CI 自动运行
   # 运行测试、构建、部署到测试环境

5. Code Review
   # 团队成员 review 代码

6. 合并到 develop
   # PR 通过后合并

7. 部署到测试环境
   # 自动部署

8. 测试通过后，创建 PR: develop → main

9. 部署到生产环境
   # 自动部署
```

---

## 🎯 小实验：自己动手

### 实验 1：基本 CI 流程

```yaml
# .github/workflows/ci.yml
name: CI

on: [push]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Run tests
      run: |
        pip install -r requirements.txt
        pytest
```

---

### 实验 2：自动构建镜像

```yaml
jobs:
  build:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Build Docker image
      run: docker build -t myapp:${{ github.sha }} .

    - name: Push to registry
      run: docker push myapp:${{ github.sha }}
```

---

## 📚 检查理解

回答这些问题来测试你的理解：

1. **什么是 CI 和 CD？**
   - 提示：持续集成、持续部署/交付

2. **CI/CD 的好处？**
   - 提示：快速、可靠、可追溯

3. **GitHub Actions 的核心概念？**
   - 提示：Workflow、Job、Step

4. **什么是 Git Flow？**
   - 提示：分支管理策略

5. **如何实现自动化测试？**
   - 提示：在 CI 流程中运行测试命令

---

## 🚀 下一步

现在你已经掌握了 CI/CD 基础，接下来：

1. **学习多环境配置**：`notes/05_multi_env.md`
2. **查看实际代码**：`examples/.github/workflows/`

**记住**：CI/CD 让软件开发像流水线一样高效、可靠！**

---

**费曼技巧总结**：
- ✅ 汽车生产线类比
- ✅ CI/CD 流程图
- ✅ 完整的 GitHub Actions 示例
- ✅ 代码质量检查、安全扫描
- ✅ 多环境部署策略
- ✅ Git Flow 分支策略
