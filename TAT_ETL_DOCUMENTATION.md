# TAT Open Data ETL Feature

This document describes the implementation of the ETL (Extract, Transform, Load) feature for loading tourism attraction data from TAT (Tourism Authority of Thailand) Open Data CSV into PostgreSQL.

## Overview

The TAT ETL feature extends the existing ETL architecture to support CSV data from Thailand's official tourism database. It follows the same patterns as the existing external API ETL but is specifically designed for TAT's CSV format and Thai tourism data.

## Features

- **CSV Data Extraction**: Downloads and processes CSV files from TAT Open Data
- **Thai Text Support**: Handles Thai language encoding (UTF-8, TIS-620, CP874)
- **Tourism-Specific Fields**: Supports additional fields like opening hours, entrance fees, contact information
- **Automatic Scheduling**: Weekly ETL runs to keep data current
- **Manual Triggers**: API endpoint for on-demand synchronization
- **Geocoding Support**: Optional coordinate lookup for missing location data
- **Backward Compatibility**: Works alongside existing attraction data

## Architecture

### Files Modified/Created

1. **`extractors/tat_csv.py`** - New TAT CSV extractor
2. **`app/models.py`** - Enhanced Attraction model with tourism fields
3. **`transformers/attraction_transformer.py`** - Added TAT data transformer
4. **`etl_orchestrator.py`** - Added TAT ETL orchestration method
5. **`tasks.py`** - Added background task for TAT ETL
6. **`app/routes/attractions.py`** - Added API endpoint for manual sync
7. **`scheduler.py`** - Added weekly scheduling

### Database Schema Enhancement

The `Attraction` model has been enhanced with tourism-specific fields while maintaining backward compatibility:

```python
# New tourism fields
name = db.Column(db.String(200), nullable=True)  # Alternative to title
description = db.Column(db.Text, nullable=True)  # Alternative to body
address = db.Column(db.Text, nullable=True)
district = db.Column(db.String(100), nullable=True)
category = db.Column(db.String(100), nullable=True)
opening_hours = db.Column(db.Text, nullable=True)
entrance_fee = db.Column(db.Text, nullable=True)
contact_phone = db.Column(db.String(50), nullable=True)
source = db.Column(db.String(100), nullable=True)  # Data source identifier
```

## Usage

### 1. Manual API Sync

**Basic sync with default TAT URL:**
```bash
curl -X POST http://localhost:5000/api/attractions/sync/tat
```

**Sync with custom CSV URL:**
```bash
curl -X POST http://localhost:5000/api/attractions/sync/tat \
     -H "Content-Type: application/json" \
     -d '{"csv_url": "https://custom-url.com/attractions.csv"}'
```

**Sync with geocoding enabled:**
```bash
curl -X POST http://localhost:5000/api/attractions/sync/tat \
     -H "Content-Type: application/json" \
     -d '{"enable_geocoding": true}'
```

### 2. Programmatic Usage

```python
from etl_orchestrator import ETLOrchestrator

# Basic ETL
result = ETLOrchestrator.run_tat_csv_etl(
    csv_url="https://opendata.tourismthailand.org/data/attractions.csv"
)

# ETL with geocoding
result = ETLOrchestrator.run_tat_csv_etl(
    csv_url="https://opendata.tourismthailand.org/data/attractions.csv",
    enable_geocoding=True,
    google_api_key="your-api-key"
)

print(f"Processed: {result['total_processed']}")
print(f"Saved: {result['saved']}")
print(f"Updated: {result['updated']}")
print(f"Skipped: {result['skipped']}")
```

### 3. Background Task

```python
from tasks import fetch_tat_attractions_task

# Queue TAT ETL task
task = fetch_tat_attractions_task.delay(
    csv_url="https://opendata.tourismthailand.org/data/attractions.csv",
    enable_geocoding=False
)

# Check task status
result = task.get()
```

## Scheduled Execution

The TAT ETL runs automatically every Monday at 1:30 AM (configured in `scheduler.py`):

```python
'fetch-tat-attractions-weekly': {
    'task': 'tasks.fetch_tat_attractions_task',
    'schedule': crontab(hour=1, minute=30, day_of_week=1),
    'kwargs': {'enable_geocoding': False}
}
```

## Data Mapping

The ETL process maps TAT CSV fields to database fields with support for both English and Thai column names:

| TAT CSV Field | Database Field | Thai Alternative |
|---------------|----------------|------------------|
| name | name, title | ชื่อสถานที่ |
| description | description, body | รายละเอียด |
| province | province | จังหวัด |
| district | district | อำเภอ |
| latitude | latitude | ละติจูด |
| longitude | longitude | ลองจิจูด |
| category | category | ประเภท |
| opening_hours | opening_hours | เวลาเปิด |
| entrance_fee | entrance_fee | ค่าเข้าชม |
| contact_phone | contact_phone | โทรศัพท์ |
| address | address | ที่อยู่ |

## Configuration

### Environment Variables

```env
# TAT ETL Configuration
API_TIMEOUT=60                    # Timeout for CSV download (seconds)
AUTO_BACKUP_BEFORE_SYNC=true     # Create backup before ETL
GOOGLE_GEOCODING_API_KEY=key     # For geocoding (optional)
```

### Default Settings

- **Default CSV URL**: `https://opendata.tourismthailand.org/data/attractions.csv`
- **Timeout**: 60 seconds
- **Geocoding**: Disabled by default (to avoid API rate limits)
- **Schedule**: Weekly on Monday at 1:30 AM
- **Source Tag**: "TAT Open Data"

## Error Handling

The ETL process includes comprehensive error handling:

1. **Network Errors**: Automatic retries for CSV download failures
2. **Encoding Issues**: Multiple encoding attempts for Thai text
3. **Data Validation**: Graceful handling of malformed records
4. **Database Errors**: Transaction rollback and error reporting
5. **Duplicate Handling**: Automatic duplicate detection and skipping

## Monitoring

### API Response

```json
{
  "success": true,
  "message": "TAT CSV ETL sync completed",
  "csv_url": "https://opendata.tourismthailand.org/data/attractions.csv",
  "geocoding_enabled": false,
  "saved": 150,
  "updated": 25,
  "skipped": 5,
  "errors": 0,
  "total_processed": 180
}
```

### Sync Statistics

The system automatically records ETL statistics in the `sync_statistics` table:

- Processing time
- Success rate
- Number of items processed/saved/skipped/errors
- API source identification

### Logs

All ETL operations are logged with appropriate levels:

```
INFO - Starting ETL process for TAT CSV data
INFO - CSV URL: https://opendata.tourismthailand.org/data/attractions.csv
INFO - Successfully extracted 180 TAT CSV items
INFO - Successfully transformed 180 TAT CSV attractions
INFO - Loading 180 attractions to database
INFO - TAT CSV ETL process completed: {'saved': 150, 'updated': 25, 'skipped': 5}
```

## Testing

### Run Tests

```bash
# Test basic functionality
python test_tat_etl.py

# Test full integration
python test_tat_integration.py

# Run example
python example_tat_etl.py
```

### Sample Data Testing

The implementation includes sample data for testing without network access:

```python
# Demo with sample data
echo "1" | python example_tat_etl.py
```

## Benefits

1. **Comprehensive Tourism Data**: Access to official TAT attraction database
2. **Automated Updates**: Weekly synchronization keeps data current
3. **Flexible Execution**: Manual triggers and scheduled runs
4. **Data Quality**: Duplicate detection and validation
5. **Scalability**: Memory-efficient CSV processing
6. **Monitoring**: Built-in statistics and logging
7. **Compatibility**: Works with existing attraction data structure

## Integration with Existing Features

The TAT ETL seamlessly integrates with existing system features:

- **AI Features**: Keyword extraction, content improvement
- **Geocoding**: Automatic coordinate lookup
- **Versioning**: History tracking for data changes
- **Backup**: Automatic pre-sync backups
- **Dashboard**: Real-time monitoring and statistics
- **API**: RESTful endpoints for data access

## Production Considerations

1. **API Limits**: Disable geocoding for scheduled runs to avoid quota issues
2. **Data Volume**: TAT CSV may contain thousands of attractions
3. **Encoding**: Ensure proper Thai text handling in production environment
4. **Monitoring**: Set up alerts for ETL failures
5. **Backup**: Verify backup system before large data imports
6. **Performance**: Monitor database performance with large datasets

This implementation provides a robust, scalable solution for integrating TAT Open Data into the 'ไปไหนดี' (Painaidee) tourism application.