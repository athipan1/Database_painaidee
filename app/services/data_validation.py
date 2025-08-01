"""
Data validation service for validating and cleaning attraction data.
"""
import re
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import json


class DataValidator:
    """Service for validating and cleaning attraction data."""
    
    def __init__(self):
        # Validation rules and patterns
        self.email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        self.url_pattern = re.compile(r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))?)?')
        self.phone_pattern = re.compile(r'(\+\d{1,3}[-.\s]?)?(\d{1,4}[-.\s]?)?(\d{1,4}[-.\s]?)(\d{1,9})')
        
        # Thai province validation
        self.thai_provinces = {
            'bangkok', 'samut prakan', 'nonthaburi', 'pathum thani', 'phra nakhon si ayutthaya',
            'ang thong', 'lopburi', 'sing buri', 'chai nat', 'saraburi', 'chonburi', 'rayong',
            'chanthaburi', 'trat', 'chachoengsao', 'prachin buri', 'nakhon nayok', 'sa kaeo',
            'nakhon ratchasima', 'buri ram', 'surin', 'si sa ket', 'ubon ratchathani',
            'yasothon', 'chaiyaphum', 'amnat charoen', 'nong bua lam phu', 'khon kaen',
            'udon thani', 'loei', 'nong khai', 'maha sarakham', 'roi et', 'kalasin',
            'sakon nakhon', 'nakhon phanom', 'mukdahan',
            'chiang mai', 'lamphun', 'lampang', 'uttaradit', 'phrae', 'nan', 'phayao',
            'chiang rai', 'mae hong son', 'nakhon sawan', 'uthai thani', 'kamphaeng phet',
            'tak', 'sukhothai', 'phitsanulok', 'phichit', 'phetchabun',
            'ratchaburi', 'kanchanaburi', 'suphan buri', 'nakhon pathom', 'samut sakhon',
            'samut songkhram', 'phetchaburi', 'prachuap khiri khan',
            'nakhon si thammarat', 'krabi', 'phang nga', 'phuket', 'surat thani',
            'ranong', 'chumphon', 'songkhla', 'satun', 'trang', 'phatthalung', 'pattani',
            'yala', 'narathiwat'
        }
        
        # Common data quality issues
        self.spam_indicators = [
            'click here', 'free money', 'guaranteed', 'act now', 'limited time',
            'casino', 'poker', 'gambling', 'viagra', 'pharmacy'
        ]
        
        self.inappropriate_words = [
            'hate', 'violence', 'discrimination', 'offensive', 'inappropriate'
        ]
    
    def validate_attraction_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and clean attraction data.
        
        Args:
            data: Dictionary containing attraction data
            
        Returns:
            Dictionary with validation results and cleaned data
        """
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'cleaned_data': data.copy(),
            'quality_score': 0.0
        }
        
        # Validate required fields
        required_fields = ['title', 'external_id']
        for field in required_fields:
            if field not in data or not data[field]:
                validation_result['errors'].append(f"Missing required field: {field}")
                validation_result['valid'] = False
        
        # Validate and clean title
        if 'title' in data:
            title_validation = self._validate_title(data['title'])
            validation_result['cleaned_data']['title'] = title_validation['cleaned']
            validation_result['errors'].extend(title_validation['errors'])
            validation_result['warnings'].extend(title_validation['warnings'])
        
        # Validate and clean body/description
        if 'body' in data and data['body']:
            body_validation = self._validate_description(data['body'])
            validation_result['cleaned_data']['body'] = body_validation['cleaned']
            validation_result['errors'].extend(body_validation['errors'])
            validation_result['warnings'].extend(body_validation['warnings'])
        
        # Validate coordinates
        if 'latitude' in data and 'longitude' in data:
            coord_validation = self._validate_coordinates(
                data.get('latitude'), 
                data.get('longitude')
            )
            validation_result['errors'].extend(coord_validation['errors'])
            validation_result['warnings'].extend(coord_validation['warnings'])
        
        # Validate province
        if 'province' in data and data['province']:
            province_validation = self._validate_province(data['province'])
            validation_result['cleaned_data']['province'] = province_validation['cleaned']
            validation_result['warnings'].extend(province_validation['warnings'])
        
        # Validate external_id
        if 'external_id' in data:
            id_validation = self._validate_external_id(data['external_id'])
            validation_result['errors'].extend(id_validation['errors'])
        
        # Calculate quality score
        validation_result['quality_score'] = self._calculate_quality_score(
            validation_result['cleaned_data'], 
            validation_result['errors'], 
            validation_result['warnings']
        )
        
        return validation_result
    
    def _validate_title(self, title: str) -> Dict[str, Any]:
        """Validate and clean attraction title."""
        result = {
            'cleaned': title,
            'errors': [],
            'warnings': []
        }
        
        if not title or not title.strip():
            result['errors'].append("Title cannot be empty")
            return result
        
        # Clean title
        cleaned_title = title.strip()
        
        # Check length
        if len(cleaned_title) < 3:
            result['errors'].append("Title too short (minimum 3 characters)")
        elif len(cleaned_title) > 200:
            result['warnings'].append("Title too long (maximum 200 characters recommended)")
            cleaned_title = cleaned_title[:200]
        
        # Check for spam indicators
        title_lower = cleaned_title.lower()
        for indicator in self.spam_indicators:
            if indicator in title_lower:
                result['warnings'].append(f"Potential spam indicator detected: {indicator}")
        
        # Check for inappropriate content
        for word in self.inappropriate_words:
            if word in title_lower:
                result['errors'].append(f"Inappropriate content detected: {word}")
        
        # Remove excessive whitespace and special characters
        cleaned_title = re.sub(r'\s+', ' ', cleaned_title)
        cleaned_title = re.sub(r'[^\w\s\-\(\)\[\].,!?]', '', cleaned_title)
        
        result['cleaned'] = cleaned_title
        return result
    
    def _validate_description(self, description: str) -> Dict[str, Any]:
        """Validate and clean attraction description."""
        result = {
            'cleaned': description,
            'errors': [],
            'warnings': []
        }
        
        if not description:
            return result
        
        # Clean description
        cleaned_desc = description.strip()
        
        # Check length
        if len(cleaned_desc) > 5000:
            result['warnings'].append("Description too long (maximum 5000 characters recommended)")
            cleaned_desc = cleaned_desc[:5000]
        
        # Check for spam indicators
        desc_lower = cleaned_desc.lower()
        for indicator in self.spam_indicators:
            if indicator in desc_lower:
                result['warnings'].append(f"Potential spam indicator detected: {indicator}")
        
        # Check for inappropriate content
        for word in self.inappropriate_words:
            if word in desc_lower:
                result['errors'].append(f"Inappropriate content detected: {word}")
        
        # Clean up formatting
        cleaned_desc = re.sub(r'\n\s*\n', '\n\n', cleaned_desc)  # Normalize line breaks
        cleaned_desc = re.sub(r'\s+', ' ', cleaned_desc)  # Normalize spaces
        
        result['cleaned'] = cleaned_desc
        return result
    
    def _validate_coordinates(self, latitude: Any, longitude: Any) -> Dict[str, Any]:
        """Validate geographical coordinates."""
        result = {
            'errors': [],
            'warnings': []
        }
        
        try:
            if latitude is not None:
                lat = float(latitude)
                if not (-90 <= lat <= 90):
                    result['errors'].append("Latitude must be between -90 and 90")
                elif not (5.0 <= lat <= 21.0):  # Thailand's approximate latitude range
                    result['warnings'].append("Latitude outside Thailand's typical range")
            
            if longitude is not None:
                lng = float(longitude)
                if not (-180 <= lng <= 180):
                    result['errors'].append("Longitude must be between -180 and 180")
                elif not (97.0 <= lng <= 106.0):  # Thailand's approximate longitude range
                    result['warnings'].append("Longitude outside Thailand's typical range")
        
        except (ValueError, TypeError):
            result['errors'].append("Invalid coordinate format")
        
        return result
    
    def _validate_province(self, province: str) -> Dict[str, Any]:
        """Validate and normalize province name."""
        result = {
            'cleaned': province,
            'warnings': []
        }
        
        if not province:
            return result
        
        cleaned_province = province.strip().lower()
        
        # Check if province exists in Thailand
        if cleaned_province not in self.thai_provinces:
            # Try to find close match
            close_match = self._find_close_province_match(cleaned_province)
            if close_match:
                result['cleaned'] = close_match.title()
                result['warnings'].append(f"Province name corrected from '{province}' to '{close_match.title()}'")
            else:
                result['warnings'].append(f"Province '{province}' not recognized as Thai province")
        else:
            result['cleaned'] = cleaned_province.title()
        
        return result
    
    def _validate_external_id(self, external_id: Any) -> Dict[str, Any]:
        """Validate external ID."""
        result = {
            'errors': []
        }
        
        if external_id is None:
            result['errors'].append("External ID cannot be null")
            return result
        
        try:
            int(external_id)
        except (ValueError, TypeError):
            result['errors'].append("External ID must be a valid integer")
        
        return result
    
    def _find_close_province_match(self, province: str) -> Optional[str]:
        """Find close match for province name using simple string similarity."""
        province_lower = province.lower()
        
        # Check for partial matches
        for thai_province in self.thai_provinces:
            if province_lower in thai_province or thai_province in province_lower:
                return thai_province
        
        # Check for common abbreviations or alternative names
        abbreviations = {
            'bkk': 'bangkok',
            'cm': 'chiang mai',
            'phuket': 'phuket',
            'krabi': 'krabi',
            'pattaya': 'chonburi'  # Pattaya is in Chonburi province
        }
        
        if province_lower in abbreviations:
            return abbreviations[province_lower]
        
        return None
    
    def _calculate_quality_score(
        self, 
        data: Dict[str, Any], 
        errors: List[str], 
        warnings: List[str]
    ) -> float:
        """Calculate data quality score (0.0 to 1.0)."""
        if errors:
            return 0.0  # Invalid data gets 0 score
        
        score = 1.0
        
        # Deduct for warnings
        score -= len(warnings) * 0.1
        
        # Bonus for completeness
        optional_fields = ['body', 'province', 'latitude', 'longitude']
        completed_fields = sum(1 for field in optional_fields if data.get(field))
        completeness_bonus = completed_fields / len(optional_fields) * 0.2
        score += completeness_bonus
        
        # Bonus for good description length
        if data.get('body') and 50 <= len(data['body']) <= 1000:
            score += 0.1
        
        # Bonus for coordinates
        if data.get('latitude') and data.get('longitude'):
            score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def validate_batch(self, attractions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate a batch of attractions."""
        results = []
        summary = {
            'total': len(attractions),
            'valid': 0,
            'invalid': 0,
            'warnings': 0,
            'avg_quality_score': 0.0
        }
        
        total_quality = 0.0
        
        for attraction in attractions:
            result = self.validate_attraction_data(attraction)
            results.append(result)
            
            if result['valid']:
                summary['valid'] += 1
            else:
                summary['invalid'] += 1
            
            if result['warnings']:
                summary['warnings'] += 1
            
            total_quality += result['quality_score']
        
        if attractions:
            summary['avg_quality_score'] = total_quality / len(attractions)
        
        return {
            'summary': summary,
            'results': results
        }