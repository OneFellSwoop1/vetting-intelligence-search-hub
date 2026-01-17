#!/bin/bash
# Script to simulate CI environment locally for debugging

echo "🔍 SIMULATING CI ENVIRONMENT LOCALLY"
echo "===================================="

# Clean up any existing virtual environment
rm -rf .ci_test_venv

# Create fresh virtual environment with Python 3.11
echo "📦 Creating Python 3.11 virtual environment..."
python3.11 -m venv .ci_test_venv || python3 -m venv .ci_test_venv

# Activate virtual environment
source .ci_test_venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
cd backend
pip install --quiet -r requirements.txt

# Create environment.env file (like CI does)
echo "📝 Creating environment.env..."
cat > environment.env << 'EOF'
# Minimal CI environment file for Pydantic Settings
JWT_SECRET_KEY=test_jwt_secret_key_for_ci_testing_min_32_chars_1234567890abcdefghij
SECRET_KEY=test_secret_key_for_ci_1234567890
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
ENVIRONMENT=test
LOG_LEVEL=INFO
REDIS_URL=redis://localhost:6379/0
EOF

# Test import (like CI does)
echo "🧪 Testing backend import..."
python -c "from app.main import app; print('✅ Backend imports successful')"

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "✅ SUCCESS! Backend imports work in CI-like environment"
else
    echo ""
    echo "❌ FAILED! Backend imports failed with exit code $EXIT_CODE"
fi

# Cleanup
cd ..
deactivate
rm -rf .ci_test_venv

exit $EXIT_CODE
