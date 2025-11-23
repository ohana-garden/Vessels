"""
Fact-checking logic for the Gardener agent.

Detects contradictions in community memory and flags them
for human review.
"""

import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class Contradiction:
    """Represents a detected contradiction between memories."""
    id: str
    memory_a_id: str
    memory_b_id: str
    memory_a_content: str
    memory_b_content: str
    contradiction_type: str  # "factual", "temporal", "logical"
    confidence: float
    detected_at: datetime
    resolution: Optional[str] = None  # "memory_a_correct", "memory_b_correct", "both_wrong", etc.

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "memory_a_id": self.memory_a_id,
            "memory_b_id": self.memory_b_id,
            "memory_a_content": self.memory_a_content,
            "memory_b_content": self.memory_b_content,
            "contradiction_type": self.contradiction_type,
            "confidence": self.confidence,
            "detected_at": self.detected_at.isoformat(),
            "resolution": self.resolution
        }


class FactChecker:
    """
    Detects contradictions in community memory.

    Strategies:
    - Keyword-based contradiction detection
    - Temporal inconsistency detection
    - Logical inconsistency detection
    """

    def __init__(self):
        """Initialize fact checker."""
        self.contradictions_found = []
        self.contradiction_keywords = self._load_contradiction_keywords()

    def _load_contradiction_keywords(self) -> Dict[str, List[str]]:
        """
        Load keyword pairs that indicate contradictions.

        Returns:
            Dict of contradiction types to keyword pairs
        """
        return {
            "location": [
                ("road open", "road closed"),
                ("available", "unavailable"),
                ("operating", "not operating"),
            ],
            "status": [
                ("success", "failure"),
                ("completed", "incomplete"),
                ("working", "broken"),
            ],
            "boolean": [
                ("yes", "no"),
                ("true", "false"),
                ("confirmed", "denied"),
            ]
        }

    def find_contradictions(
        self,
        memories: List[Dict[str, Any]]
    ) -> List[Contradiction]:
        """
        Find contradictions in memories.

        Args:
            memories: List of memory dictionaries

        Returns:
            List of detected contradictions
        """
        self.contradictions_found = []

        # Check all pairs of memories
        for i in range(len(memories)):
            for j in range(i + 1, len(memories)):
                memory_a = memories[i]
                memory_b = memories[j]

                # Check for contradictions
                contradiction = self._check_pair_for_contradiction(memory_a, memory_b)
                if contradiction:
                    self.contradictions_found.append(contradiction)

        logger.info(f"Found {len(self.contradictions_found)} contradictions")

        return self.contradictions_found

    def _check_pair_for_contradiction(
        self,
        memory_a: Dict[str, Any],
        memory_b: Dict[str, Any]
    ) -> Optional[Contradiction]:
        """
        Check if two memories contradict each other.

        Args:
            memory_a: First memory
            memory_b: Second memory

        Returns:
            Contradiction object if contradiction detected, None otherwise
        """
        # Extract content
        content_a = self._extract_content(memory_a)
        content_b = self._extract_content(memory_b)

        if not content_a or not content_b:
            return None

        # Normalize to lowercase
        content_a_lower = content_a.lower()
        content_b_lower = content_b.lower()

        # Check keyword-based contradictions
        for contradiction_type, keyword_pairs in self.contradiction_keywords.items():
            for phrase_a, phrase_b in keyword_pairs:
                if phrase_a in content_a_lower and phrase_b in content_b_lower:
                    # Found contradiction!
                    import uuid
                    return Contradiction(
                        id=str(uuid.uuid4()),
                        memory_a_id=memory_a.get("id") or memory_a.get("memory_id", "unknown"),
                        memory_b_id=memory_b.get("id") or memory_b.get("memory_id", "unknown"),
                        memory_a_content=content_a,
                        memory_b_content=content_b,
                        contradiction_type=contradiction_type,
                        confidence=0.8,  # Keyword-based has medium confidence
                        detected_at=datetime.now()
                    )

        # Check temporal contradictions
        temporal_contradiction = self._check_temporal_contradiction(memory_a, memory_b)
        if temporal_contradiction:
            return temporal_contradiction

        return None

    def _extract_content(self, memory: Dict[str, Any]) -> str:
        """Extract content string from memory."""
        content = memory.get("content")

        if isinstance(content, dict):
            # Try common keys
            return (
                content.get("content") or
                content.get("description") or
                content.get("text") or
                str(content)
            )
        elif isinstance(content, str):
            return content
        else:
            return str(content) if content else ""

    def _check_temporal_contradiction(
        self,
        memory_a: Dict[str, Any],
        memory_b: Dict[str, Any]
    ) -> Optional[Contradiction]:
        """
        Check for temporal contradictions.

        Example: "Event happened at 2pm" vs "Event happened at 3pm"

        Args:
            memory_a: First memory
            memory_b: Second memory

        Returns:
            Contradiction if found
        """
        # Simple heuristic: look for time-related keywords with different values
        # TODO: Implement sophisticated temporal reasoning

        content_a = self._extract_content(memory_a)
        content_b = self._extract_content(memory_b)

        # Check for time contradictions
        time_keywords = ["at", "on", "during", "scheduled"]
        has_time_a = any(kw in content_a.lower() for kw in time_keywords)
        has_time_b = any(kw in content_b.lower() for kw in time_keywords)

        # If both mention time and content differs significantly, might be temporal contradiction
        # This is a simplification - real implementation would parse times
        if has_time_a and has_time_b:
            # Check if they're about the same topic (have overlapping keywords)
            words_a = set(content_a.lower().split())
            words_b = set(content_b.lower().split())
            overlap = words_a & words_b

            # If significant overlap but different times mentioned, flag as potential contradiction
            if len(overlap) > 3:  # At least 3 common words
                import uuid
                return Contradiction(
                    id=str(uuid.uuid4()),
                    memory_a_id=memory_a.get("id", "unknown"),
                    memory_b_id=memory_b.get("id", "unknown"),
                    memory_a_content=content_a,
                    memory_b_content=content_b,
                    contradiction_type="temporal",
                    confidence=0.5,  # Lower confidence for temporal
                    detected_at=datetime.now()
                )

        return None

    def flag_for_review(
        self,
        contradiction: Contradiction,
        review_callback: callable = None
    ) -> None:
        """
        Flag a contradiction for human review.

        Args:
            contradiction: Contradiction to flag
            review_callback: Optional callback for review system
        """
        logger.warning(
            f"Contradiction flagged for review: "
            f"{contradiction.memory_a_id} vs {contradiction.memory_b_id} "
            f"({contradiction.contradiction_type})"
        )

        if review_callback:
            review_callback(contradiction)

    def get_flagged_contradictions(self) -> List[Contradiction]:
        """Get all flagged contradictions."""
        return self.contradictions_found
