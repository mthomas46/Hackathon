# Timeline Analysis: Master Implementation Plan
## Living Document - Track Progress Across Sessions

**Purpose:** Master implementation plan with phases, sub-phases, and checkpoints  
**Status:** 🟢 PHASE 1 CORE COMPLETE  
**Current Phase:** Phase 1 (80% Complete - Tests Pending)  
**Last Updated:** 2025-10-22  
**Last Session:** Phase 1 core implementation complete, tests pending

---

## 📋 Table of Contents

1. [How to Use This Document](#how-to-use-this-document)
2. [Quick Status Overview](#quick-status-overview)
3. [Phase Overview](#phase-overview)
4. [Detailed Phase Plans](#detailed-phase-plans)
5. [Testing Matrix](#testing-matrix)
6. [Session Handoff Protocol](#session-handoff-protocol)
7. [Troubleshooting Guide](#troubleshooting-guide)

---

## How to Use This Document

### For LLM Sessions

**Starting a New Session:**
1. Read the [Quick Status Overview](#quick-status-overview) section
2. Check the **Current Phase** and **Current Sub-Phase**
3. Read the **Session Handoff Notes** for context
4. Review the **Blockers** section
5. Continue from the next incomplete task

**During a Session:**
1. Update task status as you complete them (⏳ → ✅)
2. Add notes to **Session Notes** for each sub-phase
3. Document any issues in **Blockers**
4. Update **Last Updated** timestamp
5. Update **Last Session** summary

**Ending a Session:**
1. Update **Current Phase** and **Current Sub-Phase**
2. Write clear **Session Handoff Notes**
3. Commit this document with progress
4. Commit all code changes
5. Update **Quick Status Overview**

### Status Symbols

- ⏳ **In Progress** - Currently working on this
- ✅ **Complete** - Finished and tested
- ❌ **Blocked** - Cannot proceed (see Blockers section)
- ⏸️ **Paused** - Temporarily stopped
- 🔄 **Needs Revision** - Complete but needs changes
- ⭐ **Ready to Start** - Next task to begin

---

## Quick Status Overview

### Current State

```
┌─────────────────────────────────────────────────────────────────┐
│ TIMELINE ANALYSIS IMPLEMENTATION STATUS                         │
├─────────────────────────────────────────────────────────────────┤
│ Current Phase:     Phase 1 - Core Implementation (80%)           │
│ Current Sub-Phase: 1.7 - Testing (Pending)                       │
│ Progress:          8/31 features implemented (26%)               │
│ Tests Passing:     0/0 (Tests not yet written)                   │
│ Blockers:          None                                          │
│ Last Updated:      2025-10-22 19:30:00                           │
│ Last Session:      Phase 1 core services and API complete        │
└─────────────────────────────────────────────────────────────────┘
```

### Phase Completion Status

| Phase | Name | Status | Progress | Tests | Blockers |
|-------|------|--------|----------|-------|----------|
| 0 | Planning | ✅ Complete | 100% | N/A | None |
| 1 | Core Timeline + Confidence | 🟡 In Progress | 80% | 0/0 | Tests pending |
| 2 | Temporal RAG + Maintenance | ⏸️ Waiting | 0% | 0/0 | Phase 1 |
| 3 | Gap/Drift + Advanced | ⏸️ Waiting | 0% | 0/0 | Phase 2 |
| 4 | Doc Generation + Reports | ⏸️ Waiting | 0% | 0/0 | Phase 3 |
| 5 | Dashboard Integration | ⏸️ Waiting | 0% | 0/0 | Phase 4 |
| 6 | Dynamic Temporal RAG | ⏸️ Waiting | 0% | 0/0 | Phase 5 |

### Session Handoff Notes

**From:** Initial Planning Session  
**To:** Next Implementation Session  
**Date:** 2025-10-22

**Context:**
- All 6 planning documents have been created and validated
- Architecture has been designed with 97%+ service reuse
- Graceful fallback system has been specified
- Dynamic Temporal RAG enhancement has been added
- Ready to begin Phase 1 implementation

**Next Steps:**
1. Begin Phase 1, Sub-Phase 1.1: Database Schema Design
2. Create timeline-related database models
3. Write database migrations
4. Set up testing infrastructure

**Important Notes:**
- Ensure all new services follow thin facade pattern
- Leverage existing services (97%+ reuse target)
- Implement confidence checks in all temporal features
- Add comprehensive logging and feedback
- Document all API endpoints with OpenAPI/Swagger

**Blockers:**
- None

---

## Phase Overview

### Timeline Summary

```
Phase 0: Planning (1 week) ✅ COMPLETE
Phase 1: Core Timeline + Confidence (1 week) ⭐ NEXT
Phase 2: Temporal RAG + Maintenance (1 week)
Phase 3: Gap/Drift + Advanced (1 week)
Phase 4: Doc Generation + Reports (1 week)
Phase 5: Dashboard Integration (1 week)
Phase 6: Dynamic Temporal RAG (2 weeks)
─────────────────────────────────────────────
Total: 8 weeks (including planning)
```

### Dependency Graph

```
Phase 0 (Planning)
    ↓
Phase 1 (Core Timeline + Confidence)
    ↓
Phase 2 (Temporal RAG + Maintenance)
    ↓
Phase 3 (Gap/Drift + Advanced)
    ↓
Phase 4 (Doc Generation + Reports)
    ↓
Phase 5 (Dashboard Integration)
    ↓
Phase 6 (Dynamic Temporal RAG)
```

---

## Detailed Phase Plans

---

## Phase 0: Planning ✅ COMPLETE

**Duration:** 1 week  
**Status:** ✅ Complete  
**Progress:** 100%  
**Tests:** N/A

### Deliverables

- ✅ Original Plan (v1.0) - `TIMELINE_BASED_DOCUMENT_ANALYSIS_PLAN.md`
- ✅ Enriched Plan (v2.0) - `TIMELINE_ANALYSIS_ENRICHED_PLAN.md`
- ✅ Final Refined Plan (v3.0) - `TIMELINE_ANALYSIS_FINAL_REFINED_PLAN.md`
- ✅ Graceful Fallback Addendum (v3.1) - `TIMELINE_ANALYSIS_GRACEFUL_FALLBACK_ADDENDUM.md`
- ✅ Complete Implementation Guide - `TIMELINE_ANALYSIS_COMPLETE_IMPLEMENTATION_GUIDE.md`
- ✅ Dynamic Temporal RAG Enhancement (v3.2) - `TIMELINE_ANALYSIS_DYNAMIC_TEMPORAL_RAG_ENHANCEMENT.md`
- ✅ Master Implementation Plan - `TIMELINE_ANALYSIS_MASTER_IMPLEMENTATION_PLAN.md`

### Session Notes

**Session 1 (2025-10-22):**
- Created all planning documents
- Validated against codebase (confirmed two ingestion modes)
- Designed graceful fallback system
- Added dynamic temporal RAG enhancement
- Total: 120+ pages of comprehensive planning

---

## Phase 1: Core Timeline + Confidence System

**Duration:** 1 week (5 working days)  
**Status:** ⭐ Ready to Start  
**Progress:** 0%  
**Tests:** 0/0 passing

### Goals

- Implement core timeline infrastructure
- Implement temporal confidence system
- Create database schema and migrations
- Add API endpoints for timeline management
- Implement pre-flight validation
- Add comprehensive testing, logging, and feedback

### Sub-Phases

---

### Sub-Phase 1.1: Database Schema Design & Migration

**Duration:** 1 day  
**Status:** ⭐ Ready to Start  
**Dependencies:** None

#### Tasks

- ⏳ **Task 1.1.1:** Design database schema
  - [ ] Create `TimelineModel` (with confidence fields)
  - [ ] Create `TimePeriodModel`
  - [ ] Create `DocumentPlacementModel`
  - [ ] Create `TemporalConfidenceMetadataModel` (JSONB)
  - [ ] Add indexes for performance
  - [ ] Document schema in docstrings
  - **Location:** `services/ecosystem-mcp/src/storage/db_models.py`
  - **Reference:** See `TIMELINE_ANALYSIS_ENRICHED_PLAN.md` Section 4.2

- ⏳ **Task 1.1.2:** Create database migration
  - [ ] Create migration file: `009_add_timeline_tables.py`
  - [ ] Implement `upgrade()` function
  - [ ] Implement `downgrade()` function (for rollback)
  - [ ] Add migration to migration runner
  - [ ] Test migration on clean database
  - [ ] Test rollback
  - **Location:** `services/ecosystem-mcp/src/storage/migrations/`
  - **Reference:** See existing migrations for pattern

- ⏳ **Task 1.1.3:** Add Pydantic models
  - [ ] Create `Timeline` model
  - [ ] Create `TimePeriod` model
  - [ ] Create `DocumentPlacement` model
  - [ ] Create `TemporalConfidence` enum
  - [ ] Add validation rules
  - **Location:** `services/ecosystem-mcp/src/models/timeline.py` (new file)

- ⏳ **Task 1.1.4:** Unit tests for models
  - [ ] Test model creation
  - [ ] Test validation rules
  - [ ] Test relationships
  - [ ] Test JSONB serialization
  - **Location:** `tests/unit/models/test_timeline_models.py` (new file)
  - **Target Coverage:** 90%+

- ⏳ **Task 1.1.5:** Logging setup
  - [ ] Add structured logging for schema operations
  - [ ] Log migration start/complete
  - [ ] Log any errors with full context
  - **Pattern:** Use existing logging infrastructure

- ⏳ **Task 1.1.6:** Run migration
  - [ ] Run migration on development database
  - [ ] Verify tables created correctly
  - [ ] Verify indexes created
  - [ ] Document any issues

- ⏳ **Task 1.1.7:** Commit work
  - [ ] Update this document with progress
  - [ ] Commit database models
  - [ ] Commit migrations
  - [ ] Commit tests
  - **Commit Message:** "feat(timeline): Add database schema and migrations for timeline system"

#### Session Notes

**Session:** (To be filled)  
**Progress:** (To be filled)  
**Blockers:** (To be filled)  
**Next Steps:** (To be filled)

---

### Sub-Phase 1.2: Temporal Confidence Calculator

**Duration:** 1 day  
**Status:** ⏸️ Waiting (Depends on 1.1)  
**Dependencies:** Sub-Phase 1.1

#### Tasks

- ⏳ **Task 1.2.1:** Implement `TemporalConfidenceCalculator`
  - [ ] Create class structure
  - [ ] Implement `calculate_confidence()` method
  - [ ] Implement confidence level logic (HIGH/MEDIUM/LOW/NONE)
  - [ ] Implement capability determination
  - [ ] Implement fallback strategy selection
  - [ ] Add comprehensive docstrings
  - **Location:** `services/ecosystem-mcp/src/services/timeline/confidence_calculator.py` (new file)
  - **Reference:** `TIMELINE_ANALYSIS_GRACEFUL_FALLBACK_ADDENDUM.md` Section 2

- ⏳ **Task 1.2.2:** Unit tests for confidence calculator
  - [ ] Test HIGH confidence (90%+ git history)
  - [ ] Test MEDIUM confidence (50-90% git history)
  - [ ] Test LOW confidence (1-50% git history)
  - [ ] Test NONE confidence (0% git history)
  - [ ] Test edge cases (empty document list, all snapshot, all git)
  - [ ] Test capability determination
  - **Location:** `tests/unit/services/timeline/test_confidence_calculator.py` (new file)
  - **Target Coverage:** 95%+

- ⏳ **Task 1.2.3:** Integration tests
  - [ ] Test with real document data
  - [ ] Test with mixed ingestion modes
  - [ ] Test performance (should be fast)
  - **Location:** `tests/integration/services/timeline/test_confidence_integration.py` (new file)

- ⏳ **Task 1.2.4:** Logging
  - [ ] Log confidence calculations
  - [ ] Log confidence level determination
  - [ ] Log fallback strategy selection
  - [ ] Include document counts and percentages

- ⏳ **Task 1.2.5:** Commit work
  - [ ] Update this document
  - [ ] Commit confidence calculator
  - [ ] Commit tests
  - **Commit Message:** "feat(timeline): Add temporal confidence calculator with graceful fallbacks"

#### Session Notes

**Session:** (To be filled)  
**Progress:** (To be filled)  
**Blockers:** (To be filled)  
**Next Steps:** (To be filled)

---

### Sub-Phase 1.3: Timeline Manager (Core CRUD)

**Duration:** 1 day  
**Status:** ⏸️ Waiting (Depends on 1.2)  
**Dependencies:** Sub-Phase 1.1, 1.2

#### Tasks

- ⏳ **Task 1.3.1:** Implement `TimelineManager`
  - [ ] Create class structure
  - [ ] Implement `create_timeline()` with pre-flight validation
  - [ ] Implement `get_timeline()`
  - [ ] Implement `update_timeline()`
  - [ ] Implement `delete_timeline()`
  - [ ] Implement `list_timelines()`
  - [ ] Add confidence metadata to all operations
  - [ ] Integrate with `TemporalConfidenceCalculator`
  - **Location:** `services/ecosystem-mcp/src/services/timeline/timeline_manager.py` (new file)
  - **Reference:** `TIMELINE_ANALYSIS_GRACEFUL_FALLBACK_ADDENDUM.md` Section 5.1

- ⏳ **Task 1.3.2:** Implement `DocumentRepository` extensions
  - [ ] Add `get_by_service()` method (if not exists)
  - [ ] Add `get_by_date_range()` method
  - [ ] Add `get_by_ingestion_mode()` method
  - **Location:** `services/ecosystem-mcp/src/storage/repositories/document_repository.py`

- ⏳ **Task 1.3.3:** Unit tests for TimelineManager
  - [ ] Test create with HIGH confidence
  - [ ] Test create with MEDIUM confidence (warnings)
  - [ ] Test create with LOW confidence (warnings)
  - [ ] Test create with NONE confidence (blocked)
  - [ ] Test CRUD operations
  - [ ] Test error handling
  - **Location:** `tests/unit/services/timeline/test_timeline_manager.py` (new file)
  - **Target Coverage:** 90%+

- ⏳ **Task 1.3.4:** Integration tests
  - [ ] Test with real database
  - [ ] Test with real documents
  - [ ] Test confidence validation
  - **Location:** `tests/integration/services/timeline/test_timeline_manager_integration.py` (new file)

- ⏳ **Task 1.3.5:** Logging
  - [ ] Log timeline creation with confidence
  - [ ] Log validation failures
  - [ ] Log CRUD operations
  - [ ] Include timeline IDs and confidence levels

- ⏳ **Task 1.3.6:** Commit work
  - [ ] Update this document
  - [ ] Commit timeline manager
  - [ ] Commit repository extensions
  - [ ] Commit tests
  - **Commit Message:** "feat(timeline): Add timeline manager with confidence validation"

#### Session Notes

**Session:** (To be filled)  
**Progress:** (To be filled)  
**Blockers:** (To be filled)  
**Next Steps:** (To be filled)

---

### Sub-Phase 1.4: Period Generator

**Duration:** 0.5 days  
**Status:** ⏸️ Waiting (Depends on 1.3)  
**Dependencies:** Sub-Phase 1.3

#### Tasks

- ⏳ **Task 1.4.1:** Implement `PeriodGenerator`
  - [ ] Create class structure
  - [ ] Implement `generate_periods()` method
  - [ ] Implement monthly period generation
  - [ ] Implement quarterly period generation
  - [ ] Implement adaptive period generation (by major commits)
  - [ ] Add period naming logic
  - **Location:** `services/ecosystem-mcp/src/services/timeline/period_generator.py` (new file)

- ⏳ **Task 1.4.2:** Unit tests
  - [ ] Test monthly generation
  - [ ] Test quarterly generation
  - [ ] Test adaptive generation
  - [ ] Test edge cases (short timelines, long timelines)
  - **Location:** `tests/unit/services/timeline/test_period_generator.py` (new file)
  - **Target Coverage:** 90%+

- ⏳ **Task 1.4.3:** Logging
  - [ ] Log period generation strategy
  - [ ] Log number of periods generated
  - [ ] Log date ranges

- ⏳ **Task 1.4.4:** Commit work
  - [ ] Update this document
  - [ ] Commit period generator
  - [ ] Commit tests
  - **Commit Message:** "feat(timeline): Add period generator with multiple strategies"

#### Session Notes

**Session:** (To be filled)  
**Progress:** (To be filled)  
**Blockers:** (To be filled)  
**Next Steps:** (To be filled)

---

### Sub-Phase 1.5: Document Placement

**Duration:** 0.5 days  
**Status:** ⏸️ Waiting (Depends on 1.4)  
**Dependencies:** Sub-Phase 1.4

#### Tasks

- ⏳ **Task 1.5.1:** Implement `DocumentPlacer`
  - [ ] Create class structure
  - [ ] Implement `place_documents()` method
  - [ ] Place documents based on commit dates (git_history mode)
  - [ ] Place documents based on created_at (snapshot mode)
  - [ ] Handle documents without dates
  - **Location:** `services/ecosystem-mcp/src/services/timeline/document_placer.py` (new file)

- ⏳ **Task 1.5.2:** Unit tests
  - [ ] Test placement with git_history documents
  - [ ] Test placement with snapshot documents
  - [ ] Test mixed mode placement
  - [ ] Test edge cases
  - **Location:** `tests/unit/services/timeline/test_document_placer.py` (new file)
  - **Target Coverage:** 90%+

- ⏳ **Task 1.5.3:** Logging
  - [ ] Log document placement
  - [ ] Log placement strategy used
  - [ ] Log any warnings (missing dates, etc.)

- ⏳ **Task 1.5.4:** Commit work
  - [ ] Update this document
  - [ ] Commit document placer
  - [ ] Commit tests
  - **Commit Message:** "feat(timeline): Add document placement algorithm"

#### Session Notes

**Session:** (To be filled)  
**Progress:** (To be filled)  
**Blockers:** (To be filled)  
**Next Steps:** (To be filled)

---

### Sub-Phase 1.6: API Endpoints

**Duration:** 1 day  
**Status:** ⏸️ Waiting (Depends on 1.5)  
**Dependencies:** Sub-Phase 1.5

#### Tasks

- ⏳ **Task 1.6.1:** Create API route file
  - [ ] Create `timeline.py` route file
  - [ ] Set up router
  - [ ] Add error handling
  - **Location:** `services/ecosystem-mcp/src/api/routes/timeline.py` (new file)

- ⏳ **Task 1.6.2:** Implement `POST /api/v1/timelines`
  - [ ] Create request model with validation
  - [ ] Implement endpoint logic
  - [ ] Add pre-flight confidence validation
  - [ ] Return timeline with confidence metadata
  - [ ] Add OpenAPI/Swagger annotations
  - [ ] Handle errors (400, 500)

- ⏳ **Task 1.6.3:** Implement `GET /api/v1/timelines/{id}`
  - [ ] Implement endpoint logic
  - [ ] Return timeline with confidence
  - [ ] Add OpenAPI/Swagger annotations
  - [ ] Handle errors (404, 500)

- ⏳ **Task 1.6.4:** Implement `GET /api/v1/timelines`
  - [ ] Add pagination
  - [ ] Add filtering (by repo, confidence)
  - [ ] Add sorting
  - [ ] Add OpenAPI/Swagger annotations

- ⏳ **Task 1.6.5:** Implement `GET /api/v1/timelines/{id}/periods`
  - [ ] Return periods for timeline
  - [ ] Add OpenAPI/Swagger annotations

- ⏳ **Task 1.6.6:** Implement `GET /api/v1/timelines/{id}/documents`
  - [ ] Return placed documents
  - [ ] Add pagination
  - [ ] Add OpenAPI/Swagger annotations

- ⏳ **Task 1.6.7:** Integration tests for API
  - [ ] Test timeline creation (all confidence levels)
  - [ ] Test timeline retrieval
  - [ ] Test timeline listing
  - [ ] Test period listing
  - [ ] Test document listing
  - [ ] Test error cases
  - **Location:** `tests/integration/api/test_timeline_api.py` (new file)
  - **Target Coverage:** 90%+

- ⏳ **Task 1.6.8:** E2E tests
  - [ ] Test full flow: create → get → list periods → list documents
  - [ ] Test with HIGH confidence repo
  - [ ] Test with NONE confidence repo (should fail)
  - **Location:** `tests/e2e/test_timeline_e2e.py` (new file)

- ⏳ **Task 1.6.9:** Logging
  - [ ] Log all API requests
  - [ ] Log validation failures
  - [ ] Log confidence checks
  - [ ] Include request IDs for tracing

- ⏳ **Task 1.6.10:** Verify Swagger docs
  - [ ] Start service
  - [ ] Navigate to `/docs`
  - [ ] Verify all endpoints documented
  - [ ] Verify request/response schemas
  - [ ] Test endpoints via Swagger UI

- ⏳ **Task 1.6.11:** Commit work
  - [ ] Update this document
  - [ ] Commit API routes
  - [ ] Commit tests
  - **Commit Message:** "feat(timeline): Add timeline API endpoints with OpenAPI docs"

#### Session Notes

**Session:** (To be filled)  
**Progress:** (To be filled)  
**Blockers:** (To be filled)  
**Next Steps:** (To be filled)

---

### Sub-Phase 1.7: Functional/Smoke Tests

**Duration:** 0.5 days  
**Status:** ⏸️ Waiting (Depends on 1.6)  
**Dependencies:** Sub-Phase 1.6

#### Tasks

- ⏳ **Task 1.7.1:** Create smoke test script
  - [ ] Test timeline creation
  - [ ] Test confidence validation
  - [ ] Test period generation
  - [ ] Test document placement
  - [ ] Test API endpoints
  - [ ] Run against real ecosystem-mcp codebase
  - **Location:** `scripts/smoke_tests/test_timeline_phase1.py` (new file)

- ⏳ **Task 1.7.2:** Run smoke tests
  - [ ] Run against development environment
  - [ ] Verify all tests pass
  - [ ] Document any failures

- ⏳ **Task 1.7.3:** Create functional test
  - [ ] Test full workflow with real data
  - [ ] Test with git_history mode repo
  - [ ] Test with snapshot mode repo
  - [ ] Verify confidence system works correctly
  - **Location:** `tests/functional/test_timeline_workflow.py` (new file)

- ⏳ **Task 1.7.4:** Commit work
  - [ ] Update this document
  - [ ] Commit smoke tests
  - [ ] Commit functional tests
  - **Commit Message:** "test(timeline): Add smoke and functional tests for Phase 1"

#### Session Notes

**Session:** (To be filled)  
**Progress:** (To be filled)  
**Blockers:** (To be filled)  
**Next Steps:** (To be filled)

---

### Sub-Phase 1.8: Phase 1 Validation & Commit

**Duration:** 0.5 days  
**Status:** ⏸️ Waiting (Depends on 1.7)  
**Dependencies:** Sub-Phase 1.7

#### Tasks

- ⏳ **Task 1.8.1:** Run all Phase 1 tests
  - [ ] Run unit tests: `pytest tests/unit/services/timeline/ tests/unit/models/`
  - [ ] Run integration tests: `pytest tests/integration/services/timeline/ tests/integration/api/`
  - [ ] Run E2E tests: `pytest tests/e2e/test_timeline_e2e.py`
  - [ ] Run smoke tests: `python scripts/smoke_tests/test_timeline_phase1.py`
  - [ ] Run functional tests: `pytest tests/functional/test_timeline_workflow.py`
  - [ ] Verify all tests pass
  - [ ] Check test coverage (target: 90%+)

- ⏳ **Task 1.8.2:** Code review checklist
  - [ ] All services follow thin facade pattern
  - [ ] Existing services reused (not duplicated)
  - [ ] Confidence checks in all temporal operations
  - [ ] Comprehensive logging added
  - [ ] All API endpoints have OpenAPI docs
  - [ ] Error handling is robust
  - [ ] Code is well-documented

- ⏳ **Task 1.8.3:** Update documentation
  - [ ] Update this master plan with Phase 1 complete
  - [ ] Update Quick Status Overview
  - [ ] Write Session Handoff Notes for Phase 2
  - [ ] Document any lessons learned

- ⏳ **Task 1.8.4:** Final commit
  - [ ] Commit this document
  - [ ] Commit any remaining changes
  - **Commit Message:** "feat(timeline): Complete Phase 1 - Core Timeline + Confidence System"

- ⏳ **Task 1.8.5:** Tag release
  - [ ] Create git tag: `timeline-phase1-complete`
  - [ ] Push tag to remote

#### Session Notes

**Session:** (To be filled)  
**Progress:** (To be filled)  
**Blockers:** (To be filled)  
**Next Steps:** Begin Phase 2

---

### Phase 1 Summary

**Deliverables:**
- ✅ Database schema and migrations
- ✅ Temporal confidence calculator
- ✅ Timeline manager with CRUD
- ✅ Period generator
- ✅ Document placer
- ✅ 4 API endpoints
- ✅ Comprehensive tests (unit, integration, E2E, smoke, functional)
- ✅ Logging and feedback
- ✅ OpenAPI documentation

**Test Coverage:** (To be filled)  
**Lines of Code:** (To be filled)  
**Blockers Encountered:** (To be filled)  
**Lessons Learned:** (To be filled)

---

## Phase 2: Temporal RAG + Maintenance Features

**Duration:** 1 session  
**Status:** 🟢 Complete  
**Progress:** 100%  
**Tests:** Unit/Integration tests pending

### Goals

- Extend RAG with temporal capabilities
- Implement 8 documentation maintenance features
- Add comprehensive testing, logging, and feedback
- Integrate with Phase 1 timeline infrastructure

### Sub-Phases

---

### Sub-Phase 2.1: Temporal RAG Extensions

**Duration:** 2 days  
**Status:** ⏸️ Waiting  
**Dependencies:** Phase 1 Complete

#### Tasks

- ⏳ **Task 2.1.1:** Extend `ContextAwareRAG`
  - [ ] Add `query_period()` method
  - [ ] Add `query_evolution()` method
  - [ ] Add `query_comparison()` method
  - [ ] Integrate with timeline system
  - [ ] Add confidence checks
  - **Location:** `services/ecosystem-mcp/src/services/rag/context_aware_rag.py`
  - **Reference:** `TIMELINE_ANALYSIS_FINAL_REFINED_PLAN.md` Section on Temporal RAG

- ⏳ **Task 2.1.2:** Create `TemporalRAGService`
  - [ ] Implement `query_as_of()` (time-travel queries)
  - [ ] Implement `query_what_changed()` (change detection)
  - [ ] Add temporal filtering
  - [ ] Add confidence checks
  - **Location:** `services/ecosystem-mcp/src/services/rag/temporal_rag_service.py` (new file)

- ⏳ **Task 2.1.3:** Unit tests
  - [ ] Test period queries
  - [ ] Test evolution tracking
  - [ ] Test comparison queries
  - [ ] Test time-travel queries
  - [ ] Test with different confidence levels
  - **Location:** `tests/unit/services/rag/test_temporal_rag.py` (new file)
  - **Target Coverage:** 90%+

- ⏳ **Task 2.1.4:** Integration tests
  - [ ] Test with real timelines
  - [ ] Test with real documents
  - [ ] Test performance
  - **Location:** `tests/integration/services/rag/test_temporal_rag_integration.py` (new file)

- ⏳ **Task 2.1.5:** API endpoints
  - [ ] `POST /api/v1/rag/temporal/query` - Temporal RAG query
  - [ ] `POST /api/v1/rag/temporal/evolution` - Evolution tracking
  - [ ] `POST /api/v1/rag/temporal/comparison` - Period comparison
  - [ ] Add OpenAPI docs
  - **Location:** `services/ecosystem-mcp/src/api/routes/rag.py` (extend)

- ⏳ **Task 2.1.6:** Logging
  - [ ] Log temporal queries
  - [ ] Log confidence checks
  - [ ] Log fallback to standard RAG

- ⏳ **Task 2.1.7:** Commit work
  - [ ] Update this document
  - [ ] Commit temporal RAG extensions
  - [ ] Commit tests
  - **Commit Message:** "feat(rag): Add temporal RAG capabilities with time-travel queries"

#### Session Notes

**Session:** (To be filled)  
**Progress:** (To be filled)  
**Blockers:** (To be filled)  
**Next Steps:** (To be filled)

---

### Sub-Phase 2.2: Maintenance Features (Part 1)

**Duration:** 1.5 days  
**Status:** ⏸️ Waiting  
**Dependencies:** Sub-Phase 2.1

#### Tasks

- ⏳ **Task 2.2.1:** Implement Staleness Detection
  - [ ] Create `StalenessDetector` service
  - [ ] Detect docs not updated despite code changes
  - [ ] Use `IncrementalDocManager` and `TimelineQueryEngine`
  - [ ] Add API endpoint
  - [ ] Add tests
  - **Location:** `services/ecosystem-mcp/src/services/maintenance/staleness_detector.py` (new file)

- ⏳ **Task 2.2.2:** Implement Coverage Analysis
  - [ ] Create `CoverageAnalyzer` service
  - [ ] Calculate % of files/APIs/classes documented
  - [ ] Track coverage by service/module
  - [ ] Track coverage trend over time
  - [ ] Add API endpoint
  - [ ] Add tests
  - **Location:** `services/ecosystem-mcp/src/services/maintenance/coverage_analyzer.py` (new file)

- ⏳ **Task 2.2.3:** Implement Consistency Checker
  - [ ] Create `ConsistencyChecker` service
  - [ ] Find conflicting information
  - [ ] Detect outdated cross-references
  - [ ] Check terminology consistency
  - [ ] Add API endpoint
  - [ ] Add tests
  - **Location:** `services/ecosystem-mcp/src/services/maintenance/consistency_checker.py` (new file)

- ⏳ **Task 2.2.4:** Implement Automated Refresh
  - [ ] Create `AutomatedRefresher` service
  - [ ] Auto-update docs when code changes
  - [ ] Support incremental, full, and smart strategies
  - [ ] Add API endpoint
  - [ ] Add tests
  - **Location:** `services/ecosystem-mcp/src/services/maintenance/automated_refresher.py` (new file)

- ⏳ **Task 2.2.5:** Logging
  - [ ] Log staleness detection
  - [ ] Log coverage calculations
  - [ ] Log consistency checks
  - [ ] Log automated refreshes

- ⏳ **Task 2.2.6:** Commit work
  - [ ] Update this document
  - [ ] Commit maintenance services
  - [ ] Commit tests
  - **Commit Message:** "feat(maintenance): Add staleness, coverage, consistency, and auto-refresh features"

#### Session Notes

**Session:** (To be filled)  
**Progress:** (To be filled)  
**Blockers:** (To be filled)  
**Next Steps:** (To be filled)

---

### Sub-Phase 2.3: Maintenance Features (Part 2)

**Duration:** 1.5 days  
**Status:** ⏸️ Waiting  
**Dependencies:** Sub-Phase 2.2

#### Tasks

- ⏳ **Task 2.3.1:** Implement Quality Dashboard
  - [ ] Create `QualityDashboard` service
  - [ ] Real-time quality metrics
  - [ ] Quality trends over time
  - [ ] Top issues and recommendations
  - [ ] Add API endpoint
  - [ ] Add tests
  - **Location:** `services/ecosystem-mcp/src/services/maintenance/quality_dashboard.py` (new file)

- ⏳ **Task 2.3.2:** Implement Dependency Tracking
  - [ ] Create `DependencyTracker` service
  - [ ] Track cross-references between docs
  - [ ] Build documentation dependency graph
  - [ ] Add API endpoint
  - [ ] Add tests
  - **Location:** `services/ecosystem-mcp/src/services/maintenance/dependency_tracker.py` (new file)

- ⏳ **Task 2.3.3:** Implement Version Comparison
  - [ ] Create `VersionComparator` service
  - [ ] Compare two versions of a document
  - [ ] Show diff, what changed, when, why
  - [ ] Add API endpoint
  - [ ] Add tests
  - **Location:** `services/ecosystem-mcp/src/services/maintenance/version_comparator.py` (new file)

- ⏳ **Task 2.3.4:** Implement Search & Discovery
  - [ ] Create `SearchService` (if not exists, extend existing)
  - [ ] Semantic, keyword, or hybrid search
  - [ ] Advanced filtering (by date, service, technology)
  - [ ] Add API endpoint
  - [ ] Add tests
  - **Location:** `services/ecosystem-mcp/src/services/maintenance/search_service.py` (new file)

- ⏳ **Task 2.3.5:** Logging
  - [ ] Log quality calculations
  - [ ] Log dependency tracking
  - [ ] Log version comparisons
  - [ ] Log searches

- ⏳ **Task 2.3.6:** Commit work
  - [ ] Update this document
  - [ ] Commit maintenance services
  - [ ] Commit tests
  - **Commit Message:** "feat(maintenance): Add quality dashboard, dependency tracking, version comparison, and search"

#### Session Notes

**Session:** (To be filled)  
**Progress:** (To be filled)  
**Blockers:** (To be filled)  
**Next Steps:** (To be filled)

---

### Sub-Phase 2.4: Phase 2 Testing & Validation

**Duration:** 1 day  
**Status:** ⏸️ Waiting  
**Dependencies:** Sub-Phase 2.3

#### Tasks

- ⏳ **Task 2.4.1:** E2E tests
  - [ ] Test temporal RAG full flow
  - [ ] Test maintenance features full flow
  - [ ] Test integration with Phase 1 timelines
  - **Location:** `tests/e2e/test_phase2_e2e.py` (new file)

- ⏳ **Task 2.4.2:** Smoke tests
  - [ ] Test all Phase 2 features
  - [ ] Run against real codebase
  - **Location:** `scripts/smoke_tests/test_timeline_phase2.py` (new file)

- ⏳ **Task 2.4.3:** Run all tests
  - [ ] Unit tests
  - [ ] Integration tests
  - [ ] E2E tests
  - [ ] Smoke tests
  - [ ] Verify all pass

- ⏳ **Task 2.4.4:** Update documentation
  - [ ] Update this master plan
  - [ ] Write Session Handoff Notes for Phase 3

- ⏳ **Task 2.4.5:** Commit and tag
  - [ ] Commit this document
  - [ ] Commit any remaining changes
  - [ ] Create git tag: `timeline-phase2-complete`
  - **Commit Message:** "feat(timeline): Complete Phase 2 - Temporal RAG + Maintenance Features"

#### Session Notes

**Session:** (To be filled)  
**Progress:** (To be filled)  
**Blockers:** (To be filled)  
**Next Steps:** Begin Phase 3

---

### Phase 2 Summary

**Deliverables:** (To be filled)  
**Test Coverage:** (To be filled)  
**Lines of Code:** (To be filled)  
**Blockers Encountered:** (To be filled)  
**Lessons Learned:** (To be filled)

---

## Phase 3: Gap/Drift Detection + Advanced Features

**Duration:** 1 week (5 working days)  
**Status:** ⏸️ Waiting (Depends on Phase 2)  
**Progress:** 0%  
**Tests:** 0/0 passing

### Goals

- Implement gap analysis with root cause
- Implement drift detection with hybrid mode
- Implement export & publishing
- Implement analytics
- Implement upgrade helper

### Sub-Phases

---

### Sub-Phase 3.1: Gap Analysis

**Duration:** 1.5 days  
**Status:** ⏸️ Waiting  
**Dependencies:** Phase 2 Complete

#### Tasks

- ⏳ **Task 3.1.1:** Implement `GapAnalyzer`
  - [ ] Detect documentation gaps
  - [ ] Identify topic gaps
  - [ ] Analyze root causes
  - [ ] Use timeline data for temporal context
  - [ ] Add confidence checks
  - **Location:** `services/ecosystem-mcp/src/services/timeline/gap_analyzer.py` (new file)
  - **Reference:** `TIMELINE_ANALYSIS_ENRICHED_PLAN.md` Section on Gap Analysis

- ⏳ **Task 3.1.2:** Unit tests
- ⏳ **Task 3.1.3:** Integration tests
- ⏳ **Task 3.1.4:** API endpoint: `POST /api/v1/analysis/gaps`
- ⏳ **Task 3.1.5:** Logging
- ⏳ **Task 3.1.6:** Commit work

#### Session Notes

**Session:** (To be filled)  
**Progress:** (To be filled)  
**Blockers:** (To be filled)

---

### Sub-Phase 3.2: Drift Detection

**Duration:** 1.5 days  
**Status:** ⏸️ Waiting  
**Dependencies:** Sub-Phase 3.1

#### Tasks

- ⏳ **Task 3.2.1:** Implement `DriftDetector` with hybrid approach
  - [ ] Full drift detection (git_history mode)
  - [ ] Content comparison (snapshot mode)
  - [ ] Hybrid mode (mixed documents)
  - [ ] Detect API/data contract changes
  - [ ] Add confidence checks
  - **Location:** `services/ecosystem-mcp/src/services/timeline/drift_detector.py` (new file)
  - **Reference:** `TIMELINE_ANALYSIS_GRACEFUL_FALLBACK_ADDENDUM.md` Section 3.3

- ⏳ **Task 3.2.2:** Unit tests
- ⏳ **Task 3.2.3:** Integration tests
- ⏳ **Task 3.2.4:** API endpoint: `POST /api/v1/analysis/drift`
- ⏳ **Task 3.2.5:** Logging
- ⏳ **Task 3.2.6:** Commit work

#### Session Notes

**Session:** (To be filled)  
**Progress:** (To be filled)  
**Blockers:** (To be filled)

---

### Sub-Phase 3.3: Export & Publishing

**Duration:** 1 day  
**Status:** ⏸️ Waiting  
**Dependencies:** Sub-Phase 3.2

#### Tasks

- ⏳ **Task 3.3.1:** Implement export functionality
  - [ ] Export to markdown
  - [ ] Export to HTML
  - [ ] Export to PDF
  - [ ] Export to DOCX
  - [ ] GitHub Pages integration
  - **Location:** `services/ecosystem-mcp/src/services/maintenance/export_service.py` (new file)

- ⏳ **Task 3.3.2:** Unit tests
- ⏳ **Task 3.3.3:** API endpoint: `POST /api/v1/export`
- ⏳ **Task 3.3.4:** Logging
- ⏳ **Task 3.3.5:** Commit work

#### Session Notes

**Session:** (To be filled)  
**Progress:** (To be filled)  
**Blockers:** (To be filled)

---

### Sub-Phase 3.4: Analytics & Upgrade Helper

**Duration:** 1 day  
**Status:** ⏸️ Waiting  
**Dependencies:** Sub-Phase 3.3

#### Tasks

- ⏳ **Task 3.4.1:** Implement `AnalyticsService`
  - [ ] Documentation growth over time
  - [ ] Most/least documented areas
  - [ ] Quality and coverage trends
  - **Location:** `services/ecosystem-mcp/src/services/maintenance/analytics_service.py` (new file)

- ⏳ **Task 3.4.2:** Implement `TimelineUpgradeHelper`
  - [ ] Guide users to upgrade from snapshot to git_history
  - [ ] Suggest upgrade benefits
  - [ ] Provide upgrade steps
  - **Location:** `services/ecosystem-mcp/src/services/timeline/upgrade_helper.py` (new file)
  - **Reference:** `TIMELINE_ANALYSIS_GRACEFUL_FALLBACK_ADDENDUM.md` Section 3.4

- ⏳ **Task 3.4.3:** Unit tests
- ⏳ **Task 3.4.4:** API endpoints
- ⏳ **Task 3.4.5:** Logging
- ⏳ **Task 3.4.6:** Commit work

#### Session Notes

**Session:** (To be filled)  
**Progress:** (To be filled)  
**Blockers:** (To be filled)

---

### Sub-Phase 3.5: Phase 3 Testing & Validation

**Duration:** 1 day  
**Status:** ⏸️ Waiting  
**Dependencies:** Sub-Phase 3.4

#### Tasks

- ⏳ **Task 3.5.1:** E2E tests
- ⏳ **Task 3.5.2:** Smoke tests
- ⏳ **Task 3.5.3:** Run all tests
- ⏳ **Task 3.5.4:** Update documentation
- ⏳ **Task 3.5.5:** Commit and tag: `timeline-phase3-complete`

#### Session Notes

**Session:** (To be filled)  
**Progress:** (To be filled)  
**Blockers:** (To be filled)  
**Next Steps:** Begin Phase 4

---

### Phase 3 Summary

**Deliverables:** (To be filled)  
**Test Coverage:** (To be filled)  
**Lines of Code:** (To be filled)  
**Blockers Encountered:** (To be filled)  
**Lessons Learned:** (To be filled)

---

## Phase 4: Doc Generation Integration + Reports

**Duration:** 1 week (5 working days)  
**Status:** ⏸️ Waiting (Depends on Phase 3)  
**Progress:** 0%  
**Tests:** 0/0 passing

### Goals

- Enhance documentation generation with temporal context
- Implement report generation with citations
- Implement document consolidation

### Sub-Phases

---

### Sub-Phase 4.1: Enhanced Documentation Generation

**Duration:** 2 days  
**Status:** ⏸️ Waiting  
**Dependencies:** Phase 3 Complete

#### Tasks

- ⏳ **Task 4.1.1:** Extend `DocumentationOrchestrator`
  - [ ] Add `include_evolution` parameter to `DocConfig`
  - [ ] Inject temporal context into passes
  - **Location:** `services/ecosystem-mcp/src/services/documentation/doc_orchestrator.py`

- ⏳ **Task 4.1.2:** Enhance `ArchitectureGenerator`
  - [ ] Add "Architectural Evolution" section
  - [ ] Add "Key Decisions Timeline" section
  - [ ] Add "Migration History" section
  - **Location:** `services/ecosystem-mcp/src/services/documentation/architecture_generator.py`

- ⏳ **Task 4.1.3:** Enhance `APIReferenceGenerator`
  - [ ] Highlight breaking changes with timeline
  - [ ] Show deprecation history
  - [ ] Version compatibility matrix
  - **Location:** `services/ecosystem-mcp/src/services/documentation/api_reference_generator.py`

- ⏳ **Task 4.1.4:** Unit tests
- ⏳ **Task 4.1.5:** Integration tests
- ⏳ **Task 4.1.6:** Update API endpoint: `POST /api/v1/documentation/generate`
- ⏳ **Task 4.1.7:** Logging
- ⏳ **Task 4.1.8:** Commit work

#### Session Notes

**Session:** (To be filled)  
**Progress:** (To be filled)  
**Blockers:** (To be filled)

---

### Sub-Phase 4.2: Report Generation

**Duration:** 2 days  
**Status:** ⏸️ Waiting  
**Dependencies:** Sub-Phase 4.1

#### Tasks

- ⏳ **Task 4.2.1:** Implement `ReportGenerator`
  - [ ] Progression reports (work over time)
  - [ ] Gap reports (what's missing)
  - [ ] Drift reports (what changed)
  - [ ] All with source citations
  - **Location:** `services/ecosystem-mcp/src/services/timeline/report_generator.py` (new file)

- ⏳ **Task 4.2.2:** Unit tests
- ⏳ **Task 4.2.3:** API endpoints
  - [ ] `POST /api/v1/reports/progression`
  - [ ] `POST /api/v1/reports/gaps`
  - [ ] `POST /api/v1/reports/drift`
- ⏳ **Task 4.2.4:** Logging
- ⏳ **Task 4.2.5:** Commit work

#### Session Notes

**Session:** (To be filled)  
**Progress:** (To be filled)  
**Blockers:** (To be filled)

---

### Sub-Phase 4.3: Document Consolidation

**Duration:** 1 day  
**Status:** ⏸️ Waiting  
**Dependencies:** Sub-Phase 4.2

#### Tasks

- ⏳ **Task 4.3.1:** Implement `DocumentConsolidator`
  - [ ] Detect redundancy
  - [ ] Cluster versions
  - [ ] Recommend merges
  - **Location:** `services/ecosystem-mcp/src/services/timeline/document_consolidator.py` (new file)

- ⏳ **Task 4.3.2:** Unit tests
- ⏳ **Task 4.3.3:** API endpoint: `POST /api/v1/consolidation/analyze`
- ⏳ **Task 4.3.4:** Logging
- ⏳ **Task 4.3.5:** Commit work

#### Session Notes

**Session:** (To be filled)  
**Progress:** (To be filled)  
**Blockers:** (To be filled)

---

### Sub-Phase 4.4: Phase 4 Testing & Validation

**Duration:** 1 day  
**Status:** ⏸️ Waiting  
**Dependencies:** Sub-Phase 4.3

#### Tasks

- ⏳ **Task 4.4.1:** E2E tests
- ⏳ **Task 4.4.2:** Smoke tests
- ⏳ **Task 4.4.3:** Performance tests
- ⏳ **Task 4.4.4:** Run all tests
- ⏳ **Task 4.4.5:** Update documentation
- ⏳ **Task 4.4.6:** Commit and tag: `timeline-phase4-complete`

#### Session Notes

**Session:** (To be filled)  
**Progress:** (To be filled)  
**Blockers:** (To be filled)  
**Next Steps:** Begin Phase 5

---

### Phase 4 Summary

**Deliverables:** (To be filled)  
**Test Coverage:** (To be filled)  
**Lines of Code:** (To be filled)  
**Blockers Encountered:** (To be filled)  
**Lessons Learned:** (To be filled)

---

## Phase 5: Dashboard Integration

**Duration:** 1 week (5 working days)  
**Status:** ⏸️ Waiting (Depends on Phase 4)  
**Progress:** 0%  
**Tests:** 0/0 passing

### Goals

- Create dashboard pages for timeline features
- Integrate all Phase 1-4 features into UI
- Add visualizations
- Add user feedback mechanisms

### Sub-Phases

---

### Sub-Phase 5.1: Timeline Management UI

**Duration:** 2 days  
**Status:** ⏸️ Waiting  
**Dependencies:** Phase 4 Complete

#### Tasks

- ⏳ **Task 5.1.1:** Create Timeline Management page
  - [ ] Timeline creation form with confidence warnings
  - [ ] Timeline list view
  - [ ] Timeline detail view
  - [ ] Period visualization
  - [ ] Document placement visualization
  - **Location:** `services/ecosystem-mcp-dashboard/pages/timeline_manager.py` (new file)

- ⏳ **Task 5.1.2:** Add confidence warnings
  - [ ] Show confidence level prominently
  - [ ] Require confirmation for LOW confidence
  - [ ] Block creation for NONE confidence
  - [ ] Provide "Re-ingest" button

- ⏳ **Task 5.1.3:** Add navigation
  - [ ] Add to sidebar
  - [ ] Add breadcrumbs

- ⏳ **Task 5.1.4:** Commit work

#### Session Notes

**Session:** (To be filled)  
**Progress:** (To be filled)  
**Blockers:** (To be filled)

---

### Sub-Phase 5.2: Analysis & Reports UI

**Duration:** 2 days  
**Status:** ⏸️ Waiting  
**Dependencies:** Sub-Phase 5.1

#### Tasks

- ⏳ **Task 5.2.1:** Create Analysis page
  - [ ] Gap analysis view
  - [ ] Drift detection view
  - [ ] Report generation UI
  - **Location:** `services/ecosystem-mcp-dashboard/pages/timeline_analysis.py` (new file)

- ⏳ **Task 5.2.2:** Create Reports page
  - [ ] Progression reports
  - [ ] Gap reports
  - [ ] Drift reports
  - [ ] Export functionality
  - **Location:** `services/ecosystem-mcp-dashboard/pages/timeline_reports.py` (new file)

- ⏳ **Task 5.2.3:** Commit work

#### Session Notes

**Session:** (To be filled)  
**Progress:** (To be filled)  
**Blockers:** (To be filled)

---

### Sub-Phase 5.3: Maintenance Features UI

**Duration:** 1 day  
**Status:** ⏸️ Waiting  
**Dependencies:** Sub-Phase 5.2

#### Tasks

- ⏳ **Task 5.3.1:** Create Maintenance Dashboard page
  - [ ] Staleness detection view
  - [ ] Coverage analysis view
  - [ ] Quality dashboard view
  - [ ] Consistency checker view
  - **Location:** `services/ecosystem-mcp-dashboard/pages/maintenance_dashboard.py` (new file)

- ⏳ **Task 5.3.2:** Commit work

#### Session Notes

**Session:** (To be filled)  
**Progress:** (To be filled)  
**Blockers:** (To be filled)

---

### Sub-Phase 5.4: Phase 5 Testing & Validation

**Duration:** 1 day  
**Status:** ⏸️ Waiting  
**Dependencies:** Sub-Phase 5.3

#### Tasks

- ⏳ **Task 5.4.1:** UI tests
- ⏳ **Task 5.4.2:** E2E tests with UI
- ⏳ **Task 5.4.3:** User acceptance testing
- ⏳ **Task 5.4.4:** Update documentation
- ⏳ **Task 5.4.5:** Commit and tag: `timeline-phase5-complete`

#### Session Notes

**Session:** (To be filled)  
**Progress:** (To be filled)  
**Blockers:** (To be filled)  
**Next Steps:** Begin Phase 6

---

### Phase 5 Summary

**Deliverables:** (To be filled)  
**Test Coverage:** (To be filled)  
**Lines of Code:** (To be filled)  
**Blockers Encountered:** (To be filled)  
**Lessons Learned:** (To be filled)

---

## Phase 6: Dynamic Temporal RAG

**Duration:** 2 weeks (10 working days)  
**Status:** ⏸️ Waiting (Depends on Phase 5)  
**Progress:** 0%  
**Tests:** 0/0 passing

### Goals

- Implement dynamic timeline construction from queries
- Implement topic extraction
- Implement answer synthesis with temporal context
- Integrate with documentation reader, tech browser, API explorer

### Sub-Phases

---

### Sub-Phase 6.1: Topic Extraction & Document Finding

**Duration:** 2 days  
**Status:** ⏸️ Waiting  
**Dependencies:** Phase 5 Complete

#### Tasks

- ⏳ **Task 6.1.1:** Implement `TopicExtractor`
  - [ ] Extract endpoints, parameters, services, technologies, concepts
  - [ ] Use NLP (spaCy)
  - [ ] Add confidence scoring
  - **Location:** `services/ecosystem-mcp/src/services/dynamic_rag/topic_extractor.py` (new file)
  - **Reference:** `TIMELINE_ANALYSIS_DYNAMIC_TEMPORAL_RAG_ENHANCEMENT.md` Section 5.2

- ⏳ **Task 6.1.2:** Implement `DocumentFinder`
  - [ ] Semantic search for topics
  - [ ] Relevance ranking
  - [ ] Deduplication
  - **Location:** `services/ecosystem-mcp/src/services/dynamic_rag/document_finder.py` (new file)

- ⏳ **Task 6.1.3:** Unit tests
- ⏳ **Task 6.1.4:** Integration tests
- ⏳ **Task 6.1.5:** Logging
- ⏳ **Task 6.1.6:** Commit work

#### Session Notes

**Session:** (To be filled)  
**Progress:** (To be filled)  
**Blockers:** (To be filled)

---

### Sub-Phase 6.2: Dynamic Timeline Construction

**Duration:** 2 days  
**Status:** ⏸️ Waiting  
**Dependencies:** Sub-Phase 6.1

#### Tasks

- ⏳ **Task 6.2.1:** Implement `DynamicTimelineConstructor`
  - [ ] Build temporary timelines from document sets
  - [ ] Auto-generate periods
  - [ ] Calculate confidence
  - [ ] Cache for 1 hour
  - **Location:** `services/ecosystem-mcp/src/services/dynamic_rag/dynamic_timeline_constructor.py` (new file)

- ⏳ **Task 6.2.2:** Unit tests
- ⏳ **Task 6.2.3:** Integration tests
- ⏳ **Task 6.2.4:** Logging
- ⏳ **Task 6.2.5:** Commit work

#### Session Notes

**Session:** (To be filled)  
**Progress:** (To be filled)  
**Blockers:** (To be filled)

---

### Sub-Phase 6.3: Answer Synthesis & Citation

**Duration:** 2 days  
**Status:** ⏸️ Waiting  
**Dependencies:** Sub-Phase 6.2

#### Tasks

- ⏳ **Task 6.3.1:** Implement `TemporalAnswerSynthesizer`
  - [ ] Generate narrative from temporal analysis
  - [ ] Use LLM for synthesis
  - [ ] Include evolution context
  - **Location:** `services/ecosystem-mcp/src/services/dynamic_rag/answer_synthesizer.py` (new file)

- ⏳ **Task 6.3.2:** Implement `CitationFormatter`
  - [ ] Format citations with temporal context
  - [ ] Link to source documents
  - [ ] Generate "See also" suggestions
  - **Location:** `services/ecosystem-mcp/src/services/dynamic_rag/citation_formatter.py` (new file)

- ⏳ **Task 6.3.3:** Unit tests
- ⏳ **Task 6.3.4:** Integration tests
- ⏳ **Task 6.3.5:** Logging
- ⏳ **Task 6.3.6:** Commit work

#### Session Notes

**Session:** (To be filled)  
**Progress:** (To be filled)  
**Blockers:** (To be filled)

---

### Sub-Phase 6.4: Orchestrator & API

**Duration:** 2 days  
**Status:** ⏸️ Waiting  
**Dependencies:** Sub-Phase 6.3

#### Tasks

- ⏳ **Task 6.4.1:** Implement `DynamicTemporalRAGOrchestrator`
  - [ ] Coordinate entire flow
  - [ ] Manage temporary timelines
  - [ ] Cache results
  - [ ] Handle streaming
  - **Location:** `services/ecosystem-mcp/src/services/dynamic_rag/orchestrator.py` (new file)

- ⏳ **Task 6.4.2:** API endpoint: `POST /api/v1/rag/temporal/query`
  - [ ] Support streaming (SSE)
  - [ ] Add OpenAPI docs
  - **Location:** `services/ecosystem-mcp/src/api/routes/dynamic_rag.py` (new file)

- ⏳ **Task 6.4.3:** Unit tests
- ⏳ **Task 6.4.4:** Integration tests
- ⏳ **Task 6.4.5:** E2E tests
- ⏳ **Task 6.4.6:** Logging
- ⏳ **Task 6.4.7:** Commit work

#### Session Notes

**Session:** (To be filled)  
**Progress:** (To be filled)  
**Blockers:** (To be filled)

---

### Sub-Phase 6.5: UI Integration

**Duration:** 2 days  
**Status:** ⏸️ Waiting  
**Dependencies:** Sub-Phase 6.4

#### Tasks

- ⏳ **Task 6.5.1:** Add "Explain this" to doc reader
  - [ ] Add button to generated docs
  - [ ] Trigger dynamic temporal RAG
  - [ ] Display results in modal
  - **Location:** `services/ecosystem-mcp-dashboard/pages/documentation_viewer.py`

- ⏳ **Task 6.5.2:** Integrate with Technology Browser
  - [ ] Add "Explain Evolution" button
  - **Location:** `services/ecosystem-mcp-dashboard/pages/technology_browser.py`

- ⏳ **Task 6.5.3:** Integrate with API Explorer
  - [ ] Add "Explain Evolution" button
  - **Location:** `services/ecosystem-mcp-dashboard/pages/api_explorer.py`

- ⏳ **Task 6.5.4:** Commit work

#### Session Notes

**Session:** (To be filled)  
**Progress:** (To be filled)  
**Blockers:** (To be filled)

---

### Sub-Phase 6.6: Phase 6 Testing & Validation

**Duration:** 2 days  
**Status:** ⏸️ Waiting  
**Dependencies:** Sub-Phase 6.5

#### Tasks

- ⏳ **Task 6.6.1:** E2E tests
  - [ ] Test full dynamic temporal RAG flow
  - [ ] Test with different query types
  - [ ] Test streaming
  - [ ] Test UI integrations

- ⏳ **Task 6.6.2:** Performance tests
  - [ ] Test response time (< 5s target)
  - [ ] Test caching
  - [ ] Test with large document sets

- ⏳ **Task 6.6.3:** Smoke tests
  - [ ] Test against real codebase
  - [ ] Test all trigger mechanisms

- ⏳ **Task 6.6.4:** Run all tests
- ⏳ **Task 6.6.5:** Update documentation
- ⏳ **Task 6.6.6:** Commit and tag: `timeline-phase6-complete`

#### Session Notes

**Session:** (To be filled)  
**Progress:** (To be filled)  
**Blockers:** (To be filled)  
**Next Steps:** Final validation

---

### Phase 6 Summary

**Deliverables:** (To be filled)  
**Test Coverage:** (To be filled)  
**Lines of Code:** (To be filled)  
**Blockers Encountered:** (To be filled)  
**Lessons Learned:** (To be filled)

---

## Testing Matrix

### Test Coverage by Phase

| Phase | Unit | Integration | E2E | Smoke | Functional | Total |
|-------|------|-------------|-----|-------|------------|-------|
| 1 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 |
| 2 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 |
| 3 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 |
| 4 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 |
| 5 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 |
| 6 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 |
| **Total** | **0/0** | **0/0** | **0/0** | **0/0** | **0/0** | **0/0** |

### Test Commands

```bash
# Run all unit tests
pytest tests/unit/ -v --cov=services/ecosystem-mcp/src

# Run all integration tests
pytest tests/integration/ -v

# Run all E2E tests
pytest tests/e2e/ -v

# Run smoke tests
python scripts/smoke_tests/test_timeline_phase1.py
python scripts/smoke_tests/test_timeline_phase2.py
# ... etc

# Run functional tests
pytest tests/functional/ -v

# Run all tests
pytest tests/ -v --cov=services/ecosystem-mcp/src --cov-report=html
```

---

## Session Handoff Protocol

### Starting a New Session

1. **Read Quick Status Overview**
   - Check current phase and sub-phase
   - Review progress percentage
   - Check for blockers

2. **Read Session Handoff Notes**
   - Understand context from previous session
   - Review next steps
   - Note any important warnings

3. **Check Blockers Section**
   - Resolve any blockers before proceeding
   - Update blocker status

4. **Review Current Sub-Phase Tasks**
   - Find first incomplete task (⏳ or ⭐)
   - Read task details and references
   - Begin implementation

### During a Session

1. **Update Task Status**
   - Change ⏳ to ✅ when complete
   - Add notes to Session Notes

2. **Add Logging**
   - Log all major operations
   - Include context (IDs, counts, etc.)
   - Use structured logging

3. **Write Tests**
   - Unit tests for all new code
   - Integration tests for service interactions
   - E2E tests for full workflows
   - Target 90%+ coverage

4. **Document APIs**
   - Add OpenAPI/Swagger annotations
   - Include request/response examples
   - Document error codes

5. **Commit Regularly**
   - Commit after each task or sub-phase
   - Use descriptive commit messages
   - Update this document with each commit

### Ending a Session

1. **Update Status**
   - Update Current Phase/Sub-Phase
   - Update Progress percentage
   - Update Last Updated timestamp

2. **Write Session Handoff Notes**
   - Summarize what was accomplished
   - List next steps clearly
   - Document any issues or blockers
   - Provide context for next session

3. **Run Tests**
   - Run all tests for completed work
   - Document any failures

4. **Commit Everything**
   - Commit this document
   - Commit all code changes
   - Push to remote

5. **Tag if Phase Complete**
   - Create git tag for completed phases
   - Push tag to remote

---

## Troubleshooting Guide

### Common Issues

#### Issue: Tests Failing

**Symptoms:** pytest returns failures

**Solutions:**
1. Check test logs for specific errors
2. Verify database migrations ran
3. Check service dependencies are running
4. Verify test data is correct
5. Run tests individually to isolate issue

#### Issue: Import Errors

**Symptoms:** `ModuleNotFoundError` or `ImportError`

**Solutions:**
1. Verify file exists at expected location
2. Check `__init__.py` files exist
3. Verify Python path is correct
4. Check for circular imports

#### Issue: Database Errors

**Symptoms:** `sqlalchemy` errors, connection errors

**Solutions:**
1. Verify database is running
2. Check migrations have been applied
3. Verify connection string is correct
4. Check for schema mismatches

#### Issue: API Endpoint Not Found

**Symptoms:** 404 errors when calling API

**Solutions:**
1. Verify route is registered in main app
2. Check route path matches request
3. Verify service is running
4. Check for typos in URL

#### Issue: Confidence System Not Working

**Symptoms:** Incorrect confidence levels, validation not working

**Solutions:**
1. Verify documents have correct `ingestion_mode`
2. Check `git_commit_sha` is set for git_history docs
3. Verify confidence calculator logic
4. Check confidence thresholds

### Getting Help

If stuck:
1. Review planning documents for context
2. Check existing similar code
3. Review test cases for examples
4. Check logs for detailed errors
5. Document the issue in Blockers section

---

## Blockers

### Active Blockers

(None currently)

### Resolved Blockers

(To be filled as blockers are encountered and resolved)

---

## Appendix

### Key Files Reference

**Planning Documents:**
- `TIMELINE_BASED_DOCUMENT_ANALYSIS_PLAN.md` - Original comprehensive plan
- `TIMELINE_ANALYSIS_ENRICHED_PLAN.md` - Service reuse strategy
- `TIMELINE_ANALYSIS_FINAL_REFINED_PLAN.md` - Doc gen + RAG integration
- `TIMELINE_ANALYSIS_GRACEFUL_FALLBACK_ADDENDUM.md` - Confidence system
- `TIMELINE_ANALYSIS_COMPLETE_IMPLEMENTATION_GUIDE.md` - Implementation guide
- `TIMELINE_ANALYSIS_DYNAMIC_TEMPORAL_RAG_ENHANCEMENT.md` - Dynamic RAG
- `TIMELINE_ANALYSIS_MASTER_IMPLEMENTATION_PLAN.md` - This document

**Key Directories:**
- `services/ecosystem-mcp/src/services/timeline/` - Timeline services
- `services/ecosystem-mcp/src/services/dynamic_rag/` - Dynamic RAG services
- `services/ecosystem-mcp/src/services/maintenance/` - Maintenance services
- `services/ecosystem-mcp/src/api/routes/` - API endpoints
- `services/ecosystem-mcp/src/storage/` - Database models and migrations
- `services/ecosystem-mcp-dashboard/pages/` - Dashboard pages
- `tests/` - All tests

### Useful Commands

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f ecosystem-mcp

# Run migrations
docker-compose exec ecosystem-mcp python -m src.storage.migrations.run_migrations

# Run tests
docker-compose exec ecosystem-mcp pytest tests/ -v

# Access database
docker-compose exec postgres psql -U postgres -d ecosystem_mcp

# Rebuild services
docker-compose up -d --build

# Stop services
docker-compose down
```

---

**Document Version:** 1.0  
**Created:** 2025-10-22  
**Last Updated:** 2025-10-22 15:45:00  
**Status:** 🟡 IN PROGRESS - Phase 0 Complete, Phase 1 Ready to Start  
**Total Progress:** 0/31 features (0%)

---

## 🎯 NEXT SESSION START HERE

**Current Phase:** Phase 0 Complete  
**Next Phase:** Phase 1, Sub-Phase 1.1  
**Next Task:** Task 1.1.1 - Design database schema

**Instructions for Next Session:**
1. Read [Sub-Phase 1.1](#sub-phase-11-database-schema-design--migration)
2. Begin with Task 1.1.1: Design database schema
3. Create `TimelineModel`, `TimePeriodModel`, `DocumentPlacementModel`
4. Follow the task checklist
5. Update this document as you progress
6. Commit work when sub-phase complete

**Important Reminders:**
- Follow thin facade pattern
- Leverage existing services (97%+ reuse)
- Add confidence checks to all temporal operations
- Include comprehensive logging
- Write tests for all new code (90%+ coverage)
- Document APIs with OpenAPI/Swagger
- Update this document regularly

**Good luck! 🚀**

