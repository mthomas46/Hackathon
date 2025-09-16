# Confluence Hub Service

A FastAPI service that retrieves Confluence pages and their hierarchies, converts them to markdown format, and stores them in MongoDB for NLQ (Natural Language Query) search processing.

## Features

- **Page Conversion**: Convert Confluence pages and all subpages to markdown format
- **MongoDB Storage**: Store converted pages with metadata in MongoDB
- **Health Checks**: Validate connectivity to both Confluence and MongoDB
- **Hierarchical Processing**: Recursively process page hierarchies with configurable depth
- **Session Tracking**: Group conversions by session ID for batch management
- **Flexible Search**: Find pages by ID or title within specific spaces

## Environment Variables

The service requires the following environment variables:

```bash
# Confluence Configuration
ConfluenceBaseUrl=https://your-domain.atlassian.net  # or your server URL
ConfluenceUsername=your-email@company.com
ConfluenceApiToken=your-api-token

# MongoDB Configuration
MongoConnectionString=mongodb://localhost:27017/confluence_hub
```

### Getting Confluence API Token

1. Go to your Atlassian Account Settings
2. Navigate to Security → API tokens
3. Create a new API token
4. Use your email and the token for authentication

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
    "updated_at": "datetime"
}
```

## API Endpoints

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

## Architecture Notes

- **Confluence Client**: Handles authentication and API interactions with Confluence
- **MongoDB Client**: Manages document storage and retrieval with automatic indexing
- **Content Conversion**: Basic HTML to Markdown conversion (can be enhanced with markdownify)
- **Error Handling**: Comprehensive error handling with detailed logging
- **Health Monitoring**: Built-in health checks for all external dependencies

## Database Indexes

The service automatically creates the following indexes for optimal performance:

- `session_id` - For session-based queries
- `confluence_page_id` - Unique index for page identification
- `metadata.space_key` - For space-based filtering
- Text index on `title` and `content` - For search functionality

## Docker Support

The service can be containerized using the standard Python FastAPI patterns used in other services in this project.

## Development

The service follows the project's shared patterns:

- Uses shared configuration system for environment variables
- Implements standardized health endpoints
- Follows consistent error handling patterns
- Uses shared middleware and utilities

## Future Enhancements

- Enhanced HTML to Markdown conversion using markdownify
- Embedding generation for vector search
- Incremental sync based on page modification dates
- Support for Confluence attachments
- Advanced content filtering and preprocessing
