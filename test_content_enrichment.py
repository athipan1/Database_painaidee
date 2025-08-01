"""
Tests for AI Content Enrichment features.
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from flask import Flask
from app import create_app
from app.models import db, Attraction
from app.services.content_enrichment import (
    ContentEnrichmentService,
    generate_place_description,
    translate_content,
    extract_key_features,
    generate_attraction_images,
    enrich_attraction_content
)


@pytest.fixture
def app():
    """Create and configure test Flask application."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def sample_attraction(app):
    """Create sample attraction for testing."""
    with app.app_context():
        attraction = Attraction(
            external_id=999,
            title="Wat Phra Kaew",
            body="Beautiful temple in Bangkok with traditional Thai architecture",
            province="Bangkok"
        )
        db.session.add(attraction)
        db.session.commit()
        return attraction


class TestContentEnrichmentService:
    """Test the Content Enrichment Service."""
    
    def test_service_initialization(self):
        """Test service initialization."""
        service = ContentEnrichmentService()
        assert service is not None
        assert hasattr(service, 'supported_languages')
        assert 'en' in service.supported_languages
        assert 'th' in service.supported_languages
        assert 'zh' in service.supported_languages
    
    def test_generate_place_description_fallback(self):
        """Test place description generation with fallback method."""
        service = ContentEnrichmentService()
        service.openai_enabled = False  # Force fallback
        
        attraction_data = {
            'title': 'Test Temple',
            'body': 'A beautiful ancient temple',
            'province': 'Bangkok'
        }
        
        result = service.generate_place_description(attraction_data)
        
        assert result['success'] is True
        assert 'description' in result
        assert result['method'] == 'fallback'
        assert 'Test Temple' in result['description']
        assert 'Bangkok' in result['description']
    
    def test_extract_key_features(self):
        """Test key features extraction."""
        service = ContentEnrichmentService()
        
        text = "This is a family-friendly beachfront resort with great view and traditional architecture"
        result = service.extract_key_features(text)
        
        assert result['success'] is True
        assert 'features' in result
        assert 'categories' in result
        
        features = result['features']
        assert 'family-friendly' in features
        assert 'beachfront' in features
        assert 'great view' in features
        assert 'traditional' in features
        
        categories = result['categories']
        assert len(categories) > 0
        if 'family' in categories:
            assert 'family-friendly' in categories['family']
    
    def test_multilingual_content_fallback(self):
        """Test multilingual content generation with fallback."""
        service = ContentEnrichmentService()
        service.translator_available = False  # Force fallback
        
        text = "Beautiful temple in Bangkok"
        result = service.generate_multilingual_content(text)
        
        assert result['success'] is True
        assert 'translations' in result
        assert result['method'] == 'fallback'
        
        translations = result['translations']
        assert 'original' in translations
        assert 'en' in translations
        assert 'th' in translations
        assert 'zh' in translations
    
    def test_generate_images_fallback(self):
        """Test image generation with fallback method."""
        service = ContentEnrichmentService()
        service.openai_enabled = False  # Force fallback
        
        attraction_data = {
            'title': 'Wat Phra Kaew',
            'body': 'Temple in Bangkok',
            'province': 'Bangkok'
        }
        
        result = service.generate_images(attraction_data, num_images=2)
        
        assert result['success'] is True
        assert 'image_urls' in result
        assert result['method'] == 'placeholder'
        assert len(result['image_urls']) == 2
        
        # Check URLs are valid Unsplash format
        for url in result['image_urls']:
            assert 'unsplash.com' in url
    
    def test_complete_enrichment(self):
        """Test complete attraction enrichment."""
        service = ContentEnrichmentService()
        
        attraction_data = {
            'id': 1,
            'title': 'Test Beach Resort',
            'body': 'Family-friendly beachfront location with great view',
            'province': 'Phuket'
        }
        
        result = service.enrich_attraction(attraction_data)
        
        assert result['success'] is True
        assert 'features' in result
        assert 'description' in result['features']
        assert 'key_features' in result['features']
        assert 'multilingual' in result['features']
        assert 'images' in result['features']
        
        # Check each feature was processed
        assert result['features']['description']['success'] is True
        assert result['features']['key_features']['success'] is True
        assert result['features']['multilingual']['success'] is True
        assert result['features']['images']['success'] is True


class TestContentEnrichmentRoutes:
    """Test the Content Enrichment API routes."""
    
    def test_generate_description_endpoint(self, client, sample_attraction):
        """Test the description generation endpoint."""
        response = client.post('/api/ai/enrich/description', json={
            'attraction_id': sample_attraction.id
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'description' in data
        assert data['attraction_id'] == sample_attraction.id
        assert data['changes_applied'] is False
    
    def test_generate_description_with_apply_changes(self, client, sample_attraction):
        """Test description generation with database update."""
        original_body = sample_attraction.body
        
        response = client.post('/api/ai/enrich/description', json={
            'attraction_id': sample_attraction.id,
            'apply_changes': True
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['changes_applied'] is True
        
        # Check database was updated
        with client.application.app_context():
            updated_attraction = Attraction.query.get(sample_attraction.id)
            assert updated_attraction.body != original_body
            assert updated_attraction.content_enriched is True
    
    def test_generate_description_with_data(self, client):
        """Test description generation with provided data."""
        response = client.post('/api/ai/enrich/description', json={
            'title': 'Test Temple',
            'body': 'Ancient temple',
            'province': 'Bangkok'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'description' in data
    
    def test_multilingual_endpoint(self, client, sample_attraction):
        """Test the multilingual translation endpoint."""
        response = client.post('/api/ai/enrich/multilingual', json={
            'attraction_id': sample_attraction.id,
            'field': 'title',
            'languages': ['en', 'th', 'zh']
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'translations' in data
        assert data['field'] == 'title'
        
        translations = data['translations']
        assert 'original' in translations
        assert 'en' in translations
        assert 'th' in translations
        assert 'zh' in translations
    
    def test_multilingual_with_text(self, client):
        """Test multilingual endpoint with text input."""
        response = client.post('/api/ai/enrich/multilingual', json={
            'text': 'Beautiful temple in Bangkok',
            'languages': ['en', 'th']
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'translations' in data
    
    def test_features_extraction_endpoint(self, client, sample_attraction):
        """Test the key features extraction endpoint."""
        response = client.post('/api/ai/enrich/features', json={
            'attraction_id': sample_attraction.id
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'features' in data
        assert 'categories' in data
        assert isinstance(data['features'], list)
        assert isinstance(data['categories'], dict)
    
    def test_features_with_text(self, client):
        """Test features extraction with text input."""
        response = client.post('/api/ai/enrich/features', json={
            'text': 'Family-friendly beachfront resort with great view and traditional architecture'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'features' in data
        
        features = data['features']
        assert 'family-friendly' in features
        assert 'beachfront' in features
    
    def test_image_generation_endpoint(self, client, sample_attraction):
        """Test the image generation endpoint."""
        response = client.post('/api/ai/enrich/images', json={
            'attraction_id': sample_attraction.id,
            'num_images': 2
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'image_urls' in data
        assert len(data['image_urls']) == 2
    
    def test_image_generation_with_data(self, client):
        """Test image generation with provided data."""
        response = client.post('/api/ai/enrich/images', json={
            'title': 'Wat Phra Kaew',
            'body': 'Temple in Bangkok',
            'province': 'Bangkok',
            'num_images': 1
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'image_urls' in data
        assert len(data['image_urls']) == 1
    
    def test_complete_enrichment_endpoint(self, client, sample_attraction):
        """Test the complete enrichment endpoint."""
        response = client.post('/api/ai/enrich/complete', json={
            'attraction_id': sample_attraction.id
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'features' in data
        
        features = data['features']
        assert 'description' in features
        assert 'multilingual' in features
        assert 'key_features' in features
        assert 'images' in features
    
    def test_complete_enrichment_with_apply_changes(self, client, sample_attraction):
        """Test complete enrichment with database updates."""
        response = client.post('/api/ai/enrich/complete', json={
            'attraction_id': sample_attraction.id,
            'apply_changes': True
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['changes_applied'] is True
        
        # Check database was updated
        with client.application.app_context():
            updated_attraction = Attraction.query.get(sample_attraction.id)
            assert updated_attraction.content_enriched is True
    
    def test_enrichment_stats_endpoint(self, client, sample_attraction):
        """Test the enrichment statistics endpoint."""
        # First enrich the attraction
        client.post('/api/ai/enrich/complete', json={
            'attraction_id': sample_attraction.id,
            'apply_changes': True
        })
        
        # Then check stats
        response = client.get('/api/ai/enrich/stats')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'total_attractions' in data
        assert 'enriched_attractions' in data
        assert 'enrichment_coverage' in data
        assert 'features' in data
        
        features = data['features']
        assert 'multilingual_content' in features
        assert 'key_features' in features
        assert 'generated_images' in features
    
    def test_error_handling_invalid_attraction(self, client):
        """Test error handling for invalid attraction ID."""
        response = client.post('/api/ai/enrich/description', json={
            'attraction_id': 99999  # Non-existent ID
        })
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
        assert 'not found' in data['error'].lower()
    
    def test_error_handling_missing_data(self, client):
        """Test error handling for missing required data."""
        response = client.post('/api/ai/enrich/description', json={})
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_error_handling_invalid_field(self, client, sample_attraction):
        """Test error handling for invalid field in multilingual endpoint."""
        response = client.post('/api/ai/enrich/multilingual', json={
            'attraction_id': sample_attraction.id,
            'field': 'invalid_field'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'Invalid field' in data['error']


class TestConvenienceFunctions:
    """Test the convenience functions."""
    
    def test_generate_place_description_function(self):
        """Test the convenience function for place description."""
        attraction_data = {
            'title': 'Test Location',
            'body': 'Test description',
            'province': 'Test Province'
        }
        
        result = generate_place_description(attraction_data)
        
        assert result['success'] is True
        assert 'description' in result
    
    def test_translate_content_function(self):
        """Test the convenience function for translation."""
        result = translate_content('Test text', ['en', 'th'])
        
        assert result['success'] is True
        assert 'translations' in result
    
    def test_extract_key_features_function(self):
        """Test the convenience function for key features."""
        result = extract_key_features('Family-friendly beachfront resort')
        
        assert result['success'] is True
        assert 'features' in result
        assert 'family-friendly' in result['features']
        assert 'beachfront' in result['features']
    
    def test_generate_attraction_images_function(self):
        """Test the convenience function for image generation."""
        attraction_data = {
            'title': 'Test Location',
            'body': 'Test description',
            'province': 'Test Province'
        }
        
        result = generate_attraction_images(attraction_data, 1)
        
        assert result['success'] is True
        assert 'image_urls' in result
        assert len(result['image_urls']) == 1
    
    def test_enrich_attraction_content_function(self):
        """Test the convenience function for complete enrichment."""
        attraction_data = {
            'id': 1,
            'title': 'Test Location',
            'body': 'Family-friendly place with great view',
            'province': 'Test Province'
        }
        
        result = enrich_attraction_content(attraction_data)
        
        assert result['success'] is True
        assert 'features' in result
        assert len(result['features']) > 0


@pytest.mark.integration
class TestIntegrationWithExistingFeatures:
    """Test integration with existing AI features."""
    
    def test_enrichment_with_existing_keywords(self, client, sample_attraction):
        """Test that enrichment works with existing keyword extraction."""
        # First extract keywords (existing feature)
        response = client.post('/api/ai/keywords/extract', json={
            'attraction_id': sample_attraction.id
        })
        assert response.status_code == 200
        
        # Then do enrichment
        response = client.post('/api/ai/enrich/complete', json={
            'attraction_id': sample_attraction.id,
            'apply_changes': True
        })
        assert response.status_code == 200
        
        # Check that both features worked together
        with client.application.app_context():
            updated_attraction = Attraction.query.get(sample_attraction.id)
            assert updated_attraction.keywords is not None
            assert updated_attraction.content_enriched is True
    
    def test_ai_stats_include_enrichment(self, client, sample_attraction):
        """Test that AI stats include enrichment data."""
        # Enrich an attraction
        client.post('/api/ai/enrich/complete', json={
            'attraction_id': sample_attraction.id,
            'apply_changes': True
        })
        
        # Check overall AI stats
        response = client.get('/api/ai/stats')
        assert response.status_code == 200
        
        # Check enrichment-specific stats
        response = client.get('/api/ai/enrich/stats')
        assert response.status_code == 200
        data = response.get_json()
        assert data['enriched_attractions'] > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])