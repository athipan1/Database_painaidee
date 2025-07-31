"""
Enhanced attraction data transformer with data cleaning and normalization.
"""
import logging
from typing import List, Dict, Any
from app.models import Attraction
from app.utils.data_transform import DataTransformer

logger = logging.getLogger(__name__)


class AttractionTransformer:
    """Enhanced transformer for attraction data from various sources with data cleaning."""
    
    @staticmethod
    def transform_external_api_data(raw_data: List[Dict[str, Any]]) -> List[Attraction]:
        """
        Transform raw external API data into Attraction objects with enhanced data cleaning.
        
        Args:
            raw_data: List of raw data items from external API
            
        Returns:
            List of Attraction objects ready for database insertion
        """
        logger.info(f"Transforming {len(raw_data)} external API items with enhanced processing")
        
        attractions = []
        for item in raw_data:
            try:
                # Apply data transformations
                transformed_item = DataTransformer.transform_attraction_data(item)
                
                # Create attraction with transformed data
                attraction = Attraction(
                    external_id=transformed_item.get('id'),
                    title=transformed_item.get('title'),
                    body=transformed_item.get('body'),
                    user_id=transformed_item.get('userId'),
                    location_category=transformed_item.get('location_category'),
                    province=transformed_item.get('province'),
                    district=transformed_item.get('district'),
                    original_date=transformed_item.get('original_date'),
                    normalized_date=transformed_item.get('normalized_date')
                )
                
                # Generate content hash for duplicate detection
                attraction.content_hash = attraction.generate_content_hash()
                
                attractions.append(attraction)
                
            except Exception as e:
                logger.warning(f"Failed to transform item {item.get('id', 'unknown')}: {e}")
                continue
        
        logger.info(f"Successfully transformed {len(attractions)} attractions")
        return attractions
    
    @staticmethod
    def transform_tourism_thailand_data(raw_data: List[Dict[str, Any]]) -> List[Attraction]:
        """
        Transform raw Tourism Thailand API data into Attraction objects with enhanced processing.
        
        Args:
            raw_data: List of raw tourism data items
            
        Returns:
            List of Attraction objects ready for database insertion
        """
        logger.info(f"Transforming {len(raw_data)} tourism Thailand items with enhanced processing")
        
        attractions = []
        for item in raw_data:
            try:
                # Map Tourism Thailand fields to our standard format
                mapped_item = {
                    'id': item.get('id'),
                    'title': item.get('name') or item.get('title'),
                    'body': item.get('description') or item.get('body'),
                    'userId': item.get('location_id') or item.get('userId', 1),
                    'date': item.get('created_date') or item.get('date'),
                    'address': item.get('address') or item.get('location')
                }
                
                # Apply data transformations
                transformed_item = DataTransformer.transform_attraction_data(mapped_item)
                
                # Create attraction with transformed data
                attraction = Attraction(
                    external_id=transformed_item.get('id'),
                    title=transformed_item.get('title'),
                    body=transformed_item.get('body'),
                    user_id=transformed_item.get('userId'),
                    location_category=transformed_item.get('location_category'),
                    province=transformed_item.get('province'),
                    district=transformed_item.get('district'),
                    original_date=transformed_item.get('original_date'),
                    normalized_date=transformed_item.get('normalized_date')
                )
                
                # Generate content hash
                attraction.content_hash = attraction.generate_content_hash()
                
                attractions.append(attraction)
                
            except Exception as e:
                logger.warning(f"Failed to transform tourism item {item.get('id', 'unknown')}: {e}")
                continue
        
        logger.info(f"Successfully transformed {len(attractions)} tourism attractions")
        return attractions
    
    @staticmethod
    def transform_opentripmap_data(raw_data: List[Dict[str, Any]]) -> List[Attraction]:
        """
        Transform raw OpenTripMap API data into Attraction objects with enhanced processing.
        
        Args:
            raw_data: List of raw place data items
            
        Returns:
            List of Attraction objects ready for database insertion
        """
        logger.info(f"Transforming {len(raw_data)} OpenTripMap items with enhanced processing")
        
        attractions = []
        for item in raw_data:
            try:
                # Map OpenTripMap fields to our standard format
                mapped_item = {
                    'id': item.get('xid') or item.get('id'),
                    'title': item.get('name') or item.get('title'),
                    'body': item.get('wikipedia_extracts', {}).get('text') or item.get('body'),
                    'userId': item.get('point', {}).get('lon', 1),  # Use longitude as temporary user_id
                    'address': item.get('address', {}).get('country_code') if item.get('address') else None
                }
                
                # Apply data transformations
                transformed_item = DataTransformer.transform_attraction_data(mapped_item)
                
                # Create attraction with transformed data
                attraction = Attraction(
                    external_id=transformed_item.get('id'),
                    title=transformed_item.get('title'),
                    body=transformed_item.get('body'),
                    user_id=transformed_item.get('userId'),
                    location_category=transformed_item.get('location_category'),
                    province=transformed_item.get('province'),
                    district=transformed_item.get('district'),
                    original_date=transformed_item.get('original_date'),
                    normalized_date=transformed_item.get('normalized_date')
                )
                
                # Generate content hash
                attraction.content_hash = attraction.generate_content_hash()
                
                attractions.append(attraction)
                
            except Exception as e:
                logger.warning(f"Failed to transform OpenTripMap item {item.get('xid', 'unknown')}: {e}")
                continue
        
        logger.info(f"Successfully transformed {len(attractions)} OpenTripMap attractions")
        return attractions