#!/usr/bin/env python3
"""
DYNAMIC AGENT FACTORY
Input: "I need help finding grants for elder care in Puna"
Output: Fully configured, running agents that handle the entire process
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import re
from agent_zero_core import AgentZeroCore, AgentSpecification, agent_zero
import os
import bmad_loader  # BMAD loader from the project root; resolves based on current working dir

logger = logging.getLogger(__name__)

class DynamicAgentFactory:
    """Factory that creates agents from natural language requests"""
    
    def __init__(self):
        self.intent_patterns = self._load_intent_patterns()
        self.capability_matrix = self._build_capability_matrix()
        self.tool_requirements = self._build_tool_requirements()
        # Load BMAD agent specifications from the `.bmad/agents` directory. We
        # compute the path relative to this file to ensure correctness even
        # when called from other working directories. If no BMAD agents are
        # found, this list will be empty.
        bmad_path = os.path.join(os.path.dirname(__file__), ".bmad")
        try:
            self.bmad_agents = bmad_loader.load_agents(bmad_path)
        except Exception as e:
            # If loading fails, log and continue with an empty list
            logger.warning(f"Failed to load BMAD agents: {e}")
            self.bmad_agents = []
        
    def _load_intent_patterns(self) -> Dict[str, List[str]]:
        """Load patterns for recognizing user intents"""
        config_path = Path(os.getenv("VESSELS_INTENT_CONFIG", "config/intent_config.json"))
        if config_path.exists():
            try:
                with config_path.open("r") as f:
                    config = json.load(f)
                logger.info(f"Loaded intent configuration from {config_path}")
                return {intent: data.get("patterns", []) for intent, data in config.items()}
            except Exception as e:
                logger.error(f"Failed to load intent config {config_path}: {e}")

        logger.warning("Using built-in intent patterns; provide config/intent_config.json to extend them")
        return {
            "grant_discovery": [
                r"find.*grant",
                r"search.*funding",
                r"discover.*opportunit",
                r"grant.*available",
                r"funding.*source",
                r"grant.*catalog",
                r"grant.*database",
            ],
            "grant_writing": [
                r"write.*grant",
                r"appl.*grant",
                r"submit.*proposal",
                r"grant.*applic",
                r"proposal.*writing",
                r"draft.*proposal",
                r"grant.*narrative",
            ],
            "volunteer_coordination": [
                r"coordinate.*volunteer",
                r"manage.*volunteer",
                r"volunteer.*organiz",
                r"help.*volunteer",
                r"volunteer.*recruit",
                r"volunteer.*schedule",
            ],
            "elder_care": [
                r"elder.*care",
                r"senior.*service",
                r"aging.*support",
                r"elderly.*help",
                r"senior.*care",
                r"home.*care",
            ],
            "community_coordination": [
                r"coordinate.*community",
                r"organiz.*community",
                r"community.*help",
                r"local.*support",
                r"community.*resource",
                r"community.*event",
            ],
            "resource_management": [
                r"manage.*resource",
                r"allocat.*resource",
                r"distribut.*resource",
                r"resource.*coordinat",
                r"asset.*management",
                r"inventory",
            ],
        }
    
    def _build_capability_matrix(self) -> Dict[str, List[str]]:
        """Build matrix of capabilities needed for each intent"""
        return {
            "grant_discovery": [
                "web_search", "data_analysis", "opportunity_matching", 
                "deadline_tracking", "eligibility_assessment", "grant_database_query"
            ],
            "grant_writing": [
                "document_generation", "compliance_checking", "narrative_writing",
                "budget_creation", "template_management", "submission_handling"
            ],
            "volunteer_coordination": [
                "volunteer_matching", "task_assignment", "scheduling",
                "communication", "progress_tracking", "skill_assessment"
            ],
            "elder_care": [
                "needs_assessment", "program_design", "care_coordination",
                "resource_mapping", "benefit_calculation", "service_navigation"
            ],
            "community_coordination": [
                "resource_allocation", "scheduling", "communication",
                "stakeholder_engagement", "conflict_resolution", "project_management"
            ],
            "resource_management": [
                "inventory_tracking", "allocation_optimization", "usage_monitoring",
                "procurement", "distribution", "reporting"
            ]
        }
    
    def _build_tool_requirements(self) -> Dict[str, List[str]]:
        """Build tool requirements for each capability"""
        return {
            "web_search": ["search_engine", "web_scraper", "content_extractor"],
            "data_analysis": ["data_processor", "statistical_analyzer", "visualization_tool"],
            "opportunity_matching": ["matching_algorithm", "eligibility_checker", "scoring_system"],
            "document_generation": ["template_system", "content_generator", "format_converter"],
            "compliance_checking": ["compliance_database", "rule_engine", "validator"],
            "narrative_writing": ["language_model", "story_generator", "editor"],
            "volunteer_matching": ["skill_database", "availability_tracker", "matching_engine"],
            "task_assignment": ["task_manager", "priority_queue", "notification_system"],
            "scheduling": ["calendar_system", "conflict_resolver", "reminder_service"],
            "communication": ["messaging_system", "broadcast_tool", "notification_hub"],
            "needs_assessment": ["assessment_forms", "scoring_system", "report_generator"],
            "program_design": ["program_templates", "logic_model_tool", "evaluation_planner"],
            "resource_mapping": ["resource_database", "mapping_tool", "search_engine"]
        }
    
    def process_request(self, user_request: str) -> Dict[str, Any]:
        """Process natural language request and create agents"""
        
        # Step 1: Analyze intent
        detected_intents = self._detect_intents(user_request)
        
        # Step 2: Extract context
        context = self._extract_context(user_request)
        
        # Step 3: Determine required capabilities
        required_capabilities = self._determine_capabilities(detected_intents, context)
        
        # Step 4: Generate agent specifications
        agent_specs = self._generate_agent_specifications(
            detected_intents, required_capabilities, context
        )
        
        # Step 5: Create and deploy agents
        deployed_agents = self._deploy_agents(agent_specs)
        
        # Step 6: Return deployment summary
        return {
            "request": user_request,
            "detected_intents": detected_intents,
            "context": context,
            "deployed_agents": deployed_agents,
            "deployment_time": datetime.now().isoformat(),
            "status": "success"
        }
    
    def _detect_intents(self, request: str) -> List[str]:
        """Detect intents from user request"""
        detected = []
        request_lower = request.lower()
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, request_lower, re.IGNORECASE):
                    detected.append(intent)
                    break
        
        # Remove duplicates while preserving order
        seen = set()
        unique_detected = []
        for intent in detected:
            if intent not in seen:
                seen.add(intent)
                unique_detected.append(intent)
        
        return unique_detected
    
    def _extract_context(self, request: str) -> Dict[str, Any]:
        """Extract contextual information from request"""
        context = {
            "location": None,
            "population": None,
            "urgency": "medium",
            "scope": "local",
            "specific_needs": [],
            "constraints": [],
            "preferences": []
        }
        
        request_lower = request.lower()
        
        # Extract location
        location_keywords = ["puna", "hawaii", "big island", "oahu", "maui", "kauai", "lanai", "molokai"]
        for location in location_keywords:
            if location in request_lower:
                context["location"] = location
                break
        
        # Extract population
        population_keywords = ["elder", "senior", "youth", "family", "disabled", "veteran", "homeless"]
        for pop in population_keywords:
            if pop in request_lower:
                context["population"] = pop
                break
        
        # Extract urgency
        urgency_keywords = {
            "high": ["urgent", "emergency", "asap", "immediately", "critical"],
            "low": ["when possible", "eventually", "someday", "future"]
        }
        for level, keywords in urgency_keywords.items():
            for keyword in keywords:
                if keyword in request_lower:
                    context["urgency"] = level
                    break
        
        # Extract specific needs
        need_indicators = ["transportation", "housing", "food", "healthcare", "education", "employment"]
        for need in need_indicators:
            if need in request_lower:
                context["specific_needs"].append(need)
        
        return context
    
    def _determine_capabilities(self, intents: List[str], context: Dict[str, Any]) -> List[str]:
        """Determine required capabilities based on intents and context"""
        capabilities = []
        
        for intent in intents:
            if intent in self.capability_matrix:
                capabilities.extend(self.capability_matrix[intent])
        
        # Add context-specific capabilities
        if context.get("location"):
            capabilities.append("local_knowledge")
        
        if context.get("population") == "elder":
            capabilities.extend(["age_specific_knowledge", "care_coordination"])
        
        if context.get("urgency") == "high":
            capabilities.extend(["rapid_response", "priority_handling"])
        
        # Remove duplicates
        return list(set(capabilities))
    
    def _generate_agent_specifications(self, intents: List[str], capabilities: List[str], 
                                     context: Dict[str, Any]) -> List[AgentSpecification]:
        """Generate agent specifications based on analysis"""
        specifications = []
        
        # Create specialized agents for each intent
        for intent in intents:
            spec = self._create_agent_specification_for_intent(intent, context)
            specifications.append(spec)
        
        # Always add coordination agents
        specifications.extend(self._create_coordination_agents(context))

        # Append BMAD-defined agents. These agents come from Markdown files in
        # `.bmad/agents` and are loaded during initialization. They provide
        # specialized roles such as Architect, Analyst and Orchestrator. We
        # append them here so they participate in the deployment.
        if hasattr(self, 'bmad_agents') and self.bmad_agents:
            specifications.extend(self.bmad_agents)
        
        return specifications
    
    def _create_agent_specification_for_intent(self, intent: str, context: Dict[str, Any]) -> AgentSpecification:
        """Create agent specification for specific intent"""
        
        agent_configs = {
            "grant_discovery": {
                "name": "GrantDiscoveryAgent",
                "description": "Discovers and analyzes grant opportunities",
                "specialization": "grant_discovery",
                "communication_style": "analytical",
                "autonomy_level": "high"
            },
            "grant_writing": {
                "name": "GrantWritingAgent", 
                "description": "Writes and submits grant applications",
                "specialization": "grant_writing",
                "communication_style": "professional",
                "autonomy_level": "medium"
            },
            "volunteer_coordination": {
                "name": "VolunteerCoordinationAgent",
                "description": "Coordinates volunteer activities and recruitment",
                "specialization": "volunteer_coordination", 
                "communication_style": "collaborative",
                "autonomy_level": "high"
            },
            "elder_care": {
                "name": "ElderCareSpecialistAgent",
                "description": "Specializes in elder care programs and services",
                "specialization": "elder_care",
                "communication_style": "compassionate",
                "autonomy_level": "high"
            },
            "community_coordination": {
                "name": "CommunityCoordinationAgent",
                "description": "Coordinates community resources and activities",
                "specialization": "community_coordination",
                "communication_style": "collaborative",
                "autonomy_level": "high"
            },
            "resource_management": {
                "name": "ResourceManagementAgent",
                "description": "Manages and allocates community resources",
                "specialization": "resource_management",
                "communication_style": "systematic",
                "autonomy_level": "high"
            }
        }
        
        config = agent_configs.get(intent, {
            "name": f"{intent.title()}Agent",
            "description": f"Agent specializing in {intent}",
            "specialization": intent,
            "communication_style": "collaborative",
            "autonomy_level": "medium"
        })
        
        # Get capabilities for this intent
        capabilities = self.capability_matrix.get(intent, [])
        
        # Get tools needed for these capabilities
        tools_needed = []
        for capability in capabilities:
            if capability in self.tool_requirements:
                tools_needed.extend(self.tool_requirements[capability])
        
        return AgentSpecification(
            name=config["name"],
            description=config["description"],
            capabilities=capabilities,
            tools_needed=list(set(tools_needed)),  # Remove duplicates
            communication_style=config["communication_style"],
            autonomy_level=config["autonomy_level"],
            specialization=config["specialization"]
        )
    
    def _create_coordination_agents(self, context: Dict[str, Any]) -> List[AgentSpecification]:
        """Create coordination agents"""
        return [
            AgentSpecification(
                name="SystemOrchestrator",
                description="Orchestrates all agents and coordinates system activities",
                capabilities=["orchestration", "monitoring", "optimization", "conflict_resolution"],
                tools_needed=["monitoring_system", "performance_analyzer", "resource_manager", "message_router"],
                specialization="system_orchestration",
                communication_style="directive",
                autonomy_level="full"
            ),
            AgentSpecification(
                name="CommunityMemoryAgent",
                description="Manages community knowledge and learning",
                capabilities=["memory_management", "knowledge_extraction", "pattern_recognition", "experience_sharing"],
                tools_needed=["vector_database", "knowledge_graph", "learning_system", "experience_store"],
                specialization="memory_management",
                communication_style="informative",
                autonomy_level="high"
            )
        ]
    
    def _deploy_agents(self, specifications: List[AgentSpecification]) -> List[Dict[str, Any]]:
        """Deploy agents using Agent Zero Core"""
        deployed = []
        
        # Use the global agent_zero instance
        agent_ids = agent_zero.spawn_agents(specifications)
        
        for i, agent_id in enumerate(agent_ids):
            if i < len(specifications):
                spec = specifications[i]
                deployed.append({
                    "agent_id": agent_id,
                    "name": spec.name,
                    "specialization": spec.specialization,
                    "status": "deployed",
                    "capabilities": spec.capabilities,
                    "tools": spec.tools_needed
                })
        
        return deployed
    
    def get_deployment_status(self, deployment_id: str = None) -> Dict[str, Any]:
        """Get status of deployed agents"""
        return {
            "total_agents": len(agent_zero.agents),
            "active_agents": len([a for a in agent_zero.agents.values() if a.status.value == "active"]),
            "agent_details": agent_zero.get_all_agents_status()
        }

# Global factory instance
agent_factory = DynamicAgentFactory()

def process_community_request(request: str) -> Dict[str, Any]:
    """Main entry point for processing community requests"""
    return agent_factory.process_request(request)