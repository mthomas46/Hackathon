"""DocStore Manager module for CLI service.

Provides power-user operations for document store management including
documents, analyses, search, and quality operations.
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


class DocStoreManager:
    """Manager for document store power-user operations."""

    def __init__(self, console: Console, clients):
        self.console = console
        self.clients = clients

    async def docstore_management_menu(self):
        """Main document store management menu."""
        while True:
            menu = create_menu_table("Document Store Management", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Document Operations (View, Add, Update, Delete)"),
                ("2", "Analysis Management (Run, View, Link)"),
                ("3", "Search & Discovery"),
                ("4", "Quality Metrics & Style Examples"),
                ("5", "Bulk Operations"),
                ("6", "Document Store Info & Config"),
                ("b", "Back to Main Menu")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.document_operations_menu()
            elif choice == "2":
                await self.analysis_management_menu()
            elif choice == "3":
                await self.search_discovery_menu()
            elif choice == "4":
                await self.quality_style_menu()
            elif choice == "5":
                await self.bulk_operations_menu()
            elif choice == "6":
                await self.info_config_menu()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def document_operations_menu(self):
        """Document operations submenu."""
        while True:
            menu = create_menu_table("Document Operations", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "List Documents"),
                ("2", "View Document Details"),
                ("3", "Add New Document"),
                ("4", "Update Document"),
                ("5", "Delete Document"),
                ("6", "Document Statistics"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.list_documents()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "2":
                await self.view_document_details()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "3":
                await self.add_document()
            elif choice == "4":
                await self.update_document()
            elif choice == "5":
                await self.delete_document()
            elif choice == "6":
                await self.document_statistics()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def list_documents(self):
        """List documents."""
        try:
            limit = Prompt.ask("[bold cyan]Limit[/bold cyan]", default="20")
            offset = Prompt.ask("[bold cyan]Offset[/bold cyan]", default="0")

            with self.console.status("[bold green]Fetching documents...") as status:
                response = await self.clients.get_json(f"doc-store/documents/_list?limit={limit}&offset={offset}")

            if response.get("documents"):
                table = Table(title="Documents")
                table.add_column("ID", style="cyan")
                table.add_column("Title", style="white")
                table.add_column("Type", style="green")
                table.add_column("Quality", style="yellow")
                table.add_column("Created", style="blue")

                for doc in response["documents"]:
                    quality_color = "green" if doc.get("quality_score", 0) > 7 else "yellow" if doc.get("quality_score", 0) > 4 else "red"
                    table.add_row(
                        doc.get("id", "N/A")[:8],
                        doc.get("title", "Untitled")[:40],
                        doc.get("type", "unknown"),
                        f"[{quality_color}]{doc.get('quality_score', 0):.1f}[/{quality_color}]",
                        doc.get("created_at", "unknown")[:19]
                    )

                self.console.print(table)
                self.console.print(f"[dim]Showing {len(response['documents'])} documents (offset: {offset})[/dim]")
            else:
                self.console.print("[yellow]No documents found.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error listing documents: {e}[/red]")

    async def view_document_details(self):
        """View document details."""
        try:
            doc_id = Prompt.ask("[bold cyan]Document ID[/bold cyan]")

            with self.console.status(f"[bold green]Fetching document {doc_id}...") as status:
                response = await self.clients.get_json(f"doc-store/documents/{doc_id}")

            if response.get("document"):
                doc = response["document"]
                content = f"""
[bold]Document Details[/bold]

ID: {doc.get('id', 'N/A')}
Title: {doc.get('title', 'Untitled')}
Type: {doc.get('type', 'unknown')}
Quality Score: {doc.get('quality_score', 0):.2f}/10

Created: {doc.get('created_at', 'unknown')}
Updated: {doc.get('updated_at', 'unknown')}

Content Length: {len(doc.get('content', ''))} characters

Metadata:
"""
                if doc.get("metadata"):
                    import json
                    content += f"```json\n{json.dumps(doc['metadata'], indent=2)}\n```"

                if len(doc.get('content', '')) < 500:
                    content += f"\nContent:\n{doc['content'][:500]}"
                    if len(doc['content']) > 500:
                        content += "..."
                else:
                    content += f"\nContent Preview:\n{doc['content'][:200]}..."

                print_panel(self.console, content, border_style="blue")
            else:
                self.console.print("[red]Document not found.[/red]")

        except Exception as e:
            self.console.print(f"[red]Error fetching document details: {e}[/red]")

    async def add_document(self):
        """Add new document."""
        try:
            title = Prompt.ask("[bold cyan]Document title[/bold cyan]")
            doc_type = Prompt.ask("[bold cyan]Document type[/bold cyan]", choices=["article", "documentation", "code", "other"])
            content = Prompt.ask("[bold cyan]Content[/bold cyan]")

            metadata_input = Prompt.ask("[bold cyan]Metadata (JSON)[/bold cyan]", default="{}")
            import json
            metadata = json.loads(metadata_input)

            with self.console.status("[bold green]Adding document...") as status:
                response = await self.clients.post_json("doc-store/documents", {
                    "title": title,
                    "type": doc_type,
                    "content": content,
                    "metadata": metadata
                })

            if response.get("document_id"):
                self.console.print(f"[green]✅ Document added successfully: {response['document_id']}[/green]")
            else:
                self.console.print("[red]❌ Failed to add document[/red]")

        except Exception as e:
            self.console.print(f"[red]Error adding document: {e}[/red]")

    async def update_document(self):
        """Update document."""
        try:
            doc_id = Prompt.ask("[bold cyan]Document ID[/bold cyan]")
            field = Prompt.ask("[bold cyan]Field to update[/bold cyan]", choices=["title", "content", "metadata", "type"])
            new_value = Prompt.ask(f"[bold cyan]New {field} value[/bold cyan]")

            update_data = {field: new_value}
            if field == "metadata":
                import json
                update_data[field] = json.loads(new_value)

            with self.console.status(f"[bold green]Updating document {doc_id}...") as status:
                response = await self.clients.put_json(f"doc-store/documents/{doc_id}", update_data)

            if response.get("updated"):
                self.console.print(f"[green]✅ Document {doc_id} updated successfully[/green]")
            else:
                self.console.print("[red]❌ Failed to update document[/red]")

        except Exception as e:
            self.console.print(f"[red]Error updating document: {e}[/red]")

    async def delete_document(self):
        """Delete document."""
        try:
            doc_id = Prompt.ask("[bold cyan]Document ID[/bold cyan]")
            confirm = Confirm.ask(f"[bold red]Are you sure you want to delete document {doc_id}?[/bold red]")

            if confirm:
                with self.console.status(f"[bold green]Deleting document {doc_id}...") as status:
                    response = await self.clients.delete_json(f"doc-store/documents/{doc_id}")

                if response.get("deleted"):
                    self.console.print(f"[green]✅ Document {doc_id} deleted successfully[/green]")
                else:
                    self.console.print("[red]❌ Failed to delete document[/red]")
            else:
                self.console.print("[yellow]Document deletion cancelled.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error deleting document: {e}[/red]")

    async def document_statistics(self):
        """Document statistics."""
        try:
            with self.console.status("[bold green]Fetching document statistics...") as status:
                response = await self.clients.get_json("doc-store/info")

            if response.get("stats"):
                stats = response["stats"]
                content = f"""
[bold]Document Store Statistics[/bold]

Total Documents: {stats.get('total_documents', 0)}
Total Analyses: {stats.get('total_analyses', 0)}

Document Types:
"""
                if stats.get("document_types"):
                    for doc_type, count in stats["document_types"].items():
                        content += f"  {doc_type}: {count}\n"

                content += f"""
Quality Distribution:
  High (8-10): {stats.get('quality_distribution', {}).get('high', 0)}
  Medium (5-7): {stats.get('quality_distribution', {}).get('medium', 0)}
  Low (0-4): {stats.get('quality_distribution', {}).get('low', 0)}

Average Quality: {stats.get('avg_quality', 0):.2f}/10
Storage Used: {stats.get('storage_mb', 0):.2f} MB
"""
                print_panel(self.console, content, border_style="green")
            else:
                self.console.print("[yellow]No statistics available.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error fetching document statistics: {e}[/red]")

    async def analysis_management_menu(self):
        """Analysis management submenu."""
        while True:
            menu = create_menu_table("Analysis Management", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "List Analyses"),
                ("2", "View Analysis Details"),
                ("3", "Run New Analysis"),
                ("4", "Link Analysis to Document"),
                ("5", "Delete Analysis"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.list_analyses()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "2":
                await self.view_analysis_details()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "3":
                await self.run_analysis()
            elif choice == "4":
                await self.link_analysis()
            elif choice == "5":
                await self.delete_analysis()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def list_analyses(self):
        """List analyses."""
        try:
            limit = Prompt.ask("[bold cyan]Limit[/bold cyan]", default="20")

            with self.console.status("[bold green]Fetching analyses...") as status:
                response = await self.clients.get_json(f"doc-store/analyses?limit={limit}")

            if response.get("analyses"):
                table = Table(title="Analyses")
                table.add_column("ID", style="cyan")
                table.add_column("Type", style="green")
                table.add_column("Document ID", style="yellow")
                table.add_column("Score", style="magenta")
                table.add_column("Created", style="blue")

                for analysis in response["analyses"]:
                    table.add_row(
                        analysis.get("id", "N/A")[:8],
                        analysis.get("type", "unknown"),
                        analysis.get("document_id", "N/A")[:8],
                        f"{analysis.get('score', 0):.2f}",
                        analysis.get("created_at", "unknown")[:19]
                    )

                self.console.print(table)
            else:
                self.console.print("[yellow]No analyses found.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error listing analyses: {e}[/red]")

    async def view_analysis_details(self):
        """View analysis details."""
        try:
            analysis_id = Prompt.ask("[bold cyan]Analysis ID[/bold cyan]")

            with self.console.status(f"[bold green]Fetching analysis {analysis_id}...") as status:
                response = await self.clients.get_json(f"doc-store/analyses/{analysis_id}")

            if response.get("analysis"):
                analysis = response["analysis"]
                content = f"""
[bold]Analysis Details[/bold]

ID: {analysis.get('id', 'N/A')}
Type: {analysis.get('type', 'unknown')}
Document ID: {analysis.get('document_id', 'N/A')}
Score: {analysis.get('score', 0):.2f}/10

Created: {analysis.get('created_at', 'unknown')}
Model Used: {analysis.get('model_used', 'unknown')}

Results:
"""
                if analysis.get("results"):
                    import json
                    content += f"```json\n{json.dumps(analysis['results'], indent=2)}\n```"
                else:
                    content += "No detailed results available."

                print_panel(self.console, content, border_style="cyan")
            else:
                self.console.print("[red]Analysis not found.[/red]")

        except Exception as e:
            self.console.print(f"[red]Error fetching analysis details: {e}[/red]")

    async def run_analysis(self):
        """Run new analysis."""
        try:
            doc_id = Prompt.ask("[bold cyan]Document ID[/bold cyan]")
            analysis_type = Prompt.ask("[bold cyan]Analysis type[/bold cyan]", choices=["quality", "consistency", "sentiment", "summary"])

            with self.console.status(f"[bold green]Running {analysis_type} analysis on document {doc_id}...") as status:
                response = await self.clients.post_json("doc-store/analyses", {
                    "document_id": doc_id,
                    "type": analysis_type
                })

            if response.get("analysis_id"):
                self.console.print(f"[green]✅ Analysis started: {response['analysis_id']}[/green]")
            else:
                self.console.print("[red]❌ Failed to start analysis[/red]")

        except Exception as e:
            self.console.print(f"[red]Error running analysis: {e}[/red]")

    async def link_analysis(self):
        """Link analysis to document."""
        try:
            analysis_id = Prompt.ask("[bold cyan]Analysis ID[/bold cyan]")
            doc_id = Prompt.ask("[bold cyan]Document ID[/bold cyan]")

            with self.console.status(f"[bold green]Linking analysis {analysis_id} to document {doc_id}...") as status:
                response = await self.clients.post_json(f"doc-store/analyses/{analysis_id}/link", {
                    "document_id": doc_id
                })

            if response.get("linked"):
                self.console.print(f"[green]✅ Analysis linked successfully[/green]")
            else:
                self.console.print("[red]❌ Failed to link analysis[/red]")

        except Exception as e:
            self.console.print(f"[red]Error linking analysis: {e}[/red]")

    async def delete_analysis(self):
        """Delete analysis."""
        try:
            analysis_id = Prompt.ask("[bold cyan]Analysis ID[/bold cyan]")
            confirm = Confirm.ask(f"[bold red]Are you sure you want to delete analysis {analysis_id}?[/bold red]")

            if confirm:
                with self.console.status(f"[bold green]Deleting analysis {analysis_id}...") as status:
                    response = await self.clients.delete_json(f"doc-store/analyses/{analysis_id}")

                if response.get("deleted"):
                    self.console.print(f"[green]✅ Analysis {analysis_id} deleted successfully[/green]")
                else:
                    self.console.print("[red]❌ Failed to delete analysis[/red]")
            else:
                self.console.print("[yellow]Analysis deletion cancelled.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error deleting analysis: {e}[/red]")

    async def search_discovery_menu(self):
        """Search and discovery submenu."""
        while True:
            menu = create_menu_table("Search & Discovery", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Search Documents"),
                ("2", "Advanced Search"),
                ("3", "Search by Quality Score"),
                ("4", "Find Similar Documents"),
                ("5", "Recent Documents"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.search_documents()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "2":
                await self.advanced_search()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "3":
                await self.search_by_quality()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "4":
                await self.find_similar()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "5":
                await self.recent_documents()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def search_documents(self):
        """Search documents."""
        try:
            query = Prompt.ask("[bold cyan]Search query[/bold cyan]")

            with self.console.status(f"[bold green]Searching for '{query}'...") as status:
                response = await self.clients.get_json(f"doc-store/search?q={query}")

            if response.get("results"):
                self.display_search_results(response["results"], f"Search Results for '{query}'")
            else:
                self.console.print(f"[yellow]No documents found for '{query}'.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error searching documents: {e}[/red]")

    async def advanced_search(self):
        """Advanced search."""
        try:
            filters = {}
            filters_input = Prompt.ask("[bold cyan]Search filters (JSON)[/bold cyan]", default="{}")
            import json
            filters = json.loads(filters_input)

            query = Prompt.ask("[bold cyan]Search query[/bold cyan]", default="")

            search_params = {**filters}
            if query:
                search_params["q"] = query

            param_string = "&".join([f"{k}={v}" for k, v in search_params.items()])

            with self.console.status("[bold green]Performing advanced search...") as status:
                response = await self.clients.get_json(f"doc-store/search?{param_string}")

            if response.get("results"):
                self.display_search_results(response["results"], "Advanced Search Results")
            else:
                self.console.print("[yellow]No documents found with specified filters.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error performing advanced search: {e}[/red]")

    async def search_by_quality(self):
        """Search by quality score."""
        try:
            min_score = float(Prompt.ask("[bold cyan]Minimum quality score[/bold cyan]", default="0"))
            max_score = float(Prompt.ask("[bold cyan]Maximum quality score[/bold cyan]", default="10"))

            with self.console.status(f"[bold green]Searching documents with quality {min_score}-{max_score}...") as status:
                response = await self.clients.get_json(f"doc-store/search?quality_min={min_score}&quality_max={max_score}")

            if response.get("results"):
                self.display_search_results(response["results"], f"Documents with Quality {min_score}-{max_score}")
            else:
                self.console.print(f"[yellow]No documents found with quality score between {min_score} and {max_score}.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error searching by quality: {e}[/red]")

    async def find_similar(self):
        """Find similar documents."""
        try:
            doc_id = Prompt.ask("[bold cyan]Document ID to find similar to[/bold cyan]")
            limit = Prompt.ask("[bold cyan]Limit[/bold cyan]", default="10")

            with self.console.status(f"[bold green]Finding documents similar to {doc_id}...") as status:
                response = await self.clients.get_json(f"doc-store/search/similar/{doc_id}?limit={limit}")

            if response.get("similar_documents"):
                table = Table(title=f"Documents Similar to {doc_id}")
                table.add_column("ID", style="cyan")
                table.add_column("Title", style="white")
                table.add_column("Similarity", style="green")
                table.add_column("Type", style="yellow")

                for doc in response["similar_documents"]:
                    similarity_color = "green" if doc.get("similarity", 0) > 0.8 else "yellow" if doc.get("similarity", 0) > 0.5 else "red"
                    table.add_row(
                        doc.get("id", "N/A")[:8],
                        doc.get("title", "Untitled")[:40],
                        f"[{similarity_color}]{doc.get('similarity', 0):.2f}[/{similarity_color}]",
                        doc.get("type", "unknown")
                    )

                self.console.print(table)
            else:
                self.console.print("[yellow]No similar documents found.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error finding similar documents: {e}[/red]")

    async def recent_documents(self):
        """Recent documents."""
        try:
            limit = Prompt.ask("[bold cyan]Limit[/bold cyan]", default="20")

            with self.console.status("[bold green]Fetching recent documents...") as status:
                response = await self.clients.get_json(f"doc-store/documents/_list?limit={limit}&sort=created_at&order=desc")

            if response.get("documents"):
                self.display_search_results(response["documents"], "Recent Documents")
            else:
                self.console.print("[yellow]No recent documents found.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error fetching recent documents: {e}[/red]")

    def display_search_results(self, results: List[Dict], title: str):
        """Display search results in a table."""
        table = Table(title=title)
        table.add_column("ID", style="cyan")
        table.add_column("Title", style="white")
        table.add_column("Type", style="green")
        table.add_column("Quality", style="yellow")
        table.add_column("Created", style="blue")
        table.add_column("Relevance", style="magenta")

        for result in results[:20]:  # Show first 20
            quality_color = "green" if result.get("quality_score", 0) > 7 else "yellow" if result.get("quality_score", 0) > 4 else "red"
            relevance = result.get("relevance_score", result.get("similarity", 0))
            relevance_color = "green" if relevance > 0.8 else "yellow" if relevance > 0.5 else "red"

            table.add_row(
                result.get("id", "N/A")[:8],
                result.get("title", "Untitled")[:40],
                result.get("type", "unknown"),
                f"[{quality_color}]{result.get('quality_score', 0):.1f}[/{quality_color}]",
                result.get("created_at", "unknown")[:19],
                f"[{relevance_color}]{relevance:.2f}[/{relevance_color}]" if relevance > 0 else "N/A"
            )

        self.console.print(table)

    async def quality_style_menu(self):
        """Quality and style submenu."""
        while True:
            menu = create_menu_table("Quality & Style", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "View Quality Metrics"),
                ("2", "Style Examples"),
                ("3", "Quality Improvement Tips"),
                ("4", "Bulk Quality Recalculation"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.view_quality_metrics()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "2":
                await self.view_style_examples()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "3":
                await self.quality_improvement_tips()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "4":
                await self.bulk_quality_recalc()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def view_quality_metrics(self):
        """View quality metrics."""
        try:
            with self.console.status("[bold green]Fetching quality metrics...") as status:
                response = await self.clients.get_json("doc-store/documents/quality")

            if response.get("metrics"):
                metrics = response["metrics"]
                content = f"""
[bold]Document Quality Metrics[/bold]

Overall Average Quality: {metrics.get('overall_avg', 0):.2f}/10
Total Documents: {metrics.get('total_documents', 0)}

Quality Distribution:
  Excellent (9-10): {metrics.get('distribution', {}).get('excellent', 0)} documents
  Good (7-8): {metrics.get('distribution', {}).get('good', 0)} documents
  Average (5-6): {metrics.get('distribution', {}).get('average', 0)} documents
  Poor (0-4): {metrics.get('distribution', {}).get('poor', 0)} documents

Recent Trends:
  Last 7 days: {metrics.get('trends', {}).get('last_7_days', {}).get('avg_quality', 0):.2f} avg
  Last 30 days: {metrics.get('trends', {}).get('last_30_days', {}).get('avg_quality', 0):.2f} avg

Top Issues:
"""
                if metrics.get("common_issues"):
                    for issue in metrics["common_issues"][:5]:
                        content += f"  • {issue.get('issue', 'Unknown')}: {issue.get('count', 0)} documents\n"

                print_panel(self.console, content, border_style="green")
            else:
                self.console.print("[yellow]No quality metrics available.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error fetching quality metrics: {e}[/red]")

    async def view_style_examples(self):
        """View style examples."""
        try:
            style_type = Prompt.ask("[bold cyan]Style type[/bold cyan]", choices=["good", "bad", "improved"], default="good")

            with self.console.status(f"[bold green]Fetching {style_type} style examples...") as status:
                response = await self.clients.get_json(f"doc-store/style/examples?type={style_type}")

            if response.get("examples"):
                content = f"[bold]{style_type.title()} Style Examples[/bold]\n\n"
                for i, example in enumerate(response["examples"][:5], 1):  # Show first 5
                    content += f"[bold]{i}. {example.get('title', 'Example')}[/bold]\n"
                    content += f"{example.get('content', 'No content')[:200]}...\n\n"
                    if example.get("explanation"):
                        content += f"[dim]{example['explanation']}[/dim]\n\n"

                print_panel(self.console, content, border_style="blue")
            else:
                self.console.print(f"[yellow]No {style_type} style examples available.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error fetching style examples: {e}[/red]")

    async def quality_improvement_tips(self):
        """Quality improvement tips."""
        try:
            with self.console.status("[bold green]Fetching quality improvement tips...") as status:
                response = await self.clients.get_json("doc-store/quality/tips")

            if response.get("tips"):
                content = "[bold]Quality Improvement Tips[/bold]\n\n"
                for tip in response["tips"]:
                    content += f"[bold]• {tip.get('category', 'General')}:[/bold]\n"
                    content += f"  {tip.get('tip', 'No tip available')}\n"
                    if tip.get("impact"):
                        content += f"  [dim]Impact: {tip['impact']}[/dim]\n"
                    content += "\n"

                print_panel(self.console, content, border_style="yellow")
            else:
                self.console.print("[yellow]No quality improvement tips available.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error fetching quality improvement tips: {e}[/red]")

    async def bulk_quality_recalc(self):
        """Bulk quality recalculation."""
        try:
            confirm = Confirm.ask("[bold yellow]This will recalculate quality scores for all documents. Continue?[/bold yellow]")

            if confirm:
                scope = Prompt.ask("[bold cyan]Scope[/bold cyan]", choices=["all", "low_quality", "recent"], default="all")

                with self.console.status(f"[bold green]Recalculating quality for {scope} documents...") as status:
                    response = await self.clients.post_json("doc-store/quality/recalculate", {
                        "scope": scope
                    })

                if response.get("job_id"):
                    self.console.print(f"[green]✅ Quality recalculation job started: {response['job_id']}[/green]")
                    self.console.print(f"[yellow]Documents affected: {response.get('affected_documents', 0)}[/yellow]")
                else:
                    self.console.print("[red]❌ Failed to start quality recalculation[/red]")
            else:
                self.console.print("[yellow]Quality recalculation cancelled.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error starting bulk quality recalculation: {e}[/red]")

    async def bulk_operations_menu(self):
        """Bulk operations submenu."""
        while True:
            menu = create_menu_table("Bulk Operations", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Bulk Delete Documents"),
                ("2", "Bulk Update Metadata"),
                ("3", "Bulk Reanalyze Documents"),
                ("4", "Export Documents"),
                ("5", "Import Documents"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.bulk_delete()
            elif choice == "2":
                await self.bulk_update_metadata()
            elif choice == "3":
                await self.bulk_reanalyze()
            elif choice == "4":
                await self.bulk_export()
            elif choice == "5":
                await self.bulk_import()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def bulk_delete(self):
        """Bulk delete documents."""
        try:
            criteria_input = Prompt.ask("[bold cyan]Deletion criteria (JSON)[/bold cyan]", default='{"quality_score": {"$lt": 3}}')
            import json
            criteria = json.loads(criteria_input)

            confirm = Confirm.ask(f"[bold red]This will delete documents matching: {criteria_input}. Continue?[/bold red]")

            if confirm:
                with self.console.status("[bold green]Deleting documents...") as status:
                    response = await self.clients.post_json("doc-store/bulk/delete", {
                        "criteria": criteria
                    })

                if response.get("deleted_count"):
                    self.console.print(f"[green]✅ Deleted {response['deleted_count']} documents[/green]")
                else:
                    self.console.print("[yellow]No documents matched the deletion criteria.[/yellow]")
            else:
                self.console.print("[yellow]Bulk deletion cancelled.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error performing bulk deletion: {e}[/red]")

    async def bulk_update_metadata(self):
        """Bulk update metadata."""
        try:
            criteria_input = Prompt.ask("[bold cyan]Selection criteria (JSON)[/bold cyan]")
            updates_input = Prompt.ask("[bold cyan]Updates (JSON)[/bold cyan]")

            import json
            criteria = json.loads(criteria_input)
            updates = json.loads(updates_input)

            confirm = Confirm.ask(f"[bold yellow]This will update metadata for documents matching: {criteria_input}. Continue?[/bold yellow]")

            if confirm:
                with self.console.status("[bold green]Updating metadata...") as status:
                    response = await self.clients.post_json("doc-store/bulk/update", {
                        "criteria": criteria,
                        "updates": updates
                    })

                if response.get("updated_count"):
                    self.console.print(f"[green]✅ Updated {response['updated_count']} documents[/green]")
                else:
                    self.console.print("[yellow]No documents matched the update criteria.[/yellow]")
            else:
                self.console.print("[yellow]Bulk update cancelled.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error performing bulk metadata update: {e}[/red]")

    async def bulk_reanalyze(self):
        """Bulk reanalyze documents."""
        try:
            criteria_input = Prompt.ask("[bold cyan]Selection criteria (JSON)[/bold cyan]", default='{"quality_score": {"$lt": 5}}')
            analysis_type = Prompt.ask("[bold cyan]Analysis type[/bold cyan]", choices=["quality", "consistency", "all"])

            import json
            criteria = json.loads(criteria_input)

            confirm = Confirm.ask(f"[bold yellow]This will reanalyze documents matching: {criteria_input}. Continue?[/bold yellow]")

            if confirm:
                with self.console.status(f"[bold green]Reanalyzing documents ({analysis_type})...") as status:
                    response = await self.clients.post_json("doc-store/bulk/reanalyze", {
                        "criteria": criteria,
                        "analysis_type": analysis_type
                    })

                if response.get("job_id"):
                    self.console.print(f"[green]✅ Bulk reanalysis job started: {response['job_id']}[/green]")
                    self.console.print(f"[yellow]Documents to analyze: {response.get('document_count', 0)}[/yellow]")
                else:
                    self.console.print("[red]❌ Failed to start bulk reanalysis[/red]")
            else:
                self.console.print("[yellow]Bulk reanalysis cancelled.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error starting bulk reanalysis: {e}[/red]")

    async def bulk_export(self):
        """Bulk export documents."""
        try:
            criteria_input = Prompt.ask("[bold cyan]Export criteria (JSON)[/bold cyan]", default="{}")
            format_type = Prompt.ask("[bold cyan]Export format[/bold cyan]", choices=["json", "csv", "xml"], default="json")
            filename = Prompt.ask("[bold cyan]Output filename[/bold cyan]")

            import json
            criteria = json.loads(criteria_input)

            with self.console.status(f"[bold green]Exporting documents to {filename}...") as status:
                response = await self.clients.post_json("doc-store/bulk/export", {
                    "criteria": criteria,
                    "format": format_type,
                    "filename": filename
                })

            if response.get("export_id"):
                self.console.print(f"[green]✅ Export started: {response['export_id']}[/green]")
                self.console.print(f"[yellow]Documents to export: {response.get('document_count', 0)}[/yellow]")
            else:
                self.console.print("[red]❌ Failed to start export[/red]")

        except Exception as e:
            self.console.print(f"[red]Error starting bulk export: {e}[/red]")

    async def bulk_import(self):
        """Bulk import documents."""
        try:
            filename = Prompt.ask("[bold cyan]Import file path[/bold cyan]")
            format_type = Prompt.ask("[bold cyan]Import format[/bold cyan]", choices=["json", "csv", "xml"], default="json")

            confirm = Confirm.ask(f"[bold yellow]This will import documents from {filename}. Continue?[/bold yellow]")

            if confirm:
                with self.console.status(f"[bold green]Importing documents from {filename}...") as status:
                    response = await self.clients.post_json("doc-store/bulk/import", {
                        "filename": filename,
                        "format": format_type
                    })

                if response.get("import_id"):
                    self.console.print(f"[green]✅ Import started: {response['import_id']}[/green]")
                    self.console.print(f"[yellow]Documents to import: {response.get('document_count', 0)}[/yellow]")
                else:
                    self.console.print("[red]❌ Failed to start import[/red]")
            else:
                self.console.print("[yellow]Bulk import cancelled.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error starting bulk import: {e}[/red]")

    async def info_config_menu(self):
        """Info and configuration submenu."""
        while True:
            menu = create_menu_table("Info & Configuration", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Document Store Info"),
                ("2", "View Configuration"),
                ("3", "Storage Statistics"),
                ("4", "Performance Metrics"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.docstore_info()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "2":
                await self.view_docstore_config()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "3":
                await self.storage_statistics()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "4":
                await self.performance_metrics()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def docstore_info(self):
        """Document store info."""
        try:
            with self.console.status("[bold green]Fetching document store info...") as status:
                response = await self.clients.get_json("doc-store/info")

            if response.get("info"):
                info = response["info"]
                content = f"""
[bold]Document Store Information[/bold]

Version: {info.get('version', 'unknown')}
Uptime: {info.get('uptime', 'unknown')}
Database: {info.get('database', {}).get('type', 'unknown')}
Storage: {info.get('storage', {}).get('type', 'unknown')}

Features:
"""
                if info.get("features"):
                    for feature in info["features"]:
                        content += f"  • {feature}\n"

                content += f"""
Limits:
  Max Document Size: {info.get('limits', {}).get('max_document_size', 'unknown')}
  Max Total Storage: {info.get('limits', {}).get('max_total_storage', 'unknown')}
"""
                print_panel(self.console, content, border_style="blue")
            else:
                self.console.print("[yellow]No document store info available.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error fetching document store info: {e}[/red]")

    async def view_docstore_config(self):
        """View document store configuration."""
        try:
            with self.console.status("[bold green]Fetching configuration...") as status:
                response = await self.clients.get_json("doc-store/config/effective")

            if response.get("config"):
                import json
                config_str = json.dumps(response["config"], indent=2)
                print_panel(self.console, f"[bold]Document Store Configuration[/bold]\n\n{config_str}",
                          border_style="cyan")
            else:
                self.console.print("[yellow]No configuration available.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error fetching configuration: {e}[/red]")

    async def storage_statistics(self):
        """Storage statistics."""
        try:
            with self.console.status("[bold green]Fetching storage statistics...") as status:
                response = await self.clients.get_json("doc-store/storage/stats")

            if response.get("stats"):
                stats = response["stats"]
                content = f"""
[bold]Storage Statistics[/bold]

Total Documents: {stats.get('total_documents', 0)}
Total Storage Used: {stats.get('total_storage_mb', 0):.2f} MB
Average Document Size: {stats.get('avg_document_size_kb', 0):.2f} KB

Storage Breakdown:
"""
                if stats.get("storage_breakdown"):
                    for category, size_mb in stats["storage_breakdown"].items():
                        content += f"  {category}: {size_mb:.2f} MB\n"

                content += f"""
Growth Rate:
  Daily: {stats.get('growth_rate', {}).get('daily_mb', 0):.2f} MB
  Weekly: {stats.get('growth_rate', {}).get('weekly_mb', 0):.2f} MB
  Monthly: {stats.get('growth_rate', {}).get('monthly_mb', 0):.2f} MB

Capacity:
  Used: {stats.get('capacity', {}).get('used_percent', 0):.1f}%
  Available: {stats.get('capacity', {}).get('available_mb', 0):.2f} MB
"""
                print_panel(self.console, content, border_style="green")
            else:
                self.console.print("[yellow]No storage statistics available.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error fetching storage statistics: {e}[/red]")

    async def performance_metrics(self):
        """Performance metrics."""
        try:
            with self.console.status("[bold green]Fetching performance metrics...") as status:
                response = await self.clients.get_json("doc-store/performance/metrics")

            if response.get("metrics"):
                metrics = response["metrics"]
                content = f"""
[bold]Performance Metrics[/bold]

Response Times (ms):
  Average: {metrics.get('response_times', {}).get('avg_ms', 0):.2f}
  95th Percentile: {metrics.get('response_times', {}).get('p95_ms', 0):.2f}
  99th Percentile: {metrics.get('response_times', {}).get('p99_ms', 0):.2f}

Throughput:
  Requests/sec: {metrics.get('throughput', {}).get('requests_per_second', 0):.2f}
  Documents/sec: {metrics.get('throughput', {}).get('documents_per_second', 0):.2f}

Cache Performance:
  Hit Rate: {metrics.get('cache', {}).get('hit_rate_percent', 0):.1f}%
  Hit Ratio: {metrics.get('cache', {}).get('hit_ratio', 0):.2f}

Database Performance:
  Query Time: {metrics.get('database', {}).get('avg_query_time_ms', 0):.2f} ms
  Connection Pool: {metrics.get('database', {}).get('active_connections', 0)}/{metrics.get('database', {}).get('max_connections', 0)}
"""
                print_panel(self.console, content, border_style="magenta")
            else:
                self.console.print("[yellow]No performance metrics available.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error fetching performance metrics: {e}[/red]")
