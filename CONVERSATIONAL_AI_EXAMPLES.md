# Conversational AI Examples

This document provides comprehensive examples of the new conversational AI features.

## Quick Start Example

### Basic Conversation Flow

```python
import requests

# Base URL
BASE_URL = "http://localhost:5000/api/ai"

# 1. Start a conversation
session_response = requests.post(f"{BASE_URL}/conversation/session", 
                                json={"user_id": "tourist_123"})
session_id = session_response.json()["session_id"]

# 2. Greet and ask for recommendations
chat1 = requests.post(f"{BASE_URL}/conversation/chat", json={
    "text": "สวัสดีครับ ผมต้องการหาที่เที่ยว",
    "session_id": session_id
})
print("Bot:", chat1.json()["message"])
# Output: "สวัสดีครับ! ผมสามารถช่วยแนะนำสถานที่ท่องเที่ยวได้ครับ คุณต้องการหาสถานที่ท่องเที่ยวแบบไหนบ้างครับ?"

# 3. Ask for specific location
chat2 = requests.post(f"{BASE_URL}/conversation/chat", json={
    "text": "หาที่เที่ยวในเชียงใหม่หน่อย",
    "session_id": session_id
})
print("Bot:", chat2.json()["message"])
print("Results:", len(chat2.json()["results"]))
# Output: "พบสถานที่ท่องเที่ยวในChiang Mai จำนวน 5 แห่งครับ:"

# 4. Refine search
chat3 = requests.post(f"{BASE_URL}/conversation/chat", json={
    "text": "มีวัดสวยๆ ไหม",
    "session_id": session_id
})
print("Bot:", chat3.json()["message"])
# Output: "พบสถานที่ท่องเที่ยวที่เหมาะสม 3 แห่งครับ ลองดูดังนี้:"
```

## Advanced Features

### Intent Detection Examples

```python
# Test different intent types
intents_to_test = [
    # Search intents
    ("หาที่เที่ยวในกรุงเทพ", "search_by_location"),
    ("มีวัดสวยๆ ไหม", "search_by_activity"),
    ("แนะนำสถานที่น่าเที่ยว", "get_recommendations"),
    
    # English equivalents
    ("find temples in Bangkok", "search_by_location"),
    ("recommend beautiful places", "get_recommendations"),
    
    # Greetings and conversation
    ("สวัสดีครับ", "greeting"),
    ("hello, I need help", "greeting"),
    
    # Detail requests
    ("บอกรายละเอียดหน่อย", "get_details"),
    ("tell me more about this place", "get_details")
]

for text, expected_intent in intents_to_test:
    response = requests.post(f"{BASE_URL}/nlu/intent", json={"text": text})
    data = response.json()
    print(f"Text: '{text}'")
    print(f"Intent: {data['intent']} (confidence: {data['confidence']:.2f})")
    print(f"Entities: {data['entities']}")
    print()
```

### Smart Query Generation

```python
# Test query generation with different complexity
queries = [
    "หาที่เที่ยวในกรุงเทพ",          # Location-based
    "วัดสวยๆ ในเชียงใหม่",           # Location + Activity
    "ธรรมชาติ น้ำตก ภูเก็ต",         # Multiple keywords
    "แนะนำสถานที่ยอดนิยม",          # Recommendations
    "find museums in Bangkok",       # English query
]

for query_text in queries:
    response = requests.post(f"{BASE_URL}/search/from-text", json={
        "text": query_text,
        "session_id": session_id
    })
    
    data = response.json()
    print(f"Query: '{query_text}'")
    print(f"Intent: {data['intent']['intent']}")
    print(f"Filters: {data['query_params']['filters']}")
    print(f"Search terms: {data['query_params']['search_terms']}")
    print(f"Results: {data['total_results']} attractions found")
    if data['results']:
        print(f"Top result: {data['results'][0]['title']}")
    print()
```

### Session Management and Preferences

```python
# Update user preferences
preferences = {
    "preferred_province": "Chiang Mai",
    "max_results": 5,
    "interests": ["temples", "nature", "culture"],
    "language": "thai"
}

pref_response = requests.post(f"{BASE_URL}/conversation/preferences", json={
    "session_id": session_id,
    "preferences": preferences
})

# Now queries will be influenced by preferences
chat_with_prefs = requests.post(f"{BASE_URL}/conversation/chat", json={
    "text": "แนะนำที่เที่ยวหน่อย",
    "session_id": session_id
})

# Get session information
session_info = requests.get(f"{BASE_URL}/conversation/session/{session_id}")
print("Session context:", session_info.json()["session"])
```

## Real-World Usage Scenarios

### Scenario 1: Tourist Planning Trip

```python
def tourist_conversation_example():
    """Simulate a tourist planning their trip."""
    
    # Create session
    session = requests.post(f"{BASE_URL}/conversation/session",
                           json={"user_id": "tourist_001"}).json()
    session_id = session["session_id"]
    
    conversation = [
        "สวัสดีครับ ผมจะไปเที่ยวเชียงใหม่",
        "มีวัดไหนแนะนำบ้างครับ",
        "อยากไปดูธรรมชาติด้วย",
        "มีที่ไหนใกล้กันไหม",
        "ขอบคุณครับ"
    ]
    
    for i, user_message in enumerate(conversation, 1):
        response = requests.post(f"{BASE_URL}/conversation/chat", json={
            "text": user_message,
            "session_id": session_id
        }).json()
        
        print(f"Turn {i}:")
        print(f"User: {user_message}")
        print(f"Bot: {response['message']}")
        print(f"Results: {response['total_results']} attractions")
        print()
```

### Scenario 2: Local Guide System

```python
def local_guide_example():
    """AI acting as a local guide."""
    
    session = requests.post(f"{BASE_URL}/conversation/session",
                           json={"user_id": "guide_system"}).json()
    session_id = session["session_id"]
    
    # Set preferences for comprehensive guidance
    requests.post(f"{BASE_URL}/conversation/preferences", json={
        "session_id": session_id,
        "preferences": {
            "role": "local_guide",
            "detailed_responses": True,
            "include_tips": True
        }
    })
    
    guide_queries = [
        "ช่วยแนะนำแผนท่องเที่ยวกรุงเทพ 1 วัน",
        "เริ่มจากวัดพระแก้ว",
        "หลังจากนั้นไปไหนดี",
        "อยากกินอาหารท้องถิ่น",
        "กลับโรงแรมยังไง"
    ]
    
    for query in guide_queries:
        response = requests.post(f"{BASE_URL}/conversation/chat", json={
            "text": query,
            "session_id": session_id
        }).json()
        
        print(f"Tourist: {query}")
        print(f"Guide: {response['message']}")
        print()
```

## JavaScript/React Integration

### React Hook for Conversational AI

```javascript
import { useState, useCallback } from 'react';

const useConversationalAI = () => {
    const [sessionId, setSessionId] = useState(null);
    const [conversation, setConversation] = useState([]);
    const [loading, setLoading] = useState(false);

    const createSession = useCallback(async (userId) => {
        try {
            const response = await fetch('/api/ai/conversation/session', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: userId })
            });
            const data = await response.json();
            setSessionId(data.session_id);
            return data.session_id;
        } catch (error) {
            console.error('Failed to create session:', error);
            return null;
        }
    }, []);

    const sendMessage = useCallback(async (text) => {
        if (!sessionId) return null;
        
        setLoading(true);
        try {
            // Add user message to conversation
            const userMessage = { type: 'user', text, timestamp: new Date() };
            setConversation(prev => [...prev, userMessage]);

            const response = await fetch('/api/ai/conversation/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text, session_id: sessionId })
            });
            
            const data = await response.json();
            
            // Add bot response to conversation
            const botMessage = {
                type: 'bot',
                text: data.message,
                results: data.results,
                timestamp: new Date()
            };
            setConversation(prev => [...prev, botMessage]);
            
            return data;
        } catch (error) {
            console.error('Failed to send message:', error);
            return null;
        } finally {
            setLoading(false);
        }
    }, [sessionId]);

    const updatePreferences = useCallback(async (preferences) => {
        if (!sessionId) return false;
        
        try {
            const response = await fetch('/api/ai/conversation/preferences', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId, preferences })
            });
            return response.ok;
        } catch (error) {
            console.error('Failed to update preferences:', error);
            return false;
        }
    }, [sessionId]);

    return {
        sessionId,
        conversation,
        loading,
        createSession,
        sendMessage,
        updatePreferences
    };
};

// Usage in component
const ChatBot = () => {
    const { 
        sessionId, 
        conversation, 
        loading, 
        createSession, 
        sendMessage 
    } = useConversationalAI();

    useEffect(() => {
        createSession('user123');
    }, [createSession]);

    const handleSendMessage = async (text) => {
        const response = await sendMessage(text);
        if (response && response.results.length > 0) {
            // Handle search results
            console.log('Found attractions:', response.results);
        }
    };

    return (
        <div className="chatbot">
            <div className="conversation">
                {conversation.map((msg, index) => (
                    <div key={index} className={`message ${msg.type}`}>
                        <p>{msg.text}</p>
                        {msg.results && (
                            <div className="results">
                                {msg.results.map(attraction => (
                                    <div key={attraction.id} className="attraction">
                                        <h4>{attraction.title}</h4>
                                        <p>{attraction.body}</p>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                ))}
            </div>
            {loading && <div>Bot is typing...</div>}
        </div>
    );
};
```

## Testing and Development

### Unit Testing with Pytest

```python
def test_intent_detection():
    """Test intent detection functionality."""
    from app.services.conversational_ai import IntentDetector
    
    detector = IntentDetector()
    
    # Test Thai queries
    result = detector.detect_intent("หาที่เที่ยวในเชียงใหม่")
    assert result['intent'] in ['search_by_location', 'search_attractions']
    assert len(result['entities']['locations']) > 0
    
    # Test English queries
    result = detector.detect_intent("find temples in Bangkok")
    assert result['intent'] in ['search_by_location', 'search_attractions']

def test_smart_query_generation():
    """Test smart query generation."""
    from app.services.conversational_ai import SmartQueryGenerator
    
    generator = SmartQueryGenerator()
    result = generator.generate_query_from_text("หาวัดในกรุงเทพ")
    
    assert 'temple' in result['query_params']['search_terms']
    assert result['query_params']['filters'].get('province') == 'Bangkok'
```

### Performance Testing

```python
import time
import statistics

def performance_test():
    """Test performance of conversational AI endpoints."""
    
    times = []
    for i in range(100):
        start = time.time()
        
        response = requests.post(f"{BASE_URL}/nlu/intent", 
                               json={"text": "หาที่เที่ยวในเชียงใหม่"})
        
        end = time.time()
        times.append(end - start)
    
    print(f"Intent Detection Performance:")
    print(f"Average: {statistics.mean(times):.3f}s")
    print(f"Median: {statistics.median(times):.3f}s")
    print(f"95th percentile: {sorted(times)[95]:.3f}s")
```

## Best Practices

### 1. Session Management
- Create sessions for each user conversation
- Set appropriate expiration times (24 hours default)
- Clean up expired sessions regularly

### 2. Error Handling
- Always check response status codes
- Implement fallback responses for unknown intents
- Handle network timeouts gracefully

### 3. Performance Optimization
- Cache frequent queries
- Use session context to avoid repeating queries
- Implement request rate limiting

### 4. User Experience
- Provide typing indicators during processing
- Show search results in a user-friendly format
- Allow users to refine their queries easily

This conversational AI system transforms the Database Painaidee from a simple API into an intelligent, context-aware assistant for tourism information!