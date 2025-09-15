"""Architecture Digitizer Manager module for CLI service.

Provides interactive management of architecture diagram digitization,
supporting both API-based fetching and file upload processing.
"""

from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.panel import Panel

from .shared_utils import (
    get_cli_clients,
    create_menu_table,
    add_menu_rows,
    print_panel,
    log_cli_metrics
)


class ArchitectureDigitizerManager:
    """Manager for architecture digitizer CLI operations."""

    def __init__(self, console: Console, clients, cache: Dict[str, Any] = None):
        self.console = console
        self.clients = clients
        self.cache = cache or {}

    async def architecture_digitizer_menu(self):
        """Main architecture digitizer menu."""
        while True:
            menu = create_menu_table("Architecture Digitizer", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Normalize from API (Miro, FigJam, Lucid, Confluence)"),
                ("2", "Upload & Normalize File"),
                ("3", "View Supported Systems"),
                ("4", "View Supported File Formats"),
                ("5", "View Digitization History"),
                ("b", "Back to Main Menu")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.normalize_from_api_menu()
            elif choice == "2":
                await self.upload_and_normalize_menu()
            elif choice == "3":
                await self.view_supported_systems()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "4":
                await self.view_supported_file_formats()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "5":
                await self.view_digitization_history()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def normalize_from_api_menu(self):
        """Menu for API-based diagram normalization."""
        while True:
            # Get supported systems from cache or API
            systems = await self._get_supported_systems()

            menu = create_menu_table("Normalize from API", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Miro Board"),
                ("2", "Figma FigJam"),
                ("3", "Lucidchart"),
                ("4", "Confluence Page"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select system[/bold green]")

            if choice == "1":
                await self.normalize_miro_board()
            elif choice == "2":
                await self.normalize_figjam_board()
            elif choice == "3":
                await self.normalize_lucid_board()
            elif choice == "4":
                await self.normalize_confluence_page()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def normalize_miro_board(self):
        """Normalize a Miro board."""
        self.console.print("\n[bold green]Normalize Miro Board[/bold green]")

        board_id = Prompt.ask("Miro Board ID")
        token = Prompt.ask("Miro API Token", password=True)

        if not Confirm.ask("Proceed with normalization?"):
            return

        try:
            with self.console.status("[bold green]Normalizing Miro board...") as status:
                response = await self.clients.post_json("architecture-digitizer/normalize", {
                    "system": "miro",
                    "board_id": board_id,
                    "token": token
                })

            self._display_normalization_result(response)

        except Exception as e:
            self.console.print(f"[red]Error normalizing Miro board: {e}[/red]")

    async def normalize_figjam_board(self):
        """Normalize a FigJam board."""
        self.console.print("\n[bold green]Normalize FigJam Board[/bold green]")

        board_id = Prompt.ask("FigJam File ID")
        token = Prompt.ask("Figma API Token", password=True)

        if not Confirm.ask("Proceed with normalization?"):
            return

        try:
            with self.console.status("[bold green]Normalizing FigJam board...") as status:
                response = await self.clients.post_json("architecture-digitizer/normalize", {
                    "system": "figjam",
                    "board_id": board_id,
                    "token": token
                })

            self._display_normalization_result(response)

        except Exception as e:
            self.console.print(f"[red]Error normalizing FigJam board: {e}[/red]")

    async def normalize_lucid_board(self):
        """Normalize a Lucid board."""
        self.console.print("\n[bold green]Normalize Lucid Board[/bold green]")

        board_id = Prompt.ask("Lucid Document ID")
        token = Prompt.ask("Lucid API Token", password=True)

        if not Confirm.ask("Proceed with normalization?"):
            return

        try:
            with self.console.status("[bold green]Normalizing Lucid document...") as status:
                response = await self.clients.post_json("architecture-digitizer/normalize", {
                    "system": "lucid",
                    "board_id": board_id,
                    "token": token
                })

            self._display_normalization_result(response)

        except Exception as e:
            self.console.print(f"[red]Error normalizing Lucid document: {e}[/red]")

    async def normalize_confluence_page(self):
        """Normalize a Confluence page."""
        self.console.print("\n[bold green]Normalize Confluence Page[/bold green]")

        page_id = Prompt.ask("Confluence Page ID")
        token = Prompt.ask("Confluence API Token", password=True)

        if not Confirm.ask("Proceed with normalization?"):
            return

        try:
            with self.console.status("[bold green]Normalizing Confluence page...") as status:
                response = await self.clients.post_json("architecture-digitizer/normalize", {
                    "system": "confluence",
                    "board_id": page_id,
                    "token": token
                })

            self._display_normalization_result(response)

        except Exception as e:
            self.console.print(f"[red]Error normalizing Confluence page: {e}[/red]")

    async def upload_and_normalize_menu(self):
        """Menu for file upload and normalization."""
        while True:
            # Get supported systems for file upload
            systems = await self._get_supported_systems()

            menu = create_menu_table("Upload & Normalize File", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Upload Miro Export (JSON)"),
                ("2", "Upload FigJam Export (JSON)"),
                ("3", "Upload Lucid Export (JSON)"),
                ("4", "Upload Confluence Export (XML/HTML)"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select system[/bold green]")

            if choice in ["1", "2", "3", "4"]:
                system_map = {
                    "1": ("miro", "json"),
                    "2": ("figjam", "json"),
                    "3": ("lucid", "json"),
                    "4": ("confluence", "xml")
                }
                system, file_format = system_map[choice]
                await self.upload_and_normalize_file(system, file_format)
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def upload_and_normalize_file(self, system: str, file_format: str):
        """Upload and normalize a file."""
        self.console.print(f"\n[bold green]Upload {system.title()} {file_format.upper()} File[/bold green]")

        file_path = Prompt.ask(f"Path to {file_format.upper()} file")

        if not file_path or not os.path.exists(file_path):
            self.console.print(f"[red]File not found: {file_path}[/red]")
            return

        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size > 10 * 1024 * 1024:  # 10MB limit
            self.console.print("[red]File too large. Maximum size is 10MB.[/red]")
            return

        if not Confirm.ask(f"Upload and normalize {os.path.basename(file_path)} ({file_size} bytes)?"):
            return

        try:
            # Read file content
            with open(file_path, 'rb') as f:
                file_content = f.read()

            with self.console.status(f"[bold green]Uploading and normalizing {system} file...") as status:
                # Create multipart form data
                import aiohttp
                from aiohttp import FormData

                data = FormData()
                data.add_field('file', file_content, filename=os.path.basename(file_path))
                data.add_field('system', system)
                data.add_field('file_format', file_format)

                # Use raw HTTP client for multipart upload
                async with aiohttp.ClientSession() as session:
                    url = f"{self.clients.base_url}/architecture-digitizer/normalize-file"
                    async with session.post(url, data=data) as resp:
                        if resp.status == 200:
                            response = await resp.json()
                            self._display_file_normalization_result(response)
                        else:
                            error_text = await resp.text()
                            self.console.print(f"[red]Upload failed: {error_text}[/red]")

        except Exception as e:
            self.console.print(f"[red]Error uploading file: {e}[/red]")

    async def view_supported_systems(self):
        """View supported diagram systems."""
        try:
            with self.console.status("[bold green]Fetching supported systems...") as status:
                response = await self.clients.get_json("architecture-digitizer/supported-systems")

            table = Table(title="Supported Diagram Systems")
            table.add_column("System", style="cyan")
            table.add_column("Description", style="white")
            table.add_column("Auth Type", style="green")

            for system in response.get("systems", []):
                table.add_row(
                    system.get("name", "").title(),
                    system.get("description", ""),
                    system.get("auth_type", "")
                )

            self.console.print(table)

        except Exception as e:
            self.console.print(f"[red]Error fetching supported systems: {e}[/red]")

    async def view_supported_file_formats(self):
        """View supported file formats for each system."""
        try:
            systems = ["miro", "figjam", "lucid", "confluence"]

            table = Table(title="Supported File Formats")
            table.add_column("System", style="cyan")
            table.add_column("Format", style="green")
            table.add_column("Description", style="white")
            table.add_column("Export Method", style="yellow")

            for system in systems:
                try:
                    response = await self.clients.get_json(f"architecture-digitizer/supported-file-formats/{system}")
                    for fmt in response.get("supported_formats", []):
                        table.add_row(
                            system.title(),
                            fmt.get("format", "").upper(),
                            fmt.get("description", ""),
                            fmt.get("export_method", "")
                        )
                except Exception:
                    # If API call fails, continue with next system
                    continue

            self.console.print(table)

        except Exception as e:
            self.console.print(f"[red]Error fetching file formats: {e}[/red]")

    async def view_digitization_history(self):
        """View recent digitization history."""
        # This would typically fetch from a history endpoint
        # For now, show a placeholder
        self.console.print("[yellow]Digitization history feature coming soon![/yellow]")
        self.console.print("[dim]This will show recent normalization operations and their results.[/dim]")

    def _display_normalization_result(self, response: Dict[str, Any]):
        """Display normalization result."""
        if response.get("success"):
            self.console.print(f"[green]✅ Successfully normalized {response.get('system')} diagram![/green]")

            data = response.get("data", {})
            components = data.get("components", [])
            connections = data.get("connections", [])

            self.console.print(f"📊 Components found: {len(components)}")
            self.console.print(f"🔗 Connections found: {len(connections)}")

            if components:
                table = Table(title="Components")
                table.add_column("Type", style="cyan")
                table.add_column("Name", style="white")

                for comp in components[:5]:  # Show first 5
                    table.add_row(comp.get("type", ""), comp.get("name", ""))

                if len(components) > 5:
                    table.add_row("...", f"[dim]+{len(components) - 5} more[/dim]")

                self.console.print(table)

        else:
            self.console.print(f"[red]❌ Normalization failed: {response.get('message', 'Unknown error')}[/red]")

    def _display_file_normalization_result(self, response: Dict[str, Any]):
        """Display file normalization result."""
        if response.get("success"):
            self.console.print(f"[green]✅ Successfully normalized {response.get('system')} file![/green]")
            self.console.print(f"📁 Filename: {response.get('filename')}")
            self.console.print(f"📄 Format: {response.get('file_format', '').upper()}")

            data = response.get("data", {})
            components = data.get("components", [])
            connections = data.get("connections", [])

            self.console.print(f"📊 Components found: {len(components)}")
            self.console.print(f"🔗 Connections found: {len(connections)}")

            if components:
                table = Table(title="Components")
                table.add_column("Type", style="cyan")
                table.add_column("Name", style="white")

                for comp in components[:5]:  # Show first 5
                    table.add_row(comp.get("type", ""), comp.get("name", ""))

                if len(components) > 5:
                    table.add_row("...", f"[dim]+{len(components) - 5} more[/dim]")

                self.console.print(table)

        else:
            self.console.print(f"[red]❌ File normalization failed: {response.get('message', 'Unknown error')}[/red]")

    async def _get_supported_systems(self) -> List[str]:
        """Get supported systems from cache or API."""
        cache_key = "architecture_digitizer.systems"

        # Try cache first
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if time.time() - cached['timestamp'] < 300:  # 5 min TTL
                return cached['data']

        # Fetch from API
        try:
            response = await self.clients.get_json("architecture-digitizer/supported-systems")
            systems = [s.get("name") for s in response.get("systems", [])]

            # Cache result
            self.cache[cache_key] = {
                'data': systems,
                'timestamp': time.time()
            }

            return systems
        except Exception:
            # Fallback to known systems
            return ["miro", "figjam", "lucid", "confluence"]


# Import time for timestamp operations
import time
import os
