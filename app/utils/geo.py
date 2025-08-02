"""
Geographic utility functions for attraction data processing.
"""

import re
from typing import Optional


def extract_province_from_address(address: str) -> Optional[str]:
    """
    Extract province name from a formatted address string.
    
    Args:
        address: Formatted address string
        
    Returns:
        Province name if found, None otherwise
    """
    if not address or not isinstance(address, str):
        return None
    
    # Thai provinces mapping (common variations)
    thai_provinces = {
        'กรุงเทพ': 'กรุงเทพมหานคร',
        'กรุงเทพมหานคร': 'กรุงเทพมหานคร',
        'bangkok': 'กรุงเทพมหานคร',
        'เชียงใหม่': 'เชียงใหม่',
        'chiang mai': 'เชียงใหม่',
        'ภูเก็ต': 'ภูเก็ต',
        'phuket': 'ภูเก็ต',
        'สุราษฎร์ธานี': 'สุราษฎร์ธานี',
        'surat thani': 'สุราษฎร์ธานี',
        'กระบี่': 'กระบี่',
        'krabi': 'กระบี่',
        'ชลบุรี': 'ชลบุรี',
        'chonburi': 'ชลบุรี',
        'ระยอง': 'ระยอง',
        'rayong': 'ระยอง',
        'ตราด': 'ตราด',
        'trat': 'ตราด',
        'สงขลา': 'สงขลา',
        'songkhla': 'สงขลา',
        'นนทบุรี': 'นนทบุรี',
        'nonthaburi': 'นนทบุรี',
        'ปทุมธานี': 'ปทุมธานี',
        'pathum thani': 'ปทุมธานี',
        'สมุทรปราการ': 'สมุทรปราการ',
        'samut prakan': 'สมุทรปราการ'
    }
    
    address_lower = address.lower()
    
    # Try to find province names in the address
    for province_key, province_value in thai_provinces.items():
        if province_key.lower() in address_lower:
            return province_value
    
    # Try common patterns for Thai provinces
    province_patterns = [
        r'จ\.([ก-๏]+)', # จ.ภูเก็ต
        r'จังหวัด([ก-๏]+)', # จังหวัดภูเก็ต
        r'([ก-๏]+)\s*Province', # ภูเก็ต Province
        r'Province\s+([ก-๏]+)', # Province ภูเก็ต
    ]
    
    for pattern in province_patterns:
        match = re.search(pattern, address, re.IGNORECASE)
        if match:
            province_name = match.group(1).strip()
            # Check if this matches any known province
            if province_name.lower() in thai_provinces:
                return thai_provinces[province_name.lower()]
            return province_name
    
    return None