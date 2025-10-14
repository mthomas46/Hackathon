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
            elif method == "tools/list":
                return await self.handle_tools_list(params)
            elif method == "tools/call":
                return await self.handle_tool_call(params)
            elif method == "resources/list":
                return await self.handle_resources_list(params)
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
        # Use the client's protocol version if provided
        client_protocol = params.get("protocolVersion", "2024-11-05")
        
        return {
            "result": {
                "serverInfo": {
                    "name": MCP_SERVER_NAME,
                    "version": MCP_VERSION
                },
                "capabilities": {
                    "tools": {},  # Empty object means we support tools
                    "resources": {}  # Empty object means we support resources
                },
                "protocolVersion": client_protocol
            }
        }
    
    async def handle_tools_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/list request"""
        return {
            "result": {
                "tools": [
                    {
                        "name": "query",
                        "description": "Ask a question using RAG (Retrieval Augmented Generation)",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "question": {
                                    "type": "string",
                                    "description": "The question to answer"
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
                            },
                            "required": ["question"]
                        }
                    },
                    {
                        "name": "search",
                        "description": "Search for documents in the knowledge base",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Search query"
                                },
                                "limit": {
                                    "type": "integer",
                                    "description": "Maximum number of results",
                                    "default": 10
                                }
                            },
                            "required": ["query"]
                        }
                    }
                ]
            }
        }
    
    async def handle_tool_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request"""
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        
        if tool_name == "query":
            return await self._execute_query(arguments)
        elif tool_name == "search":
            return await self._execute_search(arguments)
        else:
            return {
                "error": {
                    "code": -32602,
                    "message": f"Unknown tool: {tool_name}"
                }
            }
    
    async def handle_resources_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/list request"""
        return {
            "result": {
                "resources": []
            }
        }
    
    async def _execute_query(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute RAG query"""
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
                # Format as MCP tool response
                result_text = f"**Answer:** {data.get('answer', '')}\n\n"
                result_text += f"**Mode:** {data.get('mode', mode)}\n"
                result_text += f"**Tier:** {data.get('tier_used', 'unknown')}\n\n"
                
                sources = data.get('sources', [])
                if sources:
                    result_text += "**Sources:**\n"
                    for i, source in enumerate(sources[:5], 1):
                        result_text += f"{i}. {source.get('file_path', 'Unknown')} (relevance: {source.get('relevance_score', 0):.2f})\n"
                
                return {
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": result_text
                            }
                        ]
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
    
    async def _execute_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute search"""
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
                results = data.get("results", [])
                
                # Format as MCP tool response
                result_text = f"**Search Results for:** {query}\n\n"
                result_text += f"**Total matches:** {data.get('total', 0)}\n\n"
                
                if results:
                    for i, result in enumerate(results, 1):
                        result_text += f"{i}. **{result.get('file_path', 'Unknown')}**\n"
                        result_text += f"   Relevance: {result.get('relevance_score', 0):.3f}\n"
                        if 'content_preview' in result:
                            result_text += f"   Preview: {result['content_preview'][:100]}...\n"
                        result_text += "\n"
                
                return {
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": result_text
                            }
                        ]
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
    
    async def run(self):
        """Main server loop - read from stdin, write to stdout"""
        sys.stderr.write(f"Starting {MCP_SERVER_NAME} v{MCP_VERSION}\n")
        sys.stderr.flush()
        
        # Set up async reader for stdin
        loop = asyncio.get_event_loop()
        reader = asyncio.StreamReader(loop=loop)
        protocol = asyncio.StreamReaderProtocol(reader)
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)
        
        try:
            while True:
                try:
                    # Read JSON-RPC request from stdin (async)
                    line = await reader.readline()
                    if not line:
                        sys.stderr.write("EOF received, exiting\n")
                        sys.stderr.flush()
                        break
                    
                    line_str = line.decode('utf-8').strip()
                    if not line_str:
                        continue
                    
                    sys.stderr.write(f"Received: {line_str[:150]}...\n")
                    sys.stderr.flush()
                    
                    request = json.loads(line_str)
                    
                    # Handle notifications (no response needed)
                    if "id" not in request:
                        method = request.get("method", "")
                        sys.stderr.write(f"Notification received: {method}\n")
                        sys.stderr.flush()
                        
                        # Special handling for 'initialized' notifications
                        if method in ["initialized", "notifications/initialized"]:
                            sys.stderr.write("Server initialized and ready\n")
                            sys.stderr.flush()
                        continue
                    
                    # Process request
                    response = await self.handle_request(request)
                    
                    # Add request ID
                    response["id"] = request["id"]
                    response["jsonrpc"] = "2.0"
                    
                    # Write response to stdout
                    response_str = json.dumps(response)
                    sys.stdout.write(response_str + "\n")
                    sys.stdout.flush()
                    
                    sys.stderr.write(f"Sent: {response_str[:150]}...\n")
                    sys.stderr.flush()
                    
                except json.JSONDecodeError as e:
                    sys.stderr.write(f"Invalid JSON: {e}\n")
                    sys.stderr.flush()
                except Exception as e:
                    sys.stderr.write(f"Error processing: {e}\n")
                    import traceback
                    sys.stderr.write(traceback.format_exc())
                    sys.stderr.flush()
        finally:
            await self.client.aclose()
            sys.stderr.write("MCP server stopped\n")
            sys.stderr.flush()

async def main():
    """Main entry point"""
    server = MCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())

