#!/bin/bash
# Startup script for bedrock-proxy

# Set Python path to allow imports
export PYTHONPATH=/app:$PYTHONPATH

# Run the service
exec python -m uvicorn main:app --host 0.0.0.0 --port 7090

