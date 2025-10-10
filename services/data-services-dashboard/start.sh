#!/bin/bash
# Start script for Data Services Dashboard
# Starts both FastAPI (port 8080) and Streamlit (port 8501) in parallel

set -e  # Exit on error

echo "🚀 Starting Data Services Dashboard..."
echo ""

# Start FastAPI in background
echo "📡 Starting FastAPI REST API on port 8080..."
uvicorn api_app:app \
  --host 0.0.0.0 \
  --port 8080 \
  --log-level info &

FASTAPI_PID=$!
echo "✅ FastAPI started (PID: $FASTAPI_PID)"
echo ""

# Wait a moment for FastAPI to bind to port
sleep 2

# Start Streamlit in foreground
echo "🎨 Starting Streamlit UI on port 8501..."
streamlit run app.py \
  --server.port 8501 \
  --server.address 0.0.0.0 \
  --server.enableCORS false \
  --browser.gatherUsageStats false

# If Streamlit exits, kill FastAPI
echo ""
echo "🛑 Streamlit stopped, shutting down FastAPI..."
kill $FASTAPI_PID 2>/dev/null || true
wait $FASTAPI_PID 2>/dev/null || true

echo "✅ Dashboard stopped cleanly"

