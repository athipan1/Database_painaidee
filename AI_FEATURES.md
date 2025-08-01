# AI Features Documentation

This document describes the new AI-powered features added to the Database Painaidee system.

## Overview

The system now includes 4 AI-driven features to enhance attraction management:

1. **🔎 AI Keyword Extraction** - Extract meaningful keywords from descriptions
2. **🧠 AI Personalized Recommendations** - Suggest attractions based on user behavior
3. **📈 Heatmap/Trend AI** - Analytics and trend analysis
4. **📚 AI Content Rewriting** - Improve content readability and style

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