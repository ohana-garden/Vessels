#!/usr/bin/env python3
"""
SHOGHI - Adaptive Coordination Platform
Main entry point for the complete Shoghi system
"""

import asyncio
import json
import logging
import sys
import textwrap
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, TextIO

# Import all core modules
from agent_zero_core import agent_zero, AgentZeroCore
from dynamic_agent_factory import agent_factory, process_community_request
from community_memory import community_memory, CommunityMemory
from grant_coordination_system import grant_system, GrantCoordinationSystem
from adaptive_tools import adaptive_tools, AdaptiveTools
from shoghi_interface import shoghi_interface, ShoghiInterface
from auto_deploy import auto_deploy, deploy_shoghi_platform
from universal_connector import universal_connector, UniversalConnector

logger = logging.getLogger(__name__)


def configure_logging(
    level: int = logging.INFO,
    stream: Optional[TextIO] = None,
    log_file: Optional[str] = "shoghi.log"
) -> None:
    """Configure application logging once for CLI entrypoints.

    The platform previously configured logging at import time which caused
    duplicate handlers when the module was re-imported (common during tests).
    This helper applies the desired configuration only when no handlers are
    present so embedding applications can supply their own logging strategy.
    """

    root_logger = logging.getLogger()
    if root_logger.handlers:
        return

    resolved_stream = stream or sys.stdout
    handlers: List[logging.Handler] = [logging.StreamHandler(resolved_stream)]

    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
    )


class InteractiveConsole:
    """Console rendering helper for interactive development sessions."""

    def __init__(
        self,
        input_func: Optional[Callable[[str], str]] = None,
        output_stream: Optional[TextIO] = None,
    ) -> None:
        self._input = input_func or input
        self._output = output_stream or sys.stdout

    def render_banner(self) -> None:
        banner = textwrap.dedent(
            """
            ============================================================
            🌺 SHOGHI INTERACTIVE MODE
            ============================================================
            Type your requests in natural language
            Examples:
              - 'find grants for elder care in Puna'
              - 'coordinate volunteers for community support'
              - 'deploy grant management system'
              - 'what is your status?'
              - 'exit' to quit
            ============================================================
            """
        ).strip("\n")
        print("\n" + banner, file=self._output)

    def prompt_user(self) -> str:
        return self._input("\n🗣️  You: ").strip()

    def notify_processing(self) -> None:
        print("🤔 Processing...", file=self._output)

    def display_response(self, message: str) -> None:
        print(f"\n🤖 Shoghi: {message}", file=self._output)

    def display_suggestions(self, suggestions: List[str]) -> None:
        if not suggestions:
            return

        print("\n💡 Suggestions:", file=self._output)
        for suggestion in suggestions:
            print(f"  - {suggestion}", file=self._output)

    def display_error(self, message: str) -> None:
        print(f"❌ Error: {message}", file=self._output)

    def say_goodbye(self) -> None:
        print("👋 Goodbye! Shutting down Shoghi...", file=self._output)

class ShoghiPlatform:
    """Main Shoghi adaptive coordination platform"""

    def __init__(self, console: Optional[InteractiveConsole] = None):
        self.running = False
        self.start_time = None
        self.mode = "development"  # development, production, deployed

        # Core system components
        self.agent_core = None
        self.memory_system = None
        self.tool_system = None
        self.grant_system = None
        self.connector_system = None
        self.interface_system = None
        self.deploy_system = None

        self.console = console or InteractiveConsole()

        logger.info("🌺 Shoghi Platform initializing...")
    
    def start(self, mode: str = "development", run_loop: bool = True):
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
            
            # Enter main operation loop when requested
            if run_loop:
                self._main_operation_loop()
            
        except Exception as e:
            logger.error(f"❌ Platform startup failed: {e}")
            self.shutdown()
            raise
    
    def _initialize_core_systems(self):
        """Initialize all core system components"""
        
        logger.info("🔧 Initializing core systems...")
        
        # Initialize Community Memory (must be first)
        # TODO: Lazy-load large subsystems (e.g., memory system) only when
        # explicitly used to shorten cold-start time for CLI status queries.
        self.memory_system = community_memory
        logger.info("✅ Community Memory System initialized")
        
        # Initialize Adaptive Tools
        # TODO: Adaptive tools initialization could pre-compute capability
        # indexes asynchronously so startup remains responsive.
        self.tool_system = adaptive_tools
        logger.info("✅ Adaptive Tools System initialized")
        
        # Initialize Agent Zero Core
        # TODO: Agent core initialization currently performs synchronous
        # bootstrap; consider deferring heavy network calls to background tasks.
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
            # NOTE: discover_all_opportunities() appears to do a full crawl.
            # Introducing incremental sync with persisted checkpoints would
            # avoid redundant requests and lower latency here.
            grants = self.grant_system.discover_all_opportunities()
            logger.info(f"📊 Discovered {len(grants)} grant opportunities")
        
        # Deploy platform if requested
        if self.mode == "deployed":
            logger.info("🚀 Deploying Shoghi platform...")
            # TODO: Deployment currently blocks the main thread; offload to an
            # executor or async worker so startup logging continues promptly.
            deployment_id = self.deploy_system.deploy_shoghi_platform()
            logger.info(f"✅ Platform deployed: {deployment_id}")
        
        logger.info("✅ All platform services started")
    
    def _log_startup_completion(self):
        """Log platform startup completion"""
        
        uptime = datetime.now() - self.start_time
        
        status_report = f"""
🎉 **SHOGHI PLATFORM STARTUP COMPLETE**

⏱️  Startup Time: {uptime.total_seconds():.2f} seconds
🏃 Platform Status: RUNNING
🎯 Operation Mode: {self.mode.upper()}
📅 Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}

🔧 **Core Systems Status:**
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

        self.console.render_banner()

        while self.running:
            try:
                user_input = self.console.prompt_user()

                if user_input.lower() in ['exit', 'quit', 'bye']:
                    self.console.say_goodbye()
                    break

                if not user_input:
                    continue

                # Process user input
                self.console.notify_processing()
                response = self.interface_system.process_message("user", user_input)

                self.console.display_response(response['response'])

                if response.get('follow_up_needed'):
                    suggestions = response.get('suggestions', [])
                    self.console.display_suggestions(suggestions)

            except KeyboardInterrupt:
                break
            except Exception as e:
                self.console.display_error(str(e))
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
            # NOTE: track_and_manage() is invoked every loop; cache results or
            # emit only deltas to avoid expensive recomputation and logging.
            grants = self.grant_system.track_and_manage()
            logger.info(f"📊 Background monitoring: {len(grants)} grants tracked")
        except Exception as e:
            logger.error(f"Background task error: {e}")
    
    def _perform_health_checks(self):
        """Perform regular health checks"""
        
        try:
            # Check agent status
            # TODO: get_all_agents_status() can be costly; consider batching or
            # sampling agents during frequent health checks to minimize load.
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
            # NOTE: Re-running track_and_manage() here duplicates background
            # work; reuse cached metrics gathered by background monitors.
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
                        "active_agents": len([a for a in agent_status if a.get('status') == 'active']),
                        "specializations": len(set(a.get('specialization') for a in agent_status if a.get('specialization')))
                    },
                    "memory_system": {
                        "total_memories": memory_insights.get('total_memories', 0),
                        "memory_types": memory_insights.get('memory_types', {}),
                        "active_agents": len(memory_insights.get('agent_contributions', {}))
                    },
                    "tool_system": {
                        "total_tools": tool_insights.get('total_tools', 0),
                        "tool_types": len(tool_insights.get('tools_by_type', {})),
                        "recent_creations": len(tool_insights.get('recently_created', []))
                    },
                    "connector_system": {
                        "total_connectors": connector_insights.get('total_connectors', 0),
                        "connector_types": len(connector_insights.get('connectors_by_type', {})),
                        "active_connectors": len(connector_insights.get('recently_used', []))
                    },
                    "grant_system": {
                        "total_grants": grant_info.get('total_grants_discovered', 0),
                        "active_applications": grant_info.get('total_applications_active', 0),
                        "upcoming_deadlines": len(grant_info.get('upcoming_deadlines', []))
                    },
                    "deployment_system": {
                        "total_deployments": len(deployment_status),
                        "active_deployments": len([d for d in deployment_status if d and d.get('status') == 'running'])
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

    configure_logging()

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
            # Start platform components long enough to collect status
            platform.start(mode=args.mode, run_loop=False)
            status = platform.get_platform_status()
            print(json.dumps(status, indent=2))
            platform.shutdown()

        elif args.command:
            # Execute single command
            platform.start(mode='production', run_loop=False)
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
