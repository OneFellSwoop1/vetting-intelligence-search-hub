#!/bin/bash

# 🔧 Fix & Start Vetting Intelligence Search Hub
# This script guarantees the correct API key and proper startup

echo "🔧 FIXING API KEY ISSUES & STARTING APPLICATION"
echo "================================================"

# 1. FORCE UNSET ANY EXISTING WRONG API KEYS
echo "🧹 Step 1: Cleaning up any incorrect API key settings..."
unset LDA_API_KEY
unset SENATE_LDA_API_KEY

# Also check for and remove any wrong keys from shell history/environment
export LDA_API_KEY=""

# 2. KILL EXISTING PROCESSES
echo "🛑 Step 2: Stopping any existing processes..."
pkill -f uvicorn 2>/dev/null && echo "   ✅ Stopped uvicorn" || echo "   ℹ️  No uvicorn processes running"
pkill -f "npm run dev" 2>/dev/null && echo "   ✅ Stopped npm dev" || echo "   ℹ️  No npm processes running"
pkill -f "next dev" 2>/dev/null && echo "   ✅ Stopped next dev" || echo "   ℹ️  No next processes running"
sleep 3

# 3. VERIFY ENVIRONMENT FILE EXISTS
echo "🔍 Step 3: Verifying environment configuration..."
if [ ! -f "backend/environment.env" ]; then
    echo "   ❌ ERROR: backend/environment.env not found!"
    echo "   Create the file with the correct API key first."
    exit 1
fi

# 4. LOAD CORRECT API KEYS
echo "🔑 Step 4: Loading correct API keys from environment file..."
export $(cat backend/environment.env | grep -v '^#' | grep -v '^$' | xargs)

# 5. VERIFY API KEY IS CORRECT
echo "🔍 Step 5: Verifying API key correctness..."
echo "   Current LDA_API_KEY: ${LDA_API_KEY:0:10}..."

if [[ "$LDA_API_KEY" == "065af08d580cf15c2220836fb456a5ebe504186c" ]]; then
    echo "   ✅ CORRECT API key detected!"
else
    echo "   ❌ API KEY ERROR!"
    echo "   Expected: 065af08d580cf15c2220836fb456a5ebe504186c"
    echo "   Got:      ${LDA_API_KEY:-'NOT SET'}"
    echo ""
    echo "   Please check backend/environment.env and ensure it contains:"
    echo "   LDA_API_KEY=065af08d580cf15c2220836fb456a5ebe504186c"
    exit 1
fi

# 6. SETUP PYTHON ENVIRONMENT
echo "🐍 Step 6: Setting up Python environment..."
if [ ! -d "venv" ]; then
    echo "   Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
echo "   ✅ Virtual environment activated"

# 7. INSTALL DEPENDENCIES
echo "📦 Step 7: Installing/updating dependencies..."
cd backend
echo "   Installing Python dependencies..."
pip install -r requirements.txt --quiet

# 8. TEST API KEY BEFORE STARTING
echo "🧪 Step 8: Testing API key with a quick request..."
python3 -c "
import os
import requests
import sys

api_key = os.getenv('LDA_API_KEY')
if not api_key:
    print('   ❌ No API key found in environment')
    sys.exit(1)

try:
    headers = {'X-API-Key': api_key}
    response = requests.get('https://lda.senate.gov/api/v1/filings/?page_size=1', headers=headers, timeout=10)
    if response.status_code == 200:
        print('   ✅ API key authentication successful!')
    elif response.status_code == 401:
        print('   ❌ API key authentication failed (401 Unauthorized)')
        sys.exit(1)
    else:
        print(f'   ⚠️  API responded with status {response.status_code}')
except Exception as e:
    print(f'   ⚠️  Could not test API key: {e}')
"

if [ $? -ne 0 ]; then
    echo "   ❌ API key test failed. Please check your API key."
    exit 1
fi

# 9. START BACKEND WITH VERIFIED SETTINGS
echo "🚀 Step 9: Starting backend with verified API key..."
echo "   Starting uvicorn server..."

# Ensure we're in the backend directory and start the server properly
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload &
BACKEND_PID=$!

# 10. WAIT FOR BACKEND TO START
echo "⏳ Step 10: Waiting for backend to initialize..."
sleep 8

# Test backend health
if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo "   ✅ Backend is running successfully on port 8000"
else
    echo "   ❌ Backend failed to start properly"
    kill $BACKEND_PID 2>/dev/null
    echo "   Check backend logs for errors"
    exit 1
fi

# 11. START FRONTEND
echo "🎨 Step 11: Starting frontend..."
cd ../frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "   Installing npm dependencies..."
    npm install --silent
fi

echo "   Starting Next.js development server..."
npm run dev &
FRONTEND_PID=$!

# 12. SAVE PROCESS IDS
echo $BACKEND_PID > ../.backend_pid
echo $FRONTEND_PID > ../.frontend_pid

# 13. SUCCESS MESSAGE
echo ""
echo "🎉 APPLICATION STARTED SUCCESSFULLY!"
echo "====================================="
echo "📊 Frontend: http://localhost:3000"
echo "🔧 Backend:  http://localhost:8000"
echo "🔍 API Test: http://localhost:8000/health"
echo ""
echo "🔑 Using API Key: ${LDA_API_KEY:0:10}... (CORRECT)"
echo ""
echo "To stop the application:"
echo "  ./stop_application.sh"
echo ""
echo "To check status:"
echo "  ./check_environment.sh"

# Wait a bit then show final status
sleep 5
echo ""
echo "🔍 Final Status Check:"
echo "  Backend Health: $(curl -sf http://localhost:8000/health > /dev/null 2>&1 && echo "✅ OK" || echo "❌ Failed")"
echo "  Frontend Status: $(curl -sf http://localhost:3000 > /dev/null 2>&1 && echo "✅ OK" || echo "⏳ Starting...")"

# Keep processes running
echo ""
echo "Application is running. Press Ctrl+C to stop."
wait 