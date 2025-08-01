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
    
    # Register blueprints
    from app.routes.attractions import attractions_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.ai_features import ai_bp
    from app.routes.behavior_intelligence import behavior_bp
    app.register_blueprint(attractions_bp, url_prefix='/api')
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(ai_bp, url_prefix='/api/ai')
    app.register_blueprint(behavior_bp, url_prefix='/api')
    
    # Add a simple root route
    @app.route('/')
    def index():
        return {
            'message': 'Painaidee Database API with User Behavior Intelligence',
            'version': '1.0.0',
            'endpoints': {
                'health': '/api/health',
                'attractions': '/api/attractions',
                'sync': '/api/attractions/sync',
                'dashboard': '/api/dashboard',
                'ai_features': {
                    'keywords': '/api/ai/keywords',
                    'recommendations': '/api/ai/recommendations',
                    'trends': '/api/ai/trends',
                    'content': '/api/ai/content'
                },
                'behavior_intelligence': {
                    'track': '/api/behavior/track',
                    'analyze': '/api/behavior/analyze/<user_id>',
                    'recommendations': '/api/behavior/recommendations/<user_id>',
                    'trends': '/api/behavior/trends',
                    'heatmap': '/api/behavior/heatmap',
                    'predictions': '/api/behavior/predictions',
                    'sessions': '/api/behavior/sessions/<user_id>',
                    'preferences': '/api/behavior/preferences/<user_id>',
                    'search_queries': '/api/behavior/search-queries/<user_id>',
                    'stats': '/api/behavior/stats'
                }
            }
        }
    
    # Create tables
    with app.app_context():
        db.create_all()
    
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