#!/usr/bin/env python3
"""
VESSELS PLATFORM DEMO
Simple demonstration of the core capabilities
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import core modules without Docker dependencies
from agent_zero_core import agent_zero, AgentZeroCore
from dynamic_agent_factory import agent_factory, process_community_request
from community_memory import community_memory, CommunityMemory
from grant_coordination_system import grant_system, GrantCoordinationSystem
from adaptive_tools import adaptive_tools, AdaptiveTools
from vessels_interface import vessels_interface, VesselsInterface
from universal_connector import universal_connector, UniversalConnector

import logging
import time
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VesselsDemo:
    """Demo of Vessels Platform capabilities"""
    
    def __init__(self):
        self.running = False
        logger.info("🌺 Vessels Platform Demo initializing...")
    
    def start(self):
        """Start the demo"""
        self.running = True
        logger.info("🚀 Starting Vessels Platform Demo...")
        
        # Initialize core systems
        self._initialize_systems()
        
        # Run demo scenarios
        self._run_demo_scenarios()
        
        # Interactive mode
        self._interactive_demo()
    
    def _initialize_systems(self):
        """Initialize core systems"""
        logger.info("🔧 Initializing core systems...")
        
        # Initialize systems (already initialized by imports)
        logger.info("✅ Community Memory System ready")
        logger.info("✅ Adaptive Tools System ready")
        logger.info("✅ Agent Zero Core ready")
        logger.info("✅ Grant Coordination System ready")
        logger.info("✅ Universal Connector System ready")
        logger.info("✅ Natural Language Interface ready")
        
        logger.info("✅ All core systems initialized")
    
    def _run_demo_scenarios(self):
        """Run demonstration scenarios"""
        print("\n" + "="*60)
        print("🎯 VESSELS PLATFORM DEMONSTRATION")
        print("="*60)
        
        # Scenario 1: Grant Discovery
        self._demo_grant_discovery()
        
        # Scenario 2: Agent Creation
        self._demo_agent_creation()
        
        # Scenario 3: Community Memory
        self._demo_community_memory()
        
        # Scenario 4: Tool Creation
        self._demo_tool_creation()
        
        print("\n" + "="*60)
        print("✅ DEMO SCENARIOS COMPLETE")
        print("="*60)
    
    def _demo_grant_discovery(self):
        """Demonstrate grant discovery capabilities"""
        print("\n📊 **GRANT DISCOVERY DEMONSTRATION**")
        print("-" * 40)
        
        try:
            # Discover grants
            grants = grant_system.discover_all_opportunities()
            print(f"🎯 Found {len(grants)} grant opportunities:")
            
            for i, grant in enumerate(grants[:3]):
                print(f"\n{i+1}. **{grant.title}**")
                print(f"   Funder: {grant.funder}")
                print(f"   Amount: {grant.amount}")
                print(f"   Deadline: {grant.deadline.strftime('%Y-%m-%d')}")
                print(f"   Focus: {', '.join(grant.focus_areas[:2])}")
            
            if len(grants) > 3:
                print(f"\n... and {len(grants) - 3} more")
            
            # Generate applications
            print(f"\n📝 Generating applications for top grants...")
            applications = grant_system.generate_all_applications()
            print(f"✅ Generated {len(applications)} complete applications")
            
            print_success("Grant discovery demonstration complete")
            
        except Exception as e:
            print(f"❌ Grant discovery error: {e}")
    
    def _demo_agent_creation(self):
        """Demonstrate dynamic agent creation"""
        print("\n🤖 **AGENT CREATION DEMONSTRATION**")
        print("-" * 40)
        
        try:
            # Process community request
            request = "I need help finding grants for elder care in Puna"
            result = process_community_request(request)
            
            print(f"🎯 Request: '{request}'")
            print(f"📋 Detected intents: {', '.join(result['detected_intents'])}")
            print(f"🌍 Context: {result['context']}")
            print(f"🤖 Deployed agents: {len(result['deployed_agents'])}")
            
            for agent in result['deployed_agents']:
                print(f"   - {agent['name']} ({agent['specialization']})")
            
            print_success("Agent creation demonstration complete")
            
        except Exception as e:
            print(f"❌ Agent creation error: {e}")
    
    def _demo_community_memory(self):
        """Demonstrate community memory capabilities"""
        print("\n🧠 **COMMUNITY MEMORY DEMONSTRATION**")
        print("-" * 40)
        
        try:
            # Store some experience
            experience = {
                "type": "grant_discovery",
                "success": True,
                "method": "web_search",
                "keywords": ["elder_care", "hawaii", "community"],
                "results_count": 5
            }
            
            memory_id = community_memory.store_experience("demo_agent", experience)
            print(f"💾 Stored experience: {memory_id}")
            
            # Get memory insights
            insights = community_memory.get_memory_insights()
            print(f"📊 Memory system insights:")
            print(f"   - Total memories: {insights['total_memories']}")
            print(f"   - Memory types: {insights['memory_types']}")
            print(f"   - Recent activity: {len(insights['recent_activity'])} items")
            
            print_success("Community memory demonstration complete")
            
        except Exception as e:
            print(f"❌ Community memory error: {e}")
    
    def _demo_tool_creation(self):
        """Demonstrate adaptive tool creation"""
        print("\n🔧 **TOOL CREATION DEMONSTRATION**")
        print("-" * 40)
        
        try:
            # Identify needed capabilities
            requirements = ["web_search", "grant_discovery", "data_analysis"]
            capabilities = adaptive_tools.identify_needed_capabilities(requirements)
            print(f"🎯 Needed capabilities: {capabilities}")
            
            # Get tool insights
            insights = adaptive_tools.get_tool_insights()
            print(f"📊 Tool system insights:")
            print(f"   - Total tools: {insights['total_tools']}")
            print(f"   - Tool types: {insights['tools_by_type']}")
            print(f"   - Most used: {insights['most_used_tools'][:2]}")
            
            print_success("Tool creation demonstration complete")
            
        except Exception as e:
            print(f"❌ Tool creation error: {e}")
    
    def _interactive_demo(self):
        """Interactive demonstration mode"""
        print("\n" + "="*60)
        print("🎮 INTERACTIVE DEMO MODE")
        print("="*60)
        print("Try these commands:")
        print("  - 'find grants for elder care in Puna'")
        print("  - 'coordinate volunteers for community support'")
        print("  - 'what grants are available?'")
        print("  - 'show me the platform status'")
        print("  - 'exit' to quit")
        print("="*60)
        
        while self.running:
            try:
                user_input = input("\n🗣️  You: ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    print("👋 Goodbye! Thanks for trying Vessels!")
                    break
                
                if not user_input:
                    continue
                
                # Process through natural language interface
                print("🤔 Processing...")
                response = vessels_interface.process_message("demo_user", user_input)
                
                print(f"\n🤖 Vessels: {response['response']}")
                
                if response.get('follow_up_needed') and response.get('suggestions'):
                    print("\n💡 Suggestions:")
                    for suggestion in response['suggestions']:
                        print(f"  - {suggestion}")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                logger.error(f"Interactive demo error: {e}")
    
    def get_demo_status(self) -> Dict[str, Any]:
        """Get demo status"""
        try:
            return {
                "demo_running": self.running,
                "systems_ready": True,
                "agent_count": len(agent_zero.agents),
                "memory_count": len(community_memory.memories),
                "tool_count": len(adaptive_tools.tools),
                "connector_count": len(universal_connector.connectors)
            }
        except Exception as e:
            return {
                "demo_running": self.running,
                "error": str(e)
            }

def main():
    """Main demo function"""
    
    print("🌺 VESSELS PLATFORM DEMONSTRATION")
    print("=================================")
    print("This demo showcases the core capabilities of Vessels:")
    print("✅ Dynamic agent creation from natural language")
    print("✅ Grant discovery and application generation")
    print("✅ Community memory and learning system")
    print("✅ Adaptive tool creation and management")
    print("✅ Universal system connectivity")
    print("=================================\n")
    
    # Create and start demo
    demo = VesselsDemo()
    
    try:
        demo.start()
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
    except Exception as e:
        print(f"❌ Demo error: {e}")
        logger.error(f"Demo error: {e}")
    finally:
        print("\n🌺 Mahalo for trying Vessels!")

if __name__ == "__main__":
    main()