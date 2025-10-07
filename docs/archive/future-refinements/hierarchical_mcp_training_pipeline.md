---
llm_metadata:
  document_type: planning
  content_focus: historical
  platform:
    primary: mcp
    secondary: []
  status: archived
  created_date: '2024-09-01'
  archived_date: '2025-10-07'
  topics:
  - microservices
  - domain_driven_design
  - event_sourcing
  - fastapi
  - python
  - postgresql
  - rag
  - embeddings
  concepts: []
  technologies: []
  services_mentioned: []
  semantic_summary: Planning document about historical aspects of the mcp platform
  archive_reason: consolidated
  historical_value: medium
  reference_value: medium
semantic_embedding:
  model: text-embedding-ada-002
  embedding_date: '2025-10-07'
  embedding_checksum: pending
rag_metadata:
  chunk_strategy: semantic
  optimal_chunk_size: 512
  retrieval_priority: medium
---

# 🔄 Hierarchical MCP Training Pipeline
## Automatic Knowledge Extraction from GitHub, Jira, Confluence & FullStory

**Document Type:** Architecture Design & Implementation Guide  
**Created:** 2025-10-06  
**Status:** Design Complete, Ready for Implementation  
**Complexity:** Advanced (Multi-source data pipeline with intelligent routing)

---

## 📚 Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Data Source Mapping](#2-data-source-mapping)
3. [MCP Training Pipeline Architecture](#3-mcp-training-pipeline-architecture)
4. [Knowledge Extraction by Source](#4-knowledge-extraction-by-source)
5. [Intelligent Routing Logic](#5-intelligent-routing-logic)
6. [Implementation Guide](#6-implementation-guide)
7. [Integration with Existing Services](#7-integration-with-existing-services)
8. [Example Workflows](#8-example-workflows)
9. [Privacy & Security](#9-privacy--security)
10. [Roadmap](#10-roadmap)

---

## 1. Executive Summary

### 1.1 The Vision

**Automatically transform your company's data into a self-improving knowledge hierarchy:**

```
GitHub, Jira, Confluence, FullStory
         ↓
   MCP Training Pipeline (Wrapper Service)
         ↓ (intelligent routing)
         ├─> Ecosystem MCP (Tier 4): Individual patterns
         ├─> Team MCP (Tier 3): Team patterns
         ├─> Company MCP (Tier 2): Enterprise patterns
         └─> Project MCP (Tier 1): Project patterns
```

**Key Capabilities:**
- ✅ **Automatic ingestion** from 4 data sources
- ✅ **Intelligent classification** (which MCP tier to train)
- ✅ **Knowledge extraction** (patterns, decisions, outcomes)
- ✅ **Continuous training** (24/7 background processing)
- ✅ **Privacy-aware** (respects data sensitivity)

---

### 1.2 Data Source → MCP Tier Mapping

| Data Source | Primary Tier | Secondary Tier | Knowledge Type |
|-------------|-------------|----------------|----------------|
| **GitHub** (your repos) | Ecosystem (4) | Team (3) | Code patterns, commits, PRs |
| **GitHub** (team repos) | Team (3) | Company (2) | Team practices, code reviews |
| **Jira** (your tickets) | Ecosystem (4) | Project (1) | Work patterns, velocity |
| **Jira** (team tickets) | Team (3) | Company (2) | Team processes, estimates |
| **Confluence** (your docs) | Ecosystem (4) | Team (3) | Your documentation style |
| **Confluence** (team docs) | Team (3) | Company (2) | Team knowledge, ADRs |
| **Confluence** (company docs) | Company (2) | Project (1) | Policies, standards |
| **FullStory** (user behavior) | Project (1) | Company (2) | Usage patterns, pain points |

---

## 2. Data Source Mapping

### 2.1 GitHub: Code & Collaboration Patterns

**What to Extract:**

```python
GitHub → 4 Knowledge Types:

1. CODE PATTERNS (Ecosystem MCP)
   • How YOU write code
   • Your preferred libraries, patterns
   • Your error handling style
   • Your testing approach
   
   Example:
   "User mykal-thomas prefers FastAPI + DDD pattern,
    uses Pydantic for validation, pytest for testing,
    async/await for I/O operations"

2. TEAM PRACTICES (Team MCP)
   • Code review comments (what team values)
   • PR approval patterns (who reviews what)
   • Branch naming conventions
   • Merge strategies
   
   Example:
   "Team requires 2 approvals, enforces type hints,
    prefers small PRs (<500 lines), uses squash merges"

3. TECHNICAL DECISIONS (Company MCP)
   • Tech stack choices (PostgreSQL vs MongoDB)
   • Architecture patterns (microservices, event-driven)
   • Security practices (OAuth2, JWT)
   • Performance standards (SLAs, latency targets)
   
   Example:
   "Company standardizes on Python 3.11+, FastAPI,
    PostgreSQL for CRUD, MongoDB for flexible schemas"

4. PROJECT SUCCESS PATTERNS (Project MCP)
   • Which projects succeeded/failed
   • Why (extract from commit messages, PR discussions)
   • Timeline accuracy (planned vs actual)
   
   Example:
   "Projects using microservices completed 20% faster,
    monolithic rewrites took 2.3× longer than estimated"
```

---

### 2.2 Jira: Work Patterns & Process

**What to Extract:**

```python
Jira → 4 Knowledge Types:

1. INDIVIDUAL WORK PATTERNS (Ecosystem MCP)
   • Your velocity (story points per sprint)
   • Your estimation accuracy (estimated vs actual)
   • Types of work you excel at (frontend, backend, DevOps)
   • Your typical blockers
   
   Example:
   "Mykal averages 21 story points/sprint,
    underestimates backend tasks by 30%,
    excels at API development,
    blocked by design reviews (avg 2 days)"

2. TEAM DYNAMICS (Team MCP)
   • Sprint planning accuracy
   • Burndown patterns
   • Collaboration patterns (who helps whom)
   • Bottlenecks
   
   Example:
   "Team completes 85% of committed work,
    Alice frequently unblocks others (23 times),
    QA is bottleneck (avg 3-day wait)"

3. PROCESS EFFECTIVENESS (Company MCP)
   • Sprint lengths that work (2-week vs 3-week)
   • Estimation techniques (Planning Poker vs T-shirt)
   • Release frequency (bi-weekly vs monthly)
   • Bug rates by team
   
   Example:
   "2-week sprints have 15% higher completion rate,
    teams using Planning Poker estimate 25% more accurately,
    bi-weekly releases reduce bug backlog"

4. PROJECT RISK INDICATORS (Project MCP)
   • Early warning signs (scope creep, velocity drops)
   • Dependency delays (blocked tickets)
   • Quality trends (bugs per sprint)
   
   Example:
   "Projects with >30% scope change miss deadlines,
    velocity drop >20% signals team issues,
    bugs/sprint >15 indicates quality problems"
```

---

### 2.3 Confluence: Knowledge & Decisions

**What to Extract:**

```python
Confluence → 4 Knowledge Types:

1. DOCUMENTATION STYLE (Ecosystem MCP)
   • How YOU document
   • Your preferred formats (diagrams, code examples)
   • Your documentation frequency
   
   Example:
   "Mykal creates detailed API docs with code examples,
    includes architecture diagrams,
    updates docs within 1 day of code changes"

2. TEAM KNOWLEDGE (Team MCP)
   • Architecture Decision Records (ADRs)
   • Team runbooks, playbooks
   • Onboarding docs
   • Meeting notes, retrospectives
   
   Example:
   "Team decided to use PostgreSQL for user-store (ADR-023),
    standard onboarding takes 2 weeks,
    retrospectives identify 3 process improvements/sprint"

3. COMPANY STANDARDS (Company MCP)
   • Engineering policies (code review, testing)
   • Security policies (authentication, encryption)
   • Architecture patterns (approved vs discouraged)
   • Compliance requirements (GDPR, SOC2)
   
   Example:
   "Company requires 80% test coverage,
    mandates OAuth2 + JWT for auth,
    all services must use structured logging,
    PII must be encrypted at rest"

4. PROJECT CONTEXT (Project MCP)
   • Project requirements docs
   • Design docs, RFCs
   • Project retrospectives (lessons learned)
   • Success criteria
   
   Example:
   "Projects with detailed design docs (>10 pages)
    have 40% fewer scope changes,
    retrospectives identify 'insufficient testing'
    in 60% of delayed projects"
```

---

### 2.4 FullStory: User Behavior & Product Insights

**What to Extract:**

```python
FullStory → 3 Knowledge Types:

1. USAGE PATTERNS (Project MCP)
   • Which features users actually use
   • User journeys (happy paths, drop-offs)
   • Performance issues (slow pages, errors)
   • Device/browser distribution
   
   Example:
   "75% of users access via mobile,
    'Export' feature used by <5% (consider deprecating),
    checkout page has 23% drop-off (investigate),
    avg session duration: 4.2 minutes"

2. PAIN POINTS (Project MCP)
   • Rage clicks (frustrated users)
   • Error messages users encounter
   • Abandoned workflows
   • Support ticket correlation
   
   Example:
   "Login page: 45 rage clicks/day (password reset),
    'Upload Document' fails 12% of time (timeout),
    users abandon cart at 'Payment Method' (18%),
    78% of support tickets relate to password reset"

3. PRODUCT INSIGHTS (Company MCP)
   • Feature adoption rates
   • A/B test results
   • User segments (power users vs casual)
   • Retention metrics
   
   Example:
   "New dashboard adopted by 67% in 2 weeks,
    A/B test: blue CTA button +15% conversions,
    power users (10%) generate 60% of revenue,
    30-day retention: 45% (industry avg: 38%)"
```

---

## 3. MCP Training Pipeline Architecture

### 3.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  DATA SOURCES (External)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   GitHub API    Jira API    Confluence API    FullStory API     │
│      ↓              ↓              ↓                ↓           │
└──────┬──────────────┬──────────────┬────────────────┬───────────┘
       │              │              │                │
       ▼              ▼              ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│              LAYER 1: INGESTION (source-agent)                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  • Fetch data from APIs                                         │
│  • Rate limiting, pagination                                    │
│  • Store raw data (doc-store)                                   │
│  • Emit events: "new_github_pr", "jira_ticket_updated"         │
│                                                                 │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│         LAYER 2: KNOWLEDGE EXTRACTION (NEW SERVICE)             │
│                 mcp-training-pipeline                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  GitHub Extractor                                        │   │
│  │  • Extract code patterns (AST analysis)                  │   │
│  │  • Extract PR review patterns                            │   │
│  │  • Extract commit messages (sentiment, topics)           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Jira Extractor                                          │   │
│  │  • Extract velocity, estimates                           │   │
│  │  • Extract collaboration patterns                        │   │
│  │  • Extract blocker analysis                              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Confluence Extractor                                    │   │
│  │  • Extract ADRs (architecture decisions)                 │   │
│  │  • Extract documentation quality                         │   │
│  │  • Extract team knowledge                                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  FullStory Extractor                                     │   │
│  │  • Extract usage patterns                                │   │
│  │  • Extract pain points                                   │   │
│  │  • Extract feature adoption                              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│         LAYER 3: INTELLIGENT ROUTING (Classification)           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  For each extracted knowledge item:                             │
│  • Classify scope (individual, team, company, project)          │
│  • Classify type (pattern, decision, outcome, metric)           │
│  • Classify sensitivity (public, internal, confidential)        │
│  • Route to appropriate MCP tier(s)                             │
│                                                                 │
│  Example:                                                       │
│  Knowledge: "Alice uses FastAPI + DDD pattern"                  │
│  → Scope: Individual → Route to Ecosystem MCP (Tier 4, Alice)  │
│                                                                 │
│  Knowledge: "Team requires 2 PR approvals"                      │
│  → Scope: Team → Route to Team MCP (Tier 3)                    │
│                                                                 │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│              LAYER 4: MCP TRAINING (Knowledge Graphs)           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐                    │
│  │ Ecosystem MCP    │  │ Ecosystem MCP    │  (Individual)      │
│  │ (Alice)          │  │ (Bob)            │                    │
│  │ Neo4j + ChromaDB │  │ Neo4j + ChromaDB │                    │
│  └──────────────────┘  └──────────────────┘                    │
│            ↓                     ↓                              │
│            └─────────┬───────────┘                              │
│                      ▼                                          │
│          ┌──────────────────────┐                               │
│          │   Team MCP           │  (Aggregated)                 │
│          │   Neo4j + ChromaDB   │                               │
│          └──────────────────────┘                               │
│                      ↓                                          │
│          ┌──────────────────────┐                               │
│          │   Company MCP        │  (Enterprise)                 │
│          │   Neo4j + ChromaDB   │                               │
│          └──────────────────────┘                               │
│                      ↓                                          │
│          ┌──────────────────────┐                               │
│          │   Project MCP        │  (Project-specific)           │
│          │   Neo4j + ChromaDB   │                               │
│          └──────────────────────┘                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### 3.2 Service: `mcp-training-pipeline`

**New Microservice:**

```
services/mcp-training-pipeline/
├── main.py                     # FastAPI app
├── domain/
│   ├── extractors/
│   │   ├── github_extractor.py       # Extract from GitHub
│   │   ├── jira_extractor.py         # Extract from Jira
│   │   ├── confluence_extractor.py   # Extract from Confluence
│   │   └── fullstory_extractor.py    # Extract from FullStory
│   ├── classifiers/
│   │   ├── scope_classifier.py       # Individual/Team/Company/Project
│   │   ├── type_classifier.py        # Pattern/Decision/Outcome/Metric
│   │   └── sensitivity_classifier.py # Public/Internal/Confidential
│   └── routers/
│       └── mcp_router.py             # Route to appropriate MCP tier
├── infrastructure/
│   ├── mcp_clients/
│   │   ├── ecosystem_mcp_client.py   # Connect to Tier 4
│   │   ├── team_mcp_client.py        # Connect to Tier 3
│   │   ├── company_mcp_client.py     # Connect to Tier 2
│   │   └── project_mcp_client.py     # Connect to Tier 1
│   └── event_listeners/
│       └── source_event_listener.py  # Listen to source-agent events
└── requirements.txt
```

---

## 4. Knowledge Extraction by Source

### 4.1 GitHub Extractor

**Implementation:**

```python
# services/mcp-training-pipeline/domain/extractors/github_extractor.py

from typing import List, Dict, Any
import ast
from datetime import datetime

class GitHubKnowledgeExtractor:
    """Extract knowledge from GitHub data"""
    
    async def extract_from_pr(self, pr: Dict[str, Any]) -> List[Dict]:
        """Extract knowledge from a Pull Request"""
        
        knowledge_items = []
        
        # 1. EXTRACT CODE PATTERNS (for Ecosystem MCP)
        if pr.get('files'):
            code_patterns = await self._extract_code_patterns(pr['files'])
            for pattern in code_patterns:
                knowledge_items.append({
                    'type': 'code_pattern',
                    'scope': 'individual',  # This author's pattern
                    'author': pr['author']['username'],
                    'pattern': pattern,
                    'confidence': pattern['confidence'],
                    'source': f"github_pr_{pr['number']}",
                    'timestamp': pr['created_at']
                })
        
        # 2. EXTRACT REVIEW PATTERNS (for Team MCP)
        if pr.get('reviews'):
            review_patterns = await self._extract_review_patterns(pr['reviews'])
            for pattern in review_patterns:
                knowledge_items.append({
                    'type': 'review_pattern',
                    'scope': 'team',  # Team's review standards
                    'team': pr['repository']['team'],
                    'pattern': pattern,
                    'confidence': pattern['confidence'],
                    'source': f"github_pr_{pr['number']}",
                    'timestamp': pr['created_at']
                })
        
        # 3. EXTRACT TECHNICAL DECISIONS (for Company MCP)
        if self._is_architecture_pr(pr):
            decisions = await self._extract_technical_decisions(pr)
            for decision in decisions:
                knowledge_items.append({
                    'type': 'technical_decision',
                    'scope': 'company',  # Company-wide impact
                    'decision': decision,
                    'rationale': decision['rationale'],
                    'confidence': decision['confidence'],
                    'source': f"github_pr_{pr['number']}",
                    'timestamp': pr['created_at']
                })
        
        # 4. EXTRACT SUCCESS PATTERNS (for Project MCP)
        if pr.get('merged') and pr.get('project'):
            success_pattern = await self._extract_success_pattern(pr)
            knowledge_items.append({
                'type': 'success_pattern',
                'scope': 'project',
                'project': pr['project'],
                'pattern': success_pattern,
                'outcome': 'success' if not pr.get('reverted') else 'failure',
                'confidence': success_pattern['confidence'],
                'source': f"github_pr_{pr['number']}",
                'timestamp': pr['merged_at']
            })
        
        return knowledge_items
    
    async def _extract_code_patterns(self, files: List[Dict]) -> List[Dict]:
        """Extract coding patterns from PR files"""
        
        patterns = []
        
        for file in files:
            if file['filename'].endswith('.py'):
                # Parse Python AST
                try:
                    tree = ast.parse(file['content'])
                    
                    # Pattern: Uses async/await
                    async_functions = [
                        node for node in ast.walk(tree)
                        if isinstance(node, ast.AsyncFunctionDef)
                    ]
                    if async_functions:
                        patterns.append({
                            'name': 'uses_async_await',
                            'description': 'Author prefers async/await for I/O operations',
                            'evidence': f"{len(async_functions)} async functions",
                            'confidence': 0.8
                        })
                    
                    # Pattern: Uses type hints
                    functions = [
                        node for node in ast.walk(tree)
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    ]
                    type_hinted = [
                        f for f in functions
                        if f.returns or any(arg.annotation for arg in f.args.args)
                    ]
                    if len(type_hinted) / len(functions) > 0.8:
                        patterns.append({
                            'name': 'uses_type_hints',
                            'description': 'Author consistently uses type hints',
                            'evidence': f"{len(type_hinted)}/{len(functions)} functions",
                            'confidence': 0.9
                        })
                    
                    # Pattern: Error handling style
                    try_blocks = [
                        node for node in ast.walk(tree)
                        if isinstance(node, ast.Try)
                    ]
                    if try_blocks:
                        # Check if using specific exceptions vs bare except
                        specific_excepts = sum(
                            1 for tb in try_blocks
                            for handler in tb.handlers
                            if handler.type  # Not bare except
                        )
                        if specific_excepts / len(try_blocks) > 0.8:
                            patterns.append({
                                'name': 'specific_exception_handling',
                                'description': 'Author uses specific exceptions (not bare except)',
                                'evidence': f"{specific_excepts}/{len(try_blocks)} specific",
                                'confidence': 0.85
                            })
                
                except SyntaxError:
                    continue
        
        return patterns
    
    async def _extract_review_patterns(self, reviews: List[Dict]) -> List[Dict]:
        """Extract what team values in code reviews"""
        
        patterns = []
        
        # Aggregate review comments
        all_comments = []
        for review in reviews:
            all_comments.extend(review.get('comments', []))
        
        if not all_comments:
            return patterns
        
        # Pattern: Team cares about testing
        test_comments = [
            c for c in all_comments
            if any(word in c['body'].lower() for word in ['test', 'coverage', 'unittest'])
        ]
        if len(test_comments) / len(all_comments) > 0.2:
            patterns.append({
                'name': 'values_testing',
                'description': 'Team frequently comments on testing',
                'evidence': f"{len(test_comments)}/{len(all_comments)} comments mention testing",
                'confidence': 0.85
            })
        
        # Pattern: Team cares about performance
        perf_comments = [
            c for c in all_comments
            if any(word in c['body'].lower() for word in ['performance', 'slow', 'optimization', 'n+1'])
        ]
        if len(perf_comments) / len(all_comments) > 0.15:
            patterns.append({
                'name': 'values_performance',
                'description': 'Team frequently comments on performance',
                'evidence': f"{len(perf_comments)}/{len(all_comments)} comments mention performance",
                'confidence': 0.8
            })
        
        # Pattern: Approval threshold
        approvals_needed = self._infer_approval_threshold(reviews)
        if approvals_needed:
            patterns.append({
                'name': 'approval_threshold',
                'description': f'Team requires {approvals_needed} approvals',
                'evidence': f"Inferred from {len(reviews)} PRs",
                'confidence': 0.9
            })
        
        return patterns
    
    def _is_architecture_pr(self, pr: Dict) -> bool:
        """Check if PR contains architecture decisions"""
        
        # Check PR title/description
        keywords = ['architecture', 'design', 'rfc', 'adr', 'decision', 'migrate', 'refactor']
        title_desc = (pr.get('title', '') + ' ' + pr.get('body', '')).lower()
        
        if any(keyword in title_desc for keyword in keywords):
            return True
        
        # Check if modifies architecture docs
        if pr.get('files'):
            arch_files = [
                f for f in pr['files']
                if any(path in f['filename'].lower() for path in ['architecture', 'design', 'adr'])
            ]
            if arch_files:
                return True
        
        return False
    
    async def _extract_technical_decisions(self, pr: Dict) -> List[Dict]:
        """Extract technical decisions from architecture PRs"""
        
        decisions = []
        
        # Parse PR description for decision
        body = pr.get('body', '')
        
        # Look for structured ADR format
        if 'decision' in body.lower():
            decision_text = self._extract_section(body, 'decision')
            rationale_text = self._extract_section(body, 'rationale')
            
            decisions.append({
                'decision': decision_text,
                'rationale': rationale_text,
                'alternatives_considered': self._extract_section(body, 'alternatives'),
                'consequences': self._extract_section(body, 'consequences'),
                'confidence': 0.9 if rationale_text else 0.6
            })
        
        # Look for migration decisions
        if 'migrate' in body.lower() or 'migration' in body.lower():
            decisions.append({
                'decision': f"Migrate from X to Y",
                'rationale': self._extract_migration_rationale(body),
                'confidence': 0.75
            })
        
        return decisions
    
    async def _extract_success_pattern(self, pr: Dict) -> Dict:
        """Extract what made this PR successful"""
        
        pattern = {
            'pr_size': self._calculate_pr_size(pr),
            'time_to_merge': self._calculate_time_to_merge(pr),
            'review_rounds': len(pr.get('reviews', [])),
            'had_tests': self._check_has_tests(pr),
            'had_docs': self._check_has_docs(pr),
            'complexity': self._estimate_complexity(pr),
            'confidence': 0.8
        }
        
        return pattern
    
    def _calculate_pr_size(self, pr: Dict) -> str:
        """Calculate PR size (small/medium/large)"""
        lines_changed = pr.get('additions', 0) + pr.get('deletions', 0)
        
        if lines_changed < 200:
            return 'small'
        elif lines_changed < 500:
            return 'medium'
        else:
            return 'large'
```

---

### 4.2 Jira Extractor

**Implementation:**

```python
# services/mcp-training-pipeline/domain/extractors/jira_extractor.py

from typing import List, Dict, Any
from datetime import datetime, timedelta

class JiraKnowledgeExtractor:
    """Extract knowledge from Jira data"""
    
    async def extract_from_ticket(self, ticket: Dict[str, Any]) -> List[Dict]:
        """Extract knowledge from a Jira ticket"""
        
        knowledge_items = []
        
        # 1. EXTRACT INDIVIDUAL WORK PATTERNS (for Ecosystem MCP)
        assignee = ticket.get('assignee')
        if assignee:
            work_pattern = await self._extract_work_pattern(ticket, assignee)
            knowledge_items.append({
                'type': 'work_pattern',
                'scope': 'individual',
                'user': assignee['username'],
                'pattern': work_pattern,
                'confidence': work_pattern['confidence'],
                'source': f"jira_{ticket['key']}",
                'timestamp': ticket['updated']
            })
        
        # 2. EXTRACT TEAM DYNAMICS (for Team MCP)
        if ticket.get('sprint'):
            team_dynamic = await self._extract_team_dynamic(ticket)
            knowledge_items.append({
                'type': 'team_dynamic',
                'scope': 'team',
                'team': ticket.get('team', 'unknown'),
                'dynamic': team_dynamic,
                'confidence': team_dynamic['confidence'],
                'source': f"jira_{ticket['key']}",
                'timestamp': ticket['updated']
            })
        
        # 3. EXTRACT PROCESS EFFECTIVENESS (for Company MCP)
        if ticket.get('resolution'):
            process_metric = await self._extract_process_metric(ticket)
            knowledge_items.append({
                'type': 'process_metric',
                'scope': 'company',
                'metric': process_metric,
                'confidence': 0.9,
                'source': f"jira_{ticket['key']}",
                'timestamp': ticket['updated']
            })
        
        # 4. EXTRACT PROJECT RISK INDICATORS (for Project MCP)
        if ticket.get('project'):
            risk_indicator = await self._extract_risk_indicator(ticket)
            if risk_indicator:
                knowledge_items.append({
                    'type': 'risk_indicator',
                    'scope': 'project',
                    'project': ticket['project'],
                    'indicator': risk_indicator,
                    'severity': risk_indicator['severity'],
                    'confidence': risk_indicator['confidence'],
                    'source': f"jira_{ticket['key']}",
                    'timestamp': ticket['updated']
                })
        
        return knowledge_items
    
    async def _extract_work_pattern(self, ticket: Dict, assignee: Dict) -> Dict:
        """Extract individual work patterns"""
        
        # Calculate estimation accuracy
        estimated = ticket.get('timeestimate')  # seconds
        actual = ticket.get('timespent')  # seconds
        
        accuracy = None
        if estimated and actual:
            accuracy = actual / estimated
        
        # Identify work type
        work_type = self._categorize_work_type(ticket)
        
        # Check for blockers
        blockers = ticket.get('blocker_links', [])
        
        pattern = {
            'work_type': work_type,
            'estimation_accuracy': accuracy,
            'had_blockers': len(blockers) > 0,
            'blocker_types': [b['type'] for b in blockers],
            'story_points': ticket.get('storypoints'),
            'time_in_status': ticket.get('time_in_status', {}),
            'confidence': 0.85 if estimated and actual else 0.6
        }
        
        return pattern
    
    async def _extract_team_dynamic(self, ticket: Dict) -> Dict:
        """Extract team collaboration patterns"""
        
        # Who helped (comments from other team members)
        comments = ticket.get('comments', [])
        helpers = set()
        for comment in comments:
            if comment['author']['username'] != ticket['assignee']['username']:
                helpers.add(comment['author']['username'])
        
        # Sprint commitment
        sprint = ticket.get('sprint', {})
        committed_at_start = ticket.get('committed_at_sprint_start', False)
        
        dynamic = {
            'helpers': list(helpers),
            'help_received': len(helpers) > 0,
            'committed_at_sprint_start': committed_at_start,
            'sprint_name': sprint.get('name'),
            'completed_in_sprint': ticket.get('status') == 'Done',
            'confidence': 0.8
        }
        
        return dynamic
    
    async def _extract_process_metric(self, ticket: Dict) -> Dict:
        """Extract process effectiveness metrics"""
        
        # Calculate cycle time (created → resolved)
        created = datetime.fromisoformat(ticket['created'])
        resolved = datetime.fromisoformat(ticket['resolutiondate'])
        cycle_time_days = (resolved - created).days
        
        # Sprint accuracy
        estimated_sprint = ticket.get('estimated_sprint')
        actual_sprint = ticket.get('completed_sprint')
        sprint_accurate = estimated_sprint == actual_sprint if both else None
        
        metric = {
            'cycle_time_days': cycle_time_days,
            'sprint_estimate_accurate': sprint_accurate,
            'rework_count': len([c for c in ticket.get('changelog', []) if c['field'] == 'status' and c['toString'] == 'In Progress']),
            'had_bugs': len(ticket.get('linked_bugs', [])) > 0,
            'bug_count': len(ticket.get('linked_bugs', [])),
        }
        
        return metric
    
    async def _extract_risk_indicator(self, ticket: Dict) -> Dict:
        """Extract project risk indicators"""
        
        risks = []
        
        # Risk: Story points increased (scope creep)
        changelog = ticket.get('changelog', [])
        storypoint_changes = [
            c for c in changelog
            if c['field'] == 'Story Points'
        ]
        if storypoint_changes:
            initial = int(storypoint_changes[0]['fromString'] or 0)
            final = int(storypoint_changes[-1]['toString'] or 0)
            if final > initial * 1.3:  # 30% increase
                risks.append({
                    'type': 'scope_creep',
                    'severity': 'medium',
                    'description': f"Story points increased {initial} → {final}",
                    'confidence': 0.9
                })
        
        # Risk: Blocked for too long
        blocker_duration = sum(
            ticket.get('time_in_status', {}).get('Blocked', 0)
        )
        if blocker_duration > 172800:  # 2 days in seconds
            risks.append({
                'type': 'blocked_too_long',
                'severity': 'high',
                'description': f"Blocked for {blocker_duration / 86400:.1f} days",
                'confidence': 0.95
            })
        
        # Risk: Too many reassignments (unclear ownership)
        reassignments = [
            c for c in changelog
            if c['field'] == 'assignee'
        ]
        if len(reassignments) > 3:
            risks.append({
                'type': 'unclear_ownership',
                'severity': 'medium',
                'description': f"Reassigned {len(reassignments)} times",
                'confidence': 0.8
            })
        
        if risks:
            return {
                'risks': risks,
                'severity': max(r['severity'] for r in risks),
                'confidence': sum(r['confidence'] for r in risks) / len(risks)
            }
        
        return None
    
    def _categorize_work_type(self, ticket: Dict) -> str:
        """Categorize work type"""
        
        # Check labels
        labels = ticket.get('labels', [])
        if 'frontend' in labels:
            return 'frontend'
        if 'backend' in labels:
            return 'backend'
        if 'devops' in labels:
            return 'devops'
        if 'bug' in labels:
            return 'bugfix'
        
        # Check issue type
        issue_type = ticket.get('issuetype', {}).get('name', '').lower()
        if 'bug' in issue_type:
            return 'bugfix'
        if 'story' in issue_type:
            return 'feature'
        if 'task' in issue_type:
            return 'task'
        
        return 'unknown'
```

---

### 4.3 Confluence Extractor

**Implementation:**

```python
# services/mcp-training-pipeline/domain/extractors/confluence_extractor.py

from typing import List, Dict, Any
import re

class ConfluenceKnowledgeExtractor:
    """Extract knowledge from Confluence data"""
    
    async def extract_from_page(self, page: Dict[str, Any]) -> List[Dict]:
        """Extract knowledge from a Confluence page"""
        
        knowledge_items = []
        
        # 1. EXTRACT DOCUMENTATION STYLE (for Ecosystem MCP)
        author = page.get('author')
        if author:
            doc_style = await self._extract_documentation_style(page, author)
            knowledge_items.append({
                'type': 'documentation_style',
                'scope': 'individual',
                'user': author['username'],
                'style': doc_style,
                'confidence': doc_style['confidence'],
                'source': f"confluence_{page['id']}",
                'timestamp': page['updated']
            })
        
        # 2. EXTRACT TEAM KNOWLEDGE (for Team MCP)
        if self._is_team_page(page):
            team_knowledge = await self._extract_team_knowledge(page)
            knowledge_items.append({
                'type': 'team_knowledge',
                'scope': 'team',
                'team': page.get('space', {}).get('name'),
                'knowledge': team_knowledge,
                'confidence': team_knowledge['confidence'],
                'source': f"confluence_{page['id']}",
                'timestamp': page['updated']
            })
        
        # 3. EXTRACT COMPANY STANDARDS (for Company MCP)
        if self._is_policy_page(page):
            standard = await self._extract_company_standard(page)
            knowledge_items.append({
                'type': 'company_standard',
                'scope': 'company',
                'standard': standard,
                'confidence': 0.95,  # High confidence for official docs
                'source': f"confluence_{page['id']}",
                'timestamp': page['updated']
            })
        
        # 4. EXTRACT PROJECT CONTEXT (for Project MCP)
        if self._is_project_page(page):
            project_context = await self._extract_project_context(page)
            knowledge_items.append({
                'type': 'project_context',
                'scope': 'project',
                'project': page.get('project'),
                'context': project_context,
                'confidence': project_context['confidence'],
                'source': f"confluence_{page['id']}",
                'timestamp': page['updated']
            })
        
        return knowledge_items
    
    async def _extract_documentation_style(self, page: Dict, author: Dict) -> Dict:
        """Extract how this author documents"""
        
        content = page.get('content', {}).get('body', '')
        
        # Check for diagrams
        has_diagrams = bool(re.search(r'<ac:structured-macro.*?name="(draw\.io|gliffy|mermaid)', content))
        diagram_count = len(re.findall(r'<ac:structured-macro.*?name="(draw\.io|gliffy|mermaid)', content))
        
        # Check for code examples
        has_code = bool(re.search(r'<ac:structured-macro.*?name="code', content))
        code_block_count = len(re.findall(r'<ac:structured-macro.*?name="code', content))
        
        # Check for tables
        table_count = content.count('<table')
        
        # Check for lists
        list_count = content.count('<ul') + content.count('<ol')
        
        # Calculate length
        # Strip HTML for rough word count
        text_only = re.sub(r'<[^>]+>', '', content)
        word_count = len(text_only.split())
        
        style = {
            'uses_diagrams': has_diagrams,
            'diagrams_per_doc': diagram_count,
            'uses_code_examples': has_code,
            'code_blocks_per_doc': code_block_count,
            'uses_tables': table_count > 0,
            'tables_per_doc': table_count,
            'uses_lists': list_count > 0,
            'avg_word_count': word_count,
            'documentation_frequency': self._calculate_doc_frequency(author),
            'confidence': 0.85
        }
        
        return style
    
    def _is_team_page(self, page: Dict) -> bool:
        """Check if page contains team knowledge"""
        
        title = page.get('title', '').lower()
        keywords = ['team', 'runbook', 'playbook', 'onboarding', 'adr', 'decision', 'retrospective']
        
        return any(keyword in title for keyword in keywords)
    
    async def _extract_team_knowledge(self, page: Dict) -> Dict:
        """Extract team knowledge"""
        
        title = page.get('title', '').lower()
        content = page.get('content', {}).get('body', '')
        
        knowledge = {}
        
        # Extract ADRs (Architecture Decision Records)
        if 'adr' in title or 'decision' in title:
            knowledge['type'] = 'architecture_decision'
            knowledge['decision'] = self._extract_decision(content)
            knowledge['rationale'] = self._extract_rationale(content)
            knowledge['confidence'] = 0.9
        
        # Extract runbooks
        elif 'runbook' in title or 'playbook' in title:
            knowledge['type'] = 'runbook'
            knowledge['procedures'] = self._extract_procedures(content)
            knowledge['confidence'] = 0.85
        
        # Extract retrospectives
        elif 'retrospective' in title or 'retro' in title:
            knowledge['type'] = 'retrospective'
            knowledge['went_well'] = self._extract_section(content, 'went well')
            knowledge['improvements'] = self._extract_section(content, 'improve')
            knowledge['action_items'] = self._extract_action_items(content)
            knowledge['confidence'] = 0.8
        
        return knowledge
    
    def _is_policy_page(self, page: Dict) -> bool:
        """Check if page is a company policy/standard"""
        
        space = page.get('space', {}).get('key', '').lower()
        title = page.get('title', '').lower()
        
        # Check if in Engineering Standards space
        if space in ['eng', 'engineering', 'standards']:
            return True
        
        # Check title
        keywords = ['policy', 'standard', 'guideline', 'requirement', 'compliance']
        return any(keyword in title for keyword in keywords)
    
    async def _extract_company_standard(self, page: Dict) -> Dict:
        """Extract company standards/policies"""
        
        content = page.get('content', {}).get('body', '')
        title = page.get('title', '')
        
        standard = {
            'title': title,
            'category': self._categorize_standard(title),
            'requirements': self._extract_requirements(content),
            'exceptions': self._extract_exceptions(content),
            'enforcement': self._extract_enforcement(content),
        }
        
        return standard
    
    def _is_project_page(self, page: Dict) -> bool:
        """Check if page is project-specific"""
        
        title = page.get('title', '').lower()
        keywords = ['project', 'rfc', 'design', 'requirements', 'retrospective']
        
        return any(keyword in title for keyword in keywords)
    
    async def _extract_project_context(self, page: Dict) -> Dict:
        """Extract project context"""
        
        content = page.get('content', {}).get('body', '')
        title = page.get('title', '')
        
        context = {
            'project_name': title,
            'requirements': self._extract_requirements(content),
            'success_criteria': self._extract_success_criteria(content),
            'risks': self._extract_risks(content),
            'timeline': self._extract_timeline(content),
            'confidence': 0.75
        }
        
        return context
```

---

### 4.4 FullStory Extractor

**Implementation:**

```python
# services/mcp-training-pipeline/domain/extractors/fullstory_extractor.py

from typing import List, Dict, Any

class FullStoryKnowledgeExtractor:
    """Extract knowledge from FullStory data"""
    
    async def extract_from_sessions(self, sessions: List[Dict]) -> List[Dict]:
        """Extract knowledge from user sessions"""
        
        knowledge_items = []
        
        # 1. EXTRACT USAGE PATTERNS (for Project MCP)
        usage_patterns = await self._extract_usage_patterns(sessions)
        knowledge_items.append({
            'type': 'usage_pattern',
            'scope': 'project',
            'patterns': usage_patterns,
            'sample_size': len(sessions),
            'confidence': 0.85 if len(sessions) > 100 else 0.6,
            'source': 'fullstory_sessions',
            'timestamp': datetime.now()
        })
        
        # 2. EXTRACT PAIN POINTS (for Project MCP)
        pain_points = await self._extract_pain_points(sessions)
        if pain_points:
            knowledge_items.append({
                'type': 'pain_point',
                'scope': 'project',
                'pain_points': pain_points,
                'severity': pain_points['severity'],
                'confidence': pain_points['confidence'],
                'source': 'fullstory_sessions',
                'timestamp': datetime.now()
            })
        
        # 3. EXTRACT PRODUCT INSIGHTS (for Company MCP)
        product_insights = await self._extract_product_insights(sessions)
        knowledge_items.append({
            'type': 'product_insight',
            'scope': 'company',
            'insights': product_insights,
            'confidence': 0.9,
            'source': 'fullstory_sessions',
            'timestamp': datetime.now()
        })
        
        return knowledge_items
    
    async def _extract_usage_patterns(self, sessions: List[Dict]) -> Dict:
        """Extract how users actually use the product"""
        
        # Aggregate events across sessions
        all_events = []
        for session in sessions:
            all_events.extend(session.get('events', []))
        
        # Most common user journeys
        journeys = self._identify_journeys(sessions)
        
        # Feature usage
        feature_usage = {}
        for event in all_events:
            feature = event.get('feature')
            if feature:
                feature_usage[feature] = feature_usage.get(feature, 0) + 1
        
        # Sort by usage
        top_features = sorted(feature_usage.items(), key=lambda x: x[1], reverse=True)[:10]
        underused_features = sorted(feature_usage.items(), key=lambda x: x[1])[:5]
        
        # Device/browser distribution
        devices = {}
        browsers = {}
        for session in sessions:
            device = session.get('device_type')
            browser = session.get('browser')
            if device:
                devices[device] = devices.get(device, 0) + 1
            if browser:
                browsers[browser] = browsers.get(browser, 0) + 1
        
        patterns = {
            'total_sessions': len(sessions),
            'avg_session_duration_min': sum(s.get('duration', 0) for s in sessions) / len(sessions) / 60,
            'top_features': top_features,
            'underused_features': underused_features,
            'common_journeys': journeys[:5],
            'device_distribution': devices,
            'browser_distribution': browsers,
        }
        
        return patterns
    
    async def _extract_pain_points(self, sessions: List[Dict]) -> Dict:
        """Extract user frustrations"""
        
        pain_points = []
        
        # Rage clicks (rapid clicks on same element)
        rage_clicks = []
        for session in sessions:
            for event in session.get('events', []):
                if event.get('type') == 'rage_click':
                    rage_clicks.append({
                        'page': event.get('page_url'),
                        'element': event.get('element'),
                        'count': event.get('click_count')
                    })
        
        if rage_clicks:
            # Group by page
            rage_by_page = {}
            for rc in rage_clicks:
                page = rc['page']
                rage_by_page[page] = rage_by_page.get(page, 0) + 1
            
            top_rage_page = max(rage_by_page.items(), key=lambda x: x[1])
            
            pain_points.append({
                'type': 'rage_clicks',
                'severity': 'high' if top_rage_page[1] > 20 else 'medium',
                'page': top_rage_page[0],
                'count': top_rage_page[1],
                'description': f"Users frustrated on {top_rage_page[0]} ({top_rage_page[1]} rage clicks)"
            })
        
        # Error messages
        errors = []
        for session in sessions:
            for event in session.get('events', []):
                if event.get('type') == 'error':
                    errors.append({
                        'page': event.get('page_url'),
                        'message': event.get('error_message')
                    })
        
        if errors:
            error_rate = len(errors) / len(sessions)
            if error_rate > 0.1:  # >10% of sessions have errors
                pain_points.append({
                    'type': 'errors',
                    'severity': 'high' if error_rate > 0.2 else 'medium',
                    'error_rate': error_rate,
                    'most_common_error': self._most_common(errors, 'message'),
                    'description': f"{error_rate:.0%} of sessions encounter errors"
                })
        
        # Abandoned workflows (started but didn't complete)
        abandoned = self._identify_abandoned_workflows(sessions)
        if abandoned:
            for workflow, abandon_rate in abandoned.items():
                if abandon_rate > 0.15:  # >15% abandon
                    pain_points.append({
                        'type': 'abandoned_workflow',
                        'severity': 'high' if abandon_rate > 0.3 else 'medium',
                        'workflow': workflow,
                        'abandon_rate': abandon_rate,
                        'description': f"{abandon_rate:.0%} abandon {workflow}"
                    })
        
        if pain_points:
            # Calculate overall severity
            high_severity = len([p for p in pain_points if p['severity'] == 'high'])
            overall_severity = 'high' if high_severity > 0 else 'medium'
            
            return {
                'pain_points': pain_points,
                'count': len(pain_points),
                'severity': overall_severity,
                'confidence': 0.9 if len(sessions) > 100 else 0.7
            }
        
        return None
    
    async def _extract_product_insights(self, sessions: List[Dict]) -> Dict:
        """Extract high-level product insights"""
        
        # Feature adoption (new feature usage over time)
        # This would require time-series data, simplified here
        
        # User segments
        segments = self._segment_users(sessions)
        
        # Retention (would need historical data)
        
        insights = {
            'user_segments': segments,
            'power_users_pct': segments.get('power_users', 0) / len(sessions) if sessions else 0,
            'casual_users_pct': segments.get('casual_users', 0) / len(sessions) if sessions else 0,
        }
        
        return insights
    
    def _identify_journeys(self, sessions: List[Dict]) -> List[Dict]:
        """Identify common user journeys"""
        
        journeys = []
        
        for session in sessions:
            events = session.get('events', [])
            if not events:
                continue
            
            # Extract sequence of pages
            pages = [e.get('page_url') for e in events if e.get('page_url')]
            
            # Simplify to unique sequence
            journey = []
            for page in pages:
                if not journey or journey[-1] != page:
                    journey.append(page)
            
            journeys.append(tuple(journey))
        
        # Find most common journeys
        journey_counts = {}
        for journey in journeys:
            journey_counts[journey] = journey_counts.get(journey, 0) + 1
        
        # Convert to list of dicts
        common_journeys = [
            {'journey': list(journey), 'count': count}
            for journey, count in sorted(journey_counts.items(), key=lambda x: x[1], reverse=True)
        ]
        
        return common_journeys
```

---

## 5. Intelligent Routing Logic

### 5.1 Scope Classifier

**Determines which MCP tier to route to:**

```python
# services/mcp-training-pipeline/domain/classifiers/scope_classifier.py

from typing import Dict, List
from enum import Enum

class Scope(Enum):
    INDIVIDUAL = "individual"  # Ecosystem MCP (Tier 4)
    TEAM = "team"              # Team MCP (Tier 3)
    COMPANY = "company"        # Company MCP (Tier 2)
    PROJECT = "project"        # Project MCP (Tier 1)

class ScopeClassifier:
    """Classify scope of knowledge (which MCP tier to route to)"""
    
    def classify(self, knowledge_item: Dict) -> List[Scope]:
        """
        Classify scope of knowledge item.
        Can return multiple scopes (knowledge can feed multiple tiers).
        """
        
        # Explicit scope (from extractor)
        if 'scope' in knowledge_item:
            explicit_scope = Scope(knowledge_item['scope'])
            
            # Determine if should also feed parent tiers
            if explicit_scope == Scope.INDIVIDUAL:
                # Individual knowledge can also feed team
                return [Scope.INDIVIDUAL, Scope.TEAM]
            elif explicit_scope == Scope.TEAM:
                # Team knowledge can also feed company
                return [Scope.TEAM, Scope.COMPANY]
            else:
                return [explicit_scope]
        
        # Implicit scope (infer from content)
        scopes = []
        
        # Check knowledge type
        knowledge_type = knowledge_item.get('type')
        
        if knowledge_type == 'code_pattern':
            # Code patterns are individual, but aggregate to team
            scopes = [Scope.INDIVIDUAL, Scope.TEAM]
        
        elif knowledge_type == 'review_pattern':
            # Review patterns are team-level
            scopes = [Scope.TEAM, Scope.COMPANY]
        
        elif knowledge_type == 'technical_decision':
            # Technical decisions are company-wide
            scopes = [Scope.COMPANY, Scope.PROJECT]
        
        elif knowledge_type == 'work_pattern':
            # Work patterns are individual
            scopes = [Scope.INDIVIDUAL, Scope.TEAM]
        
        elif knowledge_type == 'process_metric':
            # Process metrics are company-level
            scopes = [Scope.COMPANY]
        
        elif knowledge_type == 'usage_pattern':
            # Usage patterns inform projects
            scopes = [Scope.PROJECT, Scope.COMPANY]
        
        elif knowledge_type == 'pain_point':
            # Pain points inform current project
            scopes = [Scope.PROJECT]
        
        else:
            # Default: route to all
            scopes = [Scope.INDIVIDUAL, Scope.TEAM, Scope.COMPANY, Scope.PROJECT]
        
        return scopes
```

---

### 5.2 MCP Router

**Routes knowledge to appropriate MCP tiers:**

```python
# services/mcp-training-pipeline/domain/routers/mcp_router.py

from typing import Dict, List
import httpx
from domain.classifiers.scope_classifier import Scope, ScopeClassifier

class MCPRouter:
    """Route knowledge to appropriate MCP tiers"""
    
    def __init__(self):
        self.scope_classifier = ScopeClassifier()
        
        # MCP endpoints
        self.mcp_endpoints = {
            Scope.INDIVIDUAL: "http://localhost:3000",  # Ecosystem MCP (your laptop)
            Scope.TEAM: "http://team-mcp-server:3000",  # Team MCP (team server)
            Scope.COMPANY: "http://company-mcp-server:3000",  # Company MCP (company server)
            Scope.PROJECT: "http://project-mcp-server:3000"  # Project MCP (project server)
        }
    
    async def route(self, knowledge_item: Dict):
        """Route knowledge item to appropriate MCP tier(s)"""
        
        # Classify scope
        scopes = self.scope_classifier.classify(knowledge_item)
        
        # Route to each scope
        results = []
        for scope in scopes:
            try:
                result = await self._send_to_mcp(scope, knowledge_item)
                results.append({
                    'scope': scope.value,
                    'success': True,
                    'result': result
                })
            except Exception as e:
                results.append({
                    'scope': scope.value,
                    'success': False,
                    'error': str(e)
                })
        
        return results
    
    async def _send_to_mcp(self, scope: Scope, knowledge_item: Dict) -> Dict:
        """Send knowledge to specific MCP tier"""
        
        endpoint = self.mcp_endpoints.get(scope)
        if not endpoint:
            raise ValueError(f"No endpoint configured for scope: {scope}")
        
        # Transform knowledge item to MCP format
        mcp_payload = self._transform_to_mcp_format(scope, knowledge_item)
        
        # Send to MCP
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{endpoint}/knowledge/ingest",
                json=mcp_payload,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    
    def _transform_to_mcp_format(self, scope: Scope, knowledge_item: Dict) -> Dict:
        """Transform knowledge item to MCP-specific format"""
        
        if scope == Scope.INDIVIDUAL:
            # Ecosystem MCP expects user-specific knowledge
            return {
                'user': knowledge_item.get('user') or knowledge_item.get('author'),
                'knowledge_type': knowledge_item['type'],
                'content': knowledge_item.get('pattern') or knowledge_item.get('content'),
                'metadata': {
                    'source': knowledge_item.get('source'),
                    'timestamp': knowledge_item.get('timestamp'),
                    'confidence': knowledge_item.get('confidence', 0.5)
                }
            }
        
        elif scope == Scope.TEAM:
            # Team MCP expects team-aggregated knowledge
            return {
                'team': knowledge_item.get('team'),
                'knowledge_type': knowledge_item['type'],
                'content': knowledge_item.get('pattern') or knowledge_item.get('content'),
                'contributors': knowledge_item.get('contributors', []),
                'metadata': {
                    'source': knowledge_item.get('source'),
                    'timestamp': knowledge_item.get('timestamp'),
                    'confidence': knowledge_item.get('confidence', 0.5)
                }
            }
        
        elif scope == Scope.COMPANY:
            # Company MCP expects enterprise-wide knowledge
            return {
                'knowledge_type': knowledge_item['type'],
                'content': knowledge_item.get('decision') or knowledge_item.get('standard') or knowledge_item.get('content'),
                'affected_teams': knowledge_item.get('affected_teams', []),
                'metadata': {
                    'source': knowledge_item.get('source'),
                    'timestamp': knowledge_item.get('timestamp'),
                    'confidence': knowledge_item.get('confidence', 0.5),
                    'enforcement': knowledge_item.get('enforcement', 'optional')
                }
            }
        
        elif scope == Scope.PROJECT:
            # Project MCP expects project-specific insights
            return {
                'project': knowledge_item.get('project'),
                'knowledge_type': knowledge_item['type'],
                'content': knowledge_item.get('pattern') or knowledge_item.get('insight') or knowledge_item.get('content'),
                'metadata': {
                    'source': knowledge_item.get('source'),
                    'timestamp': knowledge_item.get('timestamp'),
                    'confidence': knowledge_item.get('confidence', 0.5)
                }
            }
```

---

## 6. Implementation Guide

### 6.1 Main Service: `mcp-training-pipeline`

**FastAPI application:**

```python
# services/mcp-training-pipeline/main.py

from fastapi import FastAPI, BackgroundTasks
from typing import Dict, List
import httpx
from domain.extractors.github_extractor import GitHubKnowledgeExtractor
from domain.extractors.jira_extractor import JiraKnowledgeExtractor
from domain.extractors.confluence_extractor import ConfluenceKnowledgeExtractor
from domain.extractors.fullstory_extractor import FullStoryKnowledgeExtractor
from domain.routers.mcp_router import MCPRouter

app = FastAPI(title="MCP Training Pipeline")

# Initialize extractors
github_extractor = GitHubKnowledgeExtractor()
jira_extractor = JiraKnowledgeExtractor()
confluence_extractor = ConfluenceKnowledgeExtractor()
fullstory_extractor = FullStoryKnowledgeExtractor()

# Initialize router
mcp_router = MCPRouter()

# ============================================
# WEBHOOKS: Listen to source-agent events
# ============================================

@app.post("/webhooks/github/pr")
async def process_github_pr(pr: Dict, background_tasks: BackgroundTasks):
    """Process GitHub PR and extract knowledge"""
    
    background_tasks.add_task(process_pr_async, pr)
    
    return {"status": "queued", "pr_number": pr.get('number')}

async def process_pr_async(pr: Dict):
    """Background task: extract and route knowledge"""
    
    # Extract knowledge
    knowledge_items = await github_extractor.extract_from_pr(pr)
    
    # Route to appropriate MCP tiers
    for item in knowledge_items:
        await mcp_router.route(item)

@app.post("/webhooks/jira/ticket")
async def process_jira_ticket(ticket: Dict, background_tasks: BackgroundTasks):
    """Process Jira ticket and extract knowledge"""
    
    background_tasks.add_task(process_ticket_async, ticket)
    
    return {"status": "queued", "ticket_key": ticket.get('key')}

async def process_ticket_async(ticket: Dict):
    """Background task: extract and route knowledge"""
    
    knowledge_items = await jira_extractor.extract_from_ticket(ticket)
    
    for item in knowledge_items:
        await mcp_router.route(item)

@app.post("/webhooks/confluence/page")
async def process_confluence_page(page: Dict, background_tasks: BackgroundTasks):
    """Process Confluence page and extract knowledge"""
    
    background_tasks.add_task(process_page_async, page)
    
    return {"status": "queued", "page_id": page.get('id')}

async def process_page_async(page: Dict):
    """Background task: extract and route knowledge"""
    
    knowledge_items = await confluence_extractor.extract_from_page(page)
    
    for item in knowledge_items:
        await mcp_router.route(item)

@app.post("/webhooks/fullstory/sessions")
async def process_fullstory_sessions(sessions: List[Dict], background_tasks: BackgroundTasks):
    """Process FullStory sessions and extract knowledge"""
    
    background_tasks.add_task(process_sessions_async, sessions)
    
    return {"status": "queued", "session_count": len(sessions)}

async def process_sessions_async(sessions: List[Dict]):
    """Background task: extract and route knowledge"""
    
    knowledge_items = await fullstory_extractor.extract_from_sessions(sessions)
    
    for item in knowledge_items:
        await mcp_router.route(item)

# ============================================
# MANUAL TRIGGERS (for backfill)
# ============================================

@app.post("/backfill/github")
async def backfill_github(repo: str, days: int = 30):
    """Backfill GitHub data (last N days)"""
    
    # Fetch PRs from source-agent
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"http://localhost:5000/github/prs",
            params={"repo": repo, "days": days}
        )
        prs = response.json()
    
    # Process each PR
    results = []
    for pr in prs:
        knowledge_items = await github_extractor.extract_from_pr(pr)
        for item in knowledge_items:
            result = await mcp_router.route(item)
            results.append(result)
    
    return {
        "prs_processed": len(prs),
        "knowledge_items": len(results),
        "status": "complete"
    }

# Similar backfill endpoints for Jira, Confluence, FullStory

# ============================================
# MONITORING
# ============================================

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/metrics")
async def metrics():
    """Return processing metrics"""
    # Would query from database/metrics store
    return {
        "total_processed": 1234,
        "by_source": {
            "github": 456,
            "jira": 398,
            "confluence": 280,
            "fullstory": 100
        },
        "by_scope": {
            "individual": 600,
            "team": 400,
            "company": 200,
            "project": 134
        }
    }
```

---

## 7. Integration with Existing Services

### 7.1 Extend `source-agent` to Emit Events

**Modify source-agent to send webhooks:**

```python
# services/source-agent/infrastructure/event_emitter.py

import httpx

class MCPEventEmitter:
    """Emit events to MCP training pipeline"""
    
    def __init__(self, mcp_pipeline_url: str = "http://localhost:5200"):
        self.mcp_pipeline_url = mcp_pipeline_url
    
    async def emit_github_pr(self, pr: Dict):
        """Emit GitHub PR event"""
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self.mcp_pipeline_url}/webhooks/github/pr",
                json=pr,
                timeout=5.0
            )
    
    async def emit_jira_ticket(self, ticket: Dict):
        """Emit Jira ticket event"""
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self.mcp_pipeline_url}/webhooks/jira/ticket",
                json=ticket,
                timeout=5.0
            )
    
    # ... similar for Confluence, FullStory
```

**Use in source-agent:**

```python
# services/source-agent/application/use_cases/fetch_github_prs.py

from infrastructure.event_emitter import MCPEventEmitter

emitter = MCPEventEmitter()

async def fetch_github_prs(repo: str):
    """Fetch PRs and emit to MCP pipeline"""
    
    # Fetch PRs from GitHub API
    prs = await github_client.get_prs(repo)
    
    # Store in doc-store (existing behavior)
    for pr in prs:
        await doc_store.save(pr)
        
        # NEW: Emit to MCP training pipeline
        await emitter.emit_github_pr(pr)
    
    return prs
```

---

### 7.2 Create Ecosystem MCP Server (Tier 4)

**Your laptop's MCP server:**

```python
# services/ecosystem-mcp/main.py

from fastmcp import FastMCP
import chromadb
from neo4j import GraphDatabase

mcp = FastMCP("ecosystem-mcp")

# Initialize storage
chroma = chromadb.Client()
code_collection = chroma.get_or_create_collection("code_patterns")
work_collection = chroma.get_or_create_collection("work_patterns")

neo4j_driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

# ============================================
# KNOWLEDGE INGESTION (from training pipeline)
# ============================================

@mcp.tool()
async def ingest_knowledge(user: str, knowledge_type: str, content: Dict, metadata: Dict):
    """Ingest knowledge into this user's ecosystem MCP"""
    
    # Store in vector DB
    if knowledge_type == 'code_pattern':
        code_collection.add(
            documents=[str(content)],
            metadatas=[{
                'user': user,
                'type': knowledge_type,
                **metadata
            }],
            ids=[f"{user}_{knowledge_type}_{metadata['timestamp']}"]
        )
    
    elif knowledge_type == 'work_pattern':
        work_collection.add(
            documents=[str(content)],
            metadatas=[{
                'user': user,
                'type': knowledge_type,
                **metadata
            }],
            ids=[f"{user}_{knowledge_type}_{metadata['timestamp']}"]
        )
    
    # Store relationships in graph DB
    with neo4j_driver.session() as session:
        if knowledge_type == 'code_pattern':
            session.run(
                """
                MERGE (u:User {username: $user})
                CREATE (p:Pattern {
                    type: $type,
                    content: $content,
                    confidence: $confidence,
                    timestamp: $timestamp
                })
                CREATE (u)-[:HAS_PATTERN]->(p)
                """,
                user=user,
                type=knowledge_type,
                content=str(content),
                confidence=metadata.get('confidence', 0.5),
                timestamp=metadata.get('timestamp')
            )
    
    return {"status": "ingested", "user": user, "type": knowledge_type}

# ============================================
# KNOWLEDGE RETRIEVAL (for recommendations)
# ============================================

@mcp.resource("ecosystem://patterns/{user}/code")
async def get_user_code_patterns(user: str):
    """Get this user's code patterns"""
    
    results = code_collection.query(
        query_texts=["code patterns"],
        where={"user": user},
        n_results=50
    )
    
    return {
        "uri": f"ecosystem://patterns/{user}/code",
        "patterns": results['documents'],
        "count": len(results['documents'])
    }

# Start MCP server
if __name__ == "__main__":
    mcp.run(transport="sse", port=3000)
```

---

## 8. Example Workflows

### 8.1 Complete Flow: GitHub PR → MCP Training

```
1. Developer creates PR in GitHub
   ↓
2. source-agent fetches PR (periodic polling or webhook)
   ↓
3. source-agent saves PR to doc-store (existing)
   ↓
4. source-agent emits event to mcp-training-pipeline (NEW)
   POST /webhooks/github/pr
   ↓
5. mcp-training-pipeline receives event
   ↓
6. GitHubKnowledgeExtractor.extract_from_pr(pr)
   → Extracts code patterns (async/await, type hints, etc.)
   → Extracts review patterns (team values testing)
   → Extracts technical decisions (if architecture PR)
   ↓
7. ScopeClassifier.classify(knowledge_item)
   → code_pattern → [INDIVIDUAL, TEAM]
   → review_pattern → [TEAM, COMPANY]
   ↓
8. MCPRouter.route(knowledge_item)
   → Sends to Ecosystem MCP (Tier 4, developer's laptop)
   → Sends to Team MCP (Tier 3, team server)
   ↓
9. Ecosystem MCP stores in ChromaDB + Neo4j
   ↓
10. Team MCP aggregates across team members
   ↓
11. MCP is now trained and can provide recommendations!
```

---

### 8.2 Query Flow: Developer Asks for Recommendation

```
1. Developer in Cursor IDE types:
   "How should I structure this new API endpoint?"
   ↓
2. Cursor MCP client sends to Ecosystem MCP
   ↓
3. Ecosystem MCP queries ChromaDB:
   "Find similar past API endpoints by this user"
   ↓
4. Ecosystem MCP queries Neo4j:
   "What patterns does this user prefer?"
   ↓
5. Ecosystem MCP synthesizes recommendation:
   "Based on your past 23 API endpoints, you prefer:
    • FastAPI with async/await
    • Pydantic models for request/response
    • @router.post() decorator
    • Try/except with specific exceptions
    • pytest tests with fixtures"
   ↓
6. Ecosystem MCP also queries Team MCP:
   "What does the team require?"
   ↓
7. Team MCP responds:
   "Team requires:
    • 2 approvals for API changes
    • Type hints on all functions
    • OpenAPI documentation
    • At least 80% test coverage"
   ↓
8. Ecosystem MCP combines recommendations:
   "Here's a template based on YOUR preferences + TEAM requirements"
   ↓
9. Developer receives recommendation in Cursor
   ↓
10. Developer applies (or rejects)
    ↓
11. Outcome is recorded → MCP learns!
```

---

## 9. Privacy & Security

### 9.1 Data Sensitivity

**Classification:**

```python
class SensitivityClassifier:
    """Classify data sensitivity"""
    
    def classify(self, knowledge_item: Dict) -> str:
        """Classify as public, internal, or confidential"""
        
        # Check for PII
        if self._contains_pii(knowledge_item):
            return "confidential"
        
        # Check for security-sensitive info
        if self._contains_security_info(knowledge_item):
            return "confidential"
        
        # Check source
        source = knowledge_item.get('source', '')
        if 'fullstory' in source:
            # User behavior is sensitive
            return "internal"
        
        # Default
        return "internal"
    
    def _contains_pii(self, knowledge_item: Dict) -> bool:
        """Check for PII (emails, names, etc.)"""
        # Implement PII detection
        pass
    
    def _contains_security_info(self, knowledge_item: Dict) -> bool:
        """Check for security-sensitive info (keys, passwords, etc.)"""
        # Implement security detection
        pass
```

**Handling:**
- ✅ **Anonymize** PII before storing
- ✅ **Encrypt** confidential data at rest
- ✅ **Restrict access** based on sensitivity
- ✅ **Audit** all accesses to confidential knowledge

---

### 9.2 Access Control

**MCP Tier Access:**

| Tier | Who Can Access | What They See |
|------|---------------|---------------|
| **Ecosystem MCP (T4)** | Only you | Your personal patterns, work history |
| **Team MCP (T3)** | Your team | Team patterns, aggregated (not individual details) |
| **Company MCP (T2)** | All employees | Company standards, policies (not team/individual) |
| **Project MCP (T1)** | Project members | Project-specific insights (not personal data) |

---

## 10. Roadmap

### 10.1 Phase 0: Foundation (Week 1-2)

**Goal:** Setup infrastructure

- [ ] Install ChromaDB (vector database)
- [ ] Install Neo4j (graph database)
- [ ] Create `mcp-training-pipeline` service (skeleton)
- [ ] Create `ecosystem-mcp` service (skeleton)

---

### 10.2 Phase 1: GitHub Integration (Week 3-4)

**Goal:** GitHub → MCP pipeline working

- [ ] Implement `GitHubKnowledgeExtractor`
- [ ] Implement `ScopeClassifier`
- [ ] Implement `MCPRouter`
- [ ] Modify `source-agent` to emit events
- [ ] Test: GitHub PR → Ecosystem MCP

---

### 10.3 Phase 2: Jira Integration (Week 5-6)

**Goal:** Jira → MCP pipeline working

- [ ] Implement `JiraKnowledgeExtractor`
- [ ] Test: Jira ticket → Team MCP
- [ ] Test: Velocity, estimation patterns extracted

---

### 10.4 Phase 3: Confluence & FullStory (Week 7-8)

**Goal:** All 4 sources → MCP pipeline

- [ ] Implement `ConfluenceKnowledgeExtractor`
- [ ] Implement `FullStoryKnowledgeExtractor`
- [ ] Test: Confluence page → Company MCP
- [ ] Test: FullStory sessions → Project MCP

---

### 10.5 Phase 4: Hierarchical MCP (Week 9-10)

**Goal:** 4-tier MCP hierarchy working

- [ ] Create Team MCP server (Tier 3)
- [ ] Create Company MCP server (Tier 2)
- [ ] Create Project MCP server (Tier 1)
- [ ] Test: Knowledge flows up hierarchy

---

### 10.6 Phase 5: Recommendation Engine (Week 11-12)

**Goal:** MCP provides useful recommendations

- [ ] Implement recommendation synthesis
- [ ] Implement feedback loop (track outcomes)
- [ ] Integrate with Cursor IDE
- [ ] Test: Developer gets useful recommendations

---

## 11. Conclusion

### 11.1 Summary

You can build an **automated Hierarchical MCP training system** that:

✅ **Ingests** from 4 data sources (GitHub, Jira, Confluence, FullStory)  
✅ **Extracts** 4 types of knowledge (patterns, decisions, outcomes, metrics)  
✅ **Classifies** scope (individual, team, company, project)  
✅ **Routes** to appropriate MCP tier (Tier 4, 3, 2, or 1)  
✅ **Trains** knowledge graphs (ChromaDB + Neo4j)  
✅ **Learns** from outcomes (feedback loop)  
✅ **Recommends** based on historical success  

**The wrapper service (`mcp-training-pipeline`) is the key:**
- Listens to events from `source-agent`
- Extracts knowledge using source-specific extractors
- Classifies scope using intelligent classifier
- Routes to appropriate MCP tier(s)
- All happens automatically, 24/7!

**Timeline:** 12 weeks to full implementation (6 phases)

---

**📍 Location:** `/docs/HIERARCHICAL_MCP_TRAINING_PIPELINE.md`  
**📄 Status:** Design complete, ready for implementation  
**🎯 Goal:** Automatically train Hierarchical MCP from company data  
**📊 Scope:** GitHub, Jira, Confluence, FullStory → 4-tier MCP  

**Ready to build?** The architecture is designed! 🚀

