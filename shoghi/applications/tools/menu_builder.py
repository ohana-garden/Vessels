#!/usr/bin/env python3
"""
RESTAURANT MENU BUILDER - Shoghi Architecture
Dynamic agent generation for context-specific menu improvements
Voice-first conversational interface
"""

import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import uuid
from enum import Enum
import re

logger = logging.getLogger(__name__)

class MenuSection(Enum):
    """Menu section types"""
    APPETIZERS = "appetizers"
    MAINS = "mains"
    DESSERTS = "desserts"
    BEVERAGES = "beverages"
    SPECIALS = "specials"
    KIDS = "kids"

@dataclass
class MenuItem:
    """Single menu item"""
    name: str
    price: float
    description: str = ""
    section: MenuSection = MenuSection.MAINS
    dietary_tags: List[str] = field(default_factory=list)
    popularity: float = 0.5  # 0-1 score

@dataclass
class MenuState:
    """Current state of the menu"""
    restaurant_name: str
    cuisine_type: str
    items: List[MenuItem]
    design_style: str = "classic"
    target_audience: str = "general"
    price_range: str = "moderate"
    problems_identified: List[str] = field(default_factory=list)
    improvements_made: List[str] = field(default_factory=list)
    version: int = 1

class MenuAgentGenerator:
    """Generates context-specific agents based on menu analysis"""
    
    def __init__(self):
        self.generated_agents = {}
        self.chef_agent_id = str(uuid.uuid4())
        
    def analyze_menu_context(self, menu_state: MenuState) -> Dict[str, Any]:
        """Analyze menu to determine what kind of specialist is needed"""
        
        context = {
            'restaurant_type': self._infer_restaurant_type(menu_state),
            'main_issues': [],
            'opportunities': [],
            'customer_perspective_needed': None
        }
        
        # Analyze problems
        if self._has_cluttered_layout(menu_state):
            context['main_issues'].append('cluttered_layout')
            
        if self._has_pricing_issues(menu_state):
            context['main_issues'].append('pricing_confusion')
            
        if self._lacks_descriptions(menu_state):
            context['main_issues'].append('missing_descriptions')
            
        if self._has_poor_categorization(menu_state):
            context['main_issues'].append('poor_organization')
        
        # Identify opportunities
        if menu_state.cuisine_type in ['italian', 'french', 'japanese']:
            context['opportunities'].append('authenticity_emphasis')
            
        if 'family' in menu_state.target_audience.lower():
            context['opportunities'].append('family_friendly_formatting')
            
        if menu_state.price_range == 'upscale':
            context['opportunities'].append('premium_presentation')
        
        # Determine customer perspective
        if menu_state.cuisine_type in ['thai', 'ethiopian', 'korean']:
            context['customer_perspective_needed'] = 'unfamiliar_cuisine_explorer'
        elif 'tourist' in menu_state.target_audience.lower():
            context['customer_perspective_needed'] = 'tourist_seeking_local'
        elif 'business' in menu_state.target_audience.lower():
            context['customer_perspective_needed'] = 'business_lunch_scanner'
            
        return context
    
    def generate_specialist_agent(self, need: str, menu_state: MenuState) -> Dict[str, Any]:
        """Generate a context-specific specialist agent"""
        
        agent_id = str(uuid.uuid4())
        context = self.analyze_menu_context(menu_state)
        
        # Build agent prompt based on specific need and context
        agent_spec = {
            'id': agent_id,
            'type': need,
            'created_at': datetime.now().isoformat(),
            'context': context,
            'personality': '',
            'expertise': '',
            'communication_style': '',
            'focus_areas': [],
            'success_metrics': []
        }
        
        if need == 'design_specialist':
            agent_spec.update(self._generate_design_specialist(menu_state, context))
        elif need == 'pricing_strategist':
            agent_spec.update(self._generate_pricing_strategist(menu_state, context))
        elif need == 'customer_perspective':
            agent_spec.update(self._generate_customer_agent(menu_state, context))
        elif need == 'cultural_authenticity':
            agent_spec.update(self._generate_cultural_agent(menu_state, context))
        elif need == 'accessibility_expert':
            agent_spec.update(self._generate_accessibility_agent(menu_state, context))
        else:
            # Generate generic improvement specialist
            agent_spec.update(self._generate_generic_specialist(need, menu_state, context))
        
        self.generated_agents[agent_id] = agent_spec
        return agent_spec
    
    def _generate_design_specialist(self, menu_state: MenuState, context: Dict) -> Dict:
        """Generate design specialist for specific restaurant type"""
        
        if menu_state.price_range == 'upscale' and 'cluttered_layout' in context['main_issues']:
            return {
                'personality': 'Minimalist designer with fine dining experience',
                'expertise': f'Upscale {menu_state.cuisine_type} restaurant menus, white space usage, typography hierarchy',
                'communication_style': 'Visual-first, uses design terminology sparingly, shows rather than tells',
                'focus_areas': [
                    'Reduce visual noise while maintaining elegance',
                    'Create clear hierarchy for courses',
                    'Emphasize premium items subtly',
                    'Improve readability in low light'
                ],
                'success_metrics': ['scanning_time', 'item_findability', 'perceived_value']
            }
            
        elif 'family' in menu_state.target_audience.lower():
            return {
                'personality': 'Family restaurant design expert, parent of three',
                'expertise': 'Kid-friendly layouts, allergen highlighting, quick-scan sections',
                'communication_style': 'Practical, emphasizes usability over aesthetics',
                'focus_areas': [
                    'Clear kids menu separation',
                    'Visual allergen indicators',
                    'Price visibility for family budgets',
                    'Shareable portions highlighting'
                ],
                'success_metrics': ['parent_convenience', 'kid_engagement', 'order_speed']
            }
        
        else:
            return {
                'personality': 'Versatile restaurant designer',
                'expertise': 'General menu design, readability, visual hierarchy',
                'communication_style': 'Balanced, practical',
                'focus_areas': ['Clarity', 'Scannability', 'Visual appeal'],
                'success_metrics': ['customer_satisfaction', 'order_accuracy']
            }
    
    def _generate_customer_agent(self, menu_state: MenuState, context: Dict) -> Dict:
        """Generate customer perspective agent based on identified need"""
        
        customer_type = context.get('customer_perspective_needed', 'general_diner')
        
        personas = {
            'unfamiliar_cuisine_explorer': {
                'personality': 'Curious but cautious diner trying new cuisine for first time',
                'expertise': 'None with this cuisine, relies on descriptions and comparisons',
                'communication_style': 'Questions everything, needs familiar reference points',
                'focus_areas': [
                    'What do these dishes actually taste like?',
                    'What ingredients am I eating?',
                    'What should I order if I like [familiar dish]?',
                    'Are portions shareable or individual?'
                ],
                'success_metrics': ['first_timer_confidence', 'order_satisfaction']
            },
            'tourist_seeking_local': {
                'personality': 'Tourist wanting authentic local experience',
                'expertise': 'Well-traveled, seeks authentic over tourist-trap',
                'communication_style': 'Asks about local favorites, suspicious of "tourist menu"',
                'focus_areas': [
                    'What do locals actually order?',
                    'Which dishes are authentic vs adapted?',
                    'What\'s unique to this location?',
                    'What pairs well together?'
                ],
                'success_metrics': ['authenticity_perception', 'memorable_experience']
            },
            'business_lunch_scanner': {
                'personality': 'Time-pressed professional needing quick quality lunch',
                'expertise': 'Efficiency, knows what works for business meetings',
                'communication_style': 'Direct, time-conscious, outcome-focused',
                'focus_areas': [
                    'What can be eaten neatly during meeting?',
                    'What\'s quick but impressive for clients?',
                    'Clear pricing for expense reports?',
                    'Vegetarian/dietary options for diverse groups?'
                ],
                'success_metrics': ['speed_to_order', 'professional_appropriateness']
            }
        }
        
        return personas.get(customer_type, {
            'personality': 'Regular local diner',
            'expertise': 'General dining, value-seeking',
            'communication_style': 'Straightforward feedback',
            'focus_areas': ['Value', 'Taste', 'Portions', 'Service'],
            'success_metrics': ['repeat_visits', 'recommendations']
        })
    
    def _infer_restaurant_type(self, menu_state: MenuState) -> str:
        """Infer restaurant type from menu content"""
        
        # Simple inference based on cuisine and price
        if menu_state.price_range == 'upscale':
            return f"fine_dining_{menu_state.cuisine_type}"
        elif 'family' in menu_state.target_audience.lower():
            return f"family_{menu_state.cuisine_type}"
        elif menu_state.cuisine_type in ['burger', 'pizza', 'sandwich']:
            return "casual_american"
        else:
            return f"casual_{menu_state.cuisine_type}"
    
    def _has_cluttered_layout(self, menu_state: MenuState) -> bool:
        """Check if menu has layout issues"""
        return len(menu_state.items) > 30 or any(
            len(item.description) > 100 for item in menu_state.items
        )
    
    def _has_pricing_issues(self, menu_state: MenuState) -> bool:
        """Check for pricing clarity issues"""
        prices = [item.price for item in menu_state.items]
        if not prices:
            return True
        
        # Check for inconsistent pricing patterns
        price_variance = max(prices) / min(prices) if min(prices) > 0 else 100
        return price_variance > 10
    
    def _lacks_descriptions(self, menu_state: MenuState) -> bool:
        """Check if menu lacks descriptions"""
        items_without_desc = sum(1 for item in menu_state.items if not item.description)
        return items_without_desc > len(menu_state.items) * 0.3
    
    def _has_poor_categorization(self, menu_state: MenuState) -> bool:
        """Check if menu has organization issues"""
        sections = set(item.section for item in menu_state.items)
        return len(sections) < 2 or len(sections) > 8
    
    def _generate_pricing_strategist(self, menu_state: MenuState, context: Dict) -> Dict:
        """Generate pricing strategy specialist"""
        return {
            'personality': f'Revenue optimization expert for {menu_state.cuisine_type} restaurants',
            'expertise': 'Menu engineering, price anchoring, profit margin optimization',
            'communication_style': 'Data-driven but explains in simple terms',
            'focus_areas': [
                'Price point psychology',
                'Anchor items placement',
                'Bundle opportunities',
                'Margin optimization'
            ],
            'success_metrics': ['average_ticket', 'profit_margin', 'perceived_value']
        }
    
    def _generate_cultural_agent(self, menu_state: MenuState, context: Dict) -> Dict:
        """Generate cultural authenticity specialist"""
        return {
            'personality': f'Native {menu_state.cuisine_type} cuisine expert and cultural ambassador',
            'expertise': f'Traditional {menu_state.cuisine_type} cooking, ingredient authenticity, cultural context',
            'communication_style': 'Educational, passionate about authenticity, storytelling approach',
            'focus_areas': [
                'Authentic dish names and descriptions',
                'Cultural context for dishes',
                'Traditional pairings and combinations',
                'Seasonal and regional variations'
            ],
            'success_metrics': ['authenticity_score', 'cultural_education', 'customer_interest']
        }
    
    def _generate_accessibility_agent(self, menu_state: MenuState, context: Dict) -> Dict:
        """Generate accessibility specialist"""
        return {
            'personality': 'Universal design advocate with hospitality experience',
            'expertise': 'ADA compliance, cognitive load reduction, multi-sensory accessibility',
            'communication_style': 'Inclusive, practical, empathetic',
            'focus_areas': [
                'Font size and contrast for low vision',
                'Simplified language options',
                'Allergen and dietary clear marking',
                'Cognitive load reduction'
            ],
            'success_metrics': ['accessibility_score', 'inclusive_ordering', 'error_reduction']
        }
    
    def _generate_generic_specialist(self, need: str, menu_state: MenuState, context: Dict) -> Dict:
        """Fallback for generating any other type of specialist"""
        return {
            'personality': f'Specialist in {need} for {menu_state.cuisine_type} restaurants',
            'expertise': f'{need}, restaurant operations, customer experience',
            'communication_style': 'Professional, constructive, solution-focused',
            'focus_areas': [need],
            'success_metrics': ['improvement_score', 'customer_satisfaction']
        }

class MenuConversationOrchestrator:
    """Orchestrates conversation between Chef and dynamically generated specialists"""
    
    def __init__(self):
        self.agent_generator = MenuAgentGenerator()
        self.conversation_history = []
        self.current_menu_state = None
        self.active_agents = {}
        self.user_interruptions = []
        
    async def initialize_conversation(self, initial_menu: Dict[str, Any]) -> MenuState:
        """Initialize conversation with menu analysis"""
        
        # Parse menu into structured format
        self.current_menu_state = self._parse_menu(initial_menu)
        
        # Create Chef agent (persistent)
        self.active_agents['chef'] = {
            'id': self.agent_generator.chef_agent_id,
            'type': 'chef',
            'personality': 'Executive chef with 20 years experience',
            'expertise': 'Menu composition, pricing, kitchen operations, customer preferences',
            'communication_style': 'Practical, experienced, slightly protective of menu'
        }
        
        # Analyze initial context
        context = self.agent_generator.analyze_menu_context(self.current_menu_state)
        
        # Start conversation
        await self._chef_opening_analysis(context)
        
        return self.current_menu_state
    
    async def _chef_opening_analysis(self, context: Dict[str, Any]):
        """Chef's initial analysis of the menu"""
        
        analysis = {
            'speaker': 'chef',
            'timestamp': datetime.now().isoformat(),
            'message': f"Looking at this {self.current_menu_state.cuisine_type} menu... "
        }
        
        if context['main_issues']:
            issues = ', '.join(context['main_issues'])
            analysis['message'] += f"I see some issues with {issues}. "
            
        if context['opportunities']:
            ops = ', '.join(context['opportunities']) 
            analysis['message'] += f"There's opportunity to enhance {ops}. "
        
        analysis['message'] += "Let me bring in a specialist to help."
        
        self.conversation_history.append(analysis)
        
        # Determine what specialist to summon
        if 'cluttered_layout' in context['main_issues']:
            await self.summon_specialist('design_specialist')
        elif 'pricing_confusion' in context['main_issues']:
            await self.summon_specialist('pricing_strategist')
        elif context.get('customer_perspective_needed'):
            await self.summon_specialist('customer_perspective')
    
    async def summon_specialist(self, specialist_type: str) -> str:
        """Chef summons a context-specific specialist"""
        
        # Generate specialist based on current menu state
        specialist = self.agent_generator.generate_specialist_agent(
            specialist_type, 
            self.current_menu_state
        )
        
        self.active_agents[specialist['id']] = specialist
        
        # Announce specialist arrival
        announcement = {
            'speaker': 'chef',
            'timestamp': datetime.now().isoformat(),
            'message': f"I'm bringing in a {specialist['personality']} to help with this.",
            'action': 'summon_specialist',
            'specialist_id': specialist['id']
        }
        self.conversation_history.append(announcement)
        
        # Specialist introduction
        intro = {
            'speaker': specialist['id'],
            'timestamp': datetime.now().isoformat(),
            'message': f"Hi, I'm here to help. {self._specialist_opening(specialist)}",
            'agent_type': specialist_type
        }
        self.conversation_history.append(intro)
        
        return specialist['id']
    
    def _specialist_opening(self, specialist: Dict[str, Any]) -> str:
        """Generate specialist's opening statement based on their focus"""
        
        focus = specialist['focus_areas'][0] if specialist['focus_areas'] else "improvements"
        
        if specialist['type'] == 'design_specialist':
            return f"Looking at the layout, I can see {focus}. Let's clean this up."
        elif specialist['type'] == 'customer_perspective':
            return f"As someone who would be ordering here, {focus}"
        elif specialist['type'] == 'pricing_strategist':
            return f"From a revenue perspective, {focus}"
        else:
            return f"I notice {focus}. Let's address that."
    
    async def process_user_interruption(self, user_input: str) -> Dict[str, Any]:
        """Handle user interruption during agent conversation"""
        
        interruption = {
            'timestamp': datetime.now().isoformat(),
            'input': user_input,
            'current_speaker': self.conversation_history[-1]['speaker'] if self.conversation_history else None
        }
        self.user_interruptions.append(interruption)
        
        # Parse user intent
        intent = self._parse_user_intent(user_input)
        
        response = {
            'acknowledged': True,
            'action': intent['action'],
            'response': ''
        }
        
        if intent['action'] == 'redirect':
            # User wants to change focus
            response['response'] = f"Got it. Let's focus on {intent['focus']}."
            await self.summon_specialist(intent['specialist_needed'])
            
        elif intent['action'] == 'stop':
            response['response'] = "Stopping here. What would you like to do with the current version?"
            response['menu_state'] = self.current_menu_state
            
        elif intent['action'] == 'approve':
            response['response'] = "Great! Making that change now."
            await self.apply_change(intent['change_to_apply'])
            
        elif intent['action'] == 'question':
            response['response'] = await self.answer_user_question(intent['question'])
        
        return response
    
    def _parse_user_intent(self, user_input: str) -> Dict[str, Any]:
        """Parse what the user wants from their interruption"""
        
        input_lower = user_input.lower()
        
        if any(word in input_lower for word in ['stop', 'enough', 'done']):
            return {'action': 'stop'}
            
        elif any(word in input_lower for word in ['yes', 'good', 'approve', 'like that']):
            return {'action': 'approve', 'change_to_apply': 'last_suggested'}
            
        elif any(word in input_lower for word in ['no', 'not', "don't", 'different']):
            return {'action': 'redirect', 'focus': 'alternative_approach', 'specialist_needed': 'design_specialist'}
            
        elif '?' in user_input:
            return {'action': 'question', 'question': user_input}
            
        else:
            # Try to infer what they want to focus on
            if 'price' in input_lower:
                return {'action': 'redirect', 'focus': 'pricing', 'specialist_needed': 'pricing_strategist'}
            elif 'design' in input_lower or 'look' in input_lower:
                return {'action': 'redirect', 'focus': 'design', 'specialist_needed': 'design_specialist'}
            elif 'customer' in input_lower:
                return {'action': 'redirect', 'focus': 'customer experience', 'specialist_needed': 'customer_perspective'}
            else:
                return {'action': 'clarify', 'original_input': user_input}
    
    async def apply_change(self, change_type: str) -> MenuState:
        """Apply agreed change to menu"""
        
        # Update menu state based on change
        self.current_menu_state.version += 1
        self.current_menu_state.improvements_made.append(change_type)
        
        # Log the change
        change_log = {
            'speaker': 'system',
            'timestamp': datetime.now().isoformat(),
            'message': f"Applied change: {change_type}",
            'action': 'menu_updated',
            'version': self.current_menu_state.version
        }
        self.conversation_history.append(change_log)
        
        return self.current_menu_state
    
    async def answer_user_question(self, question: str) -> str:
        """Have appropriate agent answer user question"""
        
        # Determine which agent should answer
        if 'price' in question.lower():
            responder = 'pricing_strategist'
        elif 'look' in question.lower() or 'design' in question.lower():
            responder = 'design_specialist'
        else:
            responder = 'chef'
        
        # Generate contextual answer
        answer = f"Based on the current menu, {question} "
        
        # Add specific answer based on question type
        if 'why' in question.lower():
            answer += "This approach works because it addresses the main issue we identified."
        elif 'how' in question.lower():
            answer += "We would implement this by adjusting the layout and descriptions."
        elif 'what' in question.lower():
            answer += "The impact would be improved readability and faster ordering."
        else:
            answer += "That's a good point to consider."
        
        return answer
    
    def _parse_menu(self, raw_menu: Dict[str, Any]) -> MenuState:
        """Parse raw menu into structured MenuState"""
        
        # Extract restaurant info
        restaurant_name = raw_menu.get('restaurant_name', 'Restaurant')
        cuisine_type = raw_menu.get('cuisine_type', 'american')
        
        # Parse items
        items = []
        for item_data in raw_menu.get('items', []):
            item = MenuItem(
                name=item_data.get('name', 'Unknown Item'),
                price=item_data.get('price', 0.0),
                description=item_data.get('description', ''),
                section=MenuSection(item_data.get('section', 'mains'))
            )
            items.append(item)
        
        return MenuState(
            restaurant_name=restaurant_name,
            cuisine_type=cuisine_type,
            items=items,
            design_style=raw_menu.get('design_style', 'classic'),
            target_audience=raw_menu.get('target_audience', 'general'),
            price_range=raw_menu.get('price_range', 'moderate')
        )
    
    def get_conversation_display(self) -> List[Dict[str, Any]]:
        """Get conversation for display with speaker names"""
        
        display_messages = []
        
        for message in self.conversation_history:
            speaker_id = message['speaker']
            
            if speaker_id == 'chef':
                speaker_name = "Chef"
                speaker_role = "Executive Chef"
            elif speaker_id == 'system':
                speaker_name = "System"
                speaker_role = "Update"
            else:
                agent = self.active_agents.get(speaker_id, {})
                speaker_name = agent.get('type', 'Specialist').replace('_', ' ').title()
                speaker_role = agent.get('personality', 'Specialist')[:50]
            
            display_messages.append({
                'speaker_name': speaker_name,
                'speaker_role': speaker_role,
                'message': message['message'],
                'timestamp': message['timestamp']
            })
        
        return display_messages

# Singleton instance
menu_orchestrator = MenuConversationOrchestrator()
