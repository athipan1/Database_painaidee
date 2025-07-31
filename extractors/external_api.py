"""
External API extractor for JSONPlaceholder API (current implementation).
This serves as a base extractor that can be extended for other APIs.
"""
import logging
from typing import List, Dict, Any
from app.utils.fetch import fetch_json_with_retry

logger = logging.getLogger(__name__)


class ExternalAPIExtractor:
    """Extractor for external API data (JSONPlaceholder as base implementation)."""
    
    def __init__(self, api_url: str, timeout: int = 30):
        """
        Initialize the extractor.
        
        Args:
            api_url: The API endpoint URL
            timeout: Request timeout in seconds
        """
        self.api_url = api_url
        self.timeout = timeout
    
    def extract(self) -> List[Dict[str, Any]]:
        """
        Extract data from the external API.
        
        Returns:
            List of raw data items from the API
            
        Raises:
            requests.RequestException: If data extraction fails after retries
        """
        logger.info(f"Extracting data from: {self.api_url}")
        
        raw_data = fetch_json_with_retry(self.api_url, timeout=self.timeout)
        
        logger.info(f"Successfully extracted {len(raw_data)} items from external API")
        return raw_data