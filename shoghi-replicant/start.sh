#!/bin/bash

# Shoghi Replicant - One-Command Startup Script
# This script sets up and starts the entire Shoghi system

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Banner
echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║            SHOGHI REPLICANT - STARTUP SCRIPT              ║"
echo "║                                                           ║"
echo "║  AI Agent Coordination Platform with Moral Constraints   ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Function to print colored messages
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
print_info "Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    echo "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    echo "Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

# Use 'docker compose' or 'docker-compose' based on availability
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

print_success "Docker and Docker Compose are installed"

# Check if .env file exists
if [ ! -f .env ]; then
    print_warning ".env file not found. Creating from .env.example..."
    cp .env.example .env
    print_info "Please edit .env file to add your API keys and configuration"
    print_warning "Continuing with default configuration..."
    sleep 2
fi

# Parse command line arguments
MODE="${1:-start}"
PROFILE="${2:-}"

case "$MODE" in
    start)
        print_info "Starting Shoghi Replicant..."

        # Build images if needed
        print_info "Building Docker images (this may take a few minutes on first run)..."
        $DOCKER_COMPOSE build

        # Start services
        print_info "Starting services..."
        if [ -n "$PROFILE" ]; then
            $DOCKER_COMPOSE --profile "$PROFILE" up -d
        else
            $DOCKER_COMPOSE up -d
        fi

        # Wait for services to be healthy
        print_info "Waiting for services to be ready..."
        sleep 10

        # Check service health
        print_info "Checking service health..."
        $DOCKER_COMPOSE ps

        print_success "Shoghi Replicant is running!"
        echo ""
        echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║                    ACCESS INFORMATION                     ║${NC}"
        echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
        echo -e "  ${BLUE}Shoghi Web Interface:${NC}  http://localhost:5000"
        echo -e "  ${BLUE}Redis:${NC}                 localhost:6379"
        echo -e "  ${BLUE}PostgreSQL:${NC}            localhost:5432"
        echo ""
        echo -e "${YELLOW}To view logs:${NC}       ./start.sh logs"
        echo -e "${YELLOW}To stop:${NC}            ./start.sh stop"
        echo -e "${YELLOW}To restart:${NC}         ./start.sh restart"
        echo -e "${YELLOW}With debug tools:${NC}   ./start.sh start debug"
        echo ""
        ;;

    stop)
        print_info "Stopping Shoghi Replicant..."
        $DOCKER_COMPOSE down
        print_success "Shoghi Replicant stopped"
        ;;

    restart)
        print_info "Restarting Shoghi Replicant..."
        $DOCKER_COMPOSE restart
        print_success "Shoghi Replicant restarted"
        ;;

    logs)
        print_info "Showing logs (Ctrl+C to exit)..."
        $DOCKER_COMPOSE logs -f
        ;;

    status)
        print_info "Service status:"
        $DOCKER_COMPOSE ps
        ;;

    clean)
        print_warning "This will remove all containers, volumes, and data!"
        read -p "Are you sure? (yes/no): " -n 3 -r
        echo
        if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
            print_info "Cleaning up..."
            $DOCKER_COMPOSE down -v --remove-orphans
            print_success "Cleanup complete"
        else
            print_info "Cleanup cancelled"
        fi
        ;;

    shell)
        print_info "Opening shell in Shoghi container..."
        docker exec -it shoghi-replicant /bin/bash
        ;;

    rebuild)
        print_info "Rebuilding Shoghi Replicant..."
        $DOCKER_COMPOSE down
        $DOCKER_COMPOSE build --no-cache
        $DOCKER_COMPOSE up -d
        print_success "Rebuild complete"
        ;;

    *)
        echo "Shoghi Replicant - Startup Script"
        echo ""
        echo "Usage: ./start.sh [command] [profile]"
        echo ""
        echo "Commands:"
        echo "  start [profile]  - Start Shoghi (default, add 'debug' for debug tools)"
        echo "  stop             - Stop all services"
        echo "  restart          - Restart all services"
        echo "  logs             - View logs (live tail)"
        echo "  status           - Show service status"
        echo "  clean            - Remove all containers and volumes"
        echo "  shell            - Open shell in Shoghi container"
        echo "  rebuild          - Rebuild and restart from scratch"
        echo ""
        echo "Examples:"
        echo "  ./start.sh                  # Start normally"
        echo "  ./start.sh start debug      # Start with Redis Commander & pgAdmin"
        echo "  ./start.sh logs             # View logs"
        echo "  ./start.sh stop             # Stop everything"
        echo ""
        exit 1
        ;;
esac
