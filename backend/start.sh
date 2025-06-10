#!/bin/bash

# Navigate to backend directory
cd "$(dirname "$0")"

# Clear any existing LDA_API_KEY to prevent conflicts
unset LDA_API_KEY

# Load environment variables from environment.env
if [ -f "environment.env" ]; then
    # Load variables and export them
    set -a  # automatically export all variables
    source environment.env
    set +a  # stop auto-exporting
    
    echo "✅ Loaded environment variables from environment.env"
    echo "🔑 LDA_API_KEY loaded: ${LDA_API_KEY:0:10}..." # Show first 10 chars for verification
    
    # Verify the API key is correct (should start with 065)
    if [[ "$LDA_API_KEY" == 065* ]]; then
        echo "✅ Correct LDA API key detected (starting with 065)"
    else
        echo "❌ WARNING: LDA API key may be incorrect - should start with 065"
        echo "Current key starts with: ${LDA_API_KEY:0:3}"
    fi
else
    echo "❌ environment.env file not found!"
    exit 1
fi

# Activate virtual environment if not already active
if [ -z "$VIRTUAL_ENV" ]; then
    if [ -f "../venv/bin/activate" ]; then
        source ../venv/bin/activate
        echo "✅ Activated virtual environment"
    else
        echo "❌ Virtual environment not found at ../venv/"
        exit 1
    fi
fi

# Start the backend server
echo "🚀 Starting backend server with correct environment..."
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload 