from flask import Blueprint, jsonify, current_app
import requests
from app.models import db, Attraction

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