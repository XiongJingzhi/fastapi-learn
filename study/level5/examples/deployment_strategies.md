# 部署策略说明

> **零停机部署的终极指南**

## 目录

1. [蓝绿部署（Blue-Green Deployment）](#1-蓝绿部署blue-green-deployment)
2. [滚动更新（Rolling Update）](#2-滚动更新rolling-update)
3. [金丝雀发布（Canary Deployment）](#3-金丝雀发布canary-deployment)
4. [A/B 测试（A/B Testing）](#4-ab-测试a-b-testing)
5. [回滚策略（Rollback Strategy）](#5-回滚策略rollback-strategy)

---

## 1. 蓝绿部署（Blue-Green Deployment）

### 概念

```
蓝绿部署是一种零停机部署策略，通过维护两套相同的生产环境：
- 蓝环境（Blue）：当前生产版本
- 绿环境（Green）：新版本

部署流程：
1. 部署新版本到绿环境
2. 在绿环境进行测试
3. 切换流量：蓝 → 绿
4. 如果有问题，立即切回蓝环境
```

### 示意图

```
部署前：
    用户流量 → [蓝环境 v1.0]
               [绿环境 (空闲)]

部署后：
    用户流量 → [绿环境 v2.0] ✅
               [蓝环境 v1.0] (备用，可随时切回)
```

### Kubernetes 实现

```yaml
# 蓝绿部署示例

# 步骤 1: 部署新版本（绿环境）
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-app-green  # 新版本
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fastapi-app
      version: v2.0  # 新版本标签
  template:
    metadata:
      labels:
        app: fastapi-app
        version: v2.0
    spec:
      containers:
      - name: fastapi-app
        image: fastapi-app:v2.0
        ports:
        - containerPort: 8000

---
# 步骤 2: 更新 Service（切换流量）
apiVersion: v1
kind: Service
metadata:
  name: fastapi-service
spec:
  selector:
    app: fastapi-app
    version: v2.0  # 切换到新版本
  ports:
  - port: 80
    targetPort: 8000

---
# 步骤 3: 如果有问题，切回旧版本
apiVersion: v1
kind: Service
metadata:
  name: fastapi-service
spec:
  selector:
    app: fastapi-app
    version: v1.0  # 切回旧版本
  ports:
  - port: 80
    targetPort: 8000
```

### 优缺点

| 优点 | 缺点 |
|------|------|
| 零停机时间 | 需要双倍资源（两套环境） |
| 快速回滚（几秒钟） | 切换前必须充分测试 |
| 部署风险低 | 数据库迁移可能不兼容 |
| 实施简单 | 成本高 |

### 适用场景

- 关键业务系统（不能容忍停机）
- 大版本更新（v1.0 → v2.0）
- 需要快速回滚
- 资源充足

### 实战脚本

```bash
#!/bin/bash
# 蓝绿部署脚本

# 配置
BLUE_VERSION="v1.0"
GREEN_VERSION="v2.0"
NAMESPACE="production"

# 步骤 1: 部署绿环境
echo "部署绿环境..."
kubectl apply -f deployment-green.yaml -n $NAMESPACE

# 步骤 2: 等待绿环境就绪
echo "等待绿环境就绪..."
kubectl rollout status deployment/fastapi-app-green -n $NAMESPACE

# 步骤 3: 运行健康检查
echo "运行健康检查..."
HEALTH_CHECK_URL="http://green-service.$NAMESPACE.svc.cluster.local/health"
if curl -f $HEALTH_CHECK_URL; then
    echo "✅ 健康检查通过"
else
    echo "❌ 健康检查失败，停止部署"
    exit 1
fi

# 步骤 4: 切换流量
echo "切换流量到绿环境..."
kubectl patch service fastapi-service -n $NAMESPACE -p '{"spec":{"selector":{"version":"'$GREEN_VERSION'"}}}'

echo "✅ 部署成功！"

# 保留蓝环境一段时间（以防需要回滚）
# 确认无误后删除蓝环境：
# kubectl delete deployment fastapi-app-blue -n $NAMESPACE
```

---

## 2. 滚动更新（Rolling Update）

### 概念

```
滚动更新是逐步替换旧版本为新版本的策略：
- 逐个（或逐批）替换 Pod
- 逐渐增加新版本副本
- 逐渐减少旧版本副本

默认的 Kubernetes Deployment 策略
```

### 示意图

```
初始状态：
[旧版] [旧版] [旧版] [旧版]
100% 旧版本

滚动更新中：
[新版] [旧版] [旧版] [旧版] 25% 新版本
[新版] [新版] [旧版] [旧版] 50% 新版本
[新版] [新版] [新版] [旧版] 75% 新版本

完成状态：
[新版] [新版] [新版] [新版]
100% 新版本
```

### Kubernetes 配置

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-app
spec:
  replicas: 4  # 总副本数

  # 滚动更新策略
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1        # 最多可以多出 1 个 Pod（总数最多 5 个）
      maxUnavailable: 1  # 最多允许 1 个 Pod 不可用

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
        image: fastapi-app:v2.0
        # ... 其他配置
```

### 参数说明

```yaml
maxSurge: 1
# 部署时最多可以多出的 Pod 数量（可以是数字或百分比）
# 例如：maxSurge: 25% 表示 25% 的副本数

maxUnavailable: 1
# 部署时最多允许不可用的 Pod 数量（可以是数字或百分比）
# 例如：maxUnavailable: 25% 表示 25% 的副本数
```

### 滚动更新示例

```yaml
# 示例 1: 保守策略（慢慢来，稳）
replicas: 10
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1        # 每次最多多 1 个 Pod
    maxUnavailable: 0  # 不允许 Pod 不可用（慢但稳）

# 示例 2: 平衡策略（推荐）
replicas: 10
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 2        # 每次最多多 2 个 Pod
    maxUnavailable: 1  # 最多 1 个 Pod 不可用

# 示例 3: 激进策略（快）
replicas: 10
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 5        # 每次最多多 5 个 Pod
    maxUnavailable: 3  # 最多 3 个 Pod 不可用
```

### 优缺点

| 优点 | 缺点 |
|------|------|
| 资源利用率高（不需要双倍资源） | 回滚慢（需要重新滚动） |
| 自动化程度高 | 部署时间长 |
| 零停机（配置正确时） | 新旧版本同时在线（可能不兼容） |
| 默认策略，开箱即用 | 逐步暴露问题 |

### 适用场景

- 常规版本更新
- 资源有限
- 向后兼容的更新
- 需要渐进式部署

### 实战命令

```bash
# 1. 更新镜像（触发滚动更新）
kubectl set image deployment/fastapi-app fastapi-app=fastapi-app:v2.0

# 2. 查看滚动更新状态
kubectl rollout status deployment/fastapi-app

# 3. 查看更新历史
kubectl rollout history deployment/fastapi-app

# 4. 暂停滚动更新
kubectl rollout pause deployment/fastapi-app

# 5. 恢复滚动更新
kubectl rollout resume deployment/fastapi-app

# 6. 回滚到上一个版本
kubectl rollout undo deployment/fastapi-app

# 7. 回滚到指定版本
kubectl rollout undo deployment/fastapi-app --to-revision=2

# 8. 查看实时 Pod 状态
watch kubectl get pods -l app=fastapi-app
```

---

## 3. 金丝雀发布（Canary Deployment）

### 概念

```
金丝雀发布是将新版本先发布给少量用户验证的策略：
- 小部分流量到新版本（如 5%）
- 观察新版本是否正常
- 逐步增加流量（10% → 25% → 50% → 100%）

名称来源：矿工用金丝雀检测有毒气体
```

### 示意图

```
阶段 1: 5% 流量到新版本
95% 流量 → [旧版 v1.0]
 5% 流量 → [新版 v2.0] ✅ 无问题

阶段 2: 25% 流量到新版本
75% 流量 → [旧版 v1.0]
25% 流量 → [新版 v2.0] ✅ 无问题

阶段 3: 100% 流量到新版本
 0% 流量 → [旧版 v1.0]
100% 流量 → [新版 v2.0] ✅ 完成
```

### Kubernetes 实现（使用 Istio）

```yaml
# 步骤 1: 部署新版本（金丝雀）
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-app-v2
spec:
  replicas: 1  # 初始只有 1 个副本
  selector:
    matchLabels:
      app: fastapi-app
      version: v2
  template:
    metadata:
      labels:
        app: fastapi-app
        version: v2
    spec:
      containers:
      - name: fastapi-app
        image: fastapi-app:v2.0
        ports:
        - containerPort: 8000

---
# 步骤 2: 配置流量路由（Istio VirtualService）
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: fastapi-service
spec:
  hosts:
  - fastapi-service
  http:
  - match:
    - headers:
        x-canary:  # 如果有这个 Header，路由到金丝雀
          exact: "true"
    route:
    - destination:
        host: fastapi-service
        subset: v2  # 金丝雀版本
      weight: 100
  - route:  # 默认流量
    - destination:
        host: fastapi-service
        subset: v1  # 旧版本
      weight: 95  # 95% 流量
    - destination:
        host: fastapi-service
        subset: v2  # 金丝雀版本
      weight: 5   # 5% 流量

---
# 步骤 3: 定义 Service Subsets（Istio DestinationRule）
apiVersion: networking.istio.io/v1alpha3
kind: DestinationRule
metadata:
  name: fastapi-service
spec:
  host: fastapi-service
  subsets:
  - name: v1
    labels:
      version: v1
  - name: v2
    labels:
      version: v2
```

### NGINX Ingress 实现

```yaml
# 金丝雀发布（NGINX Ingress）
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: fastapi-ingress-canary
  annotations:
    kubernetes.io/ingress.class: nginx
    # 金丝雀配置
    nginx.ingress.kubernetes.io/canary: "true"
    nginx.ingress.kubernetes.io/canary-weight: "10"  # 10% 流量到金丝雀
    # 或者基于 Header：
    # nginx.ingress.kubernetes.io/canary-by-header: "X-Canary"
    # nginx.ingress.kubernetes.io/canary-by-header-value: "true"
    # 或者基于 Cookie：
    # nginx.ingress.kubernetes.io/canary-by-cookie: "canary_user"
spec:
  rules:
  - host: fastapi.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: fastapi-service-v2  # 金丝雀服务
            port:
              number: 80
```

### 优缺点

| 优点 | 缺点 |
|------|------|
| 风险可控（小范围测试） | 实施复杂（需要流量管理） |
| 快速发现问题 | 新旧版本同时运行 |
| 支持自动回滚 | 需要监控指标 |
| 精细化控制流量 | 可能存在兼容性问题 |

### 适用场景

- 不确定的新功能
- 数据库迁移
- 第三方依赖更新
- 性能敏感的系统

### 金丝雀发布流程

```bash
#!/bin/bash
# 金丝雀发布脚本

# 配置
CANARY_WEIGHT=5  # 初始 5% 流量
INCREMENT=5      # 每次增加 5%
MAX_WEIGHT=100   # 最终 100% 流量
CHECK_INTERVAL=300  # 每 5 分钟检查一次

# 步骤 1: 部署金丝雀版本
kubectl apply -f deployment-canary.yaml

# 步骤 2: 逐步增加流量
while [ $CANARY_WEIGHT -le $MAX_WEIGHT ]; do
    echo "设置金丝雀流量权重: $CANARY_WEIGHT%"

    # 更新 Ingress 注解
    kubectl annotate ingress fastapi-ingress-canary \
        nginx.ingress.kubernetes.io/canary-weight="$CANARY_WEIGHT" \
        --overwrite

    # 等待一段时间，检查指标
    echo "等待 $CHECK_INTERVAL 秒..."
    sleep $CHECK_INTERVAL

    # 检查错误率（示例：使用 Prometheus）
    ERROR_RATE=$(curl -s 'http://prometheus:9090/api/v1/query?query=rate(http_requests_total{status=~"5.."}[5m])' | jq '.data.result[0].value[1]')

    # 如果错误率超过阈值，回滚
    if (( $(echo "$ERROR_RATE > 0.05" | bc -l) )); then
        echo "❌ 错误率过高，回滚到旧版本"
        kubectl annotate ingress fastapi-ingress-canary \
            nginx.ingress.kubernetes.io/canary-weight="0" \
            --overwrite
        exit 1
    fi

    # 增加流量权重
    CANARY_WEIGHT=$((CANARY_WEIGHT + INCREMENT))
done

echo "✅ 金丝雀发布完成！"
```

---

## 4. A/B 测试（A/B Testing）

### 概念

```
A/B 测试是同时运行多个版本，对比效果的策略：
- 版本 A：当前版本（对照组）
- 版本 B：新版本（实验组）
- 根据用户属性分配（随机、用户ID、地区等）
- 收集数据，决定最终版本
```

### 示意图

```
用户分流：
- 随机分配：50% → 版本 A, 50% → 版本 B
- 基于 Cookie：特定用户 → 版本 B
- 基于 Header：API 调用 → 版本 B
- 基于 地理位置：北京 → 版本 B

数据收集：
- 转化率
- 用户停留时间
- 点击率
- 错误率
```

### Kubernetes 实现

```yaml
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: fastapi-service
spec:
  hosts:
  - fastapi-service
  http:
  # 规则 1: 基于 Header 分流
  - match:
    - headers:
        x-ab-test:  # 如果有这个 Header
          exact: "version-b"  # 值为 "version-b"
    route:
    - destination:
        host: fastapi-service
        subset: version-b
      weight: 100  # 全部流量到版本 B
  # 规则 2: 默认分流（50/50）
  - route:
    - destination:
        host: fastapi-service
        subset: version-a
      weight: 50  # 50% 流量到版本 A
    - destination:
        host: fastapi-service
        subset: version-b
      weight: 50  # 50% 流量到版本 B
```

### Python 实现（FastAPI）

```python
from fastapi import FastAPI, Request
import random

app = FastAPI()

@app.get("/api/feature")
async def feature(request: Request):
    # 方式 1: 基于 Cookie 分流
    ab_test = request.cookies.get("ab_test", "a")

    if ab_test == "b":
        # 版本 B：新功能
        return {"version": "B", "data": "new feature"}
    else:
        # 版本 A：旧功能
        return {"version": "A", "data": "old feature"}

@app.get("/api/feature2")
async def feature2(request: Request):
    # 方式 2: 随机分流（50/50）
    if random.random() < 0.5:
        # 版本 B
        return {"version": "B", "data": "new feature"}
    else:
        # 版本 A
        return {"version": "A", "data": "old feature"}

@app.get("/api/feature3")
async def feature3(request: Request):
    # 方式 3: 基于 Header 分流
    ab_test = request.headers.get("X-AB-Test", "a")

    if ab_test == "b":
        # 版本 B
        return {"version": "B", "data": "new feature"}
    else:
        # 版本 A
        return {"version": "A", "data": "old feature"}
```

### 适用场景

- 新功能验证
- UI/UX 优化
- 算法对比
- 营销活动测试

---

## 5. 回滚策略（Rollback Strategy）

### 概念

```
回滚是当新版本出现问题时，恢复到旧版本的策略：

快速回滚的关键：
1. 自动化回滚（无需人工干预）
2. 监控告警（及时发现问题）
3. 预设回滚条件（错误率 > 阈值）
4. 数据库兼容性（新旧版本共用数据库）
```

### Kubernetes 回滚

```bash
# 1. 回滚到上一个版本
kubectl rollout undo deployment/fastapi-app

# 2. 回滚到指定版本
kubectl rollout undo deployment/fastapi-app --to-revision=3

# 3. 查看回滚历史
kubectl rollout history deployment/fastapi-app

# 4. 暂停回滚
kubectl rollout pause deployment/fastapi-app

# 5. 恢复回滚
kubectl rollout resume deployment/fastapi-app
```

### 自动回滚脚本

```bash
#!/bin/bash
# 自动回滚脚本

# 配置
DEPLOYMENT_NAME="fastapi-app"
NAMESPACE="production"
ERROR_THRESHOLD=0.05  # 错误率阈值 5%
CHECK_INTERVAL=60    # 每分钟检查一次

# 监控函数
monitor_deployment() {
    local start_time=$(date +%s)
    local timeout=1800  # 30 分钟超时

    while true; do
        current_time=$(date +%s)
        elapsed=$((current_time - start_time))

        # 超时检查
        if [ $elapsed -gt $timeout ]; then
            echo "⏰ 监控超时，部署正常"
            return 0
        fi

        # 检查错误率（Prometheus）
        ERROR_RATE=$(curl -s "http://prometheus:9090/api/v1/query?query=rate(http_requests_total{status=~\"5..\"}[5m])" | jq '.data.result[0].value[1]')

        # 检查 Pod 状态
        NOT_READY=$(kubectl get pods -n $NAMESPACE -l app=$DEPLOYMENT_NAME --field-selector=status.phase!=Running | wc -l)

        # 判断是否需要回滚
        if (( $(echo "$ERROR_RATE > $ERROR_THRESHOLD" | bc -l) )) || [ $NOT_READY -gt 0 ]; then
            echo "❌ 检测到问题，自动回滚..."
            echo "错误率: $ERROR_RATE"
            echo "未就绪 Pod: $NOT_READY"

            # 回滚
            kubectl rollout undo deployment/$DEPLOYMENT_NAME -n $NAMESPACE

            # 通知
            send_notification "❌ 部署失败，已自动回滚"

            return 1
        fi

        echo "✅ 监控中... 错误率: $ERROR_RATE, 未就绪 Pod: $NOT_READY"
        sleep $CHECK_INTERVAL
    done
}

# 监控部署
if monitor_deployment; then
    echo "✅ 部署成功"
    send_notification "✅ 部署成功"
else
    echo "❌ 部署失败，已回滚"
    exit 1
fi

# 通知函数（示例：钉钉）
send_notification() {
    local message=$1
    curl -X POST "https://oapi.dingtalk.com/robot/send?access_token=$DINGTALK_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"msgtype\":\"text\",\"text\":{\"content\":\"$message\"}}"
}
```

### 数据库回滚

```bash
# 使用 Alembic 回滚数据库
alembic downgrade -1  # 回滚一个版本
alembic downgrade base  # 回滚到初始状态

# 或指定版本
alembic downgrade <revision_id>
```

### 回滚检查清单

- [ ] 部署前备份数据库
- [ ] 测试回滚流程
- [ ] 确认数据库兼容性
- [ ] 配置监控和告警
- [ ] 准备回滚脚本
- [ ] 通知相关人员

---

## 总结对比

| 策略 | 复杂度 | 资源需求 | 回滚速度 | 适用场景 |
|------|--------|----------|----------|----------|
| 蓝绿部署 | ⭐⭐ | ⭐⭐⭐ (双倍) | ⚡ 秒级 | 大版本、关键系统 |
| 滚动更新 | ⭐ | ⭐ (正常) | 🐢 分钟级 | 常规更新、默认策略 |
| 金丝雀发布 | ⭐⭐⭐ | ⭐⭐ (1.5x) | ⚡ 秒级 | 不确定的功能 |
| A/B 测试 | ⭐⭐⭐⭐ | ⭐⭐⭐ (多版本) | ⚡ 秒级 | 功能验证、优化 |

---

## 最佳实践

1. **选择合适的策略**
   - 小版本更新：滚动更新
   - 大版本升级：蓝绿部署
   - 不确定的功能：金丝雀发布
   - 性能对比：A/B 测试

2. **自动化**
   - 使用 CI/CD 自动部署
   - 配置自动回滚
   - 监控和告警

3. **测试**
   - 部署前充分测试
   - 预发环境验证
   - 准备测试数据

4. **监控**
   - 实时监控错误率
   - 监控响应时间
   - 监控资源使用

5. **文档**
   - 记录部署流程
   - 记录回滚步骤
   - 更新运行手册

---

**记住：好的部署策略能够在出现问题时快速恢复，而不是避免问题！** 🚀
