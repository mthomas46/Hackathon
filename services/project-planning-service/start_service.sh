#!/bin/bash
# Start Project Planning Service with proper Python path

cd "$(dirname "$0")"

export PYTHONPATH="/Users/mykalthomas/Documents/work/Hackathon:$PYTHONPATH"
export DATABASE_PATH="data/project_planning.db"
export LOG_COLLECTOR_URL="http://localhost:5080"
export INTERPRETER_URL="http://localhost:5120"
export LLM_GATEWAY_URL="http://localhost:5055"
export USER_STORE_URL="http://localhost:5150"

echo "🚀 Starting Project Planning Service..."
echo "   PYTHONPATH: $PYTHONPATH"
echo "   Database: $DATABASE_PATH"
echo ""

python3 -m uvicorn main:app --host 127.0.0.1 --port 5170 --reload

