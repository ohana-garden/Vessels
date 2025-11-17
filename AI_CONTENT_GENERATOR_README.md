# AI-Enhanced Content Generator for Shoghi

## Overview

The AI-Enhanced Content Generator integrates powerful language models (OpenAI GPT-4 and Anthropic Claude) with Shoghi's cultural intelligence framework to generate high-quality, culturally-aware content for community coordination.

## Features

- **AI-Powered Generation**: Uses GPT-4 or Claude for intelligent content creation
- **Cultural Intelligence**: Maintains Hawaiian, Japanese, and Filipino cultural adaptations
- **Quality Assurance**: Automatic validation of readability, tone, and cultural sensitivity
- **Multimodal Output**: Generates text, audio scripts, visual layouts, and interactive elements
- **Feedback Loop**: Learn and improve from user feedback
- **Flexible Provider**: Works with OpenAI, Anthropic, or template-based fallback

## Setup Instructions

### 1. Install Dependencies

```bash
pip install openai anthropic python-dotenv
```

### 2. Configure API Keys

**IMPORTANT: Never commit API keys to version control!**

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```bash
# Use either OpenAI OR Anthropic (or both)

# Option 1: OpenAI (GPT-4)
OPENAI_API_KEY=sk-your-actual-openai-key-here

# Option 2: Anthropic (Claude)
ANTHROPIC_API_KEY=sk-ant-your-actual-anthropic-key-here

# Provider preference (auto, openai, or anthropic)
AI_PROVIDER=auto
```

**To get API keys:**
- OpenAI: https://platform.openai.com/api-keys
- Anthropic: https://console.anthropic.com/

### 3. Secure Your API Key

**🔒 SECURITY BEST PRACTICES:**

1. **Immediately revoke** the API key you shared in chat
2. **Never** share API keys in plain text
3. Always use environment variables
4. Add `.env` to your `.gitignore`:

```bash
echo ".env" >> .gitignore
```

### 4. Test the System

```bash
# Quick test
python test_ai_content_generation.py --quick

# Full test suite
python test_ai_content_generation.py
```

## Usage

### Basic Usage

```python
import asyncio
from content_generation import ContentContext, ContentType
from ai_content_generator import generate_ai_content

async def generate_content():
    content = await generate_ai_content(
        content_type=ContentType.GRANT_NARRATIVE,
        target_audience="federal funders",
        cultural_context="hawaiian",
        emotional_tone="formal",
        specific_requirements={
            "focus": "elder care program in Lower Puna",
            "include_statistics": True
        }
    )

    print(f"Generated: {content.title}")
    print(content.body)

asyncio.run(generate_content())
```

### Advanced Usage with Quality Checks

```python
from ai_content_generator import AIContentGenerator
from content_quality_checker import ContentQualityChecker

async def generate_with_quality_check():
    # Generate content
    generator = AIContentGenerator()
    content = await generator.generate_content(context)

    # Check quality
    checker = ContentQualityChecker()
    report = await checker.validate_content(content)

    if not report.passed:
        print("Quality issues found:")
        for issue in report.issues:
            print(f"  - {issue.message}")
    else:
        print(f"Quality score: {report.overall_score:.2f}")
```

### Regenerate with Feedback

```python
async def improve_content():
    # Generate initial content
    content = await generate_ai_content(...)

    # User provides feedback
    feedback = {
        'rating': 3,
        'issues': ['too_long', 'too_formal'],
        'comments': 'Need more casual tone'
    }

    # Regenerate with improvements
    generator = AIContentGenerator()
    improved = await generator.regenerate_with_feedback(content, feedback)
```

### Multimodal Generation

```python
async def create_multimodal():
    generator = AIContentGenerator()

    multimodal = await generator.generate_multimodal_content(context)

    # Access different formats
    text_content = multimodal['text']
    audio_script = multimodal['audio_script']
    visual_layout = multimodal['visual_layout']
    interactive_elements = multimodal['interactive']
```

## Content Types Supported

1. **GRANT_NARRATIVE** - Compelling grant proposals with data and storytelling
2. **ELDER_CARE_PROTOCOL** - Step-by-step care procedures with safety emphasis
3. **VOLUNTEER_SCRIPT** - Conversation guides with cultural variations
4. **DISASTER_RESPONSE** - Urgent, prioritized action plans
5. **COMMUNITY_FLYER** - Engaging community announcements
6. **TRAINING_MATERIAL** - Educational content for volunteers
7. **ONBOARDING_GUIDE** - New member orientation materials
8. **FOOD_SAFETY** - Food handling and safety protocols

## Cultural Contexts

The system adapts content for:

- **Hawaiian**: Integrates aloha spirit, Hawaiian values (kuleana, malama, pono)
- **Japanese**: Respectful language, elder honor, group harmony
- **Filipino**: Family-first values, bayanihan spirit, elder respect
- **Multicultural**: Inclusive, accessible to diverse audiences

## Quality Assurance

The system automatically checks:

1. **Readability**: Flesch score, grade level, word complexity
2. **Tone**: Matches expected emotional tone
3. **Cultural Sensitivity**: Appropriate language and concepts
4. **Structure**: Proper formatting, sections, lists
5. **Content Requirements**: Type-specific elements (e.g., grant components)

### Quality Scores

- **0.9-1.0**: Excellent - Ready to use
- **0.7-0.9**: Good - Minor improvements suggested
- **0.5-0.7**: Fair - Review and revise recommended
- **Below 0.5**: Needs significant improvement

## Architecture

```
ai_content_generator.py          # Main AI generation engine
├── LLMProvider                  # OpenAI/Anthropic integration
├── AIContentGenerator           # Core generation logic
└── GenerationResult             # Output with metadata

content_quality_checker.py       # Quality assurance
├── ReadabilityAnalyzer          # Flesch score, grade level
├── ToneAnalyzer                 # Emotional tone detection
├── CulturalSensitivityChecker   # Cultural appropriateness
└── ContentQualityChecker        # Overall validation

content_generation.py            # Base template system (fallback)
└── ContextualContentGenerator   # Cultural adaptations
```

## Cost Considerations

### OpenAI GPT-4 Pricing (as of 2024)
- Input: $0.03 per 1K tokens
- Output: $0.06 per 1K tokens
- Typical content (2000 words): ~$0.20-0.40 per generation

### Anthropic Claude Pricing
- Input: $0.003 per 1K tokens
- Output: $0.015 per 1K tokens
- Typical content (2000 words): ~$0.03-0.06 per generation

**💡 Cost Saving Tips:**
1. Use Claude for high-volume generation (cheaper)
2. Use GPT-4 for complex grant narratives (better reasoning)
3. Enable caching to reuse similar content
4. Set `max_tokens` appropriately for content type

## Troubleshooting

### No API Keys Available

**Error**: "No AI provider available, falling back to template-based generation"

**Solution**:
1. Check `.env` file exists
2. Verify API key is correct
3. Load environment variables: `from dotenv import load_dotenv; load_dotenv()`

### API Rate Limits

**Error**: "Rate limit exceeded"

**Solution**:
1. Wait and retry
2. Implement exponential backoff
3. Upgrade API plan
4. Use caching to reduce calls

### Quality Check Failures

**Issue**: Content fails quality checks

**Solution**:
1. Review quality report issues
2. Adjust context parameters (tone, audience)
3. Add specific requirements
4. Use feedback loop to regenerate

### Cultural Adaptation Not Applied

**Issue**: Hawaiian terms not appearing

**Solution**:
1. Verify `cultural_context="hawaiian"` in ContentContext
2. Check content length (very short content may not have terms)
3. Review specific_requirements for conflicts
4. Generate with higher temperature for more creativity

## Examples

### Example 1: Grant Narrative for Elder Care

```python
content = await generate_ai_content(
    content_type=ContentType.GRANT_NARRATIVE,
    target_audience="foundation program officers",
    cultural_context="hawaiian",
    emotional_tone="hopeful",
    specific_requirements={
        "focus": "Kupuna care coordination in Lower Puna",
        "amount_requested": "$50,000",
        "duration": "12 months",
        "include_statistics": True
    }
)
```

**Output includes:**
- Compelling narrative about community need
- Hawaiian cultural values integration
- Data on elder population
- Measurable outcomes
- Sustainability plan

### Example 2: Emergency Response Protocol

```python
content = await generate_ai_content(
    content_type=ContentType.DISASTER_RESPONSE,
    target_audience="community members",
    cultural_context="multicultural",
    emotional_tone="urgent",
    urgency_level="critical",
    specific_requirements={
        "situation": "Hurricane warning - 24 hours",
        "location": "Lower Puna"
    }
)
```

**Output includes:**
- Immediate safety actions (0-2 hours)
- Short-term priorities (2-24 hours)
- Emergency contact numbers
- Resource locations
- Clear, actionable steps

### Example 3: Volunteer Coordination Script

```python
content = await generate_ai_content(
    content_type=ContentType.VOLUNTEER_SCRIPT,
    target_audience="new volunteers",
    cultural_context="hawaiian",
    emotional_tone="warm",
    specific_requirements={
        "task": "Coordinating meal delivery to kupuna",
        "include_conversation_starters": True
    }
)
```

**Output includes:**
- Multiple greeting options (formal/informal)
- Cultural communication tips
- Conversation flow guide
- Common questions and responses
- Closing and follow-up

## Integration with Shoghi Platform

The AI content generator integrates seamlessly with existing Shoghi components:

```python
from shoghi_fixed import ShoghiPlatform
from ai_content_generator import generate_ai_content

# In your Shoghi workflow
async def generate_grant_content(request):
    # Use Shoghi to understand request
    analysis = shoghi.analyze_request(request)

    # Generate content with AI
    content = await generate_ai_content(
        content_type=ContentType.GRANT_NARRATIVE,
        target_audience=analysis['target_audience'],
        cultural_context=analysis['cultural_context'],
        specific_requirements=analysis['requirements']
    )

    return content
```

## Future Enhancements

Planned improvements:

1. **Template Library**: Reusable, version-controlled templates
2. **Active Learning**: Automatic improvement from usage patterns
3. **Multi-language**: Full translation support
4. **Moral Alignment**: Integration with Shoghi moral constraint system
5. **Collaborative Editing**: Real-time multi-user content refinement
6. **Analytics Dashboard**: Track content effectiveness over time

## Support

For issues or questions:
1. Check this README
2. Review test scripts for examples
3. Check logs for detailed error messages
4. Review `.env.example` for configuration options

## License

Part of the Shoghi community coordination platform.

---

**Remember**: Always protect your API keys and never commit them to version control! 🔒
