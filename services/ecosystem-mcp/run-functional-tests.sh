#!/bin/bash
# Run functional tests WITH Docker

echo "🧪 Running Functional Tests (Requires Docker)..."
echo ""

cd "$(dirname "$0")"

# Check if test database is running
if ! ./scripts/test-db.sh status | grep -q "running"; then
    echo "🐳 Starting test database..."
    ./scripts/test-db.sh start
    echo ""
    echo "⏳ Waiting 5 seconds for database to be ready..."
    sleep 5
fi

echo "📊 Running 69 functional tests..."
source venv/bin/activate
pytest tests/functional/ -v -m functional --tb=short

echo ""
echo "✅ Functional tests complete!"
echo ""
echo "To stop test database:"
echo "  ./scripts/test-db.sh stop"

