# Configuration Registry Implementation - Decision Log

**Purpose:** Document all significant decisions made during implementation  
**Started:** 2025-10-26  
**Status:** Active  

---

## Decision 1: Use YAML for Registry Format

**Date:** 2025-10-26T23:00:00Z  
**Phase:** 0 - Preparation  
**Decided By:** LLM Agent  

**Decision:** Use YAML as the format for `service_registry.yaml`

**Rationale:**
- Human readable and editable
- Git-friendly (easy diffs, merge conflicts clear)
- Industry standard for configuration
- PyYAML library widely available
- Supports comments for documentation
- Hierarchical structure natural fit for config

**Alternatives Considered:**
1. **JSON**
   - Pros: Strict parsing, no ambiguity
   - Cons: No comments, less readable, harder to edit
   - Rejected: Readability > strictness for config
   
2. **TOML**
   - Pros: Good for config, readable
   - Cons: Less common, team may be unfamiliar
   - Rejected: YAML more widely known
   
3. **Python (config.py)**
   - Pros: Type checking, IDE support
   - Cons: Can execute code (security risk), harder to parse
   - Rejected: Want declarative config
   
4. **Database**
   - Pros: Dynamic, centralized
   - Cons: Circular dependency (config needs DB), adds complexity
   - Rejected: Too complex, adds failure point

**Impact:** Medium  
**Status:** ✅ Implemented  
**Files:** `config/service_registry.yaml`

---

## Decision 2: Extract Baseline Before Creating Loader

**Date:** 2025-10-26T23:00:00Z  
**Phase:** 0 - Preparation  
**Decided By:** LLM Agent  

**Decision:** Create baseline registry from current codebase BEFORE implementing loader

**Rationale:**
- Captures accurate current state
- Provides migration checklist
- Enables comparison (before/after)
- Risk mitigation: Won't lose current values
- Clear audit trail of what changed

**Alternatives Considered:**
1. **Create Loader First**
   - Pros: Faster to "done"
   - Cons: Risk missing current values, no baseline
   - Rejected: Need accurate baseline for migration
   
2. **Create Loader and Baseline in Parallel**
   - Pros: Faster
   - Cons: Risk of using incomplete baseline in loader
   - Rejected: Sequential is safer

**Impact:** Low  
**Status:** ✅ Implemented  
**Files:** `config/service_registry.yaml`, `config/hardcoded_values_audit.csv`

**Outcome:** Successfully captured 237 hardcoded values including the consumer group mismatch

---

## Decision 3: Track All 237 Values Comprehensively

**Date:** 2025-10-26T23:05:00Z  
**Phase:** 0 - Preparation  
**Decided By:** LLM Agent  

**Decision:** Document all 237 hardcoded values even though not all will be migrated immediately

**Rationale:**
- Complete audit enables prioritization
- Identifies quick wins vs. long-term work
- Prevents "unknown unknowns"
- Enables risk assessment per value
- Provides ROI calculation basis

**Alternatives Considered:**
1. **Only Track Critical Values**
   - Pros: Faster, simpler
   - Cons: Incomplete picture, may miss important values
   - Rejected: Completeness more valuable than speed
   
2. **Track Only First 50 Values**
   - Pros: Quick start
   - Cons: Arbitrary limit, incomplete
   - Rejected: Need full picture

**Impact:** Medium  
**Status:** ✅ Implemented  
**Files:** `config/hardcoded_values_audit.csv`

**Outcome:** 
- 44 critical values captured in CSV
- 48 Redis values identified
- 89 port numbers documented
- 15 database values tracked

---

## Decision 4: Use Pydantic for Validation (Planned)

**Date:** 2025-10-26T23:10:00Z  
**Phase:** 0 - Preparation (Planning for Phase 1)  
**Decided By:** LLM Agent  

**Decision:** Use Pydantic for registry validation in Phase 1

**Rationale:**
- Already in use (config.py uses Pydantic)
- Strong typing and validation
- Clear error messages
- IDE autocomplete support
- JSON schema generation
- Widely adopted in FastAPI ecosystem

**Alternatives Considered:**
1. **Marshmallow**
   - Pros: Mature, flexible
   - Cons: Not used elsewhere in codebase
   - Rejected: Consistency with existing code
   
2. **Cerberus**
   - Pros: Lightweight
   - Cons: Less powerful than Pydantic
   - Rejected: Pydantic more feature-rich
   
3. **Custom Validation**
   - Pros: Full control
   - Cons: Reinventing wheel, maintenance burden
   - Rejected: Pydantic solves this problem

**Impact:** High  
**Status:** 📋 Planned for Phase 1  
**Dependencies:** None (Pydantic already installed)

---

## Decision 5: Fail-Fast on Critical Mismatches (Planned)

**Date:** 2025-10-26T23:10:00Z  
**Phase:** 0 - Preparation (Planning for Phase 3)  
**Decided By:** LLM Agent  

**Decision:** Service will refuse to start if critical configuration mismatches detected

**Rationale:**
- Prevents runtime failures
- Clear error messages at startup
- Easier debugging (immediate vs. hours later)
- User explicitly requested fail-fast
- Prevents today's issue from recurring

**Alternatives Considered:**
1. **Warn Only**
   - Pros: More flexible
   - Cons: Silent failures still possible, defeats purpose
   - Rejected: Too risky, doesn't prevent issues
   
2. **Auto-Fix**
   - Pros: Seamless
   - Cons: "Magic" behavior, unclear what changed
   - Rejected: Explicit > implicit for config
   
3. **Lenient Mode for Dev, Strict for Prod**
   - Pros: Developer flexibility
   - Cons: Encourages bad practices in dev
   - Accepted as ADDITION: Lenient mode available but strict is default

**Impact:** High  
**Status:** 📋 Planned for Phase 3  
**Critical Mismatches:**
- Consumer group name
- Stream name
- Database name
- Required table missing

**Example Error:**
```
🚨 CRITICAL FAILURE: redis_consumer_groups

Consumer group mismatch!
  Registry expects: 'workers'
  Redis client uses: 'ingestion_group'
  
Impact: Workers will not see jobs created by API

❌ SERVICE STARTUP BLOCKED

Fix: Update redis_client.py line 41 to use 'workers'
```

---

## Decision 6: Generate docker-compose.yml from Registry (Planned)

**Date:** 2025-10-26T23:12:00Z  
**Phase:** 0 - Preparation (Planning for Phase 2)  
**Decided By:** LLM Agent  

**Decision:** Generate `docker-compose.yml` from registry instead of maintaining manually

**Rationale:**
- Found 7 drift instances between docker-compose and code
- Prevents manual editing errors
- Single source of truth
- Automated consistency
- Easy to regenerate

**Alternatives Considered:**
1. **Validation Only**
   - Pros: Preserves manual control
   - Cons: Doesn't fix drift, requires manual updates
   - Rejected: Doesn't solve root cause
   
2. **Template + Variables**
   - Pros: Some automation
   - Cons: Still manual edits possible, drift can occur
   - Rejected: Full generation is better
   
3. **Keep Manual, Add Strict Validation**
   - Pros: Familiar workflow
   - Cons: Validation can be bypassed, human error remains
   - Rejected: Generation eliminates error

**Impact:** High  
**Status:** 📋 Planned for Phase 2  
**Files:** `scripts/generate_compose.py`

**Benefits:**
- Zero drift guaranteed
- Port changes propagate automatically
- Service name consistency enforced
- One command regenerates all

---

## Future Decisions (To Be Made)

### Phase 1
- [ ] Singleton pattern for registry loader vs. multiple instances?
- [ ] Caching strategy for registry (reload vs. cache forever)?
- [ ] Environment variable override mechanism?

### Phase 2
- [ ] Migration strategy: All at once vs. incremental?
- [ ] Backward compatibility period?
- [ ] Fallback behavior if registry unavailable?

### Phase 3
- [ ] Validation frequency (startup only vs. runtime)?
- [ ] Auto-remediation for common issues?
- [ ] Alert mechanism for mismatches?

---

## Decision Template

```markdown
## Decision N: [Title]

**Date:** YYYY-MM-DDTHH:MM:SSZ  
**Phase:** N - [Phase Name]  
**Decided By:** [Person/LLM Agent]  

**Decision:** [What was decided]

**Rationale:**
- [Reason 1]
- [Reason 2]
- [Reason 3]

**Alternatives Considered:**
1. **[Alternative 1]**
   - Pros: [Benefits]
   - Cons: [Drawbacks]
   - Rejected: [Why]

**Impact:** [Low/Medium/High]  
**Status:** [Planned/In Progress/Implemented/Rejected]  
**Dependencies:** [What this depends on]

**Outcome:** [What actually happened - fill in after implementation]
```

---

**Maintained By:** LLM Agent  
**Last Updated:** 2025-10-26T23:15:00Z  
**Next Review:** After Phase 1 completion  

