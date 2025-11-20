#!/bin/bash
# Build Vessels single container

set -e

echo "Building Vessels container..."
docker build -t vessels:latest .

echo ""
echo "✓ Build complete!"
echo ""
echo "Run the container:"
echo ""
echo "  # Run demo (default)"
echo "  docker run --rm vessels:latest"
echo ""
echo "  # Run demo with persistent data"
echo "  docker run --rm -v vessels-data:/data/falkordb -v vessels-work:/app/work_dir vessels:latest"
echo ""
echo "  # Run web server"
echo "  docker run -d -p 5000:5000 -p 6379:6379 -v vessels-data:/data/falkordb vessels:latest web"
echo ""
echo "  # Interactive shell"
echo "  docker run -it --rm vessels:latest shell"
echo ""
