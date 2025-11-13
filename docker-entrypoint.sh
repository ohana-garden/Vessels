#!/bin/bash
set -e

echo "🌺 SHOGHI PLATFORM - Docker Container Initialization"
echo "======================================================"

# Function to display colored output
info() {
    echo -e "\033[1;34m[INFO]\033[0m $1"
}

success() {
    echo -e "\033[1;32m[SUCCESS]\033[0m $1"
}

error() {
    echo -e "\033[1;31m[ERROR]\033[0m $1"
}

# Initialize directories
info "Setting up directories..."
mkdir -p /app/logs /app/data
chmod 755 /app/logs /app/data

# Check if database exists, create if not
if [ ! -f "/app/shoghi_grants.db" ]; then
    info "Initializing database..."
    touch /app/shoghi_grants.db
    chmod 644 /app/shoghi_grants.db
fi

# Run any database migrations or setup if needed
if [ -f "/app/setup_database.py" ]; then
    info "Running database setup..."
    python3 /app/setup_database.py || true
fi

# Display system information
info "Python version: $(python3 --version)"
info "Working directory: $(pwd)"
info "Available memory: $(free -h | grep Mem | awk '{print $7}')"

# Check dependencies
info "Verifying dependencies..."
python3 -c "
import sys
required = ['flask', 'flask_cors', 'aiohttp', 'requests', 'websockets', 'numpy', 'pandas']
missing = []
for pkg in required:
    try:
        __import__(pkg)
    except ImportError:
        missing.append(pkg)
if missing:
    print('Missing packages:', ', '.join(missing))
    sys.exit(1)
print('All required packages installed')
"

if [ $? -eq 0 ]; then
    success "All dependencies verified"
else
    error "Missing dependencies detected"
    exit 1
fi

# Run tests to verify everything is working
if [ "$RUN_TESTS" = "true" ]; then
    info "Running test suite..."
    pytest test_bmad_loader.py test_adaptive_tools.py test_universal_connector.py \
           test_menu_builder.py test_dynamic_agent_factory.py test_community_memory.py \
           -v --tb=short || true
fi

# Display startup banner
echo ""
echo "======================================================"
echo "🌺 SHOGHI PLATFORM READY"
echo "======================================================"
echo ""
echo "📍 Container Information:"
echo "   • Hostname: $(hostname)"
echo "   • IP: $(hostname -i 2>/dev/null || echo 'N/A')"
echo "   • Working Dir: /app"
echo ""
echo "🌐 Endpoints:"
echo "   • Web UI: http://localhost:5000"
echo "   • API: http://localhost:5001 (if enabled)"
echo ""
echo "📁 Directories:"
echo "   • Application: /app"
echo "   • Logs: /app/logs"
echo "   • Data: /app/data"
echo "   • BMAD: /app/.bmad"
echo ""
echo "🚀 Starting application..."
echo "======================================================"
echo ""

# Execute the main command
exec "$@"
