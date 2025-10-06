# MCP System - Ecosystem Integration Guide

## Overview

This document provides comprehensive guidance for integrating the MCP System into the existing `doc-ecosystem-dev` infrastructure. It defines standards, patterns, and best practices that **MUST** be followed to ensure consistency with the established ecosystem architecture.

**Status:** ✅ Mandatory for all MCP service implementations  
**Last Updated:** 2025-10-06  
**Applies To:** All services in `docs/mcp-system-plan/`

---

## Table of Contents

1. [Architecture Principles](#architecture-principles)
2. [Domain-Driven Design (DDD) Standards](#domain-driven-design-ddd-standards)
3. [Service Structure Templates](#service-structure-templates)
4. [LLM Gateway Integration](#llm-gateway-integration)
5. [Docker Compose Integration](#docker-compose-integration)
6. [REST API & OpenAPI Standards](#rest-api--openapi-standards)
7. [Testing with Mock Data Generator](#testing-with-mock-data-generator)
8. [Shared Libraries Usage](#shared-libraries-usage)
9. [Deployment & DevOps](#deployment--devops)

---

## Architecture Principles

### 1. KISS (Keep It Simple, Stupid)

**Principle:** Favor simple, maintainable solutions over complex, clever ones.

**Application to MCP Services:**
- ✅ Each service has ONE primary responsibility
- ✅ Avoid over-engineering - implement only what's needed
- ✅ Clear, readable code over optimizations
- ✅ Straightforward data flows

**Example:**
```python
# ❌ BAD: Over-engineered
class MCPQueryProcessor:
    def __init__(self):
        self.strategy_factory = StrategyFactoryBuilder().with_cache().with_fallback().build()
        self.pipeline = Pipeline(stages=[PreprocessStage(), AnalyzeStage(), PostprocessStage()])
    
    async def process(self, query):
        strategy = await self.strategy_factory.get_optimal_strategy(query)
        return await self.pipeline.execute(query, strategy)

# ✅ GOOD: Simple and clear
class MCPQueryProcessor:
    def __init__(self, llm_client, cache):
        self.llm_client = llm_client
        self.cache = cache
    
    async def process(self, query: str) -> Dict:
        # Check cache
        if cached := await self.cache.get(query):
            return cached
        
        # Process query
        result = await self.llm_client.generate(prompt=query)
        
        # Cache result
        await self.cache.set(query, result)
        return result
```

### 2. DRY (Don't Repeat Yourself)

**Principle:** Every piece of knowledge should have a single, unambiguous representation.

**Application to MCP Services:**
- ✅ Use `services/shared/` for common functionality
- ✅ Extract repeated patterns into base classes
- ✅ Configuration over code for variability
- ✅ Leverage existing ecosystem services

**Shared Components to Reuse:**
```python
# From services/shared/
from services.shared.domain.repositories.base_repository import BaseRepository, SqlRepository
from services.shared.domain.services.base_service import BaseService, CrudService
from services.shared.infrastructure.config import load_service_config
from services.shared.infrastructure.utilities.middleware import setup_common_middleware
from services.shared.presentation.api.responses import create_success_response, create_error_response
from services.shared.infrastructure.monitoring.health import register_health_endpoints
```

### 3. Test-Driven Development (TDD)

**Principle:** Write tests before implementation, achieve >90% coverage.

**TDD Workflow:**
```
1. Write failing test → 2. Write minimal code to pass → 3. Refactor → Repeat
```

**Coverage Requirements:**
- ✅ >90% line coverage
- ✅ >85% branch coverage
- ✅ Unit tests for all business logic
- ✅ Integration tests for all API endpoints
- ✅ End-to-end tests for critical workflows

---

## Domain-Driven Design (DDD) Standards

### Required Layered Architecture

All MCP services **MUST** follow this exact structure:

```
services/mcp-[service-name]/
├── domain/                     # Business logic (NO infrastructure dependencies)
│   ├── entities/               # Domain entities with identity
│   ├── value_objects/          # Immutable value objects
│   ├── repositories/           # Repository interfaces (abstract)
│   ├── services/               # Domain services (business logic)
│   └── events/                 # Domain events
├── application/                # Use cases & orchestration
│   ├── use_cases/              # Application-specific use cases
│   ├── dto/                    # Data transfer objects
│   └── mappers/                # Entity ↔ DTO mappers
├── infrastructure/             # External concerns
│   ├── repositories/           # Repository implementations (concrete)
│   ├── external_services/      # API clients (llm-gateway, source-agent, etc.)
│   ├── database/               # Database connections
│   └── config/                 # Configuration management
├── presentation/               # API layer
│   ├── api/
│   │   ├── routes/             # FastAPI routes (by domain)
│   │   ├── models/             # Pydantic request/response models
│   │   └── middleware/         # Request/response middleware
│   └── cli/                    # CLI commands (if applicable)
├── tests/                      # Tests mirror source structure
│   ├── unit/
│   │   ├── domain/
│   │   ├── application/
│   │   └── infrastructure/
│   ├── integration/
│   └── e2e/
├── main.py                     # FastAPI app composition
├── Dockerfile                  # Docker image definition
├── docker-compose.yml          # Standalone service compose (optional)
├── requirements.txt            # Python dependencies
├── config.yaml                 # Service-specific configuration
└── README.md                   # Service documentation
```

### Domain Layer Standards

#### Entities

**Definition:** Objects with unique identity that persist over time.

```python
# services/mcp-interpreter/domain/entities/parsed_query.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

@dataclass
class ParsedQuery:
    """Domain entity representing a parsed user query."""
    
    # Identity
    query_id: str = field(default_factory=lambda: str(uuid4()))
    
    # Attributes
    raw_query: str
    intent: str  # "retrieval", "analysis", "generation"
    entities: Dict[str, str] = field(default_factory=dict)
    required_mcps: List[str] = field(default_factory=list)
    context_priority: List[str] = field(default_factory=list)
    confidence: float = 0.0
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    # Domain behavior
    def validate(self) -> None:
        """Validate business rules."""
        if not self.raw_query or len(self.raw_query.strip()) == 0:
            raise ValueError("Query cannot be empty")
        
        if self.confidence < 0 or self.confidence > 1:
            raise ValueError("Confidence must be between 0 and 1")
        
        if self.intent not in ["retrieval", "analysis", "generation", "planning"]:
            raise ValueError(f"Invalid intent: {self.intent}")
    
    def is_high_confidence(self) -> bool:
        """Business rule: high confidence threshold."""
        return self.confidence >= 0.85
    
    def requires_multi_mcp(self) -> bool:
        """Business rule: check if multi-MCP query."""
        return len(self.required_mcps) > 1
```

#### Value Objects

**Definition:** Immutable objects without identity, compared by value.

```python
# services/mcp-orchestrator/domain/value_objects/confidence_score.py
from dataclasses import dataclass

@dataclass(frozen=True)  # Immutable
class ConfidenceScore:
    """Value object representing confidence in a result."""
    
    score: float
    
    def __post_init__(self):
        if self.score < 0 or self.score > 1:
            raise ValueError("Confidence score must be between 0 and 1")
    
    def is_high_confidence(self) -> bool:
        return self.score >= 0.85
    
    def is_medium_confidence(self) -> bool:
        return 0.70 <= self.score < 0.85
    
    def is_low_confidence(self) -> bool:
        return self.score < 0.70
    
    def approval_level(self) -> str:
        """Determine approval level based on confidence."""
        if self.score >= 0.95:
            return "auto_apply"
        elif self.score >= 0.85:
            return "auto_with_review"
        elif self.score >= 0.70:
            return "request_approval"
        else:
            return "manual_review"
```

#### Domain Services

**Definition:** Business logic that doesn't naturally fit in entities.

```python
# services/mcp-interpreter/domain/services/intent_classifier.py
from abc import ABC, abstractmethod
from typing import Dict

class IntentClassifierService(ABC):
    """Domain service for classifying query intent."""
    
    @abstractmethod
    async def classify(self, query: str) -> Dict[str, float]:
        """
        Classify the intent of a query.
        
        Returns:
            Dict mapping intent names to confidence scores
        """
        pass
    
    def determine_primary_intent(self, intent_scores: Dict[str, float]) -> str:
        """Business logic: choose highest scoring intent."""
        if not intent_scores:
            return "unknown"
        return max(intent_scores.items(), key=lambda x: x[1])[0]
```

#### Repositories (Interfaces)

**Definition:** Abstract interfaces for data access (no implementation details).

```python
# services/mcp-registry/domain/repositories/mcp_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entities.mcp_package import MCPPackage

class MCPRepository(ABC):
    """Repository interface for MCP packages."""
    
    @abstractmethod
    async def save(self, package: MCPPackage) -> None:
        """Persist an MCP package."""
        pass
    
    @abstractmethod
    async def find_by_id(self, package_id: str) -> Optional[MCPPackage]:
        """Find package by ID."""
        pass
    
    @abstractmethod
    async def find_by_tier(self, tier: int) -> List[MCPPackage]:
        """Find all packages for a tier."""
        pass
    
    @abstractmethod
    async def delete(self, package_id: str) -> None:
        """Delete a package."""
        pass
```

### Application Layer Standards

#### Use Cases

**Definition:** Application-specific workflows that orchestrate domain logic.

```python
# services/mcp-orchestrator/application/use_cases/execute_workflow.py
from dataclasses import dataclass
from typing import Dict
from domain.services.workflow_executor import WorkflowExecutor
from domain.repositories.workflow_repository import WorkflowRepository
from application.dto.workflow_result_dto import WorkflowResultDTO

@dataclass
class ExecuteWorkflowUseCase:
    """Use case for executing an MCP workflow."""
    
    workflow_repo: WorkflowRepository
    workflow_executor: WorkflowExecutor
    
    async def execute(self, workflow_id: str, parameters: Dict) -> WorkflowResultDTO:
        """
        Execute a workflow with given parameters.
        
        Args:
            workflow_id: ID of workflow to execute
            parameters: Execution parameters
        
        Returns:
            WorkflowResultDTO with execution results
        
        Raises:
            WorkflowNotFoundError: If workflow doesn't exist
            ValidationError: If parameters are invalid
        """
        # 1. Load workflow
        workflow = await self.workflow_repo.find_by_id(workflow_id)
        if not workflow:
            raise WorkflowNotFoundError(f"Workflow {workflow_id} not found")
        
        # 2. Validate parameters
        workflow.validate_parameters(parameters)
        
        # 3. Execute workflow
        result = await self.workflow_executor.execute(workflow, parameters)
        
        # 4. Map to DTO
        return WorkflowResultDTO.from_domain(result)
```

### Infrastructure Layer Standards

#### Repository Implementations

```python
# services/mcp-registry/infrastructure/repositories/sql_mcp_repository.py
from services.shared.domain.repositories.base_repository import SqlRepository
from domain.entities.mcp_package import MCPPackage
from domain.repositories.mcp_repository import MCPRepository

class SqlMCPRepository(SqlRepository[MCPPackage], MCPRepository):
    """SQL implementation of MCP repository."""
    
    def __init__(self, connection_string: str):
        super().__init__(
            entity_class=MCPPackage,
            connection_string=connection_string
        )
        self.table_name = "mcp_packages"
    
    async def find_by_tier(self, tier: int) -> List[MCPPackage]:
        """Find packages by tier."""
        query = f"SELECT * FROM {self.table_name} WHERE tier = ?"
        rows = await self._execute_query(query, (tier,))
        return [self._row_to_entity(row) for row in rows]
```

#### External Service Clients

```python
# services/mcp-interpreter/infrastructure/external_services/llm_gateway_client.py
import httpx
from typing import Dict, Optional

class LLMGatewayClient:
    """Client for llm-gateway service integration."""
    
    def __init__(self, base_url: str = "http://llm-gateway:5055"):
        self.base_url = base_url
        self.timeout = httpx.Timeout(30.0)
    
    async def generate(
        self,
        prompt: str,
        model: str = "llama3.2:3b",
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> Dict:
        """
        Generate text using LLM Gateway.
        
        Args:
            prompt: Text prompt
            model: Model name (default uses local Ollama)
            temperature: Sampling temperature
            max_tokens: Max response tokens
        
        Returns:
            Dict with 'response', 'provider', 'tokens_used'
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/query",
                json={
                    "prompt": prompt,
                    "model": model,
                    "provider": "ollama",  # Default to local
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def embeddings(self, text: str, model: str = "nomic-embed-text") -> Dict:
        """Generate embeddings via LLM Gateway."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/embeddings",
                json={
                    "text": text,
                    "model": model,
                    "provider": "ollama"
                }
            )
            response.raise_for_status()
            return response.json()
```

### Presentation Layer Standards

#### FastAPI Route Example with Full OpenAPI

```python
# services/mcp-interpreter/presentation/api/routes/query.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, List

from application.use_cases.parse_query import ParseQueryUseCase
from presentation.api.models.query_request import QueryRequest
from presentation.api.models.query_response import QueryResponse

# OpenAPI metadata
router = APIRouter(
    prefix="/query",
    tags=["Query Processing"],
    responses={
        404: {"description": "Query not found"},
        500: {"description": "Internal server error"}
    }
)

@router.post(
    "/parse",
    summary="Parse a user query",
    description="""
    Parse and analyze a natural language query to determine intent, entities, 
    and required MCP tiers.
    
    **Business Rules:**
    - Query must not be empty
    - Intent classification uses local LLM (via llm-gateway)
    - Confidence threshold: 0.70 for valid parse
    
    **Example Query:**
    ```json
    {
      "query": "What coding patterns does Team Alpha use?",
      "context": {"user_id": "user123", "session_id": "session456"}
    }
    ```
    
    **Response Example:**
    ```json
    {
      "query_id": "qry-123e4567-e89b-12d3",
      "intent": "retrieval",
      "entities": {"team": "Team Alpha", "focus": "coding patterns"},
      "required_mcps": ["team-mcp", "company-mcp"],
      "confidence": 0.92
    }
    ```
    """,
    response_model=QueryResponse,
    responses={
        200: {
            "description": "Query parsed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "query_id": "qry-123e4567-e89b-12d3",
                        "intent": "retrieval",
                        "entities": {"team": "Team Alpha"},
                        "required_mcps": ["team-mcp"],
                        "confidence": 0.92
                    }
                }
            }
        },
        400: {
            "description": "Invalid query (empty or malformed)",
            "content": {
                "application/json": {
                    "example": {"detail": "Query cannot be empty"}
                }
            }
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "query"],
                                "msg": "field required",
                                "type": "value_error.missing"
                            }
                        ]
                    }
                }
            }
        }
    },
    status_code=200
)
async def parse_query(
    request: QueryRequest,
    use_case: ParseQueryUseCase = Depends(get_parse_query_use_case)
) -> QueryResponse:
    """Parse a user query into structured format."""
    try:
        result = await use_case.execute(request.query, request.context)
        return QueryResponse.from_dto(result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Log error here
        raise HTTPException(status_code=500, detail="Internal server error")

# Dependency injection
def get_parse_query_use_case() -> ParseQueryUseCase:
    """Provide ParseQueryUseCase with dependencies."""
    # In production, use proper DI container
    from infrastructure.external_services.llm_gateway_client import LLMGatewayClient
    from domain.services.intent_classifier import IntentClassifierService
    
    llm_client = LLMGatewayClient()
    intent_classifier = IntentClassifierService(llm_client)
    
    return ParseQueryUseCase(intent_classifier=intent_classifier)
```

#### Pydantic Request/Response Models

```python
# services/mcp-interpreter/presentation/api/models/query_request.py
from pydantic import BaseModel, Field
from typing import Dict, Optional

class QueryRequest(BaseModel):
    """Request model for query parsing."""
    
    query: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Natural language query to parse",
        example="What coding patterns does Team Alpha use?"
    )
    
    context: Optional[Dict[str, str]] = Field(
        default=None,
        description="Additional context (user_id, session_id, etc.)",
        example={"user_id": "user123", "session_id": "sess456"}
    )
    
    class Config:
        schema_extra = {
            "example": {
                "query": "What coding patterns does Team Alpha use?",
                "context": {
                    "user_id": "user123",
                    "session_id": "session456"
                }
            }
        }

# services/mcp-interpreter/presentation/api/models/query_response.py
from pydantic import BaseModel, Field
from typing import Dict, List
from datetime import datetime

class QueryResponse(BaseModel):
    """Response model for parsed query."""
    
    query_id: str = Field(..., description="Unique query identifier")
    intent: str = Field(..., description="Classified intent (retrieval/analysis/generation)")
    entities: Dict[str, str] = Field(..., description="Extracted entities")
    required_mcps: List[str] = Field(..., description="List of required MCP IDs")
    context_priority: List[str] = Field(..., description="Context priority order")
    confidence: float = Field(..., ge=0, le=1, description="Classification confidence")
    created_at: datetime = Field(..., description="Timestamp of query creation")
    
    class Config:
        schema_extra = {
            "example": {
                "query_id": "qry-123e4567-e89b-12d3-a456-426614174000",
                "intent": "retrieval",
                "entities": {
                    "team": "Team Alpha",
                    "focus": "coding patterns",
                    "time_scope": "current"
                },
                "required_mcps": ["team-mcp", "company-mcp"],
                "context_priority": ["team", "company", "ecosystem"],
                "confidence": 0.92,
                "created_at": "2025-10-06T10:30:00Z"
            }
        }
```

---

## LLM Gateway Integration

### Why Use LLM Gateway (Not Direct Ollama)?

**LLM Gateway Benefits:**
1. ✅ **Intelligent Routing**: Auto-selects best provider (Ollama, OpenAI, Anthropic, Bedrock)
2. ✅ **Security**: PII detection and secure provider routing
3. ✅ **Caching**: Response caching reduces latency and cost
4. ✅ **Cost Optimization**: Budget management and usage tracking
5. ✅ **Monitoring**: Comprehensive metrics and logging
6. ✅ **Failover**: Automatic fallback if primary provider fails

### Standard LLM Gateway Client Pattern

**All MCP services MUST use this pattern:**

```python
# infrastructure/external_services/llm_gateway_client.py
import httpx
from typing import Dict, Optional, AsyncIterator
import asyncio

class LLMGatewayClient:
    """Standardized client for llm-gateway service."""
    
    def __init__(
        self,
        base_url: str = "http://llm-gateway:5055",
        default_provider: str = "ollama",  # Use local Ollama by default
        timeout: int = 60
    ):
        self.base_url = base_url
        self.default_provider = default_provider
        self.timeout = httpx.Timeout(timeout)
        self._client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()
    
    async def generate(
        self,
        prompt: str,
        model: str = "llama3.2:3b",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        provider: Optional[str] = None,
        force_refresh: bool = False
    ) -> Dict:
        """
        Generate text using LLM Gateway.
        
        Args:
            prompt: Text prompt
            model: Model name
            temperature: Sampling temperature (0-1)
            max_tokens: Max response tokens
            provider: Override provider (default: ollama)
            force_refresh: Skip cache
        
        Returns:
            {
                "response": str,
                "provider": str,
                "tokens_used": int,
                "processing_time": float,
                "cost": float,
                "cached": bool
            }
        """
        if not self._client:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        
        payload = {
            "prompt": prompt,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "provider": provider or self.default_provider,
            "force_refresh": force_refresh
        }
        
        response = await self._client.post(
            f"{self.base_url}/query",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    async def chat(
        self,
        prompt: str,
        conversation_id: Optional[str] = None,
        context: Optional[str] = None,
        model: str = "llama3.2:3b"
    ) -> Dict:
        """
        Conversational LLM interaction with memory.
        """
        if not self._client:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        
        payload = {
            "prompt": prompt,
            "model": model,
            "provider": self.default_provider
        }
        
        if conversation_id:
            payload["conversation_id"] = conversation_id
        if context:
            payload["context"] = context
        
        response = await self._client.post(
            f"{self.base_url}/chat",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    async def embeddings(
        self,
        text: str,
        model: str = "nomic-embed-text"
    ) -> Dict:
        """
        Generate text embeddings.
        
        Returns:
            {
                "embeddings": List[float],
                "model": str,
                "provider": str,
                "dimensions": int
            }
        """
        if not self._client:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        
        response = await self._client.post(
            f"{self.base_url}/embeddings",
            json={
                "text": text,
                "model": model,
                "provider": self.default_provider
            }
        )
        response.raise_for_status()
        return response.json()
    
    async def stream(
        self,
        prompt: str,
        model: str = "llama3.2:3b",
        temperature: float = 0.7
    ) -> AsyncIterator[str]:
        """
        Stream LLM responses (Server-Sent Events).
        
        Yields:
            Chunks of generated text
        """
        if not self._client:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        
        async with self._client.stream(
            "POST",
            f"{self.base_url}/stream",
            json={
                "prompt": prompt,
                "model": model,
                "provider": self.default_provider,
                "temperature": temperature
            }
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]  # Remove "data: " prefix
                    if data == "[DONE]":
                        break
                    import json
                    chunk = json.loads(data)
                    if not chunk.get("finished"):
                        yield chunk.get("chunk", "")

# Usage example in domain service
class IntentClassificationService:
    def __init__(self, llm_client: LLMGatewayClient):
        self.llm_client = llm_client
    
    async def classify(self, query: str) -> Dict[str, float]:
        """Classify query intent using LLM Gateway."""
        prompt = f"""
        Classify the intent of this query into one of these categories:
        - retrieval: Looking up information
        - analysis: Analyzing patterns or data
        - generation: Creating new content
        - planning: Creating plans or strategies
        
        Query: {query}
        
        Respond with JSON: {{"intent": "...", "confidence": 0.0-1.0}}
        """
        
        result = await self.llm_client.generate(
            prompt=prompt,
            model="llama3.2:3b",
            temperature=0.3,  # Lower temp for classification
            max_tokens=100
        )
        
        # Parse response
        import json
        classification = json.loads(result["response"])
        
        return {
            classification["intent"]: classification["confidence"]
        }
```

---

## Docker Compose Integration

### Adding MCP Services to docker-compose.dev.yml

**Location:** `/Users/mykalthomas/Documents/work/Hackathon/docker-compose.dev.yml`

**Standards:**
- ✅ All services on `hackathon_default` network (maps to `doc-ecosystem-dev`)
- ✅ Consistent naming: `mcp-[service-name]`
- ✅ Port mapping: `8XXX:5XXX` (external:internal)
- ✅ Health checks required
- ✅ Proper dependency ordering
- ✅ Environment variables follow existing patterns

### Example: MCP Interpreter Service

```yaml
  mcp-interpreter:
    build:
      context: .
      dockerfile: services/mcp-interpreter/Dockerfile
    container_name: hackathon-mcp-interpreter
    ports:
      - "8144:5100"  # External:Internal
    environment:
      # Standard service config
      - PYTHONPATH=/app
      - SERVICE_NAME=mcp-interpreter
      - SERVICE_API_PORT=5100
      - ENVIRONMENT=development
      
      # Logging
      - LOG_COLLECTOR_URL=http://log-collector:5080
      - LOG_COLLECTOR_ENABLED=true
      - LOG_LEVEL=INFO
      
      # Dependencies
      - REDIS_API_HOST=redis
      - LLM_GATEWAY_URL=http://llm-gateway:5055
      
      # DDD Architecture
      - DDD_ARCHITECTURE=true
      - DDD_CONFIG_FILE=config/ddd_config.yaml
      
      # Network resilience
      - HTTP_CONNECTION_POOL_SIZE=10
      - HTTP_MAX_KEEPALIVE_CONNECTIONS=5
      - HTTP_TIMEOUT=30
      - CIRCUIT_BREAKER_FAILURE_THRESHOLD=3
      - CIRCUIT_BREAKER_RECOVERY_TIMEOUT=45
      - RETRY_MAX_ATTEMPTS=2
      - RETRY_BACKOFF_FACTOR=2.0
    
    volumes:
      - ./:/app:ro
      - ./services/mcp-interpreter:/app/services/mcp-interpreter:rw
      - ./services/shared:/app/services/shared:ro
    
    working_dir: /app
    
    depends_on:
      redis:
        condition: service_healthy
      llm-gateway:
        condition: service_healthy
      log-collector:
        condition: service_started
    
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5100/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    
    networks:
      - hackathon_default
    
    profiles:
      - all
      - mcp_services
      - development
    
    restart: unless-stopped
```

### Complete MCP Services Docker Compose Block

```yaml
# ============================================================================
# MCP SERVICES
# ============================================================================

  mcp-interpreter:
    # ... (as above)
  
  mcp-orchestrator:
    build:
      context: .
      dockerfile: services/mcp-orchestrator/Dockerfile
    container_name: hackathon-mcp-orchestrator
    ports:
      - "8145:5200"
    environment:
      - PYTHONPATH=/app
      - SERVICE_NAME=mcp-orchestrator
      - SERVICE_API_PORT=5200
      - ENVIRONMENT=development
      - LOG_COLLECTOR_URL=http://log-collector:5080
      - LOG_COLLECTOR_ENABLED=true
      - REDIS_API_HOST=redis
      - LLM_GATEWAY_URL=http://llm-gateway:5055
      - MCP_GATEWAY_URL=http://mcp-gateway:5300
      - TEMPORAL_URL=temporal:7233  # If using Temporal
      - DDD_ARCHITECTURE=true
    volumes:
      - ./:/app:ro
      - ./services/mcp-orchestrator:/app/services/mcp-orchestrator:rw
      - ./services/shared:/app/services/shared:ro
    working_dir: /app
    depends_on:
      redis:
        condition: service_healthy
      llm-gateway:
        condition: service_healthy
      mcp-interpreter:
        condition: service_started
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5200/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - hackathon_default
    profiles:
      - all
      - mcp_services
    restart: unless-stopped
  
  mcp-gateway:
    build:
      context: .
      dockerfile: services/mcp-gateway/Dockerfile
    container_name: hackathon-mcp-gateway
    ports:
      - "8146:5300"
    environment:
      - PYTHONPATH=/app
      - SERVICE_NAME=mcp-gateway
      - SERVICE_API_PORT=5300
      - ENVIRONMENT=development
      - REDIS_API_HOST=redis
      - LOG_COLLECTOR_URL=http://log-collector:5080
      - LOG_COLLECTOR_ENABLED=true
      - DDD_ARCHITECTURE=true
    volumes:
      - ./:/app:ro
      - ./services/mcp-gateway:/app/services/mcp-gateway:rw
      - ./services/shared:/app/services/shared:ro
    working_dir: /app
    depends_on:
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5300/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - hackathon_default
    profiles:
      - all
      - mcp_services
    restart: unless-stopped
  
  mcp-provisioner:
    build:
      context: .
      dockerfile: services/mcp-provisioner/Dockerfile
    container_name: hackathon-mcp-provisioner
    ports:
      - "8147:5400"
    environment:
      - PYTHONPATH=/app
      - SERVICE_NAME=mcp-provisioner
      - SERVICE_API_PORT=5400
      - ENVIRONMENT=development
      - REDIS_API_HOST=redis
      - LOG_COLLECTOR_URL=http://log-collector:5080
      - LOG_COLLECTOR_ENABLED=true
      - DOCKER_HOST=unix:///var/run/docker.sock
      - MCP_DATA_PATH=/data/mcps
      - DDD_ARCHITECTURE=true
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock  # Docker-in-Docker
      - ./:/app:ro
      - ./services/mcp-provisioner:/app/services/mcp-provisioner:rw
      - ./services/shared:/app/services/shared:ro
      - mcp_data:/data/mcps
    working_dir: /app
    depends_on:
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5400/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - hackathon_default
    profiles:
      - all
      - mcp_services
    restart: unless-stopped
  
  mcp-registry:
    build:
      context: .
      dockerfile: services/mcp-registry/Dockerfile
    container_name: hackathon-mcp-registry
    ports:
      - "8148:5500"
    environment:
      - PYTHONPATH=/app
      - SERVICE_NAME=mcp-registry
      - SERVICE_API_PORT=5500
      - ENVIRONMENT=development
      - REDIS_API_HOST=redis
      - LOG_COLLECTOR_URL=http://log-collector:5080
      - LOG_COLLECTOR_ENABLED=true
      - DOC_STORE_URL=http://doc_store:5087
      - REGISTRY_STORAGE_PATH=/data/registry
      - DDD_ARCHITECTURE=true
    volumes:
      - ./:/app:ro
      - ./services/mcp-registry:/app/services/mcp-registry:rw
      - ./services/shared:/app/services/shared:ro
      - mcp_registry_data:/data/registry
    working_dir: /app
    depends_on:
      redis:
        condition: service_healthy
      doc_store:
        condition: service_started
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5500/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - hackathon_default
    profiles:
      - all
      - mcp_services
    restart: unless-stopped
  
  mcp-composer:
    build:
      context: .
      dockerfile: services/mcp-composer/Dockerfile
    container_name: hackathon-mcp-composer
    ports:
      - "8149:5600"
    environment:
      - PYTHONPATH=/app
      - SERVICE_NAME=mcp-composer
      - SERVICE_API_PORT=5600
      - ENVIRONMENT=development
      - REDIS_API_HOST=redis
      - LOG_COLLECTOR_URL=http://log-collector:5080
      - LOG_COLLECTOR_ENABLED=true
      - MCP_GATEWAY_URL=http://mcp-gateway:5300
      - DDD_ARCHITECTURE=true
    volumes:
      - ./:/app:ro
      - ./services/mcp-composer:/app/services/mcp-composer:rw
      - ./services/shared:/app/services/shared:ro
    working_dir: /app
    depends_on:
      redis:
        condition: service_healthy
      mcp-gateway:
        condition: service_started
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5600/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - hackathon_default
    profiles:
      - all
      - mcp_services
    restart: unless-stopped
  
  mcp-training-coordinator:
    build:
      context: .
      dockerfile: services/mcp-training-coordinator/Dockerfile
    container_name: hackathon-mcp-training-coordinator
    ports:
      - "8150:5700"
    environment:
      - PYTHONPATH=/app
      - SERVICE_NAME=mcp-training-coordinator
      - SERVICE_API_PORT=5700
      - ENVIRONMENT=development
      - REDIS_API_HOST=redis
      - LOG_COLLECTOR_URL=http://log-collector:5080
      - LOG_COLLECTOR_ENABLED=true
      - LLM_GATEWAY_URL=http://llm-gateway:5055
      - SOURCE_AGENT_URL=http://source-agent:5085
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
      - DDD_ARCHITECTURE=true
    volumes:
      - ./:/app:ro
      - ./services/mcp-training-coordinator:/app/services/mcp-training-coordinator:rw
      - ./services/shared:/app/services/shared:ro
    working_dir: /app
    depends_on:
      redis:
        condition: service_healthy
      llm-gateway:
        condition: service_healthy
      source-agent:
        condition: service_started
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5700/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - hackathon_default
    profiles:
      - all
      - mcp_services
    restart: unless-stopped

# ============================================================================
# VOLUMES
# ============================================================================

volumes:
  # ... existing volumes ...
  mcp_data:
    driver: local
  mcp_registry_data:
    driver: local
```

---

## Testing with Mock Data Generator

### Integration Testing Pattern

**Use `mock-data-generator` service for realistic test data:**

```python
# tests/integration/test_mcp_interpreter.py
import pytest
import httpx
from typing import Dict

@pytest.fixture
async def mock_data_client():
    """Client for mock-data-generator service."""
    async with httpx.AsyncClient(
        base_url="http://mock-data-generator:5065",
        timeout=30.0
    ) as client:
        yield client

@pytest.fixture
async def test_queries(mock_data_client) -> Dict:
    """Generate test queries using mock-data-generator."""
    response = await mock_data_client.post(
        "/generate",
        json={
            "type": "queries",
            "count": 10,
            "context": {
                "domain": "software_development",
                "complexity": "medium"
            }
        }
    )
    return response.json()

@pytest.mark.asyncio
async def test_parse_query_integration(test_queries):
    """Integration test: parse generated queries."""
    async with httpx.AsyncClient(
        base_url="http://mcp-interpreter:5100",
        timeout=30.0
    ) as client:
        for query in test_queries["queries"]:
            response = await client.post(
                "/query/parse",
                json={"query": query["text"]}
            )
            
            assert response.status_code == 200
            result = response.json()
            
            # Validate response structure
            assert "query_id" in result
            assert "intent" in result
            assert "confidence" in result
            assert result["confidence"] >= 0.0
            assert result["confidence"] <= 1.0
```

### Mock Data Generator Usage Examples

```python
# Generate mock GitHub data
async def generate_mock_github_data():
    async with httpx.AsyncClient(base_url="http://mock-data-generator:5065") as client:
        response = await client.post(
            "/generate",
            json={
                "type": "github",
                "subtype": "pull_requests",
                "count": 50,
                "context": {
                    "repo": "test-repo",
                    "team": "backend-team"
                }
            }
        )
        return response.json()

# Generate mock Confluence pages
async def generate_mock_confluence_data():
    async with httpx.AsyncClient(base_url="http://mock-data-generator:5065") as client:
        response = await client.post(
            "/generate",
            json={
                "type": "confluence",
                "subtype": "pages",
                "count": 20,
                "context": {
                    "space": "Engineering",
                    "topics": ["architecture", "design_patterns", "api_docs"]
                }
            }
        )
        return response.json()

# Generate mock Jira issues
async def generate_mock_jira_data():
    async with httpx.AsyncClient(base_url="http://mock-data-generator:5065") as client:
        response = await client.post(
            "/generate",
            json={
                "type": "jira",
                "subtype": "issues",
                "count": 100,
                "context": {
                    "project": "PROJECT",
                    "issue_types": ["Story", "Bug", "Epic"]
                }
            }
        )
        return response.json()
```

---

## Shared Libraries Usage

### Available Shared Components

**Location:** `services/shared/`

**Key modules to leverage:**

```python
# Domain layer
from services.shared.domain.repositories.base_repository import (
    BaseRepository, SqlRepository, InMemoryRepository
)
from services.shared.domain.services.base_service import (
    BaseService, CrudService
)
from services.shared.domain.entities.value_objects import (
    EmailAddress, Money, URL, DateRange
)

# Infrastructure layer
from services.shared.infrastructure.config import load_service_config
from services.shared.infrastructure.utilities.middleware import (
    setup_common_middleware, setup_cors, setup_logging
)
from services.shared.infrastructure.monitoring.health import (
    register_health_endpoints, HealthStatus
)
from services.shared.infrastructure.database.di.services import (
    get_database_connection, DatabaseType
)

# Presentation layer
from services.shared.presentation.api.responses import (
    create_success_response, create_error_response, StandardResponse
)
from services.shared.presentation.api.middleware import (
    add_request_id_middleware, add_error_handling_middleware
)
```

### Example: Using Shared Response Utilities

```python
# services/mcp-interpreter/main.py
from fastapi import FastAPI, HTTPException
from services.shared.presentation.api.responses import create_success_response, create_error_response
from services.shared.infrastructure.utilities.middleware import setup_common_middleware
from services.shared.infrastructure.monitoring.health import register_health_endpoints

app = FastAPI(
    title="MCP Interpreter Service",
    description="Query parsing and intent classification for MCP system",
    version="1.0.0"
)

# Setup common middleware (CORS, logging, request ID, error handling)
setup_common_middleware(app)

# Register standard health endpoints
register_health_endpoints(app)

@app.post("/query/parse")
async def parse_query(request: QueryRequest):
    try:
        result = await parse_query_use_case.execute(request)
        return create_success_response(
            data=result,
            message="Query parsed successfully"
        )
    except ValueError as e:
        return create_error_response(
            message=str(e),
            status_code=400,
            error_code="INVALID_QUERY"
        )
```

---

## Deployment & DevOps

### Running Individual Services

**Option 1: Via Docker Compose**
```bash
# Start just MCP Interpreter
docker-compose -f docker-compose.dev.yml up mcp-interpreter

# Start all MCP services
docker-compose -f docker-compose.dev.yml --profile mcp_services up

# Start with dependencies
docker-compose -f docker-compose.dev.yml up mcp-interpreter redis llm-gateway
```

**Option 2: Via Terminal (Development)**
```bash
# Navigate to service
cd services/mcp-interpreter

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export PYTHONPATH=/Users/mykalthomas/Documents/work/Hackathon
export SERVICE_NAME=mcp-interpreter
export SERVICE_API_PORT=5100
export LLM_GATEWAY_URL=http://localhost:8092  # External port
export REDIS_API_HOST=localhost
export ENVIRONMENT=development

# Run service
python main.py
```

### Service Startup Scripts

**Create `run.sh` for each service:**

```bash
#!/bin/bash
# services/mcp-interpreter/run.sh

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Set environment variables
export PYTHONPATH="/Users/mykalthomas/Documents/work/Hackathon"
export SERVICE_NAME="mcp-interpreter"
export SERVICE_API_PORT="${SERVICE_API_PORT:-5100}"
export LLM_GATEWAY_URL="${LLM_GATEWAY_URL:-http://localhost:8092}"
export REDIS_API_HOST="${REDIS_API_HOST:-localhost}"
export ENVIRONMENT="${ENVIRONMENT:-development}"

# Run service
uvicorn main:app --host 0.0.0.0 --port ${SERVICE_API_PORT} --reload
```

Make executable:
```bash
chmod +x services/mcp-interpreter/run.sh
```

### Testing Individual Services

```bash
# Run tests
cd services/mcp-interpreter
pytest tests/ -v --cov=. --cov-report=html

# Run specific test file
pytest tests/unit/domain/test_parsed_query.py -v

# Run integration tests (requires Docker)
docker-compose -f docker-compose.dev.yml up -d redis llm-gateway mock-data-generator
pytest tests/integration/ -v
```

---

## Summary Checklist

Before implementing any MCP service, verify:

- [ ] **DDD Architecture**: Layered structure (domain → application → infrastructure → presentation)
- [ ] **LLM Gateway**: Using `http://llm-gateway:5055` (NOT direct Ollama)
- [ ] **Shared Libraries**: Leveraging `services/shared/` components
- [ ] **OpenAPI Docs**: Full annotations (summary, description, response_model, responses, tags)
- [ ] **Docker Integration**: Service in `docker-compose.dev.yml` on `hackathon_default` network
- [ ] **Health Checks**: `/health` endpoint with proper checks
- [ ] **Testing**: >90% coverage, using `mock-data-generator` for integration tests
- [ ] **TDD**: Tests written before implementation
- [ ] **DRY & KISS**: No code duplication, simple solutions

---

**Next Steps:**

1. Read this guide thoroughly
2. Review example service structures in `services/orchestrator` or `services/analysis-service`
3. Start with MCP Interpreter service (simplest)
4. Follow TDD: Write tests → Implement → Refactor
5. Integrate with ecosystem incrementally

**Questions?** Refer to:
- `docs/service-standardization/patterns/coding-standards.md`
- `docs/architecture/DDD_MIGRATION.md`
- `services/shared/` for reusable components
- Existing services as reference implementations

---

**Document Version:** 1.0  
**Last Updated:** 2025-10-06  
**Status:** ✅ Production Standard - Mandatory Compliance

