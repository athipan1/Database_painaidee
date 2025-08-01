import logging
from datetime import datetime, date
from app import create_app, create_celery_app
from etl_orchestrator import ETLOrchestrator
from app.services.backup import get_backup_service
from app.services.geocoding import get_geocoding_service
from app.services.keyword_extraction import extract_keywords_from_attraction, keywords_to_json
from app.services.recommendation import RecommendationEngine
from app.services.content_rewriter import improve_attraction_content
from app.services.data_validation import validate_batch_attractions
from app.services.auto_tagging import tag_batch_attractions
from app.services.category_suggestion import suggest_categories_batch
from app.models import db, SyncStatistics, Attraction
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
def test_task():
    """Simple test task."""
    logger.info("Test task executed successfully")
    return "Task completed successfully"


@celery.task(bind=True)
def extract_keywords_batch_task(self, attraction_ids=None, limit=None):
    """Background task to extract keywords for attractions."""
    try:
        with app.app_context():
            if attraction_ids:
                # Process specific attractions
                attractions = Attraction.query.filter(Attraction.id.in_(attraction_ids)).all()
            else:
                # Process attractions without keywords
                query = Attraction.query.filter_by(keywords_extracted=False)
                if limit:
                    query = query.limit(limit)
                attractions = query.all()
            
            processed = 0
            successful = 0
            failed = 0
            
            for attraction in attractions:
                try:
                    attraction_data = {
                        'title': attraction.title,
                        'body': attraction.body
                    }
                    
                    keywords = extract_keywords_from_attraction(attraction_data)
                    
                    if keywords:
                        attraction.keywords = keywords_to_json(keywords)
                        attraction.keywords_extracted = True
                        successful += 1
                    else:
                        attraction.keywords_extracted = True  # Mark as processed even if no keywords
                        
                    processed += 1
                    
                    # Commit in batches
                    if processed % 10 == 0:
                        db.session.commit()
                        logger.info(f"Processed {processed} attractions so far...")
                        
                except Exception as e:
                    logger.error(f"Error extracting keywords for attraction {attraction.id}: {str(e)}")
                    failed += 1
                    continue
            
            # Final commit
            db.session.commit()
            
            result = {
                'total_processed': processed,
                'successful': successful,
                'failed': failed
            }
            
            logger.info(f"Keyword extraction task completed: {result}")
            return result
            
    except Exception as e:
        logger.error(f"Error in extract_keywords_batch_task: {str(e)}")
        raise


@celery.task(bind=True)
def improve_content_batch_task(self, attraction_ids=None, field='body', style='friendly', limit=None):
    """Background task to improve content for attractions."""
    try:
        with app.app_context():
            if attraction_ids:
                # Process specific attractions
                attractions = Attraction.query.filter(Attraction.id.in_(attraction_ids)).all()
            else:
                # Process attractions without improved content
                query = Attraction.query.filter_by(content_rewritten=False)
                if limit:
                    query = query.limit(limit)
                attractions = query.all()
            
            processed = 0
            successful = 0
            failed = 0
            
            for attraction in attractions:
                try:
                    if field == 'title':
                        original_text = attraction.title
                    else:
                        original_text = attraction.body
                    
                    if not original_text:
                        processed += 1
                        continue
                    
                    result = improve_attraction_content(
                        text=original_text,
                        style=style,
                        max_length=500
                    )
                    
                    if result['success']:
                        if field == 'title':
                            attraction.title = result['improved_text']
                        else:
                            attraction.body = result['improved_text']
                        
                        attraction.content_rewritten = True
                        successful += 1
                    
                    processed += 1
                    
                    # Commit in batches
                    if processed % 10 == 0:
                        db.session.commit()
                        logger.info(f"Processed {processed} attractions so far...")
                        
                    # Add small delay to prevent overwhelming the system
                    time.sleep(0.1)
                        
                except Exception as e:
                    logger.error(f"Error improving content for attraction {attraction.id}: {str(e)}")
                    failed += 1
                    continue
            
            # Final commit
            db.session.commit()
            
            result = {
                'total_processed': processed,
                'successful': successful,
                'failed': failed,
                'field': field,
                'style': style
            }
            
            logger.info(f"Content improvement task completed: {result}")
            return result
            
    except Exception as e:
        logger.error(f"Error in improve_content_batch_task: {str(e)}")
        raise


@celery.task
def cleanup_old_interactions_task(days=90):
    """Background task to clean up old user interactions."""
    try:
        with app.app_context():
            from app.models import UserInteraction
            from datetime import datetime, timedelta
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Count interactions to delete
            old_interactions = UserInteraction.query.filter(
                UserInteraction.created_at < cutoff_date
            ).count()
            
            if old_interactions > 0:
                # Delete old interactions
                UserInteraction.query.filter(
                    UserInteraction.created_at < cutoff_date
                ).delete()
                
                db.session.commit()
                
                logger.info(f"Cleaned up {old_interactions} old user interactions (older than {days} days)")
                return {'deleted_interactions': old_interactions}
            else:
                logger.info("No old interactions to clean up")
                return {'deleted_interactions': 0}
                
    except Exception as e:
        logger.error(f"Error in cleanup_old_interactions_task: {str(e)}")
        raise


# New Data Cleaning & Enrichment Tasks

@celery.task(bind=True)
def validate_attractions_batch_task(self, attraction_ids=None, limit=50):
    """Background task to validate attraction data for quality issues."""
    try:
        with app.app_context():
            if attraction_ids:
                # Process specific attractions
                attractions = Attraction.query.filter(Attraction.id.in_(attraction_ids)).all()
                attraction_ids_to_process = [a.id for a in attractions]
            else:
                # Process attractions that haven't been validated
                query = Attraction.query.filter_by(data_validated=False)
                if limit:
                    query = query.limit(limit)
                attractions = query.all()
                attraction_ids_to_process = [a.id for a in attractions]
            
            if not attraction_ids_to_process:
                logger.info("No attractions to validate")
                return {'message': 'No attractions to validate'}
            
            # Use the batch validation service
            result = validate_batch_attractions(attraction_ids_to_process)
            
            logger.info(f"Data validation task completed: {result['processed']} processed, "
                       f"{result['successful']} successful, {result['failed']} failed")
            return result
            
    except Exception as e:
        logger.error(f"Error in validate_attractions_batch_task: {str(e)}")
        raise


@celery.task(bind=True)
def auto_tag_attractions_batch_task(self, attraction_ids=None, limit=50):
    """Background task to generate automatic tags for attractions."""
    try:
        with app.app_context():
            if attraction_ids:
                # Process specific attractions
                attractions = Attraction.query.filter(Attraction.id.in_(attraction_ids)).all()
                attraction_ids_to_process = [a.id for a in attractions]
            else:
                # Process attractions that haven't been auto-tagged
                query = Attraction.query.filter_by(auto_tagged=False)
                if limit:
                    query = query.limit(limit)
                attractions = query.all()
                attraction_ids_to_process = [a.id for a in attractions]
            
            if not attraction_ids_to_process:
                logger.info("No attractions to tag")
                return {'message': 'No attractions to tag'}
            
            # Use the batch tagging service
            result = tag_batch_attractions(attraction_ids_to_process)
            
            logger.info(f"Auto-tagging task completed: {result['processed']} processed, "
                       f"{result['successful']} successful, {result['failed']} failed, "
                       f"{result['total_tags_generated']} total tags generated")
            return result
            
    except Exception as e:
        logger.error(f"Error in auto_tag_attractions_batch_task: {str(e)}")
        raise


@celery.task(bind=True)
def categorize_attractions_batch_task(self, attraction_ids=None, limit=50):
    """Background task to generate category suggestions for attractions."""
    try:
        with app.app_context():
            if attraction_ids:
                # Process specific attractions
                attractions = Attraction.query.filter(Attraction.id.in_(attraction_ids)).all()
                attraction_ids_to_process = [a.id for a in attractions]
            else:
                # Process attractions that haven't been categorized
                query = Attraction.query.filter_by(categorized=False)
                if limit:
                    query = query.limit(limit)
                attractions = query.all()
                attraction_ids_to_process = [a.id for a in attractions]
            
            if not attraction_ids_to_process:
                logger.info("No attractions to categorize")
                return {'message': 'No attractions to categorize'}
            
            # Use the batch categorization service
            result = suggest_categories_batch(attraction_ids_to_process)
            
            logger.info(f"Categorization task completed: {result['processed']} processed, "
                       f"{result['successful']} successful, {result['failed']} failed, "
                       f"{result['total_categories_suggested']} total categories suggested")
            return result
            
    except Exception as e:
        logger.error(f"Error in categorize_attractions_batch_task: {str(e)}")
        raise


@celery.task(bind=True)
def full_data_cleaning_task(self, attraction_ids=None, limit=20, config=None):
    """
    Comprehensive data cleaning task that performs validation, tagging, 
    categorization, and geocoding.
    """
    try:
        with app.app_context():
            # Default configuration
            default_config = {
                'enable_validation': True,
                'enable_tagging': True,
                'enable_categorization': True,
                'enable_geocoding': True,
                'validation_limit': limit,
                'tagging_limit': limit,
                'categorization_limit': limit
            }
            
            if config:
                default_config.update(config)
            config = default_config
            
            # Get attractions to process
            if attraction_ids:
                attractions = Attraction.query.filter(Attraction.id.in_(attraction_ids)).all()
                attraction_ids_to_process = [a.id for a in attractions]
            else:
                # Get attractions that need cleaning (prioritize by update date)
                query = Attraction.query.filter(
                    db.or_(
                        Attraction.data_validated == False,
                        Attraction.auto_tagged == False,
                        Attraction.categorized == False,
                        Attraction.geocoded == False
                    )
                ).order_by(Attraction.updated_at.desc())
                
                if limit:
                    query = query.limit(limit)
                attractions = query.all()
                attraction_ids_to_process = [a.id for a in attractions]
            
            if not attraction_ids_to_process:
                logger.info("No attractions need cleaning")
                return {'message': 'No attractions need cleaning'}
            
            results = {
                'processed_attractions': len(attraction_ids_to_process),
                'validation_results': None,
                'tagging_results': None,
                'categorization_results': None,
                'geocoding_results': {'processed': 0, 'successful': 0}
            }
            
            # Step 1: Data Validation
            if config['enable_validation']:
                try:
                    logger.info("Starting data validation...")
                    # Filter attractions that need validation
                    validation_ids = [a.id for a in attractions if not a.data_validated]
                    if validation_ids:
                        validation_result = validate_batch_attractions(validation_ids[:config['validation_limit']])
                        results['validation_results'] = validation_result
                        logger.info(f"Validation completed: {validation_result['successful']} successful")
                except Exception as e:
                    logger.error(f"Error in validation step: {str(e)}")
                    results['validation_results'] = {'error': str(e)}
            
            # Step 2: Auto-Tagging
            if config['enable_tagging']:
                try:
                    logger.info("Starting auto-tagging...")
                    # Filter attractions that need tagging
                    tagging_ids = [a.id for a in attractions if not a.auto_tagged]
                    if tagging_ids:
                        tagging_result = tag_batch_attractions(tagging_ids[:config['tagging_limit']])
                        results['tagging_results'] = tagging_result
                        logger.info(f"Tagging completed: {tagging_result['successful']} successful, "
                                   f"{tagging_result['total_tags_generated']} tags generated")
                except Exception as e:
                    logger.error(f"Error in tagging step: {str(e)}")
                    results['tagging_results'] = {'error': str(e)}
            
            # Step 3: Category Suggestion
            if config['enable_categorization']:
                try:
                    logger.info("Starting categorization...")
                    # Filter attractions that need categorization
                    categorization_ids = [a.id for a in attractions if not a.categorized]
                    if categorization_ids:
                        categorization_result = suggest_categories_batch(categorization_ids[:config['categorization_limit']])
                        results['categorization_results'] = categorization_result
                        logger.info(f"Categorization completed: {categorization_result['successful']} successful, "
                                   f"{categorization_result['total_categories_suggested']} categories suggested")
                except Exception as e:
                    logger.error(f"Error in categorization step: {str(e)}")
                    results['categorization_results'] = {'error': str(e)}
            
            # Step 4: Geocoding (existing service)
            if config['enable_geocoding']:
                try:
                    logger.info("Starting geocoding...")
                    geocoding_service = get_geocoding_service()
                    if geocoding_service:
                        geocoded_count = 0
                        successful_geocoding = 0
                        
                        # Filter attractions that need geocoding
                        for attraction in attractions:
                            if not attraction.geocoded and (attraction.province or attraction.title):
                                geocoded_count += 1
                                try:
                                    success = geocoding_service.geocode_attraction(attraction.id)
                                    if success:
                                        successful_geocoding += 1
                                    
                                    # Add delay to respect API limits
                                    time.sleep(0.2)
                                except Exception as e:
                                    logger.error(f"Error geocoding attraction {attraction.id}: {str(e)}")
                                    continue
                        
                        results['geocoding_results'] = {
                            'processed': geocoded_count,
                            'successful': successful_geocoding
                        }
                        logger.info(f"Geocoding completed: {successful_geocoding}/{geocoded_count} successful")
                    else:
                        logger.warning("Geocoding service not available")
                        results['geocoding_results'] = {'error': 'Geocoding service not available'}
                        
                except Exception as e:
                    logger.error(f"Error in geocoding step: {str(e)}")
                    results['geocoding_results'] = {'error': str(e)}
            
            logger.info(f"Full data cleaning task completed for {len(attraction_ids_to_process)} attractions")
            return results
            
    except Exception as e:
        logger.error(f"Error in full_data_cleaning_task: {str(e)}")
        raise


@celery.task
def cleanup_old_validation_results_task(days=30):
    """Background task to clean up old validation results."""
    try:
        with app.app_context():
            from app.models import DataValidationResult
            from datetime import datetime, timedelta
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Count results to delete (only fixed/ignored ones)
            old_results = DataValidationResult.query.filter(
                DataValidationResult.created_at < cutoff_date,
                DataValidationResult.status.in_(['fixed', 'ignored'])
            ).count()
            
            if old_results > 0:
                # Delete old validation results
                DataValidationResult.query.filter(
                    DataValidationResult.created_at < cutoff_date,
                    DataValidationResult.status.in_(['fixed', 'ignored'])
                ).delete()
                
                db.session.commit()
                
                logger.info(f"Cleaned up {old_results} old validation results (older than {days} days)")
                return {'deleted_results': old_results}
            else:
                logger.info("No old validation results to clean up")
                return {'deleted_results': 0}
                
    except Exception as e:
        logger.error(f"Error in cleanup_old_validation_results_task: {str(e)}")
        raise


if __name__ == '__main__':
    # Start celery worker
    celery.start()