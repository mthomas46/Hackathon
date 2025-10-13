# Architecture

# Architecture

## Overview

The overall architecture of ecosystem-mcp appears to be a microservices-based design with clear separation of concerns. It consists of several key components that interact with each other through REST APIs, message queues, and event-driven patterns. The ecosystem is designed for scalability, with horizontal scaling capabilities and load balancing strategies in place.

Here's a high-level overview of the architecture:

1. **Service Architecture**: Microservices-based design with clear separation of concerns.
2. **Data Flow**: Document ingestion → Processing → Storage → Retrieval pipelines.
3. **Integration Points**: REST APIs, message queues, and event-driven patterns.
4. **Observability**: Comprehensive logging, monitoring, and health checks.
5. **Scalability**: Horizontal scaling with load balancing and caching strategies.

The ecosystem is designed to be highly scalable, flexible, and maintainable, with a focus on observability and testing. The architecture allows for easy integration of new services and features, making it an ideal choice for complex and dynamic systems.

In terms of specific components, the ecosystem-mcp appears to include:

* A document ingestion pipeline that handles incoming data.
* A processing layer that performs various operations on the ingested data.
* A storage layer that stores the processed data.
* A retrieval layer that allows users to access the stored data.
* A set of APIs and message queues that enable communication between services.
* A logging, monitoring, and health checking system that provides visibility into the ecosystem's performance.

Overall, the architecture of ecosystem-mcp is designed to be highly scalable, flexible, and maintainable, with a focus on observability and testing.

Based on the provided context, the main service components and their responsibilities are:

1. **Intelligence Service**: Responsible for generating prompts from code and documents.
	* Located in `services/prompt_store/domain/intelligence/service.py`
2. **Service Discovery Service**: Handles automatic discovery and registration of services in the ecosystem.
	* Located in `scripts/audit-framework/infrastructure/file_system/service_discovery_service.py`
3. **File System Service**: Provides a clean interface for reading service files and directories.
	* Located in `scripts/audit-framework/infrastructure/file_system/file_system_service.py`
4. **Notification Service UI Handlers**: Handles notification service visualization, including owner resolution, notification delivery monitoring, and dead letter queue management.
	* Located in `services/frontend/modules/ui_handlers/notification_service_handlers.py`
5. **Bulk Operations Service**: Handles business logic for bulk operations on prompts.
	* Located in `services/prompt_store/domain/bulk/service.py`
6. **Analysis Operations Service**: Encapsulates complex analysis operations that were previously scattered across the main application layer.
	* Located in `services/analysis-service/domain/services/analysis_operations_service.py`
7. **Analytics Service**: Provides advanced analytics for prompt performance, optimization, and insights.
	* Located in `services/prompt_store/domain/analytics/service.py`
8. **Notifications Service**: Handles notification processing and webhook management.
	* Located in `services/doc_store/domain/notifications/service.py`
9. **Service Config**: Provides standardized configuration classes for different types of services in the LLM Documentation Ecosystem.
	* Located in `services/shared/infrastructure/config/service_config.py`
10. **Bulk Operations Service (Doc Store)**: Handles bulk processing and batch operations business rules for document store.
	* Located in `services/doc_store/domain/bulk/service.py`
11. **Relationships Service**: Contains business logic for prompt relationships and semantic connections.
	* Located in `services/prompt_store/domain/relationships/service.py`
12. **Base Service**: Provides standardized base service classes that eliminate boilerplate code for business logic patterns across all services.
	* Located in `services/shared/domain/services/base_service.py`
13. **Service Adapter**: Provides a standardized interface for all service interactions through the CLI.
	* Located in `services/cli/modules/adapters/base_service_adapter.py` and `services/cli/infrastructure/adapters/base_service_adapter.py`
14. **Prompt Service**: Handles business logic for prompts following domain-driven design.
	* Located in `services/prompt_store/domain/prompts/service.py`
15. **Dynamic Prompt Orchestration Service**: Orchestrates complex prompt workflows using conditional chains and pipelines.
	* Located in `services/prompt_store/domain/orchestration/service.py`

These service components work together to provide a comprehensive ecosystem for managing prompts, services, and analytics.

## Technical Details

Based on the provided code snippets, here's an overview of how the FastAPI application layer works:

**Endpoints:**

The FastAPI application has various endpoints for different services, such as:

1. **Analysis Service**: `/analysis` endpoint for semantic similarity analysis, sentiment analysis, tone analysis, content quality analysis, trend analysis, risk assessment, maintenance forecast, and quality degradation detection.
2. **Summarizer Hub**: Document API routes for document operations (e.g., `/documents`, `/summaries`).
3. **Expert Finder Service**: Standard and expert finding routes (e.g., `/experts`, `/find-experts`).
4. **Discovery Agent**: OpenAPI specification parsing and endpoint extraction.
5. **Datastore Services** (e.g., Doc Store, Prompt Store): Various endpoints for data operations.

**Middleware:**

The FastAPI application uses several middleware components to enhance its functionality:

1. **Request ID Middleware**: Adds a unique request ID to all requests and responses for distributed tracing purposes.
2. **Datastore Operation Logger Middleware**: Automatically logs all datastore operations (e.g., CRUD operations) to the log-collector service.

**Other Components:**

The FastAPI application also includes various other components, such as:

1. **Models**: Pydantic models define the structure of HTTP requests and responses for each endpoint.
2. **Services**: Business logic services implement the core functionality for each endpoint (e.g., analysis, summarization).
3. **Utilities**: Shared utility functions and fixtures used across multiple test files.

This is a high-level overview of how the FastAPI application layer works based on the provided code snippets. If you have specific questions or need further clarification, feel free to ask!

Based on the provided context, I don't have enough information to describe the database layer of the Ecosystem-MCP service, including its PostgreSQL schema, models, and repositories. The context only mentions a few files related to databases, but they are not comprehensive enough to provide a detailed description.

However, I can mention that there is a file `services/mcp-performance-store/infrastructure/db/__init__.py` which suggests the existence of database utilities and schemas in the service. Additionally, there is a file `services/ecosystem-mcp/src/storage/repositories/__init__.py` which implies the use of repository pattern for database access.

If you provide more context or information about the specific components of the Ecosystem-MCP service's database layer, I'll be happy to help further.

I don't have enough information to provide a detailed explanation of how ChromaDB works or the embedding process. The provided context only mentions that there are database models in `services/ecosystem-mcp/src/storage/db_models.py` and an Embedding table model (`EmbeddingModel`) is defined, but it does not contain any details about ChromaDB or the embedding process.

Based on the provided code snippets and documentation, here's an explanation of the Redis caching layer:

**What's cached:**

The Redis caching layer is used to store various types of data, including:

1. **LLM responses**: The LLM Gateway Service uses a cache manager to store LLM response entries with TTL-based expiration.
2. **Simulation progress updates**: The Project Simulation service uses Redis pub/sub for real-time communication between simulation services, storing simulation progress updates in Redis.
3. **Document generation notifications**: The Project Simulation service also stores document generation notifications in Redis.
4. **Query cache**: The MCP Interpreter domain layer uses a query cache repository to store parsed queries with TTL-based expiration.

**TTLs (Time-To-Live):**

The caching layer uses TTLs to control the expiration of cached data. For example:

1. LLM response entries have a TTL-based expiration, which means they will be automatically removed from the cache after a certain time period.
2. Simulation progress updates and document generation notifications are stored in Redis with a TTL-based expiration.

**Cache strategies:**

The caching layer uses various cache strategies to optimize performance and reduce costs:

1. **TTL-based expiration**: Data is automatically removed from the cache after a specified time period (TTL).
2. **Pattern-based cache clearing**: The LLM Gateway Service's cache manager can clear cached responses based on specific patterns.
3. **Cache analytics**: The Intelligent Cache system provides performance metrics and workflow-aware optimization.

**Intelligent caching:**

The Intelligent Caching Framework is an enterprise-grade caching solution that provides:

1. **Multiple cache strategies**: Supports various caching use cases, such as TTL-based expiration and pattern-based cache clearing.
2. **Performance monitoring**: Provides cache performance metrics and analytics.
3. **Workflow-aware optimization**: Optimizes cache behavior based on the workflow or application context.

In summary, the Redis caching layer is a critical component of several services, providing efficient storage and retrieval of various types of data with TTL-based expiration and intelligent cache strategies to optimize performance and reduce costs.

Based on the provided code snippets and documentation, it appears that Ollama is a Large Language Model (LLM) inference service. However, there is no explicit information about how Ollama integrates with other services or what specific models are used.

The provided code snippets seem to be related to various components of an LLM ecosystem, including:

1. **Orchestrator**: responsible for managing the workflow and routing requests to different providers.
2. **LLM Gateway**: acts as a bridge between clients and LLM providers, handling tasks such as authentication, request processing, and result aggregation.
3. **Source Agent**: likely responsible for fetching data from external sources or generating input for the LLM.
4. **Doc Store**: possibly a repository for storing and managing documents, summaries, or other output generated by the LLM.

The code snippets suggest that Ollama uses a modular architecture with separate components for different tasks. However, without more information about the specific models used in each component, it's difficult to determine which models are employed for LLM inference.

To answer your question accurately, I would need more context or information about how Ollama integrates with other services and what specific models are used for LLM inference. If you have any additional details or clarification regarding this topic, please let me know!

Based on the provided context, I will outline the document ingestion pipeline steps from file to embedded document:

1. **File Discovery**: The document scanner (`DocumentScanner` in `services/ecosystem-mcp/src/ingestion/scanner.py`) scans the repository for documents to ingest.
2. **Filtering**: The scanner filters files based on extension, path patterns, and `.gitignore` rules (methods like `_scan_by_extensions()`, `_should_ignore_path()`).
3. **Crawling**: Wikipedia pages are crawled using `WikipediaIngestor` in `ingestion/wikipedia_ingestor.py`.
4. **Document Creation**: A new document is created with metadata, content, and versioning information (models like `DocumentCreate` in `services/ecosystem-mcp/src/models/document.py`).
5. **Document Ingestion**: The document is ingested into the ecosystem using the intelligent ingestion engine (`IntelligentIngestion` in `services/source-agent/domain/services/intelligent_ingestion.py`), which performs predictive data ingestion, conflict resolution, and quality assessment.
6. **Document Storage**: The ingested document is stored in a repository (e.g., `DocumentRepository` in `services/source-agent/infrastructure/repositories/document_repository.py`) for persistence and retrieval.

These steps form the document ingestion pipeline from file to embedded document within the ecosystem.

Based on the provided code snippets, it appears that the RAG system is a part of the MCP (Meta Cognitive Process) ecosystem. The MCP ecosystem seems to be designed for semantic search and analysis across documents.

Here's a high-level overview of how the RAG system might work end-to-end based on the provided context:

1. **User Input**: A user submits a query or question to the RAG system.
2. **Search Request**: The search request is processed by the `SearchRequest` class, which sanitizes and validates the query.
3. **Semantic Search**: The sanitized query is then passed to the semantic search engine, which searches across documents in the MCP ecosystem.
4. **Pattern Performance Store**: The results of the search are stored in the Pattern Performance Store (PPS), which aggregates performance metrics for specific LLM patterns across multiple executions.
5. **Orchestration Execution**: When a user submits a query, an orchestration execution is created to track the complete lifecycle of executing that query through the MCP ecosystem.
6. **LLM Embedding**: The search results are then embedded using LLM (Large Language Model) techniques, such as auto-tagging or chain-of-thought reasoning.
7. **Analysis Result**: The analysis result is generated based on the embedded search results and stored in the AnalysisResult domain entity.
8. **Notification Service**: The notification service is responsible for sending notifications to users about the analysis results.

The RAG system seems to be designed to provide a comprehensive solution for semantic search, analysis, and notification across documents in the MCP ecosystem.

Here's a simplified example of how this might work end-to-end:
```python
# User submits query
query = "What is the best way to improve my coding skills?"

# Search request processing
search_request = SearchRequest(query)
sanitized_query = search_request.sanitize_query()

# Semantic search
results = semantic_search(sanitized_query)

# Pattern performance store
pattern_performance = PatternPerformance(results)

# Orchestration execution
orchestration_execution = OrchestrationExecution(pattern_performance)

# LLM embedding
embedded_results = auto_tag_task(results, ollama_url)

# Analysis result generation
analysis_result = AnalysisResult(embedded_results)
```
Note that this is a highly simplified example and the actual implementation would involve more complex logic and interactions between different components of the MCP ecosystem.

## Practical Information

Here is the complete flow for a document ingestion request:

1. **Document Ingestion Request**: A client sends a document ingestion request to the Ecosystem MCP Service.
2. **Ingestion Pipeline**: The request is received by the ingestion pipeline, which is responsible for discovering, parsing, normalizing, and embedding documents.
3. **Document Event Creation**: The ingestion pipeline creates a `DocumentEvent` entity to track the document's ingestion process.
4. **Kafka Ingestion Service**: The `DocumentEvent` entity is published to Kafka, where it is consumed by the Kafka Ingestion Service.
5. **Ingestion Job Creation**: The Kafka Ingestion Service creates an `IngestionJob` entity to track the document's ingestion process.
6. **Document Processing**: The document is processed by the Summarizer Hub service, which generates a summary of the document.
7. **Summary Storage**: The summary is stored in the Document Store service.
8. **Document Event Update**: The `DocumentEvent` entity is updated to reflect the successful processing of the document.
9. **Ingestion Job Completion**: The `IngestionJob` entity is marked as completed, indicating that the document has been successfully ingested.

This flow involves multiple services and components working together to ingest a document into the Ecosystem MCP Service.

Based on the provided context, here is the complete flow for a semantic search query:

1. **User Input**: The user submits a query to the system, such as "What is machine learning?"
2. **Preprocessing**: The query is preprocessed to remove any unnecessary characters and convert it into a format that can be understood by the system.
3. **Embedding Generation**: The preprocessed query is used to generate an embedding, which is a numerical representation of the query's meaning.
4. **Document Retrieval**: The generated embedding is used to retrieve a set of relevant documents from the database. This is done using a semantic search algorithm that takes into account the similarity between the query and each document.
5. **Context Building**: The retrieved documents are then used to build a context for the query. This involves extracting key information from multiple sources and combining it into a coherent answer.
6. **Answer Generation**: The built context is then used to generate an answer to the user's query. This is done using a language model that takes into account the context and generates a response that is relevant and accurate.
7. **Post-processing**: The generated answer is then post-processed to ensure it meets certain criteria, such as being concise and easy to understand.
8. **Response**: The final answer is then returned to the user as a response to their query.

Here's an example of what this flow might look like in code:
```python
# User input
query = "What is machine learning?"

# Preprocessing
preprocessed_query = preprocess(query)

# Embedding generation
embedding = generate_embedding(preprocessed_query)

# Document retrieval
documents = retrieve_documents(embedding)

# Context building
context = build_context(documents)

# Answer generation
answer = generate_answer(context)

# Post-processing
post_processed_answer = post_process(answer)

# Response
return post_processed_answer
```
Note that this is a simplified example and the actual implementation may vary depending on the specific requirements of the system.

I don't see any information about a RAG question-answering request in the provided context. However, based on the module descriptions and function names, I can try to provide a possible answer.

To show the complete flow for a RAG (Reasoning Augmentation Graph) question-answering request, we would need to follow the steps outlined in the `services/simulation-dashboard/components/tables/simulation_tables.py` module. This module appears to be responsible for rendering simulation tables and managing simulation data.

Here's a possible answer based on this information:

1. The user submits a RAG question-answering request, which is handled by the `render_simulation_table` function.
2. The `render_simulation_table` function prepares the simulation data as a clean DataFrame with required columns using the `_prepare_simulation_dataframe` function.
3. The function then applies filters to the simulation DataFrame using the `_apply_simulation_filters` function and renders filter controls using the `_render_simulation_filters` function.
4. Next, the function sorts the filtered DataFrame using the `_render_simulation_sorting` function and renders selection controls using the `_render_selection_controls` function.
5. After that, the function displays the main simulation table using the `_render_simulation_table_display` function and individual actions using the `_render_individual_actions` function.
6. Finally, the function renders table statistics using the `_render_simulation_statistics` function.

Please note that this is a possible answer based on the provided context, and the actual flow for a RAG question-answering request may be different depending on the specific implementation and requirements.

Based on the provided context, here are the key configuration points and environment variables:

**Configuration Points:**

1. **Unified API Dashboard**: The `Chart.yaml` file in the `services/unified-api-dashboard/deploy/helm/` directory contains configuration settings for the Unified API Dashboard service.
2. **MCP Provisioner**: The `__init__.py` file in the `services/mcp-provisioner/infrastructure/config/` directory provides configuration management for MCP Provisioner.
3. **MCP Composer**: The `__init__.py` file in the `services/mcp-composer/infrastructure/config/` directory is a configuration module.
4. **CLI Service**: The `constants.py` file in the `services/cli/infrastructure/config/` directory provides centralized constants and environment variable names for the CLI service.
5. **Analysis Service**: The `infrastructure_config.py` file in the `services/analysis-service/infrastructure/config/` directory contains main infrastructure configuration settings.

**Environment Variables:**

1. **Service URLs**: The `get_service_url()` function in the `constants.py` file returns a service URL from an environment variable with a fallback to a default URL.
2. **Service Names**: The `EnvVars` class in the `constants.py` file provides environment variable names for CLI service configuration.
3. **Service Ports**: The `ServicePorts` class in the `constants.py` file contains default service ports.

**Configuration Sources:**

1. **File Configuration Source**: The `FileConfigurationSource` class in the `configuration_service.py` file loads configuration from files (YAML, JSON, etc.).
2. **Environment Variable Configuration Source**: The `EnvironmentConfigurationSource` class in the `configuration_service.py` file loads configuration from environment variables.
3. **In-Memory Configuration Source**: The `InMemoryConfigurationSource` class in the `configuration_service.py` file provides an in-memory configuration source for testing and runtime configuration.

**Settings Managers:**

1. **Settings Manager**: The `SettingsManager` class in the `settings_manager.py` file manages settings and system diagnostics for the CLI service.
2. **Config Loader**: The `ConfigLoader` class in the `base_config.py` file loads configuration from multiple sources, including environment variables and files.

**Configuration Validation:**

1. **Config Validator**: The `ConfigValidator` class in the `config_validator.py` file validates that the `.env` file matches the `docker-compose.yml` file to prevent configuration drift.

Note that this is not an exhaustive list of all configuration points and environment variables, but rather a summary based on the provided context.

