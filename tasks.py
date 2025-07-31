import logging
from app import create_app, create_celery_app
from etl_orchestrator import ETLOrchestrator
import requests

# Create Flask and Celery apps
app = create_app()
celery = create_celery_app(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@celery.task(bind=True)
def fetch_attractions_task(self):
    """Background task to fetch attractions from external API using ETL pipeline."""
    try:
        with app.app_context():
            # Get configuration
            api_url = app.config['EXTERNAL_API_URL']
            timeout = app.config['API_TIMEOUT']
            
            logger.info(f"Starting ETL process for external API: {api_url}")
            
            # Run ETL process using orchestrator
            result = ETLOrchestrator.run_external_api_etl(api_url, timeout)
            
            logger.info(f"ETL task completed: {result}")
            return result
            
    except requests.RequestException as e:
        logger.error(f"Error in ETL process after retries: {str(e)}")
        # The fetch_json_with_retry already handles retries, so if we get here,
        # all retries have been exhausted. We can still use Celery's retry as a fallback.
        raise self.retry(countdown=300, max_retries=2)  # Wait 5 minutes, try 2 more times
    except Exception as e:
        logger.error(f"Error in fetch_attractions_task: {str(e)}")
        raise


@celery.task
def test_task():
    """Simple test task."""
    logger.info("Test task executed successfully")
    return "Task completed successfully"


if __name__ == '__main__':
    # Start celery worker
    celery.start()