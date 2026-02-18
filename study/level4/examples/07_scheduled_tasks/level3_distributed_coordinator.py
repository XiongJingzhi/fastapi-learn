"""
Level 3: 分布式任务协调

问题：多实例部署时，任务会重复执行
方案：使用Redis分布式锁

运行：
- 终端1：python level3_distributed_coordinator.py --instance-id=node1
- 终端2：python level3_distributed_coordinator.py --instance-id=node2
观察：只有一个实例执行任务
"""

import asyncio
import argparse
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DistributedScheduler:
    """分布式任务调度器（模拟版本）"""

    def __init__(self, instance_id: str):
        self.instance_id = instance_id
        self.scheduler = AsyncIOScheduler()
        # 模拟Redis锁
        self.lock_acquired = False

    async def distributed_task(self):
        """分布式任务（只在一个实例上执行）"""

        # 模拟获取分布式锁
        lock_key = "lock:monthly_report"

        # 简化版：第一个实例获取锁
        if not self.lock_acquired and self.instance_id == "node1":
            self.lock_acquired = True
            logger.info(f"[{self.instance_id}] Lock acquired, starting task...")

            # 执行任务（模拟月报生成）
            await self._generate_monthly_report()

            logger.info(f"[{self.instance_id}] Task completed")
            self.lock_acquired = False
        else:
            logger.info(f"[{self.instance_id}] Another instance is running the task")

    async def _generate_monthly_report(self):
        """生成月报（模拟耗时操作）"""
        logger.info("Generating monthly report...")
        await asyncio.sleep(2)  # 模拟2秒操作
        logger.info("Monthly report generated")

    def start(self):
        """启动调度器"""
        # 测试用：每15秒执行一次
        self.scheduler.add_job(
            self.distributed_task,
            'interval',
            seconds=15,
            id='test_distributed_task'
        )

        self.scheduler.start()
        logger.info(f"[{self.instance_id}] Distributed scheduler started")

# 运行
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - [%(levelname)s] - %(message)s'
    )

    parser = argparse.ArgumentParser()
    parser.add_argument("--instance-id", default="node1")
    args = parser.parse_args()

    coordinator = DistributedScheduler(args.instance_id)
    coordinator.start()

    try:
        asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info(f"[{args.instance_id}] Shutting down...")
        coordinator.scheduler.shutdown()
