"""
DocStore Service Adapter for CLI interaction
Handles document storage, retrieval, and management operations
"""

import asyncio
import time
from typing import Dict, List, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from .base_service_adapter import BaseServiceAdapter, ServiceInfo, ServiceStatus, CommandResult


class DocStoreAdapter(BaseServiceAdapter):
    """
    Adapter for DocStore service - handles document storage and retrieval
    """
    
    def __init__(self, console: Console, clients: Any, base_url: str):
        super().__init__(console, clients, base_url)
        self.service_info = ServiceInfo(
            name="doc_store",
            version="1.0.0",
            description="Document storage and retrieval service",
            endpoints=[
                "/health",
                "/documents",
                "/documents/{doc_id}",
                "/search",
                "/collections",
                "/status"
            ],
            dependencies=["redis", "filesystem"]
        )
    
    def get_available_commands(self) -> List[str]:
        """Return list of available commands for this service"""
        return [
            "status",
            "documents",
            "collections", 
            "search",
            "upload",
            "get",
            "delete",
            "stats"
        ]
    
    async def execute_command(self, command: str, **kwargs) -> CommandResult:
        """Execute a command against the DocStore service"""
        command_map = {
            "status": self._get_status,
            "documents": self._list_documents,
            "collections": self._list_collections,
            "search": self._search_documents,
            "upload": self._upload_document,
            "get": self._get_document,
            "delete": self._delete_document,
            "stats": self._get_stats
        }
        
        if command not in command_map:
            return CommandResult(
                success=False,
                error=f"Unknown command: {command}. Available: {', '.join(self.get_available_commands())}"
            )
        
        return await command_map[command](**kwargs)
    
    # Private command implementations
    async def _get_status(self) -> CommandResult:
        """Get DocStore service status and statistics"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/status"
            response = await self.clients.get_json(url)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message="DocStore status retrieved successfully",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to get DocStore status: {str(e)}"
            )
    
    async def _list_documents(self, limit: int = 10, offset: int = 0) -> CommandResult:
        """List documents in the store"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/documents"
            params = {"limit": limit, "offset": offset}
            response = await self.clients.get_json(url, params=params)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message=f"Retrieved {len(response.get('documents', []))} documents",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to list documents: {str(e)}"
            )
    
    async def _list_collections(self) -> CommandResult:
        """List document collections"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/collections"
            response = await self.clients.get_json(url)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message=f"Retrieved {len(response.get('collections', []))} collections",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to list collections: {str(e)}"
            )
    
    async def _search_documents(self, query: str, collection: Optional[str] = None) -> CommandResult:
        """Search for documents"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/search"
            payload = {"query": query}
            if collection:
                payload["collection"] = collection
            
            response = await self.clients.post_json(url, payload)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message=f"Search completed: {len(response.get('results', []))} results found",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to search documents: {str(e)}"
            )
    
    async def _upload_document(self, content: str, title: str, collection: Optional[str] = None) -> CommandResult:
        """Upload a document to the store"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/documents"
            payload = {
                "content": content,
                "title": title,
                "metadata": {}
            }
            if collection:
                payload["collection"] = collection
            
            response = await self.clients.post_json(url, payload)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message=f"Document uploaded successfully: {response.get('id', 'unknown')}",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to upload document: {str(e)}"
            )
    
    async def _get_document(self, doc_id: str) -> CommandResult:
        """Retrieve a specific document"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/documents/{doc_id}"
            response = await self.clients.get_json(url)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message=f"Document retrieved: {doc_id}",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to get document {doc_id}: {str(e)}"
            )
    
    async def _delete_document(self, doc_id: str) -> CommandResult:
        """Delete a specific document"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/documents/{doc_id}"
            response = await self.clients.delete_json(url)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message=f"Document deleted: {doc_id}",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to delete document {doc_id}: {str(e)}"
            )
    
    async def _get_stats(self) -> CommandResult:
        """Get DocStore statistics and metrics"""
        try:
            start_time = time.time()
            
            # Get basic status
            status_response = await self.clients.get_json(f"{self.base_url}/status")
            
            # Try to get document count
            docs_response = await self.clients.get_json(f"{self.base_url}/documents", params={"limit": 1})
            doc_count = docs_response.get("total", 0) if docs_response else 0
            
            # Try to get collections count  
            collections_response = await self.clients.get_json(f"{self.base_url}/collections")
            collection_count = len(collections_response.get("collections", [])) if collections_response else 0
            
            execution_time = time.time() - start_time
            
            stats = {
                "status": status_response,
                "document_count": doc_count,
                "collection_count": collection_count,
                "service_uptime": status_response.get("uptime", "unknown") if status_response else "unknown"
            }
            
            return CommandResult(
                success=True,
                data=stats,
                message="DocStore statistics retrieved successfully",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to get DocStore stats: {str(e)}"
            )
    
    def format_response(self, result: CommandResult, command: str) -> None:
        """Format and display the command result"""
        if not result.success:
            self.console.print(f"[red]❌ Error: {result.error}[/red]")
            return
        
        # Command-specific formatting
        if command == "status":
            self._format_status_response(result.data)
        elif command == "documents":
            self._format_documents_response(result.data)
        elif command == "collections":
            self._format_collections_response(result.data)
        elif command == "search":
            self._format_search_response(result.data)
        elif command == "stats":
            self._format_stats_response(result.data)
        else:
            # Generic formatting
            self.console.print(f"[green]✅ {result.message}[/green]")
            if result.data:
                self.console.print(Panel(str(result.data), title="Response Data", border_style="blue"))
        
        if result.execution_time:
            self.console.print(f"[dim]⏱️  Execution time: {result.execution_time:.3f}s[/dim]")
    
    def _format_status_response(self, data: Dict[str, Any]) -> None:
        """Format status response"""
        if not data:
            self.console.print("[yellow]⚠️  No status data available[/yellow]")
            return
            
        table = Table(title="📁 DocStore Status", border_style="green")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        for key, value in data.items():
            table.add_row(str(key), str(value))
        
        self.console.print(table)
    
    def _format_documents_response(self, data: Dict[str, Any]) -> None:
        """Format documents list response"""
        documents = data.get("documents", [])
        if not documents:
            self.console.print("[yellow]📄 No documents found[/yellow]")
            return
        
        table = Table(title="📄 Documents", border_style="blue")
        table.add_column("ID", style="cyan")
        table.add_column("Title", style="green")
        table.add_column("Collection", style="yellow")
        table.add_column("Created", style="dim")
        
        for doc in documents:
            table.add_row(
                doc.get("id", "N/A"),
                doc.get("title", "Untitled"),
                doc.get("collection", "default"),
                doc.get("created_at", "N/A")
            )
        
        self.console.print(table)
        
        total = data.get("total", len(documents))
        self.console.print(f"[dim]Total documents: {total}[/dim]")
    
    def _format_collections_response(self, data: Dict[str, Any]) -> None:
        """Format collections response"""
        collections = data.get("collections", [])
        if not collections:
            self.console.print("[yellow]📁 No collections found[/yellow]")
            return
        
        table = Table(title="📁 Collections", border_style="magenta")
        table.add_column("Name", style="cyan")
        table.add_column("Document Count", style="green")
        table.add_column("Description", style="yellow")
        
        for collection in collections:
            if isinstance(collection, str):
                table.add_row(collection, "N/A", "N/A")
            else:
                table.add_row(
                    collection.get("name", "N/A"),
                    str(collection.get("document_count", "N/A")),
                    collection.get("description", "N/A")
                )
        
        self.console.print(table)
    
    def _format_search_response(self, data: Dict[str, Any]) -> None:
        """Format search results"""
        results = data.get("results", [])
        if not results:
            self.console.print("[yellow]🔍 No search results found[/yellow]")
            return
        
        table = Table(title="🔍 Search Results", border_style="cyan")
        table.add_column("Score", style="green")
        table.add_column("Title", style="cyan")
        table.add_column("ID", style="dim")
        table.add_column("Snippet", style="yellow")
        
        for result in results:
            table.add_row(
                f"{result.get('score', 0):.3f}",
                result.get("title", "Untitled"),
                result.get("id", "N/A"),
                result.get("snippet", "")[:50] + "..." if len(result.get("snippet", "")) > 50 else result.get("snippet", "")
            )
        
        self.console.print(table)
        
        query = data.get("query", "")
        total = len(results)
        self.console.print(f"[dim]Query: '{query}' - {total} results[/dim]")
    
    def _format_stats_response(self, data: Dict[str, Any]) -> None:
        """Format statistics response"""
        self.console.print(Panel.fit(
            f"📊 DocStore Statistics\n\n"
            f"📄 Documents: {data.get('document_count', 'N/A')}\n"
            f"📁 Collections: {data.get('collection_count', 'N/A')}\n"
            f"⏰ Uptime: {data.get('service_uptime', 'N/A')}\n"
            f"🟢 Status: {data.get('status', {}).get('status', 'unknown') if data.get('status') else 'unknown'}",
            title="DocStore Stats",
            border_style="green"
        ))
