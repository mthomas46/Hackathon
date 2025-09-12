"""Documentation Fixtures - Specialized fixtures for documentation testing.

This module provides pytest fixtures for documentation data including Confluence
pages, GitHub wikis, and other documentation systems for comprehensive testing.
"""

import pytest
from typing import Dict, List, Any
from data.documentation import get_sample_confluence_pages, get_sample_github_wiki_pages


@pytest.fixture
def sample_confluence_page() -> Dict[str, Any]:
    """Sample Confluence page fixture."""
    pages = get_sample_confluence_pages()
    return pages[0] if pages else {
        "id": "page_123",
        "title": "API Documentation",
        "space": {"name": "Engineering", "key": "ENG"},
        "content": "<h1>API Documentation</h1><p>This is the API documentation.</p>",
        "author": {"displayName": "John Doe", "username": "john.doe"},
        "createdDate": "2024-01-01T10:00:00Z",
        "lastModified": "2024-01-15T10:00:00Z",
        "version": {"number": 5},
        "labels": ["api", "documentation"],
        "links": {"self": "https://company.atlassian.net/wiki/rest/api/content/123"}
    }


@pytest.fixture
def sample_github_wiki() -> Dict[str, Any]:
    """Sample GitHub wiki page fixture."""
    pages = get_sample_github_wiki_pages()
    return pages[0] if pages else {
        "title": "Home",
        "content": "# Welcome\n\nThis is the project documentation.\n\n## Getting Started\n\n1. Install dependencies\n2. Run the application",
        "author": {"login": "john-doe", "type": "User"},
        "last_updated": "2024-01-15T10:00:00Z",
        "file_path": "Home.md",
        "size": 256,
        "encoding": "utf-8"
    }


@pytest.fixture
def confluence_api_page() -> Dict[str, Any]:
    """Confluence page with API documentation."""
    return {
        "id": "page_api",
        "title": "REST API Reference",
        "space": {"name": "API Documentation", "key": "API"},
        "content": """
        <h1>REST API Reference</h1>

        <h2>Authentication</h2>
        <p>All API requests require JWT authentication.</p>

        <h3>GET /api/users</h3>
        <p>Retrieve list of users.</p>
        <strong>Response:</strong>
        <pre><code>HTTP 200 OK
        [{"id": 1, "name": "John Doe", "email": "john@example.com"}]</code></pre>

        <h3>POST /api/users</h3>
        <p>Create a new user.</p>
        <strong>Request:</strong>
        <pre><code>{"name": "Jane Doe", "email": "jane@example.com"}</code></pre>
        """,
        "author": {"displayName": "API Team", "username": "api-team"},
        "labels": ["api", "reference", "rest"],
        "permissions": ["view", "edit"],
        "ancestors": [{"title": "Developer Guide", "id": "page_parent"}]
    }


@pytest.fixture
def confluence_troubleshooting_page() -> Dict[str, Any]:
    """Confluence troubleshooting guide page."""
    return {
        "id": "page_troubleshoot",
        "title": "Troubleshooting Guide",
        "space": {"name": "Support", "key": "SUP"},
        "content": """
        <h1>Troubleshooting Guide</h1>

        <h2>Common Issues</h2>

        <h3>Application Won't Start</h3>
        <p><strong>Symptoms:</strong> Error on startup</p>
        <p><strong>Solution:</strong> Check database connection and environment variables</p>

        <h3>Slow Performance</h3>
        <p><strong>Symptoms:</strong> Pages load slowly</p>
        <p><strong>Solution:</strong> Clear cache and restart services</p>

        <h3>Authentication Errors</h3>
        <p><strong>Symptoms:</strong> Login failures</p>
        <p><strong>Solution:</strong> Verify credentials and token expiration</p>
        """,
        "author": {"displayName": "Support Team", "username": "support-team"},
        "labels": ["troubleshooting", "support", "faq"],
        "attachments": [
            {"filename": "error_logs.txt", "size": 2048},
            {"filename": "config_example.txt", "size": 1024}
        ]
    }


@pytest.fixture
def github_readme() -> Dict[str, Any]:
    """GitHub README.md fixture."""
    return {
        "title": "README",
        "content": """# My Awesome Project

A comprehensive solution for modern development challenges.

## Features

- 🚀 Fast and efficient
- 🔒 Secure by default
- 📊 Rich analytics
- 🎨 Beautiful UI

## Quick Start

```bash
# Clone the repository
git clone https://github.com/company/my-project.git

# Install dependencies
npm install

# Start development server
npm run dev
```

## Documentation

- [API Reference](docs/api.md)
- [User Guide](docs/user-guide.md)
- [Contributing](CONTRIBUTING.md)

## License

MIT © 2024 Company Name
""",
        "author": {"login": "project-owner", "type": "User"},
        "file_path": "README.md",
        "size": 2048,
        "lines": 35,
        "language": "Markdown"
    }


@pytest.fixture
def github_contributing_guide() -> Dict[str, Any]:
    """GitHub CONTRIBUTING.md fixture."""
    return {
        "title": "Contributing Guide",
        "content": """# Contributing to My Project

We welcome contributions! Please follow these guidelines.

## Development Setup

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/my-project.git`
3. Create a feature branch: `git checkout -b feature/your-feature`
4. Install dependencies: `npm install`

## Code Style

- Use ESLint and Prettier
- Follow conventional commits
- Write tests for new features
- Update documentation

## Pull Request Process

1. Ensure all tests pass
2. Update CHANGELOG.md
3. Request review from maintainers
4. Merge after approval

## Testing

```bash
# Run unit tests
npm test

# Run integration tests
npm run test:integration

# Run linting
npm run lint
```

Thank you for contributing! 🎉
""",
        "author": {"login": "maintainer", "type": "User"},
        "file_path": "CONTRIBUTING.md",
        "size": 1536,
        "lines": 42
    }


@pytest.fixture
def documentation_with_images() -> Dict[str, Any]:
    """Documentation with embedded images."""
    return {
        "id": "page_images",
        "title": "Architecture Overview",
        "type": "confluence",
        "content": """
        <h1>System Architecture</h1>

        <h2>High-Level Overview</h2>
        <p>The system consists of three main components:</p>

        <h3>Frontend Layer</h3>
        <p><ac:image ac:alt="Frontend Architecture"><ri:attachment ri:filename="frontend-arch.png" /></ac:image></p>

        <h3>Backend Services</h3>
        <p><ac:image ac:alt="Backend Services"><ri:attachment ri:filename="backend-services.png" /></ac:image></p>

        <h3>Data Layer</h3>
        <p><ac:image ac:alt="Database Schema"><ri:attachment ri:filename="database-schema.png" /></ac:image></p>
        """,
        "attachments": [
            {"filename": "frontend-arch.png", "size": 102400, "type": "image/png"},
            {"filename": "backend-services.png", "size": 153600, "type": "image/png"},
            {"filename": "database-schema.png", "size": 204800, "type": "image/png"}
        ]
    }


@pytest.fixture
def documentation_with_code() -> Dict[str, Any]:
    """Documentation with code examples."""
    return {
        "id": "page_code",
        "title": "Code Examples",
        "type": "github",
        "content": """# Code Examples

## Python Example

```python
from myproject import Client

# Initialize client
client = Client(api_key="your-api-key")

# Make a request
response = client.get_users()
print(f"Found {len(response['users'])} users")
```

## JavaScript Example

```javascript
import { Client } from 'myproject';

const client = new Client({
  apiKey: 'your-api-key'
});

client.getUsers()
  .then(response => {
    console.log(`Found ${response.users.length} users`);
  })
  .catch(error => {
    console.error('Error:', error);
  });
```

## Error Handling

```python
try:
    result = client.process_data(data)
except ValidationError as e:
    print(f"Validation failed: {e}")
except ConnectionError as e:
    print(f"Connection failed: {e}")
```
""",
        "language": "Markdown",
        "code_blocks": 3,
        "examples": ["python", "javascript", "error-handling"]
    }


@pytest.fixture
def documentation_search_results() -> List[Dict[str, Any]]:
    """Mock search results for documentation."""
    return [
        {
            "id": "page_1",
            "title": "Getting Started Guide",
            "excerpt": "...Welcome to our platform. Getting started is easy...",
            "relevance_score": 0.95,
            "last_modified": "2024-01-15T10:00:00Z"
        },
        {
            "id": "page_2",
            "title": "API Authentication",
            "excerpt": "...Use JWT tokens for authentication. Here's how...",
            "relevance_score": 0.87,
            "last_modified": "2024-01-10T14:30:00Z"
        },
        {
            "id": "page_3",
            "title": "Troubleshooting Database Issues",
            "excerpt": "...Common database connection problems and solutions...",
            "relevance_score": 0.76,
            "last_modified": "2024-01-12T09:15:00Z"
        }
    ]


@pytest.fixture
def documentation_metrics() -> Dict[str, Any]:
    """Documentation usage and quality metrics."""
    return {
        "total_pages": 245,
        "active_contributors": 12,
        "views_last_month": 15420,
        "avg_page_age_days": 89,
        "outdated_pages": 15,
        "pages_needing_review": 8,
        "search_success_rate": 0.78,
        "popular_topics": [
            {"topic": "API", "pages": 45, "views": 5200},
            {"topic": "Authentication", "pages": 23, "views": 3800},
            {"topic": "Database", "pages": 18, "views": 2900}
        ],
        "quality_score": 0.85,
        "coverage_score": 0.92
    }


@pytest.fixture
def documentation_templates() -> Dict[str, List[Dict[str, Any]]]:
    """Documentation templates by type."""
    return {
        "api_docs": [confluence_api_page()],
        "guides": [confluence_troubleshooting_page()],
        "readme": [github_readme()],
        "contributing": [github_contributing_guide()],
        "architecture": [documentation_with_images()]
    }
