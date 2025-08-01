"""
API routes for AI Data Cleaning & Enrichment features.
"""
from flask import Blueprint, request, jsonify
from app.models import db, Attraction, DataValidationResult, AttractionTag, AttractionCategory
from app.services.data_validation import (
    validate_attraction_data, 
    validate_batch_attractions,
    get_validation_stats
)
from app.services.auto_tagging import (
    tag_attraction,
    tag_batch_attractions,
    get_tagging_stats,
    get_tag_suggestions_for_text
)
from app.services.category_suggestion import (
    suggest_categories_for_attraction,
    suggest_categories_batch,
    get_categorization_stats,
    get_category_suggestions_for_text
)
from app.services.geocoding import get_geocoding_service  # Existing service
import logging
import time

logger = logging.getLogger(__name__)

ai_cleaning_bp = Blueprint('ai_cleaning', __name__)


# Data Validation Endpoints
@ai_cleaning_bp.route('/data-cleaning/validate', methods=['POST'])
def validate_data():
    """Validate data for a specific attraction or batch of attractions."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Single attraction validation
        if 'attraction_id' in data:
            attraction_id = data['attraction_id']
            result = validate_attraction_data(attraction_id)
            
            if 'error' in result:
                return jsonify(result), 404
            
            return jsonify({
                'success': True,
                'message': 'Data validation completed',
                'result': result
            })
        
        # Batch validation
        elif 'attraction_ids' in data:
            attraction_ids = data['attraction_ids']
            
            if not isinstance(attraction_ids, list) or len(attraction_ids) == 0:
                return jsonify({'error': 'attraction_ids must be a non-empty list'}), 400
            
            if len(attraction_ids) > 100:
                return jsonify({'error': 'Maximum 100 attractions can be processed at once'}), 400
            
            result = validate_batch_attractions(attraction_ids)
            
            return jsonify({
                'success': True,
                'message': f'Batch validation completed. Processed: {result["processed"]}, Success: {result["successful"]}, Failed: {result["failed"]}',
                'result': result
            })
        
        else:
            return jsonify({'error': 'Either attraction_id or attraction_ids must be provided'}), 400
    
    except Exception as e:
        logger.error(f"Error in data validation endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@ai_cleaning_bp.route('/data-cleaning/validation-results/<int:attraction_id>', methods=['GET'])
def get_validation_results(attraction_id):
    """Get validation results for a specific attraction."""
    try:
        results = DataValidationResult.query.filter_by(attraction_id=attraction_id).all()
        
        if not results:
            return jsonify({
                'attraction_id': attraction_id,
                'validation_results': [],
                'message': 'No validation results found'
            })
        
        return jsonify({
            'attraction_id': attraction_id,
            'validation_results': [result.to_dict() for result in results]
        })
    
    except Exception as e:
        logger.error(f"Error getting validation results: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@ai_cleaning_bp.route('/data-cleaning/validation-stats', methods=['GET'])
def get_data_validation_stats():
    """Get overall data validation statistics."""
    try:
        stats = get_validation_stats()
        
        if 'error' in stats:
            return jsonify(stats), 500
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    
    except Exception as e:
        logger.error(f"Error getting validation stats: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


# Auto-Tagging Endpoints
@ai_cleaning_bp.route('/auto-tagging/generate', methods=['POST'])
def generate_tags():
    """Generate tags for a specific attraction or batch of attractions."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Single attraction tagging
        if 'attraction_id' in data:
            attraction_id = data['attraction_id']
            result = tag_attraction(attraction_id)
            
            if 'error' in result:
                return jsonify(result), 404
            
            return jsonify({
                'success': True,
                'message': f'Generated {result["tags_generated"]} tags for attraction',
                'result': result
            })
        
        # Batch tagging
        elif 'attraction_ids' in data:
            attraction_ids = data['attraction_ids']
            
            if not isinstance(attraction_ids, list) or len(attraction_ids) == 0:
                return jsonify({'error': 'attraction_ids must be a non-empty list'}), 400
            
            if len(attraction_ids) > 50:
                return jsonify({'error': 'Maximum 50 attractions can be processed at once'}), 400
            
            result = tag_batch_attractions(attraction_ids)
            
            return jsonify({
                'success': True,
                'message': f'Batch tagging completed. Generated {result["total_tags_generated"]} tags total.',
                'result': result
            })
        
        else:
            return jsonify({'error': 'Either attraction_id or attraction_ids must be provided'}), 400
    
    except Exception as e:
        logger.error(f"Error in auto-tagging endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@ai_cleaning_bp.route('/auto-tagging/tags/<int:attraction_id>', methods=['GET'])
def get_attraction_tags(attraction_id):
    """Get tags for a specific attraction."""
    try:
        tags = AttractionTag.query.filter_by(attraction_id=attraction_id).all()
        
        return jsonify({
            'attraction_id': attraction_id,
            'tags': [tag.to_dict() for tag in tags]
        })
    
    except Exception as e:
        logger.error(f"Error getting attraction tags: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@ai_cleaning_bp.route('/auto-tagging/suggest', methods=['POST'])
def suggest_tags_for_text():
    """Get tag suggestions for arbitrary text."""
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({'error': 'Text is required'}), 400
        
        text = data['text']
        
        if len(text.strip()) == 0:
            return jsonify({'error': 'Text cannot be empty'}), 400
        
        result = get_tag_suggestions_for_text(text)
        
        if 'error' in result:
            return jsonify(result), 500
        
        return jsonify({
            'success': True,
            'result': result
        })
    
    except Exception as e:
        logger.error(f"Error in tag suggestion endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@ai_cleaning_bp.route('/auto-tagging/stats', methods=['GET'])
def get_auto_tagging_stats():
    """Get overall auto-tagging statistics."""
    try:
        stats = get_tagging_stats()
        
        if 'error' in stats:
            return jsonify(stats), 500
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    
    except Exception as e:
        logger.error(f"Error getting tagging stats: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


# Category Suggestion Endpoints
@ai_cleaning_bp.route('/category-suggestion/generate', methods=['POST'])
def suggest_categories():
    """Generate category suggestions for a specific attraction or batch of attractions."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Single attraction categorization
        if 'attraction_id' in data:
            attraction_id = data['attraction_id']
            result = suggest_categories_for_attraction(attraction_id)
            
            if 'error' in result:
                return jsonify(result), 404
            
            return jsonify({
                'success': True,
                'message': f'Generated {result["categories_suggested"]} category suggestions',
                'result': result
            })
        
        # Batch categorization
        elif 'attraction_ids' in data:
            attraction_ids = data['attraction_ids']
            
            if not isinstance(attraction_ids, list) or len(attraction_ids) == 0:
                return jsonify({'error': 'attraction_ids must be a non-empty list'}), 400
            
            if len(attraction_ids) > 50:
                return jsonify({'error': 'Maximum 50 attractions can be processed at once'}), 400
            
            result = suggest_categories_batch(attraction_ids)
            
            return jsonify({
                'success': True,
                'message': f'Batch categorization completed. Generated {result["total_categories_suggested"]} suggestions total.',
                'result': result
            })
        
        else:
            return jsonify({'error': 'Either attraction_id or attraction_ids must be provided'}), 400
    
    except Exception as e:
        logger.error(f"Error in category suggestion endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@ai_cleaning_bp.route('/category-suggestion/categories/<int:attraction_id>', methods=['GET'])
def get_attraction_categories(attraction_id):
    """Get categories for a specific attraction."""
    try:
        categories = AttractionCategory.query.filter_by(attraction_id=attraction_id).all()
        
        return jsonify({
            'attraction_id': attraction_id,
            'categories': [category.to_dict() for category in categories]
        })
    
    except Exception as e:
        logger.error(f"Error getting attraction categories: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@ai_cleaning_bp.route('/category-suggestion/suggest', methods=['POST'])
def suggest_categories_for_text():
    """Get category suggestions for arbitrary text."""
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({'error': 'Text is required'}), 400
        
        text = data['text']
        
        if len(text.strip()) == 0:
            return jsonify({'error': 'Text cannot be empty'}), 400
        
        result = get_category_suggestions_for_text(text)
        
        if 'error' in result:
            return jsonify(result), 500
        
        return jsonify({
            'success': True,
            'result': result
        })
    
    except Exception as e:
        logger.error(f"Error in category suggestion endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@ai_cleaning_bp.route('/category-suggestion/stats', methods=['GET'])
def get_category_suggestion_stats():
    """Get overall categorization statistics."""
    try:
        stats = get_categorization_stats()
        
        if 'error' in stats:
            return jsonify(stats), 500
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    
    except Exception as e:
        logger.error(f"Error getting categorization stats: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


# Comprehensive Data Cleaning Endpoints
@ai_cleaning_bp.route('/data-cleaning/full-clean', methods=['POST'])
def full_data_cleaning():
    """
    Perform complete data cleaning & enrichment for attractions.
    Includes validation, tagging, categorization, and geocoding.
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Get attraction IDs
        if 'attraction_id' in data:
            attraction_ids = [data['attraction_id']]
        elif 'attraction_ids' in data:
            attraction_ids = data['attraction_ids']
            if not isinstance(attraction_ids, list) or len(attraction_ids) == 0:
                return jsonify({'error': 'attraction_ids must be a non-empty list'}), 400
        else:
            return jsonify({'error': 'Either attraction_id or attraction_ids must be provided'}), 400
        
        if len(attraction_ids) > 20:
            return jsonify({'error': 'Maximum 20 attractions can be processed at once for full cleaning'}), 400
        
        # Configuration options
        config = data.get('config', {})
        enable_validation = config.get('enable_validation', True)
        enable_tagging = config.get('enable_tagging', True)
        enable_categorization = config.get('enable_categorization', True)
        enable_geocoding = config.get('enable_geocoding', True)
        
        results = {
            'processed_attractions': len(attraction_ids),
            'validation_results': None,
            'tagging_results': None,
            'categorization_results': None,
            'geocoding_results': {'processed': 0, 'successful': 0},
            'overall_status': 'completed'
        }
        
        # Step 1: Data Validation
        if enable_validation:
            try:
                validation_result = validate_batch_attractions(attraction_ids)
                results['validation_results'] = validation_result
            except Exception as e:
                logger.error(f"Error in validation step: {str(e)}")
                results['validation_results'] = {'error': str(e)}
        
        # Step 2: Auto-Tagging
        if enable_tagging:
            try:
                tagging_result = tag_batch_attractions(attraction_ids)
                results['tagging_results'] = tagging_result
            except Exception as e:
                logger.error(f"Error in tagging step: {str(e)}")
                results['tagging_results'] = {'error': str(e)}
        
        # Step 3: Category Suggestion
        if enable_categorization:
            try:
                categorization_result = suggest_categories_batch(attraction_ids)
                results['categorization_results'] = categorization_result
            except Exception as e:
                logger.error(f"Error in categorization step: {str(e)}")
                results['categorization_results'] = {'error': str(e)}
        
        # Step 4: Geocoding (for attractions without coordinates)
        if enable_geocoding:
            try:
                geocoding_service = get_geocoding_service()
                geocoded_count = 0
                successful_geocoding = 0
                
                if geocoding_service:
                    for attraction_id in attraction_ids:
                        attraction = Attraction.query.get(attraction_id)
                        if attraction and not attraction.geocoded:
                            geocoded_count += 1
                            try:
                                # Use the geocoding service to get coordinates
                                location_info = geocoding_service.geocode(
                                    location_name=attraction.title,
                                    province=attraction.province
                                )
                                
                                if location_info:
                                    attraction.latitude = location_info['latitude']
                                    attraction.longitude = location_info['longitude']
                                    attraction.geocoded = True
                                    db.session.commit()
                                    successful_geocoding += 1
                                
                                # Add delay to respect API limits
                                time.sleep(0.2)
                            except Exception as e:
                                logger.error(f"Error geocoding attraction {attraction.id}: {str(e)}")
                                continue
                
                results['geocoding_results'] = {
                    'processed': geocoded_count,
                    'successful': successful_geocoding
                }
            except Exception as e:
                logger.error(f"Error in geocoding step: {str(e)}")
                results['geocoding_results'] = {'error': str(e)}
        
        return jsonify({
            'success': True,
            'message': 'Full data cleaning and enrichment completed',
            'results': results
        })
    
    except Exception as e:
        logger.error(f"Error in full data cleaning endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@ai_cleaning_bp.route('/data-cleaning/overview', methods=['GET'])
def get_data_cleaning_overview():
    """Get overview of data cleaning status across all attractions."""
    try:
        # Get overall statistics
        total_attractions = Attraction.query.count()
        
        # Validation stats
        validated_count = Attraction.query.filter_by(data_validated=True).count()
        
        # Tagging stats
        tagged_count = Attraction.query.filter_by(auto_tagged=True).count()
        
        # Categorization stats
        categorized_count = Attraction.query.filter_by(categorized=True).count()
        
        # Geocoding stats
        geocoded_count = Attraction.query.filter_by(geocoded=True).count()
        
        # Quality score stats
        avg_validation_score = db.session.query(
            db.func.avg(Attraction.validation_score)
        ).filter(Attraction.validation_score.isnot(None)).scalar() or 0.0
        
        # Recent activity
        recent_cleaned = Attraction.query.filter(
            Attraction.last_cleaned_at.isnot(None)
        ).order_by(Attraction.last_cleaned_at.desc()).limit(10).all()
        
        return jsonify({
            'success': True,
            'overview': {
                'total_attractions': total_attractions,
                'validation': {
                    'count': validated_count,
                    'coverage': validated_count / total_attractions if total_attractions > 0 else 0,
                    'avg_score': round(avg_validation_score, 3)
                },
                'tagging': {
                    'count': tagged_count,
                    'coverage': tagged_count / total_attractions if total_attractions > 0 else 0
                },
                'categorization': {
                    'count': categorized_count,
                    'coverage': categorized_count / total_attractions if total_attractions > 0 else 0
                },
                'geocoding': {
                    'count': geocoded_count,
                    'coverage': geocoded_count / total_attractions if total_attractions > 0 else 0
                },
                'recent_activity': [
                    {
                        'id': attr.id,
                        'title': attr.title,
                        'last_cleaned_at': attr.last_cleaned_at.isoformat() if attr.last_cleaned_at else None
                    }
                    for attr in recent_cleaned
                ]
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting data cleaning overview: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@ai_cleaning_bp.route('/data-cleaning/status/<int:attraction_id>', methods=['GET'])
def get_attraction_cleaning_status(attraction_id):
    """Get comprehensive cleaning status for a specific attraction."""
    try:
        attraction = Attraction.query.get(attraction_id)
        
        if not attraction:
            return jsonify({'error': 'Attraction not found'}), 404
        
        # Get validation results
        validation_results = DataValidationResult.query.filter_by(attraction_id=attraction_id).all()
        
        # Get tags
        tags = AttractionTag.query.filter_by(attraction_id=attraction_id).all()
        
        # Get categories
        categories = AttractionCategory.query.filter_by(attraction_id=attraction_id).all()
        
        return jsonify({
            'success': True,
            'attraction_id': attraction_id,
            'status': {
                'data_validated': attraction.data_validated,
                'validation_score': attraction.validation_score,
                'auto_tagged': attraction.auto_tagged,
                'categorized': attraction.categorized,
                'geocoded': attraction.geocoded,
                'last_cleaned_at': attraction.last_cleaned_at.isoformat() if attraction.last_cleaned_at else None
            },
            'details': {
                'validation_issues': len(validation_results),
                'validation_results': [result.to_dict() for result in validation_results],
                'tags_count': len(tags),
                'tags': [tag.to_dict() for tag in tags],
                'categories_count': len(categories),
                'categories': [category.to_dict() for category in categories],
                'coordinates': {
                    'latitude': attraction.latitude,
                    'longitude': attraction.longitude,
                    'province': attraction.province
                }
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting attraction cleaning status: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500