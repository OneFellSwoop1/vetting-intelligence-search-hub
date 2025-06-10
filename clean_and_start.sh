#!/bin/bash

# 🧹 Clean Environment & Start Application
# This script ensures NO wrong API keys exist anywhere

echo "🧹 Cleaning up any incorrect API key settings..."

# Unset any existing LDA_API_KEY to start fresh
unset LDA_API_KEY

# Kill any existing processes that might have wrong API keys
echo "🛑 Stopping any existing processes..."
pkill -f uvicorn 2>/dev/null || true
pkill -f "npm run dev" 2>/dev/null || true
pkill -f "next dev" 2>/dev/null || true
sleep 2

# Set the CORRECT API key from the environment file
echo "🔑 Loading correct API keys from environment.env..."
if [ -f "backend/environment.env" ]; then
    export $(cat backend/environment.env | grep -v '^#' | grep -v '^$' | xargs)
    echo "✅ API keys loaded from environment.env"
else
    echo "❌ Error: backend/environment.env not found!"
    exit 1
fi

# Verify the API key is correct
if [[ "$LDA_API_KEY" == "065af08d580cf15c2220836fb456a5ebe504186c" ]]; then
    echo "✅ Correct LDA API key detected: ${LDA_API_KEY:0:8}..."
else
    echo "❌ API key verification failed!"
    echo "Current key: ${LDA_API_KEY:-'NOT SET'}"
    exit 1
fi

# Activate virtual environment
echo "🐍 Activating virtual environment..."
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate

# Install/update dependencies
echo "📦 Installing backend dependencies..."
cd backend
pip install -r requirements.txt > /dev/null 2>&1

# Start backend
echo "🚀 Starting backend with correct API key..."
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload &
BACKEND_PID=$!

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
sleep 5

# Test the backend is working
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend is running successfully"
else
    echo "❌ Backend failed to start"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Start frontend
echo "🎨 Starting frontend..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

# Save PIDs for cleanup
echo $BACKEND_PID > ../.backend_pid
echo $FRONTEND_PID > ../.frontend_pid

echo ""
echo "🎉 Application started successfully!"
echo "📊 Frontend: http://localhost:3000"
echo "🔧 Backend:  http://localhost:8000"
echo ""
echo "To stop: ./stop_application.sh"
echo "Logs: backend.log and frontend.log"

# Monitor the processes
wait 