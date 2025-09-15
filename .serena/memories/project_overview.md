# LLM Documentation Ecosystem - Project Overview

## Purpose
A modular, service-oriented platform for documentation analysis, prompt management, natural language workflows, and developer tooling. The system provides:

- **Document Analysis**: AI-powered consistency checking across documentation sources
- **Prompt Management**: Version-controlled prompt storage with A/B testing
- **Natural Language Workflows**: Intent recognition and automated task execution
- **Multi-Source Integration**: GitHub, Jira, Confluence, and custom sources
- **Developer Tooling**: CLI interface, web UI, and comprehensive APIs

## Tech Stack
- **Language**: Python 3.11+
- **Web Framework**: FastAPI 0.104.1 + Uvicorn 0.24.0
- **Data Models**: Pydantic 2.5.0
- **HTTP Client**: httpx 0.25.2
- **Caching/Queues**: Redis 5.0.1 + aioredis 2.0.1
- **Testing**: pytest with extensive markers and configuration
- **Documentation**: MkDocs

## Architecture Pattern
Microservices architecture with:
- Service registry via Orchestrator
- Standard FastAPI services with shared middleware
- Common envelope patterns for responses
- Health endpoints and observability
- Event-driven workflows and sagas

## Key Services (with ports)
- **Orchestrator** (5099): Control plane, workflows, service registry
- **Doc Store** (5087): Document storage & search
- **Source Agent** (5000): Multi-source data ingestion
- **Analysis Service** (5020): AI-powered analysis
- **Prompt Store** (5110): Prompt management
- **Interpreter** (5120): Natural language processing
- **Summarizer Hub** (5060): LLM provider abstraction
- **CLI** (N/A): Command-line interface