# Dependency Map - expert-finder-service

**Date**: October 10, 2025  
**Service**: expert-finder-service v1.0.0

---

## 📊 Service Dependencies

### Upstream Dependencies (Services We Consume)

| Service | Type | Required | Purpose | Endpoints Used | Relationship |
|---------|------|----------|---------|----------------|--------------|
| **user-store** | Internal | ✅ **YES** | Primary user data source | GET `/users`, GET `/users/{id}`, GET `/teams/{id}` | Provider |
| **doc-store** | Internal | ⚠️ Optional | Document authorship verification | GET `/documents/by-author/{user_id}` | Provider |
| **external-service-store** | Internal | ⚠️ Optional | Service expertise validation | GET `/services/{name}/contributors` | Provider |
| **llm-gateway** | Internal | ⚪ Future | Advanced query understanding | POST `/llm/query` | Provider (planned) |

### Downstream Dependencies (Services That Consume Us)

| Service | Purpose | Endpoints Used | Relationship |
|---------|---------|----------------|--------------|
| **None currently** | N/A | N/A | - |
| *(Potential)* **dashboard** | Display experts | GET `/experts/find`, GET `/experts/by-topic/*` | Consumer (future) |
| *(Potential)* **recommendation-engine** | Expert recommendations | GET `/experts/sme/*`, GET `/experts/teammates/*` | Consumer (future) |

---

## 🔄 Data Flow

### Primary Flow: Expert Search

```
User/Client
    ↓ POST /experts/find {"query": "Who knows Python?"}
expert-finder-service
    ↓ GET /users (query all users)
user-store
    ↓ Returns list of users with metadata
expert-finder-service
    ↓ (Scores each user based on query)
    ↓ (Optional) GET /documents/by-author/{user_id}
doc-store
    ↓ (Optional) Returns document count for verification
expert-finder-service
    ↓ Returns ranked experts
User/Client
```

### Secondary Flow: Topic-Based Search

```
User/Client
    ↓ GET /experts/by-topic/React
expert-finder-service
    ↓ GET /users
user-store
    ↓ Returns users
expert-finder-service
    ↓ Filters by topic_interests
    ↓ Ranks by relevance
    ↓ Returns top experts
User/Client
```

### Tertiary Flow: Service Expertise

```
User/Client
    ↓ GET /experts/by-service/payment-service
expert-finder-service
    ↓ GET /services/payment-service/contributors
external-service-store
    ↓ Returns list of user IDs
expert-finder-service
    ↓ GET /users/{id} (for each contributor)
user-store
    ↓ Returns user details
expert-finder-service
    ↓ Returns service experts
User/Client
```

---

## 🌐 Network Configuration

### Service Network
- **Network**: `hackathon_default` (172.20.0.0/16)
- **Service Port**: 5160
- **Protocol**: HTTP

### Service URLs

#### Development
```bash
USER_STORE_URL=http://localhost:5150
DOC_STORE_URL=http://localhost:5087
EXTERNAL_SERVICE_STORE_URL=http://localhost:5140
LLM_GATEWAY_URL=http://localhost:8100  # Future
```

#### Docker Compose
```bash
USER_STORE_URL=http://user-store:5150
DOC_STORE_URL=http://doc-store:5087
EXTERNAL_SERVICE_STORE_URL=http://external-service-store:5140
LLM_GATEWAY_URL=http://llm-gateway:8100  # Future
```

---

## 📦 Dependency Details

### 1. user-store (PRIMARY, REQUIRED)

**Criticality**: ⚠️ **CRITICAL** - Service cannot function without this

**API Contract**:
```
GET /users
- Returns list of all users with metadata
- Response: [{user_id, username, display_name, role, topic_interests, services, tags, team_id}]

GET /users/{user_id}
- Returns single user details
- Response: {user_id, username, display_name, role, ...}

GET /teams/{team_id}
- Returns team information
- Response: {team_id, name, members: [user_id]}
```

**Failure Impact**:
- ❌ Service completely non-functional
- ❌ All endpoints return errors
- ⚠️ Need circuit breaker or fallback

**Mitigation**:
- Health check for user-store availability
- Return 503 if user-store unavailable
- Cache frequently accessed users (future)

---

### 2. doc-store (OPTIONAL)

**Criticality**: ⚪ **LOW** - Service degrades gracefully

**API Contract**:
```
GET /documents/by-author/{user_id}
- Returns documents created/updated by user
- Response: {documents: [{doc_id, title, author_id}], count: N}
```

**Failure Impact**:
- ✅ Service continues to function
- ⚠️ Document authorship counts unavailable
- ⚠️ Slightly lower scoring accuracy

**Mitigation**:
- Graceful degradation
- Log warning if doc-store unavailable
- Skip document scoring factor

---

### 3. external-service-store (OPTIONAL)

**Criticality**: ⚪ **LOW** - Service degrades gracefully

**API Contract**:
```
GET /services/{service_name}/contributors
- Returns list of users who contributed to service
- Response: {service_name, contributors: [user_id]}
```

**Failure Impact**:
- ✅ Service continues to function
- ⚠️ Service-based expert search degraded
- ⚠️ Service expertise verification unavailable

**Mitigation**:
- Graceful degradation
- Fall back to user-store service subscriptions
- Log warning if unavailable

---

### 4. llm-gateway (FUTURE, OPTIONAL)

**Criticality**: ⚪ **LOW** - Enhancement

**Planned API Contract**:
```
POST /llm/query
- Advanced natural language query understanding
- Request: {query: "Who can help with React performance?"}
- Response: {parsed_query: {topics: ["React", "performance"], ...}}
```

**Benefits**:
- Better query understanding
- Synonym expansion
- Intent detection

---

## 🔒 Service Isolation

### Can Run Standalone?
**⚠️ NO** - Requires user-store

### Minimal Dependencies
For basic functionality, requires:
1. ✅ **user-store** (MUST have)
2. ⚪ doc-store (optional)
3. ⚪ external-service-store (optional)

### Docker Compose Minimal Setup
```yaml
services:
  user-store:
    # ... user-store config
    
  expert-finder-service:
    # ... expert-finder config
    depends_on:
      - user-store
```

---

## 📊 API Call Patterns

### Frequency Analysis

| Endpoint | Calls to user-store | Calls to doc-store | Calls to external-service-store |
|----------|---------------------|--------------------|---------------------------------|
| **POST /experts/find** | 1 (list all) + 0-N (optional enrichment) | 0-N (per matched user) | 0 |
| **GET /experts/by-topic/{topic}** | 1 (list all) | 0-N (per matched user) | 0 |
| **GET /experts/by-service/{service}** | 1-N (per contributor) | 0 | 1 (get contributors) |
| **GET /experts/sme/{area}** | 1 (list all) | N (verify document threshold) | 0 |
| **GET /experts/teammates/{user_id}** | 1 (list all) + 1 (get user) | 0 | 0 |
| **GET /teams/{team_id}/expertise** | 1 (get team) | 0 | 0 |

### Performance Considerations
- **user-store**: Called on EVERY request → Critical performance dependency
- **doc-store**: Called conditionally → Lower impact
- **external-service-store**: Called rarely → Minimal impact

### Optimization Opportunities
1. **Caching**: Cache user-store responses (5-10 minute TTL)
2. **Batch Requests**: Batch multiple user lookups into single call
3. **Pagination**: Don't fetch all users at once (implement pagination)

---

## 🚨 Failure Scenarios

### Scenario 1: user-store Unavailable
```
Impact: ❌ CRITICAL - Service cannot function
Response: 503 Service Unavailable
Mitigation: 
  - Health check catches this
  - Return clear error message
  - Future: Implement cache fallback
```

### Scenario 2: doc-store Unavailable
```
Impact: ⚠️ DEGRADED - Service continues with reduced accuracy
Response: 200 OK (with warning in logs)
Mitigation:
  - Skip document scoring
  - Continue with other factors
  - Log warning for monitoring
```

### Scenario 3: external-service-store Unavailable
```
Impact: ⚠️ DEGRADED - Service expertise degraded
Response: 200 OK (fall back to user subscriptions)
Mitigation:
  - Use user-store service subscription data
  - Log warning
  - Return partial results
```

### Scenario 4: All Services Unavailable
```
Impact: ❌ CRITICAL - Complete failure
Response: 503 Service Unavailable
Message: "Required dependencies unavailable"
```

---

## 🔍 Health Check Dependencies

### Health Endpoint Response
```json
{
  "status": "healthy | degraded | unhealthy",
  "service": "expert-finder-service",
  "version": "1.0.0",
  "dependencies": {
    "user_store": {
      "url": "http://user-store:5150",
      "status": "healthy | unavailable",
      "required": true
    },
    "doc_store": {
      "url": "http://doc-store:5087",
      "status": "healthy | unavailable",
      "required": false
    },
    "external_service_store": {
      "url": "http://external-service-store:5140",
      "status": "healthy | unavailable",
      "required": false
    }
  }
}
```

### Health Status Logic
- **healthy**: All required dependencies available
- **degraded**: Required dependencies OK, optional ones unavailable
- **unhealthy**: Required dependencies (user-store) unavailable

---

## 📝 Integration Points Summary

### Provider Services (We Consume)
1. ✅ **user-store** (required) - User data
2. ⚪ **doc-store** (optional) - Document verification
3. ⚪ **external-service-store** (optional) - Service contributors
4. ⚪ **llm-gateway** (future) - Query understanding

### Consumer Services (Consume Us)
- None currently implemented
- Potential: dashboards, recommendation engines

### Self-Contained?
**NO** - Requires user-store to function

### Ecosystem Role
**Query & Aggregation Service** - Queries multiple services, aggregates data, applies business logic (scoring), returns refined results

---

*Document Version: 1.0*  
*Created: October 10, 2025*  
*Part of Phase 1: Audit & Analysis*

