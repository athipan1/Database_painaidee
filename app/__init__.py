import os
from flask import Flask
from flask_migrate import Migrate
from dotenv import load_dotenv

from app.config import config
from app.models import db

# Load environment variables
load_dotenv()

migrate = Migrate()


def create_app(config_name=None):
    """Application factory pattern."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Initialize cache
    from app.services.cache_service import init_cache
    init_cache(app)
    
    # Register blueprints
    from app.routes.attractions import attractions_bp
    from app.routes.dashboard import dashboard_bp
    app.register_blueprint(attractions_bp, url_prefix='/api')
    app.register_blueprint(dashboard_bp)
    
    # Add a simple root route
    @app.route('/')
    def index():
        return {
            'message': 'Painaidee Database API',
            'version': '2.0.0',
            'features': [
                'AI-powered data enrichment',
                'Full-text search',
                'Recommendation system', 
                'Advanced caching',
                'Real-time dashboard'
            ],
            'endpoints': {
                'health': '/api/health',
                'attractions': '/api/attractions',
                'search': '/api/attractions/search',
                'recommendations': '/api/attractions/{id}/recommendations',
                'trending': '/api/attractions/trending',
                'sync': '/api/attractions/sync',
                'dashboard': '/api/dashboard'
            }
        }
    
    # Create tables and search indexes
    with app.app_context():
        db.create_all()
        
        # Create search indexes
        try:
            from app.services.search_service import SearchService
            SearchService.create_search_indexes()
        except Exception as e:
            app.logger.warning(f"Could not create search indexes: {str(e)}")
    
    return app


def create_celery_app(app=None):
    """Create Celery app."""
    app = app or create_app()
    
    from celery import Celery
    
    celery = Celery(
        app.import_name,
        broker=app.config['CELERY_BROKER_URL'],
        backend=app.config['CELERY_RESULT_BACKEND']
    )
    celery.conf.update(app.config)
    
    class ContextTask(celery.Task):
        """Make celery tasks work with Flask app context."""
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery