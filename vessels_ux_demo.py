#!/usr/bin/env python3
"""
Vessels UX Demo - Complete Conversation Flow with Image Generation

This demonstrates the full UX:
1. User sends message to vessel
2. Entities extracted from conversation
3. Image prompt generated from entities
4. Image generated via NanoBanana API
5. Response displayed with contextual image

Run: python vessels_ux_demo.py
"""

import os
import sys
import time
import logging
from typing import Optional, Dict, Any, List

# Setup logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(message)s'
)

# Silence library loggers
for name in ['vessels', 'urllib3', 'requests']:
    logging.getLogger(name).setLevel(logging.ERROR)


# ANSI colors for terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    END = '\033[0m'


def print_header(text: str):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'═' * 60}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'═' * 60}{Colors.END}")


def print_section(text: str):
    print(f"\n{Colors.CYAN}{Colors.BOLD}─── {text} ───{Colors.END}")


def print_user(text: str):
    print(f"\n{Colors.GREEN}{Colors.BOLD}👤 You:{Colors.END} {text}")


def print_vessel(text: str):
    print(f"\n{Colors.BLUE}{Colors.BOLD}🌺 Vessel:{Colors.END} {text}")


def print_system(text: str):
    print(f"{Colors.DIM}   {text}{Colors.END}")


def print_image_box(url: str, prompt: str):
    """Display image result in a nice box."""
    print(f"\n{Colors.YELLOW}┌{'─' * 58}┐{Colors.END}")
    print(f"{Colors.YELLOW}│{Colors.END} {Colors.BOLD}🖼️  Generated Image{Colors.END}{' ' * 38}{Colors.YELLOW}│{Colors.END}")
    print(f"{Colors.YELLOW}├{'─' * 58}┤{Colors.END}")

    # Wrap prompt
    prompt_display = prompt[:54] + "..." if len(prompt) > 54 else prompt
    print(f"{Colors.YELLOW}│{Colors.END} Prompt: {prompt_display:<48}{Colors.YELLOW}│{Colors.END}")

    if url:
        url_display = url[:54] + "..." if len(url) > 54 else url
        print(f"{Colors.YELLOW}│{Colors.END} URL: {Colors.CYAN}{url_display:<51}{Colors.END}{Colors.YELLOW}│{Colors.END}")
    else:
        print(f"{Colors.YELLOW}│{Colors.END} {Colors.DIM}(Image URL will appear here when API is available){Colors.END}  {Colors.YELLOW}│{Colors.END}")

    print(f"{Colors.YELLOW}└{'─' * 58}┘{Colors.END}")


class VesselsUXDemo:
    """Interactive demo of the Vessels conversation UX."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("NANOBANANA_API_KEY", "734e2ae0b4ce8ff06d5ccfed5d9deca4")

        # Initialize components
        from vessels.memory import ConversationStore, ConversationType, SpeakerType
        from vessels.services import get_nanobanana_client

        self.store = ConversationStore(enable_entity_extraction=False)
        self.client = get_nanobanana_client(api_key=self.api_key)
        self.ConversationType = ConversationType
        self.SpeakerType = SpeakerType

        # Current conversation
        self.conversation = None
        self.turn_count = 0

        # Vessel persona
        self.vessel_name = "Ohana Helper"
        self.vessel_id = "vessel-ohana-helper"

    def start_conversation(self, user_id: str = "demo-user", topic: str = "Community support"):
        """Start a new conversation."""
        self.conversation = self.store.start_conversation(
            conversation_type=self.ConversationType.USER_VESSEL,
            participant_ids=[user_id, self.vessel_id],
            user_id=user_id,
            vessel_id=self.vessel_id,
            topic=topic,
        )
        self.turn_count = 0
        return self.conversation

    def generate_vessel_response(self, user_message: str, entities: List[str]) -> str:
        """Generate a contextual vessel response."""
        # Simple response generation based on message content
        message_lower = user_message.lower()

        if any(word in message_lower for word in ['grant', 'funding', 'money']):
            return (
                f"I can help you find funding opportunities! Based on what you've mentioned about "
                f"{', '.join(entities[:2]) if entities else 'your project'}, "
                f"let me search for relevant grants from Hawaii Community Foundation and federal programs."
            )
        elif any(word in message_lower for word in ['garden', 'farm', 'taro', 'plant']):
            return (
                f"What a beautiful vision for your community garden! "
                f"Waipio Valley and surrounding areas have rich agricultural traditions. "
                f"I can help you connect with local farming cooperatives and find resources for "
                f"{', '.join(entities[:2]) if entities else 'sustainable agriculture'}."
            )
        elif any(word in message_lower for word in ['kupuna', 'elder', 'senior', 'care']):
            return (
                f"Supporting our kupuna is so important to Hawaiian communities. "
                f"There are programs through the Executive Office on Aging and local nonprofits "
                f"that can help with {', '.join(entities[:2]) if entities else 'elder care services'}."
            )
        elif any(word in message_lower for word in ['community', 'ohana', 'family', 'neighbor']):
            return (
                f"Building strong community connections is at the heart of Hawaiian culture. "
                f"Let me help you organize resources for {', '.join(entities[:2]) if entities else 'your community initiative'}. "
                f"Would you like me to find local gathering spaces or community programs?"
            )
        else:
            return (
                f"I understand you're interested in {entities[0] if entities else 'community support'}. "
                f"As your Ohana Helper, I can connect you with local resources, "
                f"find funding opportunities, and help coordinate with community partners."
            )

    def process_message(self, user_message: str, entities: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Process a user message through the full UX flow.

        Returns dict with:
        - response: Vessel response text
        - entities: Extracted entities
        - image_prompt: Generated image prompt
        - image_url: Generated image URL (if available)
        """
        if not self.conversation:
            self.start_conversation()

        # Auto-extract entities if not provided
        if entities is None:
            entities = self._extract_entities(user_message)

        # Generate vessel response
        response = self.generate_vessel_response(user_message, entities)

        # Record the turn
        turn = self.store.record_complete_turn(
            conversation_id=self.conversation.conversation_id,
            speaker_id="demo-user",
            speaker_type=self.SpeakerType.USER,
            message=user_message,
            response=response,
            entities=entities,
        )
        self.turn_count += 1

        # Generate image prompt
        prompt_data = self.store.generate_image_prompt(turn, self.conversation)

        # Try to generate image
        image_url = None
        if prompt_data:
            image_url = self._generate_image(prompt_data["prompt"])

        return {
            "response": response,
            "entities": entities,
            "prompt_data": prompt_data,
            "image_url": image_url,
            "turn": turn,
        }

    def _extract_entities(self, text: str) -> List[str]:
        """Extract entities from text."""
        # Hawaiian/community-focused entity keywords
        entity_keywords = {
            # Places
            'waipio valley': 'Waipio Valley',
            'kailua': 'Kailua',
            'hawaii': 'Hawaii',
            'honolulu': 'Honolulu',
            'maui': 'Maui',
            'oahu': 'Oahu',
            'community center': 'community center',
            'beach': 'beach',
            'garden': 'garden',
            'farm': 'farm',
            # People
            'kupuna': 'kupuna',
            'elder': 'elders',
            'keiki': 'keiki',
            'ohana': 'ohana',
            'family': 'family',
            'community': 'community',
            # Things
            'taro': 'taro',
            'grant': 'grants',
            'meal': 'community meal',
            'harvest': 'harvest',
        }

        text_lower = text.lower()
        found = []

        for keyword, entity in entity_keywords.items():
            if keyword in text_lower and entity not in found:
                found.append(entity)

        return found[:5]

    def _generate_image(self, prompt: str) -> Optional[str]:
        """Generate image via NanoBanana API."""
        try:
            images = self.client.generate_image(
                prompt=prompt,
                aspect_ratio="16:9",
                wait_for_result=True,
            )
            if images and images[0].url:
                return images[0].url
        except Exception as e:
            pass  # API unavailable, return None
        return None

    def run_interactive(self):
        """Run interactive demo."""
        print_header("VESSELS UX DEMO")
        print(f"\n{Colors.DIM}Welcome to Vessels - where anyone can create digital twins.{Colors.END}")
        print(f"{Colors.DIM}You're chatting with {self.vessel_name}, your community support assistant.{Colors.END}")
        print(f"{Colors.DIM}Type 'quit' to exit, 'demo' for sample conversation.{Colors.END}")

        self.start_conversation(topic="Community support")

        while True:
            try:
                user_input = input(f"\n{Colors.GREEN}You: {Colors.END}").strip()

                if not user_input:
                    continue

                if user_input.lower() in ['quit', 'exit', 'q']:
                    print(f"\n{Colors.DIM}Mahalo for using Vessels! 🌺{Colors.END}\n")
                    break

                if user_input.lower() == 'demo':
                    self.run_demo_conversation()
                    continue

                # Process the message
                print_system("Processing...")
                result = self.process_message(user_input)

                # Show extracted entities
                if result["entities"]:
                    print_system(f"Entities: {', '.join(result['entities'])}")

                # Show vessel response
                print_vessel(result["response"])

                # Show generated image
                if result["prompt_data"]:
                    print_image_box(
                        result["image_url"],
                        result["prompt_data"]["prompt"][:60]
                    )

            except KeyboardInterrupt:
                print(f"\n\n{Colors.DIM}Mahalo! 🌺{Colors.END}\n")
                break
            except Exception as e:
                print(f"{Colors.RED}Error: {e}{Colors.END}")

    def run_demo_conversation(self):
        """Run a scripted demo conversation."""
        print_section("Demo Conversation")

        demo_messages = [
            {
                "message": "I want to create a taro garden in Waipio Valley where kupuna can teach keiki traditional farming.",
                "entities": ["taro", "Waipio Valley", "kupuna", "keiki", "garden"],
            },
            {
                "message": "Our ohana is organizing a community meal at Kailua beach to celebrate the harvest.",
                "entities": ["ohana", "community meal", "Kailua", "beach", "harvest"],
            },
            {
                "message": "Can you help me find grants for our elder care program?",
                "entities": ["grants", "elders", "community"],
            },
        ]

        self.start_conversation(topic="Hawaiian community programs")

        for demo in demo_messages:
            print_user(demo["message"])
            time.sleep(0.5)

            print_system("Extracting entities...")
            time.sleep(0.3)
            print_system(f"Entities: {', '.join(demo['entities'])}")

            result = self.process_message(demo["message"], demo["entities"])

            print_vessel(result["response"])

            if result["prompt_data"]:
                print_image_box(
                    result["image_url"],
                    result["prompt_data"]["prompt"][:60]
                )

            time.sleep(1)

        print_section("Demo Complete")
        print(f"{Colors.DIM}Type your own messages to continue, or 'quit' to exit.{Colors.END}")


def main():
    """Main entry point."""
    # Check for API key
    api_key = os.getenv("NANOBANANA_API_KEY", "734e2ae0b4ce8ff06d5ccfed5d9deca4")

    demo = VesselsUXDemo(api_key=api_key)
    demo.run_interactive()


if __name__ == "__main__":
    main()
