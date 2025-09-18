#!/bin/bash
# Dockerfile Linter - Prevents configuration issues
# Validates Dockerfiles for common problems we've encountered

echo "🔍 Dockerfile Linter"
echo "===================="
echo ""

ERRORS=0
service_path="$1"

if [[ -z "$service_path" ]]; then
    echo "Usage: $0 <service-directory>"
    echo "Example: $0 services/code-analyzer"
    exit 1
fi

if [[ ! -d "$service_path" ]]; then
    echo "❌ Service directory not found: $service_path"
    exit 1
fi

dockerfile="$service_path/Dockerfile"
main_file="$service_path/main.py"
service_name=$(basename "$service_path")

echo "Linting service: $service_name"
echo "Dockerfile: $dockerfile"
echo "Main file: $main_file"
echo ""

# Check if Dockerfile exists
if [[ ! -f "$dockerfile" ]]; then
    echo "❌ ERROR: Dockerfile not found at $dockerfile"
    exit 1
fi

echo "🔍 Checking port consistency..."

# Extract port configurations
expose_port=$(grep "EXPOSE" "$dockerfile" | awk '{print $2}' | head -1)
env_port=$(grep "SERVICE_PORT=" "$dockerfile" | cut -d'=' -f2 | head -1)
health_port=$(grep -o "localhost:[0-9]*" "$dockerfile" | cut -d':' -f2 | head -1)
label_port=$(grep "LABEL port=" "$dockerfile" | cut -d'"' -f2 | head -1)

echo "  EXPOSE port: $expose_port"
echo "  SERVICE_PORT: $env_port"
echo "  Health check port: $health_port"
echo "  Label port: $label_port"

# Validate port consistency
if [[ -n "$expose_port" && -n "$env_port" && "$expose_port" != "$env_port" ]]; then
    echo "❌ ERROR: EXPOSE port ($expose_port) doesn't match SERVICE_PORT ($env_port)"
    ERRORS=$((ERRORS + 1))
fi

if [[ -n "$health_port" && -n "$expose_port" && "$health_port" != "$expose_port" ]]; then
    echo "❌ ERROR: Health check port ($health_port) doesn't match EXPOSE port ($expose_port)"
    ERRORS=$((ERRORS + 1))
fi

if [[ -n "$label_port" && -n "$expose_port" && "$label_port" != "$expose_port" ]]; then
    echo "❌ ERROR: Label port ($label_port) doesn't match EXPOSE port ($expose_port)"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo "🔍 Checking CMD instruction..."

cmd_line=$(grep "CMD" "$dockerfile" | head -1)
if [[ -z "$cmd_line" ]]; then
    echo "❌ ERROR: No CMD instruction found"
    ERRORS=$((ERRORS + 1))
else
    echo "  CMD: $cmd_line"
    
    # Check for module execution pattern
    if echo "$cmd_line" | grep -q "\-m.*\.main"; then
        echo "⚠️  WARNING: Using module execution (-m) pattern"
        echo "  This may prevent __main__ block from executing"
        echo "  Consider using direct script execution instead"
        
        # Check if main.py exists and has __main__ block
        if [[ -f "$main_file" ]] && grep -q "if __name__ == \"__main__\":" "$main_file"; then
            echo "❌ ERROR: Service uses module execution but main.py has __main__ block"
            echo "  The __main__ block will never execute with 'python -m' command"
            echo "  SOLUTION: Change CMD to: python $service_path/main.py"
            ERRORS=$((ERRORS + 1))
        fi
    fi
fi

echo ""
echo "🔍 Checking main.py startup code..."

if [[ -f "$main_file" ]]; then
    # Check for FastAPI
    if grep -q "app = FastAPI" "$main_file"; then
        echo "  ✅ FastAPI app found"
        
        # Check for uvicorn startup
        if grep -q "uvicorn.run" "$main_file"; then
            echo "  ✅ uvicorn.run found"
            
            # Check for __main__ block
            if grep -q "if __name__ == \"__main__\":" "$main_file"; then
                echo "  ✅ __main__ block found"
            else
                echo "❌ ERROR: uvicorn.run found but no __main__ block"
                echo "  Add: if __name__ == '__main__': block"
                ERRORS=$((ERRORS + 1))
            fi
        else
            echo "⚠️  WARNING: FastAPI app found but no uvicorn.run startup"
            echo "  Service may not start properly"
        fi
    fi
else
    echo "⚠️  WARNING: main.py not found at $main_file"
fi

echo ""
echo "🔍 Checking health check configuration..."

if grep -q "HEALTHCHECK" "$dockerfile"; then
    health_cmd=$(grep "HEALTHCHECK" -A 1 "$dockerfile" | grep "CMD")
    echo "  ✅ Health check configured: $health_cmd"
else
    echo "⚠️  WARNING: No health check configured"
    echo "  Consider adding: HEALTHCHECK --interval=30s --timeout=10s --retries=3 \\"
    echo "    CMD curl -f http://localhost:PORT/health || exit 1"
fi

echo ""
echo "==============================================="
echo "📊 Dockerfile Linting Summary"
echo "==============================================="
echo "Service: $service_name"
echo "Errors: $ERRORS"

if [ $ERRORS -eq 0 ]; then
    echo "Status: ✅ PASS - Dockerfile is properly configured"
    exit 0
else
    echo "Status: ❌ FAIL - $ERRORS configuration errors found"
    echo ""
    echo "🔧 Fix these issues before deployment to prevent startup problems"
    exit 1
fi
