#!/bin/bash
# TigerBeetle Cluster Initialization Script
#
# This script initializes the TigerBeetle cluster data files.
# Run this ONCE before starting the cluster for the first time.
#
# Usage: ./scripts/init-tigerbeetle.sh

set -e

CLUSTER_ID=${TIGERBEETLE_CLUSTER_ID:-0}
DATA_DIR=${TIGERBEETLE_DATA_DIR:-./data/tigerbeetle}

echo "=== TigerBeetle Cluster Initialization ==="
echo "Cluster ID: $CLUSTER_ID"
echo "Data Directory: $DATA_DIR"
echo ""

# Create data directory
mkdir -p "$DATA_DIR"

# Check if already initialized
if [ -f "$DATA_DIR/0_0.tigerbeetle" ]; then
    echo "Cluster already initialized. Delete $DATA_DIR to reinitialize."
    exit 0
fi

echo "Formatting replica data files..."

# Format each replica's data file
# 3-node cluster for fault tolerance
for replica in 0 1 2; do
    echo "  Formatting replica $replica..."
    docker run --rm -v "$DATA_DIR:/data" \
        ghcr.io/tigerbeetle/tigerbeetle:latest \
        format --cluster=$CLUSTER_ID --replica=$replica --replica-count=3 \
        /data/${CLUSTER_ID}_${replica}.tigerbeetle
done

echo ""
echo "=== Initialization Complete ==="
echo ""
echo "Data files created:"
ls -la "$DATA_DIR"/*.tigerbeetle 2>/dev/null || echo "  (files in Docker volume)"
echo ""
echo "Next steps:"
echo "  1. Start the cluster: docker-compose up -d tigerbeetle-0 tigerbeetle-1 tigerbeetle-2"
echo "  2. Verify health: docker-compose logs tigerbeetle-0"
echo "  3. Connect from Node.js: TIGERBEETLE_REPLICA_ADDRESSES=localhost:3001"
echo ""
