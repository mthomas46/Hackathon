"""API utilities for CLI operations."""

from typing import Dict, Any, Optional, List
from rich.console import Console
import asyncio


class APIClient:
    """Wrapper for API client operations with error handling."""

    def __init__(self, clients, console: Console, timeout: int = 30):
        self.clients = clients
        self.console = console
        self.timeout = timeout

    async def get_json(self, endpoint: str, **params) -> Optional[Dict[str, Any]]:
        """Get JSON from API endpoint with error handling."""
        try:
            return await asyncio.wait_for(
                self.clients.get_json(endpoint, **params),
                timeout=self.timeout
            )
        except asyncio.TimeoutError:
            self.console.print(f"[red]Timeout getting {endpoint}[/red]")
            return None
        except Exception as e:
            self.console.print(f"[red]Error getting {endpoint}: {e}[/red]")
            return None

    async def post_json(self, endpoint: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Post JSON to API endpoint with error handling."""
        try:
            return await asyncio.wait_for(
                self.clients.post_json(endpoint, data),
                timeout=self.timeout
            )
        except asyncio.TimeoutError:
            self.console.print(f"[red]Timeout posting to {endpoint}[/red]")
            return None
        except Exception as e:
            self.console.print(f"[red]Error posting to {endpoint}: {e}[/red]")
            return None

    async def put_json(self, endpoint: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Put JSON to API endpoint with error handling."""
        try:
            return await asyncio.wait_for(
                self.clients.put_json(endpoint, data),
                timeout=self.timeout
            )
        except asyncio.TimeoutError:
            self.console.print(f"[red]Timeout putting to {endpoint}[/red]")
            return None
        except Exception as e:
            self.console.print(f"[red]Error putting to {endpoint}: {e}[/red]")
            return None

    async def delete(self, endpoint: str) -> bool:
        """Delete from API endpoint with error handling."""
        try:
            await asyncio.wait_for(
                self.clients.delete(endpoint),
                timeout=self.timeout
            )
            return True
        except asyncio.TimeoutError:
            self.console.print(f"[red]Timeout deleting {endpoint}[/red]")
            return False
        except Exception as e:
            self.console.print(f"[red]Error deleting {endpoint}: {e}[/red]")
            return False

    async def batch_get(self, endpoints: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """Batch get multiple endpoints."""
        results = {}
        for endpoint in endpoints:
            results[endpoint] = await self.get_json(endpoint)
        return results

    async def health_check(self, service_urls: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
        """Perform health checks on multiple services."""
        results = {}
        for service_name, url in service_urls.items():
            try:
                response = await self.get_json(url)
                if response and response.get('status') == 'healthy':
                    results[service_name] = {
                        'status': 'healthy',
                        'response': response
                    }
                else:
                    results[service_name] = {
                        'status': 'unhealthy',
                        'response': response
                    }
            except Exception as e:
                results[service_name] = {
                    'status': 'error',
                    'error': str(e)
                }
        return results

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        # Cleanup if needed
        pass
