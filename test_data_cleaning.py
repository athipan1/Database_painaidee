"""
Tests for data cleaning services and routes.
"""
import pytest
import json
from app import create_app
from app.models import db, Attraction
from app.services.auto_tagging import AutoTagger
from app.services.category_suggestion import CategorySuggester
from app.services.data_validation import DataValidator


class TestAutoTagger:
    """Test cases for AutoTagger service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.auto_tagger = AutoTagger()
    
    def test_generate_tags_for_temple(self):
        """Test tag generation for temple attractions."""
        title = "Wat Phra Kaew Temple"
        body = "Ancient Buddhist temple with golden Buddha statue, sacred shrine for meditation and prayer"
        
        tags = self.auto_tagger.generate_tags(title, body)
        
        # Check that temple-related tags are generated
        temple_tags = {'temple', 'buddhist', 'buddha', 'sacred', 'prayer', 'meditation', 'ancient'}
        assert any(tag in temple_tags for tag in tags), f"Expected temple-related tags in {tags}"
        assert len(tags) > 0, "Should generate at least one tag"
    
    def test_generate_tags_for_waterfall(self):
        """Test tag generation for waterfall attractions."""
        title = "Erawan Falls"
        body = "Beautiful natural waterfall in tropical forest, great for swimming and hiking"
        
        tags = self.auto_tagger.generate_tags(title, body)
        
        # Check that waterfall-related tags are generated
        waterfall_tags = {'waterfall', 'falls', 'natural', 'forest', 'swimming', 'hiking', 'beautiful'}
        assert any(tag in waterfall_tags for tag in tags), f"Expected waterfall-related tags in {tags}"
        assert len(tags) > 0, "Should generate at least one tag"
    
    def test_generate_tags_empty_input(self):
        """Test tag generation with empty input."""
        tags = self.auto_tagger.generate_tags("", "")
        assert tags == [], "Empty input should return empty list"
    
    def test_generate_tags_title_only(self):
        """Test tag generation with title only."""
        title = "Beautiful Mountain Peak"
        tags = self.auto_tagger.generate_tags(title)
        
        mountain_tags = {'mountain', 'peak', 'beautiful'}
        assert any(tag in mountain_tags for tag in tags), f"Expected mountain-related tags in {tags}"
    
    def test_detect_attraction_type(self):
        """Test attraction type detection."""
        # Test temple detection
        temple_text = "ancient buddhist temple with monks"
        temple_type = self.auto_tagger._detect_attraction_type(temple_text)
        assert temple_type == 'temple'
        
        # Test waterfall detection
        waterfall_text = "beautiful waterfall cascade in forest"
        waterfall_type = self.auto_tagger._detect_attraction_type(waterfall_text)
        assert waterfall_type == 'waterfall'
    
    def test_get_suggested_tags_for_type(self):
        """Test getting suggested tags for specific attraction type."""
        temple_suggestions = self.auto_tagger.get_suggested_tags_for_type('temple')
        assert len(temple_suggestions) <= 10
        assert 'temple' in temple_suggestions
        
        waterfall_suggestions = self.auto_tagger.get_suggested_tags_for_type('waterfall')
        assert len(waterfall_suggestions) <= 10
        assert 'waterfall' in waterfall_suggestions


class TestCategorySuggester:
    """Test cases for CategorySuggester service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.category_suggester = CategorySuggester()
    
    def test_suggest_categories_for_temple(self):
        """Test category suggestion for temple attractions."""
        title = "Wat Phra Kaew Temple"
        body = "Ancient Buddhist temple with golden Buddha statue"
        
        categories = self.category_suggester.suggest_categories(title, body)
        
        # Check that religious category is suggested
        category_names = [cat['category'] for cat in categories]
        assert any('Religious' in name or 'Spiritual' in name for name in category_names), \
            f"Expected religious category in {category_names}"
        assert len(categories) > 0, "Should suggest at least one category"
        
        # Check confidence scores
        for category in categories:
            assert 0 <= category['confidence'] <= 1, "Confidence should be between 0 and 1"
    
    def test_suggest_categories_for_waterfall(self):
        """Test category suggestion for waterfall attractions."""
        title = "Erawan Falls"
        body = "Beautiful natural waterfall in tropical forest"
        
        categories = self.category_suggester.suggest_categories(title, body)
        
        # Check that natural attractions category is suggested
        category_names = [cat['category'] for cat in categories]
        assert any('Natural' in name for name in category_names), \
            f"Expected natural category in {category_names}"
        assert len(categories) > 0, "Should suggest at least one category"
    
    def test_suggest_categories_empty_input(self):
        """Test category suggestion with empty input."""
        categories = self.category_suggester.suggest_categories("", "")
        assert categories == [], "Empty input should return empty list"
    
    def test_get_category_for_attraction_type(self):
        """Test getting category for known attraction type."""
        temple_category = self.category_suggester.get_category_for_attraction_type('temple')
        assert temple_category == 'Religious & Spiritual'
        
        waterfall_category = self.category_suggester.get_category_for_attraction_type('waterfall')
        assert waterfall_category == 'Natural Attractions'
    
    def test_get_all_categories(self):
        """Test getting all available categories."""
        categories = self.category_suggester.get_all_categories()
        assert len(categories) > 0, "Should return at least one category"
        assert 'Religious & Spiritual' in categories
        assert 'Natural Attractions' in categories
    
    def test_validate_category_assignment(self):
        """Test category assignment validation."""
        text = "ancient buddhist temple with monks"
        
        # Test valid assignment
        valid_result = self.category_suggester.validate_category_assignment(
            text, 'Religious & Spiritual'
        )
        assert valid_result['valid'] is True
        assert valid_result['confidence'] > 0
        
        # Test invalid assignment
        invalid_result = self.category_suggester.validate_category_assignment(
            text, 'Beach & Coastal'
        )
        assert invalid_result['confidence'] < 0.5  # Should have low confidence


class TestDataValidator:
    """Test cases for DataValidator service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.data_validator = DataValidator()
    
    def test_validate_attraction_data_valid(self):
        """Test validation of valid attraction data."""
        data = {
            'title': 'Wat Phra Kaew',
            'external_id': 123,
            'body': 'Beautiful ancient temple in Bangkok',
            'province': 'Bangkok',
            'latitude': 13.7563,
            'longitude': 100.5018
        }
        
        result = self.data_validator.validate_attraction_data(data)
        assert result['valid'] is True
        assert len(result['errors']) == 0
        assert result['quality_score'] > 0.5
    
    def test_validate_attraction_data_missing_required(self):
        """Test validation with missing required fields."""
        data = {
            'body': 'Some description'
        }
        
        result = self.data_validator.validate_attraction_data(data)
        assert result['valid'] is False
        assert any('title' in error for error in result['errors'])
        assert any('external_id' in error for error in result['errors'])
    
    def test_validate_title(self):
        """Test title validation."""
        # Valid title
        valid_result = self.data_validator._validate_title('Beautiful Temple')
        assert len(valid_result['errors']) == 0
        assert valid_result['cleaned'] == 'Beautiful Temple'
        
        # Empty title
        empty_result = self.data_validator._validate_title('')
        assert len(empty_result['errors']) > 0
        
        # Too short title
        short_result = self.data_validator._validate_title('AB')
        assert len(short_result['errors']) > 0
    
    def test_validate_coordinates(self):
        """Test coordinate validation."""
        # Valid coordinates (Bangkok)
        valid_result = self.data_validator._validate_coordinates(13.7563, 100.5018)
        assert len(valid_result['errors']) == 0
        
        # Invalid latitude
        invalid_lat_result = self.data_validator._validate_coordinates(95, 100)
        assert len(invalid_lat_result['errors']) > 0
        
        # Invalid longitude
        invalid_lng_result = self.data_validator._validate_coordinates(13, 185)
        assert len(invalid_lng_result['errors']) > 0
    
    def test_validate_province(self):
        """Test province validation."""
        # Valid province
        valid_result = self.data_validator._validate_province('Bangkok')
        assert len(valid_result['warnings']) == 0
        assert valid_result['cleaned'] == 'Bangkok'
        
        # Invalid province
        invalid_result = self.data_validator._validate_province('Invalid Province')
        assert len(invalid_result['warnings']) > 0
    
    def test_validate_batch(self):
        """Test batch validation."""
        attractions = [
            {
                'title': 'Valid Temple',
                'external_id': 1,
                'body': 'Good description'
            },
            {
                'title': 'Invalid Attraction'
                # Missing external_id
            }
        ]
        
        result = self.data_validator.validate_batch(attractions)
        assert result['summary']['total'] == 2
        assert result['summary']['valid'] == 1
        assert result['summary']['invalid'] == 1
        assert len(result['results']) == 2


# Integration tests would go here if we had a test app setup
# For now, focusing on unit tests for the services