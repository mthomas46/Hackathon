# LLM Gateway Service

Navigation: [Home](../../README.md) · [Architecture](../../docs/architecture/) · [Testing](../../docs/guides/TESTING_GUIDE.md) · [Services](../README_SERVICES.md)
Tests: [tests/unit/llm_gateway](../../tests/unit/llm_gateway)

## Overview

The **LLM Gateway** is a centralized, secure, and intelligent access point for all Large Language Model operations in the LLM Documentation Ecosystem. It acts as a service mesh that provides:

- **Unified API** for all LLM providers (Ollama, OpenAI, Anthropic, AWS Bedrock, Grok)
- **Intelligent Routing** based on content sensitivity, cost optimization, and performance
- **Security-Aware Processing** with automatic provider selection for sensitive content
- **Caching & Optimization** to reduce costs and improve response times
- **Comprehensive Metrics** for monitoring usage, costs, and performance
- **Rate Limiting** to prevent abuse and manage resource utilization

## Key Features

### 🔀 Intelligent Provider Routing
- Automatic selection of optimal LLM provider based on content analysis
- Cost optimization with smart provider switching
- Security-aware routing for sensitive content
- Performance-based load balancing

### 🔒 Security Integration
- Content analysis for sensitive information detection
- Automatic routing to secure providers (Ollama, Bedrock) for confidential content
- Compliance with security policies and regulations
- Audit trails for all LLM interactions

### 💾 Smart Caching
- Response caching with TTL-based expiration
- Pattern-based cache clearing
- Cache analytics and hit rate monitoring
- Memory-efficient cache management

### 📊 Comprehensive Metrics
- Real-time usage tracking by provider
- Cost analysis and optimization insights
- Performance monitoring and bottleneck detection
- Error rate and success rate tracking

### 🛡️ Rate Limiting
- User-specific rate limits with burst protection
- Provider-specific limits to respect API quotas
- Global rate limiting for system protection
- Cooldown periods for abuse prevention

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   User Request  │───▶│  LLM Gateway     │───▶│  LLM Provider  │
│                 │    │                  │    │  (Ollama/OpenAI │
└─────────────────┘    │  ┌─────────────┐ │    │   /Anthropic/   │
                       │  │ Provider    │ │    │   Bedrock/Grok) │
                       │  │ Router      │ │    └─────────────────┘
                       │  └─────────────┘ │
                       │  ┌─────────────┐ │
                       │  │ Security    │ │
                       │  │ Filter      │ │
                       │  └─────────────┘ │
                       │  ┌─────────────┐ │
                       │  │ Cache       │ │
                       │  │ Manager     │ │
                       │  └─────────────┘ │
                       │  ┌─────────────┐ │
                       │  │ Metrics     │ │
                       │  │ Collector   │ │
                       │  └─────────────┘ │
                       │  ┌─────────────┐ │
                       │  │ Rate        │ │
                       │  │ Limiter     │ │
                       │  └─────────────┘ │
                       └──────────────────┘
```

## API Endpoints

### Core LLM Operations

#### `POST /query`
Execute a generic LLM query with intelligent provider routing.

**Request:**
```json
{
  "prompt": "Summarize the following content:",
  "context": "Additional context information",
  "provider": "auto",  // Optional: "auto", "ollama", "openai", "anthropic", "bedrock", "grok"
  "model": "gpt-4o",   // Optional: specific model
  "temperature": 0.7,  // Optional: 0.0-1.0
  "max_tokens": 1024,  // Optional: maximum response length
  "user_id": "user123", // Optional: for tracking
  "force_refresh": false // Optional: skip cache
}
```

**Response:**
```json
{
  "response": "Generated LLM response text",
  "provider": "openai",
  "tokens_used": 156,
  "processing_time": 2.34,
  "cost": 0.0047,
  "cached": false,
  "correlation_id": "gw-1234567890"
}
```

#### `POST /chat`
Conversational LLM interaction with conversation memory.

**Request:**
```json
{
  "prompt": "Tell me more about this topic",
  "context": "Previous conversation context",
  "conversation_id": "conv_123",
  "user_id": "user123"
}
```

#### `POST /embeddings`
Generate text embeddings for semantic search and similarity.

**Request:**
```json
{
  "text": "Text to embed",
  "model": "text-embedding-ada-002",
  "provider": "openai",
  "user_id": "user123"
}
```

**Response:**
```json
{
  "embeddings": [0.123, 0.456, ...],
  "model": "text-embedding-ada-002",
  "provider": "openai",
  "dimensions": 1536
}
```

#### `POST /stream`
Stream LLM responses for real-time interaction.

Returns Server-Sent Events (SSE) stream:
```
data: {"chunk": "The answer", "finished": false}
data: {"chunk": " is 42", "finished": true}
data: [DONE]
```

### Management Endpoints

#### `GET /providers`
List available LLM providers and their status.

**Response:**
```json
{
  "providers": [
    {
      "name": "ollama",
      "type": "local",
      "model": "llama3",
      "security_level": "high",
      "cost_per_token": 0.0,
      "status": "available"
    },
    {
      "name": "openai",
      "type": "cloud",
      "model": "gpt-4o",
      "security_level": "medium",
      "cost_per_token": 0.00003,
      "status": "available"
    }
  ]
}
```

#### `GET /metrics`
Get comprehensive usage metrics and performance statistics.

**Response:**
```json
{
  "total_requests": 1250,
  "requests_by_provider": {
    "ollama": 800,
    "openai": 350,
    "anthropic": 100
  },
  "total_tokens_used": 45670,
  "total_cost": 1.2345,
  "average_response_time": 2.34,
  "cache_hit_rate": 0.15,
  "error_rate": 2.5,
  "uptime_percentage": 99.9
}
```

#### `POST /cache/clear`
Clear LLM response cache.

**Request:**
```json
{
  "pattern": "user123_*",  // Optional: pattern to match
  "user_id": "user123"     // Optional: clear for specific user
}
```

**Response:**
```json
{
  "entries_cleared": 15,
  "pattern": "user123_*"
}
```

#### `GET /health/detailed`
Detailed health check including provider status.

**Response:**
```json
{
  "service": "healthy",
  "version": "1.0.0",
  "uptime": 86400,
  "providers": {
    "ollama": {
      "available": true,
      "status": "healthy",
      "last_checked": 1703123456.789
    },
    "openai": {
      "available": true,
      "status": "healthy",
      "last_checked": 1703123456.789
    }
  },
  "cache": {
    "status": "healthy",
    "total_entries": 234,
    "total_size_mb": 12.5
  },
  "rate_limiter": {
    "active_users": 45,
    "global_requests_last_minute": 23
  },
  "timestamp": 1703123456.789
}
```

## Configuration

### Environment Variables

#### Core Configuration
```bash
# Service
LLM_GATEWAY_PORT=5055
LLM_GATEWAY_HOST=0.0.0.0

# Provider Endpoints
OLLAMA_ENDPOINT=http://ollama-consistency:11434
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here
BEDROCK_ENDPOINT=http://bedrock-proxy:7090/invoke
GROK_API_KEY=grok-your-key-here

# Security
SENSITIVE_KEYWORDS=password,secret,token,key,credential
SENSITIVITY_THRESHOLD=0.7
SECURE_ONLY_MODELS=ollama,bedrock
ALL_PROVIDERS=bedrock,ollama,openai,anthropic,grok

# Caching
CACHE_MAX_SIZE=1000
CACHE_DEFAULT_TTL=3600
CACHE_CLEANUP_INTERVAL=300

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_REQUESTS_PER_HOUR=1000
RATE_LIMIT_TOKENS_PER_MINUTE=50000
RATE_LIMIT_BURST_LIMIT=10
RATE_LIMIT_COOLDOWN_SECONDS=60
```

### Service-Specific Configuration

Create `services/llm-gateway/config.yaml`:

```yaml
# LLM Gateway specific configuration
server:
  port: 5055
  host: 0.0.0.0

# Provider configurations
providers:
  ollama:
    model: llama3
    endpoint: ${OLLAMA_ENDPOINT}
    timeout: 60
    cost_per_token: 0.0
    security_level: high

  openai:
    model: gpt-4o
    api_key: ${OPENAI_API_KEY}
    timeout: 30
    cost_per_token: 0.00003
    security_level: medium

  anthropic:
    model: claude-3.5-sonnet
    api_key: ${ANTHROPIC_API_KEY}
    timeout: 30
    cost_per_token: 0.000015
    security_level: medium

  bedrock:
    model: anthropic.claude-3-sonnet-20240229-v1:0
    endpoint: ${BEDROCK_ENDPOINT}
    timeout: 60
    cost_per_token: 0.000015
    security_level: high

  grok:
    model: grok-1
    api_key: ${GROK_API_KEY}
    timeout: 30
    cost_per_token: 0.00001
    security_level: medium

# Rate limiting rules
rate_limiting:
  default:
    requests_per_minute: 60
    requests_per_hour: 1000
    tokens_per_minute: 50000
    burst_limit: 10
    cooldown_seconds: 60

  premium_user:
    requests_per_minute: 120
    requests_per_hour: 5000
    tokens_per_minute: 200000
    burst_limit: 20
    cooldown_seconds: 30

# Security settings
security:
  sensitive_keywords:
    - password
    - secret
    - token
    - key
    - credential
    - confidential
    - internal

  sensitivity_threshold: 0.7
  auto_classification: true

# Cache settings
cache:
  max_size: 1000
  default_ttl: 3600
  cleanup_interval: 300
  enable_compression: true

# Metrics settings
metrics:
  enable_detailed_logging: true
  retention_days: 30
  enable_cost_tracking: true
```

## Usage Examples

### Basic Query
```bash
curl -X POST "http://localhost:5055/query" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain quantum computing in simple terms",
    "temperature": 0.7,
    "max_tokens": 500
  }'
```

### Sensitive Content Query
```bash
curl -X POST "http://localhost:5055/query" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Analyze this internal API key: sk-1234567890abcdef",
    "user_id": "developer123"
  }'
# Automatically routes to secure provider (Ollama/Bedrock)
```

### Streaming Response
```bash
curl -X POST "http://localhost:5055/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write a short story about AI",
    "provider": "openai"
  }'
```

### Cache Management
```bash
# Clear all cache
curl -X POST "http://localhost:5055/cache/clear"

# Clear cache for specific user
curl -X POST "http://localhost:5055/cache/clear" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123"}'
```

### Metrics Monitoring
```bash
# Get overall metrics
curl "http://localhost:5055/metrics"

# Get detailed health status
curl "http://localhost:5055/health/detailed"
```

## Integration with Ecosystem

### 🔗 Comprehensive Service Integrations

The LLM Gateway is fully integrated with all major ecosystem services:

#### Core Services Integration

**1. Document Store (`/integrations/doc_store/{operation}`)**
- **Store LLM Results**: Save LLM interactions and responses
- **Retrieve Context**: Get relevant documents for enhanced prompting
- **Search Documents**: Find contextually relevant information
- **Integration Module**: `services/llm-gateway/modules/service_integrations.py`

**2. Prompt Store (`/integrations/prompt_store/{operation}`)**
- **Get Optimized Prompts**: Retrieve optimized prompts for tasks
- **Store New Prompts**: Save improved prompt templates
- **Category-Based Retrieval**: Get prompts by category
- **Integration Module**: `services/llm-gateway/modules/service_integrations.py`

**3. Memory Agent (`/integrations/memory_agent/{operation}`)**
- **Store Interactions**: Save LLM conversations and context
- **Retrieve Context**: Get conversation history for continuity
- **Get History**: Access full conversation threads
- **Integration Module**: `services/llm-gateway/modules/service_integrations.py`

**4. Interpreter Service (`/integrations/interpreter/{operation}`)**
- **Enhanced Query Understanding**: Use LLM for better intent recognition
- **Prompt Optimization**: Improve prompts using LLM analysis
- **Entity Extraction**: Advanced entity extraction with LLM
- **Intent Classification**: LLM-powered intent analysis
- **Integration Module**: `services/interpreter/modules/llm_gateway_integration.py`

**5. Orchestrator Service (`/integrations/orchestrator/{operation}`)**
- **Workflow Generation**: Create workflows from natural language
- **Workflow Optimization**: Optimize execution based on history
- **Service Selection**: Intelligent service recommendation
- **Performance Analysis**: LLM-powered workflow analysis
- **Integration Module**: `services/orchestrator/modules/llm_gateway_integration.py`

#### AI/ML Services Integration

**6. Summarizer Hub (`/integrations/summarizer_hub/{operation}`)**
- **Enhanced Summarization**: Improve summaries with LLM analysis
- **Provider Selection**: Choose optimal providers for summarization
- **Quality Assessment**: LLM-powered quality evaluation
- **Metadata Generation**: Rich metadata using LLM analysis
- **Integration Module**: `services/summarizer-hub/modules/llm_gateway_integration.py`

**7. Secure Analyzer (`/integrations/secure_analyzer/{operation}`)**
- **Enhanced Security Analysis**: LLM-powered threat detection
- **Provider Recommendations**: Security-aware provider selection
- **Policy Generation**: Intelligent security policy creation
- **Compliance Analysis**: LLM-powered compliance assessment
- **Integration Module**: `services/secure-analyzer/modules/llm_gateway_integration.py`

**8. Code Analyzer (`/integrations/code_analyzer/{operation}`)**
- **Code Analysis**: LLM-enhanced code understanding
- **Endpoint Extraction**: Advanced API endpoint discovery
- **Integration Module**: `services/llm-gateway/modules/service_integrations.py`

**9. Architecture Digitizer (`/integrations/architecture_digitizer/{operation}`)**
- **Architecture Analysis**: LLM-powered system analysis
- **Dependency Analysis**: Intelligent dependency mapping
- **Integration Module**: `services/llm-gateway/modules/service_integrations.py`

**10. Analysis Service (`/integrations/analysis_service/{operation}`)**
- **Consistency Analysis**: LLM-enhanced document consistency checking
- **Quality Assessment**: Advanced document quality evaluation
- **Integration Module**: `services/llm-gateway/modules/service_integrations.py`

### 🚀 Enhanced Integration Endpoints

#### `/enhanced-query`
Full ecosystem integration with all services:
```python
POST /enhanced-query
{
  "prompt": "Analyze this technical document",
  "user_id": "developer123"
}
# Leverages: Interpreter + Prompt Store + Memory Agent + Secure Analyzer + Document Store
```

#### `/workflow-query`
Orchestrator-powered workflow execution:
```python
POST /workflow-query
{
  "prompt": "Create documentation for this API",
  "user_id": "developer123"
}
Headers: X-Workflow-Type: documentation_generation
```

#### `/contextual-query`
Rich contextual information retrieval:
```python
POST /contextual-query
{
  "prompt": "Explain this error",
  "context": {"search_terms": "authentication error"}
}
# Retrieves: Conversation history + Relevant docs + Optimized prompts
```

#### `/services/status`
Comprehensive service health monitoring:
```python
GET /services/status
# Returns health status of all 10 integrated services
```

#### `/integrations/{service}/{operation}`
Direct service integration access:
```python
POST /integrations/interpreter/interpret_query
{
  "query": "analyze this code",
  "context": {"language": "python"}
}
```

### 🔧 Service-Specific Integration Examples

#### Interpreter Service Integration
```python
from services.interpreter.modules.llm_gateway_integration import llm_gateway_integration

# Enhanced query understanding
understanding = await llm_gateway_integration.enhance_query_understanding(
    query="Create a user authentication system",
    context={"project": "web_app"}
)

# Optimized prompt generation
optimized_prompt = await llm_gateway_integration.optimize_prompt_for_llm(
    original_prompt="Summarize this",
    task_type="technical_summary"
)
```

#### Orchestrator Service Integration
```python
from services.orchestrator.modules.llm_gateway_integration import llm_gateway_integration

# Generate workflow from natural language
workflow = await llm_gateway_integration.generate_workflow_from_nlp(
    natural_language_request="Build and deploy a microservice",
    available_services=["code_analyzer", "doc_store", "ci_cd"]
)

# Optimize existing workflow
optimized = await llm_gateway_integration.optimize_workflow_execution(
    workflow_spec=existing_workflow,
    execution_history=past_runs
)
```

#### Summarizer Hub Integration
```python
from services.summarizer_hub.modules.llm_gateway_integration import llm_gateway_integration

# Enhance existing summary
enhanced = await llm_gateway_integration.enhance_summarization_with_llm(
    text=original_text,
    original_summary=basic_summary,
    summarization_metadata={"technique": "extractive"}
)

# Intelligent provider selection
recommendation = await llm_gateway_integration.intelligent_provider_selection_for_summary(
    text=long_document,
    summary_requirements={"max_length": 500, "technical_level": "expert"}
)
```

#### Secure Analyzer Integration
```python
from services.secure_analyzer.modules.llm_gateway_integration import llm_gateway_integration

# Enhanced security analysis
enhanced_analysis = await llm_gateway_integration.enhance_security_analysis_with_llm(
    content=sensitive_document,
    basic_findings=keyword_matches
)

# Security-aware provider recommendation
provider_rec = await llm_gateway_integration.intelligent_provider_recommendation(
    content=confidential_data,
    security_findings=security_issues,
    available_providers=["ollama", "bedrock", "openai"]
)
```

### Service Mesh Benefits

1. **Centralized LLM Management**
   - Single point for all LLM operations
   - Unified configuration and monitoring
   - Consistent API across all services

2. **Security Integration**
   - Automatic security routing
   - Compliance enforcement
   - Audit trail consolidation

3. **Cost Optimization**
   - Intelligent provider selection
   - Response caching
   - Usage analytics for optimization

4. **Performance Optimization**
   - Load balancing across providers
   - Response caching
   - Rate limiting and throttling

5. **Observability**
   - Comprehensive metrics
   - Performance monitoring
   - Error tracking and alerting

## Security Considerations

### Content Analysis
- Automatic detection of sensitive keywords
- Configurable sensitivity thresholds
- Multiple security levels per provider

### Provider Security
- **High Security**: Ollama (local), AWS Bedrock
- **Medium Security**: OpenAI, Anthropic, Grok
- Automatic routing based on content sensitivity

### Access Control
- User-specific rate limiting
- Burst protection
- Cooldown periods for abuse prevention

## Monitoring and Analytics

### Real-time Metrics
- Request volume by provider
- Response times and latency
- Error rates and success rates
- Cost tracking and optimization

### Performance Insights
- Cache hit rates
- Provider availability status
- Rate limiting violations
- Usage patterns and trends

### Cost Analysis
- Cost per provider
- Cost per user/token
- Cost optimization recommendations
- Budget alerts and limits

## Testing

### Unit Tests
```bash
# Test LLM Gateway components
pytest tests/unit/llm_gateway/ -v

# Test specific modules
pytest tests/unit/llm_gateway/test_provider_router.py -v
pytest tests/unit/llm_gateway/test_security_filter.py -v
pytest tests/unit/llm_gateway/test_cache_manager.py -v
pytest tests/unit/llm_gateway/test_metrics_collector.py -v
pytest tests/unit/llm_gateway/test_rate_limiter.py -v
```

### Integration Tests
```bash
# Test full LLM Gateway integration
pytest tests/integration/llm_gateway/ -v

# Test with mock providers
pytest tests/integration/llm_gateway/test_mock_providers.py -v
```

### Load Testing
```bash
# Load test the gateway
pytest tests/performance/llm_gateway/ -v

# Test rate limiting
pytest tests/performance/llm_gateway/test_rate_limiting.py -v
```

## Deployment

### Docker Configuration
```yaml
# docker-compose.yml
services:
  llm-gateway:
    image: llm-docs-ecosystem/llm-gateway:latest
    ports:
      - "5055:5055"
    environment:
      - REDIS_HOST=redis
      - OLLAMA_ENDPOINT=http://ollama:11434
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - redis
      - ollama
    volumes:
      - llm_gateway_cache:/app/cache
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5055/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  llm_gateway_cache:
```

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-gateway
spec:
  replicas: 3
  selector:
    matchLabels:
      app: llm-gateway
  template:
    metadata:
      labels:
        app: llm-gateway
    spec:
      containers:
      - name: llm-gateway
        image: llm-docs-ecosystem/llm-gateway:latest
        ports:
        - containerPort: 5055
        env:
        - name: REDIS_HOST
          value: "redis-service"
        - name: OLLAMA_ENDPOINT
          value: "http://ollama-service:11434"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 5055
          initialDelaySeconds: 30
          periodSeconds: 10
```

## Troubleshooting

### Common Issues

#### Provider Unavailable
```bash
# Check provider status
curl "http://localhost:5055/providers"

# Check detailed health
curl "http://localhost:5055/health/detailed"
```

#### Rate Limiting Issues
```bash
# Check rate limit status for user
curl "http://localhost:5055/rate-limit/status?user_id=user123"

# Reset user rate limits (admin only)
curl -X POST "http://localhost:5055/admin/reset-limits" \
  -H "Authorization: Bearer admin-token" \
  -d '{"user_id": "user123"}'
```

#### Cache Issues
```bash
# Check cache status
curl "http://localhost:5055/cache/status"

# Clear cache
curl -X POST "http://localhost:5055/cache/clear"
```

#### Performance Issues
```bash
# Check metrics
curl "http://localhost:5055/metrics"

# Check slow requests
curl "http://localhost:5055/metrics/performance"
```

## Future Enhancements

### Planned Features
- **Advanced Caching**: Semantic caching with embeddings
- **Model Fine-tuning**: Automated model optimization
- **Multi-modal Support**: Image and audio processing
- **Federated Learning**: Distributed model training
- **Custom Model Hosting**: Support for custom-trained models
- **Advanced Analytics**: Predictive cost optimization

### Research Areas
- **Auto-scaling**: Dynamic provider scaling based on demand
- **Model Selection**: ML-based optimal model selection
- **Cost Prediction**: Machine learning cost forecasting
- **Quality Optimization**: Automated prompt and model optimization

---

## Quick Start

1. **Start the service:**
   ```bash
   cd services/llm-gateway
   python main.py
   ```

2. **Test basic functionality:**
   ```bash
   curl -X POST "http://localhost:5055/query" \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Hello, world!"}'
   ```

3. **Check providers:**
   ```bash
   curl "http://localhost:5055/providers"
   ```

The LLM Gateway is now ready to intelligently route, secure, and optimize all your LLM operations! 🚀
