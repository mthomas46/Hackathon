# Service Dependency Analysis Report

## Dependency Graph Summary
- Total Services: 25
- Circular Dependencies: 0
- Dependency Issues: 2

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
20. unified-api-dashboard
21. frontend
22. interpreter
23. cli
24. project-simulation
25. simulation-dashboard

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
  - project-simulation
  - unified-api-dashboard
  - code-analyzer

### orchestrator
**Depends on:**
  - ✅ redis
**Required by:**
  - frontend
  - discovery-agent
  - interpreter
  - cli
  - project-simulation

### doc_store
**Depends on:**
  - ✅ redis
**Required by:**
  - analysis-service
  - source-agent
  - mock-data-generator
  - project-simulation
  - unified-api-dashboard

### analysis-service
**Depends on:**
  - ✅ doc_store
  - ✅ llm-gateway
  - ✅ redis
**Required by:**
  - frontend
  - interpreter
  - cli
  - project-simulation
  - simulation-dashboard

### source-agent
**Depends on:**
  - ✅ doc_store

### frontend
**Depends on:**
  - ✅ orchestrator
  - ✅ analysis-service

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
  - ✅ ollama
  - ✅ redis
  - ✅ bedrock-proxy
**Required by:**
  - analysis-service
  - mock-data-generator
  - project-simulation

### mock-data-generator
**Depends on:**
  - ✅ llm-gateway
  - ✅ doc_store
  - ✅ redis
**Required by:**
  - project-simulation

### github-mcp
**No dependencies**

### memory-agent
**Depends on:**
  - ✅ redis

### discovery-agent
**Depends on:**
  - ✅ orchestrator
**Required by:**
  - unified-api-dashboard

### notification-service
**No dependencies**
**Required by:**
  - project-simulation
  - simulation-dashboard

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

### project-simulation
**Depends on:**
  - ✅ redis
  - ✅ doc_store
  - ✅ llm-gateway
  - ✅ mock-data-generator
  - ✅ analysis-service
  - ✅ orchestrator
  - ✅ notification-service
**Required by:**
  - simulation-dashboard

### simulation-dashboard
**Depends on:**
  - ✅ project-simulation
  - ✅ analysis-service
  - ✅ notification-service

### unified-api-dashboard
**Depends on:**
  - ✅ redis
  - ✅ discovery-agent
  - ✅ doc_store

### code-analyzer
**Depends on:**
  - ✅ redis

### secure-analyzer
**No dependencies**

### log-collector
**No dependencies**

## Issues Found
- ℹ️ **redis**: Service 'redis' has 10 dependents but no dependencies
  *Suggestion: Consider if this service should have infrastructure dependencies*
- 🟡 **project-simulation**: Service 'project-simulation' has 7 dependencies
  *Suggestion: Consider reducing coupling by introducing intermediary services*