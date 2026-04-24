#!/bin/bash
# Initialize FlowOS development environment

set -e

echo "🚀 Initializing FlowOS development environment..."
echo ""

# Check Python version
echo "📦 Checking Python 3.12..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
if [[ $python_version != 3.12* ]]; then
    echo "⚠️  Warning: Python 3.12 recommended (found $python_version)"
fi

# Create virtual environment if needed
if [ ! -d venv ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Setup environment
echo "⚙️  Setting up environment..."
if [ ! -f .env ]; then
    echo "   Creating .env from .env.example"
    cp .env.example .env
fi

# Initialize alembic (if not already done)
if [ ! -d alembic ]; then
    echo "⚙️  Initializing Alembic..."
    alembic init alembic
fi

# Copy updated alembic.ini if different
if [ -f alembic.ini ]; then
    echo "✓ alembic.ini exists"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. docker-compose up"
echo "  2. alembic upgrade head"
echo "  3. python verify_build.py"
echo "  4. Visit http://localhost:8000/docs"
