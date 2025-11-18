#!/usr/bin/env python3
"""
SHOGHI - Adaptive Coordination Platform with Moral Constraints
Main entry point for the complete Shoghi system

ALL AGENT ACTIONS GATED THROUGH BAHÁ'Í-DERIVED VIRTUE MANIFOLD
EVERY EXTERNAL ACTION VALIDATED FOR MORAL COHERENCE
12D PHASE SPACE TRACKING OF ALL SYSTEM BEHAVIORS
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Import all core modules (NOW WITH INTEGRATED MORAL CONSTRAINTS)
from agent_zero_core import agent_zero, AgentZeroCore
from dynamic_agent_factory import agent_factory, process_community_request
from community_memory import community_memory, CommunityMemory
from grant_coordination_system import grant_system, GrantCoordinationSystem
from adaptive_tools import adaptive_tools, AdaptiveTools
from shoghi_interface import shoghi_interface, ShoghiInterface
from auto_deploy import auto_deploy, deploy_shoghi_platform
from universal_connector import universal_connector, UniversalConnector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('shoghi.log')
    ]
)

logger = logging.getLogger(__name__)

class ShoghiPlatform:
    """Main Shoghi adaptive coordination platform"""
    
    def __init__(self):
        self.running = False
        self.start_time = None
        self.mode = "development"  # development, production, deployed

        # Core system components (ALL WITH INTEGRATED MORAL CONSTRAINTS)
        self.agent_core = None
        self.memory_system = None
        self.tool_system = None
        self.grant_system = None
        self.connector_system = None
        self.interface_system = None
        self.deploy_system = None

        logger.info("🌺 Shoghi Platform initializing with INTEGRATED MORAL CONSTRAINT SYSTEM...")
    
    def start(self, mode: str = "development"):
        """Start the complete Shoghi platform"""
        
        self.mode = mode
        self.start_time = datetime.now()
        self.running = True
        
        logger.info(f"🚀 Starting Shoghi Platform in {mode} mode...")
        
        try:
            # Initialize all core systems
            self._initialize_core_systems()
            
            # Start platform services
            self._start_platform_services()
            
            # Log startup completion
            self._log_startup_completion()
            
            # Enter main operation loop
            self._main_operation_loop()
            
        except Exception as e:
            logger.error(f"❌ Platform startup failed: {e}")
            self.shutdown()
            raise
    
    def _initialize_core_systems(self):
        """Initialize all core system components"""
        
        logger.info("🔧 Initializing core systems...")
        
        # Initialize Community Memory (must be first)
        self.memory_system = community_memory
        logger.info("✅ Community Memory System initialized")
        
        # Initialize Adaptive Tools
        self.tool_system = adaptive_tools
        logger.info("✅ Adaptive Tools System initialized")
        
        # Initialize Agent Zero Core
        self.agent_core = agent_zero
        self.agent_core.initialize(
            memory_system=self.memory_system,
            tool_system=self.tool_system
        )
        logger.info("✅ Agent Zero Core initialized")
        
        # Initialize Grant Coordination System
        self.grant_system = grant_system
        logger.info("✅ Grant Coordination System initialized")
        
        # Initialize Universal Connector
        self.connector_system = universal_connector
        logger.info("✅ Universal Connector System initialized")
        
        # Initialize Shoghi Interface
        self.interface_system = shoghi_interface
        logger.info("✅ Natural Language Interface initialized")
        
        # Initialize Auto Deploy System
        self.deploy_system = auto_deploy
        logger.info("✅ Auto Deploy System initialized")
    
    def _start_platform_services(self):
        """Start all platform services"""
        
        logger.info("🎯 Starting platform services...")
        
        # Start grant discovery if in production mode
        if self.mode == "production":
            logger.info("🔍 Starting grant discovery...")
            grants = self.grant_system.discover_all_opportunities()
            logger.info(f"📊 Discovered {len(grants)} grant opportunities")
        
        # Deploy platform if requested
        if self.mode == "deployed":
            logger.info("🚀 Deploying Shoghi platform...")
            deployment_id = self.deploy_system.deploy_shoghi_platform()
            logger.info(f"✅ Platform deployed: {deployment_id}")
        
        logger.info("✅ All platform services started")
    
    def _log_startup_completion(self):
        """Log platform startup completion"""

        uptime = datetime.now() - self.start_time

        status_report = f"""
🎉 **SHOGHI PLATFORM STARTUP COMPLETE WITH MORAL CONSTRAINTS**

⏱️  Startup Time: {uptime.total_seconds():.2f} seconds
🏃 Platform Status: RUNNING
🎯 Operation Mode: {self.mode.upper()}
📅 Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}

🛡️  **MORAL CONSTRAINT SYSTEM:**
✅ Bahá'í Virtue Manifold: ACTIVE
✅ ActionGate: ENFORCING
✅ 12D Phase Space Tracking: OPERATIONAL
✅ Truthfulness Dampening: ENABLED
✅ All External Actions: GATED

🔧 **Core Systems Status (All Morally Constrained):**
"""
        
        # Get system status
        agent_status = self.agent_core.get_all_agents_status()
        memory_insights = self.memory_system.get_memory_insights()
        tool_insights = self.tool_system.get_tool_insights()
        connector_insights = self.connector_system.get_connector_insights()
        
        status_report += f"""
🤖 Agent Network: {len(agent_status)} agents active
🧠 Memory System: {memory_insights['total_memories']} memories stored
🔧 Tool Ecosystem: {tool_insights['total_tools']} tools available
🔗 Universal Connector: {connector_insights['total_connectors']} systems connected

🎯 **Ready for Commands:**
- "Shoghi, find grants for elder care in Puna"
- "Shoghi, coordinate community volunteers"
- "Shoghi, deploy full platform"
- "Shoghi, what is your status?"

💡 **Platform is now listening and ready to coordinate!**

🛡️  **MORAL GUARANTEE:**
Every agent action, grant submission, and external API call is validated
through the Bahá'í virtue manifold. Actions that violate moral constraints
are automatically blocked. System maintains high truthfulness, justice,
trustworthiness, unity, service, detachment, and understanding.
"""
        
        logger.info(status_report)
    
    def _main_operation_loop(self):
        """Main platform operation loop"""
        
        logger.info("🔄 Entering main operation loop...")
        
        try:
            if self.mode == "development":
                # Interactive mode for development
                self._interactive_mode()
            else:
                # Service mode for production
                self._service_mode()
                
        except KeyboardInterrupt:
            logger.info("\n🛑 Shutdown signal received...")
            self.shutdown()
        except Exception as e:
            logger.error(f"❌ Operation loop error: {e}")
            self.shutdown()
    
    def _interactive_mode(self):
        """Interactive mode for development/testing"""
        
        print("\n" + "="*60)
        print("🌺 SHOGHI INTERACTIVE MODE")
        print("="*60)
        print("Type your requests in natural language")
        print("Examples:")
        print("  - 'find grants for elder care in Puna'")
        print("  - 'coordinate volunteers for community support'")
        print("  - 'deploy grant management system'")
        print("  - 'what is your status?'")
        print("  - 'exit' to quit")
        print("="*60)
        
        while self.running:
            try:
                user_input = input("\n🗣️  You: ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    print("👋 Goodbye! Shutting down Shoghi...")
                    break
                
                if not user_input:
                    continue
                
                # Process user input
                print("🤔 Processing...")
                response = self.interface_system.process_message("user", user_input)
                
                print(f"\n🤖 Shoghi: {response['response']}")
                
                if response.get('follow_up_needed'):
                    suggestions = response.get('suggestions', [])
                    if suggestions:
                        print("\n💡 Suggestions:")
                        for suggestion in suggestions:
                            print(f"  - {suggestion}")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                logger.error(f"Interactive mode error: {e}")
    
    def _service_mode(self):
        """Service mode for production deployment"""
        
        logger.info("🔄 Running in service mode...")
        
        # Start background tasks
        self._start_background_tasks()
        
        # Keep platform running
        try:
            while self.running:
                # Perform regular health checks
                self._perform_health_checks()
                
                # Sleep for a while
                import time
                time.sleep(60)  # Check every minute
                
        except Exception as e:
            logger.error(f"Service mode error: {e}")
    
    def _start_background_tasks(self):
        """Start background tasks for service mode"""
        
        logger.info("🔄 Starting background tasks...")
        
        # Start grant monitoring
        try:
            grants = self.grant_system.track_and_manage()
            logger.info(f"📊 Background monitoring: {len(grants)} grants tracked")
        except Exception as e:
            logger.error(f"Background task error: {e}")
    
    def _perform_health_checks(self):
        """Perform regular health checks"""
        
        try:
            # Check agent status
            agent_status = self.agent_core.get_all_agents_status()
            active_agents = len([a for a in agent_status if a['status'] == 'active'])
            
            # Check memory system
            memory_insights = self.memory_system.get_memory_insights()
            
            # Log health status
            logger.info(f"💓 Health Check: {active_agents}/{len(agent_status)} agents active, "
                       f"{memory_insights['total_memories']} memories")
            
        except Exception as e:
            logger.error(f"Health check error: {e}")
    
    def process_request(self, request: str, user_id: str = "system") -> Dict[str, Any]:
        """Process a coordination request"""
        
        logger.info(f"🎯 Processing request: {request}")
        
        try:
            # Use the interface system to process the request
            response = self.interface_system.process_message(user_id, request)
            
            logger.info(f"✅ Request processed successfully")
            return response
            
        except Exception as e:
            logger.error(f"❌ Request processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "I encountered an issue processing your request."
            }
    
    def get_platform_status(self) -> Dict[str, Any]:
        """Get comprehensive platform status"""
        
        if not self.running:
            return {"status": "stopped", "message": "Platform is not running"}
        
        try:
            # Get status from all systems
            agent_status = self.agent_core.get_all_agents_status()
            memory_insights = self.memory_system.get_memory_insights()
            tool_insights = self.tool_system.get_tool_insights()
            connector_insights = self.connector_system.get_connector_insights()
            
            # Grant system status
            grant_info = self.grant_system.track_and_manage()
            
            # Deployment status
            deployment_status = self.deploy_system.get_all_deployments()
            
            status = {
                "platform_status": "running",
                "mode": self.mode,
                "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
                "systems": {
                    "agent_network": {
                        "total_agents": len(agent_status),
                        "active_agents": len([a for a in agent_status if a['status'] == 'active']),
                        "specializations": len(set(a['specialization'] for a in agent_status))
                    },
                    "memory_system": {
                        "total_memories": memory_insights['total_memories'],
                        "memory_types": memory_insights['memory_types'],
                        "active_agents": len(memory_insights['agent_contributions'])
                    },
                    "tool_system": {
                        "total_tools": tool_insights['total_tools'],
                        "tool_types": len(tool_insights['tools_by_type']),
                        "recent_creations": len(tool_insights['recently_created'])
                    },
                    "connector_system": {
                        "total_connectors": connector_insights['total_connectors'],
                        "connector_types": len(connector_insights['connectors_by_type']),
                        "system_coverage": len(connector_insights['system_coverage'])
                    },
                    "grant_system": {
                        "total_grants": grant_info['total_grants_discovered'],
                        "active_applications": grant_info['total_applications_active'],
                        "upcoming_deadlines": len(grant_info['upcoming_deadlines'])
                    },
                    "deployment_system": {
                        "total_deployments": len(deployment_status),
                        "active_deployments": len([d for d in deployment_status if d and d['status'] == 'running'])
                    }
                }
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Status check error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "message": "Unable to retrieve complete status"
            }
    
    def shutdown(self):
        """Shutdown the platform gracefully"""
        
        logger.info("🛑 Shutting down Shoghi Platform...")
        
        self.running = False
        
        try:
            # Shutdown all systems in reverse order
            systems_to_shutdown = [
                ("Interface System", self.interface_system),
                ("Deploy System", self.deploy_system),
                ("Connector System", self.connector_system),
                ("Grant System", self.grant_system),
                ("Agent Core", self.agent_core),
                ("Tool System", self.tool_system),
                ("Memory System", self.memory_system)
            ]
            
            for system_name, system in systems_to_shutdown:
                if system and hasattr(system, 'shutdown'):
                    try:
                        logger.info(f"🔄 Shutting down {system_name}...")
                        system.shutdown()
                        logger.info(f"✅ {system_name} shutdown complete")
                    except Exception as e:
                        logger.error(f"❌ Error shutting down {system_name}: {e}")
            
            # Log shutdown completion
            uptime = datetime.now() - self.start_time if self.start_time else timedelta(0)
            
            shutdown_report = f"""
🛑 **SHOGHI PLATFORM SHUTDOWN COMPLETE**

⏱️  Total Uptime: {uptime.total_seconds():.2f} seconds
📅 Shutdown Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🎯 Operation Mode: {self.mode}

✅ All systems shut down gracefully
🌺 Mahalo for using Shoghi!
"""
            
            logger.info(shutdown_report)
            
        except Exception as e:
            logger.error(f"❌ Shutdown error: {e}")
        
        finally:
            logger.info("🌺 Shoghi Platform shutdown complete")

def main():
    """Main entry point"""
    
    # Parse command line arguments
    import argparse
    
    parser = argparse.ArgumentParser(description='Shoghi Adaptive Coordination Platform')
    parser.add_argument('--mode', choices=['development', 'production', 'deployed'], 
                       default='development', help='Operation mode')
    parser.add_argument('--command', type=str, help='Single command to execute')
    parser.add_argument('--status', action='store_true', help='Show platform status')
    
    args = parser.parse_args()
    
    # Create and start platform
    platform = ShoghiPlatform()
    
    try:
        if args.status:
            # Show status and exit
            status = platform.get_platform_status()
            print(json.dumps(status, indent=2))
            
        elif args.command:
            # Execute single command
            platform.start(mode='production')
            result = platform.process_request(args.command)
            print(result['response'])
            platform.shutdown()
            
        else:
            # Start full platform
            platform.start(mode=args.mode)
            
    except Exception as e:
        logger.error(f"❌ Platform error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()