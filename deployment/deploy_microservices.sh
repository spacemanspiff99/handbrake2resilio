#!/bin/bash

# HandBrake2Resilio Microservices Deployment Script
# Deploys the complete microservices architecture to production

set -e

# Configuration
PRODUCTION_HOST="akun@192.168.10.18"
PROJECT_NAME="handbrake2resilio"
DEPLOY_DIR="~/handbrake2resilio-microservices"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 HandBrake2Resilio Microservices Deployment${NC}"
echo "=================================================="

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

# Step 1: Prepare local environment
print_status "Preparing local environment..."

# Check if we're in the right directory
if [ ! -f "docker-compose.microservices.yml" ]; then
    print_error "docker-compose.microservices.yml not found. Please run from project root."
    exit 1
fi

# Create deployment package
print_status "Creating deployment package..."
tar -czf handbrake2resilio-microservices.tar.gz \
    docker-compose.microservices.yml \
    Dockerfile.api \
    Dockerfile.handbrake \
    api_gateway.py \
    handbrake_service.py \
    config.py \
    auth.py \
    job_queue.py \
    requirements.microservices.txt \
    handbrake2resilio/ui-frontend/ \
    --exclude='node_modules' \
    --exclude='.git'

# Step 2: Deploy to production server
print_status "Deploying to production server..."

# Copy files to production server
ssh $PRODUCTION_HOST "mkdir -p $DEPLOY_DIR"
scp handbrake2resilio-microservices.tar.gz $PRODUCTION_HOST:$DEPLOY_DIR/

# Extract and setup on production server
ssh $PRODUCTION_HOST << 'EOF'
    cd ~/handbrake2resilio-microservices
    
    # Extract deployment package
    tar -xzf handbrake2resilio-microservices.tar.gz
    rm handbrake2resilio-microservices.tar.gz
    
    # Stop existing containers
    docker-compose -f docker-compose.microservices.yml down 2>/dev/null || true
    docker stop handbrake2resilio-api handbrake2resilio-handbrake handbrake2resilio-redis handbrake2resilio-frontend 2>/dev/null || true
    docker rm handbrake2resilio-api handbrake2resilio-handbrake handbrake2resilio-redis handbrake2resilio-frontend 2>/dev/null || true
    
    # Create necessary directories
    mkdir -p logs data
    
    # Set environment variables
    export JWT_SECRET_KEY="$(openssl rand -hex 32)"
    echo "JWT_SECRET_KEY=$JWT_SECRET_KEY" > .env
    
    # Build and start services
    print_status "Building microservices..."
    docker-compose -f docker-compose.microservices.yml build
    
    print_status "Starting microservices..."
    docker-compose -f docker-compose.microservices.yml up -d
    
    # Wait for services to start
    print_status "Waiting for services to start..."
    sleep 30
    
    # Check service health
    print_status "Checking service health..."
    
    # Check API Gateway
    if curl -f http://localhost:8080/health >/dev/null 2>&1; then
        print_status "API Gateway is healthy"
    else
        print_error "API Gateway health check failed"
    fi
    
    # Check HandBrake Service
    if curl -f http://localhost:8081/health >/dev/null 2>&1; then
        print_status "HandBrake Service is healthy"
    else
        print_error "HandBrake Service health check failed"
    fi
    
    # Check Redis
    if docker exec handbrake2resilio-redis redis-cli ping >/dev/null 2>&1; then
        print_status "Redis is healthy"
    else
        print_error "Redis health check failed"
    fi
    
    # Check Frontend
    if curl -f http://localhost:3000 >/dev/null 2>&1; then
        print_status "Frontend is healthy"
    else
        print_error "Frontend health check failed"
    fi
    
    # Show running containers
    print_status "Running containers:"
    docker ps --filter "name=handbrake2resilio"
    
    # Show service URLs
    print_status "Service URLs:"
    echo "API Gateway: http://localhost:8080"
    echo "HandBrake Service: http://localhost:8081"
    echo "Frontend: http://localhost:3000"
    echo "Redis: localhost:6379"
    
    print_status "Microservices deployment completed!"
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

print_status "🎉 Microservices deployment completed successfully!"
echo ""
echo -e "${BLUE}Service Endpoints:${NC}"
echo "API Gateway: http://192.168.10.18:8080"
echo "HandBrake Service: http://192.168.10.18:8081"
echo "Frontend: http://192.168.10.18:3000"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "1. Test authentication: http://192.168.10.18:8080/api/auth/login"
echo "2. Test job creation: http://192.168.10.18:8080/api/jobs/add"
echo "3. Monitor logs: ssh $PRODUCTION_HOST 'docker-compose -f $DEPLOY_DIR/docker-compose.microservices.yml logs -f'" 