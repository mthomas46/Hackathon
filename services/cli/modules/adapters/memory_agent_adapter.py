"""
Memory Agent Service Adapter for CLI interaction
Handles memory management, conversation history, and context storage
"""

import asyncio
import time
from typing import Dict, List, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from .base_service_adapter import BaseServiceAdapter, ServiceInfo, ServiceStatus, CommandResult


class MemoryAgentAdapter(BaseServiceAdapter):
    """
    Adapter for Memory Agent service - handles memory and context management
    """
    
    def __init__(self, console: Console, clients: Any, base_url: str):
        super().__init__(console, clients, base_url)
        self.service_info = ServiceInfo(
            name="memory_agent",
            version="1.0.0", 
            description="Memory management and conversation context service",
            endpoints=[
                "/health",
                "/memories",
                "/memories/{memory_id}",
                "/contexts",
                "/contexts/{context_id}",
                "/search",
                "/status"
            ],
            dependencies=["redis", "vectordb"]
        )
    
    def get_available_commands(self) -> List[str]:
        """Return list of available commands for this service"""
        return [
            "status",
            "memories",
            "contexts",
            "search",
            "store",
            "recall",
            "forget",
            "stats",
            "clear"
        ]
    
    async def execute_command(self, command: str, **kwargs) -> CommandResult:
        """Execute a command against the Memory Agent service"""
        command_map = {
            "status": self._get_status,
            "memories": self._list_memories,
            "contexts": self._list_contexts,
            "search": self._search_memories,
            "store": self._store_memory,
            "recall": self._recall_memory,
            "forget": self._forget_memory,
            "stats": self._get_stats,
            "clear": self._clear_memories
        }
        
        if command not in command_map:
            return CommandResult(
                success=False,
                error=f"Unknown command: {command}. Available: {', '.join(self.get_available_commands())}"
            )
        
        return await command_map[command](**kwargs)
    
    # Private command implementations
    async def _get_status(self) -> CommandResult:
        """Get Memory Agent service status"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/status"
            response = await self.clients.get_json(url)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message="Memory Agent status retrieved successfully",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to get Memory Agent status: {str(e)}"
            )
    
    async def _list_memories(self, limit: int = 10, context_id: Optional[str] = None) -> CommandResult:
        """List stored memories"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/memories"
            params = {"limit": limit}
            if context_id:
                params["context_id"] = context_id
            
            response = await self.clients.get_json(url, params=params)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message=f"Retrieved {len(response.get('memories', []))} memories",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to list memories: {str(e)}"
            )
    
    async def _list_contexts(self) -> CommandResult:
        """List conversation contexts"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/contexts"
            response = await self.clients.get_json(url)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message=f"Retrieved {len(response.get('contexts', []))} contexts",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to list contexts: {str(e)}"
            )
    
    async def _search_memories(self, query: str, context_id: Optional[str] = None) -> CommandResult:
        """Search memories by content"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/search"
            payload = {"query": query}
            if context_id:
                payload["context_id"] = context_id
            
            response = await self.clients.post_json(url, payload)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message=f"Search completed: {len(response.get('results', []))} memories found",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to search memories: {str(e)}"
            )
    
    async def _store_memory(self, content: str, context_id: Optional[str] = None, metadata: Optional[Dict] = None) -> CommandResult:
        """Store a new memory"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/memories"
            payload = {
                "content": content,
                "metadata": metadata or {}
            }
            if context_id:
                payload["context_id"] = context_id
            
            response = await self.clients.post_json(url, payload)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message=f"Memory stored successfully: {response.get('id', 'unknown')}",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to store memory: {str(e)}"
            )
    
    async def _recall_memory(self, memory_id: str) -> CommandResult:
        """Recall a specific memory"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/memories/{memory_id}"
            response = await self.clients.get_json(url)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message=f"Memory recalled: {memory_id}",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to recall memory {memory_id}: {str(e)}"
            )
    
    async def _forget_memory(self, memory_id: str) -> CommandResult:
        """Delete a specific memory"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/memories/{memory_id}"
            response = await self.clients.delete_json(url)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message=f"Memory forgotten: {memory_id}",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to forget memory {memory_id}: {str(e)}"
            )
    
    async def _clear_memories(self, context_id: Optional[str] = None) -> CommandResult:
        """Clear memories (optionally for a specific context)"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/memories/clear"
            payload = {}
            if context_id:
                payload["context_id"] = context_id
            
            response = await self.clients.post_json(url, payload)
            execution_time = time.time() - start_time
            
            context_msg = f" for context {context_id}" if context_id else ""
            return CommandResult(
                success=True,
                data=response,
                message=f"Memories cleared{context_msg}",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to clear memories: {str(e)}"
            )
    
    async def _get_stats(self) -> CommandResult:
        """Get Memory Agent statistics"""
        try:
            start_time = time.time()
            
            # Get basic status
            status_response = await self.clients.get_json(f"{self.base_url}/status")
            
            # Try to get memory count
            memories_response = await self.clients.get_json(f"{self.base_url}/memories", params={"limit": 1})
            memory_count = memories_response.get("total", 0) if memories_response else 0
            
            # Try to get context count
            contexts_response = await self.clients.get_json(f"{self.base_url}/contexts")
            context_count = len(contexts_response.get("contexts", [])) if contexts_response else 0
            
            execution_time = time.time() - start_time
            
            stats = {
                "status": status_response,
                "memory_count": memory_count,
                "context_count": context_count,
                "service_uptime": status_response.get("uptime", "unknown") if status_response else "unknown"
            }
            
            return CommandResult(
                success=True,
                data=stats,
                message="Memory Agent statistics retrieved successfully",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to get Memory Agent stats: {str(e)}"
            )
    
    def format_response(self, result: CommandResult, command: str) -> None:
        """Format and display the command result"""
        if not result.success:
            self.console.print(f"[red]❌ Error: {result.error}[/red]")
            return
        
        # Command-specific formatting
        if command == "status":
            self._format_status_response(result.data)
        elif command == "memories":
            self._format_memories_response(result.data)
        elif command == "contexts":
            self._format_contexts_response(result.data)
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
            
        table = Table(title="🧠 Memory Agent Status", border_style="green")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        for key, value in data.items():
            table.add_row(str(key), str(value))
        
        self.console.print(table)
    
    def _format_memories_response(self, data: Dict[str, Any]) -> None:
        """Format memories list response"""
        memories = data.get("memories", [])
        if not memories:
            self.console.print("[yellow]🧠 No memories found[/yellow]")
            return
        
        table = Table(title="🧠 Memories", border_style="blue")
        table.add_column("ID", style="cyan")
        table.add_column("Content", style="green", max_width=50)
        table.add_column("Context", style="yellow")
        table.add_column("Created", style="dim")
        
        for memory in memories:
            content = memory.get("content", "")
            if len(content) > 47:
                content = content[:47] + "..."
                
            table.add_row(
                memory.get("id", "N/A"),
                content,
                memory.get("context_id", "default"),
                memory.get("created_at", "N/A")
            )
        
        self.console.print(table)
        
        total = data.get("total", len(memories))
        self.console.print(f"[dim]Total memories: {total}[/dim]")
    
    def _format_contexts_response(self, data: Dict[str, Any]) -> None:
        """Format contexts response"""
        contexts = data.get("contexts", [])
        if not contexts:
            self.console.print("[yellow]💭 No contexts found[/yellow]")
            return
        
        table = Table(title="💭 Contexts", border_style="magenta")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Memory Count", style="yellow")
        table.add_column("Created", style="dim")
        
        for context in contexts:
            if isinstance(context, str):
                table.add_row(context, "N/A", "N/A", "N/A")
            else:
                table.add_row(
                    context.get("id", "N/A"),
                    context.get("name", "Unnamed"),
                    str(context.get("memory_count", "N/A")),
                    context.get("created_at", "N/A")
                )
        
        self.console.print(table)
    
    def _format_search_response(self, data: Dict[str, Any]) -> None:
        """Format search results"""
        results = data.get("results", [])
        if not results:
            self.console.print("[yellow]🔍 No memories found[/yellow]")
            return
        
        table = Table(title="🔍 Memory Search Results", border_style="cyan")
        table.add_column("Score", style="green")
        table.add_column("Content", style="cyan", max_width=60)
        table.add_column("ID", style="dim")
        table.add_column("Context", style="yellow")
        
        for result in results:
            content = result.get("content", "")
            if len(content) > 57:
                content = content[:57] + "..."
                
            table.add_row(
                f"{result.get('score', 0):.3f}",
                content,
                result.get("id", "N/A"),
                result.get("context_id", "default")
            )
        
        self.console.print(table)
        
        query = data.get("query", "")
        total = len(results)
        self.console.print(f"[dim]Query: '{query}' - {total} results[/dim]")
    
    def _format_stats_response(self, data: Dict[str, Any]) -> None:
        """Format statistics response"""
        self.console.print(Panel.fit(
            f"📊 Memory Agent Statistics\n\n"
            f"🧠 Memories: {data.get('memory_count', 'N/A')}\n"
            f"💭 Contexts: {data.get('context_count', 'N/A')}\n"
            f"⏰ Uptime: {data.get('service_uptime', 'N/A')}\n"
            f"🟢 Status: {data.get('status', {}).get('status', 'unknown') if data.get('status') else 'unknown'}",
            title="Memory Agent Stats",
            border_style="green"
        ))
