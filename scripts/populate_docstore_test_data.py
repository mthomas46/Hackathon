#!/usr/bin/env python3
"""
Populate Doc Store with comprehensive test data covering all document types.

This script creates test documents of all types that the project processes:
- GitHub READMEs, issues, PRs
- Jira issues and epics
- Confluence pages
- Code files (Python, TypeScript, etc.)
- API documentation
- Analysis results (consistency, security, quality, style)
- Ensemble results
- Style examples
- Configuration files
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from typing import Dict, Any, List

# Add services to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.shared.utilities import utc_now, stable_hash
from services.shared.envelopes import DocumentEnvelope


def generate_content_hash(content: str) -> str:
    """Generate content hash for a document."""
    return stable_hash(content)[:16]


def create_github_documents() -> List[Dict[str, Any]]:
    """Create test GitHub documents."""
    return [
        {
            "id": "github:hackathon-project:readme",
            "content": """# Hackathon Project

A comprehensive AI-powered development platform that streamlines software engineering workflows through intelligent automation, analysis, and orchestration.

## Features

- **Source Agent**: Ingests and normalizes content from GitHub, Jira, and Confluence
- **Analysis Service**: Provides consistency, security, and quality analysis
- **Orchestrator**: Manages complex workflows and job orchestration
- **CLI Interface**: Professional command-line interface with interactive features

## Architecture

The platform consists of multiple microservices communicating via REST APIs and Redis pub/sub:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Source Agent  │───▶│  Orchestrator   │───▶│ Analysis Engine │
│                 │    │                 │    │                 │
│ GitHub/Jira/CF  │    │ Workflows       │    │ Consistency     │
└─────────────────┘    └─────────────────┘    │ Security        │
                                              │ Quality         │
                                              └─────────────────┘
```

## Getting Started

1. Clone the repository
2. Run `make setup` to configure the environment
3. Start services with `make up`
4. Access the CLI with `python3 run_cli.py`

## Configuration

Environment variables:
- `DOC_STORE_URL`: Document store endpoint
- `ANALYSIS_SERVICE_URL`: Analysis service endpoint
- `ORCHESTRATOR_URL`: Orchestrator endpoint
""",
            "metadata": {
                "source_type": "github",
                "type": "readme",
                "owner": "hackathon-project",
                "repo": "main",
                "url": "https://github.com/hackathon-project/main",
                "language": "Markdown",
                "size": 2048
            }
        },
        {
            "id": "github:hackathon-project:issue-123",
            "content": """## Issue: Implement Interactive CLI Features

**Description:**
The current CLI is functional but lacks modern interactive features that would improve user experience significantly.

**Requirements:**
- Arrow-key navigation for menus
- Search functionality within menus
- Auto-completion for commands
- Color-coded status indicators
- Loading spinners and progress bars

**Acceptance Criteria:**
- [ ] Users can navigate menus with arrow keys
- [ ] Search functionality works across all menu items
- [ ] Commands auto-complete based on context
- [ ] Status indicators show operation progress
- [ ] Loading indicators provide feedback during long operations

**Labels:** enhancement, cli, ux, questionary

**Assignee:** @developer1
**Milestone:** v2.0.0""",
            "metadata": {
                "source_type": "github",
                "type": "issue",
                "number": 123,
                "state": "open",
                "title": "Implement Interactive CLI Features",
                "labels": ["enhancement", "cli", "ux"],
                "assignee": "developer1",
                "milestone": "v2.0.0"
            }
        },
        {
            "id": "github:hackathon-project:pr-456",
            "content": """## PR: Add Interactive CLI with Questionary

This PR introduces a modern interactive CLI experience using the Questionary library.

### Changes

**services/cli/modules/interactive_overlay.py**
- New InteractiveOverlay class for enhanced UX
- Arrow-key navigation support
- Search functionality in menus
- Custom styling and themes

**services/cli/modules/base/base_manager.py**
- Updated run_menu_loop to support interactive overlay
- Backward compatibility maintained for tests

**requirements updates**
- Added questionary==2.0.1
- Added prompt-toolkit for advanced features

### Testing
- All existing tests pass
- New integration tests for interactive features
- Performance benchmarks show no regression

### Breaking Changes
None. Interactive features are opt-in via `use_interactive=True`.

Closes #123""",
            "metadata": {
                "source_type": "github",
                "type": "pull_request",
                "number": 456,
                "state": "merged",
                "title": "Add Interactive CLI with Questionary",
                "author": "developer2",
                "additions": 1200,
                "deletions": 300,
                "changed_files": 5
            }
        }
    ]


def create_jira_documents() -> List[Dict[str, Any]]:
    """Create test Jira documents."""
    return [
        {
            "id": "jira:PROJ-123",
            "content": """## Epic: Platform Architecture Redesign

**Description:**
The current microservices architecture needs modernization to support scaling requirements and improve developer experience.

**Business Value:**
- Support 10x current user load
- Reduce deployment time by 50%
- Improve debugging and monitoring capabilities

**Acceptance Criteria:**
- [ ] Container orchestration with Kubernetes
- [ ] Service mesh implementation (Istio)
- [ ] Centralized logging and metrics
- [ ] Automated deployment pipelines

**Story Points:** 21
**Priority:** High
**Epic Link:** PROJ-100 (Platform Modernization)

**Linked Issues:**
- PROJ-124: Database migration to Postgres
- PROJ-125: Service mesh implementation
- PROJ-126: CI/CD pipeline enhancement""",
            "metadata": {
                "source_type": "jira",
                "type": "epic",
                "issue_key": "PROJ-123",
                "project": "PROJ",
                "status": "In Progress",
                "priority": "High",
                "assignee": "architect1",
                "reporter": "product-owner",
                "story_points": 21,
                "epic_link": "PROJ-100",
                "url": "https://company.atlassian.net/browse/PROJ-123"
            }
        },
        {
            "id": "jira:PROJ-124",
            "content": """## Story: Database Migration to Postgres

**Description:**
Migrate from SQLite to PostgreSQL for production readiness and improved performance.

**Acceptance Criteria:**
- [ ] Postgres container deployed
- [ ] Schema migration scripts created
- [ ] Data migration tested
- [ ] Application updated to use Postgres
- [ ] Performance benchmarks completed

**Testing Notes:**
- Test with large datasets (1M+ records)
- Verify transaction isolation
- Test concurrent access patterns

**Technical Details:**
- Use asyncpg for async operations
- Implement connection pooling
- Add proper indexing strategy""",
            "metadata": {
                "source_type": "jira",
                "type": "story",
                "issue_key": "PROJ-124",
                "project": "PROJ",
                "status": "To Do",
                "priority": "Medium",
                "assignee": "backend-dev",
                "story_points": 8,
                "epic_link": "PROJ-123",
                "labels": ["database", "migration", "postgres"]
            }
        }
    ]


def create_confluence_documents() -> List[Dict[str, Any]]:
    """Create test Confluence documents."""
    return [
        {
            "id": "confluence:page-789",
            "content": """# API Documentation

## Authentication

All API endpoints require authentication using JWT tokens.

### Obtaining a Token

```bash
POST /auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password"
}
```

Response:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 3600
}
```

### Using the Token

Include the token in the Authorization header:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Document Store API

### Create Document

```bash
POST /documents
Authorization: Bearer <token>
Content-Type: application/json

{
  "content": "Document content here",
  "metadata": {
    "type": "readme",
    "source": "github"
  }
}
```

### Search Documents

```bash
GET /search?q=<query>&limit=10
Authorization: Bearer <token>
```

## Error Handling

The API uses standard HTTP status codes:

- `200 OK`: Success
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Missing or invalid token
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

Error responses include a JSON body:

```json
{
  "error": {
    "code": "INVALID_INPUT",
    "message": "The provided input is invalid",
    "details": {
      "field": "content",
      "reason": "cannot be empty"
    }
  }
}
```""",
            "metadata": {
                "source_type": "confluence",
                "type": "page",
                "page_id": "789",
                "space": "API",
                "title": "API Documentation",
                "version": 5,
                "last_modified": "2024-01-15T10:30:00Z",
                "author": "tech-writer",
                "url": "https://company.atlassian.net/wiki/spaces/API/pages/789/API+Documentation"
            }
        }
    ]


def create_code_documents() -> List[Dict[str, Any]]:
    """Create test code documents."""
    return [
        {
            "id": "code:services/cli/main.py",
            "content": """#!/usr/bin/env python3
\"\"\"Main CLI entry point for the Hackathon Platform.

This module provides the command-line interface for interacting with
all platform services including orchestration, analysis, and document management.
\"\"\"

import asyncio
import sys
from pathlib import Path

# Add services to path for imports
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

from services.cli.modules.cli_commands import CLICommands
from services.shared.config import load_config


def main():
    \"\"\"Main CLI entry point.\"\"\"
    # Load configuration
    config = load_config()

    # Initialize CLI commands
    cli = CLICommands()

    # Run the CLI
    try:
        asyncio.run(cli.run())
    except KeyboardInterrupt:
        print("\\nCLI interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"CLI error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()""",
            "metadata": {
                "source_type": "code",
                "type": "python",
                "language": "python",
                "filename": "main.py",
                "path": "services/cli/main.py",
                "lines": 35,
                "size": 1024,
                "complexity": "low"
            }
        },
        {
            "id": "code:services/shared/config.py",
            "content": """\"\"\"Configuration management for Hackathon Platform services.

Provides centralized configuration loading from multiple sources:
- Environment variables
- YAML configuration files
- Default values
\"\"\"

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class Config:
    \"\"\"Configuration manager.\"\"\"

    def __init__(self):
        self._config = {}
        self._load_config()

    def _load_config(self):
        \"\"\"Load configuration from all sources.\"\"\"
        # Load from config/app.yaml
        config_path = Path(__file__).parent.parent.parent / "config" / "app.yaml"
        if config_path.exists():
            with open(config_path) as f:
                self._config.update(yaml.safe_load(f) or {})

        # Override with environment variables
        for key, value in os.environ.items():
            if key.startswith("HACKATHON_"):
                # Convert HACKATHON_DOC_STORE_URL to doc_store.url
                config_key = key.lower().replace("hackathon_", "").replace("_", ".")
                self._set_nested_value(self._config, config_key.split("."), value)

    def _set_nested_value(self, config: Dict[str, Any], keys: List[str], value: Any):
        \"\"\"Set a nested configuration value.\"\"\"
        for key in keys[:-1]:
            config = config.setdefault(key, {})
        config[keys[-1]] = value

    def get(self, key: str, default: Any = None, section: Optional[str] = None) -> Any:
        \"\"\"Get a configuration value.\"\"\"
        if section:
            config = self._config.get(section, {})
        else:
            config = self._config

        keys = key.split(".")
        for k in keys:
            if isinstance(config, dict):
                config = config.get(k)
            else:
                return default
        return config if config is not None else default


# Global config instance
_config = Config()


def get_config_value(key: str, default: Any = None, section: Optional[str] = None) -> Any:
    \"\"\"Get a configuration value.\"\"\"
    return _config.get(key, default, section)""",
            "metadata": {
                "source_type": "code",
                "type": "python",
                "language": "python",
                "filename": "config.py",
                "path": "services/shared/config.py",
                "lines": 67,
                "size": 2048,
                "complexity": "medium"
            }
        }
    ]


def create_api_docs() -> List[Dict[str, Any]]:
    """Create test API documentation."""
    return [
        {
            "id": "api:doc-store:endpoints",
            "content": """# Doc Store API Reference

## Documents

### POST /documents
Create a new document.

**Request Body:**
```json
{
  "content": "string",
  "metadata": {
    "type": "string",
    "source_type": "string"
  },
  "correlation_id": "string (optional)"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "id": "string",
    "content_hash": "string",
    "created_at": "string"
  }
}
```

### GET /documents/{id}
Retrieve a document by ID.

**Response:**
```json
{
  "status": "success",
  "data": {
    "id": "string",
    "content": "string",
    "content_hash": "string",
    "metadata": {},
    "created_at": "string"
  }
}
```

## Search

### GET /search
Search documents using FTS.

**Query Parameters:**
- `q`: Search query
- `limit`: Maximum results (default: 10)
- `offset`: Pagination offset (default: 0)

**Response:**
```json
{
  "status": "success",
  "data": {
    "items": [
      {
        "id": "string",
        "content": "string",
        "metadata": {},
        "score": 0.95
      }
    ],
    "total": 42
  }
}
```

## Quality

### GET /documents/quality
Get document quality metrics.

**Response:**
```json
{
  "status": "success",
  "data": {
    "items": [
      {
        "id": "string",
        "stale_days": 30,
        "flags": ["stale", "no_owner"],
        "importance_score": 0.8
      }
    ]
  }
}
```""",
            "metadata": {
                "source_type": "api",
                "type": "reference",
                "service": "doc-store",
                "version": "v1.0",
                "endpoints": 15,
                "format": "OpenAPI-like"
            }
        }
    ]


def create_analysis_documents() -> List[Dict[str, Any]]:
    """Create test analysis documents."""
    return [
        {
            "id": "analysis:consistency:github:hackathon-project:readme",
            "content": """Consistency Analysis Report
==============================

Document: github:hackathon-project:readme
Analyzed at: 2024-01-15T14:30:00Z
Analyzer: consistency-v2.1
Model: gpt-4-turbo

SUMMARY
-------
Overall Score: 0.92 (High Consistency)
Issues Found: 2 minor

DETAILED FINDINGS
-----------------

1. Terminology Inconsistency (Minor)
   - Line 15: "microservices" vs Line 45: "micro-services"
   - Recommendation: Standardize to "microservices"
   - Impact: Low

2. Formatting Inconsistency (Minor)
   - Mixed use of code block languages
   - Some blocks lack language specification
   - Recommendation: Specify language for all code blocks
   - Impact: Low

RECOMMENDATIONS
---------------
1. Standardize terminology across documentation
2. Ensure consistent code block formatting
3. Consider adding automated consistency checks to CI/CD

TECHNICAL METRICS
-----------------
Processing Time: 2.3 seconds
Tokens Used: 1,247
Confidence Score: 0.94""",
            "metadata": {
                "source_type": "analysis",
                "type": "consistency",
                "analyzer": "consistency-v2.1",
                "model": "gpt-4-turbo",
                "document_id": "github:hackathon-project:readme",
                "score": 0.92,
                "issues_found": 2,
                "processing_time": 2.3,
                "tokens_used": 1247,
                "confidence": 0.94
            }
        },
        {
            "id": "analysis:security:code:services/cli/main.py",
            "content": """Security Analysis Report
========================

Document: code:services/cli/main.py
Analyzed at: 2024-01-15T14:35:00Z
Analyzer: security-v1.8
Model: gpt-4-turbo

SUMMARY
-------
Security Score: 0.88 (Good)
Vulnerabilities: 1 medium, 0 high, 0 critical

VULNERABILITIES FOUND
--------------------

1. Path Traversal Risk (Medium)
   - Location: Line 12, sys.path manipulation
   - Issue: Using parent directory calculation for path insertion
   - Risk: Potential path traversal if directory structure changes
   - Recommendation: Use absolute paths or virtual environments
   - CVSS Score: 5.3

2. Exception Handling (Low)
   - Location: Lines 28-32, main() function
   - Issue: Generic exception handling prints sensitive error details
   - Recommendation: Log errors securely, don't expose to users
   - CVSS Score: 3.2

SECURITY RECOMMENDATIONS
-----------------------
1. Use absolute paths for sys.path modifications
2. Implement proper error handling without information disclosure
3. Add input validation for file paths
4. Consider using virtual environments

COMPLIANCE CHECKS
-----------------
✅ No hardcoded secrets detected
✅ Safe import practices
⚠️ Path manipulation requires review
✅ No SQL injection risks in this file""",
            "metadata": {
                "source_type": "analysis",
                "type": "security",
                "analyzer": "security-v1.8",
                "model": "gpt-4-turbo",
                "document_id": "code:services/cli/main.py",
                "score": 0.88,
                "vulnerabilities": {"medium": 1, "high": 0, "critical": 0},
                "cvss_score": 5.3,
                "compliance": {"secrets": True, "imports": True, "paths": False, "sql": True}
            }
        },
        {
            "id": "analysis:quality:confluence:page-789",
            "content": """Quality Analysis Report
========================

Document: confluence:page-789
Analyzed at: 2024-01-15T14:40:00Z
Analyzer: quality-v3.2
Model: gpt-4-turbo

QUALITY METRICS
---------------
Overall Quality Score: 0.95 (Excellent)
Readability: 0.97
Completeness: 0.93
Accuracy: 0.96
Consistency: 0.94

CONTENT ANALYSIS
----------------
Document Type: API Documentation
Language: English
Reading Level: Intermediate
Word Count: 1,247
Code Examples: 12
Sections: 8

STRENGTHS
---------
✅ Excellent readability and structure
✅ Comprehensive code examples
✅ Clear error handling documentation
✅ Good use of formatting and hierarchy

AREAS FOR IMPROVEMENT
---------------------
⚠️ Some code examples lack error handling
⚠️ Could benefit from more cross-references
⚠️ Authentication section could be more detailed

RECOMMENDATIONS
---------------
1. Add error handling examples to code samples
2. Include links to related documentation
3. Expand authentication section with more examples
4. Consider adding a troubleshooting section

TECHNICAL METRICS
-----------------
Analysis Time: 3.1 seconds
Content Freshness: Current
Cross-references: 85% complete""",
            "metadata": {
                "source_type": "analysis",
                "type": "quality",
                "analyzer": "quality-v3.2",
                "model": "gpt-4-turbo",
                "document_id": "confluence:page-789",
                "score": 0.95,
                "metrics": {
                    "readability": 0.97,
                    "completeness": 0.93,
                    "accuracy": 0.96,
                    "consistency": 0.94
                },
                "word_count": 1247,
                "code_examples": 12,
                "sections": 8
            }
        }
    ]


def create_ensemble_documents() -> List[Dict[str, Any]]:
    """Create test ensemble analysis documents."""
    return [
        {
            "id": "ensemble:readme-analysis-suite",
            "content": """Ensemble Analysis: README Quality Assessment
==============================================

Document: github:hackathon-project:readme
Analysis Type: Multi-analyzer ensemble
Completed: 2024-01-15T15:00:00Z

PARTICIPATING ANALYZERS
-----------------------
1. Consistency Analyzer v2.1 (GPT-4 Turbo)
2. Quality Analyzer v3.2 (GPT-4 Turbo)
3. Security Analyzer v1.8 (GPT-4 Turbo)
4. Style Analyzer v1.5 (Claude-3 Haiku)

ENSEMBLE RESULTS
----------------
Overall Confidence: 0.96
Agreement Level: High (85% consensus)
Processing Time: 8.7 seconds

KEY FINDINGS
------------
✅ Strong agreement on document quality (0.91-0.95 range)
✅ All analyzers confirm good structure and readability
⚠️ Minor disagreement on security concerns (2 analyzers vs 1)
✅ Consensus on terminology consistency needs

RECOMMENDED ACTIONS
------------------
1. High Priority: Implement consistency checks in CI/CD
2. Medium Priority: Review security recommendations
3. Low Priority: Consider style guide updates

ANALYZER BREAKDOWN
------------------
Consistency (v2.1): Score 0.92, Confidence 0.94
- Focus: Terminology, formatting consistency
- Key Issue: Mixed hyphenation in "microservices"

Quality (v3.2): Score 0.95, Confidence 0.97
- Focus: Readability, completeness, structure
- Strengths: Excellent documentation organization

Security (v1.8): Score 0.88, Confidence 0.91
- Focus: Information disclosure, secure practices
- Recommendations: Improve error handling

Style (v1.5): Score 0.93, Confidence 0.89
- Focus: Writing style, tone, clarity
- Strengths: Professional and accessible language""",
            "metadata": {
                "source_type": "ensemble",
                "type": "multi_analyzer",
                "document_id": "github:hackathon-project:readme",
                "analyzers": ["consistency-v2.1", "quality-v3.2", "security-v1.8", "style-v1.5"],
                "overall_score": 0.92,
                "confidence": 0.96,
                "agreement_level": "high",
                "processing_time": 8.7,
                "recommendations": ["consistency_checks", "security_review", "style_updates"]
            }
        }
    ]


def create_style_examples() -> List[Dict[str, Any]]:
    """Create test style examples."""
    return [
        {
            "id": "style:python:function_docstring",
            "content": """def calculate_metrics(data: List[Dict[str, Any]], config: AnalysisConfig) -> MetricsResult:
    \"\"\"Calculate comprehensive metrics for the given dataset.

    This function processes raw data through multiple analysis stages including
    statistical analysis, trend detection, and quality assessment. The results
    are normalized and validated before being returned.

    Args:
        data: Raw dataset to analyze. Each dict should contain measurement
            values and metadata.
        config: Analysis configuration specifying thresholds, algorithms,
            and output formats.

    Returns:
        MetricsResult containing calculated statistics, trends, and quality
        scores. All values are normalized to [0, 1] range.

    Raises:
        ValueError: If data is empty or config is invalid.
        AnalysisError: If analysis pipeline fails during processing.

    Example:
        >>> config = AnalysisConfig(threshold=0.8, algorithm='advanced')
        >>> data = [{'value': 0.95, 'timestamp': '2024-01-01'}]
        >>> result = calculate_metrics(data, config)
        >>> result.overall_score
        0.92

    Note:
        Processing time scales linearly with dataset size. For large datasets,
        consider using batch processing.
    \"\"\"
    if not data:
        raise ValueError("Data cannot be empty")
    if not config.is_valid():
        raise ValueError("Invalid configuration")

    # Implementation follows...
    pass""",
            "metadata": {
                "source_type": "style_example",
                "type": "python",
                "language": "python",
                "category": "documentation",
                "style_guide": "PEP 257",
                "complexity": "advanced",
                "tags": ["docstring", "type_hints", "examples", "error_handling"]
            }
        },
        {
            "id": "style:typescript:interface_design",
            "content": """/**
 * Configuration interface for analysis operations.
 *
 * This interface defines the contract for analysis configuration objects,
 * ensuring type safety and comprehensive documentation across the codebase.
 */
export interface AnalysisConfig {
  /** Unique identifier for this configuration */
  readonly id: string;

  /** Human-readable name for the configuration */
  readonly name: string;

  /** Algorithm to use for analysis */
  readonly algorithm: 'basic' | 'advanced' | 'experimental';

  /** Quality threshold for accepting results (0.0 to 1.0) */
  readonly threshold: number;

  /** Maximum processing time in milliseconds */
  readonly timeoutMs: number;

  /** Whether to enable debug logging */
  readonly debug: boolean;

  /** Custom options specific to the algorithm */
  readonly options?: Record<string, unknown>;

  /** Creation timestamp */
  readonly createdAt: Date;

  /** Last modification timestamp */
  readonly updatedAt: Date;
}

/**
 * Creates a new analysis configuration with validation.
 *
 * @param params - Configuration parameters
 * @returns Validated configuration object
 * @throws {ValidationError} If parameters are invalid
 *
 * @example
 * ```typescript
 * const config = createAnalysisConfig({
 *   name: 'Quality Analysis',
 *   algorithm: 'advanced',
 *   threshold: 0.85,
 *   timeoutMs: 30000
 * });
 * ```
 */
export function createAnalysisConfig(params: {
  name: string;
  algorithm: AnalysisConfig['algorithm'];
  threshold: number;
  timeoutMs: number;
  debug?: boolean;
  options?: Record<string, unknown>;
}): AnalysisConfig {
  // Validation logic...
  if (params.threshold < 0 || params.threshold > 1) {
    throw new ValidationError('Threshold must be between 0 and 1');
  }

  return {
    id: generateId(),
    name: params.name,
    algorithm: params.algorithm,
    threshold: params.threshold,
    timeoutMs: params.timeoutMs,
    debug: params.debug ?? false,
    options: params.options,
    createdAt: new Date(),
    updatedAt: new Date()
  };
}""",
            "metadata": {
                "source_type": "style_example",
                "type": "typescript",
                "language": "typescript",
                "category": "interfaces",
                "style_guide": "TypeScript Handbook",
                "complexity": "advanced",
                "tags": ["interfaces", "documentation", "validation", "type_safety"]
            }
        }
    ]


async def populate_docstore():
    """Populate the doc-store with comprehensive test data."""
    print("🌱 Populating Doc Store with comprehensive test data...")

    # For now, populate directly to SQLite database
    # This allows us to test the data without needing the service running
    import sqlite3
    import json
    import os
    from services.shared.utilities import stable_hash, utc_now

    # Get database path from config or default
    db_path = os.environ.get("DOCSTORE_DB", "services/doc-store/db.sqlite3")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")

    # Ensure tables exist
    conn.execute("""
        CREATE TABLE IF NOT EXISTS documents (
          id TEXT PRIMARY KEY,
          content TEXT,
          content_hash TEXT,
          metadata TEXT,
          created_at TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
          id TEXT PRIMARY KEY,
          document_id TEXT,
          analyzer TEXT,
          model TEXT,
          prompt_hash TEXT,
          result TEXT,
          score REAL,
          metadata TEXT,
          created_at TEXT,
          FOREIGN KEY(document_id) REFERENCES documents(id)
        )
    """)

    # Collect all test documents
    all_documents = []
    all_documents.extend(create_github_documents())
    all_documents.extend(create_jira_documents())
    all_documents.extend(create_confluence_documents())
    all_documents.extend(create_code_documents())
    all_documents.extend(create_api_docs())

    # Add analyses separately
    analyses = create_analysis_documents()
    ensembles = create_ensemble_documents()
    style_examples = create_style_examples()

    print(f"📄 Creating {len(all_documents)} documents, {len(analyses)} analyses, {len(ensembles)} ensembles, {len(style_examples)} style examples...")

    success_count = 0
    error_count = 0
    now = utc_now().isoformat()

    # Insert documents
    for doc in all_documents:
        try:
            content_hash = stable_hash(doc["content"])
            metadata_json = json.dumps(doc["metadata"])

            conn.execute("""
                INSERT OR REPLACE INTO documents (id, content, content_hash, metadata, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (doc["id"], doc["content"], content_hash, metadata_json, now))

            success_count += 1
            doc_type = doc["metadata"].get("type", "unknown")
            source_type = doc["metadata"].get("source_type", "unknown")
            print(f"  ✅ Created {source_type}:{doc_type} - {doc['id']}")

        except Exception as e:
            error_count += 1
            print(f"  ❌ Error creating document {doc['id']}: {e}")

    # Insert analyses
    for analysis in analyses:
        try:
            analysis_id = analysis["id"]
            doc_id = analysis["id"].split(":")[-1]  # Extract document ID from analysis ID
            analyzer = analysis["metadata"].get("analyzer", "unknown")
            model = analysis["metadata"].get("model", "unknown")
            score = analysis["metadata"].get("score", 0.0)
            metadata_json = json.dumps(analysis["metadata"])

            # Use content hash of analysis content as prompt_hash for simplicity
            prompt_hash = stable_hash(analysis["content"])[:16]

            conn.execute("""
                INSERT OR REPLACE INTO analyses (id, document_id, analyzer, model, prompt_hash, result, score, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (analysis_id, doc_id, analyzer, model, prompt_hash, analysis["content"], score, metadata_json, now))

            success_count += 1
            analysis_type = analysis["metadata"].get("type", "unknown")
            print(f"  ✅ Created analysis:{analysis_type} - {analysis_id}")

        except Exception as e:
            error_count += 1
            print(f"  ❌ Error creating analysis {analysis_id}: {e}")

    # Insert ensembles (as special documents)
    for ensemble in ensembles:
        try:
            content_hash = stable_hash(ensemble["content"])
            metadata_json = json.dumps(ensemble["metadata"])

            conn.execute("""
                INSERT OR REPLACE INTO documents (id, content, content_hash, metadata, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (ensemble["id"], ensemble["content"], content_hash, metadata_json, now))

            success_count += 1
            print(f"  ✅ Created ensemble - {ensemble['id']}")

        except Exception as e:
            error_count += 1
            print(f"  ❌ Error creating ensemble {ensemble['id']}: {e}")

    # Insert style examples (as special documents)
    for style in style_examples:
        try:
            content_hash = stable_hash(style["content"])
            metadata_json = json.dumps(style["metadata"])

            conn.execute("""
                INSERT OR REPLACE INTO documents (id, content, content_hash, metadata, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (style["id"], style["content"], content_hash, metadata_json, now))

            success_count += 1
            style_type = style["metadata"].get("type", "unknown")
            print(f"  ✅ Created style:{style_type} - {style['id']}")

        except Exception as e:
            error_count += 1
            print(f"  ❌ Error creating style example {style['id']}: {e}")

    conn.commit()
    conn.close()

    print("\n📊 Summary:")
    print(f"  ✅ Successful: {success_count}")
    print(f"  ❌ Failed: {error_count}")
    total_items = len(all_documents) + len(analyses) + len(ensembles) + len(style_examples)
    print(f"  📈 Success Rate: {(success_count / total_items) * 100:.1f}%")

    if success_count > 0:
        print("\n🎯 Test data ready! Database populated with:")
        print(f"  • {len(all_documents)} documents (GitHub, Jira, Confluence, Code, API)")
        print(f"  • {len(analyses)} analyses (consistency, security, quality)")
        print(f"  • {len(ensembles)} ensemble results")
        print(f"  • {len(style_examples)} style examples")
        print("\n🔧 Next steps:")
        print("  1. Run doc-store service: python3 services/doc-store/main.py")
        print("  2. Test via CLI: python3 run_cli.py → Document Store")
        print("  3. Verify operations: list, search, quality analysis, etc.")


if __name__ == "__main__":
    asyncio.run(populate_docstore())
