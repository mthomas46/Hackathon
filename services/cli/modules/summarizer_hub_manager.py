"""Summarizer Hub Manager module for CLI service.

Provides power-user operations for summarizer hub including
ensemble summarization, model management, and AI operations.
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

from .shared_utils import (
    get_cli_clients,
    create_menu_table,
    add_menu_rows,
    print_panel,
    log_cli_metrics
)


class SummarizerHubManager:
    """Manager for summarizer hub power-user operations."""

    def __init__(self, console: Console, clients):
        self.console = console
        self.clients = clients

    async def summarizer_hub_menu(self):
        """Main summarizer hub menu."""
        while True:
            menu = create_menu_table("Summarizer Hub Management", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Ensemble Summarization (Multi-provider AI operations)"),
                ("2", "Provider Management (Configure and test LLM providers)"),
                ("3", "Model Performance Analysis"),
                ("4", "Summarization Job Monitoring"),
                ("5", "AI Operations Analytics"),
                ("6", "Summarizer Hub Health & Configuration"),
                ("b", "Back to Main Menu")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.ensemble_summarization_menu()
            elif choice == "2":
                await self.provider_management_menu()
            elif choice == "3":
                await self.model_performance_menu()
            elif choice == "4":
                await self.summarization_job_monitoring_menu()
            elif choice == "5":
                await self.ai_operations_analytics_menu()
            elif choice == "6":
                await self.summarizer_hub_health_menu()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def ensemble_summarization_menu(self):
        """Ensemble summarization submenu."""
        while True:
            menu = create_menu_table("Ensemble Summarization", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Summarize Text with Multiple Providers"),
                ("2", "Summarize File Content"),
                ("3", "Batch Summarization from Files"),
                ("4", "Interactive Summarization Console"),
                ("5", "Custom Prompt Summarization"),
                ("6", "Provider Comparison Mode"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.summarize_text()
            elif choice == "2":
                await self.summarize_file()
            elif choice == "3":
                await self.batch_summarization()
            elif choice == "4":
                await self.interactive_summarization()
            elif choice == "5":
                await self.custom_prompt_summarization()
            elif choice == "6":
                await self.provider_comparison_mode()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def summarize_text(self):
        """Summarize text using multiple providers."""
        try:
            self.console.print("[yellow]Enter text to summarize (press Ctrl+D on new line when done):[/yellow]")
            content_lines = []
            try:
                while True:
                    line = input()
                    content_lines.append(line)
            except EOFError:
                pass

            text = "\n".join(content_lines).strip()
            if not text:
                self.console.print("[red]No text provided[/red]")
                return

            # Get providers
            providers_input = Prompt.ask("[bold cyan]Providers (comma-separated, default: ollama)[/bold cyan]", default="ollama")
            providers = [p.strip() for p in providers_input.split(",") if p.strip()]

            if not providers:
                self.console.print("[red]No providers specified[/red]")
                return

            # Convert to provider configs
            provider_configs = []
            for provider in providers:
                config = {"name": provider}
                # Add default models for known providers
                if provider == "ollama":
                    config["model"] = "llama3"
                    config["endpoint"] = "http://localhost:11434"
                elif provider == "openai":
                    config["model"] = "gpt-4"
                elif provider == "anthropic":
                    config["model"] = "claude-3-sonnet-20240229"
                elif provider == "grok":
                    config["model"] = "grok-1"
                elif provider == "bedrock":
                    config["model"] = "anthropic.claude-3-sonnet-20240229-v1:0"
                    config["region"] = "us-east-1"

                provider_configs.append(config)

            # Get custom prompt
            custom_prompt = Prompt.ask("[bold cyan]Custom prompt (optional)[/bold cyan]", default="")

            # Use hub config?
            use_hub_config = Confirm.ask("[bold cyan]Use hub configuration defaults?[/bold cyan]", default=True)

            request_data = {
                "text": text,
                "providers": provider_configs,
                "prompt": custom_prompt if custom_prompt else None,
                "use_hub_config": use_hub_config
            }

            with self.console.status(f"[bold green]Summarizing with {len(providers)} providers...[/bold green]") as status:
                response = await self.clients.post_json("summarizer-hub/summarize/ensemble", request_data)

            if response:
                await self.display_summarization_results(response, text[:200] + "..." if len(text) > 200 else text)
            else:
                self.console.print("[red]❌ Failed to generate summaries[/red]")

        except KeyboardInterrupt:
            self.console.print("[yellow]Summarization cancelled[/yellow]")
        except Exception as e:
            self.console.print(f"[red]Error during summarization: {e}[/red]")

    async def display_summarization_results(self, results: Dict[str, Any], text_preview: str):
        """Display ensemble summarization results."""
        summaries = results.get("summaries", {})
        analysis = results.get("analysis", {})
        normalized = results.get("normalized", {})

        content = f"""
[bold]Ensemble Summarization Results[/bold]

[bold blue]Input Text Preview:[/bold blue] {text_preview}
[bold blue]Providers Used:[/bold blue] {len(summaries)}

[bold green]Individual Provider Summaries:[/bold green]
"""

        for provider, summary in summaries.items():
            provider_icon = {
                "ollama": "🦙",
                "openai": "🤖",
                "anthropic": "🧠",
                "grok": "🚀",
                "bedrock": "☁️"
            }.get(provider, "🤖")

            content += f"\n[bold cyan]{provider_icon} {provider.upper()}:[/bold cyan]\n{summary[:300]}{'...' if len(summary) > 300 else ''}\n"

        # Show analysis if available
        if analysis:
            content += f"\n[bold yellow]Consistency Analysis:[/bold yellow]\n"
            content += f"• Analysis Type: {analysis.get('type', 'N/A')}\n"
            if analysis.get('score'):
                content += f"• Consistency Score: {analysis['score']:.2f}\n"
            if analysis.get('insights'):
                content += f"• Insights: {analysis['insights'][:200]}...\n"

        # Show normalized results
        if normalized:
            content += f"\n[bold magenta]Normalized Results:[/bold magenta]\n"
            if normalized.get('consensus_summary'):
                content += f"• Consensus: {normalized['consensus_summary'][:300]}...\n"
            if normalized.get('confidence'):
                content += f"• Confidence: {normalized['confidence']:.2f}\n"

        print_panel(self.console, content, border_style="green")

        # Show detailed table if multiple providers
        if len(summaries) > 1:
            table = Table(title="Provider Comparison")
            table.add_column("Provider", style="cyan")
            table.add_column("Summary Length", style="green", justify="right")
            table.add_column("Preview", style="white")

            for provider, summary in summaries.items():
                preview = summary[:80] + "..." if len(summary) > 80 else summary
                table.add_row(provider.upper(), str(len(summary)), preview)

            self.console.print(table)

    async def summarize_file(self):
        """Summarize content from a file."""
        try:
            file_path = Prompt.ask("[bold cyan]File path to summarize[/bold cyan]")

            if not os.path.exists(file_path):
                self.console.print(f"[red]File not found: {file_path}[/red]")
                return

            # Check file size (reasonable limit for summarization)
            file_size = os.path.getsize(file_path)
            if file_size > 100000:  # ~100KB limit
                self.console.print("[red]File too large for summarization (max 100KB)[/red]")
                return

            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            if not content.strip():
                self.console.print("[red]File is empty[/red]")
                return

            # Get providers (simplified for file mode)
            providers_input = Prompt.ask("[bold cyan]Providers (default: ollama)[/bold cyan]", default="ollama")
            providers = [p.strip() for p in providers_input.split(",") if p.strip()]

            provider_configs = []
            for provider in providers:
                config = {"name": provider}
                if provider == "ollama":
                    config["model"] = "llama3"
                    config["endpoint"] = "http://localhost:11434"
                provider_configs.append(config)

            request_data = {
                "text": content,
                "providers": provider_configs,
                "use_hub_config": True
            }

            with self.console.status(f"[bold green]Summarizing {os.path.basename(file_path)}...[/bold green]") as status:
                response = await self.clients.post_json("summarizer-hub/summarize/ensemble", request_data)

            if response:
                content_preview = f"File: {os.path.basename(file_path)} ({len(content)} chars)"
                await self.display_summarization_results(response, content_preview)
            else:
                self.console.print("[red]❌ Failed to summarize file[/red]")

        except Exception as e:
            self.console.print(f"[red]Error summarizing file: {e}[/red]")

    async def batch_summarization(self):
        """Perform batch summarization on multiple files."""
        try:
            directory = Prompt.ask("[bold cyan]Directory containing files to summarize[/bold cyan]")

            if not os.path.exists(directory):
                self.console.print(f"[red]Directory not found: {directory}[/red]")
                return

            import glob
            # Support common text file extensions
            file_pattern = Prompt.ask("[bold cyan]File pattern[/bold cyan]", default="*.txt,*.md")
            patterns = [p.strip() for p in file_pattern.split(",")]

            files = []
            for pattern in patterns:
                files.extend(glob.glob(os.path.join(directory, pattern)))

            if not files:
                self.console.print(f"[red]No files found matching patterns: {file_pattern}[/red]")
                return

            self.console.print(f"[yellow]Found {len(files)} files to summarize:[/yellow]")
            for i, file_path in enumerate(files[:5], 1):
                self.console.print(f"  {i}. {os.path.basename(file_path)}")

            if len(files) > 5:
                self.console.print(f"  ... and {len(files) - 5} more files")

            proceed = Confirm.ask(f"[bold cyan]Summarize {len(files)} files?[/bold cyan]", default=False)

            if proceed:
                # Simplified provider config for batch mode
                provider_configs = [{"name": "ollama", "model": "llama3", "endpoint": "http://localhost:11434"}]

                results = []
                for file_path in files:
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()

                        if content.strip():
                            request_data = {
                                "text": content[:50000],  # Limit content size
                                "providers": provider_configs,
                                "use_hub_config": True
                            }

                            response = await self.clients.post_json("summarizer-hub/summarize/ensemble", request_data)

                            if response and response.get("summaries"):
                                summary = list(response["summaries"].values())[0]
                                results.append({
                                    "file": os.path.basename(file_path),
                                    "summary": summary[:200] + "..." if len(summary) > 200 else summary,
                                    "status": "success"
                                })
                            else:
                                results.append({
                                    "file": os.path.basename(file_path),
                                    "summary": "Failed to generate summary",
                                    "status": "failed"
                                })
                        else:
                            results.append({
                                "file": os.path.basename(file_path),
                                "summary": "Empty file",
                                "status": "skipped"
                            })

                    except Exception as e:
                        results.append({
                            "file": os.path.basename(file_path),
                            "summary": f"Error: {str(e)[:50]}",
                            "status": "error"
                        })

                # Display batch results
                table = Table(title="Batch Summarization Results")
                table.add_column("File", style="cyan")
                table.add_column("Status", style="green")
                table.add_column("Summary Preview", style="white")

                for result in results:
                    status_icon = {
                        "success": "✅",
                        "failed": "❌",
                        "skipped": "⏭️",
                        "error": "⚠️"
                    }.get(result["status"], "❓")

                    table.add_row(
                        result["file"][:30] + "..." if len(result["file"]) > 30 else result["file"],
                        f"{status_icon} {result['status']}",
                        result["summary"][:50] + "..." if len(result["summary"]) > 50 else result["summary"]
                    )

                self.console.print(table)

        except Exception as e:
            self.console.print(f"[red]Error in batch summarization: {e}[/red]")

    async def interactive_summarization(self):
        """Interactive summarization console."""
        try:
            self.console.print("[yellow]Interactive Summarization Console[/yellow]")
            self.console.print("[yellow]Enter text to summarize (press Enter on empty line to finish):[/yellow]")

            provider_configs = [{"name": "ollama", "model": "llama3", "endpoint": "http://localhost:11434"}]

            while True:
                content = Prompt.ask("[bold cyan]Text[/bold cyan]")
                if not content.strip():
                    break

                request_data = {
                    "text": content,
                    "providers": provider_configs,
                    "use_hub_config": True
                }

                response = await self.clients.post_json("summarizer-hub/summarize/ensemble", request_data)

                if response and response.get("summaries"):
                    summary = list(response["summaries"].values())[0]
                    self.console.print(f"[green]Summary:[/green] {summary}")
                else:
                    self.console.print("[red]Failed to generate summary[/red]")

                continue_session = Confirm.ask("[bold cyan]Continue?[/bold cyan]", default=True)
                if not continue_session:
                    break

        except Exception as e:
            self.console.print(f"[red]Error in interactive summarization: {e}[/red]")

    async def custom_prompt_summarization(self):
        """Summarize with custom prompts."""
        try:
            text = Prompt.ask("[bold cyan]Text to summarize[/bold cyan]")
            custom_prompt = Prompt.ask("[bold cyan]Custom summarization prompt[/bold cyan]")

            if not text.strip():
                self.console.print("[red]No text provided[/red]")
                return

            provider_configs = [{"name": "ollama", "model": "llama3", "endpoint": "http://localhost:11434"}]

            request_data = {
                "text": text,
                "providers": provider_configs,
                "prompt": custom_prompt,
                "use_hub_config": True
            }

            with self.console.status("[bold green]Generating custom summary...[/bold green]") as status:
                response = await self.clients.post_json("summarizer-hub/summarize/ensemble", request_data)

            if response:
                await self.display_summarization_results(response, text)
            else:
                self.console.print("[red]❌ Failed to generate custom summary[/red]")

        except Exception as e:
            self.console.print(f"[red]Error with custom prompt: {e}[/red]")

    async def provider_comparison_mode(self):
        """Compare different providers side by side."""
        try:
            text = Prompt.ask("[bold cyan]Text to summarize[/bold cyan]")

            if not text.strip():
                self.console.print("[red]No text provided[/red]")
                return

            # Use multiple providers for comparison
            provider_configs = [
                {"name": "ollama", "model": "llama3", "endpoint": "http://localhost:11434"}
                # Add more providers as needed for comparison
            ]

            request_data = {
                "text": text,
                "providers": provider_configs,
                "use_hub_config": True
            }

            with self.console.status("[bold green]Comparing provider performance...[/bold green]") as status:
                response = await self.clients.post_json("summarizer-hub/summarize/ensemble", request_data)

            if response:
                await self.display_provider_comparison(response, text)
            else:
                self.console.print("[red]❌ Failed to compare providers[/red]")

        except Exception as e:
            self.console.print(f"[red]Error in provider comparison: {e}[/red]")

    async def display_provider_comparison(self, results: Dict[str, Any], text: str):
        """Display provider comparison results."""
        summaries = results.get("summaries", {})

        if len(summaries) <= 1:
            self.console.print("[yellow]Need multiple providers for meaningful comparison[/yellow]")
            return

        content = f"""
[bold]Provider Comparison Results[/bold]

[bold blue]Input Text:[/bold blue] {text[:100]}{'...' if len(text) > 100 else ''}

[bold green]Provider Summaries:[/bold green]
"""

        # Create comparison table
        table = Table(title="Provider Performance Comparison")
        table.add_column("Provider", style="cyan")
        table.add_column("Length", style="green", justify="right")
        table.add_column("Summary", style="white")

        for provider, summary in summaries.items():
            provider_icon = {
                "ollama": "🦙",
                "openai": "🤖",
                "anthropic": "🧠",
                "grok": "🚀",
                "bedrock": "☁️"
            }.get(provider, "🤖")

            table.add_row(
                f"{provider_icon} {provider.upper()}",
                str(len(summary)),
                summary[:80] + "..." if len(summary) > 80 else summary
            )

        self.console.print(table)

        # Show analysis
        analysis = results.get("analysis", {})
        if analysis:
            content += f"\n[bold yellow]Analysis:[/bold yellow]\n"
            if analysis.get('type'):
                content += f"• Analysis Type: {analysis['type']}\n"
            if analysis.get('insights'):
                content += f"• Insights: {analysis['insights'][:200]}...\n"

            print_panel(self.console, content, border_style="blue")

    async def provider_management_menu(self):
        """Provider management submenu."""
        while True:
            menu = create_menu_table("Provider Management", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "List Available Providers"),
                ("2", "Test Provider Connectivity"),
                ("3", "Configure Provider Settings"),
                ("4", "Provider Performance Testing"),
                ("5", "Manage Provider Credentials"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.list_providers()
            elif choice == "2":
                await self.test_provider_connectivity()
            elif choice == "3":
                await self.configure_provider_settings()
            elif choice == "4":
                await self.provider_performance_testing()
            elif choice == "5":
                await self.manage_provider_credentials()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def list_providers(self):
        """List all available providers."""
        try:
            providers = [
                {"name": "ollama", "type": "Local", "description": "Open-source LLM server"},
                {"name": "openai", "type": "Cloud", "description": "OpenAI GPT models"},
                {"name": "anthropic", "type": "Cloud", "description": "Anthropic Claude models"},
                {"name": "grok", "type": "Cloud", "description": "xAI Grok models"},
                {"name": "bedrock", "type": "Cloud", "description": "AWS Bedrock models"}
            ]

            table = Table(title="Available LLM Providers")
            table.add_column("Provider", style="cyan")
            table.add_column("Type", style="green")
            table.add_column("Description", style="white")

            for provider in providers:
                table.add_row(
                    provider["name"].upper(),
                    provider["type"],
                    provider["description"]
                )

            self.console.print(table)

            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error listing providers: {e}[/red]")

    async def test_provider_connectivity(self):
        """Test connectivity to providers."""
        try:
            provider = Prompt.ask("[bold cyan]Provider to test[/bold cyan]", default="ollama")

            # Create a simple test request
            test_config = {"name": provider}
            if provider == "ollama":
                test_config.update({
                    "model": "llama3",
                    "endpoint": "http://localhost:11434"
                })

            test_request = {
                "text": "Hello world",
                "providers": [test_config],
                "use_hub_config": False
            }

            with self.console.status(f"[bold green]Testing {provider} connectivity...[/bold green]") as status:
                response = await self.clients.post_json("summarizer-hub/summarize/ensemble", test_request)

            if response and response.get("summaries"):
                self.console.print(f"[green]✅ {provider.upper()} connection successful[/green]")
                if response.get("summaries", {}).get(provider):
                    summary = response["summaries"][provider]
                    self.console.print(f"[green]Test response: {summary[:100]}...[/green]")
            else:
                self.console.print(f"[red]❌ {provider.upper()} connection failed[/red]")

        except Exception as e:
            self.console.print(f"[red]Error testing provider connectivity: {e}[/red]")

    async def configure_provider_settings(self):
        """Configure provider settings."""
        try:
            self.console.print("[yellow]Provider configuration would allow setting endpoints, models, and credentials[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error configuring provider settings: {e}[/red]")

    async def provider_performance_testing(self):
        """Test provider performance."""
        try:
            self.console.print("[yellow]Performance testing would measure response times, quality scores, and reliability[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in performance testing: {e}[/red]")

    async def manage_provider_credentials(self):
        """Manage provider credentials."""
        try:
            self.console.print("[yellow]Credential management would securely store and rotate API keys[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error managing credentials: {e}[/red]")

    async def model_performance_menu(self):
        """Model performance analysis submenu."""
        while True:
            menu = create_menu_table("Model Performance Analysis", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Compare Model Outputs"),
                ("2", "Analyze Response Quality"),
                ("3", "Performance Benchmarking"),
                ("4", "Model Selection Recommendations"),
                ("5", "Cost-Performance Analysis"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.compare_model_outputs()
            elif choice == "2":
                await self.analyze_response_quality()
            elif choice == "3":
                await self.performance_benchmarking()
            elif choice == "4":
                await self.model_selection_recommendations()
            elif choice == "5":
                await self.cost_performance_analysis()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def compare_model_outputs(self):
        """Compare outputs from different models."""
        try:
            self.console.print("[yellow]Model output comparison would analyze differences in summarization quality[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error comparing model outputs: {e}[/red]")

    async def analyze_response_quality(self):
        """Analyze response quality metrics."""
        try:
            self.console.print("[yellow]Quality analysis would measure coherence, relevance, and factual accuracy[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error analyzing quality: {e}[/red]")

    async def performance_benchmarking(self):
        """Run performance benchmarks."""
        try:
            self.console.print("[yellow]Benchmarking would test speed, reliability, and resource usage[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in benchmarking: {e}[/red]")

    async def model_selection_recommendations(self):
        """Get model selection recommendations."""
        try:
            self.console.print("[yellow]Model recommendations would suggest optimal models based on use case[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error getting recommendations: {e}[/red]")

    async def cost_performance_analysis(self):
        """Analyze cost vs performance."""
        try:
            self.console.print("[yellow]Cost analysis would compare pricing with performance metrics[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in cost analysis: {e}[/red]")

    async def summarization_job_monitoring_menu(self):
        """Summarization job monitoring submenu."""
        while True:
            menu = create_menu_table("Summarization Job Monitoring", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "View Recent Jobs"),
                ("2", "Monitor Active Jobs"),
                ("3", "Job Performance Statistics"),
                ("4", "Failed Job Analysis"),
                ("5", "Job History and Trends"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.view_recent_jobs()
            elif choice == "2":
                await self.monitor_active_jobs()
            elif choice == "3":
                await self.job_performance_statistics()
            elif choice == "4":
                await self.failed_job_analysis()
            elif choice == "5":
                await self.job_history_trends()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def view_recent_jobs(self):
        """View recent summarization jobs."""
        try:
            self.console.print("[yellow]Recent jobs would show last N summarization operations[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error viewing recent jobs: {e}[/red]")

    async def monitor_active_jobs(self):
        """Monitor currently active jobs."""
        try:
            self.console.print("[yellow]Active job monitoring would show running summarization tasks[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error monitoring active jobs: {e}[/red]")

    async def job_performance_statistics(self):
        """Show job performance statistics."""
        try:
            self.console.print("[yellow]Performance stats would show response times, success rates, and throughput[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error showing performance stats: {e}[/red]")

    async def failed_job_analysis(self):
        """Analyze failed jobs."""
        try:
            self.console.print("[yellow]Failed job analysis would identify common failure patterns[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error analyzing failed jobs: {e}[/red]")

    async def job_history_trends(self):
        """Show job history and trends."""
        try:
            self.console.print("[yellow]Job history trends would show usage patterns over time[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error showing job trends: {e}[/red]")

    async def ai_operations_analytics_menu(self):
        """AI operations analytics submenu."""
        while True:
            menu = create_menu_table("AI Operations Analytics", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Provider Usage Analytics"),
                ("2", "Content Type Analysis"),
                ("3", "Quality Metrics Dashboard"),
                ("4", "Cost and Usage Tracking"),
                ("5", "AI Operations Reports"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.provider_usage_analytics()
            elif choice == "2":
                await self.content_type_analysis()
            elif choice == "3":
                await self.quality_metrics_dashboard()
            elif choice == "4":
                await self.cost_usage_tracking()
            elif choice == "5":
                await self.ai_operations_reports()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def provider_usage_analytics(self):
        """Analyze provider usage patterns."""
        try:
            self.console.print("[yellow]Provider usage analytics would show which models are used most[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in usage analytics: {e}[/red]")

    async def content_type_analysis(self):
        """Analyze content types being processed."""
        try:
            self.console.print("[yellow]Content type analysis would categorize processed documents[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in content analysis: {e}[/red]")

    async def quality_metrics_dashboard(self):
        """Show quality metrics dashboard."""
        try:
            self.console.print("[yellow]Quality metrics would show summarization accuracy and coherence scores[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error showing quality dashboard: {e}[/red]")

    async def cost_usage_tracking(self):
        """Track costs and usage."""
        try:
            self.console.print("[yellow]Cost tracking would monitor API usage costs across providers[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in cost tracking: {e}[/red]")

    async def ai_operations_reports(self):
        """Generate AI operations reports."""
        try:
            self.console.print("[yellow]AI operations reports would provide comprehensive analytics[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error generating reports: {e}[/red]")

    async def summarizer_hub_health_menu(self):
        """Summarizer hub health and configuration submenu."""
        while True:
            menu = create_menu_table("Summarizer Hub Health & Configuration", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "View Service Health"),
                ("2", "Rate Limiting Status"),
                ("3", "Provider Health Checks"),
                ("4", "Configuration Management"),
                ("5", "System Performance Monitoring"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.view_service_health()
            elif choice == "2":
                await self.rate_limiting_status()
            elif choice == "3":
                await self.provider_health_checks()
            elif choice == "4":
                await self.configuration_management()
            elif choice == "5":
                await self.system_performance_monitoring()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def view_service_health(self):
        """View summarizer hub service health."""
        try:
            response = await self.clients.get_json("summarizer-hub/health")

            if response:
                content = f"""
[bold]Summarizer Hub Health Status[/bold]

[bold blue]Status:[/bold blue] {response.get('status', 'unknown')}
[bold blue]Service:[/bold blue] {response.get('service', 'unknown')}
[bold blue]Version:[/bold blue] {response.get('version', 'unknown')}

[bold cyan]Description:[/bold cyan] {response.get('description', 'N/A')}
"""

                print_panel(self.console, content, border_style="green")
            else:
                self.console.print("[red]Failed to retrieve service health[/red]")

        except Exception as e:
            self.console.print(f"[red]Error viewing service health: {e}[/red]")

    async def rate_limiting_status(self):
        """Check rate limiting status."""
        try:
            self.console.print("[yellow]Rate limiting status would show current request rates and limits[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error checking rate limits: {e}[/red]")

    async def provider_health_checks(self):
        """Run provider health checks."""
        try:
            self.console.print("[yellow]Provider health checks would test connectivity to all configured providers[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error running health checks: {e}[/red]")

    async def configuration_management(self):
        """Manage summarizer hub configuration."""
        try:
            self.console.print("[yellow]Configuration management would allow editing hub settings[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in configuration management: {e}[/red]")

    async def system_performance_monitoring(self):
        """Monitor system performance."""
        try:
            self.console.print("[yellow]System performance monitoring would show CPU, memory, and throughput metrics[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in performance monitoring: {e}[/red]")

    async def summarize_from_cli(self, summarize_request: Dict[str, Any]):
        """Generate ensemble summary for CLI usage."""
        try:
            with self.console.status(f"[bold green]Generating ensemble summary...[/bold green]") as status:
                response = await self.clients.post_json("summarizer-hub/summarize/ensemble", summarize_request)

            if response:
                text = summarize_request.get("text", "")
                await self.display_summarization_results(response, text[:200] + "..." if len(text) > 200 else text)
            else:
                self.console.print("[red]❌ Failed to generate summary[/red]")

        except Exception as e:
            self.console.print(f"[red]Error generating summary: {e}[/red]")
