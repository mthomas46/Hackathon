"""UI Handlers for Frontend Service.

Organized by service for better maintainability and modularity.
"""
from .main_handlers import MainUIHandlers
from .workflow_handlers import WorkflowUIHandlers
from .doc_store_handlers import DocStoreUIHandlers
from .prompt_store_handlers import PromptStoreUIHandlers
from .code_analyzer_handlers import CodeAnalyzerUIHandlers
from .bedrock_proxy_handlers import BedrockProxyUIHandlers
from .discovery_agent_handlers import DiscoveryAgentUIHandlers
from .github_mcp_handlers import GithubMcpUIHandlers
from .interpreter_handlers import InterpreterUIHandlers
from .memory_agent_handlers import MemoryAgentUIHandlers
from .notification_service_handlers import NotificationServiceUIHandlers
from .secure_analyzer_handlers import SecureAnalyzerUIHandlers
from .source_agent_handlers import SourceAgentUIHandlers
from .services_overview_handlers import ServicesOverviewUIHandlers
from .cli_handlers import CLIUIHandlers

# Create singleton instances for each handler type
main_handlers = MainUIHandlers()
workflow_handlers = WorkflowUIHandlers()
doc_store_handlers = DocStoreUIHandlers()
prompt_store_handlers = PromptStoreUIHandlers()
code_analyzer_handlers = CodeAnalyzerUIHandlers()
bedrock_proxy_handlers = BedrockProxyUIHandlers()
discovery_agent_handlers = DiscoveryAgentUIHandlers()
github_mcp_handlers = GithubMcpUIHandlers()
interpreter_handlers = InterpreterUIHandlers()
memory_agent_handlers = MemoryAgentUIHandlers()
notification_service_handlers = NotificationServiceUIHandlers()
secure_analyzer_handlers = SecureAnalyzerUIHandlers()
source_agent_handlers = SourceAgentUIHandlers()
services_overview_handlers = ServicesOverviewUIHandlers()
cli_handlers = CLIUIHandlers()

# Legacy compatibility - create a combined UIHandlers class
class UIHandlers:
    """Combined UI handlers for backward compatibility."""

    # Main dashboard handlers
    def handle_index(self) -> 'HTMLResponse':
        return main_handlers.handle_index()

    def handle_owner_coverage(self) -> 'HTMLResponse':
        return main_handlers.handle_owner_coverage()

    def handle_topics(self) -> 'HTMLResponse':
        return main_handlers.handle_topics()

    def handle_confluence_consolidation(self) -> 'HTMLResponse':
        return main_handlers.handle_confluence_consolidation()

    def handle_jira_staleness(self, min_confidence: float = 0.0, min_duplicate_confidence: float = 0.0, limit: int = 50, summarize: bool = False) -> 'HTMLResponse':
        return main_handlers.handle_jira_staleness(min_confidence, min_duplicate_confidence, limit, summarize)

    def handle_duplicate_clusters(self) -> 'HTMLResponse':
        return main_handlers.handle_duplicate_clusters()

    def handle_search(self, q: str = "kubernetes") -> 'HTMLResponse':
        return main_handlers.handle_search(q)

    def handle_docs_quality(self) -> 'HTMLResponse':
        return main_handlers.handle_docs_quality()

    def handle_findings(self) -> 'HTMLResponse':
        return main_handlers.handle_findings()

    def handle_findings_by_severity(self) -> 'HTMLResponse':
        return main_handlers.handle_findings_by_severity()

    def handle_findings_by_type(self) -> 'HTMLResponse':
        return main_handlers.handle_findings_by_type()

    def handle_report(self) -> 'HTMLResponse':
        return main_handlers.handle_report()

    # Service-specific handlers
    def handle_workflows_status(self) -> 'HTMLResponse':
        return workflow_handlers.handle_workflows_status()

    def handle_doc_store_browser(self) -> 'HTMLResponse':
        return doc_store_handlers.handle_doc_store_browser()

    def handle_prompt_store_browser(self) -> 'HTMLResponse':
        return prompt_store_handlers.handle_prompt_store_browser()

    def handle_code_analyzer_dashboard(self) -> 'HTMLResponse':
        return code_analyzer_handlers.handle_code_analyzer_dashboard()

    def handle_bedrock_proxy_dashboard(self) -> 'HTMLResponse':
        return bedrock_proxy_handlers.handle_bedrock_proxy_dashboard()

    def handle_discovery_agent_dashboard(self) -> 'HTMLResponse':
        return discovery_agent_handlers.handle_discovery_agent_dashboard()

    def handle_github_mcp_dashboard(self) -> 'HTMLResponse':
        return github_mcp_handlers.handle_github_mcp_dashboard()

    def handle_interpreter_dashboard(self) -> 'HTMLResponse':
        return interpreter_handlers.handle_interpreter_dashboard()

    def handle_memory_agent_dashboard(self) -> 'HTMLResponse':
        return memory_agent_handlers.handle_memory_agent_dashboard()

    def handle_notification_service_dashboard(self) -> 'HTMLResponse':
        return notification_service_handlers.handle_notification_service_dashboard()

    def handle_secure_analyzer_dashboard(self) -> 'HTMLResponse':
        return secure_analyzer_handlers.handle_secure_analyzer_dashboard()

    def handle_source_agent_dashboard(self) -> 'HTMLResponse':
        return source_agent_handlers.handle_source_agent_dashboard()

    def handle_services_overview(self) -> 'HTMLResponse':
        return services_overview_handlers.handle_services_overview()

    def handle_cli_terminal(self) -> 'HTMLResponse':
        return cli_handlers.handle_cli_terminal()

# Create singleton instance for backward compatibility
ui_handlers = UIHandlers()
