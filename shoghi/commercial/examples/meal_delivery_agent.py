"""
Example: Meal Delivery Commercial Agent

Demonstrates how to create a commercial agent for a local meal delivery service
using the Shoghi commercial agent framework.
"""

from shoghi.commercial.agent_builder import CommercialAgentBuilder, CommercialAgentConfig
from shoghi.commercial.fee_structure import ProductCategory


def create_aloha_meals_agent(
    creator_id: str,
    community_id: str = "lower_puna_elders"
) -> CommercialAgentConfig:
    """
    Create commercial agent for Aloha Meals Hawaii

    This demonstrates the full agent creation process with all required
    components: product knowledge, honest positioning, consultative questions,
    and disclosure scripts.

    Args:
        creator_id: User ID of creator
        community_id: Community this agent will serve

    Returns:
        CommercialAgentConfig ready for submission to registry
    """
    builder = CommercialAgentBuilder()

    # Step 1: Create base agent
    agent = builder.create_commercial_agent(
        company_name="Aloha Meals Hawaii",
        product_service="Prepared meal delivery service with local ingredients",
        product_category=ProductCategory.LOCAL_SERVICES,
        creator_id=creator_id,
        community_id=community_id,
        product_description="Locally sourced, Hawaiian/Asian fusion prepared meals delivered twice weekly",
        company_description="Local Puna-based meal delivery service supporting local farmers"
    )

    # Step 2: Add product knowledge
    builder.add_product_knowledge(
        pricing="$12-18 per meal, 5-meal minimum + $3.50 delivery fee",
        features=[
            "Locally sourced ingredients from Puna farms",
            "Hawaiian/Asian fusion menu",
            "Dietary accommodations (vegetarian, diabetic-friendly, low-sodium)",
            "Delivery Tuesday/Thursday",
            "Order by Sunday 5pm for that week",
            "Reusable containers (reduce waste)",
            "Weekly rotating menu"
        ],
        limitations=[
            "Only 2 delivery days per week (Tue/Thu)",
            "5-meal minimum order required",
            "Limited to Puna district",
            "Must order 48 hours in advance",
            "Menu is preset (not fully customizable)",
            "More expensive than cooking yourself",
            "$3.50 delivery fee per order"
        ],
        use_cases=[
            "Kupuna who have difficulty cooking",
            "Busy families wanting healthy local food",
            "Recovery from surgery/illness",
            "Weekly meal prep alternative",
            "Supporting local agriculture"
        ],
        support_process="Call (808) 555-1234 or email support@alohameals.hi for questions, menu changes, or issues",
        return_policy="Full refund for damaged/incorrect meals. Contact us within 24 hours of delivery."
    )

    # Step 3: Add honest positioning
    builder.add_honest_positioning(
        our_strengths=[
            "100% locally sourced ingredients",
            "Support Puna farmers and food economy",
            "Hawaiian/Asian fusion - authentic local flavors",
            "Accommodate dietary restrictions",
            "Reusable containers (environmentally conscious)",
            "Consistent quality and reliability"
        ],
        our_limitations=[
            "Only 2 delivery days/week (not daily)",
            "5-meal minimum order",
            "More expensive than home cooking ($12-18/meal vs $5-8)",
            "Preset menu (limited customization)",
            "Delivery fee adds to cost",
            "Limited to Puna district only"
        ],
        competitors=[
            {
                "name": "Community meal sharing (Ohana networks)",
                "cost": "$0-5 donation",
                "tradeoff": "Free/very low cost, but inconsistent availability and menu variety. Depends on volunteer cooks."
            },
            {
                "name": "Meals on Wheels Hawaii",
                "cost": "Free or subsidized for qualifying seniors (60+)",
                "tradeoff": "Free if you qualify! Limited menu options and strict eligibility. Check if you're eligible - this may be better for you."
            },
            {
                "name": "Restaurant delivery (DoorDash/Uber Eats)",
                "cost": "$15-30 per meal + fees",
                "tradeoff": "Much more variety, on-demand ordering. Higher cost, not always local ingredients, inconsistent quality."
            },
            {
                "name": "Home cooking",
                "cost": "$5-8 per meal (grocery costs)",
                "tradeoff": "Cheapest option. Requires time, energy, and cooking ability. You control everything."
            },
            {
                "name": "Hilo Health meal prep services",
                "cost": "$10-15 per meal",
                "tradeoff": "Similar service in Hilo. Wider service area but longer delivery times to Puna."
            }
        ],
        ideal_customer=[
            "You want prepared meals 2x/week (Tue/Thu works for you)",
            "You value locally sourced and Hawaiian/Asian cuisine",
            "You're willing to pay $12-18/meal for quality and convenience",
            "You can commit to 5-meal minimum orders",
            "You live in Puna district",
            "You want to support local farmers and food economy"
        ],
        poor_fit=[
            "You need daily delivery (we only do Tue/Thu)",
            "You're on a tight budget (community meal sharing or Meals on Wheels might be better)",
            "You qualify for Meals on Wheels (that's free! Check eligibility first)",
            "You want fully customizable meals every time",
            "You live outside Puna district",
            "You prefer cooking your own meals"
        ]
    )

    # Step 4: Add consultative questions
    builder.add_consultative_questions([
        "How often do you need prepared meals each week?",
        "Do you have any dietary restrictions I should know about? (vegetarian, diabetic-friendly, low-sodium, allergies)",
        "Would Tuesday and Thursday delivery work with your schedule?",
        "What's your budget per meal? (Our meals are $12-18)",
        "Have you checked if you qualify for Meals on Wheels? (If you're 60+ and meet criteria, that's free and might be better)",
        "Are you comfortable with a 5-meal minimum order?",
        "Do you live in the Puna district?",
        "What's most important to you: supporting local farms, dietary accommodations, convenience, or cost?",
        "Have you tried meal delivery services before? What was your experience?"
    ])

    # Step 5: Generate disclosure script
    builder.generate_disclosure_script(
        employment_status="I work with Aloha Meals Hawaii to help connect kupuna and families with meal services"
    )

    # Step 6: Validate and build
    agent_config = builder.validate_and_build()

    return agent_config


def create_agent_and_submit_example():
    """
    Complete example showing agent creation and submission to registry

    This would be the full workflow from creation to community approval.
    """
    from shoghi.commercial.registry import CommercialAgentRegistry

    # Create agent
    agent_config = create_aloha_meals_agent(
        creator_id="user_makoa_12345",
        community_id="lower_puna_elders"
    )

    print("=" * 80)
    print("ALOHA MEALS COMMERCIAL AGENT CREATED")
    print("=" * 80)
    print(f"\nAgent ID: {agent_config.agent_id}")
    print(f"Agent Name: {agent_config.name}")
    print(f"Company: {agent_config.company_name}")
    print(f"Community: {agent_config.community_id}")
    print(f"\nProduct Category: {agent_config.product_category.value}")
    print(f"Fee Model: {agent_config.fee_config.fee_type.value}")
    print(f"Fee Amount: ${agent_config.fee_config.flat_amount}")
    print(f"Fee Paid To: {agent_config.fee_paid_to}")

    print("\n" + "=" * 80)
    print("DISCLOSURE SCRIPT")
    print("=" * 80)
    print(agent_config.disclosure_script)

    print("\n" + "=" * 80)
    print("HONEST POSITIONING - COMPETITORS")
    print("=" * 80)
    for competitor in agent_config.honest_positioning["competitors"]:
        print(f"\n{competitor['name']}")
        print(f"  Cost: {competitor['cost']}")
        print(f"  Tradeoff: {competitor['tradeoff']}")

    print("\n" + "=" * 80)
    print("IDEAL CUSTOMER")
    print("=" * 80)
    for item in agent_config.honest_positioning["ideal_customer"]:
        print(f"✓ {item}")

    print("\n" + "=" * 80)
    print("NOT A GOOD FIT IF")
    print("=" * 80)
    for item in agent_config.honest_positioning["poor_fit"]:
        print(f"✗ {item}")

    # Submit to registry
    print("\n" + "=" * 80)
    print("SUBMITTING TO COMMUNITY REGISTRY")
    print("=" * 80)

    registry = CommercialAgentRegistry()
    submission_id = registry.submit_for_approval(
        agent_config=agent_config,
        submitted_by="user_makoa_12345"
    )

    print(f"✓ Submitted for community approval: {submission_id}")
    print(f"✓ Public comment period: 7 days")
    print(f"✓ Required reviews: {len(registry.submissions[submission_id].review_checks)} checks")
    print("\nAgent will be activated after community approval.")

    return agent_config, submission_id


if __name__ == "__main__":
    # Run example
    agent_config, submission_id = create_agent_and_submit_example()
