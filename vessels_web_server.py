#!/usr/bin/env python3
"""
VESSELS WEB SERVER - Cleaned & Standardized
Voice-First UI with proper architectural integration
"""

from flask import Flask, abort, jsonify, render_template, request
from flask_cors import CORS
import logging
import os

# Import the Clean System (replaces vessels_fixed)
from vessels.system import VesselsSystem

app = Flask(__name__, template_folder=".")
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024  # 1MB cap
CORS(app)

# Initialize the Clean System
system = VesselsSystem()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# TODO: Replace with Redis/FalkorDB in production
# This is a known limitation for Tier 2+ deployment
SESSION_STORE = {}


@app.errorhandler(Exception)
def handle_errors(err):
    """Return JSON errors with proper status codes."""
    status = getattr(err, "code", 500)
    message = getattr(err, "description", "Internal server error")
    logger.error("Request failed", exc_info=err)
    return jsonify({"error": message}), status


@app.route('/')
def index():
    """Serve the voice-first UI"""
    if os.path.exists('vessels_voice_ui_connected.html'):
        return render_template('vessels_voice_ui_connected.html')
    return jsonify({"error": "UI template not found"}), 404


@app.route('/api/voice/process', methods=['POST'])
def process_voice():
    """
    Process voice input and return response with UI instructions.
    Delegates all business logic to VesselsSystem.
    """
    # Validate request
    if not request.is_json:
        abort(415, description="Content-Type must be application/json")

    data = request.get_json()
    text = data.get('text', '').strip()
    session_id = data.get('session_id', 'default')

    if not text or len(text) > 10000:
        abort(400, description="Text is required and must be under 10k characters")

    # Update Session State
    if session_id not in SESSION_STORE:
        SESSION_STORE[session_id] = {
            'history': [],
            'emotion_history': [],
            'context': {}
        }

    session = SESSION_STORE[session_id]
    session['history'].append(text)

    # Store emotion if provided
    emotion = data.get('emotion', 'neutral')
    session['emotion_history'].append(emotion)

    # Delegate to the Core System
    try:
        result = system.process_request(
            text=text,
            session_id=session_id,
            context=session
        )

        # Map System result to UI format
        response = _format_ui_response(result)

        return jsonify(response)

    except Exception as e:
        logger.error(f"System processing error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


def _format_ui_response(system_result: dict) -> dict:
    """
    Format VesselsSystem response for the UI.
    This isolates UI-specific formatting from business logic.
    """
    agent_name = system_result.get('agent', 'Host')
    content_type = system_result.get('content_type', 'chat')
    data = system_result.get('data', {})

    response = {
        'agents': [{
            'id': agent_name.lower().replace(' ', '_'),
            'name': agent_name,
            'type': 'specialist' if agent_name != 'Host' else 'host'
        }],
        'content_type': content_type,
        'content_data': data,
        'subtitles': _generate_subtitles(agent_name, content_type, data)
    }

    return response


def _generate_subtitles(agent_name: str, content_type: str, data: dict) -> list:
    """Generate subtitle messages based on agent and content type."""
    subtitles = []

    # Generate appropriate subtitle based on content type
    if content_type == 'grant_cards':
        grants = data.get('grants', [])
        subtitles.append({
            'text': f"I found {len(grants)} matching grants for your needs",
            'speaker': agent_name,
            'type': 'agent-grant',
            'delay': 500
        })
        if grants:
            subtitles.append({
                'text': "The federal one offers the most funding. Should I start the application?",
                'speaker': agent_name,
                'type': 'agent-grant',
                'delay': 2500
            })

    elif content_type == 'care_protocol':
        subtitles.append({
            'text': "Here's a care protocol adapted for Hawaiian kupuna",
            'speaker': agent_name,
            'type': 'agent-care',
            'delay': 500
        })
        subtitles.append({
            'text': "It includes talk story time and ohana coordination",
            'speaker': agent_name,
            'type': 'agent-care',
            'delay': 2000
        })

    else:
        # Default subtitle
        message = data.get('message', 'Processing your request...')
        subtitles.append({
            'text': message,
            'speaker': agent_name,
            'type': 'agent-care',
            'delay': 500
        })

    return subtitles


@app.route('/api/status', methods=['GET'])
def get_status():
    """Get system status from VesselsSystem."""
    try:
        status = system.get_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Status check failed: {e}", exc_info=True)
        return jsonify({
            "error": "Status check failed",
            "system": "error"
        }), 500


@app.route('/api/session/<session_id>', methods=['GET'])
def get_session(session_id):
    """Get session information."""
    if session_id in SESSION_STORE:
        return jsonify(SESSION_STORE[session_id])
    return jsonify({'error': 'Session not found'}), 404


if __name__ == '__main__':
    logger.info("🌺 Starting Refactored Vessels Server...")
    logger.info("📱 Open http://localhost:5000 in your browser")
    logger.info("🎤 Allow microphone access when prompted")
    logger.info("🏗️  Architecture: Clean separation between web layer and business logic")

    app.run(host='0.0.0.0', port=5000, debug=False)
