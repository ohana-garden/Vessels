#!/bin/bash
# Start FalkorDB for Shoghi development

echo "Starting FalkorDB..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker first."
    exit 1
fi

# Start FalkorDB using Docker Compose
cd "$(dirname "$0")/.." || exit

docker-compose up -d falkordb

# Wait for FalkorDB to be healthy
echo "Waiting for FalkorDB to be ready..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if docker exec shoghi-falkordb redis-cli ping > /dev/null 2>&1; then
        echo "✓ FalkorDB is ready!"
        echo ""
        echo "FalkorDB running at: localhost:6379"
        echo ""
        echo "Test connection:"
        echo "  redis-cli PING"
        echo ""
        echo "Stop FalkorDB:"
        echo "  docker-compose down"
        echo ""
        exit 0
    fi

    attempt=$((attempt + 1))
    sleep 1
done

echo "Error: FalkorDB did not start within 30 seconds"
docker-compose logs falkordb
exit 1
