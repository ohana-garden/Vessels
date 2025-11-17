#!/usr/bin/env python3
"""
AI-ENHANCED CONTENT GENERATION SYSTEM
Integrates OpenAI/Anthropic LLMs with cultural intelligence
Generates high-quality, culturally-aware content using AI
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from dataclasses import dataclass
import openai
from anthropic import Anthropic, AsyncAnthropic

from content_generation import (
    ContextualContentGenerator,
    ContentContext,
    ContentType,
    GeneratedContent
)

logger = logging.getLogger(__name__)


class LLMProvider:
    """Enum for LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AUTO = "auto"


@dataclass
class GenerationResult:
    """Result from AI generation"""
    content: str
    model_used: str
    tokens_used: int
    generation_time: float
    quality_score: float
    metadata: Dict[str, Any]


class AIContentGenerator:
    """Enhanced content generator using AI/LLM"""

    def __init__(self, provider: str = LLMProvider.AUTO):
        """
        Initialize AI content generator

        Args:
            provider: 'openai', 'anthropic', or 'auto' (tries both)
        """
        self.provider = provider
        self.base_generator = ContextualContentGenerator()

        # Initialize clients based on available API keys
        self.openai_client = self._init_openai()
        self.anthropic_client = self._init_anthropic()

        # Determine which provider to use
        if provider == LLMProvider.AUTO:
            if self.anthropic_client:
                self.active_provider = LLMProvider.ANTHROPIC
                logger.info("Using Anthropic Claude for content generation")
            elif self.openai_client:
                self.active_provider = LLMProvider.OPENAI
                logger.info("Using OpenAI GPT for content generation")
            else:
                self.active_provider = None
                logger.warning("No AI providers available, falling back to template-based generation")
        else:
            self.active_provider = provider

        # Load generation strategies
        self.generation_strategies = self._load_generation_strategies()

    def _init_openai(self) -> Optional[openai.OpenAI]:
        """Initialize OpenAI client if API key available"""
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            try:
                return openai.OpenAI(api_key=api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
        return None

    def _init_anthropic(self) -> Optional[Anthropic]:
        """Initialize Anthropic client if API key available"""
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if api_key:
            try:
                return Anthropic(api_key=api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize Anthropic client: {e}")
        return None

    def _load_generation_strategies(self) -> Dict[str, Dict[str, Any]]:
        """Load AI generation strategies for different content types"""
        return {
            ContentType.GRANT_NARRATIVE: {
                'temperature': 0.7,
                'max_tokens': 3000,
                'style': 'professional_persuasive',
                'structure': 'narrative_arc',
                'emphasis': ['impact', 'sustainability', 'community_need']
            },
            ContentType.ELDER_CARE_PROTOCOL: {
                'temperature': 0.3,
                'max_tokens': 2000,
                'style': 'clear_compassionate',
                'structure': 'step_by_step',
                'emphasis': ['safety', 'dignity', 'clarity']
            },
            ContentType.VOLUNTEER_SCRIPT: {
                'temperature': 0.6,
                'max_tokens': 1500,
                'style': 'warm_conversational',
                'structure': 'dialogue_flow',
                'emphasis': ['warmth', 'respect', 'empowerment']
            },
            ContentType.DISASTER_RESPONSE: {
                'temperature': 0.2,
                'max_tokens': 1500,
                'style': 'urgent_actionable',
                'structure': 'priority_list',
                'emphasis': ['safety', 'immediacy', 'clarity']
            },
            ContentType.COMMUNITY_FLYER: {
                'temperature': 0.7,
                'max_tokens': 1000,
                'style': 'engaging_accessible',
                'structure': 'attention_grabbing',
                'emphasis': ['visual_appeal', 'call_to_action', 'inclusivity']
            }
        }

    async def generate_content(self, context: ContentContext) -> GeneratedContent:
        """
        Generate content using AI with cultural intelligence

        Args:
            context: Content generation context

        Returns:
            Generated content with metadata
        """
        start_time = datetime.now()

        # If no AI provider available, fall back to template-based
        if not self.active_provider:
            logger.info("No AI provider available, using template-based generation")
            return await self.base_generator.generate_content(context)

        try:
            # Build AI prompt from context
            prompt = self._build_generation_prompt(context)
            system_prompt = self._build_system_prompt(context)

            # Get generation strategy for this content type
            strategy = self.generation_strategies.get(
                context.content_type,
                {'temperature': 0.7, 'max_tokens': 2000}
            )

            # Generate content using active provider
            if self.active_provider == LLMProvider.ANTHROPIC:
                result = await self._generate_with_anthropic(
                    system_prompt, prompt, strategy
                )
            else:
                result = await self._generate_with_openai(
                    system_prompt, prompt, strategy
                )

            # Apply cultural adaptations
            adapted_content = self.base_generator._apply_adaptations(
                {'title': result.metadata.get('title', 'Generated Content'),
                 'body': result.content,
                 'metadata': result.metadata},
                context
            )

            # Package final content
            generated = GeneratedContent(
                id=result.metadata.get('id', ''),
                content_type=context.content_type,
                title=adapted_content['title'],
                body=adapted_content['body'],
                metadata={
                    **adapted_content['metadata'],
                    'ai_model': result.model_used,
                    'tokens_used': result.tokens_used,
                    'generation_time': result.generation_time,
                    'quality_score': result.quality_score,
                    'provider': self.active_provider
                },
                sources_used=['ai_generated', f'model:{result.model_used}'],
                generation_context=context,
                created_at=datetime.now()
            )

            # Cache for reuse
            self.base_generator._cache_content(generated)

            logger.info(f"Generated content using {result.model_used} in {result.generation_time}s")
            return generated

        except Exception as e:
            logger.error(f"AI generation failed: {e}, falling back to template-based")
            return await self.base_generator.generate_content(context)

    def _build_system_prompt(self, context: ContentContext) -> str:
        """Build system prompt for AI with Shoghi's values"""

        base_system = """You are Shoghi, an AI assistant that helps communities coordinate care and resources.

Your core values are:
- ALOHA: Lead with love, compassion, and kindness
- OHANA: Treat everyone as family, build belonging
- MALAMA: Care for and protect the community
- KULEANA: Honor responsibility and privilege
- PONO: Maintain righteousness, balance, and harmony

Your communication style:
- Culturally sensitive and respectful
- Clear and actionable
- Warm yet professional
- Community-centered"""

        # Add content-specific instructions
        if context.content_type == ContentType.GRANT_NARRATIVE:
            base_system += """

For grant narratives:
- Tell a compelling story grounded in community need
- Use data and evidence to support claims
- Emphasize sustainability and community ownership
- Demonstrate cultural competence
- Show measurable impact potential"""

        elif context.content_type == ContentType.ELDER_CARE_PROTOCOL:
            base_system += """

For elder care protocols:
- Prioritize safety and dignity above all
- Use clear, step-by-step instructions
- Show deep respect for elders (kupuna)
- Include cultural considerations
- Ensure procedures are easy to follow"""

        elif context.content_type == ContentType.VOLUNTEER_SCRIPT:
            base_system += """

For volunteer scripts:
- Use warm, welcoming language
- Provide conversation starters and flow
- Adapt to different cultural contexts
- Empower volunteers with clear guidance
- Build confidence through examples"""

        elif context.content_type == ContentType.DISASTER_RESPONSE:
            base_system += """

For disaster response:
- Lead with safety and immediate actions
- Use clear, urgent but calm language
- Provide prioritized steps with timeframes
- Include emergency resources and contacts
- Be direct and actionable"""

        # Add cultural context
        if context.cultural_context:
            base_system += f"""

Cultural Context: {context.cultural_context}
- Honor cultural values and communication styles
- Use culturally appropriate language
- Respect traditions and customs
- Build on community strengths"""

        return base_system

    def _build_generation_prompt(self, context: ContentContext) -> str:
        """Build detailed generation prompt from context"""

        prompt_parts = []

        # Content type and purpose
        prompt_parts.append(f"Generate a {context.content_type.value.replace('_', ' ')}.")

        # Target audience
        prompt_parts.append(f"\nTarget Audience: {context.target_audience}")

        # Emotional tone
        prompt_parts.append(f"Emotional Tone: {context.emotional_tone}")

        # Urgency level
        prompt_parts.append(f"Urgency: {context.urgency_level}")

        # Specific requirements
        if context.specific_requirements:
            prompt_parts.append("\nSpecific Requirements:")
            for key, value in context.specific_requirements.items():
                prompt_parts.append(f"- {key}: {value}")

        # Constraints
        if context.constraints:
            prompt_parts.append("\nConstraints:")
            for constraint in context.constraints:
                prompt_parts.append(f"- {constraint}")

        # Language and cultural context
        prompt_parts.append(f"\nLanguage: {context.language}")
        prompt_parts.append(f"Cultural Context: {context.cultural_context}")

        # Add context-specific guidance
        if context.content_type == ContentType.GRANT_NARRATIVE:
            prompt_parts.append("""

Please structure the grant narrative with:
1. Compelling opening that establishes community need
2. Clear problem statement with data
3. Proposed solution grounded in community strengths
4. Implementation plan with timeline
5. Expected outcomes (measurable)
6. Evaluation approach
7. Sustainability plan

Use storytelling to make it compelling while maintaining professionalism.""")

        elif context.content_type == ContentType.ELDER_CARE_PROTOCOL:
            prompt_parts.append("""

Please structure the protocol with:
1. Preparation checklist
2. Step-by-step procedure (numbered)
3. Safety considerations (highlighted)
4. Cultural considerations
5. Documentation requirements
6. Emergency contacts/procedures

Ensure every step respects elder dignity and autonomy.""")

        elif context.content_type == ContentType.VOLUNTEER_SCRIPT:
            prompt_parts.append("""

Please provide:
1. Multiple greeting options (formal/informal)
2. Rapport-building conversation starters
3. Key questions to ask
4. How to handle common situations
5. Closing and next steps

Include cultural variations where appropriate.""")

        elif context.content_type == ContentType.DISASTER_RESPONSE:
            prompt_parts.append("""

Please organize by priority:
1. IMMEDIATE (0-2 hours): Safety-critical actions
2. SHORT-TERM (2-24 hours): Essential needs
3. MEDIUM-TERM (1-7 days): Stabilization
4. LONG-TERM (7+ days): Recovery support

Include emergency contact numbers and resources.""")

        prompt_parts.append("\n\nProvide the complete content ready to use.")

        return "\n".join(prompt_parts)

    async def _generate_with_anthropic(
        self,
        system_prompt: str,
        user_prompt: str,
        strategy: Dict[str, Any]
    ) -> GenerationResult:
        """Generate content using Anthropic Claude"""

        start_time = datetime.now()

        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=strategy.get('max_tokens', 2000),
                temperature=strategy.get('temperature', 0.7),
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )

            content = response.content[0].text
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            generation_time = (datetime.now() - start_time).total_seconds()

            # Calculate quality score (basic heuristic)
            quality_score = self._calculate_quality_score(
                content,
                len(content.split()),
                strategy
            )

            return GenerationResult(
                content=content,
                model_used="claude-3-5-sonnet-20241022",
                tokens_used=tokens_used,
                generation_time=generation_time,
                quality_score=quality_score,
                metadata={
                    'provider': 'anthropic',
                    'id': response.id,
                    'stop_reason': response.stop_reason
                }
            )

        except Exception as e:
            logger.error(f"Anthropic generation failed: {e}")
            raise

    async def _generate_with_openai(
        self,
        system_prompt: str,
        user_prompt: str,
        strategy: Dict[str, Any]
    ) -> GenerationResult:
        """Generate content using OpenAI GPT"""

        start_time = datetime.now()

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",  # or "gpt-4-turbo-preview"
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=strategy.get('max_tokens', 2000),
                temperature=strategy.get('temperature', 0.7)
            )

            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            generation_time = (datetime.now() - start_time).total_seconds()

            # Calculate quality score
            quality_score = self._calculate_quality_score(
                content,
                len(content.split()),
                strategy
            )

            return GenerationResult(
                content=content,
                model_used=response.model,
                tokens_used=tokens_used,
                generation_time=generation_time,
                quality_score=quality_score,
                metadata={
                    'provider': 'openai',
                    'id': response.id,
                    'finish_reason': response.choices[0].finish_reason
                }
            )

        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise

    def _calculate_quality_score(
        self,
        content: str,
        word_count: int,
        strategy: Dict[str, Any]
    ) -> float:
        """Calculate basic quality score for generated content"""

        score = 0.5  # Base score

        # Check length appropriateness
        expected_min_words = strategy.get('max_tokens', 2000) * 0.3
        expected_max_words = strategy.get('max_tokens', 2000) * 0.8

        if expected_min_words <= word_count <= expected_max_words:
            score += 0.2

        # Check structure (has multiple paragraphs)
        paragraphs = content.split('\n\n')
        if len(paragraphs) >= 3:
            score += 0.1

        # Check for lists/structure
        if any(marker in content for marker in ['1.', '2.', '•', '-', '*']):
            score += 0.1

        # Check for headers
        if any(marker in content for marker in ['#', '**']):
            score += 0.1

        return min(1.0, score)

    async def generate_multimodal_content(
        self,
        context: ContentContext
    ) -> Dict[str, Any]:
        """Generate content in multiple formats using AI"""

        # Generate base text content with AI
        text_content = await self.generate_content(context)

        # Use base generator for multimodal adaptations
        # (audio scripts, visual layouts, interactive elements)
        audio_script = self.base_generator._generate_audio_script(
            text_content, context
        )
        visual_layout = self.base_generator._generate_visual_layout(
            text_content, context
        )
        interactive = self.base_generator._generate_interactive_elements(
            text_content, context
        )

        return {
            'text': text_content,
            'audio_script': audio_script,
            'visual_layout': visual_layout,
            'interactive': interactive,
            'formats': ['text', 'audio', 'visual', 'interactive']
        }

    async def regenerate_with_feedback(
        self,
        original_content: GeneratedContent,
        feedback: Dict[str, Any]
    ) -> GeneratedContent:
        """Regenerate content incorporating user feedback"""

        # Extract what to improve from feedback
        improvements_needed = []

        if feedback.get('rating', 5) < 4:
            if 'too_long' in feedback.get('issues', []):
                improvements_needed.append("Make it more concise")
            if 'too_formal' in feedback.get('issues', []):
                improvements_needed.append("Use more casual, warm language")
            if 'unclear' in feedback.get('issues', []):
                improvements_needed.append("Make instructions clearer and more specific")
            if 'missing_cultural_elements' in feedback.get('issues', []):
                improvements_needed.append("Strengthen cultural adaptation")

        if feedback.get('user_edits'):
            improvements_needed.append(
                f"User made these edits: {feedback['user_edits'][:200]}"
            )

        # Build regeneration prompt
        regeneration_context = original_content.generation_context
        regeneration_context.specific_requirements['improvements'] = improvements_needed
        regeneration_context.specific_requirements['previous_version'] = original_content.body[:500]

        # Regenerate
        new_content = await self.generate_content(regeneration_context)
        new_content.version = original_content.version + 1

        return new_content


# Global AI content generator instance
ai_content_generator = None


def get_ai_content_generator(provider: str = LLMProvider.AUTO) -> AIContentGenerator:
    """Get or create global AI content generator instance"""
    global ai_content_generator
    if ai_content_generator is None:
        ai_content_generator = AIContentGenerator(provider=provider)
    return ai_content_generator


# Convenience function for quick content generation
async def generate_ai_content(
    content_type: ContentType,
    target_audience: str,
    cultural_context: str = "multicultural",
    emotional_tone: str = "warm",
    urgency_level: str = "normal",
    specific_requirements: Dict[str, Any] = None,
    provider: str = LLMProvider.AUTO
) -> GeneratedContent:
    """
    Quick content generation function

    Example:
        content = await generate_ai_content(
            content_type=ContentType.GRANT_NARRATIVE,
            target_audience="federal funders",
            cultural_context="hawaiian",
            specific_requirements={"focus": "elder care program"}
        )
    """
    context = ContentContext(
        content_type=content_type,
        target_audience=target_audience,
        cultural_context=cultural_context,
        language="en",
        emotional_tone=emotional_tone,
        urgency_level=urgency_level,
        specific_requirements=specific_requirements or {}
    )

    generator = get_ai_content_generator(provider)
    return await generator.generate_content(context)
