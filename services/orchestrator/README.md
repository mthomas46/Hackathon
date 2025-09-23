# 🏢 Orchestrator Service

<!--
LLM Processing Metadata:
- document_type: "service_documentation"
- service_name: "orchestrator"
- port: 5099
- key_concepts: ["ddd", "workflow_orchestration", "service_coordination", "langgraph"]
- architecture: "domain_driven_design"
- processing_hints: "Core service with DDD implementation, workflow management, and service registry"
- cross_references: ["../../ECOSYSTEM_MASTER_LIVING_DOCUMENT.md", "../shared/", "../../tests/orchestrator/"]
- integration_points: ["all_services", "redis", "service_registry", "event_streaming"]
-->

**Enterprise-Grade Workflow Orchestration Platform**

The Orchestrator service is the central coordination and control plane for the LLM Documentation Ecosystem. It provides comprehensive workflow management, multi-service orchestration, enterprise integration, and real-time monitoring capabilities.

[![Tests](https://img.shields.io/badge/tests-50+-brightgreen)](tests/orchestrator/)
[![API Endpoints](https://img.shields.io/badge/API-17-blue)](main.py)
[![Enterprise Ready](https://img.shields.io/badge/enterprise-ready-orange)](README.md)

Navigation: [Home](../../README.md) · [Architecture](../../docs/architecture/) · [Testing](../../docs/guides/TESTING_GUIDE.md) · [Services](../README_SERVICES.md)

## 🎯 Key Features

### 🔄 Workflow Management
- **Parameterized Workflows** - Dynamic input handling with validation and type safety
- **Complex Dependencies** - Action sequencing and dependency resolution with conditional logic
- **Execution Monitoring** - Real-time status tracking and progress reporting with detailed metrics
- **Version Control** - Workflow versioning, change management, and rollback capabilities
- **Template System** - Pre-built workflow templates for common scenarios with customization
- **Error Handling** - Comprehensive error recovery, retry mechanisms, and failure analysis
- **Performance Optimization** - Intelligent resource allocation and execution scheduling

### 🤝 Multi-Service Orchestration
- **Service Discovery** - Automatic service location, health checking, and dynamic registration
- **Cross-Service Communication** - Secure inter-service messaging with correlation tracking
- **Event-Driven Processing** - Real-time event handling, correlation, and saga patterns
- **Load Balancing** - Intelligent request distribution with health-aware routing
- **Circuit Breaking** - Fault tolerance, graceful degradation, and automatic recovery
- **Context Propagation** - Request context, authentication, and metadata across services
- **Rate Limiting** - Service-level rate limiting and throttling protection

### 🏢 Enterprise Integration
- **Service Mesh** - Mutual TLS, authentication, traffic management, and observability
- **Event Streaming** - Real-time event publishing, subscription, and message queuing
- **Enterprise Monitoring** - Health checks, metrics, alerting, and performance monitoring
- **Audit Trails** - Complete request tracking, compliance logging, and security auditing
- **Security** - Enterprise-grade authentication, authorization, and access control
- **High Availability** - Multi-region deployment, failover, and disaster recovery
- **Scalability** - Horizontal scaling, auto-scaling, and resource optimization

## 🏗️ Architecture

### 🎨 Domain-Driven Design Implementation

The Orchestrator follows **enterprise-grade Domain-Driven Design (DDD)** principles with clear bounded contexts and sophisticated architectural patterns:

```
services/orchestrator/
├── domain/                    # Pure business logic organized by bounded contexts
│   ├── workflow_management/   # Workflow execution and lifecycle management
│   │   ├── entities/          # Workflow, Execution, Action entities
│   │   ├── value_objects/     # WorkflowId, ExecutionStatus, ActionConfig
│   │   ├── services/          # WorkflowValidationService, ExecutionService
│   │   ├── events/            # WorkflowCreated, ExecutionStarted, ActionCompleted
│   │   └── repositories/      # WorkflowRepository, ExecutionRepository
│   ├── service_registry/      # Service discovery and capability management
│   │   ├── entities/          # Service, Capability, Endpoint entities
│   │   ├── value_objects/     # ServiceName, CapabilityType, HealthStatus
│   │   ├── services/          # ServiceDiscoveryService, HealthCheckService
│   │   ├── events/            # ServiceRegistered, HealthCheckFailed
│   │   └── repositories/      # ServiceRepository, CapabilityRepository
│   ├── health_monitoring/     # System health and performance monitoring
│   │   ├── entities/          # HealthCheck, Metric, Alert entities
│   │   ├── value_objects/     # HealthStatus, MetricType, AlertSeverity
│   │   ├── services/          # HealthMonitoringService, AlertService
│   │   ├── events/            # HealthDegraded, AlertTriggered
│   │   └── repositories/      # HealthCheckRepository, MetricRepository
│   ├── infrastructure/        # Infrastructure orchestration and management
│   │   ├── entities/          # Saga, DeadLetterQueue, CircuitBreaker entities
│   │   ├── value_objects/     # SagaId, QueueMessage, CircuitState
│   │   ├── services/          # SagaOrchestrator, QueueManager, CircuitBreakerService
│   │   ├── events/            # SagaCompensation, QueueMessageProcessed
│   │   └── repositories/      # SagaRepository, MessageQueueRepository
│   ├── ingestion/            # Data ingestion workflow orchestration
│   │   ├── entities/          # IngestionJob, DataSource, ProcessingRule entities
│   │   ├── value_objects/     # IngestionType, ProcessingStatus, QualityScore
│   │   ├── services/          # IngestionOrchestrator, QualityAnalyzer
│   │   ├── events/            # IngestionStarted, QualityAnalyzed
│   │   └── repositories/      # IngestionRepository, DataSourceRepository
│   └── query_processing/      # Query execution and coordination
│       ├── entities/          # Query, Result, Intent entities
│       ├── value_objects/     # QueryType, IntentType, ResultFormat
│       ├── services/          # QueryProcessor, IntentClassifier
│       ├── events/            # QueryExecuted, IntentClassified
│       └── repositories/      # QueryRepository, IntentRepository
├── application/               # Application services and use cases
│   ├── workflow_management/   # Workflow management use cases
│   ├── service_registry/      # Service registry use cases
│   ├── health_monitoring/     # Health monitoring use cases
│   ├── infrastructure/        # Infrastructure use cases
│   ├── ingestion/            # Ingestion use cases
│   └── query_processing/      # Query processing use cases
├── infrastructure/           # External services, persistence, and adapters
│   ├── persistence/          # Database adapters and repositories
│   ├── external_services/     # Service clients and integrations
│   ├── message_brokers/       # Event streaming and messaging
│   └── security/             # Authentication and authorization
└── presentation/             # API controllers, DTOs, and presentation logic
    ├── api/                  # REST API endpoints and controllers
    ├── cli/                  # Command-line interface
    ├── events/               # Event handlers and subscribers
    └── webhooks/             # Webhook handlers and integrations
```

### 🏛️ Core Architectural Patterns

#### **1. Domain-Driven Design (DDD)**
- **Bounded Contexts**: Clear separation between workflow management, service registry, health monitoring, infrastructure, ingestion, and query processing
- **Entities & Value Objects**: Rich domain models with business logic and validation
- **Domain Services**: Complex business operations that don't belong to a single entity
- **Repositories**: Abstract data access with clean interfaces
- **Domain Events**: Event sourcing for audit trails and decoupled processing

#### **2. Command Query Responsibility Segregation (CQRS)**
- **Command Side**: Write operations with optimistic locking and validation
- **Query Side**: Read operations with optimized queries and caching
- **Event Sourcing**: Complete audit trail of all state changes
- **Materialized Views**: Pre-computed views for efficient querying

#### **3. Event-Driven Architecture**
- **Event Storming**: Domain events capture business intent and state changes
- **Saga Pattern**: Long-running transaction coordination across services
- **Event Sourcing**: Complete system history for debugging and analysis
- **Circuit Breaker**: Fault tolerance with automatic recovery

### 🔗 Service Interaction Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │  Orchestrator   │    │  Service Mesh   │
│   Interface     │◄──►│   Service       │◄──►│   (Security)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Workflow       │    │  Event          │    │  Health         │
│  Management     │    │  Streaming      │    │  Monitoring     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Ecosystem Services                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │ Interpreter │ │ Doc Store   │ │ Analysis    │ ...      │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

### 🎯 Key Design Decisions

#### **1. Microservices Orchestration**
- **Decision**: Adopt orchestration over choreography for complex workflows
- **Rationale**: Central coordination provides better visibility, debugging, and failure handling
- **Implementation**: Dependency injection container with clean separation of concerns

#### **2. Event-Driven Architecture**
- **Decision**: Redis-based event streaming with saga patterns
- **Rationale**: Asynchronous processing for AI workloads, resilience through event replay
- **Components**: Event ordering, saga orchestration, circuit breakers, dead letter queues

#### **3. LangGraph Integration**
- **Decision**: AI-powered workflow orchestration capabilities
- **Rationale**: Enable intelligent decision making and workflow optimization
- **Implementation**: Service-to-tool conversion, context-aware execution planning

### 🔄 Service Dependencies

**Primary Dependencies**:
- **Redis**: Service coordination, event streaming, caching
- **All Ecosystem Services**: Orchestration targets and health monitoring

**Service Interaction Patterns**:
```mermaid
orchestrator --> discovery-agent: Service registration
orchestrator --> llm-gateway: AI workflow coordination  
orchestrator --> doc_store: Document orchestration
orchestrator --> analysis-service: Analysis coordination
orchestrator --> memory-agent: Context management
```

## 🚀 Quick Start

### Prerequisites
```bash
Python 3.8+
pip install -r ../../../requirements.txt
```

### Running the Service
```bash
# Start the orchestrator service
python main.py

# Or run with uvicorn
uvicorn main:app --host 0.0.0.0 --port 5080 --reload
```

### Basic Usage
```python
from orchestrator.modules.workflow_management.service import WorkflowManagementService

# Create workflow service
workflow_service = WorkflowManagementService()

# Create a simple workflow
workflow_data = {
    "name": "Hello World Workflow",
    "description": "A simple notification workflow",
    "parameters": [
        {
            "name": "message",
            "type": "string",
            "description": "Message to display",
            "required": True
        }
    ],
    "actions": [
        {
            "action_id": "notify",
            "action_type": "notification",
            "name": "Send Notification",
            "description": "Send completion notification",
            "config": {
                "message": "{{message}}",
                "channels": ["log"]
            }
        }
    ]
}

# Create workflow
success, message, workflow = await workflow_service.create_workflow(
    workflow_data, "user@example.com"
)

# Execute workflow
success, message, execution = await workflow_service.execute_workflow(
    workflow.workflow_id,
    {"message": "Hello, World!"},
    "user@example.com"
)
```

## 📚 API Documentation

### Base URL
```
http://localhost:5080
```

### Authentication
All API endpoints support enterprise-grade authentication via headers:
```
Authorization: Bearer <token>
X-User-ID: <user_id>
X-Correlation-ID: <correlation_id>
X-Request-ID: <request_id>
```

### Request/Response Format

#### Standard Response Envelope
```json
{
  "success": true,
  "data": {},
  "message": "Operation completed successfully",
  "correlation_id": "req-abc123def456",
  "request_id": "req-abc123def456",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0",
  "metadata": {
    "processing_time_ms": 150,
    "service_version": "2.1.0"
  }
}
```

#### Error Response Format
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid workflow parameters",
    "details": {
      "field": "actions",
      "issue": "Required field missing"
    },
    "correlation_id": "req-abc123def456",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

### Core Endpoints

#### 📝 Workflow Management

##### Create Workflow
**Endpoint**: `POST /workflows`

**Request Body**:
```json
{
  "name": "Document Analysis Workflow",
  "description": "Analyze documents for quality and insights",
  "parameters": [
    {
      "name": "document_url",
      "type": "string",
      "description": "URL of document to analyze",
      "required": true,
      "validation": {
        "pattern": "^https?://.*",
        "min_length": 10
      }
    },
    {
      "name": "analysis_type",
      "type": "string",
      "description": "Type of analysis to perform",
      "required": false,
      "default": "comprehensive",
      "allowed_values": ["basic", "comprehensive", "security"]
    }
  ],
  "actions": [
    {
      "action_id": "fetch_doc",
      "action_type": "service_call",
      "name": "Fetch Document",
      "description": "Retrieve document content from source",
      "config": {
        "service": "source_agent",
        "endpoint": "/fetch",
        "method": "POST",
        "parameters": {
          "url": "{{document_url}}"
        },
        "timeout": 30,
        "retry_attempts": 3
      },
      "depends_on": []
    },
    {
      "action_id": "analyze_content",
      "action_type": "service_call",
      "name": "Analyze Content",
      "description": "Perform quality analysis on document",
      "config": {
        "service": "analysis_service",
        "endpoint": "/analyze",
        "method": "POST",
        "parameters": {
          "content": "{{fetch_doc.response.content}}",
          "analysis_type": "{{analysis_type}}"
        },
        "timeout": 60,
        "retry_attempts": 2
      },
      "depends_on": ["fetch_doc"],
      "condition": "{{fetch_doc.success}}"
    },
    {
      "action_id": "store_results",
      "action_type": "service_call",
      "name": "Store Analysis Results",
      "description": "Persist analysis results to document store",
      "config": {
        "service": "doc_store",
        "endpoint": "/documents",
        "method": "POST",
        "parameters": {
          "title": "{{fetch_doc.response.title}}",
          "content": "{{analyze_content.response.summary}}",
          "metadata": {
            "analysis_type": "{{analysis_type}}",
            "quality_score": "{{analyze_content.response.quality_score}}",
            "source_url": "{{document_url}}"
          }
        }
      },
      "depends_on": ["analyze_content"],
      "condition": "{{analyze_content.success}}"
    }
  ],
  "tags": ["document_analysis", "quality_check"],
  "version": "1.0",
  "created_by": "user@example.com"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "workflow_id": "workflow_abc123def456",
    "name": "Document Analysis Workflow",
    "description": "Analyze documents for quality and insights",
    "status": "active",
    "version": "1.0",
    "created_at": "2024-01-15T10:30:00Z",
    "created_by": "user@example.com"
  },
  "message": "Workflow created successfully",
  "correlation_id": "req_abc123def456",
  "timestamp": "2024-01-15T10:30:05Z"
}
```

**Parameters Schema**:
- **name** (string, required): Unique workflow name
- **description** (string, optional): Human-readable description
- **parameters** (array, required): Input parameter definitions
  - **name** (string): Parameter identifier
  - **type** (string): Data type (string, integer, boolean, object)
  - **description** (string): Human-readable description
  - **required** (boolean): Whether parameter is mandatory
  - **default** (any): Default value if not provided
  - **validation** (object): Validation rules (pattern, min_length, etc.)
- **actions** (array, required): Sequence of actions to execute
  - **action_id** (string): Unique action identifier
  - **action_type** (string): Type of action (service_call, notification, etc.)
  - **name** (string): Human-readable action name
  - **config** (object): Action-specific configuration
  - **depends_on** (array): Action IDs this action depends on
  - **condition** (string): Conditional expression for execution
- **tags** (array, optional): Categorization labels
- **version** (string, optional): Workflow version
- **created_by** (string, optional): User who created the workflow

##### List Workflows
**Endpoint**: `GET /workflows`

**Query Parameters**:
- `page` (integer, optional): Page number for pagination (default: 1)
- `page_size` (integer, optional): Number of items per page (default: 50, max: 100)
- `status` (string, optional): Filter by status (active, inactive, draft)
- `created_by` (string, optional): Filter by creator
- `tags` (string, optional): Filter by tags (comma-separated)
- `search` (string, optional): Search in name and description
- `sort_by` (string, optional): Sort field (name, created_at, updated_at)
- `sort_order` (string, optional): Sort order (asc, desc)

**Response**:
```json
{
  "success": true,
  "data": {
    "workflows": [
      {
        "workflow_id": "workflow_abc123def456",
        "name": "Document Analysis Workflow",
        "description": "Analyze documents for quality and insights",
        "status": "active",
        "version": "1.0",
        "tags": ["document_analysis", "quality_check"],
        "created_at": "2024-01-15T10:30:00Z",
        "created_by": "user@example.com",
        "updated_at": "2024-01-15T10:30:00Z",
        "execution_count": 25,
        "success_rate": 0.96
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 50,
      "total_items": 150,
      "total_pages": 3,
      "has_next": true,
      "has_previous": false
    },
    "filters": {
      "status": "active",
      "created_by": "user@example.com"
    }
  },
  "correlation_id": "req_abc123def456",
  "timestamp": "2024-01-15T10:30:05Z"
}
```

##### Get Workflow Details
**Endpoint**: `GET /workflows/{workflow_id}`

**Response**:
```json
{
  "success": true,
  "data": {
    "workflow_id": "workflow_abc123def456",
    "name": "Document Analysis Workflow",
    "description": "Analyze documents for quality and insights",
    "status": "active",
    "version": "1.0",
    "parameters": [...],
    "actions": [...],
    "tags": ["document_analysis", "quality_check"],
    "created_at": "2024-01-15T10:30:00Z",
    "created_by": "user@example.com",
    "updated_at": "2024-01-15T10:30:00Z",
    "execution_count": 25,
    "success_rate": 0.96,
    "average_execution_time": 45.2,
    "metadata": {
      "category": "analysis",
      "complexity": "medium",
      "estimated_cost": 0.15
    }
  },
  "correlation_id": "req_abc123def456",
  "timestamp": "2024-01-15T10:30:05Z"
}
```

##### Update Workflow
**Endpoint**: `PUT /workflows/{workflow_id}`

**Request Body**:
```json
{
  "name": "Updated Document Analysis Workflow",
  "description": "Enhanced analysis with security scanning",
  "parameters": [
    {
      "name": "document_url",
      "type": "string",
      "description": "URL of document to analyze",
      "required": true,
      "validation": {
        "pattern": "^https?://.*",
        "min_length": 10
      }
    },
    {
      "name": "enable_security_scan",
      "type": "boolean",
      "description": "Include security vulnerability scanning",
      "required": false,
      "default": false
    }
  ],
  "actions": [...],
  "tags": ["document_analysis", "quality_check", "security"],
  "version": "1.1"
}
```

**Response**: Same format as Create Workflow

##### Delete Workflow
**Endpoint**: `DELETE /workflows/{workflow_id}`

**Response**:
```json
{
  "success": true,
  "data": {
    "workflow_id": "workflow_abc123def456",
    "deleted_at": "2024-01-15T10:30:00Z"
  },
  "message": "Workflow deleted successfully",
  "correlation_id": "req_abc123def456",
  "timestamp": "2024-01-15T10:30:05Z"
}
```

##### Clone Workflow
**Endpoint**: `POST /workflows/{workflow_id}/clone`

**Request Body**:
```json
{
  "name": "Cloned Document Analysis Workflow",
  "description": "Customized version with additional checks",
  "customizations": {
    "parameters": {
      "add_security_scan": {
        "name": "enable_security_scan",
        "type": "boolean",
        "description": "Include security vulnerability scanning",
        "required": false,
        "default": true
      }
    },
    "actions": {
      "add_security_check": {
        "action_id": "security_scan",
        "action_type": "service_call",
        "name": "Security Scan",
        "config": {
          "service": "secure_analyzer",
          "endpoint": "/scan",
          "method": "POST",
          "parameters": {
            "content": "{{analyze_content.response.content}}"
          }
        },
        "depends_on": ["analyze_content"],
        "condition": "{{enable_security_scan}}"
      }
    }
  }
}
```

**Response**: Same format as Create Workflow

#### 🚀 Workflow Execution

##### Execute Workflow
**Endpoint**: `POST /workflows/{workflow_id}/execute`

**Request Body**:
```json
{
  "parameters": {
    "document_url": "https://example.com/doc.pdf",
    "analysis_type": "comprehensive",
    "enable_security_scan": true
  },
  "execution_options": {
    "priority": "high",
    "timeout_minutes": 30,
    "retry_on_failure": true,
    "continue_on_error": false,
    "callback_url": "https://example.com/webhook/execution-complete",
    "metadata": {
      "source": "api",
      "user_id": "user123",
      "project": "document_analysis"
    }
  },
  "created_by": "user@example.com"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "execution_id": "exec_abc123def456",
    "workflow_id": "workflow_abc123def456",
    "status": "running",
    "parameters": {
      "document_url": "https://example.com/doc.pdf",
      "analysis_type": "comprehensive",
      "enable_security_scan": true
    },
    "execution_options": {
      "priority": "high",
      "timeout_minutes": 30,
      "retry_on_failure": true,
      "continue_on_error": false,
      "callback_url": "https://example.com/webhook/execution-complete"
    },
    "started_at": "2024-01-15T10:30:00Z",
    "estimated_completion": "2024-01-15T10:32:00Z",
    "progress": {
      "current_step": 0,
      "total_steps": 3,
      "current_action": "fetch_doc",
      "completion_percentage": 0
    }
  },
  "message": "Workflow execution started successfully",
  "correlation_id": "req_abc123def456",
  "timestamp": "2024-01-15T10:30:05Z"
}
```

**Execution Options**:
- **priority** (string): Execution priority (low, normal, high, urgent)
- **timeout_minutes** (integer): Maximum execution time
- **retry_on_failure** (boolean): Whether to retry failed actions
- **continue_on_error** (boolean): Continue execution on action failures
- **callback_url** (string): URL to call on completion
- **metadata** (object): Additional execution context

##### Get Execution Status
**Endpoint**: `GET /workflows/executions/{execution_id}`

**Response**:
```json
{
  "success": true,
  "data": {
    "execution_id": "exec_abc123def456",
    "workflow_id": "workflow_abc123def456",
    "status": "completed",
    "parameters": {...},
    "execution_options": {...},
    "started_at": "2024-01-15T10:30:00Z",
    "completed_at": "2024-01-15T10:31:45Z",
    "duration_seconds": 105,
    "progress": {
      "current_step": 3,
      "total_steps": 3,
      "current_action": "store_results",
      "completion_percentage": 100
    },
    "results": {
      "fetch_doc": {
        "success": true,
        "duration": 15.2,
        "response": {
          "title": "API Documentation",
          "content": "...",
          "content_type": "application/pdf"
        }
      },
      "analyze_content": {
        "success": true,
        "duration": 45.8,
        "response": {
          "quality_score": 0.87,
          "summary": "Well-structured API documentation...",
          "findings": [...]
        }
      },
      "store_results": {
        "success": true,
        "duration": 5.1,
        "response": {
          "document_id": "doc_xyz789ghi012",
          "stored_at": "2024-01-15T10:31:40Z"
        }
      }
    },
    "errors": [],
    "cost_estimate": 0.12,
    "created_by": "user@example.com"
  },
  "correlation_id": "req_abc123def456",
  "timestamp": "2024-01-15T10:32:00Z"
}
```

##### List Workflow Executions
**Endpoint**: `GET /workflows/{workflow_id}/executions`

**Query Parameters**:
- `limit` (integer, optional): Maximum executions to return (default: 50)
- `offset` (integer, optional): Number of executions to skip (default: 0)
- `status` (string, optional): Filter by status (running, completed, failed, cancelled)
- `created_by` (string, optional): Filter by executor
- `start_date` (string, optional): Filter by start date (ISO 8601)
- `end_date` (string, optional): Filter by end date (ISO 8601)
- `sort_by` (string, optional): Sort field (started_at, completed_at, duration)
- `sort_order` (string, optional): Sort order (asc, desc)

**Response**:
```json
{
  "success": true,
  "data": {
    "executions": [
      {
        "execution_id": "exec_abc123def456",
        "status": "completed",
        "started_at": "2024-01-15T10:30:00Z",
        "completed_at": "2024-01-15T10:31:45Z",
        "duration_seconds": 105,
        "success": true,
        "cost_estimate": 0.12,
        "created_by": "user@example.com"
      }
    ],
    "pagination": {
      "limit": 50,
      "offset": 0,
      "total": 125,
      "has_more": true
    },
    "summary": {
      "total_executions": 125,
      "successful_executions": 120,
      "failed_executions": 3,
      "cancelled_executions": 2,
      "average_duration": 98.5,
      "average_cost": 0.15
    }
  },
  "correlation_id": "req_abc123def456",
  "timestamp": "2024-01-15T10:32:00Z"
}
```

##### Cancel Execution
**Endpoint**: `POST /workflows/executions/{execution_id}/cancel`

**Request Body** (optional):
```json
{
  "reason": "User requested cancellation",
  "force": false
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "execution_id": "exec_abc123def456",
    "status": "cancelled",
    "cancelled_at": "2024-01-15T10:30:30Z",
    "reason": "User requested cancellation"
  },
  "message": "Execution cancelled successfully",
  "correlation_id": "req_abc123def456",
  "timestamp": "2024-01-15T10:30:35Z"
}
```

#### 🎯 Advanced Features

##### Create from Template
```http
POST /workflows/from-template
Content-Type: application/json

{
  "template_name": "document_analysis",
  "customizations": {
    "name": "Custom Document Analysis",
    "description": "Customized workflow"
  }
}
```

##### Search Workflows
```http
GET /workflows/search?q=document&limit=50
```

##### Get Statistics
```http
GET /workflows/statistics
```

##### Health Check
```http
GET /workflows/health
```

### Legacy API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | /health/system | System health |
| GET | /workflows | List workflows |
| GET | /info | Service info |
| GET | /config/effective | Effective config |
| GET | /metrics | Metrics |
| GET | /ready | Readiness |
| POST | /ingest | Request ingestion |
| POST | /workflows/run | Trigger ingestion workflow |
| POST | /demo/e2e | Demo bundle |
| POST | /registry/register | Register a service |
| GET | /registry | List services |
| GET | /infrastructure/dlq/stats | DLQ stats |
| POST | /infrastructure/dlq/retry | DLQ retry |
| GET | /infrastructure/saga/stats | Saga stats |
| GET | /infrastructure/saga/{saga_id} | Saga by id |
| GET | /infrastructure/events/history | Event history |
| POST | /infrastructure/events/replay | Replay events |
| GET | /infrastructure/tracing/stats | Tracing stats |
| GET | /infrastructure/tracing/trace/{trace_id} | Trace by id |
| GET | /infrastructure/tracing/service/{service_name} | Traces for service |
| POST | /infrastructure/events/clear | Clear events |
| GET | /peers | Orchestrator peers |
| POST | /registry/poll-openapi | Poll OpenAPI |
| GET | /workflows/history | Workflow history |
| POST | /jobs/recalc-quality | Recalc quality |
| POST | /jobs/notify-consolidation | Notify consolidation |
| POST | /docstore/save | Save to doc store |

## 🧪 Testing

### Test Structure
```
tests/orchestrator/
├── test_orchestrator_features.py     # Unit tests for core features
├── test_integration_scenarios.py     # Integration and scenario tests
├── test_api_endpoints.py            # API endpoint tests
├── conftest.py                       # Test fixtures and configuration
└── test_runner.py                    # Automated test runner
```

### Running Tests

#### Run All Tests
```bash
cd /path/to/orchestrator
PYTHONPATH=/path/to/services python -m pytest tests/orchestrator/ -v
```

#### Run Specific Test Categories
```bash
# Unit tests
PYTHONPATH=/path/to/services python -m pytest tests/orchestrator/test_orchestrator_features.py -v

# Integration tests
PYTHONPATH=/path/to/services python -m pytest tests/orchestrator/test_integration_scenarios.py -v

# API tests
PYTHONPATH=/path/to/services python -m pytest tests/orchestrator/test_api_endpoints.py -v
```

#### Run with Coverage
```bash
PYTHONPATH=/path/to/services python -m pytest tests/orchestrator/ --cov=orchestrator --cov-report=html
```

### Test Fixtures

#### Available Fixtures
- `workflow_service` - Workflow management service instance
- `event_stream` - Event streaming processor
- `service_mesh` - Service mesh integration
- `sample_workflow_data` - Pre-configured workflow data
- `complex_workflow_data` - Advanced workflow scenarios
- `performance_monitor` - Test performance tracking

## 🎯 Workflow Examples

### 1. Document Analysis Workflow
```python
workflow_data = {
    "name": "Document Quality Analysis",
    "description": "Analyze document for quality and insights",
    "parameters": [
        {
            "name": "document_url",
            "type": "string",
            "description": "Document URL to analyze",
            "required": True
        }
    ],
    "actions": [
        {
            "action_id": "fetch_doc",
            "action_type": "service_call",
            "name": "Fetch Document",
            "config": {
                "service": "source_agent",
                "endpoint": "/fetch",
                "method": "POST",
                "parameters": {"url": "{{document_url}}"}
            }
        },
        {
            "action_id": "analyze_quality",
            "action_type": "service_call",
            "name": "Analyze Quality",
            "config": {
                "service": "analysis_service",
                "endpoint": "/analyze",
                "method": "POST",
                "parameters": {"content": "{{fetch_doc.response.content}}"}
            },
            "depends_on": ["fetch_doc"]
        }
    ]
}
```

### 2. PR Confidence Analysis
```python
workflow_data = {
    "name": "PR Confidence Analysis",
    "description": "Analyze PR confidence against requirements",
    "parameters": [
        {
            "name": "pr_number",
            "type": "integer",
            "required": True
        },
        {
            "name": "repository",
            "type": "string",
            "required": True
        }
    ],
    "actions": [
        {
            "action_id": "fetch_pr",
            "action_type": "service_call",
            "name": "Fetch PR Data",
            "config": {
                "service": "source_agent",
                "endpoint": "/github/pr",
                "method": "GET",
                "parameters": {
                    "pr_number": "{{pr_number}}",
                    "repository": "{{repository}}"
                }
            }
        },
        {
            "action_id": "analyze_confidence",
            "action_type": "service_call",
            "name": "Analyze Confidence",
            "config": {
                "service": "analysis_service",
                "endpoint": "/calculate_confidence",
                "method": "POST",
                "parameters": {"pr_data": "{{fetch_pr.response}}"}
            },
            "depends_on": ["fetch_pr"]
        }
    ]
}
```

## 🔧 Configuration

### Environment Variables
```bash
# Database
ORCHESTRATOR_DB_PATH=../../data/orchestrator_workflows.db

# Service Discovery
ORCHESTRATOR_SERVICE_HOST=localhost
ORCHESTRATOR_SERVICE_PORT=5080

# Enterprise Features
ORCHESTRATOR_ENABLE_TLS=true
ORCHESTRATOR_TLS_CERT_PATH=./certs/server.crt
ORCHESTRATOR_TLS_KEY_PATH=./certs/server.key

# Monitoring
ORCHESTRATOR_METRICS_ENABLED=true
ORCHESTRATOR_HEALTH_CHECK_INTERVAL=30

# Security
ORCHESTRATOR_JWT_SECRET=your-secret-key
ORCHESTRATOR_API_KEY=your-api-key

# Legacy Environment Variables
REDIS_HOST=redis
REPORTING_URL=http://reporting:5030
ORCHESTRATOR_PEERS=
DOC_STORE_URL=
NOTIFICATION_URL=http://notification-service:5095
```

### Configuration File
```yaml
# config/orchestrator.yaml
database:
  path: ../../data/orchestrator_workflows.db
  connection_pool_size: 10
  timeout_seconds: 30

services:
  host: localhost
  port: 5080
  workers: 4

security:
  enable_tls: true
  tls_cert_path: ./certs/server.crt
  tls_key_path: ./certs/server.key
  jwt_secret: your-secret-key

monitoring:
  enabled: true
  metrics_interval: 60
  health_check_interval: 30
  log_level: INFO

enterprise:
  service_mesh_enabled: true
  event_streaming_enabled: true
  circuit_breaker_enabled: true
  rate_limiting_enabled: true
```

## 🤝 Contributing

### Development Setup
```bash
# Clone repository
git clone <repository-url>
cd services/orchestrator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r ../../../requirements.txt

# Install development dependencies
pip install pytest pytest-asyncio pytest-cov black isort mypy

# Set PYTHONPATH
export PYTHONPATH=/path/to/services:$PYTHONPATH
```

### Code Standards
- **Black** for code formatting
- **isort** for import sorting
- **mypy** for type checking
- **pytest** for testing

### Running Code Quality Checks
```bash
# Format code
black .

# Sort imports
isort .

# Type checking
mypy .

# Run tests
PYTHONPATH=/path/to/services python -m pytest tests/orchestrator/ -v

# Run with coverage
PYTHONPATH=/path/to/services python -m pytest tests/orchestrator/ --cov=orchestrator --cov-report=html
```

### Pull Request Process
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Update documentation
7. Submit pull request

### Commit Message Format
```
feat: add new workflow template system
fix: resolve parameter validation bug
docs: update API documentation
test: add integration tests for service mesh
refactor: improve error handling in workflow execution
```

## 📊 Features

### Core Functionality
- **Service registry** with peer replication and `/peers` listing
- **Workflow endpoints** and scheduled jobs (`/jobs/*`)
- **Event emission** with Redis events and trace IDs when configured
- **Health monitoring** with `/info`, `/config/effective`, `/metrics`, health/ready endpoints
- **Infrastructure management** with DLQ, saga, tracing, and event handling

### Enterprise Features
- **Workflow Management** - Complete CRUD operations for parameterized workflows
- **Multi-Service Orchestration** - Coordinate complex workflows across ecosystem services
- **Event-Driven Processing** - Real-time event handling and correlation
- **Service Mesh Integration** - Secure inter-service communication with mutual TLS
- **Enterprise Monitoring** - Comprehensive health checks and performance metrics
- **Template System** - Pre-built workflow templates for common use cases

---

## 🎉 Getting Started

1. **Set up the environment**:
   ```bash
   export PYTHONPATH=/path/to/services:$PYTHONPATH
   ```

2. **Start the orchestrator service**:
   ```bash
   python main.py
   ```

3. **Create your first workflow**:
   ```bash
   curl -X POST http://localhost:5080/workflows \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Hello World",
       "description": "My first workflow",
       "parameters": [{"name": "message", "type": "string", "required": true}],
       "actions": [{
         "action_id": "greet",
         "action_type": "notification",
         "name": "Send Greeting",
         "config": {"message": "{{message}}"}
       }]
     }'
   ```

4. **Execute the workflow**:
   ```bash
   curl -X POST http://localhost:5080/workflows/{workflow_id}/execute \
     -H "Content-Type: application/json" \
     -d '{"parameters": {"message": "Hello, Orchestrator!"}}'
   ```

5. **Monitor execution**:
   ```bash
   curl http://localhost:5080/workflows/executions/{execution_id}
   ```

Welcome to the Orchestrator service! 🚀

## Goal
- Coordinate ingestion workflows across agents (GitHub, Jira, Confluence, Swagger) and trigger analyses in the Consistency Engine.
- Act as the control plane API for scheduling, on-demand runs, and status.

## Overview and role in the ecosystem
- Acts as the central control plane: service registry, workflow runner, and operational endpoints.
- Provides eventing, DLQ management, tracing, and peer replication to keep the mesh healthy.
- Exposes job endpoints to kick off cross-service operations (quality recalculation, consolidation notifications).

> See also: [Glossary](../../docs/Glossary.md) · [Features & Interactions](../../docs/FEATURES_AND_INTERACTIONS.md)

## Endpoints (initial)
- `GET /health`: Liveness.
- `GET /ready`: Readiness.
- `POST /ingest`: Request ingestion `{source, scope, correlation_id}` (adds `trace_id`).
- `POST /workflows/run`: Trigger multi-source ingestion.
- `POST /registry/register`: Register a service.
- `GET /registry`: List registered services.
- `POST /registry/sync-peers`: Replicate registry to peer orchestrators.
- `POST /registry/poll-openapi`: Poll OpenAPI and compute drift.
- `POST /report/request`: Proxy to reporting service (`generate`, `life_of_ticket`, `pr_confidence`).
- `POST /summarization/suggest`: Policy-aware summarization via `secure-analyzer`.
- `POST /demo/e2e`: Returns a bundle `{ summary, log_analysis }` using reporting endpoints.

## Configuration
Configuration is config-first via `services/shared/config.get_config_value` with precedence: env > `config/app.yaml` > defaults.

- `PORT`: Service port (default 5099).
- `REPORTING_URL`: Base URL for reporting (default `http://reporting:5030`).
- `REDIS_HOST`: Redis hostname for events (optional).
- `ORCHESTRATOR_PEERS`: Comma-separated peer base URLs (also supported under `orchestrator.ORCHESTRATOR_PEERS` in `config/app.yaml`).
- `LOG_COLLECTOR_URL`: If set, emits structured logs to log-collector.

See also: `config/app.yaml` sections `services`, `redis`, `orchestrator`.

## Secrets
- Use `services/shared/credentials.get_secret(name)` to read secrets (env/secret backends).
- Pass secrets via env or Docker/K8s secrets; do not commit to git.

## Run locally

```bash
# Dev stack with live code
docker compose -f docker-compose.dev.yml up -d orchestrator redis

curl http://localhost:5099/health
```

## Shared utilities
- Request/metrics middleware: `services/shared/request_id.py`, `services/shared/metrics.py`.
- Config and constants: `services/shared/config.py`, `services/shared/constants.py`.
- JSON HTTP helpers (timeouts/retries/circuit): `services/shared/clients.py`.

## Demo: /demo/e2e
Example:
```bash
curl -s -X POST "$ORCHESTRATOR_URL/demo/e2e" -H 'content-type: application/json' -d '{"format":"json","log_limit":50}' | jq .
```
Response shape:
```json
{
  "summary": {"total": 3, "by_severity": {"low":2, "med":1}},
  "log_analysis": {"overview": {"count": 12, "by_level": {"info":9, "warn":2, "error":1}}, "sample": [ {"service":"orchestrator", "level":"info", "message":"workflow run requested"} ]}
}
```

## Roadmap
- Track workflow status and surface metrics.
- AuthN/Z for operator endpoints.
- End-to-end job that collects logs and returns a Log Analysis report.

## Related
- Doc Store: [../doc_store/README.md](../doc_store/README.md)
- Source Agent: [../source-agent/README.md](../source-agent/README.md)
- Analysis Service: [../analysis-service/README.md](../analysis-service/README.md)

## Testing
- Unit tests: [tests/unit/orchestrator](../../tests/unit/orchestrator)
- Strategies:
  - Registry endpoints (`/registry/*`) with envelope-aware assertions
  - Health/ready checks and config endpoints
  - Workflows/jobs stubs with flexible response validation
