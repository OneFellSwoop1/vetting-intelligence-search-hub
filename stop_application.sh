#!/bin/bash

# 🛑 Vetting Intelligence Search Hub - Stop Script

echo "🛑 Stopping Vetting Intelligence Search Hub..."

# Function to kill processes by PID
kill_by_pid() {
    local pid_file=$1
    local service_name=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo "  Stopping $service_name (PID: $pid)..."
            kill "$pid" 2>/dev/null
            sleep 2
            # Force kill if still running
            if kill -0 "$pid" 2>/dev/null; then
                echo "  Force stopping $service_name..."
                kill -9 "$pid" 2>/dev/null
            fi
        fi
        rm -f "$pid_file"
    fi
}

# Kill by saved PIDs
kill_by_pid ".backend_pid" "Backend"
kill_by_pid ".frontend_pid" "Frontend"

# Kill any remaining processes on the ports
echo "🧹 Cleaning up any remaining processes..."

if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "  Stopping remaining backend processes..."
    lsof -Pi :8000 -sTCP:LISTEN -t | xargs kill -9 2>/dev/null || true
fi

if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "  Stopping remaining frontend processes..."
    lsof -Pi :3000 -sTCP:LISTEN -t | xargs kill -9 2>/dev/null || true
fi

echo "✅ Application stopped successfully!"
echo ""
echo "📝 Log files are preserved:"
echo "   backend.log"
echo "   frontend.log"
echo ""
echo "🚀 To start again: ./start_application.sh" 