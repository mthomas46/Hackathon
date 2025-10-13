#!/bin/bash
#
# Circuit Breaker for Documentation Generation
# Creates a signal file to gracefully stop active generation
#

cd "$(dirname "$0")"

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║        🛑 STOPPING DOCUMENTATION GENERATION 🛑                ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Create stop signal file
touch .stop_generation
echo "✅ Stop signal created: .stop_generation"
echo ""

# Check if process is running
if pgrep -f "generate_deep_docs.py" > /dev/null; then
    echo "📊 Active generation detected:"
    ps aux | grep "[p]ython3 generate_deep_docs.py" | awk '{print "   PID:", $2, "| Memory:", $6/1024"MB"}'
    echo ""
    echo "⏳ Waiting for graceful shutdown..."
    echo "   (Generator will stop at next query)"
    echo ""
    echo "💡 If it doesn't stop in 30s, run:"
    echo "   pkill -INT -f generate_deep_docs.py"
else
    echo "ℹ️  No active generation found"
    echo "   (Signal file created for prevention)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "To resume generation later, remove the signal file:"
echo "   rm .stop_generation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

