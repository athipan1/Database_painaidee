"""
Conversational AI service for natural language understanding and smart query generation.
Provides intent detection, query generation, and context management.
"""
import json
import re
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from app.models import db, Attraction, ConversationSession, UserInteraction
from app.services.keyword_extraction import extract_keywords_from_attraction


class IntentDetector:
    """Detects user intents from natural language queries."""
    
    def __init__(self):
        """Initialize the intent detector with predefined patterns."""
        self.intent_patterns = {
            'search_attractions': [
                r'หา.*สถานที่', r'มี.*ที่เที่ยว', r'แนะนำ.*สถานที่', r'ที่เที่ยว.*ไหน',
                r'find.*place', r'recommend.*attraction', r'where.*visit', r'places.*to.*go',
                r'tourism', r'travel', r'attractions?', r'destinations?'
            ],
            'search_by_location': [
                r'ใน.*จังหวัด', r'ที่.*เชียงใหม่', r'ใน.*กรุงเทพ', r'ใน.*ภูเก็ต',
                r'in.*province', r'in.*bangkok', r'in.*chiang.*mai', r'in.*phuket',
                r'near.*', r'around.*', r'close.*to'
            ],
            'search_by_activity': [
                r'ธรรมชาติ', r'วัด', r'พิพิธภัณฑ์', r'ชายหาด', r'ภูเขา',
                r'nature', r'temple', r'museum', r'beach', r'mountain',
                r'hiking', r'swimming', r'shopping', r'food', r'culture'
            ],
            'get_details': [
                r'รายละเอียด', r'ข้อมูล.*เพิ่มเติม', r'บอก.*เกี่ยวกับ',
                r'details', r'information.*about', r'tell.*me.*about',
                r'more.*info', r'describe'
            ],
            'get_recommendations': [
                r'แนะนำ', r'เหมาะสม', r'น่าสนใจ',
                r'recommend', r'suggest', r'suitable', r'interesting',
                r'what.*should', r'best.*for'
            ],
            'greeting': [
                r'สวัสดี', r'หวัดดี', r'ขอความช่วยเหลือ',
                r'hello', r'hi', r'hey', r'good.*morning', r'good.*afternoon'
            ]
        }
        
        # Context keywords for search refinement
        self.location_keywords = {
            'เชียงใหม่': 'Chiang Mai', 'กรุงเทพ': 'Bangkok', 'ภูเก็ต': 'Phuket',
            'เชียงราย': 'Chiang Rai', 'ขอนแก่น': 'Khon Kaen', 'นครราชสีมา': 'Nakhon Ratchasima',
            'อยุธยา': 'Ayutthaya', 'สุโขทัย': 'Sukhothai', 'กาญจนบุรี': 'Kanchanaburi',
            'chiang mai': 'Chiang Mai', 'bangkok': 'Bangkok', 'phuket': 'Phuket'
        }
        
        self.activity_keywords = {
            'ธรรมชาติ': 'nature', 'วัด': 'temple', 'พิพิธภัณฑ์': 'museum',
            'ชายหาด': 'beach', 'ภูเขา': 'mountain', 'น้ำตก': 'waterfall',
            'nature': 'nature', 'temple': 'temple', 'museum': 'museum',
            'beach': 'beach', 'mountain': 'mountain', 'waterfall': 'waterfall'
        }
    
    def detect_intent(self, text: str) -> Dict:
        """
        Detect intent from user text.
        
        Args:
            text: User input text
            
        Returns:
            Dictionary with intent, confidence, and extracted entities
        """
        text_lower = text.lower()
        
        # Check for each intent pattern
        intent_scores = {}
        for intent, patterns in self.intent_patterns.items():
            score = 0
            matched_patterns = []
            
            for pattern in patterns:
                try:
                    if re.search(pattern, text_lower, re.IGNORECASE):
                        score += 1
                        matched_patterns.append(pattern)
                except re.error:
                    # Skip invalid regex patterns
                    continue
            
            if score > 0:
                intent_scores[intent] = {
                    'score': score,
                    'patterns': matched_patterns
                }
        
        # Determine primary intent
        if not intent_scores:
            primary_intent = 'unknown'
            confidence = 0.0
        else:
            primary_intent = max(intent_scores.keys(), key=lambda x: intent_scores[x]['score'])
            confidence = min(intent_scores[primary_intent]['score'] / len(self.intent_patterns[primary_intent]), 1.0)
        
        # Extract entities
        entities = self._extract_entities(text_lower)
        
        return {
            'intent': primary_intent,
            'confidence': confidence,
            'entities': entities,
            'all_intents': intent_scores,
            'original_text': text
        }
    
    def _extract_entities(self, text: str) -> Dict:
        """Extract entities like locations and activities from text."""
        entities = {
            'locations': [],
            'activities': [],
            'keywords': []
        }
        
        # Extract locations
        for thai_location, english_location in self.location_keywords.items():
            if thai_location in text:
                entities['locations'].append({
                    'thai': thai_location,
                    'english': english_location,
                    'normalized': english_location
                })
        
        # Extract activities
        for thai_activity, english_activity in self.activity_keywords.items():
            if thai_activity in text:
                entities['activities'].append({
                    'thai': thai_activity,
                    'english': english_activity,
                    'normalized': english_activity
                })
        
        # Extract general keywords using existing keyword extraction
        try:
            fake_attraction = {'title': '', 'body': text}
            extracted_keywords = extract_keywords_from_attraction(fake_attraction)
            entities['keywords'] = extracted_keywords.get('keywords', [])
        except Exception:
            # If keyword extraction fails, fallback to empty list
            entities['keywords'] = []
        
        return entities


class SmartQueryGenerator:
    """Generates database queries from natural language text."""
    
    def __init__(self):
        """Initialize the query generator."""
        self.intent_detector = IntentDetector()
    
    def generate_query_from_text(self, text: str, session_id: Optional[str] = None) -> Dict:
        """
        Generate database query from natural language text.
        
        Args:
            text: Natural language query
            session_id: Optional session ID for context
            
        Returns:
            Dictionary with query parameters and results
        """
        # Detect intent and extract entities
        intent_result = self.intent_detector.detect_intent(text)
        
        # Get conversation context if session provided
        context = self._get_conversation_context(session_id) if session_id else {}
        
        # Generate query based on intent
        query_params = self._generate_query_params(intent_result, context)
        
        # Execute query
        results = self._execute_attraction_query(query_params)
        
        # Update context if session provided
        if session_id:
            self._update_conversation_context(session_id, intent_result, query_params)
        
        return {
            'intent': intent_result,
            'query_params': query_params,
            'results': results,
            'total_results': len(results),
            'session_id': session_id
        }
    
    def _generate_query_params(self, intent_result: Dict, context: Dict) -> Dict:
        """Generate query parameters based on intent and context."""
        params = {
            'filters': {},
            'search_terms': [],
            'limit': 10,
            'order_by': 'view_count'
        }
        
        intent = intent_result['intent']
        entities = intent_result['entities']
        
        # Location-based filtering
        if entities['locations']:
            # Use the first detected location
            location = entities['locations'][0]['normalized']
            params['filters']['province'] = location
        
        # Activity-based search terms
        if entities['activities']:
            for activity in entities['activities']:
                params['search_terms'].append(activity['normalized'])
        
        # General keyword search
        if entities['keywords']:
            params['search_terms'].extend(entities['keywords'])
        
        # Intent-specific adjustments
        if intent == 'get_recommendations':
            params['limit'] = 5
            params['order_by'] = 'view_count'  # Popular attractions first
        elif intent == 'search_by_location':
            params['order_by'] = 'created_at'  # Newest first
        elif intent == 'search_by_activity':
            params['limit'] = 8
        
        # Apply context preferences
        if context.get('preferences'):
            try:
                prefs = json.loads(context['preferences'])
                if prefs.get('preferred_province'):
                    params['filters']['province'] = prefs['preferred_province']
                if prefs.get('max_results'):
                    params['limit'] = min(params['limit'], prefs['max_results'])
            except (json.JSONDecodeError, KeyError):
                pass
        
        return params
    
    def _execute_attraction_query(self, params: Dict) -> List[Dict]:
        """Execute the generated query and return results."""
        query = Attraction.query
        
        # Apply filters
        for field, value in params['filters'].items():
            if field == 'province' and value:
                query = query.filter(Attraction.province.ilike(f'%{value}%'))
        
        # Apply search terms
        if params['search_terms']:
            search_conditions = []
            for term in params['search_terms']:
                search_conditions.append(Attraction.title.ilike(f'%{term}%'))
                search_conditions.append(Attraction.body.ilike(f'%{term}%'))
            
            # Combine with OR logic
            if search_conditions:
                from sqlalchemy import or_
                query = query.filter(or_(*search_conditions))
        
        # Apply ordering
        if params['order_by'] == 'view_count':
            query = query.order_by(Attraction.view_count.desc())
        elif params['order_by'] == 'created_at':
            query = query.order_by(Attraction.created_at.desc())
        
        # Apply limit
        query = query.limit(params['limit'])
        
        # Execute and convert to dict
        attractions = query.all()
        return [attraction.to_dict() for attraction in attractions]
    
    def _get_conversation_context(self, session_id: str) -> Dict:
        """Get conversation context for session."""
        session = ConversationSession.query.filter_by(session_id=session_id).first()
        if session:
            return {
                'context_data': session.context_data,
                'last_intent': session.last_intent,
                'preferences': session.preferences
            }
        return {}
    
    def _update_conversation_context(self, session_id: str, intent_result: Dict, query_params: Dict):
        """Update conversation context with new information."""
        session = ConversationSession.query.filter_by(session_id=session_id).first()
        
        if not session:
            # Create new session
            session = ConversationSession(
                session_id=session_id,
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )
            db.session.add(session)
        
        # Update context
        context = {
            'last_query': intent_result['original_text'],
            'last_entities': intent_result['entities'],
            'last_filters': query_params['filters'],
            'query_history': []
        }
        
        # Preserve existing context
        if session.context_data:
            try:
                existing_context = json.loads(session.context_data)
                if 'query_history' in existing_context:
                    context['query_history'] = existing_context['query_history'][-4:]  # Keep last 5
            except json.JSONDecodeError:
                pass
        
        # Add current query to history
        context['query_history'].append({
            'text': intent_result['original_text'],
            'intent': intent_result['intent'],
            'timestamp': datetime.utcnow().isoformat()
        })
        
        session.context_data = json.dumps(context)
        session.last_intent = intent_result['intent']
        session.updated_at = datetime.utcnow()
        
        db.session.commit()


class ConversationalContextEngine:
    """Manages conversational context and personalization."""
    
    def __init__(self):
        """Initialize the context engine."""
        self.intent_detector = IntentDetector()
        self.query_generator = SmartQueryGenerator()
    
    def create_session(self, user_id: Optional[str] = None) -> str:
        """Create a new conversation session."""
        session_id = str(uuid.uuid4())
        
        session = ConversationSession(
            session_id=session_id,
            user_id=user_id,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        
        db.session.add(session)
        db.session.commit()
        
        return session_id
    
    def get_session_context(self, session_id: str) -> Optional[Dict]:
        """Get context for a conversation session."""
        session = ConversationSession.query.filter_by(session_id=session_id).first()
        
        if not session:
            return None
        
        if session.expires_at and session.expires_at < datetime.utcnow():
            # Session expired
            db.session.delete(session)
            db.session.commit()
            return None
        
        return session.to_dict()
    
    def update_preferences(self, session_id: str, preferences: Dict) -> bool:
        """Update user preferences for a session."""
        session = ConversationSession.query.filter_by(session_id=session_id).first()
        
        if not session:
            return False
        
        try:
            # Merge with existing preferences
            existing_prefs = {}
            if session.preferences:
                existing_prefs = json.loads(session.preferences)
            
            existing_prefs.update(preferences)
            session.preferences = json.dumps(existing_prefs)
            session.updated_at = datetime.utcnow()
            
            db.session.commit()
            return True
        except Exception:
            return False
    
    def get_contextual_response(self, session_id: str, user_text: str) -> Dict:
        """Generate contextual response based on conversation history."""
        # Get current context
        context = self.get_session_context(session_id)
        
        if not context:
            # Create new session if not exists
            session_id = self.create_session()
            context = self.get_session_context(session_id)
        
        # Generate query with context
        query_result = self.query_generator.generate_query_from_text(user_text, session_id)
        
        # Generate contextual response message
        response_message = self._generate_response_message(query_result, context)
        
        return {
            'session_id': session_id,
            'response_message': response_message,
            'query_result': query_result,
            'context_updated': True
        }
    
    def _generate_response_message(self, query_result: Dict, context: Dict) -> str:
        """Generate a friendly response message based on query results."""
        intent = query_result['intent']['intent']
        results_count = query_result['total_results']
        
        # Base response templates
        if intent == 'greeting':
            return "สวัสดีครับ! ผมสามารถช่วยแนะนำสถานที่ท่องเที่ยวได้ครับ คุณต้องการหาสถานที่ท่องเที่ยวแบบไหนบ้างครับ?"
        
        elif intent == 'search_attractions' and results_count > 0:
            return f"พบสถานที่ท่องเที่ยวที่เหมาะสม {results_count} แห่งครับ ลองดูดังนี้:"
        
        elif intent == 'search_by_location' and results_count > 0:
            location = query_result['query_params']['filters'].get('province', 'บริเวณที่คุณสนใจ')
            return f"พบสถานที่ท่องเที่ยวใน{location} จำนวน {results_count} แห่งครับ:"
        
        elif intent == 'get_recommendations' and results_count > 0:
            return f"แนะนำสถานที่ท่องเที่ยวน่าสนใจ {results_count} แห่งครับ:"
        
        elif results_count == 0:
            return "ขออภัยครับ ไม่พบสถานที่ท่องเที่ยวที่ตรงกับที่คุณต้องการ ลองใช้คำค้นหาอื่นดูครับ หรือจะให้ผมแนะนำสถานที่ยอดนิยมไหมครับ?"
        
        else:
            return f"พบข้อมูลที่เกี่ยวข้อง {results_count} รายการครับ:"


# Service instances
intent_detector = IntentDetector()
query_generator = SmartQueryGenerator()
context_engine = ConversationalContextEngine()


def detect_user_intent(text: str) -> Dict:
    """Detect user intent from text."""
    return intent_detector.detect_intent(text)


def generate_smart_query(text: str, session_id: Optional[str] = None) -> Dict:
    """Generate smart query from text."""
    return query_generator.generate_query_from_text(text, session_id)


def create_conversation_session(user_id: Optional[str] = None) -> str:
    """Create new conversation session."""
    return context_engine.create_session(user_id)


def get_contextual_response(session_id: str, user_text: str) -> Dict:
    """Get contextual response for user input."""
    return context_engine.get_contextual_response(session_id, user_text)


def update_session_preferences(session_id: str, preferences: Dict) -> bool:
    """Update session preferences."""
    return context_engine.update_preferences(session_id, preferences)