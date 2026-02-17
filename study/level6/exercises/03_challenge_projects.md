# Level 6 挑战项目

## 🎯 项目目标

通过完整的微服务项目，综合运用所学知识，构建一个生产级的微服务架构系统。

---

## 项目：电商平台微服务架构

### 项目描述

构建一个完整的电商平台微服务系统，包含用户、商品、订单、支付、库存、通知等服务。

### 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        客户端                                │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      API 网关                                 │
│  - 路由转发  - 认证授权  - 限流熔断  - 响应聚合                │
└─────────────────────────────────────────────────────────────┘
          ↓           ↓           ↓           ↓           ↓
    ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
    │用户服务 │ │商品服务 │ │订单服务 │ │库存服务 │ │支付服务 │
    └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘
          ↓           ↓           ↓           ↓           ↓
    ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
    │用户 DB  │ │商品 DB  │ │订单 DB  │ │库存 DB  │ │支付 DB  │
    └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘

                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    基础设施                                   │
│  - 服务发现  - 配置中心  - 消息队列  - 缓存  - 追踪           │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 功能需求

### 1. 用户服务（User Service）

**功能**：
- 用户注册、登录
- 用户信息管理
- 用户地址管理
- 用户认证（JWT）

**API**：
```
POST   /api/users/register      # 注册
POST   /api/users/login         # 登录
GET    /api/users/profile       # 获取个人信息
PUT    /api/users/profile       # 更新个人信息
GET    /api/users/addresses     # 获取地址列表
POST   /api/users/addresses     # 添加地址
```

### 2. 商品服务（Product Service）

**功能**：
- 商品列表、搜索
- 商品详情
- 商品分类
- 商品评价

**API**：
```
GET    /api/products            # 商品列表
GET    /api/products/{id}       # 商品详情
GET    /api/products/categories  # 分类列表
GET    /api/products/search     # 搜索商品
```

### 3. 订单服务（Order Service）

**功能**：
- 创建订单
- 订单列表
- 订单详情
- 订单状态更新
- 调用库存服务扣减库存
- 调用支付服务处理支付

**API**：
```
POST   /api/orders              # 创建订单
GET    /api/orders              # 订单列表
GET    /api/orders/{id}         # 订单详情
PUT    /api/orders/{id}/status  # 更新状态
```

### 4. 库存服务（Inventory Service）

**功能**：
- 库存查询
- 库存扣减
- 库存返还
- 库存预警

**API**：
```
GET    /api/inventory/{product_id}  # 查询库存
POST   /api/inventory/deduct        # 扣减库存
POST   /api/inventory/restore       # 返还库存
```

### 5. 支付服务（Payment Service）

**功能**：
- 创建支付
- 支付回调
- 支付状态查询
- 退款处理

**API**：
```
POST   /api/payments             # 创建支付
GET    /api/payments/{id}        # 支付详情
POST   /api/payments/callback    # 支付回调
POST   /api/payments/refund      # 申请退款
```

### 6. 通知服务（Notification Service）

**功能**：
- 发送邮件
- 发送短信
- 站内消息
- 订阅事件（通过消息队列）

**API**：
```
POST   /api/notifications/email    # 发送邮件
POST   /api/notifications/sms      # 发送短信
GET    /api/notifications           # 消息列表
```

---

## 🔧 非功能需求

### 1. 高可用性
- 每个服务至少 2 个副本
- 使用 Kubernetes 部署
- 健康检查和自动重启

### 2. 容错性
- 熔断器
- 降级策略
- 超时控制
- 重试机制

### 3. 性能
- Redis 缓存
- 数据库连接池
- 限流保护
- 负载均衡

### 4. 可观测性
- 分布式追踪（OpenTelemetry + Jaeger）
- 日志聚合（ELK）
- 监控告警（Prometheus + Grafana）

### 5. 安全性
- JWT 认证
- API 限流
- 服务间认证（mTLS 或 API Key）
- 敏感数据加密

---

## 📦 技术栈

### 后端框架
- FastAPI 0.109+
- Python 3.11+

### 数据库
- PostgreSQL 15（主数据存储）
- Redis 7（缓存、限流、分布式锁）

### 消息队列
- Kafka 或 RabbitMQ（异步通信）

### 服务发现与配置
- Consul 或 Nacos

### 容器化
- Docker + Docker Compose（本地开发）
- Kubernetes（生产环境）

### 可观测性
- OpenTelemetry（追踪）
- Jaeger（追踪 UI）
- Prometheus（指标）
- Grafana（可视化）
- ELK（日志）

---

## 📝 实现步骤

### 阶段 1：基础服务（第 1-2 周）

- [ ] 用户服务（注册、登录、JWT）
- [ ] 商品服务（列表、详情、搜索）
- [ ] 数据库设计与迁移
- [ ] Docker Compose 本地开发环境

### 阶段 2：核心业务（第 3-4 周）

- [ ] 订单服务（创建、查询）
- [ ] 库存服务（查询、扣减）
- [ ] 支付服务（创建、模拟支付）
- [ ] 服务间同步通信（HTTP）

### 阶段 3：异步通信（第 5 周）

- [ ] 消息队列集成
- [ ] 通知服务（邮件、短信）
- [ ] 订单状态更新事件
- [ ] 支付成功事件

### 阶段 4：容错与优化（第 6 周）

- [ ] 熔断器实现
- [ ] 降级策略
- [ ] 限流保护
- [ ] 缓存优化

### 阶段 5：可观测性（第 7 周）

- [ ] 分布式追踪
- [ ] 日志聚合
- [ ] 监控告警

### 阶段 6：生产部署（第 8 周）

- [ ] Kubernetes 配置
- [ ] CI/CD 流程
- [ ] 灰度发布
- [ ] 备份与恢复

---

## 🎯 提交要求

### 代码要求
1. 代码规范（遵循 PEP 8）
2. 类型注解（使用 Pydantic）
3. 完整的测试（pytest）
4. 文档完善（README.md + API 文档）

### 部署要求
1. Docker Compose 配置（本地开发）
2. Kubernetes 配置（生产环境）
3. CI/CD 配置（GitHub Actions 或 GitLab CI）
4. 环境变量管理（.env.example）

### 文档要求
1. 架构设计文档
2. API 接口文档（自动生成）
3. 部署文档
4. 运维手册

---

## ✅ 验收标准

### 功能验收
- [ ] 所有 API 正常工作
- [ ] 完整的下单流程（浏览→加购→下单→支付→发货）
- [ ] 用户可以正常注册登录
- [ ] 订单状态正确流转

### 性能验收
- [ ] API 响应时间 < 200ms（P95）
- [ ] 系统支持 1000 QPS
- [ ] 数据库查询优化（索引、慢查询优化）

### 稳定性验收
- [ ] 服务故障自动恢复
- [ ] 熔断器正确触发
- [ ] 限流保护生效
- [ ] 无内存泄漏

### 安全验收
- [ ] 所有 API 需要认证（除公开接口）
- [ ] 敏感数据不泄露
- [ ] SQL 注入防护
- [ ] XSS 防护

---

## 🏆 额外挑战

### 高级功能（可选）
1. **Saga 模式**：实现分布式事务
2. **灰度发布**：实现金丝雀部署
3. **A/B 测试**：实现功能开关
4. **推荐系统**：基于协同过滤的推荐
5. **搜索优化**：使用 Elasticsearch

### 性能优化（可选）
1. **数据库分库分表**
2. **读写分离**
3. **CDN 加速**
4. **静态资源分离**

---

## 📚 参考资源

### 技术文档
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [Pydantic 文档](https://docs.pydantic.dev/)
- [Docker 文档](https://docs.docker.com/)
- [Kubernetes 文档](https://kubernetes.io/docs/)

### 架构参考
- [微服务架构模式](https://microservices.io/patterns/)
- [领域驱动设计](https://martinfowler.com/bliki/DomainDrivenDesign.html)
- [Saga 模式](https://microservices.io/patterns/data/saga.html)

### 开源项目
- [Microservices Example](https://github.com/kubernetes/kubernetes/blob/master/examples/)
- [Spring PetClinic Microservices](https://github.com/spring-petclinic/spring-petclinic-microservices)

---

**祝你项目顺利！记住：微服务架构是一个持续演进的过程，不要一开始就追求完美！** 🚀
