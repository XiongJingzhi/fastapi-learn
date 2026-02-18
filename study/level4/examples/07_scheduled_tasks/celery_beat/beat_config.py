"""
Celery Beat调度配置
"""

from celery.schedules import crontab

# Beat调度配置
beat_schedule = {
    'add-every-30-seconds': {
        'task': 'tasks.add',
        'schedule': 30.0,
        'args': (16, 16)
    },
    'send-daily-report': {
        'task': 'tasks.send_email',
        'schedule': crontab(hour=18, minute=0),
        'args': ("admin@example.com", "Daily Report", "Report content")
    },
    'generate-weekly-report': {
        'task': 'tasks.generate_report',
        'schedule': crontab(day_of_week=1, hour=8, minute=0),
        'args': ("weekly",)
    },
}
