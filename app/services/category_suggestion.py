"""
Category suggestion service for recommending appropriate categories for attractions.
"""
import re
from typing import List, Dict, Optional, Set, Tuple
from collections import Counter


class CategorySuggester:
    """Service for suggesting appropriate categories for attractions."""
    
    def __init__(self):
        # Define category hierarchy and keywords
        self.categories = {
            'Religious & Spiritual': {
                'keywords': {
                    'temple', 'shrine', 'wat', 'monastery', 'pagoda', 'stupa',
                    'buddha', 'buddhist', 'monk', 'meditation', 'prayer',
                    'sacred', 'holy', 'worship', 'religious', 'spiritual',
                    'church', 'mosque', 'cathedral'
                },
                'subcategories': ['Buddhist Temple', 'Hindu Temple', 'Shrine', 'Monastery']
            },
            'Natural Attractions': {
                'keywords': {
                    'waterfall', 'falls', 'cascade', 'mountain', 'hill', 'peak',
                    'forest', 'jungle', 'nature', 'natural', 'wildlife',
                    'national park', 'conservation', 'reserve', 'cave',
                    'hot spring', 'geyser', 'lake', 'river', 'stream'
                },
                'subcategories': ['Waterfall', 'Mountain', 'Forest', 'Cave', 'Hot Spring', 'Lake']
            },
            'Beach & Coastal': {
                'keywords': {
                    'beach', 'sea', 'ocean', 'coast', 'shore', 'island',
                    'bay', 'lagoon', 'coral', 'reef', 'diving', 'snorkeling',
                    'swimming', 'surfing', 'boat', 'ferry', 'pier', 'harbor'
                },
                'subcategories': ['Beach', 'Island', 'Marine Park', 'Diving Site', 'Coastal Town']
            },
            'Historical & Cultural': {
                'keywords': {
                    'historic', 'historical', 'ancient', 'ruins', 'archaeological',
                    'museum', 'palace', 'castle', 'fort', 'monument',
                    'heritage', 'cultural', 'traditional', 'art', 'architecture',
                    'colonial', 'kingdom', 'dynasty', 'civilization'
                },
                'subcategories': ['Historical Site', 'Museum', 'Palace', 'Archaeological Site', 'Monument']
            },
            'Adventure & Outdoor': {
                'keywords': {
                    'hiking', 'trekking', 'climbing', 'adventure', 'outdoor',
                    'zip line', 'bungee', 'rafting', 'kayaking', 'camping',
                    'rock climbing', 'mountaineering', 'trail', 'expedition',
                    'extreme sports', 'adrenaline'
                },
                'subcategories': ['Hiking Trail', 'Adventure Park', 'Extreme Sports', 'Outdoor Activity']
            },
            'Urban & Modern': {
                'keywords': {
                    'city', 'urban', 'modern', 'shopping', 'mall', 'market',
                    'restaurant', 'nightlife', 'entertainment', 'skyscraper',
                    'building', 'tower', 'observation deck', 'rooftop',
                    'street food', 'local market'
                },
                'subcategories': ['Shopping', 'Nightlife', 'Market', 'Observation Deck', 'Urban Park']
            },
            'Entertainment & Recreation': {
                'keywords': {
                    'park', 'zoo', 'aquarium', 'theme park', 'amusement',
                    'recreation', 'entertainment', 'family', 'children',
                    'playground', 'games', 'show', 'performance', 'theater'
                },
                'subcategories': ['Theme Park', 'Zoo', 'Aquarium', 'Recreation Center', 'Entertainment Venue']
            }
        }
        
        # Regional categories specific to Thailand
        self.regional_categories = {
            'Northern Thailand': ['chiang mai', 'chiang rai', 'pai', 'mae hong son', 'lampang'],
            'Central Thailand': ['bangkok', 'ayutthaya', 'sukhothai', 'kanchanaburi', 'lopburi'],
            'Southern Thailand': ['phuket', 'krabi', 'koh samui', 'surat thani', 'phang nga'],
            'Eastern Thailand': ['pattaya', 'koh chang', 'rayong', 'chanthaburi'],
            'Northeastern Thailand (Isaan)': ['khon kaen', 'udon thani', 'nakhon ratchasima', 'ubon ratchathani']
        }
    
    def suggest_categories(
        self, 
        title: str, 
        body: str = "", 
        max_categories: int = 3,
        include_subcategories: bool = True
    ) -> List[Dict[str, any]]:
        """
        Suggest appropriate categories for an attraction.
        
        Args:
            title: Attraction title
            body: Attraction description
            max_categories: Maximum number of categories to suggest
            include_subcategories: Whether to include subcategory suggestions
            
        Returns:
            List of category suggestions with confidence scores
        """
        if not title:
            return []
            
        text = f"{title} {body}".lower()
        category_scores = {}
        
        # Calculate scores for each category
        for category_name, category_data in self.categories.items():
            score = self._calculate_category_score(text, category_data['keywords'])
            if score > 0:
                category_scores[category_name] = score
        
        # Sort categories by score
        sorted_categories = sorted(
            category_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:max_categories]
        
        # Build result with subcategories if requested
        results = []
        for category_name, score in sorted_categories:
            category_result = {
                'category': category_name,
                'confidence': min(score / 10.0, 1.0),  # Normalize to 0-1
                'subcategories': []
            }
            
            if include_subcategories:
                subcategories = self._suggest_subcategories(
                    text, 
                    category_name
                )
                category_result['subcategories'] = subcategories
            
            results.append(category_result)
        
        return results
    
    def _calculate_category_score(self, text: str, keywords: Set[str]) -> int:
        """Calculate relevance score for a category based on keyword matches."""
        score = 0
        for keyword in keywords:
            # Exact match gets full points
            if keyword in text:
                score += 2
            # Partial match gets partial points
            elif any(word in text for word in keyword.split()):
                score += 1
        
        return score
    
    def _suggest_subcategories(self, text: str, category_name: str) -> List[str]:
        """Suggest specific subcategories within a main category."""
        if category_name not in self.categories:
            return []
        
        subcategories = self.categories[category_name].get('subcategories', [])
        relevant_subcategories = []
        
        for subcategory in subcategories:
            subcategory_lower = subcategory.lower()
            # Check if subcategory terms appear in text
            if any(word in text for word in subcategory_lower.split()):
                relevant_subcategories.append(subcategory)
        
        return relevant_subcategories[:3]  # Limit to top 3 subcategories
    
    def get_category_for_attraction_type(self, attraction_type: str) -> Optional[str]:
        """Get the most appropriate category for a known attraction type."""
        type_mapping = {
            'temple': 'Religious & Spiritual',
            'waterfall': 'Natural Attractions',
            'beach': 'Beach & Coastal',
            'mountain': 'Natural Attractions',
            'museum': 'Historical & Cultural',
            'palace': 'Historical & Cultural',
            'market': 'Urban & Modern',
            'park': 'Entertainment & Recreation'
        }
        
        return type_mapping.get(attraction_type.lower())
    
    def suggest_regional_category(self, text: str) -> Optional[str]:
        """Suggest regional category based on location mentions."""
        text_lower = text.lower()
        
        for region, locations in self.regional_categories.items():
            for location in locations:
                if location in text_lower:
                    return region
        
        return None
    
    def get_all_categories(self) -> List[str]:
        """Get list of all available categories."""
        return list(self.categories.keys())
    
    def get_category_keywords(self, category_name: str) -> Set[str]:
        """Get keywords associated with a specific category."""
        if category_name in self.categories:
            return self.categories[category_name]['keywords']
        return set()
    
    def validate_category_assignment(
        self, 
        text: str, 
        assigned_category: str
    ) -> Dict[str, any]:
        """
        Validate if an assigned category is appropriate for the given text.
        
        Returns:
            Dictionary with validation results including confidence and suggestions
        """
        if assigned_category not in self.categories:
            return {
                'valid': False,
                'confidence': 0.0,
                'reason': 'Category does not exist',
                'suggestions': self.suggest_categories(text, max_categories=3)
            }
        
        keywords = self.categories[assigned_category]['keywords']
        score = self._calculate_category_score(text.lower(), keywords)
        confidence = min(score / 10.0, 1.0)
        
        valid = confidence > 0.2  # Threshold for validity
        
        result = {
            'valid': valid,
            'confidence': confidence,
            'reason': 'Good match' if valid else 'Low relevance to category keywords'
        }
        
        if not valid:
            result['suggestions'] = self.suggest_categories(text, max_categories=3)
        
        return result