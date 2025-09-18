# Service Dependency Analysis Report

## Dependency Graph Summary
- Total Services: 22
- Circular Dependencies: 0
- Dependency Issues: 1

## Startup Order
 1. redis
 2. ollama
 3. summarizer-hub
 4. architecture-digitizer
 5. bedrock-proxy
 6. github-mcp
 7. notification-service
 8. secure-analyzer
 9. log-collector
10. orchestrator
11. doc_store
12. memory-agent
13. prompt_store
14. code-analyzer
15. llm-gateway
16. discovery-agent
17. source-agent
18. analysis-service
19. mock-data-generator
20. frontend
21. interpreter
22. cli

## Service Dependencies
### redis
**No dependencies**
**Required by:**
  - orchestrator
  - doc_store
  - analysis-service
  - llm-gateway
  - mock-data-generator
  - memory-agent
  - prompt_store
  - code-analyzer

### orchestrator
**Depends on:**
  - ✅ redis
**Required by:**
  - frontend
  - discovery-agent
  - interpreter
  - cli

### doc_store
**Depends on:**
  - ✅ redis
**Required by:**
  - analysis-service
  - source-agent
  - mock-data-generator

### analysis-service
**Depends on:**
  - ✅ redis
  - ✅ doc_store
  - ✅ llm-gateway
**Required by:**
  - frontend
  - interpreter
  - cli

### source-agent
**Depends on:**
  - ✅ doc_store

### frontend
**Depends on:**
  - ✅ analysis-service
  - ✅ orchestrator

### ollama
**No dependencies**
**Required by:**
  - llm-gateway

### summarizer-hub
**No dependencies**

### architecture-digitizer
**No dependencies**

### bedrock-proxy
**No dependencies**
**Required by:**
  - llm-gateway

### llm-gateway
**Depends on:**
  - ✅ bedrock-proxy
  - ✅ ollama
  - ✅ redis
**Required by:**
  - analysis-service
  - mock-data-generator

### mock-data-generator
**Depends on:**
  - ✅ llm-gateway
  - ✅ doc_store
  - ✅ redis

### github-mcp
**No dependencies**

### memory-agent
**Depends on:**
  - ✅ redis

### discovery-agent
**Depends on:**
  - ✅ orchestrator

### notification-service
**No dependencies**

### prompt_store
**Depends on:**
  - ✅ redis
**Required by:**
  - interpreter
  - cli

### interpreter
**Depends on:**
  - ✅ prompt_store
  - ✅ orchestrator
  - ✅ analysis-service

### cli
**Depends on:**
  - ✅ prompt_store
  - ✅ orchestrator
  - ✅ analysis-service

### code-analyzer
**Depends on:**
  - ✅ redis

### secure-analyzer
**No dependencies**

### log-collector
**No dependencies**

## Issues Found
- ℹ️ **redis**: Service 'redis' has 8 dependents but no dependencies
  *Suggestion: Consider if this service should have infrastructure dependencies*