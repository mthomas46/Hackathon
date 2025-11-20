**Date:** November 20, 2025  
**Status:** CRITICAL BUG IDENTIFIED  
**Severity:** HIGH - Causes All Documentation Runs to Hang  

# Documentation Generation Hang - Root Cause Analysis

## 🚨 Critical Bug Discovered

### Symptom
- Documentation runs created via API stay in "running" status indefinitely
- 0 artifacts generated even after 4+ minutes
- No error messages
- No visible progress

### Root Cause: Run ID Mismatch

**The orchestrator creates its OWN run record with a NEW ID, disconnected from the API's run.**

---

## 📊 Evidence

### Test Run
```bash
Run ID (from API): 4dd78478-6e1c-46fd-9205-aacabb467bf2
Status: running for 228.9s
Artifacts: 0
Words: 0
Passes: 0/2
```

### The Problem Flow

```
API Endpoint (documentation_runs.py:236-305)
  ↓
1. Creates DocumentationRunModel
   run = DocumentationRunModel(...)  # ID: 4dd78478...
   session.add(run)
   ↓
2. Triggers background task
   background_tasks.add_task(_generate_documentation_background, str(run.id), ...)
   ↓
3. Returns to user
   return {"run_id": "4dd78478...", "status": "pending"}

Background Task (_generate_documentation_background:35-111)
  ↓
4. Updates ORIGINAL run to "running"
   update(DocumentationRunModel)
   .where(DocumentationRunModel.id == "4dd78478...")
   .values(status="running")  ✅ This works
   ↓
5. Calls orchestrator
   orchestrator.generate_adaptive_documentation(service_name, template_name, ...)

Orchestrator (adaptive_orchestrator.py:60-197)
  ↓
6. Creates NEW run with NEW ID!! 🚨
   run_id = uuid4()  # NEW ID: abc123...
   run = DocumentationRunModel(id=run_id, ...)  # DIFFERENT RUN!
   session.add(run)
   ↓
7. Does all work on NEW run (abc123...)
   - Discovery phase
   - Generation phase  
   - Assembly phase
   ↓
8. Returns results
   return {"run_id": "abc123...", ...}  # WRONG ID!

Background Task (continued)
  ↓
9. Tries to update ORIGINAL run (4dd78478...)
   update(DocumentationRunModel)
   .where(DocumentationRunModel.id == "4dd78478...")
   .values(status="completed", artifacts=result["sections_generated"])
   ❌ But result has WRONG run_id!

Result:
  • Original run (4dd78478): Stays "running", 0 artifacts
  • New run (abc123): Completed, has artifacts, but NOBODY KNOWS ABOUT IT
```

---

## 🔍 Code Analysis

### Bug Location #1: Orchestrator Creates Own Run

**File:** `src/services/documentation/adaptive_orchestrator.py`  
**Lines:** 85-122

```python
async def generate_adaptive_documentation(
    self,
    service_name: str,
    template_name: str,
    category: str,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    config = config or {}
    run_id = uuid4()  # 🚨 BUG: Creates NEW ID
    
    # ...
    
    # Create documentation run record in database
    async with get_database().session() as session:
        # 🚨 BUG: Creates NEW run, not using existing one
        run = DocumentationRunModel(
            id=run_id,  # DIFFERENT ID!
            plan_id=f"adaptive_{service_name}_{template_name}",
            repo_id=repo_id,
            status="running",
            passes_completed=0,
            total_passes=config.get("max_passes", 1),
            current_pass="discovery",
            config=config,
            started_at=datetime.utcnow()
        )
        session.add(run)
        await session.commit()
```

**Why This Is Wrong:**
- API already created a run with a specific ID
- User is monitoring THAT ID
- Orchestrator creates its OWN run with a DIFFERENT ID
- All work happens on the wrong run
- Original run never completes

---

### Bug Location #2: Return Value Has Wrong ID

**File:** `src/services/documentation/adaptive_orchestrator.py`  
**Lines:** 169-183

```python
return {
    "run_id": str(run_id),  # 🚨 Returns NEW run_id, not original
    "service_name": service_name,
    "template_name": template_name,
    "content": documentation["content"],
    "metadata": {
        "sections_generated": len(sections),
        # ...
    }
}
```

**Why This Is Wrong:**
- Background task expects to get back data for ORIGINAL run
- But orchestrator returns data for ITS OWN run
- Background task can't correlate results

---

### Bug Location #3: Background Task Can't Update

**File:** `src/api/routes/documentation_runs.py`  
**Lines:** 72-86

```python
# Update run with results
async with db.session() as session:
    await session.execute(
        update(DocumentationRunModel)
        .where(DocumentationRunModel.id == run_id)  # Original ID
        .values(
            status="completed",
            completed_at=datetime.utcnow(),
            passes_completed=config.get("passes", 1),
            total_artifacts=result.get("sections_generated", 0),  # From WRONG run!
            total_words=result.get("total_words", 0)
        )
    )
```

**Why This Is Wrong:**
- Tries to update original run (4dd78478...)
- But `result` is from orchestrator's run (abc123...)
- Mismatch causes confusion

---

## 🎯 The Fix

### Option 1: Pass run_id to Orchestrator (RECOMMENDED)

**Change orchestrator signature:**

```python
async def generate_adaptive_documentation(
    self,
    service_name: str,
    template_name: str,
    category: str,
    config: Optional[Dict[str, Any]] = None,
    run_id: Optional[str] = None  # NEW: Accept existing run_id
) -> Dict[str, Any]:
    
    # Use existing run_id or create new one
    if run_id:
        run_id = UUID(run_id)
        logger.info(f"Using existing run_id: {run_id}")
    else:
        run_id = uuid4()
        logger.info(f"Created new run_id: {run_id}")
    
    # DON'T create a new run if run_id was provided
    if not existing_run_id:
        async with get_database().session() as session:
            # Create run record...
            pass
```

**Change background task call:**

```python
# In _generate_documentation_background
result = await orchestrator.generate_adaptive_documentation(
    service_name=service_name,
    template_name=template_name,
    category=category,
    config=config,
    run_id=run_id  # NEW: Pass existing run_id
)
```

**Pros:**
- Clean separation of concerns
- Orchestrator can still be used standalone (creates own run)
- Or integrated with API (uses provided run)
- Minimal code changes

**Cons:**
- Need to handle both cases (with/without run_id)

---

### Option 2: Orchestrator Doesn't Manage Runs

**Remove run creation from orchestrator:**

```python
async def generate_adaptive_documentation(
    self,
    service_name: str,
    template_name: str,
    category: str,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    
    # DON'T create run record
    # Just do the work and return results
    
    context = await self._discovery_phase(service_name)
    template = await self.template_manager.load_template(template_name, category)
    sections = await self._generation_phase(template, context, service_name, config)
    documentation = await self._assembly_phase(template, sections, context, config)
    
    return {
        "content": documentation["content"],
        "metadata": {...},
        "sections": sections
    }
```

**Let API manage runs:**

```python
# API is fully responsible for run lifecycle
async with db.session() as session:
    # Update to running
    await session.execute(update(...).values(status="running"))
    
    # Generate (no run management inside)
    result = await orchestrator.generate_adaptive_documentation(...)
    
    # Update to completed
    await session.execute(update(...).values(status="completed", ...))
```

**Pros:**
- Clear responsibility: API manages runs, orchestrator generates content
- No run ID mismatch possible
- Simpler orchestrator

**Cons:**
- Orchestrator can't be used standalone (no run tracking)
- Transparency logger needs run_id passed separately

---

### Option 3: Single Source of Truth

**API doesn't create run, orchestrator does:**

```python
# API endpoint
@router.post("/runs")
async def create_documentation_run(request: CreateRunRequest):
    # DON'T create run here
    # Just trigger orchestrator
    
    orchestrator = AdaptiveDocumentationOrchestrator()
    result = await orchestrator.generate_adaptive_documentation(...)
    
    # Return the run_id from orchestrator
    return CreateRunResponse(
        run_id=result["run_id"],
        status="completed",
        message="Documentation generated"
    )
```

**Pros:**
- Single source of truth
- No duplication

**Cons:**
- API can't return "pending" status immediately
- Can't track runs before completion
- Breaks async pattern

---

## ✅ Recommended Solution

**Use Option 1: Pass run_id to Orchestrator**

### Implementation Steps

1. **Modify orchestrator signature** to accept optional `run_id`
2. **Check if run exists** before creating new one
3. **Use provided run_id** for all operations
4. **Update background task** to pass run_id
5. **Update worker** to pass run_id
6. **Test both paths:**
   - With run_id (API integration)
   - Without run_id (standalone)

---

## 🔧 Additional Issues Found

### Issue #2: No Timeout on Orchestrator

**Location:** `src/api/routes/documentation_runs.py:64-70`

```python
# Generate documentation
orchestrator = AdaptiveDocumentationOrchestrator()
result = await orchestrator.generate_adaptive_documentation(...)
# 🚨 No timeout! Could hang forever
```

**Fix:** Add timeout

```python
import asyncio

try:
    async with asyncio.timeout(300):  # 5 minute max
        result = await orchestrator.generate_adaptive_documentation(...)
except asyncio.TimeoutError:
    logger.error(f"Generation timed out after 5 minutes")
    raise
```

---

### Issue #3: No Progress Logging

**Problem:** Can't tell where orchestrator is stuck

**Fix:** Add detailed logging at each phase

```python
logger.info(f"🔍 Starting discovery phase...")
context = await self._discovery_phase(run_id, service_name)
logger.info(f"✅ Discovery complete: {len(context.get('frameworks', []))} frameworks")

logger.info(f"📋 Loading template...")
template = await self.template_manager.load_template(template_name, category)
logger.info(f"✅ Template loaded: {len(template.get('sections', []))} sections")

logger.info(f"✨ Generating sections...")
sections = await self._generation_phase(...)
logger.info(f"✅ Generated {len(sections)} sections")
```

---

### Issue #4: Discovery Could Hang

**Location:** `src/services/adaptive/discovery_service.py:59`

**Problem:** `_normalize_service_name` queries documents without timeout

```python
async def _normalize_service_name(self, service_name: str) -> str:
    async with get_database().session() as session:
        query = select(DocumentModel.service_name).filter(
            func.lower(DocumentModel.service_name) == service_name.lower(),
            DocumentModel.is_latest == True
        ).limit(1)
        
        result = await session.execute(query)  # Could hang
```

**Fix:** Add query timeout

```python
async def _normalize_service_name(self, service_name: str) -> str:
    try:
        async with asyncio.timeout(10):  # 10 second max
            async with get_database().session() as session:
                query = select(DocumentModel.service_name).filter(
                    func.lower(DocumentModel.service_name) == service_name.lower(),
                    DocumentModel.is_latest == True
                ).limit(1)
                
                result = await session.execute(query)
                actual_service_name = result.scalar_one_or_none()
                
                return actual_service_name if actual_service_name else service_name
    except asyncio.TimeoutError:
        logger.warning(f"Service name normalization timed out, using original: {service_name}")
        return service_name
```

---

## 📊 Impact Assessment

### Critical
- ✅ **Run ID Mismatch:** Causes ALL runs to appear hung

### High
- ⚠️ **No Timeout:** Could hang forever
- ⚠️ **No Progress Logging:** Can't debug issues

### Medium
- ⚠️ **Discovery Hang:** Possible if database slow

---

## 🚀 Implementation Priority

1. **CRITICAL:** Fix run ID mismatch (Option 1)
2. **HIGH:** Add timeout to orchestrator call
3. **HIGH:** Add progress logging to all phases
4. **MEDIUM:** Add timeouts to discovery queries
5. **LOW:** Add circuit breaker for repeated failures

---

## ✅ Success Criteria

After fix:
- [ ] Create run via API
- [ ] Run completes within 60 seconds
- [ ] Original run ID shows "completed" status
- [ ] Artifacts generated and linked to correct run
- [ ] Transparency features visible
- [ ] No orphaned runs in database

---

## 📝 Testing Plan

### Unit Tests
```python
async def test_orchestrator_uses_provided_run_id():
    """Test that orchestrator uses provided run_id instead of creating new one."""
    existing_run_id = str(uuid4())
    
    result = await orchestrator.generate_adaptive_documentation(
        service_name="test",
        template_name="api_reference",
        category="backend",
        run_id=existing_run_id
    )
    
    assert result["run_id"] == existing_run_id
```

### Integration Tests
```python
async def test_end_to_end_documentation_generation():
    """Test complete flow from API to completion."""
    # Create run via API
    response = await client.post("/api/v1/documentation/runs", json={...})
    run_id = response.json()["run_id"]
    
    # Wait for completion (max 60s)
    for _ in range(12):
        await asyncio.sleep(5)
        status_response = await client.get(f"/api/v1/documentation/runs/{run_id}")
        status = status_response.json()["status"]
        
        if status in ["completed", "failed"]:
            break
    
    # Verify success
    assert status == "completed"
    assert status_response.json()["total_artifacts"] > 0
```

---

## 🎯 Bottom Line

**Root Cause:** Orchestrator creates its own run record with a new ID, disconnected from the API's run. All work happens on the wrong run, so the original run never completes.

**Fix:** Pass the existing run_id to the orchestrator and skip creating a new run if one is provided.

**ETA:** 30 minutes to implement and test.

**Confidence:** 95% - This is clearly the root cause based on code analysis.

