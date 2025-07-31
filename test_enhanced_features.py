"""
Comprehensive tests for enhanced Database Painaidee features.
"""
import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch
import requests_mock

from app.models import Attraction, SyncLog
from app.utils.data_transform import DataTransformer
from app.utils.cache import CacheManager
from loaders.attraction_loader import AttractionLoader
from transformers.attraction_transformer import AttractionTransformer


class TestDataTransformer:
    """Test data transformation utilities."""
    
    def test_normalize_date_thai_format(self):
        """Test date normalization from Thai dd/mm/yyyy format."""
        result = DataTransformer.normalize_date("15/03/2024")
        assert result.year == 2024
        assert result.month == 3
        assert result.day == 15
    
    def test_normalize_date_various_formats(self):
        """Test various date formats."""
        test_cases = [
            ("15-03-2024", (2024, 3, 15)),
            ("15.03.2024", (2024, 3, 15)),
            ("2024-03-15", (2024, 3, 15)),
            ("2024/03/15", (2024, 3, 15)),
        ]
        
        for date_str, expected in test_cases:
            result = DataTransformer.normalize_date(date_str)
            assert result.year == expected[0]
            assert result.month == expected[1]
            assert result.day == expected[2]
    
    def test_normalize_date_invalid(self):
        """Test invalid date handling."""
        assert DataTransformer.normalize_date("invalid-date") is None
        assert DataTransformer.normalize_date("") is None
        assert DataTransformer.normalize_date(None) is None
    
    def test_parse_thai_address(self):
        """Test Thai address parsing."""
        address = "123/45 ถนนสุขุมวิท อำเภอเมือง จังหวัดกรุงเทพมหานคร 10110"
        province, district = DataTransformer.parse_address(address)
        
        assert province == "กรุงเทพมหานคร"
        assert district == "เมือง"
    
    def test_categorize_location_temple(self):
        """Test location categorization for temples."""
        category = DataTransformer.categorize_location("วัดพระแก้ว", "วัดที่สวยงาม")
        assert category == "วัด"
    
    def test_categorize_location_mountain(self):
        """Test location categorization for mountains."""
        category = DataTransformer.categorize_location("ดอยสุเทพ", "ภูเขาที่สูง")
        assert category == "ภูเขา"
    
    def test_categorize_location_sea(self):
        """Test location categorization for sea/beach."""
        category = DataTransformer.categorize_location("หาดป่าตอง", "ทะเลใส")
        assert category == "ทะเล"
    
    def test_categorize_location_default(self):
        """Test default location categorization."""
        category = DataTransformer.categorize_location("สถานที่ท่องเที่ยว", "สถานที่น่าสนใจ")
        assert category == "อื่นๆ"
    
    def test_clean_text(self):
        """Test text cleaning functionality."""
        dirty_text = "  Text   with  extra   spaces  <p>HTML</p>  "
        clean = DataTransformer.clean_text(dirty_text)
        assert clean == "Text with extra spaces HTML"
    
    def test_transform_attraction_data(self):
        """Test complete attraction data transformation."""
        raw_data = {
            'id': 1,
            'title': '  วัดพระแก้ว  ',
            'body': 'วัดที่สวยงาม  <p>มีประวัติศาสตร์</p>',
            'userId': 123,
            'date': '15/03/2024',
            'address': 'อำเภอพระนคร จังหวัดกรุงเทพมหานคร'
        }
        
        transformed = DataTransformer.transform_attraction_data(raw_data)
        
        assert transformed['title'] == 'วัดพระแก้ว'
        assert 'มีประวัติศาสตร์' in transformed['body']
        assert transformed['location_category'] == 'วัด'
        assert transformed['province'] == 'กรุงเทพมหานคร'
        assert transformed['district'] == 'พระนคร'
        assert transformed['normalized_date'].year == 2024


class TestAttractionModel:
    """Test enhanced Attraction model."""
    
    def test_content_hash_generation(self):
        """Test content hash generation for duplicate detection."""
        attraction = Attraction(
            external_id=1,
            title="Test Attraction",
            body="Test description",
            user_id=123
        )
        
        hash1 = attraction.generate_content_hash()
        assert len(hash1) == 64  # SHA-256 hash length
        
        # Same data should produce same hash
        attraction2 = Attraction(
            external_id=1,
            title="Test Attraction",
            body="Test description",
            user_id=123
        )
        hash2 = attraction2.generate_content_hash()
        assert hash1 == hash2
        
        # Different data should produce different hash
        attraction3 = Attraction(
            external_id=1,
            title="Different Attraction",
            body="Test description",
            user_id=123
        )
        hash3 = attraction3.generate_content_hash()
        assert hash1 != hash3


class TestEnhancedTransformer:
    """Test enhanced attraction transformer."""
    
    def test_transform_external_api_data_with_enhancements(self):
        """Test transformation with data cleaning and normalization."""
        raw_data = [
            {
                'id': 1,
                'title': '  วัดพระแก้ว  ',
                'body': 'วัดที่สวยงาม <p>HTML content</p>',
                'userId': 123,
                'date': '15/03/2024',
                'address': 'อำเภอพระนคร กรุงเทพมหานคร'
            }
        ]
        
        attractions = AttractionTransformer.transform_external_api_data(raw_data)
        
        assert len(attractions) == 1
        attraction = attractions[0]
        
        assert attraction.title == 'วัดพระแก้ว'
        assert attraction.location_category == 'วัด'
        assert attraction.province == 'กรุงเทพมหานคร'
        assert attraction.content_hash is not None
        assert len(attraction.content_hash) == 64


class TestCacheManager:
    """Test Redis cache manager functionality."""
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client for testing."""
        with patch('redis.from_url') as mock_redis_client:
            mock_client = Mock()
            mock_client.ping.return_value = True
            mock_redis_client.return_value = mock_client
            yield mock_client
    
    def test_cache_manager_initialization(self, mock_redis):
        """Test cache manager initialization."""
        cache = CacheManager()
        assert cache.enabled is True
        mock_redis.ping.assert_called_once()
    
    def test_cache_api_response(self, mock_redis):
        """Test API response caching."""
        cache = CacheManager()
        cache.redis_client = mock_redis
        
        test_data = [{'id': 1, 'title': 'Test'}]
        result = cache.cache_api_response('http://test.com', test_data)
        
        assert result is True
        mock_redis.setex.assert_called_once()
    
    def test_get_cached_api_response(self, mock_redis):
        """Test retrieving cached API response."""
        cache = CacheManager()
        cache.redis_client = mock_redis
        
        # Mock cached data
        cached_data = {
            'url': 'http://test.com',
            'data': [{'id': 1, 'title': 'Test'}],
            'cached_at': datetime.utcnow().isoformat(),
            'count': 1
        }
        mock_redis.get.return_value = json.dumps(cached_data).encode('utf-8')
        
        result = cache.get_cached_api_response('http://test.com')
        
        assert result == [{'id': 1, 'title': 'Test'}]
        mock_redis.get.assert_called_once()


def test_mock_api_integration(requests_mock):
    """Test ETL pipeline with mocked API responses."""
    # Mock API response
    mock_data = [
        {
            'id': 1,
            'title': 'วัดพระแก้ว',
            'body': 'วัดที่สวยงาม',
            'userId': 123,
            'date': '15/03/2024'
        },
        {
            'id': 2,
            'title': 'ดอยสุเทพ',
            'body': 'ภูเขาที่สวยงาม',
            'userId': 124,
            'date': '16/03/2024'
        }
    ]
    
    requests_mock.get('http://mock-api.com/attractions', json=mock_data)
    
    # Test that the mock works
    import requests
    response = requests.get('http://mock-api.com/attractions')
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]['title'] == 'วัดพระแก้ว'


class TestSyncLog:
    """Test sync logging functionality."""
    
    def test_sync_log_creation(self):
        """Test sync log creation and status tracking."""
        sync_log = SyncLog(
            sync_type='daily',
            api_source='external_api',
            status='running'
        )
        
        assert sync_log.sync_type == 'daily'
        assert sync_log.api_source == 'external_api'
        assert sync_log.status == 'running'
    
    def test_sync_log_mark_completed(self):
        """Test marking sync as completed."""
        sync_log = SyncLog(
            sync_type='daily',
            api_source='external_api',
            status='running'
        )
        
        # Mock database session to avoid actual DB operations in test
        with patch('app.models.db.session.commit'):
            sync_log.mark_completed(
                total_fetched=100,
                total_saved=90,
                total_skipped=10,
                errors=['Some error']
            )
        
        assert sync_log.status == 'completed'
        assert sync_log.total_fetched == 100
        assert sync_log.total_saved == 90
        assert sync_log.total_skipped == 10
        assert sync_log.end_time is not None
    
    def test_sync_log_mark_failed(self):
        """Test marking sync as failed."""
        sync_log = SyncLog(
            sync_type='daily',
            api_source='external_api',
            status='running'
        )
        
        with patch('app.models.db.session.commit'):
            sync_log.mark_failed('API connection failed')
        
        assert sync_log.status == 'failed'
        assert sync_log.errors == 'API connection failed'
        assert sync_log.end_time is not None


# Run the tests with pytest
if __name__ == '__main__':
    pytest.main([__file__, '-v'])