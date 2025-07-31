"""
Attraction data loader.
Handles duplicate checking and database insertion with enhanced features.
"""
import logging
from typing import List, Dict, Any
from sqlalchemy.exc import IntegrityError
from app.models import db, Attraction, SyncLog
from app.utils.cache import cache_manager

logger = logging.getLogger(__name__)


class AttractionLoader:
    """Enhanced loader for attraction data with multiple duplicate checking methods."""
    
    @staticmethod
    def load_attractions(attractions: List[Attraction], sync_log: SyncLog = None) -> Dict[str, int]:
        """
        Load attractions into the database with enhanced duplicate checking.
        
        Args:
            attractions: List of Attraction objects to load
            sync_log: Optional sync log for tracking progress
            
        Returns:
            Dictionary with counts of saved and skipped items
        """
        logger.info(f"Loading {len(attractions)} attractions to database")
        
        saved_count = 0
        skipped_count = 0
        errors = []
        
        for attraction in attractions:
            try:
                # Enhanced duplicate checking: check both external_id and content_hash
                existing_by_id = None
                existing_by_hash = None
                
                if attraction.external_id:
                    existing_by_id = Attraction.find_duplicate_by_external_id(attraction.external_id)
                
                if attraction.content_hash:
                    existing_by_hash = Attraction.find_duplicate_by_hash(attraction.content_hash)
                
                # Skip if duplicate found by either method
                if existing_by_id or existing_by_hash:
                    skipped_count += 1
                    duplicate_type = "external_id" if existing_by_id else "content_hash"
                    logger.debug(f"Skipping duplicate attraction (by {duplicate_type}): {attraction.external_id}")
                    continue
                
                # Save new attraction
                db.session.add(attraction)
                db.session.commit()
                saved_count += 1
                
                # Update sync progress cache if provided
                if sync_log:
                    progress_data = {
                        'processed': saved_count + skipped_count,
                        'saved': saved_count,
                        'skipped': skipped_count,
                        'last_processed_id': attraction.external_id
                    }
                    cache_manager.cache_sync_progress(str(sync_log.id), progress_data)
                
            except IntegrityError as e:
                db.session.rollback()
                skipped_count += 1
                error_msg = f"Integrity error for attraction {attraction.external_id}: {str(e)}"
                logger.warning(error_msg)
                errors.append(error_msg)
                
            except Exception as e:
                db.session.rollback()
                skipped_count += 1
                error_msg = f"Error saving attraction {attraction.external_id}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        result = {
            'saved': saved_count,
            'skipped': skipped_count,
            'total_processed': len(attractions),
            'errors': errors
        }
        
        logger.info(f"Loading completed: {result}")
        return result
    
    @staticmethod
    def check_duplicate_by_external_id(external_id: int) -> bool:
        """
        Check if an attraction with the given external_id already exists.
        
        Args:
            external_id: The external ID to check
            
        Returns:
            True if duplicate exists, False otherwise
        """
        return Attraction.find_duplicate_by_external_id(external_id) is not None
    
    @staticmethod
    def check_duplicate_by_hash(content_hash: str) -> bool:
        """
        Check if an attraction with the given content hash already exists.
        
        Args:
            content_hash: The content hash to check
            
        Returns:
            True if duplicate exists, False otherwise
        """
        return Attraction.find_duplicate_by_hash(content_hash) is not None
    
    @staticmethod
    def bulk_load_attractions(attractions: List[Attraction], batch_size: int = 100, sync_log: SyncLog = None) -> Dict[str, int]:
        """
        Load attractions in batches for better performance with large datasets.
        
        Args:
            attractions: List of Attraction objects to load
            batch_size: Number of items to process in each batch
            sync_log: Optional sync log for tracking progress
            
        Returns:
            Dictionary with counts of saved and skipped items
        """
        logger.info(f"Bulk loading {len(attractions)} attractions in batches of {batch_size}")
        
        total_saved = 0
        total_skipped = 0
        all_errors = []
        
        for i in range(0, len(attractions), batch_size):
            batch = attractions[i:i + batch_size]
            logger.debug(f"Processing batch {i//batch_size + 1}: items {i} to {i + len(batch) - 1}")
            
            result = AttractionLoader.load_attractions(batch, sync_log)
            total_saved += result['saved']
            total_skipped += result['skipped']
            all_errors.extend(result.get('errors', []))
        
        final_result = {
            'saved': total_saved,
            'skipped': total_skipped,  
            'total_processed': len(attractions),
            'errors': all_errors
        }
        
        logger.info(f"Bulk loading completed: {final_result}")
        return final_result