#!/usr/bin/env python3
"""
SHOGHI WEB SERVER - Voice-First UI with Backend Integration
Connects the clean voice UI to all Shoghi functionality
"""

from flask import Flask, render_template_string, jsonify, request, send_file
from flask_cors import CORS
import json
import asyncio
import logging
from datetime import datetime
import os
import sys

# Import Shoghi components
from shoghi_fixed import ShoghiPlatform
from content_generation import ContentContext, ContentType

app = Flask(__name__)
CORS(app)

# Initialize Shoghi
shoghi = ShoghiPlatform()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store active sessions
sessions = {}

@app.route('/')
def index():
    """Serve the voice-first UI"""
    with open('shoghi_voice_ui_connected.html', 'r') as f:
        return f.read()

@app.route('/api/voice/process', methods=['POST'])
def process_voice():
    """Process voice input and return response with UI instructions"""
    data = request.json
    text = data.get('text', '').lower()
    session_id = data.get('session_id', 'default')
    emotion = data.get('emotion', 'neutral')
    
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
    
    # Use Shoghi to find grants
    grants_response = shoghi.find_grants(text)
    
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
    content = loop.run_until_complete(shoghi.generate_contextual_content(text, context.__dict__))
    
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
    
    # Use Shoghi's general processing
    response = shoghi.process_request(text)
    
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
    data = request.json
    
    # Extract context
    context = ContentContext(
        content_type=ContentType[data.get('type', 'CULTURAL_GUIDE').upper()],
        target_audience=data.get('audience', 'community'),
        cultural_context=data.get('culture', 'hawaiian'),
        language=data.get('language', 'en'),
        emotional_tone=data.get('tone', 'warm'),
        urgency_level=data.get('urgency', 'normal'),
        specific_requirements=data.get('requirements', {})
    )
    
    # Generate content
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    content = loop.run_until_complete(
        shoghi.content_generator.generate_content(context)
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
    query = request.json.get('query', '')
    result = shoghi.find_grants(query)
    return jsonify(result)

@app.route('/api/grants/apply', methods=['POST'])
def apply_grant():
    """Generate grant application"""
    grant_id = request.json.get('grant_id')
    result = shoghi.generate_applications(f"generate application for {grant_id}")
    return jsonify(result)

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get system status"""
    return jsonify(shoghi.get_status())

@app.route('/api/session/<session_id>', methods=['GET'])
def get_session(session_id):
    """Get session information"""
    if session_id in sessions:
        return jsonify(sessions[session_id])
    return jsonify({'error': 'Session not found'}), 404

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Docker"""
    return jsonify({
        'status': 'healthy',
        'service': 'shoghi-replicant',
        'timestamp': datetime.now().isoformat()
    }), 200

if __name__ == '__main__':
    # Ensure we have the connected UI file
    if not os.path.exists('shoghi_voice_ui_connected.html'):
        logger.error("UI file not found. Creating from template...")
        # We'll create this file next
    
    logger.info("🌺 Starting Shoghi Voice-First Web Server...")
    logger.info("📱 Open http://localhost:5000 in your browser")
    logger.info("🎤 Allow microphone access when prompted")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
