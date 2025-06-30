#!/bin/bash

echo "🚀 STARTING VETTING INTELLIGENCE SEARCH HUB SERVER"

# Clear any existing wrong API keys from shell environment
unset LDA_API_KEY
unset SENATE_LDA_API_KEY

# Change to correct directory
cd backend

# Load environment variables from file
if [ -f "environment.env" ]; then
    echo "📄 Loading environment from backend/environment.env"
    export $(grep -v '^#' environment.env | xargs)
else
    echo "❌ Error: backend/environment.env not found"
    exit 1
fi

# Verify correct API key is loaded
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
source ../venv/bin/activate

# Start server
echo "🌐 Starting FastAPI server on http://127.0.0.1:8000"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload 