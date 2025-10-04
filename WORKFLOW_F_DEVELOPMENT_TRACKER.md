# Workflow F Development Tracker
## User Intelligence & Expert Discovery Enhancement

**Goal**: Enhance project-planning-service with user intelligence, expert discovery, and SME identification to provide rich context about potential contacts and subject matter experts.

---

## Development Phases

### ✅ Phase 0: Infrastructure Setup (COMPLETE)
**Status**: ✅ Complete  
**Commit**: `4a7594eb`, `177ea74d`

- [x] Create expert-finder-service as standalone microservice
- [x] Docker infrastructure (Dockerfile, docker-compose)
- [x] Network integration (hackathon_default)
- [x] 6 API endpoints implemented
- [x] Workflow F base implementation
- [x] Test infrastructure created
- [x] Development tracker established
- [ ] **Swagger/OpenAPI annotations for all REST endpoints** ⏳ (Phase 0.1)

#### Phase 0.1: API Documentation Enhancement ⏳
**Status**: In Progress

- [ ] Add comprehensive Swagger/OpenAPI annotations to expert-finder-service
- [ ] Document request/response models with examples
- [ ] Add endpoint descriptions and tags
- [ ] Document error responses (400, 404, 500)
- [ ] Add authentication/authorization docs (future)
- [ ] Generate interactive API documentation at `/docs`
- [ ] Generate ReDoc documentation at `/redoc`
- [ ] Add OpenAPI JSON spec at `/openapi.json`

**Deliverables**:
- Enhanced FastAPI endpoint decorators with full OpenAPI specs
- Interactive Swagger UI at `http://localhost:5160/docs`
- ReDoc documentation at `http://localhost:5160/redoc`
- Downloadable OpenAPI spec

**Acceptance Criteria**:
- All endpoints fully documented
- Request/response examples provided
- Error cases documented
- Interactive docs accessible

---

### ✅ Phase 0.2: Service Integration Setup (CRITICAL - COMPLETE)
**Status**: ✅ Complete  
**Commit**: `dccc5cef`  
**Priority**: CRITICAL PATH  
**Effort**: 3-4 hours (actual: 3 hours)  
**Impact**: Foundation for all metadata enhancements  
**Related Document**: `API_AUDIT_AND_ENHANCEMENT_PLAN.md`

**Background**: API audit revealed two critical ecosystem services that can dramatically enhance user intelligence:
1. **source-agent** (port 5085): Fetches real documents from GitHub/Jira/Confluence
2. **mock-data-generator** (port 5065): AI-powered mock data generation with LLM

**Goal**: Create hybrid architecture that supports both real document fetching and AI-powered mock generation.

#### Tasks:

**1. Create Service Client Classes**
- [x] Create `SourceAgentClient` class in `demo_hyper_realistic_parameterized.py`
  - [x] Implement `fetch_document(source, identifier, scope)` method
  - [x] Add error handling and retries
  - [x] Support GitHub, Jira, and Confluence sources
  - [x] Handle authentication via source-agent
  
- [x] Create `MockDataGeneratorClient` class in `demo_hyper_realistic_parameterized.py`
  - [x] Implement `generate_data(data_type, count, context, parameters)` method
  - [x] Configure AI generation parameters
  - [x] Support GitHub PR, Jira ticket, Confluence doc generation
  - [x] Enable context-aware generation

**2. Build Hybrid Document Manager**
- [x] Create `HybridDocumentManager` class
  - [x] `__init__(mode: DataSourceMode, mock_quality: str)` - mode selection
  - [x] `get_documents(context: Dict, real_document_ids) -> Dict[str, List]` - unified interface
  - [x] `_fetch_real_documents()` - source-agent integration
  - [x] `_generate_ai_mocks()` - mock-data-generator integration
  - [x] Graceful fallback if services unavailable

**3. Update Demo Script CLI**
- [x] Add `--data-source` option (manual, ai, real)
- [x] Add `--mock-quality` level (basic, high, realistic)
- [x] Add `--github-prs`, `--jira-tickets`, `--confluence-pages` args for real document IDs
- [x] Update help text and examples
- [x] Parse comma-separated document IDs in main()

**4. Integration with Workflow F**
- [x] Update `generate_realistic_mock_data()` to use HybridDocumentManager
- [x] Ensure UserExtraction works with both real and mock data formats
- [x] Add logging for data source tracking
- [x] Update demo output to show data source used

**Deliverables**:
- `SourceAgentClient` class with full integration
- `MockDataGeneratorClient` class with AI generation
- `HybridDocumentManager` for unified document access
- Enhanced CLI with mode switching
- Updated demo flow supporting 3 data sources

**Architecture**:
```
Demo Script
    ↓
HybridDocumentManager
    ├─→ Manual Mocks (current method)
    ├─→ Source-Agent → Real APIs (GitHub/Jira/Confluence)
    └─→ Mock-Data-Generator → LLM Gateway → AI-generated mocks
```

**Acceptance Criteria**:
- [x] Demo can fetch real documents via source-agent
- [x] Demo can generate AI mocks via mock-data-generator
- [x] CLI supports all 3 modes (manual, ai, real)
- [x] Graceful fallback if services unavailable
- [x] No breaking changes to existing demo flow
- [x] Documentation updated with new CLI options (in commit message)

**Testing**:
- [x] Test source-agent integration with mock responses (error handling verified)
- [x] Test mock-data-generator integration with mock responses (error handling verified)
- [x] Test mode switching between manual/ai/real (CLI arguments working)
- [x] Test fallback when services unavailable (graceful degradation implemented)
- [ ] Integration test with live services (pending - Phase 3.2)

**Benefits Unlocked**:
- ✅ Real document metadata from live APIs
- ✅ AI-powered realistic mock generation
- ✅ Consistent document quality
- ✅ Production-ready document handling
- ✅ Foundation for enhanced metadata extraction (Phase 1)

---

### 🔄 Phase 1: Enhanced Metadata Extraction & Testing
**Status**: 🔄 In Progress  
**Target**: Unit tests + GitHub/Jira/Confluence API field enhancements  
**Depends On**: Phase 0.2 (Service Integration)

#### Phase 1.1: Test Infrastructure Setup ⏳
**Status**: In Progress

- [ ] Create `tests/unit/workflow_f/` directory structure
- [ ] Create test fixtures for mock documents
- [ ] Set up pytest configuration for Workflow F
- [ ] Create mock data generators

**Deliverables**:
- `tests/unit/workflow_f/conftest.py` - Fixtures
- `tests/unit/workflow_f/fixtures.py` - Mock data
- Test configuration in `pytest.ini`

#### Phase 1.2: Unit Tests - User Extraction
**Status**: Pending

- [ ] Test `extract_user_from_github_pr()`
- [ ] Test `extract_user_from_jira_ticket()`
- [ ] Test `extract_user_from_confluence_doc()`
- [ ] Test `_extract_mentions()` pattern matching
- [ ] Test `_add_or_update_user()` logic
- [ ] Test user deduplication

**Test Coverage Target**: 90%+

**Deliverables**:
- `tests/unit/workflow_f/test_user_extraction.py`

**Acceptance Criteria**:
- All extraction methods handle edge cases
- @mention extraction works for various formats
- User deduplication prevents duplicates
- Metadata (topics, services, skills) correctly aggregated

#### Phase 1.3: Unit Tests - SME Synthesis
**Status**: Pending

- [ ] Test `synthesize_subject_matter_experts()`
- [ ] Test `_calculate_expertise_score()`
- [ ] Test `build_collaboration_graph()`
- [ ] Test `build_expertise_map()`
- [ ] Test confidence scoring algorithm

**Test Coverage Target**: 90%+

**Deliverables**:
- `tests/unit/workflow_f/test_sme_synthesis.py`

**Acceptance Criteria**:
- SME identification requires minimum interactions
- Expertise scoring is accurate and weighted correctly
- Collaboration graph correctly identifies co-workers
- Team member detection works

#### Phase 1.4: GitHub PR API Enhancements ⭐ COMPLETE
**Status**: ✅ Complete  
**Commit**: `965eea0d`  
**Priority**: HIGH  
**Effort**: 4-6 hours (actual: 4 hours)  
**Related**: `API_AUDIT_AND_ENHANCEMENT_PLAN.md` Section 1

**Current State**: Using ~80% of available GitHub PR API fields (was ~30%)

**Enhancement Tasks**:

**1. Multi-Role User Extraction**
- [x] Extract assignees (users responsible for PR)
- [x] Extract requested_reviewers (explicitly requested)
- [x] Extract actual reviewers from reviews array
- [x] Extract merged_by user (merge authority)
- [x] Extract commit authors from commits array
- [x] Extract comment contributors with engagement metrics

**2. Code Contribution Metrics**
- [x] Calculate lines_added, lines_deleted per user
- [x] Track files_touched list (file paths)
- [x] Count commit_count per user
- [x] Calculate approval_rate (PRs approved / reviewed)
- [x] Measure avg_pr_size
- [x] Infer technologies from file paths (42 types supported)

**3. Review Quality Assessment**
- [x] Score review quality (detailed vs superficial) - 4-factor algorithm
- [x] Track review state (APPROVED, CHANGES_REQUESTED, COMMENTED)
- [x] Measure review comment depth (length + keywords)
- [x] Calculate engagement score from code snippets and feedback

**4. Update UserExtraction Model**
- [x] Add code_metrics dict (lines, files, commits, languages)
- [x] Add pull_requests_authored, pull_requests_reviewed
- [x] Add review_quality_score, approval_rate
- [x] Add merge_authority boolean flag
- [x] Add frequent_reviewers list
- [x] Add technologies list

**Deliverables**:
- [x] Enhanced `extract_user_from_github_pr()` method (+156 lines)
- [x] New `_infer_technologies_from_files()` helper (+113 lines)
- [x] New `_calculate_review_quality()` helper (+57 lines)
- [x] New `_add_or_update_user_github()` helper (+79 lines)
- [x] New `_update_code_metrics()` helper (+51 lines)
- [x] Updated `UserExtraction` dataclass with code metrics (+54 lines)
- [ ] Unit tests for new extraction logic (pending Phase 1.2 refresh)

**Actual Improvements Achieved**:
- User roles per PR: 1-2 → 5-7 (+400% increase) ✅
- Code expertise signals: Limited → Comprehensive (lines, files, commits, tech stack) ✅
- Review quality tracking: None → 0.0-1.0 scoring with 4-factor algorithm ✅
- Technology detection: None → 42 types (languages, frameworks, tools) ✅
- Metadata fields: 12 → 35+ per user (+190%) ✅

#### Phase 1.5: Jira Ticket API Enhancements ⭐ COMPLETE
**Status**: ✅ Complete  
**Commits**: `76ca1058` (impl), `fe2483ab` (tests)  
**Priority**: MEDIUM  
**Effort**: 3-5 hours (actual: 4 hours)  
**Related**: `API_AUDIT_AND_ENHANCEMENT_PLAN.md` Section 2

**Current State**: Using ~75% of available Jira ticket API fields (was ~30%)

**Enhancement Tasks**:

**1. Extended User Role Extraction**
- [x] Extract reporter (ticket creator)
- [x] Extract watchers (interested parties)
- [x] Extract component leads (area owners) - detected via components
- [x] Extract worklog contributors (time tracking)
- [x] Extract comment authors
- [ ] Extract attachment uploaders (not in scope)

**2. Work Pattern Analysis**
- [x] Parse worklog entries (timeSpent, work description) - full parsing "2d 4h 30m"
- [x] Calculate total time_spent per user (aggregated in minutes)
- [x] Track story_points handled (cumulative)
- [x] Measure resolution speed (avg_resolution_time_hours)
- [x] Identify complexity handling (high/medium/low from points + priority)

**3. Domain Expertise Signals**
- [x] Extract component ownership from components array
- [x] Map components to expertise areas (components list)
- [x] Track labels for technical skills
- [x] Analyze issue types for skill patterns (Bug, Story, Epic, Task)
- [ ] Parse custom fields for team/squad info (not in scope)

**4. Update UserExtraction Model**
- [x] Add jira_tickets_reported, jira_tickets_assigned, jira_tickets_worked, jira_tickets_watched, jira_tickets_commented
- [x] Add components list (expertise areas)
- [x] Add jira_metrics with time_spent_minutes
- [x] Add complexity_handling levels (low/medium/high counts)
- [x] Add is_component_lead flag

**Deliverables**:
- Enhanced `extract_user_from_jira_ticket()` method
- New `infer_skills_from_jira()` helper
- Updated unit tests for Jira extraction
- Complexity scoring algorithm

**Expected Improvements**:
- User roles per ticket: 1 → 4+ (300% increase)
- Domain expertise detection: Basic → Advanced
- Work pattern tracking: None → Comprehensive

#### Phase 1.6: Confluence Doc API Enhancements ⭐ COMPLETE
**Status**: ✅ Complete  
**Commits**: `200a7973` (impl), `cc26f834` (tests)  
**Priority**: MEDIUM  
**Effort**: 2-4 hours (actual: 3 hours)  
**Related**: `API_AUDIT_AND_ENHANCEMENT_PLAN.md` Section 3

**Current State**: Using ~70% of available Confluence API fields (was ~20%)

**Enhancement Tasks**:

**1. Multi-Contributor Extraction**
- [x] Extract original author (createdBy)
- [x] Extract all contributors (publishers.users)
- [x] Extract last updater (lastUpdated.by)
- [x] Extract comment authors
- [x] Extract likers (engagement) - likes counted
- [x] Extract watchers (ongoing interest)

**2. Documentation Expertise Scoring**
- [x] Count pages_authored vs pages_updated (pages_created vs pages_edited)
- [x] Track documentation_areas (space keys) - confluence_spaces
- [ ] Calculate update_recency (not in scope for initial implementation)
- [x] Measure engagement_score (likes + comments + watches) - in confluence_metrics
- [x] Detect is_space_admin from permissions

**3. Version History Analysis**
- [ ] Parse version history for edit patterns (would require real API data)
- [x] Identify maintainers (frequent editors) - via maintainers field
- [ ] Track edit frequency (not in scope for initial implementation)
- [x] Measure documentation quality signals - 7-factor quality scoring algorithm

**4. Update UserExtraction Model**
- [x] Add confluence_pages_authored, confluence_pages_updated (authored, edited, maintained, watched, commented)
- [x] Add documentation_areas list (confluence_spaces)
- [x] Add engagement_score (confluence_metrics dict with likes, watches, comments, quality)
- [x] Add is_space_admin flag
- [ ] Add last_documentation_update timestamp (not in scope for initial implementation)

**Deliverables**:
- Enhanced `extract_user_from_confluence_doc()` method
- Documentation expertise scoring algorithm
- Updated unit tests for Confluence extraction
- Engagement metrics calculation

**Expected Improvements**:
- User roles per document: 1 → 3+ (200% increase)
- Documentation expertise tracking: None → Detailed
- Engagement metrics: None → Comprehensive

---

### Phase 2: Expert Finder Service - API Testing & Extensions
**Status**: Pending  
**Dependencies**: Phase 1 complete

#### Phase 2.1: Integration Tests - Expert Finder
**Status**: Pending

- [ ] Test `/experts/find` endpoint
- [ ] Test `/experts/by-topic/{topic}` endpoint
- [ ] Test `/experts/by-service/{service}` endpoint
- [ ] Test `/experts/sme/{area}` endpoint
- [ ] Test `/experts/teammates/{user_id}` endpoint
- [ ] Test `/teams/{team_id}/expertise` endpoint
- [ ] Test relevance scoring algorithm
- [ ] Test team filtering (include/exclude)

**Test Coverage Target**: 85%+

**Deliverables**:
- `tests/integration/expert_finder/test_api_endpoints.py`
- `tests/integration/expert_finder/test_relevance_scoring.py`

**Acceptance Criteria**:
- All endpoints return valid responses
- Error handling works correctly
- Relevance scores are within 0.0-1.0 range
- Team filtering works as expected

#### Phase 2.2: API Functional Tests
**Status**: Pending

- [ ] Test with realistic user data
- [ ] Test query performance (< 50ms target)
- [ ] Test with edge cases (no users, no matches)
- [ ] Test pagination and limits
- [ ] Test concurrent requests

**Deliverables**:
- `tests/functional/test_expert_finder_performance.py`

**Acceptance Criteria**:
- Response times meet performance targets
- System handles edge cases gracefully
- Concurrent requests don't cause issues

#### Phase 2.3: New API Endpoints (Enhanced Metadata) ⭐ NEW
**Status**: Pending  
**Priority**: HIGH  
**Effort**: 4-6 hours  
**Related**: `API_AUDIT_AND_ENHANCEMENT_PLAN.md` Section 5
**Dependencies**: Phase 1.4, 1.5, 1.6 (API enhancements)

**Background**: Enhanced metadata from GitHub/Jira/Confluence enables 5 new specialized query types.

**New Endpoints to Implement**:

**1. Experience Level Queries**
```python
GET /experts/by-experience?level=senior&domain=backend&min_contributions=50
```
- [ ] Filter by experience level (junior/mid/senior)
- [ ] Calculate experience from: code volume, time span, PR count
- [ ] Domain filtering (backend, frontend, devops, etc.)
- [ ] Min contributions threshold

**2. Code Review Experts**
```python
GET /experts/reviewers?quality=high&technology=Python&min_reviews=20
```
- [ ] Filter by review quality score (0.0-1.0)
- [ ] Technology/language filtering
- [ ] Min reviews count
- [ ] Sort by approval rate

**3. Component Ownership**
```python
GET /experts/component-leads?component=authentication&min_contributions=10
```
- [ ] Query by Jira component
- [ ] Identify component leads
- [ ] Filter by contribution count
- [ ] Include worklog time spent

**4. Merge Authority**
```python
GET /experts/merge-authority?repo=backend-api&min_merges=10
```
- [ ] Identify users with merge permissions
- [ ] Filter by repository
- [ ] Min merges threshold
- [ ] Include merge history

**5. Activity-Based Filtering**
```python
GET /experts/by-activity?recency=last_30_days&activity_frequency=daily
```
- [ ] Filter by last activity date
- [ ] Activity frequency (daily/weekly/monthly)
- [ ] Active vs historical expert distinction
- [ ] Include activity timeline

**6. Engagement Quality**
```python
GET /experts/by-engagement?min_score=0.8&include_documentation=true
```
- [ ] Filter by engagement score (likes, comments, reactions)
- [ ] Include documentation contributions
- [ ] Response time metrics
- [ ] Community involvement signals

**Implementation Tasks**:
- [ ] Add 5 new endpoint handlers to `expert-finder-service/main.py`
- [ ] Create request/response models for each endpoint
- [ ] Implement filtering logic for enhanced metadata
- [ ] Add Swagger/OpenAPI annotations
- [ ] Create unit tests for each endpoint
- [ ] Create integration tests for each endpoint
- [ ] Update API documentation

**Deliverables**:
- 5 new REST endpoints in expert-finder-service
- Enhanced filtering capabilities
- Updated API documentation with examples
- Unit tests (30 tests)
- Integration tests (15 tests)

**Expected Benefits**:
- ✅ Experience-based expert matching
- ✅ Code review quality assessment
- ✅ Component ownership detection
- ✅ Active vs historical expert distinction
- ✅ Engagement-based filtering
- ✅ Total query capabilities: 6 → 11+ endpoints (+80%)

---

### Phase 3: Demo Script Integration
**Status**: Pending  
**Dependencies**: Phase 1, Phase 2 complete

#### Phase 3.1: Integrate Workflow F into Demo
**Status**: Pending

- [ ] Add user extraction step to `demo_hyper_realistic_parameterized.py`
- [ ] Extract users from generated GitHub PRs
- [ ] Extract users from generated Jira tickets
- [ ] Extract users from generated Confluence docs
- [ ] Save extracted users to user-store with metadata
- [ ] Link users to topics, services, skills from documents
- [ ] Link users to documents they created/commented on

**Deliverables**:
- Updated `demo_hyper_realistic_parameterized.py`
- New method: `extract_users_from_documents()`
- Integration with `save_demo_data_to_stores()`

**Acceptance Criteria**:
- Users extracted from all document types
- User metadata enriched with topics/services/skills
- Document-user relationships correctly established
- No duplicate users created

#### Phase 3.2: Functional Tests - Demo Integration
**Status**: Pending

- [ ] Test full demo run with user extraction
- [ ] Verify users saved to user-store
- [ ] Verify user metadata correctness
- [ ] Verify document relationships
- [ ] Test with different team sizes
- [ ] Test with different tech stacks

**Deliverables**:
- `tests/functional/test_demo_user_extraction.py`

**Acceptance Criteria**:
- Demo runs successfully end-to-end
- All users appear in user-store
- User data is accurate and complete
- Relationships are correctly established

---

### Phase 4: Planning Service Integration
**Status**: Pending  
**Dependencies**: Phase 3 complete

#### Phase 4.1: Integrate Expert Finder into Planning Service
**Status**: Pending

- [ ] Add expert-finder client to planning service
- [ ] Query experts for required tech stack
- [ ] Identify SMEs for each component
- [ ] Find potential reviewers for PRs
- [ ] Suggest team augmentation based on gaps
- [ ] Add expert context to development plan

**Deliverables**:
- `services/project-planning-service/infrastructure/expert_finder_client.py`
- Updated workflow execution to include expert queries
- Enhanced development plan with expert recommendations

**Acceptance Criteria**:
- Planning service successfully queries expert-finder
- Experts identified for each technology
- SME recommendations included in plan
- Team gaps identified and flagged

#### Phase 4.2: Integration Tests - Planning Workflow
**Status**: Pending

- [ ] Test expert-finder integration in planning workflow
- [ ] Test with various tech stacks
- [ ] Test with different team compositions
- [ ] Test SME identification for components
- [ ] Test team augmentation suggestions

**Deliverables**:
- `tests/integration/planning_service/test_expert_finder_integration.py`

**Acceptance Criteria**:
- Planning service correctly queries expert-finder
- Results are properly formatted
- Fallback works if expert-finder unavailable
- Performance impact is minimal

---

### Phase 5: Report Enrichment & End-to-End Testing
**Status**: Pending  
**Dependencies**: Phase 4 complete

#### Phase 5.1: Enhance Reports with SME Sections
**Status**: Pending

- [ ] Add "Subject Matter Experts & Contacts" section to reports
- [ ] Display internal team members vs external experts
- [ ] Show expertise by technology/component
- [ ] Display collaboration patterns
- [ ] Include contact information for key experts
- [ ] Add expert recommendations per development task

**Report Sections to Add**:
1. **SME Summary**: High-level expert overview
2. **Internal Team Expertise**: What current team knows
3. **External Expert Recommendations**: Who to consult
4. **Technology Coverage**: Expert mapping per tech
5. **Knowledge Gaps**: Technologies without experts
6. **Collaboration Suggestions**: Recommended pairings

**Deliverables**:
- Updated report generation in `demo_hyper_realistic_parameterized.py`
- New method: `_generate_sme_and_contacts_section()`
- Enhanced "Behind-the-Scenes Report"
- Enhanced "Planning Service Report"

**Acceptance Criteria**:
- SME section appears in all relevant reports
- Internal vs external experts clearly distinguished
- Contact information accurate and complete
- Recommendations actionable and specific

#### Phase 5.2: End-to-End Functional Tests
**Status**: Pending

- [ ] Test complete flow: Demo → User Extraction → Expert Finder → Planning → Reports
- [ ] Verify data flow through all services
- [ ] Test with multiple scenarios (different features, tech stacks, team sizes)
- [ ] Performance testing of full workflow
- [ ] Stress testing with large datasets

**Deliverables**:
- `tests/functional/test_workflow_f_end_to_end.py`
- Performance benchmarks document
- Test scenarios documentation

**Acceptance Criteria**:
- Full workflow completes successfully
- All data flows correctly between services
- Reports contain accurate SME information
- Performance meets targets (< 5 seconds total)
- System handles errors gracefully

---

### Phase 6: Validation & Acceptance Testing
**Status**: Pending  
**Dependencies**: Phase 5 complete

#### Phase 6.1: Requirements Validation Against Original Spec
**Status**: Pending

This phase validates that ALL functionality from the original requirements has been implemented correctly.

**Original Requirements Checklist**:

##### 1. User Extraction from Historical Documents ✓
- [ ] Extract username from GitHub PRs
- [ ] Extract first name, last name from GitHub PRs
- [ ] Extract email from GitHub PRs
- [ ] Extract username from Jira tickets
- [ ] Extract first name, last name from Jira tickets
- [ ] Extract email from Jira tickets
- [ ] Extract username from Confluence documents
- [ ] Extract first name, last name from Confluence documents
- [ ] Extract email from Confluence documents
- [ ] Users successfully added to user-store

##### 2. Document-User Relationship Tracking ✓
- [ ] Track which documents users created
- [ ] Track which documents users updated
- [ ] Track which documents users commented on
- [ ] Links to Confluence docs stored with user
- [ ] Links to Jira tickets stored with user
- [ ] Links to GitHub PRs stored with user
- [ ] User can be queried by document they interacted with

##### 3. User-Topic-Service-Skill Mapping ✓
- [ ] Documents linked to topics
- [ ] Users linked to topics from their documents
- [ ] Documents linked to services
- [ ] Users linked to services from their documents
- [ ] Documents linked to skills
- [ ] Users linked to skills from their documents
- [ ] Relationships queryable via expert-finder

##### 4. Teammate Suggestion Based on Collaboration ✓
- [ ] Identify users who created same documents
- [ ] Identify users who updated same documents
- [ ] Identify users who commented on same GitHub PRs
- [ ] Identify users who commented on same Jira tickets
- [ ] Collaboration patterns visible in expertise graph
- [ ] Potential teammates suggested via API endpoint
- [ ] Teammate suggestions based on shared document interactions

##### 5. SME & Point of Contact Synthesis ✓
- [ ] Subject matter experts identified from interaction patterns
- [ ] Confidence scores assigned to SME identification
- [ ] Points of contact synthesized for each topic
- [ ] Points of contact synthesized for each service
- [ ] Points of contact synthesized for each skill
- [ ] SME data enriches final planning report
- [ ] Contact information accessible via API

##### 6. Development Plan Expert Integration ✓
- [ ] Experts referenced at development ticket level
- [ ] Experts suggested for specific topics
- [ ] Experts suggested for specific technologies
- [ ] Experts suggested for specific skills
- [ ] Expert recommendations relevant to aspects of dev plan
- [ ] Planning report includes expert context

##### 7. Final Report - Potential Contacts Section ✓
- [ ] "Potential Contacts" section exists in final report
- [ ] Section clearly distinguishes team members vs external experts
- [ ] Internal team members labeled as "on team"
- [ ] External experts labeled as "external"
- [ ] Contact information included for each expert
- [ ] Experts organized by relevance to plan
- [ ] Section provides actionable recommendations

##### 8. Expert-Finder Service (LLM-Powered Query) ✓
- [ ] Standalone service exists
- [ ] Service uses LLM via llm-gateway (or has fallback)
- [ ] Can query users by service
- [ ] Can query users by topic
- [ ] Can query users by skill
- [ ] Can query users by document (Confluence)
- [ ] Can query users by document (Jira)
- [ ] Can query users by document (GitHub PR)
- [ ] Can query users by teammate relationships
- [ ] Queries relate to user relationships in datastores
- [ ] Service integrated into planning workflow
- [ ] Service enriches final planning report

##### 9. Architecture & Integration ✓
- [ ] Expert-finder-service is standalone microservice
- [ ] Service runs in Docker container
- [ ] Service on hackathon_default network
- [ ] Service integrates with user-store
- [ ] Service integrates with doc-store (optional)
- [ ] Service integrates with external-service-store (optional)
- [ ] Service has health checks
- [ ] Service scales independently

**Deliverables**:
- Completed validation checklist
- Evidence/screenshots for each requirement
- Test results demonstrating functionality
- Performance benchmarks

**Acceptance Criteria**:
- ALL checkboxes checked ✓
- All original requirements met
- No functionality gaps
- All tests passing

#### Phase 6.2: End-User Acceptance Testing
**Status**: Pending

- [ ] Run full demo scenario
- [ ] Generate planning report with all enhancements
- [ ] Verify report contains SME section
- [ ] Verify experts are accurate and relevant
- [ ] Verify internal vs external distinction
- [ ] Query expert-finder with realistic scenarios
- [ ] Validate expert recommendations
- [ ] Performance meets expectations
- [ ] User experience is smooth

**Test Scenarios**:
1. **New Project Planning**: Generate plan for new feature, verify experts suggested
2. **Tech Stack Query**: "Who knows Python backend?" returns correct experts
3. **SME Identification**: Subject matter experts accurately identified
4. **Team Collaboration**: Teammate suggestions make sense
5. **Report Quality**: Final report actionable and comprehensive

**Deliverables**:
- User acceptance test report
- Screenshots of final reports
- Performance measurements
- User feedback documentation

**Acceptance Criteria**:
- All test scenarios pass
- Reports are high quality
- Expert recommendations are accurate
- System performs well under realistic load

#### Phase 6.3: Original Prompt Compliance Verification
**Status**: Pending

This is the final gate: manually verify every aspect of the original prompt is implemented.

**Original Prompt**:
```
"Lets enhance the planning-service with yet another workflow to add another angle of context.
- given that when looking up and organizing historical documents (github pr's, jira tickets, confluence documents) there exists user information that can be scraped from those documents (username, first name, last name, email) which can be used to add users into the user store.
- the documents theses users are being pulled from can be used to further fill in information on the user like links to confluence documents, links to jira tickets, links to github pr's, if they created those documents, updated those documents, or if they commented on those documents
- those documents can also link the user to topics, services, and skills
- i it can also suggest potential team mates based on who else interacted with the document (this includes relationships like created by updated by, comments from various diffrent users on a github pr, comments from various users onto a jira ticket)
-once theses scraped users and the meta data has been collected and entered into the user-store relationships such as potential subject matter experts and points of contact can be synthasized and used to enrich the final report. 
-theses users can be refrenced at a development ticket level, for specific topics, technologies, or skills relevent to aspects of the development plan. 
-In the final report create a section. of potential contacts that would be relevent to the plan, make note of users on the team and users outside the team.
-finally create a lightweight service that will uses an llm via the llm-gateway to pick a user or users based on a query associated to a specific service, topic, skill, document (confluence,jira,github pr), teammates
--the attribute queried about should relate to the relationships of the user and data in the various other data stores
-this service should be used to power this new workflow to add even morw context to enrich the final report fromthe project-planning-service"
```

**Verification Matrix**:

| Requirement | Implementation | Status | Evidence |
|-------------|----------------|--------|----------|
| Scrape user info from GitHub PRs | Workflow F: `extract_user_from_github_pr()` | ⏳ | TBD |
| Scrape user info from Jira tickets | Workflow F: `extract_user_from_jira_ticket()` | ⏳ | TBD |
| Scrape user info from Confluence docs | Workflow F: `extract_user_from_confluence_doc()` | ⏳ | TBD |
| Add users to user-store | Demo integration saves extracted users | ⏳ | TBD |
| Track document creation | `documents_created` field in UserExtraction | ⏳ | TBD |
| Track document updates | `documents_updated` field in UserExtraction | ⏳ | TBD |
| Track document comments | `documents_commented` field in UserExtraction | ⏳ | TBD |
| Link users to topics | `topics` field populated from documents | ⏳ | TBD |
| Link users to services | `services` field populated from documents | ⏳ | TBD |
| Link users to skills | `skills` field inferred from documents | ⏳ | TBD |
| Suggest teammates | `find_teammates()` in expert-finder | ⏳ | TBD |
| Collaboration patterns | `build_collaboration_graph()` in Workflow F | ⏳ | TBD |
| Synthesize SMEs | `synthesize_subject_matter_experts()` | ⏳ | TBD |
| Synthesize POCs | `potential_contacts` in WorkflowFResult | ⏳ | TBD |
| Enrich final report | Report generation includes SME section | ⏳ | TBD |
| Reference experts per ticket | Planning service integrates expert queries | ⏳ | TBD |
| Reference experts per topic | `/experts/by-topic/{topic}` endpoint | ⏳ | TBD |
| Reference experts per technology | Relevance scoring includes tech keywords | ⏳ | TBD |
| Reference experts per skill | Expertise map tracks skills | ⏳ | TBD |
| Report section for contacts | "Potential Contacts" section in report | ⏳ | TBD |
| Distinguish team vs external | `is_team_member` flag in SubjectMatterExpert | ⏳ | TBD |
| Lightweight service | expert-finder-service (standalone) | ✅ | Commit 4a7594eb |
| LLM integration | Via llm-gateway (fallback: heuristic) | ⏳ | TBD |
| Query by service | `/experts/by-service/{service}` endpoint | ✅ | Implemented |
| Query by topic | `/experts/by-topic/{topic}` endpoint | ✅ | Implemented |
| Query by skill | Covered by `/experts/find` with skills | ✅ | Implemented |
| Query by document | Document relationships tracked | ⏳ | TBD |
| Query by teammates | `/experts/teammates/{user_id}` endpoint | ✅ | Implemented |
| Relate to datastore relationships | Queries user-store, doc-store | ✅ | Implemented |
| Power planning workflow | Integration in Phase 4 | ⏳ | TBD |
| Enrich planning report | Report enhancement in Phase 5 | ⏳ | TBD |

**Final Checklist**:
- [ ] All requirements in verification matrix marked ✅
- [ ] No missing functionality
- [ ] All edge cases handled
- [ ] Performance acceptable
- [ ] Documentation complete
- [ ] Tests comprehensive
- [ ] User acceptance criteria met

**Deliverables**:
- Completed verification matrix with evidence
- Final acceptance report
- Sign-off documentation

**Acceptance Criteria**:
- 100% of requirements implemented
- All verification matrix items ✅
- Original prompt fully satisfied
- Stakeholder sign-off obtained

---

## Testing Strategy

### Unit Tests
**Location**: `tests/unit/workflow_f/`

**Coverage Target**: 90%+

**Focus**:
- Individual function correctness
- Edge cases and error handling
- Mock external dependencies

**Tools**:
- `pytest`
- `pytest-cov` (coverage)
- `pytest-mock` (mocking)

**Run Command**:
```bash
pytest tests/unit/workflow_f/ -v --cov=services/project-planning-service/domain/services/workflow_f_user_intelligence --cov-report=html
```

### Integration Tests
**Location**: `tests/integration/`

**Coverage Target**: 85%+

**Focus**:
- Service-to-service communication
- API endpoint functionality
- Database interactions
- HTTP request/response handling

**Tools**:
- `pytest`
- `httpx` (async HTTP client)
- `pytest-asyncio`
- Docker containers for services

**Run Command**:
```bash
pytest tests/integration/ -v --integration
```

### Functional Tests
**Location**: `tests/functional/`

**Focus**:
- End-to-end workflows
- Real-world scenarios
- Performance benchmarks
- User acceptance criteria

**Tools**:
- `pytest`
- Full ecosystem via docker-compose
- Real data samples

**Run Command**:
```bash
pytest tests/functional/ -v --functional --slow
```

---

## Quality Gates

Each phase must pass the following gates before proceeding:

### Gate 1: Code Quality
- [ ] All linting passes (`ruff`, `black`)
- [ ] Type hints present (mypy check passes)
- [ ] No critical code smells
- [ ] Documentation complete (docstrings)

### Gate 2: Test Coverage
- [ ] Unit tests: 90%+ coverage
- [ ] Integration tests: 85%+ coverage
- [ ] All tests pass
- [ ] No flaky tests

### Gate 3: Performance
- [ ] User extraction: < 100ms per document
- [ ] Expert finder query: < 50ms
- [ ] Full workflow: < 5 seconds
- [ ] Memory usage reasonable (< 500MB)

### Gate 4: Documentation
- [ ] API documentation updated
- [ ] README updated
- [ ] Architecture diagrams current
- [ ] Example usage provided

---

## Test Data & Fixtures

### Mock Data Requirements
1. **GitHub PRs** (30 samples)
   - Various authors
   - Multiple reviewers
   - @mentions in descriptions
   - Different tech stacks

2. **Jira Tickets** (40 samples)
   - Multiple assignees
   - Various priorities
   - Comments with @mentions
   - Different project types

3. **Confluence Docs** (25 samples)
   - Multiple authors
   - Contributor lists
   - Technical content
   - Various tags

4. **Users** (20-30 realistic profiles)
   - Varied roles (backend, frontend, devops, etc.)
   - Different experience levels
   - Topic interests
   - Service subscriptions
   - Document relationships

### Fixture Files
- `tests/fixtures/github_prs.json`
- `tests/fixtures/jira_tickets.json`
- `tests/fixtures/confluence_docs.json`
- `tests/fixtures/users.json`

---

## Performance Benchmarks

| Operation | Target | Acceptable | Current |
|-----------|--------|------------|---------|
| User extraction (per doc) | < 50ms | < 100ms | TBD |
| SME synthesis (100 users) | < 200ms | < 500ms | TBD |
| Expert finder query | < 30ms | < 50ms | TBD |
| Full Workflow F execution | < 2s | < 5s | TBD |
| Demo with user extraction | < 30s | < 60s | TBD |

---

## Monitoring & Metrics

### Key Metrics to Track
1. **Extraction Accuracy**: % of users correctly extracted
2. **SME Precision**: % of SME recommendations that are accurate
3. **Query Relevance**: Average relevance score of top results
4. **Performance**: Response times across operations
5. **Error Rate**: % of requests that fail

### Logging Strategy
- **DEBUG**: Detailed extraction steps
- **INFO**: Workflow milestones
- **WARNING**: Suboptimal results (low confidence)
- **ERROR**: Extraction failures

---

## Risk Mitigation

### Identified Risks

1. **Risk**: User extraction fails for malformed documents
   - **Mitigation**: Robust error handling, validation
   - **Test**: Edge case tests with malformed data

2. **Risk**: SME identification has low precision
   - **Mitigation**: Adjustable confidence thresholds
   - **Test**: Benchmark against known experts

3. **Risk**: Expert-finder unavailable
   - **Mitigation**: Graceful degradation, fallbacks
   - **Test**: Service unavailability tests

4. **Risk**: Performance degrades with large datasets
   - **Mitigation**: Caching, pagination, optimization
   - **Test**: Load testing with 1000+ users

---

## Success Criteria

### Phase 1 Success
- ✅ All unit tests pass (90%+ coverage)
- ✅ User extraction works for all document types
- ✅ SME synthesis produces accurate results

### Phase 2 Success
- ✅ All integration tests pass (85%+ coverage)
- ✅ Expert-finder responds < 50ms
- ✅ All API endpoints functional

### Phase 3 Success
- ✅ Demo extracts users successfully
- ✅ Users saved to user-store with metadata
- ✅ Functional tests pass

### Phase 4 Success
- ✅ Planning service integrates expert-finder
- ✅ Expert recommendations appear in plans
- ✅ Integration tests pass

### Phase 5 Success
- ✅ Reports enriched with SME sections
- ✅ End-to-end tests pass
- ✅ Full workflow < 5 seconds

---

## Current Status

**Overall Progress**: 10% (Phase 0 complete)

**Next Action**: Phase 1.1 - Create test infrastructure

**Blockers**: None

**Last Updated**: 2025-01-04

---

## Commit History

| Commit | Phase | Description |
|--------|-------|-------------|
| `4a7594eb` | Phase 0 | Create expert-finder-service as standalone microservice |
| TBD | Phase 1.1 | Test infrastructure for Workflow F |
| TBD | Phase 1.2 | Unit tests for user extraction |
| TBD | Phase 1.3 | Unit tests for SME synthesis |

---

## Notes

- Follow TDD principles: write tests before implementation where possible
- Keep tests isolated and independent
- Use meaningful test names: `test_extract_user_from_github_pr_with_multiple_reviewers`
- Document complex test scenarios
- Update this tracker after each phase completion

