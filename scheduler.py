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
        # AI-related scheduled tasks
        'extract-keywords-daily': {
            'task': 'tasks.extract_keywords_batch_task',
            'schedule': crontab(hour=4, minute=0),  # Run at 4:00 AM daily
            'kwargs': {'limit': 50}  # Process max 50 attractions per day
        },
        'improve-content-weekly': {
            'task': 'tasks.improve_content_batch_task',
            'schedule': crontab(hour=5, minute=0, day_of_week=1),  # Run at 5:00 AM every Monday
            'kwargs': {'limit': 20, 'style': 'friendly'}  # Process max 20 attractions per week
        },
        'cleanup-old-interactions-monthly': {
            'task': 'tasks.cleanup_old_interactions_task',
            'schedule': crontab(hour=6, minute=0, day=1),  # Run on the 1st day of each month at 6:00 AM
            'kwargs': {'days': 90}  # Keep interactions for 90 days
        },
    },
)

if __name__ == '__main__':
    # Start celery beat scheduler
    celery_app.start()