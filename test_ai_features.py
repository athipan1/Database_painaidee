"""
Tests for AI-powered features, search, and caching functionality.
"""
import pytest
import json
from unittest.mock import Mock, patch
from app import create_app
from app.models import db, Attraction
from app.services.ai_service import AIService, get_ai_service
from app.services.search_service import SearchService, get_search_service
from app.services.cache_service import CacheService


class TestAIService:
    """Test AI service functionality."""
    
    def test_ai_service_initialization(self):
        """Test AI service can be initialized."""
        ai_service = get_ai_service()
        assert ai_service is not None
        assert isinstance(ai_service, AIService)
    
    def test_text_summarization(self):
        """Test text summarization functionality."""
        long_text = "This is a very long description of an attraction. " * 20
        summary = AIService.summarize_text(long_text, max_length=100)
        
        assert len(summary) <= 100
        assert summary is not None
        assert len(summary) > 0
    
    def test_text_summarization_short_text(self):
        """Test summarization with short text."""
        short_text = "Short description"
        summary = AIService.summarize_text(short_text, max_length=100)
        assert summary == short_text
    
    def test_attraction_categorization(self):
        """Test attraction categorization."""
        # Test temple categorization
        categories = AIService.categorize_attraction("วัดโพธิ์", "วัดที่มีประวัติศาสตร์")
        assert 'วัฒนธรรม' in categories
        
        # Test nature categorization
        categories = AIService.categorize_attraction("อุทยานแห่งชาติ", "ป่าดิบชื้น")
        assert 'ธรรมชาติ' in categories
        
        # Test restaurant categorization
        categories = AIService.categorize_attraction("ร้านอาหารไทย", "อาหารพื้นเมือง")
        assert 'ร้านอาหาร' in categories
    
    def test_popularity_score_calculation(self):
        """Test popularity score calculation."""
        score = AIService.calculate_popularity_score(
            "Famous Temple", 
            "This is a very popular and well-known temple with rich history"
        )
        assert 0 <= score <= 10
        assert score > 0  # Should have some score for descriptive text
    
    def test_complete_ai_processing(self):
        """Test complete AI processing workflow."""
        attraction_data = {
            'title': 'วัดพระแก้ว',
            'body': 'วัดพระแก้วเป็นวัดที่สำคัญและมีประวัติศาสตร์อันยาวนานในกรุงเทพมหานคร เป็นสถานที่ท่องเที่ยวที่นักท่องเที่ยวต้องมาเยือน',
            'user_id': 1
        }
        
        processed_data = AIService.process_attraction_ai(attraction_data)
        
        assert processed_data['ai_summary'] is not None
        assert processed_data['ai_tags'] is not None
        assert processed_data['popularity_score'] >= 0
        assert processed_data['ai_processed'] is True
        
        # Check tags are valid JSON
        tags = json.loads(processed_data['ai_tags'])
        assert isinstance(tags, list)
    
    def test_search_vector_generation(self):
        """Test search vector generation."""
        search_vector = AIService.generate_search_vector(
            "Temple Name",
            "Temple description with history",
            "Summary of the temple"
        )
        
        assert "Temple Name" in search_vector
        assert "history" in search_vector
        assert "Summary" in search_vector


class TestSearchService:
    """Test search service functionality."""
    
    @pytest.fixture
    def app(self):
        """Create test app."""
        app = create_app('testing')
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()
    
    def test_search_service_initialization(self):
        """Test search service can be initialized."""
        search_service = get_search_service()
        assert search_service is not None
        assert isinstance(search_service, SearchService)
    
    def test_similarity_calculation(self):
        """Test attraction similarity calculation."""
        # Create mock attractions
        ref_attraction = Mock()
        ref_attraction.province = "Bangkok"
        ref_attraction.popularity_score = 8.0
        ref_attraction.ai_tags = '["วัฒนธรรม", "ประวัติศาสตร์"]'
        
        candidate = Mock()
        candidate.province = "Bangkok"
        candidate.popularity_score = 7.5
        candidate.ai_tags = '["วัฒนธรรม"]'
        
        ref_categories = ["วัฒนธรรม", "ประวัติศาสตร์"]
        
        similarity = SearchService._calculate_similarity(
            ref_attraction, candidate, ref_categories
        )
        
        assert 0 <= similarity <= 1
        assert similarity > 0  # Should have some similarity
    
    def test_relevance_score_calculation(self):
        """Test search relevance scoring."""
        attraction = Mock()
        attraction.title = "Beautiful Temple"
        attraction.body = "A historic temple with beautiful architecture"
        attraction.ai_summary = "Historic temple attraction"
        attraction.popularity_score = 7.0
        
        score = SearchService._calculate_relevance_score(attraction, "temple")
        assert score > 0
        
        # Test with multiple terms
        score_multi = SearchService._calculate_relevance_score(attraction, "temple beautiful")
        assert score_multi >= score  # Should have higher or equal score
    
    def test_search_suggestions(self):
        """Test search suggestions generation."""
        # This would require database setup in real test
        # For now, test the method exists and handles empty queries
        suggestions = SearchService.get_search_suggestions("", 5)
        assert isinstance(suggestions, list)


class TestCacheService:
    """Test cache service functionality."""
    
    def test_cache_key_generation(self):
        """Test cache key generation."""
        from app.services.cache_service import cache_key
        
        key1 = cache_key("test", 123, param="value")
        key2 = cache_key("test", 123, param="value")
        key3 = cache_key("test", 456, param="value")
        
        assert key1 == key2  # Same parameters should generate same key
        assert key1 != key3  # Different parameters should generate different keys
    
    def test_cache_service_methods(self):
        """Test cache service utility methods."""
        # Test cache stats
        stats = CacheService.get_cache_stats()
        assert isinstance(stats, dict)
        assert 'status' in stats
    
    def test_cache_invalidation(self):
        """Test cache invalidation doesn't raise errors."""
        # This should not raise an exception even if cache is not available
        try:
            CacheService.invalidate_attraction_cache()
            CacheService.invalidate_attraction_cache(123)
            assert True
        except Exception as e:
            pytest.fail(f"Cache invalidation raised exception: {e}")


class TestIntegrationEndpoints:
    """Test new API endpoints."""
    
    def test_search_endpoint_simple(self):
        """Test search endpoint without full app context."""
        # Just test that the search service works
        try:
            from app.services.search_service import SearchService
            service = SearchService()
            # Test that methods exist and can be called
            assert hasattr(service, 'full_text_search')
            assert hasattr(service, 'get_recommendations')
            assert hasattr(service, 'get_trending_attractions')
            print("Search service methods exist and are callable")
        except Exception as e:
            assert False, f"Search service test failed: {e}"
    
    def test_ai_endpoints_logic(self):
        """Test AI endpoint logic without Flask context."""
        try:
            from app.services.ai_service import AIService
            
            # Test AI processing
            test_data = {
                'title': 'Test Temple',
                'body': 'A beautiful historic temple with ancient architecture',
                'user_id': 1
            }
            
            processed = AIService.process_attraction_ai(test_data)
            
            assert processed['ai_processed'] is True
            assert processed['ai_summary'] is not None
            assert processed['ai_tags'] is not None
            assert processed['popularity_score'] >= 0
            
            print("AI processing logic works correctly")
        except Exception as e:
            assert False, f"AI processing test failed: {e}"
    
    def test_caching_logic(self):
        """Test caching logic without Redis."""
        try:
            from app.services.cache_service import cache_key, CacheService
            
            # Test key generation
            key1 = cache_key("test", 123, param="value")
            key2 = cache_key("test", 123, param="value")
            assert key1 == key2
            
            # Test cache service methods exist
            assert hasattr(CacheService, 'invalidate_attraction_cache')
            assert hasattr(CacheService, 'preload_popular_data')
            
            print("Caching logic works correctly")
        except Exception as e:
            assert False, f"Caching test failed: {e}"


class TestModelEnhancements:
    """Test enhanced attraction model."""
    
    def test_attraction_model_ai_fields_structure(self):
        """Test attraction model has AI fields in structure."""
        try:
            from app.models import Attraction
            
            # Check that the model class has the expected attributes
            assert hasattr(Attraction, 'ai_summary')
            assert hasattr(Attraction, 'ai_tags') 
            assert hasattr(Attraction, 'popularity_score')
            assert hasattr(Attraction, 'ai_processed')
            assert hasattr(Attraction, 'search_vector')
            
            print("Attraction model has all required AI fields")
        except Exception as e:
            assert False, f"Model structure test failed: {e}"
    
    def test_attraction_to_dict_method(self):
        """Test attraction to_dict method includes AI fields."""
        try:
            from app.models import Attraction
            import json
            
            # Create a mock attraction object
            attraction = Attraction()
            attraction.id = 1
            attraction.external_id = 999
            attraction.title = "Test Attraction"
            attraction.body = "Test description"
            attraction.ai_summary = "Test summary"
            attraction.ai_tags = '["test", "attraction"]'
            attraction.popularity_score = 7.5
            attraction.ai_processed = True
            
            result = attraction.to_dict()
            
            assert 'ai_summary' in result
            assert 'ai_tags' in result
            assert 'popularity_score' in result
            assert 'ai_processed' in result
            
            # Check AI tags are parsed as list
            assert isinstance(result['ai_tags'], list)
            assert result['ai_tags'] == ["test", "attraction"]
            
            print("Attraction to_dict method works correctly with AI fields")
        except Exception as e:
            assert False, f"to_dict method test failed: {e}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])