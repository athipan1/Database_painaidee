"""
Versioning service for managing attraction data history.
"""
import logging
from typing import Optional
from app.models import db, Attraction, AttractionHistory

logger = logging.getLogger(__name__)


class VersioningService:
    """Service for managing attraction data versioning."""
    
    @staticmethod
    def archive_attraction_version(attraction: Attraction) -> Optional[AttractionHistory]:
        """
        Archive current version of attraction before updating.
        
        Args:
            attraction: Attraction instance to archive
            
        Returns:
            AttractionHistory instance or None if failed
        """
        try:
            # Get next version number
            latest_version = db.session.query(
                db.func.max(AttractionHistory.version_number)
            ).filter(
                AttractionHistory.attraction_id == attraction.id
            ).scalar() or 0
            
            next_version = latest_version + 1
            
            # Create history record
            history = AttractionHistory(
                attraction_id=attraction.id,
                external_id=attraction.external_id,
                title=attraction.title,
                body=attraction.body,
                user_id=attraction.user_id,
                province=attraction.province,
                latitude=attraction.latitude,
                longitude=attraction.longitude,
                geocoded=attraction.geocoded,
                version_number=next_version
            )
            
            db.session.add(history)
            db.session.commit()
            
            logger.info(f"Archived attraction {attraction.id} as version {next_version}")
            return history
            
        except Exception as e:
            logger.error(f"Failed to archive attraction {attraction.id}: {str(e)}")
            db.session.rollback()
            return None
    
    @staticmethod
    def get_attraction_history(attraction_id: int, version_number: int = None) -> list:
        """
        Get history versions of an attraction.
        
        Args:
            attraction_id: ID of the attraction
            version_number: Specific version number (optional)
            
        Returns:
            List of AttractionHistory instances
        """
        query = AttractionHistory.query.filter(
            AttractionHistory.attraction_id == attraction_id
        )
        
        if version_number:
            query = query.filter(AttractionHistory.version_number == version_number)
        
        return query.order_by(AttractionHistory.version_number.desc()).all()
    
    @staticmethod
    def restore_attraction_version(attraction_id: int, version_number: int) -> bool:
        """
        Restore attraction to a specific version.
        
        Args:
            attraction_id: ID of the attraction
            version_number: Version number to restore
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the history record
            history = AttractionHistory.query.filter(
                AttractionHistory.attraction_id == attraction_id,
                AttractionHistory.version_number == version_number
            ).first()
            
            if not history:
                logger.error(f"History version {version_number} not found for attraction {attraction_id}")
                return False
            
            # Get current attraction
            attraction = Attraction.query.get(attraction_id)
            if not attraction:
                logger.error(f"Attraction {attraction_id} not found")
                return False
            
            # Archive current version before restoring
            VersioningService.archive_attraction_version(attraction)
            
            # Restore from history
            attraction.external_id = history.external_id
            attraction.title = history.title
            attraction.body = history.body
            attraction.user_id = history.user_id
            attraction.province = history.province
            attraction.latitude = history.latitude
            attraction.longitude = history.longitude
            attraction.geocoded = history.geocoded
            
            db.session.commit()
            
            logger.info(f"Restored attraction {attraction_id} to version {version_number}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore attraction {attraction_id} to version {version_number}: {str(e)}")
            db.session.rollback()
            return False
    
    @staticmethod
    def cleanup_old_versions(attraction_id: int, keep_versions: int = 10) -> int:
        """
        Clean up old versions, keeping only the specified number of recent versions.
        
        Args:
            attraction_id: ID of the attraction
            keep_versions: Number of versions to keep
            
        Returns:
            Number of versions deleted
        """
        try:
            # Get versions to delete (older than keep_versions)
            versions_to_delete = AttractionHistory.query.filter(
                AttractionHistory.attraction_id == attraction_id
            ).order_by(
                AttractionHistory.version_number.desc()
            ).offset(keep_versions).all()
            
            deleted_count = len(versions_to_delete)
            
            for version in versions_to_delete:
                db.session.delete(version)
            
            db.session.commit()
            
            logger.info(f"Deleted {deleted_count} old versions for attraction {attraction_id}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old versions for attraction {attraction_id}: {str(e)}")
            db.session.rollback()
            return 0