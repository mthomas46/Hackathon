**Date:** October 28, 2025  
**Status:** Documentation Organization Plan  
**Scope:** All 3 services (ecosystem-mcp, dashboard, embedding)  

# Documentation Organization & Cleanup Plan

## 🎯 Objectives

1. **Audit & Categorize** - Review all .md files and categorize by type
2. **Organize Structure** - Create proper directory hierarchy
3. **Consolidate** - Merge duplicate/outdated docs
4. **Comprehensive Docs** - Write master documentation for each service
5. **Add Metadata** - Tags, cross-references, LLM navigation aids

---

## 📊 Current State Analysis

### Files Found:
- **ecosystem-mcp**: ~150+ .md files
- **ecosystem-mcp-dashboard**: ~26 .md files  
- **ecosystem-mcp-embedding**: ~1 .md file (README)

### Issues Identified:
1. ❌ No consistent directory structure
2. ❌ Many files in root directories
3. ❌ Duplicate/overlapping content
4. ❌ Outdated implementation docs mixed with current
5. ❌ No clear navigation or indexing
6. ❌ Missing cross-references

---

## 🗂️ Proposed Directory Structure

### For Each Service:

```
services/<service-name>/
├── README.md                    # Main entry point
├── docs/
│   ├── INDEX.md                 # Master index with tags
│   ├── architecture/
│   │   ├── OVERVIEW.md
│   │   ├── COMPONENTS.md
│   │   └── DESIGN_DECISIONS.md
│   ├── api/
│   │   ├── ENDPOINTS.md
│   │   ├── MODELS.md
│   │   └── EXAMPLES.md
│   ├── guides/
│   │   ├── QUICK_START.md
│   │   ├── DEPLOYMENT.md
│   │   ├── CONFIGURATION.md
│   │   └── TROUBLESHOOTING.md
│   ├── features/
│   │   ├── RAG.md
│   │   ├── CACHING.md
│   │   ├── MONITORING.md
│   │   └── etc.
│   └── development/
│       ├── CONTRIBUTING.md
│       ├── TESTING.md
│       └── DEBUGGING.md
├── planning/
│   ├── implementation-plans/
│   ├── architecture-decisions/
│   └── feature-specs/
├── history/
│   ├── milestones/
│   ├── changes/
│   └── retrospectives/
└── archive/
    └── outdated/
```

---

## 📋 File Categories

### 1. **Core Documentation** (docs/)
- Service overviews
- Architecture documents
- API specifications
- User guides
- Feature documentation

### 2. **Planning Documents** (planning/)
- Implementation plans
- Feature specs
- Architecture decisions
- Phase documents

### 3. **Historical Records** (history/)
- Milestone markers
- Change logs
- Session summaries
- Retrospectives

### 4. **Generated Documentation** (docs/generated/)
- Auto-generated API docs
- Generated guides
- Reports

### 5. **Testing Documentation** (tests/)
- Test guides
- Test results
- Validation reports

### 6. **Archive** (archive/)
- Outdated documents
- Superseded implementations
- Historical artifacts

---

## 🔄 Organization Process

### Phase 1: Audit & Categorize (30 min)
1. Read each .md file header/content
2. Categorize by type
3. Identify duplicates
4. Mark outdated content

### Phase 2: Create Structure (15 min)
1. Create directory hierarchy
2. Create INDEX files
3. Set up templates

### Phase 3: Move & Organize (45 min)
1. Move files to appropriate dirs
2. Rename for consistency
3. Update internal links
4. Remove duplicates

### Phase 4: Write Comprehensive Docs (2 hours)
1. **ecosystem-mcp**: Complete service documentation
2. **ecosystem-mcp-dashboard**: Dashboard documentation
3. **ecosystem-mcp-embedding**: Embedding service documentation

### Phase 5: Add Metadata (30 min)
1. Add YAML frontmatter to all docs
2. Add tags and categories
3. Create cross-reference links
4. Build navigation index

---

## 🏷️ Metadata Schema

Each document will include:

```yaml
---
title: "Document Title"
service: "ecosystem-mcp" | "dashboard" | "embedding"
category: "architecture" | "api" | "guide" | "feature" | "planning"
tags: ["rag", "caching", "performance", etc.]
related: ["OTHER_DOC.md", "ANOTHER_DOC.md"]
status: "current" | "outdated" | "archived"
last_updated: "2025-10-28"
audience: "developer" | "user" | "operator"
difficulty: "beginner" | "intermediate" | "advanced"
---
```

---

## 🔗 Cross-Reference Strategy

### Linking System:
- **Internal Links**: `[Related Doc](../category/DOCUMENT.md)`
- **Cross-Service**: `[Dashboard Docs](../../ecosystem-mcp-dashboard/docs/INDEX.md)`
- **Tags**: `#rag #caching #performance`
- **See Also**: List of related documents at end

### Navigation Aids:
- **Breadcrumbs**: Show document location
- **Quick Links**: Jump to related sections
- **Index**: Searchable master index

---

## 📝 Documentation Templates

### Service Overview Template:
```markdown
# Service Name

## Overview
Brief description

## Architecture
High-level architecture

## Key Features
- Feature 1
- Feature 2

## Quick Start
Getting started guide

## API Reference
Link to API docs

## Configuration
Link to config guide

## Related Documents
- [Architecture](docs/architecture/OVERVIEW.md)
- [API](docs/api/ENDPOINTS.md)
```

---

## ✅ Success Criteria

1. ✅ All .md files categorized and organized
2. ✅ Clear directory structure in place
3. ✅ No files in root directories (except README)
4. ✅ Comprehensive service documentation written
5. ✅ All docs have metadata/tags
6. ✅ Cross-references functional
7. ✅ Master index created
8. ✅ LLM can navigate efficiently

---

## 🚀 Execution Plan

1. Start with ecosystem-mcp (largest)
2. Then ecosystem-mcp-dashboard
3. Finally ecosystem-mcp-embedding
4. Create unified index across all services

**Estimated Time:** 4-5 hours  
**Priority:** HIGH (improves maintainability and LLM navigation)

