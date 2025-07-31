# Database Painaidee - Enhanced Features Documentation

## 🎉 New Features Overview

This update adds comprehensive enhancements to the Database Painaidee ETL pipeline with advanced data processing, caching, and monitoring capabilities.

## 🔥 Key Features Added

### 🔁 Enhanced Duplicate Checking
- **External ID checking**: Continues to use external API IDs for duplicate detection
- **Content hash checking**: Added SHA-256 hash-based duplicate detection using `hash(json.dumps(data, sort_keys=True))`
- **Combined approach**: Checks both methods to prevent duplicates more effectively

```python
# Automatic hash generation in Attraction model
attraction.content_hash = attraction.generate_content_hash()

# Enhanced duplicate checking in loader
existing_by_id = Attraction.find_duplicate_by_external_id(external_id)
existing_by_hash = Attraction.find_duplicate_by_hash(content_hash)
```

### 📦 Comprehensive Sync Logging
- **New `sync_logs` table** tracks all sync operations with detailed metrics
- **Operation tracking**: Start/end times, fetched/saved/skipped counts, error details
- **Sync types**: 'daily', 'update', 'manual' for different operation contexts

```python
# Automatic sync logging in ETL orchestrator
sync_log = SyncLog(
    sync_type='daily',
    api_source='external_api',
    status='running'
)
```

### 📤 Advanced Data Transformation
- **Date normalization**: Converts various formats (dd/mm/yyyy, dd-mm-yyyy) to YYYY-MM-DD
- **Address parsing**: Extracts Thai provinces and districts from full addresses
- **Location categorization**: Intelligent classification into categories (วัด, ภูเขา, ทะเล, etc.)
- **Text cleaning**: Removes HTML tags, normalizes whitespace

```python
# Enhanced data transformation pipeline
transformed_data = DataTransformer.transform_attraction_data(raw_data)
# Automatically applies: date normalization, address parsing, categorization, text cleaning
```

### 💾 Redis Caching System
- **API response caching**: Caches API responses to reduce external API calls
- **Configurable TTL**: Different cache durations for different sync types
- **Cache invalidation**: Manual and automatic cache clearing
- **Graceful degradation**: Falls back to direct API calls if Redis unavailable

```python
# Cached API requests
response = fetch_json_with_retry(url, use_cache=True, cache_ttl=3600)

# Cache management
cache_manager.invalidate_api_cache(api_url)  # Clear specific URL
cache_manager.get_cache_stats()  # Get cache statistics
```

### 🕐 Multiple Scheduled Sync Times
- **Daily sync** at 1:00 AM for comprehensive data updates
- **Update sync** at 1:00 PM for latest changes check
- **Configurable sync types** with different caching strategies

```python
# Celery Beat schedule in scheduler.py
'fetch-attractions-daily': {
    'task': 'tasks.fetch_attractions_task',
    'schedule': crontab(hour=1, minute=0),
    'kwargs': {'sync_type': 'daily'}
},
'fetch-attractions-update': {
    'task': 'tasks.fetch_attractions_task', 
    'schedule': crontab(hour=13, minute=0),
    'kwargs': {'sync_type': 'update'}
}
```

### ⚠️ Enhanced Error Handling & Retry
- **Comprehensive error tracking** throughout ETL pipeline
- **Detailed error logging** with context and troubleshooting information
- **Enhanced retry logic** with exponential backoff (already present, now better integrated)
- **Error aggregation** in sync logs for easy debugging

### 🧪 Complete Mock Testing Suite
- **pytest-based testing** with requests-mock for API simulation
- **Comprehensive test coverage** for all new features
- **Mock API demonstrations** showing complete ETL pipeline
- **Edge case testing** for robust error handling

## 🚀 New API Endpoints

### Sync Logs Management
- `GET /api/sync-logs` - List sync operation history with pagination and filtering
- `GET /api/sync-logs/{id}` - Get detailed sync operation information

### Cache Management  
- `GET /api/cache/stats` - Get Redis cache statistics and health
- `POST /api/cache/invalidate` - Clear API response cache

### Enhanced Sync
- `POST /api/attractions/sync` - Enhanced manual sync with options:
  ```json
  {
    "sync_type": "manual",
    "use_cache": false
  }
  ```

### Enhanced Health Check
- `GET /api/health` - Now includes database and cache status

## 🔧 Configuration Options

### Environment Variables
```env
# Cache settings
REDIS_URL=redis://localhost:6379/0

# Pagination (already exists)
PAGINATION_ENABLED=true
PAGINATION_PAGE_SIZE=20
PAGINATION_MAX_PAGES=100

# API settings (already exists)
EXTERNAL_API_URL=https://your-api.com/data
API_TIMEOUT=30
```

## 📊 Data Model Enhancements

### Enhanced Attraction Model
```python
class Attraction(db.Model):
    # Existing fields...
    content_hash = db.Column(db.String(64), nullable=True, index=True)
    location_category = db.Column(db.String(50), nullable=True)  # 'วัด', 'ภูเขา', etc.
    province = db.Column(db.String(100), nullable=True)
    district = db.Column(db.String(100), nullable=True)
    original_date = db.Column(db.String(50), nullable=True)
    normalized_date = db.Column(db.Date, nullable=True)
```

### New SyncLog Model
```python
class SyncLog(db.Model):
    sync_type = db.Column(db.String(50), nullable=False)
    api_source = db.Column(db.String(100), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), nullable=False)
    total_fetched = db.Column(db.Integer, default=0)
    total_saved = db.Column(db.Integer, default=0)
    total_skipped = db.Column(db.Integer, default=0)
    errors = db.Column(db.Text, nullable=True)
```

## 🧪 Testing the New Features

### Run Comprehensive Tests
```bash
# Run all enhanced feature tests
python -m pytest test_enhanced_features.py -v

# Run ETL pipeline demonstration
python -m pytest test_etl_demo.py -v -s

# Run existing tests to ensure compatibility
python test_setup.py
```

### Test Thai Data Processing
```python
from app.utils.data_transform import DataTransformer

# Test date normalization
date = DataTransformer.normalize_date("15/03/2024")  # Returns datetime(2024, 3, 15)

# Test address parsing
province, district = DataTransformer.parse_address("อำเภอเมือง จังหวัดกรุงเทพมหานคร")
# Returns: ("กรุงเทพมหานคร", "เมือง")

# Test location categorization
category = DataTransformer.categorize_location("วัดพระแก้ว", "วัดที่สวยงาม")
# Returns: "วัด"
```

## 🔍 Monitoring & Debugging

### View Sync History
```bash
curl http://localhost:5000/api/sync-logs
```

### Check Cache Status
```bash
curl http://localhost:5000/api/cache/stats
```

### Enhanced Health Check
```bash
curl http://localhost:5000/api/health
```

### Clear Cache
```bash
curl -X POST http://localhost:5000/api/cache/invalidate \
  -H "Content-Type: application/json" \
  -d '{"api_url": "https://specific-url.com"}'
```

## 🎯 Location Categories Supported

The system now automatically categorizes Thai attractions into:

- **วัด** (Temples): วัด, temple, monastery, shrine, โบสถ์
- **ทะเล** (Sea/Beach): ทะเล, หาด, อ่าว, เกาะ, sea, beach, bay, island  
- **ภูเขา** (Mountains): ดอย, เขา, ภูเขา, mountain, hill, peak
- **น้ำตก** (Waterfalls): น้ำตก, waterfall, cascade, falls
- **อุทยาน** (Parks): อุทยาน, สวน, park, garden
- **พิพิธภัณฑ์** (Museums): พิพิธภัณฑ์, museum, gallery, exhibition
- **ตลาด** (Markets): ตลาด, market, bazaar, shopping
- **อื่นๆ** (Others): Default category for unmatched locations

## 🚦 Deployment Notes

1. **Database Migration**: Run database migrations to create the new `sync_logs` table
2. **Redis Setup**: Ensure Redis is available for caching (gracefully degrades if not available)
3. **Environment Variables**: Update any new configuration variables
4. **Dependencies**: Install new testing dependencies with `pip install -r requirements.txt`

All features are backwards compatible and will not break existing functionality! 🎉