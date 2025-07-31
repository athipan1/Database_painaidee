# ETL Architecture Documentation

## Overview

This project has been restructured to follow ETL (Extract, Transform, Load) best practices by separating the data pipeline into three distinct layers:

1. **Extractors** - Data extraction from various APIs
2. **Transformers** - Data transformation and normalization  
3. **Loaders** - Duplicate checking and database insertion

## Directory Structure

```
├── extractors/                    # Data extraction layer
│   ├── __init__.py
│   ├── external_api.py            # JSONPlaceholder API extractor
│   ├── tourism_thailand.py        # Tourism Thailand API extractor (placeholder)
│   └── opentripmap.py            # OpenTripMap API extractor (placeholder)
├── transformers/                  # Data transformation layer
│   ├── __init__.py
│   └── attraction_transformer.py  # Transforms raw data to database format
├── loaders/                       # Data loading layer
│   ├── __init__.py
│   └── attraction_loader.py       # Handles deduplication and database insertion
└── etl_orchestrator.py           # Coordinates the ETL pipeline
```

## Components

### Extractors (`extractors/`)

Each extractor handles data extraction from a specific API source:

- **`ExternalAPIExtractor`**: Extracts from JSONPlaceholder API (current implementation)
- **`TourismThailandExtractor`**: Placeholder for Tourism Thailand API integration
- **`OpenTripMapExtractor`**: Placeholder for OpenTripMap API integration

All extractors use the robust retry mechanism from `app.utils.fetch` for reliable data extraction.

### Transformers (`transformers/`)

The `AttractionTransformer` class provides methods to transform raw API data into database-ready `Attraction` objects:

- **`transform_external_api_data()`**: Transforms JSONPlaceholder API data
- **`transform_tourism_thailand_data()`**: Transforms Tourism Thailand API data  
- **`transform_opentripmap_data()`**: Transforms OpenTripMap API data

Each method handles the specific data format and field mappings for its source.

### Loaders (`loaders/`)

The `AttractionLoader` class handles:

- **Duplicate checking**: Prevents duplicate entries based on `external_id`
- **Database insertion**: Safely inserts new attractions with error handling
- **Batch processing**: Supports bulk loading for large datasets

### ETL Orchestrator (`etl_orchestrator.py`)

The `ETLOrchestrator` coordinates the complete ETL pipeline:

- **`run_external_api_etl()`**: Full ETL process for JSONPlaceholder API
- **`run_tourism_thailand_etl()`**: Full ETL process for Tourism Thailand API
- **`run_opentripmap_etl()`**: Full ETL process for OpenTripMap API

## Integration

### Celery Tasks (`tasks.py`)

The background task has been refactored to use the ETL pipeline:

```python
@celery.task(bind=True)
def fetch_attractions_task(self):
    """Background task using ETL pipeline."""
    with app.app_context():
        api_url = app.config['EXTERNAL_API_URL']
        timeout = app.config['API_TIMEOUT']
        result = ETLOrchestrator.run_external_api_etl(api_url, timeout)
        return result
```

### API Endpoints (`app/routes/attractions.py`)

The manual sync endpoint has been updated to use the ETL pipeline:

```python
@attractions_bp.route('/attractions/sync', methods=['POST'])
def sync_attractions():
    """Manual sync using ETL pipeline."""
    api_url = current_app.config['EXTERNAL_API_URL'] 
    timeout = current_app.config['API_TIMEOUT']
    result = ETLOrchestrator.run_external_api_etl(api_url, timeout)
    return jsonify(result)
```

## Benefits

### Separation of Concerns
- Each component has a single responsibility
- Extract, transform, and load logic are independent
- Easy to test individual components

### Extensibility
- New data sources can be added by creating new extractors
- Custom transformation logic for different APIs
- Modular design supports multiple data sources

### Maintainability
- Clear code organization
- Reduced code duplication
- Easier debugging and troubleshooting

### Scalability
- Batch processing support in loaders
- Individual components can be optimized independently
- Easy to add caching, retry logic, or monitoring

## Usage Examples

### Using Individual Components

```python
# Extract data
extractor = ExternalAPIExtractor("https://api.example.com/data")
raw_data = extractor.extract()

# Transform data
transformer = AttractionTransformer()
attractions = transformer.transform_external_api_data(raw_data)

# Load data
loader = AttractionLoader()
result = loader.load_attractions(attractions)
```

### Using ETL Orchestrator

```python
# Complete ETL pipeline
result = ETLOrchestrator.run_external_api_etl(
    "https://api.example.com/data", 
    timeout=30
)
print(f"Saved: {result['saved']}, Skipped: {result['skipped']}")
```

## Testing

Run the ETL tests to verify the structure:

```bash
python test_etl.py      # Test ETL structure and components
python test_routes.py   # Test refactored routes
python test_setup.py    # Test overall application setup
```

## Future Enhancements

1. **Add Real API Integrations**: Implement actual Tourism Thailand and OpenTripMap API calls
2. **Data Validation**: Add schema validation in transformers
3. **Monitoring**: Add logging and metrics for ETL pipeline performance
4. **Configuration**: Make transformations configurable via settings
5. **Error Handling**: Enhanced error recovery and notification mechanisms