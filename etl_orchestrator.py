"""
Enhanced ETL orchestrator with sync logging, caching, and error handling.
"""
import logging
import uuid
from typing import Dict, Any
from datetime import datetime
from extractors.external_api import ExternalAPIExtractor
from extractors.tourism_thailand import TourismThailandExtractor
from extractors.opentripmap import OpenTripMapExtractor
from transformers.attraction_transformer import AttractionTransformer
from loaders.attraction_loader import AttractionLoader
from app.models import db, SyncLog
from app.utils.cache import cache_manager

logger = logging.getLogger(__name__)


class ETLOrchestrator:
    """Enhanced orchestrator with comprehensive sync tracking and error handling."""
    
    @staticmethod
    def run_external_api_etl(
        api_url: str, 
        timeout: int = 30,
        enable_pagination: bool = False,
        page_size: int = 20,
        max_pages: int = 100,
        use_memory_efficient: bool = False,
        sync_type: str = 'manual',
        use_cache: bool = True,
        cache_ttl: int = 3600
    ) -> Dict[str, Any]:
        """
        Run enhanced ETL process for external API data with sync logging.
        
        Args:
            api_url: The external API endpoint URL
            timeout: Request timeout in seconds
            enable_pagination: Whether to use pagination
            page_size: Number of items per page (when pagination enabled)
            max_pages: Maximum number of pages to fetch (safety limit)
            use_memory_efficient: Whether to process data page by page (memory efficient)
            sync_type: Type of sync operation ('daily', 'update', 'manual')
            use_cache: Whether to use caching for API responses
            cache_ttl: Cache time-to-live in seconds
            
        Returns:
            Dictionary with ETL results including sync log info
        """
        # Create sync log entry
        sync_log = SyncLog(
            sync_type=sync_type,
            api_source='external_api',
            start_time=datetime.utcnow(),
            status='running'
        )
        db.session.add(sync_log)
        db.session.commit()
        
        sync_id = str(sync_log.id)
        logger.info(f"Starting ETL process (sync_id: {sync_id}) for external API data")
        logger.info(f"Pagination: enabled={enable_pagination}, page_size={page_size}, max_pages={max_pages}")
        logger.info(f"Memory efficient mode: {use_memory_efficient}, Cache: {use_cache}")
        
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
                total_fetched = 0
                all_errors = []
                
                for page_num, raw_data in extractor.extract_paginated():
                    logger.info(f"Processing page {page_num} with {len(raw_data)} items")
                    total_fetched += len(raw_data)
                    
                    # Transform page data
                    attractions = AttractionTransformer.transform_external_api_data(raw_data)
                    
                    # Load page data with sync tracking
                    page_result = AttractionLoader.load_attractions(attractions, sync_log)
                    
                    # Accumulate results
                    total_saved += page_result['saved']
                    total_skipped += page_result['skipped']
                    total_processed += page_result['total_processed']
                    all_errors.extend(page_result.get('errors', []))
                    
                    logger.info(f"Page {page_num} processed: saved={page_result['saved']}, skipped={page_result['skipped']}")
                
                result = {
                    'saved': total_saved,
                    'skipped': total_skipped,
                    'total_processed': total_processed,
                    'total_fetched': total_fetched,
                    'pagination_used': True,
                    'memory_efficient': True,
                    'errors': all_errors,
                    'sync_id': sync_id
                }
            else:
                # Traditional approach - load all data at once
                logger.info("Using traditional bulk processing")
                
                # Extract all data (with caching support)
                raw_data = extractor.extract()
                total_fetched = len(raw_data)
                
                # Transform
                attractions = AttractionTransformer.transform_external_api_data(raw_data)
                
                # Load with sync tracking
                result = AttractionLoader.load_attractions(attractions, sync_log)
                result['total_fetched'] = total_fetched
                result['pagination_used'] = enable_pagination
                result['memory_efficient'] = False
                result['sync_id'] = sync_id
            
            # Mark sync as completed
            sync_log.mark_completed(
                total_fetched=result['total_fetched'],
                total_saved=result['saved'],
                total_skipped=result['skipped'],
                errors=result.get('errors', [])
            )
            
            # Clear sync progress cache
            cache_manager.clear_sync_progress(sync_id)
            
            logger.info(f"ETL process completed successfully: {result}")
            return result
            
        except Exception as e:
            error_message = f"ETL process failed: {str(e)}"
            logger.error(error_message)
            
            # Mark sync as failed
            sync_log.mark_failed(error_message)
            
            # Clear sync progress cache
            cache_manager.clear_sync_progress(sync_id)
            
            raise
    
    @staticmethod
    def run_tourism_thailand_etl(
        api_url: str, 
        api_key: str = None, 
        timeout: int = 30,
        sync_type: str = 'manual'
    ) -> Dict[str, Any]:
        """
        Run enhanced ETL process for Tourism Thailand API data.
        
        Args:
            api_url: The Tourism Thailand API endpoint URL
            api_key: API key if required
            timeout: Request timeout in seconds
            sync_type: Type of sync operation
            
        Returns:
            Dictionary with ETL results including sync log info
        """
        # Create sync log entry
        sync_log = SyncLog(
            sync_type=sync_type,
            api_source='tourism_thailand',
            start_time=datetime.utcnow(),
            status='running'
        )
        db.session.add(sync_log)
        db.session.commit()
        
        sync_id = str(sync_log.id)
        logger.info(f"Starting ETL process (sync_id: {sync_id}) for Tourism Thailand data")
        
        try:
            # Extract
            extractor = TourismThailandExtractor(api_url, api_key, timeout)
            raw_data = extractor.extract()
            total_fetched = len(raw_data)
            
            # Transform
            attractions = AttractionTransformer.transform_tourism_thailand_data(raw_data)
            
            # Load with sync tracking
            result = AttractionLoader.load_attractions(attractions, sync_log)
            result['total_fetched'] = total_fetched
            result['sync_id'] = sync_id
            
            # Mark sync as completed
            sync_log.mark_completed(
                total_fetched=result['total_fetched'],
                total_saved=result['saved'],
                total_skipped=result['skipped'],
                errors=result.get('errors', [])
            )
            
            logger.info(f"Tourism Thailand ETL process completed: {result}")
            return result
            
        except Exception as e:
            error_message = f"Tourism Thailand ETL process failed: {str(e)}"
            logger.error(error_message)
            
            # Mark sync as failed
            sync_log.mark_failed(error_message)
            raise
    
    @staticmethod
    def run_opentripmap_etl(
        api_url: str, 
        api_key: str = None, 
        timeout: int = 30,
        sync_type: str = 'manual'
    ) -> Dict[str, Any]:
        """
        Run enhanced ETL process for OpenTripMap API data.
        
        Args:
            api_url: The OpenTripMap API endpoint URL
            api_key: API key if required
            timeout: Request timeout in seconds
            sync_type: Type of sync operation
            
        Returns:
            Dictionary with ETL results including sync log info
        """
        # Create sync log entry
        sync_log = SyncLog(
            sync_type=sync_type,
            api_source='opentripmap',
            start_time=datetime.utcnow(),
            status='running'
        )
        db.session.add(sync_log)
        db.session.commit()
        
        sync_id = str(sync_log.id)
        logger.info(f"Starting ETL process (sync_id: {sync_id}) for OpenTripMap data")
        
        try:
            # Extract
            extractor = OpenTripMapExtractor(api_url, api_key, timeout)
            raw_data = extractor.extract()
            total_fetched = len(raw_data)
            
            # Transform
            attractions = AttractionTransformer.transform_opentripmap_data(raw_data)
            
            # Load with sync tracking
            result = AttractionLoader.load_attractions(attractions, sync_log)
            result['total_fetched'] = total_fetched
            result['sync_id'] = sync_id
            
            # Mark sync as completed
            sync_log.mark_completed(
                total_fetched=result['total_fetched'],
                total_saved=result['saved'],
                total_skipped=result['skipped'],
                errors=result.get('errors', [])
            )
            
            logger.info(f"OpenTripMap ETL process completed: {result}")
            return result
            
        except Exception as e:
            error_message = f"OpenTripMap ETL process failed: {str(e)}"
            logger.error(error_message)
            
            # Mark sync as failed
            sync_log.mark_failed(error_message)
            raise