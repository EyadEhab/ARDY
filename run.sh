#!/bin/bash

# EgyptAgri-Pulse Startup Script
# Runs both Flask backend and Streamlit frontend

set -e

# Activate virtual environment
source venv/bin/activate

echo "=================================================="
echo "🌾 EgyptAgri-Pulse Startup"
echo "=================================================="

# Check if models exist
if [ ! -f "models/xgb_crop_classifier.pkl" ]; then
    echo "❌ Models not found. Training models..."
    python train_models.py
fi

# Start Flask backend in background
echo ""
echo "Starting Flask Backend Server..."
python backend.py &
BACKEND_PID=$!
echo "✓ Backend started (PID: $BACKEND_PID)"

# Wait for backend to start
sleep 3

# Start Streamlit frontend
echo ""
echo "Starting Streamlit Dashboard..."
echo "=================================================="
echo "Dashboard will be available at: http://localhost:8501"
echo "API Backend: http://localhost:5000"
echo "=================================================="
echo ""

streamlit run app.py --server.port=8501 --server.address=0.0.0.0

# Cleanup on exit
trap "kill $BACKEND_PID" EXIT
