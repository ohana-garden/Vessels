#!/usr/bin/env python3
"""
Test suite for menu_builder.py
Tests the restaurant menu builder and agent generation system
"""

import pytest
import asyncio
from datetime import datetime
from menu_builder import (
    MenuSection,
    MenuItem,
    MenuState,
    MenuAgentGenerator,
    MenuConversationOrchestrator,
    menu_orchestrator
)


class TestMenuSection:
    """Tests for MenuSection enum"""

    def test_menu_section_values(self):
        """Test that all menu sections have correct values"""
        assert MenuSection.APPETIZERS.value == "appetizers"
        assert MenuSection.MAINS.value == "mains"
        assert MenuSection.DESSERTS.value == "desserts"
        assert MenuSection.BEVERAGES.value == "beverages"
        assert MenuSection.SPECIALS.value == "specials"
        assert MenuSection.KIDS.value == "kids"


class TestMenuItem:
    """Tests for MenuItem dataclass"""

    def test_menu_item_creation(self):
        """Test creating a menu item"""
        item = MenuItem(
            name="Burger",
            price=12.99,
            description="Classic burger with fries",
            section=MenuSection.MAINS,
            dietary_tags=["gluten"],
            popularity=0.8
        )

        assert item.name == "Burger"
        assert item.price == 12.99
        assert item.section == MenuSection.MAINS
        assert item.popularity == 0.8

    def test_menu_item_defaults(self):
        """Test menu item with default values"""
        item = MenuItem(name="Salad", price=9.99)

        assert item.description == ""
        assert item.section == MenuSection.MAINS
        assert item.dietary_tags == []
        assert item.popularity == 0.5


class TestMenuState:
    """Tests for MenuState dataclass"""

    def test_menu_state_creation(self):
        """Test creating a menu state"""
        items = [
            MenuItem("Item1", 10.0),
            MenuItem("Item2", 15.0)
        ]

        state = MenuState(
            restaurant_name="Test Restaurant",
            cuisine_type="italian",
            items=items,
            price_range="upscale"
        )

        assert state.restaurant_name == "Test Restaurant"
        assert state.cuisine_type == "italian"
        assert len(state.items) == 2
        assert state.version == 1

    def test_menu_state_defaults(self):
        """Test menu state with default values"""
        state = MenuState(
            restaurant_name="Test",
            cuisine_type="american",
            items=[]
        )

        assert state.design_style == "classic"
        assert state.target_audience == "general"
        assert state.price_range == "moderate"
        assert state.problems_identified == []
        assert state.improvements_made == []


class TestMenuAgentGenerator:
    """Tests for MenuAgentGenerator class"""

    def setup_method(self):
        """Create fresh MenuAgentGenerator for each test"""
        self.generator = MenuAgentGenerator()

    def test_initialization(self):
        """Test generator initialization"""
        assert self.generator.generated_agents == {}
        assert self.generator.chef_agent_id is not None

    def test_analyze_menu_context_cluttered(self):
        """Test menu context analysis for cluttered menu"""
        items = [MenuItem(f"Item{i}", 10.0, f"Long description " * 20)
                for i in range(35)]

        state = MenuState(
            restaurant_name="Test",
            cuisine_type="italian",
            items=items
        )

        context = self.generator.analyze_menu_context(state)

        assert "cluttered_layout" in context["main_issues"]

    def test_analyze_menu_context_pricing_issues(self):
        """Test menu context analysis for pricing issues"""
        items = [
            MenuItem("Cheap", 1.0),
            MenuItem("Expensive", 100.0)
        ]

        state = MenuState(
            restaurant_name="Test",
            cuisine_type="american",
            items=items
        )

        context = self.generator.analyze_menu_context(state)

        assert "pricing_confusion" in context["main_issues"]

    def test_analyze_menu_context_missing_descriptions(self):
        """Test menu context analysis for missing descriptions"""
        items = [MenuItem(f"Item{i}", 10.0, "") for i in range(10)]

        state = MenuState(
            restaurant_name="Test",
            cuisine_type="thai",
            items=items
        )

        context = self.generator.analyze_menu_context(state)

        assert "missing_descriptions" in context["main_issues"]

    def test_analyze_menu_context_poor_categorization(self):
        """Test menu context analysis for poor organization"""
        items = [MenuItem("Item1", 10.0)]  # Only one section

        state = MenuState(
            restaurant_name="Test",
            cuisine_type="french",
            items=items
        )

        context = self.generator.analyze_menu_context(state)

        assert "poor_organization" in context["main_issues"]

    def test_analyze_menu_context_authenticity_opportunity(self):
        """Test detection of authenticity opportunity"""
        items = [MenuItem("Pasta", 15.0)]

        state = MenuState(
            restaurant_name="Test",
            cuisine_type="italian",
            items=items
        )

        context = self.generator.analyze_menu_context(state)

        assert "authenticity_emphasis" in context["opportunities"]

    def test_analyze_menu_context_family_friendly(self):
        """Test detection of family-friendly opportunity"""
        items = [MenuItem("Burger", 10.0)]

        state = MenuState(
            restaurant_name="Test",
            cuisine_type="american",
            items=items,
            target_audience="family"
        )

        context = self.generator.analyze_menu_context(state)

        assert "family_friendly_formatting" in context["opportunities"]

    def test_generate_design_specialist_upscale(self):
        """Test generation of upscale design specialist"""
        items = [MenuItem(f"Item{i}", 50.0, "x" * 101) for i in range(35)]

        state = MenuState(
            restaurant_name="Fine Dining",
            cuisine_type="french",
            items=items,
            price_range="upscale"
        )

        agent = self.generator.generate_specialist_agent("design_specialist", state)

        assert agent["type"] == "design_specialist"
        assert "Minimalist" in agent["personality"]
        assert "white space" in agent["expertise"].lower()
        assert len(agent["focus_areas"]) > 0

    def test_generate_design_specialist_family(self):
        """Test generation of family restaurant design specialist"""
        state = MenuState(
            restaurant_name="Family Place",
            cuisine_type="american",
            items=[MenuItem("Burger", 10.0)],
            target_audience="family restaurant"
        )

        agent = self.generator.generate_specialist_agent("design_specialist", state)

        assert "family" in agent["personality"].lower()
        assert any("kid" in area.lower() for area in agent["focus_areas"])

    def test_generate_customer_perspective_unfamiliar_cuisine(self):
        """Test generation of customer agent for unfamiliar cuisine"""
        state = MenuState(
            restaurant_name="Thai Place",
            cuisine_type="thai",
            items=[MenuItem("Pad Thai", 12.0)]
        )

        agent = self.generator.generate_specialist_agent("customer_perspective", state)

        assert agent["type"] == "customer_perspective"
        assert "Curious" in agent["personality"]

    def test_generate_customer_perspective_tourist(self):
        """Test generation of tourist customer agent"""
        state = MenuState(
            restaurant_name="Local Spot",
            cuisine_type="hawaiian",
            items=[MenuItem("Poke", 15.0)],
            target_audience="tourist"
        )

        agent = self.generator.generate_specialist_agent("customer_perspective", state)

        assert "tourist" in agent["personality"].lower() or "Tourist" in agent["personality"]

    def test_generate_pricing_strategist(self):
        """Test generation of pricing strategist"""
        state = MenuState(
            restaurant_name="Restaurant",
            cuisine_type="italian",
            items=[MenuItem("Pasta", 15.0)]
        )

        agent = self.generator.generate_specialist_agent("pricing_strategist", state)

        assert agent["type"] == "pricing_strategist"
        assert "Revenue" in agent["personality"] or "revenue" in agent["personality"]
        assert len(agent["focus_areas"]) > 0

    def test_generate_cultural_agent(self):
        """Test generation of cultural authenticity agent"""
        state = MenuState(
            restaurant_name="Restaurant",
            cuisine_type="japanese",
            items=[MenuItem("Sushi", 20.0)]
        )

        agent = self.generator.generate_specialist_agent("cultural_authenticity", state)

        assert agent["type"] == "cultural_authenticity"
        assert "japanese" in agent["personality"].lower()
        assert "authentic" in agent["expertise"].lower()

    def test_generate_accessibility_agent(self):
        """Test generation of accessibility expert"""
        state = MenuState(
            restaurant_name="Restaurant",
            cuisine_type="american",
            items=[MenuItem("Burger", 10.0)]
        )

        agent = self.generator.generate_specialist_agent("accessibility_expert", state)

        assert agent["type"] == "accessibility_expert"
        assert "accessibility" in agent["expertise"].lower()
        assert len(agent["focus_areas"]) > 0

    def test_generate_generic_specialist(self):
        """Test generation of generic specialist"""
        state = MenuState(
            restaurant_name="Restaurant",
            cuisine_type="mexican",
            items=[MenuItem("Taco", 8.0)]
        )

        agent = self.generator.generate_specialist_agent("custom_need", state)

        assert agent["type"] == "custom_need"
        assert "custom_need" in agent["personality"]


class TestMenuConversationOrchestrator:
    """Tests for MenuConversationOrchestrator class"""

    def setup_method(self):
        """Create fresh orchestrator for each test"""
        self.orchestrator = MenuConversationOrchestrator()

    def test_initialization(self):
        """Test orchestrator initialization"""
        assert self.orchestrator.conversation_history == []
        assert self.orchestrator.current_menu_state is None
        assert self.orchestrator.active_agents == {}

    def test_initialize_conversation(self):
        """Test conversation initialization"""
        menu_data = {
            "restaurant_name": "Test Restaurant",
            "cuisine_type": "italian",
            "items": [
                {"name": "Pasta", "price": 15.0, "section": "mains"}
            ]
        }

        state = asyncio.run(self.orchestrator.initialize_conversation(menu_data))

        assert state is not None
        assert state.restaurant_name == "Test Restaurant"
        assert "chef" in self.orchestrator.active_agents
        assert len(self.orchestrator.conversation_history) > 0

    def test_parse_menu(self):
        """Test menu parsing"""
        menu_data = {
            "restaurant_name": "Bistro",
            "cuisine_type": "french",
            "items": [
                {"name": "Steak", "price": 25.0, "description": "Grilled", "section": "mains"}
            ],
            "price_range": "upscale"
        }

        state = self.orchestrator._parse_menu(menu_data)

        assert state.restaurant_name == "Bistro"
        assert state.cuisine_type == "french"
        assert len(state.items) == 1
        assert state.items[0].name == "Steak"
        assert state.price_range == "upscale"

    def test_parse_menu_defaults(self):
        """Test menu parsing with defaults"""
        menu_data = {
            "restaurant_name": "Test",
            "cuisine_type": "american",
            "items": []
        }

        state = self.orchestrator._parse_menu(menu_data)

        assert state.design_style == "classic"
        assert state.target_audience == "general"
        assert state.price_range == "moderate"

    def test_parse_user_intent_stop(self):
        """Test parsing stop intent"""
        intent = self.orchestrator._parse_user_intent("stop")
        assert intent["action"] == "stop"

        intent = self.orchestrator._parse_user_intent("that's enough")
        assert intent["action"] == "stop"

    def test_parse_user_intent_approve(self):
        """Test parsing approve intent"""
        intent = self.orchestrator._parse_user_intent("yes, that's good")
        assert intent["action"] == "approve"

        intent = self.orchestrator._parse_user_intent("I like that")
        assert intent["action"] == "approve"

    def test_parse_user_intent_question(self):
        """Test parsing question intent"""
        intent = self.orchestrator._parse_user_intent("Why did you choose that?")
        assert intent["action"] == "question"

    def test_parse_user_intent_redirect_pricing(self):
        """Test parsing redirect to pricing"""
        intent = self.orchestrator._parse_user_intent("Let's focus on price")
        assert intent["action"] == "redirect"
        assert intent["specialist_needed"] == "pricing_strategist"

    def test_parse_user_intent_redirect_design(self):
        """Test parsing redirect to design"""
        intent = self.orchestrator._parse_user_intent("The design needs work")
        assert intent["action"] == "redirect"
        assert intent["specialist_needed"] == "design_specialist"

    def test_summon_specialist(self):
        """Test summoning a specialist"""
        menu_data = {
            "restaurant_name": "Test",
            "cuisine_type": "italian",
            "items": [{"name": "Pasta", "price": 15.0, "section": "mains"}]
        }

        asyncio.run(self.orchestrator.initialize_conversation(menu_data))

        specialist_id = asyncio.run(self.orchestrator.summon_specialist("pricing_strategist"))

        assert specialist_id in self.orchestrator.active_agents
        assert self.orchestrator.active_agents[specialist_id]["type"] == "pricing_strategist"

    def test_apply_change(self):
        """Test applying a change to menu"""
        menu_data = {
            "restaurant_name": "Test",
            "cuisine_type": "italian",
            "items": [{"name": "Pasta", "price": 15.0, "section": "mains"}]
        }

        asyncio.run(self.orchestrator.initialize_conversation(menu_data))

        initial_version = self.orchestrator.current_menu_state.version
        updated_state = asyncio.run(self.orchestrator.apply_change("pricing_update"))

        assert updated_state.version == initial_version + 1
        assert "pricing_update" in updated_state.improvements_made

    def test_answer_user_question(self):
        """Test answering user questions"""
        menu_data = {
            "restaurant_name": "Test",
            "cuisine_type": "italian",
            "items": [{"name": "Pasta", "price": 15.0, "section": "mains"}]
        }

        asyncio.run(self.orchestrator.initialize_conversation(menu_data))

        answer = asyncio.run(self.orchestrator.answer_user_question("Why this approach?"))

        assert isinstance(answer, str)
        assert len(answer) > 0

    def test_get_conversation_display(self):
        """Test getting conversation display"""
        self.orchestrator.conversation_history = [
            {
                "speaker": "chef",
                "message": "Test message",
                "timestamp": datetime.now().isoformat()
            }
        ]

        self.orchestrator.active_agents["chef"] = {
            "type": "chef",
            "personality": "Executive chef"
        }

        display = self.orchestrator.get_conversation_display()

        assert len(display) == 1
        assert display[0]["speaker_name"] == "Chef"
        assert display[0]["message"] == "Test message"


class TestGlobalInstance:
    """Test the global menu_orchestrator instance"""

    def test_global_instance_exists(self):
        """Test that global instance is available"""
        assert menu_orchestrator is not None
        assert isinstance(menu_orchestrator, MenuConversationOrchestrator)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
