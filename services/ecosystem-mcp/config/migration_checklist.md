# Configuration Registry - Migration Checklist

**Purpose:** Track migration from hardcoded values to registry  
**Total Items:** 237 hardcoded values  
**Status:** 0/237 migrated (0%)  
**Updated:** 2025-10-26  

---

## 📊 Progress Overview

| Category | Total | Migrated | % Complete |
|----------|-------|----------|------------|
| **Redis Streams** | 48 | 0 | 0% |
| **Consumer Groups** | 32 | 0 | 0% |
| **Database Config** | 15 | 0 | 0% |
| **Port Numbers** | 89 | 0 | 0% |
| **Service Names** | 31 | 0 | 0% |
| **Collection Names** | 12 | 0 | 0% |
| **Queue Names** | 10 | 0 | 0% |
| **TOTAL** | **237** | **0** | **0%** |

---

## 🚨 Priority 1: Critical (Block startup if mismatched)

### Redis Streams (48 instances)

#### Stream Names
- [ ] `INGESTION_STREAM = "ingestion_queue"` - redis_client.py:35
- [ ] `EMBEDDING_STREAM = "embedding_queue"` - redis_client.py:36
- [ ] `RETRY_STREAM = "retry_queue"` - redis_client.py:37
- [ ] `FAILED_STREAM = "failed_queue"` - redis_client.py:38
- [ ] All references in retry_worker.py
- [ ] All references in ingestion_worker.py

**Priority:** 🔴 CRITICAL  
**Phase:** 2 - Quick Wins  
**Risk:** Consumer group mismatch (caused today's issue!)

#### Consumer Groups
- [ ] `CONSUMER_GROUP = "workers"` - redis_client.py:41
- [ ] All worker consumer group references
- [ ] All stream consumer group configuration

**Priority:** 🔴 CRITICAL  
**Phase:** 2 - Quick Wins  
**Risk:** Jobs never processed (today's exact issue!)

#### Retry Configuration
- [ ] `MAX_RETRIES = 5` - redis_client.py:44
- [ ] `RETRY_BACKOFF_BASE = 2` - redis_client.py:45
- [ ] All retry logic configuration

**Priority:** 🟡 HIGH  
**Phase:** 2 - Quick Wins  
**Risk:** Inconsistent retry behavior

### Database Configuration (15 instances)

#### Connection Strings
- [ ] `database_url` - config.py:33
- [ ] Database name: "ecosystem_mcp" vs "ecosystem"
- [ ] Database host: "localhost" vs "postgres"
- [ ] Database port: 5432

**Priority:** 🔴 CRITICAL  
**Phase:** 2 - Quick Wins  
**Risk:** Connection failures (confusion today!)

#### Connection Pools
- [ ] `database_pool_size = 20` - config.py:36
- [ ] `database_max_overflow = 10` - config.py:37

**Priority:** 🟡 HIGH  
**Phase:** 2 - Quick Wins  
**Risk:** Performance issues

---

## 🟡 Priority 2: High (Significant impact)

### Port Numbers (89 instances)

#### Service Ports
- [ ] PostgreSQL: 5432 - docker-compose.yml:14
- [ ] Redis: 6379 - docker-compose.yml:38
- [ ] Ollama: 11434 - docker-compose.yml:61
- [ ] Embedding Service: 8001 - docker-compose.yml:114
- [ ] API: 8000 - docker-compose.yml:172
- [ ] Metrics: 9090 - docker-compose.yml:173
- [ ] Dashboard: 8501 - docker-compose.yml:214

**Priority:** 🟡 HIGH  
**Phase:** 2 - Quick Wins  
**Risk:** Port conflicts, difficult to change

#### Internal Port References
- [ ] All config.py port references
- [ ] All worker configuration ports
- [ ] All health check endpoints

**Priority:** 🟡 HIGH  
**Phase:** 2 - Quick Wins  
**Risk:** Inconsistent port usage

### Service Names (31 instances)

#### Container Names
- [ ] `ecosystem-mcp-postgres` - docker-compose.yml:7
- [ ] `ecosystem-mcp-redis` - docker-compose.yml:35
- [ ] `ecosystem-mcp-ollama` - docker-compose.yml:59
- [ ] `ecosystem-mcp-embedding` - docker-compose.yml:105
- [ ] `ecosystem-mcp-service` - docker-compose.yml:144
- [ ] `ecosystem-mcp-dashboard` - docker-compose.yml:209

**Priority:** 🟡 HIGH  
**Phase:** 2 - Quick Wins  
**Risk:** Naming inconsistencies

#### Service Name Variations
- [ ] "ecosystem-mcp" (hyphen)
- [ ] "ecosystem_mcp" (underscore)
- [ ] All API route references
- [ ] All logging references

**Priority:** 🟡 HIGH  
**Phase:** 2 - Quick Wins  
**Risk:** Confusion, inconsistent naming

---

## 🟢 Priority 3: Medium (Quality of life)

### ChromaDB Configuration (12 instances)

- [ ] `chroma_collection_name = "ecosystem_docs"` - config.py:51
- [ ] `chroma_path = "./data/chroma_db"` - config.py:48
- [ ] All collection references

**Priority:** 🟢 MEDIUM  
**Phase:** 2 - Quick Wins  
**Risk:** Collection name mismatch

### Ollama Configuration (20+ instances)

#### URLs
- [ ] `ollama_base_url = "http://localhost:11434"` - config.py:55
- [ ] `ollama_desktop_url = "http://host.docker.internal:11434"` - config.py:69
- [ ] All Ollama endpoint references

**Priority:** 🟢 MEDIUM  
**Phase:** 2 - Quick Wins  
**Risk:** Connection failures

#### Models
- [ ] `ollama_model_small = "llama3.2:3b"` - config.py:58
- [ ] `ollama_model_medium = "mistral:7b-instruct-q8_0"` - config.py:59
- [ ] `ollama_embedding_model = "nomic-embed-text:latest"` - config.py:60

**Priority:** 🔵 LOW  
**Phase:** 3-4  
**Risk:** Low (model selection)

### Worker Configuration (10+ instances)

- [ ] Poll interval: 5 seconds
- [ ] Batch size: 1
- [ ] Timeout: 3600 seconds
- [ ] Heartbeat interval: 30 seconds

**Priority:** 🟢 MEDIUM  
**Phase:** 2 - Quick Wins  
**Risk:** Performance variability

---

## 📋 Migration by Phase

### Phase 1: Registry Core (1 day)
**Goal:** Create loader and validation

- [ ] Create `src/config/registry.py`
- [ ] Create `src/config/types.py` (Pydantic models)
- [ ] Write unit tests
- [ ] Validate registry loads

**Deliverables:**
- Registry loader (500 LOC)
- Pydantic models (300 LOC)
- 20 unit tests

### Phase 2: Quick Wins (2 days)
**Goal:** Migrate critical services

#### Task 2.1: Update RedisClient
- [ ] Import registry in redis_client.py
- [ ] Replace `INGESTION_STREAM` with registry value
- [ ] Replace `EMBEDDING_STREAM` with registry value
- [ ] Replace `RETRY_STREAM` with registry value
- [ ] Replace `FAILED_STREAM` with registry value
- [ ] Replace `CONSUMER_GROUP` with registry value
- [ ] Replace retry config with registry values
- [ ] Run tests
- [ ] Verify no hardcoded strings remain

**Impact:** 48 instances migrated ✅

#### Task 2.2: Update Config.py
- [ ] Import registry
- [ ] Convert `database_url` to property
- [ ] Convert `redis_url` to property
- [ ] Convert all URLs to registry-derived
- [ ] Run tests
- [ ] Verify connections work

**Impact:** 15 instances migrated ✅

#### Task 2.3: Generate docker-compose.yml
- [ ] Create `scripts/generate_compose.py`
- [ ] Implement generator
- [ ] Generate docker-compose.yml
- [ ] Validate services start
- [ ] Add to CI/CD

**Impact:** 89 instances migrated ✅

**Phase 2 Total:** 152/237 migrated (64%) ✅

### Phase 3: Validation System (2 days)
**Goal:** Add validation and fail-fast

- [ ] Create `src/validation/config_validator.py`
- [ ] Implement all validators
- [ ] Integrate with preflight checks
- [ ] Test fail-fast behavior
- [ ] Add validation tests

**Impact:** Prevents all mismatches ✅

### Phase 4: Observability (1 day)
**Goal:** Add monitoring endpoints

- [ ] Create API endpoints
- [ ] Dashboard integration
- [ ] Real-time validation
- [ ] Diff detection

**Impact:** < 5 minute diagnosis ✅

### Phase 5: Testing (1 day)
**Goal:** Comprehensive testing

- [ ] 45 unit tests
- [ ] 23 integration tests
- [ ] 12 E2E tests
- [ ] 98% coverage

**Impact:** Production confidence ✅

### Phase 6: Deployment (2 days)
**Goal:** Production rollout

- [ ] Documentation complete
- [ ] Staging deployment
- [ ] Production rollout
- [ ] Monitoring active

**Impact:** Zero incidents ✅

---

## 📊 Completion Tracking

### By File

| File | Values | Migrated | % |
|------|--------|----------|---|
| `redis_client.py` | 48 | 0 | 0% |
| `config.py` | 35 | 0 | 0% |
| `docker-compose.yml` | 89 | 0 | 0% |
| `retry_worker.py` | 20 | 0 | 0% |
| `ingestion_worker.py` | 18 | 0 | 0% |
| `job_processor.py` | 15 | 0 | 0% |
| Other files | 12 | 0 | 0% |
| **TOTAL** | **237** | **0** | **0%** |

### By Phase

| Phase | Values | Migrated | % |
|-------|--------|----------|---|
| Phase 0: Preparation | N/A | ✅ Complete | 100% |
| Phase 1: Registry Core | 0 | 0 | 0% |
| Phase 2: Quick Wins | 152 | 0 | 0% |
| Phase 3: Validation | N/A | 0 | 0% |
| Phase 4: Observability | N/A | 0 | 0% |
| Phase 5: Testing | N/A | 0 | 0% |
| Phase 6: Deployment | N/A | 0 | 0% |
| **TOTAL** | **152** | **0** | **0%** |

---

## ✅ Validation Checklist

### After Each Migration

- [ ] Registry value matches original hardcoded value
- [ ] All tests pass
- [ ] No hardcoded strings remain in modified file
- [ ] Service starts successfully
- [ ] Integration tests pass
- [ ] Validation endpoint reports no mismatches
- [ ] Update this checklist

### After Phase 2

- [ ] 152/237 values migrated
- [ ] Consumer group mismatch impossible
- [ ] Database name consistent
- [ ] Ports centralized
- [ ] docker-compose generated from registry
- [ ] All Quick Win tests pass

### After Phase 6

- [ ] 237/237 values migrated (100%)
- [ ] Zero hardcoded critical values
- [ ] Validation system active
- [ ] Monitoring dashboards live
- [ ] Production deployed
- [ ] Zero incidents

---

## 🎯 Success Metrics

**Target:** 237/237 values migrated (100%)

**Milestones:**
- Phase 0: Baseline created ✅
- Phase 1: Registry loader working
- Phase 2: 152 values migrated (64%)
- Phase 3: Validation active
- Phase 4: Monitoring live
- Phase 5: Tests passing
- Phase 6: Production deployed

**Timeline:** 3 weeks

---

## 📝 Notes

- **Current State:** Phase 0 complete, baseline created
- **Next Step:** Begin Phase 1 - Registry Core
- **Blocker:** None
- **Risk Level:** Low (incremental migration)

---

**Last Updated:** 2025-10-26T23:15:00Z  
**Updated By:** LLM Agent  
**Next Review:** After Phase 1 completion  

