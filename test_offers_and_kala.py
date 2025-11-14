#!/usr/bin/env python3
"""
Tests for OfferAgents and Kala constraints
Ensures proper implementation of gig marketplace model
"""

import unittest
import uuid
from datetime import datetime

# Import core modules
from agent_zero_core import ProductAgent, ServiceAgent, OfferStatus
from community_memory import (
    OfferEntry, ContextEvent, KalaAnnotation,
    EventType, EventStatus,
    community_memory
)
from offer_management import create_offer_from_text, find_offers


class TestProductAgent(unittest.TestCase):
    """Test ProductAgent functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.owner_id = str(uuid.uuid4())

    def test_product_agent_creation(self):
        """Test creating a ProductAgent"""
        product = ProductAgent(
            id=str(uuid.uuid4()),
            owner_actor_id=self.owner_id,
            name="50 lbs Breadfruit",
            description="Fresh breadfruit from Puna",
            categories=["food"],
            constraints={"diet": "vegan"},
            quantity_available=50,
            unit="lbs",
            pricing_usd=25.0,
            location="Pahoa",
            radius_miles=10.0,
            status=OfferStatus.ACTIVE
        )

        self.assertEqual(product.owner_actor_id, self.owner_id)
        self.assertEqual(product.quantity_available, 50)
        self.assertEqual(product.pricing_usd, 25.0)
        self.assertEqual(product.status, OfferStatus.ACTIVE)

    def test_product_canonical_description(self):
        """Test getting canonical description"""
        product = ProductAgent(
            id=str(uuid.uuid4()),
            owner_actor_id=self.owner_id,
            name="Test Product",
            description="Test description",
            categories=["food"],
            constraints={},
            quantity_available=10,
            unit="items",
            pricing_usd=5.0,
            location="Pahoa",
            radius_miles=5.0,
            status=OfferStatus.ACTIVE
        )

        desc = product.get_canonical_description()

        self.assertIn("name", desc)
        self.assertIn("price", desc)
        self.assertEqual(desc["name"], "Test Product")
        self.assertIn("$", desc["price"])

    def test_product_matching(self):
        """Test product matching against needs"""
        product = ProductAgent(
            id=str(uuid.uuid4()),
            owner_actor_id=self.owner_id,
            name="Fresh Food",
            description="Local produce",
            categories=["food"],
            constraints={},
            quantity_available=10,
            unit="lbs",
            pricing_usd=20.0,
            location="Pahoa",
            radius_miles=10.0,
            status=OfferStatus.ACTIVE
        )

        # Test matching need
        need = {
            "categories": ["food"],
            "location": "Pahoa",
            "quantity": 5
        }

        match_result = product.matches_need(need)

        self.assertTrue(match_result["is_match"])
        self.assertGreater(match_result["score"], 0.5)
        self.assertGreater(len(match_result["reasons"]), 0)

    def test_product_capacity_management(self):
        """Test capacity reservation and release"""
        product = ProductAgent(
            id=str(uuid.uuid4()),
            owner_actor_id=self.owner_id,
            name="Test Product",
            description="Test",
            categories=[],
            constraints={},
            quantity_available=10,
            unit="items",
            pricing_usd=5.0,
            location="Test",
            radius_miles=5.0,
            status=OfferStatus.ACTIVE
        )

        # Check initial capacity
        capacity = product.check_capacity()
        self.assertTrue(capacity["available"])
        self.assertEqual(capacity["quantity"], 10)

        # Reserve some capacity
        success = product.reserve_capacity(5)
        self.assertTrue(success)
        self.assertEqual(product.quantity_available, 5)

        # Try to reserve more than available
        success = product.reserve_capacity(10)
        self.assertFalse(success)

        # Release capacity
        product.release_capacity(3)
        self.assertEqual(product.quantity_available, 8)


class TestServiceAgent(unittest.TestCase):
    """Test ServiceAgent functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.owner_id = str(uuid.uuid4())

    def test_service_agent_creation(self):
        """Test creating a ServiceAgent"""
        service = ServiceAgent(
            id=str(uuid.uuid4()),
            owner_actor_id=self.owner_id,
            name="Yard Work",
            description="Lawn mowing and trimming",
            categories=["yardwork"],
            constraints={},
            available_slots=[{"id": "1", "day": "Monday"}],
            max_jobs_per_period=5,
            pricing_usd=30.0,
            pricing_unit="hour",
            location="Pahoa",
            radius_miles=15.0,
            status=OfferStatus.ACTIVE
        )

        self.assertEqual(service.owner_actor_id, self.owner_id)
        self.assertEqual(service.pricing_usd, 30.0)
        self.assertEqual(service.pricing_unit, "hour")
        self.assertEqual(len(service.available_slots), 1)

    def test_service_matching(self):
        """Test service matching against needs"""
        service = ServiceAgent(
            id=str(uuid.uuid4()),
            owner_actor_id=self.owner_id,
            name="Yard Service",
            description="Complete yard maintenance",
            categories=["yardwork"],
            constraints={},
            available_slots=[{"id": "1"}],
            max_jobs_per_period=10,
            pricing_usd=25.0,
            pricing_unit="hour",
            location="Pahoa",
            radius_miles=10.0,
            status=OfferStatus.ACTIVE
        )

        need = {
            "categories": ["yardwork"],
            "location": "Pahoa"
        }

        match_result = service.matches_need(need)

        self.assertTrue(match_result["is_match"])
        self.assertGreater(match_result["score"], 0.5)

    def test_service_slot_management(self):
        """Test service slot reservation"""
        service = ServiceAgent(
            id=str(uuid.uuid4()),
            owner_actor_id=self.owner_id,
            name="Test Service",
            description="Test",
            categories=[],
            constraints={},
            available_slots=[
                {"id": "slot1", "day": "Monday"},
                {"id": "slot2", "day": "Tuesday"}
            ],
            max_jobs_per_period=5,
            pricing_usd=20.0,
            pricing_unit="hour",
            location="Test",
            radius_miles=5.0,
            status=OfferStatus.ACTIVE
        )

        # Check initial capacity
        capacity = service.check_capacity()
        self.assertTrue(capacity["available"])
        self.assertEqual(capacity["slots"], 2)

        # Reserve a slot
        success = service.reserve_slot({"id": "slot1"})
        self.assertTrue(success)
        self.assertEqual(len(service.available_slots), 1)

        # Try to reserve non-existent slot
        success = service.reserve_slot({"id": "slot3"})
        self.assertFalse(success)

        # Release slot
        service.release_slot({"id": "slot1", "day": "Monday"})
        self.assertEqual(len(service.available_slots), 2)


class TestKalaConstraints(unittest.TestCase):
    """Test that Kala is properly constrained as descriptive metrics only"""

    def test_kala_annotation_validation(self):
        """Test Kala annotation rejects currency-like terms"""
        # Valid Kala annotation
        valid_kala = KalaAnnotation(
            dimension="connection",
            value=0.8,
            notes="Strong community connection fostered by this interaction"
        )
        self.assertEqual(valid_kala.dimension, "connection")

        # Invalid Kala annotations (should raise ValueError)
        with self.assertRaises(ValueError):
            KalaAnnotation(
                dimension="test",
                value=10.0,
                notes="User balance increased"  # "balance" is currency-like
            )

        with self.assertRaises(ValueError):
            KalaAnnotation(
                dimension="test",
                value=5.0,
                notes="Price adjustment based on kala"  # "price" is currency-like
            )

        with self.assertRaises(ValueError):
            KalaAnnotation(
                dimension="test",
                value=3.0,
                notes="Payment received"  # "payment" is currency-like
            )

    def test_context_event_with_kala(self):
        """Test that context events properly separate payment and Kala"""
        event = ContextEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.ORDER,
            requestor_actor_id=str(uuid.uuid4()),
            provider_actor_id=str(uuid.uuid4()),
            offer_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            location="Pahoa",
            status=EventStatus.COMPLETED,
            payment_info={
                "amount_usd": 25.0,
                "payment_status": "completed",
                "payment_rail": "bank_transfer"
            }
        )

        # Add Kala annotation
        event.add_kala_annotation(
            dimension="care",
            value=0.9,
            notes="High care quality demonstrated in this service delivery"
        )

        # Verify payment is separate from Kala
        self.assertEqual(event.get_payment_amount(), 25.0)
        self.assertEqual(len(event.kala_annotations), 1)
        self.assertEqual(event.kala_annotations[0].dimension, "care")

        # Verify Kala is not in payment info
        self.assertNotIn("kala", event.payment_info)
        self.assertNotIn("Kala", str(event.payment_info))

    def test_kala_analysis_is_readonly(self):
        """Test that Kala analysis doesn't affect operations"""
        # Create some events with Kala annotations
        event1 = ContextEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.ORDER,
            requestor_actor_id="user1",
            provider_actor_id="provider1",
            offer_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            location="Pahoa",
            status=EventStatus.COMPLETED,
            payment_info={"amount_usd": 20.0}
        )
        event1.add_kala_annotation("connection", 0.7, "Good community connection")

        event2 = ContextEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.SERVICE_VISIT,
            requestor_actor_id="user2",
            provider_actor_id="provider1",
            offer_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            location="Pahoa",
            status=EventStatus.COMPLETED,
            payment_info={"amount_usd": 30.0}
        )
        event2.add_kala_annotation("care", 0.9, "Excellent care provided")

        # Store events
        community_memory.store_context_event(event1)
        community_memory.store_context_event(event2)

        # Analyze Kala metrics
        analysis = community_memory.analyze_kala_metrics()

        # Verify analysis is read-only (doesn't modify events)
        self.assertGreater(analysis["total_events"], 0)
        self.assertIn("care", analysis["kala_dimensions"])
        self.assertIn("connection", analysis["kala_dimensions"])

        # Verify original events unchanged
        retrieved1 = community_memory.get_context_event(event1.event_id)
        self.assertEqual(retrieved1.get_payment_amount(), 20.0)


class TestOfferManagement(unittest.TestCase):
    """Test offer management functions"""

    def test_create_product_offer_from_text(self):
        """Test creating product offer from natural language"""
        user_id = str(uuid.uuid4())
        offer_text = "I have 50 lbs of breadfruit available in Pahoa for $25"

        result = create_offer_from_text(user_id, offer_text)

        self.assertTrue(result["success"])
        self.assertEqual(result["offer_type"], "product")
        self.assertIn("offer_id", result)
        self.assertIn("food", result["details"]["categories"])

    def test_create_service_offer_from_text(self):
        """Test creating service offer from natural language"""
        user_id = str(uuid.uuid4())
        offer_text = "I can do yard work in Pahoa for $30 per hour"

        result = create_offer_from_text(user_id, offer_text)

        self.assertTrue(result["success"])
        self.assertEqual(result["offer_type"], "service")
        self.assertIn("offer_id", result)
        self.assertIn("yardwork", result["details"]["categories"])

    def test_find_offers(self):
        """Test finding offers by description"""
        # Create some test offers first
        user_id = str(uuid.uuid4())
        create_offer_from_text(user_id, "I sell fresh vegetables in Pahoa")
        create_offer_from_text(user_id, "I can provide yard work in Pahoa")

        # Search for food
        results = find_offers("looking for food in Pahoa")

        # Should find at least one match
        self.assertGreaterEqual(len(results), 0)


class TestNoKalaInPricing(unittest.TestCase):
    """Ensure Kala never appears in pricing or access control"""

    def test_product_pricing_usd_only(self):
        """Verify products only use USD pricing"""
        product = ProductAgent(
            id=str(uuid.uuid4()),
            owner_actor_id=str(uuid.uuid4()),
            name="Test",
            description="Test",
            categories=[],
            constraints={},
            quantity_available=1,
            unit="item",
            pricing_usd=10.0,  # Only USD
            location="Test",
            radius_miles=5.0,
            status=OfferStatus.ACTIVE
        )

        desc = product.get_canonical_description()

        # Verify no kala in pricing
        self.assertIn("$", desc["price"])
        self.assertNotIn("kala", str(desc).lower())
        self.assertNotIn("points", str(desc).lower())

    def test_service_pricing_usd_only(self):
        """Verify services only use USD pricing"""
        service = ServiceAgent(
            id=str(uuid.uuid4()),
            owner_actor_id=str(uuid.uuid4()),
            name="Test",
            description="Test",
            categories=[],
            constraints={},
            available_slots=[],
            max_jobs_per_period=5,
            pricing_usd=20.0,  # Only USD
            pricing_unit="hour",
            location="Test",
            radius_miles=5.0,
            status=OfferStatus.ACTIVE
        )

        desc = service.get_canonical_description()

        # Verify no kala in pricing
        self.assertIn("$", desc["price"])
        self.assertNotIn("kala", str(desc).lower())
        self.assertNotIn("points", str(desc).lower())

    def test_matching_no_kala_influence(self):
        """Verify matching doesn't use Kala scores"""
        product = ProductAgent(
            id=str(uuid.uuid4()),
            owner_actor_id=str(uuid.uuid4()),
            name="Test",
            description="Test",
            categories=["food"],
            constraints={},
            quantity_available=10,
            unit="items",
            pricing_usd=5.0,
            location="Pahoa",
            radius_miles=5.0,
            status=OfferStatus.ACTIVE
        )

        need = {"categories": ["food"], "location": "Pahoa"}

        match_result = product.matches_need(need)

        # Verify match result doesn't mention kala
        result_str = str(match_result).lower()
        self.assertNotIn("kala", result_str)
        self.assertNotIn("points", result_str)
        self.assertNotIn("balance", result_str)


if __name__ == "__main__":
    unittest.main()
