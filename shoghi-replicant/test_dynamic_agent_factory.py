#!/usr/bin/env python3
"""
Test suite for dynamic_agent_factory.py
Tests the dynamic agent creation from natural language requests
"""

import pytest
from unittest.mock import patch, Mock
from dynamic_agent_factory import (
    DynamicAgentFactory,
    agent_factory,
    process_community_request
)
from agent_zero_core import AgentSpecification


class TestDynamicAgentFactory:
    """Tests for DynamicAgentFactory class"""

    def setup_method(self):
        """Create fresh factory for each test"""
        self.factory = DynamicAgentFactory()

    def test_initialization(self):
        """Test factory initialization"""
        assert self.factory.intent_patterns is not None
        assert self.factory.capability_matrix is not None
        assert self.factory.tool_requirements is not None
        assert isinstance(self.factory.bmad_agents, list)

    def test_intent_patterns_loaded(self):
        """Test that intent patterns are properly loaded"""
        assert "grant_discovery" in self.factory.intent_patterns
        assert "grant_writing" in self.factory.intent_patterns
        assert "volunteer_coordination" in self.factory.intent_patterns
        assert "elder_care" in self.factory.intent_patterns

    def test_capability_matrix_loaded(self):
        """Test that capability matrix is properly loaded"""
        assert "grant_discovery" in self.factory.capability_matrix
        assert "web_search" in self.factory.capability_matrix["grant_discovery"]
        assert "opportunity_matching" in self.factory.capability_matrix["grant_discovery"]

    def test_tool_requirements_loaded(self):
        """Test that tool requirements are properly loaded"""
        assert "web_search" in self.factory.tool_requirements
        assert "data_analysis" in self.factory.tool_requirements
        assert isinstance(self.factory.tool_requirements["web_search"], list)

    def test_detect_grant_discovery_intent(self):
        """Test detection of grant discovery intent"""
        request = "I need to find grants for elder care"
        intents = self.factory._detect_intents(request)

        assert "grant_discovery" in intents

    def test_detect_grant_writing_intent(self):
        """Test detection of grant writing intent"""
        request = "Help me write a grant application"
        intents = self.factory._detect_intents(request)

        assert "grant_writing" in intents

    def test_detect_volunteer_coordination_intent(self):
        """Test detection of volunteer coordination intent"""
        request = "I need to coordinate volunteers for our program"
        intents = self.factory._detect_intents(request)

        assert "volunteer_coordination" in intents

    def test_detect_elder_care_intent(self):
        """Test detection of elder care intent"""
        request = "We need elder care services"
        intents = self.factory._detect_intents(request)

        assert "elder_care" in intents

    def test_detect_multiple_intents(self):
        """Test detection of multiple intents"""
        request = "Find grants for elder care and coordinate volunteers"
        intents = self.factory._detect_intents(request)

        assert "grant_discovery" in intents
        assert "elder_care" in intents
        assert "volunteer_coordination" in intents

    def test_detect_intents_case_insensitive(self):
        """Test that intent detection is case-insensitive"""
        request1 = "FIND GRANTS"
        request2 = "find grants"

        intents1 = self.factory._detect_intents(request1)
        intents2 = self.factory._detect_intents(request2)

        assert intents1 == intents2

    def test_detect_intents_no_duplicates(self):
        """Test that duplicate intents are removed"""
        request = "find grant funding grant search grant discover grant"
        intents = self.factory._detect_intents(request)

        assert intents.count("grant_discovery") == 1

    def test_extract_context_location(self):
        """Test extraction of location context"""
        request = "Find grants for Puna"
        context = self.factory._extract_context(request)

        assert context["location"] == "puna"

    def test_extract_context_population(self):
        """Test extraction of population context"""
        request = "Help elder population"
        context = self.factory._extract_context(request)

        assert context["population"] == "elder"

    def test_extract_context_urgency_high(self):
        """Test extraction of high urgency"""
        request = "Urgent grant assistance needed"
        context = self.factory._extract_context(request)

        assert context["urgency"] == "high"

    def test_extract_context_urgency_low(self):
        """Test extraction of low urgency"""
        request = "Eventually we will need funding"
        context = self.factory._extract_context(request)

        assert context["urgency"] == "low"

    def test_extract_context_specific_needs(self):
        """Test extraction of specific needs"""
        request = "Need transportation and housing assistance"
        context = self.factory._extract_context(request)

        assert "transportation" in context["specific_needs"]
        assert "housing" in context["specific_needs"]

    def test_extract_context_defaults(self):
        """Test default context values"""
        request = "Generic request"
        context = self.factory._extract_context(request)

        assert context["urgency"] == "medium"
        assert context["scope"] == "local"
        assert context["location"] is None

    def test_determine_capabilities_from_intents(self):
        """Test capability determination from intents"""
        intents = ["grant_discovery"]
        context = {"location": None}

        capabilities = self.factory._determine_capabilities(intents, context)

        assert "web_search" in capabilities
        assert "data_analysis" in capabilities
        assert "opportunity_matching" in capabilities

    def test_determine_capabilities_adds_context_specific(self):
        """Test that context-specific capabilities are added"""
        intents = []
        context = {
            "location": "puna",
            "population": "elder",
            "urgency": "high"
        }

        capabilities = self.factory._determine_capabilities(intents, context)

        assert "local_knowledge" in capabilities
        assert "age_specific_knowledge" in capabilities
        assert "care_coordination" in capabilities
        assert "rapid_response" in capabilities

    def test_determine_capabilities_no_duplicates(self):
        """Test that duplicate capabilities are removed"""
        intents = ["grant_discovery", "grant_writing"]
        context = {}

        capabilities = self.factory._determine_capabilities(intents, context)

        # Should not have duplicates
        assert len(capabilities) == len(set(capabilities))

    def test_generate_agent_specifications(self):
        """Test generation of agent specifications"""
        intents = ["grant_discovery"]
        capabilities = ["web_search", "data_analysis"]
        context = {"location": "puna"}

        specs = self.factory._generate_agent_specifications(intents, capabilities, context)

        # Should have at least the intent-specific agent + coordination agents
        assert len(specs) >= 3  # grant discovery + 2 coordination agents

    def test_create_agent_specification_for_grant_discovery(self):
        """Test creating grant discovery agent spec"""
        spec = self.factory._create_agent_specification_for_intent("grant_discovery", {})

        assert spec.name == "GrantDiscoveryAgent"
        assert spec.specialization == "grant_discovery"
        assert len(spec.capabilities) > 0
        assert len(spec.tools_needed) > 0

    def test_create_agent_specification_for_grant_writing(self):
        """Test creating grant writing agent spec"""
        spec = self.factory._create_agent_specification_for_intent("grant_writing", {})

        assert spec.name == "GrantWritingAgent"
        assert spec.specialization == "grant_writing"

    def test_create_agent_specification_for_volunteer_coordination(self):
        """Test creating volunteer coordination agent spec"""
        spec = self.factory._create_agent_specification_for_intent("volunteer_coordination", {})

        assert spec.name == "VolunteerCoordinationAgent"
        assert spec.specialization == "volunteer_coordination"

    def test_create_agent_specification_for_elder_care(self):
        """Test creating elder care agent spec"""
        spec = self.factory._create_agent_specification_for_intent("elder_care", {})

        assert spec.name == "ElderCareSpecialistAgent"
        assert spec.specialization == "elder_care"

    def test_create_agent_specification_for_unknown_intent(self):
        """Test creating agent spec for unknown intent"""
        spec = self.factory._create_agent_specification_for_intent("unknown_intent", {})

        # Name is title-cased (e.g., "Unknown_IntentAgent")
        assert "Unknown_Intent" in spec.name or "unknown_intent" in spec.name.lower()
        assert spec.specialization == "unknown_intent"

    def test_create_coordination_agents(self):
        """Test creation of coordination agents"""
        agents = self.factory._create_coordination_agents({})

        assert len(agents) == 2
        names = [agent.name for agent in agents]
        assert "SystemOrchestrator" in names
        assert "CommunityMemoryAgent" in names

    @patch('dynamic_agent_factory.agent_zero')
    def test_deploy_agents(self, mock_agent_zero):
        """Test deploying agents"""
        mock_agent_zero.spawn_agents.return_value = ["agent1", "agent2"]

        spec1 = AgentSpecification(
            name="TestAgent1",
            description="Test",
            capabilities=["test"],
            tools_needed=["tool1"],
            specialization="test"
        )

        deployed = self.factory._deploy_agents([spec1])

        assert len(deployed) > 0
        assert deployed[0]["agent_id"] == "agent1"
        mock_agent_zero.spawn_agents.assert_called_once()

    @patch('dynamic_agent_factory.agent_zero')
    def test_process_request_complete_flow(self, mock_agent_zero):
        """Test complete request processing flow"""
        mock_agent_zero.spawn_agents.return_value = ["agent1", "agent2", "agent3"]

        request = "I need help finding grants for elder care in Puna"
        result = self.factory.process_request(request)

        assert result["status"] == "success"
        assert "grant_discovery" in result["detected_intents"]
        assert "elder_care" in result["detected_intents"]
        assert result["context"]["location"] == "puna"
        assert result["context"]["population"] == "elder"
        assert len(result["deployed_agents"]) > 0

    @patch('dynamic_agent_factory.agent_zero')
    def test_get_deployment_status(self, mock_agent_zero):
        """Test getting deployment status"""
        mock_agent = Mock()
        mock_agent.status.value = "active"
        mock_agent_zero.agents = {"agent1": mock_agent}
        mock_agent_zero.get_all_agents_status.return_value = []

        status = self.factory.get_deployment_status()

        assert status["total_agents"] == 1
        assert status["active_agents"] == 1


class TestGlobalFactoryInstance:
    """Test the global agent_factory instance"""

    def test_global_instance_exists(self):
        """Test that global instance is available"""
        assert agent_factory is not None
        assert isinstance(agent_factory, DynamicAgentFactory)

    @patch('dynamic_agent_factory.agent_zero')
    def test_process_community_request_function(self, mock_agent_zero):
        """Test the global process_community_request function"""
        mock_agent_zero.spawn_agents.return_value = ["agent1"]

        result = process_community_request("Find grants for community center")

        assert result is not None
        assert "detected_intents" in result
        assert result["status"] == "success"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
