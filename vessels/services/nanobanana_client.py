"""
NanoBanana API Client for Image Generation

Integrates with Agent Zero's entity extraction to generate
contextual images for conversations.

API: https://nanobananaapi.ai
Docs: https://docs.nanobananaapi.ai/quickstart
"""

import logging
import requests
import time
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


class GenerationType(str, Enum):
    """NanoBanana generation types."""
    # Note: API uses "TEXTTOIAMGE" (typo in their API)
    TEXT_TO_IMAGE = "TEXTTOIAMGE"
    IMAGE_TO_IMAGE = "IMAGETOIMAGE"


@dataclass
class GeneratedImage:
    """Result of image generation."""
    url: Optional[str] = None
    base64_data: Optional[str] = None
    prompt: str = ""
    revised_prompt: Optional[str] = None
    aspect_ratio: str = "1:1"
    style: str = ""
    task_id: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class NanoBananaClient:
    """
    Client for NanoBanana image generation API.

    Integrates with Vessels' entity extraction to generate
    contextual images from conversation content.

    Uses async task-based generation:
    1. Submit generation request -> get taskId
    2. Poll record-info endpoint until complete
    3. Return image URLs
    """

    # API endpoints (per docs.nanobananaapi.ai/quickstart)
    BASE_URL = "https://api.nanobananaapi.ai/api/v1"
    GENERATE_ENDPOINT = "/nanobanana/generate"
    RECORD_INFO_ENDPOINT = "/nanobanana/record-info"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_style: str = ImageStyle.WARM_HAWAIIAN,
        default_aspect_ratio: str = AspectRatio.SQUARE,
        poll_interval: float = 2.0,
        max_poll_attempts: int = 30,
    ):
        """
        Initialize NanoBanana client.

        Args:
            api_key: API key (or set NANOBANANA_API_KEY env var)
            base_url: Override base URL
            default_style: Default image style
            default_aspect_ratio: Default aspect ratio
            poll_interval: Seconds between status checks
            max_poll_attempts: Max attempts before timeout
        """
        self.api_key = api_key or os.getenv("NANOBANANA_API_KEY")
        self.base_url = base_url or self.BASE_URL
        self.default_style = default_style
        self.default_aspect_ratio = default_aspect_ratio
        self.poll_interval = poll_interval
        self.max_poll_attempts = max_poll_attempts

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

    def _submit_generation(
        self,
        prompt: str,
        generation_type: str = GenerationType.TEXT_TO_IMAGE,
        num_images: int = 1,
        image_size: str = "1:1",
        image_urls: Optional[List[str]] = None,
        callback_url: Optional[str] = None,
    ) -> Optional[str]:
        """
        Submit image generation request.

        Returns taskId for polling, or None on error.
        """
        payload = {
            "prompt": prompt,
            "type": generation_type,
            "numImages": min(num_images, 4),
            "image_size": image_size,
        }

        if image_urls:
            payload["imageUrls"] = image_urls

        if callback_url:
            payload["callBackUrl"] = callback_url

        try:
            response = requests.post(
                f"{self.base_url}{self.GENERATE_ENDPOINT}",
                headers=self._get_headers(),
                json=payload,
                timeout=30,
            )

            if response.status_code == 200:
                data = response.json()
                task_id = data.get("taskId") or data.get("task_id")
                if task_id:
                    logger.info(f"Generation submitted: taskId={task_id}")
                    return task_id
                else:
                    # Some APIs return results directly
                    logger.info("Generation returned immediate results")
                    return data
            else:
                logger.error(f"Generation submission failed: {response.status_code} - {response.text}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Generation request failed: {e}")
            return None

    def _poll_for_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Poll for generation result.

        Returns result dict or None on timeout/error.
        """
        for attempt in range(self.max_poll_attempts):
            try:
                response = requests.get(
                    f"{self.base_url}{self.RECORD_INFO_ENDPOINT}",
                    headers=self._get_headers(),
                    params={"taskId": task_id},
                    timeout=10,
                )

                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status", "").lower()

                    if status in ("completed", "success", "done"):
                        logger.info(f"Generation completed: taskId={task_id}")
                        return data
                    elif status in ("failed", "error"):
                        logger.error(f"Generation failed: {data.get('error', 'Unknown')}")
                        return None
                    else:
                        # Still processing
                        logger.debug(f"Generation in progress: {status} (attempt {attempt + 1})")

                time.sleep(self.poll_interval)

            except requests.exceptions.RequestException as e:
                logger.warning(f"Poll request failed: {e}")
                time.sleep(self.poll_interval)

        logger.error(f"Generation timed out after {self.max_poll_attempts} attempts")
        return None

    def generate_image(
        self,
        prompt: str,
        style: Optional[str] = None,
        aspect_ratio: Optional[str] = None,
        num_images: int = 1,
        negative_prompt: Optional[str] = None,
        wait_for_result: bool = True,
    ) -> List[GeneratedImage]:
        """
        Generate images from a text prompt.

        Args:
            prompt: Text description of desired image
            style: Visual style (uses default if not specified)
            aspect_ratio: Aspect ratio (uses default if not specified)
            num_images: Number of images to generate (1-4)
            negative_prompt: What to avoid in the image
            wait_for_result: If True, poll until complete

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
        if negative_prompt:
            full_prompt += f". Avoid: {negative_prompt}"

        # Submit generation request
        result = self._submit_generation(
            prompt=full_prompt,
            generation_type=GenerationType.TEXT_TO_IMAGE,
            num_images=num_images,
            image_size=aspect_ratio,  # API uses "image_size" for aspect ratio
        )

        if result is None:
            return []

        # Handle immediate results (dict) vs async (task_id string)
        if isinstance(result, dict):
            data = result
        elif wait_for_result:
            data = self._poll_for_result(result)
            if data is None:
                return []
        else:
            # Return task_id only
            return [GeneratedImage(
                prompt=prompt,
                style=style,
                task_id=result,
                metadata={"status": "pending"},
            )]

        # Parse results
        images = []
        image_list = data.get("images", data.get("data", []))

        if isinstance(image_list, list):
            for img_data in image_list:
                if isinstance(img_data, str):
                    # Direct URL
                    images.append(GeneratedImage(
                        url=img_data,
                        prompt=prompt,
                        aspect_ratio=aspect_ratio,
                        style=style,
                        metadata={"source": "nanobanana"},
                    ))
                elif isinstance(img_data, dict):
                    images.append(GeneratedImage(
                        url=img_data.get("url") or img_data.get("imageUrl"),
                        base64_data=img_data.get("b64_json") or img_data.get("base64"),
                        prompt=prompt,
                        revised_prompt=img_data.get("revised_prompt"),
                        aspect_ratio=aspect_ratio,
                        style=style,
                        metadata={
                            "model": data.get("model"),
                            "created": data.get("created"),
                        },
                    ))

        logger.info(f"Generated {len(images)} image(s) for prompt: {prompt[:50]}...")
        return images

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

    def check_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Check status of a generation task.

        Args:
            task_id: Task ID from async generation

        Returns:
            Status dict with 'status' and optionally 'images'
        """
        try:
            response = requests.get(
                f"{self.base_url}{self.RECORD_INFO_ENDPOINT}",
                headers=self._get_headers(),
                params={"taskId": task_id},
                timeout=10,
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {"status": "error", "error": response.text}

        except requests.exceptions.RequestException as e:
            return {"status": "error", "error": str(e)}


# Singleton instance
_client: Optional[NanoBananaClient] = None


def get_nanobanana_client(api_key: Optional[str] = None) -> NanoBananaClient:
    """Get or create the NanoBanana client singleton."""
    global _client
    if _client is None or api_key:
        _client = NanoBananaClient(api_key=api_key)
    return _client
