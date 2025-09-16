# CLI Service

Navigation: [Home](../../README.md) · [Architecture](../../docs/architecture/) · [Testing](../../docs/guides/TESTING_GUIDE.md) · [Services](../README_SERVICES.md)

**🏗️ Recently Refactored**: Interactive command-line interface with mixin-based architecture, standardized manager interfaces, and 100% test coverage (153 passing tests).

- **Usage**: `python services/cli/main.py [command]`
- **Tests**: [tests/unit/cli](../../tests/unit/cli) - 153 passing tests
- **Architecture**: Mixin-based BaseManager with MenuMixin, OperationMixin, TableMixin, ValidationMixin

## Overview and role in the ecosystem
- Human-friendly entry point to orchestrate workflows, manage prompts, and check service health.
- Wraps common flows behind typed commands and an interactive TUI.
- **18+ specialized managers** for different service operations (orchestrator, analysis, source agent, etc.)
- **Mixin-based architecture** enabling consistent interfaces and reusable functionality

## 🏗️ Architecture

### **BaseManager Pattern**
All CLI managers inherit from `BaseManager` with standardized interfaces:

```python
class BaseManager(MenuMixin, OperationMixin, TableMixin, ValidationMixin, ABC):
    def __init__(self, console: Console, clients, cache: Optional[Dict[str, Any]] = None):
        # Standardized initialization with cache support

    @abstractmethod
    async def get_main_menu(self) -> List[tuple[str, str]]:
        """Return menu items for this manager"""

    @abstractmethod
    async def handle_choice(self, choice: str) -> bool:
        """Handle menu choice selection"""
```

### **Mixin Composition**
- **MenuMixin**: Standard menu loop implementation with back navigation
- **OperationMixin**: Async progress bars, confirmation dialogs, caching
- **TableMixin**: Consistent table rendering with rich formatting
- **ValidationMixin**: Input validation with error handling

### **Manager Hierarchy**
```
BaseManager (abstract)
├── OrchestratorManager    - Workflow orchestration, service registry
├── AnalysisManager        - Quality analysis, findings management
├── SourceAgentManager     - Document fetching, data normalization
├── PromptManager          - Prompt CRUD, workflow management
├── InfrastructureManager  - Redis, DLQ, sagas, tracing
├── BulkOperationsManager  - Mass operations across services
├── InterpreterManager     - Query interpretation, workflow execution
├── DiscoveryAgentManager  - OpenAPI parsing, service registration
├── MemoryAgentManager     - Context storage, event summaries
├── SecureAnalyzerManager  - Content security, policy enforcement
├── SummarizerHubManager   - AI provider management, model performance
├── CodeAnalyzerManager    - Code analysis, security scanning
├── DeploymentManager      - Service scaling, health monitoring
├── LogCollectorManager    - Log aggregation, storage
├── NotificationServiceManager - Owner resolution, notifications
└── DockerManager          - Docker configuration management
```

## Commands
| Command | Description |
|---------|-------------|
| interactive | Start interactive TUI workflow |
| get-prompt <category> <name> [--content ...] | Retrieve and render a prompt |
| health | Check service health across the stack |
| list-prompts [--category ...] | List available prompts |
| test-integration | Run cross-service checks from CLI |

## Examples
```bash
python services/cli/main.py interactive
python services/cli/main.py get-prompt summarization default --content "hello"
python services/cli/main.py health
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
