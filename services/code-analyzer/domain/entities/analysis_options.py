"""Analysis options entity."""

from dataclasses import dataclass


@dataclass
class AnalysisOptions:
    """Options for code analysis."""
    
    include_complexity: bool = True
    include_security: bool = True
    include_style: bool = True
    include_structure: bool = True

