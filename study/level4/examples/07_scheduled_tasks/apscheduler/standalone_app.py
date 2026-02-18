"""
APScheduler独立进程示例

适合生产环境的独立调度器进程
"""

from apscheduler.schedulers.blocking import BlockingScheduler
from config import SCHEDULER_CONFIG
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建调度器
scheduler = BlockingScheduler(**SCHEDULER_CONFIG)

# 定义任务
def task1():
    logger.info("Executing task1...")

def task2():
    logger.info("Executing task2...")

# 添加任务
scheduler.add_job(
    task1,
    'interval',
    minutes=10,
    id='task1',
    name='Periodic Task 1'
)

scheduler.add_job(
    task2,
    'cron',
    hour='*/2',
    id='task2',
    name='Periodic Task 2'
)

if __name__ == "__main__":
    try:
        logger.info("Starting standalone scheduler...")
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down scheduler...")
        scheduler.shutdown()
