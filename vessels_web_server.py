#!/usr/bin/env python3
"""
VESSELS WEB SERVER - Clean Architecture
Delegates all logic to vessels.system.VesselsSystem
"""

from flask import Flask, abort, jsonify, render_template, request, make_response
from flask_cors import CORS
import logging
import os
import re

# Import the NEW Clean System
from vessels.system import VesselsSystem

app = Flask(__name__, template_folder=".")
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024  # Limit request size to 1MB
CORS(app)

# Initialize the Clean System
# This creates the DB and connects to Kala
system = VesselsSystem()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# TODO: Use Redis or database-backed sessions in production
SESSION_STORE = {}

# Security: Maximum session store size to prevent memory exhaustion
MAX_SESSION_STORE_SIZE = 10000

# Input validation patterns
SESSION_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{1,128}$')
TEXT_MAX_LENGTH = 10000


def add_security_headers(response):
    """Add security headers to all responses."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = "default-src 'self' 'unsafe-inline' 'unsafe-eval'"
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response


app.after_request(add_security_headers)

@app.route('/')
def index():
    if os.path.exists('vessels_voice_ui_connected.html'):
        return render_template('vessels_voice_ui_connected.html')
    return "UI Template Not Found", 404

@app.route('/api/voice/process', methods=['POST'])
def process_voice():
    if not request.is_json:
        abort(415, description="Content-Type must be application/json")

    data = request.get_json()
    if not data:
        abort(400, description="Request body is required")

    # Input validation
    text = data.get('text', '').strip()
    session_id = data.get('session_id', 'default')

    # Validate text
    if not text:
        abort(400, description="Text field is required")

    if len(text) > TEXT_MAX_LENGTH:
        abort(400, description=f"Text exceeds maximum length of {TEXT_MAX_LENGTH} characters")

    # Validate session_id format to prevent injection
    if not SESSION_ID_PATTERN.match(session_id):
        logger.warning(f"Invalid session_id format: {session_id}")
        abort(400, description="Invalid session_id format")

    # Prevent memory exhaustion from unlimited sessions
    if session_id not in SESSION_STORE and len(SESSION_STORE) >= MAX_SESSION_STORE_SIZE:
        logger.warning(f"Session store at capacity ({MAX_SESSION_STORE_SIZE}), rejecting new session")
        abort(503, description="Service temporarily unavailable")

    # Update Session State (In-Memory for now)
    if session_id not in SESSION_STORE:
        SESSION_STORE[session_id] = {'history': [], 'created_at': None}

    # Limit history size per session
    if len(SESSION_STORE[session_id]['history']) > 100:
        SESSION_STORE[session_id]['history'] = SESSION_STORE[session_id]['history'][-100:]

    SESSION_STORE[session_id]['history'].append(text)

    try:
        # DELEGATE TO CORE SYSTEM
        result = system.process_request(
            text=text,
            session_id=session_id,
            context=SESSION_STORE[session_id]
        )

        # Map System result to UI format
        response = {
            'agents': [{'id': result['agent'].lower(), 'name': result['agent'], 'type': 'specialist'}],
            'content_type': result.get('content_type', 'chat'),
            'content_data': result.get('data', {}),
            'subtitles': [{
                'text': f"Processed via Clean Architecture: {result['agent']}",
                'speaker': result['agent'],
                'type': 'status',
                'delay': 500
            }]
        }
        return jsonify(response)

    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        return jsonify({'error': 'Invalid input'}), 400
    except Exception as e:
        logger.error(f"System processing error: {e}", exc_info=True)
        # Don't expose internal error details to clients
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify(system.get_status())

if __name__ == '__main__':
    logger.info("🌺 Starting Vessels (Clean Architecture)...")
    app.run(host='0.0.0.0', port=5000)
