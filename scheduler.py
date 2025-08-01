import os
from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Celery configuration
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

# Create Celery instance for scheduling
celery_app = Celery(
    'scheduler',
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='Asia/Bangkok',
    enable_utc=True,
    imports=['tasks'],  # Import tasks module
    beat_schedule={
        'fetch-attractions-daily': {
            'task': 'tasks.fetch_attractions_task',
            'schedule': crontab(hour=1, minute=0),  # Run at 1:00 AM daily
        },
        'geocode-attractions-daily': {
            'task': 'tasks.geocode_attractions_task',
            'schedule': crontab(hour=2, minute=0),  # Run at 2:00 AM daily (after sync)
        },
        'backup-database-daily': {
            'task': 'tasks.backup_database_task',
            'schedule': crontab(hour=0, minute=30),  # Run at 12:30 AM daily (before sync)
        },
        'cleanup-old-versions-weekly': {
            'task': 'tasks.cleanup_old_versions_task',
            'schedule': crontab(hour=3, minute=0, day_of_week=0),  # Run at 3:00 AM every Sunday
        },
    },
)

if __name__ == '__main__':
    # Start celery beat scheduler
    celery_app.start()