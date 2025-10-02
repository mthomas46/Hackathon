#!/bin/bash
# Start all services in the LLM Documentation Ecosystem

echo "🚀 Starting the Complete LLM Documentation Ecosystem..."
echo ""
echo "📋 Available profiles: all, core, ai_services, development, tooling, audit, simulation, production, utility, ci"
echo ""

# Use all profiles to ensure all services start
echo "🔄 Starting services with all profiles activated..."
docker-compose \
  -f docker-compose.dev.yml \
  --profile all \
  --profile core \
  --profile ai_services \
  --profile development \
  --profile tooling \
  --profile audit \
  --profile simulation \
  --profile production \
  --profile utility \
  --profile ci \
  up -d

echo ""
echo "✅ Services starting in background..."
echo ""
echo "📊 Check status with: docker-compose ps"
echo "📋 View logs with: docker-compose logs -f [service-name]"
echo "🛑 Stop all with: docker-compose down"
echo ""
echo "💡 Note: Services may take time to become healthy. Check health with: docker-compose ps"
