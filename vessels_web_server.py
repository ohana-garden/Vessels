#!/usr/bin/env python3
"""
VESSELS WEB SERVER - Clean Architecture
Delegates all logic to vessels.system.VesselsSystem
"""

from flask import Flask, abort, jsonify, render_template, request
from flask_cors import CORS
import logging
import os
import threading

# Import the NEW Clean System
from vessels.system import VesselsSystem
from vessels_gist_extractor import get_best_gist

# Configuration constants
MAX_REQUEST_SIZE = 1024 * 1024  # 1MB
MAX_TEXT_LENGTH = 10000
MAX_SESSION_ID_LENGTH = 255
ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', 'http://localhost:3000,http://localhost:5000').split(',')

app = Flask(__name__, template_folder=".")
app.config["MAX_CONTENT_LENGTH"] = MAX_REQUEST_SIZE

# Secure CORS configuration - only allow specified origins
CORS(app, resources={
    r"/api/*": {
        "origins": ALLOWED_ORIGINS,
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Initialize the Clean System
# This creates the DB and connects to Kala
system = VesselsSystem()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Thread-safe session store (Replace with Redis in production)
_session_lock = threading.RLock()
SESSION_STORE = {}

@app.route('/')
def index():
    if os.path.exists('vessels_voice_ui_connected.html'):
        return render_template('vessels_voice_ui_connected.html')
    return "UI Template Not Found", 404

@app.route('/api/voice/process', methods=['POST'])
def process_voice():
    """Process voice/text input through the Vessels system."""
    if not request.is_json:
        abort(415, description="Content-Type must be application/json")

    data = request.get_json()
    if not data:
        abort(400, description="Request body required")

    # Input validation
    text = data.get('text', '')
    if not isinstance(text, str):
        abort(400, description="'text' must be a string")
    text = text.strip()

    if not text:
        abort(400, description="'text' is required and cannot be empty")

    if len(text) > MAX_TEXT_LENGTH:
        abort(400, description=f"'text' exceeds maximum length of {MAX_TEXT_LENGTH} characters")

    session_id = data.get('session_id', 'default')
    if not isinstance(session_id, str):
        abort(400, description="'session_id' must be a string")

    if len(session_id) > MAX_SESSION_ID_LENGTH:
        abort(400, description=f"'session_id' exceeds maximum length of {MAX_SESSION_ID_LENGTH} characters")

    # Thread-safe session update
    with _session_lock:
        if session_id not in SESSION_STORE:
            SESSION_STORE[session_id] = {'history': []}
        SESSION_STORE[session_id]['history'].append(text)
        context = SESSION_STORE[session_id].copy()

    try:
        # DELEGATE TO CORE SYSTEM
        result = system.process_request(
            text=text,
            session_id=session_id,
            context=context
        )

        # Map System result to UI format
        response = {
            'agents': [{'id': result['agent'].lower(), 'name': result['agent'], 'type': 'specialist'}],
            'content_type': result.get('content_type', 'chat'),
            'content_data': result.get('data', {}),
            'subtitles': [{
                'text': f"Processed via System: {result['agent']}",
                'speaker': result['agent'],
                'type': 'status',
                'delay': 500
            }]
        }

        # Extract gist from response if present
        response_text = result.get('response', '') or str(result.get('data', ''))
        gist = get_best_gist(response_text, text)
        if gist and gist.get('confidence', 0) >= 0.7:
            response['gist'] = gist

        return jsonify(response)

    except ValueError as e:
        # Known validation/business logic errors - safe to expose message
        logger.warning(f"Validation error: {e}")
        return jsonify({'error': str(e)}), 400
    except KeyError as e:
        logger.warning(f"Missing data error: {e}")
        return jsonify({'error': 'Invalid response from processing system'}), 500
    except Exception as e:
        # Unknown errors - log details but return generic message
        logger.error(f"System processing error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify(system.get_status())

if __name__ == '__main__':
    logger.info("🌺 Starting Vessels (Clean Architecture)...")
    app.run(host='0.0.0.0', port=5000)
