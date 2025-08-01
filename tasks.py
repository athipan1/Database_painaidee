import logging
from datetime import datetime, date
from sqlalchemy import or_
from app import create_app, create_celery_app
from etl_orchestrator import ETLOrchestrator
from app.services.backup import get_backup_service
from app.services.geocoding import get_geocoding_service
from app.models import db, SyncStatistics
import requests
import time

# Create Flask and Celery apps
app = create_app()
celery = create_celery_app(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@celery.task(bind=True)
def fetch_attractions_task(self):
    """Background task to fetch attractions from external API using ETL pipeline."""
    start_time = time.time()
    
    try:
        with app.app_context():
            # Get configuration
            api_url = app.config['EXTERNAL_API_URL']
            timeout = app.config['API_TIMEOUT']
            auto_backup = app.config.get('AUTO_BACKUP_BEFORE_SYNC', True)
            
            # Create pre-sync backup if enabled
            if auto_backup:
                logger.info("Creating pre-sync backup...")
                backup_service = get_backup_service(app.config['SQLALCHEMY_DATABASE_URI'])
                if backup_service:
                    backup_path = backup_service.create_pre_sync_backup()
                    if backup_path:
                        logger.info(f"Pre-sync backup created: {backup_path}")
                    else:
                        logger.warning("Failed to create pre-sync backup, continuing with sync...")
            
            # Get pagination settings
            enable_pagination = app.config.get('PAGINATION_ENABLED', True)
            page_size = app.config.get('PAGINATION_PAGE_SIZE', 20)
            max_pages = app.config.get('PAGINATION_MAX_PAGES', 100)
            
            logger.info(f"Starting ETL process for external API: {api_url}")
            logger.info(f"Pagination settings: enabled={enable_pagination}, page_size={page_size}, max_pages={max_pages}")
            
            # Get geocoding settings
            enable_geocoding = app.config.get('USE_GOOGLE_GEOCODING', False)
            google_api_key = app.config.get('GOOGLE_GEOCODING_API_KEY')
            
            # Run ETL process using orchestrator with pagination and geocoding
            result = ETLOrchestrator.run_external_api_etl(
                api_url=api_url,
                timeout=timeout,
                enable_pagination=enable_pagination,
                page_size=page_size,
                max_pages=max_pages,
                use_memory_efficient=enable_pagination,  # Use memory efficient mode when pagination is enabled
                enable_geocoding=enable_geocoding,
                google_api_key=google_api_key
            )
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Calculate success rate
            total_processed = result.get('total_processed', 0)
            errors = result.get('errors', 0)  # Add this to ETL result if not present
            success_rate = ((total_processed - errors) / total_processed * 100) if total_processed > 0 else 0
            
            # Save sync statistics
            try:
                sync_stat = SyncStatistics(
                    sync_date=date.today(),
                    total_processed=total_processed,
                    total_saved=result.get('saved', 0),
                    total_skipped=result.get('skipped', 0),
                    total_errors=errors,
                    success_rate=round(success_rate, 2),
                    processing_time_seconds=round(processing_time, 2),
                    api_source=api_url
                )
                db.session.add(sync_stat)
                db.session.commit()
                logger.info(f"Sync statistics saved: {sync_stat.to_dict()}")
            except Exception as e:
                logger.error(f"Failed to save sync statistics: {str(e)}")
            
            result['processing_time_seconds'] = round(processing_time, 2)
            result['success_rate'] = round(success_rate, 2)
            
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
def geocode_attractions_task():
    """Background task to geocode attractions that don't have coordinates."""
    try:
        with app.app_context():
            from app.models import Attraction
            
            # Get configuration
            google_api_key = app.config.get('GOOGLE_GEOCODING_API_KEY')
            use_google = app.config.get('USE_GOOGLE_GEOCODING', True)
            
            # Initialize geocoding service
            geocoding_service = get_geocoding_service(google_api_key, use_google)
            
            # Find attractions without coordinates
            attractions_to_geocode = Attraction.query.filter(
                Attraction.latitude.is_(None),
                Attraction.longitude.is_(None),
                Attraction.geocoded == False
            ).limit(50).all()  # Process in batches of 50
            
            logger.info(f"Found {len(attractions_to_geocode)} attractions to geocode")
            
            geocoded_count = 0
            failed_count = 0
            
            for attraction in attractions_to_geocode:
                try:
                    # Attempt geocoding
                    location_data = geocoding_service.geocode(
                        attraction.title, 
                        attraction.province
                    )
                    
                    if location_data:
                        attraction.latitude = location_data['latitude']
                        attraction.longitude = location_data['longitude']
                        attraction.geocoded = True
                        geocoded_count += 1
                        logger.info(f"Geocoded attraction {attraction.id}: {attraction.title}")
                    else:
                        attraction.geocoded = False  # Mark as attempted but failed
                        failed_count += 1
                        logger.warning(f"Failed to geocode attraction {attraction.id}: {attraction.title}")
                    
                    db.session.commit()
                    
                    # Add delay to respect API rate limits
                    time.sleep(1.1)  # Slightly over 1 second
                    
                except Exception as e:
                    logger.error(f"Error geocoding attraction {attraction.id}: {str(e)}")
                    failed_count += 1
                    continue
            
            result = {
                'total_processed': len(attractions_to_geocode),
                'geocoded_count': geocoded_count,
                'failed_count': failed_count
            }
            
            logger.info(f"Geocoding task completed: {result}")
            return result
            
    except Exception as e:
        logger.error(f"Error in geocode_attractions_task: {str(e)}")
        raise


@celery.task
def backup_database_task():
    """Background task to create database backup."""
    try:
        with app.app_context():
            backup_service = get_backup_service(
                app.config['SQLALCHEMY_DATABASE_URI'],
                app.config.get('BACKUP_DIR', '/tmp/db_backups')
            )
            
            backup_path = backup_service.create_backup()
            
            if backup_path:
                # Cleanup old backups
                retention_days = app.config.get('BACKUP_RETENTION_DAYS', 7)
                deleted_count = backup_service.cleanup_old_backups(retention_days)
                
                result = {
                    'backup_path': backup_path,
                    'deleted_old_backups': deleted_count,
                    'status': 'success'
                }
                logger.info(f"Backup task completed: {result}")
                return result
            else:
                raise Exception("Failed to create backup")
                
    except Exception as e:
        logger.error(f"Error in backup_database_task: {str(e)}")
        raise


@celery.task
def cleanup_old_versions_task():
    """Background task to cleanup old attraction versions."""
    try:
        with app.app_context():
            from app.services.versioning import VersioningService
            from app.models import Attraction
            
            # Get all attractions and cleanup their old versions
            attractions = Attraction.query.all()
            total_deleted = 0
            
            for attraction in attractions:
                deleted = VersioningService.cleanup_old_versions(
                    attraction.id, 
                    keep_versions=10  # Keep last 10 versions
                )
                total_deleted += deleted
            
            result = {
                'attractions_processed': len(attractions),
                'versions_deleted': total_deleted,
                'status': 'success'
            }
            
            logger.info(f"Cleanup task completed: {result}")
            return result
            
    except Exception as e:
        logger.error(f"Error in cleanup_old_versions_task: {str(e)}")
        raise


@celery.task
def process_attractions_ai_task():
    """Background task to process attractions with AI features."""
    try:
        with app.app_context():
            from app.models import Attraction
            from app.services.ai_service import get_ai_service
            from app.services.cache_service import CacheService
            
            # Get configuration
            batch_size = app.config.get('AI_BATCH_SIZE', 50)
            ai_enabled = app.config.get('AI_PROCESSING_ENABLED', True)
            
            if not ai_enabled:
                logger.info("AI processing is disabled")
                return {'status': 'disabled'}
            
            # Find attractions that need AI processing
            attractions_to_process = Attraction.query.filter(
                Attraction.ai_processed == False,
                Attraction.body.isnot(None)  # Only process attractions with descriptions
            ).limit(batch_size).all()
            
            logger.info(f"Found {len(attractions_to_process)} attractions to process with AI")
            
            ai_service = get_ai_service()
            processed_count = 0
            failed_count = 0
            
            for attraction in attractions_to_process:
                try:
                    # Prepare attraction data for AI processing
                    attraction_data = {
                        'title': attraction.title,
                        'body': attraction.body,
                        'user_id': attraction.user_id
                    }
                    
                    # Process with AI
                    processed_data = ai_service.process_attraction_ai(attraction_data)
                    
                    # Update attraction with AI results
                    attraction.ai_summary = processed_data.get('ai_summary')
                    attraction.ai_tags = processed_data.get('ai_tags')
                    attraction.popularity_score = processed_data.get('popularity_score', 0.0)
                    attraction.ai_processed = True
                    
                    # Generate search vector
                    attraction.search_vector = ai_service.generate_search_vector(
                        attraction.title, attraction.body, attraction.ai_summary
                    )
                    
                    db.session.commit()
                    processed_count += 1
                    
                    logger.info(f"AI processed attraction {attraction.id}: {attraction.title}")
                    
                except Exception as e:
                    logger.error(f"Error processing attraction {attraction.id} with AI: {str(e)}")
                    failed_count += 1
                    db.session.rollback()
                    continue
            
            # Invalidate cache for updated attractions
            CacheService.invalidate_attraction_cache()
            
            result = {
                'total_processed': len(attractions_to_process),
                'success_count': processed_count,
                'failed_count': failed_count,
                'status': 'completed'
            }
            
            logger.info(f"AI processing task completed: {result}")
            return result
            
    except Exception as e:
        logger.error(f"Error in AI processing task: {str(e)}")
        raise


@celery.task
def preload_cache_task():
    """Background task to preload frequently accessed data into cache."""
    try:
        with app.app_context():
            from app.services.cache_service import CacheService
            
            logger.info("Starting cache preload task")
            
            # Preload popular data
            CacheService.preload_popular_data()
            
            result = {
                'status': 'completed',
                'message': 'Cache preloaded successfully'
            }
            
            logger.info(f"Cache preload task completed: {result}")
            return result
            
    except Exception as e:
        logger.error(f"Error in cache preload task: {str(e)}")
        raise


@celery.task
def update_search_vectors_task():
    """Background task to update search vectors for attractions."""
    try:
        with app.app_context():
            from app.models import Attraction
            from app.services.ai_service import get_ai_service
            
            # Find attractions that need search vector updates
            attractions_to_update = Attraction.query.filter(
                or_(
                    Attraction.search_vector.is_(None),
                    Attraction.search_vector == ''
                )
            ).limit(100).all()
            
            logger.info(f"Found {len(attractions_to_update)} attractions to update search vectors")
            
            ai_service = get_ai_service()
            updated_count = 0
            
            for attraction in attractions_to_update:
                try:
                    # Generate search vector
                    attraction.search_vector = ai_service.generate_search_vector(
                        attraction.title, 
                        attraction.body or '', 
                        attraction.ai_summary or ''
                    )
                    
                    db.session.commit()
                    updated_count += 1
                    
                except Exception as e:
                    logger.error(f"Error updating search vector for attraction {attraction.id}: {str(e)}")
                    db.session.rollback()
                    continue
            
            result = {
                'total_processed': len(attractions_to_update),
                'updated_count': updated_count,
                'status': 'completed'
            }
            
            logger.info(f"Search vector update task completed: {result}")
            return result
            
    except Exception as e:
        logger.error(f"Error in search vector update task: {str(e)}")
        raise


@celery.task
def test_task():
    """Simple test task."""
    logger.info("Test task executed successfully")
    return "Task completed successfully"


if __name__ == '__main__':
    # Start celery worker
    celery.start()