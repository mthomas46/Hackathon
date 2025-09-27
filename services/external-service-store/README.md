# External Service Store

A lightweight SQLite-based service for managing external service metadata, relationships, and technical specifications in the LLM Documentation Ecosystem.

## Overview

The External Service Store acts as a centralized registry and metadata repository for all external services in the ecosystem. It maintains comprehensive information about each service including technical specifications, API contracts, dependencies, relationships to documents/users/topics, and activity tracking.

## Key Features

### 🔧 **Service Metadata Management**
- **Complete Service Registry**: Track all external services with comprehensive metadata
- **Version Management**: Semantic versioning with release tracking
- **Technical Specifications**: Technologies, runtime requirements, health checks
- **Status Tracking**: Active, inactive, deprecated, maintenance states

### 📋 **API Contract Documentation**
- **Endpoint Specifications**: HTTP methods, paths, parameters, authentication
- **Data Contracts**: Request/response schemas and content types
- **Rate Limiting**: API usage constraints and limits
- **Interactive Documentation**: OpenAPI/Swagger integration

### 🔗 **Relationship Management**
- **Service Dependencies**: Runtime, build, and optional dependencies with version constraints
- **Document Relationships**: Links to Confluence pages, Jira tickets, GitHub PRs
- **User Associations**: Maintainers, contributors, and service users
- **Topic Categorization**: Technical and business domain classification

### 🔍 **Intelligent Discovery**
- **Technology Search**: Find services by programming languages, frameworks, databases
- **Topic-Based Discovery**: Locate services by technical domains (ML, APIs, security)
- **User Service Mapping**: Find services maintained or used by specific users
- **Dependency Graphs**: Understand service interrelationships

### 💾 **SQLite Persistence**
- **Lightweight Database**: File-based SQLite with proper indexing
- **ACID Transactions**: Data consistency and integrity
- **Concurrent Access**: Thread-safe operations
- **Schema Migrations**: Version-controlled database schema

## API Endpoints

### Service Management
```
POST   /services                    # Create service
GET    /services/{id}               # Get service details
PUT    /services/{id}               # Update service
DELETE /services/{id}               # Delete service
GET    /services                    # List services
GET    /services/search             # Search services
```

### Endpoint Management
```
POST   /services/{id}/endpoints     # Add API endpoint
GET    /services/{id}/endpoints     # Get service endpoints
```

### Dependency Management
```
POST   /services/dependencies        # Add dependency
GET    /services/{id}/dependencies  # Get dependencies
GET    /services/{id}/dependents    # Get dependent services
```

### Document-Service Bidirectional Relationships
```
POST   /documents/{doc_id}/process-relationships   # Process document & auto-create service relationships
POST   /documents/{doc_id}/sync-relationships      # Bulk sync document-service relationships
GET    /documents/{doc_id}/services                # Get services related to document
GET    /services/{id}/documents-paginated          # Get paginated documents for service
GET    /relationships/health                       # Relationship health check
GET    /relationships/cross-reference              # Cross-reference analysis
```

### Document Relationships
```
POST   /services/{id}/documents     # Add document relationship
GET    /services/{id}/documents     # Get service documents
GET    /documents/{id}/services     # Get services by document
```

### User Relationships
```
POST   /services/{id}/users         # Add user relationship
GET    /services/{id}/users         # Get service users
GET    /users/{id}/services         # Get user services
```

### Topic Relationships
```
POST   /services/{id}/topics        # Add topic relationship
GET    /services/{id}/topics        # Get service topics
GET    /topics/{name}/services      # Get services by topic
```

### Analytics & Discovery
```
GET    /analytics/overview          # Ecosystem overview
GET    /services/by-technology/{tech}  # Services by technology
GET    /services/by-user/{user}     # Services by user
GET    /services/recent-activity/{id}  # Recent service activity
```

## Document Ingestion Integration

### Bidirectional Relationship Enhancement

The External Service Store provides automatic bidirectional relationship creation during document ingestion. When documents are processed by the source agent, the system automatically:

1. **Analyzes Document Content**: Scans for service mentions by name, display name, and other identifiers
2. **Creates Bidirectional Links**: Establishes relationships from both document→service and service→document perspectives
3. **Updates Service Activity**: Tracks recent document references (Confluence, Jira, GitHub PR)
4. **Enhances Discoverability**: Improves cross-referencing between documentation and services

### Integration with Source Agent

The source agent can enhance document ingestion by calling:

```bash
# Process document and auto-create service relationships
curl -X POST "http://localhost:8010/documents/confluence:API_DOCS:USER_STORE/process-relationships" \
  -F "content=API documentation content mentioning user-store and document-store services" \
  -F "metadata={\"author\": \"Dev Team\", \"labels\": [\"api\", \"documentation\"]}" \
  -F "document_type=confluence"
```

Response includes detected services and relationship creation results.

### Bulk Synchronization

For existing documents or bulk operations:

```bash
# Bulk sync relationships for a document
curl -X POST "http://localhost:8010/documents/confluence:API_DOCS:USER_STORE/sync-relationships" \
  -F "service_ids=user-store-service,document-store-service,notification-service" \
  -F "document_type=confluence" \
  -F "relationship_type=documentation"
```

### Service Detection Examples

The system detects services mentioned in various ways:

- **Direct mentions**: "The user-store service provides..."
- **API references**: "Call the document-store API..."
- **Dependency lists**: "Depends on: notification-service, cache-service"
- **Metadata**: Labels and tags containing service names

## Usage Examples

### Register a New Service
```bash
curl -X POST "http://localhost:8010/services" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "user-store",
    "display_name": "User Store Service",
    "description": "Manages user profiles and relationships",
    "service_type": "api",
    "version": "1.0.0",
    "technologies": ["python", "fastapi", "sqlite"],
    "base_url": "http://localhost:8001",
    "health_endpoint": "/health"
  }'
```

### Add API Endpoint
```bash
curl -X POST "http://localhost:8010/services/user-store/endpoints" \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/users",
    "method": "POST",
    "description": "Create a new user",
    "request_contract": {
      "email": "string",
      "username": "string"
    },
    "response_contract": {
      "id": "string",
      "email": "string"
    },
    "authentication_required": true
  }'
```

### Add Service Dependency
```bash
curl -X POST "http://localhost:8010/services/dependencies" \
  -H "Content-Type: application/json" \
  -d '{
    "dependent_service_id": "user-store",
    "dependency_service_id": "document-store",
    "dependency_type": "runtime",
    "version_constraint": ">=1.0.0",
    "description": "User store depends on document store for profile data"
  }'
```

### Add Document Relationship
```bash
curl -X POST "http://localhost:8010/services/user-store/documents" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "confluence:USER_STORE_API",
    "document_type": "confluence",
    "relationship_type": "documentation",
    "description": "API documentation for user store service"
  }'
```

### Add User Relationship
```bash
curl -X POST "http://localhost:8010/services/user-store/users" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "john.doe",
    "relationship_type": "maintainer",
    "role": "Lead Developer",
    "permissions": ["read", "write", "admin"]
  }'
```

### Add Topic Relationship
```bash
curl -X POST "http://localhost:8010/services/user-store/topics" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "user-management",
    "relevance_score": 95,
    "description": "Core functionality is user profile management"
  }'
```

### Search Services
```bash
# Search by name or description
curl "http://localhost:8010/services/search?q=user"

# Find services using Python
curl "http://localhost:8010/services/by-technology/python"

# Find services related to machine learning
curl "http://localhost:8010/topics/machine-learning/services"
```

### Relationship Health Monitoring

```bash
# Check relationship health and consistency
curl "http://localhost:8010/relationships/health"

# Get cross-reference analysis
curl "http://localhost:8010/relationships/cross-reference"
```

### Enhanced Document Ingestion

```bash
# Process document with automatic service relationship creation
curl -X POST "http://localhost:8010/documents/confluence:API_DOCS:USER_STORE/process-relationships" \
  -F "content=API documentation mentioning user-store and document-store" \
  -F "metadata={\"author\": \"Dev Team\"}" \
  -F "document_type=confluence"

# Response shows detected services and relationships created
{
  "document_id": "confluence:API_DOCS:USER_STORE",
  "document_type": "confluence",
  "detected_services": 3,
  "relationships_created": 3,
  "service_ids": ["user-store", "document-store", "notification-service"]
}
```

## Architecture

### Domain Layer
- **Entities**: ExternalService, ServiceEndpoint, ServiceDependency, ServiceDocument, ServiceUser, ServiceTopic
- **Services**: ExternalServiceService for business logic
- **Repositories**: Abstract interfaces for data access

### Infrastructure Layer
- **SQLite Repositories**: Concrete implementations with database operations
- **Database Schema**: Normalized tables with proper relationships and indexes
- **Transaction Management**: Data consistency across related entities

### Integration Layer
- **Document Ingestion Integration**: Automatic service relationship creation during document processing
- **Source Agent Integration**: APIs for enhancing document ingestion with service detection
- **Bidirectional Synchronization**: Ensures consistent relationships across services
- **Health Monitoring**: Relationship consistency and data quality checks

### Presentation Layer
- **FastAPI Application**: REST API with automatic OpenAPI documentation
- **Pydantic Models**: Request/response validation and serialization
- **CORS Support**: Cross-origin request handling

## Data Model

### ExternalService Entity
```python
{
  "id": "unique-identifier",
  "name": "service-name",
  "display_name": "Human Readable Name",
  "description": "Service description",
  "service_type": "api|database|message_queue|cache|storage|...",
  "status": "active|inactive|deprecated|maintenance",
  "version": "1.2.3",
  "technologies": ["python", "fastapi", "sqlite"],
  "run_requirements": {"python": ">=3.8", "memory": "512MB"},
  "base_url": "http://localhost:8001",
  "health_endpoint": "/health",
  "endpoints": [...],  # API endpoints with contracts
  "dependencies": [...],  # Service dependencies
  "documents": [...],   # Related documents
  "users": [...],       # Associated users
  "topics": [...]       # Related topics
}
```

### Relationships

#### Service Dependencies
- **Runtime**: Required for service operation
- **Build**: Required for development/compilation
- **Optional**: Enhancements or optional features
- **Version Constraints**: Semantic version requirements

#### Document Relationships
- **Confluence**: Documentation pages
- **Jira**: Issue tickets and epics
- **GitHub PR**: Pull requests and code changes
- **README**: Service documentation files

#### User Relationships
- **Maintainers**: Responsible for service development and operations
- **Contributors**: Contribute code, documentation, or features
- **Users**: Consume the service functionality

#### Topic Relationships
- **Technical Domains**: machine-learning, api-design, databases, security
- **Business Domains**: finance, healthcare, e-commerce, analytics
- **Operational Concerns**: monitoring, logging, caching, messaging

## Integration Points

### Document Store
- **Document Relationships**: Track which documents relate to each service
- **Activity Updates**: Update service last_document fields when docs change
- **Version Control**: Link services to specific documentation versions

### User Store
- **User Relationships**: Track service maintainers and contributors
- **Permission Management**: Define user roles and permissions per service
- **Activity Tracking**: Monitor user interactions with services

### Source Agent
- **Service Discovery**: Automatically register new services found in code
- **Dependency Analysis**: Extract service dependencies from code and configs
- **Endpoint Detection**: Discover API endpoints from source code

### Interpreter Service
- **Service Queries**: Find services by various criteria for analysis
- **Dependency Graphs**: Understand service relationships for impact analysis
- **Topic-Based Search**: Locate services in specific technical domains

## Configuration

```yaml
service:
  name: "external-service-store"
  version: "1.0.0"
  port: 8010

database:
  path: "data/external_service_store.db"
  max_connections: 10

features:
  auto_discovery: true
  health_checks: true
  dependency_tracking: true
  activity_monitoring: true
```

## Development

### Running Locally
```bash
cd services/external-service-store
python main.py
```

### Testing
```bash
pytest tests/ -v
```

### API Documentation
Access the interactive API documentation at:
```
http://localhost:8010/docs
```

## Future Enhancements

- **Service Health Monitoring**: Real-time health checks and status updates
- **Dependency Graph Visualization**: Interactive dependency graphs
- **Service Metrics**: Performance and usage analytics
- **Automated Discovery**: Auto-register services from Kubernetes/docker-compose
- **Version Compatibility**: Dependency version conflict detection
- **Service Templates**: Standardized service registration templates
- **Bulk Operations**: Batch updates for multiple services
- **Audit Logging**: Track all service metadata changes
- **Notification Integration**: Alerts for service status changes
