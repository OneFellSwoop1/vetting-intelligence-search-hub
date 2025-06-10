#!/bin/bash

# 🔍 Environment API Key Checker
# This script checks for any instances of incorrect API keys

echo "🔍 Checking environment for API key issues..."

# Check current shell environment
if [ -n "$LDA_API_KEY" ]; then
    if [[ "$LDA_API_KEY" == "REDACTED_OLD_LDA_API_KEY" ]]; then
        echo "✅ Shell environment has correct API key"
    else
        echo "❌ Shell environment has wrong API key!"
        echo "Current: $LDA_API_KEY"
        echo "Run: unset LDA_API_KEY"
    fi
else
    echo "ℹ️  No LDA_API_KEY set in shell environment"
fi

# Check environment file
if [ -f "backend/environment.env" ]; then
    env_key=$(grep "^LDA_API_KEY=" backend/environment.env | cut -d'=' -f2)
    if [[ "$env_key" == "REDACTED_OLD_LDA_API_KEY" ]]; then
        echo "✅ environment.env has correct API key"
    else
        echo "❌ environment.env has wrong API key!"
        echo "Found: $env_key"
    fi
else
    echo "❌ backend/environment.env not found!"
fi

# Check for any processes that might have wrong API key
echo ""
echo "🔍 Checking running processes..."
if pgrep -f uvicorn > /dev/null; then
    echo "⚠️  Backend is currently running - stop and restart to ensure correct API key"
    echo "Run: pkill -f uvicorn"
else
    echo "ℹ️  No backend processes running"
fi

echo ""
echo "📋 Summary:"
echo "- Use: ./clean_and_start.sh to start with guaranteed correct API key"
echo "- Use: unset LDA_API_KEY to clear wrong shell variable"
echo "- Use: ./stop_application.sh to stop all processes" 