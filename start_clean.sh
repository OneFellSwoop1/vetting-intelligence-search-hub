#!/bin/bash

echo "🧹 CLEAN START - Ensuring correct API key configuration"

# Clear any existing wrong API keys from shell environment
unset LDA_API_KEY
unset SENATE_LDA_API_KEY

# Source the correct environment file
if [ -f "backend/environment.env" ]; then
    echo "📄 Loading environment from backend/environment.env"
    export $(grep -v '^#' backend/environment.env | xargs)
else
    echo "❌ Error: backend/environment.env not found"
    exit 1
fi

# Verify the correct API key is loaded
if [[ "$LDA_API_KEY" == 065* ]]; then
    echo "✅ Correct LDA API key loaded: ${LDA_API_KEY:0:10}..."
else
    echo "❌ ERROR: Wrong or missing API key!"
    echo "   Expected: Should start with '065'"
    echo "   Got:      ${LDA_API_KEY:-'NOT SET'}"
    exit 1
fi

# Activate virtual environment
echo "🐍 Activating virtual environment..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "❌ Virtual environment not found. Run: python -m venv venv && source venv/bin/activate && pip install -r backend/requirements.txt"
    exit 1
fi

# Start backend
echo "🚀 Starting backend server..."
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload 