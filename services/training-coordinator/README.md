# Training Coordinator Service

**Version:** 1.0.0  
**Port:** 5600

Orchestrates MCP training pipeline with job management and worker coordination.

## Features

- **Job Management** - Create, execute, track training jobs
- **Worker Orchestration** - Coordinate extraction, normalization, embedding, storage workers
- **Priority Queue** - 5-level priority system
- **10-State Pipeline** - Complete job lifecycle management
- **9 Data Sources** - GitHub, Confluence, Jira, FullStory, Slack, Google Drive, etc.
- **Resource Limits** - Document, duration, cost limits
- **Progress Tracking** - Real-time progress monitoring
- **Complete DDD Architecture**

## Architecture

```
Domain Layer:
- 4 Value Objects (JobStatus, JobPriority, WorkerType, DataSource)
- 3 Entities (TrainingJob, WorkerPool, JobResult)
- 2 Repositories

Application Layer:
- 3 DTOs
- 3 Use Cases

Infrastructure Layer:
- Settings
- RedisJobRepository

Presentation Layer:
- FastAPI with 3 endpoints
```

## API Endpoints

- `POST /api/v1/jobs` - Create training job
- `GET /api/v1/jobs/{job_id}` - Get job details
- `POST /api/v1/jobs/{job_id}/execute` - Execute job

## Configuration

Environment variables (see docker-compose.dev.yml):
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB` - Redis configuration
- `MAX_CONCURRENT_JOBS` - Max concurrent jobs
- `DEFAULT_JOB_TIMEOUT_SECONDS` - Default timeout
- Worker pool limits for each worker type

## Running

### Docker
```bash
docker-compose --profile training_services up training-coordinator
```

### Local Development
```bash
cd services/training-coordinator
pip install -r requirements.txt
python main.py
```

## Integration

- **MCP Provisioner** - Provisions MCP instances
- **MCP Infrastructure** - Context management
- **Celery** - Background task execution
- **PostgreSQL** - Job persistence (future)

## Pipeline Stages

1. **Validation** - Validate job configuration
2. **Extraction** - Extract data from sources
3. **Normalization** - Normalize to markdown
4. **Embedding** - Generate embeddings
5. **Storage** - Store to vector/graph DBs

## Status

**Production-Ready Foundation** - Core infrastructure complete, worker implementations pending.

---

Part of the MCP System - 7th and final core service! 🎉

