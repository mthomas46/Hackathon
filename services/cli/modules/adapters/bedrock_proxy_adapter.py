"""
Bedrock Proxy Service Adapter for CLI interaction
Handles AWS Bedrock API interactions and LLM model access
"""

import asyncio
import time
from typing import Dict, List, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from .base_service_adapter import BaseServiceAdapter, ServiceInfo, ServiceStatus, CommandResult


class BedrockProxyAdapter(BaseServiceAdapter):
    """
    Adapter for Bedrock Proxy service - handles AWS Bedrock LLM interactions
    """
    
    def __init__(self, console: Console, clients: Any, base_url: str):
        super().__init__(console, clients, base_url)
        self.service_info = ServiceInfo(
            name="bedrock_proxy",
            version="1.0.0",
            description="AWS Bedrock API proxy for LLM model access",
            endpoints=[
                "/health",
                "/models",
                "/chat/completions",
                "/completions",
                "/embeddings",
                "/status"
            ],
            dependencies=["aws-bedrock", "boto3"]
        )
    
    def get_available_commands(self) -> List[str]:
        """Return list of available commands for this service"""
        return [
            "status",
            "models",
            "chat",
            "complete",
            "embed",
            "test-connection",
            "stats"
        ]
    
    async def execute_command(self, command: str, **kwargs) -> CommandResult:
        """Execute a command against the Bedrock Proxy service"""
        command_map = {
            "status": self._get_status,
            "models": self._list_models,
            "chat": self._chat_completion,
            "complete": self._text_completion,
            "embed": self._create_embeddings,
            "test-connection": self._test_connection,
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
        """Get Bedrock Proxy service status"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/status"
            response = await self.clients.get_json(url)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message="Bedrock Proxy status retrieved successfully",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to get Bedrock Proxy status: {str(e)}"
            )
    
    async def _list_models(self) -> CommandResult:
        """List available Bedrock models"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/models"
            response = await self.clients.get_json(url)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message=f"Retrieved {len(response.get('models', []))} available models",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to list models: {str(e)}"
            )
    
    async def _chat_completion(self, message: str, model: str = "claude-3", max_tokens: int = 1000) -> CommandResult:
        """Create a chat completion"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/chat/completions"
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": message}],
                "max_tokens": max_tokens
            }
            
            response = await self.clients.post_json(url, payload)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message="Chat completion generated successfully",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to create chat completion: {str(e)}"
            )
    
    async def _text_completion(self, prompt: str, model: str = "titan-text", max_tokens: int = 1000) -> CommandResult:
        """Create a text completion"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/completions"
            payload = {
                "model": model,
                "prompt": prompt,
                "max_tokens": max_tokens
            }
            
            response = await self.clients.post_json(url, payload)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message="Text completion generated successfully",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to create text completion: {str(e)}"
            )
    
    async def _create_embeddings(self, text: str, model: str = "titan-embed") -> CommandResult:
        """Create embeddings for text"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/embeddings"
            payload = {
                "model": model,
                "input": text
            }
            
            response = await self.clients.post_json(url, payload)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message="Embeddings created successfully",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to create embeddings: {str(e)}"
            )
    
    async def _test_connection(self) -> CommandResult:
        """Test connection to AWS Bedrock"""
        try:
            start_time = time.time()
            
            # First check service health
            health_response = await self.clients.get_json(f"{self.base_url}/health")
            
            # Then try to list models to test Bedrock connection
            models_response = await self.clients.get_json(f"{self.base_url}/models")
            
            execution_time = time.time() - start_time
            
            test_result = {
                "service_health": health_response,
                "bedrock_connection": "success" if models_response else "failed",
                "available_models": len(models_response.get("models", [])) if models_response else 0
            }
            
            return CommandResult(
                success=True,
                data=test_result,
                message="Bedrock connection test completed",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to test Bedrock connection: {str(e)}"
            )
    
    async def _get_stats(self) -> CommandResult:
        """Get Bedrock Proxy statistics"""
        try:
            start_time = time.time()
            
            # Get basic status
            status_response = await self.clients.get_json(f"{self.base_url}/status")
            
            # Try to get model count
            models_response = await self.clients.get_json(f"{self.base_url}/models")
            model_count = len(models_response.get("models", [])) if models_response else 0
            
            execution_time = time.time() - start_time
            
            stats = {
                "status": status_response,
                "available_models": model_count,
                "service_uptime": status_response.get("uptime", "unknown") if status_response else "unknown",
                "aws_region": status_response.get("aws_region", "unknown") if status_response else "unknown"
            }
            
            return CommandResult(
                success=True,
                data=stats,
                message="Bedrock Proxy statistics retrieved successfully",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to get Bedrock Proxy stats: {str(e)}"
            )
    
    def format_response(self, result: CommandResult, command: str) -> None:
        """Format and display the command result"""
        if not result.success:
            self.console.print(f"[red]❌ Error: {result.error}[/red]")
            return
        
        # Command-specific formatting
        if command == "status":
            self._format_status_response(result.data)
        elif command == "models":
            self._format_models_response(result.data)
        elif command == "chat":
            self._format_chat_response(result.data)
        elif command == "complete":
            self._format_completion_response(result.data)
        elif command == "embed":
            self._format_embeddings_response(result.data)
        elif command == "test-connection":
            self._format_test_response(result.data)
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
            
        table = Table(title="🤖 Bedrock Proxy Status", border_style="green")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        for key, value in data.items():
            table.add_row(str(key), str(value))
        
        self.console.print(table)
    
    def _format_models_response(self, data: Dict[str, Any]) -> None:
        """Format models list response"""
        models = data.get("models", [])
        if not models:
            self.console.print("[yellow]🤖 No models available[/yellow]")
            return
        
        table = Table(title="🤖 Available Bedrock Models", border_style="blue")
        table.add_column("Model ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Provider", style="yellow")
        table.add_column("Type", style="magenta")
        table.add_column("Max Tokens", style="dim")
        
        for model in models:
            if isinstance(model, str):
                table.add_row(model, "N/A", "N/A", "N/A", "N/A")
            else:
                table.add_row(
                    model.get("modelId", "N/A"),
                    model.get("modelName", "N/A"),
                    model.get("providerName", "N/A"),
                    model.get("modelType", "N/A"),
                    str(model.get("maxTokens", "N/A"))
                )
        
        self.console.print(table)
        
        self.console.print(f"[dim]Total models: {len(models)}[/dim]")
    
    def _format_chat_response(self, data: Dict[str, Any]) -> None:
        """Format chat completion response"""
        if not data:
            self.console.print("[yellow]💬 No response data[/yellow]")
            return
        
        choices = data.get("choices", [])
        if choices:
            message = choices[0].get("message", {}).get("content", "No content")
            self.console.print(Panel(
                message,
                title="💬 Chat Response",
                border_style="blue"
            ))
        
        usage = data.get("usage", {})
        if usage:
            self.console.print(f"[dim]📊 Token Usage: {usage.get('prompt_tokens', 0)} prompt + {usage.get('completion_tokens', 0)} completion = {usage.get('total_tokens', 0)} total[/dim]")
    
    def _format_completion_response(self, data: Dict[str, Any]) -> None:
        """Format text completion response"""
        if not data:
            self.console.print("[yellow]📝 No completion data[/yellow]")
            return
        
        choices = data.get("choices", [])
        if choices:
            text = choices[0].get("text", "No text")
            self.console.print(Panel(
                text,
                title="📝 Text Completion",
                border_style="green"
            ))
        
        usage = data.get("usage", {})
        if usage:
            self.console.print(f"[dim]📊 Token Usage: {usage.get('prompt_tokens', 0)} prompt + {usage.get('completion_tokens', 0)} completion = {usage.get('total_tokens', 0)} total[/dim]")
    
    def _format_embeddings_response(self, data: Dict[str, Any]) -> None:
        """Format embeddings response"""
        if not data:
            self.console.print("[yellow]🔢 No embeddings data[/yellow]")
            return
        
        embeddings = data.get("data", [])
        if embeddings:
            embedding = embeddings[0].get("embedding", [])
            self.console.print(Panel.fit(
                f"🔢 Embeddings Generated\n\n"
                f"📏 Dimensions: {len(embedding)}\n"
                f"📊 Sample values: {embedding[:5] if len(embedding) >= 5 else embedding}\n"
                f"🎯 Model: {data.get('model', 'unknown')}",
                title="Embeddings",
                border_style="cyan"
            ))
        
        usage = data.get("usage", {})
        if usage:
            self.console.print(f"[dim]📊 Token Usage: {usage.get('total_tokens', 0)} tokens[/dim]")
    
    def _format_test_response(self, data: Dict[str, Any]) -> None:
        """Format connection test response"""
        service_health = data.get("service_health", {})
        bedrock_status = data.get("bedrock_connection", "unknown")
        model_count = data.get("available_models", 0)
        
        status_color = "green" if bedrock_status == "success" else "red"
        status_icon = "✅" if bedrock_status == "success" else "❌"
        
        self.console.print(Panel.fit(
            f"🔗 Bedrock Connection Test\n\n"
            f"🟢 Service Health: {service_health.get('status', 'unknown')}\n"
            f"{status_icon} Bedrock Connection: [{status_color}]{bedrock_status}[/{status_color}]\n"
            f"🤖 Available Models: {model_count}\n"
            f"🌍 AWS Region: {service_health.get('aws_region', 'unknown')}",
            title="Connection Test Results",
            border_style=status_color
        ))
    
    def _format_stats_response(self, data: Dict[str, Any]) -> None:
        """Format statistics response"""
        self.console.print(Panel.fit(
            f"📊 Bedrock Proxy Statistics\n\n"
            f"🤖 Available Models: {data.get('available_models', 'N/A')}\n"
            f"🌍 AWS Region: {data.get('aws_region', 'N/A')}\n"
            f"⏰ Uptime: {data.get('service_uptime', 'N/A')}\n"
            f"🟢 Status: {data.get('status', {}).get('status', 'unknown') if data.get('status') else 'unknown'}",
            title="Bedrock Proxy Stats",
            border_style="green"
        ))
