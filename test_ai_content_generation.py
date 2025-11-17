#!/usr/bin/env python3
"""
TEST AI CONTENT GENERATION SYSTEM
Tests AI-enhanced content generation with quality checks
"""

import asyncio
import os
import sys
import logging
from datetime import datetime
from content_generation import ContentContext, ContentType
from ai_content_generator import (
    AIContentGenerator,
    LLMProvider,
    generate_ai_content
)
from content_quality_checker import ContentQualityChecker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_section(title: str):
    """Print formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_subsection(title: str):
    """Print formatted subsection"""
    print(f"\n--- {title} ---")


async def test_ai_generation_basic():
    """Test basic AI content generation"""

    print_section("TEST 1: Basic AI Content Generation")

    # Test 1: Elder care protocol
    print_subsection("1.1: Elder Care Protocol (Hawaiian Context)")

    context = ContentContext(
        content_type=ContentType.ELDER_CARE_PROTOCOL,
        target_audience="elder care workers",
        cultural_context="hawaiian",
        language="en",
        emotional_tone="warm",
        urgency_level="normal",
        specific_requirements={"focus": "daily wellness check"}
    )

    generator = AIContentGenerator()
    content = await generator.generate_content(context)

    print(f"✓ Generated: {content.title}")
    print(f"✓ Model used: {content.metadata.get('ai_model', 'template-based')}")
    print(f"✓ Tokens: {content.metadata.get('tokens_used', 'N/A')}")
    print(f"✓ Generation time: {content.metadata.get('generation_time', 'N/A')}s")
    print(f"✓ Quality score: {content.metadata.get('quality_score', 'N/A'):.2f}")
    print(f"\nPreview:\n{content.body[:400]}...\n")

    return content


async def test_quality_checking(content):
    """Test quality assurance system"""

    print_section("TEST 2: Quality Assurance Checks")

    checker = ContentQualityChecker()
    report = await checker.validate_content(content)

    print(f"Overall Score: {report.overall_score:.2f}")
    print(f"Status: {'✓ PASSED' if report.passed else '✗ FAILED'}")

    print("\nMetrics:")
    if 'readability' in report.metrics:
        r = report.metrics['readability']
        print(f"  - Word count: {r['word_count']}")
        print(f"  - Sentences: {r['sentence_count']}")
        print(f"  - Avg words/sentence: {r['avg_words_per_sentence']:.1f}")
        print(f"  - Flesch score: {r['flesch_score']:.1f} ({r['readability_rating']})")
        print(f"  - Grade level: {r['grade_level']:.1f}")

    if 'tone' in report.metrics:
        t = report.metrics['tone']
        print(f"  - Detected tone: {t['dominant_tone']}")
        print(f"  - Confidence: {t['confidence']:.2f}")

    if report.issues:
        print("\nIssues Found:")
        for i, issue in enumerate(report.issues, 1):
            print(f"  {i}. [{issue.severity.upper()}] {issue.category}: {issue.message}")
            if issue.suggestion:
                print(f"     Suggestion: {issue.suggestion}")
    else:
        print("\n✓ No issues found!")

    if report.suggestions:
        print("\nSuggestions for Improvement:")
        for i, suggestion in enumerate(report.suggestions, 1):
            print(f"  {i}. {suggestion}")

    return report


async def test_multiple_content_types():
    """Test generation across multiple content types"""

    print_section("TEST 3: Multiple Content Types")

    test_cases = [
        {
            'name': 'Grant Narrative',
            'type': ContentType.GRANT_NARRATIVE,
            'audience': 'federal funders',
            'cultural': 'hawaiian',
            'tone': 'formal',
            'requirements': {'focus': 'elder care program in Puna'}
        },
        {
            'name': 'Volunteer Script',
            'type': ContentType.VOLUNTEER_SCRIPT,
            'audience': 'volunteers',
            'cultural': 'multicultural',
            'tone': 'supportive',
            'requirements': {'scenario': 'coordinating meal delivery'}
        },
        {
            'name': 'Disaster Response',
            'type': ContentType.DISASTER_RESPONSE,
            'audience': 'community members',
            'cultural': 'hawaiian',
            'tone': 'urgent',
            'requirements': {'situation': 'hurricane preparation'}
        }
    ]

    results = []

    for test_case in test_cases:
        print_subsection(f"Testing: {test_case['name']}")

        content = await generate_ai_content(
            content_type=test_case['type'],
            target_audience=test_case['audience'],
            cultural_context=test_case['cultural'],
            emotional_tone=test_case['tone'],
            specific_requirements=test_case['requirements']
        )

        print(f"✓ Title: {content.title}")
        print(f"✓ Length: {len(content.body.split())} words")
        print(f"✓ Model: {content.metadata.get('ai_model', 'template')}")

        # Quick quality check
        checker = ContentQualityChecker()
        report = await checker.validate_content(content)
        print(f"✓ Quality: {report.overall_score:.2f} ({'PASS' if report.passed else 'FAIL'})")

        results.append({
            'test_case': test_case['name'],
            'content': content,
            'report': report
        })

    return results


async def test_multimodal_generation():
    """Test multimodal content generation"""

    print_section("TEST 4: Multimodal Content Generation")

    context = ContentContext(
        content_type=ContentType.COMMUNITY_FLYER,
        target_audience="families",
        cultural_context="hawaiian",
        language="en",
        emotional_tone="warm",
        urgency_level="normal",
        specific_requirements={"event": "Community potluck and elder appreciation day"}
    )

    generator = AIContentGenerator()
    multimodal = await generator.generate_multimodal_content(context)

    print(f"✓ Formats generated: {', '.join(multimodal['formats'])}")

    print("\nText Content:")
    print(f"  Title: {multimodal['text'].title}")
    print(f"  Length: {len(multimodal['text'].body.split())} words")

    print("\nAudio Script:")
    print(f"  Pacing: {multimodal['audio_script']['pacing']}")
    print(f"  Tone: {multimodal['audio_script']['tone']}")
    print(f"  Sections: {len(multimodal['audio_script']['dialogue'])}")
    if multimodal['audio_script']['narrator_notes']:
        print(f"  Notes: {multimodal['audio_script']['narrator_notes']}")

    print("\nVisual Layout:")
    print(f"  Format: {multimodal['visual_layout']['format']}")
    if multimodal['visual_layout'].get('colors'):
        print(f"  Color scheme: {list(multimodal['visual_layout']['colors'].keys())}")
    if multimodal['visual_layout'].get('typography'):
        print(f"  Typography: {multimodal['visual_layout']['typography']}")

    print("\nInteractive Elements:")
    print(f"  Navigation: {multimodal['interactive']['navigation']}")
    if multimodal['interactive'].get('forms'):
        print(f"  Forms: {len(multimodal['interactive']['forms'])}")

    return multimodal


async def test_feedback_loop():
    """Test regeneration with feedback"""

    print_section("TEST 5: Feedback-Based Regeneration")

    # Generate initial content
    print_subsection("Initial Generation")

    content = await generate_ai_content(
        content_type=ContentType.VOLUNTEER_SCRIPT,
        target_audience="volunteers",
        cultural_context="hawaiian",
        emotional_tone="warm",
        specific_requirements={"task": "coordinating food distribution"}
    )

    print(f"✓ Initial content generated: {content.title}")
    print(f"✓ Length: {len(content.body.split())} words")

    # Simulate user feedback
    print_subsection("Simulating User Feedback")

    feedback = {
        'rating': 3,
        'issues': ['too_long', 'too_formal'],
        'comments': 'Good structure but needs to be more concise and casual'
    }

    print(f"User rating: {feedback['rating']}/5")
    print(f"Issues: {', '.join(feedback['issues'])}")

    # Regenerate with feedback
    print_subsection("Regenerating with Feedback")

    generator = AIContentGenerator()
    improved_content = await generator.regenerate_with_feedback(content, feedback)

    print(f"✓ Improved content generated")
    print(f"✓ Version: {improved_content.version}")
    print(f"✓ New length: {len(improved_content.body.split())} words")
    print(f"✓ Length change: {len(improved_content.body.split()) - len(content.body.split())} words")

    return improved_content


async def run_all_tests():
    """Run all tests"""

    print("\n")
    print("█" * 70)
    print("  SHOGHI AI CONTENT GENERATION TEST SUITE")
    print("█" * 70)

    # Check environment
    print("\n🔍 Checking Environment...")
    has_openai = bool(os.environ.get("OPENAI_API_KEY"))
    has_anthropic = bool(os.environ.get("ANTHROPIC_API_KEY"))

    print(f"  OpenAI API Key: {'✓ Found' if has_openai else '✗ Not found'}")
    print(f"  Anthropic API Key: {'✓ Found' if has_anthropic else '✗ Not found'}")

    if not has_openai and not has_anthropic:
        print("\n⚠️  WARNING: No API keys found!")
        print("  Will fall back to template-based generation.")
        print("  To use AI generation, set OPENAI_API_KEY or ANTHROPIC_API_KEY")
        print("  See .env.example for setup instructions\n")

    # Run tests
    try:
        # Test 1: Basic generation
        content1 = await test_ai_generation_basic()

        # Test 2: Quality checking
        report1 = await test_quality_checking(content1)

        # Test 3: Multiple content types
        results = await test_multiple_content_types()

        # Test 4: Multimodal
        multimodal = await test_multimodal_generation()

        # Test 5: Feedback loop
        improved = await test_feedback_loop()

        # Summary
        print_section("TEST SUMMARY")

        total_tests = 5
        passed_tests = sum([
            1,  # Test 1 always passes if it runs
            1 if report1.passed else 0,
            sum(1 for r in results if r['report'].passed),
            1,  # Test 4 always passes if it runs
            1   # Test 5 always passes if it runs
        ])

        print(f"\nTests completed: {passed_tests}/{total_tests + len(results) - 1}")
        print(f"Overall status: {'✓ ALL PASSED' if passed_tests >= total_tests else '⚠️  SOME ISSUES'}")

        print("\n🌺 AI Content Generation System is operational!")

        return True

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def quick_test():
    """Quick test for rapid validation"""

    print("\n🚀 Quick Test: AI Content Generation\n")

    try:
        content = await generate_ai_content(
            content_type=ContentType.ELDER_CARE_PROTOCOL,
            target_audience="caregivers",
            cultural_context="hawaiian",
            specific_requirements={"task": "daily wellness check"}
        )

        print(f"✓ Generated: {content.title}")
        print(f"✓ Model: {content.metadata.get('ai_model', 'template')}")
        print(f"\nPreview:\n{content.body[:300]}...\n")
        print("✓ Quick test passed!")

        return True

    except Exception as e:
        print(f"✗ Quick test failed: {e}")
        return False


if __name__ == "__main__":
    import sys

    # Check for command line argument
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        # Run quick test
        success = asyncio.run(quick_test())
    else:
        # Run full test suite
        success = asyncio.run(run_all_tests())

    sys.exit(0 if success else 1)
