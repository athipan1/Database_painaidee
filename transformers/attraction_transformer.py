"""
Attraction data transformer.
Transforms raw API data into database-ready format with optional geocoding.
"""
import logging
from typing import List, Dict, Any, Optional
from app.models import Attraction
from app.services.geocoding import get_geocoding_service
from app.utils.geo import extract_province_from_address
from app.utils.category import normalize_categories

logger = logging.getLogger(__name__)


class AttractionTransformer:
    """Transformer for attraction data from various sources."""
    
    def __init__(self):
        """Initialize transformer with default settings."""
        self.default_province = "กรุงเทพมหานคร"
    
    def transform(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """แปลงข้อมูลดิบให้อยู่ใน schema ที่ระบบใช้"""
        return {
            "title": raw_data.get("name") or "ชื่อไม่ระบุ",
            "description": raw_data.get("description", "").strip() or "ไม่มีคำอธิบาย",
            "province": extract_province_from_address(raw_data.get("formatted_address", "")) or self.default_province,
            "latitude": float(raw_data["geometry"]["location"]["lat"]) if raw_data.get("geometry", {}).get("location", {}).get("lat") else None,
            "longitude": float(raw_data["geometry"]["location"]["lng"]) if raw_data.get("geometry", {}).get("location", {}).get("lng") else None,
            "category": normalize_categories(raw_data.get("types", [])) or "สถานที่ท่องเที่ยว",
            "opening_hours": self.clean_opening_hours(raw_data.get("opening_hours")),
            "contact_phone": raw_data.get("phone", None),
        }

    def clean_opening_hours(self, hours_data: Any) -> str:
        """แปลงเวลาเปิด-ปิดให้อยู่ในรูปแบบสั้นและเข้าใจง่าย"""
        if not hours_data:
            return "ไม่ระบุเวลาเปิดทำการ"
        # สมมุติว่าเป็น dict with weekday_text
        if isinstance(hours_data, dict):
            weekday_text = hours_data.get("weekday_text", [])
            if isinstance(weekday_text, list):
                return "; ".join(weekday_text)
        # If it's already a string, return as is
        if isinstance(hours_data, str):
            return hours_data
        # If it's a list, join it
        if isinstance(hours_data, list):
            return "; ".join(str(item) for item in hours_data)
        return "ไม่ระบุเวลาเปิดทำการ"
    
    @staticmethod
    def transform_external_api_data(
        raw_data: List[Dict[str, Any]], 
        enable_geocoding: bool = False,
        google_api_key: str = None
    ) -> List[Attraction]:
        """
        Transform raw external API data into Attraction objects with optional geocoding.
        
        Args:
            raw_data: List of raw data items from external API
            enable_geocoding: Whether to attempt geocoding for items without coordinates
            google_api_key: Google API key for geocoding (optional)
            
        Returns:
            List of Attraction objects ready for database insertion
        """
        logger.info(f"Transforming {len(raw_data)} external API items (geocoding: {enable_geocoding})")
        
        geocoding_service = None
        if enable_geocoding:
            geocoding_service = get_geocoding_service(google_api_key)
        
        attractions = []
        geocoded_count = 0
        
        for item in raw_data:
            try:
                # First, create attraction from basic data
                attraction = Attraction.create_from_external_data(item)
                
                # Attempt geocoding if enabled and coordinates are missing
                if (enable_geocoding and geocoding_service and 
                    attraction.latitude is None and attraction.longitude is None and 
                    attraction.title):
                    
                    try:
                        location_data = geocoding_service.geocode(
                            attraction.title, 
                            attraction.province
                        )
                        
                        if location_data:
                            attraction.latitude = location_data['latitude']
                            attraction.longitude = location_data['longitude']
                            attraction.geocoded = True
                            geocoded_count += 1
                            logger.debug(f"Geocoded attraction: {attraction.title}")
                        
                    except Exception as geo_error:
                        logger.warning(f"Geocoding failed for {attraction.title}: {geo_error}")
                
                attractions.append(attraction)
                
            except Exception as e:
                logger.warning(f"Failed to transform item {item.get('id', 'unknown')}: {e}")
                continue
        
        logger.info(f"Successfully transformed {len(attractions)} attractions (geocoded: {geocoded_count})")
        return attractions
    
    @staticmethod
    def transform_tourism_thailand_data(
        raw_data: List[Dict[str, Any]], 
        enable_geocoding: bool = False,
        google_api_key: str = None
    ) -> List[Attraction]:
        """
        Transform raw Tourism Thailand API data into Attraction objects with optional geocoding.
        
        Args:
            raw_data: List of raw tourism data items
            enable_geocoding: Whether to attempt geocoding for items without coordinates
            google_api_key: Google API key for geocoding (optional)
            
        Returns:
            List of Attraction objects ready for database insertion
        """
        logger.info(f"Transforming {len(raw_data)} tourism Thailand items (geocoding: {enable_geocoding})")
        
        geocoding_service = None
        if enable_geocoding:
            geocoding_service = get_geocoding_service(google_api_key)
        
        attractions = []
        geocoded_count = 0
        
        for item in raw_data:
            try:
                # Transform Tourism Thailand specific fields
                transformed_item = {
                    'id': item.get('id'),
                    'title': item.get('name') or item.get('title'),
                    'body': item.get('description') or item.get('body'),
                    'userId': item.get('location_id') or item.get('userId', 1),
                    'province': item.get('province') or item.get('location', {}).get('province'),
                    'latitude': item.get('latitude') or item.get('location', {}).get('lat'),
                    'longitude': item.get('longitude') or item.get('location', {}).get('lng'),
                    'geocoded': item.get('latitude') is not None and item.get('longitude') is not None
                }
                
                attraction = Attraction.create_from_external_data(transformed_item)
                
                # Attempt geocoding if enabled and coordinates are missing
                if (enable_geocoding and geocoding_service and 
                    attraction.latitude is None and attraction.longitude is None and 
                    attraction.title):
                    
                    try:
                        location_data = geocoding_service.geocode(
                            attraction.title, 
                            attraction.province
                        )
                        
                        if location_data:
                            attraction.latitude = location_data['latitude']
                            attraction.longitude = location_data['longitude']
                            attraction.geocoded = True
                            geocoded_count += 1
                            logger.debug(f"Geocoded tourism attraction: {attraction.title}")
                        
                    except Exception as geo_error:
                        logger.warning(f"Geocoding failed for {attraction.title}: {geo_error}")
                
                attractions.append(attraction)
                
            except Exception as e:
                logger.warning(f"Failed to transform tourism item {item.get('id', 'unknown')}: {e}")
                continue
        
        logger.info(f"Successfully transformed {len(attractions)} tourism attractions (geocoded: {geocoded_count})")
        return attractions
    
    @staticmethod
    def transform_opentripmap_data(
        raw_data: List[Dict[str, Any]], 
        enable_geocoding: bool = False,
        google_api_key: str = None
    ) -> List[Attraction]:
        """
        Transform raw OpenTripMap API data into Attraction objects with optional geocoding.
        
        Args:
            raw_data: List of raw place data items
            enable_geocoding: Whether to attempt geocoding for items without coordinates
            google_api_key: Google API key for geocoding (optional)
            
        Returns:
            List of Attraction objects ready for database insertion
        """
        logger.info(f"Transforming {len(raw_data)} OpenTripMap items (geocoding: {enable_geocoding})")
        
        geocoding_service = None
        if enable_geocoding:
            geocoding_service = get_geocoding_service(google_api_key)
        
        attractions = []
        geocoded_count = 0
        
        for item in raw_data:
            try:
                # Transform OpenTripMap specific fields
                point = item.get('point', {})
                transformed_item = {
                    'id': item.get('xid') or item.get('id'),
                    'title': item.get('name') or item.get('title'),
                    'body': item.get('wikipedia_extracts', {}).get('text') or item.get('body'),
                    'userId': 1,  # Default user ID for OpenTripMap data
                    'latitude': point.get('lat'),
                    'longitude': point.get('lon'),
                    'geocoded': point.get('lat') is not None and point.get('lon') is not None
                }
                
                attraction = Attraction.create_from_external_data(transformed_item)
                
                # Attempt geocoding if enabled and coordinates are missing
                if (enable_geocoding and geocoding_service and 
                    attraction.latitude is None and attraction.longitude is None and 
                    attraction.title):
                    
                    try:
                        location_data = geocoding_service.geocode(attraction.title)
                        
                        if location_data:
                            attraction.latitude = location_data['latitude']
                            attraction.longitude = location_data['longitude']
                            attraction.geocoded = True
                            geocoded_count += 1
                            logger.debug(f"Geocoded OpenTripMap attraction: {attraction.title}")
                        
                    except Exception as geo_error:
                        logger.warning(f"Geocoding failed for {attraction.title}: {geo_error}")
                
                attractions.append(attraction)
                
            except Exception as e:
                logger.warning(f"Failed to transform OpenTripMap item {item.get('xid', 'unknown')}: {e}")
                continue
        
        logger.info(f"Successfully transformed {len(attractions)} OpenTripMap attractions (geocoded: {geocoded_count})")
        return attractions
    
    @staticmethod
    def extract_province_from_title(title: str) -> Optional[str]:
        """
        Extract province name from attraction title using common patterns.
        
        Args:
            title: Attraction title string
            
        Returns:
            Province name if found, None otherwise
        """
        # Common Thai province patterns
        thai_provinces = [
            'กรุงเทพ', 'นนทบุรี', 'ปทุมธานี', 'สมุทรปราการ', 'ชลบุรี', 'เชียงใหม่', 
            'ภูเก็ต', 'สุราษฎร์ธานี', 'กระบี่', 'ระยอง', 'ตราด', 'สงขลา'
        ]
        
        title_lower = title.lower()
        
        for province in thai_provinces:
            if province in title or province.lower() in title_lower:
                return province
        
        # English province patterns
        english_provinces = [
            'bangkok', 'chiang mai', 'phuket', 'pattaya', 'hua hin', 'krabi', 
            'koh samui', 'rayong', 'trat', 'songkhla'
        ]
        
        for province in english_provinces:
            if province in title_lower:
                return province.title()
        
        return None