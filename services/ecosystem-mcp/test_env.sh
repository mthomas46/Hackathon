#!/bin/bash
export OLLAMA_MODEL_SMALL=llama3.2:3b
python3 -m uvicorn src.api.app:create_app --factory --host 0.0.0.0 --port 8000 &
SERVICE_PID=$!
echo "Started service PID: $SERVICE_PID"
sleep 20
ps -p $SERVICE_PID
