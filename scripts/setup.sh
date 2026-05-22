#!/usr/bin/env bash
set -euo pipefail

echo "========================================="
echo "  Support Agent - Setup Script"
echo "========================================="

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
if (( $(echo "$PYTHON_VERSION < 3.11" | bc -l) )); then
    echo "Error: Python 3.11+ required. Found: $PYTHON_VERSION"
    exit 1
fi
echo "✓ Python $PYTHON_VERSION"

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi
echo "✓ Virtual environment ready"

# Activate and install
source .venv/bin/activate
echo "Installing dependencies..."
pip install -e ".[dev]" --quiet
echo "✓ Dependencies installed"

# Setup config
if [ ! -f "config/config.yaml" ]; then
    echo "Creating config from template..."
    cp config/config.example.yaml config/config.yaml
    echo "→ Edit config/config.yaml with your settings"
fi
echo "✓ Configuration ready"

# Setup .env
if [ ! -f ".env" ]; then
    echo "Creating .env from template..."
    cp .env.example .env
    echo "→ Edit .env with your API keys"
fi
echo "✓ Environment ready"

# Run tests
echo "Running tests..."
python -m pytest tests/ -v --tb=short
echo "✓ Tests passed"

echo ""
echo "========================================="
echo "  Setup complete!"
echo ""
echo "  Next steps:"
echo "  1. Edit .env with your MiMo API key"
echo "  2. Edit config/config.yaml"
echo "  3. Run: python -m support_agent --help"
echo "========================================="
