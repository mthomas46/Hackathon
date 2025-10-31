# Ecosystem MCP Audit Script - Usage Guide

## Overview

The `audit_and_ingest.py` script provides comprehensive auditing and testing capabilities for the ecosystem-mcp service, including:

- Service health checks and API endpoint inventory
- Batch document ingestion with progress tracking
- RAG query performance testing with metrics
- Comprehensive report generation (JSON + Markdown)

## Installation

Ensure you have the required dependencies:

```bash
pip install httpx
```

## Quick Start

### Basic Audit (No Ingestion)

Test the service with existing documents:

```bash
python3 audit_and_ingest.py --skip-ingestion
```

### Full Audit with Ingestion

Ingest documents and test RAG queries:

```bash
python3 audit_and_ingest.py \
  --batch-size 10 \
  --output-dir ./audit_results
```

### Fast Test (Limited Queries)

Quick sanity check with just 3 queries:

```bash
python3 audit_and_ingest.py \
  --skip-ingestion \
  --max-queries 3 \
  --query-timeout 30
```

## Command-Line Options

### Core Options

| Option | Default | Description |
|--------|---------|-------------|
| `--base-url` | `http://localhost:8000` | Service URL |
| `--output-dir` | `./audit_results` | Report output directory |
| `--repo-path` | `../ecosystem-mcp` | Repository path for ingestion |

### Ingestion Options

| Option | Default | Description |
|--------|---------|-------------|
| `--batch-size` | `10` | Documents per batch |
| `--skip-ingestion` | `False` | Skip document ingestion |
| `--no-wait` | `False` | Don't wait for ingestion completion |

### Query Options

| Option | Default | Description |
|--------|---------|-------------|
| `--skip-queries` | `False` | Skip RAG queries |
| `--max-queries` | `10` | Maximum queries to run |
| `--query-timeout` | `60` | Timeout per query (seconds) |

## Usage Examples

### 1. Production Health Check

Quick check without any ingestion or long queries:

```bash
python3 audit_and_ingest.py \
  --base-url https://api.example.com \
  --skip-ingestion \
  --max-queries 5 \
  --query-timeout 30 \
  --output-dir ./prod_check
```

**Use Case**: Quick production health verification  
**Duration**: ~2-3 minutes  
**Output**: Service health, 5 fast RAG queries

### 2. Performance Benchmarking

Full RAG query performance test:

```bash
python3 audit_and_ingest.py \
  --skip-ingestion \
  --query-timeout 120 \
  --output-dir ./performance_$(date +%Y%m%d)
```

**Use Case**: Measure RAG query latency and quality  
**Duration**: ~10-15 minutes (10 queries)  
**Output**: Detailed latency metrics, confidence scores

### 3. Ingestion Testing

Test document ingestion pipeline:

```bash
python3 audit_and_ingest.py \
  --repo-path /path/to/docs \
  --batch-size 20 \
  --no-wait \
  --skip-queries \
  --output-dir ./ingestion_test
```

**Use Case**: Test ingestion with custom document set  
**Duration**: ~5 minutes (async jobs)  
**Output**: Ingestion job IDs, batch metrics

### 4. Continuous Integration

Automated testing in CI/CD:

```bash
#!/bin/bash
set -e

# Start service (assume it's in docker-compose)
docker-compose up -d ecosystem-mcp

# Wait for service to be healthy
timeout 60 bash -c 'until curl -f http://localhost:8000/health; do sleep 2; done'

# Run audit
python3 audit_and_ingest.py \
  --skip-ingestion \
  --max-queries 5 \
  --query-timeout 30 \
  --output-dir ./ci_results

# Check results
if [ $? -eq 0 ]; then
  echo "✅ Audit passed"
  exit 0
else
  echo "❌ Audit failed"
  exit 1
fi
```

**Use Case**: CI/CD pipeline integration  
**Duration**: ~3-4 minutes  
**Output**: Pass/fail + audit reports

### 5. Development Testing

Quick iteration during development:

```bash
python3 audit_and_ingest.py \
  --skip-ingestion \
  --max-queries 3 \
  --query-timeout 20 \
  --output-dir /tmp/dev_test
```

**Use Case**: Rapid testing during development  
**Duration**: ~1-2 minutes  
**Output**: Quick sanity check

### 6. Load Testing Preparation

Collect baseline metrics:

```bash
# Run multiple times to get averages
for i in {1..5}; do
  python3 audit_and_ingest.py \
    --skip-ingestion \
    --output-dir ./baseline_run_$i
  sleep 60  # Cool-down between runs
done
```

**Use Case**: Establish performance baselines  
**Duration**: ~50 minutes (5 runs)  
**Output**: Multiple metric sets for averaging

## Understanding the Output

### Console Output

The script provides real-time feedback:

```
================================================================================
ECOSYSTEM MCP SERVICE AUDIT
================================================================================

🔍 Checking service health...
   Status: healthy

🔍 Getting service information...
   Service: ecosystem-mcp
   Version: 0.1.0

================================================================================
RAG QUERY PERFORMANCE TESTING
================================================================================

📊 Running 10 test queries...

────────────────────────────────────────────────────────────────────────────────
Query 1/10
────────────────────────────────────────────────────────────────────────────────
❓ Question: What is ecosystem-mcp and what does it do?
⏱️  Timeout: 60s

   ⏳ Processing....... [5s]....... [10s]....... [15s]

✅ Answer (1120 chars, 18.5s):
   Based on the provided text, ecosystem-mcp is a system...

📚 Sources: 10
🎯 Confidence: 0.87
```

### Progress Indicators

- **Dots (`.`)**: Processing continues (every 1 second)
- **Time markers (`[5s]`)**: Elapsed time (every 5 seconds)
- **Timeout warning**: When approaching timeout limit

### Report Files

Two files are generated in the output directory:

#### 1. JSON Report (`audit_report_YYYYMMDD_HHMMSS.json`)

Complete structured data:

```json
{
  "audit_timestamp": "20251012_194558",
  "service_audit": { ... },
  "ingestion_summary": { ... },
  "query_summary": {
    "total_queries": 10,
    "successful_queries": 9,
    "failed_queries": 1,
    "average_query_duration": 22.28,
    "average_confidence": 0.84
  },
  "query_metrics": [ ... ]
}
```

#### 2. Markdown Summary (`audit_summary_YYYYMMDD_HHMMSS.md`)

Human-readable report with tables and charts.

## Timeout Protection

### Query Timeouts

Each RAG query has an individual timeout (default: 60s):

```bash
--query-timeout 30  # 30 second limit per query
```

**When a query times out:**
- ⏱️ Marked as failed with timeout error
- Partial results saved
- Next query proceeds normally

### Ingestion Timeouts

Job completion wait has a 300-second timeout:

```bash
--no-wait  # Skip waiting entirely
```

**When ingestion times out:**
- Job continues in background
- Audit proceeds to queries
- Job status available via API

## Interrupting the Audit

Press `Ctrl+C` to interrupt at any time:

```
^C
⚠️ Audit interrupted by user

📊 Partial results collected:
   Ingestion batches: 3
   RAG queries: 5

💾 Saving partial results to ./audit_results...
✅ Partial results saved
```

**Behavior:**
- Saves all collected metrics
- Generates partial report
- Exits gracefully

## Troubleshooting

### Issue: Queries Taking Too Long

**Solution 1**: Reduce timeout
```bash
--query-timeout 30
```

**Solution 2**: Limit queries
```bash
--max-queries 3
```

**Solution 3**: Check Ollama
```bash
curl http://localhost:11434/api/tags
```

### Issue: Service Not Responding

**Check service health:**
```bash
curl http://localhost:8000/health
```

**Check service logs:**
```bash
docker-compose logs ecosystem-mcp
```

**Verify network:**
```bash
--base-url http://localhost:8000
```

### Issue: Ingestion Failures

**Check git repository:**
```bash
cd /path/to/repo && git status
```

**Try smaller batch:**
```bash
--batch-size 5
```

**Check job status:**
```bash
curl http://localhost:8000/api/v1/admin/ingest/status
```

### Issue: Out of Memory

**Reduce concurrent operations:**
```bash
--batch-size 5 \
--max-queries 3
```

**Skip ingestion:**
```bash
--skip-ingestion
```

## Integration Examples

### Grafana Dashboard

Parse JSON output for time-series metrics:

```bash
#!/bin/bash
# Run audit and post to Grafana
python3 audit_and_ingest.py --skip-ingestion --output-dir ./metrics

# Extract metrics
jq '.query_summary.average_query_duration' ./metrics/audit_report_*.json

# Post to Prometheus pushgateway
# ... (custom integration)
```

### Slack Notifications

Send results to Slack:

```bash
#!/bin/bash
python3 audit_and_ingest.py --skip-ingestion --output-dir ./results

# Parse results
SUCCESS_RATE=$(jq '.query_summary.success_rate' ./results/audit_report_*.json)

# Send to Slack
curl -X POST https://hooks.slack.com/services/YOUR/WEBHOOK/URL \
  -H 'Content-Type: application/json' \
  -d "{\"text\": \"Audit complete: ${SUCCESS_RATE}% success rate\"}"
```

### Database Logging

Store metrics in database:

```python
import json
import psycopg2

# Load results
with open('audit_report_*.json') as f:
    data = json.load(f)

# Insert into database
conn = psycopg2.connect(...)
cursor = conn.cursor()
cursor.execute(
    "INSERT INTO audit_metrics (timestamp, success_rate, avg_duration) VALUES (%s, %s, %s)",
    (data['audit_timestamp'], data['query_summary']['success_rate'], data['query_summary']['average_query_duration'])
)
conn.commit()
```

## Advanced Configuration

### Custom Test Queries

Modify the script to add your own queries:

```python
self.test_queries = [
    "Your custom question 1?",
    "Your custom question 2?",
    # ... more questions
]
```

### Custom Metrics

Add custom metrics to the `QueryMetrics` dataclass:

```python
@dataclass
class QueryMetrics:
    # ... existing fields ...
    custom_metric: float = 0.0
```

## Best Practices

1. **Start Small**: Use `--max-queries 3` for initial testing
2. **Set Realistic Timeouts**: RAG queries can take 20-40s with large models
3. **Monitor Progress**: Watch for timeout patterns
4. **Save Results**: Always specify `--output-dir`
5. **Test Incrementally**: Skip ingestion when testing queries
6. **Use CI/CD**: Integrate into automated testing pipelines
7. **Track Trends**: Run regularly and compare metrics over time

## Performance Expectations

### Typical Query Times

| Model Size | Avg Duration | Range |
|------------|--------------|-------|
| Small (3B) | 15-20s | 10-30s |
| Medium (7B) | 30-45s | 20-60s |
| Large (13B+) | 60-90s | 45-120s |

### Typical Confidence Scores

| Range | Interpretation |
|-------|----------------|
| 0.9-1.0 | Excellent - High confidence |
| 0.7-0.9 | Good - Reliable answer |
| 0.5-0.7 | Fair - Verify answer |
| 0.0-0.5 | Poor - Insufficient context |

## Support

For issues or questions:

1. Check service logs: `docker-compose logs ecosystem-mcp`
2. Review audit reports in output directory
3. Verify service health: `curl http://localhost:8000/health`
4. Check documentation: `curl http://localhost:8000/docs`

---

**Last Updated**: October 12, 2025  
**Script Version**: 1.1 (with timeout protection)  
**Compatible with**: ecosystem-mcp v0.1.0+

