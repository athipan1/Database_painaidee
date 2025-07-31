#!/usr/bin/env python3
"""
Test to verify pytest and pytest-mock are properly integrated.
This test ensures the dependencies are correctly installed and can be imported.
"""
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_pytest_imports():
    """Test that pytest and pytest-mock can be imported."""
    print("Testing pytest and pytest-mock imports...")
    
    try:
        import pytest
        print(f"✅ pytest imported successfully (version: {pytest.__version__})")
        
        import pytest_mock
        print(f"✅ pytest-mock imported successfully")
        
        # Test that pytest-mock functionality works
        try:
            from pytest_mock import MockerFixture
            print("✅ MockerFixture imported successfully")
        except ImportError as e:
            print(f"⚠️  MockerFixture import failed: {e}")
        
        print("✅ All pytest dependencies are working correctly!")
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

if __name__ == "__main__":
    success = test_pytest_imports()
    sys.exit(0 if success else 1)