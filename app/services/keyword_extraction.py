"""
Keyword extraction service using NLP for analyzing attraction descriptions.
"""
import json
import re
from typing import List, Dict, Optional
from collections import Counter

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False


class KeywordExtractor:
    """Service for extracting keywords from attraction descriptions."""
    
    def __init__(self):
        self.fallback_extractor = FallbackKeywordExtractor()
        
        if TRANSFORMERS_AVAILABLE:
            try:
                # Use a lightweight model for keyword extraction
                self.ner_pipeline = pipeline("ner", model="dbmdz/bert-large-cased-finetuned-conll03-english")
                self.use_transformers = True
            except Exception:
                self.use_transformers = False
        else:
            self.use_transformers = False
            
        if SPACY_AVAILABLE:
            try:
                # Try to load English model
                self.nlp = spacy.load("en_core_web_sm")
                self.use_spacy = True
            except OSError:
                # Fallback if model not downloaded
                self.use_spacy = False
        else:
            self.use_spacy = False
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """
        Extract keywords from text using available NLP libraries or fallback method.
        
        Args:
            text: Input text to extract keywords from
            max_keywords: Maximum number of keywords to return
            
        Returns:
            List of extracted keywords
        """
        if not text or not text.strip():
            return []
        
        keywords = []
        
        # Try spaCy first (most accurate)
        if self.use_spacy:
            keywords.extend(self._extract_with_spacy(text))
        
        # Try transformers for named entities
        if self.use_transformers and len(keywords) < max_keywords:
            keywords.extend(self._extract_with_transformers(text))
        
        # Always use fallback to ensure we get some keywords
        fallback_keywords = self.fallback_extractor.extract_keywords(text, max_keywords)
        keywords.extend(fallback_keywords)
        
        # Remove duplicates and limit results
        unique_keywords = list(dict.fromkeys(keywords))  # Preserve order
        return unique_keywords[:max_keywords]
    
    def _extract_with_spacy(self, text: str) -> List[str]:
        """Extract keywords using spaCy NLP."""
        doc = self.nlp(text)
        keywords = []
        
        # Extract named entities
        for ent in doc.ents:
            if ent.label_ in ['GPE', 'LOC', 'ORG', 'EVENT', 'FAC']:  # Relevant entity types
                keywords.append(ent.text.lower())
        
        # Extract important nouns and adjectives
        for token in doc:
            if (token.pos_ in ['NOUN', 'PROPN', 'ADJ'] and 
                len(token.text) > 2 and 
                not token.is_stop and 
                not token.is_punct):
                keywords.append(token.lemma_.lower())
        
        return keywords
    
    def _extract_with_transformers(self, text: str) -> List[str]:
        """Extract named entities using transformers."""
        try:
            entities = self.ner_pipeline(text)
            keywords = []
            
            for entity in entities:
                if entity['entity'] in ['B-LOC', 'I-LOC', 'B-ORG', 'I-ORG', 'B-MISC', 'I-MISC']:
                    word = entity['word'].replace('##', '')  # Clean BERT subword tokens
                    if len(word) > 2:
                        keywords.append(word.lower())
            
            return keywords
        except Exception:
            return []
    
    def extract_keywords_batch(self, texts: List[str], max_keywords: int = 10) -> List[List[str]]:
        """Extract keywords from multiple texts."""
        return [self.extract_keywords(text, max_keywords) for text in texts]
    
    def get_keyword_categories(self, keywords: List[str]) -> Dict[str, List[str]]:
        """Categorize keywords into different types."""
        categories = {
            'places': [],
            'nature': [],
            'culture': [],
            'activities': [],
            'food': [],
            'other': []
        }
        
        # Simple keyword categorization
        nature_words = {'river', 'mountain', 'forest', 'beach', 'park', 'nature', 'tree', 'water', 'sea', 'lake'}
        culture_words = {'temple', 'museum', 'ancient', 'historical', 'culture', 'traditional', 'art', 'heritage'}
        activity_words = {'shopping', 'restaurant', 'cafe', 'market', 'festival', 'tour', 'experience'}
        food_words = {'food', 'restaurant', 'cafe', 'local', 'cuisine', 'dish', 'taste', 'delicious'}
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if any(word in keyword_lower for word in nature_words):
                categories['nature'].append(keyword)
            elif any(word in keyword_lower for word in culture_words):
                categories['culture'].append(keyword)
            elif any(word in keyword_lower for word in activity_words):
                categories['activities'].append(keyword)
            elif any(word in keyword_lower for word in food_words):
                categories['food'].append(keyword)
            else:
                categories['other'].append(keyword)
        
        return categories


class FallbackKeywordExtractor:
    """Simple keyword extractor that doesn't require external libraries."""
    
    def __init__(self):
        # Common stop words in English and Thai
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'could', 'should', 'may', 'might', 'can', 'must', 'this', 'that', 'these', 'those',
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his',
            'her', 'its', 'our', 'their', 'myself', 'yourself', 'himself', 'herself', 'itself', 'ourselves',
            'yourselves', 'themselves', 'very', 'really', 'quite', 'just', 'so', 'too', 'also', 'much', 'many',
            'ใน', 'ของ', 'ที่', 'เป็น', 'มี', 'จะ', 'ไม่', 'และ', 'หรือ', 'ก็', 'ได้', 'แล้ว', 'กับ'
        }
        
        # Keywords that indicate important places/attractions
        self.important_keywords = {
            'temple', 'wat', 'museum', 'park', 'market', 'beach', 'mountain', 'river', 'island',
            'restaurant', 'cafe', 'shopping', 'mall', 'street', 'road', 'bridge', 'palace',
            'ancient', 'historical', 'cultural', 'traditional', 'local', 'famous', 'popular',
            'beautiful', 'amazing', 'wonderful', 'spectacular', 'stunning', 'breathtaking'
        }
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """Extract keywords using simple text processing."""
        if not text:
            return []
        
        # Clean and tokenize text
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = text.split()
        
        # Filter words
        keywords = []
        for word in words:
            if (len(word) > 2 and 
                word not in self.stop_words and
                not word.isdigit()):
                keywords.append(word)
        
        # Count frequency and prioritize important keywords
        word_counts = Counter(keywords)
        
        # Boost important keywords
        for word in self.important_keywords:
            if word in word_counts:
                word_counts[word] *= 2
        
        # Get most common keywords
        most_common = word_counts.most_common(max_keywords)
        return [word for word, count in most_common]


def extract_keywords_from_attraction(attraction_data: Dict) -> List[str]:
    """
    Extract keywords from attraction data.
    
    Args:
        attraction_data: Dictionary containing attraction information
        
    Returns:
        List of extracted keywords
    """
    extractor = KeywordExtractor()
    
    # Combine title and body for keyword extraction
    text_parts = []
    if attraction_data.get('title'):
        text_parts.append(attraction_data['title'])
    if attraction_data.get('body'):
        text_parts.append(attraction_data['body'])
    
    combined_text = ' '.join(text_parts)
    keywords = extractor.extract_keywords(combined_text)
    
    return keywords


def keywords_to_json(keywords: List[str]) -> str:
    """Convert keywords list to JSON string for database storage."""
    return json.dumps(keywords, ensure_ascii=False)


def keywords_from_json(keywords_json: str) -> List[str]:
    """Parse keywords from JSON string."""
    if not keywords_json:
        return []
    try:
        return json.loads(keywords_json)
    except (json.JSONDecodeError, TypeError):
        return []