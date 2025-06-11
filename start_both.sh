#!/bin/bash

# Start both frontend and backend services
echo "🚀 Starting Vetting Intelligence Search Hub..."

# Function to handle cleanup
cleanup() {
    echo "🛑 Shutting down services..."
    jobs -p | xargs -r kill
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Activate virtual environment and start backend
echo "📡 Starting backend on port 8000..."
(cd backend && source ../venv/bin/activate && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload) &

# Wait a moment for backend to start
sleep 3

# Start frontend
echo "🎨 Starting frontend on port 3000..."
(cd frontend && npm run dev) &

echo "✅ Services started!"
echo "   - Backend: http://127.0.0.1:8000"
echo "   - Frontend: http://127.0.0.1:3000"
echo ""
echo "Press Ctrl+C to stop both services"

# Wait for all background jobs
wait 