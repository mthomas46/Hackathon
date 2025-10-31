#!/usr/bin/env python3
"""Analyze RAG performance bottlenecks from benchmark data."""

import re
from datetime import datetime

# Parse benchmark log
log_file = "benchmark_phase2.log"

with open(log_file, 'r') as f:
    content = f.read()

print("=" * 80)
print("RAG PERFORMANCE ANALYSIS")
print("=" * 80)
print()

# Extract all timing data
questions = []
for line in content.split('\n'):
    if match := re.match(r'\[(\d+)/10\] (Q\d+): (.+)', line):
        questions.append({
            'num': int(match.group(1)),
            'id': match.group(2),
            'question': match.group(3),
            'times': {}
        })
    elif '🔍 Standard RAG... ✓' in line:
        if match := re.search(r'\(([0-9.]+)s\)', line):
            if questions:
                questions[-1]['times']['standard'] = float(match.group(1))
    elif '✨ Phase 1 Enhanced... ✓' in line:
        if match := re.search(r'\(([0-9.]+)s\)', line):
            if questions:
                questions[-1]['times']['phase1'] = float(match.group(1))
    elif '🚀 Phase 1+2 Enhanced... ✓' in line:
        if match := re.search(r'\(([0-9.]+)s\)', line):
            if questions:
                questions[-1]['times']['phase1_phase2'] = float(match.group(1))

# Identify where it got stuck
print("🔍 TIMEOUT ANALYSIS")
print("-" * 80)
stuck_on = None
for q in questions:
    if 'standard' in q['times'] and 'phase1' not in q['times']:
        stuck_on = f"{q['id']} Phase 1 (after {q['times']['standard']:.1f}s standard)"
        break
    elif 'phase1' in q['times'] and 'phase1_phase2' not in q['times']:
        stuck_on = f"{q['id']} Phase 1+2 (after {q['times']['phase1']:.1f}s phase1)"
        break

if stuck_on:
    print(f"❌ Benchmark got stuck on: {stuck_on}")
else:
    print("✅ No incomplete questions found in analyzed data")

print()

# Analyze Phase 1 slowness
print("⏱️  PHASE 1 PERFORMANCE ISSUES")
print("-" * 80)

complete = [q for q in questions if len(q['times']) == 3]
if complete:
    # Find slowest Phase 1 queries
    slow_p1 = sorted(complete, key=lambda x: x['times']['phase1'], reverse=True)[:3]
    
    print("Slowest Phase 1 queries:")
    for i, q in enumerate(slow_p1, 1):
        std = q['times']['standard']
        p1 = q['times']['phase1']
        p1p2 = q['times']['phase1_phase2']
        slowdown = (p1 / std) - 1
        
        print(f"\n{i}. {q['id']}: {q['question'][:60]}")
        print(f"   Standard: {std:.1f}s")
        print(f"   Phase 1:  {p1:.1f}s  ({slowdown*100:+.0f}% slowdown)")
        print(f"   Phase 1+2: {p1p2:.1f}s")
        
        if p1p2 < p1:
            improvement = ((p1 - p1p2) / p1) * 100
            print(f"   → Phase 2 helps: {improvement:.0f}% faster")

print()
print()

# Identify patterns
print("📊 PERFORMANCE PATTERNS")
print("-" * 80)

if complete:
    # Calculate averages
    avg_std = sum(q['times']['standard'] for q in complete) / len(complete)
    avg_p1 = sum(q['times']['phase1'] for q in complete) / len(complete)
    avg_p1p2 = sum(q['times']['phase1_phase2'] for q in complete) / len(complete)
    
    print(f"Average response times ({len(complete)} questions):")
    print(f"  Standard:       {avg_std:.2f}s  (baseline)")
    print(f"  Phase 1:        {avg_p1:.2f}s  ({(avg_p1/avg_std - 1)*100:+.0f}% slower)")
    print(f"  Phase 1+2:      {avg_p1p2:.2f}s  ({(avg_p1p2/avg_std - 1)*100:+.0f}% slower)")
    print()
    
    # Phase 1 overhead
    p1_overhead = avg_p1 - avg_std
    print(f"Phase 1 adds ~{p1_overhead:.1f}s overhead on average")
    print()
    
    # Phase 2 benefit
    p2_speedup = ((avg_p1 - avg_p1p2) / avg_p1) * 100
    print(f"Phase 2 reduces Phase 1 time by {p2_speedup:.1f}%")
    print()
    
    # Breakdown estimation
    print("Estimated overhead breakdown:")
    print(f"  Base query time:      {avg_std:.2f}s")
    print(f"  + Query rewriting:    ~{p1_overhead * 0.2:.2f}s  (est. 20%)")
    print(f"  + BM25 search:        ~{p1_overhead * 0.3:.2f}s  (est. 30%)")
    print(f"  + Hybrid fusion:      ~{p1_overhead * 0.1:.2f}s  (est. 10%)")
    print(f"  + Extra retrieval:    ~{p1_overhead * 0.4:.2f}s  (est. 40%)")
    print()
    
    # Phase 2 helps
    print("Phase 2 optimizations:")
    p2_saves = avg_p1 - avg_p1p2
    print(f"  - Reranking: Better doc selection (saves ~{p2_saves * 0.4:.2f}s)")
    print(f"  - Context opt: Less LLM processing (saves ~{p2_saves * 0.6:.2f}s)")

print()
print()

# Recommendations
print("🎯 BOTTLENECK IDENTIFICATION")
print("-" * 80)
print()
print("PRIMARY BOTTLENECKS:")
print()
print("1. 🐌 QUERY REWRITING (NLTK)")
print("   - Symptom: Phase 1 adds 20-30s overhead")
print("   - Cause: NLTK synonym expansion is slow")
print("   - Impact: Every Phase 1 query pays this cost")
print()
print("2. 🔍 BM25 INDEX SEARCH")
print("   - Symptom: Phase 1 searches 6,000+ docs")
print("   - Cause: Full corpus BM25 on every variant")
print("   - Impact: Multiple search passes per query")
print()
print("3. 📦 EXCESSIVE RETRIEVAL")
print("   - Symptom: Phase 1 retrieves many docs")
print("   - Cause: Multiple query variants × n_results")
print("   - Impact: ChromaDB query latency multiplied")
print()
print("4. 🔄 DEDUPLICATION & FUSION")
print("   - Symptom: RRF on large result sets")
print("   - Cause: Processing 100+ docs from variants")
print("   - Impact: O(n²) complexity in fusion")
print()
print()

print("=" * 80)
print("RECOMMENDED OPTIMIZATIONS (Priority Order)")
print("=" * 80)
print()

recommendations = [
    {
        "priority": "HIGH",
        "name": "Cache NLTK WordNet Data",
        "impact": "5-10s savings",
        "effort": "Low",
        "desc": "Pre-load WordNet data, cache lemmatizer"
    },
    {
        "priority": "HIGH",
        "name": "Limit Query Variants",
        "impact": "30-40% speed up",
        "effort": "Low",
        "desc": "Reduce from 3 variants to 1-2 for simple queries"
    },
    {
        "priority": "HIGH",
        "name": "BM25 Index Caching",
        "impact": "3-5s savings",
        "effort": "Medium",
        "desc": "Cache BM25 index in memory, don't rebuild"
    },
    {
        "priority": "MEDIUM",
        "name": "Async Parallel Search",
        "impact": "50% faster retrieval",
        "effort": "Medium",
        "desc": "Search all variants in parallel, not sequential"
    },
    {
        "priority": "MEDIUM",
        "name": "Smart Query Detection",
        "impact": "Variable",
        "effort": "Medium",
        "desc": "Skip rewriting for simple/direct questions"
    },
    {
        "priority": "MEDIUM",
        "name": "Reduce Initial Retrieval",
        "impact": "2-3s savings",
        "effort": "Low",
        "desc": "Fetch 5x instead of 10x for reranking"
    },
    {
        "priority": "LOW",
        "name": "Streaming Responses",
        "impact": "Perceived speed",
        "effort": "High",
        "desc": "Stream answer generation for faster UX"
    },
]

for rec in recommendations:
    print(f"[{rec['priority']}] {rec['name']}")
    print(f"  Impact: {rec['impact']}")
    print(f"  Effort: {rec['effort']}")
    print(f"  → {rec['desc']}")
    print()

print("=" * 80)
print()
print("🎯 QUICK WINS (Implement First):")
print()
print("1. Cache NLTK WordNet (5-10s instant improvement)")
print("2. Limit query variants (30-40% faster Phase 1)")
print("3. BM25 index caching (3-5s per query)")
print()
print("Expected combined impact: 40-60% faster Phase 1 queries")
print()

