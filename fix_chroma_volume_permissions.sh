#!/usr/bin/env bash
set -euo pipefail

# Helper: Fix permissions of the chroma named volume so the container can run as UID 1000
# Usage: run this on the host where Docker runs. It will ask for sudo when required.

MOUNT="/var/lib/docker/volumes/chroma_data/_data"

echo "[chroma] Fix volume permissions helper"

if [ ! -d "$MOUNT" ]; then
  echo "Error: volume mountpoint not found: $MOUNT" >&2
  echo "Run: docker volume inspect chroma_data --format '{{.Mountpoint}}'" >&2
  exit 1
fi

echo "Stopping chroma service (if running)..."
cd "$(dirname "$0")" || true
docker compose stop chroma 2>/dev/null || docker stop chroma-test 2>/dev/null || true

echo "Changing ownership of $MOUNT to UID:GID 1000:1000 (requires sudo)"
sudo chown -R 1000:1000 "$MOUNT"

echo "Starting chroma service..."
docker compose up -d chroma 2>/dev/null || docker start chroma-test 2>/dev/null || true

echo "Done. Verify health with:"
echo "  docker ps --filter name=chroma-test --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"
echo "  docker inspect --format='{{json .State.Health}}' chroma-test"

exit 0
