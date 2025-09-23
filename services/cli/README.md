# CLI Service

Navigation: [Home](../../README.md) · [Architecture](../../docs/architecture/) · [Testing](../../docs/guides/TESTING_GUIDE.md) · [Services](../README_SERVICES.md)

**🏗️ Recently Refactored**: Interactive command-line interface with mixin-based architecture, standardized manager interfaces, and 100% test coverage (153 passing tests).

- **Usage**: `python services/cli/main.py [command]`
- **Tests**: [tests/unit/cli](../../tests/unit/cli) - 153 passing tests
- **Architecture**: Mixin-based BaseManager with MenuMixin, OperationMixin, TableMixin, ValidationMixin

## 📋 Overview

The **CLI Service** is the **enterprise-grade command-line interface and orchestration platform** for the LLM Documentation Ecosystem. It provides a sophisticated, interactive command-line interface with comprehensive service management, workflow orchestration, and system administration capabilities.

### 🎯 **Service Details**
- **🔌 Entry Point**: `python services/cli/main.py`
- **🏗️ Architecture**: Mixin-based BaseManager with standardized interfaces
- **🧪 Testing**: 153+ passing tests with 100% coverage
- **📊 Commands**: 50+ specialized commands across 18+ service domains
- **🔄 Integration**: Complete ecosystem integration with all services
- **⚡ Performance**: Async operations with intelligent caching and progress tracking

### 🚀 **Key Capabilities**

#### **🖥️ Interactive Terminal User Interface (TUI)**
- **Comprehensive Menu System**: Hierarchical navigation with contextual help
- **Real-Time Progress Tracking**: Live progress bars and status updates
- **Intelligent Command Completion**: Context-aware suggestions and auto-completion
- **Error Recovery**: Graceful error handling with actionable suggestions
- **Session Persistence**: State management across command sessions

#### **🎛️ Multi-Service Orchestration**
- **Service Discovery**: Automatic detection and health monitoring of all ecosystem services
- **Workflow Management**: Complex workflow orchestration with dependency resolution
- **Resource Management**: Intelligent resource allocation and load balancing
- **Health Monitoring**: Real-time service health checks and alerting
- **Performance Optimization**: Intelligent caching and execution planning

#### **⚙️ Enterprise Management Features**
- **Configuration Management**: Centralized configuration with validation and hot-reloading
- **Security Integration**: Enterprise-grade authentication and authorization
- **Audit Logging**: Complete command history and execution tracking
- **Bulk Operations**: High-performance batch processing across services
- **Monitoring & Analytics**: Comprehensive metrics and performance insights

#### **🔧 Developer Experience**
- **Consistent Interfaces**: Standardized command patterns and output formats
- **Rich Formatting**: Beautiful terminal output with tables, progress bars, and colors
- **Error Handling**: Clear error messages with actionable resolution steps
- **Documentation Integration**: Built-in help system with contextual information
- **Extensibility**: Plugin architecture for custom commands and integrations

## 🏗️ Architecture

### **🎯 Intelligent CLI Processing Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Command       │    │   Service       │    │   Ecosystem     │
│   Input &       │───▶│   Manager       │───▶│   Service      │
│   Validation    │    │   Layer         │    │   Integration   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Interactive   │    │   Output        │    │   Cache &       │
│   Menu System   │    │   Formatting    │    │   Performance   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Ecosystem Services                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │ Orchestrator│ │ Analysis    │ │ Prompt      │ ...      │
│  │ Service     │ │ Service     │ │ Store       │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

### **🏛️ BaseManager Pattern**

All CLI managers inherit from `BaseManager` with standardized interfaces:

```python
class BaseManager(MenuMixin, OperationMixin, TableMixin, ValidationMixin, ABC):
    """Abstract base class for all CLI service managers."""

    def __init__(self, console: Console, clients: Dict[str, Any],
                 cache: Optional[Dict[str, Any]] = None):
        """
        Standardized initialization with dependency injection.

        Args:
            console: Rich console for formatted output
            clients: Service client adapters for ecosystem integration
            cache: Optional caching layer for performance optimization
        """
        self.console = console
        self.clients = clients
        self.cache = cache or {}

    @abstractmethod
    async def get_main_menu(self) -> List[Tuple[str, str]]:
        """Return menu items for this manager's main interface."""

    @abstractmethod
    async def handle_choice(self, choice: str) -> bool:
        """Handle user menu selection and return True to continue, False to exit."""

    async def display_welcome(self) -> None:
        """Display manager-specific welcome message and overview."""

    async def display_help(self) -> None:
        """Display context-sensitive help information."""
```

### **🔧 Mixin Composition Architecture**

#### **MenuMixin** - Interactive Menu System
```python
class MenuMixin:
    """Provides standardized menu loop implementation."""

    async def run_menu_loop(self, menu_items: List[Tuple[str, str]]) -> bool:
        """Main menu interaction loop with navigation and error handling."""

    async def get_user_choice(self, prompt: str) -> str:
        """Get validated user input with completion suggestions."""

    async def display_menu(self, items: List[Tuple[str, str]]) -> None:
        """Render formatted menu with Rich console styling."""
```

#### **OperationMixin** - Async Operations & Progress
```python
class OperationMixin:
    """Handles async operations with progress tracking and caching."""

    async def run_with_progress(self, operation_name: str,
                               operation_func: Callable) -> Any:
        """Execute async operation with progress bar and error handling."""

    async def confirm_action(self, message: str, default: bool = False) -> bool:
        """Get user confirmation with clear yes/no prompts."""

    def get_cached_result(self, key: str) -> Optional[Any]:
        """Retrieve cached operation result with TTL checking."""
```

#### **TableMixin** - Rich Data Formatting
```python
class TableMixin:
    """Provides consistent table rendering and data formatting."""

    def create_table(self, title: str, columns: List[str]) -> Table:
        """Create Rich table with consistent styling."""

    def format_service_status(self, status: Dict[str, Any]) -> str:
        """Format service health status with color coding."""

    def format_metrics_data(self, metrics: Dict[str, Any]) -> Table:
        """Format performance metrics in readable table format."""
```

#### **ValidationMixin** - Input Validation & Error Handling
```python
class ValidationMixin:
    """Handles input validation and error recovery."""

    def validate_required(self, value: Any, field_name: str) -> Any:
        """Validate required field with meaningful error messages."""

    def validate_choice(self, choice: str, valid_options: List[str]) -> str:
        """Validate user selection against allowed options."""

    async def handle_validation_error(self, error: ValidationError) -> None:
        """Display user-friendly validation error with suggestions."""
```

### **🎯 Manager Hierarchy & Specialization**

```
BaseManager (abstract)
├── 📋 OrchestratorManager        - Workflow orchestration, service registry
├── 🔍 AnalysisManager           - Quality analysis, findings management
├── 📥 SourceAgentManager        - Document fetching, data normalization
├── 💬 PromptManager             - Prompt CRUD, workflow management
├── 🏗️ InfrastructureManager     - Redis, DLQ, sagas, tracing
├── 📦 BulkOperationsManager     - Mass operations across services
├── 🧠 InterpreterManager        - Query interpretation, workflow execution
├── 🔎 DiscoveryAgentManager     - OpenAPI parsing, service registration
├── 🧠 MemoryAgentManager        - Context storage, event summaries
├── 🔒 SecureAnalyzerManager     - Content security, policy enforcement
├── 📝 SummarizerHubManager      - AI provider management, model performance
├── 💻 CodeAnalyzerManager       - Code analysis, security scanning
├── 🚀 DeploymentManager         - Service scaling, health monitoring
├── 📊 LogCollectorManager       - Log aggregation, storage
├── 🔔 NotificationServiceManager - Owner resolution, notifications
├── 🐳 DockerManager             - Docker configuration management
└── ⚙️ ConfigManager             - System configuration management
```

### **🏢 Enterprise Design Patterns**

#### **1. Command Pattern with Mixins**
- **Command Encapsulation**: Each manager encapsulates related operations
- **Mixin Composition**: Reusable functionality through mixin inheritance
- **Interface Segregation**: Clean separation between menu, operations, formatting, and validation
- **Dependency Injection**: Loose coupling through constructor injection

#### **2. Repository Pattern for Data Access**
- **Service Client Adapters**: Abstract interfaces for all ecosystem services
- **Data Transformation**: Consistent data mapping between services and CLI
- **Caching Layer**: Intelligent caching with TTL and invalidation strategies
- **Error Handling**: Comprehensive error handling with fallback mechanisms

#### **3. Observer Pattern for Real-time Updates**
- **Progress Callbacks**: Real-time progress updates during long operations
- **Status Monitoring**: Live service health and status updates
- **Event Streaming**: Integration with ecosystem event system
- **Notification System**: User notifications for operation completion

#### **4. Strategy Pattern for Output Formatting**
- **Multiple Formatters**: Table, JSON, YAML, and custom format options
- **Adaptive Rendering**: Automatic format selection based on data type and size
- **Rich Styling**: Consistent visual styling with Rich console library
- **Accessibility**: Support for different terminal capabilities and preferences

### 📚 **Command Reference**

#### **Base URL & Entry Point**
```bash
python services/cli/main.py [command] [options]
```

#### **Authentication**
All commands support enterprise-grade authentication via environment variables:
```bash
export CLI_USER_ID="user@example.com"
export CLI_API_KEY="your-api-key"
export CLI_JWT_TOKEN="your-jwt-token"
```

#### **🎯 Core Commands (50+ Available)**

##### **System Management**
| Command | Description | Example |
|---------|-------------|---------|
| `interactive` | Start interactive TUI workflow | `python main.py interactive` |
| `health` | Check service health across ecosystem | `python main.py health --detailed` |
| `status` | Get detailed system status | `python main.py status --format json` |
| `config` | Manage CLI configuration | `python main.py config list` |
| `version` | Show CLI and service versions | `python main.py version --ecosystem` |

##### **📋 Orchestrator Management**
| Command | Description | Example |
|---------|-------------|---------|
| `orchestrator workflows` | List and manage workflows | `python main.py orchestrator workflows --status active` |
| `orchestrator execute` | Execute workflow by ID | `python main.py orchestrator execute wf_123 --params file.json` |
| `orchestrator registry` | Manage service registry | `python main.py orchestrator registry --refresh` |
| `orchestrator infrastructure` | Infrastructure operations | `python main.py orchestrator infrastructure --dlq-stats` |

##### **🔍 Analysis Service Management**
| Command | Description | Example |
|---------|-------------|---------|
| `analysis documents` | Analyze documents | `python main.py analysis documents --url https://example.com/doc` |
| `analysis quality` | Check document quality | `python main.py analysis quality --document-id doc_123` |
| `analysis reports` | Generate analysis reports | `python main.py analysis reports --format pdf` |
| `analysis findings` | Manage analysis findings | `python main.py analysis findings --severity high` |

##### **💬 Prompt Store Management**
| Command | Description | Example |
|---------|-------------|---------|
| `prompts list` | List available prompts | `python main.py prompts list --category analysis` |
| `prompts create` | Create new prompt | `python main.py prompts create --file prompt.json` |
| `prompts get` | Get prompt by ID | `python main.py prompts get prompt_123 --include-analytics` |
| `prompts test` | Test prompt execution | `python main.py prompts test prompt_123 --input "test content"` |

##### **📥 Source Agent Management**
| Command | Description | Example |
|---------|-------------|---------|
| `source fetch` | Fetch content from sources | `python main.py source fetch --url https://github.com/user/repo` |
| `source normalize` | Normalize document formats | `python main.py source normalize --document-id doc_123` |
| `source validate` | Validate source configurations | `python main.py source validate --config config.yaml` |

##### **🔎 Discovery Agent Management**
| Command | Description | Example |
|---------|-------------|---------|
| `discovery register` | Register API specifications | `python main.py discovery register --openapi spec.yaml` |
| `discovery analyze` | Analyze service capabilities | `python main.py discovery analyze --service analysis-service` |
| `discovery drift` | Detect API drift | `python main.py discovery drift --baseline spec_v1.yaml` |

##### **🧠 Memory Agent Management**
| Command | Description | Example |
|---------|-------------|---------|
| `memory store` | Store context information | `python main.py memory store --content "important context"` |
| `memory retrieve` | Retrieve stored context | `python main.py memory retrieve --query "specific context"` |
| `memory list` | List stored memories | `python main.py memory list --limit 20` |

##### **🔒 Secure Analyzer Management**
| Command | Description | Example |
|---------|-------------|---------|
| `security scan` | Scan content for security issues | `python main.py security scan --content "sensitive data"` |
| `security policies` | Manage security policies | `python main.py security policies --list` |
| `security compliance` | Check compliance status | `python main.py security compliance --report` |

##### **📝 Summarizer Hub Management**
| Command | Description | Example |
|---------|-------------|---------|
| `summarize content` | Generate content summaries | `python main.py summarize content --document-id doc_123` |
| `summarize models` | Manage AI models | `python main.py summarize models --list` |
| `summarize performance` | Model performance analytics | `python main.py summarize performance --model gpt-4` |

##### **💻 Code Analyzer Management**
| Command | Description | Example |
|---------|-------------|---------|
| `code analyze` | Analyze code repositories | `python main.py code analyze --repo https://github.com/user/repo` |
| `code security` | Security scanning | `python main.py code security --scan-type full` |
| `code metrics` | Code quality metrics | `python main.py code metrics --format json` |

##### **🚀 Deployment Management**
| Command | Description | Example |
|---------|-------------|---------|
| `deploy status` | Check deployment status | `python main.py deploy status --service analysis-service` |
| `deploy scale` | Scale service instances | `python main.py deploy scale --service web --replicas 3` |
| `deploy health` | Health monitoring | `python main.py deploy health --detailed` |

##### **📊 Log Collector Management**
| Command | Description | Example |
|---------|-------------|---------|
| `logs collect` | Collect system logs | `python main.py logs collect --service analysis-service` |
| `logs search` | Search log entries | `python main.py logs search --query "error" --timeframe 1h` |
| `logs analyze` | Analyze log patterns | `python main.py logs analyze --pattern-matching` |

##### **🔔 Notification Management**
| Command | Description | Example |
|---------|-------------|---------|
| `notifications send` | Send notifications | `python main.py notifications send --channel email --to user@example.com` |
| `notifications owners` | Manage owner mappings | `python main.py notifications owners --list` |
| `notifications stats` | Notification statistics | `python main.py notifications stats --timeframe 24h` |

##### **🐳 Docker Management**
| Command | Description | Example |
|---------|-------------|---------|
| `docker status` | Docker service status | `python main.py docker status --all` |
| `docker logs` | Docker service logs | `python main.py docker logs --service analysis-service` |
| `docker restart` | Restart services | `python main.py docker restart --service analysis-service` |

### 📋 **Command Examples & Usage**

#### **Interactive Mode**
```bash
# Start interactive CLI
python services/cli/main.py interactive

# Start with specific service manager
python services/cli/main.py interactive --manager orchestrator

# Start with debug logging
DEBUG=1 python services/cli/main.py interactive
```

#### **Service Health Monitoring**
```bash
# Basic health check
python services/cli/main.py health

# Detailed health with metrics
python services/cli/main.py health --detailed --format json

# Health check with specific services
python services/cli/main.py health --services analysis-service,prompt-store

# Continuous health monitoring
python services/cli/main.py health --watch --interval 30
```

#### **Workflow Management**
```bash
# List all workflows
python services/cli/main.py orchestrator workflows

# Execute workflow with parameters
python services/cli/main.py orchestrator execute workflow_123 \
  --parameters '{"document_url": "https://example.com/doc.pdf"}'

# Monitor workflow execution
python services/cli/main.py orchestrator execute workflow_123 --watch

# Get workflow analytics
python services/cli/main.py orchestrator workflows --analytics
```

#### **Document Analysis**
```bash
# Analyze document from URL
python services/cli/main.py analysis documents \
  --url "https://example.com/api-docs" \
  --analysis-type comprehensive

# Analyze local document
python services/cli/main.py analysis documents \
  --file "/path/to/document.pdf" \
  --include-security

# Generate analysis report
python services/cli/main.py analysis reports \
  --document-id doc_123 \
  --format pdf \
  --output report.pdf
```

#### **Prompt Management**
```bash
# List prompts by category
python services/cli/main.py prompts list --category analysis

# Create prompt from file
python services/cli/main.py prompts create --file prompt.json

# Test prompt execution
python services/cli/main.py prompts test prompt_123 \
  --input "Analyze this document" \
  --model gpt-4

# Get prompt analytics
python services/cli/main.py prompts get prompt_123 --include-analytics
```

#### **Advanced Features**
```bash
# Bulk operations across services
python services/cli/main.py bulk operations --create-documents --count 100

# Cross-service workflow orchestration
python services/cli/main.py orchestrator execute complex_workflow \
  --services analysis-service,prompt-store,doc-store

# Performance monitoring dashboard
python services/cli/main.py monitoring dashboard --real-time --refresh 5

# Configuration management
python services/cli/main.py config validate --all
python services/cli/main.py config export --format json --output config.json
```

### ⚙️ **Configuration Management**

#### **Environment Variables**
| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `CLI_USER_ID` | Default user ID | - | user@example.com |
| `CLI_API_KEY` | API authentication key | - | your-api-key |
| `CLI_JWT_TOKEN` | JWT authentication token | - | eyJ0eXAi... |
| `CLI_FORMAT` | Default output format | table | json, yaml |
| `CLI_CACHE_TTL` | Cache time-to-live | 300 | 1800 |
| `CLI_TIMEOUT` | Request timeout seconds | 30 | 60 |
| `CLI_DEBUG` | Enable debug logging | 0 | 1 |
| `CLI_COLOR` | Enable colored output | 1 | 0 |
| `CLI_PAGINATION` | Default page size | 20 | 50 |

#### **Configuration File**
```yaml
# config/cli.yaml
cli:
  default_format: table
  pagination_size: 20
  timeout: 30
  cache_ttl: 300
  debug: false
  color_enabled: true

services:
  default_timeout: 30
  retry_attempts: 3
  health_check_interval: 60

output:
  table_style: rounded
  color_scheme: default
  progress_bars: true

logging:
  level: INFO
  format: rich
  file: logs/cli.log
```

## Related
- Prompt Store: [../prompt-store/README.md](../prompt-store/README.md)
- Interpreter: [../interpreter/README.md](../interpreter/README.md)
- Services index: [../README_SERVICES.md](../README_SERVICES.md)

## 🧪 Testing & Quality Assurance

### **Test Coverage**
- **153 passing unit tests** (100% improvement from 72 initial tests)
- **Complete manager coverage** - All 18+ managers tested with integration patterns
- **Mixin functionality validation** - Menu loops, operations, tables, validation
- **Error handling verification** - Standardized error responses and recovery

### **Test Architecture**
```
tests/unit/cli/
├── conftest.py              # Centralized fixtures (mock_console, mock_clients, mock_cache, cli_service)
├── test_base.py             # Shared test utilities and mixins (BaseManagerTestMixin, APITestMixin)
├── test_base_classes.py     # Base class testing (BaseManager, BaseHandler, BaseFormatter)
├── test_cli_core.py         # CLI service integration tests
├── test_cli_dry_audit.py    # DRY principle validation
├── test_cli_integration.py  # Cross-service integration
├── test_cli_validation.py   # Input validation and edge cases
├── test_manager_structure.py # Manager interface compliance
└── test_utility_modules.py  # Utility function testing
```

### **Testing Strategies**
- **Async client mocks** with `AsyncMock` for service client interfaces
- **Manager integration tests** verifying menu loops and choice handling
- **Mixin functionality tests** ensuring consistent behavior across managers
- **Error handling validation** with standardized error response checking
- **Fixture composition** enabling comprehensive CLI service testing

### **Test Results**
- ✅ **BaseManager inheritance**: All managers properly implement abstract methods
- ✅ **Mixin composition**: MenuMixin, OperationMixin, TableMixin, ValidationMixin working
- ✅ **Async operations**: Proper handling of async/await patterns throughout
- ✅ **Error resilience**: Graceful error handling with user-friendly messages
- ✅ **Service integration**: CLI service initializes without errors
