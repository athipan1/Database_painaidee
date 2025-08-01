from flask import Blueprint, jsonify, current_app, request
import requests
from app.models import db, Attraction
from app.services.cache_service import cached_api, CacheService
from app.services.search_service import SearchService
from app.services.ai_service import get_ai_service

attractions_bp = Blueprint('attractions', __name__)


@attractions_bp.route('/attractions', methods=['GET'])
@cached_api(timeout=600, key_prefix="attractions_list")
def get_attractions():
    """Get all attractions from database with pagination and filtering."""
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        province = request.args.get('province')
        min_score = request.args.get('min_score', type=float)
        ai_processed = request.args.get('ai_processed', type=bool)
        
        # Build query
        query = Attraction.query
        
        # Apply filters
        if province:
            query = query.filter(Attraction.province == province)
        if min_score is not None:
            query = query.filter(Attraction.popularity_score >= min_score)
        if ai_processed is not None:
            query = query.filter(Attraction.ai_processed == ai_processed)
        
        # Order by popularity and recency
        query = query.order_by(
            Attraction.popularity_score.desc(),
            Attraction.updated_at.desc()
        )
        
        # Paginate
        paginated = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': [attraction.to_dict() for attraction in paginated.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': paginated.total,
                'pages': paginated.pages
            },
            'filters': {
                'province': province,
                'min_score': min_score,
                'ai_processed': ai_processed
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error fetching attractions: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch attractions'
        }), 500


@attractions_bp.route('/attractions/<int:attraction_id>', methods=['GET'])
@cached_api(timeout=900, key_prefix="attraction_detail")
def get_attraction(attraction_id):
    """Get a specific attraction by ID."""
    try:
        attraction = Attraction.query.get_or_404(attraction_id)
        
        return jsonify({
            'success': True,
            'data': attraction.to_dict()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error fetching attraction {attraction_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch attraction'
        }), 500


@attractions_bp.route('/attractions/search', methods=['GET'])
@cached_api(timeout=300, key_prefix="attractions_search")
def search_attractions():
    """Search attractions with full-text search."""
    try:
        # Get query parameters
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({
                'success': False,
                'error': 'Search query is required'
            }), 400
        
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        # Build filters
        filters = {}
        if request.args.get('province'):
            filters['province'] = request.args.get('province')
        if request.args.get('min_score'):
            filters['min_score'] = float(request.args.get('min_score'))
        if request.args.get('categories'):
            filters['categories'] = request.args.get('categories').split(',')
        
        # Perform search
        search_service = SearchService()
        results = search_service.full_text_search(
            query=query,
            page=page,
            per_page=per_page,
            filters=filters
        )
        
        return jsonify({
            'success': True,
            'data': results['attractions'],
            'pagination': {
                'page': results['current_page'],
                'per_page': results['per_page'],
                'total': results['total'],
                'pages': results['pages']
            },
            'search': {
                'query': results['query'],
                'filters': results['filters']
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error searching attractions: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to search attractions'
        }), 500


@attractions_bp.route('/attractions/<int:attraction_id>/recommendations', methods=['GET'])
@cached_api(timeout=1800, key_prefix="attraction_recommendations")
def get_recommendations(attraction_id):
    """Get recommendations for a specific attraction."""
    try:
        limit = min(request.args.get('limit', 5, type=int), 20)
        
        search_service = SearchService()
        recommendations = search_service.get_recommendations(
            attraction_id=attraction_id,
            limit=limit
        )
        
        return jsonify({
            'success': True,
            'data': recommendations,
            'count': len(recommendations),
            'attraction_id': attraction_id
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting recommendations for {attraction_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get recommendations'
        }), 500


@attractions_bp.route('/attractions/trending', methods=['GET'])
@cached_api(timeout=900, key_prefix="attractions_trending")
def get_trending():
    """Get trending attractions."""
    try:
        period = request.args.get('period', 'week')
        limit = min(request.args.get('limit', 10, type=int), 50)
        
        if period not in ['day', 'week', 'month']:
            period = 'week'
        
        search_service = SearchService()
        trending = search_service.get_trending_attractions(
            period=period,
            limit=limit
        )
        
        return jsonify({
            'success': True,
            'data': trending,
            'count': len(trending),
            'period': period
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting trending attractions: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get trending attractions'
        }), 500


@attractions_bp.route('/attractions/suggestions', methods=['GET'])
def get_search_suggestions():
    """Get search suggestions based on query."""
    try:
        query = request.args.get('q', '').strip()
        if not query or len(query) < 2:
            return jsonify({
                'success': True,
                'data': [],
                'message': 'Query too short'
            })
        
        limit = min(request.args.get('limit', 5, type=int), 10)
        
        # Check cache first
        cached_suggestions = CacheService.get_cached_search_suggestions(query)
        if cached_suggestions:
            return jsonify({
                'success': True,
                'data': cached_suggestions[:limit],
                'cached': True
            })
        
        # Get suggestions
        search_service = SearchService()
        suggestions = search_service.get_search_suggestions(query, limit)
        
        # Cache suggestions
        CacheService.cache_search_suggestions(query, suggestions)
        
        return jsonify({
            'success': True,
            'data': suggestions,
            'cached': False
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting search suggestions: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get suggestions'
        }), 500


@attractions_bp.route('/attractions/stats', methods=['GET'])
@cached_api(timeout=1800, key_prefix="attractions_stats")
def get_stats():
    """Get attraction statistics."""
    try:
        # Basic stats
        total_attractions = Attraction.query.count()
        ai_processed = Attraction.query.filter(Attraction.ai_processed == True).count()
        geocoded = Attraction.query.filter(Attraction.geocoded == True).count()
        
        # Province distribution
        province_stats = db.session.query(
            Attraction.province,
            db.func.count(Attraction.id).label('count')
        ).filter(
            Attraction.province.isnot(None)
        ).group_by(Attraction.province).all()
        
        # Category distribution (from AI tags)
        category_stats = {}
        attractions_with_tags = Attraction.query.filter(
            Attraction.ai_tags.isnot(None)
        ).all()
        
        for attraction in attractions_with_tags:
            try:
                import json
                tags = json.loads(attraction.ai_tags)
                for tag in tags:
                    category_stats[tag] = category_stats.get(tag, 0) + 1
            except:
                continue
        
        return jsonify({
            'success': True,
            'data': {
                'total_attractions': total_attractions,
                'ai_processed': ai_processed,
                'ai_processed_percentage': round((ai_processed / total_attractions * 100), 2) if total_attractions > 0 else 0,
                'geocoded': geocoded,
                'geocoded_percentage': round((geocoded / total_attractions * 100), 2) if total_attractions > 0 else 0,
                'provinces': [{'province': p.province, 'count': p.count} for p in province_stats],
                'categories': category_stats
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting attraction stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get statistics'
        }), 500


@attractions_bp.route('/attractions/process-ai', methods=['POST'])
def process_ai():
    """Manually trigger AI processing for attractions."""
    try:
        # Import here to avoid circular imports
        from tasks import process_attractions_ai_task
        
        # Trigger AI processing task
        task = process_attractions_ai_task.delay()
        
        return jsonify({
            'success': True,
            'message': 'AI processing task started',
            'task_id': task.id
        })
        
    except Exception as e:
        current_app.logger.error(f"Error triggering AI processing: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to start AI processing'
        }), 500


@attractions_bp.route('/attractions/cache/clear', methods=['POST'])
def clear_cache():
    """Clear attraction-related cache."""
    try:
        attraction_id = request.json.get('attraction_id') if request.is_json else None
        
        CacheService.invalidate_attraction_cache(attraction_id)
        
        return jsonify({
            'success': True,
            'message': f'Cache cleared for attraction {attraction_id}' if attraction_id else 'All attraction cache cleared'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error clearing cache: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to clear cache'
        }), 500


@attractions_bp.route('/attractions/cache/preload', methods=['POST'])
def preload_cache():
    """Preload frequently accessed data into cache."""
    try:
        # Import here to avoid circular imports
        from tasks import preload_cache_task
        
        # Trigger cache preload task
        task = preload_cache_task.delay()
        
        return jsonify({
            'success': True,
            'message': 'Cache preload task started',
            'task_id': task.id
        })
        
    except Exception as e:
        current_app.logger.error(f"Error preloading cache: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to preload cache'
        }), 500


@attractions_bp.route('/attractions', methods=['GET'])
def get_attractions():
    """Get all attractions from database."""
    try:
        attractions = Attraction.query.all()
        return jsonify({
            'success': True,
            'data': [attraction.to_dict() for attraction in attractions],
            'count': len(attractions)
        })
    except Exception as e:
        current_app.logger.error(f"Error fetching attractions: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch attractions'
        }), 500


@attractions_bp.route('/attractions/sync', methods=['POST'])
def sync_attractions():
    """Manually trigger attraction data sync from external API using ETL pipeline."""
    try:
        # Get configuration
        api_url = current_app.config['EXTERNAL_API_URL']
        timeout = current_app.config['API_TIMEOUT']
        
        # Get pagination settings
        enable_pagination = current_app.config.get('PAGINATION_ENABLED', True)
        page_size = current_app.config.get('PAGINATION_PAGE_SIZE', 20)
        max_pages = current_app.config.get('PAGINATION_MAX_PAGES', 100)
        
        # Import here to avoid circular imports
        from etl_orchestrator import ETLOrchestrator
        
        # Run ETL process using orchestrator with pagination
        result = ETLOrchestrator.run_external_api_etl(
            api_url=api_url,
            timeout=timeout,
            enable_pagination=enable_pagination,
            page_size=page_size,
            max_pages=max_pages,
            use_memory_efficient=enable_pagination  # Use memory efficient mode when pagination is enabled
        )
        
        return jsonify({
            'success': True,
            'message': 'ETL sync completed',
            'saved': result['saved'],
            'skipped': result['skipped'],
            'total_processed': result['total_processed'],
            'pagination_used': result.get('pagination_used', False),
            'memory_efficient': result.get('memory_efficient', False)
        })
        
    except requests.RequestException as e:
        current_app.logger.error(f"Error in ETL process after retries: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch external data after multiple retry attempts'
        }), 500
    except Exception as e:
        current_app.logger.error(f"Error in ETL sync: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to sync attractions'
        }), 500


@attractions_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'success': True,
        'message': 'API is healthy',
        'database_connected': True
    })