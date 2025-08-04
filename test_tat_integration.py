#!/usr/bin/env python3
"""
Comprehensive test for TAT ETL integration.
Tests the complete TAT ETL pipeline integration with the existing system.
"""

import sys
import logging
import unittest.mock
from io import StringIO

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_complete_integration():
    """Test complete TAT ETL integration without database."""
    print("🧪 Testing Complete TAT ETL Integration")
    print("=" * 50)
    
    try:
        # Test 1: Import all required modules
        print("📦 Testing imports...")
        from extractors.tat_csv import TATCSVExtractor
        from transformers.attraction_transformer import AttractionTransformer
        from etl_orchestrator import ETLOrchestrator
        from app.models import Attraction
        print("✅ All modules imported successfully")
        
        # Test 2: Verify orchestrator has TAT method
        print("🔧 Testing orchestrator...")
        assert hasattr(ETLOrchestrator, 'run_tat_csv_etl'), "Missing run_tat_csv_etl method"
        print("✅ ETL orchestrator has TAT CSV method")
        
        # Test 3: Test model enhancements
        print("🗄️ Testing model enhancements...")
        
        # Test new fields in model
        attraction = Attraction()
        required_fields = ['name', 'description', 'address', 'district', 'category', 
                          'opening_hours', 'entrance_fee', 'contact_phone', 'source']
        
        for field in required_fields:
            assert hasattr(attraction, field), f"Missing field: {field}"
        
        # Test TAT data creation
        tat_data = {
            'name': 'วัดพระแก้ว',
            'description': 'วัดสำคัญของไทย',
            'address': '123 ถนนพระนคร',
            'district': 'พระนคร',
            'province': 'กรุงเทพมหานคร',
            'category': 'วัด',
            'opening_hours': '08:30-15:30',
            'entrance_fee': '500 บาท',
            'contact_phone': '02-123-4567',
            'latitude': 13.7515,
            'longitude': 100.4924,
            'source': 'TAT Open Data'
        }
        
        attraction = Attraction.create_from_tat_data(tat_data, external_id=1)
        assert attraction.name == 'วัดพระแก้ว'
        assert attraction.category == 'วัด'
        assert attraction.source == 'TAT Open Data'
        assert attraction.geocoded == True  # Should be True when coordinates provided
        
        # Test to_dict includes new fields
        data_dict = attraction.to_dict()
        for field in required_fields:
            assert field in data_dict, f"Missing field {field} in to_dict output"
        
        print("✅ Model enhancements working correctly")
        
        # Test 4: Test CSV extraction with mock data
        print("📊 Testing CSV extraction...")
        
        sample_csv = """ชื่อสถานที่,รายละเอียด,จังหวัด,อำเภอ,ละติจูด,ลองจิจูด,ประเภท,เวลาเปิด,ค่าเข้าชม,โทรศัพท์
วัดพระแก้ว,วัดพระแก้วเป็นวัดที่สำคัญในประเทศไทย,กรุงเทพมหานคร,พระนคร,13.7515,100.4924,วัด,08:30-15:30,500 บาท,02-123-4567
อุทยานประวัติศาสตร์สุโขทัย,อุทยานประวัติศาสตร์ที่มีความสำคัญทางประวัติศาสตร์,สุโขทัย,เมืองสุโขทัย,17.0238,99.7033,อุทยาน,06:00-18:00,100 บาท,055-123-456"""
        
        class MockResponse:
            def __init__(self, content):
                self.content = content.encode('utf-8')
            def raise_for_status(self):
                pass
        
        with unittest.mock.patch('requests.get') as mock_get:
            mock_get.return_value = MockResponse(sample_csv)
            
            extractor = TATCSVExtractor("http://test.com/attractions.csv")
            raw_data = extractor.extract()
            
            assert len(raw_data) == 2, f"Expected 2 items, got {len(raw_data)}"
            assert 'ชื่อสถานที่' in raw_data[0], "Missing Thai column"
        
        print("✅ CSV extraction working correctly")
        
        # Test 5: Test transformation
        print("🔄 Testing transformation...")
        
        attractions = AttractionTransformer.transform_tat_csv_data(raw_data, enable_geocoding=False)
        
        assert len(attractions) == 2, f"Expected 2 attractions, got {len(attractions)}"
        
        # Check first attraction details
        attr1 = attractions[0]
        assert attr1.name == 'วัดพระแก้ว'
        assert attr1.province == 'กรุงเทพมหานคร'
        assert attr1.district == 'พระนคร'
        assert attr1.category == 'วัด'
        assert attr1.opening_hours == '08:30-15:30'
        assert attr1.entrance_fee == '500 บาท'
        assert attr1.contact_phone == '02-123-4567'
        assert attr1.latitude == 13.7515
        assert attr1.longitude == 100.4924
        assert attr1.source == 'TAT Open Data'
        
        print("✅ Transformation working correctly")
        
        # Test 6: Test task and route definitions exist
        print("🚀 Testing task and route definitions...")
        
        try:
            from tasks import fetch_tat_attractions_task
            print("✅ TAT ETL task defined")
        except ImportError:
            print("❌ TAT ETL task not found")
            return False
        
        # Check if route exists by looking at the file
        with open('app/routes/attractions.py', 'r') as f:
            routes_content = f.read()
            if '/attractions/sync/tat' in routes_content:
                print("✅ TAT sync route defined")
            else:
                print("❌ TAT sync route not found")
                return False
        
        # Check scheduler
        with open('scheduler.py', 'r') as f:
            scheduler_content = f.read()
            if 'fetch_tat_attractions_task' in scheduler_content:
                print("✅ TAT ETL scheduled")
            else:
                print("❌ TAT ETL not in scheduler")
                return False
        
        print("✅ All integration tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def print_implementation_summary():
    """Print summary of the TAT ETL implementation."""
    print("\n🎯 TAT ETL Implementation Summary")
    print("=" * 50)
    print()
    print("📁 Files Created/Modified:")
    print("   • extractors/tat_csv.py - TAT CSV data extractor")
    print("   • app/models.py - Enhanced with tourism fields")
    print("   • transformers/attraction_transformer.py - Added TAT transformer")
    print("   • etl_orchestrator.py - Added TAT ETL orchestration")
    print("   • tasks.py - Added TAT ETL background task")
    print("   • app/routes/attractions.py - Added TAT sync endpoint")
    print("   • scheduler.py - Added weekly TAT ETL schedule")
    print()
    print("🔌 API Endpoints:")
    print("   • POST /api/attractions/sync/tat - Manual TAT sync")
    print("     Parameters: csv_url (optional), enable_geocoding (optional)")
    print()
    print("⏰ Scheduled Tasks:")
    print("   • Weekly TAT ETL - Every Monday at 1:30 AM")
    print()
    print("🛠️ Usage Examples:")
    print("   1. Manual sync via API:")
    print("      curl -X POST http://localhost:5000/api/attractions/sync/tat")
    print()
    print("   2. Manual sync with custom URL:")
    print("      curl -X POST http://localhost:5000/api/attractions/sync/tat \\")
    print("           -H 'Content-Type: application/json' \\")
    print("           -d '{\"csv_url\": \"https://example.com/data.csv\"}'")
    print()
    print("   3. Run ETL programmatically:")
    print("      from etl_orchestrator import ETLOrchestrator")
    print("      result = ETLOrchestrator.run_tat_csv_etl(csv_url)")
    print()
    print("🗄️ Database Schema:")
    print("   Enhanced Attraction model with fields:")
    print("   • name, description, address, district, category")
    print("   • opening_hours, entrance_fee, contact_phone, source")
    print("   • Backward compatible with existing title/body fields")
    print()
    print("🔄 ETL Process:")
    print("   1. Extract: Download CSV from TAT Open Data")
    print("   2. Transform: Convert to database format with field mapping")
    print("   3. Load: Insert/update with duplicate checking")
    print("   4. Optional: Geocoding for missing coordinates")


def main():
    """Run integration tests and show summary."""
    print("🧪 TAT ETL Integration Tests\n")
    
    # Run integration test
    if test_complete_integration():
        print_implementation_summary()
        print("\n🎉 TAT ETL implementation is complete and working!")
        print("\n💡 Next steps:")
        print("   1. Deploy the application with updated code")
        print("   2. Test the API endpoint manually")
        print("   3. Monitor the scheduled weekly ETL runs")
        print("   4. Consider enabling geocoding with Google API key")
        return 0
    else:
        print("\n💥 Some tests failed. Please review the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())