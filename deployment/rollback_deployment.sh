#!/bin/bash
# Emergency Rollback Script for HandBrake2Resilio
# Quickly reverts to last known working state

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVER="akun@192.168.10.18"

echo -e "${RED}🚨 EMERGENCY ROLLBACK INITIATED${NC}"
echo -e "${YELLOW}This will revert to the simple static frontend that was working before${NC}"

# Ask for confirmation
read -p "Are you sure you want to rollback? This will stop current containers. (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}Rollback cancelled.${NC}"
    exit 1
fi

echo -e "\n${YELLOW}🔄 Step 1: Stopping current containers...${NC}"
ssh $SERVER "docker stop handbrake2resilio-api-gateway handbrake2resilio-frontend 2>/dev/null || true"
ssh $SERVER "docker rm handbrake2resilio-api-gateway handbrake2resilio-frontend 2>/dev/null || true"

echo -e "\n${YELLOW}🔄 Step 2: Starting API Gateway with last known working version...${NC}"
ssh $SERVER "docker run -d --name handbrake2resilio-api-gateway \
    -p 8080:8080 \
    -v /home/akun/logs:/app/logs \
    -v /home/akun/data:/app/data \
    -e FLASK_ENV=production \
    -e HOST=0.0.0.0 \
    -e PORT=8080 \
    --restart unless-stopped \
    handbrake2resilio-api-gateway:latest 2>/dev/null || echo 'Using existing API image'"

echo -e "\n${YELLOW}🔄 Step 3: Creating emergency static frontend...${NC}"

# Create a simple emergency frontend
ssh $SERVER 'cat > /tmp/emergency_index.html << EOF
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HandBrake2Resilio - Emergency Mode</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f4f4f4; color: #333; }
        .container { max-width: 800px; margin: auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .alert { background-color: #fff3cd; border: 1px solid #ffeaa7; color: #856404; padding: 10px; border-radius: 4px; margin-bottom: 20px; }
        .status { margin-top: 20px; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
        .btn { background-color: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; margin: 5px; }
        .btn:hover { background-color: #0056b3; }
        .form-group { margin-bottom: 15px; }
        .form-control { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚨 HandBrake2Resilio - Emergency Mode</h1>
        
        <div class="alert">
            <strong>Notice:</strong> The application is running in emergency mode with basic functionality.
        </div>

        <div id="status" class="status">
            <h3>System Status</h3>
            <p>Loading...</p>
        </div>

        <div class="tab-section">
            <h3>Tab Management</h3>
            <div class="form-group">
                <input type="text" id="tabName" class="form-control" placeholder="Tab Name">
            </div>
            <div class="form-group">
                <input type="text" id="tabDestination" class="form-control" placeholder="Destination Path">
            </div>
            <div class="form-group">
                <select id="tabType" class="form-control">
                    <option value="tv">TV Shows</option>
                    <option value="movie">Movies</option>
                </select>
            </div>
            <button class="btn" onclick="createTab()">Create Tab</button>
            <button class="btn" onclick="loadTabs()">Refresh Tabs</button>
        </div>

        <div id="tabs" class="status">
            <h3>Current Tabs</h3>
            <div id="tabsList"></div>
        </div>
    </div>

    <script>
        const API_URL = "http://192.168.10.18:8080";

        async function loadStatus() {
            try {
                const response = await fetch(API_URL + "/health");
                const data = await response.json();
                document.getElementById("status").innerHTML = 
                    "<h3>System Status</h3><p>✅ API Gateway: Connected</p><pre>" + 
                    JSON.stringify(data, null, 2) + "</pre>";
            } catch (error) {
                document.getElementById("status").innerHTML = 
                    "<h3>System Status</h3><p>❌ API Gateway: Disconnected</p><p>Error: " + error.message + "</p>";
            }
        }

        async function loadTabs() {
            try {
                const response = await fetch(API_URL + "/api/tabs");
                const data = await response.json();
                const tabsList = document.getElementById("tabsList");
                
                if (data.success && data.tabs) {
                    tabsList.innerHTML = data.tabs.map(tab => 
                        "<div style=\"margin: 10px 0; padding: 10px; border: 1px solid #ddd; border-radius: 4px;\">" +
                        "<strong>" + tab.name + "</strong> (" + tab.source_type + ")<br>" +
                        "<small>" + tab.destination + "</small>" +
                        "</div>"
                    ).join("");
                } else {
                    tabsList.innerHTML = "<p>No tabs found or API error</p>";
                }
            } catch (error) {
                document.getElementById("tabsList").innerHTML = "<p>Error loading tabs: " + error.message + "</p>";
            }
        }

        async function createTab() {
            const name = document.getElementById("tabName").value;
            const destination = document.getElementById("tabDestination").value;
            const source_type = document.getElementById("tabType").value;

            if (!name || !destination) {
                alert("Please fill in all fields");
                return;
            }

            try {
                const response = await fetch(API_URL + "/api/tabs", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({ name, destination, source_type })
                });

                const data = await response.json();
                if (data.success) {
                    alert("Tab created successfully!");
                    document.getElementById("tabName").value = "";
                    document.getElementById("tabDestination").value = "";
                    loadTabs();
                } else {
                    alert("Error creating tab: " + (data.error || "Unknown error"));
                }
            } catch (error) {
                alert("Error creating tab: " + error.message);
            }
        }

        // Load initial data
        loadStatus();
        loadTabs();
        
        // Refresh every 30 seconds
        setInterval(loadStatus, 30000);
    </script>
</body>
</html>
EOF'

echo -e "\n${YELLOW}🔄 Step 4: Starting emergency frontend...${NC}"
ssh $SERVER "docker run -d --name handbrake2resilio-frontend \
    -p 3000:80 \
    -v /tmp/emergency_index.html:/usr/share/nginx/html/index.html:ro \
    --restart unless-stopped \
    nginx:alpine"

echo -e "\n${YELLOW}⏳ Step 5: Waiting for services...${NC}"
sleep 5

echo -e "\n${YELLOW}✅ Step 6: Verifying rollback...${NC}"

# Check API
API_STATUS=$(ssh $SERVER "curl -s -o /dev/null -w '%{http_code}' http://localhost:8080/health")
if [ "$API_STATUS" = "200" ]; then
    echo -e "${GREEN}✅ API Gateway: HEALTHY${NC}"
else
    echo -e "${RED}❌ API Gateway: UNHEALTHY (HTTP $API_STATUS)${NC}"
fi

# Check Frontend
FRONTEND_STATUS=$(ssh $SERVER "curl -s -o /dev/null -w '%{http_code}' http://localhost:3000")
if [ "$FRONTEND_STATUS" = "200" ]; then
    echo -e "${GREEN}✅ Emergency Frontend: HEALTHY${NC}"
else
    echo -e "${RED}❌ Emergency Frontend: UNHEALTHY (HTTP $FRONTEND_STATUS)${NC}"
fi

echo -e "\n${BLUE}📊 ROLLBACK SUMMARY${NC}"
echo -e "${BLUE}==================${NC}"

if [ "$API_STATUS" = "200" ] && [ "$FRONTEND_STATUS" = "200" ]; then
    echo -e "${GREEN}🎉 ROLLBACK SUCCESSFUL!${NC}"
    echo -e "${GREEN}Emergency mode is active with basic functionality.${NC}"
    echo -e "\n${BLUE}🌐 Access URLs:${NC}"
    echo -e "Emergency Frontend: ${GREEN}http://192.168.10.18:3000${NC}"
    echo -e "API Gateway:       ${GREEN}http://192.168.10.18:8080${NC}"
    echo -e "\n${YELLOW}Next Steps:${NC}"
    echo -e "1. Investigate what caused the original deployment to fail"
    echo -e "2. Fix the issues in your code"
    echo -e "3. Run a clean deployment again with: ./deploy_clean.sh"
    echo -e "4. The emergency frontend provides basic tab management functionality"
else
    echo -e "${RED}❌ ROLLBACK FAILED${NC}"
    echo -e "${RED}Manual intervention required.${NC}"
    echo -e "\n${YELLOW}Manual Rollback Commands:${NC}"
    echo -e "ssh $SERVER 'docker ps -a'"
    echo -e "ssh $SERVER 'docker logs handbrake2resilio-api-gateway'"
    echo -e "ssh $SERVER 'docker logs handbrake2resilio-frontend'"
fi