"""
Attraction data loader.
Handles duplicate checking, database insertion, and versioning.
"""
import logging
from typing import List, Dict, Any
from sqlalchemy.exc import IntegrityError
from app.models import db, Attraction
from app.services.versioning import VersioningService

logger = logging.getLogger(__name__)


class AttractionLoader:
    """Loader for attraction data with duplicate checking and versioning."""
    
    @staticmethod
    def load_attractions(attractions: List[Attraction]) -> Dict[str, int]:
        """
        Load attractions into the database with duplicate checking and versioning.
        
        Args:
            attractions: List of Attraction objects to load
            
        Returns:
            Dictionary with counts of saved, updated, and skipped items
        """
        logger.info(f"Loading {len(attractions)} attractions to database")
        
        saved_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0
        
        for attraction in attractions:
            try:
                # Check if attraction already exists
                existing = Attraction.query.filter_by(external_id=attraction.external_id).first()
                
                if existing:
                    # Check if data has changed
                    if AttractionLoader._has_data_changed(existing, attraction):
                        # Archive current version before updating
                        VersioningService.archive_attraction_version(existing)
                        
                        # Update existing attraction
                        AttractionLoader._update_attraction(existing, attraction)
                        db.session.commit()
                        updated_count += 1
                        logger.debug(f"Updated attraction with external_id: {attraction.external_id}")
                    else:
                        skipped_count += 1
                        logger.debug(f"No changes for attraction with external_id: {attraction.external_id}")
                else:
                    # Save new attraction
                    db.session.add(attraction)
                    db.session.commit()
                    saved_count += 1
                    logger.debug(f"Saved new attraction with external_id: {attraction.external_id}")
                
            except IntegrityError:
                db.session.rollback()
                skipped_count += 1
                logger.warning(f"Duplicate attraction with external_id: {attraction.external_id}")
            except Exception as e:
                db.session.rollback()
                error_count += 1
                logger.error(f"Error processing attraction {attraction.external_id}: {str(e)}")
        
        result = {
            'saved': saved_count,
            'updated': updated_count,
            'skipped': skipped_count,
            'errors': error_count,
            'total_processed': len(attractions)
        }
        
        logger.info(f"Loading completed: {result}")
        return result
    
    @staticmethod
    def _has_data_changed(existing: Attraction, new: Attraction) -> bool:
        """
        Check if attraction data has changed.
        
        Args:
            existing: Existing attraction from database
            new: New attraction data
            
        Returns:
            True if data has changed, False otherwise
        """
        return (
            existing.title != new.title or
            existing.body != new.body or
            existing.user_id != new.user_id or
            existing.province != new.province or
            (existing.latitude != new.latitude if new.latitude is not None else False) or
            (existing.longitude != new.longitude if new.longitude is not None else False)
        )
    
    @staticmethod
    def _update_attraction(existing: Attraction, new: Attraction) -> None:
        """
        Update existing attraction with new data.
        
        Args:
            existing: Existing attraction to update
            new: New attraction data
        """
        existing.title = new.title
        existing.body = new.body
        existing.user_id = new.user_id
        existing.province = new.province
        
        # Only update coordinates if new ones are provided
        if new.latitude is not None:
            existing.latitude = new.latitude
        if new.longitude is not None:
            existing.longitude = new.longitude
        if new.geocoded is not None:
            existing.geocoded = new.geocoded
    
    @staticmethod
    def check_duplicate(external_id: int) -> bool:
        """
        Check if an attraction with the given external_id already exists.
        
        Args:
            external_id: The external ID to check
            
        Returns:
            True if duplicate exists, False otherwise
        """
        existing = Attraction.query.filter_by(external_id=external_id).first()
        return existing is not None
    
    @staticmethod
    def bulk_load_attractions(attractions: List[Attraction], batch_size: int = 100) -> Dict[str, int]:
        """
        Load attractions in batches for better performance with large datasets.
        
        Args:
            attractions: List of Attraction objects to load
            batch_size: Number of items to process in each batch
            
        Returns:
            Dictionary with counts of saved, updated, and skipped items
        """
        logger.info(f"Bulk loading {len(attractions)} attractions in batches of {batch_size}")
        
        total_saved = 0
        total_updated = 0
        total_skipped = 0
        total_errors = 0
        
        for i in range(0, len(attractions), batch_size):
            batch = attractions[i:i + batch_size]
            logger.debug(f"Processing batch {i//batch_size + 1}: items {i} to {i + len(batch) - 1}")
            
            result = AttractionLoader.load_attractions(batch)
            total_saved += result['saved']
            total_updated += result.get('updated', 0)
            total_skipped += result['skipped']
            total_errors += result.get('errors', 0)
        
        final_result = {
            'saved': total_saved,
            'updated': total_updated,
            'skipped': total_skipped,
            'errors': total_errors,
            'total_processed': len(attractions)
        }
        
        logger.info(f"Bulk loading completed: {final_result}")
        return final_result