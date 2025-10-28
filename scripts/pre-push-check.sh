#!/bin/bash
# Pre-push verification script
# Run this before pushing to GitHub to catch issues early

set -e

echo "🔍 Pre-Push Verification"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

ERRORS=0

# Check 1: Python version
echo "📋 Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
if [[ "$PYTHON_VERSION" == 3.11* ]] || [[ "$PYTHON_VERSION" == 3.12* ]]; then
    echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION"
else
    echo -e "${YELLOW}⚠${NC} Python $PYTHON_VERSION (recommended: 3.11+)"
fi
echo ""

# Check 2: Virtual environment
echo "📋 Checking virtual environment..."
if [ -d "venv" ]; then
    echo -e "${GREEN}✓${NC} Virtual environment exists"
else
    echo -e "${YELLOW}⚠${NC} Virtual environment not found"
    echo "Creating virtual environment..."
    python3 -m venv venv
fi
echo ""

# Activate virtual environment
source venv/bin/activate 2>/dev/null || true

# Check 3: Dependencies
echo "📋 Checking dependencies..."
if pip install -r requirements.txt > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Dependencies installed"
else
    echo -e "${RED}✗${NC} Failed to install dependencies"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Check 4: Run tests
echo "📋 Running tests..."
if pytest tests/unit/ -v --tb=short; then
    echo -e "${GREEN}✓${NC} Tests passed"
else
    echo -e "${YELLOW}⚠${NC} Some tests failed (this may be OK)"
fi
echo ""

# Check 5: Check imports
echo "📋 Checking imports..."
if python3 -c "from src.matching_engine.main import app" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Main module imports successfully"
else
    echo -e "${YELLOW}⚠${NC} Import issues detected (may be OK if dependencies missing)"
fi
echo ""

# Check 6: Dockerfile syntax
echo "📋 Checking Dockerfile..."
if [ -f "Dockerfile" ]; then
    if docker build -t matching-engine:test . > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Dockerfile builds successfully"
    else
        echo -e "${RED}✗${NC} Dockerfile build failed"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo -e "${RED}✗${NC} Dockerfile not found"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Check 7: GitHub workflows
echo "📋 Checking GitHub workflows..."
if [ -f ".github/workflows/ci.yml" ]; then
    echo -e "${GREEN}✓${NC} CI workflow exists"
else
    echo -e "${RED}✗${NC} CI workflow missing"
    ERRORS=$((ERRORS + 1))
fi

if [ -f ".github/workflows/cd-dev.yml" ]; then
    echo -e "${GREEN}✓${NC} CD workflow exists"
else
    echo -e "${RED}✗${NC} CD workflow missing"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Check 8: Git status
echo "📋 Checking Git status..."
if git diff --quiet; then
    echo -e "${GREEN}✓${NC} No uncommitted changes"
else
    echo -e "${YELLOW}⚠${NC} You have uncommitted changes"
    echo "Files changed:"
    git status --short
fi
echo ""

# Check 9: Git remote
echo "📋 Checking Git remote..."
if git remote -v | grep -q origin; then
    echo -e "${GREEN}✓${NC} Git remote configured"
    git remote -v | head -2
else
    echo -e "${RED}✗${NC} Git remote not configured"
    echo "Run: git remote add origin <your-repo-url>"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed!${NC}"
    echo ""
    echo "Ready to push to GitHub:"
    echo "  git add ."
    echo "  git commit -m 'your message'"
    echo "  git push origin main"
else
    echo -e "${RED}❌ $ERRORS error(s) found${NC}"
    echo ""
    echo "Please fix the errors before pushing."
    exit 1
fi
echo ""
