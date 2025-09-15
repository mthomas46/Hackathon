"""Secure Analyzer Manager module for CLI service.

Provides power-user operations for secure analyzer including
content detection, policy enforcement, and secure summarization.
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


class SecureAnalyzerManager:
    """Manager for secure analyzer power-user operations."""

    def __init__(self, console: Console, clients):
        self.console = console
        self.clients = clients

    async def secure_analyzer_menu(self):
        """Main secure analyzer menu."""
        while True:
            menu = create_menu_table("Secure Analyzer Management", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Content Security Analysis (Detection, scanning, validation)"),
                ("2", "Model Policy Management (Suggestions, restrictions, overrides)"),
                ("3", "Secure Summarization (Policy-filtered AI operations)"),
                ("4", "Security Policy Configuration"),
                ("5", "Compliance Reporting & Analytics"),
                ("6", "Secure Analyzer Health & Monitoring"),
                ("b", "Back to Main Menu")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.content_security_analysis_menu()
            elif choice == "2":
                await self.model_policy_management_menu()
            elif choice == "3":
                await self.secure_summarization_menu()
            elif choice == "4":
                await self.security_policy_config_menu()
            elif choice == "5":
                await self.compliance_reporting_menu()
            elif choice == "6":
                await self.secure_analyzer_monitoring_menu()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def content_security_analysis_menu(self):
        """Content security analysis submenu."""
        while True:
            menu = create_menu_table("Content Security Analysis", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Analyze Content for Sensitive Information"),
                ("2", "Batch Content Scanning"),
                ("3", "File-Based Content Analysis"),
                ("4", "Interactive Content Scanner"),
                ("5", "Security Pattern Testing"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.analyze_single_content()
            elif choice == "2":
                await self.batch_content_scanning()
            elif choice == "3":
                await self.file_based_analysis()
            elif choice == "4":
                await self.interactive_content_scanner()
            elif choice == "5":
                await self.security_pattern_testing()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def analyze_single_content(self):
        """Analyze a single piece of content for sensitive information."""
        try:
            self.console.print("[yellow]Enter content to analyze (press Ctrl+D on new line when done):[/yellow]")
            content_lines = []
            try:
                while True:
                    line = input()
                    content_lines.append(line)
            except EOFError:
                pass

            content = "\n".join(content_lines).strip()
            if not content:
                self.console.print("[red]No content provided[/red]")
                return

            # Get custom keywords
            add_keywords = Confirm.ask("[bold cyan]Add custom keywords?[/bold cyan]", default=False)
            keywords = None
            if add_keywords:
                keywords_input = Prompt.ask("[bold cyan]Keywords (comma-separated)[/bold cyan]")
                keywords = [k.strip() for k in keywords_input.split(",") if k.strip()]

            # Perform detection
            detect_request = {
                "content": content,
                "keywords": keywords
            }

            with self.console.status("[bold green]Analyzing content for security risks...[/bold green]") as status:
                response = await self.clients.post_json("secure-analyzer/detect", detect_request)

            if response:
                await self.display_detection_results(response, content[:200] + "..." if len(content) > 200 else content)
            else:
                self.console.print("[red]❌ Failed to analyze content[/red]")

        except KeyboardInterrupt:
            self.console.print("[yellow]Content input cancelled[/yellow]")
        except Exception as e:
            self.console.print(f"[red]Error analyzing content: {e}[/red]")

    async def display_detection_results(self, results: Dict[str, Any], content_preview: str):
        """Display content detection results in a formatted way."""
        sensitive = results.get("sensitive", False)
        matches = results.get("matches", [])
        topics = results.get("topics", [])

        status_icon = "🚨" if sensitive else "✅"
        status_text = "SENSITIVE CONTENT DETECTED" if sensitive else "CONTENT IS SAFE"

        content = f"""
[bold]Content Security Analysis Results[/bold]

[bold blue]Status:[/bold blue] {status_icon} {status_text}
[bold blue]Content Preview:[/bold blue] {content_preview}

[bold green]Security Topics Detected:[/bold green] {len(topics)}
"""

        if topics:
            content += "\n[bold yellow]Topics:[/bold yellow]\n"
            for topic in topics:
                content += f"• {topic}\n"

        content += f"\n[bold red]Security Matches Found:[/bold red] {len(matches)}\n"

        if matches:
            for i, match in enumerate(matches[:10], 1):  # Show first 10
                content += f"{i:2d}. {match}\n"
            if len(matches) > 10:
                content += f"    ... and {len(matches) - 10} more matches\n"

        # Risk assessment
        risk_level = "HIGH" if sensitive and len(matches) > 3 else "MEDIUM" if sensitive else "LOW"
        risk_color = {"HIGH": "red", "MEDIUM": "yellow", "LOW": "green"}.get(risk_level, "white")

        content += f"\n[bold {risk_color}]Risk Assessment: {risk_level}[/bold {risk_color}]"

        if sensitive:
            content += "\n\n[bold red]⚠️  SECURITY RECOMMENDATIONS:[/bold red]"
            content += "\n• Avoid using sensitive AI models for this content"
            content += "\n• Consider content redaction before processing"
            content += "\n• Review data handling policies"
            if "pii" in topics:
                content += "\n• Contains PII - ensure GDPR/HIPAA compliance"
            if "secrets" in topics or "credentials" in topics:
                content += "\n• Contains secrets - never log or store unencrypted"

        print_panel(self.console, content, border_style="red" if sensitive else "green")

    async def batch_content_scanning(self):
        """Perform batch content scanning."""
        try:
            self.console.print("[yellow]Batch content scanning allows processing multiple content items[/yellow]")
            self.console.print("[yellow]This would process files or datasets for security analysis[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in batch scanning: {e}[/red]")

    async def file_based_analysis(self):
        """Analyze content from files."""
        try:
            file_path = Prompt.ask("[bold cyan]File path to analyze[/bold cyan]")

            if not os.path.exists(file_path):
                self.console.print(f"[red]File not found: {file_path}[/red]")
                return

            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > 1000000:  # 1MB limit
                self.console.print("[red]File too large (max 1MB)[/red]")
                return

            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            if not content.strip():
                self.console.print("[red]File is empty or unreadable[/red]")
                return

            # Get custom keywords
            keywords = None
            if file_path.endswith(('.py', '.js', '.java', '.cpp', '.c', '.h')):
                keywords = ['password', 'secret', 'key', 'token', 'api_key']

            detect_request = {
                "content": content,
                "keywords": keywords
            }

            with self.console.status(f"[bold green]Analyzing {os.path.basename(file_path)}...[/bold green]") as status:
                response = await self.clients.post_json("secure-analyzer/detect", detect_request)

            if response:
                content_preview = f"File: {os.path.basename(file_path)} ({len(content)} chars)"
                await self.display_detection_results(response, content_preview)
            else:
                self.console.print("[red]❌ Failed to analyze file[/red]")

        except Exception as e:
            self.console.print(f"[red]Error analyzing file: {e}[/red]")

    async def interactive_content_scanner(self):
        """Interactive content scanner for real-time analysis."""
        try:
            self.console.print("[yellow]Interactive Content Scanner[/yellow]")
            self.console.print("[yellow]Type content to scan (press Enter on empty line to finish):[/yellow]")

            while True:
                content = Prompt.ask("[bold cyan]Content[/bold cyan]")
                if not content.strip():
                    break

                detect_request = {"content": content}

                response = await self.clients.post_json("secure-analyzer/detect", detect_request)

                if response and response.get("sensitive"):
                    self.console.print("[red]🚨 SENSITIVE CONTENT DETECTED![/red]")
                    matches = response.get("matches", [])
                    if matches:
                        self.console.print(f"[red]Matches: {', '.join(matches[:3])}{'...' if len(matches) > 3 else ''}[/red]")
                else:
                    self.console.print("[green]✅ Content appears safe[/green]")

                continue_scan = Confirm.ask("[bold cyan]Continue scanning?[/bold cyan]", default=True)
                if not continue_scan:
                    break

        except Exception as e:
            self.console.print(f"[red]Error in interactive scanner: {e}[/red]")

    async def security_pattern_testing(self):
        """Test security patterns and detection rules."""
        try:
            self.console.print("[yellow]Security Pattern Testing[/yellow]")
            self.console.print("[yellow]Test various patterns to validate detection rules[/yellow]")

            test_patterns = {
                "API Key": "sk-1234567890abcdef1234567890abcdef",
                "Password": "mySecretPassword123!",
                "Database URL": "postgres://user:password123@localhost:5432/mydb",
                "Credit Card": "4111-1111-1111-1111",
                "SSN": "123-45-6789",
                "Email": "user@example.com",
                "IP Address": "192.168.1.100",
                "JWT Token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
            }

            results = []
            for pattern_name, test_content in test_patterns.items():
                detect_request = {"content": test_content}

                try:
                    response = await self.clients.post_json("secure-analyzer/detect", detect_request)
                    detected = response.get("sensitive", False) if response else False
                    results.append({
                        "pattern": pattern_name,
                        "content": test_content[:50] + "..." if len(test_content) > 50 else test_content,
                        "detected": detected,
                        "matches": len(response.get("matches", [])) if response else 0
                    })
                except Exception as e:
                    results.append({
                        "pattern": pattern_name,
                        "content": test_content[:50] + "..." if len(test_content) > 50 else test_content,
                        "detected": False,
                        "matches": 0,
                        "error": str(e)
                    })

            # Display results
            table = Table(title="Security Pattern Detection Test Results")
            table.add_column("Pattern", style="cyan")
            table.add_column("Content", style="white")
            table.add_column("Detected", style="green")
            table.add_column("Matches", style="yellow", justify="right")

            for result in results:
                detected_str = "✅ Yes" if result["detected"] else "❌ No"
                detected_style = "green" if result["detected"] else "red"

                table.add_row(
                    result["pattern"],
                    result["content"],
                    f"[{detected_style}]{detected_str}[/{detected_style}]",
                    str(result["matches"])
                )

            self.console.print(table)

        except Exception as e:
            self.console.print(f"[red]Error testing patterns: {e}[/red]")

    async def model_policy_management_menu(self):
        """Model policy management submenu."""
        while True:
            menu = create_menu_table("Model Policy Management", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Get Model Suggestions for Content"),
                ("2", "View Security Policies"),
                ("3", "Test Policy Enforcement"),
                ("4", "Override Policy Restrictions"),
                ("5", "Policy Compliance Checking"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.get_model_suggestions()
            elif choice == "2":
                await self.view_security_policies()
            elif choice == "3":
                await self.test_policy_enforcement()
            elif choice == "4":
                await self.override_policy_restrictions()
            elif choice == "5":
                await self.policy_compliance_checking()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def get_model_suggestions(self):
        """Get AI model suggestions based on content sensitivity."""
        try:
            self.console.print("[yellow]Enter content to get model suggestions for:[/yellow]")
            content = Prompt.ask("[bold cyan]Content[/bold cyan]")

            if not content.strip():
                self.console.print("[red]No content provided[/red]")
                return

            suggest_request = {"content": content}

            with self.console.status("[bold green]Getting model suggestions...[/bold green]") as status:
                response = await self.clients.post_json("secure-analyzer/suggest", suggest_request)

            if response:
                await self.display_model_suggestions(response, content)
            else:
                self.console.print("[red]❌ Failed to get model suggestions[/red]")

        except Exception as e:
            self.console.print(f"[red]Error getting suggestions: {e}[/red]")

    async def display_model_suggestions(self, results: Dict[str, Any], content: str):
        """Display model suggestions in a formatted way."""
        sensitive = results.get("sensitive", False)
        allowed_models = results.get("allowed_models", [])
        suggestion = results.get("suggestion", "")

        content = f"""
[bold]AI Model Suggestions[/bold]

[bold blue]Content Sensitivity:[/bold blue] {'🚨 SENSITIVE' if sensitive else '✅ SAFE'}
[bold blue]Content Preview:[/bold blue] {content[:100]}{'...' if len(content) > 100 else ''}

[bold green]Suggested Models:[/bold green] {len(allowed_models)}
"""

        if allowed_models:
            content += "\n[bold cyan]Allowed Models:[/bold cyan]\n"
            for i, model in enumerate(allowed_models, 1):
                content += f"{i}. {model}\n"

        content += f"\n[bold yellow]Policy Suggestion:[/bold yellow]\n{suggestion}"

        if sensitive:
            content += "\n\n[bold red]⚠️  SECURITY NOTICE:[/bold red]"
            content += "\n• Content contains sensitive information"
            content += "\n• Only approved models can be used"
            content += "\n• Additional security measures recommended"

        print_panel(self.console, content, border_style="yellow" if sensitive else "green")

    async def view_security_policies(self):
        """View current security policies."""
        try:
            self.console.print("[yellow]Security Policy Information[/yellow]")
            self.console.print("[yellow]• Sensitive content requires approved AI models only[/yellow]")
            self.console.print("[yellow]• PII, secrets, and credentials trigger restrictions[/yellow]")
            self.console.print("[yellow]• Policy overrides require explicit approval[/yellow]")
            self.console.print("[yellow]• Circuit breaker protects against cascade failures[/yellow]")

            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error viewing policies: {e}[/red]")

    async def test_policy_enforcement(self):
        """Test policy enforcement with various content types."""
        try:
            test_cases = [
                ("Safe content", "This is a normal document about software development."),
                ("Sensitive content", "User password: secret123, API key: sk-1234567890abcdef"),
                ("PII content", "Social Security: 123-45-6789, Credit card: 4111-1111-1111-1111"),
                ("Mixed content", "Normal text with password: mypass123 and email: user@domain.com")
            ]

            results = []
            for case_name, test_content in test_cases:
                suggest_request = {"content": test_content}

                try:
                    response = await self.clients.post_json("secure-analyzer/suggest", suggest_request)
                    if response:
                        results.append({
                            "case": case_name,
                            "sensitive": response.get("sensitive", False),
                            "models_allowed": len(response.get("allowed_models", [])),
                            "suggestion": response.get("suggestion", "")[:50] + "..."
                        })
                    else:
                        results.append({
                            "case": case_name,
                            "sensitive": False,
                            "models_allowed": 0,
                            "suggestion": "Request failed"
                        })
                except Exception as e:
                    results.append({
                        "case": case_name,
                        "sensitive": False,
                        "models_allowed": 0,
                        "suggestion": f"Error: {str(e)[:30]}"
                    })

            # Display results
            table = Table(title="Policy Enforcement Test Results")
            table.add_column("Test Case", style="cyan")
            table.add_column("Sensitive", style="red")
            table.add_column("Models Allowed", style="green", justify="right")
            table.add_column("Policy Action", style="yellow")

            for result in results:
                sensitive_str = "🚨 Yes" if result["sensitive"] else "✅ No"
                sensitive_style = "red" if result["sensitive"] else "green"

                table.add_row(
                    result["case"],
                    f"[{sensitive_style}]{sensitive_str}[/{sensitive_style}]",
                    str(result["models_allowed"]),
                    result["suggestion"]
                )

            self.console.print(table)

        except Exception as e:
            self.console.print(f"[red]Error testing policy enforcement: {e}[/red]")

    async def override_policy_restrictions(self):
        """Override policy restrictions for special cases."""
        try:
            self.console.print("[yellow]Policy Override Functionality[/yellow]")
            self.console.print("[yellow]This would allow bypassing security restrictions for approved cases[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error with policy override: {e}[/red]")

    async def policy_compliance_checking(self):
        """Check policy compliance across operations."""
        try:
            self.console.print("[yellow]Policy Compliance Checking[/yellow]")
            self.console.print("[yellow]This would audit past operations for policy compliance[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error checking compliance: {e}[/red]")

    async def secure_summarization_menu(self):
        """Secure summarization submenu."""
        while True:
            menu = create_menu_table("Secure Summarization", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Generate Secure Summary"),
                ("2", "Summarize File Content"),
                ("3", "Batch Summarization"),
                ("4", "Custom Prompt Summarization"),
                ("5", "Provider-Specific Summarization"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.generate_secure_summary()
            elif choice == "2":
                await self.summarize_file_content()
            elif choice == "3":
                await self.batch_summarization()
            elif choice == "4":
                await self.custom_prompt_summarization()
            elif choice == "5":
                await self.provider_specific_summarization()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def generate_secure_summary(self):
        """Generate a secure summary of content."""
        try:
            self.console.print("[yellow]Enter content to summarize securely:[/yellow]")
            content = Prompt.ask("[bold cyan]Content[/bold cyan]")

            if not content.strip():
                self.console.print("[red]No content provided[/red]")
                return

            override_policy = Confirm.ask("[bold cyan]Override security policy?[/bold cyan]", default=False)

            summarize_request = {
                "content": content,
                "override_policy": override_policy
            }

            with self.console.status("[bold green]Generating secure summary...[/bold green]") as status:
                response = await self.clients.post_json("secure-analyzer/summarize", summarize_request)

            if response:
                await self.display_secure_summary(response, content)
            else:
                self.console.print("[red]❌ Failed to generate summary[/red]")

        except Exception as e:
            self.console.print(f"[red]Error generating summary: {e}[/red]")

    async def display_secure_summary(self, results: Dict[str, Any], original_content: str):
        """Display secure summary results."""
        summary = results.get("summary", "No summary generated")
        provider_used = results.get("provider_used", "unknown")
        confidence = results.get("confidence", 0.0)
        word_count = results.get("word_count", 0)
        topics_detected = results.get("topics_detected", [])
        policy_enforced = results.get("policy_enforced", False)

        content = f"""
[bold]Secure Content Summary[/bold]

[bold blue]Provider Used:[/bold blue] {provider_used}
[bold blue]Confidence:[/bold blue] {confidence:.2f}
[bold blue]Original Word Count:[/bold blue] {word_count}
[bold blue]Security Policy Enforced:[/bold blue] {'✅ Yes' if policy_enforced else '❌ No'}

[bold green]Security Topics Detected:[/bold green] {len(topics_detected)}
"""

        if topics_detected:
            content += "\n[bold yellow]Topics:[/bold yellow] " + ", ".join(topics_detected[:5])
            if len(topics_detected) > 5:
                content += f" ... and {len(topics_detected) - 5} more"

        content += f"\n\n[bold cyan]Summary:[/bold cyan]\n{summary}"

        if policy_enforced:
            content += "\n\n[bold red]⚠️  SECURITY MEASURES APPLIED:[/bold red]"
            content += "\n• Content filtered through security policies"
            content += "\n• Only approved AI models used"
            content += "\n• Sensitive information protected"

        print_panel(self.console, content, border_style="green" if confidence > 0.7 else "yellow")

    async def summarize_file_content(self):
        """Summarize content from a file."""
        try:
            file_path = Prompt.ask("[bold cyan]File path to summarize[/bold cyan]")

            if not os.path.exists(file_path):
                self.console.print(f"[red]File not found: {file_path}[/red]")
                return

            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            if not content.strip():
                self.console.print("[red]File is empty[/red]")
                return

            override_policy = Confirm.ask("[bold cyan]Override security policy?[/bold cyan]", default=False)

            summarize_request = {
                "content": content,
                "override_policy": override_policy
            }

            with self.console.status(f"[bold green]Summarizing {os.path.basename(file_path)}...[/bold green]") as status:
                response = await self.clients.post_json("secure-analyzer/summarize", summarize_request)

            if response:
                content_preview = f"File: {os.path.basename(file_path)} ({len(content)} chars)"
                await self.display_secure_summary(response, content_preview)
            else:
                self.console.print("[red]❌ Failed to summarize file[/red]")

        except Exception as e:
            self.console.print(f"[red]Error summarizing file: {e}[/red]")

    async def batch_summarization(self):
        """Perform batch summarization."""
        try:
            self.console.print("[yellow]Batch summarization would process multiple documents[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in batch summarization: {e}[/red]")

    async def custom_prompt_summarization(self):
        """Summarize with custom prompts."""
        try:
            content = Prompt.ask("[bold cyan]Content to summarize[/bold cyan]")
            custom_prompt = Prompt.ask("[bold cyan]Custom prompt[/bold cyan]")

            if not content.strip():
                self.console.print("[red]No content provided[/red]")
                return

            summarize_request = {
                "content": content,
                "prompt": custom_prompt
            }

            with self.console.status("[bold green]Generating custom summary...[/bold green]") as status:
                response = await self.clients.post_json("secure-analyzer/summarize", summarize_request)

            if response:
                await self.display_secure_summary(response, content)
            else:
                self.console.print("[red]❌ Failed to generate custom summary[/red]")

        except Exception as e:
            self.console.print(f"[red]Error with custom prompt: {e}[/red]")

    async def provider_specific_summarization(self):
        """Summarize with specific provider configuration."""
        try:
            self.console.print("[yellow]Provider-specific summarization allows targeting specific AI models[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error with provider-specific summarization: {e}[/red]")

    async def security_policy_config_menu(self):
        """Security policy configuration submenu."""
        while True:
            menu = create_menu_table("Security Policy Configuration", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "View Current Policies"),
                ("2", "Configure Detection Patterns"),
                ("3", "Set Model Restrictions"),
                ("4", "Circuit Breaker Settings"),
                ("5", "Policy Override Rules"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.view_current_policies()
            elif choice == "2":
                await self.configure_detection_patterns()
            elif choice == "3":
                await self.set_model_restrictions()
            elif choice == "4":
                await self.circuit_breaker_settings()
            elif choice == "5":
                await self.policy_override_rules()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def view_current_policies(self):
        """View current security policies."""
        try:
            self.console.print("[yellow]Current Security Policies:[/yellow]")
            self.console.print("[yellow]• Content Detection: PII, secrets, credentials, sensitive keywords[/yellow]")
            self.console.print("[yellow]• Model Restrictions: Sensitive content limited to approved models[/yellow]")
            self.console.print("[yellow]• Circuit Breaker: Automatic failure protection[/yellow]")
            self.console.print("[yellow]• Override Controls: Administrative policy bypass capabilities[/yellow]")

            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error viewing policies: {e}[/red]")

    async def configure_detection_patterns(self):
        """Configure detection patterns."""
        try:
            self.console.print("[yellow]Detection pattern configuration would allow customizing security rules[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error configuring patterns: {e}[/red]")

    async def set_model_restrictions(self):
        """Set model restrictions."""
        try:
            self.console.print("[yellow]Model restriction settings control which AI models can process content[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error setting restrictions: {e}[/red]")

    async def circuit_breaker_settings(self):
        """Configure circuit breaker settings."""
        try:
            self.console.print("[yellow]Circuit breaker prevents cascade failures and protects system stability[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error with circuit breaker: {e}[/red]")

    async def policy_override_rules(self):
        """Configure policy override rules."""
        try:
            self.console.print("[yellow]Policy override rules define when security policies can be bypassed[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error with override rules: {e}[/red]")

    async def compliance_reporting_menu(self):
        """Compliance reporting and analytics submenu."""
        while True:
            menu = create_menu_table("Compliance Reporting & Analytics", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Security Audit Report"),
                ("2", "Content Sensitivity Analytics"),
                ("3", "Policy Violation Tracking"),
                ("4", "Compliance Dashboard"),
                ("5", "Security Incident Log"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.security_audit_report()
            elif choice == "2":
                await self.content_sensitivity_analytics()
            elif choice == "3":
                await self.policy_violation_tracking()
            elif choice == "4":
                await self.compliance_dashboard()
            elif choice == "5":
                await self.security_incident_log()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def security_audit_report(self):
        """Generate security audit report."""
        try:
            self.console.print("[yellow]Security audit reports would show historical security analysis[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error generating audit report: {e}[/red]")

    async def content_sensitivity_analytics(self):
        """Analyze content sensitivity trends."""
        try:
            self.console.print("[yellow]Content sensitivity analytics would show trends in detected content[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error with sensitivity analytics: {e}[/red]")

    async def policy_violation_tracking(self):
        """Track policy violations."""
        try:
            self.console.print("[yellow]Policy violation tracking would monitor security policy compliance[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error tracking violations: {e}[/red]")

    async def compliance_dashboard(self):
        """Show compliance dashboard."""
        try:
            self.console.print("[yellow]Compliance dashboard would provide real-time security metrics[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error with compliance dashboard: {e}[/red]")

    async def security_incident_log(self):
        """View security incident log."""
        try:
            self.console.print("[yellow]Security incident log would track security-related events[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error with incident log: {e}[/red]")

    async def secure_analyzer_monitoring_menu(self):
        """Secure analyzer health and monitoring submenu."""
        while True:
            menu = create_menu_table("Secure Analyzer Health & Monitoring", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "View Service Health"),
                ("2", "Circuit Breaker Status"),
                ("3", "Performance Metrics"),
                ("4", "Error Rate Monitoring"),
                ("5", "Service Logs"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.view_service_health()
            elif choice == "2":
                await self.circuit_breaker_status()
            elif choice == "3":
                await self.performance_metrics()
            elif choice == "4":
                await self.error_rate_monitoring()
            elif choice == "5":
                await self.service_logs()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def view_service_health(self):
        """View secure analyzer service health."""
        try:
            response = await self.clients.get_json("secure-analyzer/health")

            if response:
                circuit_open = response.get("circuit_breaker_open", False)

                content = f"""
[bold]Secure Analyzer Health Status[/bold]

[bold blue]Status:[/bold blue] {response.get('status', 'unknown')}
[bold blue]Service:[/bold blue] {response.get('service', 'unknown')}
[bold blue]Version:[/bold blue] {response.get('version', 'unknown')}

[bold green]Circuit Breaker:[/bold green] {'🔴 OPEN' if circuit_open else '🟢 CLOSED'}
"""

                if circuit_open:
                    content += "\n[bold red]⚠️  Circuit breaker is open - service is temporarily unavailable[/bold red]"

                print_panel(self.console, content, border_style="red" if circuit_open else "green")
            else:
                self.console.print("[red]Failed to retrieve service health[/red]")

        except Exception as e:
            self.console.print(f"[red]Error viewing service health: {e}[/red]")

    async def circuit_breaker_status(self):
        """Check circuit breaker status."""
        try:
            response = await self.clients.get_json("secure-analyzer/health")

            if response:
                circuit_open = response.get("circuit_breaker_open", False)

                status = "OPEN (blocking requests)" if circuit_open else "CLOSED (normal operation)"
                icon = "🔴" if circuit_open else "🟢"

                self.console.print(f"[bold]Circuit Breaker Status: {icon} {status}[/bold]")

                if circuit_open:
                    self.console.print("[yellow]The circuit breaker opens when too many failures occur[/yellow]")
                    self.console.print("[yellow]This protects the system from cascade failures[/yellow]")
                else:
                    self.console.print("[green]Service is operating normally[/green]")

            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error checking circuit breaker: {e}[/red]")

    async def performance_metrics(self):
        """View performance metrics."""
        try:
            self.console.print("[yellow]Performance metrics would show response times, throughput, etc.[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error viewing metrics: {e}[/red]")

    async def error_rate_monitoring(self):
        """Monitor error rates."""
        try:
            self.console.print("[yellow]Error rate monitoring would track failure rates and patterns[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error monitoring rates: {e}[/red]")

    async def service_logs(self):
        """View service logs."""
        try:
            self.console.print("[yellow]Service logs would show recent secure analyzer operations[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error viewing logs: {e}[/red]")

    async def detect_content_from_cli(self, detect_request: Dict[str, Any]):
        """Detect sensitive content for CLI usage (no interactive prompts)."""
        try:
            with self.console.status(f"[bold green]Detecting sensitive content...[/bold green]") as status:
                response = await self.clients.post_json("secure-analyzer/detect", detect_request)

            if response:
                await self.display_detection_results(response, detect_request.get("content", "")[:200] + "...")
            else:
                self.console.print("[red]❌ Content detection failed[/red]")

        except Exception as e:
            self.console.print(f"[red]Error detecting content: {e}[/red]")

    async def suggest_models_from_cli(self, suggest_request: Dict[str, Any]):
        """Get model suggestions for CLI usage."""
        try:
            with self.console.status(f"[bold green]Getting model suggestions...[/bold green]") as status:
                response = await self.clients.post_json("secure-analyzer/suggest", suggest_request)

            if response:
                await self.display_model_suggestions(response, suggest_request.get("content", ""))
            else:
                self.console.print("[red]❌ Failed to get suggestions[/red]")

        except Exception as e:
            self.console.print(f"[red]Error getting suggestions: {e}[/red]")

    async def summarize_content_from_cli(self, summarize_request: Dict[str, Any]):
        """Generate secure summary for CLI usage."""
        try:
            with self.console.status(f"[bold green]Generating secure summary...[/bold green]") as status:
                response = await self.clients.post_json("secure-analyzer/summarize", summarize_request)

            if response:
                await self.display_secure_summary(response, summarize_request.get("content", ""))
            else:
                self.console.print("[red]❌ Failed to generate summary[/red]")

        except Exception as e:
            self.console.print(f"[red]Error generating summary: {e}[/red]")
