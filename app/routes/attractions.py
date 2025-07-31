from flask import Blueprint, jsonify, current_app, request
import requests
from app.models import db, Attraction, SyncLog
from app.utils.cache import cache_manager

attractions_bp = Blueprint('attractions', __name__)


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
    """Manually trigger attraction data sync from external API using enhanced ETL pipeline."""
    try:
        # Get configuration
        api_url = current_app.config['EXTERNAL_API_URL']
        timeout = current_app.config['API_TIMEOUT']
        
        # Get pagination settings
        enable_pagination = current_app.config.get('PAGINATION_ENABLED', True)
        page_size = current_app.config.get('PAGINATION_PAGE_SIZE', 20)
        max_pages = current_app.config.get('PAGINATION_MAX_PAGES', 100)
        
        # Get sync options from request
        sync_type = request.json.get('sync_type', 'manual') if request.is_json else 'manual'
        use_cache = request.json.get('use_cache', False) if request.is_json else False
        
        # Import here to avoid circular imports
        from etl_orchestrator import ETLOrchestrator
        
        # Run enhanced ETL process with sync logging
        result = ETLOrchestrator.run_external_api_etl(
            api_url=api_url,
            timeout=timeout,
            enable_pagination=enable_pagination,
            page_size=page_size,
            max_pages=max_pages,
            use_memory_efficient=enable_pagination,
            sync_type=sync_type,
            use_cache=use_cache
        )
        
        return jsonify({
            'success': True,
            'message': 'Enhanced ETL sync completed',
            'sync_id': result.get('sync_id'),
            'saved': result['saved'],
            'skipped': result['skipped'],
            'total_processed': result['total_processed'],
            'total_fetched': result.get('total_fetched', 0),
            'pagination_used': result.get('pagination_used', False),
            'memory_efficient': result.get('memory_efficient', False),
            'errors': result.get('errors', [])
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


@attractions_bp.route('/sync-logs', methods=['GET'])
def get_sync_logs():
    """Get sync operation history."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')  # Filter by status
        sync_type = request.args.get('sync_type')  # Filter by sync type
        
        query = SyncLog.query
        
        if status:
            query = query.filter_by(status=status)
        if sync_type:
            query = query.filter_by(sync_type=sync_type)
        
        # Order by most recent first
        query = query.order_by(SyncLog.created_at.desc())
        
        sync_logs = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': [log.to_dict() for log in sync_logs.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': sync_logs.total,
                'pages': sync_logs.pages,
                'has_next': sync_logs.has_next,
                'has_prev': sync_logs.has_prev
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error fetching sync logs: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch sync logs'
        }), 500


@attractions_bp.route('/sync-logs/<int:sync_id>', methods=['GET'])
def get_sync_log_detail(sync_id):
    """Get detailed information about a specific sync operation."""
    try:
        sync_log = SyncLog.query.get_or_404(sync_id)
        return jsonify({
            'success': True,
            'data': sync_log.to_dict()
        })
    except Exception as e:
        current_app.logger.error(f"Error fetching sync log {sync_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch sync log details'
        }), 500


@attractions_bp.route('/cache/stats', methods=['GET'])
def get_cache_stats():
    """Get cache statistics and status."""
    try:
        stats = cache_manager.get_cache_stats()
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        current_app.logger.error(f"Error fetching cache stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch cache statistics'
        }), 500


@attractions_bp.route('/cache/invalidate', methods=['POST'])
def invalidate_cache():
    """Invalidate API response cache."""
    try:
        # Get specific URL to invalidate from request body
        api_url = None
        if request.is_json and 'api_url' in request.json:
            api_url = request.json['api_url']
        
        result = cache_manager.invalidate_api_cache(api_url)
        
        return jsonify({
            'success': True,
            'message': f'Cache {"invalidated for specific URL" if api_url else "cleared completely"}',
            'invalidated': result
        })
        
    except Exception as e:
        current_app.logger.error(f"Error invalidating cache: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to invalidate cache'
        }), 500


@attractions_bp.route('/health', methods=['GET'])
def health_check():
    """Enhanced health check endpoint with cache and database status."""
    try:
        # Check database connection
        db_connected = True
        try:
            db.session.execute('SELECT 1')
        except Exception:
            db_connected = False
        
        # Check cache status
        cache_stats = cache_manager.get_cache_stats()
        
        return jsonify({
            'success': True,
            'message': 'API is healthy',
            'database_connected': db_connected,
            'cache_enabled': cache_stats.get('enabled', False),
            'cache_stats': cache_stats
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in health check: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Health check failed'
        }), 500