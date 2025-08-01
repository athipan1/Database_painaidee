"""
Geocoding service for converting location names to coordinates.
Supports both Google Geocoding API and OpenStreetMap Nominatim.
"""
import logging
import requests
import time
from typing import Dict, Optional, Tuple
from urllib.parse import quote

logger = logging.getLogger(__name__)


class GeocodingService:
    """Service for geocoding location names to coordinates."""
    
    def __init__(self, google_api_key: str = None, use_google: bool = True, timeout: int = 10):
        """
        Initialize geocoding service.
        
        Args:
            google_api_key: Google Geocoding API key
            use_google: Whether to use Google API (True) or OpenStreetMap (False)
            timeout: Request timeout in seconds
        """
        self.google_api_key = google_api_key
        self.use_google = use_google and google_api_key is not None
        self.timeout = timeout
        self.session = requests.Session()
        
        # Rate limiting for free APIs
        self.last_request_time = 0
        self.min_request_interval = 1.0  # 1 second between requests for free APIs
        
        logger.info(f"GeocodingService initialized with {'Google API' if self.use_google else 'OpenStreetMap'}")
    
    def geocode(self, location_name: str, province: str = None) -> Optional[Dict]:
        """
        Geocode a location name to coordinates.
        
        Args:
            location_name: Name of the location/attraction
            province: Province or state name (optional)
            
        Returns:
            Dictionary with 'latitude', 'longitude', 'formatted_address' or None if failed
        """
        if not location_name:
            return None
        
        # Construct search query
        query = location_name
        if province:
            query = f"{location_name}, {province}"
        
        logger.info(f"Geocoding location: {query}")
        
        try:
            if self.use_google:
                return self._geocode_with_google(query)
            else:
                return self._geocode_with_osm(query)
        except Exception as e:
            logger.error(f"Geocoding failed for '{query}': {str(e)}")
            return None
    
    def _geocode_with_google(self, query: str) -> Optional[Dict]:
        """Geocode using Google Geocoding API."""
        self._rate_limit()
        
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            'address': query,
            'key': self.google_api_key,
            'region': 'th'  # Bias towards Thailand
        }
        
        response = self.session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('status') != 'OK' or not data.get('results'):
            logger.warning(f"Google Geocoding API returned no results for: {query}")
            return None
        
        result = data['results'][0]
        location = result['geometry']['location']
        
        return {
            'latitude': location['lat'],
            'longitude': location['lng'],
            'formatted_address': result.get('formatted_address', query)
        }
    
    def _geocode_with_osm(self, query: str) -> Optional[Dict]:
        """Geocode using OpenStreetMap Nominatim API."""
        self._rate_limit()
        
        # Add Thailand to query for better results
        if 'thailand' not in query.lower() and 'ประเทศไทย' not in query:
            query += ', Thailand'
        
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': query,
            'format': 'json',
            'limit': 1,
            'countrycodes': 'th',  # Limit to Thailand
            'addressdetails': 1
        }
        
        headers = {
            'User-Agent': 'Database_painaidee/1.0 (attraction_geocoding)'
        }
        
        response = self.session.get(url, params=params, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        
        data = response.json()
        
        if not data:
            logger.warning(f"OpenStreetMap Nominatim returned no results for: {query}")
            return None
        
        result = data[0]
        
        return {
            'latitude': float(result['lat']),
            'longitude': float(result['lon']),
            'formatted_address': result.get('display_name', query)
        }
    
    def _rate_limit(self):
        """Implement rate limiting to respect API limits."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def batch_geocode(self, locations: list, delay: float = 1.0) -> Dict[str, Optional[Dict]]:
        """
        Geocode multiple locations with delay between requests.
        
        Args:
            locations: List of location dictionaries with 'name' and optional 'province'
            delay: Delay between requests in seconds
            
        Returns:
            Dictionary mapping location keys to geocoding results
        """
        results = {}
        
        for i, location in enumerate(locations):
            location_name = location.get('name', '')
            province = location.get('province', '')
            
            if not location_name:
                continue
            
            key = f"{location_name}_{province}" if province else location_name
            
            logger.info(f"Batch geocoding {i+1}/{len(locations)}: {key}")
            
            result = self.geocode(location_name, province)
            results[key] = result
            
            # Add delay between requests
            if i < len(locations) - 1:
                time.sleep(delay)
        
        return results


# Global geocoding service instance
_geocoding_service = None


def get_geocoding_service(google_api_key: str = None, use_google: bool = True) -> GeocodingService:
    """Get or create global geocoding service instance."""
    global _geocoding_service
    
    if _geocoding_service is None:
        _geocoding_service = GeocodingService(google_api_key, use_google)
    
    return _geocoding_service