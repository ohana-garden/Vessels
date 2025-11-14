#!/usr/bin/env python3
"""
OFFER MANAGEMENT SYSTEM
Handles creation and matching of product and service offers
Gig business owners can declare what they offer
Customers can find local products/services
"""

import logging
import re
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

from agent_zero_core import ProductAgent, ServiceAgent, OfferStatus
from community_memory import OfferEntry, community_memory

logger = logging.getLogger(__name__)

def create_offer_from_text(user_id: str, offer_text: str) -> Dict[str, Any]:
    """Create a ProductAgent or ServiceAgent from natural language description

    Args:
        user_id: ID of the actor offering the product/service
        offer_text: Natural language description of what they offer

    Returns:
        Dictionary with offer details and success status
    """
    # Detect if this is a product or service
    is_product = any(
        word in offer_text.lower() for word in ["sell", "selling", "lbs", "pounds", "bags", "items", "have"]
    )
    is_service = any(
        word in offer_text.lower() for word in ["can do", "can help", "can provide", "offer rides", "offer care", "can cook", "can drive", "can repair"]
    )

    # Extract offer details
    offer_details = _extract_offer_details(offer_text, is_product)

    # Generate IDs
    offer_id = str(uuid.uuid4())

    if is_product:
        # Create ProductAgent
        product = ProductAgent(
            id=offer_id,
            owner_actor_id=user_id,
            name=offer_details.get("name", "Unnamed Product"),
            description=offer_details.get("description", offer_text),
            categories=offer_details.get("categories", []),
            constraints=offer_details.get("constraints", {}),
            quantity_available=offer_details.get("quantity", 1),
            unit=offer_details.get("unit", "unit"),
            pricing_usd=offer_details.get("price", 0.0),
            location=offer_details.get("location", ""),
            radius_miles=offer_details.get("radius", 10.0),
            status=OfferStatus.ACTIVE,
            metadata=offer_details.get("metadata", {})
        )

        # Store as OfferEntry in community memory
        offer_entry = OfferEntry(
            offer_id=offer_id,
            owner_actor_id=user_id,
            offer_type="product",
            categories=offer_details.get("categories", []),
            description=product.get_canonical_description(),
            capacity_info={"quantity": product.quantity_available, "unit": product.unit},
            location=product.location,
            radius_miles=product.radius_miles,
            pricing_usd={"amount": product.pricing_usd, "currency": "USD"},
            constraints=product.constraints,
            status="active",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        community_memory.store_offer(offer_entry)

        logger.info(f"Created product offer {offer_id} for user {user_id}")

        return {
            "success": True,
            "offer_type": "product",
            "offer_id": offer_id,
            "offer": product,
            "details": offer_details
        }

    elif is_service:
        # Create ServiceAgent
        service = ServiceAgent(
            id=offer_id,
            owner_actor_id=user_id,
            name=offer_details.get("name", "Unnamed Service"),
            description=offer_details.get("description", offer_text),
            categories=offer_details.get("categories", []),
            constraints=offer_details.get("constraints", {}),
            available_slots=offer_details.get("slots", []),
            max_jobs_per_period=offer_details.get("max_jobs", 10),
            pricing_usd=offer_details.get("price", 0.0),
            pricing_unit=offer_details.get("pricing_unit", "hour"),
            location=offer_details.get("location", ""),
            radius_miles=offer_details.get("radius", 10.0),
            status=OfferStatus.ACTIVE,
            metadata=offer_details.get("metadata", {})
        )

        # Store as OfferEntry in community memory
        offer_entry = OfferEntry(
            offer_id=offer_id,
            owner_actor_id=user_id,
            offer_type="service",
            categories=offer_details.get("categories", []),
            description=service.get_canonical_description(),
            capacity_info={"slots": len(service.available_slots), "max_jobs": service.max_jobs_per_period},
            location=service.location,
            radius_miles=service.radius_miles,
            pricing_usd={"amount": service.pricing_usd, "per": service.pricing_unit, "currency": "USD"},
            constraints=service.constraints,
            status="active",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        community_memory.store_offer(offer_entry)

        logger.info(f"Created service offer {offer_id} for user {user_id}")

        return {
            "success": True,
            "offer_type": "service",
            "offer_id": offer_id,
            "offer": service,
            "details": offer_details
        }

    else:
        return {
            "success": False,
            "error": "Could not determine if this is a product or service offer"
        }

def _extract_offer_details(offer_text: str, is_product: bool) -> Dict[str, Any]:
    """Extract structured details from offer description"""
    details = {
        "name": "",
        "description": offer_text,
        "categories": [],
        "constraints": {},
        "location": "",
        "radius": 10.0,
        "price": 0.0,
        "metadata": {}
    }

    text_lower = offer_text.lower()

    # Extract quantity for products
    if is_product:
        quantity_match = re.search(r'(\d+)\s*(lbs?|pounds?|bags?|items?|units?)', text_lower)
        if quantity_match:
            details["quantity"] = int(quantity_match.group(1))
            details["unit"] = quantity_match.group(2)

    # Extract location
    location_keywords = ["in", "at", "from", "near"]
    for keyword in location_keywords:
        pattern = rf"{keyword}\s+([A-Z][a-zA-Z\s]+?)(?:\s|$|,)"
        match = re.search(pattern, offer_text)
        if match:
            details["location"] = match.group(1).strip()
            break

    # Extract price
    price_match = re.search(r'\$(\d+(?:\.\d{2})?)', offer_text)
    if price_match:
        details["price"] = float(price_match.group(1))

    # Extract categories based on keywords
    category_keywords = {
        "food": ["food", "meal", "plate lunch", "breadfruit", "ulu", "produce", "vegetables"],
        "care": ["care", "caregiving", "elder care", "childcare"],
        "transportation": ["rides", "transport", "driving", "pickup", "delivery"],
        "yardwork": ["yardwork", "yard work", "landscaping", "mowing", "gardening"],
        "repair": ["repair", "fix", "maintenance", "plumbing", "electrical"],
        "cleaning": ["cleaning", "housekeeping", "janitorial"],
        "cooking": ["cooking", "meal prep", "catering"]
    }

    for category, keywords in category_keywords.items():
        if any(kw in text_lower for kw in keywords):
            details["categories"].append(category)

    # Generate name if not provided
    if not details["name"]:
        # Use first 50 chars of description as name
        details["name"] = offer_text[:50].strip()

    # Service-specific details
    if not is_product:
        details["slots"] = []  # Would need more complex parsing to extract actual slots
        details["max_jobs"] = 10
        details["pricing_unit"] = "hour"

        # Try to detect pricing unit
        if "per day" in text_lower or "daily" in text_lower:
            details["pricing_unit"] = "day"
        elif "per visit" in text_lower or "per job" in text_lower:
            details["pricing_unit"] = "visit"

    return details

def find_offers(need_description: str) -> List[Dict[str, Any]]:
    """Find offers that match a need description"""
    # Convert need description to structured query
    need_query = {
        "description": need_description,
        "categories": _extract_categories_from_text(need_description),
        "location": _extract_location_from_text(need_description)
    }

    # Search community memory for matching offers
    matching_offers = community_memory.find_matching_offers(need_query)

    return matching_offers

def _extract_categories_from_text(text: str) -> List[str]:
    """Extract category keywords from text"""
    categories = []
    text_lower = text.lower()

    category_keywords = {
        "food": ["food", "meal", "eat", "hungry", "breadfruit", "produce"],
        "care": ["care", "help", "support", "elder", "senior"],
        "transportation": ["ride", "transport", "drive", "pickup"],
        "yardwork": ["yard", "lawn", "garden", "landscap"],
        "repair": ["repair", "fix", "broken", "maintenance"],
        "cleaning": ["clean", "housekeeping", "tidy"]
    }

    for category, keywords in category_keywords.items():
        if any(kw in text_lower for kw in keywords):
            categories.append(category)

    return categories

def _extract_location_from_text(text: str) -> str:
    """Extract location from text"""
    location_keywords = ["in", "at", "near", "from"]
    for keyword in location_keywords:
        pattern = rf"{keyword}\s+([A-Z][a-zA-Z\s]+?)(?:\s|$|,)"
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    return ""

def get_offers_by_owner(owner_id: str) -> List[OfferEntry]:
    """Get all offers from a specific owner"""
    return community_memory.get_offers_by_owner(owner_id)
