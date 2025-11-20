#!/bin/bash
# Run Vessels container with common configurations

MODE=${1:-demo}

case "$MODE" in
    demo)
        echo "Running Vessels demo..."
        docker run --rm \
            --name vessels-demo \
            vessels:latest demo
        ;;

    demo-persist)
        echo "Running Vessels demo with persistent data..."
        docker run --rm \
            --name vessels-demo \
            -v vessels-data:/data/falkordb \
            -v vessels-work:/app/work_dir \
            vessels:latest demo
        ;;

    web)
        echo "Starting Vessels web server (daemon mode)..."
        docker run -d \
            --name vessels-web \
            -p 5000:5000 \
            -p 6379:6379 \
            -v vessels-data:/data/falkordb \
            -v vessels-work:/app/work_dir \
            -e DAEMON=true \
            vessels:latest web

        echo ""
        echo "✓ Vessels web server started"
        echo ""
        echo "  Web UI: http://localhost:5000"
        echo "  FalkorDB: localhost:6379"
        echo ""
        echo "View logs:"
        echo "  docker logs -f vessels-web"
        echo ""
        echo "Stop server:"
        echo "  docker stop vessels-web"
        echo "  docker rm vessels-web"
        echo ""
        ;;

    shell)
        echo "Starting interactive shell..."
        docker run -it --rm \
            --name vessels-shell \
            -v vessels-data:/data/falkordb \
            -v vessels-work:/app/work_dir \
            vessels:latest shell
        ;;

    stop)
        echo "Stopping all Vessels containers..."
        docker stop vessels-web 2>/dev/null || true
        docker rm vessels-web 2>/dev/null || true
        echo "✓ Stopped"
        ;;

    clean)
        echo "Cleaning up Vessels containers and volumes..."
        docker stop vessels-web 2>/dev/null || true
        docker rm vessels-web 2>/dev/null || true
        docker volume rm vessels-data 2>/dev/null || true
        docker volume rm vessels-work 2>/dev/null || true
        echo "✓ Cleaned up"
        ;;

    *)
        echo "Usage: $0 {demo|demo-persist|web|shell|stop|clean}"
        echo ""
        echo "Commands:"
        echo "  demo          - Run demo (ephemeral)"
        echo "  demo-persist  - Run demo with persistent data"
        echo "  web           - Start web server (daemon)"
        echo "  shell         - Interactive shell"
        echo "  stop          - Stop web server"
        echo "  clean         - Remove containers and volumes"
        exit 1
        ;;
esac
