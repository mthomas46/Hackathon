#!/bin/bash
#
# Docker Memory Verification Script
# Verifies Docker Desktop and Ollama container memory allocation
#

echo "════════════════════════════════════════════════════════════════════════════════"
echo "🔍 DOCKER MEMORY VERIFICATION"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

# Check Docker Desktop total memory
echo "1. Docker Desktop Memory Allocation"
echo "───────────────────────────────────────────────────────────────────────────────"
DOCKER_MEMORY=$(docker info 2>/dev/null | grep "Total Memory" | awk '{print $3, $4}')
DOCKER_MEMORY_GB=$(docker info 2>/dev/null | grep "Total Memory" | awk '{print $3}' | sed 's/GiB//')

echo "   Total Memory: $DOCKER_MEMORY"

if (( $(echo "$DOCKER_MEMORY_GB < 20" | bc -l) )); then
    echo "   Status: ❌ INSUFFICIENT (< 20 GB)"
    echo "   Action: Increase Docker Desktop memory to 32+ GB"
    DOCKER_OK=false
elif (( $(echo "$DOCKER_MEMORY_GB < 28" | bc -l) )); then
    echo "   Status: ⚠️  MARGINAL (20-28 GB)"
    echo "   Action: Recommended to increase to 32+ GB for optimal performance"
    DOCKER_OK=partial
else
    echo "   Status: ✅ SUFFICIENT (>= 28 GB)"
    DOCKER_OK=true
fi
echo ""

# Check if Ollama container exists
echo "2. Ollama Container Configuration"
echo "───────────────────────────────────────────────────────────────────────────────"

if ! docker ps -a --format '{{.Names}}' | grep -q "ecosystem-mcp-ollama"; then
    echo "   Status: ❌ Container not found"
    echo "   Action: Run 'docker-compose up -d ollama'"
    exit 1
fi

# Check Ollama container memory limit
CONTAINER_MEMORY=$(docker inspect ecosystem-mcp-ollama 2>/dev/null | python3 -c "import sys, json; c=json.load(sys.stdin)[0]; mem=c['HostConfig'].get('Memory', 0); print(f'{mem/1024**3:.1f}' if mem > 0 else '0')")

echo "   Container Memory Limit: ${CONTAINER_MEMORY} GB"

if (( $(echo "$CONTAINER_MEMORY < 20" | bc -l) )); then
    echo "   Status: ❌ INSUFFICIENT (< 20 GB)"
    echo "   Action: Container limit set but may be constrained by Docker Desktop"
    CONTAINER_OK=false
elif (( $(echo "$CONTAINER_MEMORY < 28" | bc -l) )); then
    echo "   Status: ⚠️  MARGINAL (20-28 GB)"
    CONTAINER_OK=partial
else
    echo "   Status: ✅ SUFFICIENT (>= 28 GB)"
    CONTAINER_OK=true
fi
echo ""

# Check if Ollama is running
echo "3. Ollama Service Status"
echo "───────────────────────────────────────────────────────────────────────────────"

if docker ps --format '{{.Names}}' | grep -q "ecosystem-mcp-ollama"; then
    echo "   Container: ✅ Running"
    
    # Check if Ollama API is responding
    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        echo "   API:       ✅ Responding"
        OLLAMA_OK=true
    else
        echo "   API:       ❌ Not responding"
        echo "   Action: Run 'docker-compose restart ollama'"
        OLLAMA_OK=false
    fi
else
    echo "   Container: ❌ Not running"
    echo "   Action: Run 'docker-compose up -d ollama'"
    OLLAMA_OK=false
fi
echo ""

# Test model loading (only if everything else is OK)
if [ "$DOCKER_OK" = "true" ] && [ "$OLLAMA_OK" = "true" ]; then
    echo "4. Model Loading Test"
    echo "───────────────────────────────────────────────────────────────────────────────"
    
    # Test LLaMA 3.1 8B
    echo "   Testing llama3.1:8b-instruct-q8_0..."
    
    RESPONSE=$(curl -s -X POST http://localhost:11434/api/generate \
        -d '{"model":"llama3.1:8b-instruct-q8_0","prompt":"Test","stream":false}' 2>&1)
    
    if echo "$RESPONSE" | grep -q "error"; then
        ERROR_MSG=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('error', 'Unknown error'))" 2>/dev/null)
        echo "   Status: ❌ FAILED"
        echo "   Error:  $ERROR_MSG"
        MODEL_OK=false
        
        if echo "$ERROR_MSG" | grep -q "more system memory"; then
            echo ""
            echo "   ⚠️  ISSUE: Docker Desktop memory allocation is still too low"
            echo "   Current Docker Memory: $DOCKER_MEMORY"
            echo "   Required for LLaMA 8B: 8.8 GB minimum"
            echo ""
            echo "   📋 ACTION REQUIRED:"
            echo "   1. Open Docker Desktop Settings"
            echo "   2. Go to Resources → Advanced"
            echo "   3. Increase Memory to 32 GB or higher"
            echo "   4. Click 'Apply & Restart'"
            echo "   5. Wait for Docker to restart"
            echo "   6. Run this script again"
        fi
    elif echo "$RESPONSE" | grep -q "response"; then
        RESPONSE_TEXT=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('response', '')[:50])" 2>/dev/null)
        echo "   Status:   ✅ SUCCESS"
        echo "   Response: ${RESPONSE_TEXT}..."
        MODEL_OK=true
    else
        echo "   Status: ⚠️  UNKNOWN (unexpected response)"
        MODEL_OK=unknown
    fi
    echo ""
fi

# Summary
echo "════════════════════════════════════════════════════════════════════════════════"
echo "📊 SUMMARY"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

if [ "$DOCKER_OK" = "true" ] && [ "$OLLAMA_OK" = "true" ] && [ "$MODEL_OK" = "true" ]; then
    echo "✅ All checks passed!"
    echo ""
    echo "Your system is ready for:"
    echo "  • Multiple LLaMA models (8B, 13B)"
    echo "  • High-quality RAG responses"
    echo "  • Fast model switching"
    echo ""
    echo "Next steps:"
    echo "  1. Load additional models:"
    echo "     docker exec ecosystem-mcp-ollama ollama pull mistral:7b-instruct-q8_0"
    echo "  2. Test RAG endpoint:"
    echo "     python3 generate_dev_history.py"
    exit 0
elif [ "$DOCKER_OK" = "partial" ] || [ "$CONTAINER_OK" = "partial" ]; then
    echo "⚠️  System has marginal memory allocation"
    echo ""
    echo "Current setup will work but may be limited. Consider:"
    echo "  • Increasing Docker Desktop memory to 32+ GB"
    echo "  • Closing other memory-intensive applications"
    echo ""
    exit 0
else
    echo "❌ System not ready for large models"
    echo ""
    echo "Required actions:"
    if [ "$DOCKER_OK" = "false" ]; then
        echo "  1. Increase Docker Desktop memory allocation"
        echo "     Settings → Resources → Advanced → Memory: 32+ GB"
    fi
    if [ "$OLLAMA_OK" = "false" ]; then
        echo "  2. Start Ollama container:"
        echo "     docker-compose up -d ollama"
    fi
    echo ""
    echo "For detailed instructions, see:"
    echo "  ./DOCKER_MEMORY_INCREASE_GUIDE.md"
    echo ""
    exit 1
fi

