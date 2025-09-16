#!/bin/bash

# Confluence Hub Service Startup Script
# This script helps you start the service with all dependencies

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Starting Confluence Hub Service"
echo "=================================="
echo "📍 Working directory: $SCRIPT_DIR"

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from template..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "📝 Please edit .env file with your Confluence and MongoDB credentials"
        echo "   Required variables:"
        echo "   - ConfluenceBaseUrl"
        echo "   - ConfluenceUsername" 
        echo "   - ConfluenceApiToken"
        echo "   - MongoConnectionString"
        echo ""
        echo "💡 Example for Confluence Cloud:"
        echo "   ConfluenceBaseUrl=https://your-domain.atlassian.net"
        echo "   ConfluenceUsername=your-email@company.com"
        echo "   ConfluenceApiToken=your-api-token"
        echo ""
        exit 1
    else
        echo "❌ .env.example file not found"
        exit 1
    fi
fi

# Load environment variables
echo "📋 Loading environment variables from .env..."
source .env

# Check required variables
required_vars=("ConfluenceBaseUrl" "ConfluenceUsername" "ConfluenceApiToken" "MongoConnectionString")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    echo "❌ Missing required environment variables:"
    printf '   - %s\n' "${missing_vars[@]}"
    echo ""
    echo "📝 Please edit .env file with your credentials"
    exit 1
fi

echo "✅ All required environment variables are set"

# Check if MongoDB is running (if using local MongoDB)
if [[ "$MongoConnectionString" == *"localhost"* ]] || [[ "$MongoConnectionString" == *"127.0.0.1"* ]]; then
    echo "🔍 Checking if MongoDB is running locally..."
    
    # Try multiple ways to detect MongoDB
    MONGODB_RUNNING=false
    
    # Method 1: Check for mongod process
    if pgrep -x "mongod" > /dev/null; then
        MONGODB_RUNNING=true
    fi
    
    # Method 2: Check for docker container named mongodb
    if command -v docker &> /dev/null && docker ps --format "table {{.Names}}" | grep -q "mongodb"; then
        MONGODB_RUNNING=true
    fi
    
    # Method 3: Try to connect to MongoDB port
    if command -v nc &> /dev/null && nc -z localhost 27017; then
        MONGODB_RUNNING=true
    fi
    
    # Method 4: Try to connect with mongo/mongosh if available
    if command -v mongosh &> /dev/null && mongosh --eval "db.adminCommand('ping')" --quiet > /dev/null 2>&1; then
        MONGODB_RUNNING=true
    elif command -v mongo &> /dev/null && mongo --eval "db.adminCommand('ping')" --quiet > /dev/null 2>&1; then
        MONGODB_RUNNING=true
    fi
    
    if [ "$MONGODB_RUNNING" = false ]; then
        echo "⚠️  MongoDB doesn't appear to be running locally"
        echo "💡 To start MongoDB with Docker:"
        echo "   docker run -d -p 27017:27017 --name mongodb mongo:latest"
        echo ""
        echo "   Or start the full stack with:"
        echo "   docker-compose -f docker-compose.services.yml up mongodb"
        echo ""
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        echo "✅ MongoDB is running"
    fi
fi

# Detect and use virtual environment
VENV_PATH=""
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [ -f "$PROJECT_ROOT/.venv/bin/python" ]; then
    VENV_PATH="$PROJECT_ROOT/.venv/bin/"
    echo "📦 Using virtual environment at $PROJECT_ROOT/.venv/"
elif [ -f "$SCRIPT_DIR/.venv/bin/python" ]; then
    VENV_PATH="$SCRIPT_DIR/.venv/bin/"
    echo "📦 Using virtual environment at $SCRIPT_DIR/.venv/"
else
    echo "📦 No virtual environment found, using system Python"
fi

# Install dependencies if needed
if [ ! -z "$VENV_PATH" ] && [ ! -f "${VENV_PATH}uvicorn" ]; then
    echo "📦 Installing dependencies..."
    ${VENV_PATH}pip install -r requirements.txt
fi

# Start the service
echo "🎯 Starting Confluence Hub Service on port 5070..."
echo "   Health endpoint: http://localhost:5070/confluence-hub/health"
echo "   API docs: http://localhost:5070/docs"
echo ""

# Export environment variables for the Python process
export ConfluenceBaseUrl
export ConfluenceUsername
export ConfluenceApiToken
export MongoConnectionString

# Set Python path for imports
export PYTHONPATH="$PROJECT_ROOT"

# Start with uvicorn
if [ ! -z "$VENV_PATH" ] && [ -f "${VENV_PATH}uvicorn" ]; then
    echo "🚀 Starting with virtual environment..."
    cd "$PROJECT_ROOT"
    "${VENV_PATH}uvicorn" services.confluence-hub.main:app --host 0.0.0.0 --port 5070 --reload
elif command -v uvicorn &> /dev/null; then
    echo "🚀 Starting with system uvicorn..."
    cd "$PROJECT_ROOT"
    uvicorn services.confluence-hub.main:app --host 0.0.0.0 --port 5070 --reload
else
    echo "⚠️  uvicorn not found. Installing..."
    if [ ! -z "$VENV_PATH" ]; then
        "${VENV_PATH}pip" install uvicorn[standard]
        cd "$PROJECT_ROOT"
        "${VENV_PATH}uvicorn" services.confluence-hub.main:app --host 0.0.0.0 --port 5070 --reload
    else
        pip install uvicorn[standard]
        cd "$PROJECT_ROOT"
        uvicorn services.confluence-hub.main:app --host 0.0.0.0 --port 5070 --reload
    fi
fi