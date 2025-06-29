#!/bin/bash

# Live UI Gemini Backend Server Startup Script
# This script starts the FastAPI backend server with proper environment setup

set -e  # Exit on any error

echo "🚀 Starting Live UI Gemini Backend Server..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}📁 Project root: $PROJECT_ROOT${NC}"
echo -e "${BLUE}📁 Backend directory: $SCRIPT_DIR${NC}"

# Change to project root
cd "$PROJECT_ROOT"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found!${NC}"
    echo -e "${YELLOW}💡 Please create a virtual environment first:${NC}"
    echo "   python -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r backend/requirements.txt"
    exit 1
fi

# Activate virtual environment
echo -e "${YELLOW}🔄 Activating virtual environment...${NC}"
source venv/bin/activate

# Check if requirements are installed
if ! python -c "import fastapi, uvicorn" 2>/dev/null; then
    echo -e "${YELLOW}📦 Installing/updating requirements...${NC}"
    pip install -r backend/requirements.txt
fi

# Check if .env file exists
if [ ! -f "backend/.env" ]; then
    echo -e "${RED}❌ Environment file not found!${NC}"
    echo -e "${YELLOW}💡 Please create backend/.env with:${NC}"
    echo "   GOOGLE_API_KEY=your_api_key_here"
    exit 1
fi

# Check if GOOGLE_API_KEY is set
if ! grep -q "GOOGLE_API_KEY=" backend/.env || grep -q "GOOGLE_API_KEY=$" backend/.env; then
    echo -e "${RED}❌ GOOGLE_API_KEY not set in backend/.env${NC}"
    echo -e "${YELLOW}💡 Please add your Google API key to backend/.env:${NC}"
    echo "   GOOGLE_API_KEY=your_actual_api_key_here"
    exit 1
fi

# Change to backend directory
cd backend

# Kill any existing uvicorn processes
echo -e "${YELLOW}🔄 Stopping any existing server processes...${NC}"
pkill -f "uvicorn main:app" 2>/dev/null || true

# Wait a moment for processes to stop
sleep 2

# Start the server
echo -e "${GREEN}✅ Starting FastAPI server...${NC}"
echo -e "${BLUE}🌐 Server will be available at: http://localhost:8000${NC}"
echo -e "${BLUE}📊 Health check: http://localhost:8000/api/health${NC}"
echo -e "${BLUE}📖 API docs: http://localhost:8000/docs${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Start uvicorn with auto-reload
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload 