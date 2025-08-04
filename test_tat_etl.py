#!/usr/bin/env python3
"""
Test script for TAT CSV ETL functionality.
Tests the new TAT Open Data ETL pipeline without requiring database connection.
"""

import sys
import tempfile
import logging
from io import StringIO

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_tat_csv_extractor():
    """Test TAT CSV extractor with sample data."""
    print("🧪 Testing TAT CSV Extractor...")
    
    try:
        from extractors.tat_csv import TATCSVExtractor
        
        # Create sample CSV data
        sample_csv = """ชื่อสถานที่,รายละเอียด,จังหวัด,ละติจูด,ลองจิจูด,ประเภท
วัดพระแก้ว,วัดพระแก้วเป็นวัดที่สำคัญในประเทศไทย,กรุงเทพมหานคร,13.7515,100.4924,วัด
อุทยานประวัติศาสตร์สุโขทัย,อุทยานประวัติศาสตร์ที่มีความสำคัญทางประวัติศาสตร์,สุโขทัย,17.0238,99.7033,อุทยาน
ตลาดน้ำดำเนินสะดวก,ตลาดน้ำที่มีชื่อเสียง,ราชบุรี,13.5177,99.9551,ตลาด"""
        
        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(sample_csv)
            temp_file = f.name
        
        # Test extraction by creating a mock HTTP response
        import unittest.mock
        
        class MockResponse:
            def __init__(self, content):
                self.content = content.encode('utf-8')
            
            def raise_for_status(self):
                pass
        
        with unittest.mock.patch('requests.get') as mock_get:
            mock_get.return_value = MockResponse(sample_csv)
            
            extractor = TATCSVExtractor("http://example.com/test.csv")
            raw_data = extractor.extract()
            
            assert len(raw_data) == 3, f"Expected 3 items, got {len(raw_data)}"
            assert 'ชื่อสถานที่' in raw_data[0], "Missing Thai column name"
            print("✅ TAT CSV Extractor test passed")
            return True
            
    except Exception as e:
        print(f"❌ TAT CSV Extractor test failed: {e}")
        return False


def test_tat_transformer():
    """Test TAT data transformer."""
    print("🧪 Testing TAT Transformer...")
    
    try:
        from transformers.attraction_transformer import AttractionTransformer
        
        # Sample data from CSV extraction
        raw_data = [
            {
                'ชื่อสถานที่': 'วัดพระแก้ว',
                'รายละเอียด': 'วัดพระแก้วเป็นวัดที่สำคัญในประเทศไทย',
                'จังหวัด': 'กรุงเทพมหานคร',
                'ละติจูด': '13.7515',
                'ลองจิจูด': '100.4924',
                'ประเภท': 'วัด'
            },
            {
                'ชื่อสถานที่': 'อุทยานประวัติศาสตร์สุโขทัย',
                'รายละเอียด': 'อุทยานประวัติศาสตร์ที่มีความสำคัญทางประวัติศาสตร์',
                'จังหวัด': 'สุโขทัย',
                'ละติจูด': '17.0238',
                'ลองจิจูด': '99.7033',
                'ประเภท': 'อุทยาน'
            }
        ]
        
        # Transform data (without geocoding to avoid external dependencies)
        attractions = AttractionTransformer.transform_tat_csv_data(
            raw_data, 
            enable_geocoding=False
        )
        
        assert len(attractions) == 2, f"Expected 2 attractions, got {len(attractions)}"
        
        # Check first attraction
        attr1 = attractions[0]
        assert attr1.name == 'วัดพระแก้ว', f"Unexpected name: {attr1.name}"
        assert attr1.province == 'กรุงเทพมหานคร', f"Unexpected province: {attr1.province}"
        assert attr1.latitude == 13.7515, f"Unexpected latitude: {attr1.latitude}"
        assert attr1.source == 'TAT Open Data', f"Unexpected source: {attr1.source}"
        
        print("✅ TAT Transformer test passed")
        return True
        
    except Exception as e:
        print(f"❌ TAT Transformer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tat_model_creation():
    """Test TAT attraction model creation."""
    print("🧪 Testing TAT Model Creation...")
    
    try:
        from app.models import Attraction
        
        # Sample TAT data
        tat_data = {
            'name': 'วัดพระแก้ว',
            'description': 'วัดพระแก้วเป็นวัดที่สำคัญในประเทศไทย',
            'province': 'กรุงเทพมหานคร',
            'category': 'วัด',
            'latitude': 13.7515,
            'longitude': 100.4924,
            'source': 'TAT Open Data'
        }
        
        # Create attraction from TAT data
        attraction = Attraction.create_from_tat_data(tat_data, external_id=1)
        
        assert attraction.name == 'วัดพระแก้ว', f"Unexpected name: {attraction.name}"
        assert attraction.title == 'วัดพระแก้ว', f"Title should match name: {attraction.title}"
        assert attraction.province == 'กรุงเทพมหานคร', f"Unexpected province: {attraction.province}"
        assert attraction.category == 'วัด', f"Unexpected category: {attraction.category}"
        assert attraction.source == 'TAT Open Data', f"Unexpected source: {attraction.source}"
        assert attraction.geocoded == True, "Should be marked as geocoded when coordinates present"
        
        # Test to_dict includes new fields
        data_dict = attraction.to_dict()
        assert 'name' in data_dict, "Missing name field in dict"
        assert 'category' in data_dict, "Missing category field in dict"
        assert 'source' in data_dict, "Missing source field in dict"
        
        print("✅ TAT Model Creation test passed")
        return True
        
    except Exception as e:
        print(f"❌ TAT Model Creation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_import_structure():
    """Test that all required modules can be imported."""
    print("🧪 Testing Import Structure...")
    
    try:
        # Test imports
        from extractors.tat_csv import TATCSVExtractor
        from transformers.attraction_transformer import AttractionTransformer  
        from etl_orchestrator import ETLOrchestrator
        from app.models import Attraction
        
        # Check that TAT CSV ETL method exists
        assert hasattr(ETLOrchestrator, 'run_tat_csv_etl'), "Missing run_tat_csv_etl method"
        
        # Check that TAT transformer method exists
        assert hasattr(AttractionTransformer, 'transform_tat_csv_data'), "Missing transform_tat_csv_data method"
        
        # Check that TAT model creation method exists  
        assert hasattr(Attraction, 'create_from_tat_data'), "Missing create_from_tat_data method"
        
        print("✅ Import Structure test passed")
        return True
        
    except Exception as e:
        print(f"❌ Import Structure test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all TAT ETL tests."""
    print("🧪 Running TAT CSV ETL Tests\n")
    
    tests = [
        test_import_structure,
        test_tat_model_creation,
        test_tat_csv_extractor,
        test_tat_transformer
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            print()  # Add spacing between tests
        except Exception as e:
            print(f"❌ Test {test_func.__name__} crashed: {e}")
            print()
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! TAT CSV ETL implementation is working correctly.")
        return 0
    else:
        print("💥 Some tests failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())