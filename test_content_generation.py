#!/usr/bin/env python3
"""Focused tests for contextual content generation."""

import asyncio

from content_generation import ContentContext, ContentType, content_generator


def _run(coro):
    """Execute an async coroutine within a synchronous test."""
    return asyncio.run(coro)


def test_elder_care_protocol_uses_hawaiian_context():
    """Ensure Hawaiian cultural context is woven into elder care guidance."""
    context = ContentContext(
        content_type=ContentType.ELDER_CARE_PROTOCOL,
        target_audience="elder care workers",
        cultural_context="hawaiian",
        language="en",
        emotional_tone="warm",
        urgency_level="normal",
        specific_requirements={"simple_language": True},
    )

    content = _run(content_generator.generate_content(context))

    assert content.title
    assert "hawaiian context" in content.body.lower()
    assert content.metadata.get("cultural_context") == "hawaiian"


def test_disaster_response_marks_critical_urgency():
    """Disaster response content should surface critical urgency metadata."""
    context = ContentContext(
        content_type=ContentType.DISASTER_RESPONSE,
        target_audience="community members",
        cultural_context="multicultural",
        language="en",
        emotional_tone="urgent",
        urgency_level="critical",
        specific_requirements={},
    )

    content = _run(content_generator.generate_content(context))

    assert content.metadata.get("urgency") == "critical"
    assert "immediate" in content.body.lower()


def test_grant_narrative_produces_structured_sections():
    """Grant narratives should emit multiple structured sections."""
    context = ContentContext(
        content_type=ContentType.GRANT_NARRATIVE,
        target_audience="federal funders",
        cultural_context="hawaiian",
        language="en",
        emotional_tone="formal",
        urgency_level="normal",
        specific_requirements={
            "include_statistics": True,
            "include_success_stories": True,
        },
    )

    content = _run(content_generator.generate_content(context))

    sections = [segment for segment in content.body.split("\n\n") if segment.strip()]

    assert len(sections) >= 2
    assert content.metadata.get("cultural_context") == "hawaiian"
    emphasis = content.metadata.get("emphasis_points", [])
    assert "community_need" in emphasis
    assert "cultural_alignment" in emphasis


def test_volunteer_script_mentions_requested_culture():
    """Volunteer scripts should acknowledge the requested cultural context."""
    context = ContentContext(
        content_type=ContentType.VOLUNTEER_SCRIPT,
        target_audience="volunteers",
        cultural_context="japanese",
        language="en",
        emotional_tone="supportive",
        urgency_level="normal",
        specific_requirements={},
    )

    content = _run(content_generator.generate_content(context))

    assert "japanese context" in content.body.lower()
    assert "respect" in content.metadata.get("emphasis_points", [])


def test_multimodal_content_includes_all_channels():
    """Multimodal output should include layout and audio script artifacts."""
    context = ContentContext(
        content_type=ContentType.COMMUNITY_FLYER,
        target_audience="families",
        cultural_context="hawaiian",
        language="en",
        emotional_tone="warm",
        urgency_level="normal",
        specific_requirements={},
    )

    multimodal = _run(content_generator.generate_multimodal_content(context))

    assert "formats" in multimodal
    assert "visual_layout" in multimodal
    assert multimodal["visual_layout"].get("format")
    assert "audio_script" in multimodal
    assert len(multimodal["audio_script"].get("dialogue", [])) >= 1


if __name__ == "__main__":
    for test in [
        test_elder_care_protocol_uses_hawaiian_context,
        test_disaster_response_marks_critical_urgency,
        test_grant_narrative_produces_structured_sections,
        test_volunteer_script_mentions_requested_culture,
        test_multimodal_content_includes_all_channels,
    ]:
        test()
    print("All contextual content generation tests passed.")
