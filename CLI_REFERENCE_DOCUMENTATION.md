# 🚀 CLI Reference Documentation - LLM Documentation Ecosystem

**CLI Service**: Comprehensive command-line interface for the entire ecosystem  
**Total Commands**: 60+ commands across 15 categories  
**Access Methods**: Docker exec, Web terminal, Direct Python execution  
**Last Updated**: September 18, 2025

---

## 📋 **Quick Start**

### **Access the CLI**

#### **Option 1: Web Terminal (Recommended)**
```bash
# Open browser to http://localhost:3000/cli/terminal
# Interactive web-based terminal with full CLI access
```

#### **Option 2: Docker Exec**
```bash
# Access CLI container directly
docker exec -it hackathon-cli-1 /bin/bash
cd /app && python services/cli/main.py --help
```

#### **Option 3: Direct Execution**
```bash
# From project root
cd /Users/mykalthomas/Documents/work/Hackathon
python services/cli/main.py --help
```

### **Basic Usage**
```bash
# Show all available commands
./cli.py --help

# Get help for specific command
./cli.py health --help

# Interactive mode for guided operations
./cli.py interactive
```

---

## 📊 **Command Categories Overview**

| Category | Commands | Primary Use Case |
|----------|----------|------------------|
| **🏥 Health & Monitoring** | 8 commands | Service health, monitoring, diagnostics |
| **🤖 AI & LLM Operations** | 12 commands | LLM queries, prompt management, AI workflows |
| **📄 Document Management** | 10 commands | Document persistence, provenance, downloads |
| **🔍 Analysis & Quality** | 8 commands | Document analysis, findings, reports |
| **🔧 Service Management** | 6 commands | Service discovery, configuration, deployment |
| **💾 Data Operations** | 5 commands | Memory management, data import/export |
| **🔒 Security & Compliance** | 4 commands | Security analysis, content detection |
| **📨 Notifications** | 3 commands | Alert management, notification delivery |
| **📊 Logging & Events** | 4 commands | Log collection, event monitoring |
| **⚙️ Configuration** | 5 commands | Environment, config, validation |

---

## 🏥 **Health & Monitoring Commands**

### **Basic Health Checks**

#### **`health`** - System Health Overview
```bash
# Check ecosystem health status
./cli.py health

# Example output:
# ✅ All 17 services healthy
# Average response time: 0.123s
# Last check: 2025-09-18 10:30:15
```

#### **`redis-info`** - Redis Status
```bash
# Check Redis connectivity and stats
./cli.py redis-info

# Shows: Memory usage, connected clients, keyspace info
```

#### **`dlq-stats`** - Dead Letter Queue Status
```bash
# Check failed message queue status
./cli.py dlq-stats

# Shows: Failed messages, retry counts, error patterns
```

### **Advanced Monitoring**

#### **`saga-monitor`** - Workflow Monitoring
```bash
# Monitor distributed workflow status
./cli.py saga-monitor

# Shows: Active sagas, completion rates, failed transactions
```

#### **`view-dashboards`** - Monitoring Dashboards
```bash
# Access monitoring dashboards
./cli.py view-dashboards

# Opens: Grafana, Prometheus, custom dashboards
```

#### **`view-alerts`** - System Alerts
```bash
# View active system alerts
./cli.py view-alerts

# Shows: Critical alerts, warnings, resolved issues
```

#### **`view-metrics`** - Performance Metrics
```bash
# View system performance metrics
./cli.py view-metrics

# Shows: CPU, memory, response times, throughput
```

#### **`view-slo-status`** - Service Level Objectives
```bash
# View SLO compliance status
./cli.py view-slo-status

# Shows: Uptime, performance SLOs, compliance rates
```

---

## 🤖 **AI & LLM Operations**

### **Core LLM Operations**

#### **`invoke-ai`** - Direct LLM Queries
```bash
# Simple AI query with auto-provider selection
./cli.py invoke-ai "Explain Docker containers"

# With user context
./cli.py invoke-ai "Generate API documentation" --user-id developer1

# Example output:
# Provider: ollama (auto-selected)
# Response: Docker containers are lightweight, portable...
# Tokens: 150, Cost: $0.001, Time: 2.3s
```

#### **`multi-ai-query`** - Multi-Provider Comparison
```bash
# Compare responses across multiple providers
./cli.py multi-ai-query "What is microservices architecture?" \
  --providers ollama,openai,anthropic

# Shows side-by-side comparison of responses
```

#### **`test-ai-provider`** - Provider Testing
```bash
# Test specific AI provider
./cli.py test-ai-provider ollama

# Output: Provider status, available models, response time
```

### **Advanced AI Operations**

#### **`ai-templates`** - Available AI Templates
```bash
# List available AI response templates
./cli.py ai-templates

# Templates: summary, risks, decisions, pr_confidence, life_of_ticket
```

#### **`ai-recent-invocations`** - AI Usage History
```bash
# View recent AI invocations
./cli.py ai-recent-invocations --limit 10

# Shows: Queries, providers used, response times, costs
```

### **Document Generation Workflows**

#### **`execute-e2e-query`** - End-to-End Document Generation
```bash
# Natural language to persistent document
./cli.py execute-e2e-query "Create a REST API specification" --format markdown

# Process: Query → Interpretation → Workflow → Document → Storage
# Output: Document ID, download URL, provenance data
```

#### **`execute-direct-workflow`** - Direct Workflow Execution
```bash
# Execute specific workflow template
./cli.py execute-direct-workflow --name "api_documentation" \
  --params '{"service": "user-service", "version": "1.0"}'

# Available workflows: api_docs, technical_spec, user_guide, etc.
```

#### **`list-workflow-templates`** - Available Templates
```bash
# List all workflow templates
./cli.py list-workflow-templates

# Output: Template names, descriptions, required parameters
```

#### **`get-supported-formats`** - Output Formats
```bash
# List supported output formats
./cli.py get-supported-formats

# Formats: json, pdf, csv, markdown, zip, txt
```

---

## 📄 **Document Management**

### **Document Persistence Operations**

#### **`download-file`** - Download Generated Files
```bash
# Download by file ID
./cli.py download-file --file-id "doc_12345" --save-path "./output.pdf"

# Downloads files generated by workflows
```

#### **`download-document`** - Download from Doc Store
```bash
# Download persistent document
./cli.py download-document --doc-id "store_67890" --save-path "./report.md"

# Downloads documents stored in doc_store with full metadata
```

#### **`get-document-provenance`** - Document Provenance
```bash
# Get comprehensive document provenance
./cli.py get-document-provenance --doc-id "store_67890"

# Shows: Creation workflow, prompts used, service chain, timestamps
```

#### **`list-workflow-documents`** - Documents by Workflow
```bash
# List documents generated by specific workflow
./cli.py list-workflow-documents --workflow "api_documentation" --limit 20

# Shows: Document IDs, creation dates, file sizes, formats
```

#### **`get-execution-trace`** - Workflow Execution Details
```bash
# Get detailed execution trace
./cli.py get-execution-trace --execution-id "exec_abc123"

# Shows: Step-by-step execution, timing, intermediate results
```

### **Document Import/Export**

#### **`export-documents`** - Bulk Document Export
```bash
# Export documents matching criteria
./cli.py export-documents --format json --criteria '{"type": "api_docs"}'

# Exports to: JSON, CSV, XML formats
```

#### **`import-documents`** - Bulk Document Import
```bash
# Import documents from file
./cli.py import-documents --file "documents.json" --format json

# Supports: JSON, CSV, XML import formats
```

---

## 🔍 **Analysis & Quality Commands**

### **Document Analysis**

#### **`run-analysis`** - Document Analysis
```bash
# Analyze specific documents
./cli.py run-analysis doc1 doc2 doc3 --detectors consistency,quality,security

# Available detectors: consistency, quality, security, readability, completeness
```

#### **`view-findings`** - Analysis Results
```bash
# View analysis findings with filtering
./cli.py view-findings --severity high --type consistency

# Severities: critical, high, medium, low, info
# Types: consistency, quality, security, readability
```

#### **`generate-report`** - Analysis Reports
```bash
# Generate comprehensive analysis reports
./cli.py generate-report --type summary
./cli.py generate-report --type trends --time-period 30d
./cli.py generate-report --type quality

# Report types: summary, trends, quality, compliance
```

### **Quality Management**

#### **`recalculate-quality-scores`** - Quality Recalculation
```bash
# Recalculate quality scores
./cli.py recalculate-quality-scores --type all --threshold 0.7

# Recalculates scores for documents below threshold
```

#### **`notify-owners`** - Quality Notifications
```bash
# Notify document owners of quality issues
./cli.py notify-owners --criteria '{"quality_score": {"lt": 0.6}}' \
  --message "Please review document quality"

# Sends notifications based on quality criteria
```

---

## 🔧 **Service Management**

### **Service Discovery & Configuration**

#### **`discover-tools`** - Service Discovery
```bash
# Discover tools from specific service
./cli.py discover-tools orchestrator

# Discover from all services
./cli.py discover-tools --all-services

# Output: Available tools, capabilities, API endpoints
```

#### **`list-tools`** - Available Tools
```bash
# List discovered tools with filtering
./cli.py list-tools --category analysis --service prompt_store

# Shows: Tool names, descriptions, parameters, examples
```

#### **`test-tools`** - Tool Testing
```bash
# Test tools for specific service
./cli.py test-tools prompt_store --tool-name create_prompt

# Validates tool functionality and parameters
```

#### **`register-service`** - Service Registration
```bash
# Register new service with discovery
./cli.py register-service --name "custom-service" --url "http://localhost:8080"

# Registers service for ecosystem integration
```

### **Configuration Management**

#### **`view-config`** - View Configuration
```bash
# View configuration for specific service
./cli.py view-config --service llm-gateway

# View system-wide configuration
./cli.py view-config

# Shows: Environment variables, service settings, feature flags
```

#### **`set-env`** - Set Environment Variables
```bash
# Set environment variable
./cli.py set-env DEBUG true
./cli.py set-env MAX_WORKERS 8

# Updates runtime configuration
```

#### **`get-env`** - View Environment
```bash
# View current environment variables
./cli.py get-env

# Shows: All environment variables with values
```

#### **`validate-config`** - Configuration Validation
```bash
# Validate system configuration
./cli.py validate-config

# Checks: Required variables, service connectivity, dependencies
```

### **Deployment Management**

#### **`scale-service`** - Service Scaling
```bash
# Scale service replicas
./cli.py scale-service orchestrator 3

# Scales service to specified number of replicas
```

#### **`deployment-status`** - Deployment Status
```bash
# Check deployment status
./cli.py deployment-status

# Shows: Service versions, replica counts, health status
```

#### **`update-service`** - Service Updates
```bash
# Update service image
./cli.py update-service llm-gateway myregistry/llm-gateway:v2.0

# Triggers rolling update to new version
```

---

## 💾 **Data Operations**

### **Memory Management**

#### **`store-memory`** - Store Memory Items
```bash
# Store operational memory
./cli.py store-memory --type operation --key "workflow_123" \
  "Successfully completed document analysis workflow"

# Types: operation, llm_summary, doc_summary, api_summary, finding
```

#### **`list-memory`** - List Memory Items
```bash
# List memory items with filtering
./cli.py list-memory --type operation --key "workflow_*"

# Shows: Memory items, types, keys, timestamps, content
```

### **Prompt Management**

#### **`list-prompts`** - List Available Prompts
```bash
# List prompts by category
./cli.py list-prompts --category analysis

# Shows: Prompt names, categories, descriptions, usage stats
```

#### **`get-prompt`** - Get Specific Prompt
```bash
# Retrieve specific prompt
./cli.py get-prompt analysis consistency_check

# Shows: Prompt content, metadata, usage examples
```

---

## 🔒 **Security & Compliance**

### **Content Security**

#### **`detect-sensitive`** - Sensitive Content Detection
```bash
# Detect sensitive information in text
./cli.py detect-sensitive "User email: john@company.com, SSN: 123-45-6789" \
  --keywords "api-key,password"

# Detects: PII, credentials, sensitive keywords
```

#### **`suggest-security`** - Security Suggestions
```bash
# Get security improvement suggestions
./cli.py suggest-security "API documentation with example API keys"

# Provides: Security recommendations, best practices
```

#### **`secure-summarize`** - Secure Summarization
```bash
# Generate secure summary with policy enforcement
./cli.py secure-summarize "Confidential project documentation" \
  --override-policy

# Creates: Sanitized summaries, removes sensitive content
```

### **Code Security**

#### **`analyze-code-security`** - Code Security Analysis
```bash
# Analyze code for security issues
./cli.py analyze-code-security "def authenticate(password):" \
  --language python

# Detects: Security vulnerabilities, unsafe patterns
```

---

## 📨 **Notification Management**

### **Notification Operations**

#### **`send-notification`** - Send Notifications
```bash
# Send webhook notification
./cli.py send-notification --channel webhook \
  --target "https://hooks.slack.com/..." \
  --subject "System Alert" \
  --message "High CPU usage detected"

# Channels: webhook, email, slack
```

#### **`resolve-owners`** - Owner Resolution
```bash
# Resolve notification targets for owners
./cli.py resolve-owners "john.doe,team-alpha"

# Output: Resolved email addresses, Slack channels, webhooks
```

#### **`update-ownership`** - Update Document Ownership
```bash
# Update document ownership
./cli.py update-ownership --id "doc_123" --owner "new-team"

# Updates: Document ownership metadata
```

---

## 📊 **Logging & Events**

### **Log Management**

#### **`create-log-entry`** - Create Log Entry
```bash
# Create structured log entry
./cli.py create-log-entry --service "custom-service" --level warning \
  --message "Custom workflow completed with warnings" \
  --metadata '{"workflow_id": "wf_123", "duration": 45.2}'

# Levels: debug, info, warning, error, fatal
```

#### **`view-logs`** - View System Logs
```bash
# View logs with filtering
./cli.py view-logs --service llm-gateway --level error --limit 50

# Shows: Timestamp, service, level, message, metadata
```

#### **`log-stats`** - Log Statistics
```bash
# View log statistics and trends
./cli.py log-stats

# Shows: Log volume by service, error rates, trends
```

#### **`workflow-triggered-analysis`** - Workflow Events
```bash
# Trigger analysis from workflow events
./cli.py workflow-triggered-analysis --type "document_updated" \
  --config '{"auto_analyze": true, "detectors": ["quality", "consistency"]}'

# Triggers: Automated analysis based on workflow events
```

---

## 📋 **Interactive Mode**

### **`interactive`** - Guided CLI Experience
```bash
# Start interactive mode for guided operations
./cli.py interactive

# Provides:
# 1. Menu-driven interface
# 2. Command suggestions
# 3. Parameter guidance
# 4. Operation wizards
# 5. Help context
```

**Interactive Menu Structure:**
```
🏥 Health & Monitoring
  ├── Check System Health
  ├── View Service Status
  ├── Monitor Performance
  └── View Alerts

🤖 AI & LLM Operations
  ├── Execute AI Query
  ├── Compare Providers
  ├── Generate Documents
  └── Manage Prompts

📄 Document Management
  ├── Create Documents
  ├── Download Files
  ├── View Provenance
  └── Manage Storage

🔍 Analysis & Quality
  ├── Run Analysis
  ├── View Findings
  ├── Generate Reports
  └── Quality Management

🔧 Service Management
  ├── Discover Services
  ├── Configuration
  ├── Deployment
  └── Tool Management
```

---

## 🎯 **Common Workflow Examples**

### **End-to-End Document Generation**
```bash
# Complete workflow: Query → Document → Download
./cli.py execute-e2e-query "Create user authentication API documentation" --format pdf
./cli.py list-workflow-documents --workflow "api_documentation" --limit 5
./cli.py download-document --doc-id "generated_id" --save-path "./auth_api.pdf"
./cli.py get-document-provenance --doc-id "generated_id"
```

### **System Health & Performance Monitoring**
```bash
# Comprehensive system monitoring
./cli.py health
./cli.py view-alerts
./cli.py view-metrics
./cli.py redis-info
./cli.py dlq-stats
```

### **AI Provider Testing & Comparison**
```bash
# Test and compare AI providers
./cli.py test-ai-provider ollama
./cli.py multi-ai-query "Explain REST APIs" --providers ollama,openai
./cli.py ai-recent-invocations --limit 10
```

### **Document Analysis & Quality Management**
```bash
# Analyze and manage document quality
./cli.py run-analysis doc1 doc2 --detectors quality,consistency
./cli.py view-findings --severity high
./cli.py generate-report --type quality
./cli.py notify-owners --criteria '{"quality_score": {"lt": 0.7}}' --message "Quality review needed"
```

### **Service Discovery & Tool Management**
```bash
# Discover and test ecosystem tools
./cli.py discover-tools --all-services
./cli.py list-tools --category analysis
./cli.py test-tools prompt_store
./cli.py view-config --service llm-gateway
```

---

## 🔧 **Advanced Usage**

### **JSON Parameters & Criteria**
Many commands accept JSON parameters for complex configurations:

```bash
# Complex analysis criteria
./cli.py export-documents --criteria '{
  "type": "api_docs",
  "quality_score": {"gte": 0.8},
  "last_modified": {"gte": "2025-09-01"},
  "tags": ["production", "public"]
}'

# Workflow parameters
./cli.py execute-direct-workflow --name "compliance_report" --params '{
  "compliance_frameworks": ["SOC2", "GDPR"],
  "include_remediation": true,
  "output_format": "pdf"
}'

# Memory filtering
./cli.py list-memory --type operation --key "workflow_*" --criteria '{
  "timestamp": {"gte": "2025-09-15"},
  "status": "completed"
}'
```

### **Batch Operations**
```bash
# Batch document analysis
./cli.py run-analysis $(./cli.py search-documents --criteria '{"type": "api_docs"}' --format ids)

# Batch notification
./cli.py notify-owners --criteria '{"quality_score": {"lt": 0.6}}' \
  --message "Quarterly quality review required"

# Batch memory storage
for workflow in $(./cli.py list-workflows --active); do
  ./cli.py store-memory --type operation --key "$workflow" "Workflow $workflow completed"
done
```

### **Pipeline Integration**
```bash
# CI/CD pipeline integration
set -e  # Exit on error

# Health check before deployment
./cli.py health || exit 1

# Run quality analysis
./cli.py run-analysis $(./cli.py list-documents --recent) --detectors all

# Check for critical findings
CRITICAL_COUNT=$(./cli.py view-findings --severity critical --format count)
if [ "$CRITICAL_COUNT" -gt 0 ]; then
  echo "Critical findings detected, stopping deployment"
  exit 1
fi

# Deploy and verify
./cli.py update-service myservice myregistry/myservice:latest
./cli.py health
```

---

## 🎓 **Tips & Best Practices**

### **Performance Optimization**
- Use `--limit` parameters for large datasets
- Filter results with `--criteria` for complex queries
- Use batch operations for multiple related tasks
- Monitor system resources with health commands

### **Error Handling**
- Check command exit codes in scripts
- Use `--help` for parameter details
- View logs with `view-logs` for troubleshooting
- Validate configuration with `validate-config`

### **Security Best Practices**
- Use `detect-sensitive` before sharing content
- Apply security policies with `secure-summarize`
- Regular security analysis with `analyze-code-security`
- Monitor sensitive operations with logging

### **Workflow Efficiency**
- Start with `interactive` mode for learning
- Use templates with `list-workflow-templates`
- Monitor executions with `get-execution-trace`
- Maintain provenance with document operations

---

## 📞 **Getting Help**

### **Command-Level Help**
```bash
# General help
./cli.py --help

# Command-specific help
./cli.py health --help
./cli.py execute-e2e-query --help

# Interactive guidance
./cli.py interactive
```

### **Documentation Resources**
- **[API Documentation Index](API_DOCUMENTATION_INDEX.md)** - Complete API reference
- **[Developer Onboarding](DEVELOPER_ONBOARDING.md)** - Getting started guide
- **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - Production deployment
- **[Service READMEs](services/)** - Individual service documentation

### **Troubleshooting**
- Check service health: `./cli.py health`
- View system logs: `./cli.py view-logs`
- Validate configuration: `./cli.py validate-config`
- Monitor alerts: `./cli.py view-alerts`

---

**🎯 The CLI provides complete access to all 350+ endpoints across 17 services in the LLM Documentation Ecosystem, enabling powerful automation, monitoring, and development workflows through a unified command-line interface.**

**Happy automating!** 🚀
