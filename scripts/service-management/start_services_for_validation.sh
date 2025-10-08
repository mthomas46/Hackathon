#!/bin/bash

# Start services for validation testing
# This script starts the 4 datastore services needed for persistence validation

echo "🚀 Starting Datastore Services..."

cd /Users/mykalthomas/Documents/work/Hackathon

# Start prompt_store
echo "Starting prompt_store on port 5110..."
cd services/prompt_store
python3 main.py > /tmp/prompt_store_val.log 2>&1 &
PROMPT_PID=$!
echo "  Started with PID: $PROMPT_PID"
cd ../..

# Start doc_store  
echo "Starting doc_store on port 5087..."
cd services/doc_store
python3 main.py > /tmp/doc_store_val.log 2>&1 &
DOC_PID=$!
echo "  Started with PID: $DOC_PID"
cd ../..

# Start external-service-store
echo "Starting external-service-store on port 5140..."
cd services/external-service-store
python3 main.py > /tmp/external_service_store_val.log 2>&1 &
EXTERNAL_PID=$!
echo "  Started with PID: $EXTERNAL_PID"
cd ../..

# Start memory-agent
echo "Starting memory-agent on port 5090..."
cd services/memory-agent
python3 main.py > /tmp/memory_agent_val.log 2>&1 &
MEMORY_PID=$!
echo "  Started with PID: $MEMORY_PID"
cd ../..

echo ""
echo "⏳ Waiting 10 seconds for services to initialize..."
sleep 10

echo ""
echo "🔍 Checking service health..."
python3 check_services.py

echo ""
echo "📝 Process IDs:"
echo "  prompt_store: $PROMPT_PID"
echo "  doc_store: $DOC_PID"
echo "  external-service-store: $EXTERNAL_PID"
echo "  memory-agent: $MEMORY_PID"

echo ""
echo "✅ Services started! Run validate_data_persistence.py to test."

