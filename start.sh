#!/bin/bash

echo "🚀 Starting Live UI Gemini Application..."

# Check if .env file exists in backend directory
if [ ! -f "backend/.env" ]; then
    echo "❌ Error: backend/.env file not found!"
    echo "📝 Please create backend/.env and add your GOOGLE_API_KEY"
    echo "💡 Example: cp backend/.env.example backend/.env"
    exit 1
fi

# Check if GOOGLE_API_KEY is set
if ! grep -q "GOOGLE_API_KEY=" backend/.env; then
    echo "❌ Error: GOOGLE_API_KEY not found in backend/.env"
    echo "📝 Please add your Gemini API key to backend/.env"
    exit 1
fi

echo "✅ Environment file found"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if Python is installed
if ! command_exists python3 && ! command_exists python; then
    echo "❌ Error: Python is not installed"
    echo "📥 Please install Python 3.8+ from https://python.org"
    exit 1
fi

# Check if Node.js is installed
if ! command_exists node; then
    echo "❌ Error: Node.js is not installed"
    echo "📥 Please install Node.js 18+ from https://nodejs.org"
    exit 1
fi

echo "✅ Python and Node.js are installed"

# Install Python dependencies if needed
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "📦 Activating virtual environment and installing Python dependencies..."
source venv/bin/activate
pip install -r requirements.txt

# Install Node.js dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing Node.js dependencies..."
    npm install
fi

echo "🎯 Starting services..."

# Function to cleanup background processes
cleanup() {
    echo "🛑 Stopping services..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit
}

# Set trap to cleanup on exit
trap cleanup SIGINT SIGTERM

# Start backend server in background
echo "🐍 Starting Python FastAPI backend on port 8000..."
cd backend
source ../venv/bin/activate
python run.py &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 3

# Start frontend server in background
echo "⚛️  Starting Next.js frontend on port 3000..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "🎉 Application started successfully!"
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📖 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for either process to exit
wait 