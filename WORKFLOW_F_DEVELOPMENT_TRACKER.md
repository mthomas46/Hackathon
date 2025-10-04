# Workflow F Development Tracker
## User Intelligence & Expert Discovery Enhancement

**Goal**: Enhance project-planning-service with user intelligence, expert discovery, and SME identification to provide rich context about potential contacts and subject matter experts.

---

## Development Phases

### ✅ Phase 0: Infrastructure Setup (COMPLETE)
**Status**: ✅ Complete  
**Commit**: `4a7594eb`

- [x] Create expert-finder-service as standalone microservice
- [x] Docker infrastructure (Dockerfile, docker-compose)
- [x] Network integration (hackathon_default)
- [x] 6 API endpoints implemented
- [x] Workflow F base implementation

---

### 🔄 Phase 1: Workflow F Core - User Extraction & Testing
**Status**: 🔄 In Progress  
**Target**: Unit tests for all user extraction logic

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

---

### Phase 2: Expert Finder Service - API Testing
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

