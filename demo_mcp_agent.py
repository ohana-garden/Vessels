#!/usr/bin/env python3
"""
MCP Discovery Agent - Usage Examples

Demonstrates how to use the MCP discovery agent for context-sensitive
server recommendations and automatic catalog updates.
"""

import logging
from mcp_discovery_agent import mcp_agent, discover_and_recommend, auto_discover_and_update

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def example_1_basic_discovery():
    """Example 1: Basic server discovery"""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Server Discovery")
    print("="*60)

    # Discover all available MCP servers
    servers = mcp_agent.discover_servers()

    print(f"\nDiscovered {len(servers)} MCP servers:")
    for server in servers:
        print(f"\n  📦 {server.name}")
        print(f"     Type: {server.server_type.value}")
        print(f"     Description: {server.description}")
        print(f"     Capabilities: {len(server.capabilities)}")
        print(f"     Tags: {', '.join(server.tags[:5])}")


def example_2_context_recommendations():
    """Example 2: Context-sensitive recommendations"""
    print("\n" + "="*60)
    print("EXAMPLE 2: Context-Sensitive Recommendations")
    print("="*60)

    # Different contexts to test
    contexts = [
        "I need to search for grants in Hawaii for elder care programs",
        "Help me query a SQLite database for customer records",
        "I want to read and write files on the local filesystem",
        "Send an email notification to the team",
    ]

    for context in contexts:
        print(f"\n📝 Context: {context}")
        print("-" * 60)

        # Get recommendations
        recommendations = mcp_agent.recommend_for_context(context, max_recommendations=3)

        if recommendations:
            print(f"✅ Found {len(recommendations)} relevant servers:\n")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec.server.name}")
                print(f"     Relevance: {rec.relevance_score:.2f}")
                print(f"     Reason: {rec.reasoning}")
                print(f"     Matching capabilities: {', '.join(rec.matching_capabilities)}")
                if rec.suggested_operations:
                    print(f"     Suggested operations: {', '.join(rec.suggested_operations)}")
                print()
        else:
            print("❌ No relevant servers found\n")


def example_3_one_shot_function():
    """Example 3: One-shot discover and recommend"""
    print("\n" + "="*60)
    print("EXAMPLE 3: One-Shot Function")
    print("="*60)

    # Use convenience function for quick results
    context = "I need to work with a database"
    print(f"\n📝 Context: {context}\n")

    recommendations = discover_and_recommend(context)

    print(f"✅ Found {len(recommendations)} recommendations:")
    for rec in recommendations[:3]:
        print(f"  • {rec.server.name} (relevance: {rec.relevance_score:.2f})")


def example_4_update_connector_catalog():
    """Example 4: Update universal connector catalog"""
    print("\n" + "="*60)
    print("EXAMPLE 4: Update Universal Connector Catalog")
    print("="*60)

    # Discover servers
    servers = mcp_agent.discover_servers()
    print(f"\nDiscovered {len(servers)} servers")

    # Update universal connector with discovered servers
    added = mcp_agent.update_connector_catalog()
    print(f"✅ Added {added} servers to universal connector catalog")

    # Show what's now available in universal connector
    try:
        from universal_connector import universal_connector
        print(f"\nUniversal connector now has {len(universal_connector.connector_specs)} connectors:")
        for name in list(universal_connector.connector_specs.keys())[:10]:
            print(f"  • {name}")
    except ImportError:
        print("  (universal_connector not available for import)")


def example_5_background_discovery():
    """Example 5: Background discovery with auto-updates"""
    print("\n" + "="*60)
    print("EXAMPLE 5: Background Discovery")
    print("="*60)

    print("\nStarting background discovery (every 24 hours)...")
    auto_discover_and_update(interval_hours=24)

    # Check status
    status = mcp_agent.get_discovery_status()
    print("\n📊 Discovery Status:")
    print(f"  Total servers: {status['total_servers']}")
    print(f"  Active servers: {status['active_servers']}")
    print(f"  Background running: {status['background_running']}")
    print(f"  Last discovery: {status['last_discovery']}")

    print("\n  Servers by type:")
    for server_type, count in status['servers_by_type'].items():
        print(f"    • {server_type}: {count}")

    print("\n  Discovery sources:")
    for source in status['discovery_sources']:
        status_icon = "✅" if source['enabled'] else "❌"
        print(f"    {status_icon} {source['name']}")

    # Stop background discovery
    print("\nStopping background discovery...")
    mcp_agent.stop_background_discovery()
    print("✅ Stopped")


def example_6_custom_local_servers():
    """Example 6: Adding custom local servers"""
    print("\n" + "="*60)
    print("EXAMPLE 6: Custom Local Servers")
    print("="*60)

    import json
    import os

    # Create example local configuration
    config_dir = os.path.expanduser("~/.mcp")
    config_path = os.path.join(config_dir, "servers.json")

    example_config = {
        "servers": [
            {
                "id": "my-custom-api",
                "name": "My Custom API",
                "description": "Custom API for internal services",
                "type": "tool_provider",
                "url": "https://api.mycompany.com",
                "version": "1.0.0",
                "capabilities": [
                    {
                        "name": "search_employees",
                        "type": "tool",
                        "description": "Search employee directory",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string"}
                            }
                        },
                        "tags": ["search", "employees", "directory"]
                    }
                ],
                "authentication": {
                    "type": "api_key"
                },
                "metadata": {
                    "category": "internal",
                    "owner": "it-team"
                },
                "tags": ["internal", "employees", "hr"]
            }
        ]
    }

    print(f"\n📝 Example local configuration:")
    print(f"   Path: {config_path}")
    print(f"   Content: {json.dumps(example_config, indent=2)[:300]}...")

    print(f"\n💡 To use local servers:")
    print(f"   1. Create directory: mkdir -p {config_dir}")
    print(f"   2. Create file: {config_path}")
    print(f"   3. Add your server configurations")
    print(f"   4. Run discovery - local servers will be automatically loaded")


def example_7_practical_workflow():
    """Example 7: Practical workflow example"""
    print("\n" + "="*60)
    print("EXAMPLE 7: Practical Workflow")
    print("="*60)

    print("\n🎯 Scenario: Building a grant application assistant\n")

    # Step 1: Discover servers
    print("Step 1: Discover available MCP servers...")
    servers = mcp_agent.discover_servers()
    print(f"  ✅ Found {len(servers)} servers\n")

    # Step 2: Get recommendations for grant search
    print("Step 2: Find servers for grant searching...")
    context = "search for grants and funding opportunities"
    recommendations = mcp_agent.recommend_for_context(context, max_recommendations=3)
    print(f"  ✅ Found {len(recommendations)} relevant servers:\n")
    for rec in recommendations:
        print(f"     • {rec.server.name} (score: {rec.relevance_score:.2f})")
    print()

    # Step 3: Get recommendations for document generation
    print("Step 3: Find servers for document generation...")
    context = "generate and write documents and PDFs"
    recommendations = mcp_agent.recommend_for_context(context, max_recommendations=3)
    print(f"  ✅ Found {len(recommendations)} relevant servers:\n")
    for rec in recommendations:
        print(f"     • {rec.server.name} (score: {rec.relevance_score:.2f})")
    print()

    # Step 4: Update connector catalog
    print("Step 4: Update universal connector catalog...")
    added = mcp_agent.update_connector_catalog()
    print(f"  ✅ Added {added} servers to catalog\n")

    # Step 5: Start background updates
    print("Step 5: Enable automatic updates...")
    auto_discover_and_update(interval_hours=24)
    print("  ✅ Background discovery active\n")

    print("✨ Grant assistant is now ready with dynamic MCP server integration!")

    # Cleanup
    mcp_agent.stop_background_discovery()


def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("MCP DISCOVERY AGENT - DEMONSTRATION")
    print("="*60)

    try:
        example_1_basic_discovery()
        example_2_context_recommendations()
        example_3_one_shot_function()
        example_4_update_connector_catalog()
        example_5_background_discovery()
        example_6_custom_local_servers()
        example_7_practical_workflow()

        print("\n" + "="*60)
        print("✅ All examples completed successfully!")
        print("="*60 + "\n")

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        logger.error(f"Error running examples: {e}", exc_info=True)
    finally:
        # Cleanup
        mcp_agent.stop_background_discovery()


if __name__ == "__main__":
    main()
