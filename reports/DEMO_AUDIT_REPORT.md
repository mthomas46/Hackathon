# Demo Lifecycle Script Audit Report

**Generated**: 2025-10-08  
**Audited File**: `demo_mcp_lifecycle.py`  
**Status**: 🔴 **CRITICAL ISSUES FOUND**

---

## Executive Summary

The `demo_mcp_lifecycle.py` script has several critical issues that prevent it from working properly with the live services. By comparing the script against the e2e test suite, we've identified incorrect service endpoints, port mismatches, and missing service integrations.

**Key Findings:**
- ❌ MCP creation uses **wrong endpoint** (404 errors expected)
- ❌ Training workflow uses **wrong endpoint**
- ⚠️ Port mismatch for `llm-tagging` service (8022 vs 8021)
- ⚠️ Missing critical services (provisioner, coordinator)
- ⚠️ Offline services prevent full workflow execution

---

## Critical Issues

### 1. ❌ CRITICAL: Wrong MCP Creation Endpoint

**Location**: Line 340-344  
**Current Code**:
```python
response = await self.client.post(
    f"{self.services['mcp-training']}/api/v1/mcp/create",
    json=mcp_payload,
    ...
)
```

**Issue**: This endpoint **does not exist**. The script tries to create an MCP via `mcp-training` service, but according to e2e tests, MCPs should be provisioned via `mcp-provisioner` service.

**Expected Endpoint** (from `test_mcp_provisioning_workflow.py:23-28`):
```python
# Correct way:
provisioner_url = service_urls["mcp_provisioner"]  # NEW SERVICE
response = await http_client.post(
    f"{provisioner_url}/api/v1/mcps",  # Different endpoint
    json=test_mcp_config
)
```

**Impact**: 
- Always returns 404
- MCP ID is None
- All subsequent phases fail

---

### 2. ❌ CRITICAL: Wrong Training Endpoint

**Location**: Line 391-395  
**Current Code**:
```python
response = await self.client.post(
    f"{self.services['mcp-training']}/api/v1/training/start",
    json=training_payload,
    ...
)
```

**Issue**: Training jobs should be created via `training-coordinator` service, not `mcp-training`.

**Expected Endpoint** (from `test_training_pipeline.py:46-58`):
```python
# Correct way:
coordinator_url = service_urls["training_coordinator"]  # Different service
response = await http_client.post(
    f"{coordinator_url}/api/v1/jobs",  # Different endpoint
    params={
        "mcp_id": mcp_id,
        "name": job_name,
        "description": description,
        "data_sources": data_sources,
    }
)
# Then execute:
await http_client.post(f"{coordinator_url}/api/v1/jobs/{job_id}/execute")
```

**Impact**:
- Training always fails with 404
- Demo shows "simulated" instead of real training

---

### 3. ⚠️ Port Mismatch: LLM Tagging Service

**Location**: Line 56  
**Current**: `"llm-tagging": "http://localhost:8022"`  
**Expected** (from `conftest.py:41`): `"llm-tagging": "http://localhost:8021"`

**Impact**: 
- May connect to wrong service or nothing at all
- Works if port 8022 is actually correct in deployment, but inconsistent with tests

---

### 4. ⚠️ Missing Services

The demo script is missing several services that are used in the e2e test suite:

| Service | Purpose | Used In Test | Missing From Demo |
|---------|---------|--------------|-------------------|
| `mcp_provisioner` | MCP creation & lifecycle | `test_mcp_provisioning_workflow.py` | ✓ |
| `training_coordinator` | Training job management | `test_training_pipeline.py` | ✓ |
| `mcp_infrastructure` | Context registration | `test_mcp_provisioning_workflow.py` | ✓ |
| `mcp_interpreter` | Query parsing | `test_query_workflow.py` | ✓ |
| `mcp_orchestrator` | Workflow orchestration | `test_query_workflow.py` | ✓ |

**Impact**:
- Cannot demonstrate complete MCP lifecycle
- Script uses fallback/simulation modes

---

### 5. ⚠️ Offline Services

From the last run, the following services were offline:

| Service | Port | Status | Criticality |
|---------|------|--------|-------------|
| `mcp-registry` | 8102 | ✗ Offline | Medium |
| `mcp-gateway` | 8001 | ✗ Offline | High |
| `doc_store` | 5087 | ✗ Offline | Medium |
| `mock-data-generator` | 5065 | ✗ Offline | Low |

**Impact**:
- Gateway queries fail
- Some features use fallback logic
- Full ecosystem not validated

---

## Endpoint Comparison: Demo vs Tests

### Document Ingestion ✅
**Demo (Line 254)**: `POST /api/v1/ingestion/ingest` @ kafka-ingestion:5700  
**Tests (Line 44)**: `POST /api/v1/ingestion/ingest` @ kafka-ingestion:5700  
**Status**: ✅ **CORRECT**

### LLM Tagging ⚠️
**Demo (Line 300)**: `POST /api/v1/tagging/tag` @ llm-tagging:8022  
**Tests (Line 49)**: `POST /api/v1/tagging/tag` @ llm-tagging:8021  
**Status**: ⚠️ **PORT MISMATCH** (endpoint correct)

### MCP Creation ❌
**Demo (Line 342)**: `POST /api/v1/mcp/create` @ mcp-training:8100  
**Tests (Line 26)**: `POST /api/v1/mcps` @ mcp_provisioner:(unknown port)  
**Status**: ❌ **WRONG SERVICE & ENDPOINT**

### Training Start ❌
**Demo (Line 392)**: `POST /api/v1/training/start` @ mcp-training:8100  
**Tests (Line 48)**: `POST /api/v1/jobs` @ training_coordinator:(unknown port)  
**Status**: ❌ **WRONG SERVICE & ENDPOINT**

### MCP Registration ⚠️
**Demo (Line 447)**: `POST /api/v1/registry/register` @ mcp-registry:8102  
**Tests**: Not directly tested (allowed to fail in Line 86)  
**Status**: ⚠️ **SERVICE OFFLINE**

### Package Export ✅
**Demo (Line 532)**: `POST /api/v1/packages/export` @ mcp-package-manager:8103  
**Tests**: Not directly tested but service exists  
**Status**: ✅ **LIKELY CORRECT**

---

## Test Failure Analysis

Based on terminal output from last run:

```
Phase 5 (MCP Creation): ❌ Failed with 404
Phase 6 (Training): ❌ No MCP ID available (cascading failure)
Phase 7 (Registration): ❌ Service offline
Phase 8 (Gateway Query): ❌ Service offline
Phase 9 (Persistence): ⚠️ Simulated (service issues)
```

**Root Causes**:
1. Phase 5 fails because endpoint doesn't exist → creates None MCP ID
2. Phases 6-9 fail because no MCP ID (cascading)
3. Fallback logic prevents complete failure but doesn't test real system

---

## Architecture Mismatches

### Demo's Mental Model:
```
docs → kafka-ingestion → llm-tagging → mcp-training (create + train)
       → mcp-store → mcp-registry → mcp-gateway (query)
```

### Actual Architecture (from tests):
```
docs → kafka-ingestion → llm-tagging → mcp_provisioner (create)
       → training_coordinator (training jobs) → training workers
       → mcp_infrastructure (context) → mcp-gateway (query via interpreter/orchestrator)
```

**Key Differences**:
- Provisioning is separate from training
- Training uses coordinator + worker pattern (Celery)
- Gateway uses interpreter + orchestrator for queries
- Infrastructure service manages context

---

## Recommendations

### 🔴 Priority 1: Fix Critical Endpoints

1. **Add missing services**:
   ```python
   self.services = {
       # ... existing ...
       "mcp-provisioner": "http://localhost:????",  # Find correct port
       "training-coordinator": "http://localhost:????",  # Find correct port
       "mcp-infrastructure": "http://localhost:????",  # Find correct port
   }
   ```

2. **Update MCP creation** (Line 340):
   ```python
   response = await self.client.post(
       f"{self.services['mcp-provisioner']}/api/v1/mcps",
       json=mcp_payload,
       ...
   )
   ```

3. **Update training workflow** (Line 391):
   ```python
   # Create job
   response = await self.client.post(
       f"{self.services['training-coordinator']}/api/v1/jobs",
       params={...}
   )
   job_id = response.json()["job_id"]
   
   # Execute job
   await self.client.post(
       f"{self.services['training-coordinator']}/api/v1/jobs/{job_id}/execute"
   )
   ```

### ⚠️ Priority 2: Fix Port Mismatches

4. **Update llm-tagging port** (Line 56):
   ```python
   "llm-tagging": "http://localhost:8021",  # Was 8022
   ```

### 📝 Priority 3: Service Discovery

5. **Find missing service ports**:
   - Check `docker-compose-mcp-ecosystem.yml`
   - Check service documentation in `docs/`
   - Run service health checks to discover ports

6. **Start offline services**:
   - mcp-registry (port 8102)
   - mcp-gateway (port 8001)
   - doc_store (port 5087)
   - mock-data-generator (port 5065)

### ✅ Priority 4: Organization (Already Fixed)

7. **✅ Per-run directories**: IMPLEMENTED
   - Each run now creates `reports/run_TIMESTAMP_ID/`
   - Artifacts are isolated per execution

---

## Fixed Issues

### ✅ Per-Run Directory Structure

**Implementation** (Lines 69-82):
```python
# Create unique directory for this run
run_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
run_id = uuid.uuid4().hex[:8]
self.run_dir_name = f"run_{run_timestamp}_{run_id}"

self.base_reports_dir = Path("reports")
self.reports_dir = self.base_reports_dir / self.run_dir_name
```

**Benefits**:
- ✅ All artifacts from single run are together
- ✅ Easy to compare runs
- ✅ No filename collisions
- ✅ Clear audit trail

**Example Output**:
```
reports/
  run_20251007_185937_d558b070/
    ├── websocket_events_20251007_185939.json
    ├── mcp_lifecycle_report_20251007_190001.md
    └── mcp_lifecycle_report_20251007_190001.json
  run_20251007_190515_a3b2c1d4/
    ├── ...
```

### ✅ Improved Error Handling

**Implementation** (Lines 360-367):
```python
else:
    self.print_warning(f"MCP service returned {response.status_code}, using fallback")
    # Use fallback MCP ID to continue demo
    self.mcp_id = f"mcp_{uuid.uuid4().hex[:12]}"
    self.print_info(f"Using fallback MCP ID: {self.mcp_id}")
    self.results["mcp_created"] = "simulated"
    self.results["mcp_id"] = self.mcp_id
    return True
```

**Benefits**:
- ✅ Demo continues even with 404 errors
- ✅ Clear indication of fallback mode
- ✅ Remaining phases can still be tested

---

## Service Port Discovery Needed

To complete the fix, we need to find the ports for:

1. **mcp-provisioner**: Used for MCP lifecycle management
2. **training-coordinator**: Used for training job orchestration  
3. **mcp-infrastructure**: Used for context registration
4. **mcp-interpreter**: Used for query parsing
5. **mcp-orchestrator**: Used for workflow orchestration

**Action**: Search `docker-compose-mcp-ecosystem.yml` for these services.

---

## Testing Checklist

After fixes are applied:

- [ ] Phase 0: All services report healthy
- [ ] Phase 1-2: Document collection works
- [ ] Phase 3: Document ingestion succeeds
- [ ] Phase 4: LLM tagging succeeds
- [ ] Phase 5: MCP creation returns real MCP ID (not simulated)
- [ ] Phase 6: Training job created and executed
- [ ] Phase 7: MCP registered in registry
- [ ] Phase 8: Gateway queries return responses
- [ ] Phase 9: Export/import works
- [ ] Phase 10: Evergreen docs generated
- [ ] Phase 11: Reports saved to unique directory

---

## Conclusion

The demo script has solid structure but is calling incorrect endpoints. The issues are fixable:

1. **Root cause**: Script doesn't match actual service architecture
2. **Fix complexity**: Medium (need port discovery + endpoint updates)
3. **Current workaround**: Fallback mode allows script to complete but doesn't validate real system

**Next Steps**:
1. Find missing service ports in docker-compose
2. Update endpoints in demo script
3. Start offline services
4. Re-run and verify all phases pass

---

*This audit was performed by comparing `demo_mcp_lifecycle.py` against the e2e test suite in `tests/e2e/`.*
