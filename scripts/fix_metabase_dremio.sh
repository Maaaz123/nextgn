#!/bin/bash
# Force Metabase to use our v0.51.14 + Dremio image (not metabase:latest).
# The Dremio driver 1.5.0 only works with Metabase 0.51.x.
set -e
cd "$(dirname "$0")/.."
echo "Stopping Metabase..."
docker compose stop metabase 2>/dev/null || true
echo "Removing container..."
docker rm -f data_tools_metabase 2>/dev/null || true
echo "Building Metabase image (v0.51.14 + Dremio driver)..."
docker compose build metabase --no-cache
echo "Starting Metabase..."
docker compose up -d metabase
echo "Waiting 30s for startup..."
sleep 30
VER=$(curl -s http://localhost:3000/api/session/properties 2>/dev/null | grep -o '"tag":"[^"]*"' || echo "unable to fetch")
echo "Metabase version: $VER"
echo "Open http://localhost:3000 → Admin → Databases → Add database → Dremio should appear"
