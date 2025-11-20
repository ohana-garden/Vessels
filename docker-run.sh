#!/bin/bash
# Run Shoghi container with common configurations

MODE=${1:-demo}

case "$MODE" in
    demo)
        echo "Running Shoghi demo..."
        docker run --rm \
            --name shoghi-demo \
            shoghi:latest demo
        ;;

    demo-persist)
        echo "Running Shoghi demo with persistent data..."
        docker run --rm \
            --name shoghi-demo \
            -v shoghi-data:/data/falkordb \
            -v shoghi-work:/app/work_dir \
            shoghi:latest demo
        ;;

    web)
        echo "Starting Shoghi web server (daemon mode)..."
        docker run -d \
            --name shoghi-web \
            -p 5000:5000 \
            -p 6379:6379 \
            -v shoghi-data:/data/falkordb \
            -v shoghi-work:/app/work_dir \
            -e DAEMON=true \
            shoghi:latest web

        echo ""
        echo "✓ Shoghi web server started"
        echo ""
        echo "  Web UI: http://localhost:5000"
        echo "  FalkorDB: localhost:6379"
        echo ""
        echo "View logs:"
        echo "  docker logs -f shoghi-web"
        echo ""
        echo "Stop server:"
        echo "  docker stop shoghi-web"
        echo "  docker rm shoghi-web"
        echo ""
        ;;

    shell)
        echo "Starting interactive shell..."
        docker run -it --rm \
            --name shoghi-shell \
            -v shoghi-data:/data/falkordb \
            -v shoghi-work:/app/work_dir \
            shoghi:latest shell
        ;;

    stop)
        echo "Stopping all Shoghi containers..."
        docker stop shoghi-web 2>/dev/null || true
        docker rm shoghi-web 2>/dev/null || true
        echo "✓ Stopped"
        ;;

    clean)
        echo "Cleaning up Shoghi containers and volumes..."
        docker stop shoghi-web 2>/dev/null || true
        docker rm shoghi-web 2>/dev/null || true
        docker volume rm shoghi-data 2>/dev/null || true
        docker volume rm shoghi-work 2>/dev/null || true
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
