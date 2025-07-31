"""
Robust HTTP fetch utilities with retry and exponential backoff using tenacity.
"""
import logging
import requests
from typing import Dict, Any, Optional
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