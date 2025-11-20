#!/usr/bin/env python3
"""
VOICE INTERFACE MODULE - Hume.ai EVI Integration
Voice-first interface for Vessels platform
Handles emotional voice interactions, agent generation, and coordination
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import os
import websockets
import re
from enum import Enum

logger = logging.getLogger(__name__)

class EmotionalState(Enum):
    """Detected emotional states from voice"""
    CONFIDENT = "confident"
    UNCERTAIN = "uncertain"
    FRUSTRATED = "frustrated"
    EXCITED = "excited"
    CONFUSED = "confused"
    SATISFIED = "satisfied"
    STRESSED = "stressed"
    NEUTRAL = "neutral"

@dataclass
class VoiceSession:
    """Voice interaction session"""
    session_id: str
    user_id: str
    language: str
    start_time: datetime
    emotional_history: List[Dict[str, float]] = field(default_factory=list)
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    current_context: Dict[str, Any] = field(default_factory=dict)
    active_agents: List[str] = field(default_factory=list)
    
class HumeVoiceInterface:
    """Hume.ai Empathic Voice Interface for Vessels"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('HUME_API_KEY')
        self.active_sessions: Dict[str, VoiceSession] = {}
        self.websocket_connections: Dict[str, Any] = {}
        self.emotion_thresholds = {
            'uncertainty': 0.7,
            'frustration': 0.6,
            'excitement': 0.7,
            'confusion': 0.6,
            'satisfaction': 0.8,
            'stress': 0.6
        }
        logger.info("Hume Voice Interface initialized")
    
    async def create_session(self, user_id: str, context: str = "grant_discovery", 
                            language: str = "en") -> VoiceSession:
        """Create new voice session with emotional context"""
        session_id = str(uuid.uuid4())
        
        session = VoiceSession(
            session_id=session_id,
            user_id=user_id,
            language=language,
            start_time=datetime.now(),
            current_context={'task': context, 'mode': 'voice_first'}
        )
        
        self.active_sessions[session_id] = session
        
        # Initialize Hume WebSocket connection
        await self._connect_hume_websocket(session_id)
        
        logger.info(f"Voice session created: {session_id} for user {user_id}")
        return session
    
    async def _connect_hume_websocket(self, session_id: str):
        """Connect to Hume EVI WebSocket"""
        try:
            ws_url = f"wss://api.hume.ai/v0/assistant/chat"
            headers = {
                "X-Hume-Api-Key": self.api_key,
                "Content-Type": "application/json"
            }
            
            # Store WebSocket connection
            self.websocket_connections[session_id] = {
                'url': ws_url,
                'headers': headers,
                'connected': False
            }
            
            logger.info(f"WebSocket prepared for session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to prepare WebSocket: {e}")
    
    async def process_voice_input(self, session_id: str, audio_data: bytes) -> Dict[str, Any]:
        """Process voice input with emotion detection"""
        
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        
        # Simulate Hume API processing (in production, actual API call)
        transcription, emotions = await self._transcribe_with_emotions(audio_data)
        
        # Update session with emotional data
        session.emotional_history.append({
            'timestamp': datetime.now().isoformat(),
            'emotions': emotions
        })
        
        # Determine emotional state
        emotional_state = self._determine_emotional_state(emotions)
        
        # Process based on emotional context
        response = await self._generate_emotionally_aware_response(
            session, transcription, emotional_state, emotions
        )
        
        # Update conversation history
        session.conversation_history.append({
            'user': transcription,
            'emotions': emotions,
            'state': emotional_state.value,
            'agent_response': response['text'],
            'timestamp': datetime.now().isoformat()
        })
        
        return {
            'transcription': transcription,
            'emotions': emotions,
            'emotional_state': emotional_state.value,
            'response': response,
            'session_id': session_id
        }
    
    async def _transcribe_with_emotions(self, audio_data: bytes) -> Tuple[str, Dict[str, float]]:
        """Transcribe audio and detect emotions"""
        
        # In production, this would call Hume API
        # Simulating response for development
        
        # Placeholder transcription
        transcription = "I need help finding grants for elder care in Puna"
        
        # Simulated emotion detection
        emotions = {
            'uncertainty': 0.45,
            'hope': 0.62,
            'determination': 0.71,
            'frustration': 0.15,
            'confusion': 0.22,
            'excitement': 0.38,
            'stress': 0.31
        }
        
        return transcription, emotions
    
    def _determine_emotional_state(self, emotions: Dict[str, float]) -> EmotionalState:
        """Determine primary emotional state from emotion scores"""
        
        # Check thresholds in priority order
        if emotions.get('frustration', 0) > self.emotion_thresholds['frustration']:
            return EmotionalState.FRUSTRATED
        elif emotions.get('uncertainty', 0) > self.emotion_thresholds['uncertainty']:
            return EmotionalState.UNCERTAIN
        elif emotions.get('confusion', 0) > self.emotion_thresholds['confusion']:
            return EmotionalState.CONFUSED
        elif emotions.get('stress', 0) > self.emotion_thresholds['stress']:
            return EmotionalState.STRESSED
        elif emotions.get('excitement', 0) > self.emotion_thresholds['excitement']:
            return EmotionalState.EXCITED
        elif emotions.get('satisfaction', 0) > self.emotion_thresholds['satisfaction']:
            return EmotionalState.SATISFIED
        elif emotions.get('determination', 0) > 0.6:
            return EmotionalState.CONFIDENT
        else:
            return EmotionalState.NEUTRAL
    
    async def _generate_emotionally_aware_response(self, session: VoiceSession, 
                                                  transcription: str,
                                                  emotional_state: EmotionalState,
                                                  emotions: Dict[str, float]) -> Dict[str, Any]:
        """Generate response adapted to emotional state"""
        
        response = {
            'text': '',
            'voice_modulation': 'neutral',
            'pacing': 'normal',
            'agent_action': None
        }
        
        # Adapt response based on emotional state
        if emotional_state == EmotionalState.FRUSTRATED:
            response['text'] = "I hear your frustration. Let me simplify this. "
            response['voice_modulation'] = 'calm_reassuring'
            response['pacing'] = 'slower'
            
        elif emotional_state == EmotionalState.UNCERTAIN:
            response['text'] = "No worries at all. Let's figure this out together step by step. "
            response['voice_modulation'] = 'warm_supportive'
            response['pacing'] = 'gentle'
            
        elif emotional_state == EmotionalState.CONFUSED:
            response['text'] = "Let me explain that more clearly. "
            response['voice_modulation'] = 'clear_patient'
            response['pacing'] = 'slower'
            
        elif emotional_state == EmotionalState.EXCITED:
            response['text'] = "I can feel your excitement! Let's make this happen. "
            response['voice_modulation'] = 'energetic_enthusiastic'
            response['pacing'] = 'dynamic'
            
        elif emotional_state == EmotionalState.STRESSED:
            response['text'] = "Let's take this one step at a time. No rush. "
            response['voice_modulation'] = 'calm_grounding'
            response['pacing'] = 'relaxed'
            
        elif emotional_state == EmotionalState.SATISFIED:
            response['text'] = "Great! I think we're on the right track. "
            response['voice_modulation'] = 'warm_confirming'
            response['pacing'] = 'normal'
            
        else:
            response['voice_modulation'] = 'friendly_professional'
            response['pacing'] = 'normal'
        
        # Add task-specific response
        if 'grant' in transcription.lower():
            response['text'] += "I'll help you find grants for elder care in Puna. Let me search for you."
            response['agent_action'] = 'spawn_grant_finder'
        elif 'help' in transcription.lower():
            response['text'] += "I'm here to help coordinate resources for your community. What do you need?"
        
        return response
    
    async def synthesize_speech(self, text: str, voice_params: Dict[str, str]) -> bytes:
        """Synthesize speech with emotional modulation"""
        
        # In production, call Hume API for synthesis
        # Placeholder for development
        
        logger.info(f"Synthesizing: {text[:50]}... with {voice_params}")
        
        # Return placeholder audio data
        return b"audio_data_placeholder"
    
    async def handle_interruption(self, session_id: str) -> Dict[str, Any]:
        """Handle user interruption during agent speech"""
        
        if session_id not in self.active_sessions:
            return {'error': 'Session not found'}
        
        session = self.active_sessions[session_id]
        
        # Stop current synthesis
        # Clear pending responses
        # Acknowledge interruption
        
        return {
            'status': 'interrupted',
            'response': "I hear you. What would you like me to focus on?",
            'session_id': session_id
        }
    
    async def spawn_voice_agent(self, agent_type: str, context: Dict[str, Any]) -> str:
        """Spawn specialized voice agent based on need"""
        
        agent_configs = {
            'elder_care': {
                'voice': 'warm_maternal',
                'pacing': 'patient',
                'personality': 'caring and thorough',
                'language_style': 'simple and clear'
            },
            'grant_finder': {
                'voice': 'professional_supportive',
                'pacing': 'efficient',
                'personality': 'knowledgeable and helpful',
                'language_style': 'precise but accessible'
            },
            'coordinator': {
                'voice': 'friendly_organizer',
                'pacing': 'dynamic',
                'personality': 'energetic problem-solver',
                'language_style': 'action-oriented'
            },
            'cultural_guide': {
                'voice': 'respectful_educator',
                'pacing': 'thoughtful',
                'personality': 'culturally aware and sensitive',
                'language_style': 'inclusive and respectful'
            }
        }
        
        config = agent_configs.get(agent_type, agent_configs['coordinator'])
        agent_id = str(uuid.uuid4())
        
        logger.info(f"Spawned voice agent {agent_id} of type {agent_type}")
        
        return agent_id
    
    def get_emotional_metrics(self, session_id: str) -> Dict[str, Any]:
        """Get emotional metrics for session"""
        
        if session_id not in self.active_sessions:
            return {}
        
        session = self.active_sessions[session_id]
        
        if not session.emotional_history:
            return {'status': 'no_data'}
        
        # Calculate averages and trends
        all_emotions = {}
        for entry in session.emotional_history:
            for emotion, value in entry['emotions'].items():
                if emotion not in all_emotions:
                    all_emotions[emotion] = []
                all_emotions[emotion].append(value)
        
        metrics = {
            'session_id': session_id,
            'duration_minutes': (datetime.now() - session.start_time).total_seconds() / 60,
            'emotional_journey': session.emotional_history,
            'averages': {},
            'peaks': {},
            'trend': {}
        }
        
        for emotion, values in all_emotions.items():
            metrics['averages'][emotion] = sum(values) / len(values)
            metrics['peaks'][emotion] = max(values)
            
            # Simple trend: comparing first half to second half
            if len(values) > 1:
                mid = len(values) // 2
                first_half = sum(values[:mid]) / mid
                second_half = sum(values[mid:]) / len(values[mid:])
                
                if second_half > first_half * 1.2:
                    metrics['trend'][emotion] = 'increasing'
                elif second_half < first_half * 0.8:
                    metrics['trend'][emotion] = 'decreasing'
                else:
                    metrics['trend'][emotion] = 'stable'
        
        return metrics
    
    async def close_session(self, session_id: str) -> Dict[str, Any]:
        """Close voice session and cleanup"""
        
        if session_id not in self.active_sessions:
            return {'error': 'Session not found'}
        
        # Get final metrics
        metrics = self.get_emotional_metrics(session_id)
        
        # Close WebSocket if exists
        if session_id in self.websocket_connections:
            # Close connection logic here
            del self.websocket_connections[session_id]
        
        # Remove session
        del self.active_sessions[session_id]
        
        logger.info(f"Closed voice session {session_id}")
        
        return {
            'status': 'closed',
            'session_id': session_id,
            'final_metrics': metrics
        }

# Voice command processor
class VoiceCommandProcessor:
    """Process natural language voice commands"""
    
    def __init__(self):
        self.command_patterns = {
            'find_grants': ['find grant', 'search grant', 'funding', 'money for'],
            'coordinate': ['coordinate', 'organize', 'volunteer', 'help with'],
            'status': ['status', 'what happening', 'update', 'how going'],
            'help': ['help', 'what can you', 'how do', 'explain'],
            'stop': ['stop', 'cancel', 'nevermind', 'quit']
        }
    
    def extract_intent(self, transcription: str) -> Tuple[str, Dict[str, Any]]:
        """Extract intent and entities from transcription"""
        
        text_lower = transcription.lower()
        intent = 'unknown'
        entities = {}
        
        # Check for command patterns
        for command, patterns in self.command_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                intent = command
                break
        
        # Extract entities
        if 'elder' in text_lower or 'kupuna' in text_lower:
            entities['population'] = 'elder'
        
        if 'puna' in text_lower:
            entities['location'] = 'puna'
        elif 'hawaii' in text_lower:
            entities['location'] = 'hawaii'
        
        if 'care' in text_lower:
            entities['service'] = 'care'
        elif 'food' in text_lower:
            entities['service'] = 'food'
        elif 'transport' in text_lower:
            entities['service'] = 'transportation'
        
        return intent, entities
    
    def generate_voice_prompt(self, intent: str, entities: Dict[str, Any], 
                             emotional_context: str) -> str:
        """Generate appropriate voice response based on intent and emotion"""
        
        prompts = {
            'find_grants': {
                'confident': "Let me find those grants for you right now.",
                'uncertain': "I'll help you find grants. Can you tell me more about what you need?",
                'frustrated': "I understand. Let's simplify this and find exactly what you need."
            },
            'coordinate': {
                'confident': "I'll coordinate that for you immediately.",
                'uncertain': "Let me help coordinate. What specific support do you need?",
                'frustrated': "No problem, I'll handle the coordination. Just tell me the basics."
            },
            'help': {
                'confident': "I can help with grant discovery, volunteer coordination, and resource management.",
                'uncertain': "I'm here to help! I can find grants, coordinate volunteers, or connect resources.",
                'frustrated': "Let me explain simply: I find money, organize help, and connect people."
            }
        }
        
        if intent in prompts and emotional_context in prompts[intent]:
            base_prompt = prompts[intent][emotional_context]
        else:
            base_prompt = "I'm here to help. Tell me what you need."
        
        # Add entity-specific context
        if entities.get('population') == 'elder':
            base_prompt += " I see you're focused on elder care."
        if entities.get('location'):
            base_prompt += f" Looking in {entities['location'].title()}."
        
        return base_prompt

# Create singleton instances
hume_interface = HumeVoiceInterface()
voice_processor = VoiceCommandProcessor()


PII_PATTERNS = [
    re.compile(r"\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b"),
    re.compile(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I),
]

def _redact(text: str) -> str:
    for pat in PII_PATTERNS:
        text = pat.sub("[REDACTED]", text)
    return text
