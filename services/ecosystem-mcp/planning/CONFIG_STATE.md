# Configuration State - Post Phase 1

**Last Updated**: 2025-10-11  
**Version**: 0.1.0  
**Status**: Production Ready

## Current Configuration

### Dependencies (`requirements.txt`)

#### Core
- fastapi>=0.104.0,<0.105.0
- uvicorn[standard]>=0.24.0,<0.25.0
- pydantic>=2.4.0,<3.0.0
- pydantic-settings>=2.0.0,<3.0.0

#### Database & Storage
- sqlalchemy>=2.0.0,<3.0.0
- asyncpg>=0.29.0,<0.30.0
- psycopg2-binary>=2.9.0,<3.0.0
- alembic>=1.12.0,<2.0.0
- chromadb>=0.4.0,<0.5.0
- redis>=5.0.0,<6.0.0
- **greenlet>=3.0.0,<4.0.0** ✅ (Added Phase 1 - SQLAlchemy async)

#### Security & Validation
- **slowapi>=0.1.9,<0.2.0** ✅ (Added Phase 1 - Rate limiting)
- python-jose[cryptography]>=3.3.0,<4.0.0

#### Utilities
- httpx>=0.25.0,<0.26.0
- python-dotenv>=1.0.0,<2.0.0
- gitpython>=3.1.0,<4.0.0
- structlog>=23.1.0,<24.0.0

### Environment Variables

#### Required
```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/ecosystem_mcp

# Redis
REDIS_URL=redis://localhost:6379/0

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBEDDING_MODEL=nomic-embed-text  # ✅ Installed in Phase 1

# ChromaDB
CHROMA_HOST=localhost
CHROMA_PORT=8001

# Service
LOG_LEVEL=INFO
ENVIRONMENT=development  # development, staging, production, test
```

#### Optional (Phase 1 Additions)
```bash
# CORS (for production)
CORS_ORIGINS=https://app.example.com,https://dashboard.example.com

# Rate Limiting (configured in code, no env vars needed)

# Preflight Checks
PREFLIGHT_MODE=strict  # strict, lenient
PREFLIGHT_FAIL_FAST=false
```

### Docker Compose Services

#### Current Services
1. **postgres** - PostgreSQL 15
   - Port: 5432
   - Volume: postgres_data
   - Health check: pg_isready

2. **redis** - Redis 7-alpine
   - Port: 6379
   - Volume: redis_data
   - Health check: redis-cli ping

3. **chroma** - ChromaDB
   - Port: 8001
   - Volume: chroma_data
   - Health check: HTTP /api/v1/heartbeat

4. **ollama** - Ollama (external)
   - Port: 11434
   - Volume: ollama_data
   - **Model installed**: nomic-embed-text (274 MB) ✅

5. **ecosystem-mcp** - Main service
   - Port: 8000
   - Depends on: postgres, redis, chroma, ollama
   - Health check: HTTP /health

### Database Migrations

#### Alembic Configuration
- **Location**: `alembic/`
- **Config**: `alembic.ini`
- **Migrations**: `alembic/versions/`

#### Current Migrations
1. ✅ `b576fd99f779_initial_schema.py` - Initial schema (Phase 1)
   - Documents table
   - Embeddings table
   - Git commits table
   - Ingestion jobs table (with fixed column names)
   - Model requests table
   - Document versions table

#### Migration Commands
```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### API Configuration

#### Rate Limiting (Phase 1)
- **Library**: slowapi
- **Key function**: `get_remote_address` (IP-based)
- **Limits**:
  - Health endpoints: 60/minute
  - Search endpoints: 10/minute
  - Query endpoints: 20/minute
  - Admin endpoints: 5/minute

#### CORS (Phase 1)
- **Allowed origins**: Specific list (configurable via env)
- **Allowed methods**: GET, POST, PUT, DELETE, PATCH
- **Allowed headers**: Content-Type, Authorization, X-Request-ID
- **Credentials**: Enabled

#### Input Validation (Phase 1)
- **XSS protection**: HTML sanitization
- **Path traversal**: Prevented
- **Max query length**: 500 characters
- **Max document size**: 10 MB
- **Max offset**: 10,000
- **Max limit**: 500

### Logging Configuration

#### Structured Logging
- **Library**: structlog
- **Format**: JSON (production), console (development)
- **Fields**: timestamp, level, message, request_id, context
- **Rotation**: 10 MB max, 5 backups

#### Log Levels
- **Development**: INFO
- **Staging**: INFO
- **Production**: WARNING
- **Test**: DEBUG

### Phase 1 Achievements

#### Security Hardening
- ✅ CORS configured with specific origins
- ✅ Rate limiting on all endpoints
- ✅ XSS/injection protection
- ✅ Path traversal prevention
- ✅ Input validation across all routes

#### Reliability
- ✅ Database migrations tracked
- ✅ Job persistence (crash recovery)
- ✅ Retry logic on health checks
- ✅ Graceful error handling

#### Performance
- ✅ Pagination limits (prevents DB overload)
- ✅ Connection pooling (httpx)
- ✅ Async operations throughout

#### Infrastructure
- ✅ Ollama embedding model installed
- ✅ All Docker services healthy
- ✅ Preflight checks implemented

## Configuration Files Status

### ✅ Up to Date
- `requirements.txt` - All dependencies current
- `alembic.ini` - Database migrations configured
- `alembic/env.py` - Async database URL configured
- `src/config.py` - Environment validation added
- `.gitignore` - Appropriate files ignored

### ⚠️ May Need Updates
- `docker-compose.yml` - Review service configurations
- `.env.example` - Add new environment variables
- `README.md` - Update with Phase 1 changes

### 📝 New Files Created (Phase 1)
- `src/utils/validation.py` - Input validation utilities
- `src/utils/pagination.py` - Pagination utilities
- `src/storage/repositories/ingestion_job_repository.py` - Job persistence
- `tests/unit/test_validation.py` - Validation tests
- `PHASE1_COMPLETE.md` - Documentation
- `PHASE1_COMPLETE_FINAL.md` - Documentation

## Next Steps (Phase 2)

1. **Health Check Enhancement** (in progress)
   - Add component response times
   - Add service version
   - Add uptime tracking
   - Add Ollama status

2. **Graceful Shutdown**
   - Signal handlers
   - Connection cleanup
   - In-flight request completion

3. **Error Standardization**
   - Consistent error format
   - Error codes
   - User-friendly messages

4. **Request Timeouts**
   - Endpoint-specific timeouts
   - Database query timeouts
   - External service timeouts

5. **Integration Tests**
   - Target 50% coverage
   - Test all endpoints
   - Test error scenarios
   - Test rate limiting

## Configuration Best Practices

### Development
- Use `.env` file (not committed)
- Use `development` environment
- Enable verbose logging
- Use lenient preflight mode

### Staging
- Use environment variables
- Use `staging` environment
- Enable INFO logging
- Use strict preflight mode

### Production
- Use environment variables (never `.env`)
- Use `production` environment
- Enable WARNING/ERROR logging
- Use strict preflight mode
- Configure specific CORS origins
- Enable all monitoring
- Use secrets management

## Validation

All configuration is validated on startup via:
1. Pydantic Settings validation
2. Environment validation (`src/utils/environment.py`)
3. Preflight checks (`src/utils/preflight.py`)

Any configuration errors will prevent service startup.

