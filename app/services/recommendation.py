"""
AI-powered recommendation service for personalized attraction suggestions.
"""
import json
from typing import List, Dict, Tuple, Optional
from collections import defaultdict, Counter
from datetime import datetime, timedelta

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.cluster import KMeans
    import numpy as np
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from app.models import Attraction, UserInteraction
from app.services.keyword_extraction import keywords_from_json


class RecommendationEngine:
    """AI-powered recommendation engine for attractions."""
    
    def __init__(self):
        self.fallback_recommender = FallbackRecommender()
        self.use_ml = SKLEARN_AVAILABLE
    
    def get_personalized_recommendations(
        self, 
        user_id: str, 
        num_recommendations: int = 10,
        exclude_viewed: bool = True
    ) -> List[Dict]:
        """
        Get personalized recommendations for a user.
        
        Args:
            user_id: User identifier
            num_recommendations: Number of recommendations to return
            exclude_viewed: Whether to exclude already viewed attractions
            
        Returns:
            List of recommended attractions with scores
        """
        if self.use_ml:
            return self._get_ml_recommendations(user_id, num_recommendations, exclude_viewed)
        else:
            return self.fallback_recommender.get_recommendations(user_id, num_recommendations, exclude_viewed)
    
    def _get_ml_recommendations(
        self, 
        user_id: str, 
        num_recommendations: int,
        exclude_viewed: bool
    ) -> List[Dict]:
        """Get recommendations using machine learning algorithms."""
        
        # Get user's interaction history
        user_interactions = UserInteraction.query.filter_by(user_id=user_id).all()
        
        if not user_interactions:
            # New user - use popularity-based recommendations
            return self._get_popularity_recommendations(num_recommendations)
        
        # Get user preferences from interactions
        user_preferences = self._analyze_user_preferences(user_interactions)
        
        # Get all attractions
        all_attractions = Attraction.query.all()
        
        if exclude_viewed:
            viewed_attraction_ids = {interaction.attraction_id for interaction in user_interactions}
            candidate_attractions = [a for a in all_attractions if a.id not in viewed_attraction_ids]
        else:
            candidate_attractions = all_attractions
        
        if not candidate_attractions:
            return []
        
        # Calculate recommendation scores
        recommendations = []
        for attraction in candidate_attractions:
            score = self._calculate_recommendation_score(attraction, user_preferences, user_interactions)
            recommendations.append({
                'attraction': attraction.to_dict(),
                'score': score,
                'reasons': self._get_recommendation_reasons(attraction, user_preferences)
            })
        
        # Sort by score and return top recommendations
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        return recommendations[:num_recommendations]
    
    def _analyze_user_preferences(self, interactions: List[UserInteraction]) -> Dict:
        """Analyze user preferences from interaction history."""
        preferences = {
            'preferred_keywords': Counter(),
            'preferred_provinces': Counter(),
            'interaction_weights': {},
            'total_interactions': len(interactions)
        }
        
        for interaction in interactions:
            attraction = interaction.attraction
            weight = interaction.interaction_value
            
            # Count preferred keywords
            if attraction.keywords:
                keywords = keywords_from_json(attraction.keywords)
                for keyword in keywords:
                    preferences['preferred_keywords'][keyword] += weight
            
            # Count preferred provinces
            if attraction.province:
                preferences['preferred_provinces'][attraction.province] += weight
            
            # Store interaction weights
            preferences['interaction_weights'][attraction.id] = weight
        
        return preferences
    
    def _calculate_recommendation_score(
        self, 
        attraction: Attraction, 
        user_preferences: Dict,
        user_interactions: List[UserInteraction]
    ) -> float:
        """Calculate recommendation score for an attraction."""
        score = 0.0
        
        # Keyword similarity score (40% weight)
        keyword_score = self._calculate_keyword_similarity(attraction, user_preferences)
        score += keyword_score * 0.4
        
        # Province preference score (20% weight)
        province_score = self._calculate_province_preference(attraction, user_preferences)
        score += province_score * 0.2
        
        # Popularity score (20% weight)
        popularity_score = self._calculate_popularity_score(attraction)
        score += popularity_score * 0.2
        
        # Collaborative filtering score (20% weight)
        collaborative_score = self._calculate_collaborative_score(attraction, user_interactions)
        score += collaborative_score * 0.2
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _calculate_keyword_similarity(self, attraction: Attraction, user_preferences: Dict) -> float:
        """Calculate keyword similarity score."""
        if not attraction.keywords or not user_preferences['preferred_keywords']:
            return 0.0
        
        attraction_keywords = set(keywords_from_json(attraction.keywords))
        user_keywords = set(user_preferences['preferred_keywords'].keys())
        
        if not attraction_keywords or not user_keywords:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = len(attraction_keywords.intersection(user_keywords))
        union = len(attraction_keywords.union(user_keywords))
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_province_preference(self, attraction: Attraction, user_preferences: Dict) -> float:
        """Calculate province preference score."""
        if not attraction.province or not user_preferences['preferred_provinces']:
            return 0.0
        
        province_count = user_preferences['preferred_provinces'].get(attraction.province, 0)
        max_province_count = max(user_preferences['preferred_provinces'].values()) if user_preferences['preferred_provinces'] else 1
        
        return province_count / max_province_count
    
    def _calculate_popularity_score(self, attraction: Attraction) -> float:
        """Calculate popularity score based on view count."""
        max_views = 1000  # Assume max views for normalization
        return min(attraction.view_count / max_views, 1.0)
    
    def _calculate_collaborative_score(self, attraction: Attraction, user_interactions: List[UserInteraction]) -> float:
        """Calculate collaborative filtering score."""
        # Simple collaborative filtering based on users with similar preferences
        user_attraction_ids = {interaction.attraction_id for interaction in user_interactions}
        
        # Find users who liked similar attractions
        similar_users = UserInteraction.query.filter(
            UserInteraction.attraction_id.in_(user_attraction_ids),
            UserInteraction.interaction_value > 0.5
        ).distinct(UserInteraction.user_id).all()
        
        if not similar_users:
            return 0.0
        
        # Count how many similar users liked this attraction
        similar_user_ids = [user.user_id for user in similar_users]
        attraction_likes = UserInteraction.query.filter(
            UserInteraction.attraction_id == attraction.id,
            UserInteraction.user_id.in_(similar_user_ids),
            UserInteraction.interaction_value > 0.5
        ).count()
        
        return attraction_likes / len(similar_user_ids) if similar_user_ids else 0.0
    
    def _get_recommendation_reasons(self, attraction: Attraction, user_preferences: Dict) -> List[str]:
        """Get reasons why this attraction is recommended."""
        reasons = []
        
        # Check keyword matches
        if attraction.keywords:
            attraction_keywords = set(keywords_from_json(attraction.keywords))
            user_keywords = set(user_preferences['preferred_keywords'].keys())
            common_keywords = attraction_keywords.intersection(user_keywords)
            
            if common_keywords:
                reasons.append(f"Matches your interests: {', '.join(list(common_keywords)[:3])}")
        
        # Check province preference
        if attraction.province and attraction.province in user_preferences['preferred_provinces']:
            reasons.append(f"You've shown interest in {attraction.province}")
        
        # Check popularity
        if attraction.view_count > 100:
            reasons.append("Popular destination")
        
        return reasons[:3]  # Limit to 3 reasons
    
    def _get_popularity_recommendations(self, num_recommendations: int) -> List[Dict]:
        """Get recommendations based on popularity for new users."""
        popular_attractions = Attraction.query.order_by(
            Attraction.view_count.desc()
        ).limit(num_recommendations).all()
        
        recommendations = []
        for attraction in popular_attractions:
            recommendations.append({
                'attraction': attraction.to_dict(),
                'score': min(attraction.view_count / 1000, 1.0),
                'reasons': ['Popular destination', 'Highly viewed by other users']
            })
        
        return recommendations
    
    def get_similar_attractions(self, attraction_id: int, num_similar: int = 5) -> List[Dict]:
        """Get attractions similar to a given attraction."""
        target_attraction = Attraction.query.get(attraction_id)
        if not target_attraction:
            return []
        
        all_attractions = Attraction.query.filter(Attraction.id != attraction_id).all()
        
        if not all_attractions:
            return []
        
        similarities = []
        for attraction in all_attractions:
            similarity = self._calculate_attraction_similarity(target_attraction, attraction)
            similarities.append({
                'attraction': attraction.to_dict(),
                'similarity': similarity
            })
        
        # Sort by similarity and return top results
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return similarities[:num_similar]
    
    def _calculate_attraction_similarity(self, attraction1: Attraction, attraction2: Attraction) -> float:
        """Calculate similarity between two attractions."""
        similarity = 0.0
        
        # Keyword similarity (50% weight)
        if attraction1.keywords and attraction2.keywords:
            keywords1 = set(keywords_from_json(attraction1.keywords))
            keywords2 = set(keywords_from_json(attraction2.keywords))
            
            if keywords1 and keywords2:
                intersection = len(keywords1.intersection(keywords2))
                union = len(keywords1.union(keywords2))
                keyword_similarity = intersection / union if union > 0 else 0.0
                similarity += keyword_similarity * 0.5
        
        # Province similarity (30% weight)
        if attraction1.province and attraction2.province:
            if attraction1.province == attraction2.province:
                similarity += 0.3
        
        # Geographic proximity (20% weight) - if coordinates available
        if (attraction1.latitude and attraction1.longitude and
            attraction2.latitude and attraction2.longitude):
            distance = self._calculate_distance(
                attraction1.latitude, attraction1.longitude,
                attraction2.latitude, attraction2.longitude
            )
            # Closer attractions are more similar (inverse relationship)
            geo_similarity = max(0, 1 - (distance / 100))  # Normalize by 100km
            similarity += geo_similarity * 0.2
        
        return min(similarity, 1.0)
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates in kilometers."""
        try:
            import math
            
            # Haversine formula
            R = 6371  # Earth's radius in kilometers
            
            dlat = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)
            
            a = (math.sin(dlat/2) * math.sin(dlat/2) +
                 math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
                 math.sin(dlon/2) * math.sin(dlon/2))
            
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            distance = R * c
            
            return distance
        except:
            return float('inf')
    
    def record_user_interaction(
        self, 
        user_id: str, 
        attraction_id: int, 
        interaction_type: str = 'view',
        interaction_value: float = 1.0
    ) -> bool:
        """Record a user interaction for recommendation learning."""
        try:
            from app.models import db
            
            # Update attraction view count
            attraction = Attraction.query.get(attraction_id)
            if attraction:
                attraction.view_count += 1
            
            # Record interaction
            interaction = UserInteraction(
                user_id=user_id,
                attraction_id=attraction_id,
                interaction_type=interaction_type,
                interaction_value=interaction_value
            )
            
            db.session.add(interaction)
            db.session.commit()
            
            return True
        except Exception as e:
            print(f"Error recording interaction: {e}")
            return False


class FallbackRecommender:
    """Simple recommendation system that doesn't require ML libraries."""
    
    def get_recommendations(
        self, 
        user_id: str, 
        num_recommendations: int = 10,
        exclude_viewed: bool = True
    ) -> List[Dict]:
        """Get simple popularity-based recommendations."""
        
        # Get user's viewed attractions if excluding them
        viewed_ids = set()
        if exclude_viewed:
            user_interactions = UserInteraction.query.filter_by(user_id=user_id).all()
            viewed_ids = {interaction.attraction_id for interaction in user_interactions}
        
        # Get popular attractions
        query = Attraction.query
        if viewed_ids:
            query = query.filter(~Attraction.id.in_(viewed_ids))
        
        popular_attractions = query.order_by(
            Attraction.view_count.desc()
        ).limit(num_recommendations).all()
        
        recommendations = []
        for attraction in popular_attractions:
            score = min(attraction.view_count / 100, 1.0)  # Normalize score
            recommendations.append({
                'attraction': attraction.to_dict(),
                'score': score,
                'reasons': ['Popular destination'] if attraction.view_count > 10 else ['New destination']
            })
        
        return recommendations


def get_user_recommendations(user_id: str, num_recommendations: int = 10) -> List[Dict]:
    """
    Get personalized recommendations for a user.
    
    Args:
        user_id: User identifier
        num_recommendations: Number of recommendations to return
        
    Returns:
        List of recommended attractions
    """
    engine = RecommendationEngine()
    return engine.get_personalized_recommendations(user_id, num_recommendations)


def record_interaction(user_id: str, attraction_id: int, interaction_type: str = 'view') -> bool:
    """
    Record a user interaction.
    
    Args:
        user_id: User identifier
        attraction_id: Attraction ID
        interaction_type: Type of interaction ('view', 'like', 'click', etc.)
        
    Returns:
        Success status
    """
    engine = RecommendationEngine()
    
    # Set interaction values based on type
    interaction_values = {
        'view': 0.5,
        'click': 0.7,
        'like': 1.0,
        'share': 0.8,
        'bookmark': 0.9
    }
    
    value = interaction_values.get(interaction_type, 0.5)
    return engine.record_user_interaction(user_id, attraction_id, interaction_type, value)