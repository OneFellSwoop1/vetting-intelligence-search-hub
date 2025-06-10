#!/bin/bash

# Simple run script - use this instead of manual export commands
echo "🔧 Setting up correct environment..."

# Go to backend directory and activate venv
cd /Users/nicholas/Projects/vetting-intelligence-search-hub/backend
source ../venv/bin/activate

# Load correct environment variables (this loads the correct API key)
export $(cat environment.env | grep -v '^#' | xargs)

# Verify we have the correct API key
echo "🔑 Using LDA_API_KEY: ${LDA_API_KEY:0:10}..."
if [[ "$LDA_API_KEY" == 065* ]]; then
    echo "✅ Correct API key loaded (starts with 065)"
else
    echo "❌ ERROR: Wrong API key! Should start with 065, but starts with: ${LDA_API_KEY:0:3}"
    exit 1
fi

# Start server
echo "🚀 Starting server with correct API key..."
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload 