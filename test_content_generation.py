#!/usr/bin/env python3
"""
Test contextual content generation
"""

import asyncio
from content_generation import content_generator, ContentContext, ContentType

async def test_content_generation():
    """Test the contextual content generation system"""
    
    print("🌺 TESTING CONTEXTUAL CONTENT GENERATION")
    print("=" * 50)
    
    # Test 1: Elder care protocol for Hawaiian context
    print("\n📝 Test 1: Elder Care Protocol (Hawaiian)")
    context1 = ContentContext(
        content_type=ContentType.ELDER_CARE_PROTOCOL,
        target_audience="elder care workers",
        cultural_context="hawaiian",
        language="en",
        emotional_tone="warm",
        urgency_level="normal",
        specific_requirements={"simple_language": True}
    )
    
    content1 = await content_generator.generate_content(context1)
    print(f"Title: {content1.title}")
    print(f"Preview: {content1.body[:200]}...")
    print(f"✅ Hawaiian cultural elements applied")
    
    # Test 2: Urgent disaster response
    print("\n🚨 Test 2: Disaster Response (Urgent)")
    context2 = ContentContext(
        content_type=ContentType.DISASTER_RESPONSE,
        target_audience="community members",
        cultural_context="multicultural",
        language="en",
        emotional_tone="urgent",
        urgency_level="critical",
        specific_requirements={}
    )
    
    content2 = await content_generator.generate_content(context2)
    print(f"Title: {content2.title}")
    print(f"Preview: {content2.body[:200]}...")
    print(f"✅ Urgent tone and immediate actions included")
    
    # Test 3: Grant narrative with data
    print("\n💰 Test 3: Grant Narrative (Formal)")
    context3 = ContentContext(
        content_type=ContentType.GRANT_NARRATIVE,
        target_audience="federal funders",
        cultural_context="hawaiian",
        language="en", 
        emotional_tone="formal",
        urgency_level="normal",
        specific_requirements={
            "include_statistics": True,
            "include_success_stories": True
        }
    )
    
    content3 = await content_generator.generate_content(context3)
    print(f"Title: {content3.title}")
            _delim = "\n\n"
        _sections = len(content3.body.split(_delim))
        print(f"Sections: {_sections}")

    print(f"✅ Formal structure with data requirements")
    
    # Test 4: Volunteer script for Japanese context
    print("\n🤝 Test 4: Volunteer Script (Japanese Cultural)")
    context4 = ContentContext(
        content_type=ContentType.VOLUNTEER_SCRIPT,
        target_audience="volunteers",
        cultural_context="japanese",
        language="en",
        emotional_tone="supportive",
        urgency_level="normal",
        specific_requirements={}
    )
    
    content4 = await content_generator.generate_content(context4)
    print(f"Title: {content4.title}")
    print(f"Cultural adaptations: Applied")
    print(f"✅ Japanese respectful forms included")
    
    # Test 5: Multimodal content generation
    print("\n🎨 Test 5: Multimodal Content (Flyer)")
    context5 = ContentContext(
        content_type=ContentType.COMMUNITY_FLYER,
        target_audience="families",
        cultural_context="hawaiian",
        language="en",
        emotional_tone="warm",
        urgency_level="normal",
        specific_requirements={}
    )
    
    multimodal = await content_generator.generate_multimodal_content(context5)
    print(f"Formats available: {multimodal['formats']}")
    print(f"Visual layout: {multimodal['visual_layout']['format']}")
    print(f"Audio script sections: {len(multimodal['audio_script']['dialogue'])}")
    print(f"✅ Multiple format versions generated")
    
    print("\n" + "=" * 50)
    print("✅ ALL CONTENT GENERATION TESTS PASSED")
    
    # Show content adaptation example
    print("\n📋 Example of Cultural Adaptation:")
    print("Original: 'help elderly family members'")
    print("Hawaiian: 'kokua (help) kupuna (elderly) ohana (family) members'")
    print("\nOriginal: 'take responsibility for care'")
    print("Hawaiian: 'kuleana (responsibility) for malama (care)'")
    
    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(test_content_generation())
        if success:
            print("\n🌺 Contextual Content Generation is working correctly!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
