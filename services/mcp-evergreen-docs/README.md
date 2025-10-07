---
llm_metadata:
  document_type: reference
  content_focus: operational
  platform:
    primary: mcp
  status: active
  created_date: '2025-10-07'
  last_modified: '2025-10-07'
  topics:
  - documentation
  - content_management
  - knowledge_base
  - documentation_automation
  - content_synchronization
  concepts: []
  technologies:
  - python
  - markdown
  - git
  - sqlite
  - redis
  semantic_summary: Reference documentation for the MCP Evergreen Docs service providing automated documentation maintenance, synchronization, and knowledge base management
  archive_reason: n/a
  historical_value: current
  reference_value: high
semantic_embedding:
  model: text-embedding-ada-002
  embedding_date: '2025-10-07'
  embedding_checksum: pending
rag_metadata:
  chunk_strategy: semantic
  optimal_chunk_size: 512
  retrieval_priority: high
---

# 🌿 MCP Evergreen Docs Service

**Port: 8017** | **Purpose: Automated Documentation Maintenance & Knowledge Base Management**

The MCP Evergreen Docs Service provides intelligent documentation lifecycle management, ensuring that all technical documentation remains current, accurate, and synchronized across the Model Context Protocol ecosystem.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Doc Sources    │    │ MCP Evergreen   │    │  Knowledge      │
│                 │◄──►│   Docs Service  │◄──►│   Base          │
│ • Code Comments │    │   (Port 8017)   │    │                 │
│ • API Specs     │    │                 │    │ • Indexed Docs  │
│ • Config Files  │    │ • Auto-Update   │    │ • Searchable    │
│ • Test Cases    │    │ • Validation    │    │ • Versioned     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                       ▲                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Sync Engine   │    │  Validation     │    │   Publishing    │
│                 │    │   Pipeline      │    │   System        │
│ • Git Sync      │    │                 │    │                 │
│ • Webhook Int   │    │ • Accuracy Chk  │    │ • Multi-format  │
│ • Conflict Res  │    │ • Completeness  │    │ • Distribution  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Core Features

### 📝 Automated Documentation Updates
- **Code-to-Docs Sync**: Automatic documentation generation from code comments
- **API Documentation**: Real-time API spec synchronization
- **Configuration Tracking**: Automated config file documentation
- **Cross-Reference Updates**: Intelligent link maintenance and validation

### ✅ Documentation Validation
- **Accuracy Checking**: Automated validation against actual implementations
- **Completeness Analysis**: Gap identification in documentation coverage
- **Consistency Verification**: Cross-document reference validation
- **Freshness Monitoring**: Outdated documentation detection

### 🔄 Synchronization Engine
- **Multi-Source Sync**: Synchronize docs across repositories and platforms
- **Conflict Resolution**: Intelligent merge conflict handling
- **Version Control Integration**: Git-based documentation versioning
- **Webhook Automation**: Event-driven documentation updates

### 📚 Knowledge Base Management
- **Content Indexing**: Full-text search and semantic indexing
- **Relationship Mapping**: Document dependency and reference tracking
- **Content Classification**: Automatic categorization and tagging
- **Access Control**: Role-based documentation access management

## 📋 Documentation Lifecycle

### 1. Discovery Phase
- **Source Identification**: Locate documentation sources across the ecosystem
- **Content Extraction**: Parse and extract documentation from various formats
- **Metadata Collection**: Gather context and relationship information
- **Initial Indexing**: Create searchable content index

### 2. Validation Phase
- **Accuracy Verification**: Cross-reference with actual implementations
- **Completeness Assessment**: Identify missing or incomplete documentation
- **Consistency Checking**: Ensure terminology and format consistency
- **Freshness Analysis**: Detect outdated or stale content

### 3. Update Phase
- **Automated Updates**: Apply changes based on code and config changes
- **Manual Review Queue**: Flag changes requiring human review
- **Version Control**: Track all documentation changes with audit trail
- **Notification System**: Alert stakeholders of important updates

### 4. Publishing Phase
- **Format Conversion**: Generate multiple output formats (HTML, PDF, etc.)
- **Distribution**: Publish to configured destinations and platforms
- **Access Control**: Apply appropriate permissions and restrictions
- **Analytics Tracking**: Monitor documentation usage and effectiveness

## 🛠️ API Endpoints

### Documentation Management
```bash
# Sync documentation from sources
POST /api/v1/docs/sync
{
  "sources": [
    {
      "type": "git",
      "url": "https://github.com/org/repo",
      "paths": ["docs/", "README.md"]
    }
  ],
  "options": {
    "validate": true,
    "update_links": true,
    "create_missing": false
  }
}

# Validate documentation accuracy
POST /api/v1/docs/validate
{
  "scope": "all",
  "checks": ["accuracy", "completeness", "consistency"],
  "report_format": "detailed"
}

# Update specific documentation
PUT /api/v1/docs/{doc_id}
{
  "content": "# Updated Documentation\n\nNew content here...",
  "metadata": {
    "last_updated": "2025-10-07T15:30:00Z",
    "updated_by": "mcp-evergreen-docs",
    "change_reason": "automated_sync"
  }
}
```

### Content Search & Retrieval
```bash
# Search documentation
GET /api/v1/docs/search?q=microservices&category=api&limit=10

# Get document by ID
GET /api/v1/docs/{doc_id}

# Get document relationships
GET /api/v1/docs/{doc_id}/relationships

# Get documentation index
GET /api/v1/docs/index?category=architecture
```

### Validation & Analytics
```bash
# Get validation report
GET /api/v1/validation/report?scope=week&type=accuracy

# Get documentation metrics
GET /api/v1/analytics/docs?metric=coverage&time_range=month

# Get outdated documentation
GET /api/v1/docs/outdated?threshold_days=30

# Get documentation health score
GET /api/v1/health/docs
```

## ⚙️ Configuration

### Environment Variables
```bash
# Service Configuration
MCP_EVERGREEN_DOCS_PORT=8017
MCP_EVERGREEN_DOCS_HOST=0.0.0.0

# Storage Configuration
DATABASE_URL=sqlite:///evergreen_docs.db
REDIS_URL=redis://localhost:6379
GIT_CACHE_DIR=/tmp/git_cache

# Source Configuration
GITHUB_TOKEN=your-github-token
GITLAB_TOKEN=your-gitlab-token
SYNC_INTERVAL_MINUTES=60

# Validation Configuration
VALIDATION_STRICT_MODE=true
AUTO_UPDATE_ENABLED=true
NOTIFICATION_WEBHOOK_URL=https://hooks.slack.com/...
```

### Source Configuration
```yaml
# sources.yaml
sources:
  - name: "mcp-core"
    type: "git"
    url: "https://github.com/modelcontextprotocol/core"
    branches: ["main", "develop"]
    paths:
      - "docs/"
      - "README.md"
      - "api/"
    update_strategy: "auto"

  - name: "mcp-gateway"
    type: "api"
    url: "http://localhost:8014/docs"
    format: "openapi"
    update_strategy: "scheduled"

  - name: "service-configs"
    type: "filesystem"
    path: "/etc/mcp/services/"
    pattern: "*.yaml"
    update_strategy: "watch"
```

### Docker Deployment
```yaml
version: '3.8'
services:
  mcp-evergreen-docs:
    image: mcp-evergreen-docs:latest
    ports:
      - "8017:8017"
    environment:
      - DATABASE_URL=sqlite:///data/evergreen_docs.db
      - REDIS_URL=redis://redis:6379
      - GITHUB_TOKEN=${GITHUB_TOKEN}
    volumes:
      - ./sources.yaml:/app/config/sources.yaml
      - ./data:/app/data
      - ./git-cache:/tmp/git_cache
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

## 🔄 Synchronization Capabilities

### Git Integration
- **Repository Monitoring**: Track changes across multiple repositories
- **Branch Management**: Handle different branches and release versions
- **Conflict Resolution**: Intelligent merge conflict handling for docs
- **Commit Tracking**: Link documentation changes to code commits

### API Synchronization
- **OpenAPI Specs**: Automatic API documentation from OpenAPI/Swagger
- **Service Discovery**: Auto-discovery of running services and their APIs
- **Health Checks**: Validate API documentation against live services
- **Version Tracking**: Track API changes and documentation updates

### Filesystem Monitoring
- **File Watching**: Real-time monitoring of configuration and doc files
- **Change Detection**: Identify and process file modifications
- **Backup Integration**: Coordinate with backup systems for data safety
- **Permission Handling**: Respect file permissions and access controls

## ✅ Validation Engine

### Accuracy Validation
- **Code Reference Checking**: Verify code examples are current
- **API Endpoint Validation**: Confirm documented endpoints exist
- **Configuration Verification**: Validate config examples against schemas
- **Link Integrity**: Check all cross-references are valid

### Completeness Analysis
- **Coverage Metrics**: Calculate documentation coverage by component
- **Gap Identification**: Find undocumented features and APIs
- **Template Matching**: Compare against documentation standards
- **Dependency Tracking**: Ensure all dependencies are documented

### Consistency Checking
- **Terminology Standardization**: Verify consistent use of terms
- **Format Compliance**: Check adherence to documentation standards
- **Style Consistency**: Maintain consistent formatting and structure
- **Template Usage**: Ensure proper use of documentation templates

## 📊 Analytics & Reporting

### Documentation Metrics
- **Coverage Statistics**: Documentation completeness by category
- **Update Frequency**: How often documentation is updated
- **Usage Analytics**: Which documentation is most accessed
- **Quality Scores**: Automated quality assessment

### Validation Reports
- **Accuracy Reports**: Detailed accuracy validation results
- **Completeness Reports**: Gap analysis and coverage statistics
- **Consistency Reports**: Style and terminology issues
- **Trend Analysis**: Documentation quality over time

## 🔧 Troubleshooting

### Common Issues

#### Synchronization Failures
```bash
# Check source connectivity
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/repos/org/repo

# Verify Git credentials
git ls-remote https://github.com/org/repo.git

# Check service logs
docker logs mcp-evergreen-docs | grep "sync"
```

#### Validation Errors
```bash
# Run manual validation
curl -X POST http://localhost:8017/api/v1/docs/validate \
  -H "Content-Type: application/json" \
  -d '{"scope": "all", "checks": ["accuracy"]}'

# Check validation logs
docker logs mcp-evergreen-docs | grep "validation"

# Review error details
curl http://localhost:8017/api/v1/validation/report?type=accuracy
```

#### Search Issues
```bash
# Rebuild search index
curl -X POST http://localhost:8017/api/v1/search/rebuild

# Check index status
curl http://localhost:8017/api/v1/search/status

# Verify content ingestion
curl http://localhost:8017/api/v1/docs/search?q=test
```

## 🔗 Integration Examples

### Automated Documentation Updates
```python
import requests
from pathlib import Path

class DocsUpdater:
    def __init__(self, service_url="http://localhost:8017"):
        self.service_url = service_url

    def sync_from_git(self, repo_url, paths=None):
        """Sync documentation from a Git repository."""
        payload = {
            "sources": [{
                "type": "git",
                "url": repo_url,
                "paths": paths or ["docs/", "README.md"]
            }],
            "options": {
                "validate": True,
                "update_links": True
            }
        }

        response = requests.post(f"{self.service_url}/api/v1/docs/sync", json=payload)
        return response.json()

    def validate_docs(self, scope="all"):
        """Validate documentation accuracy."""
        payload = {
            "scope": scope,
            "checks": ["accuracy", "completeness", "consistency"],
            "report_format": "detailed"
        }

        response = requests.post(f"{self.service_url}/api/v1/docs/validate", json=payload)
        return response.json()

# Usage
updater = DocsUpdater()
result = updater.sync_from_git("https://github.com/org/mcp-service")
validation = updater.validate_docs()
```

### Content Search Integration
```python
import requests

class DocsSearch:
    def __init__(self, service_url="http://localhost:8017"):
        self.service_url = service_url

    def search_docs(self, query, category=None, limit=10):
        """Search documentation with semantic matching."""
        params = {
            "q": query,
            "limit": limit
        }
        if category:
            params["category"] = category

        response = requests.get(f"{self.service_url}/api/v1/docs/search", params=params)
        return response.json()

    def get_related_docs(self, doc_id):
        """Get documents related to a specific document."""
        response = requests.get(f"{self.service_url}/api/v1/docs/{doc_id}/relationships")
        return response.json()

# Usage
search = DocsSearch()
results = search.search_docs("authentication", category="security")
related = search.get_related_docs("api-auth-guide")
```

## 📚 Dependencies

- **Python 3.9+**
- **GitPython**: Git repository integration
- **SQLAlchemy**: Database ORM for metadata storage
- **Redis**: Caching and queue management
- **FastAPI**: Web API framework
- **Markdown**: Documentation parsing and processing
- **PyGitHub**: GitHub API integration (optional)

## 🚀 Getting Started

1. **Configure sources**
   ```yaml
   # Create sources.yaml
   sources:
     - name: "mcp-core"
       type: "git"
       url: "https://github.com/your-org/mcp-core"
       paths: ["docs/", "README.md"]
   ```

2. **Set environment variables**
   ```bash
   export MCP_EVERGREEN_DOCS_PORT=8017
   export DATABASE_URL=sqlite:///evergreen_docs.db
   export GITHUB_TOKEN=your_github_token
   ```

3. **Run the service**
   ```bash
   cd services/mcp-evergreen-docs
   python -m uvicorn main:app --host 0.0.0.0 --port 8017
   ```

4. **Initial sync**
   ```bash
   curl -X POST http://localhost:8017/api/v1/docs/sync \
     -H "Content-Type: application/json" \
     -d @sources.yaml
   ```

5. **Validate documentation**
   ```bash
   curl -X POST http://localhost:8017/api/v1/docs/validate \
     -H "Content-Type: application/json" \
     -d '{"scope": "all"}'
   ```

## 🎯 Use Cases

### Development Workflow Integration
- **CI/CD Pipeline Integration**: Automatic documentation updates on code changes
- **Pull Request Validation**: Documentation validation before merges
- **Release Automation**: Documentation publishing with releases
- **Branch Management**: Documentation sync across development branches

### Knowledge Base Management
- **Internal Wiki Maintenance**: Keep internal documentation current
- **API Documentation**: Real-time API documentation from code
- **Configuration Management**: Automated config documentation
- **Training Materials**: Keep training docs synchronized with product changes

### Compliance & Governance
- **Documentation Standards**: Enforce documentation quality standards
- **Audit Trails**: Track all documentation changes and updates
- **Regulatory Compliance**: Maintain required documentation currency
- **Quality Assurance**: Automated quality checks and validation

### Multi-Platform Publishing
- **Format Conversion**: Generate docs in multiple formats (PDF, HTML, etc.)
- **Platform Distribution**: Publish to multiple platforms automatically
- **Access Control**: Apply different permissions for different audiences
- **Analytics Integration**: Track documentation usage and effectiveness

## 🤝 Contributing

### Development Setup
```bash
# Clone repository
git clone <repository>
cd services/mcp-evergreen-docs

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/

# Start development server
uvicorn main:app --reload --host 0.0.0.0 --port 8017
```

### Adding New Source Types
1. **Create source handler** in the sources module
2. **Implement sync logic** for the new source type
3. **Add validation rules** specific to the source type
4. **Update configuration schema** to include new options
5. **Add comprehensive tests** for the new functionality

## 📄 License

This service is part of the LLM Documentation Ecosystem. See project LICENSE for details.

---

**Status:** 🟢 Production Ready | **Port:** 8017 | **Storage:** SQLite + Redis | **Integration:** Git, APIs, Filesystems
