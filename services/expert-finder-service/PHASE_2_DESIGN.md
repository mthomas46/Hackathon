# Phase 2: Design & Planning - expert-finder-service

**Date**: October 10, 2025  
**Status**: In Progress  
**Service**: expert-finder-service (Port: 5160)

---

## 📋 Domain Model

### Entities

#### `Expert`
```python
@dataclass(frozen=True)
class Expert:
    """Domain entity representing an expert/developer"""
    user_id: str
    name: str
    email: str
    role: str
    github_username: Optional[str]
    skills: List[str]
    topics: List[str]
    services: List[str]
    recent_activity: List[Activity]
    relevance_scores: Dict[str, float]  # Calculated scores by criteria
    
    def calculate_relevance_for_topic(self, topic: str) -> float:
        """Calculate relevance score for a specific topic"""
        pass
    
    def calculate_relevance_for_service(self, service: str) -> float:
        """Calculate relevance score for a specific service"""
        pass
```

#### `ExpertSearchResult`
```python
@dataclass
class ExpertSearchResult:
    """Aggregate root for expert search results"""
    query: ExpertQuery
    experts: List[ExpertMatch]
    total_found: int
    execution_time_ms: float
    scoring_breakdown: ScoringBreakdown
```

#### `ExpertMatch`
```python
@dataclass
class ExpertMatch:
    """Value object representing an expert match"""
    expert: Expert
    overall_score: float
    role_score: float
    topic_score: float
    service_score: float
    document_score: float
    explanation: str  # Human-readable explanation of match
```

### Value Objects

#### `ExpertQuery`
```python
@dataclass(frozen=True)
class ExpertQuery:
    """Value object for expert search query"""
    topics: List[str]
    services: List[str]
    role: Optional[str]
    limit: int = 10
    include_inactive: bool = False
```

#### `ScoringWeights`
```python
@dataclass(frozen=True)
class ScoringWeights:
    """Value object for scoring algorithm weights"""
    role_weight: float = 0.30  # 30%
    topic_weight: float = 0.40  # 40%
    service_weight: float = 0.20  # 20%
    document_weight: float = 0.10  # 10%
    
    def __post_init__(self):
        """Validate weights sum to 1.0"""
        total = (self.role_weight + self.topic_weight + 
                 self.service_weight + self.document_weight)
        if not (0.99 <= total <= 1.01):  # Allow small floating point error
            raise ValueError(f"Weights must sum to 1.0, got {total}")
```

#### `ScoringBreakdown`
```python
@dataclass
class ScoringBreakdown:
    """Value object showing scoring breakdown"""
    weights_used: ScoringWeights
    total_experts_evaluated: int
    filters_applied: List[str]
```

---

## 🏗️ Application Layer

### Use Cases

#### `FindExpertsByTopicUseCase`
```python
class FindExpertsByTopicUseCase:
    """Find experts with expertise in specific topics"""
    
    def __init__(
        self,
        user_repository: UserRepository,
        document_repository: DocumentRepository,
        scoring_service: RelevanceScoringService
    ):
        self.user_repository = user_repository
        self.document_repository = document_repository
        self.scoring_service = scoring_service
    
    async def execute(self, query: ExpertQuery) -> ExpertSearchResult:
        """Execute expert search"""
        pass
```

#### `FindExpertsByServiceUseCase`
```python
class FindExpertsByServiceUseCase:
    """Find experts working on specific services"""
    pass
```

#### `GetTeamExpertiseUseCase`
```python
class GetTeamExpertiseUseCase:
    """Analyze expertise distribution across a team"""
    pass
```

### Domain Services

#### `RelevanceScoringService`
```python
class RelevanceScoringService:
    """Domain service for calculating expert relevance scores"""
    
    def __init__(self, weights: ScoringWeights):
        self.weights = weights
    
    def calculate_relevance(
        self,
        expert: Expert,
        query: ExpertQuery
    ) -> ExpertMatch:
        """Calculate overall relevance score"""
        role_score = self._calculate_role_score(expert, query)
        topic_score = self._calculate_topic_score(expert, query)
        service_score = self._calculate_service_score(expert, query)
        document_score = self._calculate_document_score(expert, query)
        
        overall_score = (
            role_score * self.weights.role_weight +
            topic_score * self.weights.topic_weight +
            service_score * self.weights.service_weight +
            document_score * self.weights.document_score
        )
        
        return ExpertMatch(
            expert=expert,
            overall_score=overall_score,
            role_score=role_score,
            topic_score=topic_score,
            service_score=service_score,
            document_score=document_score,
            explanation=self._generate_explanation(...)
        )
```

---

## 🔌 Infrastructure Layer

### Repositories

#### `UserRepository` (Interface)
```python
class UserRepository(ABC):
    """Repository interface for user/expert data"""
    
    @abstractmethod
    async def get_all_users(self) -> List[Expert]:
        """Get all users/experts"""
        pass
    
    @abstractmethod
    async def get_user_by_id(self, user_id: str) -> Optional[Expert]:
        """Get user by ID"""
        pass
    
    @abstractmethod
    async def find_by_topics(self, topics: List[str]) -> List[Expert]:
        """Find users with specific topic expertise"""
        pass
```

#### `HttpUserRepository` (Implementation)
```python
class HttpUserRepository(UserRepository):
    """HTTP client implementation for user-store"""
    
    def __init__(self, user_store_url: str, client: httpx.AsyncClient):
        self.user_store_url = user_store_url
        self.client = client
    
    async def get_all_users(self) -> List[Expert]:
        """Call user-store GET /users endpoint"""
        try:
            response = await self.client.get(f"{self.user_store_url}/users")
            response.raise_for_status()
            data = response.json()
            return [self._map_to_expert(user) for user in data["users"]]
        except httpx.HTTPError as e:
            raise RepositoryError(f"Failed to fetch users: {e}")
```

#### `DocumentRepository` (Interface)
```python
class DocumentRepository(ABC):
    """Repository interface for document data"""
    
    @abstractmethod
    async def find_documents_by_author(self, user_id: str) -> List[Document]:
        """Find documents authored by user"""
        pass
```

---

## 🎨 Presentation Layer (API)

### Routes

#### Expert Search Routes (`/api/v1/experts`)

##### `POST /api/v1/experts/search`
**Description**: Search for experts by topics/services  
**Request Body**:
```json
{
  "topics": ["python", "fastapi"],
  "services": ["code-analyzer"],
  "role": "senior_developer",
  "limit": 10
}
```

**Response**:
```json
{
  "total_found": 5,
  "execution_time_ms": 45.2,
  "scoring_weights": {
    "role": 0.30,
    "topics": 0.40,
    "services": 0.20,
    "documents": 0.10
  },
  "experts": [
    {
      "user_id": "user-123",
      "name": "Alice Developer",
      "role": "senior_developer",
      "overall_score": 0.92,
      "score_breakdown": {
        "role": 0.95,
        "topics": 0.90,
        "services": 0.88,
        "documents": 0.95
      },
      "explanation": "Strong match: Exact role match, high topic relevance (2/2 topics), active on requested service",
      "contact": {
        "email": "alice@company.com",
        "github": "alice-dev"
      }
    }
  ]
}
```

##### `GET /api/v1/experts/topic/{topic}`
**Description**: Find experts for a specific topic  
**Response**: List of experts with relevance scores

##### `GET /api/v1/experts/service/{service}`
**Description**: Find experts working on a specific service  
**Response**: List of experts with contribution data

#### Team Analysis Routes (`/api/v1/teams`)

##### `GET /api/v1/teams/{team_id}/expertise`
**Description**: Analyze team expertise distribution  
**Response**: Expertise gaps, coverage, recommendations

##### `POST /api/v1/teams/find-sme`
**Description**: Find subject matter expert for a topic  
**Response**: Top expert with justification

#### Standard Endpoints

##### `GET /health`
**Description**: Health check  
**Response**: `{"status": "healthy", "dependencies": {"user-store": "connected"}}`

##### `GET /about-me`
**Description**: Service metadata  
**Response**: Service description, capabilities, dependencies

##### `GET /endpoints`
**Description**: List all endpoints  
**Response**: Array of endpoint descriptions

##### `GET /provider-consumer`
**Description**: Service relationships  
**Response**: 
```json
{
  "providers": ["user-store"],
  "consumers": [],
  "optional_providers": ["doc-store", "external-service-store"]
}
```

##### `GET /demos`
**Description**: List executable demos  
**Response**: Array of demo descriptions

##### `POST /run-demo`
**Description**: Execute a demo  
**Body**: `{"demo_id": "basic-search"}`

---

## 🗂️ Proposed Directory Structure

```
expert-finder-service/
├── domain/
│   ├── __init__.py
│   ├── entities/
│   │   ├── __init__.py
│   │   ├── expert.py
│   │   └── expert_match.py
│   ├── value_objects/
│   │   ├── __init__.py
│   │   ├── expert_query.py
│   │   ├── scoring_weights.py
│   │   └── scoring_breakdown.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── relevance_scoring_service.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── user_repository.py
│   │   └── document_repository.py
│   └── exceptions/
│       ├── __init__.py
│       └── expert_finder_exceptions.py
├── application/
│   ├── __init__.py
│   ├── use_cases/
│   │   ├── __init__.py
│   │   ├── find_experts_by_topic.py
│   │   ├── find_experts_by_service.py
│   │   └── get_team_expertise.py
│   └── dtos/
│       ├── __init__.py
│       ├── expert_search_request.py
│       └── expert_search_response.py
├── infrastructure/
│   ├── __init__.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── http_user_repository.py
│   │   └── http_document_repository.py
│   └── config/
│       ├── __init__.py
│       └── settings.py
├── presentation/
│   ├── __init__.py
│   └── api/
│       ├── __init__.py
│       ├── routes/
│       │   ├── __init__.py
│       │   ├── expert_routes.py
│       │   ├── team_routes.py
│       │   ├── standard_routes.py
│       │   └── demo_routes.py
│       ├── schemas/
│       │   ├── __init__.py
│       │   ├── expert_schemas.py
│       │   └── team_schemas.py
│       └── dependencies.py
├── tests/
│   ├── unit/
│   │   ├── domain/
│   │   ├── application/
│   │   ├── infrastructure/
│   │   └── presentation/
│   ├── integration/
│   └── e2e/
├── main.py
├── CONFIG.md (will create)
├── TESTING_GUIDE.md (will create in Phase 5)
├── E2E_TEST_PLAN.md (will create in Phase 10)
├── DEMO_PLAN.md (will create in Phase 10)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pytest.ini
└── README.md
```

---

## 🎯 Test Plan (High-Level)

### Unit Tests (60% of test suite)
- **Domain Layer**:
  - Expert entity methods (relevance calculation)
  - Value objects (validation, immutability)
  - Relevance scoring service (all scoring algorithms)
- **Application Layer**:
  - Use cases (with mocked repositories)
  - DTOs (serialization/deserialization)
- **Infrastructure Layer**:
  - Repository implementations (with mocked HTTP)
- **Presentation Layer**:
  - Route handlers (with mocked use cases)
  - Request/response schemas

### Integration Tests (30%)
- Repository → External Services (user-store, doc-store)
- Use Case → Repository → Scoring Service (full flow)
- API → Use Case → Repository (end-to-end API flow)

### E2E Tests (10%)
- Full expert search workflow (with test user-store data)
- Team expertise analysis workflow
- Error scenarios (service down, invalid data)

---

## 🔧 Configuration Plan

### Environment Variables

```bash
# Service Configuration
SERVICE_NAME=expert-finder-service
SERVICE_PORT=5160
ENVIRONMENT=development  # development, test, staging, production

# Dependency Services
USER_STORE_URL=http://localhost:5110  # REQUIRED
DOC_STORE_URL=http://localhost:5100  # Optional
EXTERNAL_SERVICE_STORE_URL=http://localhost:5150  # Optional

# Scoring Algorithm Configuration
SCORING_ROLE_WEIGHT=0.30
SCORING_TOPIC_WEIGHT=0.40
SCORING_SERVICE_WEIGHT=0.20
SCORING_DOCUMENT_WEIGHT=0.10

# HTTP Client Configuration
HTTP_TIMEOUT_SECONDS=30
HTTP_MAX_RETRIES=3
HTTP_POOL_SIZE=10

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
LOG_COLLECTOR_URL=http://localhost:5140

# Performance
CACHE_TTL_SECONDS=300  # 5 minutes
MAX_RESULTS=100
```

### Configuration Profiles

#### Development
- Debug logging
- Mock external services (optional)
- Small connection pools
- Detailed error messages

#### Production
- Info logging
- Real external services
- Large connection pools (50 connections)
- Sanitized error messages
- Caching enabled (5 min TTL)

---

## 🚀 Migration Strategy

### Backward Compatibility

**Current Endpoints** (main.py monolith):
```
GET  /find-expert - Find experts by topic/service
GET  /topic/{topic} - Find experts by topic
GET  /service/{service} - Find experts by service
GET  /find-sme - Find subject matter expert
POST /team/teammates - Find teammates
GET  /team/expertise - Get team expertise
```

**New Endpoints** (v1 API):
```
POST /api/v1/experts/search - Unified search (replaces /find-expert)
GET  /api/v1/experts/topic/{topic} - (same functionality)
GET  /api/v1/experts/service/{service} - (same functionality)
POST /api/v1/teams/find-sme - (enhanced with justification)
POST /api/v1/teams/teammates - (same functionality)
GET  /api/v1/teams/{team_id}/expertise - (enhanced with gaps)
```

**Strategy**:
1. **Phase 3**: Implement v1 API with new DDD structure
2. **Phase 3**: Keep old endpoints (delegate to v1 API internally)
3. **Phase 3**: Add deprecation warnings to old endpoints
4. **Phase 4**: Test both old and new endpoints
5. **Phase 6**: Document migration path in README
6. **Phase 11 (Optional)**: Remove old endpoints after ecosystem migrates

---

## 📊 Performance Targets

| Metric | Target | Rationale |
|--------|--------|-----------|
| Search Response Time (P95) | < 200ms | Most searches use cached user data |
| Search Response Time (P99) | < 500ms | With external service calls |
| Throughput | > 50 req/s | Typical load |
| Memory Usage | < 256 MB | Lightweight service |
| Cold Start Time | < 5 seconds | FastAPI starts fast |
| Health Check Response | < 100ms | Critical for monitoring |

---

## ✅ Phase 2 Deliverables Checklist

- [x] Domain Model designed (entities, value objects, services)
- [x] Application Layer designed (use cases, DTOs)
- [x] Infrastructure Layer designed (repositories, external services)
- [x] Presentation Layer designed (routes, schemas)
- [x] Test Plan outlined (unit, integration, E2E)
- [x] Configuration strategy defined (env vars, profiles)
- [x] Migration strategy defined (backward compatibility)
- [x] Performance targets set
- [ ] OpenAPI specification generated (will do in Phase 3)
- [ ] CONFIG.md created (next step)
- [ ] Service Makefile created (next step)
- [ ] Port conflict check (next step)
- [ ] MASTER_CONFIGURATION_REGISTRY.md updated (next step)

---

**Status**: Design complete, ready for CONFIG.md creation and Phase 2 optimization

