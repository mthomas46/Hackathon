# User Store Service

A persistent user storage and relationship management service for the LLM Documentation Ecosystem.

## Overview

The User Store service provides centralized user management with automatic relationship extraction from documents processed by the source agent. It creates two-way relationships between users and documents based on content analysis and metadata parsing.

## Key Features

### 🔐 User Management
- **CRUD Operations**: Create, read, update, delete users
- **Role-Based Access**: Admin, Analyst, Developer, Manager, Viewer roles
- **Status Management**: Active, Inactive, Suspended, Pending states
- **Profile Management**: Avatars, bios, preferences
- **Contact Information**: Multiple notification channels (email, webhook, Slack)

### 🤖 Automatic Expertise Inference
- **Tag-Based Expertise**: Users gain expertise tags from documents they work on
- **Intelligent Inference**: Expertise inferred from repeated tag associations
- **Expertise Scoring**: Quantitative expertise levels based on document interactions
- **Topic Discovery**: Find users with specific technical expertise

### 🔗 Advanced Relationship Extraction
- **Document Analysis**: Extracts user relationships from GitHub PRs, Jira issues, Confluence pages
- **Smart Parsing**: Recognizes markers like "created by", "assigned to", "reviewed by"
- **Two-Way Relationships**: Links users to documents and documents to users
- **Auto User Creation**: Creates placeholder users for unknown identifiers
- **Tag Propagation**: Document tags automatically extend to user expertise profiles

### 🎯 Intelligent User Discovery
- **Expertise Queries**: Find users by technical topics and skills
- **Relationship Queries**: Discover users by document associations
- **Multi-Criteria Search**: Combine topics, services, and document types
- **Interpreter Integration**: Supports complex user queries from the interpreter service
- **Analysis Support**: Enables sophisticated user-based analysis across the ecosystem

### 💾 Persistent SQLite Storage
- **Relational Database**: Full SQLite implementation with proper indexing
- **Data Persistence**: All user data, relationships, and expertise stored durably
- **Query Performance**: Optimized indexes for fast user and relationship queries
- **Concurrent Access**: Thread-safe database operations

## API Endpoints

### User Management
```
POST   /users                    # Create user
GET    /users/{user_id}          # Get user
PUT    /users/{user_id}          # Update user
DELETE /users/{user_id}          # Delete user
GET    /users                    # List/search users
GET    /users/stats              # User statistics
```

### Document Relationship Management
```
POST   /users/{user_id}/documents/{doc_id}     # Add document relationship
PUT    /users/{user_id}/documents/{doc_id}     # Update document relationship
DELETE /users/{user_id}/documents/{doc_id}     # Remove document relationship
```

### Topic Management
```
POST   /users/{user_id}/topics                 # Add topic interest
DELETE /users/{user_id}/topics/{topic}         # Remove topic interest
GET    /users/{user_id}/topics                 # Get user topics
```

### Service Subscription Management
```
POST   /users/{user_id}/services                # Subscribe to service
DELETE /users/{user_id}/services/{service}      # Unsubscribe from service
GET    /users/{user_id}/services                # Get user subscriptions
```

### Document Relationships
```
POST   /documents/{doc_id}/process-relationships  # Auto-create relationships
GET    /documents/{doc_id}/users                 # Get document users
GET    /users/{user_id}/documents                # Get user documents
GET    /relationships/stats                      # Relationship statistics
```

### Expertise & User Discovery
```
GET    /users/expertise/{topic}        # Find users by expertise topic
GET    /users/{user_id}/expertise      # Get user expertise profile
PUT    /users/{user_id}/contact        # Update contact information
GET    /users/{user_id}/contacts       # Get user contacts
```

### User Preferences
```
PUT    /users/{user_id}/preferences   # Update preferences
POST   /users/{user_id}/login         # Record login
```

### Query Operations
```
GET    /users/search?q={query}       # Search users
GET    /users/query                  # Query by relationships
```

## Relationship Extraction

The service automatically extracts user relationships from document content and metadata:

### Supported Sources

#### GitHub PRs/Issues
- **Metadata**: `user.login`, `assignees`, `reviews.user.login`
- **Content**: `@username`, `by @user`, `reviewed by @user`
- **Markers**: `opened by`, `assigned to`, `reviewed by`

#### Jira Issues
- **Metadata**: `reporter.emailAddress`, `assignee.emailAddress`
- **Content**: `created by user`, `assigned to user`
- **Markers**: `reporter:`, `assignee:`, `commented by`

#### Confluence Pages
- **Metadata**: `creator.email`, `lastModifier.email`
- **Content**: `created by user`, `last modified by user`
- **Markers**: `authors:`, `contributors:`, `restrictions.user`

### Relationship Types

- **Owner**: Created the document
- **Contributor**: Modified or contributed to the document
- **Reviewer**: Reviewed the document (GitHub)
- **Subscriber**: Assigned to or following the document
- **Viewer**: Has access to view the document

## Integration Points

### Source Agent
When documents are processed, the source agent calls:
```
POST /documents/{document_id}/process-relationships
```
With document content, metadata, and source type to automatically create relationships.

### Interpreter Service
Queries users based on relationships:
```
GET /users/query?document_id={id}&service_name={service}&topic={topic}
```

### Analysis Services
Retrieves user lists for analysis:
```
GET /documents/{doc_id}/users
GET /users/{user_id}/documents
```

### Notification Service
Uses user relationships for targeted notifications based on document changes.

## Usage Examples

### Automatic Relationship Creation
```bash
curl -X POST "http://localhost:8001/documents/github:pr:123/process-relationships" \
  -F "content=PR content with @user mentions" \
  -F "metadata={\"user\":{\"login\":\"octocat\"}}" \
  -F "source_type=github"
```

### Query Users by Document
```bash
curl "http://localhost:8001/documents/github:pr:123/users"
```

### Query Documents by User
```bash
curl "http://localhost:8001/users/user_123/documents"
```

### Search Users
```bash
curl "http://localhost:8001/users/search?q=octocat"
```

### Find Users by Expertise
```bash
curl "http://localhost:8001/users/expertise/machine-learning"
# Returns: {"topic": "machine-learning", "users": [...], "total": 5}
```

### Get User Expertise Profile
```bash
curl "http://localhost:8001/users/user_123/expertise"
# Returns: comprehensive expertise analysis with scores and top skills
```

### Update User Contact Information
```bash
curl -X PUT "http://localhost:8001/users/user_123/contact" \
  -H "Content-Type: application/json" \
  -d '{"contact_webhook": "https://slack.com/webhook/123", "contact_slack": "#notifications"}'
```

### Add Document Relationship
```bash
curl -X POST "http://localhost:8001/users/user_123/documents/doc_456?relationship_type=owner&access_level=write"
```

### Remove Document Relationship
```bash
curl -X DELETE "http://localhost:8001/users/user_123/documents/doc_456"
```

### Add Topic Interest
```bash
curl -X POST "http://localhost:8001/users/user_123/topics?topic=machine-learning"
```

### Remove Topic Interest
```bash
curl -X DELETE "http://localhost:8001/users/user_123/topics/machine-learning"
```

### Subscribe to Service
```bash
curl -X POST "http://localhost:8001/users/user_123/services?service_name=document-store"
```

### Unsubscribe from Service
```bash
curl -X DELETE "http://localhost:8001/users/user_123/services/document-store"
```

### Get User Topics and Services
```bash
# Get user topics
curl "http://localhost:8001/users/user_123/topics"

# Get user service subscriptions
curl "http://localhost:8001/users/user_123/services"
```

## Architecture

### Domain Layer
- **Entities**: User, UserPreferences, DocumentRelationship (with expertise inference)
- **Services**: UserService, DocumentUserExtractionService
- **Value Objects**: UserRole, UserStatus, RelationshipType, AccessLevel
- **Relationship Management**: CRUD operations for document, topic, and service associations

### Application Layer
- **Use Cases**: CreateUser, QueryUsersByRelationship, ProcessDocumentRelationships
- **DTOs**: User requests/responses, validation models
- **Relationship Management**: Business logic for managing user associations

### Infrastructure Layer
- **Repositories**: SQLite implementations with full persistence and indexing
- **Database Schema**: Optimized tables for users, relationships, and expertise data
- **Query Optimization**: Indexes on frequently queried fields
- **Contact Integration**: Support for multiple notification channels

### Presentation Layer
- **API Models**: Pydantic models for request/response validation
- **Routes**: FastAPI endpoints with comprehensive documentation

## Configuration

```yaml
service_name: "user-store"
service_description: "User Store Service"
service_version: "1.0.0"
port: 8001
environment: "development"

repository:
  type: "in_memory"  # or sqlite, postgres

dependencies:
  - "document-store"
  - "notification-service"
```

## Development

### Running Locally
```bash
cd services/user-store
python main.py
```

### Testing
```bash
pytest tests/
```

### Docker
```bash
docker build -t user-store .
docker run -p 8001:8001 user-store
```

## Future Enhancements

- **Database Integration**: PostgreSQL/SQLite persistence
- **Authentication**: JWT token validation
- **Advanced Queries**: Graph-based relationship queries
- **Audit Logging**: User action tracking
- **Bulk Operations**: Batch user/document processing
- **Real-time Updates**: WebSocket notifications for relationship changes
