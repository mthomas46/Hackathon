# Environment Variable Migration Report

## Summary
- Total services analyzed: 30
- Services using environment variables: 23
- Environment variables migrated: 68
- Environment variables requiring manual review: 168

## interpreter

**Environment variables found:** 9

### Migrated Variables
- `DOC_STORE_URL` → `services.doc_store_url`
- `PROMPT_STORE_URL` → `services.prompt_store_url`

### Variables Requiring Manual Review
- `INTERPRETER_API_PORT` (no standard mapping found)
- `INTERPRETER_SERVICE_API_HOST` (no standard mapping found)
- `INTERPRETER_SERVICE_API_PORT` (no standard mapping found)

### Usage Locations
#### interpreter/main.py
  - Line 138: `self.doc_store_url = os.getenv("DOC_STORE_URL", "http://doc-store:5087")`
  - Line 780: `"url": os.getenv("DOC_STORE_URL", "http://doc-store:5087"),`
  - Line 784: `"url": os.getenv("PROMPT_STORE_URL", "http://prompt-store:5110"),`
  - Line 827: `"url": os.getenv("DOC_STORE_URL", "http://doc-store:5087"),`
  - Line 832: `"url": os.getenv("PROMPT_STORE_URL", "http://prompt-store:5110"),`
  - ... and 3 more

#### interpreter/modules/shared_utils.py
  - Line 24: `_INTERPRETER_API_PORT = int(os.environ.get("INTERPRETER_API_PORT", "5120"))`

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

## source-agent

**Environment variables found:** 2

### Variables Requiring Manual Review
- `SERVICE_API_PORT` (no standard mapping found)
- `USE_GITHUB_MCP` (no standard mapping found)

### Usage Locations
#### source-agent/main.py
  - Line 51: `DEFAULT_API_PORT = int(os.environ.get("SERVICE_API_PORT", 5070))`

#### source-agent/domain/services/fetch_handler.py
  - Line 33: `if os.environ.get("USE_GITHUB_MCP", "0") in ("1", "true", "TRUE"):`

## frontend

**Environment variables found:** 9

### Migrated Variables
- `DOC_STORE_URL` → `services.doc_store_url`
- `ORCHESTRATOR_URL` → `services.orchestrator_url`
- `SUMMARIZER_HUB_URL` → `services.summarizer_hub_url`

### Variables Requiring Manual Review
- `CONSISTENCY_ENGINE_URL` (no standard mapping found)
- `ENVIRONMENT` (no standard mapping found)
- `FRONTEND_SERVICE_API_HOST` (no standard mapping found)
- `FRONTEND_SERVICE_API_PORT` (no standard mapping found)
- `REAPI_PORTING_URL` (no standard mapping found)
- `SERVICE_API_PORT` (no standard mapping found)

### Usage Locations
#### frontend/start.py
  - Line 43: `host = os.environ.get("FRONTEND_SERVICE_API_HOST", "0.0.0.0")`
  - Line 44: `port = int(os.environ.get("SERVICE_API_PORT", 3000))`

#### frontend/main.py
  - Line 288: `return os.getenv("CONSISTENCY_ENGINE_URL", "http://localhost:5001")`
  - Line 291: `return os.getenv("DOC_STORE_URL", "http://localhost:5005")`
  - Line 297: `return os.getenv("ORCHESTRATOR_URL", "http://localhost:5007")`
  - Line 300: `return os.getenv("REAPI_PORTING_URL", "http://localhost:5008")`
  - Line 303: `return os.getenv("SUMMARIZER_HUB_URL", "http://localhost:5009")`
  - ... and 2 more

## notification-service

**Environment variables found:** 4

### Variables Requiring Manual Review
- `NOTIFY_OWNER_MAP_FILE` (no standard mapping found)
- `NOTIFY_OWNER_MAP_JSON` (no standard mapping found)
- `SERVICE_API_HOST` (no standard mapping found)
- `SERVICE_API_PORT` (no standard mapping found)

### Usage Locations
#### notification-service/main.py
  - Line 102: `port = int(os.getenv("SERVICE_API_PORT", "5020"))`
  - Line 103: `host = os.getenv("SERVICE_API_HOST", "0.0.0.0")`

#### notification-service/domain/services/owner_resolver.py
  - Line 113: `json_config = os.environ.get("NOTIFY_OWNER_MAP_JSON")`
  - Line 123: `config_file_path = os.environ.get("NOTIFY_OWNER_MAP_FILE")`

## code-analyzer

**Environment variables found:** 9

### Migrated Variables
- `DOC_STORE_URL` → `services.doc_store_url`
- `REDIS_API_HOST` → `redis.host`

### Variables Requiring Manual Review
- `SERVICE_API_PORT` (no standard mapping found)

### Usage Locations
#### code-analyzer/main.py
  - Line 271: `port = int(os.environ.get("SERVICE_API_PORT", 5025))`

#### code-analyzer/modules/persistence.py
  - Line 15: `host = os.environ.get("REDIS_API_HOST")`
  - Line 26: `ds = os.environ.get("DOC_STORE_URL")`

#### code-analyzer/modules/style_manager.py
  - Line 32: `ds = os.environ.get("DOC_STORE_URL")`
  - Line 54: `ds = os.environ.get("DOC_STORE_URL")`
  - Line 78: `ds = os.environ.get("DOC_STORE_URL")`

#### code-analyzer/domain/services/style_manager.py
  - Line 32: `ds = os.environ.get("DOC_STORE_URL")`
  - Line 54: `ds = os.environ.get("DOC_STORE_URL")`
  - Line 78: `ds = os.environ.get("DOC_STORE_URL")`

## project-simulation

**Environment variables found:** 85

### Migrated Variables
- `ANALYSIS_SERVICE_URL` → `services.analysis_service_url`
- `CORS_ORIGINS` → `security.cors_origins`
- `DEBUG` → `server.debug`
- `DISCOVERY_AGENT_URL` → `services.discovery_agent_url`
- `DOC_STORE_URL` → `services.doc_store_url`
- `FRONTEND_URL` → `services.frontend_url`
- `INTERPRETER_URL` → `services.interpreter_url`
- `JWT_SECRET` → `security.jwt_secret`
- `LLM_GATEWAY_URL` → `services.llm_gateway_url`
- `LOG_COLLECTOR_URL` → `services.log_collector_url`
- `LOG_FILE` → `logging.file_path`
- `LOG_FORMAT` → `logging.format`
- `LOG_LEVEL` → `logging.level`
- `MOCK_DATA_GENERATOR_URL` → `services.mock_data_generator_url`
- `NOTIFICATION_SERVICE_URL` → `services.notification_service_url`
- `ORCHESTRATOR_URL` → `services.orchestrator_url`
- `SUMMARIZER_HUB_URL` → `services.summarizer_hub_url`
- `TESTING` → `analysis.testing`

### Variables Requiring Manual Review
- `API_KEY` (no standard mapping found)
- `AUTO_RELOAD` (no standard mapping found)
- `CI` (no standard mapping found)
- `DATABASE_URL` (no standard mapping found)
- `DEBUG_MODE` (no standard mapping found)
- `DISABLE_RATE_LIMITS` (no standard mapping found)
- `DOCKER_COMPOSE_FILE` (no standard mapping found)
- `DOCKER_CONTAINER` (no standard mapping found)
- `DOCKER_API_HOST` (no standard mapping found)
- `DOCKER_IMAGE_TAG` (no standard mapping found)
- `FEATURE_ADVANCED_ANALYTICS` (no standard mapping found)
- `FEATURE_CONSOLE_LOGGING` (no standard mapping found)
- `FEATURE_CORRELATION_ID` (no standard mapping found)
- `FEATURE_CORS` (no standard mapping found)
- `FEATURE_DETAILED_METRICS` (no standard mapping found)
- `FEATURE_EXTENDED_LOGGING` (no standard mapping found)
- `FEATURE_FILE_LOGGING` (no standard mapping found)
- `FEATURE_HEALTH_CHECKS` (no standard mapping found)
- `FEATURE_METRICS` (no standard mapping found)
- `FEATURE_PROFILING` (no standard mapping found)
- `FEATURE_REAL_TIME_UPDATES` (no standard mapping found)
- `FEATURE_REDOC` (no standard mapping found)
- `FEATURE_SWAGGER` (no standard mapping found)
- `ENVIRONMENT` (no standard mapping found)
- `API_HOST` (no standard mapping found)
- `API_HOSTNAME` (no standard mapping found)
- `METRICS_API_PORT` (no standard mapping found)
- `MOCK_DATA_ENABLED` (no standard mapping found)
- `OLLAMA_BASE_URL` (no standard mapping found)
- `OLLAMA_MODEL` (no standard mapping found)
- `API_PORT` (no standard mapping found)
- `PROFILING_OUTPUT_DIR` (no standard mapping found)
- `PYDEVD_ENABLE` (no standard mapping found)
- `PYTEST_CURRENT_TEST` (no standard mapping found)
- `RATE_LIMIT_ENABLED` (no standard mapping found)
- `REDIS_URL` (no standard mapping found)
- `RELOAD` (no standard mapping found)
- `SERVICE_NAME` (no standard mapping found)
- `SERVICE_VERSION` (no standard mapping found)
- `SIMULATION_ENVIRONMENT` (no standard mapping found)
- `STAGING` (no standard mapping found)
- `TEST_DATABASE_URL` (no standard mapping found)
- `USER` (no standard mapping found)
- `USE_MOCK_SERVICES` (no standard mapping found)

### Usage Locations
#### project-simulation/main.py
  - Line 555: `"environment": os.getenv("ENVIRONMENT", "development")`
  - Line 877: `"environment": os.getenv("ENVIRONMENT", "development"),`
  - Line 1198: `doc_store_url = os.getenv("DOC_STORE_URL", "http://localhost:5051")`
  - Line 1251: `doc_store_url = os.getenv("DOC_STORE_URL", "http://localhost:5051")`
  - Line 1344: `doc_store_url = os.getenv("DOC_STORE_URL", "http://localhost:5051")`
  - ... and 3 more

#### project-simulation/simulation/infrastructure/config/config_manager.py
  - Line 175: `environment = environment or os.getenv("ENVIRONMENT", "development")`
  - Line 238: `self.config.service.name = os.getenv("SERVICE_NAME", self.config.service.name)`
  - Line 239: `self.config.service.version = os.getenv("SERVICE_VERSION", self.config.service.version)`
  - Line 240: `self.config.service.environment = os.getenv("ENVIRONMENT", self.config.service.environment)`
  - Line 241: `self.config.service.host = os.getenv("API_HOST", self.config.service.host)`
  - ... and 47 more

#### project-simulation/simulation/infrastructure/config/environment_manager.py
  - Line 471: `env_var = os.getenv("SIMULATION_ENVIRONMENT", "").lower()`

#### project-simulation/simulation/infrastructure/config/environment.py
  - Line 23: `env = os.getenv("ENVIRONMENT")`
  - Line 52: `os.getenv("DEBUG", "").lower() == "true",`
  - Line 53: `os.getenv("RELOAD", "").lower() == "true",`
  - Line 54: `os.getenv("PYDEVD_ENABLE", "").lower() == "true",`
  - Line 58: `os.getenv("USER", "").startswith(("dev", "user")),`
  - ... and 11 more

#### project-simulation/simulation/application/analysis/simulation_analyzer.py
  - Line 35: `(os.getenv('DOCKER_CONTAINER') or '').lower() in ('true', '1', 'yes'),`
  - Line 37: `os.getenv('DOCKER_API_HOST') is not None,`
  - Line 39: `(os.getenv('API_HOSTNAME') or '').startswith('docker-')`
  - Line 90: `"hostname": os.getenv('API_HOSTNAME', 'unknown'),`
  - Line 94: `"docker_env_var": os.getenv('DOCKER_CONTAINER', '').lower() in ('true', '1', 'yes'),`
  - ... and 3 more

## prompt_store

**Environment variables found:** 2

### Variables Requiring Manual Review
- `PROMPT_STORE_CONNECTION_POOL_SIZE` (no standard mapping found)
- `PROMPT_STORE_DB` (no standard mapping found)

### Usage Locations
#### prompt_store/db/connection.py
  - Line 31: `_DB_PATH = _validate_db_path(os.environ.get("PROMPT_STORE_DB", "prompt_store.db"))`
  - Line 33: `os.environ.get("PROMPT_STORE_CONNECTION_POOL_SIZE", "5")`

## summarizer-hub

**Environment variables found:** 20

### Migrated Variables
- `DEBUG` → `server.debug`
- `LLM_GATEWAY_URL` → `services.llm_gateway_url`

### Variables Requiring Manual Review
- `AWS_REGION` (no standard mapping found)
- `BEDROCK_API_KEY` (no standard mapping found)
- `BEDROCK_ENDPOINT` (no standard mapping found)
- `BEDROCK_MODEL` (no standard mapping found)
- `BEDROCK_REGION` (no standard mapping found)
- `ENVIRONMENT` (no standard mapping found)
- `JIRA_API_TOKEN` (no standard mapping found)
- `JIRA_BASE_URL` (no standard mapping found)
- `JIRA_DEFAULT_PROJECT` (no standard mapping found)
- `JIRA_USERNAME` (no standard mapping found)
- `MAX_SUMMARY_LENGTH` (no standard mapping found)
- `OLLAMA_API_HOST` (no standard mapping found)
- `SH_CONFIG` (no standard mapping found)
- `SUMMARIZER_HUB_API_HOST` (no standard mapping found)
- `SUMMARIZER_HUB_API_PORT` (no standard mapping found)
- `SUMMARIZER_TIMEOUT` (no standard mapping found)

### Usage Locations
#### summarizer-hub/main_ddd.py
  - Line 141: `details=str(exc) if os.getenv("DEBUG", "false").lower() == "true" else None`
  - Line 150: `host = os.getenv("SUMMARIZER_HUB_API_HOST", config.server.host)`
  - Line 151: `port = int(os.getenv("SUMMARIZER_HUB_API_PORT", config.server.port))`

#### summarizer-hub/main.py
  - Line 25: `LLM_GATEWAY_URL = os.getenv("LLM_GATEWAY_URL", "http://llm-gateway:5055")`
  - Line 26: `ENVIRONMENT = os.getenv("ENVIRONMENT", "development")`
  - Line 29: `JIRA_BASE_URL = os.getenv("JIRA_BASE_URL", "https://your-domain.atlassian.net")`
  - Line 30: `JIRA_USERNAME = os.getenv("JIRA_USERNAME", "")`
  - Line 31: `JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")`
  - ... and 1 more

#### summarizer-hub/modules/config_manager.py
  - Line 32: `config_path = os.getenv("SH_CONFIG", "config.yaml")`

#### summarizer-hub/modules/shared_utils.py
  - Line 18: `_DEFAULT_TIMEOUT = int(os.environ.get("SUMMARIZER_TIMEOUT", "60"))`
  - Line 19: `_MAX_SUMMARY_LENGTH = int(os.environ.get("MAX_SUMMARY_LENGTH", "2000"))`

#### summarizer-hub/modules/provider_implementations.py
  - Line 25: `ollama_host = os.getenv("OLLAMA_API_HOST", "http://localhost:11434")`
  - Line 73: `"BEDROCK_REGION", os.environ.get("AWS_REGION") or "us-east-1"`
  - Line 108: `or os.getenv("BEDROCK_ENDPOINT", "")`
  - Line 117: `or os.getenv("BEDROCK_API_KEY")`
  - Line 123: `or os.getenv("BEDROCK_MODEL", "anthropic.claude-3-sonnet-20240229-v1:0"),`
  - ... and 2 more

#### summarizer-hub/modules/llm_gateway_integration.py
  - Line 25: `self.llm_gateway_url = os.getenv("LLM_GATEWAY_URL", "http://llm-gateway:5055")`

## llm-gateway

**Environment variables found:** 3

### Migrated Variables
- `REDIS_API_HOST` → `redis.host`

### Variables Requiring Manual Review
- `ENVIRONMENT` (no standard mapping found)
- `OLLAMA_ENDPOINT` (no standard mapping found)

### Usage Locations
#### llm-gateway/main.py
  - Line 62: `OLLAMA_ENDPOINT = os.getenv("OLLAMA_ENDPOINT", "http://ollama:11434")`
  - Line 63: `REDIS_API_HOST = os.getenv("REDIS_API_HOST", "redis")`
  - Line 64: `ENVIRONMENT = os.getenv("ENVIRONMENT", "development")`

## secure-analyzer

**Environment variables found:** 4

### Migrated Variables
- `LLM_GATEWAY_URL` → `services.llm_gateway_url`
- `TESTING` → `analysis.testing`

### Variables Requiring Manual Review
- `PYTEST_CURRENT_TEST` (no standard mapping found)
- `SECURE_ONLY_MODELS` (no standard mapping found)

### Usage Locations
#### secure-analyzer/main.py
  - Line 381: `if os.environ.get("PYTEST_CURRENT_TEST") or os.environ.get("TESTING"):`
  - Line 381: `if os.environ.get("PYTEST_CURRENT_TEST") or os.environ.get("TESTING"):`

#### secure-analyzer/modules/policy_enforcer.py
  - Line 57: `models = os.environ.get("SECURE_ONLY_MODELS", "bedrock,ollama").split(",")`

#### secure-analyzer/modules/llm_gateway_integration.py
  - Line 25: `self.llm_gateway_url = os.getenv("LLM_GATEWAY_URL", "http://llm-gateway:5055")`

## cli

**Environment variables found:** 13

### Migrated Variables
- `REDIS_API_HOST` → `redis.host`

### Variables Requiring Manual Review
- `GITHUB_API_BASE` (no standard mapping found)
- `GITHUB_OWNER` (no standard mapping found)
- `JIRA_BASE_URL` (no standard mapping found)
- `JIRA_EMAIL` (no standard mapping found)
- `USER` (no standard mapping found)

### Usage Locations
#### cli/modules/cli_commands.py
  - Line 60: `self.current_user = os.environ.get("USER", "cli_user")`

#### cli/modules/shared_utils.py
  - Line 29: `_DEFAULT_USER = os.environ.get("USER", "cli_user")`

#### cli/application/commands/cli_commands.py
  - Line 60: `self.current_user = os.environ.get("USER", "cli_user")`

#### cli/application/handlers/service_actions.py
  - Line 687: `host = str(os.getenv("REDIS_API_HOST", "redis")).strip()`

#### cli/application/handlers/actions/source_agent.py
  - Line 67: `api_default = os.environ.get("GITHUB_API_BASE", "https://api.github.com")`
  - Line 69: `owner_default = os.environ.get("GITHUB_OWNER", "")`
  - Line 96: `api_default = os.environ.get("GITHUB_API_BASE", "https://api.github.com")`
  - Line 98: `owner_default = os.environ.get("GITHUB_OWNER", "")`
  - Line 156: `base_default = os.environ.get("JIRA_BASE_URL", "https://example.atlassian.net")`
  - ... and 3 more

#### cli/application/handlers/actions/orchestrator.py
  - Line 43: `host = str(os.getenv("REDIS_API_HOST", "redis")).strip()`

## external-service-store

**Environment variables found:** 2

### Variables Requiring Manual Review
- `SERVICE_API_HOST` (no standard mapping found)
- `SERVICE_API_PORT` (no standard mapping found)

### Usage Locations
#### external-service-store/main.py
  - Line 1270: `port = int(os.getenv("SERVICE_API_PORT", "5140"))`
  - Line 1271: `host = os.getenv("SERVICE_API_HOST", "0.0.0.0")`

## simulation-dashboard

**Environment variables found:** 1

### Variables Requiring Manual Review
- `DASHBOARD_API_PORT` (no standard mapping found)

### Usage Locations
#### simulation-dashboard/infrastructure/scripts/run_dashboard.py
  - Line 145: `port = int(os.environ.get("DASHBOARD_API_PORT", 8501))`

## analysis-service

**Environment variables found:** 50

### Migrated Variables
- `DEBUG` → `server.debug`
- `LOG_LEVEL` → `logging.level`
- `REDIS_DB` → `redis.db`
- `REDIS_API_HOST` → `redis.host`
- `REDIS_PASSWORD` → `redis.password`
- `REDIS_API_PORT` → `redis.port`
- `TESTING` → `analysis.testing`

### Variables Requiring Manual Review
- `ANALYSIS_DB_PATH` (no standard mapping found)
- `CACHE_CONNECTION_TIMEOUT` (no standard mapping found)
- `CACHE_DEFAULT_TTL` (no standard mapping found)
- `CACHE_ENABLE_COMPRESSION` (no standard mapping found)
- `CACHE_MAX_MEMORY` (no standard mapping found)
- `CACHE_MAX_RETRIES` (no standard mapping found)
- `CACHE_POOL_SIZE` (no standard mapping found)
- `CACHE_RETRY_ON_TIMEOUT` (no standard mapping found)
- `DB_CONNECTION_TIMEOUT` (no standard mapping found)
- `DB_ENABLE_MIGRATIONS` (no standard mapping found)
- `DB_MAX_CONNECTIONS` (no standard mapping found)
- `DB_MIN_CONNECTIONS` (no standard mapping found)
- `ENABLE_CACHING` (no standard mapping found)
- `FEATURE_METRICS` (no standard mapping found)
- `ENABLE_TRACING` (no standard mapping found)
- `ENVIRONMENT` (no standard mapping found)
- `EXTERNAL_MAX_RETRIES` (no standard mapping found)
- `EXTERNAL_REQUEST_TIMEOUT` (no standard mapping found)
- `EXTERNAL_RETRY_DELAY` (no standard mapping found)
- `MAX_CONCURRENT_REQUESTS` (no standard mapping found)
- `EXTERNAL_OPENAI_API_KEY` (no standard mapping found)
- `OPENAI_MAX_TOKENS` (no standard mapping found)
- `OPENAI_MODEL` (no standard mapping found)
- `OPENAI_TEMPERATURE` (no standard mapping found)
- `POSTGRES_DB` (no standard mapping found)
- `POSTGRES_API_HOST` (no standard mapping found)
- `POSTGRES_PASSWORD` (no standard mapping found)
- `POSTGRES_API_PORT` (no standard mapping found)
- `POSTGRES_USER` (no standard mapping found)
- `REDIS_SSL` (no standard mapping found)
- `REQUEST_TIMEOUT` (no standard mapping found)
- `SEMANTIC_BATCH_SIZE` (no standard mapping found)
- `SEMANTIC_MODEL_PATH` (no standard mapping found)
- `SEMANTIC_SIMILARITY_THRESHOLD` (no standard mapping found)
- `SENTIMENT_CONFIDENCE_THRESHOLD` (no standard mapping found)
- `SENTIMENT_MODEL` (no standard mapping found)
- `SERVICE_API_PORT` (no standard mapping found)

### Usage Locations
#### analysis-service/start.py
  - Line 36: `port = int(os.environ.get("SERVICE_API_PORT", 5020))`

#### analysis-service/main.py
  - Line 3709: `if os.environ.get("TESTING", "").lower() == "true":`
  - Line 3825: `if os.environ.get("TESTING", "").lower() == "true":`
  - Line 3890: `if os.environ.get("TESTING", "").lower() == "true":`

#### analysis-service/modules/analysis_handlers_backup.py
  - Line 83: `if os.environ.get("TESTING", "").lower() == "true":`

#### analysis-service/modules/integration_handlers.py
  - Line 65: `if os.environ.get("TESTING", "").lower() == "true":`
  - Line 133: `if os.environ.get("TESTING", "").lower() == "true":`

#### analysis-service/modules/report_handlers.py
  - Line 114: `if os.environ.get("TESTING", "").lower() == "true":`

#### analysis-service/infrastructure/config/database_config.py
  - Line 35: `sqlite_path=os.getenv('ANALYSIS_DB_PATH', ':memory:'),`
  - Line 36: `postgres_host=os.getenv('POSTGRES_API_HOST'),`
  - Line 37: `postgres_port=int(os.getenv('POSTGRES_API_PORT', '5432')),`
  - Line 38: `postgres_database=os.getenv('POSTGRES_DB'),`
  - Line 39: `postgres_user=os.getenv('POSTGRES_USER'),`
  - ... and 5 more

#### analysis-service/infrastructure/config/cache_config.py
  - Line 39: `redis_host=os.getenv('REDIS_API_HOST', 'localhost'),`
  - Line 40: `redis_port=int(os.getenv('REDIS_API_PORT', '6379')),`
  - Line 41: `redis_db=int(os.getenv('REDIS_DB', '0')),`
  - Line 42: `redis_password=os.getenv('REDIS_PASSWORD'),`
  - Line 43: `redis_ssl=os.getenv('REDIS_SSL', 'false').lower() == 'true',`
  - ... and 7 more

#### analysis-service/infrastructure/config/external_service_config.py
  - Line 36: `openai_api_key=os.getenv('EXTERNAL_OPENAI_API_KEY'),`
  - Line 37: `openai_model=os.getenv('OPENAI_MODEL', 'gpt-4'),`
  - Line 38: `openai_max_tokens=int(os.getenv('OPENAI_MAX_TOKENS', '2000')),`
  - Line 39: `openai_temperature=float(os.getenv('OPENAI_TEMPERATURE', '0.7')),`
  - Line 40: `semantic_model_path=os.getenv('SEMANTIC_MODEL_PATH'),`
  - ... and 7 more

#### analysis-service/infrastructure/config/infrastructure_config.py
  - Line 41: `environment=os.getenv('ENVIRONMENT', 'development'),`
  - Line 42: `debug_mode=os.getenv('DEBUG', 'false').lower() == 'true',`
  - Line 43: `log_level=os.getenv('LOG_LEVEL', 'INFO'),`
  - Line 44: `enable_caching=os.getenv('ENABLE_CACHING', 'true').lower() == 'true',`
  - Line 45: `enable_metrics=os.getenv('FEATURE_METRICS', 'true').lower() == 'true',`
  - ... and 3 more

## memory-agent

**Environment variables found:** 5

### Variables Requiring Manual Review
- `ENVIRONMENT` (no standard mapping found)
- `MEMORY_AGENT_API_HOST` (no standard mapping found)
- `MEMORY_MAX_ITEMS` (no standard mapping found)
- `MEMORY_TTL_SECONDS` (no standard mapping found)
- `REDIS_URL` (no standard mapping found)

### Usage Locations
#### memory-agent/main.py
  - Line 274: `"environment": os.environ.get("ENVIRONMENT", "development"),`
  - Line 350: `host = os.getenv("MEMORY_AGENT_API_HOST", "0.0.0.0")`

#### memory-agent/modules/shared_utils.py
  - Line 23: `_MEMORY_MAX_ITEMS = int(os.environ.get("MEMORY_MAX_ITEMS", "1000"))`
  - Line 24: `_MEMORY_TTL_SECONDS = int(os.environ.get("MEMORY_TTL_SECONDS", "3600"))`
  - Line 25: `_REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379")`

## discovery-agent

**Environment variables found:** 2

### Variables Requiring Manual Review
- `SERVICE_API_PORT` (no standard mapping found)

### Usage Locations
#### discovery-agent/main.py
  - Line 24: `port = int(os.getenv('SERVICE_API_PORT', '5045'))`
  - Line 150: `port = getattr(config, 'port', None) or getattr(config, 'server', {}).get('port', None) or int(os.getenv('SERVICE_API_PORT', '5045'))`

## github-mcp

**Environment variables found:** 7

### Variables Requiring Manual Review
- `GITHUB_DYNAMIC_TOOLSETS` (no standard mapping found)
- `GITHUB_API_HOST` (no standard mapping found)
- `GITHUB_MOCK` (no standard mapping found)
- `GITHUB_PERSONAL_ACCESS_TOKEN` (no standard mapping found)
- `GITHUB_READ_ONLY` (no standard mapping found)
- `GITHUB_TOOLSETS` (no standard mapping found)
- `USE_OFFICIAL_GH_MCP` (no standard mapping found)

### Usage Locations
#### github-mcp/modules/config.py
  - Line 42: `env = os.environ.get("GITHUB_TOOLSETS", "").strip()`
  - Line 51: `return os.environ.get("GITHUB_DYNAMIC_TOOLSETS", "0") in ("1", "true", "TRUE")`
  - Line 56: `return os.environ.get("GITHUB_READ_ONLY", "0") in ("1", "true", "TRUE")`
  - Line 61: `return os.environ.get("GITHUB_MOCK", "1") == "1"`
  - Line 66: `return os.environ.get("GITHUB_API_HOST")`
  - ... and 2 more

## user-store

**Environment variables found:** 2

### Variables Requiring Manual Review
- `SERVICE_API_HOST` (no standard mapping found)
- `SERVICE_API_PORT` (no standard mapping found)

### Usage Locations
#### user-store/main.py
  - Line 1011: `port = int(os.getenv("SERVICE_API_PORT", "5150"))`
  - Line 1012: `host = os.getenv("SERVICE_API_HOST", "0.0.0.0")`

## mock-data-generator

**Environment variables found:** 4

### Migrated Variables
- `DOC_STORE_URL` → `services.doc_store_url`
- `LLM_GATEWAY_URL` → `services.llm_gateway_url`

### Variables Requiring Manual Review
- `ENVIRONMENT` (no standard mapping found)
- `MOCK_DATA_GENERATOR_API_HOST` (no standard mapping found)

### Usage Locations
#### mock-data-generator/main.py
  - Line 40: `LLM_GATEWAY_URL = os.getenv("LLM_GATEWAY_URL", "http://llm-gateway:5055")`
  - Line 41: `DOC_STORE_URL = os.getenv("DOC_STORE_URL", "http://doc_store:5010")`
  - Line 42: `ENVIRONMENT = os.getenv("ENVIRONMENT", "development")`
  - Line 2737: `host = os.getenv("MOCK_DATA_GENERATOR_API_HOST", "0.0.0.0")`

## doc_store

**Environment variables found:** 9

### Variables Requiring Manual Review
- `DOCSTORE_CONNECTION_POOL_SIZE` (no standard mapping found)
- `DOCSTORE_DB` (no standard mapping found)
- `DOC_STORE_CACHE_TTL` (no standard mapping found)
- `DOC_STORE_DB_PATH` (no standard mapping found)
- `DOC_STORE_DEBUG` (no standard mapping found)
- `DOC_STORE_LOG_LEVEL` (no standard mapping found)
- `DOC_STORE_MAX_CONNECTIONS` (no standard mapping found)
- `DOC_STORE_SERVICE_NAME` (no standard mapping found)
- `DOC_STORE_VERSION` (no standard mapping found)

### Usage Locations
#### doc_store/db/connection.py
  - Line 32: `os.environ.get("DOCSTORE_DB", "services/doc_store/db.sqlite3")`
  - Line 35: `os.environ.get("DOCSTORE_CONNECTION_POOL_SIZE", "5")`

#### doc_store/infrastructure/config/settings.py
  - Line 27: `service_name=os.getenv("DOC_STORE_SERVICE_NAME", "doc_store"),`
  - Line 28: `service_version=os.getenv("DOC_STORE_VERSION", "1.0.0"),`
  - Line 29: `debug_mode=os.getenv("DOC_STORE_DEBUG", "false").lower() == "true",`
  - Line 30: `max_connections=int(os.getenv("DOC_STORE_MAX_CONNECTIONS", "100")),`
  - Line 31: `cache_ttl=int(os.getenv("DOC_STORE_CACHE_TTL", "3600")),`
  - ... and 2 more

## unified-api-dashboard

**Environment variables found:** 12

### Migrated Variables
- `DISCOVERY_AGENT_URL` → `services.discovery_agent_url`
- `LOG_LEVEL` → `logging.level`

### Variables Requiring Manual Review
- `ALLOWED_API_HOSTS` (no standard mapping found)
- `ENVIRONMENT` (no standard mapping found)
- `SERVICE_API_HOST` (no standard mapping found)
- `SERVICE_API_PORT` (no standard mapping found)

### Usage Locations
#### unified-api-dashboard/app.py
  - Line 212: `base_url=os.getenv("DISCOVERY_AGENT_URL", "http://localhost:5045")`
  - Line 361: `if os.getenv("ENVIRONMENT") == "production":`
  - Line 365: `os.getenv("ALLOWED_API_HOSTS", "").split(",")`
  - Line 366: `if os.getenv("ALLOWED_API_HOSTS")`
  - Line 821: `port = int(os.getenv("SERVICE_API_PORT", "8000"))`
  - ... and 3 more

#### unified-api-dashboard/main.py
  - Line 20: `port = int(os.getenv("SERVICE_API_PORT", "8000"))`
  - Line 21: `host = os.getenv("SERVICE_API_HOST", "127.0.0.1")`
  - Line 33: `reload=os.getenv("ENVIRONMENT") == "development",`
  - Line 34: `log_level=os.getenv("LOG_LEVEL", "info").lower(),`

## orchestrator

**Environment variables found:** 5

### Migrated Variables
- `PROJECT_SIMULATION_URL` → `services.project_simulation_url`

### Variables Requiring Manual Review
- `DOCKER_CONTAINER` (no standard mapping found)
- `DOCKER_API_HOST` (no standard mapping found)
- `API_HOSTNAME` (no standard mapping found)
- `ORCHESTRATOR_PEERS` (no standard mapping found)

### Usage Locations
#### orchestrator/routes/query.py
  - Line 319: `(os.getenv("DOCKER_CONTAINER") or "").lower() in ("true", "1", "yes"),`
  - Line 320: `os.getenv("DOCKER_API_HOST") is not None,`
  - Line 321: `(os.getenv("API_HOSTNAME") or "").startswith("docker-"),`
  - Line 329: `override_url = os.getenv("PROJECT_SIMULATION_URL")`

#### orchestrator/routes/registry.py
  - Line 36: `for p in os.getenv("ORCHESTRATOR_PEERS", "").split(",")`
