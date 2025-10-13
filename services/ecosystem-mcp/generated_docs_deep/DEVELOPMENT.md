# Development

# Development Guide

## Overview

To set up a development environment for ecosystem-mcp, follow these steps:

1. **Clone the repository**: Clone the ecosystem-mcp repository from GitHub using `git clone https://github.com/your-username/ecosystem-mcp.git`.
2. **Install dependencies**: Navigate to the cloned directory and run `pip install -r requirements.txt` to install all required dependencies.
3. **Create a virtual environment**: Create a new virtual environment using `python -m venv venv` (assuming you're using Python 3.x).
4. **Activate the virtual environment**: Activate the virtual environment by running `source venv/bin/activate` on Linux/Mac or `venv\Scripts\activate` on Windows.
5. **Install MCP dependencies**: Run `pip install -r mcp-requirements.txt` to install MCP-specific dependencies.
6. **Set up database**: Set up a PostgreSQL database and create the necessary tables using the provided SQL scripts.
7. **Configure environment variables**: Create a `.env` file in the root directory with your environment variables, such as `MCP_DB_HOST`, `MCP_DB_PORT`, etc.
8. **Run migrations**: Run `python manage.py migrate` to apply database migrations.
9. **Start the development server**: Run `python manage.py runserver` to start the development server.

Note: Make sure you have Python 3.x installed on your system, and you've cloned the repository from the correct GitHub repository. Additionally, ensure that you've created a new virtual environment for each project to avoid dependency conflicts.

I don't have enough information to provide a specific answer about the code structure and organization. However, I can suggest that you may be looking for information related to the `analyze_code_structure` function in [Source 8] services/analysis-service/tests/infrastructure/test_analysis_core.py.

This function is part of the test suite for the analysis core service and appears to analyze the code structure and organization. If you're interested in learning more about how this function works or what it does, I recommend reviewing the source code and documentation related to this function.

## Technical Details

Based on the provided context from the documentation, here is a description of the directory structure and what each directory contains:

**services**

* This directory contains various services, including:
	+ **summarizer-hub**: A service for summarizing documents.
		- `domain/entities/document.py`: Defines the Document entity.
		- `domain/repositories/document_repository.py`: Defines the interface for document repository operations.
	+ **doc_store**: A service for storing and managing documents.
		- `domain/lifecycle/__init__.py`: Manages lifecycle transitions for documents.
		- `application/handlers/dto/__init__.py`: Handles data transfer objects (DTOs) for document-related operations.
		- `application/commands/__init__.py`: Defines commands for write operations related to documents.
	+ **interpreter**: A service for interpreting and generating documents.
		- `domain/entities/document.py`: Defines the Document entity.
		- `domain/repositories/document_repository.py`: Defines the interface for document repository operations.

**scripts**

* This directory contains scripts, including:
	+ **audit-framework**: An audit framework for services in the ecosystem.
		- `domain/entities/service_info.py`: Defines the ServiceInfo entity, which represents a service with its metadata and business rules.

**services/shared**

* This directory contains shared utilities and infrastructure code across multiple services.
	+ `config.py`: Loads configuration from environment variables or files.
	+ `constants.py`: Defines common constants used across services.
	+ `envelopes.py`: Provides envelope patterns for structured responses.
	+ `html.py`: Composes HTML templates using helpers.

**services/mcp-evergreen-docs**

* This directory contains infrastructure code for the MCP Evergreen Docs service.
	+ `infrastructure/storage/redis_documentation_repository.py`: Implements a Redis-based documentation repository.

**services/doc_store**

* This directory contains infrastructure code for the Doc Store service.
	+ `infrastructure/repositories/__init__.py`: Defines repositories for data access operations.
	+ `infrastructure/database/__init__.py`: Handles database connections, migrations, and schema management.

**services/github-mcp**

* This directory contains presentation-layer code for the GitHub MCP service.
	+ `presentation/api/routes/repositories.py`: Defines API routes for repository-related operations.

**services/ecosystem-mcp**

* This directory contains infrastructure code for the Ecosystem MCP Service.
	+ `src/storage/__init__.py`: Provides a storage layer for database access using the repository pattern.
	+ `src/storage/repositories/document_repository.py`: Implements a document repository with domain-specific methods.

Note that this is not an exhaustive list, and there may be other directories or files not mentioned here.

Based on the provided context, here is a summary of the key Python modules and their purposes:

1. **`services/mcp-performance-store/infrastructure/repositories/__init__.py`**: Repository implementations for MCP Performance Store.
2. **`services/ecosystem-mcp/src/api/routes/__init__.py`**: API route modules for Ecosystem-MCP.
3. **`services/mcp-store/infrastructure/database/__init__.py`**: Database module for MCP Store.
4. **`services/mcp-performance-store/application/use_cases/__init__.py`**: Use cases for MCP Performance Store.
5. **`services/mcp-provisioner/infrastructure/database/__init__.py`**: Database connections and management for MCP Provisioner.
6. **`services/mcp-interpreter/application/use_cases/__init__.py`**: Use Cases for MCP Interpreter Application Layer.
7. **`services/mcp_local_llm/infrastructure/config/__init__.py`**: Configuration management for MCP Local LLM.
8. **`services/mcp-orchestrator/domain/repositories/__init__.py`**: Repository Interfaces for MCP Orchestrator domain.
9. **`services/github-mcp/presentation/api/__init__.py`**: GitHub MCP API presentation layer.
10. **`services/unified-api-dashboard/modules/security.py`**: Security module for Unified API Dashboard.

These modules are part of the Ecosystem-MCP microservices documentation system and provide various functionalities such as repository implementations, API routes, database management, use cases, configuration management, and security features.

The codebase appears to be organized into several layers:

1. **Services**: These are high-level components that encapsulate business logic and interact with other services or external systems. Examples include `analysis-service`, `orchestrator`, `prompt_store`, etc.
2. **Repositories**: These are data access objects (DAOs) that provide a layer of abstraction between the service logic and the underlying storage system. Repositories often implement CRUD operations for specific entities, such as users, features, or AI models. Examples include `user_repository`, `feature_repository`, `ai_model_repository`, etc.
3. **Models**: These are data structures that represent the shape of the data being stored or transmitted between services. Models can be used to validate and serialize data, ensuring consistency across different endpoints and services. Examples include `APIResponse`, `ErrorResponse`, `HealthResponse`, etc.
4. **Infrastructure**: This layer includes components that provide underlying functionality for the service, such as database connections, caching, logging, and error handling. Examples include `base_repository`, `sql_repository`, `in_memory_repository`, etc.

The codebase also appears to follow a microservices architecture, with each service being responsible for its own domain logic and interacting with other services through APIs or message queues. This allows for loose coupling between services and enables scalability, flexibility, and fault tolerance.

Based on the provided code snippets and descriptions, it appears that a combination of unit, integration, and functional testing strategies are being used.

**Unit Tests**

* Many files have names starting with "test_" or contain test-related functions, indicating they are designed for unit testing.
* Functions like `_assert_http_ok(response)` and `load_frontend_service()` suggest they are part of a larger testing framework, likely used to verify specific components or behaviors in isolation.
* Examples include:
	+ `services/frontend/tests/unit/test_domain_entities_clean.py`
	+ `services/doc_store/tests/unit/test_utils.py`

**Integration Tests**

* Files with names like "test_api_endpoints" or "test_redis_integration" suggest they are designed for integration testing, where multiple components or services are tested together.
* These tests often involve simulating real-world usage scenarios or workflows to ensure that different parts of the system interact correctly.
* Examples include:
	+ `services/kafka-ingestion-service/tests/functional/test_api_endpoints.py`
	+ `tests/integration/tagging/test_hierarchical_integration.py`

**Functional Tests**

* Files with names like "test_workflows" suggest they are designed for functional testing, where entire workflows or user journeys are tested to ensure the system behaves as expected.
* These tests often involve simulating real-world usage scenarios and verifying that the system produces the correct output or behavior.
* Examples include:
	+ `services/code-analyzer/tests/integration/test_workflows.py`

Overall, it appears that a combination of unit, integration, and functional testing strategies are being used to ensure the quality and reliability of the codebase.

I don't have enough information to provide a detailed answer on how to add a new API endpoint. The provided context includes various modules and classes related to the Ecosystem-MCP microservices documentation system, but it does not explicitly mention how to create or add new API endpoints.

However, based on the `BaseHandler` class in `services/doc_store/application/handlers/base_handler.py`, it appears that adding a new API endpoint would involve creating a new handler class that inherits from `BaseHandler`. This class would then define the specific logic for handling requests and responses for the new endpoint.

To add a new API endpoint, you might need to:

1. Create a new Python module or file in the relevant package (e.g., `services/doc_store/presentation/api/endpoints/`).
2. Define a new handler class that inherits from `BaseHandler`.
3. Implement the necessary logic for handling requests and responses for the new endpoint.
4. Register the new endpoint with the FastAPI application using the `@app.get()` or other decorator.

Please note that this is a high-level overview, and the actual implementation details may vary depending on your specific use case and requirements.

If you need more detailed guidance or have further questions, please provide more context or clarify what you are trying to achieve.

To add a new caching layer, you would need to create a new class that implements the caching logic and then integrate it with your existing storage layer. Here's an example of how you could do this:

First, let's assume we want to add a Redis-based caching layer. We can create a new class called `RedisCache`:
```python
import redis

class RedisCache:
    def __init__(self, host='localhost', port=6379):
        self.redis_client = redis.Redis(host=host, port=port)

    def get(self, key):
        return self.redis_client.get(key)

    def set(self, key, value):
        self.redis_client.set(key, value)
```
Next, we need to integrate this caching layer with our existing storage layer. We can do this by creating a new class that wraps the `RedisCache` and provides a consistent interface for accessing data:
```python
class CacheWrapper:
    def __init__(self, cache):
        self.cache = cache

    def get(self, key):
        return self.cache.get(key)

    def set(self, key, value):
        self.cache.set(key, value)
```
Now we can use the `CacheWrapper` class to access our cached data. For example:
```python
cache = CacheWrapper(RedisCache())
value = cache.get('my_key')
if value is None:
    # fetch from database if not in cache
    value = db.fetch('my_key')
    cache.set('my_key', value)
```
To integrate this caching layer with our existing storage layer, we can modify the `storage` module to use the `CacheWrapper` class instead of directly accessing the database. For example:
```python
from . import redis_cache

class Storage:
    def __init__(self):
        self.cache = CacheWrapper(redis_cache.RedisCache())

    def get(self, key):
        return self.cache.get(key)

    def set(self, key, value):
        self.cache.set(key, value)
```
This way, when we access data through the `Storage` class, it will first check the cache and if the data is not in the cache, it will fetch it from the database and store it in the cache for future use.

Note that this is just a simple example and you may need to modify it based on your specific requirements. Additionally, you should consider implementing caching strategies such as time-to-live (TTL) and cache invalidation to ensure that your cache remains up-to-date and efficient.

Based on the provided context, it appears that there is no specific information about coding standards and best practices. However, I can suggest some general guidelines based on the code snippets and module descriptions.

1. **Consistent naming conventions**: The code uses both camelCase and underscore notation for variable and function names. It's recommended to stick to a single convention throughout the project.
2. **Type hints**: Many modules use type hints for function parameters and return types, which is good practice for improving code readability and maintainability.
3. **Docstrings**: Some modules include docstrings that provide brief descriptions of classes, functions, or methods. This is helpful for understanding the purpose and behavior of different components.
4. **Error handling**: The `base_use_case` module provides a consistent interface for error handling across all use cases, which is a good practice for ensuring robustness and reliability.
5. **Testing**: There are several test modules (e.g., `test_utils`, `test_compression_service`) that demonstrate the importance of testing in ensuring the quality and correctness of the code.

To provide more specific guidance on coding standards and best practices, I would need more information about the project's requirements and constraints. If you have any additional context or questions, feel free to ask!

## Practical Information

Based on the provided context, specifically from [Source 14] docs/CONTRIBUTING.md, you can run tests locally by executing the following command:

```bash
make test   # run tests
```

This will execute all the tests in your project. If you want to build the documentation site locally as well, you can use the `make docs` command.

Additionally, from [Source 15] services/frontend/tests/unit/test_utils.py and other similar files (e.g., [Source 16], [Source 18]), it seems that there are test client fixtures available for various services. These fixtures might be used to run tests for specific services locally. However, the exact command to run these tests is not explicitly mentioned in the provided context.

To get more information on how to run tests for a specific service, you may need to refer to the documentation or code of that particular service.

To debug the application, you can use various tools and techniques depending on your development environment and the specific issues you're experiencing. Here are some general steps:

1. **Use a debugger**: Most IDEs (Integrated Development Environments) come with built-in debuggers that allow you to set breakpoints, inspect variables, and step through code execution.
2. **Print statements**: Add print statements throughout your code to see the values of variables at different points in the execution flow.
3. **Log messages**: Use a logging library to output messages at various levels (e.g., debug, info, warning, error) to help you understand what's happening during execution.
4. **Use a debugger like pdb**: If you're working on a command-line interface or don't have access to an IDE with a built-in debugger, you can use the `pdb` module in Python to set breakpoints and inspect variables.
5. **Check error messages**: When your application crashes or encounters an error, examine the error message for clues about what went wrong.
6. **Use a code analysis tool**: Tools like `pylint`, `flake8`, or `mypy` can help you identify potential issues with your code before they become problems during execution.

Some specific tools and techniques that might be useful in this context include:

* Using the `logging` module to output debug messages
* Setting breakpoints in an IDE's debugger
* Using `pdb` to inspect variables and step through code execution
* Checking error messages for clues about what went wrong

Here's an example of how you might use the `logging` module to add debug messages to your application:
```python
import logging

# Set up a logger
logger = logging.getLogger(__name__)

def my_function():
    # Add a debug message
    logger.debug("Entering my_function")

    # Do some work...
    result = do_something()

    # Add another debug message
    logger.debug("Exiting my_function with result: %s", result)

    return result
```
You can then configure your logging setup to output these messages at the desired level (e.g., `DEBUG`).

Similarly, you might use an IDE's debugger to set breakpoints and inspect variables. For example, in PyCharm, you could:

1. Open the "Run" menu and select "Debug"
2. Set a breakpoint by clicking on the line number where you want to pause execution
3. Run the application with the debugger attached

When the breakpoint is hit, you can inspect variables using the IDE's debugging tools.

I hope this helps! Let me know if you have any specific questions or need further guidance.

Based on the provided code snippets, here are some examples of common development tasks that can be inferred:

1. **Project Planning**:
	* Creating a project plan with milestones and phases.
	* Assigning team members to specific roles and tasks.
	* Estimating completion dates and tracking progress.
2. **Collaboration and Communication**:
	* Managing collaboration sessions for multiple users.
	* Tracking changes made by participants and resolving conflicts.
	* Notifying team members of updates and changes.
3. **Resource Allocation**:
	* Allocating resources (e.g., personnel, equipment) to specific tasks or phases.
	* Tracking resource utilization and availability.
4. **Job Management**:
	* Creating and managing training jobs for knowledge base updates.
	* Tracking job status and progress.
5. **Simulation and Planning**:
	* Simulating project timelines and Gantt charts.
	* Visualizing resource allocation and dependencies.

These tasks are likely to be performed by developers working on the services mentioned in the code snippets, such as:

1. Project planning service
2. Simulation dashboard service
3. Collaboration service
4. Job management service
5. Resource allocation service

Developers may use various tools and technologies, including Python, Kafka, and databases, to implement these tasks and services.

Based on the provided context from the documentation, it appears that contributing to workflows involves several steps:

1. **Pull Requests**: To contribute to workflows, you can submit a pull request with your changes. This is indicated in [Source 19] services/expert-finder-service/tests/integration/test_workflow_integration.py, where it mentions "Integration tests for end-to-end workflows" and includes methods like `test_workflow_find_experts_by_role()` and `test_workflow_sme_identification()`.
2. **Code Review**: After submitting a pull request, your code will be reviewed by others to ensure that it meets the required standards and is free of errors. This process is implied in [Source 16] services/orchestrator/application/workflow_management/commands.py, where it mentions "Application Commands for Workflow Management" and includes classes like `CreateWorkflowCommand` and `UpdateWorkflowCommand`.
3. **Workflows**: To contribute to workflows, you can also participate in the workflow management process by creating, updating, or deleting workflows. This is indicated in [Source 16] services/orchestrator/application/workflow_management/commands.py, where it mentions "Application Commands for Workflow Management" and includes classes like `CreateWorkflowCommand` and `UpdateWorkflowCommand`.

To contribute to workflows, you can follow these general steps:

1. Identify the workflow you want to contribute to.
2. Review the existing code and documentation related to that workflow.
3. Submit a pull request with your changes.
4. Participate in code review to ensure that your changes meet the required standards.

Note: The specific details of contributing to workflows may vary depending on the project or organization you are working with. It's always best to consult the official documentation and guidelines for the specific project or organization you are contributing to.

