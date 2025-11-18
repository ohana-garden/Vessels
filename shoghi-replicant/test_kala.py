#!/usr/bin/env python3
"""
Test suite for Kala value system
Demonstrates tracking contributions and generating reports
"""

import unittest
from datetime import datetime, timedelta
from kala import (
    KalaValueSystem,
    ContributionType,
    value_elder_care_visit,
    value_meal_delivery,
    value_transportation
)

class TestKalaSystem(unittest.TestCase):
    """Test the Kala value tracking system"""

    def setUp(self):
        """Set up a fresh kala system for each test"""
        self.kala = KalaValueSystem()

    def test_create_account(self):
        """Test creating a kala account"""
        account = self.kala.create_account("maria@ohana.org", "Maria Silva")
        self.assertEqual(account.id, "maria@ohana.org")
        self.assertEqual(account.name, "Maria Silva")
        self.assertEqual(account.total_kala_given, 0.0)

    def test_record_time_contribution(self):
        """Test recording a time-based contribution"""
        # Record elder care visit
        contribution = self.kala.record_contribution(
            contributor_id="maria@ohana.org",
            contribution_type=ContributionType.CARE,
            description="Elder care visit - wellness check and medication reminder",
            kala_value=self.kala.value_time_contribution(
                hours=2.0,
                skill_level="skilled"
            ),
            tags=["elder_care", "kupuna", "wellness"]
        )

        # Check contribution was recorded
        self.assertIsNotNone(contribution.id)
        self.assertEqual(contribution.contributor_id, "maria@ohana.org")
        self.assertEqual(contribution.contribution_type, ContributionType.CARE)
        self.assertEqual(contribution.kala_value, 70.0)  # 2 hours * 35/hour
        self.assertEqual(contribution.usd_equivalent, 70.0)

        # Check account was updated
        account = self.kala.get_account("maria@ohana.org")
        self.assertEqual(account.total_kala_given, 70.0)

    def test_record_food_contribution(self):
        """Test recording a food contribution"""
        contribution = self.kala.record_contribution(
            contributor_id="ana@garden.org",
            contribution_type=ContributionType.FOOD,
            description="50 lbs fresh breadfruit from garden",
            kala_value=self.kala.value_resource_contribution(
                resource_description="50 lbs breadfruit",
                market_value_usd=30.0
            ),
            tags=["food", "produce", "local"]
        )

        self.assertEqual(contribution.kala_value, 30.0)
        self.assertEqual(contribution.contribution_type, ContributionType.FOOD)

    def test_value_time_different_skill_levels(self):
        """Test time valuation at different skill levels"""
        general = self.kala.value_time_contribution(1.0, "general")
        skilled = self.kala.value_time_contribution(1.0, "skilled")
        professional = self.kala.value_time_contribution(1.0, "professional")
        expert = self.kala.value_time_contribution(1.0, "expert")

        self.assertEqual(general, 15.0)
        self.assertEqual(skilled, 35.0)
        self.assertEqual(professional, 75.0)
        self.assertEqual(expert, 150.0)

    def test_account_balance(self):
        """Test getting account balance"""
        # Record some contributions
        self.kala.record_contribution(
            contributor_id="maria@ohana.org",
            contribution_type=ContributionType.CARE,
            description="Elder care visit",
            kala_value=70.0
        )

        self.kala.record_contribution(
            contributor_id="maria@ohana.org",
            contribution_type=ContributionType.TRANSPORT,
            description="Transportation to clinic",
            kala_value=20.0
        )

        # Check balance
        balance = self.kala.get_account_balance("maria@ohana.org")
        self.assertEqual(balance["given"], 90.0)
        self.assertEqual(balance["usd_equivalent_given"], 90.0)

    def test_community_total(self):
        """Test getting community-wide totals"""
        # Record contributions from multiple people
        self.kala.record_contribution(
            contributor_id="maria@ohana.org",
            contribution_type=ContributionType.CARE,
            description="Elder care",
            kala_value=70.0
        )

        self.kala.record_contribution(
            contributor_id="john@volunteer.org",
            contribution_type=ContributionType.FOOD,
            description="Meal delivery",
            kala_value=50.0
        )

        # Get community total
        total = self.kala.get_community_total()

        self.assertEqual(total["total_kala"], 120.0)
        self.assertEqual(total["total_usd_equivalent"], 120.0)
        self.assertEqual(total["contribution_count"], 2)
        self.assertEqual(total["by_type"]["care"], 70.0)
        self.assertEqual(total["by_type"]["food"], 50.0)

    def test_contributions_by_type(self):
        """Test filtering contributions by type"""
        # Record different types
        self.kala.record_contribution(
            contributor_id="maria@ohana.org",
            contribution_type=ContributionType.CARE,
            description="Elder care",
            kala_value=70.0
        )

        self.kala.record_contribution(
            contributor_id="maria@ohana.org",
            contribution_type=ContributionType.FOOD,
            description="Meal prep",
            kala_value=30.0
        )

        # Get care contributions only
        care_contributions = self.kala.get_contributions_by_type(ContributionType.CARE)
        self.assertEqual(len(care_contributions), 1)
        self.assertEqual(care_contributions[0].kala_value, 70.0)

    def test_verify_contribution(self):
        """Test verifying contributions"""
        contribution = self.kala.record_contribution(
            contributor_id="maria@ohana.org",
            contribution_type=ContributionType.CARE,
            description="Elder care",
            kala_value=70.0
        )

        # Initially not verified
        self.assertFalse(contribution.verified)

        # Verify it
        self.kala.verify_contribution(contribution.id)

        # Check it's verified
        verified_contribution = self.kala.get_contribution(contribution.id)
        self.assertTrue(verified_contribution.verified)

    def test_generate_report(self):
        """Test generating contribution reports"""
        # Record some contributions
        self.kala.record_contribution(
            contributor_id="maria@ohana.org",
            contribution_type=ContributionType.CARE,
            description="Elder care visit",
            kala_value=70.0,
            tags=["elder_care"]
        )

        self.kala.record_contribution(
            contributor_id="maria@ohana.org",
            contribution_type=ContributionType.TRANSPORT,
            description="Transportation",
            kala_value=20.0,
            tags=["transport"]
        )

        # Generate individual report
        report = self.kala.generate_report(account_id="maria@ohana.org")

        self.assertEqual(report["account"]["id"], "maria@ohana.org")
        self.assertEqual(report["summary"]["given"], 90.0)
        self.assertEqual(len(report["contributions"]), 2)

    def test_helper_functions(self):
        """Test helper functions for common valuations"""
        # Elder care visit (2 hours skilled)
        elder_care = value_elder_care_visit(2.0)
        self.assertEqual(elder_care, 70.0)

        # Meal delivery (5 meals)
        meals = value_meal_delivery(5)
        self.assertEqual(meals, 60.0)

        # Transportation (20 miles)
        transport = value_transportation(20.0)
        self.assertAlmostEqual(transport, 13.4, places=1)

    def test_date_range_filtering(self):
        """Test filtering contributions by date range"""
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        tomorrow = now + timedelta(days=1)

        # Record contribution
        self.kala.record_contribution(
            contributor_id="maria@ohana.org",
            contribution_type=ContributionType.CARE,
            description="Elder care",
            kala_value=70.0
        )

        # Get total for date range including today
        total_with = self.kala.get_community_total(
            start_date=yesterday,
            end_date=tomorrow
        )
        self.assertEqual(total_with["total_kala"], 70.0)

        # Get total for date range before today
        total_without = self.kala.get_community_total(
            start_date=yesterday - timedelta(days=7),
            end_date=yesterday
        )
        self.assertEqual(total_without["total_kala"], 0.0)

    def test_recipient_tracking(self):
        """Test tracking contributions to specific recipients"""
        # Record contribution to specific recipient
        self.kala.record_contribution(
            contributor_id="maria@ohana.org",
            recipient_id="uncle_joe@kupuna.org",
            contribution_type=ContributionType.CARE,
            description="Elder care visit for Uncle Joe",
            kala_value=70.0
        )

        # Check contributor account
        contributor = self.kala.get_account("maria@ohana.org")
        self.assertEqual(contributor.total_kala_given, 70.0)

        # Check recipient account
        recipient = self.kala.get_account("uncle_joe@kupuna.org")
        self.assertEqual(recipient.total_kala_received, 70.0)

        # Check balance reflects both
        balance = self.kala.get_account_balance("uncle_joe@kupuna.org")
        self.assertEqual(balance["received"], 70.0)
        self.assertEqual(balance["net"], 70.0)

    def test_export_data(self):
        """Test exporting kala data"""
        # Record some contributions
        self.kala.record_contribution(
            contributor_id="maria@ohana.org",
            contribution_type=ContributionType.CARE,
            description="Elder care",
            kala_value=70.0
        )

        # Export data
        data = self.kala.export_data()

        self.assertEqual(data["exchange_rate"], 1.0)
        self.assertIn("maria@ohana.org", data["accounts"])
        self.assertEqual(len(data["contributions"]), 1)

class TestKalaIntegrationExamples(unittest.TestCase):
    """Real-world examples of kala usage"""

    def setUp(self):
        self.kala = KalaValueSystem()

    def test_elder_care_scenario(self):
        """Test a complete elder care scenario"""
        # Maria does a comprehensive kupuna visit
        # - 1 hour travel time (general volunteer)
        # - 2 hours elder care (skilled nursing)
        # - 30 miles round trip

        travel_time = self.kala.value_time_contribution(1.0, "general")
        care_time = self.kala.value_time_contribution(2.0, "skilled")
        transport = value_transportation(30.0)

        total_kala = travel_time + care_time + transport

        contribution = self.kala.record_contribution(
            contributor_id="maria@ohana.org",
            recipient_id="uncle_joe@kupuna.org",
            contribution_type=ContributionType.CARE,
            description="Comprehensive kupuna care visit - travel, wellness check, medication reminder, talk story",
            kala_value=total_kala,
            metadata={
                "travel_time_hours": 1.0,
                "care_time_hours": 2.0,
                "miles_driven": 30.0,
                "location": "Puna, Hawaii"
            },
            tags=["elder_care", "kupuna", "puna"]
        )

        # Total should be about 105 kala
        self.assertAlmostEqual(contribution.kala_value, 105.1, places=0)
        self.assertEqual(contribution.usd_equivalent, contribution.kala_value)

    def test_food_hub_scenario(self):
        """Test a food distribution scenario"""
        # Ana harvests and shares breadfruit
        breadfruit = self.kala.record_contribution(
            contributor_id="ana@garden.org",
            contribution_type=ContributionType.FOOD,
            description="50 lbs fresh breadfruit",
            kala_value=self.kala.value_resource_contribution(
                resource_description="50 lbs breadfruit",
                market_value_usd=30.0
            ),
            tags=["food", "produce", "breadfruit"]
        )

        # John coordinates pickup and delivery (3 hours)
        coordination = self.kala.record_contribution(
            contributor_id="john@volunteer.org",
            contribution_type=ContributionType.COORDINATION,
            description="Food hub coordination and delivery",
            kala_value=self.kala.value_time_contribution(3.0, "general"),
            tags=["food", "coordination", "delivery"]
        )

        # Total community value: 75 kala
        total = self.kala.get_community_total()
        self.assertEqual(total["total_kala"], 75.0)

    def test_monthly_community_report(self):
        """Test generating a monthly community report"""
        # Simulate a month of contributions
        contributors = [
            ("maria@ohana.org", "Maria Silva"),
            ("john@volunteer.org", "John Kealoha"),
            ("ana@garden.org", "Ana Patel")
        ]

        # Create accounts
        for contributor_id, name in contributors:
            self.kala.create_account(contributor_id, name)

        # Record various contributions
        contributions = [
            ("maria@ohana.org", ContributionType.CARE, 70.0, "Elder care visit"),
            ("maria@ohana.org", ContributionType.TRANSPORT, 20.0, "Transportation"),
            ("john@volunteer.org", ContributionType.COORDINATION, 45.0, "Event coordination"),
            ("john@volunteer.org", ContributionType.FOOD, 36.0, "Meal preparation"),
            ("ana@garden.org", ContributionType.FOOD, 60.0, "Garden produce"),
            ("ana@garden.org", ContributionType.KNOWLEDGE, 105.0, "Gardening workshop")
        ]

        for contributor_id, cont_type, kala_value, description in contributions:
            self.kala.record_contribution(
                contributor_id=contributor_id,
                contribution_type=cont_type,
                description=description,
                kala_value=kala_value
            )

        # Generate community report
        report = self.kala.generate_report()

        # Check totals
        self.assertEqual(report["community"]["total_kala"], 336.0)
        self.assertEqual(report["community"]["contribution_count"], 6)
        self.assertEqual(report["active_accounts"], 3)

        # Check top contributors
        top = report["top_contributors"]
        self.assertEqual(len(top), 3)
        # Ana should be top with 165 kala
        self.assertEqual(top[0]["name"], "Ana Patel")
        self.assertEqual(top[0]["total_kala_given"], 165.0)

if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
