"""UI Handlers for Frontend Service.

Organized by service for better maintainability and modularity.
"""
from .main_handlers import MainUIHandlers
from .workflow_handlers import WorkflowUIHandlers
from .doc_store_handlers import DocStoreUIHandlers
from .prompt_store_handlers import PromptStoreUIHandlers
from .code_analyzer_handlers import CodeAnalyzerUIHandlers

# Create singleton instances for each handler type
main_handlers = MainUIHandlers()
workflow_handlers = WorkflowUIHandlers()
doc_store_handlers = DocStoreUIHandlers()
prompt_store_handlers = PromptStoreUIHandlers()
code_analyzer_handlers = CodeAnalyzerUIHandlers()

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

# Create singleton instance for backward compatibility
ui_handlers = UIHandlers()
