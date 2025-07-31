#!/usr/bin/env python3
"""
Test pagination functionality.
"""
import sys
import os
import unittest
import importlib
from unittest.mock import patch, MagicMock
import json

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_pagination_utilities():
    """Test the pagination utilities in fetch.py"""
    print("Testing pagination utilities...")
    
    try:
        from app.utils.fetch import fetch_paginated_data, fetch_all_paginated_data
        print("✅ Pagination utilities imported successfully")
        
        # Mock response data for testing
        mock_page1 = [{"id": 1, "title": "Test 1"}, {"id": 2, "title": "Test 2"}]
        mock_page2 = [{"id": 3, "title": "Test 3"}]
        mock_empty = []
        
        with patch('app.utils.fetch.fetch_json_with_retry') as mock_fetch:
            # Configure mock to return different pages
            mock_fetch.side_effect = [mock_page1, mock_page2, mock_empty]
            
            # Test fetch_all_paginated_data
            result = fetch_all_paginated_data(
                base_url="https://test.api.com/items",
                page_size=2,
                max_pages=3
            )
            
            # Verify results
            assert len(result) == 3, f"Expected 3 items, got {len(result)}"
            assert result[0]["id"] == 1, "First item should have id=1"
            assert result[2]["id"] == 3, "Third item should have id=3"
            
            print("✅ fetch_all_paginated_data works correctly")
            
            # Test individual page iteration
            mock_fetch.side_effect = [mock_page1, mock_page2, mock_empty]
            pages = list(fetch_paginated_data(
                base_url="https://test.api.com/items",
                page_size=2,
                max_pages=3
            ))
            
            assert len(pages) == 2, f"Expected 2 pages, got {len(pages)}"
            assert pages[0][0] == 1, "First page number should be 1"
            assert len(pages[0][1]) == 2, "First page should have 2 items"
            assert pages[1][0] == 2, "Second page number should be 2"
            assert len(pages[1][1]) == 1, "Second page should have 1 item"
            
            print("✅ fetch_paginated_data iteration works correctly")
            
    except Exception as e:
        print(f"❌ Pagination utilities test failed: {e}")
        return False
    
    return True


def test_external_api_extractor():
    """Test the updated ExternalAPIExtractor with pagination support"""
    print("Testing ExternalAPIExtractor with pagination...")
    
    try:
        from extractors.external_api import ExternalAPIExtractor
        print("✅ ExternalAPIExtractor imported successfully")
        
        # Test initialization with pagination
        extractor = ExternalAPIExtractor(
            api_url="https://test.api.com/items",
            timeout=30,
            enable_pagination=True,
            page_size=10,
            max_pages=5
        )
        
        assert extractor.enable_pagination == True, "Pagination should be enabled"
        assert extractor.page_size == 10, "Page size should be 10"
        assert extractor.max_pages == 5, "Max pages should be 5"
        
        print("✅ ExternalAPIExtractor initialization with pagination works")
        
        # Test without pagination (backward compatibility)
        extractor_legacy = ExternalAPIExtractor(
            api_url="https://test.api.com/items",
            timeout=30
        )
        
        assert extractor_legacy.enable_pagination == False, "Pagination should be disabled by default"
        
        print("✅ ExternalAPIExtractor backward compatibility maintained")
        
    except Exception as e:
        print(f"❌ ExternalAPIExtractor test failed: {e}")
        return False
    
    return True


def test_configuration():
    """Test the configuration updates"""
    print("Testing configuration updates...")
    
    try:
        from app.config import Config
        
        # Test default values (will use environment or defaults)
        config = Config()
        assert hasattr(config, 'PAGINATION_ENABLED'), "PAGINATION_ENABLED should be defined"
        assert hasattr(config, 'PAGINATION_PAGE_SIZE'), "PAGINATION_PAGE_SIZE should be defined"
        assert hasattr(config, 'PAGINATION_MAX_PAGES'), "PAGINATION_MAX_PAGES should be defined"
        
        # Test that they are the expected types
        assert isinstance(config.PAGINATION_ENABLED, bool), "PAGINATION_ENABLED should be boolean"
        assert isinstance(config.PAGINATION_PAGE_SIZE, int), "PAGINATION_PAGE_SIZE should be int"
        assert isinstance(config.PAGINATION_MAX_PAGES, int), "PAGINATION_MAX_PAGES should be int"
        
        print("✅ Configuration has correct pagination settings with proper types")
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False
    
    return True


def test_etl_orchestrator():
    """Test the updated ETL orchestrator"""
    print("Testing ETL orchestrator with pagination...")
    
    try:
        from etl_orchestrator import ETLOrchestrator
        print("✅ ETLOrchestrator imported successfully")
        
        # Test method signature
        import inspect
        sig = inspect.signature(ETLOrchestrator.run_external_api_etl)
        
        expected_params = [
            'api_url', 'timeout', 'enable_pagination', 
            'page_size', 'max_pages', 'use_memory_efficient'
        ]
        
        for param in expected_params:
            assert param in sig.parameters, f"Parameter {param} should be in method signature"
        
        print("✅ ETLOrchestrator method signature updated correctly")
        
    except Exception as e:
        print(f"❌ ETL orchestrator test failed: {e}")
        return False
    
    return True


def test_api_response_formats():
    """Test handling of different API response formats"""
    print("Testing different API response formats...")
    
    try:
        from app.utils.fetch import fetch_all_paginated_data
        
        # Test direct list response
        with patch('app.utils.fetch.fetch_json_with_retry') as mock_fetch:
            mock_fetch.side_effect = [
                [{"id": 1, "title": "Item 1"}],
                []  # Empty page to stop iteration
            ]
            
            result = fetch_all_paginated_data("https://test.api.com", page_size=1, max_pages=2)
            assert len(result) == 1, f"Should handle direct list response, got {len(result)} items"
            print("✅ Direct list response handled correctly")
        
        # Test object with 'data' field 
        with patch('app.utils.fetch.fetch_json_with_retry') as mock_fetch:
            mock_fetch.side_effect = [
                {"data": [{"id": 1, "title": "Item 1"}]},
                {"data": []}  # Empty data to stop iteration, no extra metadata
            ]
            
            result = fetch_all_paginated_data("https://test.api.com", page_size=1, max_pages=2)
            assert len(result) == 1, f"Should handle object with 'data' field, got {len(result)} items"
            print("✅ Object with 'data' field handled correctly")
        
        # Test object with 'items' field  
        with patch('app.utils.fetch.fetch_json_with_retry') as mock_fetch:
            mock_fetch.side_effect = [
                {"items": [{"id": 1, "title": "Item 1"}]},
                {"items": []}  # Empty items to stop iteration
            ]
            
            result = fetch_all_paginated_data("https://test.api.com", page_size=1, max_pages=2)
            assert len(result) == 1, f"Should handle object with 'items' field, got {len(result)} items"
            print("✅ Object with 'items' field handled correctly")
            
        print("✅ Different API response formats handled correctly")
            
    except Exception as e:
        print(f"❌ API response formats test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def main():
    """Run all tests"""
    print("🧪 Running pagination functionality tests...\n")
    
    tests = [
        test_configuration,
        test_pagination_utilities,
        test_external_api_extractor,
        test_etl_orchestrator,
        test_api_response_formats,
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
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            failed += 1
        print()
    
    print("📊 Test Results:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    if failed > 0:
        print("\n💥 Some tests failed. Please check the errors above.")
        return 1
    else:
        print("\n🎉 All tests passed!")
        return 0


if __name__ == '__main__':
    sys.exit(main())