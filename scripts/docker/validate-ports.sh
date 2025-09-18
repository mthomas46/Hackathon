#!/bin/bash
# Port Configuration Validation Script
# Manual version - validates current ecosystem port assignments

echo "🔍 Validating Service Port Configurations..."
echo ""

ERRORS=0
WARNINGS=0

# Check for port conflicts - using simple approach to avoid bash version issues
EXTERNAL_PORTS_LIST=""
INTERNAL_PORTS_LIST=""

# Function to check port assignment
check_port() {
    local service="$1"
    local external="$2"
    local internal="$3"
    local description="$4"
    
    printf "%-25s %s:%s " "$service" "$external" "$internal"
    
    if [[ -n "${EXTERNAL_PORTS[$external]}" ]]; then
        echo "❌ ERROR: External port $external conflict with ${EXTERNAL_PORTS[$external]}"
        ERRORS=$((ERRORS + 1))
    else
        EXTERNAL_PORTS[$external]="$service"
        
        if [[ "$external" == "$internal" ]]; then
            echo "✅ OK"
        else
            echo "⚠️  MAPPED ($external→$internal)"
            WARNINGS=$((WARNINGS + 1))
        fi
    fi
    
    if [[ -n "${INTERNAL_PORTS[$internal]}" && "${INTERNAL_PORTS[$internal]}" != "$service" ]]; then
        printf "%-25s %s:%s ⚠️  WARNING: Internal port $internal shared with ${INTERNAL_PORTS[$internal]}\n" "" "" ""
        WARNINGS=$((WARNINGS + 1))
    fi
    INTERNAL_PORTS[$internal]="$service"
}

echo "Core Infrastructure Services:"
echo "-----------------------------"
check_port "redis" "6379" "6379" "Core caching & storage"
check_port "doc_store" "5087" "5010" "Document persistence"
check_port "orchestrator" "5099" "5099" "Service coordination"

echo ""
echo "AI/ML Services:"
echo "---------------"
check_port "llm-gateway" "5055" "5055" "LLM routing and management"
check_port "mock-data-generator" "5065" "5065" "AI-powered mock data generation"
check_port "summarizer-hub" "5160" "5160" "Content summarization service"
check_port "bedrock-proxy" "5060" "7090" "AWS Bedrock API proxy"
check_port "github-mcp" "5030" "5072" "GitHub Model Context Protocol"
check_port "ollama" "11434" "11434" "Local LLM inference engine"

echo ""
echo "Agent Services:"
echo "---------------"
check_port "memory-agent" "5090" "5040" "Memory and context management"
check_port "discovery-agent" "5050" "5050" "Service discovery and registry"
check_port "source-agent" "5085" "5085" "Source code analysis agent"

echo ""
echo "Analysis Services:"
echo "------------------"
check_port "analysis-service" "5080" "5020" "Document analysis and consistency"
check_port "code-analyzer" "5025" "5025" "Code analysis and metrics"
check_port "secure-analyzer" "5100" "5070" "Security analysis and scanning"
check_port "log-collector" "5040" "5080" "Centralized logging service"

echo ""
echo "Utility Services:"
echo "-----------------"
check_port "prompt_store" "5110" "5110" "Centralized prompt management"
check_port "interpreter" "5120" "5120" "Document interpretation service"
check_port "architecture-digitizer" "5105" "5105" "Architecture diagram processing"
check_port "notification-service" "5130" "5130" "Event notification system"

echo ""
echo "Web Services:"
echo "-------------"
check_port "frontend" "3000" "3000" "Web frontend interface"

echo ""
echo "==============================================="
echo "📊 Validation Summary"
echo "==============================================="
echo "Errors:   $ERRORS"
echo "Warnings: $WARNINGS"

if [ $ERRORS -eq 0 ]; then
    if [ $WARNINGS -eq 0 ]; then
        echo "Status:   ✅ PERFECT - No issues found!"
        echo ""
        echo "🎉 All port configurations are optimal!"
    else
        echo "Status:   ⚠️  GOOD - $WARNINGS port mappings detected"
        echo ""
        echo "ℹ️  Port mappings are normal when internal/external ports differ"
        echo "   This is often intentional for containerized services"
    fi
    exit 0
else
    echo "Status:   ❌ ISSUES FOUND - $ERRORS conflicts detected!"
    echo ""
    echo "🔧 Please resolve port conflicts before deployment"
    exit 1
fi
