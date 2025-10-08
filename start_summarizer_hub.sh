#!/bin/bash
# Start summarizer-hub service for hierarchical topic extraction

echo "🚀 Starting summarizer-hub service..."

cd "$(dirname "$0")"

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose not found. Please install Docker Compose."
    exit 1
fi

# Start summarizer-hub service
docker-compose -f docker-compose-mcp-ecosystem.yml up -d summarizer-hub

# Wait for service to be healthy
echo "⏳ Waiting for summarizer-hub to be healthy..."
for i in {1..30}; do
    if curl -f http://localhost:5160/health &> /dev/null || curl -f http://localhost:5160/api/health &> /dev/null; then
        echo "✅ Summarizer-hub is healthy!"
        exit 0
    fi
    echo "   Attempt $i/30..."
    sleep 2
done

echo "⚠️  Summarizer-hub may not be fully ready, but container is running."
echo "   Check logs with: docker-compose -f docker-compose-mcp-ecosystem.yml logs summarizer-hub"
exit 0

