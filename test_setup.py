#!/usr/bin/env python3
"""
Simple test script to verify the application setup.
Run this after setting up the environment to test basic functionality.
"""
import sys
import os
import json
import sqlite3
from datetime import datetime

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    
    try:
        # Test app imports
        from app.config import Config
        from app.models import Attraction
        print("✅ App modules imported successfully")
        
        # Test configuration
        config = Config()
        assert hasattr(config, 'SECRET_KEY')
        assert hasattr(config, 'SQLALCHEMY_DATABASE_URI')
        print("✅ Configuration loaded successfully")
        
        # Test model structure
        attraction_fields = ['id', 'external_id', 'title', 'body', 'user_id', 'created_at', 'updated_at']
        for field in attraction_fields:
            assert hasattr(Attraction, field), f"Missing field: {field}"
        print("✅ Attraction model structure verified")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_model_methods():
    """Test model methods."""
    print("\nTesting model methods...")
    
    try:
        from app.models import Attraction
        
        # Test model creation from external data
        sample_data = {
            'id': 1,
            'title': 'Test Attraction',
            'body': 'Test description',
            'userId': 123
        }
        
        attraction = Attraction.create_from_external_data(sample_data)
        assert attraction.external_id == 1
        assert attraction.title == 'Test Attraction'
        assert attraction.body == 'Test description'
        assert attraction.user_id == 123
        print("✅ Model creation from external data works")
        
        # Test to_dict method
        attraction.id = 1
        attraction.created_at = datetime.now()
        attraction.updated_at = datetime.now()
        
        data_dict = attraction.to_dict()
        assert 'id' in data_dict
        assert 'external_id' in data_dict
        assert 'title' in data_dict
        print("✅ Model to_dict method works")
        
        return True
        
    except Exception as e:
        print(f"❌ Model test error: {e}")
        return False

def test_app_factory():
    """Test Flask app factory."""
    print("\nTesting Flask app factory...")
    
    try:
        from app import create_app
        
        # Create test app
        app = create_app('testing')
        assert app is not None
        assert app.config['TESTING'] is True
        print("✅ Flask app factory works")
        
        # Test that routes are registered
        with app.test_client() as client:
            response = client.get('/')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'message' in data
            assert 'endpoints' in data
            print("✅ Root endpoint works")
            
            # Test health endpoint
            response = client.get('/api/health')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            print("✅ Health endpoint works")
        
        return True
        
    except Exception as e:
        print(f"❌ App factory test error: {e}")
        return False

def test_celery_config():
    """Test Celery configuration."""
    print("\nTesting Celery configuration...")
    
    try:
        from tasks import celery
        from scheduler import celery_app
        
        # Test that celery instances are created
        assert celery is not None
        assert celery_app is not None
        
        # Test configuration
        assert celery.conf.task_serializer == 'json'
        assert celery.conf.timezone == 'Asia/Bangkok'
        print("✅ Celery configuration loaded")
        
        # Test scheduler configuration
        beat_schedule = celery_app.conf.beat_schedule
        assert 'fetch-attractions-daily' in beat_schedule
        daily_task = beat_schedule['fetch-attractions-daily']
        assert daily_task['task'] == 'tasks.fetch_attractions_task'
        print("✅ Celery beat schedule configured")
        
        return True
        
    except Exception as e:
        print(f"❌ Celery test error: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Running application tests...\n")
    
    tests = [
        test_imports,
        test_model_methods,
        test_app_factory,
        test_celery_config
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
        print("\n🎉 All tests passed! Your Flask backend setup is ready.")
        print("\n📋 Next steps:")
        print("1. Copy .env.example to .env and adjust settings if needed")
        print("2. Run: docker compose up -d")
        print("3. Test API endpoints:")
        print("   - GET http://localhost:5000/")
        print("   - GET http://localhost:5000/api/health")
        print("   - GET http://localhost:5000/api/attractions")
        print("   - POST http://localhost:5000/api/attractions/sync")
        return 0
    else:
        print("\n💥 Some tests failed. Please check the errors above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())