#!/usr/bin/env python3
"""
Test the new ETL structure.
"""
import sys
import os
import json

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_etl_structure():
    """Test that ETL modules can be imported and instantiated."""
    print("Testing ETL structure...")
    
    try:
        # Test extractor imports
        from extractors.external_api import ExternalAPIExtractor
        from extractors.tourism_thailand import TourismThailandExtractor
        from extractors.opentripmap import OpenTripMapExtractor
        print("✅ Extractor modules imported successfully")
        
        # Test transformer imports
        from transformers.attraction_transformer import AttractionTransformer
        print("✅ Transformer modules imported successfully")
        
        # Test loader imports
        from loaders.attraction_loader import AttractionLoader
        print("✅ Loader modules imported successfully")
        
        # Test orchestrator import
        from etl_orchestrator import ETLOrchestrator
        print("✅ ETL orchestrator imported successfully")
        
        # Test instantiation
        extractor = ExternalAPIExtractor("https://test.com")
        assert extractor.api_url == "https://test.com"
        assert extractor.timeout == 30
        print("✅ Extractor instantiation works")
        
        # Test transformer static methods exist
        assert hasattr(AttractionTransformer, 'transform_external_api_data')
        assert hasattr(AttractionTransformer, 'transform_tourism_thailand_data')
        assert hasattr(AttractionTransformer, 'transform_opentripmap_data')
        print("✅ Transformer methods available")
        
        # Test loader static methods exist
        assert hasattr(AttractionLoader, 'load_attractions')
        assert hasattr(AttractionLoader, 'check_duplicate')
        assert hasattr(AttractionLoader, 'bulk_load_attractions')
        print("✅ Loader methods available")
        
        # Test orchestrator static methods exist
        assert hasattr(ETLOrchestrator, 'run_external_api_etl')
        assert hasattr(ETLOrchestrator, 'run_tourism_thailand_etl')
        assert hasattr(ETLOrchestrator, 'run_opentripmap_etl')
        print("✅ ETL orchestrator methods available")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_transformer_logic():
    """Test transformer logic with sample data.""" 
    print("\nTesting transformer logic...")
    
    try:
        from transformers.attraction_transformer import AttractionTransformer
        from app.models import Attraction
        
        # Test external API transformation
        sample_data = [{
            'id': 1,
            'title': 'Test Attraction',
            'body': 'Test description',
            'userId': 123
        }]
        
        attractions = AttractionTransformer.transform_external_api_data(sample_data)
        assert len(attractions) == 1
        assert attractions[0].external_id == 1
        assert attractions[0].title == 'Test Attraction'
        print("✅ External API transformation works")
        
        # Test tourism Thailand transformation with different data format
        tourism_data = [{
            'id': 2,
            'name': 'Tourism Attraction',
            'description': 'Tourism description',
            'location_id': 456
        }]
        
        tourism_attractions = AttractionTransformer.transform_tourism_thailand_data(tourism_data)
        assert len(tourism_attractions) == 1
        assert tourism_attractions[0].external_id == 2
        assert tourism_attractions[0].title == 'Tourism Attraction'
        print("✅ Tourism Thailand transformation works")
        
        return True
        
    except Exception as e:
        print(f"❌ Transformer test error: {e}")
        return False

def test_refactored_imports():
    """Test that refactored tasks.py and routes still work."""
    print("\nTesting refactored imports...")
    
    try:
        # Test that tasks.py can import ETL orchestrator
        import tasks
        print("✅ Refactored tasks.py imports successfully")
        
        # Test that Flask app still works after route changes
        from app import create_app
        app = create_app('testing')
        
        with app.test_client() as client:
            response = client.get('/api/health')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            print("✅ Refactored routes work")
        
        return True
        
    except Exception as e:
        print(f"❌ Refactored imports test error: {e}")
        return False

def main():
    """Run all ETL tests."""
    print("🧪 Testing new ETL structure...\n")
    
    tests = [
        test_etl_structure,
        test_transformer_logic,
        test_refactored_imports
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            failed += 1
    
    print(f"\n📊 ETL Test Results:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 All ETL tests passed! The restructuring is working correctly.")
        print("\n📁 New ETL Structure:")
        print("├── extractors/")
        print("│   ├── external_api.py      # JSONPlaceholder API extractor")
        print("│   ├── tourism_thailand.py  # Tourism Thailand API extractor")  
        print("│   └── opentripmap.py       # OpenTripMap API extractor")
        print("├── transformers/")
        print("│   └── attraction_transformer.py  # Data transformation logic")
        print("├── loaders/")
        print("│   └── attraction_loader.py       # Database loading & deduplication")
        print("└── etl_orchestrator.py            # ETL pipeline coordination")
        return 0
    else:
        print("\n💥 Some ETL tests failed. Please check the errors above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())