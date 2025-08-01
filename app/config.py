import os
from datetime import timedelta


class Config:
    """Base configuration class."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://user:password@localhost:5432/painaidee_db'
    
    # Redis
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    
    # Celery
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL') or 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND') or 'redis://localhost:6379/0'
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_TIMEZONE = 'Asia/Bangkok'
    CELERY_ENABLE_UTC = True
    
    # External API
    EXTERNAL_API_URL = os.environ.get('EXTERNAL_API_URL') or 'https://jsonplaceholder.typicode.com/posts'
    API_TIMEOUT = int(os.environ.get('API_TIMEOUT', 30))
    
    # Pagination settings
    PAGINATION_ENABLED = os.environ.get('PAGINATION_ENABLED', 'true').lower() == 'true'
    PAGINATION_PAGE_SIZE = int(os.environ.get('PAGINATION_PAGE_SIZE', 20))
    PAGINATION_MAX_PAGES = int(os.environ.get('PAGINATION_MAX_PAGES', 100))  # Safety limit
    
    # Geocoding settings
    GOOGLE_GEOCODING_API_KEY = os.environ.get('GOOGLE_GEOCODING_API_KEY')
    USE_GOOGLE_GEOCODING = os.environ.get('USE_GOOGLE_GEOCODING', 'true').lower() == 'true'
    GEOCODING_TIMEOUT = int(os.environ.get('GEOCODING_TIMEOUT', 10))
    
    # Backup settings
    BACKUP_DIR = os.environ.get('BACKUP_DIR', '/tmp/db_backups')
    BACKUP_RETENTION_DAYS = int(os.environ.get('BACKUP_RETENTION_DAYS', 7))
    AUTO_BACKUP_BEFORE_SYNC = os.environ.get('AUTO_BACKUP_BEFORE_SYNC', 'true').lower() == 'true'


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}