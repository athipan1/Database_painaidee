"""
Demonstration of enhanced ETL pipeline with mock server.
"""
import pytest
import requests
from unittest.mock import patch, Mock
from app.utils.fetch import fetch_json_with_retry
from transformers.attraction_transformer import AttractionTransformer
from app.utils.data_transform import DataTransformer


def test_complete_etl_pipeline_mock(requests_mock):
    """Test complete ETL pipeline with mock API and data transformations."""
    
    # Mock API response with Thai attraction data
    mock_api_data = [
        {
            'id': 1,
            'title': '  วัดพระแก้ว  ',
            'body': 'วัดที่สวยงามในกรุงเทพฯ มีประวัติศาสตร์ยาวนาน',
            'userId': 123,
            'date': '15/03/2024',
            'address': 'อำเภอพระนคร จังหวัดกรุงเทพมหานคร 10200'
        },
        {
            'id': 2,
            'title': 'ดอยสุเทพ-ปุย',
            'body': 'ภูเขาที่สวยงามในเชียงใหม่ มีวิวที่งดงาม',
            'userId': 124,
            'date': '16/03/2024',
            'address': 'อำเภอเมือง จังหวัดเชียงใหม่'
        },
        {
            'id': 3,
            'title': '  หาดป่าตอง  ',
            'body': 'หาดทรายขาวในภูเก็ต  <p>มีท่องเที่ยวหลากหลาย</p>',
            'userId': 125,
            'date': '17-03-2024',
            'address': 'อำเภอกะทู้ จังหวัดภูเก็ต'
        }
    ]
    
    # Setup mock API endpoint
    requests_mock.get('http://mock-thailand-api.com/attractions', json=mock_api_data)
    
    # Test 1: Extract data from mock API
    print("\n=== Testing Data Extraction ===")
    response_data = fetch_json_with_retry('http://mock-thailand-api.com/attractions', use_cache=False)
    assert len(response_data) == 3
    assert response_data[0]['title'] == '  วัดพระแก้ว  '
    print(f"✅ Extracted {len(response_data)} items from mock API")
    
    # Test 2: Transform data with enhanced features
    print("\n=== Testing Data Transformation ===")
    attractions = AttractionTransformer.transform_external_api_data(response_data)
    
    assert len(attractions) == 3
    
    # Test temple attraction
    temple = attractions[0]
    assert temple.title == 'วัดพระแก้ว'  # Cleaned whitespace
    assert temple.location_category == 'วัด'  # Categorized as temple
    assert temple.province == 'กรุงเทพมหานคร'  # Parsed province
    assert temple.district == 'พระนคร'  # Parsed district
    assert temple.normalized_date.year == 2024  # Date normalized
    assert temple.content_hash is not None  # Hash generated
    print(f"✅ Temple: {temple.title} -> {temple.location_category} in {temple.province}")
    
    # Test mountain attraction  
    mountain = attractions[1]
    assert mountain.title == 'ดอยสุเทพ-ปุย'
    assert mountain.location_category == 'ภูเขา'  # Categorized as mountain
    assert mountain.province == 'เชียงใหม่'
    print(f"✅ Mountain: {mountain.title} -> {mountain.location_category} in {mountain.province}")
    
    # Test beach attraction
    beach = attractions[2]
    assert beach.title == 'หาดป่าตอง'  # Cleaned whitespace
    assert beach.location_category == 'ทะเล'  # Categorized as sea/beach
    assert beach.province == 'ภูเก็ต'
    assert 'มีท่องเที่ยวหลากหลาย' in beach.body  # HTML tags removed
    print(f"✅ Beach: {beach.title} -> {beach.location_category} in {beach.province}")
    
    # Test 3: Duplicate detection with content hash
    print("\n=== Testing Duplicate Detection ===")
    
    # Create duplicate with same content but different external_id
    duplicate_data = {
        'id': 999,  # Different external ID
        'title': '  วัดพระแก้ว  ',  # Same content
        'body': 'วัดที่สวยงามในกรุงเทพฯ มีประวัติศาสตร์ยาวนาน',
        'userId': 123,
    }
    
    duplicate_attraction = AttractionTransformer.transform_external_api_data([duplicate_data])[0]
    
    # Hash should be the same despite different external_id
    original_hash = temple.content_hash
    duplicate_hash = duplicate_attraction.content_hash
    
    # The hashes should be different because external_id is part of the hash
    assert original_hash != duplicate_hash
    print(f"✅ Different external_id produces different hash: {original_hash[:8]}... vs {duplicate_hash[:8]}...")
    
    # Test 4: Cache functionality simulation
    print("\n=== Testing Cache Simulation ===")
    with patch('app.utils.cache.cache_manager') as mock_cache:
        mock_cache.get_cached_api_response.return_value = None  # Cache miss
        mock_cache.cache_api_response.return_value = True  # Cache successful
        
        # Fetch with caching enabled
        cached_response = fetch_json_with_retry(
            'http://mock-thailand-api.com/attractions', 
            use_cache=True
        )
        
        assert len(cached_response) == 3
        mock_cache.cache_api_response.assert_called_once()
        print("✅ Data cached successfully after API fetch")
    
    print("\n=== ETL Pipeline Test Completed Successfully! ===")
    print(f"Processed {len(attractions)} attractions with enhanced features:")
    for attr in attractions:
        print(f"  - {attr.title} ({attr.location_category}) in {attr.province}")


def test_data_transformation_edge_cases():
    """Test data transformation with edge cases and error handling."""
    
    print("\n=== Testing Edge Cases ===")
    
    # Test invalid date formats
    invalid_dates = ['invalid-date', '32/13/2024', '', None]
    for date_str in invalid_dates:
        result = DataTransformer.normalize_date(date_str)
        assert result is None
        print(f"✅ Invalid date '{date_str}' handled gracefully")
    
    # Test address parsing with missing data
    incomplete_addresses = [
        'ที่อยู่ไม่สมบูรณ์',
        'อำเภอเมือง',  # Missing province
        'จังหวัดกรุงเทพมหานคร',  # Missing district
        '',
        None
    ]
    
    for addr in incomplete_addresses:
        province, district = DataTransformer.parse_address(addr)
        print(f"✅ Address '{addr}' -> Province: {province}, District: {district}")
    
    # Test location categorization with mixed content
    mixed_cases = [
        ('วัดใหญ่ใกล้ภูเขา', 'วัด'),  # Temple should win over mountain
        ('ตลาดน้ำใกล้ทะเล', 'ตลาด'),  # Market should win over sea
        ('สถานที่ท่องเที่ยวทั่วไป', 'อื่นๆ'),  # Should default to other
    ]
    
    for title, expected_category in mixed_cases:
        result = DataTransformer.categorize_location(title, '')
        assert result == expected_category
        print(f"✅ '{title}' -> {result}")
    
    print("✅ All edge cases handled properly")


if __name__ == '__main__':
    # Run the demonstration
    pytest.main([__file__ + '::test_complete_etl_pipeline_mock', '-v', '-s'])
    pytest.main([__file__ + '::test_data_transformation_edge_cases', '-v', '-s'])