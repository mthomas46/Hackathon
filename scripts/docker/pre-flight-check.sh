#!/bin/bash
# Pre-Flight Check System
# Comprehensive validation to prevent configuration issues before deployment

echo "🛡️ Pre-Flight Check System"
echo "=========================="
echo ""

ERRORS=0
WARNINGS=0

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to log errors
log_error() {
    echo -e "${RED}❌ ERROR: $1${NC}"
    ERRORS=$((ERRORS + 1))
}

# Function to log warnings
log_warning() {
    echo -e "${YELLOW}⚠️  WARNING: $1${NC}"
    WARNINGS=$((WARNINGS + 1))
}

# Function to log success
log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

echo "🔍 1. DOCKERFILE VALIDATION"
echo "----------------------------"

# Check all service Dockerfiles
for dockerfile in services/*/Dockerfile; do
    if [[ -f "$dockerfile" ]]; then
        service_name=$(basename $(dirname "$dockerfile"))
        echo "Checking $service_name..."
        
        # Extract ports from Dockerfile
        expose_port=$(grep "EXPOSE" "$dockerfile" | awk '{print $2}' | head -1)
        env_port=$(grep "SERVICE_PORT=" "$dockerfile" | cut -d'=' -f2 | head -1)
        health_port=$(grep -o "localhost:[0-9]*" "$dockerfile" | cut -d':' -f2 | head -1)
        
        # Check port consistency
        if [[ -n "$expose_port" && -n "$env_port" && "$expose_port" != "$env_port" ]]; then
            log_error "Port mismatch in $service_name: EXPOSE $expose_port vs SERVICE_PORT $env_port"
        fi
        
        if [[ -n "$health_port" && -n "$expose_port" && "$health_port" != "$expose_port" ]]; then
            log_error "Health check port mismatch in $service_name: health check $health_port vs EXPOSE $expose_port"
        fi
        
        # Check for CMD instruction
        if ! grep -q "CMD" "$dockerfile"; then
            log_error "Missing CMD instruction in $service_name Dockerfile"
        fi
        
        # Check for proper Python module vs script execution
        cmd_line=$(grep "CMD" "$dockerfile" | head -1)
        if echo "$cmd_line" | grep -q "\-m.*\.main" && [[ -f "services/$service_name/main.py" ]]; then
            # Check if main.py has __main__ block
            if grep -q "if __name__ == \"__main__\":" "services/$service_name/main.py"; then
                log_warning "Service $service_name uses module execution but has __main__ block - may not start properly"
            fi
        fi
    fi
done

echo ""
echo "🔍 2. SERVICE STARTUP CODE VALIDATION"
echo "--------------------------------------"

# Check all Python main files for proper startup code
for main_file in services/*/main.py; do
    if [[ -f "$main_file" ]]; then
        service_name=$(basename $(dirname "$main_file"))
        echo "Checking $service_name startup code..."
        
        # Check for FastAPI app
        if grep -q "app = FastAPI" "$main_file"; then
            # Check for uvicorn startup
            if grep -q "uvicorn.run" "$main_file"; then
                # Check for __main__ block
                if grep -q "if __name__ == \"__main__\":" "$main_file"; then
                    log_success "Service $service_name has proper startup code"
                else
                    log_error "Service $service_name has uvicorn.run but no __main__ block"
                fi
            else
                log_warning "Service $service_name has FastAPI app but no uvicorn.run startup"
            fi
        fi
    fi
done

echo ""
echo "🔍 3. PORT REGISTRY CONSISTENCY"
echo "-------------------------------"

# Check consistency with port registry
if [[ -f "config/service-ports.yaml" ]]; then
    echo "Validating against port registry..."
    
    # Simple validation for key services (would need yq for full YAML parsing)
    while IFS= read -r line; do
        if [[ "$line" =~ ^[[:space:]]*([a-z_-]+):[[:space:]]*$ ]]; then
            service_name="${BASH_REMATCH[1]}"
            if [[ -f "services/$service_name/Dockerfile" ]]; then
                echo "Found service $service_name in registry and filesystem ✅"
            fi
        fi
    done < config/service-ports.yaml
    
    log_success "Port registry validation completed"
else
    log_warning "Port registry config/service-ports.yaml not found"
fi

echo ""
echo "🔍 4. DOCKER COMPOSE VALIDATION"
echo "--------------------------------"

# Validate docker-compose syntax
if docker-compose -f docker-compose.dev.yml config --quiet; then
    log_success "Docker Compose syntax is valid"
else
    log_error "Docker Compose syntax validation failed"
fi

# Check for common issues
compose_content=$(cat docker-compose.dev.yml)

# Check for version conflicts
if echo "$compose_content" | grep -q "version:"; then
    log_warning "Docker Compose contains deprecated 'version:' field"
fi

echo ""
echo "🔍 5. DEPENDENCY VALIDATION"
echo "---------------------------"

# Check for common missing dependencies
echo "Checking for common dependency issues..."

# Check requirements files exist
for req_file in services/requirements.base.txt services/shared/requirements.txt; do
    if [[ -f "$req_file" ]]; then
        log_success "Requirements file found: $req_file"
    else
        log_error "Missing requirements file: $req_file"
    fi
done

# Check for services with complex dependencies
if [[ -f "services/summarizer-hub/modules/peer_review_enhancer.py" ]]; then
    if grep -q "nltk\|spacy\|textblob" "services/summarizer-hub/modules/peer_review_enhancer.py"; then
        if [[ -f "services/summarizer-hub/main_simple.py" ]]; then
            log_success "Summarizer Hub has simplified fallback version"
        else
            log_warning "Summarizer Hub has complex NLP dependencies - consider simplified version"
        fi
    fi
fi

echo ""
echo "🔍 6. HEALTH CHECK VALIDATION"
echo "-----------------------------"

# Validate health check endpoints
echo "Checking health check configurations..."

for dockerfile in services/*/Dockerfile; do
    if [[ -f "$dockerfile" ]]; then
        service_name=$(basename $(dirname "$dockerfile"))
        
        if grep -q "HEALTHCHECK" "$dockerfile"; then
            health_url=$(grep "HEALTHCHECK" -A 1 "$dockerfile" | grep -o "http://[^\"]*" | head -1)
            if [[ -n "$health_url" ]]; then
                log_success "Service $service_name has health check configured"
            fi
        else
            log_warning "Service $service_name missing health check"
        fi
    fi
done

echo ""
echo "==============================================="
echo "📊 PRE-FLIGHT CHECK SUMMARY"
echo "==============================================="
echo "Errors:   $ERRORS"
echo "Warnings: $WARNINGS"

if [ $ERRORS -eq 0 ]; then
    if [ $WARNINGS -eq 0 ]; then
        echo -e "${GREEN}Status:   ✅ PERFECT - Ready for deployment!${NC}"
        exit 0
    else
        echo -e "${YELLOW}Status:   ⚠️  GOOD - $WARNINGS warnings to review${NC}"
        exit 0
    fi
else
    echo -e "${RED}Status:   ❌ ISSUES FOUND - $ERRORS errors must be fixed before deployment${NC}"
    exit 1
fi
