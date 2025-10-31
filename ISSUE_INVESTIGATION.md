**Date:** October 29, 2025
**Status:** Issue Investigation

# Issue Investigation Report

## Issue #1: Standard RAG Returns 0 Documents

Testing basic query endpoint...

**Response**: 200
**Keys**: ['documents', 'total', 'limit', 'offset', 'has_next', 'has_previous']
**Full Response**:
```json
{'documents': [{'id': '328034dc-ec41-483e-abe3-c2f01945a544', 'service_name': 'ecosystem-mcp', 'file_path': 'DOCUMENTATION_GENERATOR_README.md', 'original_format': '.md', 'normalized_content': '# 🌲 Evergreen Documentation Generator\n\n**File**: `DOCUMENTATION_GENERATOR_README.md`\n**Service**: unknown\n\n---\n\n# 🌲 Evergreen Documentation Generator\n\n## Overview\n\nYour ecosystem-mcp service now has **AI-powered documentation generation** using its own RAG system. This creates "evergreen" docum
```

## Issue #2: Contexts Endpoint 500 Error

**Response**: 500
**Response Text**: {"success":false,"error":"Failed to list contexts: 'Database' object does not support the asynchronous context manager protocol","error_code":"INTERNAL_ERROR","status_code":500,"details":null,"request_id":"40e703fc-6918-4332-8aa4-650d2f5cda82","timestamp":"2025-10-29T18:48:24.990361","path":"/api/v1/contexts"}

## Issue #3: Cache Clear 500 Error

**Response**: 500
**Response Text**: {"success":false,"error":"An internal server error occurred","error_code":"INTERNAL_ERROR","status_code":500,"details":null,"request_id":"f87eacb7-c6e5-4072-a955-815c7797106b","timestamp":"2025-10-29T18:48:24.999564","path":"/api/v1/admin/clear-cache"}

## Document Database Status

**Total Documents**: Unknown
**Total Embeddings**: Unknown
**ChromaDB Documents**: Unknown

