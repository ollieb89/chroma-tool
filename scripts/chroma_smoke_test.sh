#!/usr/bin/env bash
set -euo pipefail

# Simple smoke test for Chroma service used by CI or locally.
# Rebuilds the chroma image, starts the service, and checks health + heartbeat.

RETRIES=6
SLEEP=5

echo "Building image (no-cache)..."
docker compose build --no-cache chroma

echo "Starting chroma..."
docker compose up -d --force-recreate chroma

# Wait and poll health
for i in $(seq 1 "$RETRIES"); do
  echo "Check $i/$RETRIES..."
  health=$(docker inspect --format='{{json .State.Health}}' chroma-test || true)
  echo "Docker health: $health"

  # Try HTTP heartbeat
  if curl -sS http://localhost:9500/api/v2/heartbeat >/dev/null 2>&1; then
    echo "Heartbeat responded"
    exit 0
  fi

  echo "Heartbeat not responding yet, sleeping ${SLEEP}s"
  sleep "$SLEEP"
done

# If we reached here, smoke test failed
echo "Smoke test failed: heartbeat did not respond"
docker compose logs --no-color --tail 200 chroma || true
exit 2
