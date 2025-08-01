"""
AI-powered content rewriting service for improving attraction descriptions.
"""
import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime

try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


class ContentRewriter:
    """AI-powered content rewriter for attraction descriptions."""
    
    def __init__(self):
        self.fallback_rewriter = FallbackContentRewriter()
        self.use_transformers = TRANSFORMERS_AVAILABLE
        self.model_loaded = False
        
        if self.use_transformers:
            try:
                # Try to load a lightweight text generation model
                # Using a smaller model that's more likely to be available
                self.rewriter = pipeline(
                    "text2text-generation", 
                    model="t5-small",
                    max_length=512,
                    device=-1  # Use CPU
                )
                self.model_loaded = True
            except Exception as e:
                print(f"Failed to load transformer model: {e}")
                self.use_transformers = False
    
    def improve_content(
        self, 
        text: str, 
        style: str = 'friendly',
        max_length: int = 500
    ) -> Dict:
        """
        Improve content readability and style.
        
        Args:
            text: Original text to improve
            style: Target style ('friendly', 'professional', 'casual', 'formal')
            max_length: Maximum length of improved text
            
        Returns:
            Dictionary with improved text and metadata
        """
        if not text or not text.strip():
            return {
                'original_text': text,
                'improved_text': text,
                'improvements': [],
                'style': style,
                'success': False,
                'method': 'none'
            }
        
        if self.use_transformers and self.model_loaded:
            return self._improve_with_transformers(text, style, max_length)
        else:
            return self.fallback_rewriter.improve_content(text, style, max_length)
    
    def _improve_with_transformers(
        self, 
        text: str, 
        style: str,
        max_length: int
    ) -> Dict:
        """Improve content using transformer models."""
        try:
            # Create a prompt based on the desired style
            prompt = self._create_improvement_prompt(text, style)
            
            # Generate improved text
            result = self.rewriter(
                prompt,
                max_length=max_length,
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True
            )
            
            improved_text = result[0]['generated_text']
            
            # Clean up the generated text
            improved_text = self._clean_generated_text(improved_text, text)
            
            # Analyze improvements made
            improvements = self._analyze_improvements(text, improved_text)
            
            return {
                'original_text': text,
                'improved_text': improved_text,
                'improvements': improvements,
                'style': style,
                'success': True,
                'method': 'transformer',
                'model': 't5-small'
            }
            
        except Exception as e:
            print(f"Transformer rewriting failed: {e}")
            # Fallback to rule-based improvement
            return self.fallback_rewriter.improve_content(text, style, max_length)
    
    def _create_improvement_prompt(self, text: str, style: str) -> str:
        """Create a prompt for text improvement."""
        style_instructions = {
            'friendly': 'Rewrite this text to be more friendly and welcoming while keeping all important information',
            'professional': 'Rewrite this text to be more professional and formal while maintaining clarity',
            'casual': 'Rewrite this text to be more casual and conversational while preserving key details',
            'formal': 'Rewrite this text to be more formal and polished while keeping it accessible'
        }
        
        instruction = style_instructions.get(style, style_instructions['friendly'])
        return f"{instruction}: {text}"
    
    def _clean_generated_text(self, generated_text: str, original_text: str) -> str:
        """Clean and validate generated text."""
        # Remove the prompt if it's still in the output
        generated_text = generated_text.strip()
        
        # Basic cleaning
        generated_text = re.sub(r'\s+', ' ', generated_text)  # Multiple spaces
        generated_text = re.sub(r'([.!?])\s*([.!?])', r'\1 \2', generated_text)  # Double punctuation
        
        # Ensure minimum length (if too short, return improved original)
        if len(generated_text) < len(original_text) * 0.5:
            return self.fallback_rewriter.improve_content(original_text)['improved_text']
        
        return generated_text
    
    def _analyze_improvements(self, original: str, improved: str) -> List[str]:
        """Analyze what improvements were made."""
        improvements = []
        
        # Length comparison
        if len(improved) > len(original):
            improvements.append("Added more descriptive content")
        elif len(improved) < len(original):
            improvements.append("Made text more concise")
        
        # Sentence structure
        original_sentences = len(re.findall(r'[.!?]+', original))
        improved_sentences = len(re.findall(r'[.!?]+', improved))
        
        if improved_sentences > original_sentences:
            improvements.append("Improved sentence structure")
        
        # Check for common improvements
        if len(re.findall(r'\b(amazing|wonderful|beautiful|spectacular)\b', improved.lower())) > 0:
            improvements.append("Added positive descriptive words")
        
        if len(re.findall(r'\b(you|your)\b', improved.lower())) > len(re.findall(r'\b(you|your)\b', original.lower())):
            improvements.append("Made text more engaging and personal")
        
        return improvements if improvements else ["General text improvement"]
    
    def batch_improve_content(
        self, 
        texts: List[str], 
        style: str = 'friendly'
    ) -> List[Dict]:
        """Improve multiple texts in batch."""
        results = []
        for text in texts:
            result = self.improve_content(text, style)
            results.append(result)
        return results
    
    def suggest_improvements(self, text: str) -> List[Dict]:
        """Suggest specific improvements without rewriting."""
        suggestions = []
        
        if not text or not text.strip():
            return suggestions
        
        # Check text length
        if len(text) < 50:
            suggestions.append({
                'type': 'length',
                'issue': 'Text is too short',
                'suggestion': 'Add more descriptive details about the attraction',
                'priority': 'high'
            })
        elif len(text) > 1000:
            suggestions.append({
                'type': 'length',
                'issue': 'Text is very long',
                'suggestion': 'Consider breaking into shorter paragraphs or summarizing key points',
                'priority': 'medium'
            })
        
        # Check sentence structure
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) == 1 and len(text) > 100:
            suggestions.append({
                'type': 'structure',
                'issue': 'Single long sentence',
                'suggestion': 'Break into multiple sentences for better readability',
                'priority': 'medium'
            })
        
        # Check for repetitive words
        words = re.findall(r'\b\w+\b', text.lower())
        word_counts = {}
        for word in words:
            if len(word) > 3:  # Only check meaningful words
                word_counts[word] = word_counts.get(word, 0) + 1
        
        repetitive_words = [word for word, count in word_counts.items() if count > 3]
        if repetitive_words:
            suggestions.append({
                'type': 'repetition',
                'issue': f'Repetitive words: {", ".join(repetitive_words[:3])}',
                'suggestion': 'Use synonyms to avoid repetition',
                'priority': 'low'
            })
        
        # Check for engaging language
        engaging_words = ['amazing', 'wonderful', 'beautiful', 'spectacular', 'stunning', 'breathtaking']
        if not any(word in text.lower() for word in engaging_words):
            suggestions.append({
                'type': 'engagement',
                'issue': 'Text lacks engaging descriptive words',
                'suggestion': 'Add more vivid and appealing adjectives',
                'priority': 'medium'
            })
        
        # Check for personal pronouns (engagement)
        personal_pronouns = ['you', 'your', 'visit', 'explore', 'experience']
        personal_count = sum(1 for word in personal_pronouns if word in text.lower())
        
        if personal_count == 0:
            suggestions.append({
                'type': 'engagement',
                'issue': 'Text is not directly addressing the reader',
                'suggestion': 'Use "you" and action words to make it more engaging',
                'priority': 'medium'
            })
        
        return suggestions
    
    def calculate_readability_score(self, text: str) -> Dict:
        """Calculate a simple readability score."""
        if not text or not text.strip():
            return {'score': 0, 'level': 'unreadable', 'issues': ['No content']}
        
        # Simple readability metrics
        sentences = len(re.findall(r'[.!?]+', text))
        words = len(re.findall(r'\b\w+\b', text))
        characters = len(re.sub(r'\s', '', text))
        
        if sentences == 0:
            sentences = 1  # Avoid division by zero
        
        avg_words_per_sentence = words / sentences
        avg_chars_per_word = characters / words if words > 0 else 0
        
        # Simple scoring (0-100)
        score = 100
        issues = []
        
        # Penalize very long sentences
        if avg_words_per_sentence > 25:
            score -= 20
            issues.append('Sentences are too long')
        elif avg_words_per_sentence > 20:
            score -= 10
            issues.append('Sentences could be shorter')
        
        # Penalize very long words
        if avg_chars_per_word > 6:
            score -= 15
            issues.append('Words are too complex')
        
        # Penalize very short or very long text
        if words < 20:
            score -= 25
            issues.append('Text is too short')
        elif words > 200:
            score -= 10
            issues.append('Text might be too long')
        
        # Determine readability level
        if score >= 80:
            level = 'excellent'
        elif score >= 60:
            level = 'good'
        elif score >= 40:
            level = 'fair'
        elif score >= 20:
            level = 'poor'
        else:
            level = 'unreadable'
        
        return {
            'score': max(0, score),
            'level': level,
            'issues': issues,
            'metrics': {
                'words': words,
                'sentences': sentences,
                'avg_words_per_sentence': round(avg_words_per_sentence, 1),
                'avg_chars_per_word': round(avg_chars_per_word, 1)
            }
        }


class FallbackContentRewriter:
    """Rule-based content rewriter that doesn't require ML libraries."""
    
    def __init__(self):
        self.style_transformations = {
            'friendly': {
                'replacements': [
                    (r'\bis\b', 'is certainly'),
                    (r'\bhas\b', 'features'),
                    (r'\bcan\b', 'you can'),
                    (r'\bwill\b', 'you\'ll'),
                ],
                'additions': ['Welcome to', 'Don\'t miss', 'Be sure to visit', 'You\'ll love']
            },
            'professional': {
                'replacements': [
                    (r'\bgreat\b', 'excellent'),
                    (r'\bnice\b', 'notable'),
                    (r'\bgood\b', 'quality'),
                    (r'\bbig\b', 'significant'),
                ],
                'additions': ['This establishment', 'The facility provides', 'Visitors can expect']
            },
            'casual': {
                'replacements': [
                    (r'\bexcellent\b', 'awesome'),
                    (r'\bnotable\b', 'cool'),
                    (r'\bsignificant\b', 'big'),
                    (r'\bestablishment\b', 'place'),
                ],
                'additions': ['Check out', 'You gotta see', 'This place is', 'Super cool']
            }
        }
    
    def improve_content(
        self, 
        text: str, 
        style: str = 'friendly',
        max_length: int = 500
    ) -> Dict:
        """Improve content using rule-based transformations."""
        if not text or not text.strip():
            return {
                'original_text': text,
                'improved_text': text,
                'improvements': [],
                'style': style,
                'success': False,
                'method': 'none'
            }
        
        improved_text = text
        improvements = []
        
        # Apply style-specific transformations
        if style in self.style_transformations:
            transformations = self.style_transformations[style]
            
            # Apply replacements
            for pattern, replacement in transformations['replacements']:
                old_text = improved_text
                improved_text = re.sub(pattern, replacement, improved_text, flags=re.IGNORECASE)
                if old_text != improved_text:
                    improvements.append(f"Applied {style} style transformation")
        
        # General improvements
        improved_text = self._apply_general_improvements(improved_text, improvements)
        
        # Ensure it doesn't exceed max length
        if len(improved_text) > max_length:
            improved_text = improved_text[:max_length-3] + '...'
            improvements.append("Trimmed to fit length limit")
        
        return {
            'original_text': text,
            'improved_text': improved_text,
            'improvements': list(set(improvements)),  # Remove duplicates
            'style': style,
            'success': len(improvements) > 0,
            'method': 'rule-based'
        }
    
    def _apply_general_improvements(self, text: str, improvements: List[str]) -> str:
        """Apply general text improvements."""
        improved = text
        
        # Fix multiple spaces
        old_text = improved
        improved = re.sub(r'\s+', ' ', improved)
        if old_text != improved:
            improvements.append("Fixed spacing")
        
        # Capitalize first letter of sentences
        improved = re.sub(r'([.!?]\s*)([a-z])', lambda m: m.group(1) + m.group(2).upper(), improved)
        improved = improved[0].upper() + improved[1:] if improved else improved
        
        # Add period if missing at the end
        if improved and not improved.strip().endswith(('.', '!', '?')):
            improved = improved.strip() + '.'
            improvements.append("Added proper sentence ending")
        
        # Remove excessive punctuation
        old_text = improved
        improved = re.sub(r'([.!?]){2,}', r'\1', improved)
        if old_text != improved:
            improvements.append("Fixed punctuation")
        
        return improved


def improve_attraction_content(
    text: str, 
    style: str = 'friendly',
    max_length: int = 500
) -> Dict:
    """
    Improve attraction content text.
    
    Args:
        text: Original text to improve
        style: Target style ('friendly', 'professional', 'casual', 'formal')
        max_length: Maximum length of improved text
        
    Returns:
        Dictionary with improved text and metadata
    """
    rewriter = ContentRewriter()
    return rewriter.improve_content(text, style, max_length)


def get_content_suggestions(text: str) -> List[Dict]:
    """
    Get suggestions for improving content.
    
    Args:
        text: Text to analyze
        
    Returns:
        List of improvement suggestions
    """
    rewriter = ContentRewriter()
    return rewriter.suggest_improvements(text)


def calculate_content_readability(text: str) -> Dict:
    """
    Calculate readability score for content.
    
    Args:
        text: Text to analyze
        
    Returns:
        Readability analysis
    """
    rewriter = ContentRewriter()
    return rewriter.calculate_readability_score(text)