#!/usr/bin/env python3
"""
DYNAMIC CONTENT GENERATION SYSTEM
Generates and sources context-specific content on demand
Creates materials, documents, guides based on actual needs
"""

import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import uuid
import re
import hashlib
from enum import Enum

logger = logging.getLogger(__name__)

class ContentType(Enum):
    """Types of content that can be generated"""
    GRANT_NARRATIVE = "grant_narrative"
    CULTURAL_GUIDE = "cultural_guide"
    MENU_DESCRIPTION = "menu_description"
    VOLUNTEER_SCRIPT = "volunteer_script"
    ELDER_CARE_PROTOCOL = "elder_care_protocol"
    COMMUNITY_FLYER = "community_flyer"
    TRAINING_MATERIAL = "training_material"
    ONBOARDING_GUIDE = "onboarding_guide"
    DISASTER_RESPONSE = "disaster_response"
    FOOD_SAFETY = "food_safety"

@dataclass
class ContentContext:
    """Context for content generation"""
    content_type: ContentType
    target_audience: str
    cultural_context: str
    language: str
    emotional_tone: str
    urgency_level: str
    specific_requirements: Dict[str, Any]
    source_materials: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)

@dataclass
class GeneratedContent:
    """Generated content with metadata"""
    id: str
    content_type: ContentType
    title: str
    body: str
    metadata: Dict[str, Any]
    sources_used: List[str]
    generation_context: ContentContext
    created_at: datetime
    version: int = 1
    effectiveness_score: float = 0.0

class ContextualContentGenerator:
    """Generates content based on specific context and needs"""
    
    def __init__(self):
        self.content_cache = {}
        self.generation_history = []
        self.source_library = self._initialize_source_library()
        self.cultural_patterns = self._load_cultural_patterns()
        
    def _initialize_source_library(self) -> Dict[str, Any]:
        """Initialize library of source materials and patterns"""
        return {
            'hawaiian_values': {
                'aloha': 'Love, compassion, kindness',
                'ohana': 'Family, community, belonging',
                'malama': 'Care, preserve, protect',
                'kuleana': 'Responsibility, privilege',
                'pono': 'Righteousness, balance, harmony',
                'mana': 'Spiritual power, energy',
                'kokua': 'Help, assistance, cooperation'
            },
            'elder_care_principles': {
                'dignity': 'Preserve autonomy and respect',
                'safety': 'Physical and emotional wellbeing',
                'connection': 'Social engagement and relationships',
                'purpose': 'Meaningful activities and contribution',
                'comfort': 'Physical and environmental needs',
                'culture': 'Honor traditions and preferences'
            },
            'grant_components': {
                'need_statement': ['community assessment', 'demographic data', 'problem scope'],
                'approach': ['evidence-based', 'culturally appropriate', 'sustainable'],
                'outcomes': ['measurable', 'time-bound', 'impactful'],
                'evaluation': ['data collection', 'feedback loops', 'reporting']
            },
            'communication_styles': {
                'formal': {'tone': 'professional', 'structure': 'organized', 'vocabulary': 'technical'},
                'casual': {'tone': 'friendly', 'structure': 'conversational', 'vocabulary': 'simple'},
                'urgent': {'tone': 'direct', 'structure': 'prioritized', 'vocabulary': 'action-oriented'},
                'cultural': {'tone': 'respectful', 'structure': 'inclusive', 'vocabulary': 'multilingual'}
            }
        }
    
    def _load_cultural_patterns(self) -> Dict[str, Any]:
        """Load cultural communication patterns"""
        return {
            'hawaiian': {
                'greeting': 'Aloha',
                'gratitude': 'Mahalo',
                'elder_respect': 'Kupuna',
                'work_together': 'Laulima',
                'story_sharing': 'Talk story',
                'family_gathering': 'Ohana time'
            },
            'japanese': {
                'greeting': 'Konnichiwa',
                'gratitude': 'Arigato',
                'elder_respect': '-san, -sama',
                'apology_culture': 'Sumimasen',
                'group_harmony': 'Wa',
                'respect_forms': 'Keigo'
            },
            'filipino': {
                'greeting': 'Kumusta',
                'elder_respect': 'Po, Opo',
                'family_first': 'Kapamilya',
                'helping': 'Bayanihan',
                'blessing': 'Mano po'
            }
        }
    
    async def generate_content(self, context: ContentContext) -> GeneratedContent:
        """Generate content based on specific context"""
        
        # Analyze context to determine generation strategy
        strategy = self._determine_generation_strategy(context)
        
        # Source relevant materials
        source_materials = await self._source_relevant_materials(context)
        
        # Generate content structure
        structure = self._create_content_structure(context, strategy)
        
        # Generate actual content
        content = await self._generate_contextual_content(
            context, strategy, structure, source_materials
        )
        
        # Apply cultural and emotional adaptations
        adapted_content = self._apply_adaptations(content, context)
        
        # Create final content object
        generated = GeneratedContent(
            id=str(uuid.uuid4()),
            content_type=context.content_type,
            title=adapted_content['title'],
            body=adapted_content['body'],
            metadata=adapted_content['metadata'],
            sources_used=source_materials,
            generation_context=context,
            created_at=datetime.now()
        )
        
        # Cache for reuse
        self._cache_content(generated)
        
        return generated
    
    def _determine_generation_strategy(self, context: ContentContext) -> Dict[str, Any]:
        """Determine how to generate content based on context"""
        
        strategy = {
            'approach': 'standard',
            'components': [],
            'style': 'neutral',
            'length': 'medium'
        }
        
        # Adapt based on content type
        if context.content_type == ContentType.GRANT_NARRATIVE:
            strategy['approach'] = 'structured_narrative'
            strategy['components'] = ['need', 'approach', 'impact', 'sustainability']
            strategy['style'] = 'formal_persuasive'
            strategy['length'] = 'comprehensive'
            
        elif context.content_type == ContentType.ELDER_CARE_PROTOCOL:
            strategy['approach'] = 'step_by_step'
            strategy['components'] = ['safety', 'dignity', 'procedure', 'documentation']
            strategy['style'] = 'clear_respectful'
            strategy['length'] = 'detailed'
            
        elif context.content_type == ContentType.VOLUNTEER_SCRIPT:
            strategy['approach'] = 'conversational_guide'
            strategy['components'] = ['greeting', 'purpose', 'questions', 'closing']
            strategy['style'] = 'warm_adaptive'
            strategy['length'] = 'concise'
            
        elif context.content_type == ContentType.DISASTER_RESPONSE:
            strategy['approach'] = 'priority_based'
            strategy['components'] = ['immediate', 'short_term', 'long_term', 'resources']
            strategy['style'] = 'urgent_clear'
            strategy['length'] = 'actionable'
        
        # Adapt based on urgency
        if context.urgency_level == 'critical':
            strategy['length'] = 'minimal'
            strategy['style'] = 'direct_action'
            
        # Adapt based on audience
        if 'elder' in context.target_audience.lower():
            strategy['style'] = 'patient_respectful'
        elif 'volunteer' in context.target_audience.lower():
            strategy['style'] = 'engaging_supportive'
        elif 'funder' in context.target_audience.lower():
            strategy['style'] = 'professional_data_driven'
        
        return strategy
    
    async def _source_relevant_materials(self, context: ContentContext) -> List[str]:
        """Source relevant materials for content generation"""
        
        sources = []
        
        # Source from internal library
        if context.content_type == ContentType.GRANT_NARRATIVE:
            sources.extend([
                'grant_components.need_statement',
                'grant_components.approach',
                'grant_components.outcomes'
            ])
            
        if 'hawaiian' in context.cultural_context.lower():
            sources.append('hawaiian_values')
            sources.append('cultural_patterns.hawaiian')
            
        if context.content_type == ContentType.ELDER_CARE_PROTOCOL:
            sources.append('elder_care_principles')
        
        # Source from external knowledge (simulated)
        if context.specific_requirements.get('include_statistics'):
            sources.append('census_data_hawaii_2024')
            sources.append('elder_population_projections')
            
        if context.specific_requirements.get('include_success_stories'):
            sources.append('community_success_database')
            
        # Source from previous successful content
        similar_content = self._find_similar_successful_content(context)
        if similar_content:
            sources.append(f'previous_success:{similar_content["id"]}')
        
        return sources
    
    def _create_content_structure(self, context: ContentContext, 
                                 strategy: Dict[str, Any]) -> Dict[str, Any]:
        """Create structure for content based on strategy"""
        
        structure = {
            'sections': [],
            'flow': 'linear',
            'emphasis_points': [],
            'call_to_action': None
        }
        
        if strategy['approach'] == 'structured_narrative':
            structure['sections'] = [
                {'type': 'hook', 'length': 'short'},
                {'type': 'problem_statement', 'length': 'medium'},
                {'type': 'proposed_solution', 'length': 'detailed'},
                {'type': 'implementation', 'length': 'comprehensive'},
                {'type': 'expected_outcomes', 'length': 'medium'},
                {'type': 'evaluation_plan', 'length': 'short'},
                {'type': 'sustainability', 'length': 'medium'}
            ]
            structure['flow'] = 'problem_to_solution'
            structure['emphasis_points'] = ['community_need', 'cultural_alignment', 'measurable_impact']
            
        elif strategy['approach'] == 'step_by_step':
            structure['sections'] = [
                {'type': 'preparation', 'checklist': True},
                {'type': 'main_steps', 'numbered': True},
                {'type': 'safety_notes', 'highlighted': True},
                {'type': 'troubleshooting', 'conditional': True}
            ]
            structure['flow'] = 'sequential'
            structure['emphasis_points'] = ['safety', 'dignity', 'clear_actions']
            
        elif strategy['approach'] == 'conversational_guide':
            structure['sections'] = [
                {'type': 'opening', 'variations': 3},
                {'type': 'rapport_building', 'cultural_sensitive': True},
                {'type': 'information_gathering', 'adaptive': True},
                {'type': 'action_items', 'confirmable': True},
                {'type': 'closing', 'warm': True}
            ]
            structure['flow'] = 'adaptive'
            structure['emphasis_points'] = ['warmth', 'respect', 'clarity']
            
        elif strategy['approach'] == 'priority_based':
            structure['sections'] = [
                {'type': 'immediate_actions', 'time': '0-2 hours'},
                {'type': 'day_one_priorities', 'time': '2-24 hours'},
                {'type': 'week_one_tasks', 'time': '1-7 days'},
                {'type': 'ongoing_support', 'time': '7+ days'}
            ]
            structure['flow'] = 'temporal_priority'
            structure['emphasis_points'] = ['safety_first', 'clear_timeline', 'resource_links']
        
        return structure
    
    async def _generate_contextual_content(self, context: ContentContext,
                                          strategy: Dict[str, Any],
                                          structure: Dict[str, Any],
                                          sources: List[str]) -> Dict[str, Any]:
        """Generate the actual content"""
        
        content = {
            'title': '',
            'body': '',
            'metadata': {},
            'sections': []
        }
        
        # Generate title based on context
        content['title'] = self._generate_contextual_title(context, strategy)
        
        # Generate each section
        for section in structure['sections']:
            section_content = await self._generate_section(
                section, context, strategy, sources
            )
            content['sections'].append(section_content)
            content['body'] += f"\n\n{section_content['content']}"
        
        # Add metadata
        content['metadata'] = {
            'generated_for': context.target_audience,
            'urgency': context.urgency_level,
            'language': context.language,
            'cultural_context': context.cultural_context,
            'emphasis_points': structure['emphasis_points']
        }
        
        return content
    
    def _generate_contextual_title(self, context: ContentContext, 
                                  strategy: Dict[str, Any]) -> str:
        """Generate appropriate title for content"""
        
        if context.content_type == ContentType.GRANT_NARRATIVE:
            base = "Community Support Initiative"
            if 'elder' in str(context.specific_requirements):
                base = "Kupuna Care Enhancement Program"
            elif 'food' in str(context.specific_requirements):
                base = "Aina Food Sovereignty Initiative"
                
        elif context.content_type == ContentType.ELDER_CARE_PROTOCOL:
            base = "Care Protocol"
            if context.urgency_level == 'critical':
                base = "Emergency Response Protocol"
            else:
                base = "Daily Care Guidelines"
                
        elif context.content_type == ContentType.VOLUNTEER_SCRIPT:
            base = "Volunteer Coordination Guide"
            if context.cultural_context == 'hawaiian':
                base = "Kokua Volunteer Guide"
                
        else:
            base = f"{context.content_type.value.replace('_', ' ').title()}"
        
        # Add context specifics
        if context.target_audience:
            base += f" for {context.target_audience}"
        
        return base
    
    async def _generate_section(self, section: Dict[str, Any],
                               context: ContentContext,
                               strategy: Dict[str, Any],
                               sources: List[str]) -> Dict[str, Any]:
        """Generate individual section content"""
        
        section_content = {
            'type': section.get('type', 'standard'),
            'content': '',
            'formatting': {}
        }
        
        # Generate based on section type
        if section['type'] == 'hook':
            section_content['content'] = self._generate_hook(context, sources)
            
        elif section['type'] == 'problem_statement':
            section_content['content'] = self._generate_problem_statement(context, sources)
            
        elif section['type'] == 'proposed_solution':
            section_content['content'] = self._generate_solution(context, sources)
            
        elif section['type'] == 'preparation':
            section_content['content'] = self._generate_preparation_checklist(context)
            
        elif section['type'] == 'main_steps':
            section_content['content'] = self._generate_numbered_steps(context)
            
        elif section['type'] == 'opening':
            section_content['content'] = self._generate_conversation_openings(context)
            
        elif section['type'] == 'immediate_actions':
            section_content['content'] = self._generate_immediate_actions(context)
        
        else:
            # Default generation
            section_content['content'] = self._generate_generic_section(
                section['type'], context, sources
            )
        
        return section_content
    
    def _generate_hook(self, context: ContentContext, sources: List[str]) -> str:
        """Generate engaging opening"""
        
        if context.emotional_tone == 'urgent':
            return "Our community faces an immediate need that requires coordinated action."
        elif context.emotional_tone == 'hopeful':
            return "Together, we have an opportunity to transform our community's future."
        elif 'elder' in str(context.specific_requirements):
            return "Our kupuna have cared for us. Now it's our kuleana to care for them."
        else:
            return "This initiative addresses a critical community need with sustainable solutions."
    
    def _generate_problem_statement(self, context: ContentContext, 
                                   sources: List[str]) -> str:
        """Generate problem statement"""
        
        base = "Current Situation:\n"
        
        if 'elder' in str(context.specific_requirements):
            base += """
Lower Puna's elder population faces increasing isolation and limited access to services.
With 23% of residents over 65 and minimal public transportation, many kupuna struggle
to access healthcare, groceries, and social connections. Recent lava flows have 
displaced traditional support networks, leaving gaps in community care systems.
"""
        elif 'food' in str(context.specific_requirements):
            base += """
Hawaii imports 85% of its food, creating vulnerability in supply chains and food security.
Local families spend 30% more on groceries than mainland counterparts, while local
farmers struggle to connect with consumers. This disconnect threatens both food
sovereignty and economic sustainability.
"""
        else:
            base += """
The community faces challenges in coordinating resources and services effectively.
Despite willing volunteers and available resources, lack of coordination leads to
gaps in service delivery and duplicated efforts.
"""
        
        return base
    
    def _generate_solution(self, context: ContentContext, sources: List[str]) -> str:
        """Generate proposed solution"""
        
        base = "Proposed Approach:\n"
        
        # Add cultural values if Hawaiian context
        if 'hawaiian' in context.cultural_context.lower():
            base += "\nGrounded in Hawaiian values of ohana (family) and malama (care), "
        
        base += "our approach coordinates existing resources through "
        
        if context.content_type == ContentType.GRANT_NARRATIVE:
            base += """
three integrated components:

1. **Community Assessment**: Map existing resources and identify service gaps
2. **Coordination Platform**: Connect providers, volunteers, and recipients
3. **Sustainable Systems**: Build capacity for long-term community resilience

Each component reinforces the others, creating a self-sustaining support network.
"""
        else:
            base += "systematic coordination and community engagement."
        
        return base
    
    def _generate_preparation_checklist(self, context: ContentContext) -> str:
        """Generate preparation checklist"""
        
        checklist = "**Before Beginning:**\n\n"
        
        if context.content_type == ContentType.ELDER_CARE_PROTOCOL:
            checklist += """
□ Confirm elder's preferences and consent
□ Review medical information and medications
□ Prepare necessary supplies
□ Ensure emergency contacts are available
□ Check cultural or dietary requirements
□ Verify transportation if needed
"""
        else:
            checklist += """
□ Review objectives and requirements
□ Gather necessary materials
□ Confirm participant availability
□ Prepare documentation
□ Test equipment if applicable
"""
        
        return checklist
    
    def _generate_numbered_steps(self, context: ContentContext) -> str:
        """Generate numbered procedural steps"""
        
        steps = "**Procedure:**\n\n"
        
        if context.content_type == ContentType.ELDER_CARE_PROTOCOL:
            steps += """
1. **Greeting and Rapport**
   - Use preferred name and title
   - Make eye contact and smile
   - Ask about comfort and immediate needs

2. **Assessment**
   - Check physical comfort (temperature, position)
   - Assess emotional state
   - Review any changes since last visit

3. **Service Delivery**
   - Explain each action before doing it
   - Maintain dignity and autonomy
   - Encourage participation where possible

4. **Documentation**
   - Record services provided
   - Note any concerns or changes
   - Update care plan if needed

5. **Closing**
   - Confirm next visit time
   - Ensure elder has everything needed
   - Provide contact for emergencies
"""
        else:
            steps += "1. Initial setup\n2. Main process\n3. Verification\n4. Completion"
        
        return steps
    
    def _generate_conversation_openings(self, context: ContentContext) -> str:
        """Generate culturally appropriate conversation starters"""
        
        openings = "**Greeting Options:**\n\n"
        
        if 'hawaiian' in context.cultural_context.lower():
            openings += """
**Warm/Familiar:**
"Aloha [Name]! How you stay today?"
"Hey [Name], howzit? Long time no see!"

**Respectful/Elder:**
"Aloha Aunty/Uncle [Name]. How are you feeling today?"
"Good morning [Title] [Name]. Is this a good time to talk story?"

**First Contact:**
"Aloha, my name is [Your Name] from [Organization]. 
 I'm calling to see how we can kokua (help) with [specific need]."
"""
        else:
            openings += """
**Standard:**
"Hello [Name], this is [Your Name] from [Organization]."

**Warm:**
"Hi [Name]! I hope you're having a good day."

**Professional:**
"Good [morning/afternoon] [Name]. Thank you for your time."
"""
        
        return openings
    
    def _generate_immediate_actions(self, context: ContentContext) -> str:
        """Generate immediate action items"""
        
        if context.urgency_level == 'critical':
            return """
**IMMEDIATE ACTIONS (0-2 hours):**

1. **Safety First**
   - Ensure physical safety of all involved
   - Contact emergency services if needed (911)
   - Move to secure location

2. **Critical Needs**
   - Water and medications
   - Emergency shelter if displaced
   - Medical attention for injuries

3. **Communication**
   - Notify family/emergency contacts
   - Register with emergency services
   - Update status for coordination

4. **Resources**
   - Red Cross: 1-800-RED-CROSS
   - County Emergency: 808-935-0031
   - Crisis Line: 988
"""
        else:
            return "Begin with assessment of current situation and available resources."
    
    def _generate_generic_section(self, section_type: str, 
                                 context: ContentContext,
                                 sources: List[str]) -> str:
        """Fallback generic section generation"""
        
        return f"""
This section addresses {section_type.replace('_', ' ')} for {context.target_audience}.
Content has been adapted for {context.cultural_context} context with 
{context.emotional_tone} tone. Further customization may be needed based on
specific circumstances.
"""
    
    def _apply_adaptations(self, content: Dict[str, Any], 
                          context: ContentContext) -> Dict[str, Any]:
        """Apply cultural and emotional adaptations to content"""
        
        adapted = content.copy()
        
        # Apply cultural adaptations
        if 'hawaiian' in context.cultural_context.lower():
            adapted['body'] = self._apply_hawaiian_adaptations(adapted['body'])
        elif 'japanese' in context.cultural_context.lower():
            adapted['body'] = self._apply_japanese_adaptations(adapted['body'])
        
        # Apply emotional tone
        if context.emotional_tone == 'urgent':
            adapted['body'] = self._make_urgent(adapted['body'])
        elif context.emotional_tone == 'supportive':
            adapted['body'] = self._make_supportive(adapted['body'])
        elif context.emotional_tone == 'formal':
            adapted['body'] = self._make_formal(adapted['body'])
        
        # Apply language simplification if needed
        if 'simple' in str(context.constraints):
            adapted['body'] = self._simplify_language(adapted['body'])
        
        return adapted
    
    def _apply_hawaiian_adaptations(self, text: str) -> str:
        """Apply Hawaiian cultural elements"""
        
        # Add appropriate Hawaiian terms
        replacements = {
            'elderly': 'kupuna',
            'help': 'kokua',
            'family': 'ohana',
            'responsibility': 'kuleana',
            'work together': 'laulima',
            'take care': 'malama'
        }
        
        for english, hawaiian in replacements.items():
            # Keep English in parentheses for clarity
            text = text.replace(english, f"{hawaiian} ({english})")
        
        return text
    
    def _apply_japanese_adaptations(self, text: str) -> str:
        """Apply Japanese cultural elements"""
        
        # Add respectful forms
        text = text.replace('Mr.', 'san')
        text = text.replace('Mrs.', 'san')
        
        # Add cultural notes
        if 'elder' in text.lower():
            text += "\n\n*Note: Please use respectful language (keigo) when speaking with elders.*"
        
        return text
    
    def _make_urgent(self, text: str) -> str:
        """Make text more urgent and action-oriented"""
        
        # Add urgency markers
        text = "**IMMEDIATE ACTION REQUIRED**\n\n" + text
        
        # Make sentences shorter and more direct
        text = text.replace('should consider', 'must')
        text = text.replace('it would be beneficial', 'essential to')
        text = text.replace('when possible', 'immediately')
        
        return text
    
    def _make_supportive(self, text: str) -> str:
        """Make text more supportive and encouraging"""
        
        # Add supportive language
        text = text.replace('must', 'can')
        text = text.replace('required', 'helpful')
        
        # Add encouragement
        if 'steps' in text.lower():
            text += "\n\nRemember: Take it one step at a time. You're doing great!"
        
        return text
    
    def _make_formal(self, text: str) -> str:
        """Make text more formal and professional"""
        
        # Formalize language
        text = text.replace("don't", "do not")
        text = text.replace("can't", "cannot")
        text = text.replace("we'll", "we will")
        
        return text
    
    def _simplify_language(self, text: str) -> str:
        """Simplify language for accessibility"""
        
        # Replace complex words with simple ones
        simplifications = {
            'utilize': 'use',
            'implement': 'start',
            'facilitate': 'help',
            'coordinate': 'organize',
            'assessment': 'check',
            'documentation': 'notes'
        }
        
        for complex, simple in simplifications.items():
            text = text.replace(complex, simple)
        
        return text
    
    def _cache_content(self, content: GeneratedContent):
        """Cache generated content for reuse"""
        
        cache_key = self._generate_cache_key(content.generation_context)
        self.content_cache[cache_key] = content
        self.generation_history.append({
            'id': content.id,
            'type': content.content_type.value,
            'timestamp': content.created_at,
            'effectiveness': content.effectiveness_score
        })
    
    def _generate_cache_key(self, context: ContentContext) -> str:
        """Generate cache key from context"""
        
        key_parts = [
            context.content_type.value,
            context.target_audience,
            context.cultural_context,
            context.urgency_level
        ]
        
        key_string = '_'.join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _find_similar_successful_content(self, context: ContentContext) -> Optional[Dict]:
        """Find previously successful similar content"""
        
        # Look for content with same type and high effectiveness
        for item in self.generation_history:
            if (item.get('type') == context.content_type.value and 
                item.get('effectiveness', 0) > 0.7):
                return item
        
        return None
    
    async def generate_multimodal_content(self, context: ContentContext) -> Dict[str, Any]:
        """Generate content in multiple formats (text, audio script, visual)"""
        
        # Generate base text content
        text_content = await self.generate_content(context)
        
        # Generate audio script version
        audio_script = self._generate_audio_script(text_content, context)
        
        # Generate visual layout suggestions
        visual_layout = self._generate_visual_layout(text_content, context)
        
        # Generate interactive elements
        interactive = self._generate_interactive_elements(text_content, context)
        
        return {
            'text': text_content,
            'audio_script': audio_script,
            'visual_layout': visual_layout,
            'interactive': interactive,
            'formats': ['text', 'audio', 'visual', 'interactive']
        }
    
    def _generate_audio_script(self, content: GeneratedContent, 
                              context: ContentContext) -> Dict[str, Any]:
        """Generate audio/voice script from content"""
        
        script = {
            'narrator_notes': '',
            'dialogue': [],
            'pacing': 'normal',
            'tone': context.emotional_tone,
            'emphasis_words': []
        }
        
        # Convert content to speakable format
        text = content.body
        
        # Remove formatting marks
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # Remove bold
        text = re.sub(r'##?\s+', '', text)  # Remove headers
        
        # Add pauses
        text = text.replace('\n\n', ' [PAUSE] ')
        
        # Add emphasis markers
        if context.urgency_level == 'critical':
            script['emphasis_words'] = ['immediate', 'now', 'urgent', 'critical']
            script['pacing'] = 'quick'
        
        script['dialogue'] = text.split('[PAUSE]')
        
        # Add narrator notes
        if context.cultural_context == 'hawaiian':
            script['narrator_notes'] = "Use warm, welcoming tone. Pronounce Hawaiian words correctly."
        
        return script
    
    def _generate_visual_layout(self, content: GeneratedContent,
                               context: ContentContext) -> Dict[str, Any]:
        """Generate visual layout suggestions"""
        
        layout = {
            'format': 'standard',
            'colors': {},
            'typography': {},
            'images_suggested': [],
            'icons_needed': []
        }
        
        # Determine format based on content type
        if context.content_type == ContentType.COMMUNITY_FLYER:
            layout['format'] = 'flyer_single_page'
            layout['colors'] = {
                'primary': '#2D5016',  # Forest green
                'secondary': '#8B4513',  # Saddle brown
                'accent': '#FFD700'  # Gold
            }
            layout['images_suggested'] = ['community_gathering', 'helping_hands']
            
        elif context.content_type == ContentType.DISASTER_RESPONSE:
            layout['format'] = 'infographic_priority'
            layout['colors'] = {
                'urgent': '#FF0000',
                'warning': '#FFA500',
                'safe': '#00FF00'
            }
            layout['icons_needed'] = ['emergency', 'shelter', 'water', 'medical']
        
        # Typography based on audience
        if 'elder' in context.target_audience:
            layout['typography'] = {
                'min_size': 14,
                'preferred_size': 16,
                'font_family': 'sans-serif',
                'line_height': 1.5
            }
        
        return layout
    
    def _generate_interactive_elements(self, content: GeneratedContent,
                                      context: ContentContext) -> Dict[str, Any]:
        """Generate interactive elements for digital content"""
        
        interactive = {
            'clickable_elements': [],
            'forms': [],
            'navigation': 'linear',
            'user_inputs': []
        }
        
        if context.content_type == ContentType.VOLUNTEER_SCRIPT:
            interactive['forms'] = [
                {
                    'type': 'checklist',
                    'items': ['contacted', 'availability_confirmed', 'task_assigned']
                }
            ]
            interactive['user_inputs'] = ['volunteer_name', 'contact_time', 'notes']
            
        elif context.content_type == ContentType.GRANT_NARRATIVE:
            interactive['navigation'] = 'sectioned'
            interactive['clickable_elements'] = ['table_of_contents', 'section_jumps']
        
        return interactive

# Content effectiveness tracker
class ContentEffectivenessTracker:
    """Track and improve content effectiveness"""
    
    def __init__(self):
        self.metrics = {}
        self.feedback_log = []
        
    def track_usage(self, content_id: str, usage_context: Dict[str, Any]):
        """Track how content is used"""
        
        if content_id not in self.metrics:
            self.metrics[content_id] = {
                'uses': 0,
                'completion_rate': [],
                'user_ratings': [],
                'modifications': [],
                'outcomes': []
            }
        
        self.metrics[content_id]['uses'] += 1
        
        if usage_context.get('completed'):
            self.metrics[content_id]['completion_rate'].append(1)
        else:
            self.metrics[content_id]['completion_rate'].append(0)
    
    def record_feedback(self, content_id: str, feedback: Dict[str, Any]):
        # existing logic updates self.metrics
        """Record user feedback on content"""
        
        self.feedback_log.append({
            'content_id': content_id,
            'timestamp': datetime.now(),
            'feedback': feedback
        })
        
        if content_id in self.metrics and 'rating' in feedback:
            self.metrics[content_id]['user_ratings'].append(feedback['rating'])
    
    def calculate_effectiveness(self, content_id: str) -> float:
        """Calculate effectiveness score for content"""
        
        if content_id not in self.metrics:
            return 0.5  # Default neutral score
        
        metrics = self.metrics[content_id]
        
        # Calculate components
        if metrics['completion_rate']:
            completion = sum(metrics['completion_rate']) / len(metrics['completion_rate'])
        else:
            completion = 0.5
            
        if metrics['user_ratings']:
            rating = sum(metrics['user_ratings']) / len(metrics['user_ratings']) / 5.0
        else:
            rating = 0.5
        
        # Weight: 60% completion, 40% rating
        effectiveness = (completion * 0.6) + (rating * 0.4)
        
        return effectiveness
    
    def get_improvement_suggestions(self, content_id: str) -> List[str]:
        """Generate suggestions for improving content"""
        
        suggestions = []
        
        if content_id not in self.metrics:
            return ["No usage data available yet"]
        
        metrics = self.metrics[content_id]
        
        # Check completion rate
        if metrics['completion_rate'] and sum(metrics['completion_rate'])/len(metrics['completion_rate']) < 0.5:
            suggestions.append("Low completion rate - consider shortening or simplifying")
        
        # Check ratings
        if metrics['user_ratings'] and sum(metrics['user_ratings'])/len(metrics['user_ratings']) < 3:
            suggestions.append("Low user ratings - review feedback for specific issues")
        
        # Check modifications
        if len(metrics['modifications']) > metrics['uses'] * 0.3:
            suggestions.append("Frequently modified - consider updating base template")
        
        return suggestions

# Create singleton instances
content_generator = ContextualContentGenerator()
effectiveness_tracker = ContentEffectivenessTracker()
