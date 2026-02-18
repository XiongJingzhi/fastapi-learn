"""
Celery任务定义
"""

from celery import Celery
import logging

logger = logging.getLogger(__name__)

# 创建Celery应用
app = Celery('tasks')

# 配置
app.conf.update(
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/1',
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# 定义任务
@app.task
def add(x, y):
    """简单加法任务"""
    result = x + y
    logger.info(f"Adding {x} + {y} = {result}")
    return result

@app.task
def send_email(to, subject, body):
    """发送邮件任务"""
    logger.info(f"Sending email to {to}: {subject}")
    # 模拟发送邮件
    import time
    time.sleep(1)
    logger.info(f"Email sent to {to}")
    return {"status": "sent", "to": to}

@app.task
def generate_report(report_type):
    """生成报表任务"""
    logger.info(f"Generating {report_type} report...")
    import time
    time.sleep(2)
    logger.info(f"{report_type} report generated")
    return {"report": report_type, "status": "completed"}
