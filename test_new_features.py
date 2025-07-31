"""
Tests for new features: geocoding, versioning, dashboard, backup.
"""
import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import date, datetime

# Mock the Flask app and database for testing
@pytest.fixture
def mock_app():
    """Mock Flask app for testing."""
    with patch('app.create_app') as mock_create_app:
        app = Mock()
        app.config = {
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'GOOGLE_GEOCODING_API_KEY': 'test-key',
            'USE_GOOGLE_GEOCODING': True,
            'BACKUP_DIR': '/tmp/test_backups'
        }
        mock_create_app.return_value = app
        yield app


def test_geocoding_service_google():
    """Test Google geocoding service."""
    from app.services.geocoding import GeocodingService
    
    with patch('requests.Session.get') as mock_get:
        # Mock successful Google API response
        mock_response = Mock()
        mock_response.json.return_value = {
            'status': 'OK',
            'results': [{
                'geometry': {
                    'location': {'lat': 13.7563, 'lng': 100.5018}
                },
                'formatted_address': 'Bangkok, Thailand'
            }]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        service = GeocodingService('test-key', use_google=True)
        result = service.geocode('Bangkok', 'Thailand')
        
        assert result is not None
        assert result['latitude'] == 13.7563
        assert result['longitude'] == 100.5018
        assert 'Bangkok' in result['formatted_address']


def test_geocoding_service_osm():
    """Test OpenStreetMap geocoding service."""
    from app.services.geocoding import GeocodingService
    
    with patch('requests.Session.get') as mock_get:
        # Mock successful OSM API response
        mock_response = Mock()
        mock_response.json.return_value = [{
            'lat': '13.7563',
            'lon': '100.5018',
            'display_name': 'Bangkok, Thailand'
        }]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        service = GeocodingService(use_google=False)
        result = service.geocode('Bangkok', 'Thailand')
        
        assert result is not None
        assert result['latitude'] == 13.7563
        assert result['longitude'] == 100.5018
        assert 'Bangkok' in result['formatted_address']


def test_attraction_model_with_geocoding():
    """Test Attraction model with new geocoding fields."""
    from app.models import Attraction
    
    data = {
        'id': 1,
        'title': 'Test Attraction',
        'body': 'Test description',
        'userId': 1,
        'province': 'Bangkok',
        'latitude': 13.7563,
        'longitude': 100.5018,
        'geocoded': True
    }
    
    attraction = Attraction.create_from_external_data(data)
    
    assert attraction.external_id == 1
    assert attraction.title == 'Test Attraction'
    assert attraction.province == 'Bangkok'
    assert attraction.latitude == 13.7563
    assert attraction.longitude == 100.5018
    assert attraction.geocoded == True


def test_attraction_to_dict_with_geocoding():
    """Test Attraction to_dict method with geocoding fields."""
    from app.models import Attraction
    
    attraction = Attraction(
        external_id=1,
        title='Test Attraction',
        body='Test description',
        user_id=1,
        province='Bangkok',
        latitude=13.7563,
        longitude=100.5018,
        geocoded=True
    )
    
    result = attraction.to_dict()
    
    assert result['external_id'] == 1
    assert result['title'] == 'Test Attraction'
    assert result['province'] == 'Bangkok'
    assert result['latitude'] == 13.7563
    assert result['longitude'] == 100.5018
    assert result['geocoded'] == True


def test_sync_statistics_model():
    """Test SyncStatistics model."""
    from app.models import SyncStatistics
    
    stats = SyncStatistics(
        sync_date=date.today(),
        total_processed=100,
        total_saved=80,
        total_skipped=15,
        total_errors=5,
        success_rate=95.0,
        processing_time_seconds=45.2,
        api_source='test-api'
    )
    
    result = stats.to_dict()
    
    assert result['total_processed'] == 100
    assert result['total_saved'] == 80
    assert result['total_skipped'] == 15
    assert result['total_errors'] == 5
    assert result['success_rate'] == 95.0
    assert result['processing_time_seconds'] == 45.2
    assert result['api_source'] == 'test-api'


def test_attraction_history_model():
    """Test AttractionHistory model."""
    from app.models import AttractionHistory
    
    history = AttractionHistory(
        attraction_id=1,
        external_id=1,
        title='Old Title',
        body='Old description',
        user_id=1,
        province='Bangkok',
        latitude=13.7563,
        longitude=100.5018,
        geocoded=True,
        version_number=1
    )
    
    result = history.to_dict()
    
    assert result['attraction_id'] == 1
    assert result['external_id'] == 1
    assert result['title'] == 'Old Title'
    assert result['version_number'] == 1
    assert result['latitude'] == 13.7563
    assert result['longitude'] == 100.5018
    assert result['geocoded'] == True


def test_backup_service_initialization():
    """Test BackupService initialization."""
    from app.services.backup import BackupService
    
    db_url = 'postgresql://user:pass@localhost:5432/testdb'
    backup_dir = '/tmp/test_backups'
    
    service = BackupService(db_url, backup_dir)
    
    assert service.db_host == 'localhost'
    assert service.db_port == 5432
    assert service.db_name == 'testdb'
    assert service.db_user == 'user'
    assert service.db_password == 'pass'


def test_transformer_with_geocoding():
    """Test AttractionTransformer with geocoding enabled."""
    from transformers.attraction_transformer import AttractionTransformer
    
    raw_data = [
        {
            'id': 1,
            'title': 'Test Attraction',
            'body': 'Test description',
            'userId': 1
        }
    ]
    
    with patch('transformers.attraction_transformer.get_geocoding_service') as mock_get_service:
        # Mock geocoding service
        mock_geocoding = Mock()
        mock_geocoding.geocode.return_value = {
            'latitude': 13.7563,
            'longitude': 100.5018,
            'formatted_address': 'Bangkok, Thailand'
        }
        mock_get_service.return_value = mock_geocoding
        
        attractions = AttractionTransformer.transform_external_api_data(
            raw_data, enable_geocoding=True, google_api_key='test-key'
        )
        
        assert len(attractions) == 1
        attraction = attractions[0]
        assert attraction.external_id == 1
        assert attraction.title == 'Test Attraction'
        assert attraction.latitude == 13.7563
        assert attraction.longitude == 100.5018
        assert attraction.geocoded == True
        
        # Verify that geocoding was called
        mock_geocoding.geocode.assert_called_once_with('Test Attraction', None)


def test_province_extraction():
    """Test province extraction from title."""
    from transformers.attraction_transformer import AttractionTransformer
    
    # Test Thai province
    result = AttractionTransformer.extract_province_from_title('วัดในกรุงเทพ')
    assert result == 'กรุงเทพ'
    
    # Test English province
    result = AttractionTransformer.extract_province_from_title('Temple in Bangkok')
    assert result == 'Bangkok'
    
    # Test no province found
    result = AttractionTransformer.extract_province_from_title('Some random title')
    assert result is None


if __name__ == '__main__':
    pytest.main([__file__])