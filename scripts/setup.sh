#!/bin/bash

# Setup script for Trading Signal Analyzer
# This script initializes the project for first-time use

echo "?? Trading Signal Analyzer - Setup Script"
echo "========================================"
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "Found Python $python_version"

# Check Node version
echo "Checking Node.js version..."
node_version=$(node --version 2>&1)
echo "Found Node.js $node_version"

echo ""
echo "Setting up Backend..."
echo "--------------------"

# Backend setup
cd backend

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create .env file
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
fi

# Initialize database
echo "Initializing database..."
python -c "from database import init_db; init_db()"

# Create directories
mkdir -p data/cache data/reports logs

echo "? Backend setup complete!"
echo ""

# Frontend setup
cd ../frontend

echo "Setting up Frontend..."
echo "--------------------"

# Install dependencies
echo "Installing Node.js dependencies..."
npm install

# Create .env file
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
fi

echo "? Frontend setup complete!"
echo ""

cd ..

echo "?? Setup Complete!"
echo "================="
echo ""
echo "To start the application:"
echo ""
echo "Option 1 - Using Docker:"
echo "  docker-compose up"
echo ""
echo "Option 2 - Manual (requires 2 terminals):"
echo "  Terminal 1: cd backend && source venv/bin/activate && python app.py"
echo "  Terminal 2: cd frontend && npm start"
echo ""
echo "Then open http://localhost:3000 in your browser"
echo ""
