# 定时任务示例导航

## 🎯 按难度渐进学习

### Level 1: Hello World
- `level1_simple_timer.py` - 最简单的定时任务
  - 5秒后执行一次
  - 每3秒打印"Hello"
  - 代码量：20行

### Level 2: 实际场景
- `level2_data_cleanup.py` - 数据清理任务
  - 删除过期token
  - 错误处理
  - 代码量：80行

### Level 3: 分布式协调
- `level3_distributed_coordinator.py` - 多实例只执行一次
  - 分布式锁（模拟）
  - 任务协调
  - 代码量：100行

### Level 4: 生产监控
- `level4_production_monitor.py` - 完整生产级方案
  - 任务监控
  - 执行历史
  - Web管理界面
  - 代码量：300行

## 🛠️ 技术栈完整示例

### APScheduler完整实现
- `apscheduler/embedded_app.py` - 嵌入FastAPI
- `apscheduler/standalone_app.py` - 独立进程
- `apscheduler/config.py` - 配置管理

### Celery Beat完整实现
- `celery_beat/tasks.py` - 任务定义
- `celery_beat/beat_config.py` - Beat配置
- `celery_beat/standalone_worker.py` - 独立worker

## 🚀 快速运行

### Level 1示例
```bash
cd study/level4/examples/07_scheduled_tasks
python level1_simple_timer.py
```

### Level 2示例
```bash
python level2_data_cleanup.py
```

### Level 4示例（需要FastAPI）
```bash
pip install fastapi uvicorn
python level4_production_monitor.py
# 访问 http://localhost:8000/docs
```

### Celery示例（需要Redis）
```bash
# 启动Redis
docker run -d -p 6379:6379 redis:alpine

# 启动Worker
cd celery_beat
celery -A standalone_worker worker --loglevel=info

# 启动Beat（另一个终端）
celery -A standalone_worker beat --loglevel=info
```

## 📦 依赖安装

```bash
# 基础依赖
pip install apscheduler

# FastAPI依赖
pip install fastapi uvicorn

# Celery依赖
pip install celery redis
```
