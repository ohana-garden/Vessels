#!/usr/bin/env python3
"""
VESSELS GIST EXTRACTOR
Identifies meaningful "gists" in conversation responses
A gist is a crystallized insight, decision, action, or milestone
"""

import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class GistType(Enum):
    """Types of gists that can emerge from conversation"""
    INSIGHT = "insight"
    DECISION = "decision"
    ACTION = "action"
    RESOURCE = "resource"
    CONNECTION = "connection"
    MILESTONE = "milestone"


@dataclass
class Gist:
    """A crystallized moment from conversation"""
    type: GistType
    content: str
    confidence: float
    context: Optional[str] = None
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.type.value,
            'content': self.content,
            'confidence': self.confidence,
            'context': self.context,
            'metadata': self.metadata or {}
        }


class GistExtractor:
    """Extracts meaningful gists from text"""

    # Pattern definitions for each gist type
    PATTERNS = {
        GistType.INSIGHT: [
            (r'(?:key|important|critical)\s+(?:insight|finding|observation)[:\s]+(.{20,200})', 0.9),
            (r'(?:we|I)\s+(?:now\s+)?understand\s+that\s+(.{20,150})', 0.85),
            (r'(?:this|that)\s+means\s+(.{20,150})', 0.7),
            (r'(?:the\s+)?(?:real|core|key)\s+(?:issue|point|thing)\s+is\s+(.{20,150})', 0.8),
            (r"we'?(?:ve|ll)\s+(?:discovered|learned|realized)\s+(?:that\s+)?(.{20,150})", 0.85),
            (r'breakthrough[:\s]+(.{20,200})', 0.9),
        ],
        GistType.DECISION: [
            (r'(?:we|I)\s+(?:have\s+)?decided\s+(?:to\s+)?(.{20,150})', 0.9),
            (r"let'?s\s+(?:go\s+with|proceed\s+with|do)\s+(.{20,150})", 0.85),
            (r'(?:the\s+)?decision\s+is[:\s]+(.{20,150})', 0.9),
            (r'(?:we|I)\s+will\s+(?:proceed|move\s+forward)\s+with\s+(.{20,150})', 0.85),
            (r'confirmed[:\s]+(.{20,150})', 0.8),
            (r'our\s+choice\s+is\s+(.{20,150})', 0.85),
        ],
        GistType.ACTION: [
            (r'next\s+step(?:s)?[:\s]+(.{20,200})', 0.9),
            (r'action\s+item(?:s)?[:\s]+(.{20,200})', 0.95),
            (r'todo[:\s]+(.{20,150})', 0.9),
            (r'(?:we|you)\s+need\s+to\s+(.{20,150})', 0.75),
            (r'follow[- ]?up[:\s]+(.{20,150})', 0.85),
            (r'task[:\s]+(.{20,150})', 0.85),
            (r'please\s+(?:do|complete|finish)\s+(.{20,150})', 0.8),
        ],
        GistType.RESOURCE: [
            (r'(?:found|identified|discovered)\s+(?:a\s+)?(?:\$[\d,]+[KMB]?)\s+(.{20,150})', 0.95),
            (r'grant(?:s)?\s+(?:found|identified|available)[:\s]+(.{20,200})', 0.9),
            (r'funding\s+opportunity[:\s]+(.{20,200})', 0.9),
            (r'resource(?:s)?\s+available[:\s]+(.{20,150})', 0.85),
            (r'budget[:\s]+\$?([\d,]+[KMB]?)\s+(.{20,100})', 0.8),
            (r'contact[:\s]+(.{10,100})', 0.75),
        ],
        GistType.CONNECTION: [
            (r'(?:connected|linked)\s+with\s+(.{10,150})', 0.85),
            (r'partnership\s+with\s+(.{10,150})', 0.9),
            (r'collaboration\s+with\s+(.{10,150})', 0.85),
            (r'introduced\s+to\s+(.{10,100})', 0.8),
            (r'relationship\s+with\s+(.{10,150})', 0.75),
            (r'network(?:ed|ing)\s+with\s+(.{10,150})', 0.8),
        ],
        GistType.MILESTONE: [
            (r'milestone[!:\s]+(.{20,200})', 0.95),
            (r'achievement[!:\s]+(.{20,200})', 0.95),
            (r'(?:successfully\s+)?completed[!:\s]+(.{20,150})', 0.9),
            (r'success[!:\s]+(.{20,200})', 0.85),
            (r'accomplished\s+(.{20,150})', 0.9),
            (r'reached\s+(?:our\s+)?goal\s+(?:of\s+)?(.{20,150})', 0.9),
            (r'celebration[!:\s]+(.{20,150})', 0.8),
        ]
    }

    # Booster keywords that increase confidence
    CONFIDENCE_BOOSTERS = {
        'important': 0.1,
        'critical': 0.15,
        'significant': 0.1,
        'breakthrough': 0.15,
        'major': 0.1,
        'key': 0.1,
        'essential': 0.1,
    }

    def __init__(self):
        self.compiled_patterns = {}
        for gist_type, patterns in self.PATTERNS.items():
            self.compiled_patterns[gist_type] = [
                (re.compile(pattern, re.IGNORECASE | re.DOTALL), confidence)
                for pattern, confidence in patterns
            ]

    def extract_gists(self, text: str, context: str = None) -> List[Gist]:
        """
        Extract all gists from text.

        Args:
            text: The text to analyze
            context: Optional broader context

        Returns:
            List of Gist objects
        """
        gists = []

        for gist_type, patterns in self.compiled_patterns.items():
            for pattern, base_confidence in patterns:
                matches = pattern.findall(text)
                for match in matches:
                    # Handle tuple matches (from groups)
                    content = match if isinstance(match, str) else ' '.join(match)
                    content = self._clean_content(content)

                    if len(content) < 15:  # Too short to be meaningful
                        continue

                    # Calculate confidence with boosters
                    confidence = base_confidence
                    for word, boost in self.CONFIDENCE_BOOSTERS.items():
                        if word in text.lower():
                            confidence = min(1.0, confidence + boost)

                    gist = Gist(
                        type=gist_type,
                        content=content,
                        confidence=confidence,
                        context=context[:200] if context else None
                    )
                    gists.append(gist)

        # Deduplicate and sort by confidence
        gists = self._deduplicate_gists(gists)
        gists.sort(key=lambda g: g.confidence, reverse=True)

        return gists

    def extract_best_gist(self, text: str, context: str = None) -> Optional[Gist]:
        """
        Extract the single best gist from text.

        Args:
            text: The text to analyze
            context: Optional broader context

        Returns:
            Best Gist or None
        """
        gists = self.extract_gists(text, context)
        return gists[0] if gists else None

    def _clean_content(self, content: str) -> str:
        """Clean and normalize gist content"""
        # Remove extra whitespace
        content = ' '.join(content.split())
        # Remove trailing punctuation except periods
        content = re.sub(r'[,;:]+$', '', content)
        # Capitalize first letter
        if content:
            content = content[0].upper() + content[1:]
        return content.strip()

    def _deduplicate_gists(self, gists: List[Gist]) -> List[Gist]:
        """Remove duplicate or highly similar gists"""
        seen = set()
        unique = []

        for gist in gists:
            # Create a normalized key
            key = (gist.type, gist.content[:50].lower())
            if key not in seen:
                seen.add(key)
                unique.append(gist)

        return unique


# Singleton instance
gist_extractor = GistExtractor()


def extract_gists_from_response(response_text: str, request_text: str = None) -> List[Dict]:
    """
    Convenience function to extract gists from a response.

    Args:
        response_text: The response to analyze
        request_text: Optional original request for context

    Returns:
        List of gist dictionaries
    """
    gists = gist_extractor.extract_gists(response_text, request_text)
    return [g.to_dict() for g in gists]


def get_best_gist(response_text: str, request_text: str = None) -> Optional[Dict]:
    """
    Get the single best gist from a response.

    Args:
        response_text: The response to analyze
        request_text: Optional original request for context

    Returns:
        Gist dictionary or None
    """
    gist = gist_extractor.extract_best_gist(response_text, request_text)
    return gist.to_dict() if gist else None


# Demo/testing
if __name__ == '__main__':
    test_texts = [
        "Key insight: The community garden project could serve as a central hub for both food distribution and social gathering.",
        "We have decided to proceed with the grant application for the Older Americans Act funding.",
        "Next steps: Schedule meeting with County Elder Services to discuss partnership opportunities.",
        "Found $50,000 Hawaii Community Foundation grant matching our elder care criteria.",
        "Connected with Aunty Leilani who coordinates meals for 12 kupuna in Waimea.",
        "Milestone! First successful week of volunteer-coordinated meal deliveries - 45 meals served!",
    ]

    print("Testing Gist Extractor:\n")
    for text in test_texts:
        gist = get_best_gist(text)
        if gist:
            print(f"  Type: {gist['type']}")
            print(f"  Content: {gist['content']}")
            print(f"  Confidence: {gist['confidence']:.2f}")
            print()
