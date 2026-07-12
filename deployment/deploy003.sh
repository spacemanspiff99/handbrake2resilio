#!/usr/bin/env bash
# =============================================================================
# deploy003.sh — remote production deploy over SSH (current stack)
# Supersedes deploy002.sh, which targeted the removed "simple stack"
# (docker-compose.simple.yml, root-level config.py/auth.py/job_queue.py,
# frontend on a port that no longer applies — none of which exist anymore).
#
# Run from the PROJECT ROOT on a machine with SSH access to production:
#   bash deployment/deploy003.sh
#
# DO NOT run without explicit user go-ahead — this rebuilds production.
# =============================================================================
set -euo pipefail

PRODUCTION_HOST="akun@192.168.10.18"
PROJECT_NAME="h2r"                       # actual container prefix: h2r-*
DEPLOY_DIR="h2r-deploy"   # relative to remote $HOME
COMPOSE_FILE="deployment/docker-compose.yml"
PACKAGE="h2r-deploy.tar.gz"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; BLUE='\033[0;34m'; NC='\033[0m'
status()  { echo -e "${GREEN}✅ $1${NC}"; }
warn()    { echo -e "${YELLOW}⚠️  $1${NC}"; }
fail()    { echo -e "${RED}❌ $1${NC}"; exit 1; }

echo -e "${BLUE}🚀 handbrake2resilio production deploy (deploy003)${NC}"
echo "=========================================================="

# ── Step 0: sanity ───────────────────────────────────────────────────────────
[ -f "$COMPOSE_FILE" ] || fail "$COMPOSE_FILE not found. Run from project root."

status "Checking production disk space (rules: alert >80%, fail >90%)..."
DISK_PCT=$(ssh $PRODUCTION_HOST "df --output=pcent / | tail -1 | tr -dc '0-9'") || fail "Cannot reach production host ${PRODUCTION_HOST}"
echo "   production / is at ${DISK_PCT}% used"
[ "$DISK_PCT" -lt 90 ] || fail "Production disk >90% used — clean up before deploying."
[ "$DISK_PCT" -lt 80 ] || warn "Production disk >80% used."

# ── Step 1: package current stack ────────────────────────────────────────────
# Compose build contexts are the repo root; ship every tree the builds need.
status "Creating deployment package..."
tar -czf "$PACKAGE" \
    --exclude='node_modules' \
    --exclude='.git' \
    --exclude='ui-frontend/tests' \
    deployment/docker-compose.yml \
    deployment/Dockerfile.api \
    deployment/Dockerfile.handbrake \
    deployment/nginx.conf \
    deployment/requirements.simple.txt \
    api-gateway/ \
    handbrake-service/ \
    shared/ \
    ui-frontend/ \
    .env.example

# ── Step 2: clean project containers/images on production (project-scoped) ──
# Scope strictly to this compose project (label), never by port or name substring —
# a shared prod box may run other services on adjacent ports.
COMPOSE_LABEL="com.docker.compose.project=deployment"
status "Stopping and removing this project's containers on production..."
ssh $PRODUCTION_HOST "docker ps -aq --filter 'label=${COMPOSE_LABEL}' | xargs -r docker stop 2>/dev/null || true"
ssh $PRODUCTION_HOST "docker ps -aq --filter 'label=${COMPOSE_LABEL}' | xargs -r docker rm 2>/dev/null || true"
ssh $PRODUCTION_HOST "docker images -q --filter 'label=${COMPOSE_LABEL}' | xargs -r docker rmi --force 2>/dev/null || true"

# ── Step 3: upload and build ─────────────────────────────────────────────────
status "Uploading package..."
ssh $PRODUCTION_HOST "mkdir -p $DEPLOY_DIR"
scp "$PACKAGE" $PRODUCTION_HOST:$DEPLOY_DIR/
rm -f "$PACKAGE"

ssh $PRODUCTION_HOST bash -s <<EOF
    set -euo pipefail
    cd $DEPLOY_DIR
    tar -xzf $PACKAGE && rm $PACKAGE

    # Compose v2 reads .env from the compose file's directory (deployment/)
    if [ ! -f deployment/.env ]; then
        echo "Creating deployment/.env from .env.example..."
        cp .env.example deployment/.env
        sed -i "s|^JWT_SECRET_KEY=.*|JWT_SECRET_KEY=\$(openssl rand -base64 32)|" deployment/.env
        sed -i "s|^MEDIA_INPUT_PATH=.*|MEDIA_INPUT_PATH=\$HOME/media/input|"  deployment/.env
        sed -i "s|^MEDIA_OUTPUT_PATH=.*|MEDIA_OUTPUT_PATH=\$HOME/media/output|" deployment/.env
    fi
    mkdir -p ~/media/input ~/media/output
    # HandBrake container runs as uid 999 and must write the output dir.
    # Prefer chown 999 + 775 (needs passwordless sudo); fall back to 777.
    if sudo -n chown 999:\$(id -gn) ~/media/output 2>/dev/null; then
        chmod 775 ~/media/output
    else
        echo "WARN: passwordless sudo unavailable — falling back to chmod 777 on ~/media/output"
        chmod 777 ~/media/output
    fi

    echo "Building (full clean rebuild, no cache)..."
    docker compose -f deployment/docker-compose.yml build --no-cache
    echo "Starting stack..."
    docker compose -f deployment/docker-compose.yml up -d
EOF

# ── Step 4: verify ───────────────────────────────────────────────────────────
status "Waiting for containers to become healthy..."
for i in $(seq 1 24); do
    sleep 10
    HEALTHY=$(ssh $PRODUCTION_HOST "cd $DEPLOY_DIR && docker compose -f deployment/docker-compose.yml ps | grep -c '(healthy)' || true") || HEALTHY=0
    HEALTHY=${HEALTHY:-0}
    [ "$HEALTHY" -ge 3 ] && break
done
ssh $PRODUCTION_HOST "cd $DEPLOY_DIR && docker compose -f deployment/docker-compose.yml ps"

ssh $PRODUCTION_HOST "curl -sf http://localhost:8080/health >/dev/null" && status "API Gateway healthy"        || fail "API Gateway health check failed"
ssh $PRODUCTION_HOST "curl -sf http://localhost:8081/health >/dev/null" && status "HandBrake service healthy"  || fail "HandBrake health check failed"
ssh $PRODUCTION_HOST "curl -sf http://localhost:7474 >/dev/null"        && status "Frontend responding (7474)" || fail "Frontend check failed"

# Rules: verify the running artifact is fresh (container creation vs code date)
ssh $PRODUCTION_HOST "docker ps --filter name=${PROJECT_NAME}- --format '{{.Names}}\t{{.CreatedAt}}'"

status "🎉 Deployment complete"
echo -e "${BLUE}Endpoints:${NC}  UI http://192.168.10.18:7474  |  API :8080  |  HandBrake :8081"
echo "Post-deploy: log in (admin/admin123 — change it), convert a real test video via the UI,"
echo "and run the Playwright smoke suite from a dev machine with BASE_URL=http://192.168.10.18:7474."
