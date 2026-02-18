"""
Celery独立Worker示例

启动命令：
  celery -A standalone_worker worker --loglevel=info

启动Beat：
  celery -A standalone_worker beat --loglevel=info
"""

from tasks import app, beat_schedule

# 添加beat配置
app.conf.beat_schedule = beat_schedule

if __name__ == "__main__":
    app.start()
