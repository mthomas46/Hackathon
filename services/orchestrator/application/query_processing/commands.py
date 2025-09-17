"""Query Processing Application Commands"""

from dataclasses import dataclass


@dataclass
class ProcessNaturalLanguageQueryCommand:
    """Command to process a natural language query."""
    query_text: str
    context: dict = None


@dataclass
class ExecuteStructuredQueryCommand:
    """Command to execute a structured query."""
    query_type: str
    parameters: dict
