# Expert Finder Service

An ecosystem-level microservice for intelligent user discovery and subject matter expert identification.

## Overview

The Expert Finder Service provides smart, relevance-based user search capabilities across the ecosystem. It queries the user-store and analyzes user data, relationships, and document associations to identify relevant experts, SMEs, and potential collaborators.

## Features

- **Natural Language Queries**: "Who knows Python backend development?"
- **Topic-Based Expert Search**: Find users by technology or domain
- **Service-Based Expert Search**: Find users who worked on specific services
- **Subject Matter Expert Identification**: High-bar expert search with document threshold
- **Teammate Discovery**: Find potential collaborators based on shared interests
- **Team Expertise Summaries**: Aggregate team capabilities and knowledge areas

## Architecture

- **Tightly Coupled (Functionally)**: Primarily queries user-store data
- **Architecturally Independent**: Runs in its own Docker container
- **Stateless**: No persistent storage, queries other services
- **Horizontally Scalable**: Can run multiple instances

## API Endpoints

### POST `/experts/find`
Natural language expert search.

**Request:**
```json
{
  "query": "Who knows Python backend development?",
  "max_results": 5,
  "team_id": "team_123",  // optional
  "exclude_team": false,   // optional
  "min_score": 0.1         // optional
}
```

**Response:**
```json
{
  "query": "Who knows Python backend development?",
  "experts": [
    {
      "user_id": "user_123",
      "display_name": "Sarah Chen",
      "username": "sarah.chen",
      "relevance_score": 0.85,
      "explanation": "Matched on: Role: developer, Topic expertise: Python, Backend...",
      "evidence": ["Role: developer", "Topic expertise: Python, Backend", "15 related documents"],
      "metadata": {
        "role": "developer",
        "topics": ["Python", "Backend", "APIs"],
        "services": ["user-service", "auth-service"],
        "document_count": 15,
        "team_id": "team_123"
      }
    }
  ],
  "total_candidates": 6,
  "execution_time_ms": 12.5
}
```

### GET `/experts/by-topic/{topic}`
Find experts for a specific topic.

**Example:** `/experts/by-topic/React?max_results=5`

### GET `/experts/by-service/{service}`
Find users who worked on a specific service.

**Example:** `/experts/by-service/payment-service`

### GET `/experts/sme/{area}`
Find subject matter experts (requires minimum document threshold).

**Example:** `/experts/sme/Python?min_documents=5&max_results=3`

### GET `/experts/teammates/{user_id}`
Find potential teammates for a user.

**Example:** `/experts/teammates/user_123?max_results=5`

### GET `/teams/{team_id}/expertise`
Get expertise summary for a team.

**Example:** `/teams/team_123/expertise`

## Relevance Scoring Algorithm

Multi-factor scoring (0.0 to 1.0):

1. **Role Matching (30% weight)**
   - Matches user's role against query keywords
   
2. **Topic/Interest Matching (40% weight)**
   - Strongest signal for expertise
   - User's `topic_interests` matched against query
   
3. **Service Subscriptions (20% weight)**
   - Services user has worked on
   
4. **Document Relationships (10% weight)**
   - Actual work: created/updated/commented documents
   - Shows real contribution, not just claims
   
5. **User Tags (bonus)**
   - Inferred expertise from document analysis
   
6. **Name Matching (bonus)**
   - Username or display name contains query terms

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVICE_PORT` | `5160` | Port the service listens on |
| `USER_STORE_URL` | `http://localhost:5150` | User store service URL |
| `DOC_STORE_URL` | `http://localhost:5087` | Document store service URL |
| `EXTERNAL_SERVICE_STORE_URL` | `http://localhost:5140` | External service store URL |
| `LLM_GATEWAY_URL` | `http://localhost:8100` | LLM gateway URL (future) |

## Running Standalone

### Local Development
```bash
cd services/expert-finder-service
pip install -r requirements.txt
python main.py
```

Service will start on `http://localhost:5160`

### Docker
```bash
# Build image
docker build -t expert-finder-service:latest .

# Run container
docker run -p 5160:5160 \
  -e USER_STORE_URL=http://user-store:5150 \
  expert-finder-service:latest
```

## Running with Ecosystem

The service is included in `docker-compose.dev.yml`:

```bash
# Start entire ecosystem
docker-compose -f docker-compose.dev.yml up -d

# Start just expert-finder and dependencies
docker-compose -f docker-compose.dev.yml up -d user-store expert-finder-service
```

## Health Check

```bash
curl http://localhost:5160/health
```

Response:
```json
{
  "status": "healthy",
  "service": "expert-finder-service",
  "version": "1.0.0",
  "timestamp": "2025-01-04T10:30:00Z",
  "dependencies": {
    "user_store": "http://localhost:5150",
    "doc_store": "http://localhost:5087",
    "external_service_store": "http://localhost:5140"
  }
}
```

## Dependencies

- **user-store**: Primary data source for user information
- **doc-store**: (Optional) For document authorship verification
- **external-service-store**: (Optional) For service expertise validation

## Future Enhancements

- [ ] LLM integration via llm-gateway for advanced query understanding
- [ ] Caching layer for frequently queried experts
- [ ] Real-time updates when user data changes
- [ ] Machine learning-based relevance scoring
- [ ] Collaboration pattern analysis
- [ ] Expert recommendation engine
- [ ] GraphQL API support

## Monitoring

Key metrics to monitor:
- Query response time (target: < 50ms)
- User-store availability
- Expert match success rate
- Query complexity vs. response time
- Cache hit rate (when implemented)

## License

Part of the Hackathon microservices ecosystem.

