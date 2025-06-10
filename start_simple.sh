#!/bin/bash

# 🚀 SIMPLE START - Vetting Intelligence Search Hub
echo "🚀 Starting Vetting Intelligence Search Hub..."

# Kill any existing processes
pkill -f uvicorn 2>/dev/null || true
pkill -f "npm run dev" 2>/dev/null || true

# Set correct API key from environment file
export $(cat backend/environment.env | grep -v '^#' | grep -v '^$' | xargs)
echo "✅ API Key: ${LDA_API_KEY:0:10}..."

# Activate venv and start backend
source venv/bin/activate
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload &
echo "✅ Backend starting on port 8000..."

# Start frontend  
cd ../frontend
npm run dev &
echo "✅ Frontend starting on port 3000..."

echo ""
echo "🎉 Application started!"
echo "📊 Frontend: http://localhost:3000"
echo "🔧 Backend:  http://localhost:8000" 