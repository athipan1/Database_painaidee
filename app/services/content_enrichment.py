"""
AI Content Enrichment service for generating place descriptions, 
multilingual content, key features, and images.
"""
import json
import os
import re
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from googletrans import Translator
    GOOGLETRANS_AVAILABLE = True
except ImportError:
    GOOGLETRANS_AVAILABLE = False

try:
    from langdetect import detect
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False


class ContentEnrichmentService:
    """AI-powered content enrichment for attraction data."""
    
    def __init__(self):
        self.openai_available = OPENAI_AVAILABLE
        self.translator_available = GOOGLETRANS_AVAILABLE
        self.langdetect_available = LANGDETECT_AVAILABLE
        
        # Initialize OpenAI client if available
        if self.openai_available:
            try:
                openai.api_key = os.getenv('OPENAI_API_KEY')
                self.openai_model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
                self.openai_enabled = bool(openai.api_key)
            except Exception as e:
                print(f"OpenAI initialization failed: {e}")
                self.openai_enabled = False
        else:
            self.openai_enabled = False
        
        # Initialize translator if available
        if self.translator_available:
            try:
                self.translator = Translator()
            except Exception as e:
                print(f"Translator initialization failed: {e}")
                self.translator_available = False
        
        # Configuration
        self.supported_languages = ['en', 'th', 'zh']
        self.key_features_keywords = [
            'family-friendly', 'family friendly', 'kids', 'children',
            'great view', 'scenic view', 'panoramic', 'view',
            'beachfront', 'beach', 'waterfront', 'sea view', 'ocean view',
            'historical', 'ancient', 'heritage', 'traditional',
            'modern', 'contemporary', 'new',
            'romantic', 'couples', 'honeymoon',
            'adventure', 'exciting', 'thrilling',
            'peaceful', 'quiet', 'serene', 'relaxing',
            'cultural', 'local culture', 'authentic',
            'shopping', 'market', 'mall',
            'dining', 'restaurant', 'food', 'cuisine',
            'nightlife', 'entertainment', 'bar', 'club',
            'nature', 'natural', 'wildlife', 'park',
            'religious', 'temple', 'shrine', 'church',
            'architectural', 'building', 'design',
            'photography', 'instagram', 'photo-worthy'
        ]
    
    def generate_place_description(self, attraction_data: Dict) -> Dict[str, Any]:
        """
        Generate rich description for a place using GPT or fallback methods.
        
        Args:
            attraction_data: Dictionary containing attraction information
            
        Returns:
            Dict with generated description and metadata
        """
        title = attraction_data.get('title', '')
        body = attraction_data.get('body', '')
        province = attraction_data.get('province', '')
        
        if self.openai_enabled:
            return self._generate_description_with_gpt(title, body, province)
        else:
            return self._generate_description_fallback(title, body, province)
    
    def _generate_description_with_gpt(self, title: str, body: str, province: str) -> Dict[str, Any]:
        """Generate description using GPT."""
        try:
            prompt = self._create_description_prompt(title, body, province)
            
            response = openai.Completion.create(
                model="text-davinci-003",  # Using available model for older OpenAI version
                prompt=prompt,
                max_tokens=300,
                temperature=0.7
            )
            
            generated_text = response.choices[0].text.strip()
            
            return {
                'success': True,
                'description': generated_text,
                'method': 'gpt',
                'model': 'text-davinci-003',
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"GPT description generation failed: {e}")
            return self._generate_description_fallback(title, body, province)
    
    def _generate_description_fallback(self, title: str, body: str, province: str) -> Dict[str, Any]:
        """Generate description using rule-based methods."""
        try:
            # Create enhanced description using template-based approach
            description = self._create_fallback_description(title, body, province)
            
            return {
                'success': True,
                'description': description,
                'method': 'fallback',
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'method': 'fallback'
            }
    
    def _create_description_prompt(self, title: str, body: str, province: str) -> str:
        """Create prompt for GPT description generation."""
        prompt = f"""
        Create an engaging and informative description for this Thai attraction:
        
        Title: {title}
        Existing Description: {body or 'No description available'}
        Province: {province or 'Unknown'}
        
        Requirements:
        - Write 2-3 paragraphs (150-250 words)
        - Include what makes this place special
        - Mention practical visitor information if relevant
        - Use engaging but informative tone
        - Focus on unique features and experiences
        - Keep it suitable for tourists and locals
        
        Generate only the description, no additional text.
        """
        return prompt.strip()
    
    def _create_fallback_description(self, title: str, body: str, province: str) -> str:
        """Create description using template-based approach."""
        templates = [
            f"Discover the beauty of {title}, a remarkable destination in {province or 'Thailand'}. {body or 'This unique attraction offers visitors an unforgettable experience.'} Whether you're seeking adventure, culture, or relaxation, this location provides something special for every traveler.",
            
            f"{title} stands as one of {province or 'Thailand'}'s most intriguing attractions. {body or 'Visitors can expect to be captivated by its distinctive charm and character.'} This destination perfectly combines natural beauty with cultural significance, making it a must-visit location.",
            
            f"Experience the wonder of {title}, nestled in the heart of {province or 'Thailand'}. {body or 'This exceptional place offers a perfect blend of tradition and modern appeal.'} From its stunning features to its welcoming atmosphere, every visitor leaves with lasting memories."
        ]
        
        # Choose template based on title length
        template_index = len(title) % len(templates)
        return templates[template_index]
    
    def generate_multilingual_content(self, text: str, target_languages: List[str] = None) -> Dict[str, Any]:
        """
        Generate multilingual versions of content.
        
        Args:
            text: Original text to translate
            target_languages: List of language codes (default: ['en', 'th', 'zh'])
            
        Returns:
            Dict with translations for each language
        """
        if target_languages is None:
            target_languages = ['en', 'th', 'zh']
        
        if self.translator_available:
            return self._translate_with_googletrans(text, target_languages)
        else:
            return self._translate_fallback(text, target_languages)
    
    def _translate_with_googletrans(self, text: str, target_languages: List[str]) -> Dict[str, Any]:
        """Translate using Google Translate."""
        translations = {'original': text}
        
        try:
            # Detect source language
            if self.langdetect_available:
                try:
                    source_lang = detect(text)
                except:
                    source_lang = 'auto'
            else:
                source_lang = 'auto'
            
            for lang in target_languages:
                try:
                    result = self.translator.translate(text, src=source_lang, dest=lang)
                    translations[lang] = result.text
                except Exception as e:
                    print(f"Translation to {lang} failed: {e}")
                    translations[lang] = text  # Fallback to original
            
            return {
                'success': True,
                'translations': translations,
                'method': 'googletrans',
                'source_language': source_lang,
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Google Translate failed: {e}")
            return self._translate_fallback(text, target_languages)
    
    def _translate_fallback(self, text: str, target_languages: List[str]) -> Dict[str, Any]:
        """Fallback translation (returns original text with note)."""
        translations = {'original': text}
        
        for lang in target_languages:
            if lang == 'en':
                translations[lang] = text  # Assume original is English or keep as-is
            else:
                translations[lang] = f"{text} [Translation to {lang} not available]"
        
        return {
            'success': True,
            'translations': translations,
            'method': 'fallback',
            'note': 'Translation service not available - returning original text',
            'generated_at': datetime.utcnow().isoformat()
        }
    
    def extract_key_features(self, text: str) -> Dict[str, Any]:
        """
        Extract key features from attraction description.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dict with extracted features
        """
        try:
            text_lower = text.lower()
            found_features = []
            
            # Check for key feature keywords
            for feature in self.key_features_keywords:
                if feature.lower() in text_lower:
                    found_features.append(feature)
            
            # Remove duplicates and sort
            found_features = sorted(list(set(found_features)))
            
            # Categorize features
            categories = self._categorize_features(found_features)
            
            return {
                'success': True,
                'features': found_features,
                'categories': categories,
                'feature_count': len(found_features),
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'features': [],
                'categories': {}
            }
    
    def _categorize_features(self, features: List[str]) -> Dict[str, List[str]]:
        """Categorize features into groups."""
        categories = {
            'family': [],
            'scenery': [],
            'location': [],
            'style': [],
            'activities': [],
            'atmosphere': [],
            'other': []
        }
        
        category_keywords = {
            'family': ['family-friendly', 'family friendly', 'kids', 'children'],
            'scenery': ['great view', 'scenic view', 'panoramic', 'view', 'nature', 'natural'],
            'location': ['beachfront', 'beach', 'waterfront', 'sea view', 'ocean view'],
            'style': ['historical', 'ancient', 'heritage', 'traditional', 'modern', 'contemporary'],
            'activities': ['adventure', 'shopping', 'dining', 'nightlife', 'photography'],
            'atmosphere': ['romantic', 'peaceful', 'quiet', 'serene', 'relaxing', 'cultural']
        }
        
        for feature in features:
            categorized = False
            for category, keywords in category_keywords.items():
                if any(keyword in feature.lower() for keyword in keywords):
                    categories[category].append(feature)
                    categorized = True
                    break
            
            if not categorized:
                categories['other'].append(feature)
        
        # Remove empty categories
        return {k: v for k, v in categories.items() if v}
    
    def generate_images(self, attraction_data: Dict, num_images: int = 1) -> Dict[str, Any]:
        """
        Generate images for attraction using DALL-E or fallback methods.
        
        Args:
            attraction_data: Dictionary containing attraction information
            num_images: Number of images to generate
            
        Returns:
            Dict with generated image URLs or placeholders
        """
        title = attraction_data.get('title', '')
        body = attraction_data.get('body', '')
        province = attraction_data.get('province', '')
        
        if self.openai_enabled:
            return self._generate_images_with_dalle(title, body, province, num_images)
        else:
            return self._generate_images_fallback(title, body, province, num_images)
    
    def _generate_images_with_dalle(self, title: str, body: str, province: str, num_images: int) -> Dict[str, Any]:
        """Generate images using DALL-E."""
        try:
            prompt = self._create_image_prompt(title, body, province)
            
            response = openai.Image.create(
                prompt=prompt,
                n=min(num_images, 4),  # DALL-E supports up to 4 images
                size="1024x1024"
            )
            
            image_urls = []
            for image in response['data']:
                image_urls.append(image['url'])
            
            return {
                'success': True,
                'image_urls': image_urls,
                'method': 'dall-e',
                'prompt': prompt,
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"DALL-E image generation failed: {e}")
            return self._generate_images_fallback(title, body, province, num_images)
    
    def _generate_images_fallback(self, title: str, body: str, province: str, num_images: int) -> Dict[str, Any]:
        """Generate placeholder images with relevant URLs."""
        try:
            # Create placeholder image URLs using a service like Unsplash
            base_keywords = ['thailand', 'travel', 'attraction', 'tourism']
            if province:
                base_keywords.append(province.lower())
            
            keywords_from_title = re.findall(r'\w+', title.lower())
            search_terms = base_keywords + keywords_from_title[:3]  # Limit to avoid overly long URLs
            
            search_query = '+'.join(search_terms[:5])  # Limit to 5 terms
            
            image_urls = []
            for i in range(num_images):
                # Using Unsplash as placeholder image service
                url = f"https://source.unsplash.com/1024x768/?{search_query}&sig={i}"
                image_urls.append(url)
            
            return {
                'success': True,
                'image_urls': image_urls,
                'method': 'placeholder',
                'search_query': search_query,
                'note': 'Using placeholder images from Unsplash',
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'image_urls': [],
                'method': 'fallback'
            }
    
    def _create_image_prompt(self, title: str, body: str, province: str) -> str:
        """Create prompt for DALL-E image generation."""
        prompt_parts = []
        
        # Base description
        prompt_parts.append(f"A beautiful photograph of {title}")
        
        # Add location context
        if province:
            prompt_parts.append(f"located in {province}, Thailand")
        else:
            prompt_parts.append("in Thailand")
        
        # Add style descriptors
        prompt_parts.append("showing the authentic Thai culture and natural beauty")
        prompt_parts.append("high quality, professional photography, vibrant colors")
        prompt_parts.append("suitable for travel brochure, attractive to tourists")
        
        return ", ".join(prompt_parts)
    
    def enrich_attraction(self, attraction_data: Dict) -> Dict[str, Any]:
        """
        Perform comprehensive content enrichment for an attraction.
        
        Args:
            attraction_data: Dictionary containing attraction information
            
        Returns:
            Dict with all enrichment results
        """
        results = {
            'attraction_id': attraction_data.get('id'),
            'success': True,
            'enriched_at': datetime.utcnow().isoformat(),
            'features': {}
        }
        
        try:
            # Generate enhanced description
            description_result = self.generate_place_description(attraction_data)
            results['features']['description'] = description_result
            
            # Extract key features
            text_to_analyze = attraction_data.get('body', '') or attraction_data.get('title', '')
            if description_result.get('success'):
                text_to_analyze += " " + description_result.get('description', '')
            
            features_result = self.extract_key_features(text_to_analyze)
            results['features']['key_features'] = features_result
            
            # Generate multilingual content
            content_to_translate = description_result.get('description') or text_to_analyze
            if content_to_translate:
                multilingual_result = self.generate_multilingual_content(content_to_translate)
                results['features']['multilingual'] = multilingual_result
            
            # Generate images
            images_result = self.generate_images(attraction_data)
            results['features']['images'] = images_result
            
            return results
            
        except Exception as e:
            results['success'] = False
            results['error'] = str(e)
            return results


# Convenience functions for easier usage
def enrich_attraction_content(attraction_data: Dict) -> Dict[str, Any]:
    """Convenience function to enrich attraction content."""
    service = ContentEnrichmentService()
    return service.enrich_attraction(attraction_data)


def generate_place_description(attraction_data: Dict) -> Dict[str, Any]:
    """Convenience function to generate place description."""
    service = ContentEnrichmentService()
    return service.generate_place_description(attraction_data)


def translate_content(text: str, target_languages: List[str] = None) -> Dict[str, Any]:
    """Convenience function to translate content."""
    service = ContentEnrichmentService()
    return service.generate_multilingual_content(text, target_languages)


def extract_key_features(text: str) -> Dict[str, Any]:
    """Convenience function to extract key features."""
    service = ContentEnrichmentService()
    return service.extract_key_features(text)


def generate_attraction_images(attraction_data: Dict, num_images: int = 1) -> Dict[str, Any]:
    """Convenience function to generate images."""
    service = ContentEnrichmentService()
    return service.generate_images(attraction_data, num_images)