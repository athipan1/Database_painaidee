"""
AI Auto-Tagging Service for automatically generating tags for attractions.
"""
import re
import json
import logging
from typing import Dict, List, Set, Optional
from datetime import datetime
from collections import Counter
from app.models import db, Attraction, AttractionTag

logger = logging.getLogger(__name__)


class AutoTagger:
    """Main class for automatic tagging of attractions."""
    
    def __init__(self):
        """Initialize the auto-tagger with predefined tag patterns."""
        
        # Thai attraction type patterns
        self.attraction_patterns = {
            'temple': {
                'keywords': ['วัด', 'โบสถ์', 'สวนสน', 'เจดีย์', 'พระ', 'บูชา', 'ศาสนา'],
                'tag_type': 'category',
                'confidence': 0.9
            },
            'museum': {
                'keywords': ['พิพิธภัณฑ์', 'หอศิลป์', 'แกลเลอรี่', 'นิทรรศการ', 'ศิลปะ'],
                'tag_type': 'category',
                'confidence': 0.9
            },
            'palace': {
                'keywords': ['พระราชวัง', 'ราชวัง', 'วัง', 'พระที่นั่ง', 'หอพระ'],
                'tag_type': 'category',
                'confidence': 0.9
            },
            'park': {
                'keywords': ['สวน', 'อุทยาน', 'ป่า', 'สวนสาธารณะ', 'สวนสวย'],
                'tag_type': 'category',
                'confidence': 0.8
            },
            'waterfall': {
                'keywords': ['น้ำตก', 'ธารน้ำ', 'ลำธาร'],
                'tag_type': 'category',
                'confidence': 0.95
            },
            'mountain': {
                'keywords': ['เขา', 'ดอย', 'ภูเขา', 'ยอดเขา', 'ลำเนา'],
                'tag_type': 'category',
                'confidence': 0.9
            },
            'beach': {
                'keywords': ['หาด', 'ชายหาด', 'อ่าว', 'เกาะ', 'ทะเล'],
                'tag_type': 'category',
                'confidence': 0.9
            },
            'market': {
                'keywords': ['ตลาด', 'ตลาดน้ำ', 'ตลาดโบราณ', 'ช้อปปิ้ง', 'ซื้อของ'],
                'tag_type': 'category',
                'confidence': 0.8
            },
            'bridge': {
                'keywords': ['สะพาน', 'สะพานแขวน', 'ข้ามแม่น้ำ'],
                'tag_type': 'category',
                'confidence': 0.9
            },
            'cave': {
                'keywords': ['ถ้ำ', 'โพรง', 'ถ้ำหิน'],
                'tag_type': 'category',
                'confidence': 0.95
            }
        }
        
        # Activity-based tags
        self.activity_patterns = {
            'photography': {
                'keywords': ['ถ่ายรูป', 'ภาพสวย', 'วิว', 'ชมวิว', 'เช็คอิน'],
                'tag_type': 'activity',
                'confidence': 0.7
            },
            'hiking': {
                'keywords': ['เดินป่า', 'ปีนเขา', 'เดินทาง', 'ธรรมชาติ', 'ออกกำลัง'],
                'tag_type': 'activity',
                'confidence': 0.8
            },
            'swimming': {
                'keywords': ['ว่ายน้ำ', 'เล่นน้ำ', 'อาบน้ำ', 'ดำน้ำ'],
                'tag_type': 'activity',
                'confidence': 0.9
            },
            'cultural': {
                'keywords': ['วัฒนธรรม', 'ประวัติศาสตร์', 'โบราณ', 'ศิลปะ', 'ภูมิปัญญา'],
                'tag_type': 'activity',
                'confidence': 0.8
            },
            'shopping': {
                'keywords': ['ช้อปปิ้ง', 'ซื้อของ', 'ของฝาก', 'สินค้า', 'ร้านค้า'],
                'tag_type': 'activity',
                'confidence': 0.8
            },
            'meditation': {
                'keywords': ['ทำสมาधิ', 'วิปัสสนา', 'สงบ', 'ปฏิบัติธรรม', 'นั่งสมาधิ'],
                'tag_type': 'activity',
                'confidence': 0.9
            }
        }
        
        # Feature-based tags
        self.feature_patterns = {
            'scenic_view': {
                'keywords': ['วิวสวย', 'ชมวิว', 'ทิวทัศน์', 'ววยาม', 'บรรยากาศดี'],
                'tag_type': 'feature',
                'confidence': 0.7
            },
            'historic': {
                'keywords': ['โบราณ', 'ประวัติศาสตร์', 'มรดก', 'โบราณคดี', 'อายุ'],
                'tag_type': 'feature',
                'confidence': 0.8
            },
            'peaceful': {
                'keywords': ['สงบ', 'เงียบ', 'สงบสุข', 'ผ่อนคลาย', 'สบาย'],
                'tag_type': 'feature',
                'confidence': 0.7
            },
            'family_friendly': {
                'keywords': ['ครอบครัว', 'เด็ก', 'ปลอดภัย', 'สนุก', 'เหมาะสำหรับเด็ก'],
                'tag_type': 'feature',
                'confidence': 0.8
            },
            'accessible': {
                'keywords': ['เข้าถึงง่าย', 'สะดวก', 'ใกล้', 'การเดินทาง', 'รถยนต์'],
                'tag_type': 'feature',
                'confidence': 0.6
            }
        }
        
        # Location-based patterns (extracted from province mapping)
        self.location_patterns = {
            'bangkok': {
                'keywords': ['กรุงเทพ', 'บางกอก', 'เมืองหลวง'],
                'tag_type': 'location',
                'confidence': 0.9
            },
            'northern': {
                'keywords': ['เชียงใหม่', 'เชียงราย', 'ลำปาง', 'ลำพูน', 'แม่ฮ่องสอน'],
                'tag_type': 'location',
                'confidence': 0.9
            },
            'southern': {
                'keywords': ['ภูเก็ต', 'กระบี่', 'สุราษฎร์ธานี', 'นครศรี', 'ชุมพร'],
                'tag_type': 'location',
                'confidence': 0.9
            },
            'northeastern': {
                'keywords': ['ขอนแก่น', 'อุดรธานี', 'นครราชสีมา', 'บุรีรัมย์'],
                'tag_type': 'location', 
                'confidence': 0.9
            }
        }
        
        # Combine all patterns
        self.all_patterns = {
            **self.attraction_patterns,
            **self.activity_patterns,
            **self.feature_patterns,
            **self.location_patterns
        }
    
    def generate_tags(self, attraction: Attraction) -> List[Dict]:
        """
        Generate tags for an attraction based on its content.
        
        Args:
            attraction: Attraction model instance
            
        Returns:
            list: List of tag dictionaries
        """
        tags = []
        
        # Combine title and body for analysis
        content = f"{attraction.title or ''} {attraction.body or ''}".lower()
        
        # Extract tags based on patterns
        for tag_name, pattern_info in self.all_patterns.items():
            confidence = self._calculate_tag_confidence(content, pattern_info)
            
            if confidence > 0.5:  # Minimum confidence threshold
                tags.append({
                    'tag_name': tag_name,
                    'tag_type': pattern_info['tag_type'],
                    'confidence_score': confidence,
                    'source': 'ai_auto'
                })
        
        # Add province-based location tag if available
        if attraction.province:
            tags.append({
                'tag_name': f"province_{attraction.province.lower().replace(' ', '_')}",
                'tag_type': 'location',
                'confidence_score': 1.0,
                'source': 'ai_auto'
            })
        
        # Add geocoded location context if available
        if attraction.latitude and attraction.longitude:
            region_tag = self._get_region_from_coordinates(attraction.latitude, attraction.longitude)
            if region_tag:
                tags.append({
                    'tag_name': region_tag,
                    'tag_type': 'location',
                    'confidence_score': 0.8,
                    'source': 'ai_auto'
                })
        
        # Extract keyword-based tags
        keyword_tags = self._extract_keyword_tags(content)
        tags.extend(keyword_tags)
        
        # Remove duplicates and sort by confidence
        unique_tags = []
        seen_tags = set()
        
        for tag in sorted(tags, key=lambda x: x['confidence_score'], reverse=True):
            tag_key = (tag['tag_name'], tag['tag_type'])
            if tag_key not in seen_tags:
                unique_tags.append(tag)
                seen_tags.add(tag_key)
        
        return unique_tags[:10]  # Return top 10 tags
    
    def _calculate_tag_confidence(self, content: str, pattern_info: Dict) -> float:
        """Calculate confidence score for a tag based on keyword matches."""
        keywords = pattern_info['keywords']
        base_confidence = pattern_info['confidence']
        
        # Count keyword matches
        matches = 0
        total_keywords = len(keywords)
        
        for keyword in keywords:
            # Use word boundaries to avoid partial matches
            if re.search(r'\b' + re.escape(keyword.lower()) + r'\b', content):
                matches += 1
        
        if matches == 0:
            return 0.0
        
        # Calculate confidence based on match ratio
        match_ratio = matches / total_keywords
        confidence = base_confidence * (0.5 + 0.5 * match_ratio)
        
        return min(1.0, confidence)
    
    def _get_region_from_coordinates(self, lat: float, lng: float) -> Optional[str]:
        """Get region tag based on coordinates (simplified)."""
        try:
            # Very basic region detection for Thailand
            if lat > 18.0:  # Northern Thailand
                return 'region_northern'
            elif lat < 12.0:  # Southern Thailand
                return 'region_southern'
            elif lng < 101.0:  # Western Thailand
                return 'region_western'
            elif lng > 104.0:  # Eastern Thailand
                return 'region_eastern'
            else:  # Central Thailand
                return 'region_central'
        except Exception:
            return None
    
    def _extract_keyword_tags(self, content: str) -> List[Dict]:
        """Extract additional keyword-based tags from content."""
        tags = []
        
        # Extract color mentions
        colors = ['แดง', 'เขียว', 'น้ำเงิน', 'เหลือง', 'ขาว', 'ดำ', 'ชมพู', 'ทอง']
        for color in colors:
            if color in content:
                tags.append({
                    'tag_name': f'color_{color}',
                    'tag_type': 'feature',
                    'confidence_score': 0.6,
                    'source': 'ai_auto'
                })
        
        # Extract time-related tags
        time_keywords = {
            'sunrise': ['พระอาทิตย์ขึ้น', 'แสงแรก', 'เช้า'],
            'sunset': ['พระอาทิตย์ตก', 'แสงส้ม', 'เย็น'],
            'night': ['กลางคืน', 'ไฟ', 'ส่องแสง']
        }
        
        for time_tag, keywords in time_keywords.items():
            for keyword in keywords:
                if keyword in content:
                    tags.append({
                        'tag_name': f'time_{time_tag}',
                        'tag_type': 'feature',
                        'confidence_score': 0.7,
                        'source': 'ai_auto'
                    })
                    break
        
        return tags
    
    def save_tags(self, attraction_id: int, tags: List[Dict]) -> None:
        """
        Save generated tags to database.
        
        Args:
            attraction_id: ID of the attraction
            tags: List of tag dictionaries
        """
        try:
            # Remove existing auto-generated tags
            AttractionTag.query.filter_by(
                attraction_id=attraction_id,
                source='ai_auto'
            ).delete()
            
            # Save new tags
            for tag_data in tags:
                tag = AttractionTag(
                    attraction_id=attraction_id,
                    tag_name=tag_data['tag_name'],
                    tag_type=tag_data['tag_type'],
                    confidence_score=tag_data['confidence_score'],
                    source=tag_data['source']
                )
                db.session.add(tag)
            
            # Update attraction tagging status
            attraction = Attraction.query.get(attraction_id)
            if attraction:
                attraction.auto_tagged = True
                attraction.last_cleaned_at = datetime.utcnow()
            
            db.session.commit()
            logger.info(f"Saved {len(tags)} tags for attraction {attraction_id}")
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving tags for attraction {attraction_id}: {str(e)}")
    
    def get_tag_suggestions(self, text: str) -> List[Dict]:
        """
        Get tag suggestions for arbitrary text.
        
        Args:
            text: Text to analyze for tags
            
        Returns:
            list: List of suggested tags
        """
        content = text.lower()
        suggestions = []
        
        for tag_name, pattern_info in self.all_patterns.items():
            confidence = self._calculate_tag_confidence(content, pattern_info)
            
            if confidence > 0.3:  # Lower threshold for suggestions
                suggestions.append({
                    'tag_name': tag_name,
                    'tag_type': pattern_info['tag_type'],
                    'confidence_score': confidence
                })
        
        return sorted(suggestions, key=lambda x: x['confidence_score'], reverse=True)[:15]


def tag_attraction(attraction_id: int) -> Dict:
    """
    Generate and save tags for a specific attraction.
    
    Args:
        attraction_id: ID of attraction to tag
        
    Returns:
        dict: Tagging results
    """
    try:
        attraction = Attraction.query.get(attraction_id)
        if not attraction:
            return {'error': 'Attraction not found'}
        
        tagger = AutoTagger()
        tags = tagger.generate_tags(attraction)
        
        # Save tags to database
        tagger.save_tags(attraction_id, tags)
        
        return {
            'attraction_id': attraction_id,
            'tags_generated': len(tags),
            'tags': tags
        }
    
    except Exception as e:
        logger.error(f"Error tagging attraction {attraction_id}: {str(e)}")
        return {'error': str(e)}


def tag_batch_attractions(attraction_ids: List[int]) -> Dict:
    """
    Generate tags for multiple attractions at once.
    
    Args:
        attraction_ids: List of attraction IDs to tag
        
    Returns:
        dict: Batch tagging results
    """
    results = {
        'processed': 0,
        'successful': 0,
        'failed': 0,
        'total_tags_generated': 0,
        'results': []
    }
    
    tagger = AutoTagger()
    
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
            
            tags = tagger.generate_tags(attraction)
            tagger.save_tags(attraction_id, tags)
            
            results['successful'] += 1
            results['total_tags_generated'] += len(tags)
            results['results'].append({
                'attraction_id': attraction_id,
                'tags_generated': len(tags),
                'tags': tags
            })
        
        except Exception as e:
            results['failed'] += 1
            results['results'].append({
                'attraction_id': attraction_id,
                'error': str(e)
            })
            logger.error(f"Error tagging attraction {attraction_id}: {str(e)}")
        
        results['processed'] += 1
    
    return results


def get_tagging_stats() -> Dict:
    """Get overall tagging statistics."""
    try:
        total_attractions = Attraction.query.count()
        tagged_attractions = Attraction.query.filter_by(auto_tagged=True).count()
        
        # Get tag counts by type
        tag_counts = db.session.query(
            AttractionTag.tag_type,
            db.func.count(AttractionTag.id)
        ).group_by(AttractionTag.tag_type).all()
        
        # Get most common tags
        common_tags = db.session.query(
            AttractionTag.tag_name,
            db.func.count(AttractionTag.id).label('count')
        ).group_by(AttractionTag.tag_name).order_by(
            db.func.count(AttractionTag.id).desc()
        ).limit(10).all()
        
        return {
            'total_attractions': total_attractions,
            'tagged_attractions': tagged_attractions,
            'tagging_coverage': tagged_attractions / total_attractions if total_attractions > 0 else 0,
            'tags_by_type': dict(tag_counts),
            'most_common_tags': [{'tag': tag, 'count': count} for tag, count in common_tags],
            'avg_tags_per_attraction': db.session.query(
                db.func.avg(db.func.count(AttractionTag.id))
            ).select_from(AttractionTag).group_by(AttractionTag.attraction_id).scalar() or 0
        }
    
    except Exception as e:
        logger.error(f"Error getting tagging stats: {str(e)}")
        return {'error': str(e)}


def get_tag_suggestions_for_text(text: str) -> Dict:
    """
    Get tag suggestions for arbitrary text.
    
    Args:
        text: Text to analyze
        
    Returns:
        dict: Tag suggestions
    """
    try:
        tagger = AutoTagger()
        suggestions = tagger.get_tag_suggestions(text)
        
        return {
            'text': text[:100] + '...' if len(text) > 100 else text,
            'suggestions': suggestions
        }
    
    except Exception as e:
        logger.error(f"Error getting tag suggestions: {str(e)}")
        return {'error': str(e)}