"""
Level 1: 最简单的定时任务

学习目标：
- 理解Scheduler基本概念
- 运行你的第一个定时任务
- 看到实际效果

运行：python level1_simple_timer.py
预期：每3秒打印一次"Hello, Scheduler!"
"""

from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime, timedelta

# 创建调度器
scheduler = BlockingScheduler()

# 定义任务
def print_hello():
    print(f"[{datetime.now()}] Hello, Scheduler!")

# 添加任务：每3秒执行一次
scheduler.add_job(print_hello, 'interval', seconds=3)

# 添加任务：5秒后执行一次
scheduler.add_job(
    lambda: print(f"[{datetime.now()}] One-time task!"),
    'date',
    run_date=datetime.now() + timedelta(seconds=5)
)

print("Scheduler started. Press Ctrl+C to exit.")

# 启动调度器（阻塞）
try:
    scheduler.start()
except (KeyboardInterrupt, SystemExit):
    print("Scheduler stopped.")
