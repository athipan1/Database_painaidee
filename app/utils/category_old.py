"""
Category utility functions for attraction data processing.
"""

from typing import List, Optional, Any


def normalize_categories(types_list: List[str]) -> Optional[str]:
    """
    Normalize and categorize attraction types into standard categories.
    
    Args:
        types_list: List of category/type strings from external sources
        
    Returns:
        Normalized category string or None if no suitable category found
    """
    if not types_list or not isinstance(types_list, list):
        return None
    
    # Category mappings from external API types to our standard categories
    category_mapping = {
        # Religious/Temple categories
        'place_of_worship': 'วัด/ศาสนสถান',
        'temple': 'วัด/ศาสนสถান',
        'church': 'วัด/ศาสนสถান',
        'mosque': 'วัด/ศาสนสถান',
        'shrine': 'วัด/ศาสนสถان',
        'hindu_temple': 'วัด/ศาสนสถาน',
        'buddhist_temple': 'วัด/ศาสนสถาน',
        
        # Tourist attractions
        'tourist_attraction': 'สถานที่ท่องเที่ยว',
        'point_of_interest': 'สถานที่ท่องเที่ยว',
        'establishment': 'สถานที่ท่องเที่ยว',
        'amusement_park': 'สวนสนุก',
        'zoo': 'สวนสัตว์',
        'aquarium': 'พิพิธภัณฑ์สัตว์น้ำ',
        
        # Cultural/Historical
        'museum': 'พิพิธภัณฌ์',
        'art_gallery': 'หอศิลป์',
        'historical': 'สถานที่ประวัติศาสตร์',
        'landmark': 'สถานที่สำคัญ',
        'cultural': 'วัฒนธรรม',
        
        # Nature/Parks
        'park': 'สวนสาธารณะ',
        'natural_feature': 'แหล่งธรรมชาติ',
        'beach': 'ชายหาด',
        'waterfall': 'น้ำตก',
        'mountain': 'ภูเขา',
        
        # Entertainment
        'night_club': 'สถานบันเทิง',
        'bar': 'สถานบันเทิง',
        'shopping_mall': 'ศูนย์การค้า',
        'market': 'ตลาด',
        
        # Accommodation
        'lodging': 'ที่พัก',
        'hotel': 'โรงแรม',
        'resort': 'รีสอร์ท',
        
        # Food
        'restaurant': 'ร้านอาหาร',
        'food': 'ร้านอาหาร',
        'cafe': 'คาเฟ่',
    }
    
    # Convert all types to lowercase for matching
    types_lower = [t.lower() for t in types_list if isinstance(t, str)]
    
    # Priority order for category selection (more specific first)
    priority_categories = [
        'วัด/ศาสนสถาน',
        'พิพิธภัณฌ์',
        'สวนสนุก',
        'สวนสัตว์',
        'พิพิธภัณฑ์สัตว์น้ำ',
        'หอศิลป์',
        'สถานที่ประวัติศาสตร์',
        'แหล่งธรรมชาติ',
        'ชายหาด',
        'น้ำตก',
        'ภูเขา',
        'สวนสาธารณะ',
        'ศูนย์การค้า',
        'ตลาด',
        'โรงแรม',
        'รีสอร์ท',
        'ที่พัก',
        'ร้านอาหาร',
        'คาเฟ่',
        'สถานบันเทิง',
        'สถานที่สำคัญ',
        'วัฒนธรรม',
        'สถานที่ท่องเที่ยว'
    ]
    
    # Find matching categories
    matched_categories = []
    for type_str in types_lower:
        if type_str in category_mapping:
            category = category_mapping[type_str]
            if category not in matched_categories:
                matched_categories.append(category)
    
    # Return the highest priority category found
    for priority_cat in priority_categories:
        if priority_cat in matched_categories:
            return priority_cat
    
    # If no specific mapping found, try some keyword matching
    keywords_mapping = {
        'วัด': 'วัด/ศาสนสถาน',
        'temple': 'วัด/ศาสนสถาน',
        'พิพิธภัณฑ์': 'พิพิธภัณฌ์',
        'museum': 'พิพิธภัณฌ์',
        'สวน': 'สวนสาธารณะ',
        'park': 'สวนสาธารณะ',
        'ชายหาด': 'ชายหาด',
        'beach': 'ชายหาด',
        'ตลาด': 'ตลาด',
        'market': 'ตลาด',
        'โรงแรม': 'โรงแรม',
        'hotel': 'โรงแรม',
        'ร้านอาหาร': 'ร้านอาหาร',
        'restaurant': 'ร้านอาหาร'
    }
    
    original_text = ' '.join(types_list).lower()
    for keyword, category in keywords_mapping.items():
        if keyword in original_text:
            return category
    
    # Default category if nothing matches
    return 'สถานที่ท่องเที่ยว'