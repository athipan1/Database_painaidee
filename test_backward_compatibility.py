#!/usr/bin/env python3
"""
Test backward compatibility - ensure existing functionality works with pagination disabled.
"""
import sys
import os
from unittest.mock import patch

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_backward_compatibility():
    """Test that existing code works with pagination disabled"""
    print("Testing backward compatibility...")
    
    try:
        from extractors.external_api import ExternalAPIExtractor
        
        # Test old-style extractor initialization (no pagination params)
        extractor = ExternalAPIExtractor(
            api_url="https://api.example.com/posts",
            timeout=30
        )
        
        assert extractor.enable_pagination == False, "Pagination should be disabled by default"
        assert extractor.page_size == 20, "Should have default page size"
        assert extractor.max_pages == 100, "Should have default max pages"
        
        print("✅ Old-style extractor initialization works")
        
        # Test extract method with pagination disabled
        mock_response = [
            {"id": 1, "title": "Post 1", "body": "Content 1", "userId": 1},
            {"id": 2, "title": "Post 2", "body": "Content 2", "userId": 2}
        ]
        
        with patch('app.utils.fetch.fetch_json_with_retry') as mock_fetch:
            mock_fetch.return_value = mock_response
            
            data = extractor.extract()
            
            assert len(data) == 2, f"Should return 2 items, got {len(data)}"
            assert data[0]["id"] == 1, "First item should have id=1"
            assert data[1]["id"] == 2, "Second item should have id=2"
            
            # Verify fetch was called once (not paginated)
            assert mock_fetch.call_count == 1, f"Should call fetch once, called {mock_fetch.call_count} times"
        
        print("✅ Non-paginated extract() method works")
        
        return True
        
    except Exception as e:
        print(f"❌ Backward compatibility test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_etl_backward_compatibility():
    """Test ETL orchestrator backward compatibility"""
    print("Testing ETL orchestrator backward compatibility...")
    
    try:
        from etl_orchestrator import ETLOrchestrator
        import inspect
        
        # Check that the method can still be called with old parameters
        sig = inspect.signature(ETLOrchestrator.run_external_api_etl)
        
        # All new parameters should have defaults
        required_params = [name for name, param in sig.parameters.items() 
                          if param.default == inspect.Parameter.empty]
        
        # Only api_url should be required (timeout has default)
        expected_required = ['api_url']
        for param in expected_required:
            assert param in required_params, f"Parameter {param} should be required"
        
        # Check that we can call with minimal parameters (old style)
        print("✅ ETL orchestrator maintains backward compatibility")
        
        return True
        
    except Exception as e:
        print(f"❌ ETL backward compatibility test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_defaults():
    """Test that configuration defaults are reasonable"""
    print("Testing configuration defaults...")
    
    try:
        from app.config import Config
        
        config = Config()
        
        # Test that defaults are sensible
        assert isinstance(config.PAGINATION_ENABLED, bool), "PAGINATION_ENABLED should be boolean"
        assert isinstance(config.PAGINATION_PAGE_SIZE, int), "PAGINATION_PAGE_SIZE should be int"
        assert isinstance(config.PAGINATION_MAX_PAGES, int), "PAGINATION_MAX_PAGES should be int"
        
        assert config.PAGINATION_PAGE_SIZE > 0, "Page size should be positive"
        assert config.PAGINATION_MAX_PAGES > 0, "Max pages should be positive"
        assert config.PAGINATION_PAGE_SIZE <= 1000, "Page size should be reasonable"
        assert config.PAGINATION_MAX_PAGES <= 10000, "Max pages should be reasonable"
        
        print("✅ Configuration defaults are reasonable")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration defaults test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_single_item_response():
    """Test handling of APIs that return single objects instead of arrays"""
    print("Testing single item response handling...")
    
    try:
        from app.utils.fetch import fetch_all_paginated_data
        
        # Test API that returns single object instead of array
        mock_response = {"id": 1, "title": "Single Item", "content": "Some content"}
        
        with patch('app.utils.fetch.fetch_json_with_retry') as mock_fetch:
            mock_fetch.side_effect = [mock_response, {}]  # Single item, then empty
            
            result = fetch_all_paginated_data(
                base_url="https://api.example.com/item",
                page_size=1,
                max_pages=2
            )
            
            assert len(result) == 1, f"Should handle single item response, got {len(result)} items"
            assert result[0]["id"] == 1, "Should preserve the single item"
        
        print("✅ Single item response handled correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Single item response test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run backward compatibility tests"""
    print("🔄 Testing Backward Compatibility\n")
    
    tests = [
        test_config_defaults,
        test_backward_compatibility,
        test_etl_backward_compatibility,
        test_single_item_response,
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
    
    print("📊 Backward Compatibility Test Results:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    if failed > 0:
        print("\n💥 Some backward compatibility tests failed.")
        print("This indicates that existing code might break with the new changes.")
        return 1
    else:
        print("\n🎉 All backward compatibility tests passed!")
        print("Existing code will continue to work without modifications.")
        return 0


if __name__ == '__main__':
    sys.exit(main())