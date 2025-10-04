#!/bin/bash

# Complete Ecosystem Restart - Nuclear Clean Option
# This script performs a complete cleanup and restart of all services

set -e

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                              ║"
echo "║              🔄 COMPLETE ECOSYSTEM RESTART - NUCLEAR CLEAN                   ║"
echo "║                                                                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Change to project directory
cd /Users/mykalthomas/Documents/work/Hackathon

# ============================================================================
# STEP 1: KILL ALL PROCESSES
# ============================================================================
echo "🛑 STEP 1: Killing all running processes..."
echo "="*80

# Kill Python processes
pkill -9 -f "python.*main.py" 2>/dev/null || echo "  No main.py processes found"
pkill -9 -f "uvicorn" 2>/dev/null || echo "  No uvicorn processes found"
pkill -9 -f "fastapi" 2>/dev/null || echo "  No fastapi processes found"

# Kill processes on specific ports
for port in 5087 5110 5140 5090 8104; do
    lsof -ti:$port | xargs kill -9 2>/dev/null || echo "  Port $port already free"
done

sleep 2
echo "✅ All processes killed"
echo ""

# ============================================================================
# STEP 2: CLEAR PYTHON CACHE
# ============================================================================
echo "🧹 STEP 2: Clearing Python bytecode cache..."
echo "="*80

# Find and delete all .pyc files
echo "  Removing .pyc files..."
find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Find and delete all __pycache__ directories
echo "  Removing __pycache__ directories..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Clear any .pytest_cache
echo "  Removing .pytest_cache..."
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

echo "✅ Python cache cleared"
echo ""

# ============================================================================
# STEP 3: CLEAR DOCKER (IF USING)
# ============================================================================
echo "🐳 STEP 3: Clearing Docker containers..."
echo "="*80

if command -v docker &> /dev/null; then
    # Stop all containers
    docker ps -aq | xargs docker stop 2>/dev/null || echo "  No containers to stop"
    
    # Remove all containers
    docker ps -aq | xargs docker rm 2>/dev/null || echo "  No containers to remove"
    
    echo "✅ Docker cleaned"
else
    echo "  Docker not found, skipping"
fi
echo ""

# ============================================================================
# STEP 4: CLEAR TEMP LOGS
# ============================================================================
echo "📝 STEP 4: Clearing temp logs..."
echo "="*80

rm -f /tmp/*_store*.log 2>/dev/null || true
rm -f /tmp/*_agent*.log 2>/dev/null || true
rm -f /tmp/*service*.log 2>/dev/null || true

echo "✅ Temp logs cleared"
echo ""

# ============================================================================
# STEP 5: START SERVICES FRESH
# ============================================================================
echo "🚀 STEP 5: Starting services fresh..."
echo "="*80

# Start doc_store
echo "  [1/7] Starting doc_store on port 5087..."
python3 services/doc_store/main.py > /tmp/doc_store_clean.log 2>&1 &
DOC_PID=$!
echo "        PID: $DOC_PID"

sleep 2

# Start prompt_store
echo "  [2/7] Starting prompt_store on port 5110..."
python3 services/prompt_store/main.py > /tmp/prompt_store_clean.log 2>&1 &
PROMPT_PID=$!
echo "        PID: $PROMPT_PID"

sleep 2

# Start external-service-store
echo "  [3/7] Starting external-service-store on port 5140..."
python3 services/external-service-store/main.py > /tmp/external_service_store_clean.log 2>&1 &
EXTERNAL_PID=$!
echo "        PID: $EXTERNAL_PID"

sleep 2

# Start memory-agent
echo "  [4/7] Starting memory-agent on port 5090..."
python3 services/memory-agent/main.py > /tmp/memory_agent_clean.log 2>&1 &
MEMORY_PID=$!
echo "        PID: $MEMORY_PID"

sleep 2

# Start log-collector
echo "  [5/7] Starting log-collector on port 8104..."
python3 services/log-collector/main.py > /tmp/log_collector_clean.log 2>&1 &
LOG_PID=$!
echo "        PID: $LOG_PID"

sleep 2

# Start user-store (WORKFLOW F REQUIRED)
echo "  [6/7] Starting user-store on port 5150..."
python3 services/user-store/main.py > /tmp/user_store_clean.log 2>&1 &
USER_PID=$!
echo "        PID: $USER_PID"

sleep 2

# Start expert-finder-service (WORKFLOW F REQUIRED)
echo "  [7/7] Starting expert-finder-service on port 5160..."
python3 services/expert-finder-service/main.py > /tmp/expert_finder_clean.log 2>&1 &
EXPERT_PID=$!
echo "        PID: $EXPERT_PID"

echo ""
echo "✅ All 7 services started"
echo ""

# ============================================================================
# STEP 6: WAIT FOR INITIALIZATION
# ============================================================================
echo "⏳ STEP 6: Waiting 15 seconds for services to initialize..."
echo "="*80

for i in {15..1}; do
    echo -ne "  Waiting... $i seconds remaining\r"
    sleep 1
done
echo ""
echo "✅ Wait complete"
echo ""

# ============================================================================
# STEP 7: VERIFY SERVICES
# ============================================================================
echo "🔍 STEP 7: Verifying service health..."
echo "="*80

python3 check_services.py

echo ""

# ============================================================================
# STEP 8: TEST FIXES
# ============================================================================
echo "🧪 STEP 8: Testing persistence fixes..."
echo "="*80

python3 -c "
import asyncio
import httpx

async def test_all():
    services_tested = 0
    services_working = 0
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Test prompt_store
        print('  Testing prompt_store...')
        try:
            response = await client.post(
                'http://localhost:5110/api/v1/prompts',
                json={
                    'name': 'ecosystem_restart_test',
                    'category': 'testing',
                    'content': 'Testing after ecosystem restart',
                    'description': 'Validation test',
                    'tags': ['test'],
                    'variables': [],
                    'is_template': False
                }
            )
            services_tested += 1
            if response.status_code < 400:
                print(f'    ✅ prompt_store: {response.status_code} - Working!')
                services_working += 1
            else:
                print(f'    ❌ prompt_store: {response.status_code} - {response.text[:100]}')
        except Exception as e:
            print(f'    ❌ prompt_store: {str(e)[:100]}')
            services_tested += 1
        
        # Test doc_store
        print('  Testing doc_store...')
        try:
            response = await client.post(
                'http://localhost:5087/api/v1/documents',
                json={
                    'id': 'ecosystem_restart_test',
                    'content': 'Testing after ecosystem restart',
                    'metadata': {'test': True}
                }
            )
            services_tested += 1
            if response.status_code < 400:
                print(f'    ✅ doc_store: {response.status_code} - Working!')
                services_working += 1
            else:
                print(f'    ❌ doc_store: {response.status_code} - {response.text[:100]}')
        except Exception as e:
            print(f'    ❌ doc_store: {str(e)[:100]}')
            services_tested += 1
        
        # Test external-service-store
        print('  Testing external-service-store...')
        try:
            response = await client.post(
                'http://localhost:5140/services',
                json={
                    'name': 'ecosystem_restart_test',
                    'service_type': 'API',
                    'description': 'Testing after restart'
                }
            )
            services_tested += 1
            if response.status_code < 400:
                print(f'    ✅ external-service-store: {response.status_code} - Working!')
                services_working += 1
            else:
                print(f'    ❌ external-service-store: {response.status_code} - {response.text[:100]}')
        except Exception as e:
            print(f'    ❌ external-service-store: {str(e)[:100]}')
            services_tested += 1
        
        # Test memory-agent
        print('  Testing memory-agent...')
        try:
            response = await client.post(
                'http://localhost:5090/memory/put',
                json={
                    'item': {
                        'id': 'ecosystem_restart_test',
                        'user_id': 'test_user',
                        'memory_type': 'context',
                        'content': 'Testing after restart',
                        'metadata': {}
                    }
                }
            )
            services_tested += 1
            if response.status_code < 400:
                print(f'    ✅ memory-agent: {response.status_code} - Working!')
                services_working += 1
            else:
                print(f'    ❌ memory-agent: {response.status_code} - {response.text[:100]}')
        except Exception as e:
            print(f'    ❌ memory-agent: {str(e)[:100]}')
            services_tested += 1
        
        # Test user-store
        print('  Testing user-store...')
        try:
            response = await client.post(
                'http://localhost:5150/users',
                json={
                    'name': 'Test User',
                    'email': 'test@example.com',
                    'role': 'developer'
                }
            )
            services_tested += 1
            if response.status_code < 400:
                print(f'    ✅ user-store: {response.status_code} - Working!')
                services_working += 1
            else:
                print(f'    ❌ user-store: {response.status_code} - {response.text[:100]}')
        except Exception as e:
            print(f'    ❌ user-store: {str(e)[:100]}')
            services_tested += 1
        
        # Test expert-finder-service
        print('  Testing expert-finder-service...')
        try:
            response = await client.get('http://localhost:5160/health')
            services_tested += 1
            if response.status_code < 400:
                print(f'    ✅ expert-finder-service: {response.status_code} - Working!')
                services_working += 1
            else:
                print(f'    ❌ expert-finder-service: {response.status_code} - {response.text[:100]}')
        except Exception as e:
            print(f'    ❌ expert-finder-service: {str(e)[:100]}')
            services_tested += 1
    
    print()
    print(f'  Services Tested: {services_tested}/7')
    print(f'  Services Working: {services_working}/7')
    
    if services_working == 7:
        print()
        print('  🎉🎉🎉 ALL 7 SERVICES WORKING WITH FIXES! 🎉🎉🎉')
        return 0
    elif services_working > 0:
        print()
        print(f'  ⚠️  Partial success: {services_working}/7 services working')
        return 1
    else:
        print()
        print('  ❌ No services working - check logs')
        return 2

import sys
sys.exit(asyncio.run(test_all()))
"

TEST_RESULT=$?

echo ""
echo "="*80

# ============================================================================
# STEP 9: SUMMARY
# ============================================================================
echo ""
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                              ║"
echo "║                           📊 RESTART SUMMARY                                 ║"
echo "║                                                                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

echo "Process IDs:"
echo "  doc_store:              $DOC_PID"
echo "  prompt_store:           $PROMPT_PID"
echo "  external-service-store: $EXTERNAL_PID"
echo "  memory-agent:           $MEMORY_PID"
echo "  log-collector:          $LOG_PID"
echo "  user-store:             $USER_PID"
echo "  expert-finder-service:  $EXPERT_PID"
echo ""

echo "Logs:"
echo "  doc_store:              /tmp/doc_store_clean.log"
echo "  prompt_store:           /tmp/prompt_store_clean.log"
echo "  external-service-store: /tmp/external_service_store_clean.log"
echo "  memory-agent:           /tmp/memory_agent_clean.log"
echo "  log-collector:          /tmp/log_collector_clean.log"
echo "  user-store:             /tmp/user_store_clean.log"
echo "  expert-finder-service:  /tmp/expert_finder_clean.log"
echo ""

if [ $TEST_RESULT -eq 0 ]; then
    echo "✅ SUCCESS: All services are working with fixes!"
    echo ""
    echo "Next steps:"
    echo "  1. Run validation: python3 validate_data_persistence.py"
    echo "  2. Run demo: python3 demo_hyper_realistic_parameterized.py --output scala_elm_crud_demo_v11_VALIDATED --tickets 35 --team 8"
    echo "  3. Verify: Data Persisted ≠ 0 in reports"
elif [ $TEST_RESULT -eq 1 ]; then
    echo "⚠️  PARTIAL: Some services working, check logs for errors"
    echo ""
    echo "Check logs:"
    echo "  tail -50 /tmp/*_clean.log"
else
    echo "❌ FAILED: Services not working, check logs"
    echo ""
    echo "Check logs:"
    echo "  tail -50 /tmp/*_clean.log"
    echo ""
    echo "Try manual restart:"
    echo "  cd services/prompt_store && python3 main.py"
fi

echo ""
echo "="*80

exit $TEST_RESULT

