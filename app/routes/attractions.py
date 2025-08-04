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


@attractions_bp.route('/attractions/sync/tat', methods=['POST'])
def sync_tat_attractions():
    """Manually trigger TAT Open Data attraction sync from CSV using ETL pipeline."""
    from flask import request
    
    try:
        # Get request parameters
        data = request.get_json() or {}
        csv_url = data.get('csv_url', "https://opendata.tourismthailand.org/data/attractions.csv")
        enable_geocoding = data.get('enable_geocoding', False)
        
        # Get configuration
        timeout = current_app.config.get('API_TIMEOUT', 60)
        google_api_key = current_app.config.get('GOOGLE_GEOCODING_API_KEY') if enable_geocoding else None
        
        current_app.logger.info(f"Starting TAT CSV sync from URL: {csv_url}")
        
        # Import here to avoid circular imports
        from etl_orchestrator import ETLOrchestrator
        
        # Run TAT CSV ETL process
        result = ETLOrchestrator.run_tat_csv_etl(
            csv_url=csv_url,
            timeout=timeout,
            enable_geocoding=enable_geocoding,
            google_api_key=google_api_key
        )
        
        return jsonify({
            'success': True,
            'message': 'TAT CSV ETL sync completed',
            'csv_url': csv_url,
            'geocoding_enabled': enable_geocoding,
            'saved': result.get('saved', 0),
            'updated': result.get('updated', 0),
            'skipped': result.get('skipped', 0),
            'errors': result.get('errors', 0),
            'total_processed': result.get('total_processed', 0)
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in TAT CSV ETL sync: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to sync TAT attractions: {str(e)}'
        }), 500


@attractions_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'success': True,
        'message': 'API is healthy',
        'database_connected': True
    })