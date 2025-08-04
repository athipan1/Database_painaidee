"""
ETL orchestrator for coordinating data extraction, transformation, and loading.
"""
import logging
from typing import Dict, Any
from extractors.external_api import ExternalAPIExtractor
from extractors.tourism_thailand import TourismThailandExtractor
from extractors.opentripmap import OpenTripMapExtractor
from extractors.tat_csv import TATCSVExtractor
from transformers.attraction_transformer import AttractionTransformer
from loaders.attraction_loader import AttractionLoader

logger = logging.getLogger(__name__)


class ETLOrchestrator:
    """Orchestrates the ETL process for attraction data."""
    
    @staticmethod
    def run_external_api_etl(
        api_url: str, 
        timeout: int = 30,
        enable_pagination: bool = False,
        page_size: int = 20,
        max_pages: int = 100,
        use_memory_efficient: bool = False,
        enable_geocoding: bool = False,
        google_api_key: str = None
    ) -> Dict[str, Any]:
        """
        Run ETL process for external API data.
        
        Args:
            api_url: The external API endpoint URL
            timeout: Request timeout in seconds
            enable_pagination: Whether to use pagination
            page_size: Number of items per page (when pagination enabled)
            max_pages: Maximum number of pages to fetch (safety limit)
            use_memory_efficient: Whether to process data page by page (memory efficient)
            enable_geocoding: Whether to attempt geocoding for missing coordinates
            google_api_key: Google API key for geocoding (optional)
            
        Returns:
            Dictionary with ETL results
        """
        logger.info("Starting ETL process for external API data")
        logger.info(f"Pagination: enabled={enable_pagination}, page_size={page_size}, max_pages={max_pages}")
        logger.info(f"Memory efficient mode: {use_memory_efficient}")
        
        try:
            # Initialize extractor with pagination settings
            extractor = ExternalAPIExtractor(
                api_url=api_url,
                timeout=timeout,
                enable_pagination=enable_pagination,
                page_size=page_size,
                max_pages=max_pages
            )
            
            if use_memory_efficient and enable_pagination:
                # Process data page by page to save memory
                logger.info("Using memory-efficient paginated processing")
                total_saved = 0
                total_skipped = 0
                total_processed = 0
                
                for page_num, raw_data in extractor.extract_paginated():
                    logger.info(f"Processing page {page_num} with {len(raw_data)} items")
                    
                    # Transform page data with optional geocoding
                    attractions = AttractionTransformer.transform_external_api_data(
                        raw_data, enable_geocoding, google_api_key
                    )
                    
                    # Load page data
                    page_result = AttractionLoader.load_attractions(attractions)
                    
                    # Accumulate results
                    total_saved += page_result['saved']
                    total_skipped += page_result['skipped']
                    total_processed += page_result['total_processed']
                    
                    logger.info(f"Page {page_num} processed: saved={page_result['saved']}, skipped={page_result['skipped']}")
                
                result = {
                    'saved': total_saved,
                    'skipped': total_skipped,
                    'total_processed': total_processed,
                    'pagination_used': True,
                    'memory_efficient': True
                }
            else:
                # Traditional approach - load all data at once
                logger.info("Using traditional bulk processing")
                
                # Extract all data
                raw_data = extractor.extract()
                
                # Transform with optional geocoding
                attractions = AttractionTransformer.transform_external_api_data(
                    raw_data, enable_geocoding, google_api_key
                )
                
                # Load
                result = AttractionLoader.load_attractions(attractions)
                result['pagination_used'] = enable_pagination
                result['memory_efficient'] = False
            
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
    
    @staticmethod
    def run_tat_csv_etl(
        csv_url: str, 
        timeout: int = 30,
        enable_geocoding: bool = False,
        google_api_key: str = None
    ) -> Dict[str, Any]:
        """
        Run ETL process for TAT Open Data CSV.
        
        Args:
            csv_url: The TAT CSV download URL
            timeout: Request timeout in seconds  
            enable_geocoding: Whether to attempt geocoding for missing coordinates
            google_api_key: Google API key for geocoding (optional)
            
        Returns:
            Dictionary with ETL results
        """
        logger.info("Starting ETL process for TAT CSV data")
        logger.info(f"CSV URL: {csv_url}")
        logger.info(f"Geocoding enabled: {enable_geocoding}")
        
        try:
            # Extract
            extractor = TATCSVExtractor(csv_url, timeout)
            raw_data = extractor.extract()
            
            # Transform
            attractions = AttractionTransformer.transform_tat_csv_data(
                raw_data, 
                enable_geocoding=enable_geocoding,
                google_api_key=google_api_key
            )
            
            # Load
            loader = AttractionLoader()
            result = loader.load_attractions(attractions)
            
            logger.info(f"TAT CSV ETL process completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"TAT CSV ETL process failed: {str(e)}")
            raise