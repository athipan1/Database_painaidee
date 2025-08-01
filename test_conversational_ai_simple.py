"""
Simple test for conversational AI features to validate functionality.
"""
import os
import tempfile
import pytest
from app import create_app
from app.models import db
from app.services.conversational_ai import IntentDetector, detect_user_intent


def test_intent_detection_standalone():
    """Test intent detection without database."""
    detector = IntentDetector()
    
    # Test Thai query
    result = detector.detect_intent('หาสถานที่ท่องเที่ยวหน่อย')
    assert result['intent'] == 'search_attractions'
    assert result['confidence'] > 0
    
    # Test English query
    result = detector.detect_intent('find places to visit')
    assert result['intent'] == 'search_attractions'
    assert result['confidence'] > 0
    
    # Test location query
    result = detector.detect_intent('มีที่เที่ยวในเชียงใหม่ไหม')
    assert len(result['entities']['locations']) > 0
    assert result['entities']['locations'][0]['normalized'] == 'Chiang Mai'
    
    # Test greeting
    result = detector.detect_intent('สวัสดีครับ')
    assert result['intent'] == 'greeting'
    
    # Test unknown
    result = detector.detect_intent('ราคาน้ำมันวันนี้')
    assert result['intent'] == 'unknown'
    assert result['confidence'] == 0.0


def test_service_function():
    """Test the service function wrapper."""
    result = detect_user_intent('หาที่เที่ยวในกรุงเทพ')
    assert 'intent' in result
    assert 'confidence' in result
    assert 'entities' in result
    

def test_app_creation_with_conversational_ai():
    """Test that the app can be created and conversational AI routes work."""
    # Create temporary database
    db_fd, db_path = tempfile.mkstemp()
    
    try:
        # Configure environment
        os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'
        
        app = create_app()
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        
        with app.app_context():
            db.create_all()
            
            # Test intent detection route
            with app.test_client() as client:
                response = client.post('/api/ai/nlu/intent', 
                                     json={'text': 'หาที่เที่ยวในเชียงใหม่'})
                
                assert response.status_code == 200
                data = response.get_json()
                assert data['success'] is True
                assert 'intent' in data
                
                # Test session creation with proper headers
                response = client.post('/api/ai/conversation/session',
                                     headers={'Content-Type': 'application/json'},
                                     json={})
                assert response.status_code == 200
                session_data = response.get_json()
                assert 'session_id' in session_data
                
                # Test chat with session
                response = client.post('/api/ai/conversation/chat',
                                     json={'text': 'สวัสดี'})
                assert response.status_code == 200
                chat_data = response.get_json()
                assert 'message' in chat_data
                
    finally:
        os.close(db_fd)
        os.unlink(db_path)


if __name__ == '__main__':
    test_intent_detection_standalone()
    test_service_function()
    test_app_creation_with_conversational_ai()
    print("All basic tests passed!")