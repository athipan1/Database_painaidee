"""
External API extractor for JSONPlaceholder API (current implementation).
This serves as a base extractor that can be extended for other APIs.
Supports both paginated and non-paginated data fetching.
"""
import logging
from typing import List, Dict, Any, Optional, Iterator, Tuple
from app.utils.fetch import fetch_json_with_retry, fetch_paginated_data, fetch_all_paginated_data

logger = logging.getLogger(__name__)


class ExternalAPIExtractor:
    """Extractor for external API data (JSONPlaceholder as base implementation)."""
    
    def __init__(
        self, 
        api_url: str, 
        timeout: int = 30,
        enable_pagination: bool = False,
        page_size: int = 20,
        max_pages: int = 100,
        page_param: str = 'page',
        limit_param: str = 'limit'
    ):
        """
        Initialize the extractor.
        
        Args:
            api_url: The API endpoint URL
            timeout: Request timeout in seconds
            enable_pagination: Whether to use pagination
            page_size: Number of items per page (when pagination enabled)
            max_pages: Maximum number of pages to fetch (safety limit)
            page_param: Query parameter name for page number
            limit_param: Query parameter name for page size
        """
        self.api_url = api_url
        self.timeout = timeout
        self.enable_pagination = enable_pagination
        self.page_size = page_size
        self.max_pages = max_pages
        self.page_param = page_param
        self.limit_param = limit_param
    
    def extract(self) -> List[Dict[str, Any]]:
        """
        Extract data from the external API.
        
        Returns:
            List of raw data items from the API
            
        Raises:
            requests.RequestException: If data extraction fails after retries
        """
        logger.info(f"Extracting data from: {self.api_url}")
        
        if self.enable_pagination:
            logger.info(f"Using pagination: page_size={self.page_size}, max_pages={self.max_pages}")
            raw_data = fetch_all_paginated_data(
                base_url=self.api_url,
                page_size=self.page_size,
                max_pages=self.max_pages,
                page_param=self.page_param,
                limit_param=self.limit_param,
                timeout=self.timeout
            )
        else:
            logger.info("Using non-paginated fetch")
            raw_data = fetch_json_with_retry(self.api_url, timeout=self.timeout)
            
            # Ensure we always return a list
            if not isinstance(raw_data, list):
                raw_data = [raw_data] if raw_data else []
        
        logger.info(f"Successfully extracted {len(raw_data)} items from external API")
        return raw_data
    
    def extract_paginated(self) -> Iterator[Tuple[int, List[Dict[str, Any]]]]:
        """
        Extract data from the external API page by page (memory efficient).
        
        Yields:
            Tuple of (page_number, data_list) for each page
            
        Raises:
            requests.RequestException: If data extraction fails after retries
        """
        if not self.enable_pagination:
            logger.warning("Pagination not enabled, falling back to single page fetch")
            # Fetch all data and yield as single "page"
            raw_data = fetch_json_with_retry(self.api_url, timeout=self.timeout)
            if not isinstance(raw_data, list):
                raw_data = [raw_data] if raw_data else []
            yield 1, raw_data
            return
        
        logger.info(f"Starting paginated extraction from: {self.api_url}")
        logger.info(f"Pagination settings: page_size={self.page_size}, max_pages={self.max_pages}")
        
        for page_num, items in fetch_paginated_data(
            base_url=self.api_url,
            page_size=self.page_size,
            max_pages=self.max_pages,
            page_param=self.page_param,
            limit_param=self.limit_param,
            timeout=self.timeout
        ):
            yield page_num, items