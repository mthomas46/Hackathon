# 📦 MCP Registry Service

**Version:** 1.0.0  
**Port:** 8006  
**Role:** Package Catalog & Version Management

The **MCP Registry Service** is the centralized catalog for all MCP packages, patterns, and versions. It functions as the "npm registry" or "Docker Hub" for the MCP ecosystem, providing discovery, versioning, and metadata management for MCP knowledge packages.

---

## 🎯 **Overview**

The MCP Registry Service manages the complete lifecycle of MCP packages:

- **Package Catalog**: Centralized repository of all available MCP packages
- **Version Management**: Track multiple versions of packages with semantic versioning
- **Dependency Resolution**: Manage package dependencies and compatibility
- **Discovery**: Search and browse available packages
- **Metadata Management**: Store rich metadata about packages (authors, tags, descriptions)
- **Publishing**: Accept new package registrations and updates

---

## ✨ **Key Features**

### 1. Package Catalog Management
- ✅ Register new MCP packages
- ✅ Update existing packages
- ✅ Delete/deprecate packages
- ✅ List all available packages
- ✅ Search packages by name, tag, category

### 2. Version Control
- ✅ Semantic versioning (major.minor.patch)
- ✅ Version history tracking
- ✅ Latest/stable version identification
- ✅ Version comparison and compatibility
- ✅ Rollback to previous versions

### 3. Dependency Management
- ✅ Track package dependencies
- ✅ Resolve dependency chains
- ✅ Detect circular dependencies
- ✅ Version constraint checking
- ✅ Dependency graph visualization

### 4. Package Discovery
- ✅ Search by keywords, tags, categories
- ✅ Browse by popularity, downloads
- ✅ Filter by version, author, date
- ✅ Package recommendations
- ✅ Trending packages

### 5. Metadata Management
- ✅ Package descriptions and README
- ✅ Author information
- ✅ Tags and categories
- ✅ Download statistics
- ✅ Star ratings and reviews

---

## 🏗️ **Architecture**

### Domain-Driven Design (DDD)

```
services/mcp-registry/
├── domain/
│   ├── entities/
│   │   ├── package.py           # Package entity
│   │   ├── version.py           # Version entity
│   │   └── dependency.py        # Dependency entity
│   ├── value_objects/
│   │   ├── package_id.py        # Package identifier
│   │   ├── semantic_version.py  # Version number
│   │   └── package_status.py    # Published/deprecated/etc
│   └── repositories/
│       └── package_repository.py # Abstract repository
├── application/
│   ├── dtos/
│   │   ├── register_package_request.py
│   │   ├── package_response.py
│   │   └── search_request.py
│   └── use_cases/
│       ├── register_package.py
│       ├── search_packages.py
│       └── resolve_dependencies.py
├── infrastructure/
│   ├── persistence/
│   │   └── postgres_package_repository.py
│   └── config/
│       └── settings.py
└── presentation/
    └── api/
        └── routes.py            # FastAPI endpoints
```

### Data Model

```python
Package:
  - id: PackageId
  - name: str
  - description: str
  - author: str
  - tags: List[str]
  - category: str
  - versions: List[Version]
  - created_at: datetime
  - updated_at: datetime

Version:
  - package_id: PackageId
  - version: SemanticVersion
  - release_date: datetime
  - changelog: str
  - dependencies: List[Dependency]
  - download_count: int
  - is_latest: bool

Dependency:
  - package_id: PackageId
  - version_constraint: str  # e.g., ">=1.0.0,<2.0.0"
  - required: bool
```

---

## 📡 **API Endpoints**

### Package Management

```http
POST   /api/v1/packages              # Register new package
GET    /api/v1/packages              # List all packages
GET    /api/v1/packages/{id}         # Get package details
PUT    /api/v1/packages/{id}         # Update package
DELETE /api/v1/packages/{id}         # Delete package
```

### Version Management

```http
POST   /api/v1/packages/{id}/versions       # Publish new version
GET    /api/v1/packages/{id}/versions       # List package versions
GET    /api/v1/packages/{id}/versions/{ver} # Get specific version
DELETE /api/v1/packages/{id}/versions/{ver} # Delete version
```

### Discovery & Search

```http
GET    /api/v1/search                # Search packages
GET    /api/v1/packages/trending     # Get trending packages
GET    /api/v1/packages/popular      # Get popular packages
GET    /api/v1/tags                  # List all tags
GET    /api/v1/categories            # List all categories
```

### Dependencies

```http
GET    /api/v1/packages/{id}/dependencies     # Get package dependencies
POST   /api/v1/dependencies/resolve           # Resolve dependency chain
GET    /api/v1/packages/{id}/dependents       # Who depends on this package
```

---

## 🔗 **MCP Ecosystem Integration**

The MCP Registry is a **CORE SERVICE** that enables package management and version control across the entire MCP ecosystem.

### Service Interactions

#### 1. **MCP Package Manager** (Port: 8012)
**Relationship**: Primary consumer  
**Interaction**: 
- Package Manager queries Registry for available packages
- Downloads package metadata before import
- Checks version compatibility
- Reports package downloads

**Flow**:
```
MCP Package Manager → Registry: "Get package 'llm-patterns' v1.2.0"
Registry → Package Manager: Package metadata + download URL
Package Manager → MCP Store: Import package
Package Manager → Registry: Increment download count
```

#### 2. **MCP Store** (Port: 8008)
**Relationship**: Package storage backend  
**Interaction**:
- Registry stores package metadata
- MCP Store holds actual package binaries
- Registry links to Store for downloads

**Flow**:
```
Developer → Registry: Register new package
Registry → MCP Store: Upload package binary
Registry: Store metadata + link to Store
```

#### 3. **MCP Provisioner** (Port: 8003)
**Relationship**: Package deployment  
**Interaction**:
- Provisioner checks Registry for required packages
- Downloads and deploys packages to new MCPs
- Verifies package compatibility

**Flow**:
```
Provisioner: Create new MCP instance
Provisioner → Registry: Get required packages
Registry → Provisioner: Package list with versions
Provisioner → Package Manager: Install packages
```

#### 4. **MCP Gateway** (Port: 8001)
**Relationship**: External access  
**Interaction**:
- Gateway routes external package queries to Registry
- Handles authentication for package publishing
- Rate limiting for search/browse operations

**Flow**:
```
External Developer → Gateway: "Search for NLP packages"
Gateway → Registry: Forward search request
Registry → Gateway: Search results
Gateway → Developer: Formatted results
```

#### 5. **MCP Orchestrator** (Port: 8004)
**Relationship**: Pattern registry  
**Interaction**:
- Orchestrator registers LLM pattern packages
- Queries Registry for available patterns
- Uses Registry for pattern versioning

**Flow**:
```
Orchestrator: Need RAG pattern v2.0.0
Orchestrator → Registry: Get RAG pattern package
Registry → Orchestrator: Package metadata
Orchestrator → Package Manager: Install pattern
```

#### 6. **MCP Infrastructure** (Port: 8007)
**Relationship**: Health monitoring  
**Interaction**:
- Infrastructure monitors Registry health
- Tracks Registry availability
- Alerts on Registry issues

**Flow**:
```
Infrastructure: Health check loop
Infrastructure → Registry: GET /health
Registry → Infrastructure: {"status": "healthy"}
Infrastructure: Update service status dashboard
```

---

## 🔄 **Data Flow in MCP Ecosystem**

### Package Publishing Flow

```
┌─────────────┐
│  Developer  │
└──────┬──────┘
       │ 1. Publish package
       ▼
┌─────────────────┐
│ Package Manager │
└──────┬──────────┘
       │ 2. Register metadata
       ▼
┌─────────────┐        ┌──────────────┐
│   Registry  │◄───────┤  MCP Store   │
│  (Metadata) │   3.   │  (Binaries)  │
└──────┬──────┘  Upload └──────────────┘
       │
       │ 4. Index & catalog
       ▼
┌─────────────┐
│  Searchable │
│   Catalog   │
└─────────────┘
```

### Package Installation Flow

```
┌──────────────┐
│     User     │
└──────┬───────┘
       │ 1. Request package
       ▼
┌──────────────┐
│   Gateway    │
└──────┬───────┘
       │ 2. Query metadata
       ▼
┌──────────────┐        ┌──────────────┐
│   Registry   │───────►│ Package Mgr  │
│              │   3.   │              │
└──────────────┘  Return└──────┬───────┘
                   metadata    │
                               │ 4. Download binary
                               ▼
                        ┌──────────────┐
                        │  MCP Store   │
                        └──────┬───────┘
                               │ 5. Install
                               ▼
                        ┌──────────────┐
                        │   MCP Host   │
                        └──────────────┘
```

---

## 🎯 **Role in MCP Architecture**

The MCP Registry serves as the **CENTRAL CATALOG** in the MCP architecture:

### 1. **Package Discovery Hub**
- Single source of truth for all available packages
- Enables developers to find and explore MCP packages
- Provides search and browse capabilities

### 2. **Version Control Authority**
- Manages semantic versioning across ecosystem
- Ensures version compatibility
- Tracks package evolution

### 3. **Dependency Resolution**
- Resolves complex dependency chains
- Prevents dependency conflicts
- Ensures package compatibility

### 4. **Marketplace Foundation**
- Enables package ratings and reviews
- Tracks download statistics
- Supports trending/popular packages

### 5. **Ecosystem Health Monitor**
- Tracks active packages
- Monitors package usage
- Identifies deprecated packages

---

## 🔧 **Configuration**

### Environment Variables

```bash
# Service Configuration
PORT=8006
SERVICE_NAME=mcp-registry

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/mcp_registry
REDIS_URL=redis://localhost:6379/4

# Storage
PACKAGE_STORAGE_URL=http://mcp-store:8008
MAX_PACKAGE_SIZE_MB=100

# Search
ELASTICSEARCH_URL=http://localhost:9200
SEARCH_INDEX=mcp-packages

# Cache
CACHE_TTL_SECONDS=300
MAX_CACHE_SIZE_MB=512
```

---

## 🚀 **Running the Service**

### Docker (Recommended)

```bash
docker-compose --profile mcp_services up mcp-registry
```

### Local Development

```bash
cd services/mcp-registry
pip install -r requirements.txt
python main.py
```

### With Full Ecosystem

```bash
# Start all MCP services
docker-compose up -d

# Registry will be available at:
# http://localhost:8006
```

---

## 📊 **Monitoring & Health**

### Health Check Endpoint

```http
GET /health
```

**Response**:
```json
{
  "status": "healthy",
  "service": "mcp-registry",
  "version": "1.0.0",
  "timestamp": "2024-10-07T10:30:00Z",
  "dependencies": {
    "database": "healthy",
    "cache": "healthy",
    "storage": "healthy"
  },
  "metrics": {
    "total_packages": 142,
    "total_versions": 587,
    "active_packages": 138,
    "deprecated_packages": 4
  }
}
```

---

## 📚 **Usage Examples**

### Register a New Package

```bash
curl -X POST http://localhost:8006/api/v1/packages \
  -H "Content-Type: application/json" \
  -d '{
    "name": "llm-patterns",
    "description": "Collection of LLM patterns",
    "author": "MCP Team",
    "version": "1.0.0",
    "tags": ["llm", "patterns", "ai"],
    "category": "patterns"
  }'
```

### Search for Packages

```bash
curl "http://localhost:8006/api/v1/search?q=nlp&category=patterns"
```

### Get Package Details

```bash
curl http://localhost:8006/api/v1/packages/llm-patterns
```

### Resolve Dependencies

```bash
curl -X POST http://localhost:8006/api/v1/dependencies/resolve \
  -H "Content-Type: application/json" \
  -d '{
    "package": "rag-system",
    "version": "2.0.0"
  }'
```

---

## 🎓 **Best Practices**

### For Package Publishers

1. ✅ Use semantic versioning (major.minor.patch)
2. ✅ Write comprehensive package descriptions
3. ✅ Include clear dependency declarations
4. ✅ Maintain changelog for each version
5. ✅ Tag packages appropriately
6. ✅ Test packages before publishing

### For Package Consumers

1. ✅ Pin exact versions in production
2. ✅ Use version ranges for development
3. ✅ Check package dependencies before installing
4. ✅ Review changelogs when upgrading
5. ✅ Report issues to package authors
6. ✅ Star and review helpful packages

---

## 🔒 **Security**

### Package Verification
- ✅ Checksum validation
- ✅ Digital signatures
- ✅ Author verification
- ✅ Malware scanning

### Access Control
- ✅ Authentication for publishing
- ✅ Role-based permissions
- ✅ Package ownership
- ✅ Admin controls

---

## 📈 **Scalability**

### Horizontal Scaling
- ✅ Stateless service design
- ✅ Load balancer compatible
- ✅ Distributed caching (Redis)
- ✅ Read replicas for database

### Performance Optimization
- ✅ Elasticsearch for fast search
- ✅ Redis caching for metadata
- ✅ CDN for package distribution
- ✅ Database indexing

---

## 🎯 **Future Enhancements**

### Planned Features
- [ ] Package ratings and reviews
- [ ] Download analytics dashboard
- [ ] Automated security scanning
- [ ] Package recommendations
- [ ] Private package registries
- [ ] API rate limiting per user
- [ ] Package mirroring
- [ ] Webhook notifications

---

## 📞 **Support & Documentation**

- **Architecture**: See [MCP_ECOSYSTEM_ARCHITECTURE.md](/MCP_ECOSYSTEM_ARCHITECTURE.md)
- **Visual Guide**: See [MCP_VISUAL_ARCHITECTURE.md](/MCP_VISUAL_ARCHITECTURE.md)
- **API Docs**: See [API_REFERENCE.md](./docs/API_REFERENCE.md)
- **Package Manager**: See [/services/mcp_package_manager/README.md](/services/mcp_package_manager/README.md)

---

**Status**: Production-Ready  
**Maintainer**: MCP Team  
**Last Updated**: October 7, 2025

*The package catalog that powers the MCP ecosystem!* 📦✨

