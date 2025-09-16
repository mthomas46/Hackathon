"""Source Agent Manager module for CLI service.

Provides power-user operations for source agent including
document fetching, normalization, and code analysis.
"""

from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.panel import Panel

from ...base.base_manager import BaseManager


class SourceAgentManager(BaseManager):
    """Manager for source agent power-user operations."""

    def __init__(self, console: Console, clients, cache: Optional[Dict[str, Any]] = None):
        super().__init__(console, clients, cache)

    async def get_main_menu(self) -> List[tuple[str, str]]:
        """Return the main menu items for source agent operations."""
        return [
            ("1", "Document Fetching (GitHub, Jira, Confluence)"),
            ("2", "Data Normalization"),
            ("3", "Code Analysis & Processing"),
            ("4", "Source Management"),
            ("5", "Integration Status")
        ]

    async def handle_choice(self, choice: str) -> bool:
        """Handle a menu choice. Return True to continue, False to exit."""
        if choice == "1":
            await self.document_fetching_menu()
        elif choice == "2":
            await self.data_normalization_menu()
        elif choice == "3":
            await self.code_analysis_menu()
        elif choice == "4":
            await self.source_management_menu()
        elif choice == "5":
            await self.integration_status_menu()
        else:
            self.display.show_error("Invalid option. Please try again.")
        return True

    async def document_fetching_menu(self):
        """Document fetching submenu."""
        while True:
            menu = create_menu_table("Document Fetching", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Fetch from GitHub"),
                ("2", "Fetch from Jira"),
                ("3", "Fetch from Confluence"),
                ("4", "Bulk Fetch from Multiple Sources"),
                ("5", "View Fetch History"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.fetch_github()
            elif choice == "2":
                await self.fetch_jira()
            elif choice == "3":
                await self.fetch_confluence()
            elif choice == "4":
                await self.bulk_fetch()
            elif choice == "5":
                await self.view_fetch_history()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def fetch_github(self):
        """Fetch documents from GitHub."""
        try:
            repo_url = Prompt.ask("[bold cyan]GitHub repository URL[/bold cyan]")
            branch = Prompt.ask("[bold cyan]Branch[/bold cyan]", default="main")
            include_docs = Confirm.ask("[bold cyan]Include documentation files?[/bold cyan]", default=True)
            include_code = Confirm.ask("[bold cyan]Include code files?[/bold cyan]", default=False)

            fetch_config = {
                "url": repo_url,
                "branch": branch,
                "include_patterns": [],
                "exclude_patterns": []
            }

            if include_docs:
                fetch_config["include_patterns"].extend(["*.md", "*.rst", "*.txt", "docs/**"])
            if include_code:
                fetch_config["include_patterns"].extend(["*.py", "*.js", "*.java", "*.go", "src/**"])

            with self.console.status(f"[bold green]Fetching from GitHub: {repo_url}...") as status:
                response = await self.clients.post_json("source-agent/docs/fetch", fetch_config)

            if response.get("fetch_id"):
                self.console.print(f"[green]✅ GitHub fetch started: {response['fetch_id']}[/green]")
                self.console.print(f"[yellow]Files to fetch: {response.get('file_count', 0)}[/yellow]")
            else:
                self.console.print("[red]❌ Failed to start GitHub fetch[/red]")

        except Exception as e:
            self.console.print(f"[red]Error fetching from GitHub: {e}[/red]")

    async def fetch_jira(self):
        """Fetch documents from Jira."""
        try:
            jira_url = Prompt.ask("[bold cyan]Jira instance URL[/bold cyan]")
            project_key = Prompt.ask("[bold cyan]Project key[/bold cyan]")
            issue_filter = Prompt.ask("[bold cyan]Issue filter (JQL)[/bold cyan]", default="")
            include_comments = Confirm.ask("[bold cyan]Include comments?[/bold cyan]", default=True)
            include_attachments = Confirm.ask("[bold cyan]Include attachments?[/bold cyan]", default=False)

            fetch_config = {
                "url": jira_url,
                "project_key": project_key,
                "filter": issue_filter,
                "include_comments": include_comments,
                "include_attachments": include_attachments
            }

            with self.console.status(f"[bold green]Fetching from Jira: {project_key}...") as status:
                response = await self.clients.post_json("source-agent/docs/fetch", fetch_config)

            if response.get("fetch_id"):
                self.console.print(f"[green]✅ Jira fetch started: {response['fetch_id']}[/green]")
                self.console.print(f"[yellow]Issues to fetch: {response.get('issue_count', 0)}[/yellow]")
            else:
                self.console.print("[red]❌ Failed to start Jira fetch[/red]")

        except Exception as e:
            self.console.print(f"[red]Error fetching from Jira: {e}[/red]")

    async def fetch_confluence(self):
        """Fetch documents from Confluence."""
        try:
            confluence_url = Prompt.ask("[bold cyan]Confluence instance URL[/bold cyan]")
            space_key = Prompt.ask("[bold cyan]Space key[/bold cyan]")
            parent_page = Prompt.ask("[bold cyan]Parent page ID (optional)[/bold cyan]", default="")
            include_children = Confirm.ask("[bold cyan]Include child pages?[/bold cyan]", default=True)

            fetch_config = {
                "url": confluence_url,
                "space_key": space_key,
                "include_children": include_children
            }

            if parent_page:
                fetch_config["parent_page_id"] = parent_page

            with self.console.status(f"[bold green]Fetching from Confluence: {space_key}...") as status:
                response = await self.clients.post_json("source-agent/docs/fetch", fetch_config)

            if response.get("fetch_id"):
                self.console.print(f"[green]✅ Confluence fetch started: {response['fetch_id']}[/green]")
                self.console.print(f"[yellow]Pages to fetch: {response.get('page_count', 0)}[/yellow]")
            else:
                self.console.print("[red]❌ Failed to start Confluence fetch[/red]")

        except Exception as e:
            self.console.print(f"[red]Error fetching from Confluence: {e}[/red]")

    async def bulk_fetch(self):
        """Bulk fetch from multiple sources."""
        try:
            sources_input = Prompt.ask("[bold cyan]Sources configuration (JSON)[/bold cyan]")
            import json
            sources = json.loads(sources_input)

            confirm = Confirm.ask(f"[bold yellow]This will fetch from {len(sources)} sources. Continue?[/bold yellow]")

            if confirm:
                with self.console.status("[bold green]Starting bulk fetch...") as status:
                    response = await self.clients.post_json("source-agent/docs/bulk-fetch", {
                        "sources": sources
                    })

                if response.get("bulk_fetch_id"):
                    self.console.print(f"[green]✅ Bulk fetch started: {response['bulk_fetch_id']}[/green]")
                    self.console.print(f"[yellow]Total items to fetch: {response.get('total_items', 0)}[/yellow]")
                else:
                    self.console.print("[red]❌ Failed to start bulk fetch[/red]")
            else:
                self.console.print("[yellow]Bulk fetch cancelled.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error starting bulk fetch: {e}[/red]")

    async def view_fetch_history(self):
        """View fetch history."""
        try:
            limit = Prompt.ask("[bold cyan]Limit[/bold cyan]", default="20")

            with self.console.status("[bold green]Fetching fetch history...") as status:
                response = await self.clients.get_json(f"source-agent/fetches?limit={limit}")

            if response.get("fetches"):
                table = Table(title="Fetch History")
                table.add_column("ID", style="cyan")
                table.add_column("Source", style="green")
                table.add_column("Type", style="yellow")
                table.add_column("Status", style="magenta")
                table.add_column("Items", style="white")
                table.add_column("Started", style="blue")

                for fetch in response["fetches"]:
                    status_color = {
                        "completed": "green",
                        "running": "yellow",
                        "failed": "red",
                        "pending": "blue"
                    }.get(fetch.get("status", "unknown"), "white")

                    table.add_row(
                        fetch.get("id", "N/A")[:8],
                        fetch.get("source_url", "N/A")[:30],
                        fetch.get("source_type", "unknown"),
                        f"[{status_color}]{fetch.get('status', 'unknown')}[/{status_color}]",
                        str(fetch.get("items_fetched", 0)),
                        fetch.get("started_at", "unknown")[:19]
                    )

                self.console.print(table)
            else:
                self.console.print("[yellow]No fetch history found.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error fetching fetch history: {e}[/red]")

    async def data_normalization_menu(self):
        """Data normalization submenu."""
        while True:
            menu = create_menu_table("Data Normalization", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Normalize Fetched Data"),
                ("2", "View Normalization Rules"),
                ("3", "Custom Normalization"),
                ("4", "Normalization History"),
                ("5", "Validate Normalized Data"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.normalize_data()
            elif choice == "2":
                await self.view_normalization_rules()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "3":
                await self.custom_normalization()
            elif choice == "4":
                await self.normalization_history()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "5":
                await self.validate_normalized_data()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def normalize_data(self):
        """Normalize fetched data."""
        try:
            fetch_id = Prompt.ask("[bold cyan]Fetch ID to normalize[/bold cyan]")
            normalization_type = Prompt.ask("[bold cyan]Normalization type[/bold cyan]",
                                          choices=["standard", "custom", "minimal"], default="standard")

            with self.console.status(f"[bold green]Normalizing data from fetch {fetch_id}...") as status:
                response = await self.clients.post_json("source-agent/normalize", {
                    "fetch_id": fetch_id,
                    "normalization_type": normalization_type
                })

            if response.get("normalization_id"):
                self.console.print(f"[green]✅ Data normalization started: {response['normalization_id']}[/green]")
                self.console.print(f"[yellow]Items to normalize: {response.get('item_count', 0)}[/yellow]")
            else:
                self.console.print("[red]❌ Failed to start data normalization[/red]")

        except Exception as e:
            self.console.print(f"[red]Error starting data normalization: {e}[/red]")

    async def view_normalization_rules(self):
        """View normalization rules."""
        try:
            with self.console.status("[bold green]Fetching normalization rules...") as status:
                response = await self.clients.get_json("source-agent/normalization/rules")

            if response.get("rules"):
                content = "[bold]Normalization Rules[/bold]\n\n"

                for rule_set in response["rules"]:
                    content += f"[bold]{rule_set.get('name', 'Unknown Rule Set')}:[/bold]\n"
                    content += f"  Description: {rule_set.get('description', 'No description')}\n"
                    content += f"  Applies to: {', '.join(rule_set.get('applies_to', []))}\n\n"

                    if rule_set.get("rules"):
                        content += "  Rules:\n"
                        for rule in rule_set["rules"][:5]:  # Show first 5 rules
                            content += f"    • {rule.get('name', 'Unknown')}: {rule.get('description', 'No description')}\n"
                        if len(rule_set["rules"]) > 5:
                            content += f"    ... and {len(rule_set['rules']) - 5} more rules\n"

                    content += "\n"

                print_panel(self.console, content, border_style="blue")
            else:
                self.console.print("[yellow]No normalization rules available.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error fetching normalization rules: {e}[/red]")

    async def custom_normalization(self):
        """Custom normalization."""
        try:
            fetch_id = Prompt.ask("[bold cyan]Fetch ID[/bold cyan]")
            rules_input = Prompt.ask("[bold cyan]Custom rules (JSON)[/bold cyan]")
            import json
            custom_rules = json.loads(rules_input)

            with self.console.status(f"[bold green]Applying custom normalization to fetch {fetch_id}...") as status:
                response = await self.clients.post_json("source-agent/normalize/custom", {
                    "fetch_id": fetch_id,
                    "custom_rules": custom_rules
                })

            if response.get("normalization_id"):
                self.console.print(f"[green]✅ Custom normalization started: {response['normalization_id']}[/green]")
            else:
                self.console.print("[red]❌ Failed to start custom normalization[/red]")

        except Exception as e:
            self.console.print(f"[red]Error starting custom normalization: {e}[/red]")

    async def normalization_history(self):
        """Normalization history."""
        try:
            limit = Prompt.ask("[bold cyan]Limit[/bold cyan]", default="20")

            with self.console.status("[bold green]Fetching normalization history...") as status:
                response = await self.clients.get_json(f"source-agent/normalizations?limit={limit}")

            if response.get("normalizations"):
                table = Table(title="Normalization History")
                table.add_column("ID", style="cyan")
                table.add_column("Fetch ID", style="green")
                table.add_column("Type", style="yellow")
                table.add_column("Status", style="magenta")
                table.add_column("Items", style="white")
                table.add_column("Completed", style="blue")

                for norm in response["normalizations"]:
                    status_color = {
                        "completed": "green",
                        "running": "yellow",
                        "failed": "red",
                        "pending": "blue"
                    }.get(norm.get("status", "unknown"), "white")

                    table.add_row(
                        norm.get("id", "N/A")[:8],
                        norm.get("fetch_id", "N/A")[:8],
                        norm.get("normalization_type", "unknown"),
                        f"[{status_color}]{norm.get('status', 'unknown')}[/{status_color}]",
                        str(norm.get("items_processed", 0)),
                        norm.get("completed_at", "unknown")[:19] if norm.get("completed_at") else "running"
                    )

                self.console.print(table)
            else:
                self.console.print("[yellow]No normalization history found.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error fetching normalization history: {e}[/red]")

    async def validate_normalized_data(self):
        """Validate normalized data."""
        try:
            normalization_id = Prompt.ask("[bold cyan]Normalization ID[/bold cyan]")

            with self.console.status(f"[bold green]Validating normalized data {normalization_id}...") as status:
                response = await self.clients.post_json("source-agent/normalize/validate", {
                    "normalization_id": normalization_id
                })

            if response.get("validation"):
                validation = response["validation"]
                content = f"""
[bold]Normalization Validation Results[/bold]

Normalization ID: {normalization_id}

Validation Status: {'✅ PASSED' if validation.get('passed') else '❌ FAILED'}

Summary:
  Total Items: {validation.get('total_items', 0)}
  Valid Items: {validation.get('valid_items', 0)}
  Invalid Items: {validation.get('invalid_items', 0)}
  Success Rate: {validation.get('success_rate', 0):.1f}%

Issues Found:
"""
                if validation.get("issues"):
                    for issue in validation["issues"][:10]:  # Show first 10 issues
                        content += f"  • {issue.get('type', 'Unknown')}: {issue.get('description', 'No description')}\n"
                    if len(validation["issues"]) > 10:
                        content += f"  ... and {len(validation['issues']) - 10} more issues\n"
                else:
                    content += "  No issues found ✅\n"

                print_panel(self.console, content, border_style="green" if validation.get('passed') else "red")
            else:
                self.console.print("[red]❌ Failed to validate normalized data[/red]")

        except Exception as e:
            self.console.print(f"[red]Error validating normalized data: {e}[/red]")

    async def code_analysis_menu(self):
        """Code analysis submenu."""
        while True:
            menu = create_menu_table("Code Analysis", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Analyze Repository Code"),
                ("2", "Language-Specific Analysis"),
                ("3", "Security Analysis"),
                ("4", "Performance Analysis"),
                ("5", "Analysis History"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.analyze_repository_code()
            elif choice == "2":
                await self.language_specific_analysis()
            elif choice == "3":
                await self.security_analysis()
            elif choice == "4":
                await self.performance_analysis()
            elif choice == "5":
                await self.analysis_history()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def analyze_repository_code(self):
        """Analyze repository code."""
        try:
            repo_url = Prompt.ask("[bold cyan]Repository URL[/bold cyan]")
            analysis_types = Prompt.ask("[bold cyan]Analysis types (comma-separated)[/bold cyan]",
                                      default="structure,complexity,patterns")

            analysis_list = [t.strip() for t in analysis_types.split(",")]

            with self.console.status(f"[bold green]Analyzing code from {repo_url}...") as status:
                response = await self.clients.post_json("source-agent/code/analyze", {
                    "repository_url": repo_url,
                    "analysis_types": analysis_list
                })

            if response.get("analysis_id"):
                self.console.print(f"[green]✅ Code analysis started: {response['analysis_id']}[/green]")
                self.console.print(f"[yellow]Files to analyze: {response.get('file_count', 0)}[/yellow]")
            else:
                self.console.print("[red]❌ Failed to start code analysis[/red]")

        except Exception as e:
            self.console.print(f"[red]Error starting code analysis: {e}[/red]")

    async def language_specific_analysis(self):
        """Language-specific analysis."""
        try:
            language = Prompt.ask("[bold cyan]Programming language[/bold cyan]",
                                choices=["python", "javascript", "java", "go", "rust", "cpp"])
            analysis_scope = Prompt.ask("[bold cyan]Analysis scope[/bold cyan]",
                                      choices=["files", "functions", "classes", "modules"], default="files")

            with self.console.status(f"[bold green]Running {language} {analysis_scope} analysis...") as status:
                response = await self.clients.post_json("source-agent/code/analyze/language", {
                    "language": language,
                    "scope": analysis_scope
                })

            if response.get("analysis_id"):
                self.console.print(f"[green]✅ {language.title()} analysis started: {response['analysis_id']}[/green]")
            else:
                self.console.print(f"[red]❌ Failed to start {language} analysis[/red]")

        except Exception as e:
            self.console.print(f"[red]Error starting language-specific analysis: {e}[/red]")

    async def security_analysis(self):
        """Security analysis."""
        try:
            target = Prompt.ask("[bold cyan]Analysis target[/bold cyan]",
                              choices=["repository", "files", "dependencies"], default="repository")

            with self.console.status(f"[bold green]Running security analysis on {target}...") as status:
                response = await self.clients.post_json("source-agent/code/security-scan", {
                    "target": target
                })

            if response.get("analysis_id"):
                self.console.print(f"[green]✅ Security analysis started: {response['analysis_id']}[/green]")
                self.console.print(f"[yellow]Vulnerabilities found: {response.get('vulnerability_count', 0)}[/yellow]")
            else:
                self.console.print("[red]❌ Failed to start security analysis[/red]")

        except Exception as e:
            self.console.print(f"[red]Error starting security analysis: {e}[/red]")

    async def performance_analysis(self):
        """Performance analysis."""
        try:
            analysis_target = Prompt.ask("[bold cyan]Analysis target[/bold cyan]",
                                       choices=["code", "queries", "operations"], default="code")

            with self.console.status(f"[bold green]Running performance analysis on {analysis_target}...") as status:
                response = await self.clients.post_json("source-agent/code/performance", {
                    "target": analysis_target
                })

            if response.get("analysis_id"):
                self.console.print(f"[green]✅ Performance analysis started: {response['analysis_id']}[/green]")
            else:
                self.console.print("[red]❌ Failed to start performance analysis[/red]")

        except Exception as e:
            self.console.print(f"[red]Error starting performance analysis: {e}[/red]")

    async def analysis_history(self):
        """Analysis history."""
        try:
            limit = Prompt.ask("[bold cyan]Limit[/bold cyan]", default="20")

            with self.console.status("[bold green]Fetching analysis history...") as status:
                response = await self.clients.get_json(f"source-agent/analyses?limit={limit}")

            if response.get("analyses"):
                table = Table(title="Code Analysis History")
                table.add_column("ID", style="cyan")
                table.add_column("Type", style="green")
                table.add_column("Target", style="yellow")
                table.add_column("Status", style="magenta")
                table.add_column("Findings", style="white")
                table.add_column("Completed", style="blue")

                for analysis in response["analyses"]:
                    status_color = {
                        "completed": "green",
                        "running": "yellow",
                        "failed": "red",
                        "pending": "blue"
                    }.get(analysis.get("status", "unknown"), "white")

                    table.add_row(
                        analysis.get("id", "N/A")[:8],
                        analysis.get("analysis_type", "unknown"),
                        analysis.get("target", "unknown")[:30],
                        f"[{status_color}]{analysis.get('status', 'unknown')}[/{status_color}]",
                        str(analysis.get("findings_count", 0)),
                        analysis.get("completed_at", "unknown")[:19] if analysis.get("completed_at") else "running"
                    )

                self.console.print(table)
            else:
                self.console.print("[yellow]No analysis history found.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error fetching analysis history: {e}[/red]")

    async def source_management_menu(self):
        """Source management submenu."""
        while True:
            menu = create_menu_table("Source Management", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "List Configured Sources"),
                ("2", "Add New Source"),
                ("3", "Update Source Configuration"),
                ("4", "Remove Source"),
                ("5", "Test Source Connection"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.list_sources()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "2":
                await self.add_source()
            elif choice == "3":
                await self.update_source()
            elif choice == "4":
                await self.remove_source()
            elif choice == "5":
                await self.test_source_connection()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def list_sources(self):
        """List configured sources."""
        try:
            with self.console.status("[bold green]Fetching configured sources...") as status:
                response = await self.clients.get_json("source-agent/sources")

            if response.get("sources"):
                table = Table(title="Configured Sources")
                table.add_column("ID", style="cyan")
                table.add_column("Type", style="green")
                table.add_column("URL/Name", style="yellow")
                table.add_column("Status", style="magenta")
                table.add_column("Last Sync", style="blue")

                for source in response["sources"]:
                    status_color = {
                        "active": "green",
                        "inactive": "red",
                        "error": "red",
                        "syncing": "yellow"
                    }.get(source.get("status", "unknown"), "white")

                    table.add_row(
                        source.get("id", "N/A")[:8],
                        source.get("type", "unknown"),
                        source.get("url", source.get("name", "unknown"))[:40],
                        f"[{status_color}]{source.get('status', 'unknown')}[/{status_color}]",
                        source.get("last_sync", "never")[:19]
                    )

                self.console.print(table)
            else:
                self.console.print("[yellow]No sources configured.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error fetching sources: {e}[/red]")

    async def add_source(self):
        """Add new source."""
        try:
            source_type = Prompt.ask("[bold cyan]Source type[/bold cyan]",
                                   choices=["github", "jira", "confluence", "filesystem", "database"])
            source_url = Prompt.ask("[bold cyan]Source URL or identifier[/bold cyan]")

            config = {
                "type": source_type,
                "url": source_url
            }

            # Type-specific configuration
            if source_type == "github":
                config["token"] = Prompt.ask("[bold cyan]GitHub token[/bold cyan]")
                config["branch"] = Prompt.ask("[bold cyan]Default branch[/bold cyan]", default="main")
            elif source_type == "jira":
                config["username"] = Prompt.ask("[bold cyan]Jira username[/bold cyan]")
                config["api_token"] = Prompt.ask("[bold cyan]Jira API token[/bold cyan]")
            elif source_type == "confluence":
                config["username"] = Prompt.ask("[bold cyan]Confluence username[/bold cyan]")
                config["api_token"] = Prompt.ask("[bold cyan]Confluence API token[/bold cyan]")

            with self.console.status(f"[bold green]Adding {source_type} source...") as status:
                response = await self.clients.post_json("source-agent/sources", config)

            if response.get("source_id"):
                self.console.print(f"[green]✅ Source added successfully: {response['source_id']}[/green]")
            else:
                self.console.print("[red]❌ Failed to add source[/red]")

        except Exception as e:
            self.console.print(f"[red]Error adding source: {e}[/red]")

    async def update_source(self):
        """Update source configuration."""
        try:
            source_id = Prompt.ask("[bold cyan]Source ID[/bold cyan]")
            field = Prompt.ask("[bold cyan]Field to update[/bold cyan]")
            new_value = Prompt.ask(f"[bold cyan]New {field} value[/bold cyan]")

            with self.console.status(f"[bold green]Updating source {source_id}...") as status:
                response = await self.clients.put_json(f"source-agent/sources/{source_id}", {
                    field: new_value
                })

            if response.get("updated"):
                self.console.print(f"[green]✅ Source {source_id} updated successfully[/green]")
            else:
                self.console.print("[red]❌ Failed to update source[/red]")

        except Exception as e:
            self.console.print(f"[red]Error updating source: {e}[/red]")

    async def remove_source(self):
        """Remove source."""
        try:
            source_id = Prompt.ask("[bold cyan]Source ID[/bold cyan]")
            confirm = Confirm.ask(f"[bold red]Are you sure you want to remove source {source_id}?[/bold red]")

            if confirm:
                with self.console.status(f"[bold green]Removing source {source_id}...") as status:
                    response = await self.clients.delete_json(f"source-agent/sources/{source_id}")

                if response.get("removed"):
                    self.console.print(f"[green]✅ Source {source_id} removed successfully[/green]")
                else:
                    self.console.print("[red]❌ Failed to remove source[/red]")
            else:
                self.console.print("[yellow]Source removal cancelled.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error removing source: {e}[/red]")

    async def test_source_connection(self):
        """Test source connection."""
        try:
            source_id = Prompt.ask("[bold cyan]Source ID[/bold cyan]")

            with self.console.status(f"[bold green]Testing connection to source {source_id}...") as status:
                response = await self.clients.post_json(f"source-agent/sources/{source_id}/test", {})

            if response.get("connection_test"):
                test_result = response["connection_test"]
                content = f"""
[bold]Connection Test Results[/bold]

Source ID: {source_id}
Status: {'✅ CONNECTED' if test_result.get('connected') else '❌ FAILED'}

Response Time: {test_result.get('response_time_ms', 0):.2f} ms
Error: {test_result.get('error', 'None')}

Details:
"""
                if test_result.get("details"):
                    for key, value in test_result["details"].items():
                        content += f"  {key}: {value}\n"

                print_panel(self.console, content, border_style="green" if test_result.get('connected') else "red")
            else:
                self.console.print("[red]❌ Connection test failed[/red]")

        except Exception as e:
            self.console.print(f"[red]Error testing source connection: {e}[/red]")

    async def integration_status_menu(self):
        """Integration status submenu."""
        while True:
            menu = create_menu_table("Integration Status", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Source Agent Health"),
                ("2", "Integration Metrics"),
                ("3", "Active Connections"),
                ("4", "Error Logs"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.source_agent_health()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "2":
                await self.integration_metrics()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "3":
                await self.active_connections()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "4":
                await self.error_logs()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def source_agent_health(self):
        """Source agent health."""
        try:
            with self.console.status("[bold green]Checking source agent health...") as status:
                response = await self.clients.get_json("source-agent/health")

            if response.get("health"):
                health = response["health"]
                content = f"""
[bold]Source Agent Health[/bold]

Overall Status: {'✅ HEALTHY' if health.get('healthy') else '❌ UNHEALTHY'}

Services:
"""
                if health.get("services"):
                    for service, service_health in health["services"].items():
                        status_icon = "✅" if service_health.get("healthy") else "❌"
                        content += f"  {status_icon} {service}: {service_health.get('status', 'unknown')}\n"

                content += f"""
Metrics:
  Active Connections: {health.get('active_connections', 0)}
  Queued Tasks: {health.get('queued_tasks', 0)}
  Processed Today: {health.get('processed_today', 0)}

Last Health Check: {health.get('last_check', 'unknown')}
"""
                print_panel(self.console, content, border_style="green" if health.get('healthy') else "red")
            else:
                self.console.print("[red]Unable to retrieve source agent health.[/red]")

        except Exception as e:
            self.console.print(f"[red]Error checking source agent health: {e}[/red]")

    async def integration_metrics(self):
        """Integration metrics."""
        try:
            with self.console.status("[bold green]Fetching integration metrics...") as status:
                response = await self.clients.get_json("source-agent/metrics")

            if response.get("metrics"):
                metrics = response["metrics"]
                content = f"""
[bold]Integration Metrics[/bold]

Data Sources:
  Total Sources: {metrics.get('total_sources', 0)}
  Active Sources: {metrics.get('active_sources', 0)}
  Failed Sources: {metrics.get('failed_sources', 0)}

Data Processing:
  Documents Fetched: {metrics.get('documents_fetched', 0)}
  Documents Normalized: {metrics.get('documents_normalized', 0)}
  Documents Analyzed: {metrics.get('documents_analyzed', 0)}

Performance:
  Average Fetch Time: {metrics.get('avg_fetch_time_sec', 0):.2f} sec
  Average Process Time: {metrics.get('avg_process_time_sec', 0):.2f} sec
  Success Rate: {metrics.get('success_rate_percent', 0):.1f}%

Time Period: Last 24 hours
"""
                print_panel(self.console, content, border_style="blue")
            else:
                self.console.print("[yellow]No integration metrics available.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error fetching integration metrics: {e}[/red]")

    async def active_connections(self):
        """Active connections."""
        try:
            with self.console.status("[bold green]Fetching active connections...") as status:
                response = await self.clients.get_json("source-agent/connections")

            if response.get("connections"):
                table = Table(title="Active Connections")
                table.add_column("Source", style="cyan")
                table.add_column("Type", style="green")
                table.add_column("Status", style="yellow")
                table.add_column("Connected", style="magenta")
                table.add_column("Last Activity", style="blue")

                for conn in response["connections"]:
                    status_color = {
                        "connected": "green",
                        "connecting": "yellow",
                        "disconnected": "red",
                        "error": "red"
                    }.get(conn.get("status", "unknown"), "white")

                    table.add_row(
                        conn.get("source_name", "unknown"),
                        conn.get("source_type", "unknown"),
                        f"[{status_color}]{conn.get('status', 'unknown')}[/{status_color}]",
                        conn.get("connected_at", "unknown")[:19],
                        conn.get("last_activity", "unknown")[:19]
                    )

                self.console.print(table)
            else:
                self.console.print("[yellow]No active connections.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error fetching active connections: {e}[/red]")

    async def error_logs(self):
        """Error logs."""
        try:
            limit = Prompt.ask("[bold cyan]Limit[/bold cyan]", default="20")

            with self.console.status("[bold green]Fetching error logs...") as status:
                response = await self.clients.get_json(f"source-agent/errors?limit={limit}")

            if response.get("errors"):
                table = Table(title="Error Logs")
                table.add_column("Time", style="cyan")
                table.add_column("Source", style="green")
                table.add_column("Error Type", style="red")
                table.add_column("Message", style="white")

                for error in response["errors"]:
                    table.add_row(
                        error.get("timestamp", "unknown")[:19],
                        error.get("source", "unknown")[:20],
                        error.get("error_type", "unknown"),
                        error.get("message", "No message")[:50]
                    )

                self.console.print(table)
            else:
                self.console.print("[yellow]No error logs found.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error fetching error logs: {e}[/red]")
