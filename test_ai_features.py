"""
Tests for AI-powered features.
"""
import pytest
from unittest.mock import Mock, patch
from app import create_app
from app.models import db, Attraction, UserInteraction
from app.services.keyword_extraction import (
    KeywordExtractor, 
    FallbackKeywordExtractor,
    extract_keywords_from_attraction
)
from app.services.recommendation import RecommendationEngine, get_user_recommendations
from app.services.trend_analysis import TrendAnalyzer, analyze_attraction_trends
from app.services.content_rewriter import ContentRewriter, improve_attraction_content


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
            title="Beautiful Temple in Bangkok",
            body="A stunning ancient temple with golden decorations and peaceful gardens.",
            user_id=1,
            province="Bangkok",
            view_count=100
        ),
        Attraction(
            external_id=2,
            title="Mountain Park with River",
            body="Amazing mountain park featuring crystal clear river and hiking trails.",
            user_id=1,
            province="Chiang Mai",
            view_count=50
        ),
        Attraction(
            external_id=3,
            title="Local Market Street Food",
            body="Traditional market with delicious local cuisine and authentic Thai dishes.",
            user_id=1,
            province="Bangkok",
            view_count=75
        )
    ]
    
    for attraction in attractions:
        db.session.add(attraction)
    
    db.session.commit()
    return attractions


class TestKeywordExtraction:
    """Test keyword extraction functionality."""
    
    def test_fallback_keyword_extractor(self):
        """Test fallback keyword extractor."""
        extractor = FallbackKeywordExtractor()
        
        text = "Beautiful temple with ancient architecture and peaceful gardens"
        keywords = extractor.extract_keywords(text, max_keywords=5)
        
        assert isinstance(keywords, list)
        assert len(keywords) <= 5
        assert 'beautiful' in keywords or 'temple' in keywords
    
    def test_keyword_extractor_empty_text(self):
        """Test keyword extraction with empty text."""
        extractor = KeywordExtractor()
        
        keywords = extractor.extract_keywords("")
        assert keywords == []
        
        keywords = extractor.extract_keywords(None)
        assert keywords == []
    
    def test_keyword_extractor_with_text(self):
        """Test keyword extraction with sample text."""
        extractor = KeywordExtractor()
        
        text = "Amazing temple in Bangkok with beautiful architecture and peaceful atmosphere"
        keywords = extractor.extract_keywords(text, max_keywords=10)
        
        assert isinstance(keywords, list)
        assert len(keywords) <= 10
        # Should contain some meaningful keywords
        assert any(keyword in ['temple', 'bangkok', 'beautiful', 'architecture', 'peaceful', 'amazing'] 
                  for keyword in keywords)
    
    def test_extract_keywords_from_attraction(self):
        """Test extracting keywords from attraction data."""
        attraction_data = {
            'title': 'Beautiful Temple',
            'body': 'Ancient temple with stunning architecture'
        }
        
        keywords = extract_keywords_from_attraction(attraction_data)
        
        assert isinstance(keywords, list)
        assert len(keywords) > 0
    
    def test_keyword_categorization(self):
        """Test keyword categorization."""
        extractor = KeywordExtractor()
        
        keywords = ['temple', 'river', 'restaurant', 'ancient', 'mountain', 'food']
        categories = extractor.get_keyword_categories(keywords)
        
        assert 'nature' in categories
        assert 'culture' in categories
        assert 'activities' in categories
        assert 'food' in categories
        assert 'other' in categories


class TestRecommendationEngine:
    """Test recommendation engine functionality."""
    
    def test_recommendation_engine_initialization(self):
        """Test recommendation engine initialization."""
        engine = RecommendationEngine()
        assert engine is not None
        assert hasattr(engine, 'fallback_recommender')
    
    def test_get_recommendations_new_user(self, app_context, sample_attractions):
        """Test getting recommendations for new user."""
        engine = RecommendationEngine()
        
        recommendations = engine.get_personalized_recommendations('new_user_123', 5)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) <= 5
        
        if recommendations:
            assert 'attraction' in recommendations[0]
            assert 'score' in recommendations[0]
    
    def test_record_user_interaction(self, app_context, sample_attractions):
        """Test recording user interaction."""
        engine = RecommendationEngine()
        
        success = engine.record_user_interaction('user_123', sample_attractions[0].id, 'view')
        assert success is True
        
        # Verify interaction was recorded
        interaction = UserInteraction.query.filter_by(
            user_id='user_123',
            attraction_id=sample_attractions[0].id
        ).first()
        
        assert interaction is not None
        assert interaction.interaction_type == 'view'
    
    def test_get_similar_attractions(self, app_context, sample_attractions):
        """Test getting similar attractions."""
        engine = RecommendationEngine()
        
        # Set keywords for attractions to test similarity
        sample_attractions[0].keywords = '["temple", "beautiful", "ancient"]'
        sample_attractions[1].keywords = '["mountain", "nature", "hiking"]'
        sample_attractions[2].keywords = '["food", "market", "local"]'
        db.session.commit()
        
        similar = engine.get_similar_attractions(sample_attractions[0].id, 2)
        
        assert isinstance(similar, list)
        assert len(similar) <= 2


class TestTrendAnalysis:
    """Test trend analysis functionality."""
    
    def test_trend_analyzer_initialization(self):
        """Test trend analyzer initialization."""
        analyzer = TrendAnalyzer()
        assert analyzer is not None
    
    def test_analyze_popularity_trends_empty_data(self, app_context):
        """Test trend analysis with no data."""
        analyzer = TrendAnalyzer()
        
        trends = analyzer.analyze_popularity_trends(7)
        
        assert isinstance(trends, dict)
        assert 'period' in trends
        assert 'daily_trends' in trends
        assert 'keyword_trends' in trends
        assert trends['total_interactions'] == 0
    
    def test_generate_heatmap_data_empty(self, app_context):
        """Test heatmap generation with no data."""
        analyzer = TrendAnalyzer()
        
        heatmap = analyzer.generate_heatmap_data(7)
        
        assert isinstance(heatmap, dict)
        assert 'grid_data' in heatmap
        assert 'total_interactions' in heatmap
        assert heatmap['total_interactions'] == 0
    
    def test_predict_future_trends_empty_data(self, app_context):
        """Test trend prediction with no data."""
        analyzer = TrendAnalyzer()
        
        predictions = analyzer.predict_future_trends(7)
        
        assert isinstance(predictions, dict)
        assert 'predictions' in predictions
        assert 'confidence' in predictions


class TestContentRewriter:
    """Test content rewriting functionality."""
    
    def test_content_rewriter_initialization(self):
        """Test content rewriter initialization."""
        rewriter = ContentRewriter()
        assert rewriter is not None
        assert hasattr(rewriter, 'fallback_rewriter')
    
    def test_improve_content_empty_text(self):
        """Test content improvement with empty text."""
        rewriter = ContentRewriter()
        
        result = rewriter.improve_content("")
        
        assert isinstance(result, dict)
        assert result['success'] is False
        assert result['original_text'] == ""
        assert result['improved_text'] == ""
    
    def test_improve_content_with_text(self):
        """Test content improvement with sample text."""
        rewriter = ContentRewriter()
        
        text = "this is a temple. it is nice."
        result = rewriter.improve_content(text, style='friendly')
        
        assert isinstance(result, dict)
        assert 'original_text' in result
        assert 'improved_text' in result
        assert 'improvements' in result
        assert 'style' in result
        assert result['style'] == 'friendly'
    
    def test_suggest_improvements(self):
        """Test content improvement suggestions."""
        rewriter = ContentRewriter()
        
        text = "short text"
        suggestions = rewriter.suggest_improvements(text)
        
        assert isinstance(suggestions, list)
        if suggestions:
            assert 'type' in suggestions[0]
            assert 'suggestion' in suggestions[0]
    
    def test_calculate_readability_score(self):
        """Test readability score calculation."""
        rewriter = ContentRewriter()
        
        text = "This is a well-written sentence with good structure and appropriate length."
        score_result = rewriter.calculate_readability_score(text)
        
        assert isinstance(score_result, dict)
        assert 'score' in score_result
        assert 'level' in score_result
        assert 'metrics' in score_result
        assert 0 <= score_result['score'] <= 100


class TestAIRoutes:
    """Test AI feature API routes."""
    
    def test_extract_keywords_route(self, client, app_context, sample_attractions):
        """Test keyword extraction API route."""
        data = {
            'attraction_id': sample_attractions[0].id
        }
        
        response = client.post('/api/ai/keywords/extract', json=data)
        
        assert response.status_code == 200
        result = response.get_json()
        assert 'keywords' in result
        assert 'success' in result
    
    def test_extract_keywords_route_with_text(self, client, app_context):
        """Test keyword extraction API route with text."""
        data = {
            'text': 'Beautiful temple with ancient architecture'
        }
        
        response = client.post('/api/ai/keywords/extract', json=data)
        
        assert response.status_code == 200
        result = response.get_json()
        assert 'keywords' in result
        assert 'success' in result
    
    def test_get_recommendations_route(self, client, app_context, sample_attractions):
        """Test recommendations API route."""
        response = client.get('/api/ai/recommendations/test_user?limit=5')
        
        assert response.status_code == 200
        result = response.get_json()
        assert 'recommendations' in result
        assert 'user_id' in result
        assert result['user_id'] == 'test_user'
    
    def test_record_interaction_route(self, client, app_context, sample_attractions):
        """Test interaction recording API route."""
        data = {
            'user_id': 'test_user',
            'attraction_id': sample_attractions[0].id,
            'interaction_type': 'view'
        }
        
        response = client.post('/api/ai/interactions', json=data)
        
        assert response.status_code == 200
        result = response.get_json()
        assert result['success'] is True
    
    def test_improve_content_route(self, client, app_context, sample_attractions):
        """Test content improvement API route."""
        data = {
            'attraction_id': sample_attractions[0].id,
            'field': 'body',
            'style': 'friendly'
        }
        
        response = client.post('/api/ai/content/improve', json=data)
        
        assert response.status_code == 200
        result = response.get_json()
        assert 'original_text' in result
        assert 'improved_text' in result
    
    def test_get_content_suggestions_route(self, client, app_context, sample_attractions):
        """Test content suggestions API route."""
        data = {
            'attraction_id': sample_attractions[0].id,
            'field': 'body'
        }
        
        response = client.post('/api/ai/content/suggestions', json=data)
        
        assert response.status_code == 200
        result = response.get_json()
        assert 'suggestions' in result
        assert 'readability' in result
    
    def test_analyze_trends_route(self, client, app_context):
        """Test trends analysis API route."""
        response = client.get('/api/ai/trends/analyze?days=7')
        
        assert response.status_code == 200
        result = response.get_json()
        assert 'daily_trends' in result
        assert 'keyword_trends' in result
    
    def test_get_heatmap_route(self, client, app_context):
        """Test heatmap API route."""
        response = client.get('/api/ai/trends/heatmap?days=7')
        
        assert response.status_code == 200
        result = response.get_json()
        assert 'grid_data' in result
        assert 'total_interactions' in result
    
    def test_get_ai_stats_route(self, client, app_context, sample_attractions):
        """Test AI stats API route."""
        response = client.get('/api/ai/stats')
        
        assert response.status_code == 200
        result = response.get_json()
        assert 'attractions' in result
        assert 'interactions' in result
        assert 'total' in result['attractions']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])