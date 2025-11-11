#!/bin/bash

# SHOGHI PLATFORM - DEPLOYMENT SCRIPT (FIXED)
# Simple, working deployment for the Shoghi platform

set -e  # Exit on error

echo "🌺 SHOGHI PLATFORM DEPLOYMENT"
echo "=============================="

# Parse command line arguments
MODE=${1:-development}
PORT=${2:-5000}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Check Python version
print_info "Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -Po '(?<=Python )\d+\.\d+')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then 
    print_status "Python version $python_version is sufficient"
else
    print_error "Python version $python_version is too old. Need at least $required_version"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_info "Creating virtual environment..."
    python3 -m venv venv
    print_status "Virtual environment created"
else
    print_status "Virtual environment exists"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate

# Install/upgrade pip
print_info "Upgrading pip..."
pip install --upgrade pip --quiet

# Install basic requirements (without unavailable packages)
print_info "Installing core dependencies..."
pip install --quiet \
    requests \
    beautifulsoup4 \
    flask \
    jinja2 \
    python-dateutil \
    lxml

print_status "Core dependencies installed"

# Create necessary directories
mkdir -p logs
mkdir -p data
mkdir -p config

# Create a simple configuration file
cat > config/shoghi.json <<EOF
{
    "platform_name": "Shoghi",
    "version": "1.0.0-fixed",
    "mode": "$MODE",
    "port": $PORT,
    "database": "data/shoghi_grants.db",
    "log_level": "INFO"
}
EOF
print_status "Configuration created"

# Function to start the platform
start_platform() {
    case $MODE in
        development)
            print_info "Starting in DEVELOPMENT mode (interactive)..."
            python3 shoghi_fixed.py
            ;;
            
        production)
            print_info "Starting in PRODUCTION mode..."
            
            # Create a simple Flask API server
            cat > app.py <<'EOF'
#!/usr/bin/env python3
from flask import Flask, request, jsonify
from shoghi_fixed import ShoghiPlatform
import logging

app = Flask(__name__)
platform = ShoghiPlatform()

logging.basicConfig(level=logging.INFO)

@app.route('/')
def index():
    return jsonify({
        'service': 'Shoghi Platform',
        'version': '1.0.0-fixed',
        'status': 'operational'
    })

@app.route('/api/process', methods=['POST'])
def process():
    data = request.get_json()
    command = data.get('command', '')
    result = platform.process_request(command)
    return jsonify(result)

@app.route('/api/status')
def status():
    return jsonify(platform.get_status())

@app.route('/api/grants/search', methods=['POST'])
def search_grants():
    data = request.get_json()
    query = data.get('query', '')
    result = platform.find_grants(query)
    return jsonify(result)

@app.route('/api/grants/apply', methods=['POST'])
def apply_grant():
    data = request.get_json()
    grant_id = data.get('grant_id', '')
    result = platform.generate_applications(f"generate application for {grant_id}")
    return jsonify(result)

@app.route('/health')
def health():
    return 'OK', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=$PORT, debug=False)
EOF
            
            print_status "Flask API server created"
            print_info "Starting Flask server on port $PORT..."
            
            # Run Flask app in background
            nohup python3 app.py > logs/shoghi.log 2>&1 &
            echo $! > shoghi.pid
            
            print_status "Shoghi platform started in production mode"
            print_info "API available at http://localhost:$PORT"
            print_info "Process ID saved to shoghi.pid"
            print_info "Logs available at logs/shoghi.log"
            
            # Show example API calls
            echo ""
            echo "Example API calls:"
            echo "  curl http://localhost:$PORT/api/status"
            echo "  curl -X POST http://localhost:$PORT/api/process -H 'Content-Type: application/json' -d '{\"command\":\"find grants for elder care\"}'"
            ;;
            
        docker)
            print_info "Building Docker container..."
            
            # Create a simple Dockerfile if it doesn't exist
            cat > Dockerfile <<'EOF'
FROM python:3.9-slim

WORKDIR /app

COPY requirements_minimal.txt .
RUN pip install --no-cache-dir -r requirements_minimal.txt

COPY shoghi_fixed.py .
COPY grant_coordination_fixed.py .
COPY app.py .

EXPOSE 5000

CMD ["python3", "app.py"]
EOF
            
            # Create minimal requirements
            cat > requirements_minimal.txt <<EOF
requests
beautifulsoup4
flask
python-dateutil
lxml
EOF
            
            # Build Docker image
            docker build -t shoghi:latest .
            print_status "Docker image built"
            
            # Run container
            docker run -d -p $PORT:5000 --name shoghi-platform shoghi:latest
            print_status "Docker container started"
            print_info "Platform available at http://localhost:$PORT"
            ;;
            
        test)
            print_info "Running platform tests..."
            python3 test_fixed.py
            ;;
            
        *)
            print_error "Unknown mode: $MODE"
            echo "Usage: $0 [development|production|docker|test] [port]"
            exit 1
            ;;
    esac
}

# Function to stop the platform
stop_platform() {
    if [ -f "shoghi.pid" ]; then
        PID=$(cat shoghi.pid)
        if kill -0 $PID 2>/dev/null; then
            print_info "Stopping Shoghi platform (PID: $PID)..."
            kill $PID
            rm shoghi.pid
            print_status "Platform stopped"
        else
            print_error "Process $PID not found"
            rm shoghi.pid
        fi
    else
        print_error "No PID file found"
    fi
}

# Check if we're stopping
if [ "$MODE" = "stop" ]; then
    stop_platform
    exit 0
fi

# Start the platform
start_platform

if [ "$MODE" != "development" ] && [ "$MODE" != "test" ]; then
    echo ""
    echo "=============================="
    echo "🌺 Shoghi Platform Deployed Successfully!"
    echo "Mode: $MODE"
    echo "Port: $PORT"
    echo ""
    echo "To stop: $0 stop"
    echo "=============================="
fi
