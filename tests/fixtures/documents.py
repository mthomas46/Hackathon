"""
Document fixtures for testing.

Provides mock documents from various sources with realistic content.
"""
from datetime import datetime
from typing import Dict, Any, List
from ingestion.models import NormalizedDocument


def create_mock_document(
    document_id: str = "test-doc-001",
    title: str = "Test Document",
    content: str = "This is test content.",
    source: str = "test",
    tags: List[str] = None,
    metadata: Dict[str, Any] = None
) -> NormalizedDocument:
    """
    Create a generic mock document.
    
    Args:
        document_id: Document identifier
        title: Document title
        content: Document content (markdown)
        source: Source type
        tags: List of tags
        metadata: Additional metadata
    
    Returns:
        NormalizedDocument instance
    """
    return NormalizedDocument(
        document_id=document_id,
        title=title,
        content_md=content,
        original_format=source,
        tags=tags or ["source:test", "file_type:document"],
        metadata=metadata or {"file_type": "document", "source": source}
    )


def create_github_commit_doc(
    commit_hash: str = "abc123def",
    author: str = "John Doe",
    message: str = "feat: Add new feature",
    files_changed: List[str] = None
) -> NormalizedDocument:
    """Create a mock GitHub commit document."""
    content = f"""# Commit: {commit_hash[:7]}

**Author**: {author}
**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Message

{message}

## Files Changed

{chr(10).join(f'- {f}' for f in (files_changed or ['src/main.py', 'tests/test_main.py']))}
"""
    
    return NormalizedDocument(
        document_id=f"github-commit-{commit_hash}",
        title=message,
        content_md=content,
        original_format="github_commit",
        tags=[
            "source:github",
            "file_type:commit",
            f"author:{author.lower().replace(' ', '-')}",
            "has_code_changes"
        ],
        metadata={
            "file_type": "commit",
            "source": "github",
            "commit_hash": commit_hash,
            "author": author,
            "files_changed": files_changed or ["src/main.py", "tests/test_main.py"],
            "created_at": datetime.now().isoformat(),
            "repository": "test-repo"
        }
    )


def create_jira_ticket_doc(
    ticket_id: str = "PROJ-123",
    title: str = "Implement user authentication",
    status: str = "In Progress",
    assignee: str = "Jane Smith",
    priority: str = "High"
) -> NormalizedDocument:
    """Create a mock Jira ticket document."""
    content = f"""# {ticket_id}: {title}

**Status**: {status}
**Assignee**: {assignee}
**Priority**: {priority}

## Description

This ticket tracks the implementation of user authentication features including:
- Login/logout functionality
- Password reset
- Session management
- JWT token handling

## Acceptance Criteria

- [ ] Users can log in with email/password
- [ ] Sessions persist across page refreshes
- [ ] Password reset emails are sent
- [ ] JWT tokens expire after 24 hours
"""
    
    return NormalizedDocument(
        document_id=f"jira-{ticket_id.lower()}",
        title=f"{ticket_id}: {title}",
        content_md=content,
        original_format="jira_ticket",
        tags=[
            "source:jira",
            "file_type:ticket",
            f"status:{status.lower().replace(' ', '-')}",
            f"assignee:{assignee.lower().replace(' ', '-')}",
            f"priority:{priority.lower()}"
        ],
        metadata={
            "file_type": "ticket",
            "source": "jira",
            "ticket_id": ticket_id,
            "status": status,
            "assignee": assignee,
            "priority": priority,
            "created_at": datetime.now().isoformat(),
            "project": "PROJ"
        }
    )


def create_wikipedia_doc(
    title: str = "Artificial Intelligence",
    page_id: str = "12345",
    categories: List[str] = None
) -> NormalizedDocument:
    """Create a mock Wikipedia document."""
    content = f"""# {title}

**Artificial intelligence** (AI) is intelligence demonstrated by machines, in contrast to the natural intelligence displayed by humans and animals. Leading AI textbooks define the field as the study of "intelligent agents": any device that perceives its environment and takes actions that maximize its chance of successfully achieving its goals.

## History

The field of AI research was born at a workshop at Dartmouth College in 1956. The attendees became the founders and leaders of AI research. They and their students produced programs that the press described as "astonishing": computers were learning checkers strategies, solving word problems in algebra, proving logical theorems and speaking English.

## Applications

AI applications include:
- Advanced web search engines
- Recommendation systems
- Understanding human speech
- Self-driving cars
- Automated decision-making
- Competing at the highest level in strategic game systems

## See Also

- Machine Learning
- Deep Learning
- Neural Networks
"""
    
    return NormalizedDocument(
        document_id=f"wikipedia-{page_id}",
        title=title,
        content_md=content,
        original_format="wikipedia",
        tags=[
            "source:wikipedia",
            "file_type:document",
            "has_references",
        ] + [f"category:{cat.lower().replace(' ', '-')}" for cat in (categories or ["Technology", "Computer Science"])],
        metadata={
            "file_type": "document",
            "source": "wikipedia",
            "page_id": page_id,
            "categories": categories or ["Technology", "Computer Science"],
            "url": f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
            "last_modified": datetime.now().isoformat()
        }
    )


def create_confluence_doc(
    space: str = "TECH",
    page_id: str = "67890",
    title: str = "System Architecture",
    author: str = "Tech Team"
) -> NormalizedDocument:
    """Create a mock Confluence document."""
    content = f"""# {title}

**Space**: {space}
**Author**: {author}
**Last Updated**: {datetime.now().strftime('%Y-%m-%d')}

## Overview

This document describes the high-level architecture of our system, including:
- Service components
- Data flow
- Integration points
- Security considerations

## Architecture Diagram

```
[Client] --> [API Gateway] --> [Microservices]
                                  |
                              [Database]
```

## Components

### API Gateway
Handles incoming requests, authentication, and routing.

### Microservices
- User Service
- Order Service
- Inventory Service
- Notification Service

### Database
PostgreSQL cluster with read replicas.
"""
    
    return NormalizedDocument(
        document_id=f"confluence-{space.lower()}-{page_id}",
        title=title,
        content_md=content,
        original_format="confluence",
        tags=[
            "source:confluence",
            "file_type:document",
            f"space:{space.lower()}",
            f"author:{author.lower().replace(' ', '-')}",
            "has_diagrams"
        ],
        metadata={
            "file_type": "document",
            "source": "confluence",
            "space": space,
            "page_id": page_id,
            "author": author,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    )


def create_code_file_doc(
    filename: str = "main.py",
    language: str = "python",
    functions: List[str] = None
) -> NormalizedDocument:
    """Create a mock code file document."""
    content = f"""# Code File: {filename}

**Language**: {language}
**Type**: Source Code

## Functions

{chr(10).join(f'### {func}()' + chr(10) + 'Function implementation details...' + chr(10) for func in (functions or ['main', 'process_data', 'validate_input']))}

## Code

```{language}
def main():
    '''Main entry point.'''
    data = process_data()
    if validate_input(data):
        return data
    return None

def process_data():
    '''Process data.'''
    return {{'status': 'success'}}

def validate_input(data):
    '''Validate input data.'''
    return data is not None
```
"""
    
    return NormalizedDocument(
        document_id=f"code-{filename.replace('.', '-')}",
        title=f"Code: {filename}",
        content_md=content,
        original_format="code_file",
        tags=[
            "source:local",
            "file_type:code",
            f"language:{language}",
            "has_functions",
            "analyzed"
        ],
        metadata={
            "file_type": "code",
            "source": "local",
            "filename": filename,
            "language": language,
            "functions": functions or ["main", "process_data", "validate_input"],
            "lines_of_code": 15,
            "analyzed_at": datetime.now().isoformat()
        }
    )


# Sample document collections for testing
SAMPLE_DOCUMENTS = {
    'github': [
        create_github_commit_doc("abc123", "Alice", "feat: Add authentication"),
        create_github_commit_doc("def456", "Bob", "fix: Resolve login bug"),
        create_github_commit_doc("ghi789", "Charlie", "docs: Update README"),
    ],
    'jira': [
        create_jira_ticket_doc("PROJ-101", "User Authentication", "Done"),
        create_jira_ticket_doc("PROJ-102", "API Rate Limiting", "In Progress"),
        create_jira_ticket_doc("PROJ-103", "Database Migration", "To Do"),
    ],
    'wikipedia': [
        create_wikipedia_doc("Artificial Intelligence"),
        create_wikipedia_doc("Machine Learning", "23456"),
        create_wikipedia_doc("Neural Network", "34567"),
    ],
    'confluence': [
        create_confluence_doc("TECH", "100", "System Architecture"),
        create_confluence_doc("TECH", "101", "API Documentation"),
        create_confluence_doc("PROD", "200", "Deployment Guide"),
    ],
    'code': [
        create_code_file_doc("main.py", "python"),
        create_code_file_doc("server.js", "javascript", ["startServer", "handleRequest"]),
        create_code_file_doc("utils.ts", "typescript", ["formatDate", "validateEmail"]),
    ]
}

