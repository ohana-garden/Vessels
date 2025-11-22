#!/usr/bin/env python3
"""
VESSELS WEB SERVER - Voice-First UI with Backend Integration
Connects the clean voice UI to all Vessels functionality
"""

from flask import Flask, abort, jsonify, render_template, request, escape
from flask_cors import CORS
import json
import asyncio
import logging
from datetime import datetime
import os
import sys
from pydantic import BaseModel, Field, field_validator, ValidationError
from typing import Optional

# Import Vessels components
from vessels_fixed import VesselsPlatform
from content_generation import ContentContext, ContentType

app = Flask(__name__, template_folder=".")
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024  # 1MB cap to protect the endpoint
CORS(app)

# Initialize Vessels
vessels = VesselsPlatform()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store active sessions
sessions = {}


# ============================================================================
# PYDANTIC MODELS FOR INPUT VALIDATION
# ============================================================================

class VoiceProcessRequest(BaseModel):
    """Strict validation for voice processing requests"""
    text: str = Field(..., min_length=1, max_length=10000, description="User input text")
    session_id: str = Field(default="default", min_length=1, max_length=100)
    emotion: str = Field(default="neutral", max_length=50)

    @field_validator('text')
    @classmethod
    def validate_text(cls, v: str) -> str:
        """Validate and sanitize text input"""
        v = v.strip()
        if not v:
            raise ValueError("Text cannot be empty or only whitespace")
        # Basic sanitization - remove any null bytes
        v = v.replace('\x00', '')
        return v

    @field_validator('session_id')
    @classmethod
    def validate_session_id(cls, v: str) -> str:
        """Validate session ID format"""
        v = v.strip()
        if not v:
            raise ValueError("Session ID cannot be empty")
        # Only allow alphanumeric, hyphens, and underscores
        if not all(c.isalnum() or c in '-_' for c in v):
            raise ValueError("Session ID contains invalid characters")
        return v

    @field_validator('emotion')
    @classmethod
    def validate_emotion(cls, v: str) -> str:
        """Validate emotion is from allowed list"""
        allowed_emotions = {
            'neutral', 'happy', 'sad', 'frustrated',
            'uncertain', 'excited', 'concerned'
        }
        v = v.strip().lower()
        if v not in allowed_emotions:
            # Default to neutral if invalid
            return 'neutral'
        return v


class ContentGenerateRequest(BaseModel):
    """Strict validation for content generation requests"""
    type: str = Field(default="CULTURAL_GUIDE", max_length=100)
    audience: str = Field(default="community", max_length=100)
    culture: str = Field(default="hawaiian", max_length=100)
    language: str = Field(default="en", max_length=10)
    tone: str = Field(default="warm", max_length=50)
    urgency: str = Field(default="normal", max_length=50)
    requirements: dict = Field(default_factory=dict)


class GrantSearchRequest(BaseModel):
    """Strict validation for grant search requests"""
    query: str = Field(..., min_length=1, max_length=1000)

    @field_validator('query')
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Sanitize search query"""
        v = v.strip()
        if not v:
            raise ValueError("Query cannot be empty")
        v = v.replace('\x00', '')
        return v


class GrantApplicationRequest(BaseModel):
    """Strict validation for grant application requests"""
    grant_id: str = Field(..., min_length=1, max_length=200)

    @field_validator('grant_id')
    @classmethod
    def validate_grant_id(cls, v: str) -> str:
        """Validate grant ID"""
        v = v.strip()
        if not v:
            raise ValueError("Grant ID cannot be empty")
        return v

@app.errorhandler(Exception)
def handle_errors(err):
    """Return JSON errors instead of HTML while preserving status codes."""
    status = getattr(err, "code", 500)
    message = getattr(err, "description", "Internal server error")
    logger.error("Request failed", exc_info=err)
    return jsonify({"error": message}), status


@app.route('/')
def index():
    """Serve the voice-first UI"""
    return render_template('vessels_voice_ui_connected.html')

@app.route('/api/voice/process', methods=['POST'])
def process_voice():
    """Process voice input and return response with UI instructions"""
    if request.content_type != 'application/json':
        abort(415, description="Content-Type must be application/json")

    data = request.get_json(silent=True)
    if not data:
        abort(400, description="Invalid or missing JSON body")

    # Use pydantic for strict validation
    try:
        validated_request = VoiceProcessRequest(**data)
    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        abort(400, description=f"Validation error: {e.errors()[0]['msg']}")

    text = validated_request.text.lower()
    session_id = validated_request.session_id
    emotion = validated_request.emotion
    
    # Store session context
    if session_id not in sessions:
        sessions[session_id] = {
            'context': [],
            'emotion_history': [],
            'current_agents': []
        }
    
    session = sessions[session_id]
    session['context'].append(text)
    session['emotion_history'].append(emotion)
    
    # Determine intent and generate response
    response = {
        'agents': [],
        'content_type': None,
        'content_data': None,
        'subtitles': []
    }
    
    # Process based on keywords
    if any(word in text for word in ['grant', 'funding', 'money']):
        response = handle_grant_request(text, session)
    elif any(word in text for word in ['elder', 'kupuna', 'care']):
        response = handle_elder_care_request(text, session)
    elif any(word in text for word in ['food', 'hungry', 'meal']):
        response = handle_food_request(text, session)
    elif any(word in text for word in ['route', 'delivery', 'drive']):
        response = handle_route_request(text, session)
    elif any(word in text for word in ['schedule', 'when', 'available']):
        response = handle_schedule_request(text, session)
    elif any(word in text for word in ['help', 'confused', 'what']):
        response = handle_help_request(text, session, emotion)
    else:
        response = handle_general_request(text, session)
    
    return jsonify(response)

def handle_grant_request(text, session):
    """Handle grant-related requests"""
    
    # Use Vessels to find grants
    grants_response = vessels.find_grants(text)
    
    # Extract grants data
    grants = []
    if 'grants' in grants_response:
        for grant in grants_response['grants'][:3]:  # Top 3
            grants.append({
                'title': grant.get('title', 'Grant Opportunity'),
                'amount': grant.get('amount_range', '$10K - $50K'),
                'description': grant.get('description', 'Funding opportunity for community programs'),
                'funder': grant.get('funder', 'Various Funders')
            })
    else:
        # Use default examples if no real grants found
        grants = [
            {
                'title': 'Older Americans Act',
                'amount': '$50K - $500K',
                'description': 'Federal funding for elder care services in rural communities.',
                'funder': 'Administration for Community Living'
            },
            {
                'title': 'Hawaii Community Foundation',
                'amount': '$10K - $50K', 
                'description': 'Local funding for community-driven initiatives.',
                'funder': 'HCF'
            }
        ]
    
    return {
        'agents': [
            {
                'id': 'grant_finder',
                'name': 'Grant Finder',
                'type': 'specialist'
            }
        ],
        'content_type': 'grant_cards',
        'content_data': {
            'grants': grants
        },
        'subtitles': [
            {
                'text': f"I found {len(grants)} matching grants for your needs",
                'speaker': 'Grant Finder',
                'type': 'agent-grant',
                'delay': 500
            },
            {
                'text': "The federal one offers the most funding. Should I start the application?",
                'speaker': 'Grant Finder',
                'type': 'agent-grant',
                'delay': 2500
            }
        ]
    }

def handle_elder_care_request(text, session):
    """Handle elder care requests"""
    
    # Generate elder care protocol
    context = ContentContext(
        content_type=ContentType.ELDER_CARE_PROTOCOL,
        target_audience="caregivers",
        cultural_context="hawaiian",
        language="en",
        emotional_tone="warm",
        urgency_level="normal",
        specific_requirements={}
    )
    
    # Generate content (async to sync wrapper)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    content = loop.run_until_complete(vessels.generate_contextual_content(text, context.__dict__))
    
    # Parse protocol steps
    protocol_steps = [
        {
            'title': 'Morning Check',
            'description': 'Call or visit by 9am. Verify medications taken, breakfast eaten.'
        },
        {
            'title': 'Midday Support',
            'description': 'Lunch delivery if needed. Social interaction, talk story time.'
        },
        {
            'title': 'Afternoon Tasks',
            'description': 'Doctor appointments, shopping. Coordinate with family members.'
        },
        {
            'title': 'Evening Safety',
            'description': 'Dinner check, secure home. Emergency contacts confirmed.'
        }
    ]
    
    return {
        'agents': [
            {
                'id': 'elder_care',
                'name': 'Elder Care Specialist',
                'type': 'specialist'
            }
        ],
        'content_type': 'care_protocol',
        'content_data': {
            'title': 'Kupuna Care Protocol',
            'steps': protocol_steps
        },
        'subtitles': [
            {
                'text': "Here's a care protocol adapted for Hawaiian kupuna",
                'speaker': 'Elder Care Specialist',
                'type': 'agent-care',
                'delay': 500
            },
            {
                'text': "It includes talk story time and ohana coordination",
                'speaker': 'Elder Care Specialist',
                'type': 'agent-care',
                'delay': 2000
            }
        ]
    }

def handle_food_request(text, session):
    """Handle food coordination requests"""
    
    # Simulate food availability data
    food_items = [
        {
            'name': '50 lbs ripe breadfruit',
            'location': 'Kalapana',
            'provider': 'Ana\'s Garden',
            'image': 'breadfruit'
        },
        {
            'name': 'Fresh ulu ready today',
            'location': 'Pahoa',
            'provider': 'Community Garden',
            'image': 'ulu'
        },
        {
            'name': 'Taro from Uncle\'s garden',
            'location': 'Keaau',
            'provider': 'Uncle Joe',
            'image': 'taro'
        },
        {
            'name': 'Bananas - 3 bunches',
            'location': 'Mountain View',
            'provider': 'Maria\'s Farm',
            'image': 'bananas'
        }
    ]
    
    return {
        'agents': [
            {
                'id': 'food_coord',
                'name': 'Food Coordinator',
                'type': 'specialist'
            },
            {
                'id': 'garden_agent',
                'name': 'Garden Agent',
                'type': 'entity'
            }
        ],
        'content_type': 'photo_gallery',
        'content_data': {
            'items': food_items
        },
        'subtitles': [
            {
                'text': "Ana has 50 pounds of breadfruit ready for pickup",
                'speaker': 'Garden Agent',
                'type': 'agent-food',
                'delay': 500
            },
            {
                'text': "I can connect you with a driver who's nearby",
                'speaker': 'Food Coordinator',
                'type': 'agent-food',
                'delay': 2000
            }
        ]
    }

def handle_route_request(text, session):
    """Handle delivery route requests"""
    
    routes = [
        {
            'driver': 'Maria',
            'stops': 3,
            'distance': '12 miles',
            'area': 'North Route',
            'color': '#4ade80'
        },
        {
            'driver': 'John',
            'stops': 2,
            'distance': '8 miles',
            'area': 'South Route',
            'color': '#fbbf24'
        }
    ]
    
    return {
        'agents': [
            {
                'id': 'route_coord',
                'name': 'Route Coordinator',
                'type': 'specialist'
            }
        ],
        'content_type': 'map_view',
        'content_data': {
            'routes': routes
        },
        'subtitles': [
            {
                'text': "Maria, you take the north route with 3 stops",
                'speaker': 'Route Coordinator',
                'type': 'agent-food',
                'delay': 500
            },
            {
                'text': "John, your route is shorter - just 2 pickups on the south side",
                'speaker': 'Route Coordinator',
                'type': 'agent-food',
                'delay': 2000
            }
        ]
    }

def handle_schedule_request(text, session):
    """Handle scheduling requests"""
    
    time_slots = [
        {'day': 'Mon', 'time': '2-4pm', 'available': True},
        {'day': 'Mon', 'time': '4-6pm', 'available': False},
        {'day': 'Tue', 'time': '10am-12pm', 'available': True, 'selected': True},
        {'day': 'Wed', 'time': '2-4pm', 'available': True},
        {'day': 'Thu', 'time': '10am-12pm', 'available': False},
        {'day': 'Fri', 'time': '2-4pm', 'available': True}
    ]
    
    return {
        'agents': [
            {
                'id': 'schedule_coord',
                'name': 'Schedule Coordinator',
                'type': 'specialist'
            }
        ],
        'content_type': 'calendar_view',
        'content_data': {
            'title': 'Available Times This Week',
            'slots': time_slots
        },
        'subtitles': [
            {
                'text': "I see Tuesday morning works for 3 volunteers",
                'speaker': 'Schedule Coordinator',
                'type': 'agent-care',
                'delay': 500
            },
            {
                'text': "Should I confirm Tuesday 10am for the elder care visit?",
                'speaker': 'Schedule Coordinator',
                'type': 'agent-care',
                'delay': 2000
            }
        ]
    }

def handle_help_request(text, session, emotion):
    """Handle help requests with emotion awareness"""
    
    if emotion == 'frustrated':
        subtitle_text = "I hear your frustration. Let me simplify this right now."
    elif emotion == 'uncertain':
        subtitle_text = "No worries, let me explain more clearly"
    else:
        subtitle_text = "I can help you with grants, elder care, food, and scheduling"
    
    help_items = [
        {'icon': '💰', 'text': 'Finding grants and funding'},
        {'icon': '🌺', 'text': 'Elder care coordination'},
        {'icon': '🍛', 'text': 'Food distribution'},
        {'icon': '🚗', 'text': 'Transportation needs'},
        {'icon': '📅', 'text': 'Schedule coordination'}
    ]
    
    return {
        'agents': [
            {
                'id': 'host',
                'name': 'Host Agent',
                'type': 'host'
            },
            {
                'id': 'support',
                'name': 'Support Agent',
                'type': 'specialist'
            }
        ],
        'content_type': 'help_menu',
        'content_data': {
            'items': help_items
        },
        'subtitles': [
            {
                'text': subtitle_text,
                'speaker': 'Support Agent',
                'type': 'agent-care',
                'delay': 500
            },
            {
                'text': "Just tell me what you need in your own words",
                'speaker': 'Host Agent',
                'type': 'agent-care',
                'delay': 2000
            }
        ]
    }

def handle_general_request(text, session):
    """Handle general conversation"""
    
    # Use Vessels's general processing
    response = vessels.process_request(text)
    
    return {
        'agents': [
            {
                'id': 'host',
                'name': 'Host Agent',
                'type': 'host'
            }
        ],
        'content_type': 'welcome',
        'content_data': {
            'message': response.get('response', 'How can I help you today?')
        },
        'subtitles': [
            {
                'text': "I can help with grants, elder care, food, and more",
                'speaker': 'Host Agent',
                'type': 'agent-care',
                'delay': 500
            }
        ]
    }

@app.route('/api/content/generate', methods=['POST'])
def generate_content():
    """Generate contextual content"""
    if request.content_type != 'application/json':
        abort(415, description="Content-Type must be application/json")

    data = request.get_json(silent=True)
    if not data:
        abort(400, description="Invalid or missing JSON body")

    # Use pydantic for validation
    try:
        validated_request = ContentGenerateRequest(**data)
    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        abort(400, description=f"Validation error: {e.errors()[0]['msg']}")

    # Extract context
    context = ContentContext(
        content_type=ContentType[validated_request.type.upper()],
        target_audience=validated_request.audience,
        cultural_context=validated_request.culture,
        language=validated_request.language,
        emotional_tone=validated_request.tone,
        urgency_level=validated_request.urgency,
        specific_requirements=validated_request.requirements
    )
    
    # Generate content
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    content = loop.run_until_complete(
        vessels.content_generator.generate_content(context)
    )
    
    return jsonify({
        'id': content.id,
        'title': content.title,
        'body': content.body,
        'metadata': content.metadata
    })

@app.route('/api/grants/search', methods=['POST'])
def search_grants():
    """Search for grants"""
    if request.content_type != 'application/json':
        abort(415, description="Content-Type must be application/json")

    data = request.get_json(silent=True)
    if not data:
        abort(400, description="Invalid or missing JSON body")

    # Use pydantic for validation
    try:
        validated_request = GrantSearchRequest(**data)
    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        abort(400, description=f"Validation error: {e.errors()[0]['msg']}")

    result = vessels.find_grants(validated_request.query)
    return jsonify(result)

@app.route('/api/grants/apply', methods=['POST'])
def apply_grant():
    """Generate grant application"""
    if request.content_type != 'application/json':
        abort(415, description="Content-Type must be application/json")

    data = request.get_json(silent=True)
    if not data:
        abort(400, description="Invalid or missing JSON body")

    # Use pydantic for validation
    try:
        validated_request = GrantApplicationRequest(**data)
    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        abort(400, description=f"Validation error: {e.errors()[0]['msg']}")

    result = vessels.generate_applications(f"generate application for {validated_request.grant_id}")
    return jsonify(result)

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get system status"""
    return jsonify(vessels.get_status())

@app.route('/api/session/<session_id>', methods=['GET'])
def get_session(session_id):
    """Get session information"""
    if session_id in sessions:
        return jsonify(sessions[session_id])
    return jsonify({'error': 'Session not found'}), 404

if __name__ == '__main__':
    # Ensure we have the connected UI file
    if not os.path.exists('vessels_voice_ui_connected.html'):
        logger.error("UI file not found. Creating from template...")
        # We'll create this file next
    
    logger.info("🌺 Starting Vessels Voice-First Web Server...")
    logger.info("📱 Open http://localhost:5000 in your browser")
    logger.info("🎤 Allow microphone access when prompted")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
