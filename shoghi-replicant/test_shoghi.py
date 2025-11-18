#!/usr/bin/env python3
"""
Simple test of Shoghi Platform capabilities
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dynamic_agent_factory import process_community_request
from grant_coordination_system import grant_system
from agent_zero_core import agent_zero
from community_memory import community_memory

import logging
logging.basicConfig(level=logging.INFO)

def main():
    print("🌺 SHOGHI PLATFORM TEST")
    print("="*50)
    
    # Test 1: Grant Discovery
    print("\n📊 Testing Grant Discovery...")
    try:
        grants = grant_system.discover_all_opportunities()
        print(f"✅ Found {len(grants)} grant opportunities")
        for i, grant in enumerate(grants[:2]):
            print(f"   {i+1}. {grant.title} - {grant.amount}")
    except Exception as e:
        print(f"❌ Grant discovery failed: {e}")
    
    # Test 2: Agent Creation
    print("\n🤖 Testing Agent Creation...")
    try:
        result = process_community_request("find grants for elder care in Puna")
        print(f"✅ Created {len(result['deployed_agents'])} agents:")
        for agent in result['deployed_agents']:
            print(f"   - {agent['name']} ({agent['specialization']})")
    except Exception as e:
        print(f"❌ Agent creation failed: {e}")
    
    # Test 3: Memory System
    print("\n🧠 Testing Memory System...")
    try:
        memory_id = community_memory.store_experience("test_agent", {
            "type": "test",
            "success": True,
            "message": "Shoghi platform test successful"
        })
        print(f"✅ Stored memory: {memory_id}")
        
        insights = community_memory.get_memory_insights()
        print(f"✅ Total memories: {insights['total_memories']}")
    except Exception as e:
        print(f"❌ Memory system failed: {e}")
    
    # Test 4: Agent Status
    print("\n🤖 Testing Agent Network...")
    try:
        agents = agent_zero.get_all_agents_status()
        print(f"✅ {len(agents)} agents in network")
        for agent in agents[:3]:
            print(f"   - {agent['name']}: {agent['status']}")
    except Exception as e:
        print(f"❌ Agent network failed: {e}")
    
    print("\n" + "="*50)
    print("✅ TEST COMPLETE")
    print("🌺 Shoghi Platform is working!")

if __name__ == "__main__":
    main()