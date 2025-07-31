#!/usr/bin/env python3
"""
Test script to verify the retry functionality with tenacity.
"""
import sys
import os
import json
import time
import logging
from unittest.mock import patch, Mock
from datetime import datetime

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging to see retry attempts
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_fetch_utility_import():
    """Test that the fetch utility can be imported."""
    print("Testing fetch utility import...")
    try:
        from app.utils.fetch import fetch_with_retry, fetch_json_with_retry
        print("✅ Fetch utilities imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_fetch_with_retry_success():
    """Test successful fetch without retries."""
    print("\nTesting successful fetch without retries...")
    try:
        from app.utils.fetch import fetch_json_with_retry
        import requests
        
        # Mock successful response
        with patch('requests.request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = [{'id': 1, 'title': 'Test'}]
            mock_response.raise_for_status.return_value = None
            mock_request.return_value = mock_response
            
            # Call the function
            result = fetch_json_with_retry('https://test.com/api', timeout=10)
            
            # Verify
            assert result == [{'id': 1, 'title': 'Test'}]
            assert mock_request.call_count == 1
            print("✅ Successful fetch without retries works")
            return True
            
    except Exception as e:
        print(f"❌ Fetch success test error: {e}")
        return False

def test_fetch_with_retry_on_timeout():
    """Test retry behavior on timeout."""
    print("\nTesting retry behavior on timeout...")
    try:
        from app.utils.fetch import fetch_json_with_retry
        import requests
        
        # Mock timeout then success
        with patch('requests.request') as mock_request:
            # First 3 calls timeout, 4th succeeds
            timeout_response = Mock()
            timeout_response.side_effect = requests.exceptions.Timeout("Request timed out")
            
            success_response = Mock()
            success_response.status_code = 200
            success_response.json.return_value = [{'id': 1, 'title': 'Test'}]
            success_response.raise_for_status.return_value = None
            
            mock_request.side_effect = [
                requests.exceptions.Timeout("Request timed out"),
                requests.exceptions.Timeout("Request timed out"),
                requests.exceptions.Timeout("Request timed out"),
                success_response
            ]
            
            # Call the function - should succeed after retries
            result = fetch_json_with_retry('https://test.com/api', timeout=10)
            
            # Verify
            assert result == [{'id': 1, 'title': 'Test'}]
            assert mock_request.call_count == 4  # 1 initial + 3 retries
            print("✅ Retry on timeout works (4 attempts total)")
            return True
            
    except Exception as e:
        print(f"❌ Retry timeout test error: {e}")
        return False

def test_fetch_with_retry_on_http_error():
    """Test retry behavior on HTTP errors."""
    print("\nTesting retry behavior on HTTP errors...")
    try:
        from app.utils.fetch import fetch_json_with_retry
        import requests
        
        # Mock HTTP error then success
        with patch('requests.request') as mock_request:
            # First 2 calls return 500 error, 3rd succeeds
            error_response = Mock()
            error_response.status_code = 500
            error_response.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error")
            
            success_response = Mock()
            success_response.status_code = 200
            success_response.json.return_value = [{'id': 1, 'title': 'Test'}]
            success_response.raise_for_status.return_value = None
            
            mock_request.side_effect = [
                error_response,
                error_response,
                success_response
            ]
            
            # Call the function - should succeed after retries
            result = fetch_json_with_retry('https://test.com/api', timeout=10)
            
            # Verify
            assert result == [{'id': 1, 'title': 'Test'}]
            assert mock_request.call_count == 3  # 1 initial + 2 retries
            print("✅ Retry on HTTP error works (3 attempts total)")
            return True
            
    except Exception as e:
        print(f"❌ Retry HTTP error test error: {e}")
        return False

def test_fetch_exhausts_retries():
    """Test that retries are exhausted and exception is raised."""
    print("\nTesting retry exhaustion...")
    try:
        from app.utils.fetch import fetch_json_with_retry
        from tenacity import RetryError
        import requests
        
        # Mock continuous failures
        with patch('requests.request') as mock_request:
            mock_request.side_effect = requests.exceptions.Timeout("Request timed out")
            
            # Call the function - should fail after all retries
            try:
                result = fetch_json_with_retry('https://test.com/api', timeout=10)
                print("❌ Should have raised exception after retries exhausted")
                return False
            except RetryError:
                # Should have tried 4 times (1 initial + 3 retries)
                assert mock_request.call_count == 4
                print("✅ Retry exhaustion works correctly (4 attempts total)")
                return True
            
    except Exception as e:
        print(f"❌ Retry exhaustion test error: {e}")
        return False

def test_updated_tasks_import():
    """Test that updated tasks.py can be imported."""
    print("\nTesting updated tasks.py import...")
    try:
        # Mock Flask app context and celery to avoid configuration issues
        with patch('app.create_app') as mock_create_app, \
             patch('app.create_celery_app') as mock_create_celery:
            
            mock_app = Mock()
            mock_app.config = {
                'EXTERNAL_API_URL': 'https://test.com/api',
                'API_TIMEOUT': 30,
                'CELERY_BROKER_URL': 'redis://localhost:6379/0',
                'CELERY_RESULT_BACKEND': 'redis://localhost:6379/0'
            }
            mock_create_app.return_value = mock_app
            
            mock_celery = Mock()
            mock_create_celery.return_value = mock_celery
            
            import tasks
            assert hasattr(tasks, 'fetch_attractions_task')
            print("✅ Updated tasks.py imports successfully")
            return True
            
    except ImportError as e:
        print(f"❌ Tasks import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Tasks test error: {e}")
        return False

def test_updated_routes_import():
    """Test that updated routes can be imported."""
    print("\nTesting updated routes import...")
    try:
        from app.routes.attractions import attractions_bp
        assert attractions_bp is not None
        print("✅ Updated routes import successfully")
        return True
    except ImportError as e:
        print(f"❌ Routes import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Routes test error: {e}")
        return False

def main():
    """Run all retry functionality tests."""
    print("🧪 Running retry functionality tests...\n")
    
    tests = [
        test_fetch_utility_import,
        test_fetch_with_retry_success,
        test_fetch_with_retry_on_timeout,
        test_fetch_with_retry_on_http_error,
        test_fetch_exhausts_retries,
        test_updated_tasks_import,
        test_updated_routes_import
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
    
    print(f"\n📊 Test Results:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 All retry functionality tests passed!")
        print("\n✨ Retry system features:")
        print("   - Exponential backoff with jitter (1s, 2s, 4s, 8s)")
        print("   - Retries on timeout, connection errors, and HTTP errors")
        print("   - Structured logging of retry attempts")
        print("   - Maximum 4 attempts (1 initial + 3 retries)")
        print("   - Integrated into both Celery tasks and API routes")
        return 0
    else:
        print("\n💥 Some tests failed. Please check the errors above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())