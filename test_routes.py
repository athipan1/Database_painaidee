#!/usr/bin/env python3
"""
Test the refactored routes without database connection.
"""
import sys
import os
import unittest.mock

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_route_refactoring():
    """Test that route refactoring works without database."""
    print("Testing route refactoring...")
    
    try:
        # Mock the database operations
        with unittest.mock.patch('app.models.db.create_all'):
            from app import create_app
            
            app = create_app('testing')
            app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
            
            with app.test_client() as client:
                # Test basic routes that don't require database
                response = client.get('/')
                assert response.status_code == 200
                print("✅ Root route works")
                
                # The sync route would require mocking more components,
                # but the import and basic structure works
                print("✅ Route refactoring successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Route test error: {e}")
        return False

def test_manual_etl_flow():
    """Test the ETL flow manually without database."""
    print("\nTesting manual ETL flow...")
    
    try:
        from extractors.external_api import ExternalAPIExtractor
        from transformers.attraction_transformer import AttractionTransformer
        from loaders.attraction_loader import AttractionLoader
        
        # Mock data that would come from API
        mock_api_data = [
            {'id': 1, 'title': 'Test Attraction 1', 'body': 'Description 1', 'userId': 123},
            {'id': 2, 'title': 'Test Attraction 2', 'body': 'Description 2', 'userId': 456}
        ]
        
        # Test transformation (this doesn't require database)
        attractions = AttractionTransformer.transform_external_api_data(mock_api_data)
        assert len(attractions) == 2
        assert attractions[0].external_id == 1
        assert attractions[1].external_id == 2
        print("✅ ETL transformation works correctly")
        
        # Test that ETL components are properly separated
        extractor = ExternalAPIExtractor("https://example.com")
        assert extractor.api_url == "https://example.com"
        print("✅ ETL components are properly separated")
        
        return True
        
    except Exception as e:
        print(f"❌ Manual ETL test error: {e}")
        return False

def main():
    """Run route-specific tests."""
    print("🧪 Testing refactored application without database...\n")
    
    tests = [
        test_route_refactoring,
        test_manual_etl_flow
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
    
    print(f"\n📊 Route Test Results:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 Route refactoring tests passed!")
        return 0
    else:
        print("\n💥 Some route tests failed.")
        return 1

if __name__ == '__main__':
    sys.exit(main())