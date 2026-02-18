"""
APScheduler配置
"""

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor

# JobStore配置
JOBSTORES = {
    'default': SQLAlchemyJobStore(url='sqlite:///jobs.db')
}

# Executor配置
EXECUTORS = {
    'default': ThreadPoolExecutor(max_workers=20)
}

# 任务默认配置
JOB_DEFAULTS = {
    'coalesce': True,
    'max_instances': 3,
    'misfire_grace_time': 60
}

# 调度器配置
SCHEDULER_CONFIG = {
    'jobstores': JOBSTORES,
    'executors': EXECUTORS,
    'job_defaults': JOB_DEFAULTS,
    'timezone': 'UTC'
}
