import logging
from app import create_app, create_celery_app
from app.models import db, Attraction
from app.utils.fetch import fetch_json_with_retry
from sqlalchemy.exc import IntegrityError
import requests

# Create Flask and Celery apps
app = create_app()
celery = create_celery_app(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@celery.task(bind=True)
def fetch_attractions_task(self):
    """Background task to fetch attractions from external API."""
    try:
        with app.app_context():
            # Fetch data from external API using retry mechanism
            api_url = app.config['EXTERNAL_API_URL']
            timeout = app.config['API_TIMEOUT']
            
            logger.info(f"Fetching data from: {api_url}")
            external_data = fetch_json_with_retry(api_url, timeout=timeout)
            logger.info(f"Fetched {len(external_data)} items from external API")
            
            # Process and save data
            saved_count = 0
            skipped_count = 0
            
            for item in external_data:
                try:
                    # Check if attraction already exists
                    existing = Attraction.query.filter_by(external_id=item.get('id')).first()
                    
                    if existing:
                        skipped_count += 1
                        continue
                    
                    # Create new attraction
                    attraction = Attraction.create_from_external_data(item)
                    db.session.add(attraction)
                    db.session.commit()
                    saved_count += 1
                    
                except IntegrityError:
                    db.session.rollback()
                    skipped_count += 1
                    logger.warning(f"Duplicate attraction with external_id: {item.get('id')}")
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"Error processing item {item.get('id')}: {str(e)}")
                    skipped_count += 1
            
            result = {
                'saved': saved_count,
                'skipped': skipped_count,
                'total_processed': len(external_data)
            }
            
            logger.info(f"Task completed: {result}")
            return result
            
    except requests.RequestException as e:
        logger.error(f"Error fetching external data after retries: {str(e)}")
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