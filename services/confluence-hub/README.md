# Confluence Hub Service

A FastAPI service that retrieves Confluence pages and their hierarchies, converts them to markdown format, stores them in MongoDB, and provides semantic search capabilities through OpenAI embeddings.

## Features

- **Page Conversion**: Convert Confluence pages and all subpages to markdown format
- **MongoDB Storage**: Store converted pages with metadata in MongoDB
- **Semantic Search**: Generate embeddings using OpenAI and perform vector similarity search
- **In-Memory Vector Cache**: Fast similarity search with cosine similarity algorithm
- **Embeddings Management**: Batch processing and automatic embedding generation
- **Health Checks**: Validate connectivity to Confluence, MongoDB, and OpenAI
- **Hierarchical Processing**: Recursively process page hierarchies with configurable depth
- **Session Tracking**: Group conversions by session ID for batch management
- **Flexible Search**: Find pages by ID, title, or semantic similarity

## Environment Variables

The service requires the following environment variables:

```bash
# Confluence Configuration
ConfluenceBaseUrl=https://your-domain.atlassian.net  # or your server URL
ConfluenceUsername=your-email@company.com
ConfluenceApiToken=your-api-token

# MongoDB Configuration
MongoConnectionString=mongodb://localhost:27017/confluence_hub

# OpenAI Configuration (Optional - for embeddings functionality)
OpenAIApiKey=sk-your-openai-api-key-here
```

### Getting API Tokens

**Confluence API Token:**
1. Go to your Atlassian Account Settings
2. Navigate to Security → API tokens
3. Create a new API token
4. Use your email and the token for authentication

**OpenAI API Key:**
1. Go to [OpenAI API Keys](https://platform.openai.com/api-keys)
2. Create a new API key
3. Copy the key and set it as `OpenAIApiKey`
4. If not provided, embeddings functionality will be disabled

## Database Structure

The service uses MongoDB with the following structure:

- **Database**: `confluence_hub`
- **Collection**: `confluence_pages`

### Document Schema

```python
{
    "_id": "ObjectId",
    "session_id": "string",
    "confluence_page_id": "string",
    "title": "string",
    "content": "string",  # Markdown content
    "metadata": {
        "original_url": "string",
        "space_key": "string",
        "parent_page_id": "string",
        "last_modified": "datetime",
        "author": "string",
        "version": "number"
    },
    "file_path": "string",
    "created_at": "datetime",
    "updated_at": "datetime",
    "embedding": [float],  # Optional: 1536-dimensional embedding vector
    "embedding_updated_at": "datetime"  # Optional: When embedding was generated
}
```

## API Endpoints

### Core Endpoints

### POST /convert-page

Convert a Confluence page and all its subpages to markdown and store in MongoDB.

**Request Body:**

```json
{
  "page_id": "123456789", // Optional: Confluence page ID
  "page_title": "My Page", // Optional: Page title to search for
  "space_key": "SPACE", // Required when using page_title
  "session_id": "session-123", // Required: Session identifier
  "max_depth": 10, // Optional: Maximum recursion depth
  "include_content": true // Optional: Whether to include page content
}
```

**Response:**

```json
{
    "success": true,
    "data": {
        "session_id": "session-123",
        "pages_processed": 5,
        "total_pages_found": 5,
        "pages": [...]
    },
    "message": "Successfully processed 5 pages"
}
```

### GET /pages

Retrieve stored pages with optional filtering.

**Query Parameters:**

- `session_id` (optional): Filter by session ID
- `limit` (optional): Number of pages to return (default: 100)
- `skip` (optional): Number of pages to skip (default: 0)

### GET /pages/{page_id}

Get a specific page by its Confluence page ID.

### DELETE /pages/{page_id}

Delete a specific page from the database.

### GET /health

Health check endpoint that validates MongoDB and Confluence connectivity.

### Embeddings Endpoints

### POST /embeddings/generate

Generate embeddings for all pages that don't have embeddings yet.

**Response:**
```json
{
    "success": true,
    "data": {
        "message": "Generated embeddings for 15 documents",
        "statistics": {
            "initial": {"total_documents": 20, "documents_with_embeddings": 5},
            "final": {"total_documents": 20, "documents_with_embeddings": 20},
            "processed": 15,
            "successful": 15,
            "failed": 0
        },
        "processing_time_seconds": 45.2
    }
}
```

### POST /embeddings/generate/{page_id}

Generate embedding for a specific page by its MongoDB document ID.

### GET /embeddings/stats

Get statistics about embeddings and service status.

**Response:**
```json
{
    "success": true,
    "data": {
        "statistics": {
            "total_documents": 20,
            "documents_with_embeddings": 15,
            "documents_without_embeddings": 5
        },
        "service_status": {
            "initialized": true,
            "openai_service_initialized": true,
            "vector_search_initialized": true,
            "embedding_model": "text-embedding-3-small",
            "embedding_dimension": 1536,
            "vector_cache_statistics": {
                "cache_size": 15,
                "memory_usage": "0.09 MB"
            }
        }
    }
}
```

### POST /search

Search for documents similar to a query text using semantic search.

**Request Body:**
```json
{
    "query": "API documentation and best practices",
    "limit": 5,
    "min_score": 0.15
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "query": "API documentation and best practices",
        "results": [
            {
                "document_id": "507f1f77bcf86cd799439011",
                "title": "REST API Guidelines",
                "confluence_page_id": "123456",
                "similarity_score": 0.89,
                "content_preview": "Our REST API follows standard conventions...",
                "metadata": {...}
            }
        ],
        "total_found": 3
    }
}
```

### POST /embeddings/refresh

Refresh the in-memory embeddings cache by reloading from MongoDB.

## Installation and Setup

1. **Install Dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Set Environment Variables:**

   ```bash
   export ConfluenceBaseUrl="https://your-domain.atlassian.net"
   export ConfluenceUsername="your-email@company.com"
   export ConfluenceApiToken="your-api-token"
   export MongoConnectionString="mongodb://localhost:27017/confluence_hub"
   export OpenAIApiKey="sk-your-openai-api-key-here"  # Optional
   ```

3. **Start MongoDB:**

   ```bash
   # Using Docker
   docker run -d -p 27017:27017 --name mongodb mongo:latest

   # Or use existing MongoDB instance
   ```

4. **Run the Service:**

   ```bash
   python main.py
   ```

   The service will start on port 5070.

## Usage Examples

### Core Functionality

### Convert a Page by ID

```bash
curl -X POST "http://localhost:5070/convert-page" \
  -H "Content-Type: application/json" \
  -d '{
    "page_id": "123456789",
    "session_id": "my-session-1",
    "max_depth": 5
  }'
```

### Convert a Page by Title

```bash
curl -X POST "http://localhost:5070/convert-page" \
  -H "Content-Type: application/json" \
  -d '{
    "page_title": "API Documentation",
    "space_key": "DEV",
    "session_id": "my-session-1",
    "max_depth": 3
  }'
```

### Get All Pages for a Session

```bash
curl "http://localhost:5070/pages?session_id=my-session-1"
```

### Health Check

```bash
curl "http://localhost:5070/health"
```

### Embeddings Functionality

### Generate Embeddings for All Pages

```bash
curl -X POST "http://localhost:5070/embeddings/generate" \
  -H "Content-Type: application/json"
```

### Generate Embedding for Specific Page

```bash
curl -X POST "http://localhost:5070/embeddings/generate/507f1f77bcf86cd799439011" \
  -H "Content-Type: application/json"
```

### Get Embeddings Statistics

```bash
curl "http://localhost:5070/embeddings/stats"
```

### Semantic Search

```bash
curl -X POST "http://localhost:5070/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "authentication and security best practices",
    "limit": 3,
    "min_score": 0.2
  }'
```

### Refresh Embeddings Cache

```bash
curl -X POST "http://localhost:5070/embeddings/refresh" \
  -H "Content-Type: application/json"
```

## Architecture Notes

- **Confluence Client**: Handles authentication and API interactions with Confluence
- **MongoDB Client**: Manages document storage and retrieval with automatic indexing and embedding support
- **OpenAI Service**: Integrates with OpenAI API for generating embeddings using text-embedding-3-small model
- **Vector Search Service**: Manages in-memory vector cache and performs cosine similarity search
- **Embeddings Manager**: Orchestrates embedding generation, storage, and search operations
- **Content Conversion**: Basic HTML to Markdown conversion (can be enhanced with markdownify)
- **Error Handling**: Comprehensive error handling with graceful degradation when services are unavailable
- **Health Monitoring**: Built-in health checks for all external dependencies including OpenAI

## Database Indexes

The service automatically creates the following indexes for optimal performance:

- `session_id` - For session-based queries
- `confluence_page_id` - Unique index for page identification
- `metadata.space_key` - For space-based filtering
- Text index on `title` and `content` - For search functionality
- `embedding` - For documents with embedding vectors

## Embeddings System

The service includes a comprehensive embeddings system that provides semantic search capabilities:

### Components

- **OpenAI Integration**: Uses OpenAI's `text-embedding-3-small` model (1536 dimensions)
- **Vector Storage**: Embeddings stored in MongoDB with automatic indexing
- **In-Memory Cache**: Fast vector similarity search with cosine similarity algorithm
- **Batch Processing**: Efficient batch embedding generation with rate limiting
- **Error Handling**: Graceful degradation when OpenAI API is unavailable

### Features

- **Automatic Generation**: Generate embeddings for all pages without embeddings
- **Incremental Updates**: Generate embeddings for specific pages
- **Semantic Search**: Find similar documents using natural language queries
- **Statistics & Monitoring**: Track embedding coverage and service health
- **Cache Management**: Automatic refresh of in-memory vector cache

### Performance

- **Search Speed**: Sub-second similarity search against thousands of documents
- **Memory Usage**: ~6KB per document embedding (1536 float32 values)
- **Rate Limiting**: Built-in rate limiting to respect OpenAI API limits
- **Batch Processing**: Process multiple documents efficiently

## Docker Support

The service can be containerized using the standard Python FastAPI patterns used in other services in this project.

## Development

The service follows the project's shared patterns:

- Uses shared configuration system for environment variables
- Implements standardized health endpoints
- Follows consistent error handling patterns
- Uses shared middleware and utilities
- Modular architecture with clear separation of concerns

### Dependencies

- **Core**: FastAPI, Motor (MongoDB), httpx
- **Embeddings**: OpenAI API client, python-dotenv
- **Content**: markdownify (optional for enhanced HTML conversion)

## Future Enhancements

- ~~Enhanced HTML to Markdown conversion using markdownify~~ ✅ Available
- ~~Embedding generation for vector search~~ ✅ Implemented
- ~~Semantic search capabilities~~ ✅ Implemented
- Incremental sync based on page modification dates
- Support for Confluence attachments
- Advanced content filtering and preprocessing
- Multi-model embedding support (different OpenAI models)
- Vector database integration (Pinecone, Weaviate, etc.)
- Embedding fine-tuning for domain-specific search
