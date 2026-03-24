#!/usr/bin/env bash
# =============================================================================
# deploy001.sh — HandBrake2Resilio local Docker Compose deployment
# Run from the PROJECT ROOT: bash deployment/deploy001.sh
# =============================================================================
set -euo pipefail

COMPOSE_FILE="deployment/docker-compose.yml"
ENV_FILE=".env"
COMPOSE_CMD="docker compose -f $COMPOSE_FILE --env-file $ENV_FILE"
CONTAINERS=("h2r-api-gateway" "h2r-handbrake" "h2r-frontend")
HEALTH_TIMEOUT=120  # seconds to wait for all containers healthy

# ── Colours ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
info()  { echo -e "${BLUE}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
fail()  { echo -e "${RED}[FAIL]${NC}  $*"; exit 1; }

echo ""
echo "════════════════════════════════════════════════════════════"
echo "  HandBrake2Resilio — Deploy Script"
echo "  $(date)"
echo "════════════════════════════════════════════════════════════"
echo ""

# ── 1. Pre-flight checks ─────────────────────────────────────────────────────
info "Step 1/6: Pre-flight checks"

# Must run from project root
[[ -f "$COMPOSE_FILE" ]] || fail "Run from project root — $COMPOSE_FILE not found"

# .env must exist
if [[ ! -f "$ENV_FILE" ]]; then
    warn ".env not found — copying from .env.example"
    cp deployment/.env.example .env
    fail "Edit .env before deploying: set JWT_SECRET_KEY (openssl rand -base64 32) and media paths"
fi

# JWT_SECRET_KEY must not be the placeholder
JWT_KEY=$(grep '^JWT_SECRET_KEY=' .env | cut -d= -f2- | xargs)
if [[ -z "$JWT_KEY" || "$JWT_KEY" == "change-me-to-a-random-string" ]]; then
    fail "Set a real JWT_SECRET_KEY in .env before deploying\n  Generate one: openssl rand -base64 32"
fi
ok ".env present and JWT_SECRET_KEY is set"

# Disk space check (fail if > 90%, warn if > 80%)
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | tr -d '%')
if [[ "$DISK_USAGE" -gt 90 ]]; then
    fail "Disk usage is ${DISK_USAGE}% — clean up before deploying (threshold: 90%)"
elif [[ "$DISK_USAGE" -gt 80 ]]; then
    warn "Disk usage is ${DISK_USAGE}% — consider cleaning up (threshold: 80%)"
else
    ok "Disk usage: ${DISK_USAGE}%"
fi

# Docker available
docker info &>/dev/null || fail "Docker is not running"
ok "Docker is running"

# ── 2. Stop and remove existing containers ──────────────────────────────────
info "Step 2/6: Stopping existing containers"

$COMPOSE_CMD down --remove-orphans 2>/dev/null || true
ok "Previous containers stopped"

# ── 3. Prune build cache to avoid stale layers ──────────────────────────────
info "Step 3/6: Pruning Docker build cache"
docker builder prune -f --filter type=exec.cachemount &>/dev/null || true
ok "Build cache pruned"

# ── 4. Build and start ───────────────────────────────────────────────────────
info "Step 4/6: Building and starting containers (this takes 5-10 min on first run)"
echo ""
# Ensure data/logs dirs are writable by container user (uid=999)
mkdir -p data logs
chmod 777 data logs

$COMPOSE_CMD up --build -d
echo ""
ok "Containers started"

# ── 5. Wait for health checks ────────────────────────────────────────────────
info "Step 5/6: Waiting for health checks (timeout: ${HEALTH_TIMEOUT}s)"

ELAPSED=0
ALL_HEALTHY=false

while [[ $ELAPSED -lt $HEALTH_TIMEOUT ]]; do
    HEALTHY_COUNT=0
    for CONTAINER in "${CONTAINERS[@]}"; do
        STATUS=$(docker inspect --format='{{.State.Health.Status}}' "$CONTAINER" 2>/dev/null || echo "missing")
        if [[ "$STATUS" == "healthy" ]]; then
            ((HEALTHY_COUNT++))
        fi
    done

    if [[ $HEALTHY_COUNT -eq ${#CONTAINERS[@]} ]]; then
        ALL_HEALTHY=true
        break
    fi

    echo -ne "\r  Healthy: ${HEALTHY_COUNT}/${#CONTAINERS[@]} ... ${ELAPSED}s elapsed"
    sleep 5
    ((ELAPSED+=5))
done

echo ""

if [[ "$ALL_HEALTHY" == "true" ]]; then
    ok "All ${#CONTAINERS[@]} containers healthy after ${ELAPSED}s"
else
    warn "Health timeout reached after ${HEALTH_TIMEOUT}s — showing container status:"
    $COMPOSE_CMD ps
    echo ""
    warn "Showing last 30 lines of logs per service:"
    $COMPOSE_CMD logs --tail=30
    fail "Not all containers reached healthy state — see logs above"
fi

# ── 6. Smoke test ────────────────────────────────────────────────────────────
info "Step 6/6: Smoke testing endpoints"

# Detect host IP for display
HOST_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "localhost")
API_PORT=$(grep '^API_PORT=' .env | cut -d= -f2- | xargs || echo "8080")
FRONTEND_PORT=$(grep '^FRONTEND_PORT=' .env | cut -d= -f2- | xargs || echo "7474")

# Test API health
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${API_PORT}/health" --max-time 5 || echo "000")
if [[ "$HTTP_CODE" == "200" ]]; then
    ok "API health: http://localhost:${API_PORT}/health → 200"
else
    warn "API health returned HTTP ${HTTP_CODE} — may still be starting"
fi

# Test frontend
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${FRONTEND_PORT}/" --max-time 5 || echo "000")
if [[ "$HTTP_CODE" == "200" ]]; then
    ok "Frontend: http://localhost:${FRONTEND_PORT}/ → 200"
else
    warn "Frontend returned HTTP ${HTTP_CODE}"
fi

# ── Summary ──────────────────────────────────────────────────────────────────
echo ""
echo "════════════════════════════════════════════════════════════"
echo -e "  ${GREEN}Deployment complete!${NC}"
echo ""
echo "  Frontend:    http://${HOST_IP}:${FRONTEND_PORT}"
echo "  API Gateway: http://${HOST_IP}:${API_PORT}"
echo "  Login:       admin / admin123  (change after first login)"
echo ""
echo "  Live logs:   docker compose -f deployment/docker-compose.yml logs -f"
echo "  Status:      docker compose -f deployment/docker-compose.yml ps"
echo "  Stop:        docker compose -f deployment/docker-compose.yml down"
echo "════════════════════════════════════════════════════════════"
echo ""
