"""
Interpreter Service Adapter for CLI interaction
Handles code execution and interpretation requests
"""

import asyncio
import time
from typing import Dict, List, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax

from .base_service_adapter import BaseServiceAdapter, ServiceInfo, ServiceStatus, CommandResult


class InterpreterAdapter(BaseServiceAdapter):
    """
    Adapter for Interpreter service - handles code execution and interpretation
    """
    
    def __init__(self, console: Console, clients: Any, base_url: str):
        super().__init__(console, clients, base_url)
        self.service_info = ServiceInfo(
            name="interpreter",
            version="1.0.0",
            description="Code execution and interpretation service",
            endpoints=[
                "/health",
                "/execute",
                "/languages",
                "/status",
                "/sessions",
                "/sessions/{session_id}"
            ],
            dependencies=["python", "docker", "sandbox"]
        )
    
    def get_available_commands(self) -> List[str]:
        """Return list of available commands for this service"""
        return [
            "status",
            "languages",
            "execute",
            "sessions",
            "create-session",
            "end-session",
            "test-execute",
            "stats"
        ]
    
    async def execute_command(self, command: str, **kwargs) -> CommandResult:
        """Execute a command against the Interpreter service"""
        command_map = {
            "status": self._get_status,
            "languages": self._get_languages,
            "execute": self._execute_code,
            "sessions": self._list_sessions,
            "create-session": self._create_session,
            "end-session": self._end_session,
            "test-execute": self._test_execute,
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
        """Get Interpreter service status"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/status"
            response = await self.clients.get_json(url)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message="Interpreter status retrieved successfully",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to get Interpreter status: {str(e)}"
            )
    
    async def _get_languages(self) -> CommandResult:
        """Get supported programming languages"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/languages"
            response = await self.clients.get_json(url)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message=f"Retrieved {len(response.get('languages', []))} supported languages",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to get supported languages: {str(e)}"
            )
    
    async def _execute_code(self, code: str, language: str = "python", session_id: Optional[str] = None) -> CommandResult:
        """Execute code in the interpreter"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/execute"
            payload = {
                "code": code,
                "language": language
            }
            if session_id:
                payload["session_id"] = session_id
            
            response = await self.clients.post_json(url, payload)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message=f"Code executed in {language}",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to execute code: {str(e)}"
            )
    
    async def _list_sessions(self) -> CommandResult:
        """List active execution sessions"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/sessions"
            response = await self.clients.get_json(url)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message=f"Retrieved {len(response.get('sessions', []))} active sessions",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to list sessions: {str(e)}"
            )
    
    async def _create_session(self, language: str = "python", name: Optional[str] = None) -> CommandResult:
        """Create a new execution session"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/sessions"
            payload = {
                "language": language
            }
            if name:
                payload["name"] = name
            
            response = await self.clients.post_json(url, payload)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message=f"Session created: {response.get('session_id', 'unknown')}",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to create session: {str(e)}"
            )
    
    async def _end_session(self, session_id: str) -> CommandResult:
        """End an execution session"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/sessions/{session_id}"
            response = await self.clients.delete_json(url)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message=f"Session ended: {session_id}",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to end session {session_id}: {str(e)}"
            )
    
    async def _test_execute(self) -> CommandResult:
        """Test code execution with a simple example"""
        try:
            start_time = time.time()
            
            # Test Python execution
            test_code = "print('Hello from Interpreter!')\nresult = 2 + 2\nprint(f'2 + 2 = {result}')"
            
            url = f"{self.base_url}/execute"
            payload = {
                "code": test_code,
                "language": "python"
            }
            
            response = await self.clients.post_json(url, payload)
            execution_time = time.time() - start_time
            
            test_result = {
                "execution_result": response,
                "test_passed": bool(response and response.get("success")),
                "output_length": len(response.get("output", "")) if response else 0
            }
            
            return CommandResult(
                success=True,
                data=test_result,
                message="Test execution completed",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to test code execution: {str(e)}"
            )
    
    async def _get_stats(self) -> CommandResult:
        """Get Interpreter service statistics"""
        try:
            start_time = time.time()
            
            # Get basic status
            status_response = await self.clients.get_json(f"{self.base_url}/status")
            
            # Try to get languages
            languages_response = await self.clients.get_json(f"{self.base_url}/languages")
            language_count = len(languages_response.get("languages", [])) if languages_response else 0
            
            # Try to get sessions
            sessions_response = await self.clients.get_json(f"{self.base_url}/sessions")
            session_count = len(sessions_response.get("sessions", [])) if sessions_response else 0
            
            execution_time = time.time() - start_time
            
            stats = {
                "status": status_response,
                "supported_languages": language_count,
                "active_sessions": session_count,
                "service_uptime": status_response.get("uptime", "unknown") if status_response else "unknown"
            }
            
            return CommandResult(
                success=True,
                data=stats,
                message="Interpreter statistics retrieved successfully",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to get Interpreter stats: {str(e)}"
            )
    
    def format_response(self, result: CommandResult, command: str) -> None:
        """Format and display the command result"""
        if not result.success:
            self.console.print(f"[red]❌ Error: {result.error}[/red]")
            return
        
        # Command-specific formatting
        if command == "status":
            self._format_status_response(result.data)
        elif command == "languages":
            self._format_languages_response(result.data)
        elif command == "execute":
            self._format_execution_response(result.data)
        elif command == "sessions":
            self._format_sessions_response(result.data)
        elif command == "test-execute":
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
            
        table = Table(title="⚡ Interpreter Status", border_style="green")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        for key, value in data.items():
            table.add_row(str(key), str(value))
        
        self.console.print(table)
    
    def _format_languages_response(self, data: Dict[str, Any]) -> None:
        """Format supported languages response"""
        languages = data.get("languages", [])
        if not languages:
            self.console.print("[yellow]📝 No languages available[/yellow]")
            return
        
        table = Table(title="📝 Supported Languages", border_style="blue")
        table.add_column("Language", style="cyan")
        table.add_column("Version", style="green")
        table.add_column("Features", style="yellow")
        table.add_column("Status", style="magenta")
        
        for lang in languages:
            if isinstance(lang, str):
                table.add_row(lang, "N/A", "N/A", "available")
            else:
                features = ", ".join(lang.get("features", [])) if lang.get("features") else "N/A"
                status_color = "green" if lang.get("status") == "available" else "red"
                
                table.add_row(
                    lang.get("name", "N/A"),
                    lang.get("version", "N/A"),
                    features[:40] + "..." if len(features) > 40 else features,
                    f"[{status_color}]{lang.get('status', 'unknown')}[/{status_color}]"
                )
        
        self.console.print(table)
        
        self.console.print(f"[dim]Total languages: {len(languages)}[/dim]")
    
    def _format_execution_response(self, data: Dict[str, Any]) -> None:
        """Format code execution response"""
        if not data:
            self.console.print("[yellow]⚡ No execution data[/yellow]")
            return
        
        success = data.get("success", False)
        output = data.get("output", "")
        error = data.get("error", "")
        language = data.get("language", "unknown")
        execution_time = data.get("execution_time", 0)
        
        # Show execution status
        status_color = "green" if success else "red"
        status_icon = "✅" if success else "❌"
        
        self.console.print(f"{status_icon} Execution [{status_color}]{'SUCCESS' if success else 'FAILED'}[/{status_color}] in {language} ({execution_time:.3f}s)")
        
        # Show output if available
        if output:
            self.console.print(Panel(
                output,
                title="📤 Output",
                border_style="green"
            ))
        
        # Show error if any
        if error:
            self.console.print(Panel(
                error,
                title="❌ Error",
                border_style="red"
            ))
        
        # Show session info if available
        session_id = data.get("session_id")
        if session_id:
            self.console.print(f"[dim]🔗 Session: {session_id}[/dim]")
    
    def _format_sessions_response(self, data: Dict[str, Any]) -> None:
        """Format sessions response"""
        sessions = data.get("sessions", [])
        if not sessions:
            self.console.print("[yellow]🔗 No active sessions[/yellow]")
            return
        
        table = Table(title="🔗 Active Sessions", border_style="cyan")
        table.add_column("Session ID", style="cyan")
        table.add_column("Language", style="green")
        table.add_column("Name", style="yellow")
        table.add_column("Created", style="dim")
        table.add_column("Status", style="magenta")
        
        for session in sessions:
            if isinstance(session, str):
                table.add_row(session, "N/A", "N/A", "N/A", "active")
            else:
                status_color = "green" if session.get("status") == "active" else "red"
                
                table.add_row(
                    session.get("id", "N/A"),
                    session.get("language", "N/A"),
                    session.get("name", "unnamed"),
                    session.get("created_at", "N/A"),
                    f"[{status_color}]{session.get('status', 'unknown')}[/{status_color}]"
                )
        
        self.console.print(table)
        
        self.console.print(f"[dim]Total sessions: {len(sessions)}[/dim]")
    
    def _format_test_response(self, data: Dict[str, Any]) -> None:
        """Format test execution response"""
        test_passed = data.get("test_passed", False)
        execution_result = data.get("execution_result", {})
        output_length = data.get("output_length", 0)
        
        test_color = "green" if test_passed else "red"
        test_icon = "✅" if test_passed else "❌"
        
        self.console.print(Panel.fit(
            f"🧪 Interpreter Test Results\n\n"
            f"{test_icon} Test Status: [{test_color}]{'PASSED' if test_passed else 'FAILED'}[/{test_color}]\n"
            f"📤 Output Length: {output_length} characters\n"
            f"⚡ Execution Success: {'Yes' if execution_result.get('success') else 'No'}\n"
            f"⏱️  Execution Time: {execution_result.get('execution_time', 0):.3f}s",
            title="Test Execution",
            border_style=test_color
        ))
        
        # Show output if available and reasonable length
        output = execution_result.get("output", "")
        if output and len(output) < 200:
            self.console.print(Panel(
                output,
                title="📤 Test Output",
                border_style="green"
            ))
    
    def _format_stats_response(self, data: Dict[str, Any]) -> None:
        """Format statistics response"""
        self.console.print(Panel.fit(
            f"📊 Interpreter Statistics\n\n"
            f"📝 Supported Languages: {data.get('supported_languages', 'N/A')}\n"
            f"🔗 Active Sessions: {data.get('active_sessions', 'N/A')}\n"
            f"⏰ Uptime: {data.get('service_uptime', 'N/A')}\n"
            f"🟢 Status: {data.get('status', {}).get('status', 'unknown') if data.get('status') else 'unknown'}",
            title="Interpreter Stats",
            border_style="green"
        ))
