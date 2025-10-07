# 🎯 Phase 3.5 Incremental Completion Plan

**Approach:** Complete Performance Store fully first, then move to MCP Store  
**Timeline:** ~15-20 hours total (4-6 hour sessions)  
**Current Status:** Foundation started (5% complete)

---

## 📊 **Phase 3.5 Overview**

### **Two Services to Build:**

1. **MCP Performance Store** (Port 5647)
   - Purpose: Track performance metrics across all MCP operations
   - Estimated LOC: ~2,100
   - Current: 196 LOC (9%)
   - Remaining: ~1,904 LOC (91%)

2. **MCP Store** (Port 5648)
   - Purpose: Versioned storage for MCP packages
   - Estimated LOC: ~2,300
   - Current: 0 LOC (0%)
   - Remaining: ~2,300 LOC (100%)

---

## 🚀 **SESSION 1: Performance Store Foundation** (4-6 hours)

### **Goal:** Complete domain + infrastructure layers

### **Tasks:**

#### **Task 1.1: PatternPerformance Entity** (~150 LOC)
**File:** `services/mcp-performance-store/domain/entities/pattern_performance.py`

**Purpose:** Aggregate performance metrics per pattern

**Attributes:**
```python
@dataclass
class PatternPerformance:
    pattern_name: str
    
    # Counts
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    timeout_executions: int = 0
    
    # Timing metrics (milliseconds)
    avg_duration_ms: float = 0.0
    min_duration_ms: float = 0.0
    max_duration_ms: float = 0.0
    p50_duration_ms: float = 0.0
    p95_duration_ms: float = 0.0
    p99_duration_ms: float = 0.0
    
    # Quality metrics
    avg_confidence: float = 0.0
    avg_sources: float = 0.0
    
    # Trend data (last 24h, 7d, 30d)
    executions_24h: int = 0
    executions_7d: int = 0
    executions_30d: int = 0
    success_rate_24h: float = 0.0
    success_rate_7d: float = 0.0
    success_rate_30d: float = 0.0
    
    # Metadata
    first_seen: datetime
    last_updated: datetime
    
    # Methods
    def update_from_execution(self, execution: OrchestrationExecution)
    def get_success_rate(self) -> float
    def is_degrading(self) -> bool
    def to_dict() / from_dict()
```

---

#### **Task 1.2: ExecutionRepository Interface** (~100 LOC)
**File:** `services/mcp-performance-store/domain/repositories/execution_repository.py`

**Methods:**
```python
class ExecutionRepository(ABC):
    async def save(self, execution: OrchestrationExecution) -> None
    async def get_by_id(self, execution_id: str) -> Optional[OrchestrationExecution]
    async def get_by_pattern(self, pattern_name: str, limit: int = 100) -> List[OrchestrationExecution]
    async def get_by_status(self, status: ExecutionStatus, limit: int = 100) -> List[OrchestrationExecution]
    async def get_by_date_range(self, start: datetime, end: datetime) -> List[OrchestrationExecution]
    async def get_recent(self, limit: int = 100) -> List[OrchestrationExecution]
    async def count() -> int
    async def count_by_status(status: ExecutionStatus) -> int
```

---

#### **Task 1.3: PatternPerformanceRepository Interface** (~50 LOC)
**File:** `services/mcp-performance-store/domain/repositories/pattern_performance_repository.py`

**Methods:**
```python
class PatternPerformanceRepository(ABC):
    async def save(self, performance: PatternPerformance) -> None
    async def get_by_pattern(self, pattern_name: str) -> Optional[PatternPerformance]
    async def get_all() -> List[PatternPerformance]
    async def update(self, performance: PatternPerformance) -> None
```

---

#### **Task 1.4: RedisExecutionRepository** (~300 LOC)
**File:** `services/mcp-performance-store/infrastructure/repositories/redis_execution_repository.py`

**Implementation:**
- Use Redis hashes for storage
- Indices: status, pattern, date, all
- JSON serialization/deserialization
- Error handling

**Pattern:** Follow `RedisCompositionRepository` from MCP Composer

---

#### **Task 1.5: RedisPatternPerformanceRepository** (~150 LOC)
**File:** `services/mcp-performance-store/infrastructure/repositories/redis_pattern_performance_repository.py`

**Implementation:**
- Store aggregated metrics per pattern
- Update on each execution
- Calculate percentiles

---

#### **Task 1.6: Settings Configuration** (~50 LOC)
**File:** `services/mcp-performance-store/infrastructure/config/settings.py`

```python
class Settings(BaseSettings):
    service_name: str = "mcp-performance-store"
    service_port: int = 5647
    
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    redis_key_prefix: str = "mcp-perf"
    
    # Optional: TimescaleDB for time-series
    timescale_enabled: bool = False
    timescale_host: str = "localhost"
    timescale_port: int = 5432
    timescale_db: str = "mcp_performance"
```

---

### **Session 1 Deliverable:**

✅ Complete domain + infrastructure layer (~800 LOC)  
✅ All entities and repositories ready  
✅ Ready for use case implementation  
✅ No linter errors

**Test Command:**
```bash
# Run linter
python -m pylint services/mcp-performance-store/domain/
python -m pylint services/mcp-performance-store/infrastructure/
```

---

## 🎯 **SESSION 2: Performance Store Use Cases & API** (4-6 hours)

### **Goal:** Fully functional REST API

### **Tasks:**

#### **Task 2.1: RecordExecutionUseCase** (~300 LOC)
**File:** `services/mcp-performance-store/application/use_cases/record_execution.py`

```python
class RecordExecutionUseCase:
    """Record a new execution and update pattern performance."""
    
    def __init__(
        self,
        execution_repo: ExecutionRepository,
        pattern_repo: PatternPerformanceRepository
    ):
        ...
    
    async def execute(
        self,
        execution: OrchestrationExecution
    ) -> None:
        # 1. Save execution
        await self.execution_repo.save(execution)
        
        # 2. Update pattern performance
        if execution.pattern_name:
            perf = await self.pattern_repo.get_by_pattern(execution.pattern_name)
            if not perf:
                perf = PatternPerformance(pattern_name=execution.pattern_name)
            perf.update_from_execution(execution)
            await self.pattern_repo.update(perf)
```

---

#### **Task 2.2: QueryPerformanceUseCase** (~250 LOC)
**File:** `services/mcp-performance-store/application/use_cases/query_performance.py`

```python
class QueryPerformanceUseCase:
    """Query performance metrics with filters."""
    
    async def get_execution(self, execution_id: str) -> OrchestrationExecution
    async def get_recent_executions(self, limit: int) -> List[OrchestrationExecution]
    async def get_pattern_performance(self, pattern_name: str) -> PatternPerformance
    async def get_all_patterns() -> List[PatternPerformance]
    async def get_summary() -> Dict[str, Any]
    async def get_trends(self, hours: int = 24) -> Dict[str, Any]
```

---

#### **Task 2.3: REST API - main.py** (~250 LOC)
**File:** `services/mcp-performance-store/main.py`

**10 Endpoints:**
```python
# Health
GET  /health

# Executions
POST /api/v1/executions              # Record execution
GET  /api/v1/executions/{id}         # Get execution
GET  /api/v1/executions              # List executions (filters: status, pattern, limit)
GET  /api/v1/executions/recent       # Recent executions

# Patterns
GET  /api/v1/patterns                # List all patterns
GET  /api/v1/patterns/{name}/performance  # Pattern metrics

# Metrics & Analytics
GET  /api/v1/metrics/summary         # Overall summary
GET  /api/v1/metrics/trends          # Trends over time (24h, 7d, 30d)
GET  /api/v1/metrics/anomalies       # Detect anomalies
```

**Pattern:** Follow `main.py` from MCP Composer

---

#### **Task 2.4: DTOs** (~100 LOC)
**Files:**
- `application/dto/execution_dto.py`
- `application/dto/performance_dto.py`
- `application/dto/metrics_dto.py`

**Pydantic Models:**
```python
class RecordExecutionRequest(BaseModel):
    execution: OrchestrationExecution

class ExecutionResponse(BaseModel):
    execution_id: str
    status: str
    duration_ms: float
    ...

class PatternPerformanceResponse(BaseModel):
    pattern_name: str
    total_executions: int
    success_rate: float
    avg_duration_ms: float
    ...

class MetricsSummaryResponse(BaseModel):
    total_executions: int
    success_rate: float
    patterns_count: int
    avg_duration_ms: float
    ...
```

---

### **Session 2 Deliverable:**

✅ Fully functional REST API (~900 LOC)  
✅ 10 endpoints working  
✅ Use cases implemented  
✅ DTOs defined  
✅ Can record and query executions

**Test Command:**
```bash
# Start service
cd services/mcp-performance-store
python main.py

# Test endpoints
curl http://localhost:5647/health
curl http://localhost:5647/api/v1/metrics/summary
```

---

## 📊 **SESSION 3: Performance Store Analytics** (3-4 hours)

### **Goal:** Advanced analytics capabilities

### **Tasks:**

#### **Task 3.1: Analytics Service** (~350 LOC)
**File:** `services/mcp-performance-store/domain/services/analytics_service.py`

**Features:**
- Trend detection (improving/degrading/stable)
- Percentile calculations (p50, p95, p99)
- Pattern ranking by performance
- Time window comparisons (24h vs 7d vs 30d)

```python
class AnalyticsService:
    def calculate_trend(
        self,
        pattern_name: str,
        window_hours: int = 24
    ) -> TrendAnalysis
    
    def rank_patterns_by_performance() -> List[PatternRanking]
    
    def compare_time_windows(
        self,
        pattern_name: str
    ) -> WindowComparison
    
    def detect_performance_degradation() -> List[PatternAlert]
```

---

#### **Task 3.2: Anomaly Detection** (~200 LOC)
**File:** `services/mcp-performance-store/domain/services/anomaly_detection.py`

**Methods:**
- Z-score anomaly detection
- IQR (Interquartile Range) outliers
- Moving average deviations
- Alert thresholds

```python
class AnomalyDetector:
    def detect_anomalies(
        self,
        executions: List[OrchestrationExecution]
    ) -> List[Anomaly]
    
    def detect_outliers(
        self,
        values: List[float],
        method: str = "zscore"
    ) -> List[int]
    
    def should_alert(
        self,
        pattern_perf: PatternPerformance
    ) -> bool
```

---

### **Session 3 Deliverable:**

✅ Advanced analytics service (~550 LOC)  
✅ Trend detection working  
✅ Anomaly detection functional  
✅ Integration with REST API

**Test:**
```bash
curl http://localhost:5647/api/v1/metrics/trends?hours=24
curl http://localhost:5647/api/v1/metrics/anomalies
```

---

## 🔗 **SESSION 4: Integration & Testing** (3-4 hours)

### **Goal:** Production-ready Performance Store

### **Tasks:**

#### **Task 4.1: Service Integration**

**Orchestrator Integration:**
```python
# In mcp-orchestrator, after executing query:
await performance_store_client.record_execution(
    OrchestrationExecution(
        query=query,
        pattern_name=pattern_name,
        total_duration_ms=duration,
        ...
    )
)
```

**Composer Integration:**
```python
# In mcp-composer, after compose query:
await performance_store_client.record_execution(
    OrchestrationExecution(
        composition_id=composition_id,
        ...
    )
)
```

---

#### **Task 4.2: E2E Tests** (~200 LOC)
**File:** `tests/e2e/test_mcp_performance_store.py`

```python
class TestPerformanceStoreE2E:
    async def test_health_check()
    async def test_record_execution()
    async def test_get_execution()
    async def test_list_executions()
    async def test_pattern_performance()
    async def test_metrics_summary()
    async def test_trends()
    async def test_anomaly_detection()
```

---

#### **Task 4.3: Docker Integration** (~100 LOC)

**Files:**
- `services/mcp-performance-store/Dockerfile`
- `services/mcp-performance-store/requirements.txt`
- Update `docker-compose.dev.yml` to include performance-store

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

---

#### **Task 4.4: Documentation** (~100 LOC)

**Files:**
- `services/mcp-performance-store/README.md`
- API documentation
- Usage examples

---

### **Session 4 Deliverable:**

✅ Production-ready Performance Store  
✅ Integrated with Orchestrator/Composer  
✅ E2E tests passing (>90% coverage)  
✅ Docker deployment ready  
✅ Complete documentation

**Test:**
```bash
# Run E2E tests
pytest tests/e2e/test_mcp_performance_store.py -v

# Deploy with Docker
docker-compose -f docker-compose.dev.yml up mcp-performance-store
```

---

## 🏪 **SESSION 5: MCP Store Service** (8-12 hours)

### **Goal:** Production-ready MCP Store for versioned package storage

### **Overview:**

**Purpose:** "Docker for Knowledge Graphs" - portable MCP packages

**Features:**
- Package upload/download
- Semantic versioning (1.0.0, 2.0.0)
- Compression/decompression
- Search & discovery
- Export/import functionality
- Marketplace foundation

**Estimated LOC:** ~2,300

---

### **Tasks:**

#### **Task 5.1: Domain Entities** (~300 LOC)

**Files:**
- `domain/entities/mcp_package.py`
- `domain/entities/mcp_version.py`

```python
@dataclass
class MCPPackage:
    package_id: str
    name: str
    description: str
    author: str
    versions: List[MCPVersion]
    tags: List[str]
    downloads: int
    created_at: datetime
    updated_at: datetime

@dataclass
class MCPVersion:
    version: str  # Semantic: 1.0.0
    package_id: str
    file_path: str  # S3/MinIO path
    file_size_bytes: int
    checksum: str
    changelog: str
    created_at: datetime
```

---

#### **Task 5.2: Repositories** (~350 LOC)

**Files:**
- `domain/repositories/package_repository.py`
- `domain/repositories/storage_repository.py`
- `infrastructure/repositories/postgres_package_repository.py`
- `infrastructure/repositories/s3_storage_repository.py`

---

#### **Task 5.3: Use Cases** (~650 LOC)

**Files:**
- `application/use_cases/upload_package.py`
- `application/use_cases/download_package.py`
- `application/use_cases/version_package.py`
- `application/use_cases/search_packages.py`
- `application/use_cases/export_import.py`

---

#### **Task 5.4: REST API** (~400 LOC)

**15 Endpoints:**
```python
# Packages
POST   /api/v1/packages              # Upload
GET    /api/v1/packages/{id}         # Get
GET    /api/v1/packages              # List/Search
DELETE /api/v1/packages/{id}         # Delete

# Versions
POST   /api/v1/packages/{id}/versions  # Create version
GET    /api/v1/packages/{id}/versions  # List versions
GET    /api/v1/packages/{id}/versions/{version}  # Get version
DELETE /api/v1/packages/{id}/versions/{version}  # Delete version

# Download
GET    /api/v1/packages/{id}/download  # Download latest
GET    /api/v1/packages/{id}/versions/{version}/download  # Download specific

# Export/Import
POST   /api/v1/export                 # Export package
POST   /api/v1/import                 # Import package

# Marketplace
GET    /api/v1/marketplace            # Browse marketplace
GET    /api/v1/marketplace/popular    # Popular packages
GET    /api/v1/marketplace/search     # Search
```

---

#### **Task 5.5: Integration & Tests** (~600 LOC)

- Integration with Registry
- E2E tests
- Docker deployment
- Documentation

---

### **Session 5 Deliverable:**

✅ Production-ready MCP Store (~2,300 LOC)  
✅ Package management complete  
✅ Versioning system working  
✅ Export/import functional  
✅ Marketplace foundation

---

## 📊 **Overall Timeline**

```
Session 1: Foundation          [========          ] 4-6 hours
Session 2: API                 [========          ] 4-6 hours
Session 3: Analytics           [======            ] 3-4 hours
Session 4: Integration         [======            ] 3-4 hours
Session 5: MCP Store           [===========       ] 8-12 hours
                               -------------------------
Total:                                              22-32 hours
```

**Realistic Timeline:** 3-4 weeks at 6-8 hours/week

---

## 🎯 **Success Criteria**

### **Performance Store Complete When:**
- ✅ All 10 endpoints working
- ✅ Can record and query executions
- ✅ Analytics and anomaly detection functional
- ✅ Integrated with Orchestrator/Composer
- ✅ E2E tests passing (>90% coverage)
- ✅ Docker deployment ready
- ✅ Complete documentation

### **MCP Store Complete When:**
- ✅ All 15 endpoints working
- ✅ Can upload/download packages
- ✅ Versioning system functional
- ✅ Export/import working
- ✅ Search and marketplace operational
- ✅ E2E tests passing (>90% coverage)
- ✅ Docker deployment ready
- ✅ Complete documentation

---

## 🚀 **Ready to Start!**

**Next Command:** Start Session 1 - Create PatternPerformance entity

**File to Create:**  
`services/mcp-performance-store/domain/entities/pattern_performance.py`

**Reference:**  
`services/mcp-performance-store/domain/entities/orchestration_execution.py`

---

**Plan Created:** October 7, 2025  
**Approach:** Incremental (Complete Performance Store → MCP Store)  
**Estimated Total Time:** 22-32 hours  
**Sessions:** 5 sessions (4-8 hours each)
