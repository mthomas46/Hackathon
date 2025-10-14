#!/usr/bin/env python3
"""
MCP Server for Cursor IDE Integration
This creates a Model Context Protocol server that Cursor can connect to
"""

import asyncio
import json
import sys
import httpx
from typing import Any, Dict, Optional

# Configuration
API_BASE_URL = "http://localhost:8000"
MCP_SERVER_NAME = "ecosystem-mcp"
MCP_VERSION = "1.0.0"

class MCPServer:
    """Model Context Protocol server for ecosystem-mcp"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=300.0)
        
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP request"""
        method = request.get("method", "")
        params = request.get("params", {})
        
        try:
            if method == "initialize":
                return await self.handle_initialize(params)
            elif method == "query":
                return await self.handle_query(params)
            elif method == "search":
                return await self.handle_search(params)
            elif method == "list_tools":
                return await self.handle_list_tools(params)
            else:
                return {
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
        except Exception as e:
            return {
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
    
    async def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialize request"""
        return {
            "result": {
                "serverInfo": {
                    "name": MCP_SERVER_NAME,
                    "version": MCP_VERSION
                },
                "capabilities": {
                    "tools": ["query", "search", "rag_query"],
                    "prompts": True,
                    "resources": True
                }
            }
        }
    
    async def handle_query(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle query request (RAG query)"""
        question = params.get("question", "")
        mode = params.get("mode", "rag")
        n_results = params.get("n_results", 10)
        
        if not question:
            return {
                "error": {
                    "code": -32602,
                    "message": "Missing required parameter: question"
                }
            }
        
        try:
            # Use enhanced query endpoint
            response = await self.client.post(
                f"{API_BASE_URL}/api/v1/query/enhanced",
                json={
                    "question": question,
                    "mode": mode,
                    "tier": "auto",
                    "n_results": n_results,
                    "temperature": 0.7,
                    "max_retries": 2
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "result": {
                        "answer": data.get("answer", ""),
                        "sources": data.get("sources", []),
                        "mode": data.get("mode", mode),
                        "tier_used": data.get("tier_used", "unknown"),
                        "confidence": data.get("confidence", 0.0)
                    }
                }
            else:
                return {
                    "error": {
                        "code": -32000,
                        "message": f"API error: {response.status_code}",
                        "data": response.text
                    }
                }
        except Exception as e:
            return {
                "error": {
                    "code": -32000,
                    "message": f"Query failed: {str(e)}"
                }
            }
    
    async def handle_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle search request"""
        query = params.get("query", "")
        limit = params.get("limit", 10)
        
        if not query:
            return {
                "error": {
                    "code": -32602,
                    "message": "Missing required parameter: query"
                }
            }
        
        try:
            response = await self.client.get(
                f"{API_BASE_URL}/api/v1/search",
                params={
                    "query": query,
                    "limit": limit
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "result": {
                        "results": data.get("results", []),
                        "total": data.get("total", 0)
                    }
                }
            else:
                return {
                    "error": {
                        "code": -32000,
                        "message": f"API error: {response.status_code}"
                    }
                }
        except Exception as e:
            return {
                "error": {
                    "code": -32000,
                    "message": f"Search failed: {str(e)}"
                }
            }
    
    async def handle_list_tools(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle list_tools request"""
        return {
            "result": {
                "tools": [
                    {
                        "name": "query",
                        "description": "Ask a question using RAG (Retrieval Augmented Generation)",
                        "parameters": {
                            "question": {
                                "type": "string",
                                "description": "The question to answer",
                                "required": True
                            },
                            "mode": {
                                "type": "string",
                                "description": "Query mode: rag, contextual, or basic",
                                "default": "rag"
                            },
                            "n_results": {
                                "type": "integer",
                                "description": "Number of documents to retrieve",
                                "default": 10
                            }
                        }
                    },
                    {
                        "name": "search",
                        "description": "Search for documents",
                        "parameters": {
                            "query": {
                                "type": "string",
                                "description": "Search query",
                                "required": True
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results",
                                "default": 10
                            }
                        }
                    }
                ]
            }
        }
    
    async def run(self):
        """Main server loop - read from stdin, write to stdout"""
        sys.stderr.write(f"Starting {MCP_SERVER_NAME} v{MCP_VERSION}\n")
        sys.stderr.flush()
        
        while True:
            try:
                # Read JSON-RPC request from stdin
                line = sys.stdin.readline()
                if not line:
                    break
                
                request = json.loads(line.strip())
                
                # Process request
                response = await self.handle_request(request)
                
                # Add request ID if present
                if "id" in request:
                    response["id"] = request["id"]
                
                response["jsonrpc"] = "2.0"
                
                # Write response to stdout
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
                
            except json.JSONDecodeError as e:
                sys.stderr.write(f"Invalid JSON: {e}\n")
                sys.stderr.flush()
            except Exception as e:
                sys.stderr.write(f"Error: {e}\n")
                sys.stderr.flush()
        
        await self.client.aclose()

async def main():
    """Main entry point"""
    server = MCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())

