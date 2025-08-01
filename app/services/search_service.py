"""
Search and recommendation service.
Implements full-text search and recommendation algorithms.
"""
import logging
import json
from typing import Dict, List, Optional, Tuple
from sqlalchemy import text, or_, and_, func
from app.models import db, Attraction
from app.services.cache_service import cached_query

logger = logging.getLogger(__name__)


class SearchService:
    """Service for search and recommendation functionality."""
    
    @staticmethod
    def create_search_indexes():
        """Create full-text search indexes in PostgreSQL."""
        try:
            # Create GIN index for full-text search
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_attractions_search 
                ON attractions USING GIN (
                    to_tsvector('english', 
                        COALESCE(title, '') || ' ' || 
                        COALESCE(body, '') || ' ' || 
                        COALESCE(ai_summary, '')
                    )
                )
            """))
            
            # Create index for Thai text search  
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_attractions_search_thai 
                ON attractions USING GIN (
                    to_tsvector('simple', 
                        COALESCE(title, '') || ' ' || 
                        COALESCE(body, '') || ' ' || 
                        COALESCE(ai_summary, '')
                    )
                )
            """))
            
            # Create composite indexes for filtering
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_attractions_province_score 
                ON attractions (province, popularity_score DESC)
            """))
            
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_attractions_ai_processed 
                ON attractions (ai_processed, popularity_score DESC)
            """))
            
            db.session.commit()
            logger.info("Search indexes created successfully")
            
        except Exception as e:
            logger.error(f"Error creating search indexes: {str(e)}")
            db.session.rollback()
    
    @staticmethod
    @cached_query(timeout=300, key_prefix="fulltext_search")
    def full_text_search(query: str, page: int = 1, per_page: int = 20, 
                        filters: Dict = None) -> Dict:
        """
        Perform full-text search on attractions.
        
        Args:
            query: Search query string
            page: Page number for pagination
            per_page: Results per page
            filters: Additional filters (province, min_score, etc.)
        
        Returns:
            Dict with search results and metadata
        """
        try:
            # Prepare search query for PostgreSQL
            search_terms = query.strip().replace("'", "''")  # Escape single quotes
            
            # Build base query with full-text search
            base_query = db.session.query(Attraction).filter(
                or_(
                    # PostgreSQL full-text search
                    func.to_tsvector('english', 
                        func.coalesce(Attraction.title, '') + ' ' +
                        func.coalesce(Attraction.body, '') + ' ' +
                        func.coalesce(Attraction.ai_summary, '')
                    ).op('@@')(func.plainto_tsquery('english', search_terms)),
                    
                    # Thai/simple text search
                    func.to_tsvector('simple', 
                        func.coalesce(Attraction.title, '') + ' ' +
                        func.coalesce(Attraction.body, '') + ' ' +
                        func.coalesce(Attraction.ai_summary, '')
                    ).op('@@')(func.plainto_tsquery('simple', search_terms)),
                    
                    # Fallback LIKE search
                    Attraction.title.ilike(f'%{search_terms}%'),
                    Attraction.body.ilike(f'%{search_terms}%'),
                    Attraction.ai_summary.ilike(f'%{search_terms}%')
                )
            )
            
            # Apply filters
            if filters:
                if filters.get('province'):
                    base_query = base_query.filter(Attraction.province == filters['province'])
                
                if filters.get('min_score') is not None:
                    base_query = base_query.filter(Attraction.popularity_score >= filters['min_score'])
                
                if filters.get('ai_processed') is not None:
                    base_query = base_query.filter(Attraction.ai_processed == filters['ai_processed'])
                
                if filters.get('categories'):
                    # Search within AI tags
                    categories = filters['categories']
                    if isinstance(categories, list):
                        category_conditions = []
                        for category in categories:
                            category_conditions.append(
                                Attraction.ai_tags.ilike(f'%{category}%')
                            )
                        base_query = base_query.filter(or_(*category_conditions))
            
            # Order by relevance and popularity
            search_query = base_query.order_by(
                Attraction.popularity_score.desc(),
                Attraction.updated_at.desc()
            )
            
            # Apply pagination
            paginated = search_query.paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            
            # Format results
            results = []
            for attraction in paginated.items:
                attraction_dict = attraction.to_dict()
                # Add search relevance info
                attraction_dict['search_score'] = SearchService._calculate_relevance_score(
                    attraction, search_terms
                )
                results.append(attraction_dict)
            
            return {
                'attractions': results,
                'total': paginated.total,
                'pages': paginated.pages,
                'current_page': page,
                'per_page': per_page,
                'query': query,
                'filters': filters or {}
            }
            
        except Exception as e:
            logger.error(f"Error in full-text search: {str(e)}")
            # Fallback to simple search
            return SearchService._simple_search(query, page, per_page, filters)
    
    @staticmethod
    def _calculate_relevance_score(attraction: Attraction, search_terms: str) -> float:
        """Calculate relevance score for search result."""
        try:
            score = 0.0
            terms = search_terms.lower().split()
            
            title_lower = (attraction.title or '').lower()
            body_lower = (attraction.body or '').lower()
            summary_lower = (attraction.ai_summary or '').lower()
            
            for term in terms:
                # Title matches are most important
                if term in title_lower:
                    score += 3.0
                
                # Body matches
                if term in body_lower:
                    score += 1.0
                
                # Summary matches
                if term in summary_lower:
                    score += 2.0
            
            # Boost by popularity score
            score *= (1 + attraction.popularity_score / 10)
            
            return round(score, 2)
            
        except Exception as e:
            logger.error(f"Error calculating relevance score: {str(e)}")
            return 0.0
    
    @staticmethod
    def _simple_search(query: str, page: int = 1, per_page: int = 20, 
                      filters: Dict = None) -> Dict:
        """Fallback simple search implementation."""
        try:
            base_query = Attraction.query.filter(
                or_(
                    Attraction.title.ilike(f'%{query}%'),
                    Attraction.body.ilike(f'%{query}%'),
                    Attraction.ai_summary.ilike(f'%{query}%')
                )
            )
            
            # Apply filters
            if filters:
                if filters.get('province'):
                    base_query = base_query.filter(Attraction.province == filters['province'])
                if filters.get('min_score'):
                    base_query = base_query.filter(Attraction.popularity_score >= filters['min_score'])
            
            # Order and paginate
            search_query = base_query.order_by(
                Attraction.popularity_score.desc(),
                Attraction.updated_at.desc()
            )
            
            paginated = search_query.paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            
            return {
                'attractions': [attraction.to_dict() for attraction in paginated.items],
                'total': paginated.total,
                'pages': paginated.pages,
                'current_page': page,
                'per_page': per_page,
                'query': query,
                'filters': filters or {}
            }
            
        except Exception as e:
            logger.error(f"Error in simple search: {str(e)}")
            return {
                'attractions': [],
                'total': 0,
                'pages': 0,
                'current_page': page,
                'per_page': per_page,
                'query': query,
                'error': str(e)
            }
    
    @staticmethod
    @cached_query(timeout=600, key_prefix="recommendations")
    def get_recommendations(attraction_id: int, limit: int = 5) -> List[Dict]:
        """
        Get recommended attractions based on similarity.
        Uses content-based filtering.
        """
        try:
            # Get the reference attraction
            reference = Attraction.query.get(attraction_id)
            if not reference:
                return []
            
            # Get reference categories
            ref_categories = []
            if reference.ai_tags:
                try:
                    ref_categories = json.loads(reference.ai_tags)
                except:
                    ref_categories = []
            
            # Find similar attractions
            candidates = Attraction.query.filter(
                Attraction.id != attraction_id,
                Attraction.ai_processed == True
            ).all()
            
            # Calculate similarity scores
            recommendations = []
            for candidate in candidates:
                similarity_score = SearchService._calculate_similarity(
                    reference, candidate, ref_categories
                )
                
                if similarity_score > 0.3:  # Minimum similarity threshold
                    rec_dict = candidate.to_dict()
                    rec_dict['similarity_score'] = similarity_score
                    recommendations.append(rec_dict)
            
            # Sort by similarity and popularity
            recommendations.sort(
                key=lambda x: (x['similarity_score'], x['popularity_score']), 
                reverse=True
            )
            
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Error getting recommendations: {str(e)}")
            return []
    
    @staticmethod
    def _calculate_similarity(ref_attraction: Attraction, candidate: Attraction, 
                            ref_categories: List[str]) -> float:
        """Calculate similarity between two attractions."""
        try:
            similarity = 0.0
            
            # Category similarity
            candidate_categories = []
            if candidate.ai_tags:
                try:
                    candidate_categories = json.loads(candidate.ai_tags)
                except:
                    candidate_categories = []
            
            if ref_categories and candidate_categories:
                common_categories = set(ref_categories) & set(candidate_categories)
                category_similarity = len(common_categories) / max(len(ref_categories), len(candidate_categories))
                similarity += category_similarity * 0.5
            
            # Province similarity
            if ref_attraction.province and candidate.province:
                if ref_attraction.province == candidate.province:
                    similarity += 0.3
            
            # Popularity similarity
            if ref_attraction.popularity_score and candidate.popularity_score:
                score_diff = abs(ref_attraction.popularity_score - candidate.popularity_score)
                popularity_similarity = max(0, 1 - score_diff / 10)  # Normalize to 0-1
                similarity += popularity_similarity * 0.2
            
            return round(similarity, 3)
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {str(e)}")
            return 0.0
    
    @staticmethod
    @cached_query(timeout=1800, key_prefix="trending")
    def get_trending_attractions(period: str = 'week', limit: int = 10) -> List[Dict]:
        """
        Get trending attractions based on recent activity.
        
        Args:
            period: 'day', 'week', or 'month'
            limit: Number of results to return
        """
        try:
            from datetime import datetime, timedelta
            
            # Calculate date range
            now = datetime.utcnow()
            if period == 'day':
                since = now - timedelta(days=1)
            elif period == 'week':
                since = now - timedelta(weeks=1)
            elif period == 'month':
                since = now - timedelta(days=30)
            else:
                since = now - timedelta(weeks=1)  # Default to week
            
            # Query trending attractions
            trending_query = Attraction.query.filter(
                Attraction.updated_at >= since,
                Attraction.ai_processed == True,
                Attraction.popularity_score > 0
            ).order_by(
                Attraction.popularity_score.desc(),
                Attraction.updated_at.desc()
            ).limit(limit)
            
            results = []
            for attraction in trending_query.all():
                attraction_dict = attraction.to_dict()
                # Add trending score based on recency and popularity
                days_old = (now - attraction.updated_at).days + 1
                trending_score = attraction.popularity_score / days_old
                attraction_dict['trending_score'] = round(trending_score, 2)
                results.append(attraction_dict)
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting trending attractions: {str(e)}")
            return []
    
    @staticmethod
    def get_search_suggestions(query: str, limit: int = 5) -> List[str]:
        """Get search suggestions based on existing attraction titles."""
        try:
            if len(query) < 2:
                return []
            
            # Search for attractions with similar titles
            suggestions = db.session.query(Attraction.title).filter(
                Attraction.title.ilike(f'%{query}%')
            ).distinct().limit(limit).all()
            
            return [suggestion[0] for suggestion in suggestions]
            
        except Exception as e:
            logger.error(f"Error getting search suggestions: {str(e)}")
            return []


def get_search_service() -> SearchService:
    """Get search service instance."""
    return SearchService()