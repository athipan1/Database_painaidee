"""
Data transformation utilities for cleaning and normalizing attraction data.
"""
import re
import logging
from datetime import datetime
from typing import Optional, Dict, Tuple

logger = logging.getLogger(__name__)


class DataTransformer:
    """Utility class for data transformation and normalization."""
    
    # Location category mapping
    LOCATION_CATEGORIES = {
        'วัด': ['วัด', 'temple', 'monastery', 'shrine', 'โบสถ์'],
        'ทะเล': ['ทะเล', 'หาด', 'อ่าว', 'เกาะ', 'sea', 'beach', 'bay', 'island'],
        'ภูเขา': ['ดอย', 'เขา', 'mountain', 'hill', 'peak', 'ภูเขา'],  # Moved ภูเขา to end, removed single ภู
        'น้ำตก': ['น้ำตก', 'waterfall', 'cascade', 'falls'],
        'อุทยาน': ['อุทยาน', 'สวน', 'park', 'garden', 'national park'],
        'พิพิธภัณฑ์': ['พิพิธภัณฑ์', 'museum', 'gallery', 'exhibition'],
        'ตลาด': ['ตลาด', 'market', 'bazaar', 'shopping'],
        'อื่นๆ': []  # Default category
    }
    
    # Thai provinces for address parsing
    THAI_PROVINCES = [
        'กรุงเทพมหานคร', 'กระบี่', 'กาญจนบุรี', 'กาฬสินธุ์', 'กำแพงเพชร', 'ขอนแก่น',
        'จันทบุรี', 'ฉะเชิงเทรา', 'ชลบุรี', 'ชัยนาท', 'ชัยภูมิ', 'ชุมพร', 'เชียงราย',
        'เชียงใหม่', 'ตรัง', 'ตราด', 'ตาก', 'นครนายก', 'นครปฐม', 'นครพนม', 'นครราชสีมา',
        'นครศรีธรรมราช', 'นครสวรรค์', 'นนทบุรี', 'นราธิวาส', 'น่าน', 'บึงกาฬ', 'บุรีรัมย์',
        'ปทุมธานี', 'ประจวบคีรีขันธ์', 'ปราจีนบุรี', 'ปัตตานี', 'พระนครศรีอยุธยา', 'พังงา',
        'พัทลุง', 'พิจิตร', 'พิษณุโลก', 'เพชรบุรี', 'เพชรบูรณ์', 'แพร่', 'ภูเก็ต', 'มหาสารคาม',
        'มุกดาหาร', 'แม่ฮ่องสอน', 'ยโสธร', 'ยะลา', 'ร้อยเอ็ด', 'ระนอง', 'ระยอง', 'ราชบุรี',
        'ลพบุรี', 'ลำปาง', 'ลำพูน', 'เลย', 'ศรีสะเกษ', 'สกลนคร', 'สงขลา', 'สตูล', 'สมุทรปราการ',
        'สมุทรสงคราม', 'สมุทรสาคร', 'สระแก้ว', 'สระบุรี', 'สิงห์บุรี', 'สุโขทัย', 'สุพรรณบุรี',
        'สุราษฎร์ธานี', 'สุรินทร์', 'หนองคาย', 'หนองบัวลำภู', 'อ่างทอง', 'อำนาจเจริญ',
        'อุดรธานี', 'อุตรดิตถ์', 'อุทัยธานี', 'อุบลราชธานี'
    ]
    
    @staticmethod
    def normalize_date(date_str: str) -> Optional[datetime]:
        """
        Convert various date formats to standard YYYY-MM-DD format.
        
        Args:
            date_str: Date string in various formats (dd/mm/yyyy, dd-mm-yyyy, etc.)
            
        Returns:
            datetime object or None if parsing fails
        """
        if not date_str:
            return None
            
        # Remove extra whitespace
        date_str = date_str.strip()
        
        # Common date patterns
        patterns = [
            r'(\d{1,2})/(\d{1,2})/(\d{4})',  # dd/mm/yyyy or d/m/yyyy
            r'(\d{1,2})-(\d{1,2})-(\d{4})',  # dd-mm-yyyy or d-m-yyyy
            r'(\d{1,2})\.(\d{1,2})\.(\d{4})', # dd.mm.yyyy or d.m.yyyy
            r'(\d{4})-(\d{1,2})-(\d{1,2})',  # yyyy-mm-dd (already normalized)
            r'(\d{4})/(\d{1,2})/(\d{1,2})',  # yyyy/mm/dd
        ]
        
        for pattern in patterns:
            match = re.match(pattern, date_str)
            if match:
                try:
                    if pattern.startswith(r'(\d{4})'):  # yyyy first
                        year, month, day = match.groups()
                    else:  # dd/mm/yyyy format
                        day, month, year = match.groups()
                    
                    return datetime(int(year), int(month), int(day))
                except ValueError as e:
                    logger.warning(f"Invalid date values in '{date_str}': {e}")
                    continue
        
        logger.warning(f"Could not parse date: '{date_str}'")
        return None
    
    @staticmethod
    def parse_address(address_str: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Parse Thai address to extract province and district.
        
        Args:
            address_str: Full address string
            
        Returns:
            Tuple of (province, district) or (None, None) if parsing fails
        """
        if not address_str:
            return None, None
        
        address_str = address_str.strip()
        province = None
        district = None
        
        # Find province
        for prov in DataTransformer.THAI_PROVINCES:
            if prov in address_str:
                province = prov
                break
        
        # Find district (อำเภอ or เขต patterns)
        district_patterns = [
            r'อำเภอ([ก-๙\s]+?)(?:\s|$|,)',
            r'เขต([ก-๙\s]+?)(?:\s|$|,)',
            r'อ\.([ก-๙\s]+?)(?:\s|$|,)',
        ]
        
        for pattern in district_patterns:
            match = re.search(pattern, address_str)
            if match:
                district = match.group(1).strip()
                break
        
        return province, district
    
    @staticmethod
    def categorize_location(title: str, description: str = '') -> str:
        """
        Categorize location based on title and description with position-aware scoring.
        
        Args:
            title: Location title/name
            description: Location description
            
        Returns:
            Category string ('วัด', 'ภูเขา', 'ทะเล', etc.)
        """
        # Give higher priority to words at the beginning of title
        title_text = title.lower().strip()
        description_text = description.lower().strip()
        
        # Use scoring system to handle conflicts
        category_scores = {}
        
        for category, keywords in DataTransformer.LOCATION_CATEGORIES.items():
            if category == 'อื่นๆ':  # Skip default category
                continue
                
            score = 0
            
            for keyword in keywords:
                keyword_lower = keyword.lower()
                
                # Check in title (higher weight, position matters)
                title_pos = title_text.find(keyword_lower)
                if title_pos >= 0:
                    # Higher score for words at the beginning
                    position_weight = max(1, 5 - title_pos // 2)  # Decreases with position
                    length_weight = len(keyword)
                    title_score = length_weight * position_weight * 2  # 2x for being in title
                    score += title_score
                
                # Check in description (lower weight)
                if keyword_lower in description_text:
                    desc_score = len(keyword)
                    score += desc_score
            
            if score > 0:
                category_scores[category] = score
        
        if category_scores:
            # Return category with highest score
            return max(category_scores.items(), key=lambda x: x[1])[0]
        
        return 'อื่นๆ'  # Default category
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean and normalize text data.
        
        Args:
            text: Raw text string
            
        Returns:
            Cleaned text string
        """
        if not text:
            return ''
        
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove HTML tags if any
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove special characters but keep Thai and basic punctuation
        text = re.sub(r'[^\w\s\u0E00-\u0E7F.,!?()-]', '', text)
        
        return text
    
    @staticmethod
    def transform_attraction_data(raw_data: Dict) -> Dict:
        """
        Apply all transformations to attraction data.
        
        Args:
            raw_data: Raw attraction data from API
            
        Returns:
            Transformed data dictionary
        """
        transformed = raw_data.copy()
        
        # Clean text fields
        if 'title' in transformed:
            transformed['title'] = DataTransformer.clean_text(transformed['title'])
        
        if 'body' in transformed:
            transformed['body'] = DataTransformer.clean_text(transformed['body'])
        
        # Parse date if present
        if 'date' in raw_data:
            normalized_date = DataTransformer.normalize_date(raw_data['date'])
            transformed['normalized_date'] = normalized_date
            transformed['original_date'] = raw_data['date']
        
        # Parse address if present
        if 'address' in raw_data:
            province, district = DataTransformer.parse_address(raw_data['address'])
            transformed['province'] = province
            transformed['district'] = district
        
        # Categorize location
        title = transformed.get('title', '')
        description = transformed.get('body', '')
        transformed['location_category'] = DataTransformer.categorize_location(title, description)
        
        return transformed