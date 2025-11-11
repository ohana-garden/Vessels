#!/bin/bash

echo "🌺 SHOGHI - Voice-First Community Coordination Platform"
echo "======================================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Check and install dependencies
echo "📦 Checking dependencies..."

REQUIRED_PACKAGES="flask flask-cors aiohttp beautifulsoup4 requests websockets"

for package in $REQUIRED_PACKAGES; do
    if ! python3 -c "import ${package//-/_}" 2>/dev/null; then
        echo "Installing $package..."
        pip install $package --break-system-packages --quiet
    fi
done

# Create logs directory
mkdir -p logs

# Function to check if port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Kill any existing instances
echo "🔄 Cleaning up any existing instances..."
pkill -f "shoghi_web_server.py" 2>/dev/null
sleep 1

# Start the web server
echo "🚀 Starting Shoghi Web Server..."
nohup python3 shoghi_web_server.py > logs/web_server.log 2>&1 &
WEB_PID=$!

# Wait for server to start
echo "⏳ Waiting for server to initialize..."
for i in {1..30}; do
    if check_port 5000; then
        echo "✅ Server started successfully!"
        break
    fi
    sleep 1
done

if ! check_port 5000; then
    echo "❌ Server failed to start. Check logs/web_server.log"
    exit 1
fi

echo ""
echo "======================================================"
echo "🌺 SHOGHI IS READY!"
echo "======================================================"
echo ""
echo "🌐 Open in your browser: http://localhost:5000"
echo ""
echo "🎤 Voice Commands (or use keyboard shortcuts):"
echo "   • Say: 'I need help finding grants'"
echo "   • Say: 'Show me elder care protocol'"
echo "   • Say: 'What food is available?'"
echo "   • Say: 'Show delivery routes'"
echo "   • Say: 'When can volunteers help?'"
echo ""
echo "⌨️  Keyboard Shortcuts (for testing):"
echo "   • Press '1': Grant search"
echo "   • Press '2': Elder care protocol"
echo "   • Press '3': Food availability"
echo "   • Press '4': Delivery routes"
echo "   • Press '5': Schedule view"
echo "   • Press 'h': Help menu"
echo ""
echo "📝 Logs:"
echo "   • Web Server: logs/web_server.log"
echo ""
echo "🛑 To stop: Press Ctrl+C or run ./stop_shoghi.sh"
echo ""
echo "======================================================"

# Create stop script
cat > stop_shoghi.sh << 'EOF'
#!/bin/bash
echo "Stopping Shoghi..."
pkill -f "shoghi_web_server.py"
echo "✅ Shoghi stopped"
EOF
chmod +x stop_shoghi.sh

# Keep script running
trap "echo ''; echo 'Stopping Shoghi...'; kill $WEB_PID 2>/dev/null; exit 0" INT TERM

# Monitor the server
while true; do
    if ! kill -0 $WEB_PID 2>/dev/null; then
        echo "❌ Server stopped unexpectedly. Check logs/web_server.log"
        exit 1
    fi
    sleep 5
done
