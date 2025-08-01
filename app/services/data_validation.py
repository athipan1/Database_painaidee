"""
AI Data Validation Service for cleaning and validating attraction data.
"""
import re
import json
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from collections import Counter
from app.models import db, Attraction, DataValidationResult

logger = logging.getLogger(__name__)


class DataValidator:
    """Main class for data validation and cleaning."""
    
    def __init__(self):
        """Initialize the data validator."""
        self.thai_provinces = {
            'กรุงเทพมหานคร', 'กระบี่', 'กาญจนบุรี', 'กาฬสินธุ์', 'กำแพงเพชร',
            'ขอนแก่น', 'จังหวัดจันทบุรี', 'ฉะเชิงเทรา', 'ชลบุรี', 'ชัยนาท',
            'ชัยภูมิ', 'ชุมพร', 'เชียงราย', 'เชียงใหม่', 'ตรัง', 'ตราด',
            'ตาก', 'นครนายก', 'นครปฐม', 'นครพนม', 'นครราชสีมา', 'นครศรีธรรมราช',
            'นครสวรรค์', 'นนทบุรี', 'นราธิวาส', 'น่าน', 'บึงกาฬ', 'บุรีรัมย์',
            'ปทุมธานี', 'ประจวบคีรีขันธ์', 'ปราจีนบุรี', 'ปัตตานี', 'พระนครศรีอยุธยา',
            'พังงา', 'พัทลุง', 'พิจิตร', 'พิษณุโลก', 'เพชรบุรี', 'เพชรบูรณ์',
            'แพร่', 'พะเยา', 'ภูเก็ต', 'มหาสารคาม', 'มุกดาหาร', 'แม่ฮ่องสอน',
            'ยโสธร', 'ยะลา', 'ร้อยเอ็ด', 'ระนอง', 'ระยอง', 'ราชบุรี',
            'ลพบุรี', 'ลำปาง', 'ลำพูน', 'เลย', 'ศรีสะเกษ', 'สกลนคร',
            'สงขลา', 'สตูล', 'สมุทรปราการ', 'สมุทรสงคราม', 'สมุทรสาคร', 'สระแก้ว',
            'สระบุรี', 'สิงห์บุรี', 'สุโขทัย', 'สุพรรณบุรี', 'สุราษฎร์ธานี',
            'สุรินทร์', 'หนองคาย', 'หนองบัวลำภู', 'อ่างทอง', 'อุดรธานี',
            'อุทัยธานี', 'อุตรดิตถ์', 'อุบลราชธานี', 'อำนาจเจริญ'
        }
        
        # Common typos in Thai attractions
        self.common_typos = {
            'วัดไก่': 'วัดใหญ่',
            'วัดป่า': 'วัดป่า',
            'เมือง': 'เมือง',
            'ประเทศ': 'ประเทศ',
            'จังหวัด': 'จังหวัด',
            'อำเภอ': 'อำเภอ',
            'ตำบล': 'ตำบล'
        }
        
        # Grammar patterns for validation
        self.grammar_patterns = [
            (r'(?i)\b(วัด|เมือง|ป่า|เขา|น้ำตก)\s*$', 'incomplete_name'),
            (r'(?i)\b\d+\s*(วัด|เมือง)', 'number_in_name'),
            (r'[^\w\s\u0E00-\u0E7F.,!?()-]', 'invalid_characters'),
            (r'\s{2,}', 'multiple_spaces'),
            (r'^[\s\n]*$', 'empty_content')
        ]
    
    def validate_attraction(self, attraction: Attraction) -> Dict:
        """
        Validate a complete attraction record.
        
        Args:
            attraction: Attraction model instance
            
        Returns:
            dict: Validation results with issues found
        """
        results = {
            'attraction_id': attraction.id,
            'overall_score': 0.0,
            'issues': [],
            'suggestions': []
        }
        
        # Validate title
        title_results = self.validate_text(attraction.title, 'title')
        results['issues'].extend(title_results['issues'])
        results['suggestions'].extend(title_results['suggestions'])
        
        # Validate body
        if attraction.body:
            body_results = self.validate_text(attraction.body, 'body')
            results['issues'].extend(body_results['issues'])
            results['suggestions'].extend(body_results['suggestions'])
        
        # Check for duplicates
        duplicate_results = self.check_duplicates(attraction)
        results['issues'].extend(duplicate_results['issues'])
        results['suggestions'].extend(duplicate_results['suggestions'])
        
        # Calculate overall score
        total_checks = len(title_results.get('checks', [])) + len(body_results.get('checks', [])) + 1
        failed_checks = len([issue for issue in results['issues'] if issue.get('severity') == 'high'])
        results['overall_score'] = max(0.0, (total_checks - failed_checks) / total_checks)
        
        return results
    
    def validate_text(self, text: str, field_name: str) -> Dict:
        """
        Validate text content for grammar, typos, and formatting issues.
        
        Args:
            text: Text to validate
            field_name: Name of the field being validated
            
        Returns:
            dict: Validation results
        """
        if not text or not text.strip():
            return {
                'issues': [{
                    'type': 'empty_content',
                    'severity': 'high',
                    'field': field_name,
                    'description': f'{field_name} is empty or contains only whitespace',
                    'suggestion': f'Please provide meaningful content for {field_name}'
                }],
                'suggestions': [],
                'checks': ['empty_check']
            }
        
        results = {
            'issues': [],
            'suggestions': [],
            'checks': ['grammar', 'typos', 'formatting']
        }
        
        # Grammar validation
        grammar_issues = self._check_grammar(text, field_name)
        results['issues'].extend(grammar_issues)
        
        # Typo validation
        typo_issues = self._check_typos(text, field_name)
        results['issues'].extend(typo_issues)
        
        # Formatting validation
        format_issues = self._check_formatting(text, field_name)
        results['issues'].extend(format_issues)
        
        return results
    
    def _check_grammar(self, text: str, field_name: str) -> List[Dict]:
        """Check for grammar issues in text."""
        issues = []
        
        for pattern, issue_type in self.grammar_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                issues.append({
                    'type': issue_type,
                    'severity': 'medium',
                    'field': field_name,
                    'position': match.span(),
                    'description': f'Grammar issue detected: {issue_type}',
                    'suggestion': self._get_grammar_suggestion(issue_type, match.group())
                })
        
        return issues
    
    def _check_typos(self, text: str, field_name: str) -> List[Dict]:
        """Check for common typos in text."""
        issues = []
        
        for typo, correction in self.common_typos.items():
            if typo in text and typo != correction:
                issues.append({
                    'type': 'typo',
                    'severity': 'low',
                    'field': field_name,
                    'description': f'Possible typo: "{typo}"',
                    'suggestion': f'Consider changing "{typo}" to "{correction}"'
                })
        
        return issues
    
    def _check_formatting(self, text: str, field_name: str) -> List[Dict]:
        """Check for formatting issues in text."""
        issues = []
        
        # Check for multiple consecutive spaces
        if re.search(r'\s{2,}', text):
            issues.append({
                'type': 'formatting',
                'severity': 'low',
                'field': field_name,
                'description': 'Multiple consecutive spaces found',
                'suggestion': 'Clean up extra spaces between words'
            })
        
        # Check for inconsistent capitalization (basic check)
        if field_name == 'title':
            if text and not text[0].isupper() and not text[0].isdigit():
                issues.append({
                    'type': 'formatting',
                    'severity': 'low',
                    'field': field_name,
                    'description': 'Title should start with capital letter',
                    'suggestion': f'Consider starting with: "{text[0].upper() + text[1:]}"'
                })
        
        return issues
    
    def _get_grammar_suggestion(self, issue_type: str, text: str) -> str:
        """Get suggestion for grammar issue."""
        suggestions = {
            'incomplete_name': 'The name appears incomplete. Consider adding more details.',
            'number_in_name': 'Numbers in names might need verification.',
            'invalid_characters': 'Remove special characters that might cause issues.',
            'multiple_spaces': 'Clean up extra spaces.',
            'empty_content': 'Add meaningful content.'
        }
        return suggestions.get(issue_type, 'Please review this content.')
    
    def check_duplicates(self, attraction: Attraction) -> Dict:
        """
        Check for potential duplicate attractions.
        
        Args:
            attraction: Attraction to check
            
        Returns:
            dict: Duplicate check results
        """
        results = {
            'issues': [],
            'suggestions': []
        }
        
        try:
            # Check for exact title matches
            exact_matches = Attraction.query.filter(
                Attraction.title == attraction.title,
                Attraction.id != attraction.id
            ).count()
            
            if exact_matches > 0:
                results['issues'].append({
                    'type': 'duplicate',
                    'severity': 'high',
                    'field': 'title',
                    'description': f'Found {exact_matches} attractions with identical title',
                    'suggestion': 'Review for potential duplicates and merge if necessary'
                })
            
            # Check for similar titles (basic similarity)
            similar_titles = self._find_similar_titles(attraction.title, attraction.id)
            if similar_titles:
                results['issues'].append({
                    'type': 'similar_duplicate',
                    'severity': 'medium',
                    'field': 'title',
                    'description': f'Found {len(similar_titles)} attractions with similar titles',
                    'suggestion': f'Similar titles found: {", ".join(similar_titles[:3])}'
                })
        
        except Exception as e:
            logger.error(f"Error checking duplicates for attraction {attraction.id}: {str(e)}")
        
        return results
    
    def _find_similar_titles(self, title: str, exclude_id: int, threshold: float = 0.8) -> List[str]:
        """Find titles similar to the given title."""
        try:
            # Simple similarity check based on word overlap
            title_words = set(title.lower().split())
            similar_titles = []
            
            # Get all other attractions
            other_attractions = Attraction.query.filter(Attraction.id != exclude_id).all()
            
            for other in other_attractions:
                if not other.title:
                    continue
                    
                other_words = set(other.title.lower().split())
                
                # Calculate Jaccard similarity
                intersection = len(title_words.intersection(other_words))
                union = len(title_words.union(other_words))
                
                if union > 0:
                    similarity = intersection / union
                    if similarity >= threshold:
                        similar_titles.append(other.title)
            
            return similar_titles[:5]  # Return top 5 similar titles
        
        except Exception as e:
            logger.error(f"Error finding similar titles: {str(e)}")
            return []
    
    def fix_text_issues(self, text: str, fix_types: List[str] = None) -> str:
        """
        Automatically fix common text issues.
        
        Args:
            text: Text to fix
            fix_types: List of issue types to fix (default: all)
            
        Returns:
            str: Fixed text
        """
        if not text:
            return text
        
        fixed_text = text
        fix_types = fix_types or ['formatting', 'typos', 'grammar']
        
        if 'formatting' in fix_types:
            # Fix multiple spaces
            fixed_text = re.sub(r'\s{2,}', ' ', fixed_text)
            # Remove leading/trailing whitespace
            fixed_text = fixed_text.strip()
        
        if 'typos' in fix_types:
            # Fix common typos
            for typo, correction in self.common_typos.items():
                fixed_text = fixed_text.replace(typo, correction)
        
        return fixed_text
    
    def save_validation_results(self, attraction_id: int, validation_results: Dict) -> None:
        """
        Save validation results to database.
        
        Args:
            attraction_id: ID of the attraction
            validation_results: Results from validation
        """
        try:
            # Clear existing validation results for this attraction
            DataValidationResult.query.filter_by(attraction_id=attraction_id).delete()
            
            # Save new validation results
            for issue in validation_results.get('issues', []):
                validation_result = DataValidationResult(
                    attraction_id=attraction_id,
                    field_name=issue.get('field', 'unknown'),
                    validation_type=issue.get('type', 'unknown'),
                    issue_description=issue.get('description', ''),
                    suggested_fix=issue.get('suggestion', ''),
                    confidence_score=self._get_confidence_score(issue.get('severity', 'low'))
                )
                db.session.add(validation_result)
            
            # Update attraction validation status
            attraction = Attraction.query.get(attraction_id)
            if attraction:
                attraction.data_validated = True
                attraction.validation_score = validation_results.get('overall_score', 0.0)
                attraction.last_cleaned_at = datetime.utcnow()
            
            db.session.commit()
            logger.info(f"Saved validation results for attraction {attraction_id}")
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving validation results for attraction {attraction_id}: {str(e)}")
    
    def _get_confidence_score(self, severity: str) -> float:
        """Convert severity to confidence score."""
        severity_scores = {
            'high': 0.9,
            'medium': 0.7,
            'low': 0.5
        }
        return severity_scores.get(severity, 0.5)


def validate_attraction_data(attraction_id: int) -> Dict:
    """
    Validate a specific attraction's data.
    
    Args:
        attraction_id: ID of attraction to validate
        
    Returns:
        dict: Validation results
    """
    try:
        attraction = Attraction.query.get(attraction_id)
        if not attraction:
            return {'error': 'Attraction not found'}
        
        validator = DataValidator()
        results = validator.validate_attraction(attraction)
        
        # Save results to database
        validator.save_validation_results(attraction_id, results)
        
        return results
    
    except Exception as e:
        logger.error(f"Error validating attraction {attraction_id}: {str(e)}")
        return {'error': str(e)}


def validate_batch_attractions(attraction_ids: List[int]) -> Dict:
    """
    Validate multiple attractions at once.
    
    Args:
        attraction_ids: List of attraction IDs to validate
        
    Returns:
        dict: Batch validation results
    """
    results = {
        'processed': 0,
        'successful': 0,
        'failed': 0,
        'results': []
    }
    
    validator = DataValidator()
    
    for attraction_id in attraction_ids:
        try:
            attraction = Attraction.query.get(attraction_id)
            if not attraction:
                results['failed'] += 1
                results['results'].append({
                    'attraction_id': attraction_id,
                    'error': 'Attraction not found'
                })
                continue
            
            validation_result = validator.validate_attraction(attraction)
            validator.save_validation_results(attraction_id, validation_result)
            
            results['successful'] += 1
            results['results'].append(validation_result)
        
        except Exception as e:
            results['failed'] += 1
            results['results'].append({
                'attraction_id': attraction_id,
                'error': str(e)
            })
            logger.error(f"Error validating attraction {attraction_id}: {str(e)}")
        
        results['processed'] += 1
    
    return results


def get_validation_stats() -> Dict:
    """Get overall validation statistics."""
    try:
        total_attractions = Attraction.query.count()
        validated_attractions = Attraction.query.filter_by(data_validated=True).count()
        
        # Get issue counts by type
        issue_counts = db.session.query(
            DataValidationResult.validation_type,
            db.func.count(DataValidationResult.id)
        ).filter_by(status='pending').group_by(DataValidationResult.validation_type).all()
        
        return {
            'total_attractions': total_attractions,
            'validated_attractions': validated_attractions,
            'validation_coverage': validated_attractions / total_attractions if total_attractions > 0 else 0,
            'pending_issues': dict(issue_counts),
            'avg_validation_score': db.session.query(
                db.func.avg(Attraction.validation_score)
            ).filter(Attraction.validation_score.isnot(None)).scalar() or 0.0
        }
    
    except Exception as e:
        logger.error(f"Error getting validation stats: {str(e)}")
        return {'error': str(e)}