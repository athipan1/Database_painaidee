from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
from app.models import db, UserInteraction, UserBehaviorSession, SearchQuery, UserPreference
from app.services.behavior_intelligence import BehaviorIntelligenceService
from app.services.recommendation import RecommendationEngine
from app.services.trend_analysis import TrendAnalyzer

behavior_bp = Blueprint('behavior_intelligence', __name__)

# Initialize services
behavior_service = BehaviorIntelligenceService()
recommendation_engine = RecommendationEngine()
trend_analyzer = TrendAnalyzer()


@behavior_bp.route('/behavior/track', methods=['POST'])
def track_behavior():
    """
    Track user behavior interaction.
    ติดตามพฤติกรรมผู้ใช้: การคลิก, การค้นหา, การกด Favorite, เวลาเข้าเยี่ยมชม, และระยะเวลาที่ใช้
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('user_id'):
            return jsonify({
                'success': False,
                'error': 'User ID is required'
            }), 400
        
        result = behavior_service.track_interaction(
            user_id=data['user_id'],
            attraction_id=data.get('attraction_id'),
            interaction_type=data.get('interaction_type', 'view'),
            duration_seconds=data.get('duration_seconds'),
            search_query=data.get('search_query'),
            page_url=data.get('page_url'),
            session_id=data.get('session_id')
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        current_app.logger.error(f"Error tracking behavior: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to track behavior'
        }), 500


@behavior_bp.route('/behavior/analyze/<user_id>', methods=['GET'])
def analyze_user_behavior(user_id):
    """
    Analyze user behavior patterns.
    การวิเคราะห์แนวโน้มพฤติกรรมของผู้ใช้อย่าง dynamic
    """
    try:
        days = request.args.get('days', 30, type=int)
        
        analysis = behavior_service.analyze_user_behavior(user_id, days)
        
        return jsonify({
            'success': True,
            'data': analysis
        })
        
    except Exception as e:
        current_app.logger.error(f"Error analyzing behavior: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to analyze behavior'
        }), 500


@behavior_bp.route('/behavior/recommendations/<user_id>', methods=['GET'])
def get_real_time_recommendations(user_id):
    """
    Get real-time personalized recommendations.
    ระบบแนะนำแบบ Real-time: ใช้ข้อมูลที่วิเคราะห์เพื่อสร้างคำแนะนำแบบเรียลไทม์
    """
    try:
        num_recommendations = request.args.get('limit', 10, type=int)
        
        # Get current context from query parameters
        current_context = {}
        if request.args.get('search_query'):
            current_context['search_query'] = request.args.get('search_query')
        if request.args.get('province'):
            current_context['province'] = request.args.get('province')
        if request.args.get('category'):
            current_context['category'] = request.args.get('category')
        
        recommendations = behavior_service.get_real_time_recommendations(
            user_id=user_id,
            current_context=current_context if current_context else None,
            num_recommendations=num_recommendations
        )
        
        return jsonify({
            'success': True,
            'data': recommendations,
            'count': len(recommendations),
            'user_id': user_id,
            'context': current_context
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting recommendations: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get recommendations'
        }), 500


@behavior_bp.route('/behavior/session/<session_id>/end', methods=['POST'])
def end_session(session_id):
    """End a user behavior session."""
    try:
        success = behavior_service.end_session(session_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Session ended successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Session not found'
            }), 404
            
    except Exception as e:
        current_app.logger.error(f"Error ending session: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to end session'
        }), 500


@behavior_bp.route('/behavior/trends', methods=['GET'])
def get_behavior_trends():
    """
    Get behavioral trends and analytics.
    การวิเคราะห์แนวโน้มพฤติกรรมแบบ dynamic
    """
    try:
        days = request.args.get('days', 30, type=int)
        province = request.args.get('province')
        
        trends = trend_analyzer.analyze_popularity_trends(days, province)
        
        return jsonify({
            'success': True,
            'data': trends
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting trends: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get trends'
        }), 500


@behavior_bp.route('/behavior/heatmap', methods=['GET'])
def get_behavior_heatmap():
    """Get behavior heatmap data for geographic visualization."""
    try:
        days = request.args.get('days', 30, type=int)
        grid_size = request.args.get('grid_size', 20, type=int)
        
        heatmap_data = trend_analyzer.generate_heatmap_data(days, grid_size)
        
        return jsonify({
            'success': True,
            'data': heatmap_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting heatmap: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get heatmap data'
        }), 500


@behavior_bp.route('/behavior/predictions', methods=['GET'])
def get_behavior_predictions():
    """Get future behavior trend predictions."""
    try:
        days_ahead = request.args.get('days_ahead', 7, type=int)
        
        predictions = trend_analyzer.predict_future_trends(days_ahead)
        
        return jsonify({
            'success': True,
            'data': predictions
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting predictions: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get predictions'
        }), 500


@behavior_bp.route('/behavior/sessions/<user_id>', methods=['GET'])
def get_user_sessions(user_id):
    """Get user behavior sessions."""
    try:
        days = request.args.get('days', 30, type=int)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        sessions = UserBehaviorSession.query.filter(
            UserBehaviorSession.user_id == user_id,
            UserBehaviorSession.created_at >= start_date
        ).order_by(UserBehaviorSession.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'data': [session.to_dict() for session in sessions],
            'count': len(sessions)
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting sessions: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get sessions'
        }), 500


@behavior_bp.route('/behavior/preferences/<user_id>', methods=['GET'])
def get_user_preferences(user_id):
    """Get learned user preferences."""
    try:
        preferences = UserPreference.query.filter_by(user_id=user_id).order_by(
            UserPreference.confidence_score.desc()
        ).all()
        
        # Group preferences by type
        grouped_preferences = {}
        for pref in preferences:
            if pref.preference_type not in grouped_preferences:
                grouped_preferences[pref.preference_type] = []
            
            grouped_preferences[pref.preference_type].append({
                'value': pref.preference_value,
                'confidence_score': pref.confidence_score,
                'interaction_count': pref.interaction_count,
                'last_interaction': pref.last_interaction.isoformat() if pref.last_interaction else None
            })
        
        return jsonify({
            'success': True,
            'data': grouped_preferences,
            'user_id': user_id
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting preferences: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get preferences'
        }), 500


@behavior_bp.route('/behavior/search-queries/<user_id>', methods=['GET'])
def get_user_search_queries(user_id):
    """Get user search query history."""
    try:
        days = request.args.get('days', 30, type=int)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        queries = SearchQuery.query.filter(
            SearchQuery.user_id == user_id,
            SearchQuery.created_at >= start_date
        ).order_by(SearchQuery.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'data': [query.to_dict() for query in queries],
            'count': len(queries)
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting search queries: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get search queries'
        }), 500


@behavior_bp.route('/behavior/stats', methods=['GET'])
def get_behavior_stats():
    """Get overall behavior statistics."""
    try:
        days = request.args.get('days', 30, type=int)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get interaction statistics
        total_interactions = UserInteraction.query.filter(
            UserInteraction.created_at >= start_date
        ).count()
        
        unique_users = db.session.query(UserInteraction.user_id).filter(
            UserInteraction.created_at >= start_date
        ).distinct().count()
        
        total_sessions = UserBehaviorSession.query.filter(
            UserBehaviorSession.created_at >= start_date
        ).count()
        
        total_searches = SearchQuery.query.filter(
            SearchQuery.created_at >= start_date
        ).count()
        
        # Get most popular interaction types
        interaction_types = db.session.query(
            UserInteraction.interaction_type,
            db.func.count(UserInteraction.id).label('count')
        ).filter(
            UserInteraction.created_at >= start_date
        ).group_by(UserInteraction.interaction_type).all()
        
        return jsonify({
            'success': True,
            'data': {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': days
                },
                'totals': {
                    'interactions': total_interactions,
                    'unique_users': unique_users,
                    'sessions': total_sessions,
                    'searches': total_searches
                },
                'interaction_types': [
                    {'type': it[0], 'count': it[1]} 
                    for it in interaction_types
                ]
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get statistics'
        }), 500