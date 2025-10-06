"""MCP Interpreter Service.

Translates natural language queries into structured MCP requests.
Performs intent classification, entity extraction, and query planning.

Architecture: Domain-Driven Design (DDD)
Port: 5100 (Internal) / 8152 (External)

Key Features:
- Natural language query parsing
- Intent classification (search, analysis, comparison, recommendation)
- Entity extraction (projects, teams, clients, technologies)
- MCP tier selection (client, project, team, company, ecosystem)
- Structured query plan generation
- Query validation and optimization
"""

__version__ = "1.0.0"
__service_name__ = "mcp-interpreter"

