# MCP Training Document Access - Investigation & Fix Plan

**Date**: October 8, 2025  
**Status**: 🔍 **SYSTEMATIC INVESTIGATION IN PROGRESS**  
**Issue**: MCP containers cannot access training documents after training job submission

---

## 🎯 Problem Statement

**Symptom**: All MCP queries return `"Error accessing training documents: 0"`

**Context**:
- ✅ Training jobs create successfully
- ✅ Training jobs execute successfully  
- ✅ Documents ingested to doc_store successfully
- ❌ MCP queries return 0 documents
- ⚠️ Affects BOTH demos (systemic issue)

---

## 🔍 Investigation Strategy

### Phase 1: Service Audit
Audit all services involved in the document flow:

1. **kafka-ingestion-service** (Port 5700)
   - Receives documents from demos
   - Forwards to doc_store
   - Audit: Logging, error handling, doc_store connection

2. **doc_store** (Port 5087)
   - Stores ingested documents
   - Provides search/retrieval APIs
   - Audit: Storage verification, query endpoints, document persistence

3. **mcp-provisioner** (Port 5400)
   - Creates MCP containers
   - Audit: Container configuration, network access, environment variables

4. **mcp-training-coordinator** (Port 5600)
   - Creates training jobs
   - Executes training
   - Audit: Document fetching, MCP communication, training payload

5. **MCP Container** (Dynamic port)
   - Receives training data
   - Stores documents internally
   - Responds to queries
   - Audit: Document storage, query handling, doc_store access

### Phase 2: Logging Enhancement
Add comprehensive logging at each step:

1. **Document Ingestion Logging**
   - Log when document enters kafka-ingestion
   - Log doc_store POST response
   - Log document IDs and metadata

2. **Training Job Logging**
   - Log training job creation
   - Log document IDs sent to training
   - Log MCP ID association
   - Log training completion status

3. **MCP Container Logging**
   - Log documents received
   - Log document storage
   - Log query requests
   - Log document retrieval attempts

### Phase 3: Diagnostic Testing
Create tests to expose the issue:

1. **Test: Document Persistence in doc_store**
   ```python
   test_doc_store_has_documents()
   - Ingest documents
   - Verify doc_store has them
   - Query by ID
   ```

2. **Test: Training Job Document Flow**
   ```python
   test_training_job_includes_documents()
   - Create training job
   - Verify documents passed to coordinator
   - Check training payload
   ```

3. **Test: MCP Container Document Access**
   ```python
   test_mcp_has_training_documents()
   - Provision MCP
   - Train MCP
   - Query MCP directly
   - Assert documents > 0
   ```

4. **Test: End-to-End Document Flow**
   ```python
   test_complete_document_flow()
   - Ingest → doc_store
   - Train → MCP
   - Query → Response with content
   ```

### Phase 4: Root Cause Identification
Based on logging and tests, identify exact failure point:

- [ ] Documents reach doc_store?
- [ ] Training coordinator fetches from doc_store?
- [ ] Training coordinator sends to MCP?
- [ ] MCP receives documents?
- [ ] MCP stores documents?
- [ ] MCP queries its storage?

### Phase 5: Solution Implementation
Implement fix based on findings:

**Possible Solutions**:
1. **Add doc_store URL to MCP environment**
2. **Pass documents directly in training payload**
3. **Add async wait for training completion**
4. **Fix MCP container networking**
5. **Mount documents as volumes**

---

## 📋 Service Workflow Audit

### Current Flow (As Designed)
```
1. Demo → kafka-ingestion-service (POST /api/v1/ingestion/ingest)
2. kafka-ingestion → doc_store (POST /api/v1/documents)
3. Demo → mcp-provisioner (POST /api/v1/mcps)
4. Demo → mcp-training-coordinator (POST /api/v1/jobs)
5. Demo → mcp-training-coordinator (POST /api/v1/jobs/{id}/execute)
6. Demo → MCP container (POST /query)
```

### Missing Link (Hypothesis)
```
❓ mcp-training-coordinator → doc_store (GET /api/v1/documents?)
❓ mcp-training-coordinator → MCP container (POST /train with documents?)
❓ MCP container → doc_store (GET /api/v1/documents?)
```

**Key Question**: How do documents get FROM doc_store TO the MCP container?

---

## 🔧 Investigation Tasks

### Task 1: Audit kafka-ingestion-service
- [ ] Check if documents actually reach doc_store
- [ ] Add logging for doc_store responses
- [ ] Verify document IDs are tracked
- [ ] Test doc_store connectivity

### Task 2: Audit doc_store
- [ ] Verify documents persist after ingestion
- [ ] Test GET /api/v1/documents endpoint
- [ ] Test search endpoint with query
- [ ] Check database/storage backend

### Task 3: Audit mcp-training-coordinator
- [ ] Review training job creation code
- [ ] Check if it fetches documents from doc_store
- [ ] Review job execution code
- [ ] Check if it sends documents to MCP
- [ ] Add logging for document flow

### Task 4: Audit MCP Container
- [ ] Find MCP container implementation
- [ ] Review training endpoint (/train?)
- [ ] Review query endpoint
- [ ] Check document storage mechanism
- [ ] Verify doc_store connectivity

### Task 5: Create Diagnostic Script
- [ ] Script to query doc_store for documents
- [ ] Script to check MCP container logs
- [ ] Script to trace document IDs through system
- [ ] Script to test each service endpoint

---

## 📊 Expected Findings

### Scenario A: Documents Don't Persist in doc_store
**Symptom**: doc_store returns empty list  
**Fix**: Fix doc_store persistence  
**Likelihood**: Low (doc_store tests passing)

### Scenario B: Training Coordinator Doesn't Fetch Documents
**Symptom**: Training job has no documents  
**Fix**: Add doc_store query to training coordinator  
**Likelihood**: High (most likely cause)

### Scenario C: Training Coordinator Doesn't Send to MCP
**Symptom**: MCP never receives documents  
**Fix**: Add document payload to MCP training call  
**Likelihood**: High (possible cause)

### Scenario D: MCP Container Can't Access doc_store
**Symptom**: MCP tries but fails to connect  
**Fix**: Configure Docker networking  
**Likelihood**: Medium (network isolation)

### Scenario E: Async Training Not Complete
**Symptom**: Query happens before training done  
**Fix**: Add wait/polling for completion  
**Likelihood**: Medium (timing issue)

---

## 🎯 Success Criteria

### Investigation Complete When:
- [ ] Document flow fully traced with logs
- [ ] Exact failure point identified
- [ ] Root cause documented
- [ ] Solution designed and validated

### Fix Complete When:
- [ ] MCP queries return actual document content
- [ ] Training document count > 0
- [ ] All diagnostic tests pass
- [ ] Both demos work end-to-end

---

## 📝 Action Items

### Immediate (Next Steps)
1. Create diagnostic test suite
2. Add logging to all services
3. Run tests and collect logs
4. Identify exact failure point

### Short-Term
5. Design solution based on findings
6. Implement fix with TDD
7. Validate with both demos
8. Update documentation

### Long-Term
9. Add monitoring for document flow
10. Create health checks for training
11. Add alerting for failures

---

**Status**: 🚀 **READY TO BEGIN INVESTIGATION**

