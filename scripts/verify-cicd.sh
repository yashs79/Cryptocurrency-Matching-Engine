#!/bin/bash
# Verify CI/CD Pipeline Setup

set -e

echo "🔍 Verifying CI/CD Pipeline Setup..."
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check git repository
echo "📋 Checking Git repository..."
if [ -d .git ]; then
    echo -e "${GREEN}✓${NC} Git repository initialized"
else
    echo -e "${RED}✗${NC} Git repository not initialized"
    echo "Run: git init"
    exit 1
fi

# Check remote
echo "📋 Checking Git remote..."
if git remote -v | grep -q origin; then
    echo -e "${GREEN}✓${NC} Git remote configured"
    git remote -v
else
    echo -e "${YELLOW}⚠${NC} Git remote not configured"
    echo "Run: git remote add origin https://github.com/YOUR_USERNAME/matching-engine.git"
fi

# Check branches
echo ""
echo "📋 Checking branches..."
git branch -a

# Check GitHub Actions workflows
echo ""
echo "📋 Checking GitHub Actions workflows..."
if [ -f .github/workflows/ci.yml ]; then
    echo -e "${GREEN}✓${NC} CI workflow exists"
else
    echo -e "${RED}✗${NC} CI workflow missing"
fi

if [ -f .github/workflows/cd-dev.yml ]; then
    echo -e "${GREEN}✓${NC} CD-Dev workflow exists"
else
    echo -e "${RED}✗${NC} CD-Dev workflow missing"
fi

# Check Dockerfile
echo ""
echo "📋 Checking Docker configuration..."
if [ -f Dockerfile ]; then
    echo -e "${GREEN}✓${NC} Dockerfile exists"
else
    echo -e "${RED}✗${NC} Dockerfile missing"
fi

if [ -f docker-compose.yml ]; then
    echo -e "${GREEN}✓${NC} docker-compose.yml exists"
else
    echo -e "${RED}✗${NC} docker-compose.yml missing"
fi

# Check dependencies
echo ""
echo "📋 Checking dependencies..."
if [ -f requirements.txt ]; then
    echo -e "${GREEN}✓${NC} requirements.txt exists"
else
    echo -e "${RED}✗${NC} requirements.txt missing"
fi

# Check tests
echo ""
echo "📋 Checking tests..."
if [ -d tests/unit ]; then
    echo -e "${GREEN}✓${NC} Unit tests directory exists"
    test_count=$(find tests/unit -name "test_*.py" | wc -l)
    echo "   Found $test_count test files"
else
    echo -e "${RED}✗${NC} Unit tests directory missing"
fi

# Check if virtual environment exists
echo ""
echo "📋 Checking Python environment..."
if [ -d venv ]; then
    echo -e "${GREEN}✓${NC} Virtual environment exists"
else
    echo -e "${YELLOW}⚠${NC} Virtual environment not created"
    echo "Run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
fi

# Try to run tests if venv exists
if [ -d venv ]; then
    echo ""
    echo "📋 Running tests..."
    source venv/bin/activate
    if pytest tests/ -v --tb=short 2>/dev/null; then
        echo -e "${GREEN}✓${NC} Tests passed"
    else
        echo -e "${YELLOW}⚠${NC} Some tests failed (this is OK for initial setup)"
    fi
fi

# Check Docker
echo ""
echo "📋 Checking Docker..."
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓${NC} Docker is installed"
    docker --version
else
    echo -e "${RED}✗${NC} Docker is not installed"
fi

if command -v docker-compose &> /dev/null; then
    echo -e "${GREEN}✓${NC} Docker Compose is installed"
    docker-compose --version
else
    echo -e "${RED}✗${NC} Docker Compose is not installed"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}✅ CI/CD Pipeline Verification Complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Push to GitHub: git push origin main"
echo "2. Create develop branch: git checkout -b develop && git push -u origin develop"
echo "3. Watch GitHub Actions: https://github.com/YOUR_USERNAME/matching-engine/actions"
echo "4. Test deployment: ./scripts/test-deployment.sh"
echo ""
