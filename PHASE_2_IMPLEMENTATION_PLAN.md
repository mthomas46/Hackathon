# 🚀 Phase 2: Sub-Job Execution System - Implementation Plan

**Start Date:** 2025-10-21  
**Estimated Duration:** Weeks 4-5 (2 weeks)  
**Status:** 🟡 IN PROGRESS

---

## 🎯 Phase 2 Goals

Transform the discovery system from planning to execution by implementing parallel sub-job processing with intelligent orchestration.

### Success Criteria
- [ ] Sub-jobs execute in parallel (up to 5 concurrent)
- [ ] Dependency management working
- [ ] Real-time progress tracking
- [ ] Fault tolerance and recovery
- [ ] Resource allocation and load balancing
- [ ] Integration with existing ingestion pipeline
- [ ] Performance improvement: 3-5x faster for large repos
- [ ] Comprehensive monitoring and metrics

---

## 📋 Components to Build

### 1. Job Orchestrator (Core)
**File:** `src/services/orchestration/job_orchestrator.py`  
**Lines:** ~300  
**Purpose:** Manages sub-job execution, dependencies, and coordination

**Features:**
- Sub-job scheduling based on priority and dependencies
- Parallel execution management (up to 5 concurrent)
- Dependency resolution (topological sort)
- Resource allocation
- Error handling and retry logic
- Status tracking and updates

**Key Methods:**
```python
async def execute_plan(plan_id: str) -> ExecutionResult
async def execute_sub_job(sub_job_id: str) -> SubJobResult
async def check_dependencies(sub_job: SubJob) -> bool
async def allocate_resources(sub_job: SubJob) -> Resources
async def handle_failure(sub_job: SubJob, error: Exception)
```

### 2. Worker Pool Manager
**File:** `src/services/orchestration/worker_pool.py`  
**Lines:** ~250  
**Purpose:** Manages worker threads/processes for parallel execution

**Features:**
- Dynamic worker pool (2-5 workers based on load)
- Worker lifecycle management
- Load balancing across workers
- Health monitoring
- Graceful shutdown

**Key Methods:**
```python
async def start_workers(count: int)
async def stop_workers()
async def assign_job(sub_job: SubJob) -> Worker
async def get_available_worker() -> Optional[Worker]
async def monitor_worker_health()
```

### 3. Progress Tracker
**File:** `src/services/orchestration/progress_tracker.py`  
**Lines:** ~200  
**Purpose:** Real-time progress tracking and reporting

**Features:**
- File-level progress tracking
- Sub-job progress aggregation
- Plan-level progress calculation
- Real-time updates via Redis Pub/Sub
- Progress persistence to database
- ETA calculation

**Key Methods:**
```python
async def update_progress(sub_job_id: str, files_processed: int)
async def get_progress(plan_id: str) -> ProgressReport
async def calculate_eta(plan_id: str) -> float
async def publish_progress_update(update: ProgressUpdate)
```

### 4. Dependency Manager
**File:** `src/services/orchestration/dependency_manager.py`  
**Lines:** ~150  
**Purpose:** Manages sub-job dependencies and execution order

**Features:**
- Dependency graph construction
- Topological sorting
- Circular dependency detection
- Ready-to-execute queue management
- Dependency completion tracking

**Key Methods:**
```python
def build_dependency_graph(sub_jobs: List[SubJob]) -> Graph
def topological_sort(graph: Graph) -> List[str]
def detect_circular_dependencies(graph: Graph) -> List[Cycle]
async def get_ready_sub_jobs(plan_id: str) -> List[SubJob]
async def mark_dependency_complete(sub_job_id: str)
```

### 5. Resource Allocator
**File:** `src/services/orchestration/resource_allocator.py`  
**Lines:** ~180  
**Purpose:** Allocates and manages computational resources

**Features:**
- Memory allocation per sub-job
- CPU core allocation
- Concurrent execution limits
- Resource usage monitoring
- Dynamic reallocation

**Key Methods:**
```python
async def allocate(sub_job: SubJob) -> ResourceAllocation
async def release(allocation: ResourceAllocation)
async def get_available_resources() -> Resources
async def monitor_usage() -> ResourceMetrics
```

### 6. Sub-Job Executor
**File:** `src/services/orchestration/sub_job_executor.py`  
**Lines:** ~350  
**Purpose:** Executes individual sub-jobs (file processing)

**Features:**
- File-by-file processing within sub-job
- Integration with existing normalization pipeline
- Embedding generation
- ChromaDB storage
- Error handling per file
- Progress reporting

**Key Methods:**
```python
async def execute(sub_job: SubJob) -> ExecutionResult
async def process_file(file: ClassifiedFile) -> FileResult
async def handle_file_error(file: ClassifiedFile, error: Exception)
async def report_progress(files_processed: int)
```

### 7. Execution Monitor
**File:** `src/services/orchestration/execution_monitor.py`  
**Lines:** ~200  
**Purpose:** Monitors execution health and performance

**Features:**
- Real-time execution metrics
- Performance tracking (files/sec, throughput)
- Error rate monitoring
- Resource usage tracking
- Alerting on anomalies

**Key Methods:**
```python
async def track_execution(plan_id: str)
async def get_metrics(plan_id: str) -> ExecutionMetrics
async def detect_anomalies() -> List[Anomaly]
async def generate_report(plan_id: str) -> Report
```

### 8. API Endpoints
**File:** `src/api/routes/orchestration.py`  
**Lines:** ~300  
**Purpose:** REST API for orchestration control

**Endpoints:**
- `POST /api/v1/orchestration/execute/{plan_id}` - Start execution
- `GET /api/v1/orchestration/status/{plan_id}` - Get status
- `POST /api/v1/orchestration/pause/{plan_id}` - Pause execution
- `POST /api/v1/orchestration/resume/{plan_id}` - Resume execution
- `POST /api/v1/orchestration/cancel/{plan_id}` - Cancel execution
- `GET /api/v1/orchestration/progress/{plan_id}` - Get progress
- `GET /api/v1/orchestration/metrics/{plan_id}` - Get metrics

### 9. Database Schema Updates
**File:** `src/storage/migrations/add_orchestration_tables.py`  
**Lines:** ~150  
**Purpose:** Add tables for execution tracking

**Tables:**
- `execution_sessions` - Execution session metadata
- `sub_job_executions` - Individual sub-job execution records
- `execution_metrics` - Performance metrics
- `worker_status` - Worker health and status

---

## 🏗️ Implementation Strategy

### Week 4: Core Infrastructure

**Day 1-2: Foundation**
1. Create orchestration module structure
2. Implement Dependency Manager
3. Implement Resource Allocator
4. Write unit tests

**Day 3-4: Execution Core**
5. Implement Job Orchestrator (core logic)
6. Implement Worker Pool Manager
7. Implement Sub-Job Executor
8. Integration tests

**Day 5: Progress & Monitoring**
9. Implement Progress Tracker
10. Implement Execution Monitor
11. Redis Pub/Sub integration
12. Real-time updates

### Week 5: Integration & Testing

**Day 1-2: API & Database**
13. Create database migration
14. Implement orchestration API endpoints
15. Update EnhancedJobProcessor integration
16. API tests

**Day 3-4: End-to-End Testing**
17. Test full discovery → execution flow
18. Test parallel execution (5 concurrent)
19. Test dependency management
20. Test fault tolerance

**Day 5: Performance & Documentation**
21. Performance testing and optimization
22. Comprehensive documentation
23. Dashboard integration prep
24. Phase 2 completion report

---

## 🔄 Integration Points

### With Phase 1 (Discovery)
- Read processing plans from database
- Use classified files from discovery
- Respect priority ordering
- Execute sub-jobs in plan order

### With Existing Ingestion
- Reuse file normalization logic
- Reuse embedding generation
- Reuse ChromaDB storage
- Maintain backward compatibility

### With Infrastructure
- Redis for progress pub/sub
- PostgreSQL for state persistence
- ChromaDB for embeddings
- Existing worker infrastructure

---

## 📊 Expected Performance Improvements

### Before (Phase 1)
- Sequential processing
- Single-threaded execution
- No priority-based ordering
- 10K files: ~60 minutes

### After (Phase 2)
- Parallel sub-job execution (5 concurrent)
- Priority-based processing
- Intelligent resource allocation
- 10K files: ~15-20 minutes (3-4x faster)

### Metrics to Track
- Files processed per second
- Sub-job completion time
- Resource utilization
- Error rates
- Memory usage
- CPU usage

---

## 🧪 Testing Strategy

### Unit Tests
- Each component tested independently
- Mock dependencies
- Edge cases covered
- ~80% code coverage target

### Integration Tests
- Component interactions
- Database operations
- Redis pub/sub
- API endpoints

### End-to-End Tests
- Full discovery → execution flow
- Real repository ingestion
- Parallel execution verification
- Fault tolerance scenarios

### Performance Tests
- Large repository (10K+ files)
- Concurrent execution stress test
- Resource usage monitoring
- Throughput measurement

---

## 🚨 Risk Mitigation

### Technical Risks
1. **Race Conditions**
   - Mitigation: Proper locking, atomic operations
   
2. **Resource Exhaustion**
   - Mitigation: Resource limits, monitoring, dynamic allocation
   
3. **Deadlocks**
   - Mitigation: Dependency cycle detection, timeouts
   
4. **Data Consistency**
   - Mitigation: Database transactions, idempotent operations

### Operational Risks
1. **Worker Crashes**
   - Mitigation: Health monitoring, auto-restart, job recovery
   
2. **Database Failures**
   - Mitigation: Connection pooling, retry logic, graceful degradation
   
3. **Memory Leaks**
   - Mitigation: Resource cleanup, monitoring, limits

---

## 📝 Success Metrics

### Functional
- [ ] All sub-jobs execute successfully
- [ ] Parallel execution working (5 concurrent)
- [ ] Dependencies respected
- [ ] Progress tracking accurate
- [ ] Fault tolerance working

### Performance
- [ ] 3-5x faster than sequential
- [ ] <5% overhead from orchestration
- [ ] Real-time progress updates (<1s latency)
- [ ] Resource utilization >70%

### Quality
- [ ] 80%+ code coverage
- [ ] All tests passing
- [ ] No memory leaks
- [ ] Clean error handling
- [ ] Comprehensive logging

---

## 🎯 Phase 2 Deliverables

1. **Code**
   - 9 new components (~1,930 lines)
   - Full test suite
   - API endpoints
   - Database migration

2. **Documentation**
   - Component documentation
   - API documentation
   - Integration guide
   - Performance report

3. **Testing**
   - Unit tests
   - Integration tests
   - E2E tests
   - Performance benchmarks

4. **Deployment**
   - Migration scripts
   - Configuration updates
   - Monitoring setup
   - Rollback procedures

---

**Status:** 🟡 READY TO START  
**Next:** Begin with Dependency Manager and Resource Allocator

