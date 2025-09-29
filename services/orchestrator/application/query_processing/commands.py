"""Query Processing Application Commands"""

from dataclasses import dataclass


@dataclass
class ProcessNaturalLanguageQueryCommand:
    """Command to process a natural language query."""
    query_text: str
    context: dict = None
    max_results: int = 50
    include_explanation: bool = True


@dataclass
class ExecuteStructuredQueryCommand:
    """Command to execute a structured query."""
    query_type: str
    parameters: dict
