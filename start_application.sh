#!/bin/bash

# 🚀 Vetting Intelligence Search Hub - Complete Startup Script
# This script properly starts both backend and frontend applications

set -e  # Exit on any error

echo "🔧 Vetting Intelligence Search Hub - Starting Application..."

# Function to kill existing processes
cleanup_ports() {
    echo "🧹 Cleaning up existing processes..."
    
    # Kill any existing backend processes
    if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "  Stopping backend on port 8000..."
        lsof -Pi :8000 -sTCP:LISTEN -t | xargs kill -9 2>/dev/null || true
        sleep 2
    fi
    
    # Kill any existing frontend processes  
    if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "  Stopping frontend on port 3000..."
        lsof -Pi :3000 -sTCP:LISTEN -t | xargs kill -9 2>/dev/null || true
        sleep 2
    fi
}

# Function to check if virtual environment exists
check_venv() {
    if [ ! -d "venv" ]; then
        echo "❌ Virtual environment not found. Creating one..."
        python3 -m venv venv
        source venv/bin/activate
        echo "📦 Installing backend dependencies..."
        pip install -r backend/requirements.txt
    else
        echo "✅ Virtual environment found"
    fi
}

# Function to start backend
start_backend() {
    echo "🖥️  Starting Backend Server..."
    
    # Navigate to backend directory
    cd backend
    
    # Check if environment.env exists
    if [ ! -f "environment.env" ]; then
        echo "❌ backend/environment.env not found!"
        echo "Please create this file with the correct API keys."
        exit 1
    fi
    
    # Load environment variables
    set -a
    source environment.env
    set +a
    
    echo "✅ Environment variables loaded"
    echo "🔑 LDA_API_KEY: ${LDA_API_KEY:0:10}..."
    
    # Verify API key format
    if [[ "$LDA_API_KEY" == 065* ]]; then
        echo "✅ Correct LDA API key format detected"
    else
        echo "❌ WARNING: Incorrect LDA API key format!"
        echo "   Expected: starts with '065'"
        echo "   Current:  starts with '${LDA_API_KEY:0:3}'"
        echo "   Please check backend/environment.env file"
    fi
    
    # Activate virtual environment
    source ../venv/bin/activate
    
    # Start backend server in background
    echo "🚀 Starting FastAPI server on http://127.0.0.1:8000"
    python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload > ../backend.log 2>&1 &
    BACKEND_PID=$!
    
    echo "   Backend PID: $BACKEND_PID"
    echo "   Log file: backend.log"
    
    # Wait for backend to start
    echo "⏳ Waiting for backend to start..."
    for i in {1..30}; do
        if curl -s http://127.0.0.1:8000/health > /dev/null 2>&1; then
            echo "✅ Backend is ready!"
            break
        fi
        sleep 1
        echo -n "."
    done
    
    if ! curl -s http://127.0.0.1:8000/health > /dev/null 2>&1; then
        echo "❌ Backend failed to start. Check backend.log for errors."
        exit 1
    fi
    
    cd ..
}

# Function to start frontend
start_frontend() {
    echo "🌐 Starting Frontend Server..."
    
    cd frontend
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        echo "📦 Installing frontend dependencies..."
        npm install
    fi
    
    # Start frontend server in background
    echo "🚀 Starting Next.js server on http://localhost:3000"
    npm run dev > ../frontend.log 2>&1 &
    FRONTEND_PID=$!
    
    echo "   Frontend PID: $FRONTEND_PID"
    echo "   Log file: frontend.log"
    
    # Wait for frontend to start
    echo "⏳ Waiting for frontend to start..."
    for i in {1..30}; do
        if curl -s http://localhost:3000 > /dev/null 2>&1; then
            echo "✅ Frontend is ready!"
            break
        fi
        sleep 1
        echo -n "."
    done
    
    cd ..
}

# Function to show status
show_status() {
    echo ""
    echo "🎉 Application Started Successfully!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🌐 Frontend:  http://localhost:3000"
    echo "🖥️  Backend:   http://127.0.0.1:8000"
    echo "📚 API Docs:  http://127.0.0.1:8000/docs"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "📊 Process Information:"
    echo "   Backend PID:  $BACKEND_PID"
    echo "   Frontend PID: $FRONTEND_PID"
    echo ""
    echo "📝 Log Files:"
    echo "   Backend:  backend.log"
    echo "   Frontend: frontend.log"
    echo ""
    echo "🛑 To stop the application:"
    echo "   ./stop_application.sh"
    echo "   OR press Ctrl+C to stop this script"
    echo ""
    
    # Save PIDs for stop script
    echo "$BACKEND_PID" > .backend_pid
    echo "$FRONTEND_PID" > .frontend_pid
}

# Function to handle cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down application..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    rm -f .backend_pid .frontend_pid
    echo "✅ Application stopped"
}

# Set up signal handlers
trap cleanup EXIT INT TERM

# Main execution
echo "🏁 Starting application startup sequence..."

cleanup_ports
check_venv
start_backend
start_frontend
show_status

# Keep script running and monitor processes
echo "🔍 Monitoring application (Ctrl+C to stop)..."
while true; do
    # Check if backend is still running
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo "❌ Backend process died! Check backend.log"
        exit 1
    fi
    
    # Check if frontend is still running
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "❌ Frontend process died! Check frontend.log"
        exit 1
    fi
    
    sleep 5
done 