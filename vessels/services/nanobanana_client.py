"""
NanoBanana API Client for Image Generation

Integrates with Agent Zero's entity extraction to generate
contextual images for conversations.

API: https://nanobananaapi.ai
Docs: https://docs.nanobananaapi.ai
"""

import logging
import requests
import base64
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class AspectRatio(str, Enum):
    """Supported aspect ratios for image generation."""
    SQUARE = "1:1"
    LANDSCAPE = "16:9"
    PORTRAIT = "9:16"
    WIDE = "21:9"
    PHOTO = "4:3"
    PHOTO_PORTRAIT = "3:4"


class ImageStyle(str, Enum):
    """Visual styles for generation."""
    PHOTOREALISTIC = "photorealistic"
    ILLUSTRATION = "illustration"
    WATERCOLOR = "watercolor"
    DIGITAL_ART = "digital_art"
    WARM_HAWAIIAN = "warm, Hawaiian, community-focused"


@dataclass
class GeneratedImage:
    """Result of image generation."""
    url: Optional[str] = None
    base64_data: Optional[str] = None
    prompt: str = ""
    revised_prompt: Optional[str] = None
    aspect_ratio: str = "1:1"
    style: str = ""
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class NanoBananaClient:
    """
    Client for NanoBanana image generation API.

    Integrates with Vessels' entity extraction to generate
    contextual images from conversation content.
    """

    # API endpoints
    BASE_URL = "https://api.nanobananaapi.ai"
    TEXT_TO_IMAGE_ENDPOINT = "/v1/images/generate"
    IMAGE_TO_IMAGE_ENDPOINT = "/v1/images/edit"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_style: str = ImageStyle.WARM_HAWAIIAN,
        default_aspect_ratio: str = AspectRatio.SQUARE,
    ):
        """
        Initialize NanoBanana client.

        Args:
            api_key: API key (or set NANOBANANA_API_KEY env var)
            base_url: Override base URL
            default_style: Default image style
            default_aspect_ratio: Default aspect ratio
        """
        self.api_key = api_key or os.getenv("NANOBANANA_API_KEY")
        self.base_url = base_url or self.BASE_URL
        self.default_style = default_style
        self.default_aspect_ratio = default_aspect_ratio

        if not self.api_key:
            logger.warning("NanoBanana API key not configured")

        logger.info(f"NanoBanana client initialized (base_url: {self.base_url})")

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def generate_image(
        self,
        prompt: str,
        style: Optional[str] = None,
        aspect_ratio: Optional[str] = None,
        num_images: int = 1,
        negative_prompt: Optional[str] = None,
    ) -> List[GeneratedImage]:
        """
        Generate images from a text prompt.

        Args:
            prompt: Text description of desired image
            style: Visual style (uses default if not specified)
            aspect_ratio: Aspect ratio (uses default if not specified)
            num_images: Number of images to generate (1-4)
            negative_prompt: What to avoid in the image

        Returns:
            List of GeneratedImage results
        """
        if not self.api_key:
            logger.error("Cannot generate image: API key not configured")
            return []

        style = style or self.default_style
        aspect_ratio = aspect_ratio or self.default_aspect_ratio

        # Build full prompt with style
        full_prompt = f"{prompt}. Style: {style}"

        payload = {
            "prompt": full_prompt,
            "n": min(num_images, 4),
            "aspect_ratio": aspect_ratio,
            "response_format": "url",  # or "b64_json"
        }

        if negative_prompt:
            payload["negative_prompt"] = negative_prompt

        try:
            response = requests.post(
                f"{self.base_url}{self.TEXT_TO_IMAGE_ENDPOINT}",
                headers=self._get_headers(),
                json=payload,
                timeout=60,
            )

            if response.status_code == 200:
                data = response.json()
                images = []

                for img_data in data.get("data", []):
                    images.append(GeneratedImage(
                        url=img_data.get("url"),
                        base64_data=img_data.get("b64_json"),
                        prompt=prompt,
                        revised_prompt=img_data.get("revised_prompt"),
                        aspect_ratio=aspect_ratio,
                        style=style,
                        metadata={
                            "model": data.get("model"),
                            "created": data.get("created"),
                        }
                    ))

                logger.info(f"Generated {len(images)} image(s) for prompt: {prompt[:50]}...")
                return images

            else:
                logger.error(f"Image generation failed: {response.status_code} - {response.text}")
                return []

        except requests.exceptions.Timeout:
            logger.error("Image generation timed out")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Image generation request failed: {e}")
            return []

    def generate_from_entities(
        self,
        entities: List[str],
        topic: Optional[str] = None,
        style: Optional[str] = None,
        aspect_ratio: Optional[str] = None,
    ) -> List[GeneratedImage]:
        """
        Generate image from extracted entities.

        This is the primary integration point with Agent Zero's
        entity extraction system.

        Args:
            entities: List of extracted entities
            topic: Conversation topic for context
            style: Visual style
            aspect_ratio: Aspect ratio

        Returns:
            List of GeneratedImage results
        """
        if not entities:
            logger.warning("No entities provided for image generation")
            return []

        # Categorize entities for better prompts
        places = []
        people = []
        objects = []

        place_keywords = ['valley', 'center', 'garden', 'farm', 'beach', 'mountain', 'village', 'hawaii', 'kailua', 'waipio']
        people_keywords = ['kupuna', 'elder', 'farmer', 'family', 'community', 'neighbor', 'ohana']

        for entity in entities:
            entity_lower = entity.lower()
            if any(kw in entity_lower for kw in place_keywords):
                places.append(entity)
            elif any(kw in entity_lower for kw in people_keywords):
                people.append(entity)
            else:
                objects.append(entity)

        # Build contextual prompt
        prompt_parts = []

        if places:
            prompt_parts.append(f"A scene in {', '.join(places)}")
        else:
            prompt_parts.append("A warm Hawaiian community scene")

        if people:
            prompt_parts.append(f"featuring {', '.join(people)}")

        if objects:
            prompt_parts.append(f"with {', '.join(objects)}")

        if topic:
            prompt_parts.append(f"related to {topic}")

        prompt = ", ".join(prompt_parts)

        return self.generate_image(
            prompt=prompt,
            style=style,
            aspect_ratio=aspect_ratio,
        )

    def generate_for_turn(
        self,
        turn_data: Dict[str, Any],
        style: Optional[str] = None,
    ) -> List[GeneratedImage]:
        """
        Generate image for a conversation turn.

        Args:
            turn_data: Turn data from ConversationStore
            style: Visual style

        Returns:
            List of GeneratedImage results
        """
        entities = turn_data.get("entities_used", [])
        topic = turn_data.get("topic")
        prompt = turn_data.get("prompt")

        if prompt:
            # Use pre-generated prompt
            return self.generate_image(prompt=prompt, style=style)
        elif entities:
            # Generate from entities
            return self.generate_from_entities(entities, topic, style)
        else:
            logger.warning("No prompt or entities for image generation")
            return []


# Singleton instance
_client: Optional[NanoBananaClient] = None


def get_nanobanana_client(api_key: Optional[str] = None) -> NanoBananaClient:
    """Get or create the NanoBanana client singleton."""
    global _client
    if _client is None or api_key:
        _client = NanoBananaClient(api_key=api_key)
    return _client
