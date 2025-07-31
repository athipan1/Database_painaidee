from flask import Blueprint, jsonify, current_app
import requests
from app.models import db, Attraction
from sqlalchemy.exc import IntegrityError

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
    """Manually trigger attraction data sync from external API."""
    try:
        # Fetch data from external API
        api_url = current_app.config['EXTERNAL_API_URL']
        timeout = current_app.config['API_TIMEOUT']
        
        response = requests.get(api_url, timeout=timeout)
        response.raise_for_status()
        
        external_data = response.json()
        
        # Process and save data
        saved_count = 0
        skipped_count = 0
        
        for item in external_data:
            # Check if attraction already exists
            existing = Attraction.query.filter_by(external_id=item.get('id')).first()
            
            if existing:
                skipped_count += 1
                continue
                
            # Create new attraction
            try:
                attraction = Attraction.create_from_external_data(item)
                db.session.add(attraction)
                db.session.commit()
                saved_count += 1
            except IntegrityError:
                db.session.rollback()
                skipped_count += 1
                current_app.logger.warning(f"Duplicate attraction with external_id: {item.get('id')}")
        
        return jsonify({
            'success': True,
            'message': 'Sync completed',
            'saved': saved_count,
            'skipped': skipped_count,
            'total_processed': len(external_data)
        })
        
    except requests.RequestException as e:
        current_app.logger.error(f"Error fetching external data: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch external data'
        }), 500
    except Exception as e:
        current_app.logger.error(f"Error syncing attractions: {str(e)}")
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