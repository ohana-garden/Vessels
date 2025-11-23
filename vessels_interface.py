#!/usr/bin/env python3
"""
VESSELS INTERFACE
Natural language interface for the Vessels platform
Users say what they need in plain language
System generates entire agent networks to fulfill needs
No configuration, no setup - just describe and deploy
"""

import json
import logging
import threading
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import re
import uuid

from dynamic_agent_factory import agent_factory, process_community_request
from agent_zero_core import agent_zero
from community_memory import community_memory
from grant_coordination_system import grant_system
from adaptive_tools import adaptive_tools
from vessels.core import VesselContext, VesselRegistry

logger = logging.getLogger(__name__)

class InteractionType(Enum):
    COMMAND = "command"
    QUESTION = "question"
    REQUEST = "request"
    FEEDBACK = "feedback"
    STATUS = "status"

@dataclass
class UserInteraction:
    """User interaction with the system"""
    id: str
    user_id: str
    message: str
    interaction_type: InteractionType
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)
    response: Optional[str] = None
    follow_up_needed: bool = False

class VesselsInterface:
    """Natural language interface for Vessels platform"""

    def __init__(self, vessel_registry: Optional[VesselRegistry] = None):
        """
        Initialize Vessels Interface.

        Args:
            vessel_registry: Optional vessel registry for vessel context resolution.
                           If not provided, vessel features will be disabled.
        """
        self.interactions: Dict[str, UserInteraction] = {}
        self.user_contexts: Dict[str, Dict[str, Any]] = {}
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.interface_thread = None
        self.running = False
        self.vessel_registry = vessel_registry or VesselRegistry()

        self.initialize_interface()
    
    def initialize_interface(self):
        """Initialize the natural language interface"""
        self.running = True
        self.interface_thread = threading.Thread(target=self._interface_loop)
        self.interface_thread.daemon = True
        self.interface_thread.start()

        # Wire up agent_zero to use this interface for consultation messages
        agent_zero.interface = self

        logger.info("Vessels Natural Language Interface initialized")
    
    def process_message(self, user_id: str, message: str,
                       context: Dict[str, Any] = None,
                       vessel_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process natural language message from user.

        Args:
            user_id: User ID
            message: User message
            context: Optional context dict
            vessel_id: Optional explicit vessel ID (otherwise resolved from user_id)

        Returns:
            Response dictionary
        """
        # Resolve vessel context
        vessel_context = self._resolve_vessel_context(user_id, vessel_id)

        # Create interaction record
        interaction_id = str(uuid.uuid4())
        interaction_context = context or {}

        # Add vessel metadata to context
        if vessel_context:
            interaction_context.update(vessel_context.get_metadata())

        interaction = UserInteraction(
            id=interaction_id,
            user_id=user_id,
            message=message,
            interaction_type=self._classify_interaction(message),
            timestamp=datetime.now(),
            context=interaction_context
        )

        self.interactions[interaction_id] = interaction

        # Process the message (with vessel context available in interaction.context)
        response = self._process_interaction(interaction)

        # Update interaction with response
        interaction.response = response["response"]
        interaction.follow_up_needed = response.get("follow_up_needed", False)

        # Store user context
        self._update_user_context(user_id, interaction, response)

        return response

    def _resolve_vessel_context(
        self,
        user_id: str,
        vessel_id: Optional[str] = None
    ) -> Optional[VesselContext]:
        """
        Resolve vessel context for a user.

        Args:
            user_id: User ID
            vessel_id: Optional explicit vessel ID

        Returns:
            VesselContext or None
        """
        if not self.vessel_registry:
            return None

        if vessel_id:
            return VesselContext.from_vessel_id(vessel_id, self.vessel_registry)
        else:
            # Try to resolve from user, fall back to default
            context = VesselContext.from_user_id(user_id, self.vessel_registry)
            if context is None:
                context = VesselContext.get_default(self.vessel_registry)
            return context
    
    def _classify_interaction(self, message: str) -> InteractionType:
        """Classify the type of user interaction"""
        message_lower = message.lower().strip()
        
        # Command patterns
        command_patterns = [
            r'vessels\s+(start|begin|initiate|launch|deploy)',
            r'(create|build|make|setup)\s+(agent|system|platform)',
            r'run\s+(grant|coordination|management)',
            r'activate\s+(system|platform|agents)'
        ]
        
        # Question patterns
        question_patterns = [
            r'what\s+(is|are|can|do|does)',
            r'how\s+(do|does|can|should)',
            r'when\s+(will|can|should)',
            r'where\s+(can|do|is)',
            r'why\s+(is|are|do|does)'
        ]
        
        # Status patterns
        status_patterns = [
            r'status\s+(of|on|for)',
            r'how\s+(is|are)\s+(agent|system|grant)',
            r'what\'s\s+the\s+(status|progress|update)',
            r'show\s+(status|progress|results)'
        ]
        
        # Check patterns
        import re
        
        if any(re.search(pattern, message_lower) for pattern in command_patterns):
            return InteractionType.COMMAND
        elif any(re.search(pattern, message_lower) for pattern in question_patterns):
            return InteractionType.QUESTION
        elif any(re.search(pattern, message_lower) for pattern in status_patterns):
            return InteractionType.STATUS
        elif message_lower.startswith('vessels'):
            return InteractionType.REQUEST
        else:
            return InteractionType.REQUEST  # Default
    
    def _process_interaction(self, interaction: UserInteraction) -> Dict[str, Any]:
        """Process the user interaction and generate response"""

        # First check if this is a response to an active consultation
        consultation_response = self._check_for_consultation(
            interaction.user_id,
            interaction.message
        )
        if consultation_response:
            return consultation_response

        if interaction.interaction_type == InteractionType.COMMAND:
            return self._process_command(interaction)
        elif interaction.interaction_type == InteractionType.QUESTION:
            return self._process_question(interaction)
        elif interaction.interaction_type == InteractionType.STATUS:
            return self._process_status_request(interaction)
        else:
            return self._process_request(interaction)
    
    def _process_command(self, interaction: UserInteraction) -> Dict[str, Any]:
        """Process command-type interaction"""
        message = interaction.message
        
        # Extract command intent
        if "grant" in message.lower():
            return self._deploy_grant_system(interaction)
        elif "coordinate" in message.lower() or "volunteer" in message.lower():
            return self._deploy_coordination_system(interaction)
        elif "agent" in message.lower():
            return self._deploy_agent_system(interaction)
        elif "platform" in message.lower() or "system" in message.lower():
            return self._deploy_full_platform(interaction)
        else:
            return {
                "response": "I can deploy various systems for you. Try saying 'deploy grant system', 'coordinate volunteers', or 'activate full platform'.",
                "follow_up_needed": True,
                "suggestions": [
                    "Deploy grant management system",
                    "Coordinate community volunteers", 
                    "Activate elder care support",
                    "Start full platform deployment"
                ]
            }
    
    def _process_question(self, interaction: UserInteraction) -> Dict[str, Any]:
        """Process question-type interaction"""
        message = interaction.message
        
        if "what" in message.lower() and "grant" in message.lower():
            return self._answer_grant_questions(interaction)
        elif "how" in message.lower() and ("work" in message.lower() or "function" in message.lower()):
            return self._explain_system(interaction)
        elif "status" in message.lower():
            return self._process_status_request(interaction)
        else:
            return {
                "response": "I can answer questions about grants, system status, and coordination activities. What would you like to know?",
                "follow_up_needed": True
            }
    
    def _process_status_request(self, interaction: UserInteraction) -> Dict[str, Any]:
        """Process status request"""
        message = interaction.message
        
        if "grant" in message.lower():
            return self._get_grant_status(interaction)
        elif "agent" in message.lower():
            return self._get_agent_status(interaction)
        elif "system" in message.lower() or "platform" in message.lower():
            return self._get_system_status(interaction)
        else:
            return self._get_general_status(interaction)
    
    def _process_request(self, interaction: UserInteraction) -> Dict[str, Any]:
        """Process general request"""
        message = interaction.message
        
        # Use the agent factory to process the request
        try:
            result = process_community_request(message)
            
            response = f"""
I've analyzed your request and deployed the appropriate systems:

**Detected Needs:** {', '.join(result['detected_intents'])}

**Context:**
- Location: {result['context'].get('location', 'Not specified')}
- Population: {result['context'].get('population', 'General')}
- Urgency: {result['context'].get('urgency', 'Medium')}

**Deployed Agents:** {len(result['deployed_agents'])}
"""
            
            for agent in result['deployed_agents']:
                response += f"- {agent['name']} ({agent['specialization']})\n"
            
            response += "\nYour agents are now active and working on your request."
            
            return {
                "response": response,
                "deployment_result": result,
                "follow_up_needed": False
            }
            
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            return {
                "response": "I encountered an issue processing your request. Please try rephrasing or ask for help with specific tasks.",
                "error": str(e),
                "follow_up_needed": True
            }
    
    def _deploy_grant_system(self, interaction: UserInteraction) -> Dict[str, Any]:
        """Deploy grant management system"""
        try:
            # Discover grants immediately
            grants = grant_system.discover_all_opportunities()
            
            # Generate applications for top grants
            applications = grant_system.generate_all_applications()
            
            response = f"""
🎯 **Grant Management System Activated**

I've discovered {len(grants)} relevant grant opportunities and generated {len(applications)} applications.

**Top Grant Opportunities:**
"""
            
            for i, grant in enumerate(grants[:3]):
                response += f"{i+1}. {grant.title} - {grant.amount} (Due: {grant.deadline.strftime('%Y-%m-%d')})\n"
            
            response += f"""

**Applications Generated:**
"""
            
            for i, app in enumerate(applications[:3]):
                grant = grant_system.discovered_grants.get(app.grant_id)
                if grant:
                    response += f"- {grant.title}\n"
            
            response += "\n📋 Applications are ready for review and submission."
            
            return {
                "response": response,
                "grants_discovered": len(grants),
                "applications_generated": len(applications),
                "follow_up_needed": False
            }
            
        except Exception as e:
            return {
                "response": "I encountered an issue activating the grant system. Please try again or check system status.",
                "error": str(e),
                "follow_up_needed": True
            }
    
    def _deploy_coordination_system(self, interaction: UserInteraction) -> Dict[str, Any]:
        """Deploy volunteer coordination system"""
        try:
            # Process the coordination request
            result = process_community_request("coordinate volunteers for community elder care support")
            
            response = f"""
🤝 **Volunteer Coordination System Activated**

I've deployed {len(result['deployed_agents'])} coordination agents to manage volunteer activities.

**Active Coordinators:**
"""
            
            for agent in result['deployed_agents']:
                response += f"- {agent['name']}: {agent['specialization']}\n"
            
            response += f"""

**Coordination Features:**
✓ Volunteer recruitment and matching
✓ Task assignment and tracking
✓ Communication hub management
✓ Resource allocation optimization
✓ Progress monitoring and reporting

Your volunteer coordination network is now active and ready to organize community support.
"""
            
            return {
                "response": response,
                "deployment_result": result,
                "follow_up_needed": False
            }
            
        except Exception as e:
            return {
                "response": "I encountered an issue activating the coordination system. Please try again.",
                "error": str(e),
                "follow_up_needed": True
            }
    
    def _deploy_agent_system(self, interaction: UserInteraction) -> Dict[str, Any]:
        """Deploy general agent system"""
        try:
            # Get current agent status
            agent_status = agent_zero.get_all_agents_status()
            
            if len(agent_status) == 0:
                # No agents active, deploy basic system
                result = process_community_request("activate community coordination agents")
                
                response = f"""
🤖 **Agent System Activated**

I've deployed a new agent network with {len(result['deployed_agents'])} specialized agents.

**System Agents:**
"""
                
                for agent in result['deployed_agents']:
                    response += f"- {agent['name']} ({agent['specialization']})\n"
                
                response += "\nYour agent network is now active and coordinating activities."
                
            else:
                # Agents already active
                response = f"""
🤖 **Agent System Status**

Your agent network is already active with {len(agent_status)} agents.

**Active Agents:**
"""
                
                for agent_info in agent_status[:5]:
                    response += f"- {agent_info['name']} ({agent_info['specialization']}) - {agent_info['status']}\n"
                
                if len(agent_status) > 5:
                    response += f"... and {len(agent_status) - 5} more\n"
            
            return {
                "response": response,
                "agent_count": len(agent_status),
                "follow_up_needed": False
            }
            
        except Exception as e:
            return {
                "response": "I encountered an issue with the agent system. Please check system status.",
                "error": str(e),
                "follow_up_needed": True
            }
    
    def _deploy_full_platform(self, interaction: UserInteraction) -> Dict[str, Any]:
        """Deploy full Vessels platform"""
        try:
            # Deploy grant system
            grant_result = self._deploy_grant_system(interaction)
            
            # Deploy coordination system
            coord_result = self._deploy_coordination_system(interaction)
            
            # Deploy agent system
            agent_result = self._deploy_agent_system(interaction)
            
            response = f"""
🚀 **Full Vessels Platform Activated**

Your complete adaptive coordination platform is now running!

**Grant Management:**
{grant_result.get('grants_discovered', 0)} grants discovered
{grant_result.get('applications_generated', 0)} applications generated

**Volunteer Coordination:**
{len(coord_result.get('deployment_result', {}).get('deployed_agents', []))} coordination agents active

**Agent Network:**
{agent_result.get('agent_count', 0)} system agents operational

**Platform Features:**
✓ Dynamic agent creation and coordination
✓ Grant discovery and application generation
✓ Community memory and learning system
✓ Adaptive tool creation and management
✓ Real-time monitoring and optimization

The platform is self-managing and will adapt to your community's needs automatically.
"""
            
            return {
                "response": response,
                "full_deployment": True,
                "follow_up_needed": False
            }
            
        except Exception as e:
            return {
                "response": "I encountered an issue deploying the full platform. Please try individual components.",
                "error": str(e),
                "follow_up_needed": True
            }
    
    def _answer_grant_questions(self, interaction: UserInteraction) -> Dict[str, Any]:
        """Answer grant-related questions"""
        message = interaction.message
        
        if "available" in message.lower():
            # List available grants
            grants = grant_system.discovered_grants
            
            if len(grants) == 0:
                response = "No grants currently in the system. Let me search for opportunities."
                grants = grant_system.discover_all_opportunities()
            
            response = f"""
📊 **Available Grant Opportunities**

Found {len(grants)} grant opportunities:

"""
            
            for i, (grant_id, grant) in enumerate(list(grants.items())[:5]):
                response += f"{i+1}. **{grant.title}**\n"
                response += f"   Funder: {grant.funder}\n"
                response += f"   Amount: {grant.amount}\n"
                response += f"   Deadline: {grant.deadline.strftime('%Y-%m-%d')}\n"
                response += f"   Focus: {', '.join(grant.focus_areas[:2])}\n\n"
            
            if len(grants) > 5:
                response += f"... and {len(grants) - 5} more opportunities\n"
            
        elif "application" in message.lower():
            # Provide application information
            applications = grant_system.active_applications
            
            response = f"""
📋 **Grant Applications Status**

Currently managing {len(applications)} applications:

"""
            
            for i, (app_id, app) in enumerate(list(applications.items())[:3]):
                grant = grant_system.discovered_grants.get(app.grant_id)
                if grant:
                    response += f"{i+1}. **{grant.title}**\n"
                    response += f"   Status: {app.status.value}\n"
                    response += f"   Version: {app.version}\n"
                    if app.submission_date:
                        response += f"   Submitted: {app.submission_date.strftime('%Y-%m-%d')}\n"
                    response += "\n"
            
        else:
            response = "I can help with grants! Ask me about available opportunities, application status, or say 'find grants' to start a search."
        
        return {
            "response": response,
            "follow_up_needed": False
        }
    
    def _explain_system(self, interaction: UserInteraction) -> Dict[str, Any]:
        """Explain how the system works"""
        response = f"""
🔧 **How Vessels Works**

Vessels is an adaptive coordination platform that automatically creates and manages agent networks to fulfill community needs.

**Core Components:**

1. **Agent Zero Core** - Meta-coordination engine that spawns and manages agents
2. **Dynamic Agent Factory** - Creates agents from natural language requests
3. **Community Memory** - Shared learning and knowledge system
4. **Grant Coordination** - Complete grant discovery and application system
5. **Adaptive Tools** - Self-expanding tool ecosystem
6. **Universal Connectors** - Integration with external systems

**How It Works:**

1. **You describe your need** in natural language
2. **System analyzes** your intent and context
3. **Agents are spawned** with appropriate specializations
4. **Tools are created** or assigned as needed
5. **Coordination begins** automatically
6. **Results are delivered** and learning is shared

**Current Capabilities:**
✓ Grant discovery and application writing
✓ Volunteer coordination and management
✓ Community resource allocation
✓ Elder care program development
✓ Real-time monitoring and reporting

Simply tell me what you need, and I'll coordinate the entire solution!
"""
        
        return {
            "response": response,
            "follow_up_needed": False
        }
    
    def _get_grant_status(self, interaction: UserInteraction) -> Dict[str, Any]:
        """Get grant system status"""
        try:
            tracking_info = grant_system.track_and_manage()
            
            response = f"""
📊 **Grant System Status**

**Overall Progress:**
- Total grants discovered: {tracking_info['total_grants_discovered']}
- Active applications: {tracking_info['total_applications_active']}
- Upcoming deadlines: {len(tracking_info['upcoming_deadlines'])}

**Grant Status Distribution:**
"""
            
            for status, count in tracking_info['grants_by_status'].items():
                response += f"- {status.replace('_', ' ').title()}: {count}\n"
            
            if tracking_info['upcoming_deadlines']:
                response += "\n⚠️ **Upcoming Deadlines (30 days):**\n"
                for deadline in tracking_info['upcoming_deadlines'][:3]:
                    response += f"- {deadline['title']}: {deadline['days_remaining']} days remaining\n"
            
            if tracking_info['performance_metrics']:
                response += f"""

**Performance Metrics:**
- Application rate: {tracking_info['performance_metrics'].get('application_rate', 0):.1f}%
- Funding potential: ${tracking_info['performance_metrics'].get('funding_potential', 0):,}
"""
            
            return {
                "response": response,
                "follow_up_needed": False
            }
            
        except Exception as e:
            return {
                "response": "Unable to retrieve grant status at the moment.",
                "error": str(e),
                "follow_up_needed": True
            }
    
    def _get_agent_status(self, interaction: UserInteraction) -> Dict[str, Any]:
        """Get agent system status"""
        try:
            agent_status = agent_zero.get_all_agents_status()
            
            if len(agent_status) == 0:
                return {
                    "response": "No agents are currently active. Would you like me to deploy some?",
                    "follow_up_needed": True
                }
            
            response = f"""
🤖 **Agent System Status**

**Active Agents:** {len(agent_status)}

**Agent Details:**
"""
            
            # Group by status
            status_groups = {}
            for agent in agent_status:
                status = agent['status']
                if status not in status_groups:
                    status_groups[status] = []
                status_groups[status].append(agent)
            
            for status, agents in status_groups.items():
                response += f"\n**{status.upper()}:**\n"
                for agent in agents[:3]:
                    response += f"- {agent['name']} ({agent['specialization']})\n"
                if len(agents) > 3:
                    response += f"... and {len(agents) - 3} more\n"
            
            return {
                "response": response,
                "follow_up_needed": False
            }
            
        except Exception as e:
            return {
                "response": "Unable to retrieve agent status at the moment.",
                "error": str(e),
                "follow_up_needed": True
            }
    
    def _get_system_status(self, interaction: UserInteraction) -> Dict[str, Any]:
        """Get overall system status"""
        try:
            # Get various system statuses
            grant_info = grant_system.track_and_manage()
            agent_status = agent_zero.get_all_agents_status()
            memory_insights = community_memory.get_memory_insights()
            tool_insights = adaptive_tools.get_tool_insights()
            
            response = f"""
🌐 **Vessels Platform Status**

**System Overview:**
✓ Platform Status: ACTIVE
✓ Grant System: {'OPERATIONAL' if grant_info['total_grants_discovered'] > 0 else 'SEARCHING'}
✓ Agent Network: {'ACTIVE' if len(agent_status) > 0 else 'READY'}
✓ Memory System: {'ONLINE' if memory_insights['total_memories'] > 0 else 'INITIALIZED'}
✓ Tool System: {'EXPANDABLE' if tool_insights['total_tools'] > 0 else 'READY'}

**Detailed Metrics:**

**Grants & Applications:**
- Opportunities: {grant_info['total_grants_discovered']}
- Applications: {grant_info['total_applications_active']}
- Success Rate: {grant_info['performance_metrics'].get('application_rate', 0):.1f}%

**Agent Network:**
- Total Agents: {len(agent_status)}
- Active: {len([a for a in agent_status if a['status'] == 'active'])}
- Specializations: {len(set(a['specialization'] for a in agent_status))}

**Learning & Memory:**
- Total Memories: {memory_insights['total_memories']}
- Knowledge Items: {memory_insights['memory_types'].get('knowledge', 0)}
- Experiences: {memory_insights['memory_types'].get('experience', 0)}

**Tool Ecosystem:**
- Total Tools: {tool_insights['total_tools']}
- Tool Types: {len(tool_insights['tools_by_type'])}
- Recent Creations: {len(tool_insights['recently_created'])}

**System Health:**
All core systems are operational and ready to coordinate community needs.
"""
            
            return {
                "response": response,
                "follow_up_needed": False
            }
            
        except Exception as e:
            return {
                "response": "Unable to retrieve complete system status at the moment.",
                "error": str(e),
                "follow_up_needed": True
            }
    
    def _get_general_status(self, interaction: UserInteraction) -> Dict[str, Any]:
        """Get general status overview"""
        return self._get_system_status(interaction)
    
    def _update_user_context(self, user_id: str, interaction: UserInteraction, response: Dict[str, Any]):
        """Update user context based on interaction"""
        if user_id not in self.user_contexts:
            self.user_contexts[user_id] = {
                "interaction_history": [],
                "preferences": {},
                "active_interests": [],
                "last_activity": datetime.now()
            }
        
        context = self.user_contexts[user_id]
        
        # Add interaction to history
        context["interaction_history"].append({
            "id": interaction.id,
            "message": interaction.message,
            "response": response.get("response", "")[:100],  # Truncate for storage
            "timestamp": interaction.timestamp,
            "type": interaction.interaction_type.value
        })
        
        # Keep only last 20 interactions
        if len(context["interaction_history"]) > 20:
            context["interaction_history"] = context["interaction_history"][-20:]
        
        # Update active interests based on interaction
        if "grant" in interaction.message.lower():
            if "grant_management" not in context["active_interests"]:
                context["active_interests"].append("grant_management")
        
        if "volunteer" in interaction.message.lower() or "coordinate" in interaction.message.lower():
            if "volunteer_coordination" not in context["active_interests"]:
                context["active_interests"].append("volunteer_coordination")
        
        if "elder" in interaction.message.lower() or "care" in interaction.message.lower():
            if "elder_care" not in context["active_interests"]:
                context["active_interests"].append("elder_care")
        
        context["last_activity"] = datetime.now()
    
    def get_user_context(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user context"""
        return self.user_contexts.get(user_id)
    
    def get_interaction_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user's interaction history"""
        context = self.user_contexts.get(user_id)
        if context:
            return context["interaction_history"][-limit:]
        return []
    
    def _interface_loop(self):
        """Background interface loop for maintenance"""
        while self.running:
            try:
                # Clean up old interactions (older than 30 days)
                current_time = datetime.now()
                old_interactions = []
                
                for interaction_id, interaction in self.interactions.items():
                    if (current_time - interaction.timestamp).days > 30:
                        old_interactions.append(interaction_id)
                
                for interaction_id in old_interactions:
                    del self.interactions[interaction_id]
                
                # Clean up inactive user contexts (older than 90 days)
                inactive_users = []
                for user_id, context in self.user_contexts.items():
                    if (current_time - context["last_activity"]).days > 90:
                        inactive_users.append(user_id)
                
                for user_id in inactive_users:
                    del self.user_contexts[user_id]
                
                logger.info(f"Interface maintenance: cleaned up {len(old_interactions)} old interactions and {len(inactive_users)} inactive users")
                
            except Exception as e:
                logger.error(f"Interface maintenance error: {e}")
            
            time.sleep(3600)  # Run every hour
    
    def send_message(self, agent_id: str, message: str):
        """
        Send a message to a user (for consultation prompts).

        Args:
            agent_id: Agent ID sending the message
            message: Message content
        """
        # For now, just log it. In production, this would route to the appropriate user
        logger.info(f"Message from agent {agent_id}:\n{message}")
        print(f"\n{message}\n")

    def handle_consultation_response(
        self,
        agent_id: str,
        user_response: str
    ) -> Dict[str, Any]:
        """
        Handle user response to a consultation request.

        This routes the response to the agent orchestrator to resolve the consultation.

        Args:
            agent_id: ID of the agent in consultation
            user_response: User's response

        Returns:
            Dictionary with handling result
        """
        # Route to agent_zero for handling
        result = agent_zero.handle_consultation_response(agent_id, user_response)

        if result.get("success"):
            return {
                "response": result.get("message", "Consultation resolved."),
                "action": result.get("action"),
                "follow_up_needed": False
            }
        else:
            return {
                "response": f"Error handling consultation: {result.get('error', 'Unknown error')}",
                "follow_up_needed": True
            }

    def _check_for_consultation(self, user_id: str, message: str) -> Optional[Dict[str, Any]]:
        """
        Check if this message is a response to an active consultation.

        Args:
            user_id: User ID
            message: User message

        Returns:
            Consultation response result if applicable, None otherwise
        """
        # Check if any agents are in consultation mode for this user
        # For now, we'll check all agents (in production, map users to agents)
        for agent_id, agent in agent_zero.agents.items():
            if agent.status.value == "paused_for_consultation":
                # This message might be a consultation response
                logger.info(f"Found agent {agent_id} in consultation mode, processing response")
                return self.handle_consultation_response(agent_id, message)

        return None

    def get_system_insights(self) -> Dict[str, Any]:
        """Get insights about system usage and performance"""
        insights = {
            "total_interactions": len(self.interactions),
            "active_users": len(self.user_contexts),
            "interaction_types": {},
            "popular_requests": [],
            "system_recommendations": []
        }
        
        # Count interaction types
        for interaction in self.interactions.values():
            interaction_type = interaction.interaction_type.value
            insights["interaction_types"][interaction_type] = insights["interaction_types"].get(interaction_type, 0) + 1
        
        # Analyze popular requests
        request_keywords = defaultdict(int)
        for interaction in self.interactions.values():
            if interaction.interaction_type in [InteractionType.REQUEST, InteractionType.COMMAND]:
                words = interaction.message.lower().split()
                for word in words:
                    if word in ['grant', 'volunteer', 'coordinate', 'help', 'find', 'manage', 'system']:
                        request_keywords[word] += 1
        
        insights["popular_requests"] = sorted(request_keywords.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Generate recommendations
        if insights["total_interactions"] > 100:
            insights["system_recommendations"].append({
                "type": "usage",
                "message": f"High usage detected: {insights['total_interactions']} interactions"
            })
        
        if len(self.user_contexts) > 10:
            insights["system_recommendations"].append({
                "type": "scaling",
                "message": "Consider scaling for multiple active users"
            })
        
        return insights
    
    def shutdown(self):
        """Shutdown the interface"""
        self.running = False
        
        if self.interface_thread:
            self.interface_thread.join(timeout=10)
        
        logger.info("Vessels Interface shutdown complete")

# Global interface instance
vessels_interface = VesselsInterface()

def process_user_message(user_id: str, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Main entry point for processing user messages"""
    return vessels_interface.process_message(user_id, message, context)