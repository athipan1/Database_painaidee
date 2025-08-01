"""
AI-powered data enrichment service for attractions.
Provides text summarization, categorization, and popularity scoring.
"""
import logging
import json
import re
from typing import Dict, List, Optional, Tuple
import nltk
from collections import Counter

# Download required NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)
except:
    pass  # Fail silently if NLTK data can't be downloaded

logger = logging.getLogger(__name__)


class AIService:
    """AI service for processing attraction data."""
    
    # Thai attraction categories
    ATTRACTION_CATEGORIES = {
        'ธรรมชาติ': ['ธรรมชาติ', 'ป่า', 'เขา', 'น้ำตก', 'ทะเล', 'เกาะ', 'หาด', 'อุทยาน', 'สวน', 'ภูเขา'],
        'วัฒนธรรม': ['วัด', 'โบสถ์', 'พระราม', 'ประวัติศาสตร์', 'โบราณ', 'พิพิธภัณฑ์', 'วัฒนธรรม', 'ศิลปะ'],
        'ร้านอาหาร': ['ร้านอาหาร', 'อาหาร', 'กิน', 'ขนม', 'เครื่องดื่ม', 'ร้าน', 'คาเฟ่', 'บาร์'],
        'ที่พัก': ['โรงแรม', 'รีสอร์ต', 'ที่พัก', 'บังกะโล', 'เกสต์เฮาส์', 'โฮสเทล'],
        'กิจกรรม': ['กิจกรรม', 'เที่ยว', 'ท่อง', 'ผจญภัย', 'กีฬา', 'ดำน้ำ', 'ปีนเขา'],
        'ช้อปปิ้ง': ['ตลาด', 'ช้อปปิ้ง', 'ซื้อ', 'ของฝาก', 'สินค้า', 'ขาย']
    }
    
    @classmethod
    def summarize_text(cls, text: str, max_length: int = 200) -> str:
        """
        Generate a summary of the given text.
        Uses simple extractive summarization based on sentence scoring.
        """
        if not text or len(text.strip()) <= max_length:
            return text.strip()
        
        try:
            # Clean the text
            text = re.sub(r'\s+', ' ', text.strip())
            
            # Split into sentences (simple approach for Thai/English mixed text)
            sentences = re.split(r'[.!?।]\s+', text)
            if len(sentences) <= 2:
                return text[:max_length] + '...' if len(text) > max_length else text
            
            # Score sentences based on word frequency
            words = re.findall(r'\b\w+\b', text.lower())
            word_freq = Counter(words)
            
            sentence_scores = []
            for sentence in sentences:
                if len(sentence.strip()) < 10:  # Skip very short sentences
                    continue
                    
                sentence_words = re.findall(r'\b\w+\b', sentence.lower())
                score = sum(word_freq.get(word, 0) for word in sentence_words)
                sentence_scores.append((sentence.strip(), score, len(sentence)))
            
            # Select top sentences that fit within max_length
            sentence_scores.sort(key=lambda x: x[1], reverse=True)
            
            summary_parts = []
            current_length = 0
            
            for sentence, score, length in sentence_scores:
                if current_length + length <= max_length - 3:  # Leave room for "..."
                    summary_parts.append(sentence)
                    current_length += length + 1  # +1 for space
                elif not summary_parts:  # If no sentences fit, take the first one truncated
                    return sentence[:max_length-3] + '...'
                else:
                    break
            
            summary = ' '.join(summary_parts)
            return summary if len(summary) <= max_length else summary[:max_length-3] + '...'
            
        except Exception as e:
            logger.error(f"Error in text summarization: {str(e)}")
            return text[:max_length] + '...' if len(text) > max_length else text
    
    @classmethod
    def categorize_attraction(cls, title: str, description: str = "") -> List[str]:
        """
        Categorize attraction based on title and description.
        Returns list of relevant categories.
        """
        try:
            # Combine title and description for analysis
            full_text = f"{title} {description}".lower()
            
            categories = []
            for category, keywords in cls.ATTRACTION_CATEGORIES.items():
                # Check if any keyword appears in the text
                if any(keyword.lower() in full_text for keyword in keywords):
                    categories.append(category)
            
            # If no categories found, try to infer from common patterns
            if not categories:
                if any(word in full_text for word in ['temple', 'wat', 'church', 'museum']):
                    categories.append('วัฒนธรรม')
                elif any(word in full_text for word in ['restaurant', 'food', 'cafe', 'bar']):
                    categories.append('ร้านอาหาร')
                elif any(word in full_text for word in ['hotel', 'resort', 'accommodation']):
                    categories.append('ที่พัก')
                elif any(word in full_text for word in ['beach', 'mountain', 'park', 'nature']):
                    categories.append('ธรรมชาติ')
                else:
                    categories.append('อื่นๆ')
            
            return categories[:3]  # Return max 3 categories
            
        except Exception as e:
            logger.error(f"Error in attraction categorization: {str(e)}")
            return ['อื่นๆ']
    
    @classmethod
    def calculate_popularity_score(cls, title: str, description: str = "", user_id: int = None) -> float:
        """
        Calculate popularity score based on various factors.
        Simple heuristic-based approach.
        """
        try:
            score = 0.0
            
            # Base score from text length and quality
            if description:
                # Longer descriptions typically indicate more established attractions
                desc_length = len(description.strip())
                score += min(desc_length / 1000, 2.0)  # Max 2 points for description length
            
            # Title analysis
            title_lower = title.lower()
            
            # Popular keywords boost score
            popular_keywords = [
                'famous', 'popular', 'best', 'top', 'must-visit', 'recommended',
                'ดัง', 'นิยม', 'ต้องไป', 'แนะนำ', 'ที่เที่ยว', 'สวยงาม'
            ]
            
            for keyword in popular_keywords:
                if keyword in title_lower:
                    score += 1.0
            
            # Category-based scoring
            categories = cls.categorize_attraction(title, description)
            category_scores = {
                'ธรรมชาติ': 1.5,
                'วัฒนธรรม': 1.3,
                'ร้านอาหาร': 1.0,
                'ที่พัก': 0.8,
                'กิจกรรม': 1.2,
                'ช้อปปิ้ง': 0.9
            }
            
            for category in categories:
                score += category_scores.get(category, 0.5)
            
            # Normalize score to 0-10 scale
            score = min(score * 1.5, 10.0)
            
            return round(score, 2)
            
        except Exception as e:
            logger.error(f"Error in popularity score calculation: {str(e)}")
            return 5.0  # Default score
    
    @classmethod
    def process_attraction_ai(cls, attraction_data: Dict) -> Dict:
        """
        Process attraction data with AI features.
        Returns updated data with AI-generated fields.
        """
        try:
            title = attraction_data.get('title', '')
            body = attraction_data.get('body', '')
            
            # Generate AI summary
            ai_summary = cls.summarize_text(body) if body else ''
            
            # Generate AI tags (categories)
            ai_categories = cls.categorize_attraction(title, body)
            ai_tags = json.dumps(ai_categories, ensure_ascii=False)
            
            # Calculate popularity score
            popularity_score = cls.calculate_popularity_score(title, body, attraction_data.get('user_id'))
            
            # Update attraction data
            attraction_data.update({
                'ai_summary': ai_summary,
                'ai_tags': ai_tags,
                'popularity_score': popularity_score,
                'ai_processed': True
            })
            
            return attraction_data
            
        except Exception as e:
            logger.error(f"Error in AI processing: {str(e)}")
            return attraction_data
    
    @classmethod
    def generate_search_vector(cls, title: str, body: str = "", ai_summary: str = "") -> str:
        """
        Generate search vector text for full-text search.
        Combines title, body, and AI summary for comprehensive search.
        """
        try:
            # Combine all text fields
            search_text_parts = []
            
            if title:
                search_text_parts.append(title)
            if body:
                search_text_parts.append(body)
            if ai_summary:
                search_text_parts.append(ai_summary)
            
            # Join and clean text
            search_text = ' '.join(search_text_parts)
            search_text = re.sub(r'\s+', ' ', search_text.strip())
            
            return search_text
            
        except Exception as e:
            logger.error(f"Error generating search vector: {str(e)}")
            return title or ''


def get_ai_service() -> AIService:
    """Get AI service instance."""
    return AIService()