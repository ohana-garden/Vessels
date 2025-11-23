#!/bin/bash
set -e

echo "=================================================="
echo "  VESSELS - Projects + Graphiti Architecture"
echo "=================================================="
echo ""

# Function to handle shutdown
shutdown() {
    echo ""
    echo "Shutting down..."

    # Kill Vessels app if running
    if [ ! -z "$VESSELS_PID" ]; then
        echo "Stopping Vessels application..."
        kill -TERM "$VESSELS_PID" 2>/dev/null || true
        wait "$VESSELS_PID" 2>/dev/null || true
    fi

    # Kill Redis/FalkorDB
    if [ ! -z "$REDIS_PID" ]; then
        echo "Stopping FalkorDB..."
        kill -TERM "$REDIS_PID" 2>/dev/null || true
        wait "$REDIS_PID" 2>/dev/null || true
    fi

    echo "Shutdown complete"
    exit 0
}

# Trap signals for graceful shutdown
trap shutdown SIGTERM SIGINT SIGQUIT

# Start Redis/FalkorDB
echo "Starting FalkorDB..."
redis-server /etc/redis/redis-falkordb.conf &
REDIS_PID=$!

# Wait for Redis to be ready
echo "Waiting for FalkorDB to be ready..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if redis-cli -p 6379 ping > /dev/null 2>&1; then
        echo "✓ FalkorDB is ready!"
        break
    fi
    attempt=$((attempt + 1))
    sleep 1
done

if [ $attempt -eq $max_attempts ]; then
    echo "✗ FalkorDB failed to start"
    exit 1
fi

echo ""
echo "FalkorDB running on localhost:6379"
echo ""

# Determine what command to run
COMMAND=${1:-demo}

case "$COMMAND" in
    demo)
        echo "Running Vessels Projects Demo..."
        echo ""
        python /app/examples/projects_demo.py &
        VESSELS_PID=$!
        ;;

    web)
        echo "Starting Vessels Web Server..."
        echo "Web interface will be available at http://localhost:5000"
        echo "Access from host: http://localhost:5000"
        echo ""
        # Set DAEMON=true to keep container running
        export DAEMON=true
        python /app/vessels_web_server.py &
        VESSELS_PID=$!
        ;;

    shell)
        echo "Starting interactive shell..."
        echo "FalkorDB is available at localhost:6379"
        echo ""
        echo "Try:"
        echo "  python examples/projects_demo.py"
        echo "  redis-cli"
        echo ""
        /bin/bash
        exit 0
        ;;

    *)
        echo "Running custom command: $@"
        echo ""
        "$@" &
        VESSELS_PID=$!
        ;;
esac

# Wait for Vessels app to complete
if [ ! -z "$VESSELS_PID" ]; then
    wait "$VESSELS_PID"
    VESSELS_EXIT=$?

    echo ""
    if [ $VESSELS_EXIT -eq 0 ]; then
        echo "✓ Application completed successfully"
    else
        echo "✗ Application exited with code $VESSELS_EXIT"
    fi
fi

# Keep container running if in daemon mode
if [ "$DAEMON" = "true" ]; then
    echo ""
    echo "Running in daemon mode. Press Ctrl+C to stop."
    echo ""

    # Wait for Redis process
    wait $REDIS_PID
else
    # Graceful shutdown
    shutdown
fi
