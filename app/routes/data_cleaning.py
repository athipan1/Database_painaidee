"""
Data cleaning routes for managing attraction data quality and enrichment.
"""
from flask import Blueprint, request, jsonify
from app.services.auto_tagging import AutoTagger
from app.services.category_suggestion import CategorySuggester
from app.services.data_validation import DataValidator
from app.models import Attraction, db
import json

data_cleaning_bp = Blueprint('data_cleaning', __name__)

# Initialize services
auto_tagger = AutoTagger()
category_suggester = CategorySuggester()
data_validator = DataValidator()


@data_cleaning_bp.route('/api/data-cleaning/generate-tags', methods=['POST'])
def generate_tags():
    """Generate tags for attraction."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        title = data.get('title', '')
        body = data.get('body', '')
        max_tags = data.get('max_tags', 10)
        
        if not title:
            return jsonify({'error': 'Title is required'}), 400
        
        tags = auto_tagger.generate_tags(title, body, max_tags)
        
        return jsonify({
            'success': True,
            'tags': tags,
            'count': len(tags)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@data_cleaning_bp.route('/api/data-cleaning/suggest-categories', methods=['POST'])
def suggest_categories():
    """Suggest categories for attraction."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        title = data.get('title', '')
        body = data.get('body', '')
        max_categories = data.get('max_categories', 3)
        include_subcategories = data.get('include_subcategories', True)
        
        if not title:
            return jsonify({'error': 'Title is required'}), 400
        
        categories = category_suggester.suggest_categories(
            title, body, max_categories, include_subcategories
        )
        
        return jsonify({
            'success': True,
            'categories': categories,
            'count': len(categories)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@data_cleaning_bp.route('/api/data-cleaning/validate', methods=['POST'])
def validate_data():
    """Validate attraction data."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        validation_result = data_validator.validate_attraction_data(data)
        
        return jsonify({
            'success': True,
            'validation': validation_result
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@data_cleaning_bp.route('/api/data-cleaning/validate-batch', methods=['POST'])
def validate_batch():
    """Validate multiple attractions."""
    try:
        data = request.get_json()
        if not data or 'attractions' not in data:
            return jsonify({'error': 'No attractions data provided'}), 400
        
        attractions = data['attractions']
        if not isinstance(attractions, list):
            return jsonify({'error': 'Attractions must be a list'}), 400
        
        batch_result = data_validator.validate_batch(attractions)
        
        return jsonify({
            'success': True,
            'batch_validation': batch_result
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@data_cleaning_bp.route('/api/data-cleaning/enrich/<int:attraction_id>', methods=['POST'])
def enrich_attraction(attraction_id):
    """Enrich existing attraction with tags and categories."""
    try:
        attraction = Attraction.query.get(attraction_id)
        if not attraction:
            return jsonify({'error': 'Attraction not found'}), 404
        
        # Generate tags
        tags = auto_tagger.generate_tags(attraction.title, attraction.body or '')
        
        # Suggest categories
        categories = category_suggester.suggest_categories(
            attraction.title, attraction.body or ''
        )
        
        # Store tags as JSON string (matching the model field)
        attraction.keywords = json.dumps(tags)
        attraction.keywords_extracted = True
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'attraction_id': attraction_id,
            'generated_tags': tags,
            'suggested_categories': categories,
            'message': 'Attraction enriched successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@data_cleaning_bp.route('/api/data-cleaning/bulk-enrich', methods=['POST'])
def bulk_enrich():
    """Enrich multiple attractions."""
    try:
        data = request.get_json()
        limit = data.get('limit', 10) if data else 10
        
        # Get attractions that haven't been enriched yet
        attractions = Attraction.query.filter_by(keywords_extracted=False).limit(limit).all()
        
        enriched_count = 0
        results = []
        
        for attraction in attractions:
            try:
                # Generate tags
                tags = auto_tagger.generate_tags(attraction.title, attraction.body or '')
                
                # Suggest categories
                categories = category_suggester.suggest_categories(
                    attraction.title, attraction.body or ''
                )
                
                # Store tags
                attraction.keywords = json.dumps(tags)
                attraction.keywords_extracted = True
                
                results.append({
                    'attraction_id': attraction.id,
                    'title': attraction.title,
                    'tags': tags,
                    'categories': categories
                })
                
                enriched_count += 1
                
            except Exception as e:
                results.append({
                    'attraction_id': attraction.id,
                    'title': attraction.title,
                    'error': str(e)
                })
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'enriched_count': enriched_count,
            'total_processed': len(attractions),
            'results': results
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@data_cleaning_bp.route('/api/data-cleaning/stats', methods=['GET'])
def get_cleaning_stats():
    """Get data cleaning statistics."""
    try:
        total_attractions = Attraction.query.count()
        enriched_attractions = Attraction.query.filter_by(keywords_extracted=True).count()
        
        # Get sample of recent enrichments
        recent_enriched = Attraction.query.filter_by(keywords_extracted=True)\
            .order_by(Attraction.updated_at.desc()).limit(5).all()
        
        recent_samples = []
        for attraction in recent_enriched:
            tags = []
            if attraction.keywords:
                try:
                    tags = json.loads(attraction.keywords)
                except:
                    tags = []
            
            recent_samples.append({
                'id': attraction.id,
                'title': attraction.title,
                'tags': tags,
                'updated_at': attraction.updated_at.isoformat() if attraction.updated_at else None
            })
        
        return jsonify({
            'success': True,
            'stats': {
                'total_attractions': total_attractions,
                'enriched_attractions': enriched_attractions,
                'enrichment_percentage': (enriched_attractions / total_attractions * 100) if total_attractions > 0 else 0,
                'pending_enrichment': total_attractions - enriched_attractions
            },
            'recent_enrichments': recent_samples
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@data_cleaning_bp.route('/api/data-cleaning/categories', methods=['GET'])
def get_available_categories():
    """Get all available categories."""
    try:
        categories = category_suggester.get_all_categories()
        
        category_details = []
        for category in categories:
            keywords = list(category_suggester.get_category_keywords(category))
            category_details.append({
                'name': category,
                'keywords': keywords[:10]  # Limit to first 10 keywords
            })
        
        return jsonify({
            'success': True,
            'categories': category_details
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@data_cleaning_bp.route('/api/data-cleaning/category-keywords/<category_name>', methods=['GET'])
def get_category_keywords(category_name):
    """Get keywords for a specific category."""
    try:
        keywords = category_suggester.get_category_keywords(category_name)
        
        if not keywords:
            return jsonify({'error': 'Category not found'}), 404
        
        return jsonify({
            'success': True,
            'category': category_name,
            'keywords': list(keywords)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@data_cleaning_bp.route('/api/data-cleaning/clean-title', methods=['POST'])
def clean_title():
    """Clean and validate attraction title."""
    try:
        data = request.get_json()
        if not data or 'title' not in data:
            return jsonify({'error': 'Title is required'}), 400
        
        title = data['title']
        title_validation = data_validator._validate_title(title)
        
        return jsonify({
            'success': True,
            'original_title': title,
            'cleaned_title': title_validation['cleaned'],
            'errors': title_validation['errors'],
            'warnings': title_validation['warnings']
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500