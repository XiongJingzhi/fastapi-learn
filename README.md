# FastAPI Production Learning Project

> 一个以 **工程化、可维护性、生产可用性** 为目标的 FastAPI 学习与实践项目
>
> 本项目不是 FastAPI API 速查表，也不是 Demo 集合，而是一条 **从基础并发模型 → 真实业务 → 生产部署** 的完整学习与演进路径。

---

## 🎯 项目目标

* 系统性掌握 **FastAPI 在真实生产环境中的使用方式**
* 理解 **异步编程、依赖注入、资源管理** 等关键设计背后的原理
* 构建一个 **可测试、可扩展、可观测、可长期维护** 的 Python 后端服务
* 通过 **与 AI 结对式学习**，在实践中不断重构、纠偏和进化认知

> **核心原则**：FastAPI 只是 *传输层（Transport Layer）*，真正重要的是系统结构、边界与失败处理。

---

## 📁 项目结构

```
fastapi/
├── README.md                    # 本文件：项目概览
├── requirements.txt             # 项目依赖
├── pyproject.toml              # 项目配置
├── .gitignore                  # Git 忽略文件
│
├── study/                      # 📚 学习目录（完整的学习记录）
│   ├── README.md               # 学习目录导航
│   │
│   ├── level0/                 # Level 0: 并发与异步基础
│   │   ├── START_HERE.md       # ← 学习起点！
│   │   ├── README.md           # Level 0 概览
│   │   ├── notes/              # 学习笔记（费曼技巧）
│   │   ├── examples/           # 代码示例
│   │   └── exercises/          # 练习题
│   │
│   ├── level1/                 # Level 1: FastAPI 协议层（待创建）
│   ├── level2/                 # Level 2: 依赖注入（待创建）
│   ├── level3/                 # Level 3: 外部系统（待创建）
│   ├── level4/                 # Level 4: 生产就绪（待创建）
│   └── level5/                 # Level 5: 部署运维（待创建）
│
├── app/                        # 🚀 应用代码（随着学习逐步创建）
│   ├── api/                    #    路由层（仅处理协议）
│   ├── core/                   #    配置、生命周期、依赖注入
│   ├── domain/                 #    业务领域逻辑
│   ├── infrastructure/         #    DB / Cache / MQ / 外部服务
│   ├── schemas/                #    Pydantic 模型
│   ├── services/               #    应用服务层
│   └── main.py                 #    应用入口
│
└── tests/                      # 🧪 测试代码
    └── test_async_basics.py    # 异步基础测试
```

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 开始学习

```bash
# 进入学习目录
cd study/level0

# 从这里开始！
# 查看 START_HERE.md
```

**学习起点**：`study/level0/START_HERE.md`

---

## 📚 学习路径（5 个 Levels）

### Level 0：并发与异步基础 ⭐️ 当前阶段

**学习目标**：理解 **什么时候应该 async，什么时候不该**

**内容**：
- async/await 与事件循环
- 并发 vs 并行
- IO-bound 与 CPU-bound
- 避免阻塞操作

**预计时间**：2-3 天

**当前状态**：🟡 进行中

**学习材料**：`study/level0/`

---

### Level 1：FastAPI 作为协议适配层

**学习目标**：FastAPI 只是 **传输层（Transport Layer）**，不在 endpoint 中写业务逻辑

**内容**：
- 请求参数校验（Query / Path / Body / Header / Cookie）
- 响应处理（JSON / 文件 / Streaming / SSE / WebSocket）
- 统一响应格式与错误模型
- HTTP 状态码与语义

**预计时间**：3-4 天

**状态**：⏸️ 待开始

---

### Level 2：依赖注入与生命周期管理

**学习目标**：理解依赖注入如何解耦和复用

**内容**：
- FastAPI `Depends` 高级用法
- 类依赖 vs 函数依赖
- request-scoped / app-scoped 依赖
- 应用生命周期（lifespan）
- 资源初始化与回收

**预计时间**：3-4 天

**状态**：⏸️ 待开始

---

### Level 3：外部系统集成

**学习目标**：与不可靠的外部系统集成

**内容**：
- 数据库（MySQL、向量数据库）
- 缓存（Redis）
- 消息队列（Kafka）
- 定时任务
- 连接池、超时、重试、幂等、降级

**预计时间**：4-5 天

**状态**：⏸️ 待开始

---

### Level 4：生产就绪能力

**学习目标**：让系统**可观测、可保护、可监控**

**内容**：
- 结构化日志（JSON）
- Prometheus Metrics
- 分布式追踪（OpenTelemetry）
- 限流、熔断、降级

**预计时间**：3-4 天

**状态**：⏸️ 待开始

---

### Level 5：部署、运维与演进

**学习目标**：让系统**可部署、可扩展、可维护**

**内容**：
- Docker 多阶段构建
- 多环境配置（dev / staging / prod）
- CI/CD
- 蓝绿部署 / 金丝雀发布

**预计时间**：3-4 天

**状态**：⏸️ 待开始

---

## 🎓 学习方式

### AI 结对式学习

* 每一个阶段：
  * 先实现
  * 再重构
  * 再引入失败场景
* 主动制造错误，而不是只走 happy path
* 使用测试、日志、指标来验证理解是否正确

> 学习目标不是"写得快"，而是**写得稳、改得动、跑得久**

### i+1 学习理论

- **i** = 当前知识水平
- **+1** = 略高于当前水平的可理解输入
- 既不太简单（i+0，无进步），也不太难（i+10，挫败感）
- 持续提供"可理解性输入"，让学习者在不知不觉中进步

### 费曼技巧

- 用最简单的语言解释复杂概念
- "如果给 5 岁孩子解释，你能说清楚吗？"
- 向"同事"讲解来验证理解
- 发现知识盲区，重新学习

---

## 🧪 测试策略

* `pytest` + `httpx` 测试客户端
* 异步测试（pytest-asyncio）
* Fixture 复用
* 单元测试 vs 集成测试
* Mock 数据库与外部依赖
* 依赖覆盖（FastAPI dependency override）

---

## 🔐 安全实践

* HTTPS 强制
* 输入校验与注入防护
* JWT / OAuth2 / API Key 鉴权
* 权限控制（Scopes / Roles）
* 敏感信息管理（Secrets）
* 依赖漏洞扫描（pip-audit）

---

## 📊 项目状态

- [✅] Level 0：并发基础
- [ ] Level 1：FastAPI 协议层（🟡 进行中）
- [ ] Level 2：依赖注入与生命周期
- [ ] Level 3：外部系统集成
- [ ] Level 4：生产就绪
- [ ] Level 5：部署与演进

---

## 🧭 最终愿景

完成本项目后，你将不仅是：

> "会用 FastAPI 的开发者"

而是：

> **能够设计、实现并长期维护 Python 后端与 Agent 服务的工程师**

---

## 📞 获取帮助

- **Level 0 学习**：查看 `study/level0/START_HERE.md`
- **学习目录导航**：查看 `study/README.md`
- **问题反馈**：在团队中提问

---

**祝你学习愉快！记住：最好的学习方式是实践！** 🚀
