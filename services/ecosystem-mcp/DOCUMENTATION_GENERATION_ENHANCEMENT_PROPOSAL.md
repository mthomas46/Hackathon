**Date:** November 19, 2025  
**Status:** 📋 **PROPOSAL** - Suggested Improvements  
**Target:** Code-Heavy Repositories (e.g., adminservice)  

---

# Documentation Generation Enhancement Proposal

## 🎯 Problem Statement

**Current Situation:**
- adminservice: 666 Scala files, 45 services, 18 controllers, 410 models
- Minimal existing docs: 3 markdown files, 5 text files
- Current doc generator uses generic questions designed for mixed doc/code repos
- Generated docs lack code-specific insights

**Gap:**
The current documentation generation process is optimized for repositories with existing documentation. For **code-heavy repositories** where most knowledge is embedded in source files, we need:
1. Code structure extraction
2. API endpoint discovery from controllers
3. Data model relationships
4. Service dependency mapping
5. Code pattern recognition

---

## 📊 Current State Analysis

### adminservice Repository Structure

```
📦 adminservice (969 files)
├── 666 .scala files     ← PRIMARY SOURCE OF TRUTH
│   ├── 45 Services      ← Business logic
│   ├── 18 Controllers   ← API endpoints
│   ├── 17 Repositories  ← Data access
│   ├── 410 Models       ← Data structures
│   └── 10 Utils/Helpers
├── 293 .js files        ← Frontend code
├── 3 .md files          ← Minimal docs
├── 5 .txt files         ← Scattered notes
├── 1 routes file        ← API route definitions
└── 1 .conf file         ← Configuration
```

**Key Finding**: 99% of knowledge is in code, not documentation files.

### Current Documentation Generator

**Sections** (Good foundation):
- ✅ Overview
- ✅ Architecture
- ✅ API Reference
- ✅ Setup Guide
- ✅ Examples
- ✅ Troubleshooting

**Questions** (Too generic for code-heavy repos):
```python
"What is the main purpose and functionality of this codebase?"
"What are the key components and their relationships?"
"What technologies and frameworks are used?"
```

**Problem**: These questions work well when there's existing documentation to query, but struggle to extract structured information from raw code files.

---

## 🚀 Proposed Enhancements

### Phase 1: Code-Aware Sections (NEW)

Add **specialized sections** for code-heavy repositories:

#### 1. **📦 Data Models** (NEW)
**Purpose**: Document all data structures, their fields, relationships, and purpose

**Target Queries**:
```python
"List all data models/entities in the codebase with their fields and types"
"What are the relationships between [ModelA] and [ModelB]?"
"What validations and constraints are defined on [Model]?"
"How is data transformed between database and API layers?"
"What enum types and constants are defined?"
```

**For adminservice**: Would discover 410 models across:
- `app/models/db/` - Database entities
- `app/models/api/` - API DTOs
- `app/models/repository/` - Repository models
- `app/models/enums/` - Enumerations

**Expected Output**:
```markdown
## Data Models

### Account Model
**Location**: `app/models/db/repository/account/Account.scala`
**Purpose**: Represents a supplier or client account

**Fields**:
- `id: UUID` - Unique identifier
- `externalId: ExternalId` - External system reference
- `companyName: String` - Account company name
- `status: AccountStatus` - Current account state
- `createdAt: DateTime` - Creation timestamp

**Relationships**:
- Has many `Users` (one-to-many)
- Has many `Connections` (one-to-many)
- Belongs to `Organization` (many-to-one)

**Validations**:
- `companyName` must be non-empty
- `externalId` must be unique
```

---

#### 2. **🔌 API Endpoints** (ENHANCED)
**Purpose**: Comprehensive API catalog with examples extracted from controllers

**Current**: Generic "What are the main API endpoints?"

**Enhanced Queries**:
```python
"List all REST API endpoints with their HTTP methods, paths, and purpose"
"What request/response models are used for [Endpoint]?"
"What authentication/authorization is required for [Endpoint]?"
"What are the error responses and status codes for [Endpoint]?"
"Show example requests and responses for [Endpoint]"
"What rate limiting or caching is applied to [Endpoint]?"
```

**For adminservice**: Would extract from:
- `app/controllers/` - Controller implementations
- `conf/routes` - Route definitions
- `app/models/api/` - Request/response models

**Expected Output**:
```markdown
## API Endpoints

### POST /api/public/registration
**Controller**: `RegistrationController.registerSupplier`
**Purpose**: Register a new supplier account

**Request**:
```json
{
  "supplierRegistration": {
    "companyName": "ACME Corp",
    "email": "contact@acme.com",
    "externalId": "EXT-12345"
  }
}
```

**Response** (201 Created):
```json
{
  "accountId": "uuid-here",
  "status": "active"
}
```

**Errors**:
- `400` - Invalid input (e.g., ChecksumDuplicateDataException)
- `422` - Invalid external ID (InvalidExternalIdException)
- `500` - Internal server error

**Authentication**: Requires API key in header `X-API-Key`
**Rate Limit**: 100 requests/minute per IP
```

---

#### 3. **🏗️ Service Layer** (NEW)
**Purpose**: Document business logic services and their responsibilities

**Target Queries**:
```python
"List all service classes and their primary responsibilities"
"What dependencies does [Service] have?"
"What business rules are implemented in [Service]?"
"How do services interact with repositories and external systems?"
"What events are published by [Service]?"
```

**For adminservice**: Would analyze 45 services:
- `app/services/` - Core business logic
- `app/services/v2/` - Version 2 services
- `app/services/eventmanagers/` - Event handling
- `app/delegates/` - Delegation pattern services

**Expected Output**:
```markdown
## Service Layer

### RegistrationService
**Location**: `app/services/RegistrationService.scala`
**Purpose**: Handles supplier registration workflow

**Dependencies**:
- `AccountServiceRepository` - Account data access
- `CRMService` - CRM integration
- `GeneralConfigService` - Configuration lookup
- `KafkaProducer` - Event publishing

**Key Methods**:
1. `registerSupplier(registration: SupplierRegistration): Future[Account]`
   - Validates registration data
   - Creates account in database
   - Publishes `SupplierRegistered` event to Kafka
   - Sends welcome email via CRM

2. `validateExternalId(externalId: ExternalId): Future[Boolean]`
   - Checks for duplicate external IDs
   - Validates format based on config

**Error Handling**:
- `ChecksumDuplicateDataException` - Duplicate registration detected
- `InvalidExternalIdException` - Invalid external ID format
- `AvettaServiceException` - General service errors

**Events Published**:
- `account.supplier.registered` - When supplier is registered
- `account.registration.failed` - When registration fails
```

---

#### 4. **🗄️ Data Access Layer** (NEW)
**Purpose**: Document repositories, database queries, and data persistence

**Target Queries**:
```python
"List all repository classes and the entities they manage"
"What database operations are available for [Entity]?"
"What custom queries or complex lookups are implemented?"
"How is database migration handled (evolutions)?"
"What indexes and performance optimizations exist?"
```

**For adminservice**: Would analyze:
- `app/repositories/` - Repository implementations
- `app/repositories/v2/` - Version 2 repositories
- `evolutions/` - Database migrations

**Expected Output**:
```markdown
## Data Access Layer

### AccountServiceAdminRepository
**Location**: `app/repositories/v2/AccountServiceAdminRepository.scala`
**Manages**: `Account` entities

**Core Operations**:
- `findById(id: UUID): Future[Option[Account]]`
- `findByExternalId(extId: ExternalId): Future[Option[Account]]`
- `create(account: Account): Future[Account]`
- `update(account: Account): Future[Account]`
- `delete(id: UUID): Future[Unit]`

**Custom Queries**:
1. `findActiveAccountsByOrganization(orgId: UUID): Future[Seq[Account]]`
   - Filters by status = ACTIVE and organizationId
   - Returns sorted by createdAt DESC

2. `searchAccountsByName(query: String): Future[Seq[Account]]`
   - Case-insensitive LIKE search on companyName
   - Limited to 100 results

**Database Schema** (from evolutions):
```sql
CREATE TABLE accounts (
  id UUID PRIMARY KEY,
  external_id VARCHAR(255) UNIQUE NOT NULL,
  company_name VARCHAR(500) NOT NULL,
  status VARCHAR(50) NOT NULL,
  organization_id UUID REFERENCES organizations(id),
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_accounts_external_id ON accounts(external_id);
CREATE INDEX idx_accounts_org_id ON accounts(organization_id);
```
```

---

#### 5. **⚡ Events & Messaging** (NEW)
**Purpose**: Document event-driven architecture, Kafka topics, and message flows

**Target Queries**:
```python
"What events are published and consumed in the system?"
"What Kafka topics exist and what are they used for?"
"What is the event schema for [EventType]?"
"How are events processed and what side effects occur?"
"What error handling and dead letter queues exist?"
```

**For adminservice**: Would analyze:
- `app/kafka/producer/` - Event producers
- `app/kafka/consumer/` - Event consumers
- `app/kafka/event/` - Event models

**Expected Output**:
```markdown
## Events & Messaging

### Kafka Topics

#### `account.events`
**Purpose**: Account lifecycle events
**Partition Strategy**: By account ID
**Retention**: 7 days

**Events**:

##### `SupplierRegistered`
**Published by**: `RegistrationService`
**Consumed by**: `CRMIntegrationService`, `NotificationService`

**Schema**:
```json
{
  "eventType": "SupplierRegistered",
  "timestamp": "2025-11-19T16:00:00Z",
  "accountId": "uuid",
  "payload": {
    "externalId": "EXT-12345",
    "companyName": "ACME Corp",
    "email": "contact@acme.com"
  }
}
```

**Downstream Effects**:
1. CRM Integration - Creates CRM account
2. Notifications - Sends welcome email
3. Analytics - Tracks registration metrics

**Error Handling**:
- Consumer retries 3 times with exponential backoff
- Failed messages sent to `account.events.dlq` (dead letter queue)
```

---

#### 6. **🔒 Security & Auth** (NEW)
**Purpose**: Document authentication, authorization, and security measures

**Target Queries**:
```python
"How is authentication implemented?"
"What authorization patterns are used (RBAC, ABAC)?"
"What security headers and middleware exist?"
"How are API keys/tokens validated?"
"What security best practices are followed?"
```

**Expected Output**:
```markdown
## Security & Authorization

### Authentication
**Method**: JWT tokens + API keys
**Implementation**: `util/CustomRequestHeaders.scala`

**API Key Authentication**:
- Header: `X-API-Key: <key>`
- Validated against `api_keys` table
- Supports rate limiting per key

### Authorization
**Pattern**: Role-Based Access Control (RBAC)

**Roles**:
- `ADMIN` - Full system access
- `SUPPLIER` - Supplier account management
- `CLIENT` - Client account management
- `READONLY` - View-only access

**Middleware**:
- `RequestLoggingNoBodyAction` - Logs all requests (PII-safe)
- `RateLimitAction` - 100 req/min per IP
- `AuthenticationAction` - Validates JWT/API key
```

---

### Phase 2: Enhanced Query Patterns

#### Pattern 1: **Code Structure Discovery**

**Current**:
```python
"What are the key components and their relationships?"
```

**Enhanced**:
```python
# First pass - Inventory
"List all Scala packages and their primary purpose"
"What is the directory structure and what does each directory contain?"
"What design patterns are visible (MVC, Repository, Service Layer)?"

# Second pass - Details
"For each controller in app/controllers/, list its endpoints and responsibilities"
"For each service in app/services/, describe its business logic and dependencies"
"For each model in app/models/db/, document its fields and relationships"

# Third pass - Integration
"How do controllers, services, and repositories interact?"
"Draw a dependency graph of key components"
"What are the main request flows through the system?"
```

---

#### Pattern 2: **Framework-Aware Queries**

**Detect framework** (Play, Spring, Django, etc.) and **tailor questions**:

**For Play Framework** (like adminservice):
```python
# Configuration
"What configuration is in application.conf?"
"What environment variables are used?"
"How is dependency injection configured (Guice modules)?"

# Routes
"Parse conf/routes and list all endpoints with their controllers"
"What route parameters and path patterns exist?"

# Evolutions
"What database schema changes are in evolutions/?"
"What is the current database schema?"
"What indexes and constraints are defined?"

# Testing
"What test frameworks are used (ScalaTest, Specs2)?"
"What test coverage exists for each service?"
```

---

#### Pattern 3: **Multi-Level Detail Queries**

**Level 1 - High-Level**:
```python
"Provide a 2-3 sentence overview of this codebase"
"List the main 5-10 components"
```

**Level 2 - Component Detail**:
```python
"For [Component], describe its purpose, key classes, and responsibilities"
"What are the inputs and outputs of [Component]?"
```

**Level 3 - Implementation Detail**:
```python
"For [Class], describe each method's purpose, parameters, and return values"
"What algorithms or business logic are implemented in [Method]?"
"What error cases are handled and how?"
```

---

### Phase 3: Code Example Extraction

#### Strategy 1: **Real Code Snippets**

**Extract actual code** from ingested files for examples:

```python
# Query for controllers
"Show the implementation of the POST /api/registration endpoint"

# Expected: Return actual Scala code from RegistrationController
```

**Output**:
```markdown
### Registration Endpoint Implementation

```scala
@Singleton
class RegistrationController @Inject() (
  crmService: PublicCRMServiceable,
  admService: PublicAccountServiceable,
  registrationService: RegistrationService
)(implicit ec: ExecutionContext) extends AbstractController {

  def registerSupplier(): Action[JsValue] = Action.async(parse.json) { request =>
    request.body.validate[SupplierRegistration].fold(
      errors => Future.successful(BadRequest(Json.toJson(ApiError(inputJsonError)))),
      registration => {
        registrationService.registerSupplier(registration).map { account =>
          Created(Json.toJson(account))
        }.recover {
          case e: ChecksumDuplicateDataException =>
            BadRequest(Json.toJson(ApiError("Duplicate registration")))
          case e: InvalidExternalIdException =>
            UnprocessableEntity(Json.toJson(ApiError("Invalid external ID")))
        }
      }
    )
  }
}
```
```

---

#### Strategy 2: **Test-Driven Examples**

**Extract examples from test files**:

```python
"Find test cases that demonstrate how to use [Service/Endpoint]"
"What are example request/response payloads from tests?"
```

---

### Phase 4: Relationship Mapping

#### Feature: **Automatic Relationship Discovery**

**Queries**:
```python
"What does [ServiceA] depend on (imports, injected dependencies)?"
"What services/repositories call [MethodX]?"
"Trace the flow of data from API endpoint to database"
```

**Output**:
```markdown
### Registration Flow

```
Client Request
    ↓
RegistrationController.registerSupplier()
    ↓ (validates input)
    ↓
RegistrationService.registerSupplier()
    ├→ AccountServiceRepository.findByExternalId() (check duplicate)
    ├→ AccountServiceRepository.create() (save account)
    ├→ KafkaProducer.publish(SupplierRegistered) (notify)
    └→ CRMService.createCRMAccount() (external call)
```
```

---

### Phase 5: Documentation Templates by Language/Framework

#### Template: **Scala/Play Framework**

**Sections**:
1. **Overview** - Purpose, tech stack, Play version
2. **Architecture** - MVC pattern, service layer, event-driven
3. **Configuration** - application.conf, environment vars
4. **API Reference** - Endpoints from routes + controllers
5. **Data Models** - Case classes, Slick tables, JSON formats
6. **Services** - Business logic, dependencies
7. **Repositories** - Database access, custom queries
8. **Events** - Kafka topics, event schemas
9. **Security** - Auth, authorization, CORS
10. **Database** - Schema (from evolutions), migrations
11. **Testing** - Test structure, coverage
12. **Setup** - SBT, dependencies, running locally

---

#### Template: **Python/Django**

**Sections**:
1. Overview, Models, Views, URLs
2. Django Admin, Middleware, Signals
3. Database (migrations), Celery tasks

---

#### Template: **JavaScript/Node/Express**

**Sections**:
1. Overview, Routes, Controllers/Handlers
2. Middleware, Database (Sequelize/Mongoose)
3. API endpoints, Authentication

---

## 🎨 Implementation Plan

### Step 1: Detect Repository Type (Automatic)

**Heuristics**:
```python
if "build.sbt" and "conf/routes" in files:
    framework = "Play Framework (Scala)"
    use_template = "scala_play"
elif "pom.xml" and "src/main/java" in files:
    framework = "Spring Boot (Java)"
    use_template = "java_spring"
elif "package.json" and "express" in dependencies:
    framework = "Express (Node.js)"
    use_template = "nodejs_express"
# ... more detections
```

---

### Step 2: Add Framework-Specific Sections

**UI Changes** (`doc_generator.py`):

```python
# After detecting framework
st.markdown("### 📚 Framework-Detected Sections")

if framework == "scala_play":
    with col1:
        include_data_models = st.checkbox("📦 Data Models", value=True)
        include_api_endpoints = st.checkbox("🔌 API Endpoints", value=True)
        include_services = st.checkbox("🏗️ Services", value=True)
    with col2:
        include_repositories = st.checkbox("🗄️ Repositories", value=True)
        include_events = st.checkbox("⚡ Events", value=True)
        include_database = st.checkbox("💾 Database Schema", value=True)
```

---

### Step 3: Enhanced Question Templates

**Add to `generate_questions()` function**:

```python
templates = {
    # ... existing sections ...
    
    "DATA_MODELS": [
        "List all data model classes with their fields, types, and purpose",
        "What are the relationships between models (one-to-many, many-to-many)?",
        "What validations and constraints are defined on models?",
        "How are models used for database persistence vs API serialization?",
        "What enum types, constants, or sealed traits are defined?",
    ],
    
    "API_ENDPOINTS": [
        "List all REST API endpoints from routes and controllers",
        "For each endpoint, what is the HTTP method, path, request/response models?",
        "What authentication and authorization is required per endpoint?",
        "What are the error responses and status codes?",
        "Show example requests and responses for key endpoints",
    ],
    
    "SERVICE_LAYER": [
        "List all service classes and their responsibilities",
        "What dependencies does each service have (injection)?",
        "What business rules and validation logic exist in services?",
        "How do services interact with repositories and external APIs?",
        "What events or side effects are triggered by services?",
    ],
    
    "DATA_ACCESS": [
        "List all repository classes and the entities they manage",
        "What database operations are available (CRUD, custom queries)?",
        "What performance optimizations exist (caching, batch loading)?",
        "How are transactions handled?",
        "What database migrations/evolutions exist?",
    ],
    
    "EVENTS_MESSAGING": [
        "What message broker is used (Kafka, RabbitMQ, etc.)?",
        "List all topics/queues and their purposes",
        "What events are published and by which components?",
        "What events are consumed and what side effects occur?",
        "How are event processing errors handled?",
    ],
    
    "DATABASE_SCHEMA": [
        "What is the current database schema from migrations/evolutions?",
        "What tables, columns, and data types exist?",
        "What indexes, constraints, and foreign keys are defined?",
        "How is data partitioned or sharded?",
        "What database-level triggers or functions exist?",
    ],
}
```

---

### Step 4: Code Extraction Queries

**Add special query types** that extract literal code:

```python
def generate_code_extraction_queries(section: str, framework: str) -> List[str]:
    """Generate queries specifically for extracting code snippets."""
    
    queries = []
    
    if section == "API_ENDPOINTS" and framework == "scala_play":
        queries.extend([
            "Show the implementation of controllers in app/controllers/",
            "Extract endpoint definitions from conf/routes",
            "Show request/response case classes from app/models/api/",
        ])
    
    if section == "DATA_MODELS" and framework == "scala_play":
        queries.extend([
            "Show model definitions from app/models/db/",
            "Extract database table definitions (Slick tables)",
            "Show JSON format definitions (Reads/Writes)",
        ])
    
    return queries
```

---

### Step 5: Post-Processing Enhancement

**Add code formatting** and **syntax highlighting**:

```python
def enhance_documentation(raw_docs: str, framework: str) -> str:
    """
    Post-process generated documentation to:
    1. Extract code blocks and apply syntax highlighting
    2. Add framework-specific structure
    3. Create cross-references
    4. Validate code examples
    """
    
    # Detect code blocks
    code_blocks = extract_code_blocks(raw_docs)
    
    # Apply syntax highlighting based on language
    for block in code_blocks:
        language = detect_language(block, framework)
        block.formatted = syntax_highlight(block.content, language)
    
    # Create table of contents
    toc = generate_toc(raw_docs)
    
    # Add cross-references
    enhanced = add_cross_references(raw_docs)
    
    return f"{toc}\n\n{enhanced}"
```

---

## 📈 Expected Outcomes

### Before (Current)

**Generated Documentation for adminservice**:
```markdown
## Overview
This codebase appears to be a web application built with Scala and Play Framework...

## Architecture
The system uses a typical MVC architecture...

## API Reference
The application has various REST endpoints...
```

*Generic, lacks specifics*

---

### After (Enhanced)

**Generated Documentation for adminservice**:
```markdown
# adminservice Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Data Models](#data-models) ← NEW
4. [API Endpoints](#api-endpoints) ← ENHANCED
5. [Service Layer](#service-layer) ← NEW
6. [Repositories](#repositories) ← NEW
7. [Events & Messaging](#events) ← NEW
8. [Database Schema](#database) ← NEW
9. [Security](#security) ← NEW
10. [Setup Guide](#setup)

---

## Data Models

### Account
**Location**: `app/models/db/repository/account/Account.scala`
**Table**: `accounts`

```scala
case class Account(
  id: UUID,
  externalId: ExternalId,
  companyName: String,
  status: AccountStatus,
  organizationId: Option[UUID],
  createdAt: DateTime,
  updatedAt: DateTime
)
```

**Relationships**:
- Has many `Users` via `userId` foreign key
- Has many `Connections` via `accountId` foreign key
- Belongs to `Organization` (optional)

**JSON Format**:
```scala
implicit val accountFormat: Format[Account] = Json.format[Account]
```

---

## API Endpoints

### Registration Endpoints

#### POST /api/public/registration
**Controller**: `RegistrationController.registerSupplier`
**Auth**: API Key required

**Request**:
```json
{
  "supplierRegistration": {
    "externalId": "EXT-12345",
    "companyName": "ACME Corp",
    "contactEmail": "admin@acme.com"
  }
}
```

**Response** (201):
```json
{
  "accountId": "550e8400-e29b-41d4-a716-446655440000",
  "status": "ACTIVE"
}
```

**Implementation**:
```scala
def registerSupplier(): Action[JsValue] = Action.async(parse.json) { request =>
  request.body.validate[SupplierRegistration].fold(
    errors => Future.successful(BadRequest(Json.toJson(ApiError(inputJsonError)))),
    registration => registrationService.registerSupplier(registration).map { account =>
      Created(Json.toJson(account))
    }
  )
}
```

**Error Codes**:
- `400` - Invalid JSON (ChecksumDuplicateDataException)
- `422` - Invalid external ID (InvalidExternalIdException)
- `500` - Internal error

---

## Service Layer

### RegistrationService
**Location**: `app/services/RegistrationService.scala`

**Dependencies**:
```scala
@Inject()(
  accountRepo: AccountServiceAdminRepository,
  crmService: PublicCRMServiceable,
  kafkaProducer: KafkaProducer
)
```

**Key Methods**:

#### `registerSupplier(reg: SupplierRegistration): Future[Account]`
1. Validate external ID uniqueness
2. Create account in database
3. Publish `SupplierRegistered` event to Kafka
4. Create CRM account (async)
5. Return created account

**Error Handling**:
- Throws `ChecksumDuplicateDataException` if duplicate
- Throws `InvalidExternalIdException` if invalid format
- Wraps database errors in `AvettaServiceException`

---

*This continues for all sections with actual code, real examples, and specific details...*
```

---

## 🛠️ Technical Implementation

### Code Changes Required

#### 1. Update `doc_generator.py`

**Add framework detection**:
```python
def detect_framework(api_base_url: str, service_name: str) -> Dict[str, Any]:
    """Detect repository framework/language."""
    
    response = httpx.get(f"{api_base_url}/api/v1/documents?service={service_name}&limit=20")
    files = [doc['file_path'] for doc in response.json()['documents']]
    
    detections = {
        "scala_play": any("build.sbt" in f or "conf/routes" in f for f in files),
        "java_spring": any("pom.xml" in f or "application.properties" in f for f in files),
        "python_django": any("manage.py" in f or "settings.py" in f for f in files),
        "nodejs_express": any("package.json" in f for f in files),
    }
    
    framework = next((k for k, v in detections.items() if v), "generic")
    
    return {
        "framework": framework,
        "language": framework.split("_")[0],
        "template": framework,
    }
```

**Add new sections**:
```python
# In configuration form
if framework_info['framework'] != 'generic':
    st.markdown(f"### 📚 {framework_info['language'].title()}-Specific Sections")
    
    include_data_models = st.checkbox("📦 Data Models", value=True)
    include_service_layer = st.checkbox("🏗️ Service Layer", value=True)
    include_repositories = st.checkbox("🗄️ Repositories", value=True)
    include_events = st.checkbox("⚡ Events/Messaging", value=False)
    include_database = st.checkbox("💾 Database Schema", value=True)
```

---

#### 2. Enhance Question Generation

**Add to `generate_questions()` in `doc_generator.py`**:
```python
# Add framework-specific templates
FRAMEWORK_TEMPLATES = {
    "scala_play": {
        "DATA_MODELS": [ ... ],
        "SERVICE_LAYER": [ ... ],
        # ... as shown above
    },
    "java_spring": {
        "DATA_MODELS": [ ... ],
        "SERVICE_LAYER": [ ... ],
    },
    # ... more frameworks
}

def generate_questions(section: str, pass_name: str, count: int, framework: str = "generic"):
    # Get framework-specific templates if available
    if framework in FRAMEWORK_TEMPLATES and section in FRAMEWORK_TEMPLATES[framework]:
        base_questions = FRAMEWORK_TEMPLATES[framework][section]
    else:
        # Fall back to generic templates
        base_questions = templates.get(section, default_questions)
    
    # ... rest of function
```

---

#### 3. Add Code Extraction Mode

**New query mode** specifically for extracting code:

```python
def extract_code_examples(api_base_url: str, target_files: List[str], config: Dict) -> str:
    """Extract actual code snippets from specific files."""
    
    results = []
    
    for file_path in target_files:
        response = httpx.post(
            f"{api_base_url}/api/v1/query/enhanced",
            json={
                "question": f"Show the complete implementation from {file_path}",
                "mode": "contextual",  # Use contextual for exact file content
                "service_name": config['service_filter'],
                "n_results": 1,
                "max_tokens": 4096,
            }
        )
        
        if response.status_code == 200:
            code = response.json()['answer']
            language = detect_language_from_extension(file_path)
            
            results.append(f"### {file_path}\n\n```{language}\n{code}\n```\n")
    
    return "\n\n".join(results)
```

---

#### 4. Post-Processing Pipeline

**Add documentation enhancement**:

```python
def post_process_documentation(raw_docs: str, framework: str) -> str:
    """
    Enhance generated documentation:
    1. Extract and format code blocks
    2. Add syntax highlighting
    3. Create TOC
    4. Add cross-references
    5. Validate code examples
    """
    
    # Parse markdown
    doc = MarkdownDocument(raw_docs)
    
    # Extract code blocks
    code_blocks = doc.extract_code_blocks()
    
    # Validate code syntax
    for block in code_blocks:
        if not validate_syntax(block.content, block.language):
            block.add_warning("⚠️ Syntax may be invalid")
    
    # Add cross-references
    doc.add_cross_references()
    
    # Generate TOC
    toc = doc.generate_toc()
    
    # Add framework badge
    badge = f"![Framework: {framework}](https://img.shields.io/badge/framework-{framework}-blue)"
    
    return f"{badge}\n\n{toc}\n\n{doc.render()}"
```

---

## 📦 Deliverables

### 1. Enhanced Documentation Templates
- ✅ Scala/Play Framework template
- ✅ Java/Spring Boot template
- ✅ Python/Django template
- ✅ Node.js/Express template

### 2. Framework Detection Logic
- ✅ Auto-detect based on file patterns
- ✅ Allow manual override

### 3. New Section Types
- ✅ Data Models
- ✅ Service Layer
- ✅ Repositories
- ✅ Events/Messaging
- ✅ Database Schema
- ✅ Security/Auth

### 4. Enhanced Query Engine
- ✅ Framework-aware questions
- ✅ Code extraction mode
- ✅ Multi-level detail (high/medium/deep)

### 5. Post-Processing Pipeline
- ✅ Code syntax validation
- ✅ Cross-reference generation
- ✅ TOC generation
- ✅ Framework badges

---

## 🎯 Success Metrics

### Quality Metrics

**Before Enhancement**:
- Generic sections: 6
- Code examples: Few, often incorrect
- Specificity: Low (generic descriptions)
- Usability: Medium (requires significant editing)

**After Enhancement**:
- Total sections: 12+ (6 generic + 6+ framework-specific)
- Code examples: Many, extracted from actual source
- Specificity: High (detailed API docs, data models, etc.)
- Usability: High (minimal editing needed)

### Quantitative Goals

| Metric | Current | Target | 
|--------|---------|--------|
| Sections per doc | 6 | 12+ |
| Code examples | 2-5 | 15-30 |
| API endpoints documented | 0-3 | All endpoints |
| Data models documented | 0 | All models |
| Lines of generated docs | 500-1000 | 2000-5000 |
| Accuracy (manual review) | 60% | 90%+ |

---

## 🚧 Implementation Phases

### Phase 1 (Week 1): Framework Detection + New Sections
- ✅ Add framework detection logic
- ✅ Add UI for new section types
- ✅ Update question generation
- **Deliverable**: Can generate docs with new sections

### Phase 2 (Week 2): Enhanced Query Templates
- ✅ Add framework-specific question templates
- ✅ Implement code extraction queries
- ✅ Test on adminservice
- **Deliverable**: Improved content quality

### Phase 3 (Week 3): Post-Processing Pipeline
- ✅ Code syntax validation
- ✅ Cross-reference generation
- ✅ TOC and navigation
- **Deliverable**: Polished, professional docs

### Phase 4 (Week 4): Additional Frameworks + Testing
- ✅ Add Spring Boot template
- ✅ Add Django template
- ✅ Comprehensive testing
- **Deliverable**: Multi-framework support

---

## 🔧 Configuration Example

### For adminservice

```python
framework_config = {
    "framework": "scala_play",
    "language": "scala",
    "sections": [
        "OVERVIEW",           # Keep existing
        "ARCHITECTURE",       # Keep existing
        "DATA_MODELS",        # NEW - Extract models
        "API_ENDPOINTS",      # ENHANCED - Parse routes + controllers
        "SERVICE_LAYER",      # NEW - Document services
        "REPOSITORIES",       # NEW - Database access
        "EVENTS_MESSAGING",   # NEW - Kafka events
        "DATABASE_SCHEMA",    # NEW - From evolutions
        "SECURITY",           # NEW - Auth/authz
        "SETUP",              # Keep existing
        "EXAMPLES",           # ENHANCED - Real code examples
    ],
    "query_config": {
        "passes_per_section": 3,
        "queries_per_pass": 3,
        "n_results": 15,
        "temperature": 0.3,  # Lower for more deterministic code extraction
    },
    "post_processing": {
        "validate_code_syntax": True,
        "add_cross_references": True,
        "generate_toc": True,
        "add_framework_badge": True,
    }
}
```

---

## 💡 Future Enhancements

### 1. Interactive Documentation
- Embed runnable code examples (via CodeSandbox, etc.)
- Live API testing from docs

### 2. Documentation Versioning
- Generate docs for different git tags/branches
- Show API changes between versions

### 3. Automated Diagram Generation
- Architecture diagrams from service dependencies
- ER diagrams from data models
- Sequence diagrams from method traces

### 4. Integration with IDEs
- Generate docs directly from IDE
- Jump-to-source from documentation

### 5. Continuous Documentation
- Regenerate docs on every commit
- Track documentation coverage

---

## 📚 References

- Play Framework Documentation Patterns
- Swagger/OpenAPI for API docs
- Scaladoc best practices
- DDD (Domain-Driven Design) documentation patterns

---

**Status**: 📋 **READY FOR REVIEW**  
**Complexity**: ⚡ **MEDIUM-HIGH** (2-4 weeks implementation)  
**Impact**: 🚀 **HIGH** (10x documentation quality for code-heavy repos)  
**Risk**: 🟢 **LOW** (additive changes, backward compatible)

