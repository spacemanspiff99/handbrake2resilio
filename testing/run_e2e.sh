#!/usr/bin/env bash
# Run E2E integration tests against the full Docker stack.
# Usage: ./testing/run_e2e.sh [--no-build] [--down-after]
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$REPO_ROOT/deployment/docker-compose.yml"
NO_BUILD=false
DOWN_AFTER=false

for arg in "$@"; do
  case $arg in
    --no-build) NO_BUILD=true ;;
    --down-after) DOWN_AFTER=true ;;
  esac
done

echo "=== handbrake2resilio E2E Test Runner ==="
echo "Repo root: $REPO_ROOT"

# Check .env exists
if [ ! -f "$REPO_ROOT/deployment/.env" ]; then
  echo "WARNING: deployment/.env not found — copying from .env.example"
  cp "$REPO_ROOT/deployment/.env.example" "$REPO_ROOT/deployment/.env"
fi

echo ""
echo "=== Starting Docker stack ==="
if [ "$NO_BUILD" = true ]; then
  docker compose -f "$COMPOSE_FILE" up -d
else
  docker compose -f "$COMPOSE_FILE" up -d --build
fi

echo ""
echo "=== Waiting for services to be healthy (up to 60s) ==="
HEALTHY=false
for i in $(seq 1 30); do
  if curl -sf http://localhost:8080/health > /dev/null 2>&1; then
    echo "✓ API gateway healthy after ${i}x2s"
    HEALTHY=true
    break
  fi
  sleep 2
done

if [ "$HEALTHY" = false ]; then
  echo "ERROR: API gateway not healthy after 60s"
  docker compose -f "$COMPOSE_FILE" ps
  docker compose -f "$COMPOSE_FILE" logs --tail=20
  exit 1
fi

# Also wait for handbrake service
for i in $(seq 1 15); do
  if curl -sf http://localhost:8081/health > /dev/null 2>&1; then
    echo "✓ HandBrake service healthy"
    break
  fi
  sleep 2
done

echo ""
echo "=== Service status ==="
docker compose -f "$COMPOSE_FILE" ps

echo ""
echo "=== Running E2E integration tests ==="
cd "$REPO_ROOT"
VENV_PYTHON="$REPO_ROOT/.venv/bin/python"
if [ -f "$VENV_PYTHON" ]; then
  PYTHON="$VENV_PYTHON"
else
  PYTHON="python3"
fi

$PYTHON -m pytest testing/test_e2e_integration.py -v -m e2e --tb=short

EXIT_CODE=$?

if [ "$DOWN_AFTER" = true ]; then
  echo ""
  echo "=== Stopping Docker stack ==="
  docker compose -f "$COMPOSE_FILE" down
fi

echo ""
if [ $EXIT_CODE -eq 0 ]; then
  echo "✓ E2E tests PASSED"
else
  echo "✗ E2E tests FAILED (exit code: $EXIT_CODE)"
fi

exit $EXIT_CODE
