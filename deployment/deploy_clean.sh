#!/bin/bash
# Clean Deployment Script for HandBrake2Resilio
# Follows senior DevOps practices - complete clean rebuild every time

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVER="akun@192.168.10.18"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
TARBALL_NAME="handbrake2resilio-deploy-${TIMESTAMP}.tar.gz"

echo -e "${BLUE}🚀 Starting Clean Deployment Process${NC}"
echo -e "${BLUE}Timestamp: ${TIMESTAMP}${NC}"
echo -e "${BLUE}Target Server: ${SERVER}${NC}"

# Step 1: Stop and remove all containers
echo -e "\n${YELLOW}🧹 STEP 1: Stopping all containers...${NC}"
ssh $SERVER "docker stop \$(docker ps -aq) 2>/dev/null || true" || echo "No containers to stop"

echo -e "${YELLOW}🗑️ STEP 2: Removing all containers...${NC}"
ssh $SERVER "docker rm \$(docker ps -aq) 2>/dev/null || true" || echo "No containers to remove"

# Step 2: Remove all Docker images (force clean rebuild)
echo -e "\n${YELLOW}🔥 STEP 3: Removing all images...${NC}"
ssh $SERVER "docker rmi \$(docker images -q) --force 2>/dev/null || true" || echo "No images to remove"

# Step 3: Clean build cache and volumes
echo -e "\n${YELLOW}🧽 STEP 4: Cleaning Docker system...${NC}"
ssh $SERVER "docker system prune -af --volumes" || echo "Docker system clean completed"
ssh $SERVER "docker builder prune -af" || echo "Docker builder clean completed"

# Step 4: Remove all build files from home directory
echo -e "\n${YELLOW}📁 STEP 5: Cleaning home directory...${NC}"
ssh $SERVER "cd /home/akun && rm -rf handbrake* *.tar.gz *.zip docker-compose* Dockerfile* requirements* deploy* test* verify* standalone* 2>/dev/null || true"

# Step 5: Kill any lingering processes on target ports
echo -e "\n${YELLOW}⚔️ STEP 6: Killing lingering processes...${NC}"
ssh $SERVER "fuser -k 8080/tcp 3000/tcp 8081/tcp 2>/dev/null || true"
ssh $SERVER "pkill -f 'python.*8080' 2>/dev/null || true"
ssh $SERVER "pkill -f 'handbrake' 2>/dev/null || true"
ssh $SERVER "pkill -f 'nginx.*handbrake' 2>/dev/null || true"

# Step 6: Create clean tarball of current code
echo -e "\n${YELLOW}📦 STEP 7: Creating deployment package...${NC}"
tar -czf $TARBALL_NAME \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.DS_Store' \
    --exclude='logs' \
    --exclude='data' \
    handbrake2resilio/

echo -e "${GREEN}✅ Created tarball: ${TARBALL_NAME}${NC}"

# Step 7: Upload new code
echo -e "\n${YELLOW}📤 STEP 8: Uploading deployment package...${NC}"
scp $TARBALL_NAME $SERVER:~/

# Step 8: Extract and prepare code on server
echo -e "\n${YELLOW}📂 STEP 9: Extracting code on server...${NC}"
ssh $SERVER "cd /home/akun && tar -xzf $TARBALL_NAME"

# Step 9: Build API Gateway image
echo -e "\n${YELLOW}🏗️ STEP 10: Building API Gateway image...${NC}"
ssh $SERVER "cd /home/akun/handbrake2resilio/api-gateway && docker build --no-cache -t handbrake2resilio-api-gateway -f ../deployment/Dockerfile.api . || echo 'API Gateway build failed, trying alternate approach'"

# Alternative API Gateway build if main approach fails
ssh $SERVER "cd /home/akun/handbrake2resilio && docker build --no-cache -t handbrake2resilio-api-gateway -f deployment/Dockerfile.api . || echo 'API Gateway build failed'"

# Step 10: Build Frontend image
echo -e "\n${YELLOW}🎨 STEP 11: Building Frontend image...${NC}"
ssh $SERVER "cd /home/akun/handbrake2resilio/ui-frontend && docker build --no-cache -t handbrake2resilio-frontend ."

# Step 11: Start API Gateway
echo -e "\n${YELLOW}🚀 STEP 12: Starting API Gateway...${NC}"
ssh $SERVER "docker run -d --name handbrake2resilio-api-gateway \
    -p 8080:8080 \
    -v /home/akun/logs:/app/logs \
    -v /home/akun/data:/app/data \
    -e FLASK_ENV=production \
    -e HOST=0.0.0.0 \
    -e PORT=8080 \
    --restart unless-stopped \
    handbrake2resilio-api-gateway"

# Step 12: Start Frontend
echo -e "\n${YELLOW}🎨 STEP 13: Starting Frontend...${NC}"
ssh $SERVER "docker run -d --name handbrake2resilio-frontend \
    -p 3000:80 \
    -e REACT_APP_API_URL=http://192.168.10.18:8080 \
    -e REACT_APP_WS_URL=ws://192.168.10.18:8080 \
    -e REACT_APP_SOCKET_PATH=/socket.io/ \
    --restart unless-stopped \
    handbrake2resilio-frontend"

# Step 13: Wait for services to start
echo -e "\n${YELLOW}⏳ STEP 14: Waiting for services to start...${NC}"
sleep 10

# Step 14: Verify deployment
echo -e "\n${YELLOW}✅ STEP 15: Verifying deployment...${NC}"

# Check containers are running
echo -e "\n${BLUE}Container Status:${NC}"
ssh $SERVER "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"

# Check API Gateway health
echo -e "\n${BLUE}API Gateway Health Check:${NC}"
API_STATUS=$(ssh $SERVER "curl -s -o /dev/null -w '%{http_code}' http://localhost:8080/health")
if [ "$API_STATUS" = "200" ]; then
    echo -e "${GREEN}✅ API Gateway: HEALTHY (HTTP $API_STATUS)${NC}"
else
    echo -e "${RED}❌ API Gateway: UNHEALTHY (HTTP $API_STATUS)${NC}"
fi

# Check Frontend
echo -e "\n${BLUE}Frontend Health Check:${NC}"
FRONTEND_STATUS=$(ssh $SERVER "curl -s -o /dev/null -w '%{http_code}' http://localhost:3000")
if [ "$FRONTEND_STATUS" = "200" ]; then
    echo -e "${GREEN}✅ Frontend: HEALTHY (HTTP $FRONTEND_STATUS)${NC}"
else
    echo -e "${RED}❌ Frontend: UNHEALTHY (HTTP $FRONTEND_STATUS)${NC}"
fi

# Check tab creation functionality
echo -e "\n${BLUE}Tab API Test:${NC}"
TAB_STATUS=$(ssh $SERVER "curl -s -o /dev/null -w '%{http_code}' http://localhost:8080/api/tabs")
if [ "$TAB_STATUS" = "200" ]; then
    echo -e "${GREEN}✅ Tab API: WORKING (HTTP $TAB_STATUS)${NC}"
else
    echo -e "${RED}❌ Tab API: FAILED (HTTP $TAB_STATUS)${NC}"
fi

# Step 15: Show container logs if there are issues
if [ "$API_STATUS" != "200" ] || [ "$FRONTEND_STATUS" != "200" ]; then
    echo -e "\n${RED}⚠️ Issues detected, showing container logs:${NC}"
    
    if [ "$API_STATUS" != "200" ]; then
        echo -e "\n${YELLOW}API Gateway Logs (last 20 lines):${NC}"
        ssh $SERVER "docker logs --tail 20 handbrake2resilio-api-gateway"
    fi
    
    if [ "$FRONTEND_STATUS" != "200" ]; then
        echo -e "\n${YELLOW}Frontend Logs (last 20 lines):${NC}"
        ssh $SERVER "docker logs --tail 20 handbrake2resilio-frontend"
    fi
fi

# Clean up local tarball
echo -e "\n${YELLOW}🧹 STEP 16: Cleaning up local files...${NC}"
rm -f $TARBALL_NAME

# Final summary
echo -e "\n${BLUE}📊 DEPLOYMENT SUMMARY${NC}"
echo -e "${BLUE}===================${NC}"
echo -e "Timestamp: ${TIMESTAMP}"
echo -e "API Gateway: http://192.168.10.18:8080"
echo -e "Frontend UI: http://192.168.10.18:3000"
echo -e "Tab API: http://192.168.10.18:8080/api/tabs"

if [ "$API_STATUS" = "200" ] && [ "$FRONTEND_STATUS" = "200" ] && [ "$TAB_STATUS" = "200" ]; then
    echo -e "\n${GREEN}🎉 DEPLOYMENT SUCCESSFUL!${NC}"
    echo -e "${GREEN}All services are healthy and functional.${NC}"
    exit 0
else
    echo -e "\n${RED}❌ DEPLOYMENT ISSUES DETECTED${NC}"
    echo -e "${RED}Please check the logs above for troubleshooting.${NC}"
    exit 1
fi