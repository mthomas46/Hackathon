---
title: "Circuit Breaker for Documentation Generation"
service: "ecosystem-mcp"
category: "architecture"
tags: ['architecture', 'design', 'health', 'monitoring', 'rag', 'retrieval', 'system', 'test', 'testing']
related: ['INDEX.md', 'architecture/OVERVIEW.md', 'CODE_REFERENCE.md', 'API_ENDPOINTS_COMPLETE.md']
status: "current"
last_updated: "2025-10-28"
audience: "developer"
difficulty: "beginner"
semantic_keywords: ['architecture', 'design', 'health', 'monitoring', 'rag']
llm_search_hints: ['what is circuit breaker for documentation generation', 'how does circuit breaker for documentation generation work', 'guide to circuit breaker for documentation generation']
---

# Circuit Breaker for Documentation Generation

## Overview

The documentation generator now includes a **signal file circuit breaker** that allows graceful cancellation of active generation runs.

## How It Works

1. **Detection**: Generator checks for `.stop_generation` file before each RAG query
2. **Graceful Stop**: If file exists, raises `KeyboardInterrupt`
3. **Cleanup**: Existing KeyboardInterrupt handler:
   - Saves partial results
   - Generates metrics report
   - Cleans up resources

## Usage

### Stop Active Generation

**Method 1: Use the script (Recommended)**
```bash
cd /Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp
./stop_generation.sh
```

**Method 2: Manual**
```bash
cd /Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp
touch .stop_generation
```

### Resume Generation

Remove the signal file:
```bash
rm .stop_generation
```

Then run the generator again:
```bash
python3 generate_deep_docs.py
```

## Behavior

### When Stop Signal is Detected

```
🛑 STOP SIGNAL DETECTED - Cancelling generation...

⚠️  Generation cancelled by user
   Partial results may be available in: generated_docs_deep
   
█████████████████████████████████████████████████████████
GENERATING METRICS REPORT
█████████████████████████████████████████████████████████

✅ Saved raw metrics: generated_docs_deep/metrics/generation_metrics.json
✅ Saved metrics report: generated_docs_deep/metrics/generation_report.md
...
```

### What Gets Saved

Even when cancelled:
- ✅ All completed sections
- ✅ Partial metrics up to cancellation point
- ✅ Comprehensive metrics report
- ✅ Per-section query logs
- ✅ CSV summary

## Comparison with Other Methods

| Method | Graceful? | Metrics? | Cleanup? | Speed |
|--------|-----------|----------|----------|-------|
| **Signal File** | ✅ Yes | ✅ Yes | ✅ Yes | ~1 query time |
| `pkill -INT` | ✅ Yes | ✅ Yes | ✅ Yes | Immediate |
| `pkill -KILL` | ❌ No | ❌ No | ❌ No | Immediate |
| Ctrl+C (interactive) | ✅ Yes | ✅ Yes | ✅ Yes | Immediate |

## Examples

### Scenario 1: Generation Taking Too Long

```bash
# Start generation
python3 generate_deep_docs.py &

# ... wait some time ...

# Decide to stop
./stop_generation.sh

# Check metrics
cat generated_docs_deep/metrics/generation_report.md
```

### Scenario 2: Repeated Errors

```bash
# Generation running but seeing errors
# (like the 422 synthesis errors)

./stop_generation.sh

# Fix issues, then restart
rm .stop_generation
python3 generate_deep_docs.py
```

### Scenario 3: Testing

```bash
# Quick test run
python3 generate_deep_docs.py &

# Let it run for 1-2 sections
sleep 300

# Stop and check output
./stop_generation.sh
```

## Integration with Metrics

The circuit breaker integrates seamlessly with metrics:

```python
try:
    # Generation runs...
    await generator.generate()
    
except KeyboardInterrupt:
    print("\n⚠️ Generation cancelled by user")
    # Metrics are still generated!
    await self.generate_metrics_report()
```

**Result**: Full metrics report even for partial runs

## Preventing New Runs

Leave `.stop_generation` file in place:

```bash
# Stop current and prevent new
./stop_generation.sh

# Any new attempt will immediately stop
python3 generate_deep_docs.py
# → 🛑 STOP SIGNAL DETECTED - Cancelling generation...
```

## Monitoring

Check if signal file exists:
```bash
ls -la .stop_generation 2>/dev/null && echo "🛑 Stop signal active" || echo "✅ Ready to generate"
```

Check for active generation:
```bash
ps aux | grep "[p]ython3 generate_deep_docs.py"
```

## Advanced: Custom Signal Handling

You can also use OS signals:

```bash
# Graceful (generates metrics)
pkill -INT -f "generate_deep_docs.py"

# By PID (more precise)
kill -INT <PID>

# Force kill (no cleanup - NOT RECOMMENDED)
pkill -KILL -f "generate_deep_docs.py"
```

## Files Created

```
.stop_generation           # Signal file (transient)
stop_generation.sh         # Circuit breaker script
generated_docs_deep/       # Output directory
  ├── metrics/            # Metrics (even for partial runs)
  │   ├── generation_report.md
  │   ├── generation_metrics.json
  │   └── *_queries.json
  └── *.md               # Completed sections
```

## Best Practices

1. **Use the script**: `./stop_generation.sh` handles everything
2. **Check metrics**: Always review the report after stopping
3. **Clean up**: Remove `.stop_generation` before next run
4. **Monitor**: Check process status before stopping
5. **Be patient**: Wait ~30s for graceful shutdown

## Troubleshooting

### Signal file exists but generation won't stop

```bash
# Check if actually running
ps aux | grep generate_deep_docs

# Force stop if needed
pkill -INT -f generate_deep_docs.py

# Wait 10s, then if still running
pkill -KILL -f generate_deep_docs.py
```

### Can't create signal file

```bash
# Check permissions
ls -ld .
# Should be writable by you

# Try with explicit path
touch /Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp/.stop_generation
```

### Metrics not generated on stop

```bash
# Check for Python errors
tail -50 logs/mcp.log

# Manually generate from saved state
# (Future enhancement)
```

## Future Enhancements

Potential improvements:
- [ ] API endpoint: `POST /api/v1/generation/cancel`
- [ ] Job tracking: Multiple concurrent generations
- [ ] Progress API: `GET /api/v1/generation/status`
- [ ] Auto-resume: Continue from last completed section
- [ ] Timeout: Auto-stop after N minutes
- [ ] Resource limits: Stop if memory/CPU too high

## Summary

✅ **Simple**: Just create a file  
✅ **Graceful**: Full cleanup and metrics  
✅ **Fast**: Stops at next query (~20s)  
✅ **Safe**: No data loss  
✅ **Integrated**: Works with existing handlers  

The circuit breaker provides a clean, safe way to stop long-running documentation generation while preserving all metrics and partial results.

