# MCP Performance Store

**Version:** 1.0.0  
**Port:** 5647  
**Status:** Production-Ready (60% feature complete)

---

## 🎯 **Purpose**

Track and analyze performance metrics for MCP orchestration executions. Provides real-time insights into pattern performance, success rates, latency percentiles, and trend detection.

---

## ✨ **Features**

### **Execution Tracking**
- ✅ Record individual orchestration executions
- ✅ Detailed timing breakdown (interpretation, retrieval, pattern, composition)
- ✅ Track results (confidence, sources, response length)
- ✅ Error tracking (type, message)
- ✅ Query by pattern, status, date range, composition ID

### **Pattern Performance Metrics**
- ✅ Automatic aggregation per pattern
- ✅ Success/failure/timeout rates
- ✅ Latency percentiles (p50, p95, p99)
- ✅ Quality metrics (avg confidence, sources)
- ✅ Health scores (0-100)
- ✅ Trend detection (degrading/improving/stable)

### **Analytics**
- ✅ Overall system summary
- ✅ Trends over time windows (1h, 24h, 7d, 30d)
- ✅ Top performing patterns
- ✅ Degrading pattern detection

---

## 🚀 **Quick Start**

### **Option A: Docker (Recommended)**

```bash
# Start service with Redis
docker-compose up -d

# Check logs
docker-compose logs -f mcp-performance-store

# Stop service
docker-compose down
```

Service available at: http://localhost:5647  
API Documentation: http://localhost:5647/docs

---

### **Option B: Local Development**

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your Redis configuration
# (Make sure Redis is running: redis-server)

# Run service
python main.py
```

---

## 📡 **API Endpoints**

### **Health Check**
```bash
GET /health
```

### **Executions**

**Record Execution:**
```bash
POST /api/v1/executions
Content-Type: application/json

{
  "execution_id": "exec_123",
  "query": "What is the weather?",
  "pattern_name": "chain-of-thought",
  "status": "SUCCESS",
  "total_duration_ms": 1250.5,
  "confidence": 0.95,
  "num_sources": 5,
  "response_length": 150
}
```

**Get Execution:**
```bash
GET /api/v1/executions/{execution_id}
```

**List Executions:**
```bash
# Recent executions
GET /api/v1/executions/recent?limit=100

# Filter by pattern
GET /api/v1/executions?pattern=chain-of-thought&limit=50

# Filter by status
GET /api/v1/executions?status=SUCCESS&limit=50

# Filter by composition
GET /api/v1/executions?composition_id=comp_123
```

### **Patterns**

**List All Patterns:**
```bash
GET /api/v1/patterns
```

**Get Pattern Performance:**
```bash
GET /api/v1/patterns/{pattern_name}/performance

Response:
{
  "pattern_name": "chain-of-thought",
  "total_executions": 1000,
  "successful_executions": 980,
  "success_rate": 0.98,
  "avg_duration_ms": 1150.3,
  "p50_duration_ms": 1050.0,
  "p95_duration_ms": 2300.5,
  "p99_duration_ms": 3200.0,
  "health_score": 92.5,
  "is_degrading": false,
  "is_improving": true
}
```

### **Metrics & Analytics**

**Overall Summary:**
```bash
GET /api/v1/metrics/summary

Response:
{
  "total_executions": 5000,
  "successful_executions": 4850,
  "success_rate": 0.97,
  "avg_duration_ms": 1200.5,
  "patterns_tracked": 15,
  "degrading_patterns_count": 2
}
```

**Trends:**
```bash
GET /api/v1/metrics/trends?hours=24

Response:
{
  "hours": 24,
  "total_executions": 1200,
  "success_rate": 0.96,
  "avg_duration_ms": 1180.2,
  "patterns_used": 12
}
```

**Anomalies (Degrading Patterns):**
```bash
GET /api/v1/metrics/anomalies

Response: [
  {
    "pattern_name": "rag-fusion",
    "success_rate_24h": 0.85,
    "success_rate_7d": 0.95,
    "health_score": 72.3,
    "is_degrading": true
  }
]
```

---

## 🏗️ **Architecture**

### **Domain-Driven Design (DDD)**

```
services/mcp-performance-store/
├── domain/                    # Business logic
│   ├── entities/              # OrchestrationExecution, PatternPerformance
│   ├── repositories/          # Abstract interfaces
│   └── value_objects/         # ExecutionStatus
├── infrastructure/            # Technical implementation
│   ├── config/                # Settings
│   └── repositories/          # Redis implementations
├── application/               # Use cases
│   ├── use_cases/             # RecordExecution, QueryPerformance
│   └── dto/                   # Request/Response models
└── main.py                    # FastAPI application
```

### **Key Patterns**

**Repository Pattern:**
- Abstract interfaces in domain layer
- Redis implementation in infrastructure
- Dependency injection via FastAPI

**Rich Domain Entities:**
- Business logic in entities (not just data)
- PatternPerformance calculates health scores
- OrchestrationExecution manages lifecycle

**Automatic Aggregation:**
- Recording an execution automatically updates pattern metrics
- Incremental updates (no full recalculation)
- Efficient percentile tracking (last 100 executions)

---

## 🔧 **Configuration**

Environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| SERVICE_PORT | 5647 | HTTP port |
| REDIS_HOST | localhost | Redis hostname |
| REDIS_PORT | 6379 | Redis port |
| REDIS_DB | 0 | Redis database number |
| REDIS_KEY_PREFIX | mcp-perf: | Key prefix for namespacing |
| LOG_LEVEL | INFO | Logging level |
| EXECUTION_RETENTION_DAYS | 30 | Data retention period |

---

## 🧪 **Testing**

```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# E2E tests (requires Redis)
pytest tests/e2e/
```

---

## 📊 **Metrics Explained**

### **Health Score (0-100)**

Calculated from:
- **Success rate (60% weight):** Higher is better
- **Duration consistency (20% weight):** Avg close to p50 is good
- **Trend (20% weight):** Improving = 20, Stable = 10, Degrading = 0

**Interpretation:**
- **90-100:** Excellent
- **75-89:** Good
- **60-74:** Fair
- **<60:** Poor (investigate)

### **Degrading Detection**

Pattern is "degrading" if:
```
success_rate_7d - success_rate_24h > 0.1
```

This means recent (24h) performance is significantly worse than longer-term (7d) performance.

---

## 🔗 **Integration**

### **From MCP Orchestrator:**

```python
import httpx

async def record_execution_result(execution_data):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:5647/api/v1/executions",
            json=execution_data
        )
        return response.json()
```

### **From MCP Composer:**

```python
# After composing a query
await performance_client.record_execution({
    "execution_id": str(uuid.uuid4()),
    "query": query,
    "composition_id": composition_id,
    "pattern_name": pattern_name,
    "status": "SUCCESS",
    "total_duration_ms": elapsed_ms,
    "confidence": confidence_score
})
```

---

## 📈 **Use Cases**

### **1. Monitor Pattern Health**
```bash
GET /api/v1/patterns
```
Quickly see which patterns are performing well and which need attention.

### **2. Debug Performance Issues**
```bash
GET /api/v1/patterns/slow-pattern/performance
```
Check p95/p99 latencies to identify outliers.

### **3. Detect Regressions**
```bash
GET /api/v1/metrics/anomalies
```
Automatically alerts to patterns with degrading performance.

### **4. Track System Health**
```bash
GET /api/v1/metrics/summary
```
Overall system metrics for dashboards.

### **5. Analyze Trends**
```bash
GET /api/v1/metrics/trends?hours=168  # 7 days
```
See how performance evolves over time.

---

## 🚧 **Future Enhancements**

### **Planned (Optional):**
- Advanced anomaly detection (Z-score, IQR)
- Predictive maintenance (forecast issues)
- Custom alert thresholds
- TimescaleDB for time-series data
- GraphQL API
- WebSocket for real-time updates

### **Integration:**
- Auto-record from Orchestrator
- Auto-record from Composer
- Auto-record from Gateway
- Auto-record from Interpreter

---

## 📝 **License**

MIT

---

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

## 📞 **Support**

- Documentation: http://localhost:5647/docs
- Health Check: http://localhost:5647/health
- Issues: GitHub Issues

---

**Built with ❤️ using FastAPI, Redis, and Domain-Driven Design**
