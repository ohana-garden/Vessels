"""
Tests for Commercial Agent System

Tests fee structure, agent builder, registry, fee processor,
and transparency reporting.
"""

import pytest
from datetime import datetime, timedelta

from shoghi.commercial import (
    ProductCategory,
    FeeModel,
    FeeConfig,
    calculate_fee,
    distribute_fee,
    CommercialAgentBuilder,
    CommercialAgentRegistry,
    CommercialFeeProcessor,
    CommercialTransparencyReport,
    AgentStatus,
    ReviewCheckStatus,
    TransactionStatus,
)


class TestFeeStructure:
    """Test fee calculation and distribution"""

    def test_flat_fee_calculation(self):
        """Test flat fee calculation"""
        config = FeeConfig(
            fee_type=FeeModel.FLAT_FEE,
            flat_amount=15.00
        )
        fee = config.calculate_fee(100.0)
        assert fee == 15.00

    def test_percentage_capped_fee_calculation(self):
        """Test percentage-capped fee calculation"""
        config = FeeConfig(
            fee_type=FeeModel.PERCENTAGE_CAPPED,
            rate=0.20,
            cap=25.00,
            minimum=2.00
        )

        # Test below cap
        fee = config.calculate_fee(50.0)  # 20% = $10
        assert fee == 10.00

        # Test at cap
        fee = config.calculate_fee(200.0)  # 20% = $40, but capped at $25
        assert fee == 25.00

        # Test minimum
        fee = config.calculate_fee(5.0)  # 20% = $1, but minimum is $2
        assert fee == 2.00

    def test_predefined_digital_saas_fee(self):
        """Test predefined digital SaaS fee calculation"""
        # $10/mo app
        fee = calculate_fee(ProductCategory.DIGITAL_PRODUCTS_SAAS, 10.0)
        assert fee == 2.00  # minimum

        # $50/mo service
        fee = calculate_fee(ProductCategory.DIGITAL_PRODUCTS_SAAS, 50.0)
        assert fee == 10.00  # 20%

        # $200/mo software
        fee = calculate_fee(ProductCategory.DIGITAL_PRODUCTS_SAAS, 200.0)
        assert fee == 25.00  # capped

    def test_fee_distribution(self):
        """Test fee distribution to fund categories"""
        distribution = distribute_fee(100.0)

        assert distribution["infrastructure"] == 60.0  # 60%
        assert distribution["servant_development"] == 20.0  # 20%
        assert distribution["community_discretionary"] == 15.0  # 15%
        assert distribution["transparency_audit"] == 5.0  # 5%

        # Verify total
        assert sum(distribution.values()) == 100.0


class TestCommercialAgentBuilder:
    """Test commercial agent builder"""

    def test_create_basic_agent(self):
        """Test creating basic commercial agent"""
        builder = CommercialAgentBuilder()

        agent = builder.create_commercial_agent(
            company_name="Test Company",
            product_service="Test service",
            product_category=ProductCategory.LOCAL_SERVICES,
            creator_id="user_123",
            community_id="test_community"
        )

        assert agent.company_name == "Test Company"
        assert agent.community_id == "test_community"
        assert agent.product_category == ProductCategory.LOCAL_SERVICES
        assert agent.fee_config is not None
        assert agent.disclosure_required is True
        assert len(agent.required_skills) > 0

    def test_builder_chain(self):
        """Test builder method chaining"""
        builder = CommercialAgentBuilder()

        builder.create_commercial_agent(
            company_name="Test Meals",
            product_service="Meal delivery",
            product_category=ProductCategory.LOCAL_SERVICES,
            creator_id="user_123",
            community_id="test_community"
        )

        # Add product knowledge
        builder.add_product_knowledge(
            pricing="$15/meal",
            features=["Fresh", "Local"],
            limitations=["Limited delivery days"],
            use_cases=["Busy families"],
            support_process="Call us",
            return_policy="Full refund"
        )

        # Add honest positioning
        builder.add_honest_positioning(
            our_strengths=["Quality", "Local"],
            our_limitations=["Expensive"],
            competitors=[{"name": "Home cooking", "cost": "Cheaper", "tradeoff": "More work"}],
            ideal_customer=["Busy professionals"],
            poor_fit=["Budget conscious"]
        )

        # Add questions
        builder.add_consultative_questions([
            "What's your budget?",
            "How often do you need meals?"
        ])

        # Generate disclosure
        builder.generate_disclosure_script()

        # Validate
        agent = builder.validate_and_build()

        assert agent.product_knowledge is not None
        assert agent.honest_positioning is not None
        assert len(agent.consultative_questions) == 2
        assert len(agent.disclosure_script) > 0

    def test_builder_validation_fails_without_required_info(self):
        """Test builder validation fails without required information"""
        builder = CommercialAgentBuilder()

        builder.create_commercial_agent(
            company_name="Test",
            product_service="Service",
            product_category=ProductCategory.LOCAL_SERVICES,
            creator_id="user_123",
            community_id="test_community"
        )

        # Try to validate without adding required info
        with pytest.raises(ValueError, match="Must call add_product_knowledge"):
            builder.validate_and_build()


class TestCommercialAgentRegistry:
    """Test commercial agent registry"""

    def test_submit_agent_for_approval(self):
        """Test submitting agent for approval"""
        registry = CommercialAgentRegistry()
        builder = CommercialAgentBuilder()

        # Create complete agent
        builder.create_commercial_agent(
            company_name="Test",
            product_service="Service",
            product_category=ProductCategory.LOCAL_SERVICES,
            creator_id="user_123",
            community_id="test_community"
        )
        builder.add_product_knowledge(
            pricing="$15", features=["A"], limitations=["B"],
            use_cases=["C"], support_process="D", return_policy="E"
        )
        builder.add_honest_positioning(
            our_strengths=["A"], our_limitations=["B"],
            competitors=[{"name": "C", "cost": "D", "tradeoff": "E"}],
            ideal_customer=["F"], poor_fit=["G"]
        )
        builder.add_consultative_questions(["Q1"])
        builder.generate_disclosure_script()
        agent = builder.validate_and_build()

        # Submit
        submission_id = registry.submit_for_approval(
            agent_config=agent,
            submitted_by="user_123"
        )

        assert submission_id is not None
        submission = registry.get_submission(submission_id)
        assert submission.status == AgentStatus.PENDING_REVIEW
        assert len(submission.review_checks) > 0

    def test_update_review_checks(self):
        """Test updating review checks"""
        registry = CommercialAgentRegistry()
        builder = CommercialAgentBuilder()

        # Create and submit agent
        builder.create_commercial_agent(
            company_name="Test", product_service="Service",
            product_category=ProductCategory.LOCAL_SERVICES,
            creator_id="user_123", community_id="test_community"
        )
        builder.add_product_knowledge(
            pricing="$15", features=["A"], limitations=["B"],
            use_cases=["C"], support_process="D", return_policy="E"
        )
        builder.add_honest_positioning(
            our_strengths=["A"], our_limitations=["B"],
            competitors=[{"name": "C", "cost": "D", "tradeoff": "E"}],
            ideal_customer=["F"], poor_fit=["G"]
        )
        builder.add_consultative_questions(["Q1"])
        builder.generate_disclosure_script()
        agent = builder.validate_and_build()

        submission_id = registry.submit_for_approval(agent, "user_123")

        # Update check
        success = registry.update_review_check(
            submission_id=submission_id,
            check_name="disclosure_clarity",
            status=ReviewCheckStatus.PASS,
            notes="Disclosure is clear",
            reviewed_by="reviewer_456"
        )

        assert success is True
        submission = registry.get_submission(submission_id)
        check = next(c for c in submission.review_checks if c.name == "disclosure_clarity")
        assert check.status == ReviewCheckStatus.PASS

    def test_approval_requires_all_checks_pass(self):
        """Test that approval requires all must-pass checks"""
        registry = CommercialAgentRegistry()
        builder = CommercialAgentBuilder()

        # Create and submit agent
        builder.create_commercial_agent(
            company_name="Test", product_service="Service",
            product_category=ProductCategory.LOCAL_SERVICES,
            creator_id="user_123", community_id="test_community"
        )
        builder.add_product_knowledge(
            pricing="$15", features=["A"], limitations=["B"],
            use_cases=["C"], support_process="D", return_policy="E"
        )
        builder.add_honest_positioning(
            our_strengths=["A"], our_limitations=["B"],
            competitors=[{"name": "C", "cost": "D", "tradeoff": "E"}],
            ideal_customer=["F"], poor_fit=["G"]
        )
        builder.add_consultative_questions(["Q1"])
        builder.generate_disclosure_script()
        agent = builder.validate_and_build()

        submission_id = registry.submit_for_approval(agent, "user_123")

        # Try to evaluate before checks are complete
        can_approve, reason = registry.evaluate_approval(submission_id)
        assert can_approve is False
        assert "Failed required checks" in reason


class TestCommercialFeeProcessor:
    """Test fee processor"""

    def test_process_referral_fee(self):
        """Test processing referral fee"""
        processor = CommercialFeeProcessor()

        fee_config = FeeConfig(
            fee_type=FeeModel.FLAT_FEE,
            flat_amount=15.00
        )

        transaction_id = processor.process_referral_fee(
            company_id="company_123",
            agent_id="agent_456",
            customer_id="customer_789",
            community_id="test_community",
            transaction_amount=100.0,
            fee_config=fee_config
        )

        assert transaction_id is not None
        transaction = processor.get_transaction(transaction_id)
        assert transaction.referral_fee == 15.00
        assert transaction.community_id == "test_community"

    def test_get_community_balance(self):
        """Test getting community balance"""
        processor = CommercialFeeProcessor()

        # Process transaction (it will auto-distribute)
        fee_config = FeeConfig(fee_type=FeeModel.FLAT_FEE, flat_amount=100.00)

        processor.process_referral_fee(
            company_id="company_123", agent_id="agent_456",
            customer_id="customer_789", community_id="test_community",
            transaction_amount=100.0, fee_config=fee_config
        )

        # Get balance
        balance = processor.get_community_balance("test_community")

        assert "infrastructure" in balance
        assert "servant_development" in balance
        # Note: Values will be zero until we mock payment gateway


class TestCommercialTransparencyReport:
    """Test transparency reporting"""

    def test_generate_monthly_report(self):
        """Test generating monthly report"""
        processor = CommercialFeeProcessor()
        registry = CommercialAgentRegistry()
        transparency = CommercialTransparencyReport(
            fee_processor=processor,
            agent_registry=registry
        )

        report = transparency.generate_monthly_report(
            community_id="test_community",
            year=2024,
            month=11
        )

        assert report.community_id == "test_community"
        assert report.period_start.year == 2024
        assert report.period_start.month == 11
        assert report.revenue is not None
        assert report.community_decisions is not None

    def test_report_to_dict(self):
        """Test report conversion to dictionary"""
        processor = CommercialFeeProcessor()
        registry = CommercialAgentRegistry()
        transparency = CommercialTransparencyReport(
            fee_processor=processor,
            agent_registry=registry
        )

        report = transparency.generate_monthly_report(
            community_id="test_community",
            year=2024,
            month=11
        )

        report_dict = report.to_dict()

        assert "community" in report_dict
        assert "period" in report_dict
        assert "revenue" in report_dict
        assert "community_decisions" in report_dict
        assert report_dict["community"] == "test_community"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
