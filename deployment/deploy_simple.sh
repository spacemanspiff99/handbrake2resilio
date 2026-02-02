#!/bin/bash

# HandBrake2Resilio Simple Microservices Deployment Script
# Deploys the simplified microservices architecture with SQLite storage

set -e

# Configuration
PRODUCTION_HOST="akun@192.168.10.18"
PROJECT_NAME="handbrake2resilio"
DEPLOY_DIR="~/hb2r-simple-v2"
PROJECT_PORTS="8080 8081 3000"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

echo -e "${BLUE}🚀 HandBrake2Resilio Simple Microservices Deployment${NC}"
echo "=========================================================="

# Step 1: Prepare local environment
print_status "Preparing local environment..."

# Check if we're in the right directory
if [ ! -f "deployment/docker-compose.simple.yml" ]; then
    print_error "deployment/docker-compose.simple.yml not found. Please run from project root."
    exit 1
fi

# Create deployment package
print_status "Creating deployment package..."
tar -czf handbrake2resilio-simple.tar.gz \
    --exclude='node_modules' \
    --exclude='.git' \
    deployment/docker-compose.simple.yml \
    Dockerfile.api \
    Dockerfile.handbrake \
    api-gateway/ \
    handbrake-service/ \
    config.py \
    auth.py \
    job_queue.py \
    deployment/requirements.simple.txt \
    ui-frontend/

# Step 2: Deploy to production server
print_status "Deploying to production server..."

echo "🧹 CLEANUP: Stopping project containers..."
ssh ${PRODUCTION_HOST} "docker ps -a --filter \"name=${PROJECT_NAME}\" --format '{{.ID}}' | xargs -r docker stop 2>/dev/null || true"

echo "🗑️ CLEANUP: Removing project containers..."
ssh ${PRODUCTION_HOST} "docker ps -a --filter \"name=${PROJECT_NAME}\" --format '{{.ID}}' | xargs -r docker rm 2>/dev/null || true"

echo "🔥 CLEANUP: Removing project images..."
ssh ${PRODUCTION_HOST} "docker images --filter \"reference=${PROJECT_NAME}*\" --format '{{.ID}}' | xargs -r docker rmi --force 2>/dev/null || true"

echo "🧽 CLEANUP: Cleaning Docker system..."
ssh ${PRODUCTION_HOST} "docker system prune -f"

echo "⚔️ CLEANUP: Killing lingering processes and containers on ports..."
for port in $PROJECT_PORTS; do
    # Find containers using the port and stop them
    ssh ${PRODUCTION_HOST} "docker ps -q --filter \"publish=\$port\" | xargs -r docker stop" 2>/dev/null || true
    ssh ${PRODUCTION_HOST} "docker ps -aq --filter \"publish=\$port\" | xargs -r docker rm" 2>/dev/null || true
    # Kill any other processes
    ssh ${PRODUCTION_HOST} "fuser -k \$port/tcp 2>/dev/null || true"
done

# Copy files to production server
ssh $PRODUCTION_HOST "mkdir -p $DEPLOY_DIR"
scp handbrake2resilio-simple.tar.gz $PRODUCTION_HOST:$DEPLOY_DIR/

# Extract and setup on production server
ssh $PRODUCTION_HOST << EOF
    cd $DEPLOY_DIR
    
    echo "Extracting deployment package..."
    tar -xzf handbrake2resilio-simple.tar.gz
    rm handbrake2resilio-simple.tar.gz
    
    echo "Creating necessary directories and setting permissions..."
    mkdir -p deployment/logs deployment/data
    chmod 777 deployment/logs deployment/data
    
    # Also create them in the root just in case, but deployment/ is where compose looks
    mkdir -p logs data
    chmod 777 logs data
    
    echo "Setting environment variables..."
    if [ ! -f .env ]; then
        export JWT_SECRET_KEY="\$(openssl rand -hex 32)"
        echo "JWT_SECRET_KEY=\$JWT_SECRET_KEY" > .env
    fi
    
    echo "Building microservices..."
    docker compose -f deployment/docker-compose.simple.yml build --no-cache
    
    echo "Starting microservices..."
    docker compose -f deployment/docker-compose.simple.yml up -d
    
    echo "Waiting for services to start..."
    sleep 20
    
    echo "Checking service health..."
    
    # Check API Gateway
    if curl -s -f http://localhost:8080/health >/dev/null; then
        echo "✅ API Gateway is healthy"
    else
        echo "❌ API Gateway health check failed"
        docker compose -f deployment/docker-compose.simple.yml logs api-gateway
    fi
    
    # Check HandBrake Service
    if curl -s -f http://localhost:8081/health >/dev/null; then
        echo "✅ HandBrake Service is healthy"
    else
        echo "❌ HandBrake Service health check failed"
        docker compose -f deployment/docker-compose.simple.yml logs handbrake-service
    fi
    
    echo "Running containers:"
    docker ps --filter "name=${PROJECT_NAME}"
EOF

# Step 3: Verify deployment
print_status "Verifying deployment..."

# Test API Gateway
if ssh $PRODUCTION_HOST "curl -s http://localhost:8080/health" | grep -q "healthy"; then
    print_status "API Gateway verification successful"
else
    print_error "API Gateway verification failed"
fi

# Test HandBrake Service
if ssh $PRODUCTION_HOST "curl -s http://localhost:8081/health" | grep -q "healthy"; then
    print_status "HandBrake Service verification successful"
else
    print_error "HandBrake Service verification failed"
fi

# Test Frontend
if ssh $PRODUCTION_HOST "curl -s http://localhost:3000" | grep -q "React"; then
    print_status "Frontend verification successful"
else
    print_error "Frontend verification failed"
fi

print_status "🎉 Simple microservices deployment completed successfully!"
echo ""
echo -e "${BLUE}Service Endpoints:${NC}"
echo "API Gateway: http://192.168.10.18:8080"
echo "HandBrake Service: http://192.168.10.18:8081"
echo "Frontend: http://192.168.10.18:3000"
echo ""
echo -e "${BLUE}Database:${NC}"
echo "SQLite database: ~/handbrake2resilio-simple/data/handbrake2resilio.db"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "1. Test authentication: http://192.168.10.18:8080/api/auth/login"
echo "2. Test job creation: http://192.168.10.18:8080/api/jobs/add"
echo "3. Monitor logs: ssh $PRODUCTION_HOST 'docker compose -f $DEPLOY_DIR/docker-compose.simple.yml logs -f'"
echo "4. Check database: ssh $PRODUCTION_HOST 'sqlite3 $DEPLOY_DIR/data/handbrake2resilio.db \"SELECT * FROM jobs;\"'" 