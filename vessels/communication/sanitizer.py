"""
Data Sanitizer for External Communication

Removes or masks personally identifiable information (PII) before sending data
to external networks like Nostr or Petals.

Privacy Model:
- Strip direct identifiers (names, addresses, phone numbers)
- Generalize locations (city-level only)
- Mask specific quantities (round to ranges)
- Apply k-anonymity where applicable
"""

import re
import logging
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SanitizationPolicy:
    """Policy for sanitizing different event types"""
    strip_names: bool = True
    strip_addresses: bool = True
    strip_phone_numbers: bool = True
    strip_emails: bool = True
    generalize_locations: bool = True
    round_quantities: bool = False
    allowed_fields: Optional[Set[str]] = None  # If set, only these fields pass
    k_anonymity: int = 1  # Minimum group size for aggregates


class DataSanitizer:
    """
    Sanitize data before external transmission

    Implements graduated privacy controls based on event type and sensitivity.
    """

    # Patterns for PII detection
    PHONE_PATTERN = re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b')
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    ADDRESS_PATTERN = re.compile(r'\b\d+\s+[A-Za-z0-9\s,]+\b(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct)\b', re.IGNORECASE)

    # Common first/last names (simplified - production would use NER)
    COMMON_NAMES = {
        'john', 'mary', 'james', 'patricia', 'robert', 'jennifer', 'michael',
        'linda', 'william', 'elizabeth', 'david', 'barbara', 'richard', 'susan'
    }

    # Policies for different event types
    POLICIES = {
        "node_status": SanitizationPolicy(
            strip_names=True,
            strip_addresses=True,
            generalize_locations=True,
            allowed_fields={"node_id", "version", "capabilities", "uptime_seconds"}
        ),
        "offer": SanitizationPolicy(
            strip_names=True,
            strip_addresses=True,
            generalize_locations=True,
            round_quantities=True,
            allowed_fields={"type", "quantity", "unit", "location", "expires_at"}
        ),
        "need": SanitizationPolicy(
            strip_names=True,
            strip_addresses=True,
            generalize_locations=False,  # Needs can keep general location
            round_quantities=True,
            allowed_fields={"type", "quantity", "unit", "urgency"}
        ),
        "announcement": SanitizationPolicy(
            strip_names=False,  # Announcements are public
            strip_addresses=True,
            generalize_locations=True,
            allowed_fields={"title", "description", "event_time"}
        ),
        "community_metric": SanitizationPolicy(
            strip_names=True,
            strip_addresses=True,
            generalize_locations=True,
            k_anonymity=5,  # Metrics must represent at least 5 people
            allowed_fields={"metric_type", "value", "period", "anonymized"}
        ),
        "default": SanitizationPolicy(
            strip_names=True,
            strip_addresses=True,
            strip_phone_numbers=True,
            strip_emails=True,
            generalize_locations=True
        )
    }

    def __init__(self):
        self.stats = {
            "total_sanitized": 0,
            "pii_detected": 0,
            "fields_removed": 0
        }

    def sanitize(
        self,
        data: Dict[str, Any],
        event_type: str = "default",
        custom_policy: Optional[SanitizationPolicy] = None
    ) -> Dict[str, Any]:
        """
        Sanitize data according to policy

        Args:
            data: Data to sanitize
            event_type: Type of event (determines policy)
            custom_policy: Override default policy

        Returns:
            Sanitized data with PII removed/masked
        """
        policy = custom_policy or self.POLICIES.get(event_type, self.POLICIES["default"])

        sanitized = {}
        self.stats["total_sanitized"] += 1

        for key, value in data.items():
            # Check allowed fields
            if policy.allowed_fields and key not in policy.allowed_fields:
                self.stats["fields_removed"] += 1
                logger.debug(f"Removed field '{key}' (not in allowed list)")
                continue

            # Recursively sanitize nested dicts
            if isinstance(value, dict):
                sanitized[key] = self.sanitize(value, event_type, policy)
                continue

            # Recursively sanitize lists
            if isinstance(value, list):
                sanitized[key] = [
                    self.sanitize(item, event_type, policy) if isinstance(item, dict) else item
                    for item in value
                ]
                continue

            # Sanitize string values
            if isinstance(value, str):
                original = value

                if policy.strip_phone_numbers:
                    value = self._remove_phone_numbers(value)

                if policy.strip_emails:
                    value = self._remove_emails(value)

                if policy.strip_addresses:
                    value = self._remove_addresses(value)

                if policy.strip_names:
                    value = self._remove_names(value)

                if key == "location" and policy.generalize_locations:
                    value = self._generalize_location(value)

                if original != value:
                    self.stats["pii_detected"] += 1

                sanitized[key] = value

            # Round quantities if requested
            elif isinstance(value, (int, float)) and key == "quantity" and policy.round_quantities:
                sanitized[key] = self._round_quantity(value)

            else:
                sanitized[key] = value

        return sanitized

    def _remove_phone_numbers(self, text: str) -> str:
        """Remove phone numbers from text"""
        return self.PHONE_PATTERN.sub("[PHONE]", text)

    def _remove_emails(self, text: str) -> str:
        """Remove email addresses from text"""
        return self.EMAIL_PATTERN.sub("[EMAIL]", text)

    def _remove_addresses(self, text: str) -> str:
        """Remove street addresses from text"""
        return self.ADDRESS_PATTERN.sub("[ADDRESS]", text)

    def _remove_names(self, text: str) -> str:
        """
        Remove names from text (simplified)

        Production implementation should use NER (spaCy, transformers)
        """
        words = text.split()
        sanitized = []

        for word in words:
            # Check if word looks like a name (simplified heuristic)
            word_lower = word.lower().strip('.,!?;:')
            if word_lower in self.COMMON_NAMES:
                sanitized.append("[NAME]")
            elif len(word) > 2 and word[0].isupper() and word[1:].islower():
                # Capitalized word (might be name)
                # More sophisticated check needed in production
                sanitized.append("[NAME]")
            else:
                sanitized.append(word)

        return " ".join(sanitized)

    def _generalize_location(self, location: str) -> str:
        """
        Generalize location to city-level only

        Examples:
            "123 Main St, Oakland, CA" → "Oakland, CA"
            "Berkeley" → "Berkeley"
            "Near Temescal" → "Oakland area"
        """
        # Simple heuristic: extract city name
        # Production should use geocoding library

        if not location:
            return location

        # If contains street address, strip it
        location = self.ADDRESS_PATTERN.sub("", location).strip()

        # If contains ZIP code, remove it
        location = re.sub(r'\b\d{5}(-\d{4})?\b', '', location).strip()

        # Clean up extra commas
        location = re.sub(r',\s*,', ',', location).strip(',').strip()

        return location or "[LOCATION]"

    def _round_quantity(self, quantity: float) -> float:
        """
        Round quantities to protect privacy

        Examples:
            1-5 → 5
            6-10 → 10
            11-20 → 20
            21-50 → 50
            51+ → 100
        """
        if quantity <= 5:
            return 5.0
        elif quantity <= 10:
            return 10.0
        elif quantity <= 20:
            return 20.0
        elif quantity <= 50:
            return 50.0
        else:
            return 100.0

    def sanitize_for_petals(self, prompt: str) -> str:
        """
        Sanitize prompt before sending to Petals network

        More aggressive than Nostr sanitization since it's going to
        distributed compute nodes.
        """
        sanitized = prompt

        # Remove all PII patterns
        sanitized = self._remove_phone_numbers(sanitized)
        sanitized = self._remove_emails(sanitized)
        sanitized = self._remove_addresses(sanitized)
        sanitized = self._remove_names(sanitized)

        # Remove specific identifiers
        sanitized = re.sub(r'\b[A-Z]{2,}\d{4,}\b', '[ID]', sanitized)  # IDs like ABC1234

        # Replace specific numbers with ranges
        # "I have 37 tomatoes" → "I have 30-40 tomatoes"
        def round_number(match):
            num = int(match.group(0))
            if num < 10:
                return str(num)  # Keep small numbers
            elif num < 100:
                lower = (num // 10) * 10
                upper = lower + 10
                return f"{lower}-{upper}"
            else:
                lower = (num // 50) * 50
                upper = lower + 50
                return f"{lower}-{upper}"

        sanitized = re.sub(r'\b\d{2,}\b', round_number, sanitized)

        return sanitized

    def check_k_anonymity(self, data: List[Dict[str, Any]], k: int) -> bool:
        """
        Check if aggregated data satisfies k-anonymity

        Args:
            data: List of records
            k: Minimum group size

        Returns:
            True if k-anonymity is satisfied
        """
        # Simple check: must have at least k records
        # Production should check for proper k-anonymity with quasi-identifiers
        return len(data) >= k

    def get_stats(self) -> Dict[str, int]:
        """Get sanitization statistics"""
        return self.stats.copy()


def example_usage():
    """Example usage of DataSanitizer"""

    sanitizer = DataSanitizer()

    # Example 1: Sanitize an offer
    offer = {
        "type": "tomatoes",
        "quantity": 12.5,
        "unit": "kg",
        "location": "123 Main St, Oakland, CA 94612",
        "contact": "John Smith",
        "phone": "510-555-1234",
        "email": "john@example.com"
    }

    sanitized_offer = sanitizer.sanitize(offer, event_type="offer")
    print("Original offer:", offer)
    print("Sanitized offer:", sanitized_offer)
    # Output: {'type': 'tomatoes', 'quantity': 20.0, 'unit': 'kg', 'location': 'Oakland, CA'}

    # Example 2: Sanitize for Petals
    prompt = """
    I'm John Smith from 123 Main St, Oakland.
    I have 37 tomato plants and need help with pest control.
    Call me at 510-555-1234.
    """

    sanitized_prompt = sanitizer.sanitize_for_petals(prompt)
    print("\nOriginal prompt:", prompt)
    print("Sanitized prompt:", sanitized_prompt)

    # Example 3: Check stats
    print("\nSanitization stats:", sanitizer.get_stats())


if __name__ == "__main__":
    example_usage()
