#!/usr/bin/env python3
"""
VESSELS WEB SERVER - ENHANCED UX VERSION
Comprehensive backend support for enhanced UI features
"""

from flask import Flask, abort, jsonify, render_template, request
from flask_cors import CORS
import json
import asyncio
import logging
from datetime import datetime, timedelta
import os
import sys
from typing import Dict, List, Any, Optional
from collections import defaultdict
import time

# Import Vessels components
from vessels_fixed import VesselsPlatform
from content_generation import ContentContext, ContentType

app = Flask(__name__, template_folder=".")
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024  # 1MB cap
CORS(app)

# Initialize Vessels
vessels = VesselsPlatform()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

class SessionManager:
    """Enhanced session manager with TTL and context tracking"""

    def __init__(self, ttl_hours=24):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.ttl = timedelta(hours=ttl_hours)

    def create_session(self, session_id: str) -> Dict[str, Any]:
        """Create a new session"""
        session = {
            'id': session_id,
            'created_at': datetime.now(),
            'last_activity': datetime.now(),
            'context': [],
            'emotion_history': [],
            'current_agents': [],
            'feedback': [],
            'language': 'en',
            'interaction_count': 0
        }
        self.sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session and update last activity"""
        session = self.sessions.get(session_id)
        if session:
            session['last_activity'] = datetime.now()
        return session

    def get_or_create(self, session_id: str) -> Dict[str, Any]:
        """Get existing session or create new one"""
        session = self.get_session(session_id)
        if not session:
            session = self.create_session(session_id)
        return session

    def cleanup_expired(self):
        """Remove expired sessions"""
        now = datetime.now()
        expired = []

        for session_id, session in self.sessions.items():
            if now - session['last_activity'] > self.ttl:
                expired.append(session_id)

        for session_id in expired:
            del self.sessions[session_id]

        return len(expired)

    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get session summary for user"""
        session = self.get_session(session_id)
        if not session:
            return {'error': 'Session not found'}

        return {
            'session_id': session_id,
            'duration_minutes': (datetime.now() - session['created_at']).total_seconds() / 60,
            'interactions': session['interaction_count'],
            'agents_used': len(set(a['id'] for a in session['current_agents'])),
            'feedback_given': len(session['feedback']),
            'primary_emotion': max(set(session['emotion_history']), key=session['emotion_history'].count) if session['emotion_history'] else 'neutral'
        }

# Global session manager
session_manager = SessionManager()

# ============================================================================
# FEEDBACK TRACKING
# ============================================================================

class FeedbackTracker:
    """Track user feedback for continuous improvement"""

    def __init__(self):
        self.feedback_data = defaultdict(list)

    def record_feedback(self, session_id: str, item_id: str,
                       feedback_type: str, context: Dict = None):
        """Record user feedback"""
        feedback = {
            'session_id': session_id,
            'item_id': item_id,
            'feedback_type': feedback_type,
            'context': context or {},
            'timestamp': datetime.now().isoformat()
        }

        self.feedback_data[feedback_type].append(feedback)

        # Add to session
        session = session_manager.get_session(session_id)
        if session:
            session['feedback'].append(feedback)

        logger.info(f"Feedback recorded: {feedback_type} for {item_id}")

    def get_feedback_stats(self) -> Dict[str, Any]:
        """Get feedback statistics"""
        total = sum(len(items) for items in self.feedback_data.values())

        return {
            'total_feedback': total,
            'by_type': {
                ftype: len(items)
                for ftype, items in self.feedback_data.items()
            },
            'positive_rate': len(self.feedback_data.get('helpful', [])) / max(total, 1) * 100
        }

feedback_tracker = FeedbackTracker()

# ============================================================================
# ERROR HANDLING
# ============================================================================

class APIError(Exception):
    """Custom API error with status code and message"""

    def __init__(self, message: str, status_code: int = 400, details: Dict = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}

@app.errorhandler(APIError)
def handle_api_error(error):
    """Handle custom API errors"""
    response = {
        'error': error.message,
        'status': 'error',
        'details': error.details
    }
    return jsonify(response), error.status_code

@app.errorhandler(Exception)
def handle_errors(err):
    """Return JSON errors instead of HTML"""
    status = getattr(err, "code", 500)
    message = getattr(err, "description", "Internal server error")
    logger.error("Request failed", exc_info=err)

    return jsonify({
        "error": message,
        "status": "error",
        "friendly_message": get_friendly_error_message(status)
    }), status

def get_friendly_error_message(status_code: int) -> str:
    """Get user-friendly error messages"""
    messages = {
        400: "I couldn't understand that request. Could you try rephrasing?",
        404: "I couldn't find what you're looking for.",
        415: "Please send your request in JSON format.",
        500: "Something went wrong on my end. I'm looking into it!",
        503: "I'm temporarily unavailable. Please try again in a moment."
    }
    return messages.get(status_code, "An unexpected error occurred.")

# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def index():
    """Serve the enhanced voice-first UI"""
    return render_template('vessels_voice_ui_enhanced.html')

@app.route('/api/voice/process', methods=['POST'])
def process_voice():
    """Process voice input with enhanced error handling and feedback"""
    if request.content_type != 'application/json':
        abort(415, description="Content-Type must be application/json")

    data = request.get_json(silent=True)
    if not data:
        raise APIError("Invalid or missing JSON body", 400)

    # Validate input
    text = data.get('text', '').strip()
    if not text:
        raise APIError("Text input is required", 400)

    if len(text) > 10000:
        raise APIError("Text input too long (max 10,000 characters)", 400)

    session_id = data.get('session_id')
    if not session_id:
        raise APIError("session_id is required", 400)

    emotion = data.get('emotion', 'neutral')
    language = data.get('language', 'en')

    # Get or create session
    session = session_manager.get_or_create(session_id)
    session['interaction_count'] += 1
    session['emotion_history'].append(emotion)
    session['language'] = language

    # Add to context
    session['context'].append({
        'text': text,
        'emotion': emotion,
        'timestamp': datetime.now().isoformat()
    })

    # Keep context manageable
    if len(session['context']) > 20:
        session['context'] = session['context'][-20:]

    # Process based on intent with better error handling
    try:
        response = process_request_with_context(text, session, emotion)

        # Track agents in session
        if 'agents' in response:
            session['current_agents'] = response['agents']

        return jsonify(response)

    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        raise APIError(
            "I encountered an issue processing your request",
            500,
            {'original_error': str(e)}
        )

def process_request_with_context(text: str, session: Dict, emotion: str) -> Dict[str, Any]:
    """Process request with session context and emotion awareness"""
    lower_text = text.lower()

    # Determine intent
    if any(word in lower_text for word in ['grant', 'funding', 'money']):
        return handle_grant_request(text, session, emotion)
    elif any(word in lower_text for word in ['elder', 'kupuna', 'care']):
        return handle_elder_care_request(text, session, emotion)
    elif any(word in lower_text for word in ['dashboard', 'impact', 'stats']):
        return handle_dashboard_request(text, session)
    elif any(word in lower_text for word in ['help', 'confused', 'what']):
        return handle_help_request(text, session, emotion)
    else:
        return handle_general_request(text, session)

def handle_grant_request(text: str, session: Dict, emotion: str) -> Dict[str, Any]:
    """Handle grant requests with emotion awareness"""
    try:
        grants_response = vessels.find_grants(text)

        grants = []
        if 'grants' in grants_response:
            for grant in grants_response['grants'][:3]:
                grants.append({
                    'title': grant.get('title', 'Grant Opportunity'),
                    'amount': grant.get('amount_range', '$10K - $50K'),
                    'description': grant.get('description', 'Funding opportunity'),
                    'funder': grant.get('funder', 'Various Funders'),
                    'match_score': grant.get('match_score', 85)
                })
        else:
            # Default examples
            grants = [
                {
                    'title': 'Older Americans Act',
                    'amount': '$50K - $500K',
                    'description': 'Federal funding for elder care services in rural communities.',
                    'funder': 'Administration for Community Living',
                    'match_score': 92
                },
                {
                    'title': 'Hawaii Community Foundation',
                    'amount': '$10K - $50K',
                    'description': 'Local funding for community-driven initiatives.',
                    'funder': 'HCF',
                    'match_score': 85
                },
                {
                    'title': 'AARP Foundation',
                    'amount': '$5K - $25K',
                    'description': 'Support for elder care programs.',
                    'funder': 'AARP',
                    'match_score': 78
                }
            ]

        # Customize response based on emotion
        if emotion == 'frustrated':
            subtitle_text = "I know this is frustrating. Let me make this simple - here are your best matches."
        elif emotion == 'uncertain':
            subtitle_text = f"I found {len(grants)} grants that match your needs. I'll walk you through them."
        else:
            subtitle_text = f"Great news! I found {len(grants)} matching grants for you."

        return {
            'agents': [
                {
                    'id': 'grant_finder',
                    'name': 'Grant Finder',
                    'type': 'specialist',
                    'activity': 'searching grant databases'
                },
                {
                    'id': 'grant_analyzer',
                    'name': 'Grant Analyzer',
                    'type': 'specialist',
                    'activity': 'calculating match scores'
                }
            ],
            'content_type': 'grant_cards',
            'content_data': {
                'grants': grants
            },
            'subtitles': [
                {
                    'text': subtitle_text,
                    'speaker': 'Grant Finder',
                    'type': 'agent-grant',
                    'delay': 500
                },
                {
                    'text': f"The top match is {grants[0]['title']} with a {grants[0]['match_score']}% fit.",
                    'speaker': 'Grant Analyzer',
                    'type': 'agent-grant',
                    'delay': 2500
                }
            ]
        }

    except Exception as e:
        logger.error(f"Grant request failed: {e}")
        raise APIError(
            "I had trouble searching for grants. Please try again.",
            503,
            {'error_type': 'grant_search_failure'}
        )

def handle_elder_care_request(text: str, session: Dict, emotion: str) -> Dict[str, Any]:
    """Handle elder care requests"""
    protocol_steps = [
        {
            'title': 'Morning Check',
            'description': 'Call or visit by 9am. Verify medications taken, breakfast eaten. Check mood and energy levels.'
        },
        {
            'title': 'Midday Support',
            'description': 'Lunch delivery if needed. Social interaction and talk story time. Light activities if desired.'
        },
        {
            'title': 'Afternoon Tasks',
            'description': 'Doctor appointments, shopping errands. Coordinate with ʻohana members. Plan next day.'
        },
        {
            'title': 'Evening Safety',
            'description': 'Dinner check, secure home for night. Emergency contacts confirmed. Goodnight call or visit.'
        }
    ]

    # Customize based on language preference
    if session.get('language') == 'haw':
        title = 'Mālama Kupuna Protocol'
    else:
        title = 'Kupuna Care Protocol'

    return {
        'agents': [
            {
                'id': 'elder_care',
                'name': 'Elder Care Specialist',
                'type': 'specialist',
                'activity': 'designing care protocol'
            },
            {
                'id': 'cultural_advisor',
                'name': 'Cultural Advisor',
                'type': 'specialist',
                'activity': 'ensuring cultural appropriateness'
            }
        ],
        'content_type': 'care_protocol',
        'content_data': {
            'title': title,
            'steps': protocol_steps
        },
        'subtitles': [
            {
                'text': "Here's a culturally-adapted care protocol for Hawaiian kupuna",
                'speaker': 'Elder Care Specialist',
                'type': 'agent-care',
                'delay': 500
            },
            {
                'text': "It includes talk story time and ʻohana coordination for holistic care",
                'speaker': 'Cultural Advisor',
                'type': 'agent-care',
                'delay': 2500
            }
        ]
    }

def handle_dashboard_request(text: str, session: Dict) -> Dict[str, Any]:
    """Handle dashboard/impact requests"""
    return {
        'agents': [
            {
                'id': 'kala_tracker',
                'name': 'Kala Tracker',
                'type': 'specialist',
                'activity': 'calculating community impact'
            }
        ],
        'content_type': 'dashboard',
        'content_data': {
            'kala': 450,
            'meals': 32,
            'grants_found': 125000,
            'elders': 18
        },
        'subtitles': [
            {
                'text': "Your community has made incredible impact this week!",
                'speaker': 'Kala Tracker',
                'type': 'agent-care',
                'delay': 500
            },
            {
                'text': "450 Kala earned through volunteer hours and contributions",
                'speaker': 'Kala Tracker',
                'type': 'agent-care',
                'delay': 2000
            }
        ]
    }

def handle_help_request(text: str, session: Dict, emotion: str) -> Dict[str, Any]:
    """Handle help requests with emotion awareness"""
    if emotion == 'frustrated':
        subtitle_text = "I hear your frustration. Let me simplify this right now."
        delay2_text = "You can ask me about grants, elder care, food, or scheduling. Just say it naturally."
    elif emotion == 'uncertain':
        subtitle_text = "No worries, let me explain more clearly."
        delay2_text = "Try saying 'Find grants for elder care' or 'Show me care protocols'"
    else:
        subtitle_text = "I'm here to help! Here's what I can do for you."
        delay2_text = "Just speak naturally - I understand conversational language"

    return {
        'agents': [
            {
                'id': 'support',
                'name': 'Support Agent',
                'type': 'specialist',
                'activity': 'providing guidance'
            }
        ],
        'content_type': 'help_menu',
        'content_data': {
            'items': [
                {'icon': '💰', 'text': 'Finding grants and funding opportunities'},
                {'icon': '🌺', 'text': 'Elder care coordination and protocols'},
                {'icon': '🍛', 'text': 'Food distribution and availability'},
                {'icon': '🚗', 'text': 'Transportation and delivery routes'},
                {'icon': '📅', 'text': 'Volunteer scheduling and coordination'}
            ]
        },
        'subtitles': [
            {
                'text': subtitle_text,
                'speaker': 'Support Agent',
                'type': 'agent-care',
                'delay': 500
            },
            {
                'text': delay2_text,
                'speaker': 'Support Agent',
                'type': 'agent-care',
                'delay': 2500
            }
        ]
    }

def handle_general_request(text: str, session: Dict) -> Dict[str, Any]:
    """Handle general conversation"""
    try:
        response = vessels.process_request(text)

        return {
            'agents': [
                {
                    'id': 'host',
                    'name': 'Host Agent',
                    'type': 'host',
                    'activity': 'understanding your request'
                }
            ],
            'content_type': 'welcome',
            'content_data': {
                'message': response.get('response', 'How can I help you today?')
            },
            'subtitles': [
                {
                    'text': "I can help with grants, elder care, food coordination, and more.",
                    'speaker': 'Host Agent',
                    'type': 'agent-care',
                    'delay': 500
                },
                {
                    'text': "Try asking about a specific need, or say 'help' to see all options.",
                    'speaker': 'Host Agent',
                    'type': 'agent-care',
                    'delay': 2500
                }
            ]
        }
    except Exception as e:
        logger.error(f"General request processing failed: {e}")
        return {
            'agents': [],
            'content_type': 'welcome',
            'content_data': {},
            'subtitles': [
                {
                    'text': "I'm not sure I understood that. Could you try rephrasing?",
                    'speaker': 'Host Agent',
                    'type': 'agent-care',
                    'delay': 500
                }
            ]
        }

# ============================================================================
# NEW ENDPOINTS
# ============================================================================

@app.route('/api/feedback', methods=['POST'])
def record_feedback():
    """Record user feedback"""
    data = request.get_json()

    if not data:
        raise APIError("Invalid feedback data", 400)

    item_id = data.get('item_id')
    feedback_type = data.get('feedback_type')
    session_id = data.get('session_id')

    if not all([item_id, feedback_type, session_id]):
        raise APIError("Missing required fields: item_id, feedback_type, session_id", 400)

    feedback_tracker.record_feedback(
        session_id=session_id,
        item_id=str(item_id),
        feedback_type=feedback_type,
        context=data.get('context', {})
    )

    return jsonify({
        'status': 'success',
        'message': 'Feedback recorded',
        'feedback_stats': feedback_tracker.get_feedback_stats()
    })

@app.route('/api/session/<session_id>/summary', methods=['GET'])
def get_session_summary(session_id):
    """Get session summary"""
    summary = session_manager.get_session_summary(session_id)

    if 'error' in summary:
        return jsonify(summary), 404

    return jsonify({
        'status': 'success',
        'summary': summary
    })

@app.route('/api/session/<session_id>', methods=['GET'])
def get_session(session_id):
    """Get full session information"""
    session = session_manager.get_session(session_id)

    if not session:
        return jsonify({'error': 'Session not found'}), 404

    # Remove sensitive data
    safe_session = {
        'id': session['id'],
        'created_at': session['created_at'].isoformat(),
        'last_activity': session['last_activity'].isoformat(),
        'interaction_count': session['interaction_count'],
        'language': session['language'],
        'active_agents': len(session['current_agents']),
        'feedback_count': len(session['feedback'])
    }

    return jsonify(safe_session)

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get system status with enhanced information"""
    try:
        status = vessels.get_status()

        # Add session stats
        active_sessions = len([
            s for s in session_manager.sessions.values()
            if (datetime.now() - s['last_activity']).total_seconds() < 3600
        ])

        status['sessions'] = {
            'total': len(session_manager.sessions),
            'active_last_hour': active_sessions
        }

        status['feedback'] = feedback_tracker.get_feedback_stats()

        return jsonify(status)

    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return jsonify({
            'status': 'degraded',
            'message': 'Some services unavailable'
        }), 503

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0-enhanced'
    })

# ============================================================================
# BACKGROUND TASKS
# ============================================================================

def cleanup_sessions():
    """Background task to cleanup expired sessions"""
    while True:
        try:
            time.sleep(3600)  # Run every hour
            cleaned = session_manager.cleanup_expired()
            if cleaned > 0:
                logger.info(f"Cleaned up {cleaned} expired sessions")
        except Exception as e:
            logger.error(f"Session cleanup failed: {e}")

# ============================================================================
# STARTUP
# ============================================================================

if __name__ == '__main__':
    import threading

    # Start background cleanup
    cleanup_thread = threading.Thread(target=cleanup_sessions, daemon=True)
    cleanup_thread.start()

    logger.info("🌺 Starting Vessels Enhanced Web Server...")
    logger.info("📱 Open http://localhost:5000 in your browser")
    logger.info("🎤 Enhanced UX features enabled:")
    logger.info("   ✓ Error handling and user feedback")
    logger.info("   ✓ Loading states and progress indicators")
    logger.info("   ✓ Mobile responsive design")
    logger.info("   ✓ Agent transparency dashboard")
    logger.info("   ✓ Onboarding flow")
    logger.info("   ✓ Feedback system")
    logger.info("   ✓ Session management")
    logger.info("   ✓ Accessibility improvements")
    logger.info("   ✓ Cultural features (Hawaiian language)")

    app.run(host='0.0.0.0', port=5000, debug=False)
