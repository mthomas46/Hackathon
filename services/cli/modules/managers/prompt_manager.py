"""Prompt Management module for the CLI service.

This module contains prompt-related CLI commands and operations,
extracted from the main CLI service to improve maintainability.
"""

from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from services.shared.integrations.clients.clients import ServiceClients
from services.shared.auth.credentials import get_secret

from ..base.base_manager import BaseManager


class PromptManager(BaseManager):
    """Handle prompt management CLI operations."""

    def __init__(self, console: Console, clients: ServiceClients, cache: Optional[Dict[str, Any]] = None):
        super().__init__(console, clients, cache)

    async def get_main_menu(self) -> List[tuple[str, str]]:
        """Return the main menu items for prompt management."""
        return [
            ("1", "List Available Prompts"),
            ("2", "Search Prompts"),
            ("3", "Create New Prompt"),
            ("4", "Update Existing Prompt"),
            ("5", "Delete Prompt"),
            ("6", "View Prompt Details")
        ]

    async def handle_choice(self, choice: str) -> bool:
        """Handle menu choice selection."""
        if choice == "1":
            await self.list_prompts()
        elif choice == "2":
            await self.search_prompts()
        elif choice == "3":
            await self.create_prompt()
        elif choice == "4":
            await self.update_prompt()
        elif choice == "5":
            await self.delete_prompt()
        elif choice == "6":
            await self.view_prompt_details()
        else:
            return False
        return True

    async def prompt_management_menu(self):
        """Prompt management submenu with enhanced interactive experience."""
        await self.run_menu_loop("Prompt Management", use_interactive=True)

    async def list_prompts(self):
        """List all prompts."""
        try:
            url = f"{self.clients.prompt_store_url()}/prompts"
            response = await self.clients.get_json(url)
            prompts = response.get("prompts", [])

            if not prompts:
                self.console.print("[yellow]No prompts found.[/yellow]")
                return

            table = create_prompt_table(prompts)
            self.console.print(table)

        except Exception as e:
            self.console.print(f"[red]Error listing prompts: {e}[/red]")

    async def create_prompt(self):
        """Create a new prompt."""
        self.console.print("\n[bold green]Create New Prompt[/bold green]")

        name = Prompt.ask("Prompt name")
        category = Prompt.ask("Category", default="custom")
        description = Prompt.ask("Description", default="")
        content = Prompt.ask("Prompt content")

        # Extract variables from content
        variables = extract_variables_from_content(content)

        if variables:
            self.console.print(f"Found variables: {', '.join(variables)}")
        else:
            self.console.print("[yellow]No variables found in prompt content.[/yellow]")

        tags_input = Prompt.ask("Tags (comma-separated)", default="")
        tags = parse_tags_input(tags_input)

        # Optionally use a default author if available (example of creds/env usage)
        default_author = get_secret("PROMPT_AUTHOR") or ""
        author = Prompt.ask("Author (optional)", default=default_author)

        # Confirm creation
        confirm = Confirm.ask("Create this prompt?")
        if not confirm:
            self.console.print("[yellow]Prompt creation cancelled.[/yellow]")
            return

        try:
            validate_prompt_data(name, category, content)

            payload = {
                "name": name,
                "category": category,
                "description": description,
                "content": content,
                "variables": variables,
                "tags": tags,
                **({"author": author} if author else {})
            }

            url = f"{self.clients.prompt_store_url()}/prompts"
            response = await self.clients.post_json(url, payload)
            self.console.print("[green]✅ Prompt created successfully![/green]")
            self.console.print(f"ID: {response.get('id')}")
            self.console.print(f"Version: {response.get('version')}")

        except Exception as e:
            self.console.print(f"[red]Error creating prompt: {e}[/red]")

    async def view_prompt(self):
        """View prompt details."""
        category = Prompt.ask("Category")
        name = Prompt.ask("Prompt name")

        try:
            url = f"{self.clients.prompt_store_url()}/prompts/search/{category}/{name}"
            response = await self.clients.get_json(url)
            content = format_prompt_details(response)
            print_panel(self.console, content, border_style="cyan")

        except Exception as e:
            self.console.print(f"[red]Error viewing prompt: {e}[/red]")

    async def update_prompt(self):
        """Update an existing prompt."""
        self.console.print("\n[bold yellow]Update Prompt[/bold yellow]")

        # First, let user select a prompt
        await self.list_prompts()

        prompt_id = Prompt.ask("Enter prompt ID to update")

        try:
            # Get current prompt data
            url = f"{self.clients.prompt_store_url()}/prompts/{prompt_id}"
            response = await self.clients.get_json(url)
            current = response.get("prompt", {})

            # Get updated values
            name = Prompt.ask("New name", default=current.get("name", ""))
            category = Prompt.ask("New category", default=current.get("category", ""))
            description = Prompt.ask("New description", default=current.get("description", ""))
            content = Prompt.ask("New content", default=current.get("content", ""))

            variables = extract_variables_from_content(content)
            tags_input = Prompt.ask("New tags (comma-separated)", default="")
            tags = parse_tags_input(tags_input)

            # Confirm update
            confirm = Confirm.ask("Update this prompt?")
            if not confirm:
                self.console.print("[yellow]Prompt update cancelled.[/yellow]")
                return

            validate_prompt_data(name, category, content)

            payload = {
                "name": name,
                "category": category,
                "description": description,
                "content": content,
                "variables": variables,
                "tags": tags
            }

            url = f"{self.clients.prompt_store_url()}/prompts/{prompt_id}"
            response = await self.clients.put_json(url, payload)
            self.console.print("[green]✅ Prompt updated successfully![/green]")

        except Exception as e:
            self.console.print(f"[red]Error updating prompt: {e}[/red]")

    async def delete_prompt(self):
        """Delete a prompt."""
        self.console.print("\n[bold red]Delete Prompt[/bold red]")

        # First, let user select a prompt
        await self.list_prompts()

        prompt_id = Prompt.ask("Enter prompt ID to delete")

        # Confirm deletion
        confirm = Confirm.ask("Are you sure you want to delete this prompt?")
        if not confirm:
            self.console.print("[yellow]Prompt deletion cancelled.[/yellow]")
            return

        try:
            url = f"{self.clients.prompt_store_url()}/prompts/{prompt_id}"
            response = await self.clients.delete_json(url)
            self.console.print("[green]✅ Prompt deleted successfully![/green]")

        except Exception as e:
            self.console.print(f"[red]Error deleting prompt: {e}[/red]")

    async def fork_prompt(self):
        """Fork an existing prompt."""
        self.console.print("\n[bold blue]Fork Prompt[/bold blue]")

        # First, let user select a prompt
        await self.list_prompts()

        prompt_id = Prompt.ask("Enter prompt ID to fork")

        try:
            # Get current prompt data
            url = f"{self.clients.prompt_store_url()}/prompts/{prompt_id}"
            response = await self.clients.get_json(url)
            current = response.get("prompt", {})

            # Get fork details
            name = Prompt.ask("New prompt name", default=f"{current.get('name', '')}_fork")
            category = Prompt.ask("New category", default=current.get("category", ""))
            description = Prompt.ask("New description", default=f"Forked from {current.get('name', '')}")

            # Confirm fork
            confirm = Confirm.ask("Fork this prompt?")
            if not confirm:
                self.console.print("[yellow]Prompt fork cancelled.[/yellow]")
                return

            payload = {
                "name": name,
                "category": category,
                "description": description,
                "content": current.get("content", ""),
                "variables": current.get("variables", []),
                "tags": current.get("tags", []) + ["forked"]
            }

            url = f"{self.clients.prompt_store_url()}/prompts"
            response = await self.clients.post_json(url, payload)
            self.console.print("[green]✅ Prompt forked successfully![/green]")
            self.console.print(f"New ID: {response.get('id')}")

        except Exception as e:
            self.console.print(f"[red]Error forking prompt: {e}[/red]")

    async def search_prompts(self):
        """Search prompts."""
        query = Prompt.ask("Search query (category or tags)")

        try:
            url = f"{self.clients.prompt_store_url()}/prompts"
            response = await self.clients.get_json(url, params={"tags": query})
            prompts = response.get("prompts", [])

            if not prompts:
                self.console.print("[yellow]No prompts found matching your query.[/yellow]")
                return

            table = create_search_results_table(query, prompts)
            self.console.print(table)

        except Exception as e:
            self.console.print(f"[red]Error searching prompts: {e}[/red]")
