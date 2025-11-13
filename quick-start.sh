#!/bin/bash

# Shoghi Platform - One-Click Quick Start Script

set -e

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Banner
echo -e "${BLUE}"
cat << "EOF"
    ____  __  ______  ____________  ____
   / ___/ / / / / __ \/ ____/ __ \/  _/
   \__ \ / /_/ / / / / / __/ / / // /
  ___/ // __  / /_/ / /_/ / /_/ // /
 /____//_/ /_/\____/\____/_____/___/

 Voice-First Community Coordination Platform
EOF
echo -e "${NC}"

echo -e "${BLUE}🌺 SHOGHI PLATFORM - QUICK START${NC}"
echo "======================================"
echo ""

# Check prerequisites
check_prereq() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}❌ $1 is not installed${NC}"
        echo "Please install $1 first:"
        echo "  $2"
        exit 1
    fi
    echo -e "${GREEN}✓${NC} $1 found"
}

echo "Checking prerequisites..."
check_prereq "docker" "https://docs.docker.com/get-docker/"
check_prereq "docker-compose" "https://docs.docker.com/compose/install/"

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker daemon is not running${NC}"
    echo "Please start Docker first"
    exit 1
fi
echo -e "${GREEN}✓${NC} Docker daemon running"

echo ""
echo -e "${BLUE}Starting Shoghi Platform...${NC}"
echo ""

# Build and start
if [ "$1" == "--rebuild" ]; then
    echo "Building from scratch..."
    docker-compose down
    docker-compose build --no-cache
else
    echo "Building image (cached)..."
    docker-compose build
fi

echo ""
echo "Starting services..."
docker-compose up -d

echo ""
echo "Waiting for services to be ready..."
for i in {1..30}; do
    if docker-compose exec -T shoghi curl -f http://localhost:5000/ &> /dev/null; then
        break
    fi
    echo -n "."
    sleep 1
done
echo ""

# Check if successful
if docker-compose ps | grep -q "Up"; then
    echo ""
    echo -e "${GREEN}======================================"
    echo "🌺 SHOGHI PLATFORM IS READY!"
    echo -e "======================================${NC}"
    echo ""
    echo -e "${YELLOW}🌐 Web UI:${NC} http://localhost:5000"
    echo ""
    echo -e "${YELLOW}📋 Useful Commands:${NC}"
    echo "  • View logs:     docker-compose logs -f"
    echo "  • Stop:          docker-compose down"
    echo "  • Restart:       docker-compose restart"
    echo "  • Run tests:     docker-compose exec shoghi pytest -v"
    echo "  • Shell access:  docker-compose exec shoghi bash"
    echo ""
    echo -e "${YELLOW}📚 Full Documentation:${NC} See DOCKER_README.md"
    echo ""
    echo -e "${YELLOW}🔧 Using Makefile:${NC}"
    echo "  • make up        - Start services"
    echo "  • make down      - Stop services"
    echo "  • make logs      - View logs"
    echo "  • make test      - Run tests"
    echo "  • make help      - See all commands"
    echo ""

    # Try to open browser
    if command -v xdg-open &> /dev/null; then
        echo "Opening browser..."
        xdg-open http://localhost:5000 &
    elif command -v open &> /dev/null; then
        echo "Opening browser..."
        open http://localhost:5000 &
    else
        echo "Open http://localhost:5000 in your browser"
    fi

    echo ""
    echo -e "${GREEN}✨ Enjoy using Shoghi! ✨${NC}"
    echo ""
else
    echo -e "${RED}❌ Failed to start services${NC}"
    echo "Check logs with: docker-compose logs"
    exit 1
fi
