# 🎓 Training Coordinator Service

**Version:** 1.0.0  
**Port:** 5600  
**Role:** MCP Training Pipeline Orchestration

The **Training Coordinator Service** orchestrates the complete MCP training pipeline, managing job execution, worker coordination, and data processing from multiple sources to populate MCP knowledge bases.

---

## 🎯 **Overview**

The Training Coordinator is the central orchestration service for training MCP instances with knowledge from various data sources. It manages the end-to-end pipeline from data extraction through embedding generation and storage.

**Key Responsibilities**:
- **Job Management**: Create, schedule, and track training jobs
- **Worker Orchestration**: Coordinate extraction, normalization, embedding, and storage workers
- **Pipeline Management**: 10-state lifecycle management
- **Resource Management**: Worker pools, limits, and priorities
- **Progress Tracking**: Real-time monitoring and reporting

---

## ✨ **Key Features**

### 1. Job Management
- ✅ Create training jobs with rich configuration
- ✅ Execute jobs asynchronously
- ✅ Track job progress and status
- ✅ Query job history and results
- ✅ Cancel/pause/resume jobs

### 2. Worker Orchestration
- ✅ **Extraction Workers**: GitHub, Confluence, Jira, FullStory, Slack, Drive, etc.
- ✅ **Normalization Workers**: Convert to standardized markdown format
- ✅ **Embedding Workers**: Generate vector embeddings
- ✅ **Storage Workers**: Persist to vector/graph databases
- ✅ Worker pool management with limits
- ✅ Worker health monitoring

### 3. Priority System
5-level priority queue:
- **CRITICAL**: Immediate processing
- **HIGH**: Expedited processing
- **MEDIUM**: Standard processing (default)
- **LOW**: Background processing
- **DEFERRED**: Process when idle

### 4. Pipeline States
10-state job lifecycle:
1. **PENDING**: Job created, awaiting execution
2. **VALIDATING**: Validating job configuration
3. **EXTRACTING**: Extracting data from sources
4. **NORMALIZING**: Converting to markdown
5. **EMBEDDING**: Generating embeddings
6. **STORING**: Persisting to databases
7. **VALIDATING_RESULTS**: Verifying results
8. **COMPLETED**: Successfully finished
9. **FAILED**: Encountered errors
10. **CANCELLED**: User cancelled

### 5. Data Sources
9 supported data sources:
- **GITHUB**: Code repositories, issues, PRs, wikis
- **CONFLUENCE**: Confluence spaces and pages
- **JIRA**: Issues, epics, stories
- **FULLSTORY**: User session recordings
- **SLACK**: Channel messages and threads
- **GOOGLE_DRIVE**: Documents and sheets
- **NOTION**: Notion pages and databases
- **AIRTABLE**: Airtable bases
- **CUSTOM**: Custom data sources

### 6. Resource Limits
- **Document Limits**: Max documents per job
- **Duration Limits**: Max processing time
- **Cost Limits**: Budget constraints
- **Worker Limits**: Max concurrent workers per type

---

## 🏗️ **Architecture**

### Domain-Driven Design (DDD)

```
services/training-coordinator/
├── domain/
│   ├── entities/
│   │   ├── training_job.py      # Training job entity
│   │   ├── worker_pool.py       # Worker pool entity
│   │   └── job_result.py        # Result entity
│   ├── value_objects/
│   │   ├── job_status.py        # 10 job states
│   │   ├── job_priority.py      # 5 priority levels
│   │   ├── worker_type.py       # Worker types
│   │   └── data_source.py       # Data source types
│   └── repositories/
│       ├── job_repository.py    # Abstract job repo
│       └── worker_repository.py # Abstract worker repo
├── application/
│   ├── dtos/
│   │   ├── create_job_request.py
│   │   ├── job_response.py
│   │   └── execute_job_request.py
│   └── use_cases/
│       ├── create_training_job.py
│       ├── execute_training_job.py
│       └── get_job_status.py
├── infrastructure/
│   ├── persistence/
│   │   ├── redis_job_repository.py
│   │   └── postgres_job_repository.py
│   ├── celery/
│   │   └── tasks.py              # Celery task definitions
│   └── config/
│       └── settings.py
└── presentation/
    └── api/
        └── routes.py             # FastAPI endpoints
```

---

## 📡 **API Endpoints**

### Job Management

```http
POST   /api/v1/jobs              # Create training job
GET    /api/v1/jobs              # List all jobs
GET    /api/v1/jobs/{job_id}     # Get job details
POST   /api/v1/jobs/{job_id}/execute  # Execute job
DELETE /api/v1/jobs/{job_id}     # Cancel job
```

### Job Control

```http
POST   /api/v1/jobs/{job_id}/pause   # Pause job
POST   /api/v1/jobs/{job_id}/resume  # Resume job
POST   /api/v1/jobs/{job_id}/retry   # Retry failed job
```

### Monitoring

```http
GET    /api/v1/jobs/{job_id}/progress  # Get progress
GET    /api/v1/jobs/{job_id}/logs      # Get job logs
GET    /api/v1/workers                 # List workers
GET    /api/v1/workers/{type}/health   # Worker health
```

---

## 🔗 **MCP Ecosystem Integration**

The Training Coordinator is a **SUPPORTING SERVICE** that enables MCP instances to learn from diverse data sources.

### Service Interactions

#### 1. **MCP Provisioner** (Port: 8003)
**Relationship**: Triggers training  
**Interaction**:
- Provisioner creates new MCP instances
- Triggers Training Coordinator to populate knowledge
- Provides MCP ID and configuration

**Flow**:
```
Provisioner: Create MCP instance "acme-corp-dev"
Provisioner → Training Coordinator: "Train MCP with GitHub repos"
Training Coordinator: Create training job
Training Coordinator → Workers: Extract, normalize, embed
Training Coordinator → MCP Store: Store knowledge
Training Coordinator → Provisioner: Training complete
```

#### 2. **MCP Store** (Port: 8008)
**Relationship**: Knowledge storage destination  
**Interaction**:
- Training Coordinator sends processed data to Store
- Store receives embeddings and metadata
- Store confirms successful storage

**Flow**:
```
Training Coordinator: Job in STORING state
Training Coordinator → MCP Store: Store 1000 embeddings
MCP Store: Persist to Neo4j + ChromaDB
MCP Store → Training Coordinator: Storage confirmed
Training Coordinator: Move to COMPLETED state
```

#### 3. **MCP Infrastructure** (Port: 8007)
**Relationship**: Resource management  
**Interaction**:
- Infrastructure monitors worker health
- Provides resource allocation information
- Enforces resource limits

**Flow**:
```
Training Coordinator: Need extraction worker
Training Coordinator → Infrastructure: Request resource allocation
Infrastructure: Check available resources
Infrastructure → Training Coordinator: Allocation approved
Training Coordinator: Start worker
```

#### 4. **Celery Workers**
**Relationship**: Task execution  
**Interaction**:
- Coordinator queues tasks to Celery
- Workers execute extraction/normalization/embedding
- Workers report progress back

**Flow**:
```
Training Coordinator: Job ready for extraction
Training Coordinator → Celery: Queue GitHub extraction task
Celery Worker: Execute extraction
Worker → Training Coordinator: Progress updates (0%...100%)
Worker → Training Coordinator: Task complete
```

#### 5. **MCP Tier Manager** (Port: 8013)
**Relationship**: Hierarchical knowledge organization  
**Interaction**:
- Training Coordinator respects tier boundaries
- Associates trained knowledge with correct tier
- Enables tier-specific training

**Flow**:
```
User: Train "Project A" tier with Confluence docs
User → Training Coordinator: Create job for Project A
Training Coordinator: Identify tier from Tier Manager
Training Coordinator: Train with tier scope
Training Coordinator → MCP Store: Store with tier metadata
```

#### 6. **External Data Sources**
**Relationship**: Data ingestion  
**Interaction**:
- Workers connect to external APIs
- Extract data (GitHub, Confluence, etc.)
- Handle authentication and rate limits

**Flow**:
```
Extraction Worker: Connect to GitHub API
GitHub API: Authenticate with token
Worker: Extract repos, issues, PRs
Worker: Normalize to markdown
Worker → Training Coordinator: Data extracted
```

---

## 🔄 **Training Pipeline Flow**

### Complete Training Workflow

```
┌─────────────┐
│    User     │
└──────┬──────┘
       │ 1. Create training job
       ▼
┌─────────────────┐
│   Coordinator   │
└────────┬────────┘
         │ 2. Validate job
         ▼
┌──────────────────────┐
│  Extraction Workers  │ ◄── GitHub, Confluence, etc.
└────────┬─────────────┘
         │ 3. Extract data
         ▼
┌───────────────────────┐
│ Normalization Workers │
└────────┬──────────────┘
         │ 4. Convert to markdown
         ▼
┌──────────────────────┐
│  Embedding Workers   │
└────────┬─────────────┘
         │ 5. Generate embeddings
         ▼
┌──────────────────────┐
│  Storage Workers     │
└────────┬─────────────┘
         │ 6. Persist to DBs
         ▼
┌─────────────┐        ┌──────────────┐
│  MCP Store  │────────┤ Neo4j/Chroma │
└─────────────┘        └──────────────┘
```

### State Transitions

```
PENDING → VALIDATING → EXTRACTING → NORMALIZING → 
EMBEDDING → STORING → VALIDATING_RESULTS → COMPLETED
                                              ↓
                                          FAILED
```

---

## 🎯 **Role in MCP Architecture**

The Training Coordinator serves as the **KNOWLEDGE INGESTION ENGINE** in the MCP architecture:

### 1. **Data Pipeline Orchestration**
- Manages end-to-end data processing pipeline
- Coordinates multiple worker types
- Ensures data quality and consistency

### 2. **Multi-Source Integration**
- Connects to 9+ different data sources
- Handles various authentication mechanisms
- Normalizes diverse data formats

### 3. **Scalable Processing**
- Worker pool management
- Parallel processing capabilities
- Resource-aware scheduling

### 4. **Knowledge Population**
- Populates MCP instances with knowledge
- Generates searchable embeddings
- Builds knowledge graphs

### 5. **Quality Assurance**
- Validates extracted data
- Verifies embeddings
- Ensures storage success

---

## 🔧 **Configuration**

### Environment Variables

```bash
# Service Configuration
PORT=5600
SERVICE_NAME=training-coordinator

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=5

# Celery
CELERY_BROKER_URL=redis://localhost:6379/5
CELERY_RESULT_BACKEND=redis://localhost:6379/5

# Worker Limits
MAX_CONCURRENT_JOBS=5
EXTRACTION_WORKER_LIMIT=10
NORMALIZATION_WORKER_LIMIT=8
EMBEDDING_WORKER_LIMIT=5
STORAGE_WORKER_LIMIT=3

# Timeouts
DEFAULT_JOB_TIMEOUT_SECONDS=3600
EXTRACTION_TIMEOUT_SECONDS=600
EMBEDDING_TIMEOUT_SECONDS=900

# External Services
GITHUB_API_TOKEN=<token>
CONFLUENCE_API_TOKEN=<token>
SLACK_API_TOKEN=<token>
```

---

## 🚀 **Running the Service**

### Docker (Recommended)

```bash
docker-compose --profile training_services up training-coordinator
```

### Local Development

```bash
cd services/training-coordinator
pip install -r requirements.txt

# Start Redis
redis-server

# Start Celery workers
celery -A infrastructure.celery.tasks worker --loglevel=info

# Start service
python main.py
```

### With Full Ecosystem

```bash
# Start all services including training
docker-compose up -d
```

---

## 📊 **Monitoring & Health**

### Health Check Endpoint

```http
GET /health
```

**Response**:
```json
{
  "status": "healthy",
  "service": "training-coordinator",
  "version": "1.0.0",
  "workers": {
    "extraction": {"active": 3, "limit": 10},
    "normalization": {"active": 2, "limit": 8},
    "embedding": {"active": 1, "limit": 5},
    "storage": {"active": 1, "limit": 3}
  },
  "jobs": {
    "pending": 2,
    "executing": 3,
    "completed": 147,
    "failed": 5
  }
}
```

---

## 📚 **Usage Examples**

### Create Training Job

```bash
curl -X POST http://localhost:5600/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "mcp_id": "acme-corp-dev",
    "data_sources": ["GITHUB", "CONFLUENCE"],
    "priority": "HIGH",
    "config": {
      "github": {
        "repositories": ["acme/api", "acme/frontend"],
        "include_issues": true
      },
      "confluence": {
        "spaces": ["ENG", "PROD"]
      }
    },
    "limits": {
      "max_documents": 10000,
      "max_duration_seconds": 3600
    }
  }'
```

### Execute Job

```bash
curl -X POST http://localhost:5600/api/v1/jobs/JOB-123/execute
```

### Get Job Status

```bash
curl http://localhost:5600/api/v1/jobs/JOB-123
```

---

## 🎓 **Best Practices**

### For Job Configuration

1. ✅ Set appropriate priority based on urgency
2. ✅ Define reasonable resource limits
3. ✅ Use specific data source configurations
4. ✅ Monitor job progress regularly
5. ✅ Handle failures with retry logic

### For Worker Management

1. ✅ Scale workers based on load
2. ✅ Monitor worker health
3. ✅ Set appropriate timeouts
4. ✅ Implement error handling
5. ✅ Log worker activities

---

## 📈 **Performance Considerations**

### Optimization Strategies
- ✅ Parallel processing with worker pools
- ✅ Incremental data extraction
- ✅ Batch embedding generation
- ✅ Efficient storage operations
- ✅ Progress caching

### Scalability
- ✅ Horizontal worker scaling
- ✅ Distributed task queue (Celery)
- ✅ Redis for coordination
- ✅ PostgreSQL for job persistence

---

## 🔮 **Future Enhancements**

### Planned Features
- [ ] Incremental training (delta updates)
- [ ] Training job templates
- [ ] Automated retraining schedules
- [ ] Cost estimation before execution
- [ ] Multi-language support
- [ ] Custom worker plugins
- [ ] Training analytics dashboard

---

## 📞 **Support & Documentation**

- **Architecture**: See [MCP_ECOSYSTEM_ARCHITECTURE.md](/MCP_ECOSYSTEM_ARCHITECTURE.md)
- **Workers**: See [/services/workers/README.md](/services/workers/README.md)
- **MCP Store**: See [/services/mcp-store/README.md](/services/mcp-store/README.md)
- **Provisioner**: See [/services/mcp-provisioner/README.md](/services/mcp-provisioner/README.md)

---

**Status**: Production-Ready Foundation  
**Maintainer**: MCP Team  
**Last Updated**: October 7, 2025

*Orchestrating knowledge ingestion for the MCP ecosystem!* 🎓✨
