#!/bin/bash
# Build Shoghi single container

set -e

echo "Building Shoghi container..."
docker build -t shoghi:latest .

echo ""
echo "✓ Build complete!"
echo ""
echo "Run the container:"
echo ""
echo "  # Run demo (default)"
echo "  docker run --rm shoghi:latest"
echo ""
echo "  # Run demo with persistent data"
echo "  docker run --rm -v shoghi-data:/data/falkordb -v shoghi-work:/app/work_dir shoghi:latest"
echo ""
echo "  # Run web server"
echo "  docker run -d -p 5000:5000 -p 6379:6379 -v shoghi-data:/data/falkordb shoghi:latest web"
echo ""
echo "  # Interactive shell"
echo "  docker run -it --rm shoghi:latest shell"
echo ""
