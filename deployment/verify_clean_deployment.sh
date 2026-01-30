#!/bin/bash
# Comprehensive deployment verification script
# Verifies that the clean deployment was successful

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVER="akun@192.168.10.18"

echo -e "${BLUE}🔍 Starting Deployment Verification${NC}"
echo -e "${BLUE}Target Server: ${SERVER}${NC}"

# Test results array
declare -a TESTS=()
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run a test and record result
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_result="$3"
    
    echo -e "\n${YELLOW}Testing: ${test_name}${NC}"
    
    if eval "$test_command"; then
        if [ -n "$expected_result" ]; then
            local result=$(eval "$test_command")
            if [ "$result" = "$expected_result" ]; then
                echo -e "${GREEN}✅ PASS: ${test_name}${NC}"
                TESTS+=("PASS: $test_name")
                ((TESTS_PASSED++))
            else
                echo -e "${RED}❌ FAIL: ${test_name} (got: $result, expected: $expected_result)${NC}"
                TESTS+=("FAIL: $test_name")
                ((TESTS_FAILED++))
            fi
        else
            echo -e "${GREEN}✅ PASS: ${test_name}${NC}"
            TESTS+=("PASS: $test_name")
            ((TESTS_PASSED++))
        fi
    else
        echo -e "${RED}❌ FAIL: ${test_name}${NC}"
        TESTS+=("FAIL: $test_name")
        ((TESTS_FAILED++))
    fi
}

# Test 1: Check containers are running
run_test "API Gateway Container Running" \
    'ssh $SERVER "docker ps --filter name=handbrake2resilio-api-gateway --format \"{{.Status}}\" | grep -q \"Up\""'

run_test "Frontend Container Running" \
    'ssh $SERVER "docker ps --filter name=handbrake2resilio-frontend --format \"{{.Status}}\" | grep -q \"Up\""'

# Test 2: Check HTTP endpoints
run_test "API Gateway Health Endpoint" \
    'ssh $SERVER "curl -s -o /dev/null -w \"%{http_code}\" http://localhost:8080/health"' \
    "200"

run_test "Frontend Root Endpoint" \
    'ssh $SERVER "curl -s -o /dev/null -w \"%{http_code}\" http://localhost:3000"' \
    "200"

run_test "Tabs API Endpoint" \
    'ssh $SERVER "curl -s -o /dev/null -w \"%{http_code}\" http://localhost:8080/api/tabs"' \
    "200"

run_test "System Status API Endpoint" \
    'ssh $SERVER "curl -s -o /dev/null -w \"%{http_code}\" http://localhost:8080/api/system/status"' \
    "200"

# Test 3: Check API responses contain expected data
run_test "API Health Response Contains Status" \
    'ssh $SERVER "curl -s http://localhost:8080/health | grep -q \"status\""'

run_test "Tabs API Returns JSON" \
    'ssh $SERVER "curl -s http://localhost:8080/api/tabs | grep -q \"{\""'

# Test 4: Test tab creation functionality
run_test "Tab Creation Works" \
    'ssh $SERVER "curl -s -X POST -H \"Content-Type: application/json\" -d \"{\\\"name\\\":\\\"test-tab\\\",\\\"destination\\\":\\\"/tmp/test\\\",\\\"source_type\\\":\\\"movie\\\"}\" http://localhost:8080/api/tabs | grep -q \"success\""'

# Test 5: Check WebSocket endpoint (if accessible)
run_test "WebSocket Endpoint Accessible" \
    'ssh $SERVER "curl -s -o /dev/null -w \"%{http_code}\" http://localhost:8080/socket.io/"' \
    "200"

# Test 6: Check Docker image freshness (no old images should exist)
run_test "No Old Docker Images" \
    'ssh $SERVER "[ $(docker images -q | wc -l) -eq 2 ]"'  # Should only have 2 images: api and frontend

# Test 7: Check port accessibility from external
run_test "External API Access" \
    'curl -s -o /dev/null -w "%{http_code}" http://192.168.10.18:8080/health' \
    "200"

run_test "External Frontend Access" \
    'curl -s -o /dev/null -w "%{http_code}" http://192.168.10.18:3000' \
    "200"

# Test 8: Check container resource usage
echo -e "\n${YELLOW}Container Resource Usage:${NC}"
ssh $SERVER "docker stats --no-stream --format 'table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}'"

# Test 9: Check container logs for errors
echo -e "\n${YELLOW}Checking for errors in container logs:${NC}"

API_ERRORS=$(ssh $SERVER "docker logs --tail 50 handbrake2resilio-api-gateway 2>&1 | grep -i error | wc -l")
FRONTEND_ERRORS=$(ssh $SERVER "docker logs --tail 50 handbrake2resilio-frontend 2>&1 | grep -i error | wc -l")

if [ "$API_ERRORS" -eq 0 ]; then
    echo -e "${GREEN}✅ No errors in API Gateway logs${NC}"
    TESTS+=("PASS: No API Gateway errors")
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ Found $API_ERRORS errors in API Gateway logs${NC}"
    TESTS+=("FAIL: API Gateway has $API_ERRORS errors")
    ((TESTS_FAILED++))
fi

if [ "$FRONTEND_ERRORS" -eq 0 ]; then
    echo -e "${GREEN}✅ No errors in Frontend logs${NC}"
    TESTS+=("PASS: No Frontend errors")
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ Found $FRONTEND_ERRORS errors in Frontend logs${NC}"
    TESTS+=("FAIL: Frontend has $FRONTEND_ERRORS errors")
    ((TESTS_FAILED++))
fi

# Test 10: Verify clean deployment (no old files)
echo -e "\n${YELLOW}Checking for clean deployment (no leftover files):${NC}"

OLD_FILES=$(ssh $SERVER "ls /home/akun/*.tar.gz /home/akun/deploy_* /home/akun/test_* /home/akun/verify_* /home/akun/standalone_* 2>/dev/null | wc -l")

if [ "$OLD_FILES" -eq 0 ]; then
    echo -e "${GREEN}✅ Clean deployment - no leftover files${NC}"
    TESTS+=("PASS: Clean deployment")
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠️ Found $OLD_FILES leftover files (may be expected)${NC}"
    TESTS+=("WARN: $OLD_FILES leftover files")
fi

# Show final summary
echo -e "\n${BLUE}📊 VERIFICATION SUMMARY${NC}"
echo -e "${BLUE}=====================${NC}"

for test in "${TESTS[@]}"; do
    if [[ $test == PASS* ]]; then
        echo -e "${GREEN}$test${NC}"
    elif [[ $test == FAIL* ]]; then
        echo -e "${RED}$test${NC}"
    else
        echo -e "${YELLOW}$test${NC}"
    fi
done

echo -e "\n${BLUE}Results: ${GREEN}$TESTS_PASSED passed${NC}, ${RED}$TESTS_FAILED failed${NC}"

# Overall status
if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 ALL TESTS PASSED - DEPLOYMENT VERIFIED!${NC}"
    echo -e "${GREEN}Your HandBrake2Resilio application is fully functional.${NC}"
    
    echo -e "\n${BLUE}🌐 Access URLs:${NC}"
    echo -e "Frontend: ${GREEN}http://192.168.10.18:3000${NC}"
    echo -e "API:      ${GREEN}http://192.168.10.18:8080${NC}"
    echo -e "Tabs API: ${GREEN}http://192.168.10.18:8080/api/tabs${NC}"
    echo -e "Health:   ${GREEN}http://192.168.10.18:8080/health${NC}"
    
    exit 0
else
    echo -e "\n${RED}❌ $TESTS_FAILED TESTS FAILED - DEPLOYMENT NEEDS ATTENTION${NC}"
    echo -e "${RED}Please review the failed tests and troubleshoot accordingly.${NC}"
    
    echo -e "\n${YELLOW}Troubleshooting Commands:${NC}"
    echo -e "View containers: ${BLUE}ssh $SERVER 'docker ps -a'${NC}"
    echo -e "API logs:        ${BLUE}ssh $SERVER 'docker logs handbrake2resilio-api-gateway'${NC}"
    echo -e "Frontend logs:   ${BLUE}ssh $SERVER 'docker logs handbrake2resilio-frontend'${NC}"
    
    exit 1
fi