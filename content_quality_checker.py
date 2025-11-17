#!/usr/bin/env python3
"""
CONTENT QUALITY ASSURANCE SYSTEM
Validates generated content against quality standards
Ensures content meets cultural, accessibility, and effectiveness criteria
"""

import re
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from content_generation import GeneratedContent, ContentContext, ContentType

logger = logging.getLogger(__name__)


@dataclass
class QualityIssue:
    """Represents a quality issue found in content"""
    severity: str  # 'critical', 'warning', 'info'
    category: str  # 'readability', 'cultural', 'structure', 'tone', 'accuracy'
    message: str
    suggestion: Optional[str] = None
    location: Optional[str] = None


@dataclass
class QualityReport:
    """Quality assessment report"""
    passed: bool
    overall_score: float
    issues: List[QualityIssue]
    suggestions: List[str]
    metrics: Dict[str, Any]
    timestamp: datetime


class ReadabilityAnalyzer:
    """Analyze content readability"""

    def analyze(self, text: str) -> Dict[str, Any]:
        """Analyze text readability"""

        # Count words, sentences, syllables
        words = text.split()
        word_count = len(words)

        # Simple sentence count (periods, exclamations, questions)
        sentences = re.split(r'[.!?]+', text)
        sentence_count = len([s for s in sentences if s.strip()])

        if sentence_count == 0:
            sentence_count = 1

        # Average words per sentence
        avg_words_per_sentence = word_count / sentence_count

        # Estimate syllables (rough approximation)
        syllable_count = sum(self._count_syllables(word) for word in words)

        # Calculate Flesch Reading Ease (higher = easier)
        if word_count > 0:
            flesch_score = 206.835 - 1.015 * (word_count / sentence_count) - 84.6 * (syllable_count / word_count)
        else:
            flesch_score = 0

        # Estimate grade level
        if word_count > 0 and sentence_count > 0:
            grade_level = 0.39 * (word_count / sentence_count) + 11.8 * (syllable_count / word_count) - 15.59
        else:
            grade_level = 0

        return {
            'word_count': word_count,
            'sentence_count': sentence_count,
            'avg_words_per_sentence': avg_words_per_sentence,
            'flesch_score': max(0, min(100, flesch_score)),
            'grade_level': max(0, grade_level),
            'readability_rating': self._get_readability_rating(flesch_score)
        }

    def _count_syllables(self, word: str) -> int:
        """Rough syllable counter"""
        word = word.lower()
        vowels = 'aeiou'
        syllable_count = 0
        previous_was_vowel = False

        for char in word:
            is_vowel = char in vowels
            if is_vowel and not previous_was_vowel:
                syllable_count += 1
            previous_was_vowel = is_vowel

        # Adjust for silent 'e'
        if word.endswith('e'):
            syllable_count -= 1

        # Ensure at least one syllable
        return max(1, syllable_count)

    def _get_readability_rating(self, flesch_score: float) -> str:
        """Get readability rating from Flesch score"""
        if flesch_score >= 90:
            return "very_easy"
        elif flesch_score >= 80:
            return "easy"
        elif flesch_score >= 70:
            return "fairly_easy"
        elif flesch_score >= 60:
            return "standard"
        elif flesch_score >= 50:
            return "fairly_difficult"
        elif flesch_score >= 30:
            return "difficult"
        else:
            return "very_difficult"

    def simplify_suggestions(self, text: str, target_grade: int = 8) -> List[str]:
        """Provide suggestions for simplifying text"""
        suggestions = []
        analysis = self.analyze(text)

        if analysis['grade_level'] > target_grade:
            suggestions.append(f"Content is at grade level {analysis['grade_level']:.1f}. Target is {target_grade}.")

        if analysis['avg_words_per_sentence'] > 20:
            suggestions.append("Consider breaking long sentences into shorter ones (average is {:.1f} words/sentence)".format(
                analysis['avg_words_per_sentence']
            ))

        # Check for complex words
        complex_words = self._find_complex_words(text)
        if complex_words:
            suggestions.append(f"Consider simplifying complex words: {', '.join(complex_words[:5])}")

        return suggestions

    def _find_complex_words(self, text: str) -> List[str]:
        """Find potentially complex words"""
        words = text.split()
        complex_words = []

        for word in words:
            # Remove punctuation
            clean_word = re.sub(r'[^\w\s]', '', word)
            if len(clean_word) > 12 or self._count_syllables(clean_word) > 3:
                if clean_word.lower() not in complex_words:
                    complex_words.append(clean_word.lower())

        return complex_words[:10]


class ToneAnalyzer:
    """Analyze content tone and emotional quality"""

    def __init__(self):
        self.tone_indicators = {
            'urgent': ['immediately', 'urgent', 'critical', 'asap', 'now', 'emergency'],
            'supportive': ['help', 'support', 'together', 'can', 'encourage', 'empower'],
            'formal': ['furthermore', 'therefore', 'hereby', 'pursuant', 'shall', 'wherein'],
            'warm': ['welcome', 'aloha', 'ohana', 'care', 'love', 'family', 'kindness'],
            'professional': ['professional', 'organization', 'standards', 'process', 'procedures']
        }

    def analyze(self, text: str) -> Dict[str, Any]:
        """Analyze tone of text"""

        text_lower = text.lower()
        tone_scores = {}

        # Calculate tone scores
        for tone, indicators in self.tone_indicators.items():
            score = sum(1 for indicator in indicators if indicator in text_lower)
            tone_scores[tone] = score

        # Determine dominant tone
        if tone_scores:
            dominant_tone = max(tone_scores, key=tone_scores.get)
            max_score = tone_scores[dominant_tone]
        else:
            dominant_tone = 'neutral'
            max_score = 0

        return {
            'dominant_tone': dominant_tone,
            'tone_scores': tone_scores,
            'confidence': min(1.0, max_score / 5.0)
        }

    def matches_expected_tone(self, text: str, expected_tone: str) -> bool:
        """Check if text matches expected tone"""
        analysis = self.analyze(text)
        return analysis['dominant_tone'] == expected_tone or analysis['confidence'] < 0.3


class CulturalSensitivityChecker:
    """Check for cultural sensitivity issues"""

    def __init__(self):
        self.culturally_sensitive_terms = {
            'hawaiian': {
                'preferred': ['kupuna', 'ohana', 'malama', 'aloha', 'kuleana'],
                'avoid': ['native', 'exotic', 'primitive'],
                'context_required': ['traditional', 'authentic']
            },
            'japanese': {
                'preferred': ['san', 'sama', 'respectful language'],
                'avoid': ['oriental', 'jap'],
                'context_required': []
            },
            'filipino': {
                'preferred': ['po', 'opo', 'bayanihan'],
                'avoid': [],
                'context_required': []
            }
        }

    def check(self, text: str, cultural_context: str) -> List[QualityIssue]:
        """Check for cultural sensitivity issues"""
        issues = []
        text_lower = text.lower()

        if cultural_context in self.culturally_sensitive_terms:
            terms = self.culturally_sensitive_terms[cultural_context]

            # Check for terms to avoid
            for term in terms['avoid']:
                if term in text_lower:
                    issues.append(QualityIssue(
                        severity='critical',
                        category='cultural',
                        message=f"Potentially offensive term '{term}' found",
                        suggestion=f"Remove or replace '{term}' with culturally appropriate language"
                    ))

            # Check for preferred terms (positive signal)
            has_preferred = any(term in text_lower for term in terms['preferred'])
            if not has_preferred and len(text.split()) > 100:
                issues.append(QualityIssue(
                    severity='info',
                    category='cultural',
                    message=f"Consider adding culturally relevant terms for {cultural_context} context",
                    suggestion=f"Consider incorporating: {', '.join(terms['preferred'][:3])}"
                ))

        return issues


class ContentQualityChecker:
    """Main quality assurance system"""

    def __init__(self):
        self.readability_analyzer = ReadabilityAnalyzer()
        self.tone_analyzer = ToneAnalyzer()
        self.cultural_checker = CulturalSensitivityChecker()

    async def validate_content(
        self,
        content: GeneratedContent,
        requirements: Optional[Dict[str, Any]] = None
    ) -> QualityReport:
        """
        Comprehensive content validation

        Args:
            content: Generated content to validate
            requirements: Optional specific requirements

        Returns:
            Quality report with issues and suggestions
        """
        issues = []
        suggestions = []
        metrics = {}

        if requirements is None:
            requirements = {}

        # 1. Readability Check
        readability = self.readability_analyzer.analyze(content.body)
        metrics['readability'] = readability

        # Check if readability matches audience
        target_audience = content.generation_context.target_audience.lower()
        if any(term in target_audience for term in ['elder', 'senior', 'kupuna']):
            if readability['grade_level'] > 8:
                issues.append(QualityIssue(
                    severity='warning',
                    category='readability',
                    message=f"Content may be too complex for elder audience (grade level {readability['grade_level']:.1f})",
                    suggestion="Simplify language and sentence structure"
                ))
                suggestions.extend(
                    self.readability_analyzer.simplify_suggestions(content.body, target_grade=8)
                )

        # 2. Tone Analysis
        tone_analysis = self.tone_analyzer.analyze(content.body)
        metrics['tone'] = tone_analysis

        expected_tone = content.generation_context.emotional_tone
        if not self.tone_analyzer.matches_expected_tone(content.body, expected_tone):
            issues.append(QualityIssue(
                severity='warning',
                category='tone',
                message=f"Tone mismatch: expected '{expected_tone}', detected '{tone_analysis['dominant_tone']}'",
                suggestion=f"Adjust language to be more {expected_tone}"
            ))

        # 3. Cultural Sensitivity
        cultural_issues = self.cultural_checker.check(
            content.body,
            content.generation_context.cultural_context
        )
        issues.extend(cultural_issues)

        # 4. Structure Check
        structure_issues = self._check_structure(content)
        issues.extend(structure_issues)

        # 5. Length Check
        word_count = readability['word_count']
        metrics['word_count'] = word_count

        if content.generation_context.urgency_level == 'critical':
            if word_count > 500:
                issues.append(QualityIssue(
                    severity='warning',
                    category='structure',
                    message=f"Content too long for urgent communication ({word_count} words)",
                    suggestion="Reduce to essential information only (target: <500 words)"
                ))

        # 6. Content Type Specific Checks
        type_specific_issues = self._check_content_type_requirements(content)
        issues.extend(type_specific_issues)

        # Calculate overall score
        overall_score = self._calculate_overall_score(issues, metrics)

        # Determine if passed
        critical_issues = [i for i in issues if i.severity == 'critical']
        passed = len(critical_issues) == 0 and overall_score >= 0.7

        return QualityReport(
            passed=passed,
            overall_score=overall_score,
            issues=issues,
            suggestions=suggestions,
            metrics=metrics,
            timestamp=datetime.now()
        )

    def _check_structure(self, content: GeneratedContent) -> List[QualityIssue]:
        """Check content structure"""
        issues = []
        body = content.body

        # Check for sections/paragraphs
        paragraphs = [p for p in body.split('\n\n') if p.strip()]
        if len(paragraphs) < 2 and len(body.split()) > 200:
            issues.append(QualityIssue(
                severity='warning',
                category='structure',
                message="Long content lacks paragraph breaks",
                suggestion="Break content into logical sections for better readability"
            ))

        # Check for lists when appropriate
        if content.content_type in [ContentType.ELDER_CARE_PROTOCOL, ContentType.DISASTER_RESPONSE]:
            has_lists = any(marker in body for marker in ['1.', '2.', '•', '-', '*'])
            if not has_lists:
                issues.append(QualityIssue(
                    severity='warning',
                    category='structure',
                    message="Procedural content should include numbered lists or steps",
                    suggestion="Format key steps as numbered or bulleted lists"
                ))

        return issues

    def _check_content_type_requirements(self, content: GeneratedContent) -> List[QualityIssue]:
        """Check content type specific requirements"""
        issues = []

        if content.content_type == ContentType.GRANT_NARRATIVE:
            # Check for required grant components
            required_terms = ['need', 'approach', 'outcome', 'impact']
            missing_terms = [term for term in required_terms if term not in content.body.lower()]

            if missing_terms:
                issues.append(QualityIssue(
                    severity='warning',
                    category='structure',
                    message=f"Grant narrative may be missing key components: {', '.join(missing_terms)}",
                    suggestion="Ensure narrative includes: need statement, approach, expected outcomes, and impact"
                ))

        elif content.content_type == ContentType.ELDER_CARE_PROTOCOL:
            # Check for safety and dignity mentions
            if 'safety' not in content.body.lower():
                issues.append(QualityIssue(
                    severity='warning',
                    category='accuracy',
                    message="Elder care protocol should explicitly address safety",
                    suggestion="Add safety considerations and precautions"
                ))

            if 'dignity' not in content.body.lower() and 'respect' not in content.body.lower():
                issues.append(QualityIssue(
                    severity='warning',
                    category='cultural',
                    message="Elder care protocol should emphasize dignity and respect",
                    suggestion="Explicitly mention respecting elder dignity"
                ))

        elif content.content_type == ContentType.DISASTER_RESPONSE:
            # Check for emergency contacts
            has_emergency_info = any(term in content.body for term in ['911', 'emergency', 'contact', 'hotline'])
            if not has_emergency_info:
                issues.append(QualityIssue(
                    severity='critical',
                    category='accuracy',
                    message="Disaster response content missing emergency contact information",
                    suggestion="Add emergency phone numbers and resources"
                ))

        return issues

    def _calculate_overall_score(self, issues: List[QualityIssue], metrics: Dict[str, Any]) -> float:
        """Calculate overall quality score"""

        base_score = 1.0

        # Deduct for issues
        for issue in issues:
            if issue.severity == 'critical':
                base_score -= 0.3
            elif issue.severity == 'warning':
                base_score -= 0.1
            else:  # info
                base_score -= 0.05

        # Bonus for good readability
        if 'readability' in metrics:
            readability = metrics['readability']
            if 60 <= readability.get('flesch_score', 0) <= 80:
                base_score += 0.1

        return max(0.0, min(1.0, base_score))


# Global quality checker instance
quality_checker = ContentQualityChecker()


async def check_content_quality(content: GeneratedContent) -> QualityReport:
    """Convenience function for quality checking"""
    return await quality_checker.validate_content(content)
