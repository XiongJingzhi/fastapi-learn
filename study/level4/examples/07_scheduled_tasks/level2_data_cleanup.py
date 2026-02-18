"""
Level 2: 数据清理任务

实际场景：
- 每小时清理过期token
- 每天凌晨2点归档日志
- 任务失败自动重试

运行：python level2_data_cleanup.py
"""

import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataCleanupService:
    """数据清理服务"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()

    async def cleanup_expired_tokens(self):
        """清理过期token（Level 2示例）"""
        try:
            logger.info("Starting token cleanup...")

            # 模拟数据库操作
            expired_tokens = await self._get_expired_tokens()
            logger.info(f"Found {len(expired_tokens)} expired tokens")

            # 删除过期token
            deleted = await self._delete_tokens(expired_tokens)

            logger.info(f"Cleanup completed: {deleted} tokens deleted")

        except Exception as e:
            logger.error(f"Token cleanup failed: {e}")
            raise

    async def archive_logs(self):
        """归档日志（每天凌晨2点）"""
        try:
            logger.info("Starting log archival...")

            # 模拟归档操作
            await self._compress_logs()
            await self._upload_to_storage()

            logger.info("Log archival completed")

        except Exception as e:
            logger.error(f"Log archival failed: {e}")
            raise

    async def _get_expired_tokens(self):
        """模拟：获取过期token"""
        await asyncio.sleep(0.1)  # 模拟数据库查询
        return list(range(10))  # 模拟10个过期token

    async def _delete_tokens(self, tokens):
        """模拟：删除token"""
        await asyncio.sleep(0.2)
        return len(tokens)

    async def _compress_logs(self):
        """模拟：压缩日志"""
        await asyncio.sleep(1)

    async def _upload_to_storage(self):
        """模拟：上传存储"""
        await asyncio.sleep(2)

    def start(self):
        """启动调度器"""
        # 每小时清理过期token
        self.scheduler.add_job(
            self.cleanup_expired_tokens,
            'interval',
            hours=1,
            id='cleanup_tokens',
            max_instances=1,  # 防止任务重叠
            misfire_grace_time=300  # 容忍5秒延迟
        )

        # 每天凌晨2点归档日志
        self.scheduler.add_job(
            self.archive_logs,
            'cron',
            hour=2,
            minute=0,
            id='archive_logs',
            max_instances=1
        )

        # 测试用：每30秒执行一次
        self.scheduler.add_job(
            self.cleanup_expired_tokens,
            'interval',
            seconds=30,
            id='test_cleanup'
        )

        self.scheduler.start()
        logger.info("Data cleanup service started")

# 运行
if __name__ == "__main__":
    service = DataCleanupService()
    service.start()

    try:
        asyncio.Event().wait()  # 保持运行
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        service.scheduler.shutdown()
