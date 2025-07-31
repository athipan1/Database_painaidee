"""
ETL orchestrator for coordinating data extraction, transformation, and loading.
"""
import logging
from typing import Dict, Any
from extractors.external_api import ExternalAPIExtractor
from extractors.tourism_thailand import TourismThailandExtractor
from extractors.opentripmap import OpenTripMapExtractor
from transformers.attraction_transformer import AttractionTransformer
from loaders.attraction_loader import AttractionLoader

logger = logging.getLogger(__name__)


class ETLOrchestrator:
    """Orchestrates the ETL process for attraction data."""
    
    @staticmethod
    def run_external_api_etl(api_url: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Run ETL process for external API data.
        
        Args:
            api_url: The external API endpoint URL
            timeout: Request timeout in seconds
            
        Returns:
            Dictionary with ETL results
        """
        logger.info("Starting ETL process for external API data")
        
        try:
            # Extract
            extractor = ExternalAPIExtractor(api_url, timeout)
            raw_data = extractor.extract()
            
            # Transform
            attractions = AttractionTransformer.transform_external_api_data(raw_data)
            
            # Load
            result = AttractionLoader.load_attractions(attractions)
            
            logger.info(f"ETL process completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"ETL process failed: {str(e)}")
            raise
    
    @staticmethod
    def run_tourism_thailand_etl(api_url: str, api_key: str = None, timeout: int = 30) -> Dict[str, Any]:
        """
        Run ETL process for Tourism Thailand API data.
        
        Args:
            api_url: The Tourism Thailand API endpoint URL
            api_key: API key if required
            timeout: Request timeout in seconds
            
        Returns:
            Dictionary with ETL results
        """
        logger.info("Starting ETL process for Tourism Thailand data")
        
        try:
            # Extract
            extractor = TourismThailandExtractor(api_url, api_key, timeout)
            raw_data = extractor.extract()
            
            # Transform
            attractions = AttractionTransformer.transform_tourism_thailand_data(raw_data)
            
            # Load
            result = AttractionLoader.load_attractions(attractions)
            
            logger.info(f"Tourism Thailand ETL process completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Tourism Thailand ETL process failed: {str(e)}")
            raise
    
    @staticmethod
    def run_opentripmap_etl(api_url: str, api_key: str = None, timeout: int = 30) -> Dict[str, Any]:
        """
        Run ETL process for OpenTripMap API data.
        
        Args:
            api_url: The OpenTripMap API endpoint URL
            api_key: API key if required
            timeout: Request timeout in seconds
            
        Returns:
            Dictionary with ETL results
        """
        logger.info("Starting ETL process for OpenTripMap data")
        
        try:
            # Extract
            extractor = OpenTripMapExtractor(api_url, api_key, timeout)
            raw_data = extractor.extract()
            
            # Transform
            attractions = AttractionTransformer.transform_opentripmap_data(raw_data)
            
            # Load
            result = AttractionLoader.load_attractions(attractions)
            
            logger.info(f"OpenTripMap ETL process completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"OpenTripMap ETL process failed: {str(e)}")
            raise