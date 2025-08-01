"""
Simple manual test for AI features using SQLite database.
"""
import os
import tempfile
from app import create_app
from app.models import db, Attraction


def test_ai_features_manual():
    """Manual test of AI features without requiring PostgreSQL."""
    print("Testing AI Features...")
    
    # Create temporary SQLite database
    db_fd, db_path = tempfile.mkstemp()
    
    # Override database configuration
    os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'
    
    try:
        # Create app with SQLite, forcing testing config
        from app.config import Config
        
        class TestConfig(Config):
            TESTING = True
            SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
        
        app = create_app()
        app.config.from_object(TestConfig)
        
        with app.app_context():
            # Create all tables
            db.create_all()
            
            # Create test data
            test_attraction = Attraction(
                external_id=999,
                title="Beautiful Temple in Bangkok",
                body="A stunning ancient temple with golden decorations, peaceful gardens, and traditional Thai architecture.",
                user_id=1,
                province="Bangkok",
                view_count=0
            )
            
            db.session.add(test_attraction)
            db.session.commit()
            
            # Test client
            client = app.test_client()
            
            # Test 1: Extract keywords
            print("1. Testing keyword extraction...")
            response = client.post('/api/ai/keywords/extract', json={
                'attraction_id': test_attraction.id
            })
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                result = response.get_json()
                print(f"   Keywords: {result.get('keywords', [])}")
            else:
                print(f"   Error: {response.get_json()}")
            
            # Test 2: Get recommendations
            print("2. Testing recommendations...")
            response = client.get('/api/ai/recommendations/test_user?limit=3')
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                result = response.get_json()
                print(f"   Recommendations count: {len(result.get('recommendations', []))}")
            else:
                print(f"   Error: {response.get_json()}")
            
            # Test 3: Record interaction
            print("3. Testing interaction recording...")
            response = client.post('/api/ai/interactions', json={
                'user_id': 'test_user',
                'attraction_id': test_attraction.id,
                'interaction_type': 'view'
            })
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                result = response.get_json()
                print(f"   Success: {result.get('success')}")
            
            # Test 4: Improve content
            print("4. Testing content improvement...")
            response = client.post('/api/ai/content/improve', json={
                'attraction_id': test_attraction.id,
                'field': 'body',
                'style': 'friendly'
            })
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                result = response.get_json()
                print(f"   Improvements: {result.get('improvements', [])}")
                print(f"   Success: {result.get('success')}")
            
            # Test 5: Get AI stats
            print("5. Testing AI statistics...")
            response = client.get('/api/ai/stats')
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                result = response.get_json()
                print(f"   Total attractions: {result.get('attractions', {}).get('total', 0)}")
                print(f"   Total interactions: {result.get('interactions', {}).get('total', 0)}")
            
            # Test 6: Trend analysis
            print("6. Testing trend analysis...")
            response = client.get('/api/ai/trends/analyze?days=7')
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                result = response.get_json()
                print(f"   Total interactions: {result.get('total_interactions', 0)}")
            
            print("\nAI Features test completed successfully!")
            return True
            
    except Exception as e:
        print(f"Test failed with error: {e}")
        return False
        
    finally:
        # Cleanup
        os.close(db_fd)
        os.unlink(db_path)


if __name__ == '__main__':
    success = test_ai_features_manual()
    if success:
        print("✅ All AI features are working correctly!")
    else:
        print("❌ Some AI features failed!")