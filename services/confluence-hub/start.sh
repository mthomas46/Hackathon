#!/bin/bash

# Confluence Hub Service Startup Script
# This script helps you start the service with all dependencies

set -e

echo "🚀 Starting Confluence Hub Service"
echo "=================================="

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
    if ! pgrep -x "mongod" > /dev/null; then
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

# Install dependencies if needed
if [ ! -d "venv" ] && [ ! -f "requirements.txt" ]; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
fi

# Start the service
echo "🎯 Starting Confluence Hub Service on port 5070..."
echo "   Health endpoint: http://localhost:5070/health"
echo "   API docs: http://localhost:5070/docs"
echo ""

# Export environment variables for the Python process
export ConfluenceBaseUrl
export ConfluenceUsername
export ConfluenceApiToken
export MongoConnectionString

# Start with uvicorn if available, otherwise give instructions
if command -v uvicorn &> /dev/null; then
    uvicorn main:app --host 0.0.0.0 --port 5070 --reload
else
    echo "⚠️  uvicorn not found. Installing..."
    pip install uvicorn[standard]
    uvicorn main:app --host 0.0.0.0 --port 5070 --reload
fi