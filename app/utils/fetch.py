"""
Robust HTTP fetch utilities with retry and exponential backoff using tenacity.
Includes pagination support for efficient data fetching.
"""
import logging
import requests
from typing import Dict, Any, Optional, List, Iterator, Tuple
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log
)

logger = logging.getLogger(__name__)


@retry(
    stop=stop_after_attempt(4),  # Try up to 4 times (1 initial + 3 retries)
    wait=wait_exponential(multiplier=1, min=1, max=60),  # 1s, 2s, 4s, 8s, max 60s
    retry=retry_if_exception_type((
        requests.exceptions.Timeout,
        requests.exceptions.ConnectionError,
        requests.exceptions.HTTPError,
    )),
    before_sleep=before_sleep_log(logger, logging.INFO),
    after=after_log(logger, logging.INFO)
)
def fetch_with_retry(
    url: str,
    timeout: int = 30,
    method: str = 'GET',
    headers: Optional[Dict[str, str]] = None,
    data: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    **kwargs
) -> requests.Response:
    """
    Fetch data from URL with retry logic using exponential backoff.
    
    Args:
        url: The URL to fetch
        timeout: Request timeout in seconds
        method: HTTP method (GET, POST, etc.)
        headers: Optional headers dictionary
        data: Optional form data
        json_data: Optional JSON data
        **kwargs: Additional requests parameters
    
    Returns:
        requests.Response object
        
    Raises:
        requests.RequestException: After all retry attempts are exhausted
    """
    logger.info(f"Attempting to fetch {method} {url}")
    
    response = requests.request(
        method=method,
        url=url,
        timeout=timeout,
        headers=headers,
        data=data,
        json=json_data,
        **kwargs
    )
    
    # Raise exception for HTTP error status codes (4xx, 5xx)
    response.raise_for_status()
    
    logger.info(f"Successfully fetched {method} {url} - Status: {response.status_code}")
    return response


def fetch_json_with_retry(
    url: str,
    timeout: int = 30,
    method: str = 'GET',
    headers: Optional[Dict[str, str]] = None,
    data: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Fetch JSON data from URL with retry logic.
    
    Args:
        url: The URL to fetch
        timeout: Request timeout in seconds
        method: HTTP method (GET, POST, etc.)
        headers: Optional headers dictionary
        data: Optional form data
        json_data: Optional JSON data
        **kwargs: Additional requests parameters
    
    Returns:
        Parsed JSON response as dictionary
        
    Raises:
        requests.RequestException: After all retry attempts are exhausted
        ValueError: If response is not valid JSON
    """
    response = fetch_with_retry(
        url=url,
        timeout=timeout,
        method=method,
        headers=headers,
        data=data,
        json_data=json_data,
        **kwargs
    )
    
    try:
        return response.json()
    except ValueError as e:
        logger.error(f"Failed to parse JSON response from {url}: {e}")
        raise


def fetch_paginated_data(
    base_url: str,
    page_size: int = 20,
    max_pages: int = 100,
    page_param: str = 'page',
    limit_param: str = 'limit',
    start_page: int = 1,
    timeout: int = 30,
    headers: Optional[Dict[str, str]] = None,
    **kwargs
) -> Iterator[Tuple[int, List[Dict[str, Any]]]]:
    """
    Fetch paginated JSON data from API with retry logic.
    
    Args:
        base_url: The base API URL (without pagination parameters)
        page_size: Number of items per page
        max_pages: Maximum number of pages to fetch (safety limit)
        page_param: Query parameter name for page number (default: 'page')
        limit_param: Query parameter name for page size (default: 'limit')
        start_page: Starting page number (default: 1)
        timeout: Request timeout in seconds
        headers: Optional headers dictionary
        **kwargs: Additional requests parameters
    
    Yields:
        Tuple of (page_number, data_list) for each page
        
    Raises:
        requests.RequestException: After all retry attempts are exhausted
        ValueError: If response is not valid JSON
    """
    logger.info(f"Starting paginated fetch from {base_url} with page_size={page_size}, max_pages={max_pages}")
    
    current_page = start_page
    total_items = 0
    
    while current_page <= max_pages:
        # Build URL with pagination parameters
        separator = '&' if '?' in base_url else '?'
        paginated_url = f"{base_url}{separator}{page_param}={current_page}&{limit_param}={page_size}"
        
        logger.info(f"Fetching page {current_page}: {paginated_url}")
        
        try:
            page_data = fetch_json_with_retry(
                url=paginated_url,
                timeout=timeout,
                headers=headers,
                **kwargs
            )
            
            # Handle different API response formats
            items = []
            if isinstance(page_data, list):
                # Direct list response
                items = page_data
            elif isinstance(page_data, dict):
                # Object response - try common pagination formats
                data_items = page_data.get('data', [])
                items_items = page_data.get('items', [])
                results_items = page_data.get('results', [])
                
                # Use the first non-empty list found, or the first one if all are empty
                if data_items:
                    items = data_items
                elif items_items:
                    items = items_items
                elif results_items:
                    items = results_items
                elif 'data' in page_data:
                    items = []  # data field exists but is empty
                elif 'items' in page_data:
                    items = []  # items field exists but is empty  
                elif 'results' in page_data:
                    items = []  # results field exists but is empty
                else:
                    # No standard pagination fields - treat whole object as single item
                    # only if it contains meaningful content
                    content_keys = [key for key in page_data.keys() 
                                   if key not in ['total', 'count', 'pagination', 'meta', 'status', 'page', 'per_page', 'has_more']]
                    if content_keys:
                        items = [page_data]
            
            items_count = len(items)
            total_items += items_count
            
            logger.info(f"Page {current_page}: Retrieved {items_count} items (total so far: {total_items})")
            
            # Yield the page data
            yield current_page, items
            
            # Check if we've reached the end
            if items_count == 0 or items_count < page_size:
                logger.info(f"Reached end of data at page {current_page} (got {items_count} items, expected {page_size})")
                break
                
            current_page += 1
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch page {current_page}: {e}")
            raise
    
    logger.info(f"Completed paginated fetch: {current_page - start_page} pages, {total_items} total items")


def fetch_all_paginated_data(
    base_url: str,
    page_size: int = 20,
    max_pages: int = 100,
    page_param: str = 'page',
    limit_param: str = 'limit',
    start_page: int = 1,
    timeout: int = 30,
    headers: Optional[Dict[str, str]] = None,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    Fetch all paginated data and return as a single list.
    
    Args:
        base_url: The base API URL (without pagination parameters)
        page_size: Number of items per page
        max_pages: Maximum number of pages to fetch (safety limit)
        page_param: Query parameter name for page number (default: 'page')
        limit_param: Query parameter name for page size (default: 'limit') 
        start_page: Starting page number (default: 1)
        timeout: Request timeout in seconds
        headers: Optional headers dictionary
        **kwargs: Additional requests parameters
    
    Returns:
        List of all items from all pages
        
    Raises:
        requests.RequestException: After all retry attempts are exhausted
        ValueError: If response is not valid JSON
    """
    all_items = []
    
    for page_num, items in fetch_paginated_data(
        base_url=base_url,
        page_size=page_size,
        max_pages=max_pages,
        page_param=page_param,
        limit_param=limit_param,
        start_page=start_page,
        timeout=timeout,
        headers=headers,
        **kwargs
    ):
        all_items.extend(items)
    
    logger.info(f"Fetched all paginated data: {len(all_items)} total items")
    return all_items