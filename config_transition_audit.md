# Configuration Transition Audit Report
==================================================

## INTERPRETER

✅ Has config file
❌ Does not use config file in code
⚠️  1 hardcoded values:
   - shared_utils.py: os.environ.get("INTERPRETER_PORT", "5120")
💡 Recommendations:
   - Unused config variables: ANALYSIS_SERVICE_URL, ORCHESTRATOR_URL, PROMPT_STORE_URL

## LOG-COLLECTOR

✅ Has config file
❌ Does not use config file in code
💡 Recommendations:
   - Unused config variables: MAX_LOG_SIZE_MB, LOG_RETENTION_DAYS

## SOURCE-AGENT

✅ Has config file
✅ Uses config file in code
⚠️  3 hardcoded values:
   - main.py: os.environ.get('SERVICE_PORT', 5070)
   - fetch_handler.py: os.environ.get("USE_GITHUB_MCP", "0")
   - main.py: os.environ.get('SERVICE_PORT', 5070)

## FRONTEND

✅ Has config file
✅ Uses config file in code
⚠️  4 hardcoded values:
   - start.py: os.environ.get('SERVICE_PORT', 3000)
   - main.py: os.getenv("ENVIRONMENT", "production")
   - start.py: os.environ.get('SERVICE_PORT', 3000)
   ... and 1 more

## NOTIFICATION-SERVICE

✅ Has config file
❌ Does not use config file in code
⚠️  2 hardcoded values:
   - main.py: os.environ.get('SERVICE_PORT', 5020)
   - main.py: os.environ.get('SERVICE_PORT', 5020)
💡 Recommendations:
   - Unused config variables: NOTIFICATION_DEDUPE_WINDOW, NOTIFICATION_MAX_RETRIES, NOTIFICATION_CACHE_TTL

## REDIS

❌ No config file
❌ Does not use config file in code
🚨 Issues:
   - No config file found

## CODE-ANALYZER

✅ Has config file
❌ Does not use config file in code
⚠️  2 hardcoded values:
   - main.py: os.environ.get('SERVICE_PORT', 5025)
   - main.py: os.environ.get('SERVICE_PORT', 5025)
💡 Recommendations:
   - Unused config variables: RATE_LIMIT_ENABLED

## PROJECT-SIMULATION

❌ No config file
❌ Does not use config file in code
🚨 Issues:
   - No config file found

## PROMPT_STORE

✅ Has config file
✅ Uses config file in code
⚠️  2 hardcoded values:
   - connection.py: os.environ.get("PROMPT_STORE_DB", "prompt_store.db")
   - connection.py: os.environ.get("PROMPT_STORE_CONNECTION_POOL_SIZE", "5")
🚨 Issues:
   - Cannot parse config file: [Errno 21] Is a directory: 'services/prompt_store/config.yaml'

## SUMMARIZER-HUB

✅ Has config file
✅ Uses config file in code
⚠️  17 hardcoded values:
   - main.py: os.getenv("LLM_GATEWAY_URL", "http://llm-gateway:5055")
   - main.py: os.getenv("ENVIRONMENT", "development")
   - main.py: os.getenv("JIRA_BASE_URL", "https://your-domain.atlassian.net")
   ... and 14 more
💡 Recommendations:
   - Unused config variables: OPENAI_MODEL, OPENAI_API_KEY, ANTHROPIC_API_KEY, OLLAMA_ENDPOINT, ANTHROPIC_MODEL, OLLAMA_MODEL

## LLM-GATEWAY

✅ Has config file
✅ Uses config file in code
⚠️  6 hardcoded values:
   - main.py: os.getenv("OLLAMA_ENDPOINT", "http://ollama:11434")
   - main.py: os.getenv("REDIS_HOST", "redis")
   - main.py: os.getenv("ENVIRONMENT", "development")
   ... and 3 more
💡 Recommendations:
   - Unused config variables: SSL_ENABLED, HEALTH_TIMEOUT, RESPONSE_VALIDATION, SSL_CERT_PATH, ANTHROPIC_ENABLED, HEALTH_CHECK_INTERVAL, BEDROCK_ENABLED, BEDROCK_API_KEY, DEBUG_MODE, LOG_LEVEL, CACHE_REDIS_ENABLED, CORS_ORIGINS, CACHE_COMPRESSION, METRICS_LOGGING, METRICS_PERFORMANCE_TRACKING, ENABLE_CORS, HEALTH_RETRIES, LOG_FORMAT, GROK_ENABLED, METRICS_ERROR_TRACKING, REQUEST_VALIDATION, PROVIDER_HEALTH_CHECKS, REQUEST_LOGGING, RESPONSE_LOGGING, SSL_KEY_PATH, METRICS_DETAILED_LOGGING, MOCK_PROVIDERS, METRICS_COST_TRACKING, OPENAI_ENABLED, METRICS_RETENTION_DAYS

## SECURE-ANALYZER

✅ Has config file
✅ Uses config file in code
⚠️  6 hardcoded values:
   - main.py: os.environ.get(EnvVars.SUMMARIZER_HUB_URL_ENV, "http://summarizer-hub:5060")
   - circuit_breaker.py: os.environ.get("SECURE_ANALYZER_CIRCUIT_BREAKER_MAX_FAILURES", str(DEFAULT_CIRCUIT_BREAKER_MAX_FAILURES)
   - circuit_breaker.py: os.environ.get("SECURE_ANALYZER_CIRCUIT_BREAKER_TIMEOUT", str(DEFAULT_CIRCUIT_BREAKER_TIMEOUT)
   ... and 3 more

## SHARED

✅ Has config file
✅ Uses config file in code
⚠️  31 hardcoded values:
   - standardized_logger.py: os.environ.get('HOSTNAME', 'unknown')
   - standardized_logger.py: os.environ.get("LOG_LEVEL", "INFO")
   - standardized_logger.py: os.environ.get("LOG_FORMAT", "json")
   ... and 28 more
💡 Recommendations:
   - Unused config variables: OPENAI_MODEL, HEALTH_TIMEOUT, AWS_ACCESS_KEY_ID, OLLAMA_HOST, CONFLUENCE_BASE_URL, POSTGRES_PORT, POSTGRES_DB, HEALTH_CHECK_INTERVAL, PROMPT_STORE_DB, BEDROCK_API_KEY, DOCSTORE_CONNECTION_POOL_SIZE, REDIS_HOST, OPENAI_API_KEY, JIRA_EMAIL, JIRA_BASE_URL, POSTGRES_HOST, OLLAMA_ENDPOINT, ANTHROPIC_MODEL, OLLAMA_MODEL, GITHUB_API_BASE, POSTGRES_PASSWORD, GITHUB_MCP_URL, AWS_SECRET_ACCESS_KEY, TESTING, ANTHROPIC_API_KEY, REDIS_PORT, CONFLUENCE_EMAIL, POSTGRES_USER, GITHUB_OWNER, BEDROCK_REGION, BEDROCK_MODEL, CONFLUENCE_API_TOKEN, AWS_SESSION_TOKEN, GITHUB_TOKEN, BEDROCK_PROXY_URL, BEDROCK_ENDPOINT, JIRA_API_TOKEN, MAX_CONNECTIONS, MAX_ITEMS, AWS_REGION

## CLI

✅ Has config file
✅ Uses config file in code
⚠️  14 hardcoded values:
   - cli_commands.py: os.environ.get("USER", "cli_user")
   - shared_utils.py: os.environ.get("USER", "cli_user")
   - source_agent.py: os.environ.get("GITHUB_API_BASE", "https://api.github.com")
   ... and 11 more
💡 Recommendations:
   - Unused config variables: ANALYSIS_SERVICE_URL, ORCHESTRATOR_URL, PROMPT_STORE_URL

## .BENCHMARKS

❌ No config file
❌ Does not use config file in code
🚨 Issues:
   - No config file found

## DATA-SERVICES-DASHBOARD

❌ No config file
❌ Does not use config file in code
🚨 Issues:
   - No config file found

## ARCHITECTURE-DIGITIZER

✅ Has config file
❌ Does not use config file in code

## SIMULATION-DASHBOARD

❌ No config file
❌ Does not use config file in code
🚨 Issues:
   - No config file found

## ANALYSIS-SERVICE

✅ Has config file
✅ Uses config file in code
⚠️  58 hardcoded values:
   - start.py: os.environ.get('SERVICE_PORT', 5020)
   - main.py: os.environ.get("TESTING", "")
   - main.py: os.environ.get("TESTING", "")
   ... and 55 more

## MEMORY-AGENT

✅ Has config file
❌ Does not use config file in code
⚠️  5 hardcoded values:
   - main.py: os.environ.get("ENVIRONMENT", "development")
   - shared_utils.py: os.environ.get("MEMORY_MAX_ITEMS", "1000")
   - shared_utils.py: os.environ.get("MEMORY_TTL_SECONDS", "3600")
   ... and 2 more

## DISCOVERY-AGENT

✅ Has config file
❌ Does not use config file in code
⚠️  1 hardcoded values:
   - shared_utils.py: os.environ.get(_ORCHESTRATOR_URL_ENV, _DEFAULT_ORCHESTRATOR_URL)

## GITHUB-MCP

✅ Has config file
✅ Uses config file in code
⚠️  6 hardcoded values:
   - config.py: os.environ.get("GITHUB_TOOLSETS", "")
   - config.py: os.environ.get("GITHUB_DYNAMIC_TOOLSETS", "0")
   - config.py: os.environ.get("GITHUB_READ_ONLY", "0")
   ... and 3 more

## MOCK-DATA-GENERATOR

✅ Has config file
✅ Uses config file in code
⚠️  6 hardcoded values:
   - main.py: os.getenv("LLM_GATEWAY_URL", "http://llm-gateway:5055")
   - main.py: os.getenv("DOC_STORE_URL", "http://doc_store:5010")
   - main.py: os.getenv("ENVIRONMENT", "development")
   ... and 3 more

## OLLAMA

❌ No config file
❌ Does not use config file in code
🚨 Issues:
   - No config file found

## DOC_STORE

✅ Has config file
✅ Uses config file in code
⚠️  2 hardcoded values:
   - connection.py: os.environ.get("DOCSTORE_DB", "services/doc_store/db.sqlite3")
   - connection.py: os.environ.get("DOCSTORE_CONNECTION_POOL_SIZE", "5")
💡 Recommendations:
   - Unused config variables: TESTING

## ORCHESTRATOR

✅ Has config file
✅ Uses config file in code
⚠️  1 hardcoded values:
   - utils.py: os.environ.get(env_var, default_url)
💡 Recommendations:
   - Unused config variables: GITHUB_AGENT_URL, CONSISTENCY_ENGINE_URL, JIRA_AGENT_URL, CONFLUENCE_AGENT_URL, SWAGGER_AGENT_URL

## BEDROCK-PROXY

✅ Has config file
❌ Does not use config file in code
💡 Recommendations:
   - Unused config variables: BEDROCK_DEFAULT_MODEL, BEDROCK_DEFAULT_REGION

## SUMMARY
- **Total Services:** 27
- **Services with config files:** 21 (77%)
- **Services using config files:** 13 (48%)
- **Services with hardcoded values:** 18 (66%)

## REQUIRED ACTIONS
The following services need configuration transitions:

### interpreter
- [ ] Create/update config file
- [ ] Replace hardcoded values with config loading
- [ ] Update Dockerfile if needed
- [ ] Test configuration loading

### source-agent
- [ ] Create/update config file
- [ ] Replace hardcoded values with config loading
- [ ] Update Dockerfile if needed
- [ ] Test configuration loading

### frontend
- [ ] Create/update config file
- [ ] Replace hardcoded values with config loading
- [ ] Update Dockerfile if needed
- [ ] Test configuration loading

### notification-service
- [ ] Create/update config file
- [ ] Replace hardcoded values with config loading
- [ ] Update Dockerfile if needed
- [ ] Test configuration loading

### code-analyzer
- [ ] Create/update config file
- [ ] Replace hardcoded values with config loading
- [ ] Update Dockerfile if needed
- [ ] Test configuration loading

### prompt_store
- [ ] Create/update config file
- [ ] Replace hardcoded values with config loading
- [ ] Update Dockerfile if needed
- [ ] Test configuration loading

### summarizer-hub
- [ ] Create/update config file
- [ ] Replace hardcoded values with config loading
- [ ] Update Dockerfile if needed
- [ ] Test configuration loading

### llm-gateway
- [ ] Create/update config file
- [ ] Replace hardcoded values with config loading
- [ ] Update Dockerfile if needed
- [ ] Test configuration loading

### secure-analyzer
- [ ] Create/update config file
- [ ] Replace hardcoded values with config loading
- [ ] Update Dockerfile if needed
- [ ] Test configuration loading

### shared
- [ ] Create/update config file
- [ ] Replace hardcoded values with config loading
- [ ] Update Dockerfile if needed
- [ ] Test configuration loading

### cli
- [ ] Create/update config file
- [ ] Replace hardcoded values with config loading
- [ ] Update Dockerfile if needed
- [ ] Test configuration loading

### analysis-service
- [ ] Create/update config file
- [ ] Replace hardcoded values with config loading
- [ ] Update Dockerfile if needed
- [ ] Test configuration loading

### memory-agent
- [ ] Create/update config file
- [ ] Replace hardcoded values with config loading
- [ ] Update Dockerfile if needed
- [ ] Test configuration loading

### discovery-agent
- [ ] Create/update config file
- [ ] Replace hardcoded values with config loading
- [ ] Update Dockerfile if needed
- [ ] Test configuration loading

### github-mcp
- [ ] Create/update config file
- [ ] Replace hardcoded values with config loading
- [ ] Update Dockerfile if needed
- [ ] Test configuration loading

### mock-data-generator
- [ ] Create/update config file
- [ ] Replace hardcoded values with config loading
- [ ] Update Dockerfile if needed
- [ ] Test configuration loading

### doc_store
- [ ] Create/update config file
- [ ] Replace hardcoded values with config loading
- [ ] Update Dockerfile if needed
- [ ] Test configuration loading

### orchestrator
- [ ] Create/update config file
- [ ] Replace hardcoded values with config loading
- [ ] Update Dockerfile if needed
- [ ] Test configuration loading

## CONFIGURATION BEST PRACTICES
1. **Environment Variables**: Use ${VAR_NAME} syntax in config files
2. **Default Values**: Provide sensible defaults in config files
3. **Config Loading**: Load config files at service startup
4. **Validation**: Validate required config values on startup
5. **Documentation**: Document all configuration options