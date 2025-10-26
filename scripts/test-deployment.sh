#!/bin/bash
# Test deployment script

set -e

echo "🧪 Testing deployment..."

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
API_URL="${API_URL:-http://localhost:8000}"
WS_URL="${WS_URL:-ws://localhost:8765}"

# Test health endpoint
echo "📋 Testing health endpoint..."
response=$(curl -s -o /dev/null -w "%{http_code}" $API_URL/health)
if [ $response -eq 200 ]; then
    echo -e "${GREEN}✓${NC} Health check passed"
else
    echo -e "${RED}✗${NC} Health check failed (HTTP $response)"
    exit 1
fi

# Test root endpoint
echo "📋 Testing root endpoint..."
response=$(curl -s -o /dev/null -w "%{http_code}" $API_URL/)
if [ $response -eq 200 ]; then
    echo -e "${GREEN}✓${NC} Root endpoint passed"
else
    echo -e "${RED}✗${NC} Root endpoint failed (HTTP $response)"
    exit 1
fi

# Test API docs
echo "📋 Testing API documentation..."
response=$(curl -s -o /dev/null -w "%{http_code}" $API_URL/docs)
if [ $response -eq 200 ]; then
    echo -e "${GREEN}✓${NC} API docs available"
else
    echo -e "${RED}✗${NC} API docs failed (HTTP $response)"
    exit 1
fi

# Test metrics endpoint
echo "📋 Testing metrics endpoint..."
response=$(curl -s -o /dev/null -w "%{http_code}" $API_URL/metrics)
if [ $response -eq 200 ]; then
    echo -e "${GREEN}✓${NC} Metrics endpoint passed"
else
    echo -e "${RED}✗${NC} Metrics endpoint failed (HTTP $response)"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ All deployment tests passed!${NC}"
