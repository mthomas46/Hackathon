"""Bedrock Proxy Manager module for CLI service.

Provides power-user operations for bedrock proxy including
AI model invocations, template usage, proxy management, and history.
"""

from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.text import Text
import json
import os
import asyncio
from datetime import datetime
from collections import defaultdict

from .shared_utils import (
    get_cli_clients,
    create_menu_table,
    add_menu_rows,
    print_panel,
    log_cli_metrics
)


class BedrockProxyManager:
    """Manager for bedrock proxy power-user operations."""

    SUPPORTED_TEMPLATES = ['summary', 'risks', 'decisions', 'pr_confidence', 'life_of_ticket']
    SUPPORTED_FORMATS = ['md', 'txt', 'json']

    def __init__(self, console: Console, clients):
        self.console = console
        self.clients = clients
        self.invocation_history = []

    async def bedrock_proxy_menu(self):
        """Main bedrock proxy menu."""
        while True:
            menu = create_menu_table("Bedrock Proxy Management", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "AI Model Invocation (Execute prompts with templates)"),
                ("2", "Template Management (View, test, and customize templates)"),
                ("3", "Invocation History (Review past AI invocations)"),
                ("4", "Model Performance (Compare models and analyze results)"),
                ("5", "Batch Processing (Bulk AI operations)"),
                ("6", "Proxy Configuration (Settings and monitoring)"),
                ("b", "Back to Main Menu")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.ai_model_invocation_menu()
            elif choice == "2":
                await self.template_management_menu()
            elif choice == "3":
                await self.invocation_history_menu()
            elif choice == "4":
                await self.model_performance_menu()
            elif choice == "5":
                await self.batch_processing_menu()
            elif choice == "6":
                await self.proxy_configuration_menu()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def ai_model_invocation_menu(self):
        """AI model invocation submenu."""
        while True:
            menu = create_menu_table("AI Model Invocation", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Invoke with Template (Structured AI responses)"),
                ("2", "Invoke Custom Prompt (Free-form AI interaction)"),
                ("3", "Quick Template Test (Test all templates)"),
                ("4", "Format Comparison (Compare output formats)"),
                ("5", "Model Region Testing (Test different regions)"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.invoke_with_template()
            elif choice == "2":
                await self.invoke_custom_prompt()
            elif choice == "3":
                await self.quick_template_test()
            elif choice == "4":
                await self.format_comparison()
            elif choice == "5":
                await self.model_region_testing()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def invoke_with_template(self):
        """Invoke AI model with a specific template."""
        try:
            # Template selection
            template_table = Table(title="Available Templates")
            template_table.add_column("Template", style="cyan")
            template_table.add_column("Description", style="white")

            template_descriptions = {
                "summary": "Generate structured summaries with key points",
                "risks": "Identify risks and provide mitigation strategies",
                "decisions": "Document decisions with rationale",
                "pr_confidence": "Analyze PR confidence with endpoint validation",
                "life_of_ticket": "Track ticket lifecycle and timeline"
            }

            for template in self.SUPPORTED_TEMPLATES:
                template_table.add_row(template, template_descriptions.get(template, "Custom template"))

            self.console.print(template_table)

            template = Prompt.ask("[bold cyan]Select template[/bold cyan]", choices=self.SUPPORTED_TEMPLATES)

            # Prompt input
            prompt = Prompt.ask("[bold cyan]Enter prompt text[/bold cyan]")

            # Optional parameters
            model = Prompt.ask("[bold cyan]Model (optional)[/bold cyan]", default="")
            region = Prompt.ask("[bold cyan]Region (optional)[/bold cyan]", default="")
            fmt = Prompt.ask("[bold cyan]Output format[/bold cyan]", default="md", choices=self.SUPPORTED_FORMATS)
            title = Prompt.ask("[bold cyan]Custom title (optional)[/bold cyan]", default="")

            # Build request
            request_data = {
                "prompt": prompt,
                "template": template,
                "format": fmt
            }

            if model:
                request_data["model"] = model
            if region:
                request_data["region"] = region
            if title:
                request_data["title"] = title

            with self.console.status(f"[bold green]Invoking AI model with {template} template...[/bold green]") as status:
                response = await self.clients.post_json("bedrock-proxy/invoke", request_data)

            if response:
                # Store in history
                invocation_record = {
                    "timestamp": datetime.now().isoformat(),
                    "template": template,
                    "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt,
                    "format": fmt,
                    "model": model or "default",
                    "region": region or "default",
                    "response": response
                }
                self.invocation_history.append(invocation_record)

                await self.display_ai_response(response, template, fmt)
                self.console.print(f"[green]✅ AI invocation completed and stored in history[/green]")
            else:
                self.console.print("[red]❌ Failed to invoke AI model[/red]")

        except Exception as e:
            self.console.print(f"[red]Error invoking AI model: {e}[/red]")

    async def invoke_custom_prompt(self):
        """Invoke AI model with a custom prompt."""
        try:
            prompt = Prompt.ask("[bold cyan]Enter custom prompt[/bold cyan]")

            if not prompt.strip():
                self.console.print("[yellow]Prompt cannot be empty[/yellow]")
                return

            # Optional parameters
            model = Prompt.ask("[bold cyan]Model (optional)[/bold cyan]", default="")
            region = Prompt.ask("[bold cyan]Region (optional)[/bold cyan]", default="")
            fmt = Prompt.ask("[bold cyan]Output format[/bold cyan]", default="md", choices=self.SUPPORTED_FORMATS)
            title = Prompt.ask("[bold cyan]Custom title (optional)[/bold cyan]", default="")

            # Build request
            request_data = {
                "prompt": prompt,
                "format": fmt
            }

            if model:
                request_data["model"] = model
            if region:
                request_data["region"] = region
            if title:
                request_data["title"] = title

            with self.console.status("[bold green]Invoking AI model with custom prompt...[/bold green]") as status:
                response = await self.clients.post_json("bedrock-proxy/invoke", request_data)

            if response:
                # Store in history
                invocation_record = {
                    "timestamp": datetime.now().isoformat(),
                    "template": "custom",
                    "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt,
                    "format": fmt,
                    "model": model or "default",
                    "region": region or "default",
                    "response": response
                }
                self.invocation_history.append(invocation_record)

                await self.display_ai_response(response, "custom", fmt)
                self.console.print(f"[green]✅ Custom AI invocation completed[/green]")
            else:
                self.console.print("[red]❌ Failed to invoke AI model[/red]")

        except Exception as e:
            self.console.print(f"[red]Error with custom prompt: {e}[/red]")

    async def quick_template_test(self):
        """Test all templates with sample prompts."""
        try:
            test_prompts = {
                "summary": "Summarize the key decisions and risks for implementing a new microservices architecture.",
                "risks": "Identify potential risks in deploying this new feature to production.",
                "decisions": "Document the architectural decisions made for this system.",
                "pr_confidence": "Analyze this pull request for API endpoint implementation confidence.",
                "life_of_ticket": "Track the complete lifecycle of this development ticket."
            }

            results = []

            for template, prompt in test_prompts.items():
                self.console.print(f"[yellow]Testing {template} template...[/yellow]")

                request_data = {
                    "prompt": prompt,
                    "template": template,
                    "format": "md"
                }

                response = await self.clients.post_json("bedrock-proxy/invoke", request_data)

                if response:
                    results.append({
                        "template": template,
                        "success": True,
                        "response": response
                    })
                    self.console.print(f"[green]✅ {template} template test passed[/green]")
                else:
                    results.append({
                        "template": template,
                        "success": False,
                        "response": None
                    })
                    self.console.print(f"[red]❌ {template} template test failed[/red]")

            # Display summary
            success_count = sum(1 for r in results if r["success"])
            total_count = len(results)

            content = f"""
[bold]Template Test Results[/bold]

[bold blue]Success Rate:[/bold blue] {success_count}/{total_count} ({success_count/total_count*100:.1f}%)

[bold green]Successful Templates:[/bold green]
"""

            for result in results:
                if result["success"]:
                    content += f"• {result['template']}\n"

            if any(not r["success"] for r in results):
                content += f"\n[bold red]Failed Templates:[/bold red]\n"
                for result in results:
                    if not result["success"]:
                        content += f"• {result['template']}\n"

            print_panel(self.console, content, border_style="green" if success_count == total_count else "yellow")

        except Exception as e:
            self.console.print(f"[red]Error testing templates: {e}[/red]")

    async def format_comparison(self):
        """Compare output formats for the same prompt."""
        try:
            prompt = Prompt.ask("[bold cyan]Enter prompt to test all formats[/bold cyan]")
            template = Prompt.ask("[bold cyan]Template (optional)[/bold cyan]", default="summary")

            if not prompt.strip():
                self.console.print("[yellow]Prompt cannot be empty[/yellow]")
                return

            format_results = {}

            for fmt in self.SUPPORTED_FORMATS:
                self.console.print(f"[yellow]Testing {fmt} format...[/yellow]")

                request_data = {
                    "prompt": prompt,
                    "template": template,
                    "format": fmt
                }

                response = await self.clients.post_json("bedrock-proxy/invoke", request_data)

                if response:
                    format_results[fmt] = response
                    self.console.print(f"[green]✅ {fmt} format test passed[/green]")
                else:
                    format_results[fmt] = None
                    self.console.print(f"[red]❌ {fmt} format test failed[/red]")

            # Display comparison
            table = Table(title="Format Comparison Results")
            table.add_column("Format", style="cyan")
            table.add_column("Success", style="green")
            table.add_column("Response Preview", style="white")

            for fmt, response in format_results.items():
                success = "✅" if response else "❌"
                preview = ""
                if response:
                    # Get a short preview of the response
                    if isinstance(response, dict):
                        preview = str(response)[:50] + "..."
                    elif isinstance(response, str):
                        preview = response[:50] + "..."
                    else:
                        preview = str(response)[:50] + "..."

                table.add_row(fmt.upper(), success, preview)

            self.console.print(table)

        except Exception as e:
            self.console.print(f"[red]Error comparing formats: {e}[/red]")

    async def model_region_testing(self):
        """Test different model and region combinations."""
        try:
            prompt = Prompt.ask("[bold cyan]Enter test prompt[/bold cyan]")
            template = Prompt.ask("[bold cyan]Template (optional)[/bold cyan]", default="summary")

            if not prompt.strip():
                self.console.print("[yellow]Prompt cannot be empty[/yellow]")
                return

            # Test different model/region combinations
            test_configs = [
                {"model": "claude-3-sonnet", "region": "us-east-1"},
                {"model": "claude-3-haiku", "region": "us-west-2"},
                {"model": "gpt-4", "region": "us-east-1"},
                {"model": "", "region": ""}  # Default
            ]

            results = []

            for config in test_configs:
                config_name = f"{config['model'] or 'default'}@{config['region'] or 'default'}"
                self.console.print(f"[yellow]Testing {config_name}...[/yellow]")

                request_data = {
                    "prompt": prompt,
                    "template": template,
                    "format": "md"
                }

                if config["model"]:
                    request_data["model"] = config["model"]
                if config["region"]:
                    request_data["region"] = config["region"]

                response = await self.clients.post_json("bedrock-proxy/invoke", request_data)

                results.append({
                    "config": config_name,
                    "success": response is not None,
                    "response": response
                })

                status = "✅" if response else "❌"
                self.console.print(f"{status} {config_name}")

            # Display results
            table = Table(title="Model/Region Test Results")
            table.add_column("Configuration", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Response Size", style="yellow")

            for result in results:
                status = "✅ Success" if result["success"] else "❌ Failed"
                size = "N/A"
                if result["success"] and result["response"]:
                    size = f"{len(str(result['response']))} chars"

                table.add_row(result["config"], status, size)

            self.console.print(table)

        except Exception as e:
            self.console.print(f"[red]Error testing models/regions: {e}[/red]")

    async def display_ai_response(self, response: Dict[str, Any], template: str, fmt: str):
        """Display AI response in a formatted way."""
        if not response:
            self.console.print("[yellow]No response to display[/yellow]")
            return

        # Handle different response formats
        if fmt == "json":
            # Pretty print JSON
            content = f"```json\n{json.dumps(response, indent=2)}\n```"
        elif fmt == "txt":
            # Plain text response
            if isinstance(response, dict):
                content = "\n".join(f"{k}: {v}" for k, v in response.items())
            else:
                content = str(response)
        else:  # md or other
            # Markdown-style response
            content = ""
            if isinstance(response, dict):
                for section, items in response.items():
                    content += f"## {section}\n\n"
                    if isinstance(items, list):
                        for item in items:
                            content += f"- {item}\n"
                    else:
                        content += f"{items}\n"
                    content += "\n"
            else:
                content = str(response)

        # Create title based on template
        title_map = {
            "summary": "AI Summary Response",
            "risks": "Risk Analysis Response",
            "decisions": "Decision Documentation Response",
            "pr_confidence": "PR Confidence Analysis Response",
            "life_of_ticket": "Ticket Lifecycle Analysis Response",
            "custom": "Custom AI Response"
        }

        title = title_map.get(template, f"AI Response ({template})")

        print_panel(self.console, content, title=title, border_style="blue")

    async def template_management_menu(self):
        """Template management submenu."""
        while True:
            menu = create_menu_table("Template Management", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "List Available Templates"),
                ("2", "View Template Details"),
                ("3", "Test Template with Sample Data"),
                ("4", "Compare Template Outputs"),
                ("5", "Template Usage Statistics"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.list_available_templates()
            elif choice == "2":
                await self.view_template_details()
            elif choice == "3":
                await self.test_template_sample()
            elif choice == "4":
                await self.compare_template_outputs()
            elif choice == "5":
                await self.template_usage_statistics()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def list_available_templates(self):
        """List all available templates."""
        table = Table(title="Available AI Templates")
        table.add_column("Template", style="cyan", no_wrap=True)
        table.add_column("Description", style="white")
        table.add_column("Use Case", style="green")

        template_info = {
            "summary": {
                "description": "Generate structured summaries with key points and highlights",
                "use_case": "Documentation, reporting, content synthesis"
            },
            "risks": {
                "description": "Identify potential risks and provide mitigation strategies",
                "use_case": "Risk assessment, project planning, compliance"
            },
            "decisions": {
                "description": "Document architectural and business decisions with rationale",
                "use_case": "Decision tracking, knowledge management, governance"
            },
            "pr_confidence": {
                "description": "Analyze pull request confidence with endpoint validation",
                "use_case": "Code review, quality assurance, deployment validation"
            },
            "life_of_ticket": {
                "description": "Track complete ticket lifecycle and timeline analysis",
                "use_case": "Process optimization, workflow analysis, metrics"
            }
        }

        for template, info in template_info.items():
            table.add_row(template, info["description"], info["use_case"])

        self.console.print(table)

        Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

    async def view_template_details(self):
        """View detailed information about a specific template."""
        try:
            template = Prompt.ask("[bold cyan]Select template to view[/bold cyan]", choices=self.SUPPORTED_TEMPLATES)

            # Get template details from test data or documentation
            template_details = {
                "summary": {
                    "sections": ["Summary", "Key Points", "Conclusions"],
                    "sample_output": "Provides structured summary with bullet points and key takeaways",
                    "best_for": "Content synthesis, meeting notes, report generation"
                },
                "risks": {
                    "sections": ["Risks", "Mitigations", "Impact Assessment"],
                    "sample_output": "Lists identified risks with corresponding mitigation strategies",
                    "best_for": "Risk management, project planning, compliance reviews"
                },
                "decisions": {
                    "sections": ["Decisions", "Rationale", "Alternatives Considered"],
                    "sample_output": "Documents decisions made with supporting rationale and context",
                    "best_for": "Architecture documentation, governance, knowledge sharing"
                },
                "pr_confidence": {
                    "sections": ["Inputs", "Extracted Endpoints", "Confidence", "Suggestions"],
                    "sample_output": "Analyzes PR implementation confidence with endpoint validation",
                    "best_for": "Code review automation, quality gates, deployment validation"
                },
                "life_of_ticket": {
                    "sections": ["Timeline", "Stages", "Blockers", "Resolution"],
                    "sample_output": "Tracks complete ticket journey from creation to completion",
                    "best_for": "Process optimization, bottleneck identification, workflow analysis"
                }
            }

            details = template_details.get(template, {})

            content = f"""
[bold]Template: {template.upper()}[/bold]

[bold blue]Description:[/bold blue] {details.get('sample_output', 'N/A')}

[bold green]Sections:[/bold green]
"""

            for section in details.get('sections', []):
                content += f"• {section}\n"

            content += f"\n[bold yellow]Best For:[/bold yellow] {details.get('best_for', 'N/A')}"

            print_panel(self.console, content, border_style="green")

        except Exception as e:
            self.console.print(f"[red]Error viewing template details: {e}[/red]")

    async def test_template_sample(self):
        """Test a template with sample data."""
        try:
            template = Prompt.ask("[bold cyan]Select template to test[/bold cyan]", choices=self.SUPPORTED_TEMPLATES)

            # Use predefined sample prompts for each template
            sample_prompts = {
                "summary": "Please summarize the implementation of the new user authentication system, including key components, security measures, and integration points.",
                "risks": "Analyze the potential risks in migrating our monolithic application to a microservices architecture.",
                "decisions": "Document the key architectural decisions made during the system redesign, including technology choices and design patterns.",
                "pr_confidence": "Review this pull request that implements user registration endpoints and assess implementation confidence.",
                "life_of_ticket": "Track the complete lifecycle of ticket PROJ-123 from initial creation through to deployment."
            }

            prompt = sample_prompts.get(template, "Please provide a sample analysis.")

            self.console.print(f"[yellow]Testing template '{template}' with sample prompt:[/yellow]")
            self.console.print(f"[dim]{prompt}[/dim]\n")

            request_data = {
                "prompt": prompt,
                "template": template,
                "format": "md"
            }

            with self.console.status("[bold green]Testing template...[/bold green]") as status:
                response = await self.clients.post_json("bedrock-proxy/invoke", request_data)

            if response:
                await self.display_ai_response(response, template, "md")
                self.console.print(f"[green]✅ Template '{template}' test completed[/green]")
            else:
                self.console.print(f"[red]❌ Template '{template}' test failed[/red]")

        except Exception as e:
            self.console.print(f"[red]Error testing template: {e}[/red]")

    async def compare_template_outputs(self):
        """Compare outputs from different templates for the same prompt."""
        try:
            prompt = Prompt.ask("[bold cyan]Enter prompt to compare across templates[/bold cyan]")

            if not prompt.strip():
                self.console.print("[yellow]Prompt cannot be empty[/yellow]")
                return

            template_results = {}

            for template in self.SUPPORTED_TEMPLATES:
                self.console.print(f"[yellow]Testing {template} template...[/yellow]")

                request_data = {
                    "prompt": prompt,
                    "template": template,
                    "format": "md"
                }

                response = await self.clients.post_json("bedrock-proxy/invoke", request_data)

                if response:
                    template_results[template] = response
                    self.console.print(f"[green]✅ {template} completed[/green]")
                else:
                    template_results[template] = None
                    self.console.print(f"[red]❌ {template} failed[/red]")

            # Display comparison summary
            table = Table(title="Template Comparison Results")
            table.add_column("Template", style="cyan")
            table.add_column("Success", style="green")
            table.add_column("Sections", style="yellow", justify="right")
            table.add_column("Content Length", style="blue", justify="right")

            for template, response in template_results.items():
                if response and isinstance(response, dict):
                    sections = len(response)
                    content_length = sum(len(str(v)) for v in response.values())
                    table.add_row(template, "✅", str(sections), str(content_length))
                else:
                    table.add_row(template, "❌", "0", "0")

            self.console.print(table)

            # Show detailed comparison if requested
            show_details = Confirm.ask("[bold cyan]Show detailed comparison?[/bold cyan]", default=False)

            if show_details:
                for template, response in template_results.items():
                    if response:
                        self.console.print(f"\n[bold]{template.upper()} Template Output:[/bold]")
                        await self.display_ai_response(response, template, "md")

        except Exception as e:
            self.console.print(f"[red]Error comparing templates: {e}[/red]")

    async def template_usage_statistics(self):
        """Show template usage statistics from history."""
        try:
            if not self.invocation_history:
                self.console.print("[yellow]No invocation history available[/yellow]")
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
                return

            # Analyze history
            template_counts = defaultdict(int)
            format_counts = defaultdict(int)
            model_counts = defaultdict(int)

            for record in self.invocation_history:
                template_counts[record.get("template", "unknown")] += 1
                format_counts[record.get("format", "unknown")] += 1
                model_counts[record.get("model", "unknown")] += 1

            # Display statistics
            content = f"""
[bold]Template Usage Statistics[/bold]

[bold blue]Total Invocations:[/bold blue] {len(self.invocation_history)}

[bold green]Template Usage:[/bold green]
"""

            for template, count in sorted(template_counts.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / len(self.invocation_history)) * 100
                content += f"• {template}: {count} ({percentage:.1f}%)\n"

            content += f"\n[bold yellow]Format Usage:[/bold yellow]\n"
            for fmt, count in sorted(format_counts.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / len(self.invocation_history)) * 100
                content += f"• {fmt}: {count} ({percentage:.1f}%)\n"

            content += f"\n[bold cyan]Model Usage:[/bold cyan]\n"
            for model, count in sorted(model_counts.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / len(self.invocation_history)) * 100
                content += f"• {model}: {count} ({percentage:.1f}%)\n"

            print_panel(self.console, content, border_style="blue")

        except Exception as e:
            self.console.print(f"[red]Error showing usage statistics: {e}[/red]")

    async def invocation_history_menu(self):
        """Invocation history submenu."""
        while True:
            menu = create_menu_table("Invocation History", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "View Recent Invocations"),
                ("2", "Search History"),
                ("3", "Export History"),
                ("4", "Clear History"),
                ("5", "History Statistics"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.view_recent_invocations()
            elif choice == "2":
                await self.search_history()
            elif choice == "3":
                await self.export_history()
            elif choice == "4":
                await self.clear_history()
            elif choice == "5":
                await self.history_statistics()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def view_recent_invocations(self):
        """View recent AI invocations."""
        try:
            if not self.invocation_history:
                self.console.print("[yellow]No invocation history available[/yellow]")
                return

            limit = min(int(Prompt.ask("[bold cyan]Number of recent invocations to show[/bold cyan]", default="10")), len(self.invocation_history))

            # Show most recent first
            recent_history = self.invocation_history[-limit:]

            table = Table(title=f"Recent AI Invocations (Last {limit})")
            table.add_column("Time", style="blue", no_wrap=True)
            table.add_column("Template", style="cyan")
            table.add_column("Model", style="green")
            table.add_column("Prompt Preview", style="white")

            for record in recent_history:
                timestamp = record.get("timestamp", "")
                if timestamp and len(timestamp) > 19:
                    timestamp = timestamp[11:19]  # Show just time part

                template = record.get("template", "unknown")
                model = record.get("model", "unknown")
                prompt = record.get("prompt", "")[:50] + "..." if len(record.get("prompt", "")) > 50 else record.get("prompt", "")

                table.add_row(timestamp, template, model, prompt)

            self.console.print(table)

            # Option to view details of a specific invocation
            if recent_history:
                view_details = Confirm.ask("[bold cyan]View details of a specific invocation?[/bold cyan]", default=False)
                if view_details:
                    indices = [str(i+1) for i in range(len(recent_history))]
                    choice = Prompt.ask(f"[bold cyan]Select invocation (1-{len(recent_history)})[/bold cyan]", choices=indices)

                    selected_record = recent_history[int(choice) - 1]
                    await self.display_invocation_details(selected_record)

        except Exception as e:
            self.console.print(f"[red]Error viewing recent invocations: {e}[/red]")

    async def display_invocation_details(self, record: Dict[str, Any]):
        """Display detailed information about a specific invocation."""
        try:
            content = f"""
[bold]Invocation Details[/bold]

[bold blue]Timestamp:[/bold blue] {record.get('timestamp', 'N/A')}
[bold blue]Template:[/bold blue] {record.get('template', 'N/A')}
[bold blue]Format:[/bold blue] {record.get('format', 'N/A')}
[bold blue]Model:[/bold blue] {record.get('model', 'N/A')}
[bold blue]Region:[/bold blue] {record.get('region', 'N/A')}

[bold green]Prompt:[/bold green]
{record.get('prompt', 'N/A')}

[bold yellow]Response:[/bold yellow]
"""

            response = record.get('response')
            if response:
                if isinstance(response, dict):
                    content += json.dumps(response, indent=2)
                else:
                    content += str(response)
            else:
                content += "No response data available"

            print_panel(self.console, content, border_style="blue")

        except Exception as e:
            self.console.print(f"[red]Error displaying invocation details: {e}[/red]")

    async def search_history(self):
        """Search invocation history."""
        try:
            if not self.invocation_history:
                self.console.print("[yellow]No invocation history available[/yellow]")
                return

            search_term = Prompt.ask("[bold cyan]Search term (template, model, or prompt content)[/bold cyan]")

            if not search_term.strip():
                self.console.print("[yellow]Search term cannot be empty[/yellow]")
                return

            matching_records = []

            for record in self.invocation_history:
                # Search in template, model, prompt, and response
                searchable_text = f"{record.get('template', '')} {record.get('model', '')} {record.get('prompt', '')} {str(record.get('response', ''))}"

                if search_term.lower() in searchable_text.lower():
                    matching_records.append(record)

            if matching_records:
                self.console.print(f"[green]Found {len(matching_records)} matching invocations[/green]")

                table = Table(title=f"Search Results for '{search_term}'")
                table.add_column("Time", style="blue", no_wrap=True)
                table.add_column("Template", style="cyan")
                table.add_column("Model", style="green")
                table.add_column("Prompt Preview", style="white")

                for record in matching_records[-20:]:  # Show last 20 matches
                    timestamp = record.get("timestamp", "")
                    if timestamp and len(timestamp) > 19:
                        timestamp = timestamp[11:19]

                    template = record.get("template", "unknown")
                    model = record.get("model", "unknown")
                    prompt = record.get("prompt", "")[:40] + "..." if len(record.get("prompt", "")) > 40 else record.get("prompt", "")

                    table.add_row(timestamp, template, model, prompt)

                self.console.print(table)
            else:
                self.console.print(f"[yellow]No invocations found matching '{search_term}'[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error searching history: {e}[/red]")

    async def export_history(self):
        """Export invocation history to file."""
        try:
            if not self.invocation_history:
                self.console.print("[yellow]No invocation history to export[/yellow]")
                return

            file_path = Prompt.ask("[bold cyan]Export file path[/bold cyan]", default="bedrock_history.json")

            # Prepare export data
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "total_invocations": len(self.invocation_history),
                "invocations": self.invocation_history
            }

            with open(file_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)

            self.console.print(f"[green]✅ Exported {len(self.invocation_history)} invocations to {file_path}[/green]")

        except Exception as e:
            self.console.print(f"[red]Error exporting history: {e}[/red]")

    async def clear_history(self):
        """Clear invocation history."""
        try:
            if not self.invocation_history:
                self.console.print("[yellow]No history to clear[/yellow]")
                return

            confirm = Confirm.ask(f"[bold red]Clear all {len(self.invocation_history)} invocations from history?[/bold red]", default=False)

            if confirm:
                self.invocation_history.clear()
                self.console.print("[green]✅ Invocation history cleared[/green]")
            else:
                self.console.print("[yellow]History clearing cancelled[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error clearing history: {e}[/red]")

    async def history_statistics(self):
        """Show detailed history statistics."""
        try:
            if not self.invocation_history:
                self.console.print("[yellow]No invocation history available[/yellow]")
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
                return

            # Calculate comprehensive statistics
            stats = {
                "total_invocations": len(self.invocation_history),
                "templates_used": defaultdict(int),
                "models_used": defaultdict(int),
                "formats_used": defaultdict(int),
                "regions_used": defaultdict(int),
                "hourly_distribution": defaultdict(int),
                "success_rate": 100.0  # All stored invocations are successful
            }

            for record in self.invocation_history:
                # Template stats
                template = record.get("template", "unknown")
                stats["templates_used"][template] += 1

                # Model stats
                model = record.get("model", "unknown")
                stats["models_used"][model] += 1

                # Format stats
                fmt = record.get("format", "unknown")
                stats["formats_used"][fmt] += 1

                # Region stats
                region = record.get("region", "unknown")
                stats["regions_used"][region] += 1

                # Hourly distribution
                timestamp = record.get("timestamp", "")
                if timestamp:
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        hour = dt.hour
                        stats["hourly_distribution"][hour] += 1
                    except:
                        pass

            # Display statistics
            content = f"""
[bold]Invocation History Statistics[/bold]

[bold blue]📊 Overview[/bold blue]
• Total Invocations: {stats['total_invocations']}
• Success Rate: {stats['success_rate']:.1f}%
• Unique Templates: {len(stats['templates_used'])}
• Unique Models: {len(stats['models_used'])}

[bold green]🎯 Template Usage[/bold green]
"""

            for template, count in sorted(stats['templates_used'].items(), key=lambda x: x[1], reverse=True):
                percentage = (count / stats['total_invocations']) * 100
                content += f"• {template}: {count} ({percentage:.1f}%)\n"

            content += f"\n[bold yellow]🤖 Model Usage[/bold yellow]\n"
            for model, count in sorted(stats['models_used'].items(), key=lambda x: x[1], reverse=True):
                percentage = (count / stats['total_invocations']) * 100
                content += f"• {model}: {count} ({percentage:.1f}%)\n"

            content += f"\n[bold cyan]📄 Format Usage[/bold cyan]\n"
            for fmt, count in sorted(stats['formats_used'].items(), key=lambda x: x[1], reverse=True):
                percentage = (count / stats['total_invocations']) * 100
                content += f"• {fmt}: {count} ({percentage:.1f}%)\n"

            print_panel(self.console, content, border_style="blue")

        except Exception as e:
            self.console.print(f"[red]Error showing history statistics: {e}[/red]")

    async def model_performance_menu(self):
        """Model performance analysis submenu."""
        while True:
            menu = create_menu_table("Model Performance Analysis", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Response Time Analysis"),
                ("2", "Model Accuracy Comparison"),
                ("3", "Template Effectiveness"),
                ("4", "Cost Analysis"),
                ("5", "Performance Trends"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.response_time_analysis()
            elif choice == "2":
                await self.model_accuracy_comparison()
            elif choice == "3":
                await self.template_effectiveness()
            elif choice == "4":
                await self.cost_analysis()
            elif choice == "5":
                await self.performance_trends()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def response_time_analysis(self):
        """Analyze response times (placeholder for future implementation)."""
        try:
            self.console.print("[yellow]Response time analysis would measure AI model response times[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in response time analysis: {e}[/red]")

    async def model_accuracy_comparison(self):
        """Compare model accuracy (placeholder)."""
        try:
            self.console.print("[yellow]Model accuracy comparison would evaluate response quality[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in accuracy comparison: {e}[/red]")

    async def template_effectiveness(self):
        """Analyze template effectiveness."""
        try:
            if not self.invocation_history:
                self.console.print("[yellow]No history available for template analysis[/yellow]")
                return

            # Analyze template usage and success patterns
            template_stats = defaultdict(lambda: {"count": 0, "success": 0, "avg_sections": 0})

            for record in self.invocation_history:
                template = record.get("template", "unknown")
                response = record.get("response")

                template_stats[template]["count"] += 1

                if response and isinstance(response, dict) and response:
                    template_stats[template]["success"] += 1
                    sections = len(response)
                    template_stats[template]["avg_sections"] = (
                        (template_stats[template]["avg_sections"] * (template_stats[template]["count"] - 1) + sections) /
                        template_stats[template]["count"]
                    )

            # Display effectiveness analysis
            table = Table(title="Template Effectiveness Analysis")
            table.add_column("Template", style="cyan")
            table.add_column("Usage Count", style="green", justify="right")
            table.add_column("Success Rate", style="yellow", justify="right")
            table.add_column("Avg Sections", style="blue", justify="right")

            for template, stats in sorted(template_stats.items(), key=lambda x: x[1]["count"], reverse=True):
                success_rate = (stats["success"] / stats["count"]) * 100 if stats["count"] > 0 else 0
                table.add_row(
                    template,
                    str(stats["count"]),
                    f"{success_rate:.1f}%",
                    f"{stats['avg_sections']:.1f}"
                )

            self.console.print(table)

        except Exception as e:
            self.console.print(f"[red]Error analyzing template effectiveness: {e}[/red]")

    async def cost_analysis(self):
        """Analyze costs (placeholder)."""
        try:
            self.console.print("[yellow]Cost analysis would track AI API usage costs[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in cost analysis: {e}[/red]")

    async def performance_trends(self):
        """Show performance trends (placeholder)."""
        try:
            self.console.print("[yellow]Performance trends would show usage patterns over time[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error showing performance trends: {e}[/red]")

    async def batch_processing_menu(self):
        """Batch processing submenu."""
        while True:
            menu = create_menu_table("Batch Processing", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Process Multiple Prompts"),
                ("2", "Bulk Template Testing"),
                ("3", "Batch File Processing"),
                ("4", "Parallel Processing"),
                ("5", "Batch Results Analysis"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.process_multiple_prompts()
            elif choice == "2":
                await self.bulk_template_testing()
            elif choice == "3":
                await self.batch_file_processing()
            elif choice == "4":
                await self.parallel_processing()
            elif choice == "5":
                await self.batch_results_analysis()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def process_multiple_prompts(self):
        """Process multiple prompts in batch."""
        try:
            self.console.print("[yellow]Batch processing would handle multiple prompts efficiently[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in batch processing: {e}[/red]")

    async def bulk_template_testing(self):
        """Bulk template testing."""
        try:
            self.console.print("[yellow]Bulk template testing would validate all templates systematically[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in bulk template testing: {e}[/red]")

    async def batch_file_processing(self):
        """Process prompts from file."""
        try:
            self.console.print("[yellow]Batch file processing would handle input files with multiple prompts[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in batch file processing: {e}[/red]")

    async def parallel_processing(self):
        """Parallel processing of prompts."""
        try:
            self.console.print("[yellow]Parallel processing would execute multiple AI invocations concurrently[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in parallel processing: {e}[/red]")

    async def batch_results_analysis(self):
        """Analyze batch processing results."""
        try:
            self.console.print("[yellow]Batch results analysis would provide insights from bulk operations[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in batch results analysis: {e}[/red]")

    async def proxy_configuration_menu(self):
        """Proxy configuration submenu."""
        while True:
            menu = create_menu_table("Proxy Configuration", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "View Proxy Health"),
                ("2", "Configuration Settings"),
                ("3", "Supported Models"),
                ("4", "Rate Limiting Status"),
                ("5", "Proxy Logs"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.view_proxy_health()
            elif choice == "2":
                await self.configuration_settings()
            elif choice == "3":
                await self.supported_models()
            elif choice == "4":
                await self.rate_limiting_status()
            elif choice == "5":
                await self.proxy_logs()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def view_proxy_health(self):
        """View bedrock proxy service health."""
        try:
            response = await self.clients.get_json("bedrock-proxy/health")

            if response:
                content = f"""
[bold]Bedrock Proxy Health Status[/bold]

[bold blue]Status:[/bold blue] {response.get('status', 'unknown')}
[bold blue]Service:[/bold blue] {response.get('service', 'unknown')}
[bold blue]Version:[/bold blue] {response.get('version', 'unknown')}

[bold green]Description:[/bold green] {response.get('description', 'N/A')}
"""

                print_panel(self.console, content, border_style="green")
            else:
                self.console.print("[red]Failed to retrieve proxy health[/red]")

        except Exception as e:
            self.console.print(f"[red]Error viewing proxy health: {e}[/red]")

    async def configuration_settings(self):
        """View proxy configuration."""
        try:
            self.console.print("[yellow]Configuration settings would show current proxy parameters[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error viewing configuration: {e}[/red]")

    async def supported_models(self):
        """Show supported AI models."""
        try:
            models = [
                {"name": "claude-3-sonnet", "provider": "Anthropic", "context": "200K"},
                {"name": "claude-3-haiku", "provider": "Anthropic", "context": "200K"},
                {"name": "gpt-4", "provider": "OpenAI", "context": "128K"},
                {"name": "gpt-3.5-turbo", "provider": "OpenAI", "context": "16K"}
            ]

            table = Table(title="Supported AI Models")
            table.add_column("Model", style="cyan")
            table.add_column("Provider", style="green")
            table.add_column("Context Window", style="yellow")

            for model in models:
                table.add_row(model["name"], model["provider"], model["context"])

            self.console.print(table)

        except Exception as e:
            self.console.print(f"[red]Error showing supported models: {e}[/red]")

    async def rate_limiting_status(self):
        """Show rate limiting status."""
        try:
            self.console.print("[yellow]Rate limiting status would show current usage limits[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error showing rate limiting: {e}[/red]")

    async def proxy_logs(self):
        """View proxy service logs."""
        try:
            self.console.print("[yellow]Proxy logs would show bedrock proxy internal operations[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error viewing proxy logs: {e}[/red]")

    async def invoke_ai_from_cli(self, request_data: Dict[str, Any]):
        """Invoke AI model for CLI usage."""
        try:
            with self.console.status("[bold green]Invoking AI model...[/bold green]") as status:
                response = await self.clients.post_json("bedrock-proxy/invoke", request_data)

            if response:
                # Store in history
                invocation_record = {
                    "timestamp": datetime.now().isoformat(),
                    "template": request_data.get("template", "custom"),
                    "prompt": request_data.get("prompt", "")[:100] + "..." if len(request_data.get("prompt", "")) > 100 else request_data.get("prompt", ""),
                    "format": request_data.get("format", "md"),
                    "model": request_data.get("model", "default"),
                    "region": request_data.get("region", "default"),
                    "response": response
                }
                self.invocation_history.append(invocation_record)

                await self.display_ai_response(response, request_data.get("template", "custom"), request_data.get("format", "md"))
                self.console.print("[green]✅ AI invocation completed[/green]")
            else:
                self.console.print("[red]❌ Failed to invoke AI model[/red]")

        except Exception as e:
            self.console.print(f"[red]Error invoking AI model: {e}[/red]")
