"""
AI Category Suggestion Service for recommending appropriate categories for attractions.
"""
import re
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from collections import Counter
from app.models import db, Attraction, AttractionCategory

logger = logging.getLogger(__name__)


class CategorySuggester:
    """Main class for suggesting categories for attractions."""
    
    def __init__(self):
        """Initialize the category suggester with predefined category hierarchy."""
        
        # Main category hierarchy
        self.category_hierarchy = {
            # Religious & Cultural Sites
            'religious': {
                'name': 'Religious Sites',
                'keywords': ['วัด', 'โบสถ์', 'มัสยิด', 'ศาล', 'ศาสนา', 'พระ', 'เจดีย์', 'พุทธ', 'ฮินดู'],
                'subcategories': ['temple', 'church', 'mosque', 'shrine'],
                'confidence_base': 0.9
            },
            'cultural': {
                'name': 'Cultural Heritage',
                'keywords': ['วัฒนธรรม', 'ประเพณี', 'โบราณ', 'มรดก', 'ศิลปะ', 'พิพิธภัณฑ์', 'หอศิลป์'],
                'subcategories': ['museum', 'art_gallery', 'cultural_center', 'heritage_site'],
                'confidence_base': 0.8
            },
            
            # Natural Attractions
            'nature': {
                'name': 'Natural Attractions',
                'keywords': ['ธรรมชาติ', 'ป่า', 'เขา', 'ดอย', 'ภูเขา', 'น้ำตก', 'ถ้ำ', 'อุทยาน'],
                'subcategories': ['national_park', 'forest', 'mountain', 'waterfall', 'cave'],
                'confidence_base': 0.9
            },
            'beach_island': {
                'name': 'Beach & Islands',
                'keywords': ['หาด', 'ชายหาด', 'เกาะ', 'ทะเล', 'อ่าว', 'แหลม', 'คลื่น'],
                'subcategories': ['beach', 'island', 'bay', 'coastal'],
                'confidence_base': 0.95
            },
            
            # Entertainment & Recreation
            'entertainment': {
                'name': 'Entertainment',
                'keywords': ['สวนสนุก', 'เกม', 'โชว์', 'การแสดง', 'บันเทิง', 'สนุก', 'เล่น'],
                'subcategories': ['amusement_park', 'theme_park', 'entertainment_complex'],
                'confidence_base': 0.8
            },
            'recreation': {
                'name': 'Recreation & Sports',
                'keywords': ['กีฬา', 'ออกกำลัง', 'เล่น', 'สนาม', 'สระว่าย', 'กอล์ฟ'],
                'subcategories': ['sports_complex', 'swimming_pool', 'golf_course', 'recreation_area'],
                'confidence_base': 0.8
            },
            
            # Commercial & Urban
            'shopping': {
                'name': 'Shopping & Markets',
                'keywords': ['ตลาด', 'ช้อปปิ้ง', 'ซื้อของ', 'ห้างสรรพสินค้า', 'ของฝาก', 'ร้านค้า'],
                'subcategories': ['market', 'shopping_mall', 'night_market', 'souvenir_shop'],
                'confidence_base': 0.9
            },
            'dining': {
                'name': 'Food & Dining',
                'keywords': ['ร้านอาหาร', 'อาหาร', 'กิน', 'ครัว', 'เมนู', 'รสชาติ', 'อร่อย'],
                'subcategories': ['restaurant', 'street_food', 'local_cuisine', 'food_court'],
                'confidence_base': 0.8
            },
            
            # Accommodation & Services
            'accommodation': {
                'name': 'Accommodation',
                'keywords': ['โรงแรม', 'รีสอร์ท', 'ที่พัก', 'บังกะโล', 'เกสต์เฮาส์'],
                'subcategories': ['hotel', 'resort', 'guesthouse', 'hostel'],
                'confidence_base': 0.9
            },
            
            # Historical Sites
            'historical': {
                'name': 'Historical Sites',
                'keywords': ['ประวัติศาสตร์', 'โบราณ', 'สมัย', 'อายุ', 'ปีที่', 'สร้าง', 'โบราณคดี'],
                'subcategories': ['ancient_site', 'historical_building', 'archaeological_site'],
                'confidence_base': 0.85
            },
            
            # Modern Attractions
            'modern': {
                'name': 'Modern Attractions',
                'keywords': ['ทันสมัย', 'ใหม่', 'โมเดิร์น', 'เทคโนโลยี', 'นวัตกรรม'],
                'subcategories': ['modern_building', 'technology_center', 'innovation_hub'],
                'confidence_base': 0.7
            }
        }
        
        # Specialized category patterns
        self.specialized_patterns = {
            'palace': {
                'keywords': ['พระราชวัง', 'ราชวัง', 'วัง', 'พระที่นั่ง'],
                'parent': 'historical',
                'confidence': 0.95
            },
            'floating_market': {
                'keywords': ['ตลาดน้ำ', 'ขายของบนเรือ', 'ลอยน้ำ'],
                'parent': 'shopping',
                'confidence': 0.9
            },
            'national_park': {
                'keywords': ['อุทยานแห่งชาติ', 'อุทยาน', 'ป่าสงวน'],
                'parent': 'nature',
                'confidence': 0.95
            },
            'zoo': {
                'keywords': ['สวนสัตว์', 'สัตว์', 'เลี้ยงสัตว์'],
                'parent': 'entertainment',
                'confidence': 0.9
            },
            'aquarium': {
                'keywords': ['พิพิธภัณฑ์สัตว์น้ำ', 'ปลา', 'สัตว์น้ำ', 'ใต้น้ำ'],
                'parent': 'entertainment',
                'confidence': 0.9
            }
        }
        
        # Activity-based categories
        self.activity_categories = {
            'adventure': {
                'keywords': ['ผจญภัย', 'เสี่ยงภัย', 'ตื่นเต้น', 'กิจกรรม', 'ท้าทาย'],
                'confidence': 0.7
            },
            'relaxation': {
                'keywords': ['ผ่อนคลาย', 'สงบ', 'เงียบ', 'สบาย', 'พักผ่อน'],
                'confidence': 0.7
            },
            'educational': {
                'keywords': ['เรียนรู้', 'ความรู้', 'การศึกษา', 'วิชาการ', 'สอน'],
                'confidence': 0.8
            },
            'photography': {
                'keywords': ['ถ่ายรูป', 'ภาพสวย', 'เช็คอิน', 'ไฮไลท์', 'วิว'],
                'confidence': 0.6
            }
        }
    
    def suggest_categories(self, attraction: Attraction) -> List[Dict]:
        """
        Suggest categories for an attraction based on its content.
        
        Args:
            attraction: Attraction model instance
            
        Returns:
            list: List of category suggestions
        """
        suggestions = []
        
        # Combine title and body for analysis
        content = f"{attraction.title or ''} {attraction.body or ''}".lower()
        
        # Check main categories
        for category_id, category_info in self.category_hierarchy.items():
            confidence = self._calculate_category_confidence(content, category_info)
            
            if confidence > 0.4:  # Minimum confidence threshold
                suggestions.append({
                    'category_name': category_id,
                    'display_name': category_info['name'],
                    'parent_category': None,
                    'confidence_score': confidence,
                    'is_primary': confidence > 0.7,
                    'source': 'ai_suggestion'
                })
                
                # Check for subcategories
                subcategory_suggestions = self._check_subcategories(
                    content, category_id, category_info, confidence
                )
                suggestions.extend(subcategory_suggestions)
        
        # Check specialized patterns
        specialized_suggestions = self._check_specialized_patterns(content)
        suggestions.extend(specialized_suggestions)
        
        # Check activity-based categories
        activity_suggestions = self._check_activity_categories(content)
        suggestions.extend(activity_suggestions)
        
        # Add location-based categories if available
        if attraction.province:
            location_category = self._get_location_category(attraction.province)
            if location_category:
                suggestions.append(location_category)
        
        # Remove duplicates and sort by confidence
        unique_suggestions = []
        seen_categories = set()
        
        for suggestion in sorted(suggestions, key=lambda x: x['confidence_score'], reverse=True):
            category_key = (suggestion['category_name'], suggestion.get('parent_category'))
            if category_key not in seen_categories:
                unique_suggestions.append(suggestion)
                seen_categories.add(category_key)
        
        # Ensure we have at least one primary category
        if unique_suggestions and not any(s['is_primary'] for s in unique_suggestions):
            unique_suggestions[0]['is_primary'] = True
        
        return unique_suggestions[:8]  # Return top 8 suggestions
    
    def _calculate_category_confidence(self, content: str, category_info: Dict) -> float:
        """Calculate confidence score for a category based on keyword matches."""
        keywords = category_info['keywords']
        base_confidence = category_info['confidence_base']
        
        # Count keyword matches with weights
        total_score = 0
        max_possible_score = 0
        
        for keyword in keywords:
            # Use regex to find all matches
            matches = len(re.findall(r'\b' + re.escape(keyword.lower()) + r'\b', content))
            
            # Weight longer keywords higher
            keyword_weight = len(keyword) / 10 + 1
            total_score += matches * keyword_weight
            max_possible_score += keyword_weight
        
        if max_possible_score == 0:
            return 0.0
        
        # Normalize score and apply base confidence
        normalized_score = min(1.0, total_score / max_possible_score)
        confidence = base_confidence * normalized_score
        
        return confidence
    
    def _check_subcategories(self, content: str, parent_category: str, 
                           category_info: Dict, parent_confidence: float) -> List[Dict]:
        """Check for subcategory matches."""
        suggestions = []
        subcategories = category_info.get('subcategories', [])
        
        # Define subcategory keywords
        subcategory_keywords = {
            'temple': ['วัด', 'พระ', 'โบสถ์'],
            'church': ['โบสถ์', 'คริสต์'],
            'mosque': ['มัสยิด', 'อิสลาม'],
            'shrine': ['ศาล', 'สวนสน'],
            'museum': ['พิพิธภัณฑ์', 'หอศิลป์'],
            'art_gallery': ['แกลเลอรี่', 'ศิลปะ'],
            'national_park': ['อุทยานแห่งชาติ', 'ป่าสงวน'],
            'forest': ['ป่า', 'ไผ่'],
            'mountain': ['เขา', 'ดอย', 'ภูเขา'],
            'waterfall': ['น้ำตก', 'ธาร'],
            'cave': ['ถ้ำ', 'โพรง'],
            'beach': ['หาด', 'ชายหาด'],
            'island': ['เกาะ'],
            'market': ['ตลาด'],
            'shopping_mall': ['ห้างสรรพสินค้า', 'ช้อปปิ้ง'],
            'hotel': ['โรงแรม'],
            'resort': ['รีสอร์ท']
        }
        
        for subcategory in subcategories:
            keywords = subcategory_keywords.get(subcategory, [])
            if not keywords:
                continue
            
            # Check for subcategory keywords
            matches = sum(1 for keyword in keywords 
                         if re.search(r'\b' + re.escape(keyword.lower()) + r'\b', content))
            
            if matches > 0:
                # Subcategory confidence is based on parent confidence and matches
                confidence = parent_confidence * 0.8 * (matches / len(keywords))
                
                suggestions.append({
                    'category_name': subcategory,
                    'display_name': subcategory.replace('_', ' ').title(),
                    'parent_category': parent_category,
                    'confidence_score': confidence,
                    'is_primary': False,
                    'source': 'ai_suggestion'
                })
        
        return suggestions
    
    def _check_specialized_patterns(self, content: str) -> List[Dict]:
        """Check for specialized category patterns."""
        suggestions = []
        
        for pattern_name, pattern_info in self.specialized_patterns.items():
            keywords = pattern_info['keywords']
            matches = sum(1 for keyword in keywords 
                         if re.search(r'\b' + re.escape(keyword.lower()) + r'\b', content))
            
            if matches > 0:
                confidence = pattern_info['confidence'] * (matches / len(keywords))
                
                suggestions.append({
                    'category_name': pattern_name,
                    'display_name': pattern_name.replace('_', ' ').title(),
                    'parent_category': pattern_info.get('parent'),
                    'confidence_score': confidence,
                    'is_primary': confidence > 0.8,
                    'source': 'ai_suggestion'
                })
        
        return suggestions
    
    def _check_activity_categories(self, content: str) -> List[Dict]:
        """Check for activity-based categories."""
        suggestions = []
        
        for activity, activity_info in self.activity_categories.items():
            keywords = activity_info['keywords']
            matches = sum(1 for keyword in keywords 
                         if re.search(r'\b' + re.escape(keyword.lower()) + r'\b', content))
            
            if matches > 0:
                confidence = activity_info['confidence'] * (matches / len(keywords))
                
                suggestions.append({
                    'category_name': f'activity_{activity}',
                    'display_name': f'{activity.title()} Activity',
                    'parent_category': 'activity',
                    'confidence_score': confidence,
                    'is_primary': False,
                    'source': 'ai_suggestion'
                })
        
        return suggestions
    
    def _get_location_category(self, province: str) -> Optional[Dict]:
        """Get location-based category from province."""
        # Thailand region mapping
        region_mapping = {
            'กรุงเทพมหานคร': 'central_bangkok',
            'เชียงใหม่': 'northern',
            'เชียงราย': 'northern',
            'ลำปาง': 'northern',
            'ลำพูน': 'northern',
            'แม่ฮ่องสอน': 'northern',
            'พะเยา': 'northern',
            'แพร่': 'northern',
            'น่าน': 'northern',
            'ภูเก็ต': 'southern',
            'กระบี่': 'southern',
            'สุราษฎร์ธานี': 'southern',
            'นครศรีธรรมราช': 'southern',
            'ชุมพร': 'southern',
            'ขอนแก่น': 'northeastern',
            'อุดรธานี': 'northeastern',
            'นครราชสีมา': 'northeastern',
            'บุรีรัมย์': 'northeastern'
        }
        
        region = region_mapping.get(province)
        if region:
            return {
                'category_name': f'region_{region}',
                'display_name': f'{region.replace("_", " ").title()} Region',
                'parent_category': 'location',
                'confidence_score': 1.0,
                'is_primary': False,
                'source': 'ai_suggestion'
            }
        
        return None
    
    def save_categories(self, attraction_id: int, categories: List[Dict]) -> None:
        """
        Save suggested categories to database.
        
        Args:
            attraction_id: ID of the attraction
            categories: List of category dictionaries
        """
        try:
            # Remove existing AI-generated categories
            AttractionCategory.query.filter_by(
                attraction_id=attraction_id,
                source='ai_suggestion'
            ).delete()
            
            # Save new categories
            for category_data in categories:
                category = AttractionCategory(
                    attraction_id=attraction_id,
                    category_name=category_data['category_name'],
                    parent_category=category_data.get('parent_category'),
                    confidence_score=category_data['confidence_score'],
                    is_primary=category_data['is_primary'],
                    source=category_data['source']
                )
                db.session.add(category)
            
            # Update attraction categorization status
            attraction = Attraction.query.get(attraction_id)
            if attraction:
                attraction.categorized = True
                attraction.last_cleaned_at = datetime.utcnow()
            
            db.session.commit()
            logger.info(f"Saved {len(categories)} categories for attraction {attraction_id}")
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving categories for attraction {attraction_id}: {str(e)}")
    
    def get_category_suggestions_for_text(self, text: str) -> List[Dict]:
        """
        Get category suggestions for arbitrary text.
        
        Args:
            text: Text to analyze
            
        Returns:
            list: List of category suggestions
        """
        content = text.lower()
        suggestions = []
        
        # Check main categories
        for category_id, category_info in self.category_hierarchy.items():
            confidence = self._calculate_category_confidence(content, category_info)
            
            if confidence > 0.1:  # Lower threshold for text analysis
                suggestions.append({
                    'category_name': category_id,
                    'display_name': category_info['name'],
                    'confidence_score': confidence
                })
        
        return sorted(suggestions, key=lambda x: x['confidence_score'], reverse=True)[:10]


def suggest_categories_for_attraction(attraction_id: int) -> Dict:
    """
    Generate and save category suggestions for a specific attraction.
    
    Args:
        attraction_id: ID of attraction to categorize
        
    Returns:
        dict: Categorization results
    """
    try:
        attraction = Attraction.query.get(attraction_id)
        if not attraction:
            return {'error': 'Attraction not found'}
        
        suggester = CategorySuggester()
        categories = suggester.suggest_categories(attraction)
        
        # Save categories to database
        suggester.save_categories(attraction_id, categories)
        
        return {
            'attraction_id': attraction_id,
            'categories_suggested': len(categories),
            'categories': categories
        }
    
    except Exception as e:
        logger.error(f"Error suggesting categories for attraction {attraction_id}: {str(e)}")
        return {'error': str(e)}


def suggest_categories_batch(attraction_ids: List[int]) -> Dict:
    """
    Generate category suggestions for multiple attractions at once.
    
    Args:
        attraction_ids: List of attraction IDs to categorize
        
    Returns:
        dict: Batch categorization results
    """
    results = {
        'processed': 0,
        'successful': 0,
        'failed': 0,
        'total_categories_suggested': 0,
        'results': []
    }
    
    suggester = CategorySuggester()
    
    for attraction_id in attraction_ids:
        try:
            attraction = Attraction.query.get(attraction_id)
            if not attraction:
                results['failed'] += 1
                results['results'].append({
                    'attraction_id': attraction_id,
                    'error': 'Attraction not found'
                })
                continue
            
            categories = suggester.suggest_categories(attraction)
            suggester.save_categories(attraction_id, categories)
            
            results['successful'] += 1
            results['total_categories_suggested'] += len(categories)
            results['results'].append({
                'attraction_id': attraction_id,
                'categories_suggested': len(categories),
                'categories': categories
            })
        
        except Exception as e:
            results['failed'] += 1
            results['results'].append({
                'attraction_id': attraction_id,
                'error': str(e)
            })
            logger.error(f"Error categorizing attraction {attraction_id}: {str(e)}")
        
        results['processed'] += 1
    
    return results


def get_categorization_stats() -> Dict:
    """Get overall categorization statistics."""
    try:
        total_attractions = Attraction.query.count()
        categorized_attractions = Attraction.query.filter_by(categorized=True).count()
        
        # Get category counts
        category_counts = db.session.query(
            AttractionCategory.category_name,
            db.func.count(AttractionCategory.id).label('count')
        ).group_by(AttractionCategory.category_name).order_by(
            db.func.count(AttractionCategory.id).desc()
        ).limit(15).all()
        
        # Get primary category distribution
        primary_categories = db.session.query(
            AttractionCategory.category_name,
            db.func.count(AttractionCategory.id).label('count')
        ).filter_by(is_primary=True).group_by(
            AttractionCategory.category_name
        ).order_by(db.func.count(AttractionCategory.id).desc()).limit(10).all()
        
        return {
            'total_attractions': total_attractions,
            'categorized_attractions': categorized_attractions,
            'categorization_coverage': categorized_attractions / total_attractions if total_attractions > 0 else 0,
            'most_common_categories': [{'category': cat, 'count': count} for cat, count in category_counts],
            'primary_category_distribution': [{'category': cat, 'count': count} for cat, count in primary_categories],
            'avg_categories_per_attraction': db.session.query(
                db.func.avg(db.func.count(AttractionCategory.id))
            ).select_from(AttractionCategory).group_by(AttractionCategory.attraction_id).scalar() or 0
        }
    
    except Exception as e:
        logger.error(f"Error getting categorization stats: {str(e)}")
        return {'error': str(e)}


def get_category_suggestions_for_text(text: str) -> Dict:
    """
    Get category suggestions for arbitrary text.
    
    Args:
        text: Text to analyze
        
    Returns:
        dict: Category suggestions
    """
    try:
        suggester = CategorySuggester()
        suggestions = suggester.get_category_suggestions_for_text(text)
        
        return {
            'text': text[:100] + '...' if len(text) > 100 else text,
            'suggestions': suggestions
        }
    
    except Exception as e:
        logger.error(f"Error getting category suggestions: {str(e)}")
        return {'error': str(e)}