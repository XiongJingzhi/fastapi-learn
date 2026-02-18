import logging
from collections.abc import Awaitable, Callable
from functools import lru_cache

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import settings

logger = logging.getLogger(__name__)

WARMUP_JOB_ID = "warmup-external-todo"


@lru_cache(maxsize=1)
def get_scheduler() -> AsyncIOScheduler:
    return AsyncIOScheduler()


def setup_scheduler_jobs(warmup_job: Callable[[], Awaitable[None]]) -> None:
    scheduler = get_scheduler()
    if scheduler.get_job(WARMUP_JOB_ID):
        return
    scheduler.add_job(
        warmup_job,
        IntervalTrigger(seconds=settings.SCHEDULER_EXTERNAL_TODO_REFRESH_SECONDS),
        id=WARMUP_JOB_ID,
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )


def start_scheduler() -> None:
    if not settings.SCHEDULER_ENABLED:
        return
    scheduler = get_scheduler()
    if scheduler.running:
        return
    scheduler.start()
    logger.info("Scheduler started")


def stop_scheduler() -> None:
    scheduler = get_scheduler()
    if not scheduler.running:
        return
    scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped")


def get_scheduler_status() -> tuple[bool, list[str]]:
    scheduler = get_scheduler()
    job_ids = [job.id for job in scheduler.get_jobs()]
    return scheduler.running, job_ids
