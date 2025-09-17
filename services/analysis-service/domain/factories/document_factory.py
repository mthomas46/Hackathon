"""Document factory for creating documents from various sources."""

from datetime import datetime
from typing import Optional, Dict, Any, List

from ..entities import Document, DocumentId, Content, Metadata
from ..services import DocumentService


class DocumentFactory:
    """Factory for creating Document entities from various sources."""

    def __init__(self, document_service: Optional[DocumentService] = None):
        """Initialize factory with optional document service."""
        self.document_service = document_service or DocumentService()

    def create_from_text(self, title: str, text: str,
                        content_format: str = "markdown",
                        author: Optional[str] = None,
                        tags: Optional[List[str]] = None,
                        repository_id: Optional[str] = None,
                        metadata: Optional[Dict[str, Any]] = None) -> Document:
        """Create document from plain text."""
        return self.document_service.create_document(
            title=title,
            content_text=text,
            content_format=content_format,
            author=author,
            tags=tags,
            repository_id=repository_id
        )

    def create_from_markdown_file(self, file_path: str,
                                 title: Optional[str] = None,
                                 author: Optional[str] = None,
                                 tags: Optional[List[str]] = None,
                                 repository_id: Optional[str] = None) -> Document:
        """Create document from markdown file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract title from first heading if not provided
            if not title:
                lines = content.split('\n')
                for line in lines[:10]:  # Check first 10 lines
                    if line.strip().startswith('# '):
                        title = line.strip()[2:].strip()
                        break
                if not title:
                    title = f"Document from {file_path.split('/')[-1]}"

            return self.create_from_text(
                title=title,
                text=content,
                content_format="markdown",
                author=author,
                tags=tags,
                repository_id=repository_id,
                metadata={"source_file": file_path}
            )

        except FileNotFoundError:
            raise ValueError(f"File not found: {file_path}")
        except Exception as e:
            raise ValueError(f"Error reading file {file_path}: {str(e)}")

    def create_from_json(self, json_data: Dict[str, Any]) -> Document:
        """Create document from JSON data structure."""
        required_fields = ['title', 'content']
        for field in required_fields:
            if field not in json_data:
                raise ValueError(f"Missing required field: {field}")

        # Handle different content formats
        content = json_data['content']
        if isinstance(content, dict):
            text = content.get('text', '')
            content_format = content.get('format', 'markdown')
        else:
            text = str(content)
            content_format = json_data.get('format', 'markdown')

        return self.create_from_text(
            title=json_data['title'],
            text=text,
            content_format=content_format,
            author=json_data.get('author'),
            tags=json_data.get('tags', []),
            repository_id=json_data.get('repository_id'),
            metadata=json_data.get('metadata', {})
        )

    def create_from_api_request(self, request_data: Dict[str, Any]) -> Document:
        """Create document from API request data."""
        return self.create_from_json(request_data)

    def create_from_repository_commit(self, repository_id: str,
                                    commit_data: Dict[str, Any],
                                    file_path: str) -> Document:
        """Create document from repository commit data."""
        # This would be used when integrating with version control systems
        title = commit_data.get('title', f"Commit: {commit_data.get('hash', 'unknown')[:8]}")

        # Extract content from commit
        content = commit_data.get('content', '')
        if not content and 'files' in commit_data:
            # Find the specific file in the commit
            for file_info in commit_data['files']:
                if file_info.get('path') == file_path:
                    content = file_info.get('content', '')
                    break

        if not content:
            raise ValueError(f"No content found for file {file_path} in commit")

        metadata = {
            'source_type': 'repository_commit',
            'commit_hash': commit_data.get('hash'),
            'author': commit_data.get('author'),
            'timestamp': commit_data.get('timestamp'),
            'file_path': file_path
        }

        return self.create_from_text(
            title=title,
            text=content,
            content_format="markdown",  # Assume markdown for now
            author=commit_data.get('author'),
            tags=['repository', 'commit'],
            repository_id=repository_id,
            metadata=metadata
        )

    def create_empty_document(self, title: str = "Empty Document") -> Document:
        """Create an empty document for later population."""
        return self.create_from_text(
            title=title,
            text="",
            content_format="markdown"
        )

    def create_document_from_template(self, template_name: str,
                                    parameters: Dict[str, Any]) -> Document:
        """Create document from predefined template."""
        templates = {
            'readme': self._create_readme_template,
            'api_docs': self._create_api_docs_template,
            'architecture': self._create_architecture_template,
            'changelog': self._create_changelog_template
        }

        if template_name not in templates:
            raise ValueError(f"Unknown template: {template_name}")

        return templates[template_name](parameters)

    def _create_readme_template(self, params: Dict[str, Any]) -> Document:
        """Create README template document."""
        title = params.get('title', 'README')
        project_name = params.get('project_name', 'Project')
        description = params.get('description', 'Project description')

        content = f"""# {project_name}

{description}

## Features

- Feature 1
- Feature 2
- Feature 3

## Installation

```bash
# Installation instructions
```

## Usage

```bash
# Usage instructions
```

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
"""

        return self.create_from_text(
            title=title,
            text=content,
            content_format="markdown",
            tags=['readme', 'documentation', 'template']
        )

    def _create_api_docs_template(self, params: Dict[str, Any]) -> Document:
        """Create API documentation template."""
        title = params.get('title', 'API Documentation')
        api_name = params.get('api_name', 'API')
        version = params.get('version', '1.0.0')

        content = f"""# {api_name} API Documentation

Version: {version}

## Overview

This document provides comprehensive documentation for the {api_name} API.

## Authentication

Describe authentication methods here.

## Endpoints

### GET /api/v1/resource

Retrieve a list of resources.

**Parameters:**
- None

**Response:**
```json
{{
  "data": [],
  "meta": {{
    "total": 0,
    "page": 1
  }}
}}
```

### POST /api/v1/resource

Create a new resource.

**Parameters:**
```json
{{
  "name": "string",
  "description": "string"
}}
```

**Response:**
```json
{{
  "id": "string",
  "name": "string",
  "description": "string",
  "created_at": "2023-01-01T00:00:00Z"
}}
```

## Error Handling

The API uses standard HTTP status codes and returns error details in the following format:

```json
{{
  "error": {{
    "code": "ERROR_CODE",
    "message": "Error description",
    "details": {{}}
  }}
}}
```
"""

        return self.create_from_text(
            title=title,
            text=content,
            content_format="markdown",
            tags=['api', 'documentation', 'template']
        )

    def _create_architecture_template(self, params: Dict[str, Any]) -> Document:
        """Create architecture documentation template."""
        title = params.get('title', 'Architecture Documentation')
        system_name = params.get('system_name', 'System')

        content = f"""# {system_name} Architecture

## Overview

High-level overview of the system architecture.

## System Context

```mermaid
graph TD
    A[User] --> B[{system_name}]
    B --> C[External System 1]
    B --> D[External System 2]
    B --> E[Database]
```

## Components

### Core Components

1. **Component 1**
   - Responsibility: Description
   - Technologies: Tech stack
   - Dependencies: List of dependencies

2. **Component 2**
   - Responsibility: Description
   - Technologies: Tech stack
   - Dependencies: List of dependencies

### Infrastructure

- **Load Balancer**: Distribution strategy
- **Database**: Database technology and schema
- **Cache**: Caching strategy and technology
- **Message Queue**: Async processing and decoupling

## Data Flow

Describe how data flows through the system.

## Security Considerations

- Authentication and authorization
- Data encryption
- API security
- Infrastructure security

## Performance Characteristics

- Expected throughput
- Latency requirements
- Scalability considerations
- Monitoring and alerting

## Deployment

### Environment Requirements

- Minimum hardware requirements
- Software dependencies
- Network requirements

### Deployment Process

1. Build artifacts
2. Deploy to staging
3. Run integration tests
4. Deploy to production
5. Post-deployment verification
"""

        return self.create_from_text(
            title=title,
            text=content,
            content_format="markdown",
            tags=['architecture', 'documentation', 'template']
        )

    def _create_changelog_template(self, params: Dict[str, Any]) -> Document:
        """Create changelog template."""
        title = params.get('title', 'CHANGELOG')
        version = params.get('version', '1.0.0')

        content = f"""# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [{version}] - {datetime.now().strftime('%Y-%m-%d')}

### Added
- New feature description
- Another new feature

### Changed
- Modified existing feature
- Updated configuration

### Deprecated
- Feature that will be removed in future version

### Removed
- Removed feature

### Fixed
- Bug fix description
- Another bug fix

### Security
- Security improvement or fix

## [0.1.0] - 2023-01-01

### Added
- Initial release
- Basic functionality
"""

        return self.create_from_text(
            title=title,
            text=content,
            content_format="markdown",
            tags=['changelog', 'documentation', 'template']
        )
