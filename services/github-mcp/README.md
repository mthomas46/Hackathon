# 🐙 GitHub MCP - GitHub Integration & Model Context Protocol

<!--
LLM Processing Metadata:
- document_type: "service_documentation"
- service_name: "github-mcp"
- port: 5030
- key_concepts: ["github_integration", "mcp", "tool_interface", "repository_analysis"]
- architecture: "model_context_protocol"
- processing_hints: "GitHub integration service with MCP-based tool interface for repository operations and code analysis"
- cross_references: ["../../ECOSYSTEM_MASTER_LIVING_DOCUMENT.md", "../source-agent/README.md", "../../tests/unit/github_mcp/"]
- integration_points: ["source_agent", "code_analyzer", "orchestrator", "github_api"]
-->

**Navigation**: [Home](../../README.md) · [Architecture](../../docs/architecture/) · [Testing](../../docs/guides/TESTING_GUIDE.md) · [Services](../README_SERVICES.md)  
**Tests**: [tests/unit/github_mcp](../../tests/unit/github_mcp)

**Status**: ✅ Production Ready  
**Port**: `5030` (External) → `5072` (Internal)  
**Version**: `1.8.0`  
**Last Updated**: September 18, 2025

## 🎯 **Overview & Purpose**

The **GitHub MCP Service** is a **GitHub integration platform** implementing the Model Context Protocol (MCP) to provide seamless GitHub repository operations for the ecosystem. It offers both mock-friendly development capabilities and production GitHub integration through a standardized tool interface.

**Core Mission**: Bridge GitHub operations with ecosystem services through MCP-based tool interfaces, enabling automated repository analysis, code ingestion, and development workflow integration.

## 🚀 **Key Features & Capabilities**

### **🔧 Model Context Protocol (MCP) Implementation**
- **Standardized Tool Interface**: MCP-compliant tool definitions for consistent GitHub operations
- **Dynamic Tool Discovery**: Runtime tool registration and capability advertisement
- **Tool Categorization**: Organized tool sets for repos, issues, PRs, and code analysis
- **Flexible Invocation**: Standardized tool invocation with parameter validation

### **🐙 GitHub Integration**
- **Repository Operations**: Comprehensive repository browsing, search, and analysis capabilities
- **Issue Management**: Issue creation, reading, and lifecycle management integration
- **Pull Request Handling**: PR analysis and integration with code review workflows
- **Code Analysis**: Integration with Code Analyzer for repository code intelligence

### **🧪 Development & Testing**
- **Mock-First Design**: Comprehensive mocking capabilities for development and testing
- **Environment Switching**: Seamless switching between mock and production GitHub operations
- **Read-Only Gating**: Safety mechanisms to prevent unintended write operations
- **Local Development**: Standalone operation for development without external dependencies

### **⚙️ Flexible Configuration**
- **Dynamic Toolsets**: Runtime configuration of available tool categories
- **Query Parameter Control**: Dynamic tool filtering via API query parameters
- **Environment Adaptation**: Automatic adaptation based on deployment environment
- **External Proxy**: Optional proxying to external MCP servers for extended capabilities

## 📡 **API Reference**

### **🔧 Core MCP Endpoints**

| Method | Path | Description | Purpose |
|--------|------|-------------|---------|
| **GET** | `/health` | Service health check | System monitoring and availability verification |
| **GET** | `/info` | Service information and flags | Configuration and capability discovery |
| **GET** | `/tools` | List available tools | Tool discovery with optional toolset filtering |
| **POST** | `/tools/{tool}/invoke` | Invoke specific tool | Execute GitHub operations through MCP interface |

### **🐙 Tool Categories**

| Toolset | Operations | Purpose |
|---------|------------|---------|
| **repos** | Repository search, browsing, analysis | Repository discovery and content access |
| **issues** | Issue creation, reading, management | Issue tracking and workflow integration |
| **prs** | Pull request analysis and review | Code review and change management |
| **code** | Code analysis and extraction | Source code intelligence and processing |

### **🔍 Usage Examples**

#### **Tool Discovery**
```bash
# List all available tools
curl http://localhost:5030/tools

# List tools by category
curl http://localhost:5030/tools?toolsets=repos,issues
```

#### **Repository Search**
```bash
curl -X POST http://localhost:5030/tools/github.search_repos/invoke \
  -H 'Content-Type: application/json' \
  -d '{
    "arguments": {
      "q": "documentation ecosystem",
      "limit": 5,
      "sort": "updated"
    }
  }'
```

#### **Issue Operations**
```bash
curl -X POST http://localhost:5030/tools/github.create_issue/invoke \
  -H 'Content-Type: application/json' \
  -d '{
    "arguments": {
      "repo": "myorg/myrepo",
      "title": "Documentation Update Required",
      "body": "Analysis found inconsistencies requiring documentation updates"
    }
  }'
```

## 🏗️ **Architecture & Design**

### **🎯 MCP Architecture**
The GitHub MCP Service implements a clean, extensible architecture based on the Model Context Protocol:

#### **Core Components**
- **Tool Registry**: Dynamic registration and management of available GitHub tools
- **Mock Engine**: Comprehensive mocking system for development and testing
- **GitHub Client**: Production GitHub API integration with authentication and rate limiting
- **Request Router**: Intelligent routing between mock and production implementations

#### **Integration Patterns**
- **Tool Interface**: Standardized MCP tool definitions for consistent operation
- **Mock/Production Switching**: Environment-based switching between mock and real GitHub operations
- **Safety Mechanisms**: Read-only gating and validation for production deployments
- **Event Integration**: Integration with ecosystem event streams for workflow coordination

## ⚙️ **Configuration**

### **🔧 Environment Variables**

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GITHUB_MOCK` | Use mock responses instead of real GitHub API | `1` | Optional |
| `GITHUB_TOOLSETS` | Comma-separated list of allowed toolsets | `repos,issues` | Optional |
| `GITHUB_DYNAMIC_TOOLSETS` | Enable query parameter toolset control | `0` | Optional |
| `GITHUB_READ_ONLY` | Enable read-only mode for write operations | `0` | Optional |
| `GITHUB_TOKEN` | GitHub API token for production mode | - | Production |

### **🎯 Service Dependencies**

| Service | Purpose | Integration | Required |
|---------|---------|-------------|----------|
| **Source Agent** | Repository content ingestion | Code and documentation analysis | Integration |
| **Code Analyzer** | Repository code analysis | Automated code intelligence | Integration |
| **Orchestrator** | Workflow coordination | Automated GitHub operations | Optional |
| **GitHub API** | Production GitHub operations | Real repository access | Production |

## 🔗 **Integration Points**

### **🎯 Ecosystem Integration**
- **Source Agent**: Provides repository data for content ingestion and analysis workflows
- **Code Analyzer**: Feeds repository code for comprehensive analysis and intelligence
- **Orchestrator**: Enables automated GitHub operations within broader ecosystem workflows
- **Event Streaming**: Publishes GitHub operation events for real-time ecosystem coordination

### **🐙 GitHub Operations**
- **Repository Discovery**: Automated repository discovery and content analysis
- **Issue Automation**: Automated issue creation and management based on analysis findings
- **Code Review Integration**: PR analysis and automated code review processes
- **Workflow Automation**: Integration with GitHub Actions and workflow systems

## 🧪 **Testing**

### **🔧 Test Coverage**
- **Unit Tests**: [tests/unit/github_mcp](../../tests/unit/github_mcp) - Comprehensive unit test suite
- **Mock Validation**: Comprehensive testing of mock tool responses and behavior
- **Integration Tests**: GitHub API integration and real operation validation
- **Security Tests**: Read-only gating and permission validation

### **📊 Testing Strategies**
- **Mock Tool Invocation**: Validation of mock responses and read-only gating mechanisms
- **GitHub API Integration**: Testing real GitHub operations in controlled environments
- **Tool Discovery**: Dynamic tool registration and capability advertisement testing
- **Error Handling**: Network failures, API limits, and authentication error scenarios

## 🔗 **Related Documentation**

### **📖 Primary References**
- **[Ecosystem Master Living Document](../../ECOSYSTEM_MASTER_LIVING_DOCUMENT.md#github-mcp-service-port-5030---github-integration)** - Complete technical reference
- **[Source Agent Service](../source-agent/README.md)** - Repository content ingestion integration
- **[Code Analyzer Service](../code-analyzer/README.md)** - Repository code analysis integration

### **🎯 Integration Guides**
- **[Orchestrator Service](../orchestrator/README.md)** - Workflow automation and coordination
- **[Architecture Overview](../../docs/architecture/ECOSYSTEM_ARCHITECTURE.md)** - System design patterns
- **[Testing Guide](../../docs/guides/TESTING_GUIDE.md)** - Comprehensive testing strategies

### **⚡ Quick References**
- **[Quick Reference Guide](../../docs/guides/QUICK_REFERENCE_GUIDES.md)** - Common operations and commands
- **[Troubleshooting Index](../../docs/guides/TROUBLESHOOTING_INDEX.md)** - Issue resolution guide
- **[Services Index](../README_SERVICES.md)** - Complete service catalog

---

**🎯 The GitHub MCP Service provides seamless GitHub integration through standardized Model Context Protocol interfaces, enabling automated repository operations, code analysis, and development workflow automation across the ecosystem.**
