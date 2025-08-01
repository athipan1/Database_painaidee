"""
Auto-tagging service for generating relevant tags for attractions.
"""
import re
from typing import List, Dict, Optional, Set
from collections import Counter


class AutoTagger:
    """Service for automatically generating tags for attractions."""
    
    def __init__(self):
        # Predefined tag categories for different attraction types
        self.temple_keywords = {
            'temple', 'shrine', 'buddhist', 'wat', 'monastery', 'pagoda', 'stupa',
            'buddha', 'monk', 'meditation', 'prayer', 'sacred', 'holy', 'worship',
            'religious', 'spiritual', 'ancient', 'historic', 'architecture', 'golden',
            'traditional', 'culture'
        }
        
        self.waterfall_keywords = {
            'waterfall', 'cascade', 'falls', 'stream', 'river', 'water', 'natural',
            'nature', 'forest', 'mountain', 'hiking', 'trekking', 'swimming',
            'scenic', 'beautiful', 'pristine', 'fresh', 'cool', 'refreshing',
            'adventure', 'outdoor', 'wildlife', 'tropical', 'jungle'
        }
        
        self.beach_keywords = {
            'beach', 'sea', 'ocean', 'sand', 'shore', 'coast', 'island', 'bay',
            'sunset', 'sunrise', 'swimming', 'diving', 'snorkeling', 'surfing',
            'tropical', 'paradise', 'relaxing', 'peaceful', 'blue', 'crystal'
        }
        
        self.mountain_keywords = {
            'mountain', 'peak', 'summit', 'hill', 'climbing', 'hiking', 'trekking',
            'view', 'panoramic', 'scenic', 'elevation', 'altitude', 'fresh air',
            'adventure', 'nature', 'forest', 'wildlife', 'sunrise', 'sunset'
        }
        
        # General activity and feature tags
        self.activity_tags = {
            'photography', 'sightseeing', 'cultural', 'historical', 'adventure',
            'relaxation', 'family-friendly', 'romantic', 'educational', 'spiritual',
            'outdoor', 'indoor', 'free', 'paid', 'guided-tour', 'self-guided'
        }
        
        # Location-based tags for Thailand
        self.thailand_regions = {
            'bangkok', 'chiang mai', 'phuket', 'pattaya', 'krabi', 'koh samui',
            'ayutthaya', 'sukhothai', 'chiang rai', 'hua hin', 'kanchanaburi',
            'northern thailand', 'southern thailand', 'central thailand',
            'northeastern thailand', 'isaan'
        }
    
    def generate_tags(self, title: str, body: str = "", max_tags: int = 10) -> List[str]:
        """
        Generate tags for an attraction based on title and description.
        
        Args:
            title: Attraction title
            body: Attraction description
            max_tags: Maximum number of tags to return
            
        Returns:
            List of relevant tags
        """
        if not title:
            return []
            
        text = f"{title} {body}".lower()
        generated_tags = set()
        
        # Detect attraction type and add relevant tags
        attraction_type = self._detect_attraction_type(text)
        if attraction_type:
            generated_tags.add(attraction_type)
            
        # Add type-specific tags
        type_specific_tags = self._get_type_specific_tags(text, attraction_type)
        generated_tags.update(type_specific_tags)
        
        # Add activity tags
        activity_tags = self._extract_activity_tags(text)
        generated_tags.update(activity_tags)
        
        # Add location tags
        location_tags = self._extract_location_tags(text)
        generated_tags.update(location_tags)
        
        # Add descriptive tags
        descriptive_tags = self._extract_descriptive_tags(text)
        generated_tags.update(descriptive_tags)
        
        # Remove empty strings and limit results
        filtered_tags = [tag for tag in generated_tags if tag and len(tag) > 2]
        return sorted(filtered_tags)[:max_tags]
    
    def _detect_attraction_type(self, text: str) -> Optional[str]:
        """Detect the main type of attraction."""
        type_scores = {}
        
        # Count keywords for each type
        for keyword in self.temple_keywords:
            if keyword in text:
                type_scores['temple'] = type_scores.get('temple', 0) + 1
                
        for keyword in self.waterfall_keywords:
            if keyword in text:
                type_scores['waterfall'] = type_scores.get('waterfall', 0) + 1
                
        for keyword in self.beach_keywords:
            if keyword in text:
                type_scores['beach'] = type_scores.get('beach', 0) + 1
                
        for keyword in self.mountain_keywords:
            if keyword in text:
                type_scores['mountain'] = type_scores.get('mountain', 0) + 1
        
        # Return the type with highest score
        if type_scores:
            return max(type_scores, key=type_scores.get)
        return None
    
    def _get_type_specific_tags(self, text: str, attraction_type: str) -> Set[str]:
        """Get tags specific to the attraction type."""
        tags = set()
        
        if attraction_type == 'temple':
            for keyword in self.temple_keywords:
                if keyword in text:
                    tags.add(keyword)
        elif attraction_type == 'waterfall':
            for keyword in self.waterfall_keywords:
                if keyword in text:
                    tags.add(keyword)
        elif attraction_type == 'beach':
            for keyword in self.beach_keywords:
                if keyword in text:
                    tags.add(keyword)
        elif attraction_type == 'mountain':
            for keyword in self.mountain_keywords:
                if keyword in text:
                    tags.add(keyword)
                    
        return tags
    
    def _extract_activity_tags(self, text: str) -> Set[str]:
        """Extract activity-related tags."""
        tags = set()
        for activity in self.activity_tags:
            if activity.replace('-', ' ') in text or activity in text:
                tags.add(activity)
        return tags
    
    def _extract_location_tags(self, text: str) -> Set[str]:
        """Extract location-related tags."""
        tags = set()
        for location in self.thailand_regions:
            if location in text:
                tags.add(location)
        return tags
    
    def _extract_descriptive_tags(self, text: str) -> Set[str]:
        """Extract descriptive adjectives and features."""
        descriptive_words = {
            'beautiful', 'stunning', 'magnificent', 'peaceful', 'serene',
            'ancient', 'historic', 'modern', 'traditional', 'unique',
            'popular', 'famous', 'hidden', 'secret', 'local', 'authentic',
            'cultural', 'natural', 'artificial', 'restored', 'preserved'
        }
        
        tags = set()
        for word in descriptive_words:
            if word in text:
                tags.add(word)
        return tags
    
    def get_suggested_tags_for_type(self, attraction_type: str) -> List[str]:
        """Get suggested tags for a specific attraction type."""
        if attraction_type == 'temple':
            return list(self.temple_keywords)[:10]
        elif attraction_type == 'waterfall':
            return list(self.waterfall_keywords)[:10]
        elif attraction_type == 'beach':
            return list(self.beach_keywords)[:10]
        elif attraction_type == 'mountain':
            return list(self.mountain_keywords)[:10]
        else:
            return list(self.activity_tags)[:10]