#!/bin/bash
echo "Cleaning up Vessels architecture..."

# Remove the confusing fork files
rm -f vessels_fixed.py
rm -f vessels_web_server_fixed.py
rm -f vessels_web_server_enhanced.py

echo "Cleanup complete. Run ./vessels_web_server.py to start."
