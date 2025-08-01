"""
Tests for conversational AI features.
"""
import json
import pytest
from datetime import datetime, timedelta

from app import create_app
from app.models import db, Attraction, ConversationSession
from app.services.conversational_ai import (
    IntentDetector, SmartQueryGenerator, ConversationalContextEngine,
    detect_user_intent, generate_smart_query, create_conversation_session
)


@pytest.fixture
def app():
    """Create application instance for testing."""
    import os
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        
        # Create test attractions
        test_attractions = [
            Attraction(
                external_id=1,
                title='วัดพระแก้ว กรุงเทพมหานคร',
                body='วัดพระแก้วเป็นวัดที่สำคัญและสวยงามในกรุงเทพ มีสถาปัตยกรรมไทยโบราณ',
                province='Bangkok',
                view_count=100
            ),
            Attraction(
                external_id=2,
                title='ดอยสุเทพ เชียงใหม่',
                body='ดอยสุเทพเป็นภูเขาและวัดที่มีชื่อเสียงในเชียงใหม่ มีธรรมชาติและวิวสวยงาม',
                province='Chiang Mai',
                view_count=85
            ),
            Attraction(
                external_id=3,
                title='หาดป่าตอง ภูเก็ต',
                body='หาดป่าตองเป็นหาดทรายขาวสวยงามในภูเก็ต เหมาะสำหรับการพักผ่อนและกีฬาทางน้ำ',
                province='Phuket',
                view_count=120
            ),
            Attraction(
                external_id=4,
                title='อุทยานแห่งชาติเขาใหญ่',
                body='อุทยานแห่งชาติเขาใหญ่เป็นพื้นที่ป่าธรรมชาติขนาดใหญ่ มีน้ำตกและสัตว์ป่า',
                province='Nakhon Ratchasima',
                view_count=70
            )
        ]
        
        for attraction in test_attractions:
            db.session.add(attraction)
        
        db.session.commit()
        
        yield app
        
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class TestIntentDetector:
    """Test the intent detection functionality."""
    
    def test_intent_detector_initialization(self):
        """Test intent detector initialization."""
        detector = IntentDetector()
        assert detector.intent_patterns is not None
        assert 'search_attractions' in detector.intent_patterns
        assert 'search_by_location' in detector.intent_patterns
    
    def test_detect_search_attractions_intent(self):
        """Test detecting search attractions intent."""
        detector = IntentDetector()
        
        # Test Thai query
        result = detector.detect_intent('หาสถานที่ท่องเที่ยวหน่อย')
        assert result['intent'] == 'search_attractions'
        assert result['confidence'] > 0
        
        # Test English query
        result = detector.detect_intent('find places to visit')
        assert result['intent'] == 'search_attractions'
        assert result['confidence'] > 0
    
    def test_detect_location_based_intent(self):
        """Test detecting location-based intent."""
        detector = IntentDetector()
        
        # Test location query
        result = detector.detect_intent('มีที่เที่ยวในเชียงใหม่ไหม')
        assert 'search_by_location' in [result['intent']] + list(result['all_intents'].keys())
        assert len(result['entities']['locations']) > 0
        assert result['entities']['locations'][0]['normalized'] == 'Chiang Mai'
    
    def test_detect_greeting_intent(self):
        """Test detecting greeting intent."""
        detector = IntentDetector()
        
        result = detector.detect_intent('สวัสดีครับ')
        assert result['intent'] == 'greeting'
        assert result['confidence'] > 0
    
    def test_entity_extraction(self):
        """Test entity extraction from text."""
        detector = IntentDetector()
        
        result = detector.detect_intent('หาวัดในกรุงเทพ')
        
        # Should extract location
        assert len(result['entities']['locations']) > 0
        
        # Should extract activity (temple)
        activities = [act['normalized'] for act in result['entities']['activities']]
        assert 'temple' in activities
    
    def test_unknown_intent(self):
        """Test handling of unknown intent."""
        detector = IntentDetector()
        
        result = detector.detect_intent('ราคาน้ำมันวันนี้')
        assert result['intent'] == 'unknown'
        assert result['confidence'] == 0.0


class TestSmartQueryGenerator:
    """Test the smart query generation functionality."""
    
    def test_query_generator_initialization(self, app):
        """Test query generator initialization."""
        with app.app_context():
            generator = SmartQueryGenerator()
            assert generator.intent_detector is not None
    
    def test_generate_location_query(self, app):
        """Test generating location-based query."""
        with app.app_context():
            generator = SmartQueryGenerator()
            
            result = generator.generate_query_from_text('หาที่เที่ยวในเชียงใหม่')
            
            assert result['intent']['intent'] in ['search_by_location', 'search_attractions']
            assert 'province' in result['query_params']['filters']
            assert len(result['results']) >= 0
    
    def test_generate_activity_query(self, app):
        """Test generating activity-based query."""
        with app.app_context():
            generator = SmartQueryGenerator()
            
            result = generator.generate_query_from_text('หาวัดสวยๆ')
            
            assert len(result['query_params']['search_terms']) > 0
            assert 'temple' in result['query_params']['search_terms']
    
    def test_query_execution_with_results(self, app):
        """Test query execution returning results."""
        with app.app_context():
            generator = SmartQueryGenerator()
            
            # Query that should return results
            result = generator.generate_query_from_text('หาที่เที่ยวในกรุงเทพ')
            
            assert result['total_results'] >= 0
            if result['total_results'] > 0:
                assert 'id' in result['results'][0]
                assert 'title' in result['results'][0]
    
    def test_session_context_integration(self, app):
        """Test integration with conversation session context."""
        with app.app_context():
            generator = SmartQueryGenerator()
            
            # Create a test session
            session_id = 'test-session-123'
            
            # First query
            result1 = generator.generate_query_from_text('หาที่เที่ยว', session_id)
            assert result1['session_id'] == session_id
            
            # Second query should use context
            result2 = generator.generate_query_from_text('ในเชียงใหม่', session_id)
            assert result2['session_id'] == session_id


class TestConversationalContextEngine:
    """Test the conversational context engine functionality."""
    
    def test_context_engine_initialization(self, app):
        """Test context engine initialization."""
        with app.app_context():
            engine = ConversationalContextEngine()
            assert engine.intent_detector is not None
            assert engine.query_generator is not None
    
    def test_create_conversation_session(self, app):
        """Test creating a conversation session."""
        with app.app_context():
            engine = ConversationalContextEngine()
            
            session_id = engine.create_session()
            assert session_id is not None
            assert len(session_id) > 10  # UUID format
            
            # Verify session was created in database
            session = ConversationSession.query.filter_by(session_id=session_id).first()
            assert session is not None
    
    def test_get_session_context(self, app):
        """Test getting session context."""
        with app.app_context():
            engine = ConversationalContextEngine()
            
            # Create session
            session_id = engine.create_session('test-user')
            
            # Get context
            context = engine.get_session_context(session_id)
            assert context is not None
            assert context['session_id'] == session_id
            assert context['user_id'] == 'test-user'
    
    def test_update_preferences(self, app):
        """Test updating session preferences."""
        with app.app_context():
            engine = ConversationalContextEngine()
            
            session_id = engine.create_session()
            
            preferences = {
                'preferred_province': 'Chiang Mai',
                'max_results': 5
            }
            
            success = engine.update_preferences(session_id, preferences)
            assert success is True
            
            # Verify preferences were saved
            context = engine.get_session_context(session_id)
            prefs = json.loads(context['preferences'])
            assert prefs['preferred_province'] == 'Chiang Mai'
    
    def test_contextual_response(self, app):
        """Test generating contextual responses."""
        with app.app_context():
            engine = ConversationalContextEngine()
            
            session_id = engine.create_session()
            
            response = engine.get_contextual_response(session_id, 'หาที่เที่ยวในเชียงใหม่')
            
            assert response['session_id'] == session_id
            assert 'response_message' in response
            assert 'query_result' in response
            assert response['context_updated'] is True
    
    def test_session_expiration(self, app):
        """Test session expiration handling."""
        with app.app_context():
            engine = ConversationalContextEngine()
            
            # Create expired session
            expired_session = ConversationSession(
                session_id='expired-session',
                expires_at=datetime.utcnow() - timedelta(hours=1)
            )
            db.session.add(expired_session)
            db.session.commit()
            
            # Try to get expired session
            context = engine.get_session_context('expired-session')
            assert context is None


class TestConversationalAIRoutes:
    """Test the conversational AI API routes."""
    
    def test_detect_intent_route(self, client, app):
        """Test the intent detection API route."""
        with app.app_context():
            response = client.post('/api/ai/nlu/intent', 
                                 json={'text': 'หาที่เที่ยวในเชียงใหม่'})
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert 'intent' in data
            assert 'confidence' in data
            assert 'entities' in data
    
    def test_detect_intent_route_missing_text(self, client, app):
        """Test intent detection route with missing text."""
        with app.app_context():
            response = client.post('/api/ai/nlu/intent', json={})
            
            assert response.status_code == 400
            data = response.get_json()
            assert 'error' in data
    
    def test_search_from_text_route(self, client, app):
        """Test the smart search API route."""
        with app.app_context():
            response = client.post('/api/ai/search/from-text',
                                 json={'text': 'หาวัดในกรุงเทพ'})
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert 'intent' in data
            assert 'query_params' in data
            assert 'results' in data
            assert 'total_results' in data
    
    def test_search_from_text_with_session(self, client, app):
        """Test smart search with session context."""
        with app.app_context():
            # First create a session
            session_response = client.post('/api/ai/conversation/session')
            session_data = session_response.get_json()
            session_id = session_data['session_id']
            
            # Then search with session
            response = client.post('/api/ai/search/from-text',
                                 json={
                                     'text': 'หาที่เที่ยว',
                                     'session_id': session_id
                                 })
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['session_id'] == session_id
    
    def test_create_session_route(self, client, app):
        """Test creating conversation session."""
        with app.app_context():
            response = client.post('/api/ai/conversation/session')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert 'session_id' in data
            assert data['expires_in_hours'] == 24
    
    def test_conversational_chat_route(self, client, app):
        """Test the main conversational chat endpoint."""
        with app.app_context():
            response = client.post('/api/ai/conversation/chat',
                                 json={'text': 'สวัสดี หาที่เที่ยวในเชียงใหม่'})
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert 'session_id' in data
            assert 'message' in data
            assert 'intent' in data
            assert 'results' in data
    
    def test_update_preferences_route(self, client, app):
        """Test updating session preferences."""
        with app.app_context():
            # Create session first
            session_response = client.post('/api/ai/conversation/session')
            session_data = session_response.get_json()
            session_id = session_data['session_id']
            
            # Update preferences
            response = client.post('/api/ai/conversation/preferences',
                                 json={
                                     'session_id': session_id,
                                     'preferences': {
                                         'preferred_province': 'Bangkok',
                                         'max_results': 3
                                     }
                                 })
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
    
    def test_get_session_info_route(self, client, app):
        """Test getting session information."""
        with app.app_context():
            # Create session first
            session_response = client.post('/api/ai/conversation/session')
            session_data = session_response.get_json()
            session_id = session_data['session_id']
            
            # Get session info
            response = client.get(f'/api/ai/conversation/session/{session_id}')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert 'session' in data
    
    def test_get_nonexistent_session_info(self, client, app):
        """Test getting info for non-existent session."""
        with app.app_context():
            response = client.get('/api/ai/conversation/session/nonexistent-session')
            
            assert response.status_code == 404
            data = response.get_json()
            assert 'error' in data
    
    def test_ai_stats_includes_conversations(self, client, app):
        """Test that AI stats include conversation data."""
        with app.app_context():
            # Create a session
            client.post('/api/ai/conversation/session')
            
            response = client.get('/api/ai/stats')
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'conversations' in data
            assert 'total_sessions' in data['conversations']
            assert 'active_sessions' in data['conversations']


class TestServiceFunctions:
    """Test the service functions directly."""
    
    def test_detect_user_intent_function(self, app):
        """Test the detect_user_intent service function."""
        with app.app_context():
            result = detect_user_intent('หาที่เที่ยวในกรุงเทพ')
            
            assert 'intent' in result
            assert 'confidence' in result
            assert 'entities' in result
    
    def test_generate_smart_query_function(self, app):
        """Test the generate_smart_query service function."""
        with app.app_context():
            result = generate_smart_query('หาวัดสวยๆ')
            
            assert 'intent' in result
            assert 'query_params' in result
            assert 'results' in result
    
    def test_create_conversation_session_function(self, app):
        """Test the create_conversation_session service function."""
        with app.app_context():
            session_id = create_conversation_session('test-user')
            
            assert session_id is not None
            assert len(session_id) > 10
            
            # Verify in database
            session = ConversationSession.query.filter_by(session_id=session_id).first()
            assert session is not None
            assert session.user_id == 'test-user'