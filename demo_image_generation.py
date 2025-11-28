#!/usr/bin/env python3
"""
Demo: Entity Extraction → Image Prompt → NanoBanana Image Generation

This script demonstrates the complete flow:
1. User sends message in conversation
2. Entities are extracted from the message
3. Entities are categorized (places, people, objects, concepts)
4. Image prompt is generated from entities
5. NanoBanana API generates an image
6. Image URL is returned for display

Run: python demo_image_generation.py

Requirements:
- NANOBANANA_API_KEY env var (or edit API_KEY below)
- requests library: pip install requests
"""

import os
import sys
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("ImageDemo")

# API Key - set via env or edit here
API_KEY = os.getenv("NANOBANANA_API_KEY", "734e2ae0b4ce8ff06d5ccfed5d9deca4")


def demo_prompt_generation():
    """Step 1-4: Generate image prompts from conversation."""
    from vessels.memory import ConversationStore, ConversationType, SpeakerType

    print("\n" + "="*70)
    print("STEP 1-4: Entity Extraction → Image Prompt Generation")
    print("="*70)

    store = ConversationStore(enable_entity_extraction=False)

    # Start conversation
    conv = store.start_conversation(
        conversation_type=ConversationType.USER_VESSEL,
        participant_ids=['demo-user', 'demo-vessel'],
        user_id='demo-user',
        vessel_id='demo-vessel',
        topic='Community garden planning',
    )

    # Test messages that generate rich prompts
    test_messages = [
        {
            "message": "I want to create a taro garden in Waipio Valley where kupuna can teach keiki traditional farming.",
            "entities": ["taro garden", "Waipio Valley", "kupuna", "keiki", "traditional farming"],
        },
        {
            "message": "Our ohana is organizing a community meal at the Kailua beach park to celebrate the harvest.",
            "entities": ["ohana", "community meal", "Kailua beach park", "harvest celebration"],
        },
        {
            "message": "The elders gather at the community center every morning to share stories and weave lauhala.",
            "entities": ["elders", "community center", "morning gathering", "storytelling", "lauhala weaving"],
        },
    ]

    prompts = []

    for i, test in enumerate(test_messages, 1):
        print(f"\n--- Message {i} ---")
        print(f"USER: \"{test['message']}\"")

        turn = store.record_complete_turn(
            conversation_id=conv.conversation_id,
            speaker_id='demo-user',
            speaker_type=SpeakerType.USER,
            message=test['message'],
            response="[Demo response]",
            entities=test['entities'],
        )

        prompt_data = store.generate_image_prompt(turn, conv)
        prompts.append(prompt_data)

        print(f"\nENTITIES: {', '.join(prompt_data['entities_used'])}")
        print(f"\nIMAGE PROMPT:")
        print(f"  \"{prompt_data['prompt']}\"")

    return prompts


def demo_image_generation(prompts):
    """Step 5-6: Generate images via NanoBanana API."""
    print("\n" + "="*70)
    print("STEP 5-6: NanoBanana Image Generation")
    print("="*70)

    from vessels.services import get_nanobanana_client, ImageStyle, AspectRatio

    # Initialize client
    client = get_nanobanana_client(api_key=API_KEY)

    if not client.api_key:
        print("\nERROR: No API key configured!")
        print("Set NANOBANANA_API_KEY env var or edit API_KEY in this script.")
        return []

    print(f"\nAPI Key: {client.api_key[:8]}...{client.api_key[-4:]}")
    print(f"Base URL: {client.base_url}")
    print(f"Endpoint: {client.GENERATE_ENDPOINT}")

    results = []

    for i, prompt_data in enumerate(prompts, 1):
        print(f"\n--- Generating Image {i} ---")
        print(f"Prompt: \"{prompt_data['prompt'][:60]}...\"")

        # Generate image (mobile-optimized portrait)
        images = client.generate_image(
            prompt=prompt_data['prompt'],
            style=ImageStyle.WARM_HAWAIIAN,
            aspect_ratio=AspectRatio.PORTRAIT,  # 9:16 for smartphones
        )

        if images:
            for img in images:
                print(f"\nSUCCESS!")
                if img.url:
                    print(f"  Image URL: {img.url}")
                if img.revised_prompt:
                    print(f"  Revised prompt: {img.revised_prompt[:100]}...")
                if img.metadata:
                    print(f"  Model: {img.metadata.get('model', 'N/A')}")
                results.append(img)
        else:
            print(f"\nFailed to generate image (check logs for details)")

    return results


def demo_via_agent_zero():
    """Alternative: Generate via Agent Zero (recommended approach)."""
    print("\n" + "="*70)
    print("ALTERNATIVE: Generation via Agent Zero")
    print("="*70)

    try:
        from agent_zero_core import agent_zero

        print("\nUsing agent_zero.generate_image()...")

        # Method 1: From a raw message
        result = agent_zero.generate_image(
            message="Kupuna teaching keiki to plant taro in Waipio Valley",
            style="warm, Hawaiian, community-focused",
            aspect_ratio="16:9",
            api_key=API_KEY,
        )

        if result.get("success"):
            print(f"\nSUCCESS!")
            for img in result.get("images", []):
                print(f"  URL: {img.get('url', 'N/A')}")
        else:
            print(f"\nError: {result.get('error', 'Unknown')}")

        return result

    except Exception as e:
        print(f"\nAgent Zero not available: {e}")
        return None


def main():
    """Run the full demo."""
    print("\n" + "="*70)
    print("VESSELS IMAGE GENERATION DEMO")
    print("Entity Extraction → Image Prompt → NanoBanana → Images")
    print("="*70)

    # Step 1-4: Generate prompts from conversations
    prompts = demo_prompt_generation()

    # Step 5-6: Generate images (if API key available)
    if API_KEY:
        print("\n" + "-"*70)
        print("Attempting to generate images via NanoBanana API...")
        print("-"*70)

        images = demo_image_generation(prompts)

        if images:
            print("\n" + "="*70)
            print("RESULTS SUMMARY")
            print("="*70)
            print(f"\nGenerated {len(images)} image(s):")
            for i, img in enumerate(images, 1):
                print(f"\n  Image {i}:")
                print(f"    URL: {img.url or 'N/A'}")
                print(f"    Prompt: {img.prompt[:50]}...")
        else:
            print("\nNo images generated. Check API key and network connectivity.")
    else:
        print("\nSkipping image generation (no API key)")

    # Also try Agent Zero method
    demo_via_agent_zero()

    print("\n" + "="*70)
    print("DEMO COMPLETE")
    print("="*70)


if __name__ == "__main__":
    main()
