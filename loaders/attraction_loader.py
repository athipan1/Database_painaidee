"""
Attraction data loader.
Handles duplicate checking and database insertion.
"""
import logging
from typing import List, Dict, Any
from sqlalchemy.exc import IntegrityError
from app.models import db, Attraction

logger = logging.getLogger(__name__)


class AttractionLoader:
    """Loader for attraction data with duplicate checking."""
    
    @staticmethod
    def load_attractions(attractions: List[Attraction]) -> Dict[str, int]:
        """
        Load attractions into the database with duplicate checking.
        
        Args:
            attractions: List of Attraction objects to load
            
        Returns:
            Dictionary with counts of saved and skipped items
        """
        logger.info(f"Loading {len(attractions)} attractions to database")
        
        saved_count = 0
        skipped_count = 0
        
        for attraction in attractions:
            try:
                # Check if attraction already exists
                existing = Attraction.query.filter_by(external_id=attraction.external_id).first()
                
                if existing:
                    skipped_count += 1
                    logger.debug(f"Skipping duplicate attraction with external_id: {attraction.external_id}")
                    continue
                
                # Save new attraction
                db.session.add(attraction)
                db.session.commit()
                saved_count += 1
                
            except IntegrityError:
                db.session.rollback()
                skipped_count += 1
                logger.warning(f"Duplicate attraction with external_id: {attraction.external_id}")
            except Exception as e:
                db.session.rollback()
                skipped_count += 1
                logger.error(f"Error saving attraction {attraction.external_id}: {str(e)}")
        
        result = {
            'saved': saved_count,
            'skipped': skipped_count,
            'total_processed': len(attractions)
        }
        
        logger.info(f"Loading completed: {result}")
        return result
    
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
            Dictionary with counts of saved and skipped items
        """
        logger.info(f"Bulk loading {len(attractions)} attractions in batches of {batch_size}")
        
        total_saved = 0
        total_skipped = 0
        
        for i in range(0, len(attractions), batch_size):
            batch = attractions[i:i + batch_size]
            logger.debug(f"Processing batch {i//batch_size + 1}: items {i} to {i + len(batch) - 1}")
            
            result = AttractionLoader.load_attractions(batch)
            total_saved += result['saved']
            total_skipped += result['skipped']
        
        final_result = {
            'saved': total_saved,
            'skipped': total_skipped,
            'total_processed': len(attractions)
        }
        
        logger.info(f"Bulk loading completed: {final_result}")
        return final_result