# AI Content Enrichment Features

This document describes the new **AI Content Enrichment** features added to the Database Painaidee system, fulfilling the requirements for:

- 📝 **Create Place Descriptions** using GPT/LLMs
- 🌍 **Generate Multilingual Content** (English, Thai, Chinese)
- 🔍 **Highlight Key Features** extraction
- 🖼️ **Generate Images** using DALL·E or fallback methods

## Overview

The AI Content Enrichment system provides comprehensive content enhancement for attraction data through four main capabilities:

1. **Place Description Generation** - Creates rich, engaging descriptions using GPT or template-based fallback methods
2. **Multilingual Content Creation** - Translates content into multiple languages with culturally appropriate tone
3. **Key Features Highlighting** - Extracts and categorizes important features like "family-friendly", "great view", "beachfront"
4. **Image Generation** - Creates relevant images using DALL·E or provides curated placeholder images

## Database Schema Changes

New fields added to the `attractions` table:

```sql
-- Content Enrichment flags
ALTER TABLE attractions ADD COLUMN content_enriched BOOLEAN DEFAULT FALSE;
ALTER TABLE attractions ADD COLUMN key_features TEXT; -- JSON string of key features
ALTER TABLE attractions ADD COLUMN generated_images TEXT; -- JSON string of image URLs

-- Multilingual Content Support
ALTER TABLE attractions ADD COLUMN title_en TEXT; -- English title
ALTER TABLE attractions ADD COLUMN title_th TEXT; -- Thai title  
ALTER TABLE attractions ADD COLUMN title_zh TEXT; -- Chinese title
ALTER TABLE attractions ADD COLUMN body_en TEXT;  -- English description
ALTER TABLE attractions ADD COLUMN body_th TEXT;  -- Thai description
ALTER TABLE attractions ADD COLUMN body_zh TEXT;  -- Chinese description
```

## API Endpoints

### 1. Place Description Generation

#### Generate Enhanced Description
```http
POST /api/ai/enrich/description
Content-Type: application/json

{
    "attraction_id": 123,
    "apply_changes": false
}
```

**Or with custom data:**
```http
POST /api/ai/enrich/description
Content-Type: application/json

{
    "title": "Wat Phra Kaew",
    "body": "Temple in Bangkok",
    "province": "Bangkok"
}
```

**Response:**
```json
{
    "success": true,
    "description": "Discover the beauty of Wat Phra Kaew, a remarkable destination in Bangkok...",
    "method": "gpt",
    "model": "text-davinci-003",
    "attraction_id": 123,
    "changes_applied": false,
    "generated_at": "2024-01-15T10:30:00Z"
}
```

### 2. Multilingual Content Generation

#### Translate Content
```http
POST /api/ai/enrich/multilingual
Content-Type: application/json

{
    "attraction_id": 123,
    "field": "body",
    "languages": ["en", "th", "zh"],
    "apply_changes": true
}
```

**Or with text:**
```http
POST /api/ai/enrich/multilingual
Content-Type: application/json

{
    "text": "Beautiful temple with traditional architecture",
    "languages": ["en", "th", "zh"]
}
```

**Response:**
```json
{
    "success": true,
    "translations": {
        "original": "Beautiful temple with traditional architecture",
        "en": "Beautiful temple with traditional architecture", 
        "th": "วัดที่สวยงามด้วยสถาปัตยกรรมแบบดั้งเดิม",
        "zh": "拥有传统建筑的美丽寺庙"
    },
    "method": "googletrans",
    "source_language": "en",
    "attraction_id": 123,
    "field": "body",
    "changes_applied": true,
    "generated_at": "2024-01-15T10:30:00Z"
}
```

### 3. Key Features Highlighting

#### Extract Key Features
```http
POST /api/ai/enrich/features
Content-Type: application/json

{
    "attraction_id": 123,
    "apply_changes": true
}
```

**Or with text:**
```http
POST /api/ai/enrich/features
Content-Type: application/json

{
    "text": "Family-friendly beachfront resort with great view and traditional architecture"
}
```

**Response:**
```json
{
    "success": true,
    "features": [
        "family-friendly",
        "beachfront", 
        "great view",
        "traditional"
    ],
    "categories": {
        "family": ["family-friendly"],
        "location": ["beachfront"],
        "scenery": ["great view"],
        "style": ["traditional"]
    },
    "feature_count": 4,
    "attraction_id": 123,
    "changes_applied": true,
    "generated_at": "2024-01-15T10:30:00Z"
}
```

### 4. Image Generation

#### Generate Images
```http
POST /api/ai/enrich/images
Content-Type: application/json

{
    "attraction_id": 123,
    "num_images": 2,
    "apply_changes": true
}
```

**Or with custom data:**
```http
POST /api/ai/enrich/images
Content-Type: application/json

{
    "title": "Wat Phra Kaew",
    "body": "Temple in Bangkok",
    "province": "Bangkok",
    "num_images": 1
}
```

**Response:**
```json
{
    "success": true,
    "image_urls": [
        "https://source.unsplash.com/1024x768/?thailand+travel+wat+phra+kaew+bangkok&sig=0",
        "https://source.unsplash.com/1024x768/?thailand+travel+wat+phra+kaew+bangkok&sig=1"
    ],
    "method": "placeholder",
    "search_query": "thailand+travel+wat+phra+kaew+bangkok",
    "note": "Using placeholder images from Unsplash",
    "attraction_id": 123,
    "changes_applied": true,
    "generated_at": "2024-01-15T10:30:00Z"
}
```

### 5. Complete Enrichment

#### Perform All Enrichment Features
```http
POST /api/ai/enrich/complete
Content-Type: application/json

{
    "attraction_id": 123,
    "apply_changes": true
}
```

**Response:**
```json
{
    "success": true,
    "attraction_id": 123,
    "enriched_at": "2024-01-15T10:30:00Z",
    "changes_applied": true,
    "features": {
        "description": {
            "success": true,
            "description": "Enhanced description...",
            "method": "gpt"
        },
        "key_features": {
            "success": true,
            "features": ["family-friendly", "beachfront"],
            "categories": {...}
        },
        "multilingual": {
            "success": true,
            "translations": {...}
        },
        "images": {
            "success": true,
            "image_urls": [...]
        }
    }
}
```

### 6. Statistics

#### Get Enrichment Statistics
```http
GET /api/ai/enrich/stats
```

**Response:**
```json
{
    "total_attractions": 150,
    "enriched_attractions": 45,
    "enrichment_coverage": 30.0,
    "features": {
        "multilingual_content": {
            "count": 38,
            "coverage": 25.33
        },
        "key_features": {
            "count": 42,
            "coverage": 28.0
        },
        "generated_images": {
            "count": 35,
            "coverage": 23.33
        }
    }
}
```

## Configuration

### Environment Variables

Add these to your `.env` file:

```env
# AI Content Enrichment Configuration
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-3.5-turbo
CONTENT_ENRICHMENT_ENABLED=true
MULTILINGUAL_ENABLED=true
IMAGE_GENERATION_ENABLED=true
SUPPORTED_LANGUAGES=en,th,zh
```

### Dependencies

New dependencies added to `requirements.txt`:

```
openai>=1.0.0
Pillow>=8.0.0
googletrans==4.0.0rc1
langdetect>=1.0.9
```

## Fallback Strategy

All features are designed with robust fallback mechanisms:

### 1. Description Generation
- **Primary**: GPT/LLM generation with customizable prompts
- **Fallback**: Template-based description generation using attraction data

### 2. Multilingual Translation
- **Primary**: Google Translate API for accurate translations
- **Fallback**: Returns original text with language indicators

### 3. Key Features Extraction
- **Method**: Rule-based pattern matching against comprehensive keyword database
- **Categories**: Automatic categorization into family, scenery, location, style, activities, atmosphere

### 4. Image Generation
- **Primary**: DALL-E API for custom image generation
- **Fallback**: Curated Unsplash images based on attraction keywords

## Usage Examples

### Python Client
```python
import requests

BASE_URL = "http://localhost:5000/api/ai/enrich"

# Generate description
response = requests.post(f"{BASE_URL}/description", json={
    "attraction_id": 123,
    "apply_changes": True
})
result = response.json()
print(f"Generated: {result['description']}")

# Complete enrichment
response = requests.post(f"{BASE_URL}/complete", json={
    "attraction_id": 123,
    "apply_changes": True
})
result = response.json()
print(f"Enrichment successful: {result['success']}")

# Get statistics
response = requests.get(f"{BASE_URL}/stats")
stats = response.json()
print(f"Coverage: {stats['enrichment_coverage']}%")
```

### JavaScript Frontend
```javascript
// Generate multilingual content
const enrichMultilingual = async (attractionId) => {
    const response = await fetch('/api/ai/enrich/multilingual', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            attraction_id: attractionId,
            field: 'body',
            languages: ['en', 'th', 'zh'],
            apply_changes: true
        })
    });
    return await response.json();
};

// Extract key features
const extractFeatures = async (text) => {
    const response = await fetch('/api/ai/enrich/features', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
    });
    const result = await response.json();
    return result.features;
};

// Complete enrichment
const enrichAttraction = async (attractionId) => {
    const response = await fetch('/api/ai/enrich/complete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            attraction_id: attractionId,
            apply_changes: true
        })
    });
    return await response.json();
};
```

## Performance & Scalability

### Response Times (Fallback Methods)
- **Description Generation**: ~50-100ms per attraction
- **Key Features Extraction**: ~20-50ms per text
- **Multilingual Translation**: ~200-500ms per text (with Google Translate)
- **Image Generation**: ~100ms per request (placeholder method)

### Batch Processing
Use batch endpoints for processing multiple attractions:

```http
POST /api/ai/enrich/batch
Content-Type: application/json

{
    "attraction_ids": [1, 2, 3, 4, 5],
    "features": ["description", "multilingual", "key_features"],
    "apply_changes": true
}
```

## Integration with Existing Features

The content enrichment system integrates seamlessly with existing AI features:

- **Keywords**: Extracted features complement existing keyword extraction
- **Content Improvement**: Enhanced descriptions work with content rewriting
- **Recommendations**: Multilingual content improves recommendation accuracy
- **Analytics**: Enrichment statistics are included in overall AI stats

## Monitoring & Troubleshooting

### Monitor Usage
```bash
# Check enrichment statistics
curl http://localhost:5000/api/ai/enrich/stats

# Check overall AI statistics  
curl http://localhost:5000/api/ai/stats
```

### Common Issues

1. **No descriptions generated**: Check if attractions have title/body content
2. **Translation not working**: Verify Google Translate API availability
3. **Images not generating**: Fallback will use Unsplash placeholders
4. **Features not extracted**: Ensure attraction content contains recognizable keywords

### Debug Logging

Enable detailed logging in your application:

```python
import logging
logging.getLogger('app.services.content_enrichment').setLevel(logging.DEBUG)
```

This provides detailed information about:
- Fallback method usage
- API call results
- Processing performance
- Error details

## Future Enhancements

The modular design allows for easy extension:

- **Custom LLM Models**: Replace GPT with local models
- **Additional Languages**: Extend multilingual support
- **Advanced Image Generation**: Integration with Midjourney, Stable Diffusion
- **Feature Learning**: ML-based feature extraction from user behavior
- **Cultural Adaptation**: Tone and style adaptation for different tourist segments

## Security & Privacy

- API keys are securely stored in environment variables
- No sensitive data is logged or transmitted to external services without explicit configuration
- Fallback methods ensure functionality without external API dependencies
- All generated content is stored locally in your database