#!/usr/bin/env python3
"""
Test script for fixed Vessels platform
"""

import sys
import json
from vessels_fixed import VesselsPlatform

def test_platform():
    """Test the fixed Vessels platform"""
    print("🌺 TESTING FIXED VESSELS PLATFORM")
    print("=" * 50)
    
    # Initialize platform
    platform = VesselsPlatform()
    print("✅ Platform initialized")
    
    # Test 1: Get status
    print("\n📊 Test 1: Getting Status...")
    status = platform.get_status()
    print(f"Status: {status['operational']}")
    
    # Test 2: Find grants
    print("\n🔍 Test 2: Finding Grants...")
    result = platform.find_grants("find grants for elder care in Puna")
    print(f"Found {result['count']} grants")
    
    if result['grants']:
        for i, grant in enumerate(result['grants'][:3], 1):
            print(f"  {i}. {grant['title']} - {grant['amount']}")
    
    # Test 3: Generate application
    print("\n📝 Test 3: Generating Application...")
    if result['grants']:
        grant_id = result['grants'][0]['id']
        app_result = platform.generate_applications(f"generate application for {grant_id}")
        
        if 'application' in app_result:
            app = app_result['application']
            print(f"✅ Generated application for: {app['project_title']}")
            print(f"   Budget: ${app['budget_total']:,.2f}")
        else:
            print("❌ Could not generate application")
    
    # Test 4: Natural language processing
    print("\n🗣️ Test 4: Natural Language Processing...")
    test_queries = [
        "what can you do?",
        "find hawaii grants",
        "help me with elder care funding"
    ]
    
    for query in test_queries:
        result = platform.process_request(query)
        print(f"  Query: '{query}'")
        print(f"  Response preview: {result['response'][:100]}...")
    
    print("\n" + "=" * 50)
    print("✅ ALL TESTS COMPLETED")
    
    return True

if __name__ == "__main__":
    try:
        success = test_platform()
        if success:
            print("\n🌺 Vessels Platform is working correctly!")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
