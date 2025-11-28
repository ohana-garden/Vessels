#!/usr/bin/env python3
"""
STANDALONE IMAGE GENERATION DEMO

Run this locally (outside sandbox) to see full end-to-end flow:
  python run_image_demo.py

Or set your API key:
  NANOBANANA_API_KEY=your_key python run_image_demo.py
"""

import os
import sys

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# API key
API_KEY = os.getenv("NANOBANANA_API_KEY", "734e2ae0b4ce8ff06d5ccfed5d9deca4")


def main():
    print("\n" + "="*60)
    print("VESSELS → NANOBANANA IMAGE GENERATION")
    print("="*60)

    # Import Vessels components
    from vessels.memory import ConversationStore, ConversationType, SpeakerType
    from vessels.services import get_nanobanana_client, ImageStyle, AspectRatio

    # Test message
    message = "I want to create a taro garden in Waipio Valley where kupuna can teach keiki traditional farming."
    entities = ["taro garden", "Waipio Valley", "kupuna", "keiki", "traditional farming"]

    print(f"\nUSER MESSAGE:")
    print(f'  "{message}"')
    print(f"\nENTITIES: {', '.join(entities)}")

    # Create conversation and generate prompt
    store = ConversationStore(enable_entity_extraction=False)
    conv = store.start_conversation(
        conversation_type=ConversationType.USER_VESSEL,
        participant_ids=["user-1", "vessel-1"],
        user_id="user-1",
        vessel_id="vessel-1",
        topic="Hawaiian garden planning",
    )
    turn = store.record_complete_turn(
        conversation_id=conv.conversation_id,
        speaker_id="user-1",
        speaker_type=SpeakerType.USER,
        message=message,
        response="I can help with that!",
        entities=entities,
    )

    prompt_data = store.generate_image_prompt(turn, conv)
    print(f"\nGENERATED PROMPT:")
    print(f'  "{prompt_data["prompt"]}"')

    # Call NanoBanana API
    print(f"\n" + "-"*60)
    print("CALLING NANOBANANA API...")
    print("-"*60)

    client = get_nanobanana_client(api_key=API_KEY)
    print(f"Base URL: {client.base_url}")
    print(f"Endpoint: {client.GENERATE_ENDPOINT}")
    print(f"API Key: {API_KEY[:8]}...{API_KEY[-4:]}")

    images = client.generate_image(
        prompt=prompt_data["prompt"],
        style=ImageStyle.WARM_HAWAIIAN,
        aspect_ratio=AspectRatio.PORTRAIT,  # Mobile-optimized 9:16
    )

    if images:
        print(f"\nSUCCESS! Generated {len(images)} image(s):")
        for i, img in enumerate(images, 1):
            print(f"\n  Image {i}:")
            if img.url:
                print(f"    URL: {img.url}")
            if img.task_id:
                print(f"    Task ID: {img.task_id}")
            if img.revised_prompt:
                print(f"    Revised: {img.revised_prompt[:80]}...")
    else:
        print("\nNo images returned. Check API response and credentials.")

    print("\n" + "="*60)
    print("DEMO COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()
