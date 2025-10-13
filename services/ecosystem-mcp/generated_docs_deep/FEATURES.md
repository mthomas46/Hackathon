# Features

# Features

## Overview

Based on the provided context, here are the major features of Ecosystem-MCP:

1. **Service Architecture**: Microservices-based design with clear separation of concerns.
2. **Data Flow**: Document ingestion → Processing → Storage → Retrieval pipelines.
3. **Integration Points**: REST APIs, message queues, and event-driven patterns.
4. **Observability**: Comprehensive logging, monitoring, and health checks.
5. **Scalability**: Horizontal scaling with load balancing and caching strategies.

Additionally, the ecosystem provides various features for:

1. **Query Patterns & Best Practices**: Describes query patterns, optimization techniques, and best practices for using MCPs.
2. **Performance Tuning Guide**: Provides performance tuning guidelines, optimization techniques, and benchmarking approaches.
3. **Context Management**: Represents operational context for an MCP instance through the `MCPContext` entity, which stores operational state, metadata, and temporal information.

The ecosystem also includes various documentation and guides, such as:

1. **Query Patterns & Best Practices**
2. **Performance Tuning Guide**
3. **Context Management**

These features and guides are designed to help users effectively utilize the Ecosystem-MCP for their specific use cases.

The document ingestion system provides the following capabilities:

1. **Wikipedia Ingestion**: The `WikipediaIngestor` class in `ingestion/wikipedia_ingestor.py` allows crawling and ingesting Wikipedia pages with configurable depth.
2. **Fandom Wiki Ingestion**: The `FandomWikiIngestor` class in `ingestion/fandom_ingestor.py` provides a specialized crawler for Fandom wikis (like Warhammer 40k) with different HTML structure and API compared to standard Wikipedia.
3. **Document Parsing**: The `DocumentParser` class in `services/ecosystem-mcp/src/ingestion/parser.py` parses documents and extracts structured content from various file formats, including Python, Markdown, YAML, JSON, and text files.
4. **Metadata Extraction**: The `MetadataExtractor` class in `services/ecosystem-mcp/src/ingestion/metadata_extractor.py` extracts rich metadata from documents, including topics, tags, references, and other information.

These capabilities enable the ingestion system to collect and process various types of documents from different sources, making their content and metadata available for further analysis and processing.

Based on the provided code snippets, it appears that there are several search and retrieval features available in the system. Here are some of them:

1. **Semantic Search**: This feature allows for searching documents based on their meaning rather than just keywords. It uses embeddings to represent documents in a high-dimensional space, enabling more accurate and relevant results.
2. **Keyword Search**: A basic search feature that looks for exact matches of keywords in document titles, descriptions, or content.
3. **Hybrid Search**: Combines semantic and keyword search to provide a balance between relevance and recall.
4. **Batch Processing**: Allows for processing multiple queries simultaneously, improving performance and efficiency.
5. **Result Streaming**: Enables the system to return results as they are generated, reducing wait times and providing a more interactive experience.
6. **Cache Common Queries**: Caches frequently asked questions (FAQs) or common queries to improve response times and reduce load on the system.
7. **Pre-compute Embeddings**: Computes document embeddings in advance to speed up search operations.

These features are likely implemented using various techniques, including:

1. **Natural Language Processing (NLP)**: Used for text analysis, tokenization, stemming, and lemmatization.
2. **Information Retrieval (IR) algorithms**: Employed for ranking documents based on relevance, such as TF-IDF, BM25, or deep learning-based models.
3. **Machine Learning (ML) models**: Trained to improve search accuracy, handle ambiguity, and adapt to changing user behavior.

To answer the question "What search and retrieval features are available?" in a more formal tone:

The system provides several advanced search and retrieval features, including semantic search, keyword search, hybrid search, batch processing, result streaming, cache common queries, and pre-compute embeddings. These features leverage NLP techniques, IR algorithms, and ML models to improve the accuracy and efficiency of document retrieval.

## Technical Details

Semantic search is a technique used in information retrieval to improve the accuracy of search results by considering the meaning and context of the query, rather than just matching keywords. In the context of the provided code snippets, semantic search appears to be implemented using a combination of natural language processing (NLP) techniques and machine learning algorithms.

Here's a high-level overview of how semantic search might work in this context:

1. **Text Preprocessing**: The text data is preprocessed to remove stop words, stemming or lemmatizing words to their base form, and converting all text to lowercase.
2. **Tokenization**: The preprocessed text is tokenized into individual words or phrases, which are then analyzed for their meaning and context.
3. **Named Entity Recognition (NER)**: NER is used to identify named entities such as people, organizations, locations, and dates in the text data.
4. **Part-of-Speech (POS) Tagging**: POS tagging is used to identify the grammatical category of each word or phrase, such as noun, verb, adjective, etc.
5. **Dependency Parsing**: Dependency parsing is used to analyze the grammatical structure of the sentence and identify relationships between words.
6. **Semantic Role Labeling (SRL)**: SRL is used to identify the roles played by entities in a sentence, such as "agent," "patient," or "theme."
7. **Knowledge Graph Construction**: A knowledge graph is constructed from the preprocessed text data, where entities and their relationships are represented as nodes and edges.
8. **Query Analysis**: When a query is submitted, it is analyzed using NLP techniques to identify its meaning and context.
9. **Similarity Measurement**: The similarity between the query and the knowledge graph is measured using algorithms such as cosine similarity or Jaccard similarity.
10. **Ranking**: The search results are ranked based on their similarity to the query, with more relevant results appearing higher in the list.

Some of the specific techniques and algorithms used in semantic search include:

* **Word embeddings** (e.g., Word2Vec, GloVe): These techniques represent words as vectors in a high-dimensional space, allowing for semantic relationships between words to be captured.
* **Long Short-Term Memory (LSTM) networks**: LSTMs are a type of recurrent neural network (RNN) that can learn long-term dependencies in sequential data, such as text.
* **Attention mechanisms**: Attention mechanisms allow the model to focus on specific parts of the input data when generating output, which can improve performance on tasks like machine translation and question answering.

In the context of the provided code snippets, it appears that semantic search is implemented using a combination of NLP techniques and machine learning algorithms. The `ingestion/wikipedia_ingestor.py` module suggests that Wikipedia pages are crawled and ingested into a database, which is then used to construct a knowledge graph. The `services/doc_store/tests/unit/api/test_tagging.py` module tests the tagging functionality of the API, which likely uses semantic search techniques to identify relevant documents based on user queries.

Note that this is just a high-level overview, and the specific implementation details may vary depending on the requirements and constraints of the project.

I don't have enough information to describe the RAG implementation: retrieval, ranking, and generation. The provided context does not mention or reference any specific module or class related to RAG.

Based on the provided code snippets, the following caching strategies are implemented:

1. **Redis-based caching**: Implemented in `services/mcp-performance-store/infrastructure/repositories/redis_performance_repository.py`. This provides a fast caching layer for recent executions and pattern performance metrics.
2. **MinIO/S3 caching**: Implemented in `services/mcp-store/infrastructure/repositories/minio_storage_repository.py`. This handles binary storage of .mcp package files using MinIO client, which is compatible with S3.

Additionally, the following cache layers are mentioned:

1. **TimescaleDB**: Used for long-term storage and complex analytics in `services/mcp-performance-store/infrastructure/repositories/redis_performance_repository.py`.
2. **Cache configuration settings**: Provided by `get_cache_config()` function in `services/doc_store/infrastructure/config/settings.py`. This returns a dictionary with cache configuration.

Please note that these caching strategies might be part of a larger caching architecture, and there could be other cache layers not mentioned here.

Based on the provided code snippets and documentation, it appears that the 3-tier LLM routing refers to a system where requests are routed through three different layers or tiers:

1. **Cursor**: This is likely a local, in-memory caching layer that stores frequently accessed data. It's designed for low-latency access and high throughput.
2. **Desktop Ollama**: This tier seems to be an external service that provides LLM capabilities. It might be a cloud-based or on-premises deployment of the Ollama platform.
3. **Docker**: This tier is likely a containerized environment where the LLM model is deployed and executed.

The routing process involves sending requests from the client (e.g., the MCP-Gateway) to the Cursor, which then forwards the request to the Desktop Ollama if it's not cached locally. If the response is not available in the Cursor or Desktop Ollama, the request is sent to the Docker environment for processing.

Here's a high-level overview of how this routing might work:

1. Client (MCP-Gateway) sends a request to the Cursor.
2. The Cursor checks if it has a cached response for the requested data. If so, it returns the cached response directly to the client.
3. If the Cursor doesn't have the requested data in cache, it forwards the request to the Desktop Ollama.
4. The Desktop Ollama processes the request and returns the response to the Cursor.
5. The Cursor caches the response for future requests.
6. If the response is not available in the Cursor or Desktop Ollama, the request is sent to the Docker environment for processing.
7. The Docker environment executes the LLM model and returns the response to the Cursor.
8. The Cursor caches the response and returns it to the client.

This routing mechanism aims to provide a high-performance, scalable, and fault-tolerant system for handling LLM requests.

Based on the provided code snippets, it appears that there are several monitoring and observability features implemented across various services in the LLM Documentation Ecosystem. Here's a summary of what I found:

1. **Metrics Collection**: The `metrics.py` file in `services/shared/infrastructure/monitoring` provides a shared metrics collection service for LLM Documentation Ecosystem services, using Prometheus-compatible metrics.
2. **Alerting Manager**: The `alerting_manager.py` file in `services/cli/infrastructure/services/monitoring` manages alerting operations for CLI monitoring.
3. **Anomaly Detection**: The `anomaly_detection_service.py` file in `services/mcp-performance-store/domain/services/anomaly_detection_service` detects anomalies in performance data using statistical methods (Z-score, IQR).
4. **Log Anomaly Detection**: The `detector.py` file in `services/mcp-logs/infrastructure/anomaly/detector` uses statistical methods and ML for detecting anomalies in log patterns.
5. **Notification Status**: The `notification_status.py` file in `services/notification-service/domain/value_objects/notification_status` provides an enumeration of notification statuses, including active and terminal states.

These features suggest that the LLM Documentation Ecosystem has a robust monitoring and observability framework in place to track performance, detect anomalies, and manage notifications.

Based on the provided context, here is a comprehensive list of API endpoints with their descriptions:

**Analysis Service**

* `workflows_router`: Handles workflow-related operations. [Source 1]
* `distributed_router`: Handles distributed processing operations. [Source 7]

**Architecture Digitizer**

* Standard endpoints:
	+ Health check
	+ Service descriptor (about-me)
	+ Endpoints listing
	+ Provider-consumer relationships
	[Source 2]

**Discovery Agent**

* Discovery handler for OpenAPI endpoint discovery and registration.
	+ Handles complex logic for discovering and registering OpenAPI endpoints. [Source 3]
* UI handlers:
	+ Handles discovery agent service visualization, including endpoint registration monitoring, OpenAPI parsing, and service discovery operations. [Source 16]

**Prompt Store**

* Lifecycle management API handlers:
	+ Handles HTTP requests and responses for prompt lifecycle operations.
	+ Includes methods for getting lifecycle history, status counts, transition rules, and validating transitions. [Source 6]
* Relationships API handlers:
	+ Handles HTTP requests and responses for prompt relationship operations.
	+ Includes methods for getting relationships, updating relationship strength, deleting relationships, and more. [Source 10]
* Notifications API handlers:
	+ Handles HTTP requests and responses for webhook management and notification monitoring.
	+ Includes methods for listing webhooks, getting a specific webhook, getting notification stats, and cleaning up notifications. [Source 11]
* Bulk operations handlers:
	+ Handles HTTP requests and responses for bulk operations.
	+ Includes methods for initializing bulk operation handlers. [Source 17]

**MCP Store**

* Basic E2E API tests:
	+ Tests health endpoint (placeholder)
	+ Tests root endpoint (placeholder)
	+ Tests create package workflow (placeholder)
	+ Tests marketplace workflow (placeholder)
	+ Tests export/import workflow (placeholder) [Source 12]

**Doc Store**

* Core tests:
	+ Tests basic CRUD operations
	+ Tests health endpoints
	+ Tests core functionality at the API endpoint level. [Source 18]
* Analytics-related operations:
	+ Tests getting analytics summary and detailed analytics. [Source 18]
* Tagging-related operations:
	+ Tests tagging a document and getting document tags. [Source 18]
* Versioning-related operations:
	+ Tests creating versions, listing versions, and getting a specific version. [Source 18]

**Kafka Ingestion Service**

* Ingestion API endpoints: Handles ingestion-related operations. [Source 22]

Note that this list might not be exhaustive as there are many other modules and classes in the provided context. However, it covers most of the notable API endpoints mentioned across various services.

Also, please note that some of these endpoints might have placeholder implementations or are still under development (indicated by "placeholder" in their descriptions).

## Practical Information

Based on the provided context, I don't have enough information to provide specific examples of search queries and expected results. However, I can suggest some possible search query scenarios based on the modules and classes mentioned:

1. **Querying users by relationship**: Using the `QueryUsersByRelationshipUseCase` class from [Source 7], a user might search for experts related to a specific topic or service.
	* Search Query: "Find experts in AI"
	* Expected Result: A list of expert profiles with their relevant skills and experience
2. **Retrieving audit trends**: Using the `GetAuditTrendsQuery` class from [Source 12], an administrator might search for audit trends related to a specific service or time period.
	* Search Query: "Show me audit trends for the last quarter"
	* Expected Result: A graph or chart showing the number of audits performed, failed, or passed over time
3. **Analyzing code**: Using the `AnalysisResult` class from [Source 17], a developer might search for security issues in their codebase.
	* Search Query: "Find all security vulnerabilities in my code"
	* Expected Result: A list of identified security issues with details on how to fix them
4. **Querying document metadata**: Using the `GetDocumentQueryHandler` class from [Source 14], a user might search for documents related to a specific topic or author.
	* Search Query: "Find all documents written by John Doe"
	* Expected Result: A list of relevant documents with their metadata (title, date, etc.)

These are just a few examples based on the provided context. The actual search queries and expected results would depend on the specific implementation and requirements of each module or class.

I don't have enough information to provide examples of RAG questions with sample responses based on the provided context. The documentation sources provided focus on various aspects of the Ecosystem-MCP microservices, including testing utilities, service loading, and query execution use cases, but do not mention RAG (Red-Amber-Green) questions or their usage in this context.

However, I can suggest that RAG questions are often used in a quality assurance or audit framework to assess the status of specific items or processes. If you'd like, I can provide general information on how RAG questions might be structured and used in such contexts.

Based on the provided context, I don't have enough information to provide specific examples of API calls with curl commands. However, I can suggest some possible endpoints and methods that might be used in such scenarios:

1. **Health Check Endpoint**: You can use a GET request to check the health of the Ecosystem-MCP service.
   ```bash
curl -X GET http://localhost:8000/healthcheck
```
2. **OpenAPI Documentation**: You can use a GET request to retrieve the OpenAPI documentation for the Ecosystem-MCP API.
   ```bash
curl -X GET http://localhost:8000/openapi.json
```
3. **Query Endpoint**: You can use a POST request to query data using the Ecosystem-MCP API.
   ```bash
curl -X POST \
  http://localhost:8000/query \
  -H 'Content-Type: application/json' \
  -d '{"query": "your_query"}'
```
4. **Logs List Endpoint**: You can use a GET request to retrieve a list of logs from the Ecosystem-MCP service.
   ```bash
curl -X GET http://localhost:8000/logs/list
```

Please note that these are just examples and you should replace `http://localhost:8000` with the actual URL of your Ecosystem-MCP instance. Also, make sure to adjust the request method (GET/POST) and headers according to the specific endpoint and API requirements.

If you need more information or specific guidance on how to use these endpoints, please provide more context or details about what you are trying to achieve.

Based on the provided code snippets, it appears that there is no direct information about the performance characteristics of each feature. However, I can provide some insights based on the context and the types of features mentioned:

1. **Feature Decomposition Engine**: This feature seems to be related to breaking down high-level features into actionable tasks, user stories, and implementation steps. Its performance might depend on factors like:
	* Complexity of the input features
	* Number of decomposition rules applied
	* Efficiency of the AI-powered decomposition engine
2. **Trend Analyzer for MCP Performance Store**: This feature is responsible for analyzing trends in orchestration performance over time. Its performance might be influenced by:
	* Volume and complexity of data being analyzed
	* Effectiveness of trend detection algorithms
	* Scalability of the analytics system
3. **Event Broadcasting Integration Tests**: These tests seem to focus on verifying the functionality of event broadcasting, including WebSocket connections, event distribution, real-time updates, and integration with the simulation event system. Performance characteristics might include:
	* Throughput and latency of event broadcasting
	* Memory usage during broadcasting
	* Scalability and reliability of the broadcasting system
4. **Team Capacity Models**: This feature appears to be related to managing team capacity, skills tracking, and resource allocation. Its performance might depend on factors like:
	* Complexity of team structures and member roles
	* Number of tasks assigned and completed
	* Efficiency of skill matching and assignment algorithms

To provide more specific answers about the performance characteristics of each feature, I would need more information about the implementation details, data volumes, and usage scenarios.

