# AI Features Documentation

This document describes the AI-powered features added to the Database Painaidee system.

## Overview

The system now includes 7 AI-driven features to enhance attraction management:

1. **🔎 AI Keyword Extraction** - Extract meaningful keywords from descriptions
2. **🧠 AI Personalized Recommendations** - Suggest attractions based on user behavior
3. **📈 Heatmap/Trend AI** - Analytics and trend analysis
4. **📚 AI Content Rewriting** - Improve content readability and style
5. **🤖 Conversational AI (Intent Detection)** - Understand user intentions from natural language
6. **🔍 Smart Query Generator** - Convert natural language to database queries
7. **💬 Conversational Context Engine** - Maintain conversation history and personalization

## New Conversational AI Features

### Intent Detection API

Detects user intentions from natural language text in both Thai and English.

#### Detect Intent
```http
POST /api/ai/nlu/intent
Content-Type: application/json

{
    "text": "หาที่เที่ยวในเชียงใหม่"
}
```

**Response:**
```json
{
    "success": true,
    "intent": "search_by_location",
    "confidence": 0.85,
    "entities": {
        "locations": [{"thai": "เชียงใหม่", "english": "Chiang Mai", "normalized": "Chiang Mai"}],
        "activities": [],
        "keywords": ["เที่ยว", "สถานที่"]
    },
    "original_text": "หาที่เที่ยวในเชียงใหม่"
}
```

**Supported Intents:**
- `search_attractions` - General attraction search
- `search_by_location` - Location-specific search
- `search_by_activity` - Activity-based search (temples, nature, etc.)
- `get_details` - Request for detailed information
- `get_recommendations` - Request for recommendations
- `greeting` - Greetings and conversation starters
- `unknown` - Unrecognized intents

### Smart Query Generator API

Converts natural language text into smart database queries.

#### Generate Smart Query
```http
POST /api/ai/search/from-text
Content-Type: application/json

{
    "text": "หาวัดสวยๆ ในกรุงเทพ",
    "session_id": "optional-session-id"
}
```

**Response:**
```json
{
    "success": true,
    "intent": {
        "intent": "search_by_location",
        "confidence": 0.75,
        "entities": {...}
    },
    "query_params": {
        "filters": {"province": "Bangkok"},
        "search_terms": ["temple"],
        "limit": 10,
        "order_by": "view_count"
    },
    "results": [...],
    "total_results": 5,
    "session_id": "session-123"
}
```

### Conversational Context Engine

Manages conversation sessions with memory and personalization.

#### Create Session
```http
POST /api/ai/conversation/session
Content-Type: application/json

{
    "user_id": "optional-user-id"
}
```

#### Main Chat Endpoint
```http
POST /api/ai/conversation/chat
Content-Type: application/json

{
    "text": "สวัสดี หาที่เที่ยวในเชียงใหม่",
    "session_id": "optional-session-id"
}
```

**Response:**
```json
{
    "success": true,
    "session_id": "uuid-session-id",
    "message": "พบสถานที่ท่องเที่ยวในChiang Mai จำนวน 3 แห่งครับ:",
    "intent": {...},
    "results": [...],
    "total_results": 3,
    "context_updated": true
}
```

#### Update Preferences
```http
POST /api/ai/conversation/preferences
Content-Type: application/json

{
    "session_id": "session-id",
    "preferences": {
        "preferred_province": "Chiang Mai",
        "max_results": 5,
        "language": "thai"
    }
}
```

#### Get Session Info
```http
GET /api/ai/conversation/session/{session_id}
```

## Example Conversation Flow

```javascript
// 1. Create session
const sessionResponse = await fetch('/api/ai/conversation/session', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({user_id: 'user123'})
});
const {session_id} = await sessionResponse.json();

// 2. Start conversation
const chatResponse = await fetch('/api/ai/conversation/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        text: 'สวัสดี หาที่เที่ยวในเชียงใหม่',
        session_id
    })
});
const chatData = await chatResponse.json();
console.log('Bot:', chatData.message);
console.log('Results:', chatData.results);

// 3. Continue conversation with context
const followUpResponse = await fetch('/api/ai/conversation/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        text: 'มีวัดสวยๆ ไหม',
        session_id
    })
});
```

## Conversational AI Architecture

### IntentDetector Class
- **Pattern-based NLU**: Uses regex patterns for Thai/English intent detection
- **Entity Extraction**: Identifies locations, activities, and keywords
- **Fallback Strategy**: Works without heavy ML dependencies

### SmartQueryGenerator Class  
- **Query Translation**: Converts natural language to database queries
- **Context Integration**: Uses conversation history for better queries
- **Flexible Filtering**: Supports location, activity, and keyword-based searches

### ConversationalContextEngine Class
- **Session Management**: Maintains conversation state and history
- **Preference Learning**: Stores and applies user preferences
- **Context-Aware Responses**: Generates appropriate responses based on query results

## Database Schema

### New Table: `conversation_sessions`
```sql
CREATE TABLE conversation_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) UNIQUE NOT NULL,
    user_id VARCHAR(100),
    context_data TEXT,  -- JSON conversation history
    last_intent VARCHAR(100),
    preferences TEXT,   -- JSON user preferences
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);
```

## Usage Examples

### Python Client
```python
import requests

BASE_URL = "http://localhost:5000/api/ai"

# Detect intent
response = requests.post(f"{BASE_URL}/nlu/intent", 
                        json={"text": "หาวัดในกรุงเทพ"})
intent_data = response.json()

# Start conversation
session_response = requests.post(f"{BASE_URL}/conversation/session")
session_id = session_response.json()["session_id"]

chat_response = requests.post(f"{BASE_URL}/conversation/chat",
                             json={"text": "หาที่เที่ยวในเชียงใหม่", 
                                   "session_id": session_id})
bot_message = chat_response.json()["message"]
```

### JavaScript/React Example
```javascript
const ConversationalAI = {
    async createSession(userId) {
        const response = await fetch('/api/ai/conversation/session', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({user_id: userId})
        });
        return await response.json();
    },
    
    async chat(text, sessionId) {
        const response = await fetch('/api/ai/conversation/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({text, session_id: sessionId})
        });
        return await response.json();
    },
    
    async detectIntent(text) {
        const response = await fetch('/api/ai/nlu/intent', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({text})
        });
        return await response.json();
    }
};

// Usage
const session = await ConversationalAI.createSession('user123');
const response = await ConversationalAI.chat('หาที่เที่ยวในเชียงใหม่', 
                                            session.session_id);
```

## Performance & Scalability

- **Intent Detection**: ~10-20ms per request (rule-based)
- **Query Generation**: ~50-100ms per request (includes database queries)
- **Session Management**: ~5-10ms per operation
- **Memory Usage**: Minimal (no heavy ML models loaded)

## Configuration

### Environment Variables
```env
# Conversational AI settings (optional)
AI_CONVERSATION_ENABLED=true
AI_SESSION_TIMEOUT_HOURS=24
AI_MAX_CONVERSATION_HISTORY=10
```

## Monitoring & Analytics

- **Session Analytics**: Track active sessions, user engagement
- **Intent Distribution**: Monitor most common user intents
- **Query Performance**: Track query generation success rates
- **Conversation Flow**: Analyze conversation patterns

Updated AI stats endpoint now includes conversation metrics:
```http
GET /api/ai/stats
```

Returns conversation statistics along with existing AI metrics.

## API Endpoints

### Keyword Extraction

#### Extract Keywords from Attraction
```http
POST /api/ai/keywords/extract
Content-Type: application/json

{
    "attraction_id": 123
}
```

#### Extract Keywords from Text
```http
POST /api/ai/keywords/extract
Content-Type: application/json

{
    "text": "Beautiful temple with ancient architecture"
}
```

#### Batch Extract Keywords
```http
POST /api/ai/keywords/batch-extract
Content-Type: application/json

{
    "attraction_ids": [1, 2, 3, 4, 5]
}
```

### Personalized Recommendations

#### Get User Recommendations
```http
GET /api/ai/recommendations/{user_id}?limit=10&exclude_viewed=true
```

#### Record User Interaction
```http
POST /api/ai/interactions
Content-Type: application/json

{
    "user_id": "user123",
    "attraction_id": 456,
    "interaction_type": "view"
}
```

Interaction types: `view`, `click`, `like`, `share`, `bookmark`

### Trend Analysis

#### Analyze Popularity Trends
```http
GET /api/ai/trends/analyze?days=30&province=Bangkok
```

#### Get Heatmap Data
```http
GET /api/ai/trends/heatmap?days=30
```

#### Get Future Predictions
```http
GET /api/ai/trends/predictions?days_ahead=7
```

### Content Improvement

#### Improve Attraction Content
```http
POST /api/ai/content/improve
Content-Type: application/json

{
    "attraction_id": 123,
    "field": "body",
    "style": "friendly",
    "apply_changes": false
}
```

Styles: `friendly`, `professional`, `casual`, `formal`

#### Get Content Suggestions
```http
POST /api/ai/content/suggestions
Content-Type: application/json

{
    "attraction_id": 123,
    "field": "body"
}
```

#### Batch Content Improvement
```http
POST /api/ai/content/batch-improve
Content-Type: application/json

{
    "attraction_ids": [1, 2, 3],
    "field": "body",
    "style": "friendly",
    "apply_changes": true
}
```

### Statistics

#### Get AI Usage Statistics
```http
GET /api/ai/stats
```

## Background Tasks

The system includes several background tasks for AI processing:

### Scheduled Tasks

- **Daily Keyword Extraction** (4:00 AM) - Process 50 attractions without keywords
- **Weekly Content Improvement** (Monday 5:00 AM) - Improve 20 attractions per week
- **Monthly Interaction Cleanup** (1st day 6:00 AM) - Clean up old interactions (90+ days)

### Manual Tasks

You can trigger these tasks manually using Celery:

```python
from tasks import extract_keywords_batch_task, improve_content_batch_task

# Extract keywords for specific attractions
extract_keywords_batch_task.delay([1, 2, 3, 4, 5])

# Improve content for attractions
improve_content_batch_task.delay(
    attraction_ids=[1, 2, 3],
    field='body',
    style='friendly'
)
```

## Database Schema Changes

### New Fields in `attractions` Table

```sql
ALTER TABLE attractions ADD COLUMN keywords TEXT;
ALTER TABLE attractions ADD COLUMN keywords_extracted BOOLEAN DEFAULT FALSE;
ALTER TABLE attractions ADD COLUMN content_rewritten BOOLEAN DEFAULT FALSE;
ALTER TABLE attractions ADD COLUMN view_count INTEGER DEFAULT 0;
```

### New `user_interactions` Table

```sql
CREATE TABLE user_interactions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    attraction_id INTEGER REFERENCES attractions(id),
    interaction_type VARCHAR(50) NOT NULL,
    interaction_value FLOAT DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Usage Examples

### Python Client Examples

```python
import requests

BASE_URL = "http://localhost:5000/api/ai"

# Extract keywords
response = requests.post(f"{BASE_URL}/keywords/extract", json={
    "text": "Beautiful ancient temple with traditional Thai architecture"
})
keywords = response.json()["keywords"]
print(f"Keywords: {keywords}")

# Get recommendations
response = requests.get(f"{BASE_URL}/recommendations/user123?limit=5")
recommendations = response.json()["recommendations"]
for rec in recommendations:
    print(f"Recommended: {rec['attraction']['title']} (Score: {rec['score']})")

# Record interaction
requests.post(f"{BASE_URL}/interactions", json={
    "user_id": "user123",
    "attraction_id": 456,
    "interaction_type": "view"
})

# Improve content
response = requests.post(f"{BASE_URL}/content/improve", json={
    "text": "this place is nice",
    "style": "friendly"
})
improved = response.json()["improved_text"]
print(f"Improved: {improved}")
```

### JavaScript/Frontend Examples

```javascript
// Extract keywords
const extractKeywords = async (text) => {
    const response = await fetch('/api/ai/keywords/extract', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
    });
    const result = await response.json();
    return result.keywords;
};

// Get recommendations
const getRecommendations = async (userId, limit = 10) => {
    const response = await fetch(`/api/ai/recommendations/${userId}?limit=${limit}`);
    const result = await response.json();
    return result.recommendations;
};

// Record interaction
const recordInteraction = async (userId, attractionId, type = 'view') => {
    await fetch('/api/ai/interactions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_id: userId,
            attraction_id: attractionId,
            interaction_type: type
        })
    });
};

// Get trend data
const getTrends = async (days = 30) => {
    const response = await fetch(`/api/ai/trends/analyze?days=${days}`);
    return await response.json();
};
```

## Configuration

### Environment Variables

```env
# AI Feature settings (optional)
AI_KEYWORD_EXTRACTION_ENABLED=true
AI_CONTENT_REWRITING_ENABLED=true
AI_RECOMMENDATIONS_ENABLED=true
AI_TREND_ANALYSIS_ENABLED=true

# Advanced ML libraries (optional - fallback methods available)
USE_TRANSFORMERS=false
USE_SPACY=false
USE_SKLEARN=false
```

## Fallback Strategy

All AI features are designed with fallback mechanisms:

- **Keyword Extraction**: Falls back to rule-based text processing if ML libraries are unavailable
- **Recommendations**: Uses popularity-based recommendations if ML models can't be loaded
- **Content Rewriting**: Uses rule-based text improvements if AI models are unavailable
- **Trend Analysis**: Provides basic statistical analysis without requiring complex ML

This ensures the system remains functional even in environments with limited resources.

## Performance Considerations

- **Keyword extraction**: ~50-100ms per attraction (fallback method)
- **Recommendations**: ~100-200ms per user (with database queries)
- **Content rewriting**: ~20-50ms per text (rule-based)
- **Trend analysis**: ~200-500ms per request (depending on data size)

For better performance with large datasets, use the batch processing endpoints and background tasks.

## Monitoring

Monitor AI feature usage through:

1. **AI Statistics Endpoint**: `/api/ai/stats`
2. **Dashboard**: Integration with existing dashboard at `/api/dashboard`
3. **Logs**: Check application logs for AI service activity
4. **Database**: Monitor the `user_interactions` table growth

## Troubleshooting

### Common Issues

1. **Keywords not extracting**: Check if attractions have content in `title` or `body` fields
2. **No recommendations**: Ensure user interactions are being recorded
3. **Content not improving**: Verify the attraction has text content to improve
4. **Trend data empty**: Make sure user interactions are being recorded over time

### Debug Mode

Enable debug logging to see detailed AI service activity:

```python
import logging
logging.getLogger('app.services').setLevel(logging.DEBUG)
```

This will show detailed information about AI processing, fallback usage, and performance metrics.