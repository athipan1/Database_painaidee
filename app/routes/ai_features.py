"""
AI-powered features routes for the attractions API.
"""
from flask import Blueprint, request, jsonify
from app.models import db, Attraction, UserInteraction, ConversationSession
from app.services.keyword_extraction import (
    extract_keywords_from_attraction, 
    keywords_to_json,
    keywords_from_json
)
from app.services.recommendation import (
    get_user_recommendations,
    record_interaction
)
from app.services.trend_analysis import (
    analyze_attraction_trends,
    get_heatmap_data,
    get_trend_predictions
)
from app.services.content_rewriter import (
    improve_attraction_content,
    get_content_suggestions,
    calculate_content_readability
)
from app.services.conversational_ai import (
    detect_user_intent,
    generate_smart_query,
    create_conversation_session,
    get_contextual_response,
    update_session_preferences
)

ai_bp = Blueprint('ai', __name__)


@ai_bp.route('/keywords/extract', methods=['POST'])
def extract_keywords():
    """Extract keywords from attraction data."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Extract keywords from provided text or attraction ID
    if 'attraction_id' in data:
        attraction = Attraction.query.get(data['attraction_id'])
        if not attraction:
            return jsonify({'error': 'Attraction not found'}), 404
        
        attraction_data = {
            'title': attraction.title,
            'body': attraction.body
        }
        keywords = extract_keywords_from_attraction(attraction_data)
        
        # Update attraction with extracted keywords
        attraction.keywords = keywords_to_json(keywords)
        attraction.keywords_extracted = True
        db.session.commit()
        
        return jsonify({
            'attraction_id': attraction.id,
            'keywords': keywords,
            'success': True
        })
    
    elif 'text' in data:
        # Extract keywords from provided text
        attraction_data = {'title': '', 'body': data['text']}
        keywords = extract_keywords_from_attraction(attraction_data)
        
        return jsonify({
            'text': data['text'],
            'keywords': keywords,
            'success': True
        })
    
    else:
        return jsonify({'error': 'Either attraction_id or text must be provided'}), 400


@ai_bp.route('/keywords/batch-extract', methods=['POST'])
def batch_extract_keywords():
    """Extract keywords for multiple attractions."""
    data = request.get_json()
    
    if not data or 'attraction_ids' not in data:
        return jsonify({'error': 'attraction_ids list is required'}), 400
    
    attraction_ids = data['attraction_ids']
    results = []
    
    for attraction_id in attraction_ids:
        try:
            attraction = Attraction.query.get(attraction_id)
            if not attraction:
                results.append({
                    'attraction_id': attraction_id,
                    'success': False,
                    'error': 'Attraction not found'
                })
                continue
            
            attraction_data = {
                'title': attraction.title,
                'body': attraction.body
            }
            keywords = extract_keywords_from_attraction(attraction_data)
            
            # Update attraction
            attraction.keywords = keywords_to_json(keywords)
            attraction.keywords_extracted = True
            
            results.append({
                'attraction_id': attraction_id,
                'keywords': keywords,
                'success': True
            })
            
        except Exception as e:
            results.append({
                'attraction_id': attraction_id,
                'success': False,
                'error': str(e)
            })
    
    db.session.commit()
    
    return jsonify({
        'results': results,
        'total_processed': len(results),
        'successful': len([r for r in results if r['success']])
    })


@ai_bp.route('/recommendations/<user_id>', methods=['GET'])
def get_recommendations(user_id):
    """Get personalized recommendations for a user."""
    try:
        num_recommendations = request.args.get('limit', 10, type=int)
        exclude_viewed = request.args.get('exclude_viewed', 'true').lower() == 'true'
        
        recommendations = get_user_recommendations(
            user_id=user_id,
            num_recommendations=num_recommendations
        )
        
        return jsonify({
            'user_id': user_id,
            'recommendations': recommendations,
            'count': len(recommendations)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/interactions', methods=['POST'])
def record_user_interaction():
    """Record a user interaction for recommendation learning."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    required_fields = ['user_id', 'attraction_id']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'user_id and attraction_id are required'}), 400
    
    try:
        success = record_interaction(
            user_id=data['user_id'],
            attraction_id=data['attraction_id'],
            interaction_type=data.get('interaction_type', 'view')
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Interaction recorded successfully'
            })
        else:
            return jsonify({'error': 'Failed to record interaction'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/trends/analyze', methods=['GET'])
def analyze_trends():
    """Analyze attraction popularity trends."""
    try:
        days = request.args.get('days', 30, type=int)
        province = request.args.get('province')
        
        trends = analyze_attraction_trends(days=days, province=province)
        
        return jsonify(trends)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/trends/heatmap', methods=['GET'])
def get_heatmap():
    """Get heatmap data for geographic visualization."""
    try:
        days = request.args.get('days', 30, type=int)
        
        heatmap_data = get_heatmap_data(days=days)
        
        return jsonify(heatmap_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/trends/predictions', methods=['GET'])
def get_predictions():
    """Get future trend predictions."""
    try:
        days_ahead = request.args.get('days_ahead', 7, type=int)
        
        predictions = get_trend_predictions(days_ahead=days_ahead)
        
        return jsonify(predictions)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/content/improve', methods=['POST'])
def improve_content():
    """Improve attraction content using AI."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    if 'attraction_id' in data:
        # Improve content for specific attraction
        attraction = Attraction.query.get(data['attraction_id'])
        if not attraction:
            return jsonify({'error': 'Attraction not found'}), 404
        
        # Choose which field to improve
        field_to_improve = data.get('field', 'body')  # 'title' or 'body'
        
        if field_to_improve == 'title':
            original_text = attraction.title
        else:
            original_text = attraction.body
        
        if not original_text:
            return jsonify({'error': f'No {field_to_improve} content to improve'}), 400
        
        style = data.get('style', 'friendly')
        max_length = data.get('max_length', 500)
        
        result = improve_attraction_content(
            text=original_text,
            style=style,
            max_length=max_length
        )
        
        # Optionally update the attraction if requested
        if data.get('apply_changes', False) and result['success']:
            if field_to_improve == 'title':
                attraction.title = result['improved_text']
            else:
                attraction.body = result['improved_text']
            
            attraction.content_rewritten = True
            db.session.commit()
        
        result['attraction_id'] = attraction.id
        result['field'] = field_to_improve
        result['changes_applied'] = data.get('apply_changes', False)
        
        return jsonify(result)
    
    elif 'text' in data:
        # Improve provided text
        style = data.get('style', 'friendly')
        max_length = data.get('max_length', 500)
        
        result = improve_attraction_content(
            text=data['text'],
            style=style,
            max_length=max_length
        )
        
        return jsonify(result)
    
    else:
        return jsonify({'error': 'Either attraction_id or text must be provided'}), 400


@ai_bp.route('/content/suggestions', methods=['POST'])
def get_content_improvement_suggestions():
    """Get suggestions for improving attraction content."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    if 'attraction_id' in data:
        attraction = Attraction.query.get(data['attraction_id'])
        if not attraction:
            return jsonify({'error': 'Attraction not found'}), 404
        
        field = data.get('field', 'body')
        text = attraction.title if field == 'title' else attraction.body
        
        if not text:
            return jsonify({'error': f'No {field} content to analyze'}), 400
        
        suggestions = get_content_suggestions(text)
        readability = calculate_content_readability(text)
        
        return jsonify({
            'attraction_id': attraction.id,
            'field': field,
            'suggestions': suggestions,
            'readability': readability
        })
    
    elif 'text' in data:
        text = data['text']
        suggestions = get_content_suggestions(text)
        readability = calculate_content_readability(text)
        
        return jsonify({
            'suggestions': suggestions,
            'readability': readability
        })
    
    else:
        return jsonify({'error': 'Either attraction_id or text must be provided'}), 400


@ai_bp.route('/content/batch-improve', methods=['POST'])
def batch_improve_content():
    """Improve content for multiple attractions."""
    data = request.get_json()
    
    if not data or 'attraction_ids' not in data:
        return jsonify({'error': 'attraction_ids list is required'}), 400
    
    attraction_ids = data['attraction_ids']
    field = data.get('field', 'body')
    style = data.get('style', 'friendly')
    apply_changes = data.get('apply_changes', False)
    
    results = []
    
    for attraction_id in attraction_ids:
        try:
            attraction = Attraction.query.get(attraction_id)
            if not attraction:
                results.append({
                    'attraction_id': attraction_id,
                    'success': False,
                    'error': 'Attraction not found'
                })
                continue
            
            original_text = attraction.title if field == 'title' else attraction.body
            
            if not original_text:
                results.append({
                    'attraction_id': attraction_id,
                    'success': False,
                    'error': f'No {field} content to improve'
                })
                continue
            
            result = improve_attraction_content(
                text=original_text,
                style=style,
                max_length=500
            )
            
            # Apply changes if requested and improvement was successful
            if apply_changes and result['success']:
                if field == 'title':
                    attraction.title = result['improved_text']
                else:
                    attraction.body = result['improved_text']
                
                attraction.content_rewritten = True
            
            results.append({
                'attraction_id': attraction_id,
                'success': result['success'],
                'field': field,
                'improvements': result.get('improvements', []),
                'changes_applied': apply_changes and result['success']
            })
            
        except Exception as e:
            results.append({
                'attraction_id': attraction_id,
                'success': False,
                'error': str(e)
            })
    
    if apply_changes:
        db.session.commit()
    
    return jsonify({
        'results': results,
        'total_processed': len(results),
        'successful': len([r for r in results if r['success']]),
        'changes_applied': apply_changes
    })


@ai_bp.route('/stats', methods=['GET'])
def get_ai_stats():
    """Get AI feature usage statistics."""
    try:
        # Count attractions with AI features
        total_attractions = Attraction.query.count()
        with_keywords = Attraction.query.filter_by(keywords_extracted=True).count()
        with_improved_content = Attraction.query.filter_by(content_rewritten=True).count()
        
        # Count interactions
        total_interactions = UserInteraction.query.count()
        unique_users = UserInteraction.query.distinct(UserInteraction.user_id).count()
        
        # Count conversation sessions
        total_sessions = ConversationSession.query.count()
        active_sessions = ConversationSession.query.filter(
            ConversationSession.expires_at > db.func.now()
        ).count()
        
        return jsonify({
            'attractions': {
                'total': total_attractions,
                'with_keywords': with_keywords,
                'with_improved_content': with_improved_content,
                'keywords_coverage': round((with_keywords / total_attractions * 100), 2) if total_attractions > 0 else 0,
                'content_improvement_coverage': round((with_improved_content / total_attractions * 100), 2) if total_attractions > 0 else 0
            },
            'interactions': {
                'total': total_interactions,
                'unique_users': unique_users
            },
            'conversations': {
                'total_sessions': total_sessions,
                'active_sessions': active_sessions
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# New Conversational AI Endpoints

@ai_bp.route('/nlu/intent', methods=['POST'])
def detect_intent():
    """Detect user intent from natural language text."""
    # Handle both JSON and form data
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict() if request.form else {}
    
    if not data or 'text' not in data:
        return jsonify({'error': 'Text field is required'}), 400
    
    try:
        text = data['text']
        intent_result = detect_user_intent(text)
        
        return jsonify({
            'success': True,
            'intent': intent_result['intent'],
            'confidence': intent_result['confidence'],
            'entities': intent_result['entities'],
            'all_intents': intent_result.get('all_intents', {}),
            'original_text': text
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/search/from-text', methods=['POST'])
def search_from_text():
    """Generate smart search query from natural language text."""
    # Handle both JSON and form data
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict() if request.form else {}
    
    if not data or 'text' not in data:
        return jsonify({'error': 'Text field is required'}), 400
    
    try:
        text = data['text']
        session_id = data.get('session_id')
        
        # Generate smart query
        query_result = generate_smart_query(text, session_id)
        
        return jsonify({
            'success': True,
            'intent': query_result['intent'],
            'query_params': query_result['query_params'],
            'results': query_result['results'],
            'total_results': query_result['total_results'],
            'session_id': query_result['session_id']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/conversation/session', methods=['POST'])
def create_session():
    """Create a new conversation session."""
    # Handle both JSON and form data
    if request.is_json:
        data = request.get_json() or {}
    else:
        data = request.form.to_dict() if request.form else {}
    
    try:
        user_id = data.get('user_id')
        session_id = create_conversation_session(user_id)
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'expires_in_hours': 24
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/conversation/chat', methods=['POST'])
def conversational_chat():
    """Main conversational chat endpoint with context awareness."""
    # Handle both JSON and form data
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict() if request.form else {}
    
    if not data or 'text' not in data:
        return jsonify({'error': 'Text field is required'}), 400
    
    try:
        text = data['text']
        session_id = data.get('session_id')
        
        # If no session provided, create one
        if not session_id:
            session_id = create_conversation_session()
        
        # Get contextual response
        response = get_contextual_response(session_id, text)
        
        return jsonify({
            'success': True,
            'session_id': response['session_id'],
            'message': response['response_message'],
            'intent': response['query_result']['intent'],
            'results': response['query_result']['results'],
            'total_results': response['query_result']['total_results'],
            'context_updated': response['context_updated']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/conversation/preferences', methods=['POST'])
def update_preferences():
    """Update user preferences for a conversation session."""
    # Handle both JSON and form data
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict() if request.form else {}
    
    if not data or 'session_id' not in data or 'preferences' not in data:
        return jsonify({'error': 'session_id and preferences are required'}), 400
    
    try:
        session_id = data['session_id']
        preferences = data['preferences']
        
        success = update_session_preferences(session_id, preferences)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Preferences updated successfully'
            })
        else:
            return jsonify({'error': 'Failed to update preferences or session not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/conversation/session/<session_id>', methods=['GET'])
def get_session_info(session_id):
    """Get information about a conversation session."""
    try:
        from app.services.conversational_ai import context_engine
        session_context = context_engine.get_session_context(session_id)
        
        if not session_context:
            return jsonify({'error': 'Session not found or expired'}), 404
        
        return jsonify({
            'success': True,
            'session': session_context
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500