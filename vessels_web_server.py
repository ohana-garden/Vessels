#!/usr/bin/env python3
"""
VESSELS WEB SERVER - Clean Architecture
Delegates all logic to vessels.system.VesselsSystem
"""

from flask import Flask, abort, jsonify, render_template, request
from flask_cors import CORS
import logging
import os

# Import the NEW Clean System
from vessels.system import VesselsSystem

app = Flask(__name__, template_folder=".")
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024
CORS(app)

# Initialize the Clean System
# This creates the DB and connects to Kala
system = VesselsSystem()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple in-memory session store (Replace with Redis in production)
SESSION_STORE = {}

@app.route('/')
def index():
    if os.path.exists('vessels_voice_ui_connected.html'):
        return render_template('vessels_voice_ui_connected.html')
    return "UI Template Not Found", 404

@app.route('/api/voice/process', methods=['POST'])
def process_voice():
    if not request.is_json:
        abort(415)

    data = request.get_json()
    text = data.get('text', '').strip()
    session_id = data.get('session_id', 'default')

    if not text:
        abort(400, "Text required")

    # Update Session State
    if session_id not in SESSION_STORE:
        SESSION_STORE[session_id] = {'history': []}
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
                'text': f"Processed via System: {result['agent']}",
                'speaker': result['agent'],
                'type': 'status',
                'delay': 500
            }]
        }
        return jsonify(response)

    except Exception as e:
        logger.error(f"System processing error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify(system.get_status())

if __name__ == '__main__':
    logger.info("🌺 Starting Vessels (Clean Architecture)...")
    app.run(host='0.0.0.0', port=5000)
