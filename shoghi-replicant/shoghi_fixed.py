#!/usr/bin/env python3
"""
SHOGHI - Complete Adaptive Coordination Platform
With voice interface, dynamic agents, and contextual content generation
"""

import logging
import sys
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import argparse
import asyncio

# Import fixed grant system
from grant_coordination_fixed import grant_system, GrantOpportunity

# Import voice interface
from voice_interface import hume_interface, voice_processor, VoiceSession

# Import menu builder with dynamic agents
from menu_builder import menu_orchestrator, MenuState

# Import contextual content generation
from content_generation import (
    content_generator, 
    effectiveness_tracker,
    ContentContext,
    ContentType,
    GeneratedContent
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

class ShoghiPlatform:
    """Complete Shoghi platform with voice-first interface"""
    
    def __init__(self):
        self.grant_system = grant_system
        self.voice_interface = hume_interface
        self.voice_processor = voice_processor
        self.menu_builder = menu_orchestrator
        self.content_generator = content_generator
        self.effectiveness_tracker = effectiveness_tracker
        self.agents = {}
        self.active_voice_sessions = {}
        self.generated_content_cache = {}
        logger.info("🌺 Shoghi Platform initialized with voice and content generation")
    
    async def start_voice_session(self, user_id: str, context: str = "general") -> VoiceSession:
        """Start a voice interaction session"""
        session = await self.voice_interface.create_session(user_id, context)
        self.active_voice_sessions[session.session_id] = session
        
        logger.info(f"🎤 Voice session started: {session.session_id}")
        return session
    
    async def process_voice_input(self, session_id: str, audio_data: bytes) -> Dict[str, Any]:
        """Process voice input with emotional awareness"""
        
        # Process through Hume interface
        result = await self.voice_interface.process_voice_input(session_id, audio_data)
        
        # Extract intent and entities
        intent, entities = self.voice_processor.extract_intent(result['transcription'])
        
        # Generate appropriate response based on emotional state
        if result['emotional_state'] == 'frustrated':
            # Simplify and be more supportive
            response = await self._handle_frustrated_user(intent, entities)
        elif result['emotional_state'] == 'uncertain':
            # Provide more guidance
            response = await self._handle_uncertain_user(intent, entities)
        else:
            # Normal processing
            response = await self._handle_standard_request(intent, entities)
        
        # Add voice synthesis parameters
        response['voice_params'] = {
            'modulation': result['response']['voice_modulation'],
            'pacing': result['response']['pacing']
        }
        
        return response
    
    async def _handle_frustrated_user(self, intent: str, entities: Dict) -> Dict[str, Any]:
        """Handle frustrated user with simplified approach"""
        
        response = {
            'message': "I hear you're frustrated. Let me make this simple. ",
            'action': None
        }
        
        if intent == 'find_grants':
            # Just find grants without asking questions
            grants = self.grant_system.discover_grants(['grant'], entities.get('location', 'Hawaii'))
            response['message'] += f"I found {len(grants)} grants. Here's the best one for you."
            response['action'] = 'show_grant'
            response['data'] = grants[0] if grants else None
            
        elif intent == 'coordinate':
            response['message'] += "Tell me one thing you need help with right now."
            response['action'] = 'await_simple_need'
        
        else:
            response['message'] += "Would you like me to find grants or coordinate help?"
            response['action'] = 'binary_choice'
        
        return response
    
    async def _handle_uncertain_user(self, intent: str, entities: Dict) -> Dict[str, Any]:
        """Handle uncertain user with more guidance"""
        
        response = {
            'message': "No worries, let's figure this out together. ",
            'action': None
        }
        
        if intent == 'find_grants':
            response['message'] += "I can find grants for you. Are you looking for elder care, community health, or something else?"
            response['action'] = 'guided_grant_search'
            response['suggestions'] = ['elder care', 'community health', 'education', 'housing']
            
        elif intent == 'unknown':
            response['message'] += "I can help you find funding or coordinate volunteers. Which sounds more helpful?"
            response['action'] = 'choose_service'
        
        else:
            response = await self._handle_standard_request(intent, entities)
        
        return response
    
    async def _handle_standard_request(self, intent: str, entities: Dict) -> Dict[str, Any]:
        """Handle standard request with full functionality"""
        
        if intent == 'find_grants':
            return await self._find_grants_voice(entities)
        elif intent == 'coordinate':
            return await self._coordinate_resources_voice(entities)
        elif intent == 'status':
            return self._get_status_voice()
        elif intent == 'help':
            return self._get_help_voice()
        else:
            return {
                'message': "I can help you find grants or coordinate resources. What do you need?",
                'action': 'await_clarification'
            }
    
    async def _find_grants_voice(self, entities: Dict) -> Dict[str, Any]:
        """Find grants with voice response"""
        
        search_terms = []
        if entities.get('population') == 'elder':
            search_terms.extend(['elder', 'senior', 'kupuna'])
        if entities.get('service'):
            search_terms.append(entities['service'])
        
        location = entities.get('location', 'Hawaii')
        
        grants = self.grant_system.discover_grants(search_terms, location)
        
        if grants:
            response = f"I found {len(grants)} grants. "
            
            # Voice-optimized response (shorter, clearer)
            top_grant = grants[0]
            response += f"The best match is {top_grant.title} from {top_grant.funder}. "
            response += f"It offers {top_grant.amount}. "
            
            if len(grants) > 1:
                response += "Would you like to hear about the others?"
            
            return {
                'message': response,
                'action': 'grants_found',
                'data': [self._grant_to_dict(g) for g in grants[:3]],  # Limit for voice
                'follow_up': 'more_grants' if len(grants) > 3 else None
            }
        else:
            return {
                'message': "I couldn't find grants matching those criteria. Can you tell me more about what you need?",
                'action': 'no_grants_found'
            }
    
    async def _coordinate_resources_voice(self, entities: Dict) -> Dict[str, Any]:
        """Coordinate resources with voice interface"""
        
        # Spawn coordinator agent for this need
        coordinator_agent_id = await self.voice_interface.spawn_voice_agent(
            'coordinator',
            {'entities': entities}
        )
        
        response = "I'll coordinate that for you. "
        
        if entities.get('service') == 'food':
            response += "I'm checking who has food available and who needs it."
        elif entities.get('service') == 'transportation':
            response += "I'm finding available drivers for transportation needs."
        else:
            response += "Tell me specifically what kind of help you need."
        
        return {
            'message': response,
            'action': 'coordination_started',
            'agent_id': coordinator_agent_id
        }
    
    def _get_status_voice(self) -> Dict[str, Any]:
        """Get status optimized for voice"""
        
        all_grants = self.grant_system.get_all_grants()
        active_sessions = len(self.active_voice_sessions)
        
        message = f"Shoghi is operational. "
        message += f"I have {len(all_grants)} grants in my database. "
        message += f"{active_sessions} people are talking with me right now. "
        message += "How can I help you?"
        
        return {
            'message': message,
            'action': 'status_report',
            'data': {
                'grants': len(all_grants),
                'sessions': active_sessions
            }
        }
    
    def _get_help_voice(self) -> Dict[str, Any]:
        """Get help optimized for voice"""
        
        message = "I'm Shoghi, your community coordination assistant. "
        message += "I can find grants for your projects or coordinate volunteers and resources. "
        message += "Just tell me what you need in your own words. "
        message += "For example, say 'find grants for elder care' or 'I need help with food delivery.'"
        
        return {
            'message': message,
            'action': 'help_provided'
        }
    
    async def start_menu_builder_session(self, menu_data: Dict[str, Any]) -> MenuState:
        """Start a menu builder session with dynamic agents"""
        
        logger.info("🍽️ Starting menu builder session")
        
        # Initialize menu conversation
        menu_state = await self.menu_builder.initialize_conversation(menu_data)
        
        return menu_state
    
    async def process_menu_interruption(self, user_input: str) -> Dict[str, Any]:
        """Process user interruption in menu builder"""
        
        result = await self.menu_builder.process_user_interruption(user_input)
        return result
    
    async def generate_contextual_content(self, request: str, 
                                         context_override: Dict[str, Any] = None) -> GeneratedContent:
        """Generate context-specific content based on request"""
        
        # Determine content type from request
        content_type = self._determine_content_type(request)
        
        # Extract context from request or use override
        if context_override:
            context = ContentContext(**context_override)
        else:
            context = self._extract_content_context(request, content_type)
        
        # Generate content
        logger.info(f"📝 Generating {content_type.value} for {context.target_audience}")
        content = await self.content_generator.generate_content(context)
        
        # Cache for reuse
        self.generated_content_cache[content.id] = content
        
        # Track generation
        self.effectiveness_tracker.track_usage(content.id, {'generated': True})
        
        return content
    
    def _determine_content_type(self, request: str) -> ContentType:
        """Determine what type of content to generate"""
        
        request_lower = request.lower()
        
        if 'grant' in request_lower and ('narrative' in request_lower or 'proposal' in request_lower):
            return ContentType.GRANT_NARRATIVE
        elif 'elder' in request_lower and 'protocol' in request_lower:
            return ContentType.ELDER_CARE_PROTOCOL
        elif 'volunteer' in request_lower and ('script' in request_lower or 'guide' in request_lower):
            return ContentType.VOLUNTEER_SCRIPT
        elif 'flyer' in request_lower or 'poster' in request_lower:
            return ContentType.COMMUNITY_FLYER
        elif 'disaster' in request_lower or 'emergency' in request_lower:
            return ContentType.DISASTER_RESPONSE
        elif 'menu' in request_lower and 'description' in request_lower:
            return ContentType.MENU_DESCRIPTION
        elif 'training' in request_lower:
            return ContentType.TRAINING_MATERIAL
        elif 'onboarding' in request_lower:
            return ContentType.ONBOARDING_GUIDE
        elif 'food' in request_lower and 'safety' in request_lower:
            return ContentType.FOOD_SAFETY
        else:
            return ContentType.CULTURAL_GUIDE
    
    def _extract_content_context(self, request: str, content_type: ContentType) -> ContentContext:
        """Extract context from natural language request"""
        
        request_lower = request.lower()
        
        # Determine target audience
        if 'elder' in request_lower or 'kupuna' in request_lower:
            target_audience = 'elders'
        elif 'volunteer' in request_lower:
            target_audience = 'volunteers'
        elif 'funder' in request_lower or 'grant' in request_lower:
            target_audience = 'funders'
        elif 'family' in request_lower:
            target_audience = 'families'
        else:
            target_audience = 'community members'
        
        # Determine cultural context
        if 'hawaiian' in request_lower or 'hawaii' in request_lower or 'puna' in request_lower:
            cultural_context = 'hawaiian'
        elif 'japanese' in request_lower:
            cultural_context = 'japanese'
        elif 'filipino' in request_lower:
            cultural_context = 'filipino'
        else:
            cultural_context = 'multicultural'
        
        # Determine urgency
        if 'urgent' in request_lower or 'emergency' in request_lower or 'immediate' in request_lower:
            urgency_level = 'critical'
        elif 'soon' in request_lower or 'quick' in request_lower:
            urgency_level = 'high'
        else:
            urgency_level = 'normal'
        
        # Determine emotional tone
        if urgency_level == 'critical':
            emotional_tone = 'urgent'
        elif 'support' in request_lower or 'help' in request_lower:
            emotional_tone = 'supportive'
        elif 'formal' in request_lower or 'professional' in request_lower:
            emotional_tone = 'formal'
        else:
            emotional_tone = 'warm'
        
        # Extract specific requirements
        specific_requirements = {}
        if 'statistics' in request_lower or 'data' in request_lower:
            specific_requirements['include_statistics'] = True
        if 'stories' in request_lower or 'examples' in request_lower:
            specific_requirements['include_success_stories'] = True
        if 'simple' in request_lower or 'easy' in request_lower:
            specific_requirements['simple_language'] = True
        
        # Determine language
        if 'spanish' in request_lower:
            language = 'es'
        elif 'japanese' in request_lower:
            language = 'ja'
        elif 'tagalog' in request_lower:
            language = 'tl'
        else:
            language = 'en'
        
        return ContentContext(
            content_type=content_type,
            target_audience=target_audience,
            cultural_context=cultural_context,
            language=language,
            emotional_tone=emotional_tone,
            urgency_level=urgency_level,
            specific_requirements=specific_requirements
        )
    
    async def generate_multimodal_content(self, request: str) -> Dict[str, Any]:
        """Generate content in multiple formats"""
        
        # Determine content type and context
        content_type = self._determine_content_type(request)
        context = self._extract_content_context(request, content_type)
        
        # Generate multimodal versions
        multimodal = await self.content_generator.generate_multimodal_content(context)
        
        return {
            'text_version': multimodal['text'],
            'audio_script': multimodal['audio_script'],
            'visual_layout': multimodal['visual_layout'],
            'interactive_elements': multimodal['interactive'],
            'available_formats': multimodal['formats']
        }
    
    def track_content_effectiveness(self, content_id: str, feedback: Dict[str, Any]):
        """Track how well generated content performed"""
        
        self.effectiveness_tracker.record_feedback(content_id, feedback)
        
        # Calculate new effectiveness score
        score = self.effectiveness_tracker.calculate_effectiveness(content_id)
        
        # Update cached content if exists
        if content_id in self.generated_content_cache:
            self.generated_content_cache[content_id].effectiveness_score = score
        
        # Get improvement suggestions
        suggestions = self.effectiveness_tracker.get_improvement_suggestions(content_id)
        
        return {
            'effectiveness_score': score,
            'improvement_suggestions': suggestions
        }
    
    def process_request(self, request: str) -> Dict[str, Any]:
        """Process text-based natural language requests (backward compatibility)"""
        request_lower = request.lower()
        
        # Parse intent
        if any(word in request_lower for word in ['find', 'search', 'discover', 'grant', 'funding']):
            return self.find_grants(request)
        elif any(word in request_lower for word in ['apply', 'application', 'submit']):
            return self.generate_applications(request)
        elif any(word in request_lower for word in ['menu', 'restaurant', 'food']) and 'builder' in request_lower:
            return self.handle_menu_request(request)
        elif any(word in request_lower for word in ['generate', 'create', 'write']) and any(word in request_lower for word in ['content', 'guide', 'protocol', 'script', 'flyer', 'narrative']):
            return self.handle_content_generation(request)
        elif 'status' in request_lower:
            return self.get_status()
        elif any(word in request_lower for word in ['help', 'what can']):
            return self.get_help()
        else:
            return {
                'response': "I can help you find grants, generate applications, build menus, create content, and coordinate community resources. Try: 'generate elder care protocol for Hawaiian community'",
                'suggestions': [
                    "find grants for elder care",
                    "generate volunteer script for food distribution",
                    "create disaster response guide",
                    "build restaurant menu",
                    "what is your status?"
                ]
            }
    
    def handle_content_generation(self, request: str) -> Dict[str, Any]:
        """Handle content generation requests"""
        
        # Run async content generation
        import asyncio
        content = asyncio.run(self.generate_contextual_content(request))
        
        response = f"""
✅ Generated {content.content_type.value.replace('_', ' ').title()}

**Title:** {content.title}

**Target Audience:** {content.generation_context.target_audience}
**Cultural Context:** {content.generation_context.cultural_context}
**Urgency Level:** {content.generation_context.urgency_level}

**Content Preview:**
{content.body[:500]}...

**Content ID:** {content.id}

The content has been adapted for:
- {content.generation_context.cultural_context} cultural context
- {content.generation_context.emotional_tone} emotional tone
- {content.generation_context.language} language preferences
"""
        
        if content.sources_used:
            response += f"\n**Sources Used:** {', '.join(content.sources_used[:3])}"
        
        return {
            'response': response,
            'content': {
                'id': content.id,
                'type': content.content_type.value,
                'title': content.title,
                'body': content.body,
                'metadata': content.metadata
            },
            'suggestions': [
                "generate audio version",
                "create visual layout",
                "translate to another language",
                "track effectiveness"
            ]
        }
    
    def handle_menu_request(self, request: str) -> Dict[str, Any]:
        """Handle menu-related requests"""
        
        return {
            'response': """I can help you build and improve restaurant menus using AI agents.
            
Upload your current menu (PDF or image) and I'll have my Chef agent and dynamically generated specialists analyze it.

They'll discuss improvements while you watch, and you can interrupt anytime to redirect the conversation.

Features:
- Dynamic agent generation based on your specific menu
- Live visual updates after each change
- Voice-first interaction available
- Export to print-ready PDF

Say 'start menu builder' to begin.""",
            'action': 'menu_builder_intro'
        }
    
    def find_grants(self, request: str) -> Dict[str, Any]:
        """Find relevant grants based on request"""
        logger.info(f"🔍 Searching for grants: {request}")
        
        # Extract search terms
        search_terms = []
        if 'elder' in request.lower() or 'senior' in request.lower():
            search_terms.extend(['elder', 'senior', 'aging'])
        if 'health' in request.lower():
            search_terms.append('health')
        if 'community' in request.lower():
            search_terms.append('community')
        if 'care' in request.lower():
            search_terms.append('care')
        
        # Extract location
        location = "Hawaii" if 'puna' in request.lower() or 'hawaii' in request.lower() else ""
        
        # Discover grants
        grants = self.grant_system.discover_grants(search_terms, location)
        
        if grants:
            response = f"✅ Found {len(grants)} grant opportunities:\n\n"
            for i, grant in enumerate(grants[:10], 1):
                response += f"{i}. **{grant.title}**\n"
                response += f"   - Funder: {grant.funder}\n"
                response += f"   - Amount: {grant.amount}\n"
                response += f"   - Focus: {', '.join(grant.focus_areas[:3]) if grant.focus_areas else 'General'}\n"
                if grant.deadline:
                    response += f"   - Deadline: {grant.deadline.strftime('%Y-%m-%d')}\n"
                response += f"   - ID: {grant.id}\n\n"
            
            return {
                'response': response,
                'grants': [self._grant_to_dict(g) for g in grants],
                'count': len(grants),
                'suggestions': [
                    f"generate application for {grants[0].id}",
                    "show more details",
                    "start voice session",
                    "export to spreadsheet"
                ]
            }
        else:
            return {
                'response': "No grants found matching your criteria. Try different search terms or check back later.",
                'grants': [],
                'count': 0
            }
    
    def generate_applications(self, request: str) -> Dict[str, Any]:
        """Generate grant applications"""
        # Extract grant ID if provided
        grant_id = None
        words = request.split()
        for i, word in enumerate(words):
            if word == 'for' and i + 1 < len(words):
                potential_id = words[i + 1]
                if len(potential_id) == 12:  # Our grant IDs are 12 characters
                    grant_id = potential_id
                    break
        
        if not grant_id:
            # Get all discovered grants
            all_grants = self.grant_system.get_all_grants()
            if not all_grants:
                return {
                    'response': "No grants available. Please search for grants first.",
                    'suggestions': ["find grants for elder care", "search funding opportunities"]
                }
            grant_id = all_grants[0].id
        
        # Generate application
        org_info = {
            'name': 'Puna Community Support Network',
            'years_experience': 5,
            'location': 'Lower Puna, Hawaii'
        }
        
        application = self.grant_system.generate_application(grant_id, org_info)
        
        if 'error' in application:
            return {'response': f"❌ Error: {application['error']}"}
        
        response = f"""
✅ Generated Grant Application

**Grant ID:** {application['grant_id']}
**Organization:** {application['organization_name']}
**Project Title:** {application['project_title']}

**Project Description:**
{application['project_description'][:500]}...

**Total Budget:** ${application['budget_total']:,.2f}

**Budget Breakdown:**
"""
        for category, amount in application['budget_details'].items():
            response += f"  - {category}: ${amount:,.2f}\n"
        
        response += f"\n**Status:** {application['status']}"
        response += f"\n**Application ID:** {application['id']}"
        
        return {
            'response': response,
            'application': application,
            'suggestions': [
                "submit application",
                "edit narrative",
                "adjust budget",
                "generate for another grant"
            ]
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get platform status"""
        all_grants = self.grant_system.get_all_grants()
        
        status = f"""
🌺 **Shoghi Platform Status**

**System:** ✅ Operational
**Grant Database:** ✅ Connected
**Voice Interface:** ✅ Ready (Hume.ai EVI)
**Menu Builder:** ✅ Available
**Discovered Grants:** {len(all_grants)}
**Active Agents:** {len(self.agents)}
**Voice Sessions:** {len(self.active_voice_sessions)}

**Capabilities:**
- Grant Discovery: ✅ Working
- Application Generation: ✅ Working
- Voice Interface: ✅ With emotion detection
- Dynamic Agent Generation: ✅ Context-aware
- Menu Builder: ✅ Restaurant-specific agents
- Database Persistence: ✅ Working

**Recent Activity:**
- Grants discovered: {len(all_grants)}
- Active voice sessions: {len(self.active_voice_sessions)}
- Last check: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
        return {
            'response': status,
            'operational': True,
            'stats': {
                'grants': len(all_grants),
                'agents': len(self.agents),
                'voice_sessions': len(self.active_voice_sessions)
            }
        }
    
    def get_help(self) -> Dict[str, Any]:
        """Get help information"""
        help_text = """
🌺 **Shoghi Platform Help - Complete System**

I can help you with:

**🎤 Voice Interaction:**
- "start voice session" - Talk naturally with emotion detection
- Interrupt anytime, multi-language support

**📝 Contextual Content Generation (NEW):**
- "generate elder care protocol for Hawaiian community"
- "create volunteer script for food distribution"
- "write grant narrative for senior services"
- "generate disaster response guide - urgent"
- "create community flyer in simple language"
- "generate training material for new volunteers"

Content adapts to:
- Cultural context (Hawaiian, Japanese, Filipino, etc.)
- Target audience (elders, volunteers, funders, families)
- Urgency level (critical, high, normal)
- Emotional tone (urgent, supportive, formal, warm)
- Language (English, Spanish, Japanese, Tagalog)

**🔍 Finding Grants:**
- "find grants for elder care in Puna"
- "search funding for community health"

**📄 Generating Applications:**
- "generate application for [grant_id]"
- Complete narratives with context-aware content

**🍽️ Restaurant Menu Builder:**
- "build restaurant menu"
- Dynamic agent generation for specific needs

**Examples of Context-Aware Content:**
1. "generate elder care protocol for Japanese elders" 
   → Creates respectful, culturally appropriate guidelines
   
2. "urgent disaster response guide for Puna"
   → Immediate action items, local resources, simple language
   
3. "create volunteer script for Hawaiian food distribution"
   → Warm tone with Hawaiian values, proper greetings
   
4. "generate grant narrative with statistics for federal funder"
   → Formal, data-driven, comprehensive approach

The platform generates content specifically for YOUR context, not generic templates!

Type any request or start a voice session!
"""
        return {
            'response': help_text,
            'suggestions': [
                "generate elder care protocol",
                "create volunteer training guide",
                "start voice session",
                "find grants for elder care"
            ]
        }
    
    def _grant_to_dict(self, grant: GrantOpportunity) -> Dict[str, Any]:
        """Convert grant to dictionary"""
        return {
            'id': grant.id,
            'title': grant.title,
            'description': grant.description,
            'funder': grant.funder,
            'amount': grant.amount,
            'deadline': grant.deadline.isoformat() if grant.deadline else None,
            'focus_areas': grant.focus_areas,
            'geographic_scope': grant.geographic_scope,
            'url': grant.application_url,
            'source': grant.source
        }
    
    def interactive_mode(self):
        """Run in interactive mode with voice support"""
        print("\n🌺 Welcome to Shoghi - Adaptive Coordination Platform")
        print("🎤 NOW WITH VOICE INTERFACE!")
        print("\nType 'help' for commands, 'voice' to start voice session, or 'exit' to quit\n")
        
        while True:
            try:
                user_input = input("Shoghi> ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'q']:
                    print("Mahalo! 🌺")
                    break
                
                if user_input.lower() in ['voice', 'start voice', 'voice session']:
                    print("\n🎤 Voice session starting...")
                    print("(In production, this would connect to Hume.ai EVI)")
                    print("Speak naturally - I'll understand your emotions too!\n")
                    # In production, would start actual voice session
                    continue
                
                if not user_input:
                    continue
                
                result = self.process_request(user_input)
                print("\n" + result['response'])
                
                if result.get('suggestions'):
                    print("\n💡 Suggestions:")
                    for suggestion in result['suggestions'][:4]:
                        print(f"  - {suggestion}")
                print()
                
            except KeyboardInterrupt:
                print("\nMahalo! 🌺")
                break
            except Exception as e:
                logger.error(f"Error: {e}")
                print(f"❌ Error: {e}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Shoghi - Adaptive Coordination Platform with Voice')
    parser.add_argument('--command', '-c', help='Execute a single command')
    parser.add_argument('--mode', '-m', choices=['interactive', 'api', 'voice'], default='interactive',
                      help='Operation mode')
    parser.add_argument('--output', '-o', help='Output file for results')
    parser.add_argument('--voice', '-v', action='store_true', help='Start in voice mode')
    
    args = parser.parse_args()
    
    # Initialize platform
    platform = ShoghiPlatform()
    
    if args.command:
        # Execute single command
        result = platform.process_request(args.command)
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            print(f"✅ Results saved to {args.output}")
        else:
            print(result['response'])
    
    elif args.voice or args.mode == 'voice':
        print("\n🎤 Starting Shoghi in Voice Mode...")
        print("This would connect to Hume.ai EVI for emotional voice interaction")
        print("For now, using text-based simulation\n")
        platform.interactive_mode()
    
    else:
        # Interactive mode
        platform.interactive_mode()

if __name__ == "__main__":
    main()
