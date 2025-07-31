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
            'schedule': crontab(hour=1, minute=0),  # Run at 1:00 AM daily for full sync
            'kwargs': {'sync_type': 'daily'}
        },
        'fetch-attractions-update': {
            'task': 'tasks.fetch_attractions_task', 
            'schedule': crontab(hour=13, minute=0),  # Run at 1:00 PM for update check
            'kwargs': {'sync_type': 'update'}
        },
    },
)

if __name__ == '__main__':
    # Start celery beat scheduler
    celery_app.start()