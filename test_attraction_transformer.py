"""
Tests for the AttractionTransformer transform method and utility functions.
"""
import pytest
from transformers.attraction_transformer import AttractionTransformer
from app.utils.geo import extract_province_from_address
from app.utils.category import normalize_categories


class TestAttractionTransformMethod:
    """Test the new transform method implementation."""
    
    def test_transform_complete_data(self):
        """Test transform with complete Google Places-style data."""
        transformer = AttractionTransformer()
        
        raw_data = {
            "name": "วัดพระแก้ว",
            "description": "วัดพระแก้วเป็นวัดที่สำคัญที่สุดในประเทศไทย",
            "formatted_address": "Na Phra Lan Rd, Phra Borom Maha Ratchawang, Phra Nakhon, กรุงเทพมหานคร 10200",
            "geometry": {
                "location": {
                    "lat": 13.7500,
                    "lng": 100.4917
                }
            },
            "types": ["place_of_worship", "tourist_attraction", "establishment"],
            "opening_hours": {
                "weekday_text": [
                    "Monday: 8:30 AM – 3:30 PM",
                    "Tuesday: 8:30 AM – 3:30 PM"
                ]
            },
            "phone": "+66 2 623 5500"
        }
        
        result = transformer.transform(raw_data)
        
        assert result["title"] == "วัดพระแก้ว"
        assert result["description"] == "วัดพระแก้วเป็นวัดที่สำคัญที่สุดในประเทศไทย"
        assert result["province"] == "กรุงเทพมหานคร"
        assert result["latitude"] == 13.7500
        assert result["longitude"] == 100.4917
        assert result["category"] == "วัด/ศาสนสถาน"
        assert "Monday: 8:30 AM – 3:30 PM" in result["opening_hours"]
        assert result["contact_phone"] == "+66 2 623 5500"
    
    def test_transform_minimal_data(self):
        """Test transform with minimal required data."""
        transformer = AttractionTransformer()
        
        raw_data = {
            "geometry": {
                "location": {
                    "lat": 13.7563,
                    "lng": 100.5018
                }
            }
        }
        
        result = transformer.transform(raw_data)
        
        assert result["title"] == "ชื่อไม่ระบุ"
        assert result["description"] == "ไม่มีคำอธิบาย"
        assert result["province"] == "กรุงเทพมหานคร"  # default
        assert result["latitude"] == 13.7563
        assert result["longitude"] == 100.5018
        assert result["category"] == "สถานที่ท่องเที่ยว"  # default from normalize_categories
        assert result["opening_hours"] == "ไม่ระบุเวลาเปิดทำการ"
        assert result["contact_phone"] is None
    
    def test_transform_missing_geometry(self):
        """Test transform with missing geometry data."""
        transformer = AttractionTransformer()
        
        raw_data = {
            "name": "Test Attraction",
            "description": "A test attraction"
        }
        
        result = transformer.transform(raw_data)
        
        assert result["title"] == "Test Attraction"
        assert result["latitude"] is None
        assert result["longitude"] is None
    
    def test_transform_empty_description(self):
        """Test transform with empty description."""
        transformer = AttractionTransformer()
        
        raw_data = {
            "name": "Test Place",
            "description": "   ",  # whitespace only
            "geometry": {
                "location": {
                    "lat": 13.7563,
                    "lng": 100.5018
                }
            }
        }
        
        result = transformer.transform(raw_data)
        
        assert result["description"] == "ไม่มีคำอธิบาย"
    
    def test_clean_opening_hours_variations(self):
        """Test different opening hours data formats."""
        transformer = AttractionTransformer()
        
        # Dict format
        hours_dict = {"weekday_text": ["Mon: 9AM-5PM", "Tue: 9AM-5PM"]}
        result = transformer.clean_opening_hours(hours_dict)
        assert result == "Mon: 9AM-5PM; Tue: 9AM-5PM"
        
        # String format
        hours_string = "Daily: 9AM-5PM"
        result = transformer.clean_opening_hours(hours_string)
        assert result == "Daily: 9AM-5PM"
        
        # List format
        hours_list = ["Mon: 9AM-5PM", "Tue: 9AM-5PM"]
        result = transformer.clean_opening_hours(hours_list)
        assert result == "Mon: 9AM-5PM; Tue: 9AM-5PM"
        
        # None/empty
        result = transformer.clean_opening_hours(None)
        assert result == "ไม่ระบุเวลาเปิดทำการ"
        
        result = transformer.clean_opening_hours({})
        assert result == "ไม่ระบุเวลาเปิดทำการ"


class TestGeoUtilityFunction:
    """Test the extract_province_from_address utility function."""
    
    def test_extract_province_bangkok_thai(self):
        """Test extracting Bangkok province in Thai."""
        address = "Na Phra Lan Rd, Phra Borom Maha Ratchawang, Phra Nakhon, กรุงเทพมหานคร 10200"
        result = extract_province_from_address(address)
        assert result == "กรุงเทพมหานคร"
    
    def test_extract_province_bangkok_english(self):
        """Test extracting Bangkok province in English."""
        address = "123 Bangkok Street, Bangkok, Thailand"
        result = extract_province_from_address(address)
        assert result == "กรุงเทพมหานคร"
    
    def test_extract_province_chiang_mai(self):
        """Test extracting Chiang Mai province."""
        address = "Old City, Chiang Mai Province, Thailand"
        result = extract_province_from_address(address)
        assert result == "เชียงใหม่"
    
    def test_extract_province_phuket(self):
        """Test extracting Phuket province."""
        address = "Patong Beach, Phuket, Thailand"
        result = extract_province_from_address(address)
        assert result == "ภูเก็ต"
    
    def test_extract_province_pattern_matching(self):
        """Test province pattern matching."""
        address = "จ.เชียงใหม่ ประเทศไทย"
        result = extract_province_from_address(address)
        assert result == "เชียงใหม่"
        
        address = "จังหวัดภูเก็ต"
        result = extract_province_from_address(address)
        assert result == "ภูเก็ต"
    
    def test_extract_province_no_match(self):
        """Test when no province is found."""
        address = "Some random street address"
        result = extract_province_from_address(address)
        assert result is None
    
    def test_extract_province_empty_input(self):
        """Test with empty or invalid input."""
        assert extract_province_from_address("") is None
        assert extract_province_from_address(None) is None
        assert extract_province_from_address(123) is None


class TestCategoryUtilityFunction:
    """Test the normalize_categories utility function."""
    
    def test_normalize_temple_categories(self):
        """Test normalizing temple/religious categories."""
        types = ["place_of_worship", "tourist_attraction", "establishment"]
        result = normalize_categories(types)
        assert result == "วัด/ศาสนสถาน"
        
        types = ["temple", "hindu_temple"]
        result = normalize_categories(types)
        assert result == "วัด/ศาสนสถาน"
    
    def test_normalize_museum_categories(self):
        """Test normalizing museum categories."""
        types = ["museum", "tourist_attraction"]
        result = normalize_categories(types)
        assert result == "พิพิธภัณฑ์"
    
    def test_normalize_park_categories(self):
        """Test normalizing park categories."""
        types = ["park", "establishment"]
        result = normalize_categories(types)
        assert result == "สวนสาธารณะ"
    
    def test_normalize_restaurant_categories(self):
        """Test normalizing restaurant categories."""
        types = ["restaurant", "food", "establishment"]
        result = normalize_categories(types)
        assert result == "ร้านอาหาร"
    
    def test_normalize_keyword_matching(self):
        """Test keyword-based category matching."""
        types = ["วัดใหญ่"]
        result = normalize_categories(types)
        assert result == "วัด/ศาสนสถาน"
        
        types = ["beach resort"]
        result = normalize_categories(types)
        assert result == "ชายหาด"
    
    def test_normalize_default_category(self):
        """Test default category for unrecognized types."""
        types = ["unknown_type", "random_category"]
        result = normalize_categories(types)
        assert result == "สถานที่ท่องเที่ยว"
    
    def test_normalize_empty_input(self):
        """Test with empty or invalid input."""
        assert normalize_categories([]) is None
        assert normalize_categories(None) is None
        assert normalize_categories("not a list") is None
    
    def test_normalize_priority_order(self):
        """Test that higher priority categories are returned first."""
        # Temple should have higher priority than general tourist attraction
        types = ["tourist_attraction", "place_of_worship", "establishment"]
        result = normalize_categories(types)
        assert result == "วัด/ศาสนสถาน"
        
        # Museum should have higher priority than general tourist attraction
        types = ["establishment", "tourist_attraction", "museum"]
        result = normalize_categories(types)
        assert result == "พิพิธภัณฑ์"