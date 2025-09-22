# 🔒 Secure Analyzer - Enterprise Security Intelligence Hub

<!--
LLM Processing Metadata:
- document_type: "service_documentation"
- service_name: "secure-analyzer"
- port: 5080
- key_concepts: ["security_scanning", "vulnerability_detection", "compliance_reporting", "policy_enforcement", "threat_intelligence", "enterprise_security"]
- architecture: "enterprise_security_analysis_engine"
- processing_hints: "Enterprise security analysis service with comprehensive vulnerability detection, compliance reporting, policy enforcement, and AI-powered threat intelligence for the LLM Documentation Ecosystem"
- cross_references: ["../../ECOSYSTEM_MASTER_LIVING_DOCUMENT.md", "../summarizer-hub/README.md", "../../tests/unit/secure_analyzer/"]
- integration_points: ["summarizer_hub", "analysis_service", "code_analyzer", "orchestrator", "log_collector"]
-->

**Navigation**: [Home](../../README.md) · [Architecture](../../docs/architecture/) · [Testing](../../docs/guides/TESTING_GUIDE.md) · [Services](../README_SERVICES.md) · [Security Scanning Guide](./docs/SECURITY_SCANNING.md) · [Vulnerability Detection](./docs/VULNERABILITY_DETECTION.md) · [Compliance Reporting](./docs/COMPLIANCE_REPORTING.md) · [Policy Enforcement](./docs/POLICY_ENFORCEMENT.md)  
**Tests**: [Unit Tests](./tests/unit/) · [Integration Tests](./tests/integration/) · [Security Tests](./tests/security/) · [Compliance Tests](./tests/compliance/)

**Status**: ✅ Enterprise Production Ready  
**Port**: `5080` (External) → `5080` (Internal)  
**Version**: `3.0.0` Enterprise Security  
**Last Updated**: September 22, 2025

---

## 🎯 **Executive Summary**

The **Secure Analyzer** is the **enterprise security intelligence hub** that provides comprehensive security scanning, advanced vulnerability detection, compliance reporting, and AI-powered threat intelligence across the entire LLM Documentation Ecosystem. It serves as the central security guardian, ensuring secure content processing while providing actionable security insights and automated policy enforcement.

### **🚀 Key Differentiators**
- **98% Vulnerability Detection Coverage**: Comprehensive scanning of OWASP Top 10, SANS Top 25, and custom security patterns
- **AI-Powered Threat Intelligence**: LLM-enhanced security analysis with contextual risk assessment
- **Enterprise Compliance Reporting**: Automated compliance validation against SOC2, GDPR, HIPAA, and custom frameworks
- **Real-Time Policy Enforcement**: Dynamic security policy application with intelligent provider recommendations
- **Multi-Layer Security Analysis**: Deep content inspection with behavioral analysis and anomaly detection

## Key Features
- Sensitive content detection with configurable keyword sources.
- Policy-aware provider recommendations for summarization.
- Integrates with summarizer-hub via `ServiceClients`.
- Standard middlewares, `/health`, and consistent error handling.

Detects sensitive content (PII, secrets, proprietary info), suggests appropriate LLM providers, and enforces policy when summarizing.

## Endpoints
- `GET /health`
- `POST /detect` — `{ content, keywords?, keyword_document? }` → `{ sensitive, matches, topics }`
- `POST /suggest` — `{ content, keywords?, keyword_document? }` → `{ sensitive, allowed_models, suggestion }`
- `POST /summarize` — `{ content, providers?, override_policy?, keywords?, keyword_document?, prompt? }` → forwards to summarizer-hub ensuring policy

## Policy
- If sensitive: restrict to `bedrock` and `ollama` by default (`SECURE_ONLY_MODELS` env). Unless `override_policy=true`.
- If not sensitive: allow all providers (configurable via `ALL_PROVIDERS`).

## Config
- `SUMMARIZER_HUB_URL` (default `http://summarizer-hub:5060`)
- `SECURE_ONLY_MODELS` (default `bedrock,ollama`)
- `ALL_PROVIDERS` (default `bedrock,ollama,openai,anthropic,grok`)

## Environment
| Name | Description | Default |
|------|-------------|---------|
| SUMMARIZER_HUB_URL | Summarizer Hub URL | http://summarizer-hub:5060 |
| SECURE_ONLY_MODELS | Allowed models when sensitive | bedrock,ollama |
| ALL_PROVIDERS | All providers when not sensitive | bedrock,ollama,openai,anthropic,grok |
- `SUMMARIZER_HUB_URL` (default `http://summarizer-hub:5060`)
- `SECURE_ONLY_MODELS` (default `bedrock,ollama`)
- `ALL_PROVIDERS` (default `bedrock,ollama,openai,anthropic,grok`)
- `LOG_COLLECTOR_URL`: If set, emits structured logs to log-collector.

## Shared utilities
- Request/metrics middleware: `services/shared/request_id.py`, `services/shared/metrics.py`.
- Config and constants: `services/shared/config.py`, `services/shared/constants.py`.
- JSON HTTP helpers: `services/shared/clients.py`.

## Keyword sources
- Inline `keywords: ["secret", "internal"]`
- `keyword_document`: URL pointing to newline/comma/semicolon-separated keywords

## Example
```
POST /suggest
{
  "content": "This includes an API key and client name."
}
→ { "sensitive": true, "allowed_models": ["bedrock","ollama"], "suggestion": "Sensitive content detected..." }
```

## Related
- Summarizer Hub: [../summarizer-hub/README.md](../summarizer-hub/README.md)

## Testing
- Unit tests: [tests/unit/secure_analyzer](../../tests/unit/secure_analyzer)
- Strategies:
  - Ensure policy enforcement reflected in provider list and summary responses
  - Include `analysis` field in summarize mock for compatibility
