"""Query Intent Value Object"""

from enum import Enum


class QueryIntent(Enum):
    """Enumeration of recognized query intents."""

    # Information Retrieval
    SEARCH_DOCUMENTS = "search_documents"           # Search for documents
    RETRIEVE_INFORMATION = "retrieve_information"   # Get specific information
    LIST_RESOURCES = "list_resources"              # List available resources

    # Analysis & Processing
    ANALYZE_CONTENT = "analyze_content"            # Analyze document content
    COMPARE_ITEMS = "compare_items"                # Compare multiple items
    SUMMARIZE_CONTENT = "summarize_content"        # Summarize content

    # Workflow Execution
    EXECUTE_WORKFLOW = "execute_workflow"          # Execute a workflow
    CREATE_WORKFLOW = "create_workflow"           # Create new workflow
    MODIFY_WORKFLOW = "modify_workflow"           # Modify existing workflow

    # System Operations
    CHECK_STATUS = "check_status"                  # Check system/component status
    GET_METRICS = "get_metrics"                   # Get system metrics
    CONFIGURE_SYSTEM = "configure_system"        # Configure system settings

    # Conversational
    GREETING = "greeting"                         # Greeting/hello messages
    CLARIFICATION = "clarification"               # Request for clarification
    ACKNOWLEDGMENT = "acknowledgment"             # Acknowledgment responses

    # Unknown/Invalid
    UNKNOWN = "unknown"                           # Could not determine intent

    @property
    def is_informational(self) -> bool:
        """Check if intent is for information retrieval."""
        return self in (
            QueryIntent.SEARCH_DOCUMENTS,
            QueryIntent.RETRIEVE_INFORMATION,
            QueryIntent.LIST_RESOURCES,
            QueryIntent.CHECK_STATUS,
            QueryIntent.GET_METRICS
        )

    @property
    def is_analytical(self) -> bool:
        """Check if intent involves analysis or processing."""
        return self in (
            QueryIntent.ANALYZE_CONTENT,
            QueryIntent.COMPARE_ITEMS,
            QueryIntent.SUMMARIZE_CONTENT
        )

    @property
    def is_operational(self) -> bool:
        """Check if intent involves system operations."""
        return self in (
            QueryIntent.EXECUTE_WORKFLOW,
            QueryIntent.CREATE_WORKFLOW,
            QueryIntent.MODIFY_WORKFLOW,
            QueryIntent.CONFIGURE_SYSTEM
        )

    @property
    def is_conversational(self) -> bool:
        """Check if intent is conversational."""
        return self in (
            QueryIntent.GREETING,
            QueryIntent.CLARIFICATION,
            QueryIntent.ACKNOWLEDGMENT
        )

    @property
    def requires_execution(self) -> bool:
        """Check if intent requires execution capability."""
        return self.is_operational

    @property
    def priority(self) -> int:
        """Get priority level (higher number = more urgent)."""
        priorities = {
            # High priority operations
            QueryIntent.EXECUTE_WORKFLOW: 5,
            QueryIntent.CONFIGURE_SYSTEM: 4,

            # Medium priority informational
            QueryIntent.CHECK_STATUS: 3,
            QueryIntent.GET_METRICS: 3,
            QueryIntent.SEARCH_DOCUMENTS: 3,

            # Low priority analysis
            QueryIntent.ANALYZE_CONTENT: 2,
            QueryIntent.SUMMARIZE_CONTENT: 2,
            QueryIntent.COMPARE_ITEMS: 2,

            # Lowest priority
            QueryIntent.LIST_RESOURCES: 1,
            QueryIntent.RETRIEVE_INFORMATION: 1,
            QueryIntent.CREATE_WORKFLOW: 1,
            QueryIntent.MODIFY_WORKFLOW: 1,

            # Conversational
            QueryIntent.GREETING: 0,
            QueryIntent.CLARIFICATION: 0,
            QueryIntent.ACKNOWLEDGMENT: 0,
            QueryIntent.UNKNOWN: 0
        }
        return priorities[self]

    def __str__(self) -> str:
        return self.value.replace('_', ' ').title()
