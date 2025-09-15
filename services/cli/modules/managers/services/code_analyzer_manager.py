"""Code Analyzer Manager module for CLI service.

Provides power-user operations for code analyzer including
code analysis, security scanning, style checking, and analysis history.
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
import subprocess

from ...shared_utils import (
    get_cli_clients,
    create_menu_table,
    add_menu_rows,
    print_panel,
    log_cli_metrics
)


class CodeAnalyzerManager:
    """Manager for code analyzer power-user operations."""

    def __init__(self, console: Console, clients):
        self.console = console
        self.clients = clients

    async def code_analyzer_menu(self):
        """Main code analyzer menu."""
        while True:
            menu = create_menu_table("Code Analyzer Management", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Code Analysis (Endpoint extraction, pattern analysis)"),
                ("2", "File & Repository Analysis"),
                ("3", "Git Integration (Patch analysis, CI/CD)"),
                ("4", "Security Scanning (Vulnerability detection, secret scanning)"),
                ("5", "Style Management (Programming standards, examples)"),
                ("6", "Analysis History & Reporting"),
                ("7", "Code Analyzer Health & Configuration"),
                ("b", "Back to Main Menu")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.code_analysis_menu()
            elif choice == "2":
                await self.file_repository_analysis_menu()
            elif choice == "3":
                await self.git_integration_menu()
            elif choice == "4":
                await self.security_scanning_menu()
            elif choice == "5":
                await self.style_management_menu()
            elif choice == "6":
                await self.analysis_history_menu()
            elif choice == "7":
                await self.code_analyzer_health_menu()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def code_analysis_menu(self):
        """Code analysis submenu."""
        while True:
            menu = create_menu_table("Code Analysis", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Analyze Code Snippet"),
                ("2", "Analyze with Custom Style Examples"),
                ("3", "Interactive Code Analysis"),
                ("4", "Batch Code Analysis"),
                ("5", "Language-Specific Analysis"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.analyze_code_snippet()
            elif choice == "2":
                await self.analyze_with_custom_style()
            elif choice == "3":
                await self.interactive_code_analysis()
            elif choice == "4":
                await self.batch_code_analysis()
            elif choice == "5":
                await self.language_specific_analysis()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def analyze_code_snippet(self):
        """Analyze a code snippet for API endpoints and patterns."""
        try:
            self.console.print("[yellow]Enter code snippet to analyze (press Ctrl+D on new line when done):[/yellow]")
            code_lines = []
            try:
                while True:
                    line = input()
                    code_lines.append(line)
            except EOFError:
                pass

            code = "\n".join(code_lines).strip()
            if not code:
                self.console.print("[red]No code provided[/red]")
                return

            # Get analysis parameters
            language = Prompt.ask("[bold cyan]Programming language[/bold cyan]", default="")
            repo = Prompt.ask("[bold cyan]Repository name (optional)[/bold cyan]", default="")
            path = Prompt.ask("[bold cyan]File path (optional)[/bold cyan]", default="")
            correlation_id = Prompt.ask("[bold cyan]Correlation ID (optional)[/bold cyan]", default="")

            analysis_request = {
                "content": code,
                "language": language if language else None,
                "repo": repo if repo else None,
                "path": path if path else None,
                "correlation_id": correlation_id if correlation_id else None
            }

            with self.console.status("[bold green]Analyzing code for endpoints and patterns...[/bold green]") as status:
                response = await self.clients.post_json("code-analyzer/analyze/text", analysis_request)

            if response:
                await self.display_code_analysis_results(response, code[:200] + "..." if len(code) > 200 else code)
            else:
                self.console.print("[red]❌ Failed to analyze code[/red]")

        except KeyboardInterrupt:
            self.console.print("[yellow]Code analysis cancelled[/yellow]")
        except Exception as e:
            self.console.print(f"[red]Error analyzing code: {e}[/red]")

    async def display_code_analysis_results(self, results: Dict[str, Any], code_preview: str):
        """Display code analysis results in a formatted way."""
        document = results.get("document", {})
        metadata = document.get("metadata", {})
        source_link = metadata.get("source_link", {})
        style_examples_used = metadata.get("style_examples_used", [])

        content = f"""
[bold]Code Analysis Results[/bold]

[bold blue]Analysis ID:[/bold blue] {results.get('id', 'N/A')}
[bold blue]Code Preview:[/bold blue] {code_preview}
[bold blue]Repository:[/bold blue] {source_link.get('repo', 'N/A')}
[bold blue]File Path:[/bold blue] {source_link.get('path', 'N/A')}

[bold green]Content Hash:[/bold green] {results.get('content_hash', 'N/A')}
[bold green]Correlation ID:[/bold green] {results.get('correlation_id', 'N/A')}
"""

        # Extract and display endpoints from content
        analysis_content = document.get("content", "")
        if analysis_content and "(no endpoints)" not in analysis_content:
            content += f"\n[bold cyan]Extracted Endpoints:[/bold cyan]\n"
            endpoints = [line.strip() for line in analysis_content.split('\n') if line.strip()]
            for endpoint in endpoints:
                content += f"• {endpoint}\n"
        else:
            content += "\n[bold yellow]No endpoints detected in the code[/bold yellow]"

        if style_examples_used:
            content += f"\n[bold magenta]Style Examples Applied:[/bold magenta] {len(style_examples_used)}"

        print_panel(self.console, content, border_style="blue")

        # Show detailed metadata if available
        if metadata:
            metadata_table = Table(title="Analysis Metadata")
            metadata_table.add_column("Key", style="cyan")
            metadata_table.add_column("Value", style="white")

            for key, value in metadata.items():
                if key != "source_link":  # Already shown above
                    metadata_table.add_row(key, str(value)[:50] + "..." if len(str(value)) > 50 else str(value))

            self.console.print(metadata_table)

    async def analyze_with_custom_style(self):
        """Analyze code with custom style examples."""
        try:
            code = Prompt.ask("[bold cyan]Code to analyze[/bold cyan]")
            language = Prompt.ask("[bold cyan]Programming language[/bold cyan]")

            if not code.strip():
                self.console.print("[red]No code provided[/red]")
                return

            # Create custom style example
            style_example = {
                "language": language,
                "snippet": "def good_function_name(param1, param2):\n    \"\"\"Good docstring\"\"\"\n    return param1 + param2",
                "title": "Good Function Style",
                "description": "Example of proper function naming and documentation",
                "purpose": "style_guidance",
                "tags": ["functions", "naming", "documentation"]
            }

            analysis_request = {
                "content": code,
                "language": language,
                "style_examples": [style_example]
            }

            with self.console.status("[bold green]Analyzing code with custom style...[/bold green]") as status:
                response = await self.clients.post_json("code-analyzer/analyze/text", analysis_request)

            if response:
                await self.display_code_analysis_results(response, code)
            else:
                self.console.print("[red]❌ Failed to analyze code with custom style[/red]")

        except Exception as e:
            self.console.print(f"[red]Error in custom style analysis: {e}[/red]")

    async def interactive_code_analysis(self):
        """Interactive code analysis console."""
        try:
            self.console.print("[yellow]Interactive Code Analysis Console[/yellow]")
            self.console.print("[yellow]Enter code snippets to analyze (press Enter on empty line to finish):[/yellow]")

            while True:
                code = Prompt.ask("[bold cyan]Code snippet[/bold cyan]")
                if not code.strip():
                    break

                analysis_request = {"content": code}

                response = await self.clients.post_json("code-analyzer/analyze/text", analysis_request)

                if response:
                    document = response.get("document", {})
                    content = document.get("content", "")
                    if content and "(no endpoints)" not in content:
                        endpoints = [line.strip() for line in content.split('\n') if line.strip() and line.strip() != "(no endpoints)"]
                        if endpoints:
                            self.console.print(f"[green]✅ Found {len(endpoints)} endpoint(s):[/green]")
                            for endpoint in endpoints[:3]:  # Show first 3
                                self.console.print(f"  • {endpoint}")
                            if len(endpoints) > 3:
                                self.console.print(f"  ... and {len(endpoints) - 3} more")
                        else:
                            self.console.print("[yellow]No endpoints detected[/yellow]")
                    else:
                        self.console.print("[yellow]No endpoints detected[/yellow]")
                else:
                    self.console.print("[red]Analysis failed[/red]")

                continue_analysis = Confirm.ask("[bold cyan]Continue analyzing?[/bold cyan]", default=True)
                if not continue_analysis:
                    break

        except Exception as e:
            self.console.print(f"[red]Error in interactive analysis: {e}[/red]")

    async def batch_code_analysis(self):
        """Perform batch code analysis."""
        try:
            self.console.print("[yellow]Batch code analysis allows processing multiple code snippets[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in batch analysis: {e}[/red]")

    async def language_specific_analysis(self):
        """Perform language-specific code analysis."""
        try:
            languages = ["python", "javascript", "typescript", "java", "go", "rust", "cpp", "csharp"]

            self.console.print("[yellow]Available languages:[/yellow]")
            for i, lang in enumerate(languages, 1):
                self.console.print(f"  {i}. {lang}")

            lang_choice = Prompt.ask("[bold cyan]Select language number[/bold cyan]", default="1")

            try:
                lang_index = int(lang_choice) - 1
                if 0 <= lang_index < len(languages):
                    selected_lang = languages[lang_index]
                else:
                    selected_lang = "python"
            except ValueError:
                selected_lang = "python"

            self.console.print(f"[yellow]Selected language: {selected_lang}[/yellow]")
            code = Prompt.ask(f"[bold cyan]{selected_lang.capitalize()} code to analyze[/bold cyan]")

            if not code.strip():
                self.console.print("[red]No code provided[/red]")
                return

            analysis_request = {
                "content": code,
                "language": selected_lang
            }

            with self.console.status(f"[bold green]Analyzing {selected_lang} code...[/bold green]") as status:
                response = await self.clients.post_json("code-analyzer/analyze/text", analysis_request)

            if response:
                await self.display_code_analysis_results(response, code)
            else:
                self.console.print("[red]❌ Failed to analyze code[/red]")

        except Exception as e:
            self.console.print(f"[red]Error in language-specific analysis: {e}[/red]")

    async def file_repository_analysis_menu(self):
        """File and repository analysis submenu."""
        while True:
            menu = create_menu_table("File & Repository Analysis", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Analyze Single File"),
                ("2", "Analyze Directory/Repository"),
                ("3", "Analyze File with Dependencies"),
                ("4", "Repository Endpoint Inventory"),
                ("5", "Cross-File Analysis"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.analyze_single_file()
            elif choice == "2":
                await self.analyze_directory()
            elif choice == "3":
                await self.analyze_with_dependencies()
            elif choice == "4":
                await self.repository_endpoint_inventory()
            elif choice == "5":
                await self.cross_file_analysis()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def analyze_single_file(self):
        """Analyze a single file for endpoints and patterns."""
        try:
            file_path = Prompt.ask("[bold cyan]File path to analyze[/bold cyan]")

            if not os.path.exists(file_path):
                self.console.print(f"[red]File not found: {file_path}[/red]")
                return

            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > 100000:  # ~100KB limit
                self.console.print("[red]File too large for analysis (max 100KB)[/red]")
                return

            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            if not content.strip():
                self.console.print("[red]File is empty[/red]")
                return

            # Detect language from file extension
            _, ext = os.path.splitext(file_path)
            language_map = {
                '.py': 'python',
                '.js': 'javascript',
                '.ts': 'typescript',
                '.java': 'java',
                '.go': 'go',
                '.rs': 'rust',
                '.cpp': 'cpp',
                '.cc': 'cpp',
                '.cxx': 'cpp',
                '.c': 'c',
                '.cs': 'csharp'
            }
            language = language_map.get(ext.lower())

            analysis_request = {
                "content": content,
                "language": language,
                "path": file_path,
                "repo": os.path.basename(os.path.dirname(file_path)) if os.path.dirname(file_path) else None
            }

            with self.console.status(f"[bold green]Analyzing {os.path.basename(file_path)}...[/bold green]") as status:
                response = await self.clients.post_json("code-analyzer/analyze/text", analysis_request)

            if response:
                content_preview = f"File: {os.path.basename(file_path)} ({len(content)} chars)"
                await self.display_code_analysis_results(response, content_preview)
            else:
                self.console.print("[red]❌ Failed to analyze file[/red]")

        except Exception as e:
            self.console.print(f"[red]Error analyzing file: {e}[/red]")

    async def analyze_directory(self):
        """Analyze an entire directory/repository."""
        try:
            directory = Prompt.ask("[bold cyan]Directory path to analyze[/bold cyan]")

            if not os.path.exists(directory):
                self.console.print(f"[red]Directory not found: {directory}[/red]")
                return

            import glob

            # Find code files
            extensions = ['*.py', '*.js', '*.ts', '*.java', '*.go', '*.rs', '*.cpp', '*.cc', '*.cxx', '*.c', '*.cs']
            code_files = []

            for ext in extensions:
                code_files.extend(glob.glob(os.path.join(directory, '**', ext), recursive=True))

            if not code_files:
                self.console.print("[yellow]No code files found in directory[/yellow]")
                return

            self.console.print(f"[yellow]Found {len(code_files)} code files:[/yellow]")
            for i, file_path in enumerate(code_files[:10], 1):  # Show first 10
                rel_path = os.path.relpath(file_path, directory)
                self.console.print(f"  {i}. {rel_path}")

            if len(code_files) > 10:
                self.console.print(f"  ... and {len(code_files) - 10} more files")

            proceed = Confirm.ask(f"[bold cyan]Analyze {len(code_files)} files?[/bold cyan]", default=False)

            if proceed:
                # Create file items for analysis
                file_items = []
                total_size = 0

                for file_path in code_files:
                    try:
                        file_size = os.path.getsize(file_path)
                        if file_size > 50000:  # Skip very large files
                            continue
                        if total_size + file_size > 500000:  # Total limit
                            break

                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()

                        if content.strip():
                            rel_path = os.path.relpath(file_path, directory)
                            file_items.append({
                                "path": rel_path,
                                "content": content
                            })
                            total_size += file_size

                    except Exception as e:
                        continue  # Skip files that can't be read

                if not file_items:
                    self.console.print("[red]No valid files to analyze[/red]")
                    return

                analysis_request = {
                    "files": file_items,
                    "repo": os.path.basename(directory),
                    "language": None  # Mixed languages
                }

                with self.console.status(f"[bold green]Analyzing {len(file_items)} files...[/bold green]") as status:
                    response = await self.clients.post_json("code-analyzer/analyze/files", analysis_request)

                if response:
                    content_preview = f"Directory: {os.path.basename(directory)} ({len(file_items)} files)"
                    await self.display_code_analysis_results(response, content_preview)
                else:
                    self.console.print("[red]❌ Failed to analyze directory[/red]")

        except Exception as e:
            self.console.print(f"[red]Error analyzing directory: {e}[/red]")

    async def analyze_with_dependencies(self):
        """Analyze file with its dependencies."""
        try:
            self.console.print("[yellow]Dependency analysis would examine related files and imports[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in dependency analysis: {e}[/red]")

    async def repository_endpoint_inventory(self):
        """Create repository endpoint inventory."""
        try:
            self.console.print("[yellow]Repository endpoint inventory would catalog all API endpoints[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error creating inventory: {e}[/red]")

    async def cross_file_analysis(self):
        """Perform cross-file analysis."""
        try:
            self.console.print("[yellow]Cross-file analysis would examine relationships between files[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in cross-file analysis: {e}[/red]")

    async def git_integration_menu(self):
        """Git integration submenu."""
        while True:
            menu = create_menu_table("Git Integration", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Analyze Git Diff/Patch"),
                ("2", "Pre-commit Hook Analysis"),
                ("3", "CI/CD Pipeline Integration"),
                ("4", "Branch Comparison Analysis"),
                ("5", "Git History Analysis"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.analyze_git_patch()
            elif choice == "2":
                await self.pre_commit_analysis()
            elif choice == "3":
                await self.ci_cd_integration()
            elif choice == "4":
                await self.branch_comparison()
            elif choice == "5":
                await self.git_history_analysis()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def analyze_git_patch(self):
        """Analyze a git patch for endpoint changes."""
        try:
            # Try to get current git diff
            try:
                result = subprocess.run(['git', 'diff', '--cached'], capture_output=True, text=True, cwd='.')
                patch_content = result.stdout
            except:
                patch_content = ""

            if not patch_content.strip():
                self.console.print("[yellow]No staged changes found. Enter patch content manually:[/yellow]")
                patch_lines = []
                try:
                    while True:
                        line = input()
                        patch_lines.append(line)
                except EOFError:
                    pass
                patch_content = "\n".join(patch_lines).strip()

            if not patch_content:
                self.console.print("[red]No patch content provided[/red]")
                return

            analysis_request = {
                "patch": patch_content,
                "repo": "current",
                "correlation_id": f"git-patch-{int(asyncio.get_event_loop().time() * 1000)}"
            }

            with self.console.status("[bold green]Analyzing git patch...[/bold green]") as status:
                response = await self.clients.post_json("code-analyzer/analyze/patch", analysis_request)

            if response:
                await self.display_patch_analysis_results(response, patch_content[:200] + "..." if len(patch_content) > 200 else patch_content)
            else:
                self.console.print("[red]❌ Failed to analyze patch[/red]")

        except KeyboardInterrupt:
            self.console.print("[yellow]Patch analysis cancelled[/yellow]")
        except Exception as e:
            self.console.print(f"[red]Error analyzing patch: {e}[/red]")

    async def display_patch_analysis_results(self, results: Dict[str, Any], patch_preview: str):
        """Display patch analysis results."""
        content = f"""
[bold]Git Patch Analysis Results[/bold]

[bold blue]Analysis ID:[/bold blue] {results.get('id', 'N/A')}
[bold blue]Patch Preview:[/bold blue] {patch_preview}

[bold green]Correlation ID:[/bold green] {results.get('correlation_id', 'N/A')}
"""

        document = results.get("document", {})
        analysis_content = document.get("content", "")

        if analysis_content:
            content += f"\n[bold cyan]Analysis Results:[/bold cyan]\n{analysis_content[:500]}{'...' if len(analysis_content) > 500 else ''}"

        metadata = document.get("metadata", {})
        if metadata:
            content += f"\n[bold yellow]Metadata:[/bold yellow]\n"
            for key, value in metadata.items():
                content += f"• {key}: {value}\n"

        print_panel(self.console, content, border_style="green")

    async def pre_commit_analysis(self):
        """Run analysis as pre-commit hook."""
        try:
            self.console.print("[yellow]Pre-commit analysis would validate code before commits[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in pre-commit analysis: {e}[/red]")

    async def ci_cd_integration(self):
        """Integrate with CI/CD pipelines."""
        try:
            self.console.print("[yellow]CI/CD integration would analyze code in automated pipelines[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in CI/CD integration: {e}[/red]")

    async def branch_comparison(self):
        """Compare branches for analysis."""
        try:
            self.console.print("[yellow]Branch comparison would analyze differences between branches[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in branch comparison: {e}[/red]")

    async def git_history_analysis(self):
        """Analyze git history."""
        try:
            self.console.print("[yellow]Git history analysis would examine code evolution over time[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in git history analysis: {e}[/red]")

    async def security_scanning_menu(self):
        """Security scanning submenu."""
        while True:
            menu = create_menu_table("Security Scanning", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Scan Code for Security Issues"),
                ("2", "Scan for Sensitive Information"),
                ("3", "Custom Keyword Scanning"),
                ("4", "Security Audit Report"),
                ("5", "Vulnerability Assessment"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.scan_code_security()
            elif choice == "2":
                await self.scan_sensitive_info()
            elif choice == "3":
                await self.custom_keyword_scan()
            elif choice == "4":
                await self.security_audit_report()
            elif choice == "5":
                await self.vulnerability_assessment()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def scan_code_security(self):
        """Scan code for security issues."""
        try:
            code = Prompt.ask("[bold cyan]Code to scan for security issues[/bold cyan]")

            if not code.strip():
                self.console.print("[red]No code provided[/red]")
                return

            scan_request = {"content": code}

            with self.console.status("[bold green]Scanning code for security issues...[/bold green]") as status:
                response = await self.clients.post_json("code-analyzer/scan/secure", scan_request)

            if response:
                await self.display_security_scan_results(response, code[:200] + "..." if len(code) > 200 else code)
            else:
                self.console.print("[red]❌ Failed to scan code[/red]")

        except Exception as e:
            self.console.print(f"[red]Error scanning code: {e}[/red]")

    async def display_security_scan_results(self, results: Dict[str, Any], code_preview: str):
        """Display security scan results."""
        sensitive = results.get("sensitive", False)
        matches = results.get("matches", [])
        topics = results.get("topics", [])

        status_icon = "🚨" if sensitive else "✅"
        status_text = "SECURITY ISSUES DETECTED" if sensitive else "CODE APPEARS SECURE"

        content = f"""
[bold]Security Scan Results[/bold]

[bold blue]Status:[/bold blue] {status_icon} {status_text}
[bold blue]Code Preview:[/bold blue] {code_preview}

[bold green]Security Topics:[/bold green] {len(topics)}
"""

        if topics:
            content += "\n[bold yellow]Detected Topics:[/bold yellow]\n"
            for topic in topics:
                content += f"• {topic}\n"

        content += f"\n[bold red]Security Matches:[/bold red] {len(matches)}\n"

        if matches:
            for i, match in enumerate(matches[:10], 1):  # Show first 10
                content += f"{i:2d}. {match}\n"
            if len(matches) > 10:
                content += f"    ... and {len(matches) - 10} more matches\n"

        # Security assessment
        risk_level = "HIGH" if sensitive and len(matches) > 3 else "MEDIUM" if sensitive else "LOW"
        risk_color = {"HIGH": "red", "MEDIUM": "yellow", "LOW": "green"}.get(risk_level, "white")

        content += f"\n[bold {risk_color}]Risk Assessment: {risk_level}[/bold {risk_color}]"

        if sensitive:
            content += "\n\n[bold red]⚠️  SECURITY RECOMMENDATIONS:[/bold red]"
            content += "\n• Review and remove sensitive information"
            content += "\n• Use environment variables for secrets"
            content += "\n• Implement proper access controls"
            if "secrets" in topics or "credentials" in topics:
                content += "\n• Never commit secrets to version control"
            if "pii" in topics:
                content += "\n• Ensure PII handling complies with regulations"

        print_panel(self.console, content, border_style="red" if sensitive else "green")

    async def scan_sensitive_info(self):
        """Scan for sensitive information."""
        try:
            content = Prompt.ask("[bold cyan]Content to scan for sensitive information[/bold cyan]")

            if not content.strip():
                self.console.print("[red]No content provided[/red]")
                return

            scan_request = {"content": content}

            response = await self.clients.post_json("code-analyzer/scan/secure", scan_request)

            if response:
                await self.display_security_scan_results(response, content)
            else:
                self.console.print("[red]❌ Failed to scan content[/red]")

        except Exception as e:
            self.console.print(f"[red]Error scanning content: {e}[/red]")

    async def custom_keyword_scan(self):
        """Scan with custom keywords."""
        try:
            content = Prompt.ask("[bold cyan]Content to scan[/bold cyan]")
            keywords_input = Prompt.ask("[bold cyan]Custom keywords (comma-separated)[/bold cyan]")

            if not content.strip():
                self.console.print("[red]No content provided[/red]")
                return

            keywords = [k.strip() for k in keywords_input.split(",") if k.strip()]

            scan_request = {
                "content": content,
                "keywords": keywords
            }

            with self.console.status("[bold green]Scanning with custom keywords...[/bold green]") as status:
                response = await self.clients.post_json("code-analyzer/scan/secure", scan_request)

            if response:
                await self.display_security_scan_results(response, content)
            else:
                self.console.print("[red]❌ Failed to scan with custom keywords[/red]")

        except Exception as e:
            self.console.print(f"[red]Error in custom keyword scan: {e}[/red]")

    async def security_audit_report(self):
        """Generate security audit report."""
        try:
            self.console.print("[yellow]Security audit reports would analyze security posture[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error generating audit report: {e}[/red]")

    async def vulnerability_assessment(self):
        """Perform vulnerability assessment."""
        try:
            self.console.print("[yellow]Vulnerability assessment would identify security weaknesses[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error in vulnerability assessment: {e}[/red]")

    async def style_management_menu(self):
        """Style management submenu."""
        while True:
            menu = create_menu_table("Style Management", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "View Style Examples"),
                ("2", "Add Style Example"),
                ("3", "Import Style Examples"),
                ("4", "Language-Specific Styles"),
                ("5", "Style Compliance Checking"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.view_style_examples()
            elif choice == "2":
                await self.add_style_example()
            elif choice == "3":
                await self.import_style_examples()
            elif choice == "4":
                await self.language_specific_styles()
            elif choice == "5":
                await self.style_compliance_checking()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def view_style_examples(self):
        """View programming style examples."""
        try:
            language = Prompt.ask("[bold cyan]Language filter (optional)[/bold cyan]", default="")

            params = {}
            if language:
                params["language"] = language

            response = await self.clients.get_json("code-analyzer/style/examples", params=params)

            if response:
                examples = response
                if isinstance(examples, dict) and "examples" in examples:
                    examples = examples["examples"]

                if examples:
                    table = Table(title=f"Style Examples{' - ' + language if language else ''}")
                    table.add_column("Language", style="cyan")
                    table.add_column("Title", style="green")
                    table.add_column("Snippet Preview", style="white")

                    for example in examples:
                        snippet = example.get("snippet", "")
                        preview = snippet[:50] + "..." if len(snippet) > 50 else snippet
                        table.add_row(
                            example.get("language", "unknown"),
                            example.get("title", "Untitled"),
                            preview
                        )

                    self.console.print(table)
                else:
                    self.console.print("[yellow]No style examples found[/yellow]")
            else:
                self.console.print("[red]Failed to retrieve style examples[/red]")

        except Exception as e:
            self.console.print(f"[red]Error viewing style examples: {e}[/red]")

    async def add_style_example(self):
        """Add a new style example."""
        try:
            language = Prompt.ask("[bold cyan]Programming language[/bold cyan]")
            title = Prompt.ask("[bold cyan]Example title[/bold cyan]")
            snippet = Prompt.ask("[bold cyan]Code snippet[/bold cyan]")
            description = Prompt.ask("[bold cyan]Description (optional)[/bold cyan]", default="")
            purpose = Prompt.ask("[bold cyan]Purpose (optional)[/bold cyan]", default="")
            tags_input = Prompt.ask("[bold cyan]Tags (comma-separated, optional)[/bold cyan]", default="")

            tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()]

            style_example = {
                "language": language,
                "title": title,
                "snippet": snippet,
                "description": description if description else None,
                "purpose": purpose if purpose else None,
                "tags": tags if tags else None
            }

            style_request = {"items": [style_example]}

            response = await self.clients.post_json("code-analyzer/style/examples", style_request)

            if response:
                self.console.print("[green]✅ Style example added successfully[/green]")
                if response.get("languages"):
                    self.console.print(f"[green]Updated languages: {response['languages']}[/green]")
            else:
                self.console.print("[red]❌ Failed to add style example[/red]")

        except Exception as e:
            self.console.print(f"[red]Error adding style example: {e}[/red]")

    async def import_style_examples(self):
        """Import style examples from file."""
        try:
            self.console.print("[yellow]Style example import would load examples from JSON files[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error importing style examples: {e}[/red]")

    async def language_specific_styles(self):
        """Manage language-specific styles."""
        try:
            self.console.print("[yellow]Language-specific styles would show examples for selected languages[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error managing language styles: {e}[/red]")

    async def style_compliance_checking(self):
        """Check style compliance."""
        try:
            self.console.print("[yellow]Style compliance checking would validate code against style examples[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error checking compliance: {e}[/red]")

    async def analysis_history_menu(self):
        """Analysis history and reporting submenu."""
        while True:
            menu = create_menu_table("Analysis History & Reporting", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "View Analysis History"),
                ("2", "Search Analysis Results"),
                ("3", "Generate Analysis Report"),
                ("4", "Export Analysis Data"),
                ("5", "Analysis Trends & Metrics"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.view_analysis_history()
            elif choice == "2":
                await self.search_analysis_results()
            elif choice == "3":
                await self.generate_analysis_report()
            elif choice == "4":
                await self.export_analysis_data()
            elif choice == "5":
                await self.analysis_trends_metrics()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def view_analysis_history(self):
        """View analysis history."""
        try:
            self.console.print("[yellow]Analysis history would show past code analysis operations[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error viewing analysis history: {e}[/red]")

    async def search_analysis_results(self):
        """Search analysis results."""
        try:
            self.console.print("[yellow]Analysis search would find specific analysis results[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error searching results: {e}[/red]")

    async def generate_analysis_report(self):
        """Generate analysis report."""
        try:
            self.console.print("[yellow]Analysis reports would summarize code quality and findings[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error generating report: {e}[/red]")

    async def export_analysis_data(self):
        """Export analysis data."""
        try:
            self.console.print("[yellow]Analysis data export would save results to various formats[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error exporting data: {e}[/red]")

    async def analysis_trends_metrics(self):
        """Show analysis trends and metrics."""
        try:
            self.console.print("[yellow]Analysis trends would show code quality evolution over time[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error showing trends: {e}[/red]")

    async def code_analyzer_health_menu(self):
        """Code analyzer health and configuration submenu."""
        while True:
            menu = create_menu_table("Code Analyzer Health & Configuration", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "View Service Health"),
                ("2", "Rate Limiting Status"),
                ("3", "Configuration Settings"),
                ("4", "Performance Metrics"),
                ("5", "Service Logs"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.view_service_health()
            elif choice == "2":
                await self.rate_limiting_status()
            elif choice == "3":
                await self.configuration_settings()
            elif choice == "4":
                await self.performance_metrics()
            elif choice == "5":
                await self.service_logs()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def view_service_health(self):
        """View code analyzer service health."""
        try:
            response = await self.clients.get_json("code-analyzer/health")

            if response:
                rate_limiting = response.get("rate_limiting", False)

                content = f"""
[bold]Code Analyzer Health Status[/bold]

[bold blue]Status:[/bold blue] {response.get('status', 'unknown')}
[bold blue]Service:[/bold blue] {response.get('service', 'unknown')}
[bold blue]Version:[/bold blue] {response.get('version', 'unknown')}

[bold green]Rate Limiting:[/bold green] {'✅ Enabled' if rate_limiting else '❌ Disabled'}
"""

                if rate_limiting:
                    content += "\n[bold cyan]Rate Limits:[/bold cyan]"
                    content += "\n• Text analysis: 10 req/sec, burst 20"
                    content += "\n• File analysis: 5 req/sec, burst 10"
                    content += "\n• Patch analysis: 5 req/sec, burst 10"

                print_panel(self.console, content, border_style="green")
            else:
                self.console.print("[red]Failed to retrieve service health[/red]")

        except Exception as e:
            self.console.print(f"[red]Error viewing service health: {e}[/red]")

    async def rate_limiting_status(self):
        """Check rate limiting status."""
        try:
            self.console.print("[yellow]Rate limiting status would show current request rates[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error checking rate limits: {e}[/red]")

    async def configuration_settings(self):
        """View configuration settings."""
        try:
            self.console.print("[yellow]Configuration settings would show current service parameters[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error viewing configuration: {e}[/red]")

    async def performance_metrics(self):
        """View performance metrics."""
        try:
            self.console.print("[yellow]Performance metrics would show analysis speed and resource usage[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error viewing metrics: {e}[/red]")

    async def service_logs(self):
        """View service logs."""
        try:
            self.console.print("[yellow]Service logs would show recent code analyzer operations[/yellow]")
            Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")

        except Exception as e:
            self.console.print(f"[red]Error viewing logs: {e}[/red]")

    async def analyze_code_from_cli(self, analyze_request: Dict[str, Any]):
        """Analyze code from CLI usage."""
        try:
            with self.console.status(f"[bold green]Analyzing code...[/bold green]") as status:
                response = await self.clients.post_json("code-analyzer/analyze/text", analyze_request)

            if response:
                content = analyze_request.get("content", "")
                await self.display_code_analysis_results(response, content[:200] + "..." if len(content) > 200 else content)
            else:
                self.console.print("[red]❌ Code analysis failed[/red]")

        except Exception as e:
            self.console.print(f"[red]Error analyzing code: {e}[/red]")

    async def scan_security_from_cli(self, scan_request: Dict[str, Any]):
        """Scan for security issues from CLI usage."""
        try:
            with self.console.status(f"[bold green]Scanning for security issues...[/bold green]") as status:
                response = await self.clients.post_json("code-analyzer/scan/secure", scan_request)

            if response:
                content = scan_request.get("content", "")
                await self.display_security_scan_results(response, content[:200] + "..." if len(content) > 200 else content)
            else:
                self.console.print("[red]❌ Security scan failed[/red]")

        except Exception as e:
            self.console.print(f"[red]Error scanning security: {e}[/red]")
