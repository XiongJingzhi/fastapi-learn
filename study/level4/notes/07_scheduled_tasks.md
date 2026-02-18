# 07. 定时任务 - Scheduled Tasks

## 📍 在架构中的位置

**定时任务：让程序自动按计划执行**

```
┌─────────────────────────────────────────────────────────────┐
│          为什么需要定时任务？                                  │
└─────────────────────────────────────────────────────────────┘

手动执行：
    每天早上9点手动运行数据报表
    → 忘记执行？数据缺失 ❌
    → 人在休假？没人执行 ❌
    → 凌晨3点执行？没人愿意 ❌

定时任务：
    程序每天早上9点自动运行
    → 准时执行 ✅
    → 可靠稳定 ✅
    → 任何时间都可以 ✅
```

**🎯 你的学习目标**：掌握定时任务的实现，从简单到生产级。

---

## 🎯 什么是定时任务？

### 生活类比：闹钟

**APScheduler 就像手机闹钟**：
- 设置一次：明天早上7点叫醒我（date trigger）
- 重复：每天早上7点叫醒我（interval trigger）
- 复杂：每周一到周五早上7点（cron trigger）

**Celery Beat 就像公司前台**：
- 前台有任务清单（beat schedule）
- 到点提醒员工执行任务
- 员工可以有很多个（distributed workers）
- 前台只负责安排，不负责执行

---

### 定时任务核心概念

```
┌─────────────────────────────────────────────────────────────┐
│                  定时任务基本组件                              │
└─────────────────────────────────────────────────────────────┘

1. Scheduler（调度器）
   └─ 总指挥，负责管理所有任务

2. Trigger（触发器）
   └─ 什么时候执行？
      ├─ date: 某个具体时间
      ├─ interval: 固定间隔
      └─ cron: 复杂时间规则

3. Job（任务）
   └─ 做什么？

4. Executor（执行器）
   └─ 怎么执行？（单线程/多线程/异步）
```

---

## 📦 两个主要技术栈对比

### APScheduler vs Celery Beat

| 特性 | APScheduler | Celery Beat |
|------|-------------|-------------|
| **复杂度** | 简单 | 复杂 |
| **学习曲线** | 平缓 | 陡峭 |
| **分布式** | 需要额外方案 | 原生支持 |
| **适用场景** | 单机/小规模 | 大规模分布式 |
| **依赖** | 只需Python | 需要Redis/RabbitMQ |
| **监控** | 基础 | Flower（强大） |
| **任务链** | 不支持 | 支持（chain/group） |
| **代码量** | 10-20行 | 50-100行 |

---

## 🎓 如何选择？

### 快速选择指南

**场景 1：个人项目 / 小型应用**
```
你的需求：
- 单机运行
- 任务简单（10个以内）
- 不需要分布式

→ 推荐使用：APScheduler ✅
→ 学习文件：07a_ap_scheduler_intro.md
```

**场景 2：中型应用 / 需要可靠性**
```
你的需求：
- 多实例部署
- 任务较多（10-50个）
- 需要任务持久化

→ 推荐使用：APScheduler + 分布式锁 ✅
→ 学习文件：07b_ap_scheduler_advanced.md
```

**场景 3：大型应用 / 微服务**
```
你的需求：
- 分布式系统
- 复杂任务依赖（A完成后执行B）
- 需要强大监控

→ 推荐使用：Celery Beat ✅
→ 学习文件：07c_celery_beat_intro.md
```

---

## 📚 学习路径

### 渐进式学习（i+1 理论）

```
Level 1: Hello World（当前水平 i）
    ├─ 理解基本概念
    ├─ 最简单的APScheduler示例
    └─ 07a_ap_scheduler_intro.md

        ↓ +1

Level 2: 实际场景（i+1）
    ├─ 数据清理任务
    ├─ 错误处理
    └─ 07b_ap_scheduler_advanced.md

        ↓ +1

Level 3: 分布式挑战（i+2）
    ├─ 多实例部署的问题
    ├─ 分布式锁
    └─ 07c_celery_beat_intro.md

        ↓ +1

Level 4: 生产级（i+3）
    ├─ 监控和告警
    ├─ 任务执行历史
    └─ 07e_best_practices.md
```

---

## 🎯 学习检查点

**学完本模块后，你应该能够**：

- [ ] 理解为什么需要定时任务
- [ ] 使用APScheduler实现简单定时任务
- [ ] 理解Celery Beat的架构
- [ ] 处理任务失败和重试
- [ ] 实现分布式定时任务
- [ ] 根据场景选择合适的技术

---

## 🚀 快速开始

### 安装依赖

```bash
# APScheduler
pip install apscheduler

# Celery Beat
pip install celery redis

# 可选：Celery监控
pip install flower
```

### Hello World（10秒）

```python
from apscheduler.schedulers.blocking import BlockingScheduler

scheduler = BlockingScheduler()

def job():
    print("Hello, Scheduled Task!")

scheduler.add_job(job, 'interval', seconds=5)

scheduler.start()
```

**运行**：每5秒打印一次 "Hello, Scheduled Task!"

---

## 📖 下一步

**根据你的场景选择**：

1. **APScheduler基础** → `notes/07a_ap_scheduler_intro.md`
2. **APScheduler高级** → `notes/07b_ap_scheduler_advanced.md`
3. **Celery Beat基础** → `notes/07c_celery_beat_intro.md`
4. **Celery Beat高级** → `notes/07d_celery_beat_advanced.md`
5. **最佳实践** → `notes/07e_best_practices.md`

**代码示例**：`examples/07_scheduled_tasks/`

---

## 💡 记住

> **定时任务不是魔法，只是程序按计划执行。**
>
> - APScheduler = 轻量级闹钟
> - Celery Beat = 企业级调度系统
> - 选择合适的工具，而不是最复杂的工具

---

**祝你学习愉快！记住：最好的学习方式是实践！** 🚀
