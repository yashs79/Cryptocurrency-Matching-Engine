#!/bin/bash
# Setup script for local development

set -e

echo "🚀 Setting up Matching Engine development environment..."

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create virtual environment
echo "🔧 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please update .env with your configuration"
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs data

# Run tests
echo "🧪 Running tests..."
pytest tests/ -v || true

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Update .env file with your configuration"
echo "  3. Start services: make docker-up"
echo "  4. Run development server: make dev"
echo ""
echo "Happy coding! 🎉"
