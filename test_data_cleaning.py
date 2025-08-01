"""
Tests for AI Data Cleaning & Enrichment features.
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from app import create_app
from app.models import (
    db, Attraction, DataValidationResult, AttractionTag, 
    AttractionCategory
)
from app.services.data_validation import (
    DataValidator,
    validate_attraction_data,
    validate_batch_attractions
)
from app.services.auto_tagging import (
    AutoTagger,
    tag_attraction,
    tag_batch_attractions
)
from app.services.category_suggestion import (
    CategorySuggester,
    suggest_categories_for_attraction,
    suggest_categories_batch
)


@pytest.fixture
def app():
    """Create test Flask application."""
    app = create_app('testing')
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def app_context(app):
    """Create Flask application context."""
    with app.app_context():
        yield app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def sample_attractions(app_context):
    """Create sample attractions for testing."""
    attractions = [
        Attraction(
            external_id=1,
            title="วัดพระแก้ว กรุงเทพมหานคร",
            body="วัดสวยงามในกรุงเทพ มีพระพุทธรูปสีเขียว เป็นสถานที่ศักดิ์สิทธิ์",
            province="กรุงเทพมหานคร"
        ),
        Attraction(
            external_id=2,
            title="น้ำตกเอราวัณ กาญจนบุรี",
            body="น้ำตกที่สวยงาม มี 7 ชั้น เหมาะสำหรับเล่นน้ำและถ่ายรูป",
            province="กาญจนบุรี"
        ),
        Attraction(
            external_id=3,
            title="ตลาดน้ำดำเนินสะดวก",
            body="ตลาดน้ำโบราณ สามารถซื้อของฝากและอาหารท้องถิ่น",
            province="ราชบุรี"
        ),
        Attraction(
            external_id=4,
            title="Test attraction",
            body="This is a test   with multiple spaces and formatting issues.",
            province="Test Province"
        )
    ]
    
    for attraction in attractions:
        db.session.add(attraction)
    
    db.session.commit()
    return attractions


# Data Validation Tests

class TestDataValidator:
    """Test cases for DataValidator class."""
    
    def test_validator_initialization(self):
        """Test validator initializes correctly."""
        validator = DataValidator()
        assert validator.thai_provinces
        assert validator.grammar_patterns
        assert validator.common_typos
    
    def test_validate_empty_text(self):
        """Test validation of empty text."""
        validator = DataValidator()
        result = validator.validate_text("", "title")
        
        assert len(result['issues']) == 1
        assert result['issues'][0]['type'] == 'empty_content'
        assert result['issues'][0]['severity'] == 'high'
    
    def test_validate_text_with_issues(self):
        """Test validation of text with multiple issues."""
        validator = DataValidator()
        text = "test  multiple   spaces and invalid@#$characters"
        result = validator.validate_text(text, "title")
        
        # Should detect multiple spaces and potentially other issues
        issue_types = [issue['type'] for issue in result['issues']]
        assert 'formatting' in issue_types or 'multiple_spaces' in issue_types
    
    def test_fix_text_issues(self):
        """Test automatic text fixing."""
        validator = DataValidator()
        text = "test  multiple   spaces"
        fixed_text = validator.fix_text_issues(text, ['formatting'])
        
        assert "  " not in fixed_text  # Multiple spaces should be fixed
        assert fixed_text.strip() == fixed_text  # Leading/trailing whitespace removed


def test_validate_attraction_data(app_context, sample_attractions):
    """Test attraction data validation."""
    attraction = sample_attractions[0]  # วัดพระแก้ว
    
    result = validate_attraction_data(attraction.id)
    
    assert 'error' not in result
    assert 'attraction_id' in result
    assert 'overall_score' in result
    assert isinstance(result['issues'], list)
    assert isinstance(result['suggestions'], list)


def test_validate_batch_attractions(app_context, sample_attractions):
    """Test batch attraction validation."""
    attraction_ids = [a.id for a in sample_attractions[:2]]
    
    result = validate_batch_attractions(attraction_ids)
    
    assert result['processed'] == 2
    assert result['successful'] >= 0
    assert result['failed'] >= 0
    assert len(result['results']) == 2


# Auto-Tagging Tests

class TestAutoTagger:
    """Test cases for AutoTagger class."""
    
    def test_tagger_initialization(self):
        """Test tagger initializes correctly."""
        tagger = AutoTagger()
        assert tagger.attraction_patterns
        assert tagger.activity_patterns
        assert tagger.feature_patterns
        assert tagger.all_patterns
    
    def test_generate_tags_for_temple(self, app_context, sample_attractions):
        """Test tag generation for temple attraction."""
        temple_attraction = sample_attractions[0]  # วัดพระแก้ว
        
        tagger = AutoTagger()
        tags = tagger.generate_tags(temple_attraction)
        
        # Should generate temple-related tags
        tag_names = [tag['tag_name'] for tag in tags]
        assert any('temple' in tag_name.lower() or 'religious' in tag_name.lower() 
                  for tag_name in tag_names)
    
    def test_generate_tags_for_waterfall(self, app_context, sample_attractions):
        """Test tag generation for waterfall attraction."""
        waterfall_attraction = sample_attractions[1]  # น้ำตกเอราวัณ
        
        tagger = AutoTagger()
        tags = tagger.generate_tags(waterfall_attraction)
        
        # Should generate waterfall/nature-related tags
        tag_names = [tag['tag_name'] for tag in tags]
        assert any('waterfall' in tag_name.lower() or 'nature' in tag_name.lower() 
                  for tag_name in tag_names)
    
    def test_get_tag_suggestions_for_text(self):
        """Test tag suggestions for arbitrary text."""
        tagger = AutoTagger()
        suggestions = tagger.get_tag_suggestions("วัดสวยงาม ถ่ายรูป")
        
        # Should suggest temple and photography tags
        tag_names = [tag['tag_name'] for tag in suggestions]
        assert len(suggestions) > 0
        # At least one suggestion should be related to temple or photography
        assert any('temple' in tag_name or 'photography' in tag_name 
                  for tag_name in tag_names)


def test_tag_attraction(app_context, sample_attractions):
    """Test single attraction tagging."""
    attraction = sample_attractions[0]  # วัดพระแก้ว
    
    result = tag_attraction(attraction.id)
    
    assert 'error' not in result
    assert result['attraction_id'] == attraction.id
    assert result['tags_generated'] >= 0
    assert 'tags' in result


def test_tag_batch_attractions(app_context, sample_attractions):
    """Test batch attraction tagging."""
    attraction_ids = [a.id for a in sample_attractions[:2]]
    
    result = tag_batch_attractions(attraction_ids)
    
    assert result['processed'] == 2
    assert result['successful'] >= 0
    assert result['total_tags_generated'] >= 0


# Category Suggestion Tests

class TestCategorySuggester:
    """Test cases for CategorySuggester class."""
    
    def test_suggester_initialization(self):
        """Test suggester initializes correctly."""
        suggester = CategorySuggester()
        assert suggester.category_hierarchy
        assert suggester.specialized_patterns
        assert suggester.activity_categories
    
    def test_suggest_categories_for_temple(self, app_context, sample_attractions):
        """Test category suggestions for temple attraction."""
        temple_attraction = sample_attractions[0]  # วัดพระแก้ว
        
        suggester = CategorySuggester()
        categories = suggester.suggest_categories(temple_attraction)
        
        # Should suggest religious categories
        category_names = [cat['category_name'] for cat in categories]
        assert any('religious' in cat_name or 'temple' in cat_name 
                  for cat_name in category_names)
    
    def test_suggest_categories_for_waterfall(self, app_context, sample_attractions):
        """Test category suggestions for waterfall attraction."""
        waterfall_attraction = sample_attractions[1]  # น้ำตกเอราวัณ
        
        suggester = CategorySuggester()
        categories = suggester.suggest_categories(waterfall_attraction)
        
        # Should suggest nature categories
        category_names = [cat['category_name'] for cat in categories]
        assert any('nature' in cat_name or 'waterfall' in cat_name 
                  for cat_name in category_names)
    
    def test_get_category_suggestions_for_text(self):
        """Test category suggestions for arbitrary text."""
        suggester = CategorySuggester()
        suggestions = suggester.get_category_suggestions_for_text("ตลาดน้ำ ซื้อของ")
        
        # Should suggest shopping/market categories
        category_names = [cat['category_name'] for cat in suggestions]
        assert len(suggestions) > 0
        assert any('shopping' in cat_name or 'market' in cat_name 
                  for cat_name in category_names)


def test_suggest_categories_for_attraction(app_context, sample_attractions):
    """Test single attraction categorization."""
    attraction = sample_attractions[2]  # ตลาดน้ำ
    
    result = suggest_categories_for_attraction(attraction.id)
    
    assert 'error' not in result
    assert result['attraction_id'] == attraction.id
    assert result['categories_suggested'] >= 0
    assert 'categories' in result


def test_suggest_categories_batch(app_context, sample_attractions):
    """Test batch attraction categorization."""
    attraction_ids = [a.id for a in sample_attractions[:2]]
    
    result = suggest_categories_batch(attraction_ids)
    
    assert result['processed'] == 2
    assert result['successful'] >= 0
    assert result['total_categories_suggested'] >= 0


# API Endpoint Tests

def test_data_validation_endpoint(client, app_context, sample_attractions):
    """Test data validation API endpoint."""
    attraction = sample_attractions[0]
    
    response = client.post('/api/ai/data-cleaning/validate', 
                          json={'attraction_id': attraction.id})
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'result' in data


def test_batch_validation_endpoint(client, app_context, sample_attractions):
    """Test batch validation API endpoint."""
    attraction_ids = [a.id for a in sample_attractions[:2]]
    
    response = client.post('/api/ai/data-cleaning/validate',
                          json={'attraction_ids': attraction_ids})
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'result' in data


def test_auto_tagging_endpoint(client, app_context, sample_attractions):
    """Test auto-tagging API endpoint."""
    attraction = sample_attractions[0]
    
    response = client.post('/api/ai/auto-tagging/generate',
                          json={'attraction_id': attraction.id})
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'result' in data


def test_category_suggestion_endpoint(client, app_context, sample_attractions):
    """Test category suggestion API endpoint."""
    attraction = sample_attractions[0]
    
    response = client.post('/api/ai/category-suggestion/generate',
                          json={'attraction_id': attraction.id})
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'result' in data


def test_full_data_cleaning_endpoint(client, app_context, sample_attractions):
    """Test comprehensive data cleaning API endpoint."""
    attraction_ids = [a.id for a in sample_attractions[:2]]
    
    response = client.post('/api/ai/data-cleaning/full-clean',
                          json={
                              'attraction_ids': attraction_ids,
                              'config': {
                                  'enable_validation': True,
                                  'enable_tagging': True,
                                  'enable_categorization': True,
                                  'enable_geocoding': False  # Skip geocoding in tests
                              }
                          })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'results' in data


def test_data_cleaning_overview_endpoint(client, app_context, sample_attractions):
    """Test data cleaning overview API endpoint."""
    response = client.get('/api/ai/data-cleaning/overview')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'overview' in data
    assert 'total_attractions' in data['overview']


def test_attraction_cleaning_status_endpoint(client, app_context, sample_attractions):
    """Test attraction cleaning status API endpoint."""
    attraction = sample_attractions[0]
    
    response = client.get(f'/api/ai/data-cleaning/status/{attraction.id}')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['attraction_id'] == attraction.id
    assert 'status' in data
    assert 'details' in data


def test_tag_suggestions_for_text_endpoint(client, app_context):
    """Test tag suggestions for text API endpoint."""
    response = client.post('/api/ai/auto-tagging/suggest',
                          json={'text': 'วัดสวยงาม ถ่ายรูป'})
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'result' in data


def test_category_suggestions_for_text_endpoint(client, app_context):
    """Test category suggestions for text API endpoint."""
    response = client.post('/api/ai/category-suggestion/suggest',
                          json={'text': 'ตลาดน้ำ ซื้อของ'})
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'result' in data


# Error Handling Tests

def test_validation_with_invalid_attraction_id(client, app_context):
    """Test validation with non-existent attraction ID."""
    response = client.post('/api/ai/data-cleaning/validate',
                          json={'attraction_id': 99999})
    
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data


def test_tagging_with_empty_request(client, app_context):
    """Test tagging with empty request."""
    response = client.post('/api/ai/auto-tagging/generate', json={})
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data


def test_categorization_with_invalid_batch_size(client, app_context):
    """Test categorization with too large batch size."""
    # Create list of 100+ IDs
    large_list = list(range(1, 102))
    
    response = client.post('/api/ai/category-suggestion/generate',
                          json={'attraction_ids': large_list})
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'Maximum' in data['error']


def test_text_suggestion_with_empty_text(client, app_context):
    """Test text suggestions with empty text."""
    response = client.post('/api/ai/auto-tagging/suggest',
                          json={'text': ''})
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])