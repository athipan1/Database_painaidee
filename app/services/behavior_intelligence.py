"""
Enhanced User Behavior Intelligence Service
พัฒนาระบบเรียนรู้พฤติกรรมผู้ใช้ (User Behavior Intelligence)
"""
import json
import uuid
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from flask import request
import re

try:
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    import numpy as np
    SKLEARN_AVAILABLE = True
    NUMPY_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    try:
        import numpy as np
        NUMPY_AVAILABLE = True
    except ImportError:
        NUMPY_AVAILABLE = False

from app.models import (
    db, UserInteraction, UserBehaviorSession, SearchQuery, 
    UserPreference, Attraction
)


class BehaviorIntelligenceService:
    """Enhanced service for comprehensive user behavior intelligence."""
    
    def __init__(self):
        self.use_ml = SKLEARN_AVAILABLE
        
    def track_interaction(
        self,
        user_id: str,
        attraction_id: Optional[int] = None,
        interaction_type: str = 'view',
        duration_seconds: Optional[int] = None,
        search_query: Optional[str] = None,
        page_url: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict:
        """
        Track comprehensive user interaction.
        
        Args:
            user_id: User identifier
            attraction_id: Attraction ID (optional for general tracking)
            interaction_type: Type of interaction
            duration_seconds: Time spent on interaction
            search_query: Search query if applicable
            page_url: Current page URL
            session_id: Session identifier
            
        Returns:
            Result dictionary with tracking status
        """
        try:
            # Generate session ID if not provided
            if not session_id:
                session_id = self._get_or_create_session_id(user_id)
            
            # Update or create behavior session
            self._update_behavior_session(
                session_id, user_id, interaction_type, 
                duration_seconds, search_query
            )
            
            # Track search query separately if provided
            if search_query:
                self._track_search_query(
                    session_id, user_id, search_query, attraction_id
                )
            
            # Track interaction if attraction is specified
            if attraction_id:
                interaction = UserInteraction(
                    user_id=user_id,
                    attraction_id=attraction_id,
                    interaction_type=interaction_type,
                    interaction_value=self._calculate_interaction_value(
                        interaction_type, duration_seconds
                    ),
                    duration_seconds=duration_seconds,
                    search_query=search_query,
                    page_url=page_url,
                    user_agent=request.headers.get('User-Agent') if request else None,
                    session_id=session_id
                )
                db.session.add(interaction)
                
                # Update attraction view count
                attraction = Attraction.query.get(attraction_id)
                if attraction:
                    attraction.view_count = (attraction.view_count or 0) + 1
                
                # Learn user preferences
                self._learn_user_preferences(user_id, attraction, interaction_type)
            
            db.session.commit()
            
            return {
                'success': True,
                'session_id': session_id,
                'message': 'Interaction tracked successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_or_create_session_id(self, user_id: str) -> str:
        """Get or create session ID for user."""
        # Try to find active session in last 30 minutes
        cutoff_time = datetime.utcnow() - timedelta(minutes=30)
        
        active_session = UserBehaviorSession.query.filter(
            UserBehaviorSession.user_id == user_id,
            UserBehaviorSession.updated_at > cutoff_time,
            UserBehaviorSession.end_time.is_(None)
        ).first()
        
        if active_session:
            return active_session.session_id
        else:
            return str(uuid.uuid4())
    
    def _update_behavior_session(
        self,
        session_id: str,
        user_id: str,
        interaction_type: str,
        duration_seconds: Optional[int],
        search_query: Optional[str]
    ):
        """Update or create behavior session."""
        session = UserBehaviorSession.query.filter_by(session_id=session_id).first()
        
        if not session:
            session = UserBehaviorSession(
                session_id=session_id,
                user_id=user_id,
                user_agent=request.headers.get('User-Agent') if request else None,
                ip_address=request.remote_addr if request else None,
                device_type=self._detect_device_type()
            )
            db.session.add(session)
        
        # Update session statistics
        session.updated_at = datetime.utcnow()
        session.interactions_count = (session.interactions_count or 0) + 1
        
        if duration_seconds:
            session.total_duration_seconds = (session.total_duration_seconds or 0) + duration_seconds
        
        if interaction_type == 'page_view':
            session.page_views = (session.page_views or 0) + 1
        elif interaction_type == 'search':
            session.search_queries_count = (session.search_queries_count or 0) + 1
        elif interaction_type == 'favorite':
            session.favorites_count = (session.favorites_count or 0) + 1
        
        if search_query:
            session.search_queries_count = (session.search_queries_count or 0) + 1
    
    def _detect_device_type(self) -> str:
        """Detect device type from user agent."""
        if not request:
            return 'unknown'
            
        user_agent = request.headers.get('User-Agent', '').lower()
        
        if 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent:
            return 'mobile'
        elif 'tablet' in user_agent or 'ipad' in user_agent:
            return 'tablet'
        else:
            return 'desktop'
    
    def _track_search_query(
        self,
        session_id: str,
        user_id: str,
        query_text: str,
        clicked_attraction_id: Optional[int] = None
    ):
        """Track search query separately."""
        search_query = SearchQuery(
            session_id=session_id,
            user_id=user_id,
            query_text=query_text,
            search_context='general'  # Can be enhanced based on context
        )
        
        if clicked_attraction_id:
            search_query.clicked_results = json.dumps([clicked_attraction_id])
        
        db.session.add(search_query)
    
    def _calculate_interaction_value(
        self,
        interaction_type: str,
        duration_seconds: Optional[int]
    ) -> float:
        """Calculate interaction value based on type and duration."""
        base_values = {
            'view': 0.5,
            'click': 0.7,
            'search': 0.6,
            'favorite': 1.0,
            'share': 0.8,
            'bookmark': 0.9,
            'page_view': 0.3
        }
        
        base_value = base_values.get(interaction_type, 0.5)
        
        # Enhance value based on duration
        if duration_seconds:
            if duration_seconds > 300:  # 5+ minutes
                base_value *= 1.5
            elif duration_seconds > 60:  # 1+ minutes
                base_value *= 1.2
            elif duration_seconds < 5:  # Less than 5 seconds
                base_value *= 0.5
        
        return min(base_value, 1.0)
    
    def _learn_user_preferences(
        self,
        user_id: str,
        attraction: Attraction,
        interaction_type: str
    ):
        """Learn and update user preferences from interactions."""
        if not attraction:
            return
        
        # Learn province preference
        if attraction.province:
            self._update_preference(
                user_id, 'province', attraction.province,
                self._calculate_preference_weight(interaction_type)
            )
        
        # Learn keyword preferences
        if attraction.keywords:
            try:
                keywords = json.loads(attraction.keywords)
                for keyword in keywords[:5]:  # Top 5 keywords
                    self._update_preference(
                        user_id, 'keyword', keyword,
                        self._calculate_preference_weight(interaction_type) * 0.8
                    )
            except:
                pass
    
    def _update_preference(
        self,
        user_id: str,
        preference_type: str,
        preference_value: str,
        weight: float
    ):
        """Update user preference with new interaction."""
        preference = UserPreference.query.filter_by(
            user_id=user_id,
            preference_type=preference_type,
            preference_value=preference_value
        ).first()
        
        if preference:
            # Update existing preference
            preference.interaction_count += 1
            preference.last_interaction = datetime.utcnow()
            
            # Update confidence score using exponential moving average
            alpha = 0.1  # Learning rate
            preference.confidence_score = (
                (1 - alpha) * preference.confidence_score + alpha * weight
            )
        else:
            # Create new preference
            preference = UserPreference(
                user_id=user_id,
                preference_type=preference_type,
                preference_value=preference_value,
                confidence_score=weight * 0.5,  # Start with lower confidence
                interaction_count=1
            )
            db.session.add(preference)
    
    def _calculate_preference_weight(self, interaction_type: str) -> float:
        """Calculate preference learning weight based on interaction type."""
        weights = {
            'view': 0.3,
            'click': 0.5,
            'search': 0.4,
            'favorite': 1.0,
            'share': 0.8,
            'bookmark': 0.9
        }
        return weights.get(interaction_type, 0.3)
    
    def analyze_user_behavior(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict:
        """
        Analyze comprehensive user behavior patterns.
        
        Args:
            user_id: User identifier
            days: Analysis period in days
            
        Returns:
            Comprehensive behavior analysis
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get user interactions
        interactions = UserInteraction.query.filter(
            UserInteraction.user_id == user_id,
            UserInteraction.created_at >= start_date
        ).all()
        
        # Get user sessions
        sessions = UserBehaviorSession.query.filter(
            UserBehaviorSession.user_id == user_id,
            UserBehaviorSession.created_at >= start_date
        ).all()
        
        # Get search queries
        searches = SearchQuery.query.filter(
            SearchQuery.user_id == user_id,
            SearchQuery.created_at >= start_date
        ).all()
        
        # Get user preferences
        preferences = UserPreference.query.filter_by(user_id=user_id).all()
        
        # Analyze patterns
        behavior_patterns = self._detect_behavior_patterns(
            interactions, sessions, searches
        )
        
        # Calculate averages safely
        avg_session_duration = 0
        if sessions:
            if NUMPY_AVAILABLE:
                avg_session_duration = np.mean([s.total_duration_seconds for s in sessions])
            else:
                avg_session_duration = sum(s.total_duration_seconds for s in sessions) / len(sessions)
        
        return {
            'user_id': user_id,
            'analysis_period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days
            },
            'interaction_summary': {
                'total_interactions': len(interactions),
                'unique_attractions': len(set(i.attraction_id for i in interactions)),
                'interaction_types': dict(Counter(i.interaction_type for i in interactions)),
                'total_duration': sum(i.duration_seconds or 0 for i in interactions)
            },
            'session_summary': {
                'total_sessions': len(sessions),
                'avg_session_duration': avg_session_duration,
                'total_page_views': sum(s.page_views for s in sessions),
                'device_types': dict(Counter(s.device_type for s in sessions if s.device_type))
            },
            'search_summary': {
                'total_searches': len(searches),
                'unique_queries': len(set(s.query_text for s in searches)),
                'popular_queries': [q for q, c in Counter(s.query_text for s in searches).most_common(10)]
            },
            'preferences': {
                pref.preference_type: [
                    {
                        'value': p.preference_value,
                        'confidence': p.confidence_score,
                        'interactions': p.interaction_count
                    }
                    for p in preferences if p.preference_type == pref.preference_type
                ]
                for pref in preferences
            },
            'behavior_patterns': behavior_patterns
        }
    
    def _detect_behavior_patterns(
        self,
        interactions: List[UserInteraction],
        sessions: List[UserBehaviorSession],
        searches: List[SearchQuery]
    ) -> Dict:
        """Detect behavioral patterns from user data."""
        patterns = {
            'browsing_style': 'normal',
            'search_behavior': 'moderate',
            'engagement_level': 'medium',
            'time_patterns': {},
            'preferences_strength': 'developing'
        }
        
        if not interactions:
            return patterns
        
        # Analyze browsing style
        if NUMPY_AVAILABLE:
            avg_duration = np.mean([i.duration_seconds or 0 for i in interactions])
        else:
            durations = [i.duration_seconds or 0 for i in interactions]
            avg_duration = sum(durations) / len(durations) if durations else 0
        if avg_duration > 180:  # 3+ minutes
            patterns['browsing_style'] = 'thorough'
        elif avg_duration < 30:  # Less than 30 seconds
            patterns['browsing_style'] = 'quick'
        
        # Analyze search behavior
        search_to_interaction_ratio = len(searches) / len(interactions) if interactions else 0
        if search_to_interaction_ratio > 0.5:
            patterns['search_behavior'] = 'heavy'
        elif search_to_interaction_ratio < 0.1:
            patterns['search_behavior'] = 'light'
        
        # Analyze engagement level
        high_value_interactions = [i for i in interactions if i.interaction_value > 0.7]
        engagement_ratio = len(high_value_interactions) / len(interactions)
        if engagement_ratio > 0.3:
            patterns['engagement_level'] = 'high'
        elif engagement_ratio < 0.1:
            patterns['engagement_level'] = 'low'
        
        # Analyze time patterns
        hour_distribution = Counter(i.created_at.hour for i in interactions)
        patterns['time_patterns'] = {
            'most_active_hour': hour_distribution.most_common(1)[0][0] if hour_distribution else None,
            'activity_distribution': dict(hour_distribution)
        }
        
        return patterns
    
    def get_real_time_recommendations(
        self,
        user_id: str,
        current_context: Optional[Dict] = None,
        num_recommendations: int = 10
    ) -> List[Dict]:
        """
        Get real-time personalized recommendations.
        
        Args:
            user_id: User identifier
            current_context: Current browsing context
            num_recommendations: Number of recommendations
            
        Returns:
            List of real-time recommendations
        """
        try:
            # Get user preferences
            preferences = UserPreference.query.filter_by(user_id=user_id).all()
            
            # Get recent interactions (last 24 hours)
            recent_cutoff = datetime.utcnow() - timedelta(hours=24)
            recent_interactions = UserInteraction.query.filter(
                UserInteraction.user_id == user_id,
                UserInteraction.created_at >= recent_cutoff
            ).all()
            
            # Build recommendation query
            query = Attraction.query
            
            # Exclude recently viewed attractions
            if recent_interactions:
                viewed_ids = [i.attraction_id for i in recent_interactions]
                query = query.filter(~Attraction.id.in_(viewed_ids))
            
            all_attractions = query.all()
            
            if not all_attractions:
                return []
            
            # Score attractions based on user preferences and context
            scored_attractions = []
            for attraction in all_attractions:
                score = self._calculate_real_time_score(
                    attraction, preferences, recent_interactions, current_context
                )
                
                if score > 0.1:  # Minimum threshold
                    scored_attractions.append({
                        'attraction': attraction.to_dict(),
                        'score': score,
                        'reasons': self._get_recommendation_reasons(
                            attraction, preferences, current_context
                        )
                    })
            
            # Sort by score and return top recommendations
            scored_attractions.sort(key=lambda x: x['score'], reverse=True)
            return scored_attractions[:num_recommendations]
            
        except Exception as e:
            print(f"Error getting real-time recommendations: {e}")
            return []
    
    def _calculate_real_time_score(
        self,
        attraction: Attraction,
        preferences: List[UserPreference],
        recent_interactions: List[UserInteraction],
        current_context: Optional[Dict]
    ) -> float:
        """Calculate real-time recommendation score."""
        score = 0.0
        
        # Preference matching (40% weight)
        preference_score = self._calculate_preference_match(attraction, preferences)
        score += preference_score * 0.4
        
        # Recent behavior similarity (30% weight)
        behavior_score = self._calculate_behavior_similarity(attraction, recent_interactions)
        score += behavior_score * 0.3
        
        # Current context relevance (20% weight)
        context_score = self._calculate_context_relevance(attraction, current_context)
        score += context_score * 0.2
        
        # Popularity boost (10% weight)
        popularity_score = min(attraction.view_count / 1000, 1.0)
        score += popularity_score * 0.1
        
        return min(score, 1.0)
    
    def _calculate_preference_match(
        self,
        attraction: Attraction,
        preferences: List[UserPreference]
    ) -> float:
        """Calculate how well attraction matches user preferences."""
        if not preferences:
            return 0.0
        
        total_score = 0.0
        total_weight = 0.0
        
        for pref in preferences:
            weight = pref.confidence_score
            match_score = 0.0
            
            if pref.preference_type == 'province' and attraction.province:
                if pref.preference_value == attraction.province:
                    match_score = 1.0
            
            elif pref.preference_type == 'keyword' and attraction.keywords:
                try:
                    keywords = json.loads(attraction.keywords)
                    if pref.preference_value in keywords:
                        match_score = 0.8
                except:
                    pass
            
            total_score += match_score * weight
            total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0.0
    
    def _calculate_behavior_similarity(
        self,
        attraction: Attraction,
        recent_interactions: List[UserInteraction]
    ) -> float:
        """Calculate similarity based on recent user behavior."""
        if not recent_interactions:
            return 0.0
        
        # Find attractions with similar characteristics
        similar_score = 0.0
        
        for interaction in recent_interactions[-5:]:  # Last 5 interactions
            if interaction.attraction:
                # Province similarity
                if (attraction.province and interaction.attraction.province and
                    attraction.province == interaction.attraction.province):
                    similar_score += 0.3
                
                # Keyword similarity
                if attraction.keywords and interaction.attraction.keywords:
                    try:
                        keywords1 = set(json.loads(attraction.keywords))
                        keywords2 = set(json.loads(interaction.attraction.keywords))
                        
                        intersection = len(keywords1.intersection(keywords2))
                        union = len(keywords1.union(keywords2))
                        
                        if union > 0:
                            similar_score += (intersection / union) * 0.4
                    except:
                        pass
        
        return min(similar_score / len(recent_interactions), 1.0)
    
    def _calculate_context_relevance(
        self,
        attraction: Attraction,
        current_context: Optional[Dict]
    ) -> float:
        """Calculate relevance based on current browsing context."""
        if not current_context:
            return 0.5  # Neutral score
        
        relevance_score = 0.5
        
        # Search context
        if current_context.get('search_query'):
            query = current_context['search_query'].lower()
            
            # Check title match
            if query in attraction.title.lower():
                relevance_score += 0.3
            
            # Check keyword match
            if attraction.keywords:
                try:
                    keywords = json.loads(attraction.keywords)
                    for keyword in keywords:
                        if query in keyword.lower():
                            relevance_score += 0.2
                            break
                except:
                    pass
        
        # Location context
        if current_context.get('province') and attraction.province:
            if current_context['province'] == attraction.province:
                relevance_score += 0.2
        
        return min(relevance_score, 1.0)
    
    def _get_recommendation_reasons(
        self,
        attraction: Attraction,
        preferences: List[UserPreference],
        current_context: Optional[Dict]
    ) -> List[str]:
        """Get reasons for recommendation."""
        reasons = []
        
        # Check preference matches
        for pref in preferences:
            if pref.confidence_score > 0.5:
                if pref.preference_type == 'province' and attraction.province:
                    if pref.preference_value == attraction.province:
                        reasons.append(f"Matches your interest in {attraction.province}")
                
                elif pref.preference_type == 'keyword' and attraction.keywords:
                    try:
                        keywords = json.loads(attraction.keywords)
                        if pref.preference_value in keywords:
                            reasons.append(f"Related to {pref.preference_value}")
                    except:
                        pass
        
        # Context-based reasons
        if current_context and current_context.get('search_query'):
            query = current_context['search_query'].lower()
            if query in attraction.title.lower():
                reasons.append("Matches your search")
        
        # Popularity reason
        if attraction.view_count > 100:
            reasons.append("Popular destination")
        
        return reasons[:3]  # Limit to 3 reasons

    def end_session(self, session_id: str) -> bool:
        """End a user behavior session."""
        try:
            session = UserBehaviorSession.query.filter_by(session_id=session_id).first()
            if session:
                session.end_time = datetime.utcnow()
                db.session.commit()
                return True
            return False
        except Exception as e:
            db.session.rollback()
            print(f"Error ending session: {e}")
            return False