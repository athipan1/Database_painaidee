"""
Attraction data transformer.
Transforms raw API data into database-ready format.
"""
import logging
from typing import List, Dict, Any
from app.models import Attraction

logger = logging.getLogger(__name__)


class AttractionTransformer:
    """Transformer for attraction data from various sources."""
    
    @staticmethod
    def transform_external_api_data(raw_data: List[Dict[str, Any]]) -> List[Attraction]:
        """
        Transform raw external API data into Attraction objects.
        
        Args:
            raw_data: List of raw data items from external API
            
        Returns:
            List of Attraction objects ready for database insertion
        """
        logger.info(f"Transforming {len(raw_data)} external API items")
        
        attractions = []
        for item in raw_data:
            try:
                attraction = Attraction.create_from_external_data(item)
                attractions.append(attraction)
            except Exception as e:
                logger.warning(f"Failed to transform item {item.get('id', 'unknown')}: {e}")
                continue
        
        logger.info(f"Successfully transformed {len(attractions)} attractions")
        return attractions
    
    @staticmethod
    def transform_tourism_thailand_data(raw_data: List[Dict[str, Any]]) -> List[Attraction]:
        """
        Transform raw Tourism Thailand API data into Attraction objects.
        
        Args:
            raw_data: List of raw tourism data items
            
        Returns:
            List of Attraction objects ready for database insertion
        """
        logger.info(f"Transforming {len(raw_data)} tourism Thailand items")
        
        attractions = []
        for item in raw_data:
            try:
                # TODO: Implement specific transformation logic for Tourism Thailand data
                # This is a placeholder that should be customized based on the actual API response format
                transformed_item = {
                    'id': item.get('id'),
                    'title': item.get('name') or item.get('title'),
                    'body': item.get('description') or item.get('body'),
                    'userId': item.get('location_id') or item.get('userId', 1)
                }
                attraction = Attraction.create_from_external_data(transformed_item)
                attractions.append(attraction)
            except Exception as e:
                logger.warning(f"Failed to transform tourism item {item.get('id', 'unknown')}: {e}")
                continue
        
        logger.info(f"Successfully transformed {len(attractions)} tourism attractions")
        return attractions
    
    @staticmethod
    def transform_opentripmap_data(raw_data: List[Dict[str, Any]]) -> List[Attraction]:
        """
        Transform raw OpenTripMap API data into Attraction objects.
        
        Args:
            raw_data: List of raw place data items
            
        Returns:
            List of Attraction objects ready for database insertion
        """
        logger.info(f"Transforming {len(raw_data)} OpenTripMap items")
        
        attractions = []
        for item in raw_data:
            try:
                # TODO: Implement specific transformation logic for OpenTripMap data
                # This is a placeholder that should be customized based on the actual API response format
                transformed_item = {
                    'id': item.get('xid') or item.get('id'),
                    'title': item.get('name') or item.get('title'),
                    'body': item.get('wikipedia_extracts', {}).get('text') or item.get('body'),
                    'userId': item.get('point', {}).get('lon', 1)  # Use longitude as temporary user_id
                }
                attraction = Attraction.create_from_external_data(transformed_item)
                attractions.append(attraction)
            except Exception as e:
                logger.warning(f"Failed to transform OpenTripMap item {item.get('xid', 'unknown')}: {e}")
                continue
        
        logger.info(f"Successfully transformed {len(attractions)} OpenTripMap attractions")
        return attractions