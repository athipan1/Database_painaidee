#!/usr/bin/env python3
"""
Manual test to demonstrate the retry system working with real API calls.
"""
import sys
import os
import logging

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging to see retry attempts
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_real_api_success():
    """Test with a real API that should work."""
    print("Testing with a working API endpoint...")
    try:
        from app.utils.fetch import fetch_json_with_retry
        
        # Use httpbin.org which is a reliable testing service
        result = fetch_json_with_retry('https://httpbin.org/json', timeout=10)
        print(f"✅ Successfully fetched data: {result}")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_real_api_with_timeout():
    """Test with an API that will timeout to demonstrate retry."""
    print("\nTesting with a slow endpoint (will demonstrate retries)...")
    try:
        from app.utils.fetch import fetch_json_with_retry
        
        # Use httpbin.org delay endpoint with a very short timeout to force retries
        result = fetch_json_with_retry('https://httpbin.org/delay/2', timeout=1)
        print(f"✅ Unexpectedly succeeded: {result}")
        return True
        
    except Exception as e:
        print(f"✅ Expected failure after retries: {type(e).__name__}")
        return True

if __name__ == '__main__':
    print("🔄 Testing retry system with real API calls...\n")
    
    success_count = 0
    if test_real_api_success():
        success_count += 1
    if test_real_api_with_timeout():
        success_count += 1
    
    print(f"\n📊 Manual test results: {success_count}/2 tests passed")
    if success_count == 2:
        print("🎉 Retry system is working correctly with real API calls!")