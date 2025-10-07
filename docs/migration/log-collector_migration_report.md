---
llm_metadata:
  document_type: guide
  content_focus: analytical
  platform:
    primary: mcp
    secondary: []
  status: active
  created_date: '2024-09-01'
  last_modified: '2025-10-07'
  topics:
  - redis
  - ollama
  - rag
  concepts: []
  technologies: []
  services_mentioned: []
  semantic_summary: Guide document about analytical aspects of the mcp platform
  archive_reason: n/a
  historical_value: current
  reference_value: high
semantic_embedding:
  model: text-embedding-ada-002
  embedding_date: '2025-10-07'
  embedding_checksum: pending
rag_metadata:
  chunk_strategy: semantic
  optimal_chunk_size: 512
  retrieval_priority: high
---

# Environment Variable Migration Report

## Summary
- Total services analyzed: 1
- Services using environment variables: 1
- Environment variables migrated: 25
- Environment variables requiring manual review: 7

## log-collector

**Environment variables found:** 32

### Migrated Variables
- `ANALYSIS_SERVICE_URL` → `services.analysis_service_url`
- `ARCHITECTURE_DIGITIZER_URL` → `services.architecture_digitizer_url`
- `BEDROCK_PROXY_URL` → `services.bedrock_proxy_url`
- `CODE_ANALYZER_URL` → `services.code_analyzer_url`
- `DISCOVERY_AGENT_URL` → `services.discovery_agent_url`
- `DOC_STORE_URL` → `services.doc_store_url`
- `ENABLE_HEALTH_SAFEGUARDS` → `log_collector.enable_health_safeguards`
- `EXTERNAL_SERVICE_STORE_URL` → `services.external_service_store_url`
- `FRONTEND_URL` → `services.frontend_url`
- `GITHUB_MCP_URL` → `services.github_mcp_url`
- `INTERPRETER_URL` → `services.interpreter_url`
- `LLM_GATEWAY_URL` → `services.llm_gateway_url`
- `MEMORY_AGENT_URL` → `services.memory_agent_url`
- `MOCK_DATA_GENERATOR_URL` → `services.mock_data_generator_url`
- `NOTIFICATION_SERVICE_URL` → `services.notification_service_url`
- `ORCHESTRATOR_URL` → `services.orchestrator_url`
- `PROJECT_SIMULATION_URL` → `services.project_simulation_url`
- `PROMPT_STORE_URL` → `services.prompt_store_url`
- `SECURE_ANALYZER_URL` → `services.secure_analyzer_url`
- `SERVICE_HEALTH_CHECK_INTERVAL` → `log_collector.health_check_interval`
- `SIMULATION_DASHBOARD_URL` → `services.simulation_dashboard_url`
- `SOURCE_AGENT_URL` → `services.source_agent_url`
- `SUMMARIZER_HUB_URL` → `services.summarizer_hub_url`
- `UNIFIED_API_DASHBOARD_URL` → `services.unified_api_dashboard_url`
- `USER_STORE_URL` → `services.user_store_url`

### Variables Requiring Manual Review
- `LOG_MAX_FILES` (no standard mapping found)
- `LOG_MAX_FILE_SIZE_MB` (no standard mapping found)
- `LOG_ROTATION_DIR` (no standard mapping found)
- `LOG_ROTATION_ENABLED` (no standard mapping found)
- `LOG_STORAGE_MAX_LOGS` (no standard mapping found)
- `OLLAMA_URL` (no standard mapping found)
- `REDIS_URL` (no standard mapping found)

### Usage Locations
#### log-collector/main.py
  - Line 88: `self.check_interval = int(os.environ.get("SERVICE_HEALTH_CHECK_INTERVAL", "30"))  # seconds`
  - Line 89: `self.enable_health_safeguards = os.environ.get("ENABLE_HEALTH_SAFEGUARDS", "true").lower() == "true"`
  - Line 96: `"orchestrator": os.environ.get("ORCHESTRATOR_URL", "http://orchestrator:5099") + "/health",`
  - Line 97: `"doc_store": os.environ.get("DOC_STORE_URL", "http://doc_store:5010") + "/health",`
  - Line 98: `"analysis-service": os.environ.get("ANALYSIS_SERVICE_URL", "http://analysis-service:5020") + "/health",`
  - ... and 22 more

#### log-collector/modules/log_storage.py
  - Line 323: `max_logs=int(os.environ.get("LOG_STORAGE_MAX_LOGS", "5000")),`
  - Line 324: `enable_rotation=os.environ.get("LOG_ROTATION_ENABLED", "true").lower() == "true",`
  - Line 325: `rotation_dir=os.environ.get("LOG_ROTATION_DIR", "/app/logs/archive"),`
  - Line 326: `max_file_size_mb=int(os.environ.get("LOG_MAX_FILE_SIZE_MB", "10")),`
  - Line 327: `max_files=int(os.environ.get("LOG_MAX_FILES", "5"))`
