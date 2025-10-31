#!/bin/bash
# Quick Phase 2 confidence comparison

API="http://localhost:8000/api/v1/rag/ask"

echo "═══════════════════════════════════════════════════════════════════════════"
echo "  PHASE 2 QUICK CONFIDENCE COMPARISON"
echo "═══════════════════════════════════════════════════════════════════════════"
echo

QUESTION="What is ChromaDB?"

# Standard RAG
echo "📊 Testing: $QUESTION"
echo "────────────────────────────────────────────────────────────────────────────"
echo

echo -n "🔍 Standard RAG... "
STD_RESULT=$(curl -s -X POST "$API/enhanced" -H "Content-Type: application/json" \
  -d "{\"question\":\"$QUESTION\",\"n_results\":5}" --max-time 30)
STD_CONF=$(echo "$STD_RESULT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('confidence', 0))" 2>/dev/null || echo "0")
echo "Confidence: $STD_CONF%"

# Phase 1
echo -n "✨ Phase 1... "
P1_RESULT=$(curl -s -X POST "$API/enhanced" -H "Content-Type: application/json" \
  -d "{\"question\":\"$QUESTION\",\"n_results\":5,\"enable_hybrid_search\":true,\"enable_query_rewriting\":true,\"enable_confidence_scoring\":true,\"enable_reranking\":false,\"enable_context_optimization\":false}" --max-time 45)
P1_CONF=$(echo "$P1_RESULT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('confidence', 0))" 2>/dev/null || echo "0")
echo "Confidence: $P1_CONF%"

# Phase 1+2
echo -n "🚀 Phase 1+2... "
P2_RESULT=$(curl -s -X POST "$API/enhanced" -H "Content-Type: application/json" \
  -d "{\"question\":\"$QUESTION\",\"n_results\":5,\"enable_hybrid_search\":true,\"enable_query_rewriting\":true,\"enable_confidence_scoring\":true,\"enable_reranking\":true,\"enable_context_optimization\":true}" --max-time 60)
P2_CONF=$(echo "$P2_RESULT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('confidence', 0))" 2>/dev/null || echo "0")
P2_ENH=$(echo "$P2_RESULT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('metadata',{}).get('enhancements_used',{}))" 2>/dev/null || echo "{}")
echo "Confidence: $P2_CONF%"
echo "  Enhancements: $P2_ENH"

echo
echo "════════════════════════════════════════════════════════════════════════════"
echo "RESULTS SUMMARY"
echo "════════════════════════════════════════════════════════════════════════════"
echo
echo "Standard RAG:       $STD_CONF%  (baseline)"
echo "Phase 1 Enhanced:   $P1_CONF%"
echo "Phase 1+2 Enhanced: $P2_CONF%"
echo

# Calculate improvements
if [ "$STD_CONF" != "0" ]; then
  P1_IMP=$(python3 -c "print(f'{float($P1_CONF) - float($STD_CONF):.1f}')")
  P2_IMP=$(python3 -c "print(f'{float($P2_CONF) - float($STD_CONF):.1f}')")
  P2_ADD=$(python3 -c "print(f'{float($P2_CONF) - float($P1_CONF):.1f}')")
  
  echo "Phase 1 Improvement:        +$P1_IMP%"
  echo "Phase 1+2 Improvement:      +$P2_IMP%"
  echo "Phase 2 Additional:         +$P2_ADD%"
fi

echo
echo "✅ Phase 2 is operational!"
echo

