# 🔄 Context Limit Management - Handling Token Constraints

**Version**: 1.0.0  
**Created**: October 9, 2025  
**Status**: Active  
**Purpose**: Protect AI agents from context overflow and enable seamless continuation

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Context Limit Reality](#context-limit-reality)
3. [Warning Signs](#warning-signs)
4. [Preservation Strategy](#preservation-strategy)
5. [Summarization Protocol](#summarization-protocol)
6. [Continuation Protocol](#continuation-protocol)
7. [Validation](#validation)

---

## 🎯 Overview

### The Problem

**AI agents have token limits** (~200K-1M tokens). During refactoring:
- Reading large codebases consumes tokens fast
- Long conversations accumulate history
- Eventually: **context overflow** → forced summarization or new chat

### The Risk

❌ **Without protection**:
- Lose critical context mid-phase
- Forget key decisions
- Repeat completed work
- Break continuity

✅ **With protection**:
- Preserve essential state to disk
- Smart summarization
- Seamless continuation
- Zero context loss

---

## 📊 Context Limit Reality

### Typical Token Consumption

```
Activity                    Tokens Used    Cumulative
─────────────────────────────────────────────────────
Initial instructions        ~5,000         5,000
Read Master Plan            ~15,000        20,000
Read Service Codebase       ~50,000        70,000
Phase 1: Audit              ~10,000        80,000
Phase 2: Design             ~15,000        95,000
Phase 3: TDD (large)        ~100,000       195,000  ⚠️
Phase 4: Integration        ~20,000        215,000  🔴
Phase 5: Documentation      ~25,000        240,000  🔴
Phase 6: Final              ~10,000        250,000  🔴

Chat History Growth         ~50K/hour      Variable
```

**Critical Threshold**: ~150K-200K tokens (starts getting risky)
**Danger Zone**: > 250K tokens (summarization likely needed)

### Services by Size

| Service Type | Codebase Size | Expected Token Use |
|--------------|---------------|-------------------|
| Small (< 500 LOC) | ~10K tokens | Safe (< 100K total) |
| Medium (500-2000 LOC) | ~40K tokens | Caution (150-200K total) |
| Large (2000-5000 LOC) | ~100K tokens | Danger (250K+ total) |
| Very Large (> 5000 LOC) | ~200K+ tokens | **Critical** (400K+ total) |

---

## ⚠️ Warning Signs

### Early Warnings (Proactive)

**Monitor these indicators**:

1. **Token Counter Shows > 150K**
   - Action: Start preservation protocol
   - Save critical context to disk

2. **Conversation Length > 4 Hours**
   - Action: Create checkpoint
   - Consider starting fresh session

3. **About to Read Large Codebase**
   - Action: Pre-emptive save
   - Use grep/search instead of reading full files

4. **Complex Phase (Phase 3) Starting**
   - Action: Create checkpoint before starting
   - Expect high token use

### Critical Warnings (Reactive)

**These mean action NOW**:

1. **"Context too long" warnings appear**
   - STOP immediately
   - Execute preservation protocol
   - Start new session

2. **Responses getting truncated**
   - Context limit reached
   - Save state immediately

3. **AI starts repeating itself**
   - Possible context confusion
   - Validate context vs reality
   - Create checkpoint

---

## 💾 Preservation Strategy

### What to Preserve (Priority Order)

**P0 - CRITICAL (Always Preserve)**:
```json
{
  "execution_id": "exec_...",
  "service": "doc-store",
  "current_phase": "Phase 3: TDD Implementation",
  "current_step": "3.2.1 Domain Layer",
  "progress_percent": 45,
  
  "completed_work": [
    "Phase 1: Audit complete",
    "Phase 2: Design complete",
    "Phase 3: Domain layer implemented (15 entities, 25 tests)"
  ],
  
  "key_decisions": [
    "Using PostgreSQL for persistence",
    "UUID for all entity IDs",
    "Timestamps in UTC ISO 8601"
  ],
  
  "patterns_identified": [
    "Repository pattern for data access",
    "Result<T, Error> for command handlers"
  ],
  
  "current_blockers": [],
  
  "next_steps": [
    "Implement Application layer",
    "Add command handlers",
    "Add query handlers"
  ]
}
```

**P1 - IMPORTANT (Preserve if Possible)**:
- Recent conversation summary (last 50 messages)
- Code snippets currently working on
- Test results from current phase
- Error messages encountered

**P2 - NICE TO HAVE (Summarize or Discard)**:
- Early conversation history
- Exploratory code reads
- Background context
- General discussions

### Where to Preserve

**Primary**: `.ai_execution/context.json` (always)
**Backup**: `.ai_execution/checkpoints/checkpoint_<timestamp>.json`
**History**: `.ai_execution/session_log.md` (append-only)
**Emergency**: `git commit` with detailed message

---

## 📝 Summarization Protocol

### When to Summarize

**Triggers**:
- Token count > 200K
- Before starting complex phase
- Every 4-6 hours of work
- Before reading large codebase
- When explicitly warned by system

### How to Summarize

#### Step 1: Update Context File

```bash
python3 scripts/refactoring/update_execution_context.py \
  --step "3.2.1" \
  --status "in_progress" \
  --notes "Domain layer 50% complete, 12 entities, 15 tests passing"
```

#### Step 2: Create Checkpoint

```bash
python3 scripts/refactoring/create_checkpoint.py \
  --name "phase3_domain_midpoint" \
  --notes "Mid-phase checkpoint before context refresh"
```

#### Step 3: Write Comprehensive Summary

Create `.ai_execution/summary_<timestamp>.md`:

```markdown
# Context Summary - Phase 3 Mid-Point

**Date**: 2025-10-09 14:30 UTC
**Service**: doc-store
**Phase**: Phase 3: TDD Implementation (45% complete)
**Current Step**: 3.2.1 Domain Layer

## What We've Done

### Phase 1 ✅
- Audited doc-store service
- Found 2,500 LOC, complexity avg 8
- Identified 15 dependencies
- Gap: 45% test coverage, no logging

### Phase 2 ✅
- Designed domain model: 15 entities, 5 value objects
- Created OpenAPI v2 spec (12 endpoints)
- Planned test strategy: 80% coverage target

### Phase 3 (In Progress) ⚙️
- ✅ Test infrastructure setup
- ✅ Domain layer: 12/15 entities implemented
  - Document, Metadata, Version, Tag, Author (done)
  - DocumentContent, SearchIndex, Audit (in progress)
- ✅ 15 unit tests passing
- ⚠️ Still need: 3 more entities, 10 more tests

## Key Decisions

1. **PostgreSQL for persistence** (better query support than NoSQL)
2. **UUID for all entity IDs** (consistency, no collisions)
3. **UTC timestamps** in ISO 8601 format
4. **Result<T, Error> pattern** for error handling

## Patterns

- Repository interfaces in Domain
- Immutable value objects
- Aggregate root for DocumentAggregate
- Dependency injection throughout

## Current Blockers

None

## Next Steps

1. Complete remaining 3 domain entities
2. Add 10 more domain tests (target: 25 total)
3. Implement Application layer (5 commands, 3 queries)
4. Add application tests

## DO NOT FORGET

- Tests MUST pass before moving to next step
- Coverage target: 80%+
- Log all core features (structured JSON)
- Update context every 30 minutes

## File State

**Created**:
- `services/doc-store/domain/entities/` (12 files)
- `services/doc-store/domain/value_objects/` (5 files)
- `tests/unit/domain/` (15 tests)

**In Progress**:
- `services/doc-store/domain/entities/document_content.py`
- `services/doc-store/domain/entities/search_index.py`
- `tests/unit/domain/test_document_content.py`

**Not Started**:
- `services/doc-store/application/`
- `services/doc-store/infrastructure/`
- `services/doc-store/presentation/`
```

#### Step 4: Commit to Git

```bash
git add .
git commit -m "wip(doc-store): Phase 3 checkpoint - Domain layer 45% complete

12/15 entities implemented, 15 tests passing.
Creating checkpoint before context refresh.

Current step: 3.2.1 Domain Layer
Next: Complete 3 remaining entities, then Application layer

This is a checkpoint commit to preserve state."
```

#### Step 5: Create New Session

**New chat/session starts here**

Load context:
```bash
python3 scripts/refactoring/recover_session.py --service doc-store
```

Read summary:
```bash
cat .ai_execution/summary_*.md
```

Continue work!

---

## 🔄 Continuation Protocol

### Starting Fresh Session After Summarization

**CRITICAL**: Follow this exactly to avoid context loss

#### Step 1: Initialize Recovery

```bash
cd /Users/mykalthomas/Documents/work/Hackathon
python3 scripts/refactoring/recover_session.py --service doc-store
```

**Output tells you**:
- Current phase and step
- Completed work
- Key decisions
- Next steps

#### Step 2: Read Summary

```bash
# Find latest summary
ls -lt .ai_execution/summary_*.md | head -1

# Read it
cat .ai_execution/summary_YYYYMMDD_HHMMSS.md
```

#### Step 3: Validate Context vs Reality

```bash
# Check what actually exists
ls -la services/doc-store/domain/entities/
ls -la tests/unit/domain/

# Run tests
cd services/doc-store
pytest -v

# Check git status
git status
git log -3 --oneline
```

#### Step 4: Reconcile Discrepancies

**If context says "12 entities" but you see 10**:
- Trust the filesystem (reality)
- Update context to match reality
- Investigate: Were 2 entities deleted? Not committed?

**If tests don't pass but context says they do**:
- Reality: Tests failing
- Re-run to understand failures
- Fix before continuing

#### Step 5: Read Phase Instructions

```bash
# Read the phase you're in
cat docs/refactoring/AI_AGENT_EXECUTION_GUIDE.md | grep -A 50 "Phase 3:"
```

#### Step 6: Continue Work

- Start from **current_step** in context
- Validate deliverables for that step exist
- Continue following phase instructions
- Update context regularly

---

## ✅ Validation After Continuation

### Reality Check Checklist

**After loading context, verify**:

- [ ] Service directory exists: `ls services/<service>/`
- [ ] Current phase files exist (check deliverables)
- [ ] Tests pass: `pytest`
- [ ] Git status clean or matches context: `git status`
- [ ] Context phase/step makes sense given file state
- [ ] No missing steps (check LIVING_PROGRESS_TRACKER.md)

### Discrepancy Resolution

**If context doesn't match reality**:

```python
# Priority: Trust Reality > Trust Context

if filesystem_shows_X and context_says_Y:
    # Trust filesystem
    update_context(X)
    
if tests_fail and context_says_pass:
    # Trust test results
    update_context("tests failing")
    
if git_log_shows_phase2 and context_says_phase3:
    # Trust git (committed work)
    update_context("phase 2")
```

---

## 🚨 Emergency Procedures

### Context Overflow Mid-Step

**Symptoms**: Truncated responses, "too long" errors

**IMMEDIATE ACTION**:

```bash
# 1. Save current state (even if incomplete)
python3 scripts/refactoring/update_execution_context.py \
  --step "CURRENT_STEP" \
  --status "interrupted_context_overflow" \
  --notes "Context overflow mid-step. Checkpoint created."

# 2. Create checkpoint
python3 scripts/refactoring/create_checkpoint.py \
  --name "emergency_context_overflow" \
  --notes "Emergency checkpoint due to context overflow"

# 3. If mid-edit, commit as WIP
git add .
git commit -m "wip: Emergency checkpoint - context overflow"

# 4. Write emergency summary
echo "EMERGENCY CONTEXT OVERFLOW - see .ai_execution/emergency_summary.md" > .ai_execution/EMERGENCY

# 5. Start new session
# New session: Load context and continue
```

### Forced Summarization

**When system forces summarization**:

1. **Accept it** - Don't fight it
2. **Preserve state immediately** (context, checkpoint, commit)
3. **Write detailed summary** (what's done, what's next, critical info)
4. **Start new session**
5. **Validate continuity** (reality check)

---

## 📊 Token Budget Guidelines

### Conservative Approach (Recommended)

```
Phase Budget (tokens):
- Phase 1: 30K (audit, read code)
- Phase 2: 40K (design, plan)
- Phase 3: 80K (implement, TDD) ⚠️ Largest
- Phase 4: 30K (integration tests)
- Phase 5: 40K (documentation)
- Phase 6: 20K (validation)
─────────────────────────────
Total: ~240K tokens per service

Reserve: 60K for chat history, context

Max Safe: ~300K tokens
```

### Token Saving Techniques

**Instead of reading full files**:
```bash
# DON'T: Read entire 5000-line file
read_file("services/doc-store/main.py")  # 10K tokens

# DO: Search specific content
grep("def get_document", "services/doc-store/")  # 100 tokens
```

**Use summaries**:
```bash
# DON'T: Re-read entire plan
read_file("docs/refactoring/MASTER_REFACTORING_PLAN.md")  # 15K tokens

# DO: Reference specific phase
grep("Phase 3:", "docs/refactoring/AI_AGENT_EXECUTION_GUIDE.md")  # 500 tokens
```

**Checkpoint frequently**:
- Every 2 hours → Create checkpoint
- Before large operations → Create checkpoint
- After completing step → Update context

---

## 🎯 Best Practices

### Proactive Management

1. **Monitor token use** (check regularly)
2. **Create checkpoints frequently** (every 2 hours minimum)
3. **Update context religiously** (every 30 minutes)
4. **Commit often** (after each meaningful unit)
5. **Use grep/search over read** (save tokens)

### Reactive Management

1. **Watch for warnings** (truncation, slowness)
2. **Save state immediately** (don't wait)
3. **Create detailed summary** (aid continuation)
4. **Start fresh session** (clean slate)
5. **Validate thoroughly** (reality check)

### Critical Rule

**NEVER proceed with unclear context**

If context is fuzzy:
1. Stop
2. Validate reality (filesystem, git, tests)
3. Update context to match reality
4. Then continue

---

**Document Control**  
**Version**: 1.0.0  
**Last Updated**: October 9, 2025  
**For AI Agents**: Use this to handle token limits gracefully  
**Owner**: Hackathon Team

