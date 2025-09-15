"""Bulk Operations Manager module for CLI service.

Provides power-user operations for bulk processing across multiple services
including mass analysis, notifications, quality recalculations, and data operations.
"""

from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.panel import Panel

from ...shared_utils import (
    get_cli_clients,
    create_menu_table,
    add_menu_rows,
    print_panel,
    log_cli_metrics
)


class BulkOperationsManager:
    """Manager for bulk operations across multiple services."""

    def __init__(self, console: Console, clients):
        self.console = console
        self.clients = clients

    async def bulk_operations_menu(self):
        """Main bulk operations menu."""
        while True:
            menu = create_menu_table("Bulk Operations", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Mass Document Analysis"),
                ("2", "Bulk Quality Recalculation"),
                ("3", "Batch Notifications"),
                ("4", "Bulk Data Operations"),
                ("5", "Cross-Service Workflows"),
                ("6", "Bulk Reporting"),
                ("b", "Back to Main Menu")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.mass_document_analysis()
            elif choice == "2":
                await self.bulk_quality_recalculation()
            elif choice == "3":
                await self.batch_notifications()
            elif choice == "4":
                await self.bulk_data_operations()
            elif choice == "5":
                await self.cross_service_workflows()
            elif choice == "6":
                await self.bulk_reporting()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def mass_document_analysis(self):
        """Mass document analysis submenu."""
        while True:
            menu = create_menu_table("Mass Document Analysis", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Analyze All Documents"),
                ("2", "Analyze by Quality Score"),
                ("3", "Analyze by Document Type"),
                ("4", "Analyze Recently Modified"),
                ("5", "Custom Analysis Criteria"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.analyze_all_documents()
            elif choice == "2":
                await self.analyze_by_quality()
            elif choice == "3":
                await self.analyze_by_type()
            elif choice == "4":
                await self.analyze_recent()
            elif choice == "5":
                await self.analyze_custom_criteria()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def analyze_all_documents(self):
        """Analyze all documents."""
        try:
            analysis_type = Prompt.ask("[bold cyan]Analysis type[/bold cyan]",
                                     choices=["quality", "consistency", "security", "all"], default="quality")
            batch_size = Prompt.ask("[bold cyan]Batch size[/bold cyan]", default="50")

            confirm = Confirm.ask(f"[bold yellow]This will analyze ALL documents with {analysis_type} analysis in batches of {batch_size}. Continue?[/bold yellow]")

            if confirm:
                with self.console.status(f"[bold green]Starting mass {analysis_type} analysis...") as status:
                    response = await self.clients.post_json("bulk/analysis/all", {
                        "analysis_type": analysis_type,
                        "batch_size": int(batch_size)
                    })

                if response.get("bulk_analysis_id"):
                    analysis_id = response["bulk_analysis_id"]
                    self.console.print(f"[green]✅ Mass analysis started: {analysis_id}[/green]")
                    self.console.print(f"[yellow]Estimated documents: {response.get('estimated_count', 0)}[/yellow]")

                    # Monitor progress
                    await self.monitor_bulk_operation(analysis_id, "analysis")
                else:
                    self.console.print("[red]❌ Failed to start mass analysis[/red]")
            else:
                self.console.print("[yellow]Mass analysis cancelled.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error starting mass analysis: {e}[/red]")

    async def analyze_by_quality(self):
        """Analyze documents by quality score."""
        try:
            min_score = float(Prompt.ask("[bold cyan]Minimum quality score[/bold cyan]", default="0"))
            max_score = float(Prompt.ask("[bold cyan]Maximum quality score[/bold cyan]", default="5"))
            analysis_type = Prompt.ask("[bold cyan]Analysis type[/bold cyan]",
                                     choices=["quality", "consistency", "security"], default="consistency")

            confirm = Confirm.ask(f"[bold yellow]This will analyze documents with quality scores between {min_score} and {max_score}. Continue?[/bold yellow]")

            if confirm:
                with self.console.status(f"[bold green]Starting quality-based {analysis_type} analysis...") as status:
                    response = await self.clients.post_json("bulk/analysis/quality", {
                        "min_quality": min_score,
                        "max_quality": max_score,
                        "analysis_type": analysis_type
                    })

                if response.get("bulk_analysis_id"):
                    analysis_id = response["bulk_analysis_id"]
                    self.console.print(f"[green]✅ Quality-based analysis started: {analysis_id}[/green]")
                    self.console.print(f"[yellow]Matching documents: {response.get('matching_count', 0)}[/yellow]")

                    await self.monitor_bulk_operation(analysis_id, "analysis")
                else:
                    self.console.print("[red]❌ Failed to start quality-based analysis[/red]")
            else:
                self.console.print("[yellow]Quality-based analysis cancelled.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error starting quality-based analysis: {e}[/red]")

    async def analyze_by_type(self):
        """Analyze documents by type."""
        try:
            doc_types = Prompt.ask("[bold cyan]Document types (comma-separated)[/bold cyan]", default="article,documentation")
            analysis_type = Prompt.ask("[bold cyan]Analysis type[/bold cyan]",
                                     choices=["quality", "consistency", "security"], default="quality")

            type_list = [t.strip() for t in doc_types.split(",")]

            confirm = Confirm.ask(f"[bold yellow]This will analyze all {', '.join(type_list)} documents. Continue?[/bold yellow]")

            if confirm:
                with self.console.status(f"[bold green]Starting type-based {analysis_type} analysis...") as status:
                    response = await self.clients.post_json("bulk/analysis/type", {
                        "document_types": type_list,
                        "analysis_type": analysis_type
                    })

                if response.get("bulk_analysis_id"):
                    analysis_id = response["bulk_analysis_id"]
                    self.console.print(f"[green]✅ Type-based analysis started: {analysis_id}[/green]")
                    self.console.print(f"[yellow]Documents to analyze: {response.get('document_count', 0)}[/yellow]")

                    await self.monitor_bulk_operation(analysis_id, "analysis")
                else:
                    self.console.print("[red]❌ Failed to start type-based analysis[/red]")
            else:
                self.console.print("[yellow]Type-based analysis cancelled.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error starting type-based analysis: {e}[/red]")

    async def analyze_recent(self):
        """Analyze recently modified documents."""
        try:
            hours = int(Prompt.ask("[bold cyan]Modified within (hours)[/bold cyan]", default="24"))
            analysis_type = Prompt.ask("[bold cyan]Analysis type[/bold cyan]",
                                     choices=["quality", "consistency", "security"], default="quality")

            confirm = Confirm.ask(f"[bold yellow]This will analyze documents modified within the last {hours} hours. Continue?[/bold yellow]")

            if confirm:
                with self.console.status(f"[bold green]Starting recent document {analysis_type} analysis...") as status:
                    response = await self.clients.post_json("bulk/analysis/recent", {
                        "hours": hours,
                        "analysis_type": analysis_type
                    })

                if response.get("bulk_analysis_id"):
                    analysis_id = response["bulk_analysis_id"]
                    self.console.print(f"[green]✅ Recent document analysis started: {analysis_id}[/green]")
                    self.console.print(f"[yellow]Documents to analyze: {response.get('document_count', 0)}[/yellow]")

                    await self.monitor_bulk_operation(analysis_id, "analysis")
                else:
                    self.console.print("[red]❌ Failed to start recent document analysis[/red]")
            else:
                self.console.print("[yellow]Recent document analysis cancelled.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error starting recent document analysis: {e}[/red]")

    async def analyze_custom_criteria(self):
        """Analyze documents with custom criteria."""
        try:
            criteria_input = Prompt.ask("[bold cyan]Selection criteria (JSON)[/bold cyan]",
                                      default='{"metadata.tags": {"$exists": true}}')
            analysis_type = Prompt.ask("[bold cyan]Analysis type[/bold cyan]",
                                     choices=["quality", "consistency", "security"], default="quality")

            import json
            criteria = json.loads(criteria_input)

            confirm = Confirm.ask(f"[bold yellow]This will analyze documents matching custom criteria. Continue?[/bold yellow]")

            if confirm:
                with self.console.status(f"[bold green]Starting custom criteria {analysis_type} analysis...") as status:
                    response = await self.clients.post_json("bulk/analysis/custom", {
                        "criteria": criteria,
                        "analysis_type": analysis_type
                    })

                if response.get("bulk_analysis_id"):
                    analysis_id = response["bulk_analysis_id"]
                    self.console.print(f"[green]✅ Custom criteria analysis started: {analysis_id}[/green]")
                    self.console.print(f"[yellow]Documents to analyze: {response.get('document_count', 0)}[/yellow]")

                    await self.monitor_bulk_operation(analysis_id, "analysis")
                else:
                    self.console.print("[red]❌ Failed to start custom criteria analysis[/red]")
            else:
                self.console.print("[yellow]Custom criteria analysis cancelled.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error starting custom criteria analysis: {e}[/red]")

    async def bulk_quality_recalculation(self):
        """Bulk quality recalculation submenu."""
        while True:
            menu = create_menu_table("Bulk Quality Recalculation", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Recalculate All Documents"),
                ("2", "Recalculate by Type"),
                ("3", "Recalculate Low-Quality Only"),
                ("4", "Recalculate Custom Criteria"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.recalculate_all_quality()
            elif choice == "2":
                await self.recalculate_by_type()
            elif choice == "3":
                await self.recalculate_low_quality()
            elif choice == "4":
                await self.recalculate_custom_criteria()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def recalculate_all_quality(self):
        """Recalculate quality for all documents."""
        try:
            confirm = Confirm.ask("[bold red]This will recalculate quality scores for ALL documents. This is a heavy operation. Continue?[/bold red]")

            if confirm:
                with self.console.status("[bold green]Starting bulk quality recalculation...") as status:
                    response = await self.clients.post_json("bulk/quality/recalculate/all", {})

                if response.get("bulk_operation_id"):
                    operation_id = response["bulk_operation_id"]
                    self.console.print(f"[green]✅ Bulk quality recalculation started: {operation_id}[/green]")
                    self.console.print(f"[yellow]Total documents: {response.get('total_documents', 0)}[/yellow]")

                    await self.monitor_bulk_operation(operation_id, "quality_recalculation")
                else:
                    self.console.print("[red]❌ Failed to start bulk quality recalculation[/red]")
            else:
                self.console.print("[yellow]Bulk quality recalculation cancelled.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error starting bulk quality recalculation: {e}[/red]")

    async def recalculate_by_type(self):
        """Recalculate quality by document type."""
        try:
            doc_types = Prompt.ask("[bold cyan]Document types (comma-separated)[/bold cyan]", default="article,documentation")

            type_list = [t.strip() for t in doc_types.split(",")]

            confirm = Confirm.ask(f"[bold yellow]This will recalculate quality for {', '.join(type_list)} documents. Continue?[/bold yellow]")

            if confirm:
                with self.console.status(f"[bold green]Starting type-based quality recalculation...") as status:
                    response = await self.clients.post_json("bulk/quality/recalculate/type", {
                        "document_types": type_list
                    })

                if response.get("bulk_operation_id"):
                    operation_id = response["bulk_operation_id"]
                    self.console.print(f"[green]✅ Type-based quality recalculation started: {operation_id}[/green]")
                    self.console.print(f"[yellow]Documents to process: {response.get('document_count', 0)}[/yellow]")

                    await self.monitor_bulk_operation(operation_id, "quality_recalculation")
                else:
                    self.console.print("[red]❌ Failed to start type-based quality recalculation[/red]")
            else:
                self.console.print("[yellow]Type-based quality recalculation cancelled.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error starting type-based quality recalculation: {e}[/red]")

    async def recalculate_low_quality(self):
        """Recalculate quality for low-quality documents only."""
        try:
            threshold = float(Prompt.ask("[bold cyan]Quality threshold[/bold cyan]", default="5.0"))

            confirm = Confirm.ask(f"[bold yellow]This will recalculate quality for documents with scores below {threshold}. Continue?[/bold yellow]")

            if confirm:
                with self.console.status(f"[bold green]Starting low-quality document recalculation...") as status:
                    response = await self.clients.post_json("bulk/quality/recalculate/low", {
                        "quality_threshold": threshold
                    })

                if response.get("bulk_operation_id"):
                    operation_id = response["bulk_operation_id"]
                    self.console.print(f"[green]✅ Low-quality recalculation started: {operation_id}[/green]")
                    self.console.print(f"[yellow]Documents to process: {response.get('document_count', 0)}[/yellow]")

                    await self.monitor_bulk_operation(operation_id, "quality_recalculation")
                else:
                    self.console.print("[red]❌ Failed to start low-quality recalculation[/red]")
            else:
                self.console.print("[yellow]Low-quality recalculation cancelled.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error starting low-quality recalculation: {e}[/red]")

    async def recalculate_custom_criteria(self):
        """Recalculate quality with custom criteria."""
        try:
            criteria_input = Prompt.ask("[bold cyan]Selection criteria (JSON)[/bold cyan]",
                                      default='{"updated_at": {"$lt": "2024-01-01"}}')

            import json
            criteria = json.loads(criteria_input)

            confirm = Confirm.ask(f"[bold yellow]This will recalculate quality for documents matching custom criteria. Continue?[/bold yellow]")

            if confirm:
                with self.console.status(f"[bold green]Starting custom criteria quality recalculation...") as status:
                    response = await self.clients.post_json("bulk/quality/recalculate/custom", {
                        "criteria": criteria
                    })

                if response.get("bulk_operation_id"):
                    operation_id = response["bulk_operation_id"]
                    self.console.print(f"[green]✅ Custom criteria recalculation started: {operation_id}[/green]")
                    self.console.print(f"[yellow]Documents to process: {response.get('document_count', 0)}[/yellow]")

                    await self.monitor_bulk_operation(operation_id, "quality_recalculation")
                else:
                    self.console.print("[red]❌ Failed to start custom criteria recalculation[/red]")
            else:
                self.console.print("[yellow]Custom criteria recalculation cancelled.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error starting custom criteria recalculation: {e}[/red]")

    async def batch_notifications(self):
        """Batch notifications submenu."""
        while True:
            menu = create_menu_table("Batch Notifications", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Notify Document Owners"),
                ("2", "Send Bulk Alerts"),
                ("3", "Notification Templates"),
                ("4", "Notification History"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.notify_document_owners()
            elif choice == "2":
                await self.send_bulk_alerts()
            elif choice == "3":
                await self.notification_templates()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice == "4":
                await self.notification_history()
                Prompt.ask("\n[bold cyan]Press Enter to continue...[/bold cyan]")
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def notify_document_owners(self):
        """Notify document owners."""
        try:
            criteria_input = Prompt.ask("[bold cyan]Document selection criteria (JSON)[/bold cyan]",
                                      default='{"quality_score": {"$lt": 3}}')
            message = Prompt.ask("[bold cyan]Notification message[/bold cyan]",
                               default="Your document quality score needs improvement.")

            import json
            criteria = json.loads(criteria_input)

            confirm = Confirm.ask(f"[bold yellow]This will notify owners of documents matching the criteria. Continue?[/bold yellow]")

            if confirm:
                with self.console.status("[bold green]Sending owner notifications...") as status:
                    response = await self.clients.post_json("bulk/notifications/owners", {
                        "criteria": criteria,
                        "message": message
                    })

                if response.get("notification_batch_id"):
                    batch_id = response["notification_batch_id"]
                    self.console.print(f"[green]✅ Owner notifications sent: {batch_id}[/green]")
                    self.console.print(f"[yellow]Notifications sent: {response.get('notification_count', 0)}[/yellow]")
                    self.console.print(f"[yellow]Unique recipients: {response.get('unique_recipients', 0)}[/yellow]")
                else:
                    self.console.print("[red]❌ Failed to send owner notifications[/red]")
            else:
                self.console.print("[yellow]Owner notifications cancelled.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error sending owner notifications: {e}[/red]")

    async def send_bulk_alerts(self):
        """Send bulk alerts."""
        try:
            recipients_input = Prompt.ask("[bold cyan]Recipients (comma-separated emails)[/bold cyan]")
            subject = Prompt.ask("[bold cyan]Alert subject[/bold cyan]")
            message = Prompt.ask("[bold cyan]Alert message[/bold cyan]")
            priority = Prompt.ask("[bold cyan]Priority[/bold cyan]", choices=["low", "medium", "high", "critical"], default="medium")

            recipients = [email.strip() for email in recipients_input.split(",")]

            confirm = Confirm.ask(f"[bold yellow]This will send alerts to {len(recipients)} recipients. Continue?[/bold yellow]")

            if confirm:
                with self.console.status(f"[bold green]Sending bulk alerts...") as status:
                    response = await self.clients.post_json("bulk/notifications/alerts", {
                        "recipients": recipients,
                        "subject": subject,
                        "message": message,
                        "priority": priority
                    })

                if response.get("alert_batch_id"):
                    batch_id = response["alert_batch_id"]
                    self.console.print(f"[green]✅ Bulk alerts sent: {batch_id}[/green]")
                    self.console.print(f"[yellow]Alerts queued: {response.get('alert_count', 0)}[/yellow]")
                else:
                    self.console.print("[red]❌ Failed to send bulk alerts[/red]")
            else:
                self.console.print("[yellow]Bulk alerts cancelled.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error sending bulk alerts: {e}[/red]")

    async def notification_templates(self):
        """View notification templates."""
        try:
            with self.console.status("[bold green]Fetching notification templates...") as status:
                response = await self.clients.get_json("bulk/notifications/templates")

            if response.get("templates"):
                table = Table(title="Notification Templates")
                table.add_column("Template ID", style="cyan")
                table.add_column("Name", style="green")
                table.add_column("Type", style="yellow")
                table.add_column("Description", style="white")

                for template in response["templates"]:
                    table.add_row(
                        template.get("id", "N/A")[:8],
                        template.get("name", "unknown"),
                        template.get("type", "unknown"),
                        template.get("description", "No description")[:50]
                    )

                self.console.print(table)
            else:
                self.console.print("[yellow]No notification templates available.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error fetching notification templates: {e}[/red]")

    async def notification_history(self):
        """View notification history."""
        try:
            limit = Prompt.ask("[bold cyan]Limit[/bold cyan]", default="50")

            with self.console.status("[bold green]Fetching notification history...") as status:
                response = await self.clients.get_json(f"bulk/notifications/history?limit={limit}")

            if response.get("notifications"):
                table = Table(title="Notification History")
                table.add_column("Notification ID", style="cyan")
                table.add_column("Type", style="green")
                table.add_column("Recipients", style="yellow")
                table.add_column("Status", style="magenta")
                table.add_column("Sent", style="blue")

                for notification in response["notifications"]:
                    status_color = {
                        "sent": "green",
                        "pending": "yellow",
                        "failed": "red"
                    }.get(notification.get("status", "unknown"), "white")

                    table.add_row(
                        notification.get("id", "N/A")[:8],
                        notification.get("type", "unknown"),
                        str(notification.get("recipient_count", 0)),
                        f"[{status_color}]{notification.get('status', 'unknown')}[/{status_color}]",
                        notification.get("sent_at", "unknown")[:19]
                    )

                self.console.print(table)
            else:
                self.console.print("[yellow]No notification history found.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error fetching notification history: {e}[/red]")

    async def bulk_data_operations(self):
        """Bulk data operations submenu."""
        while True:
            menu = create_menu_table("Bulk Data Operations", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Bulk Export Documents"),
                ("2", "Bulk Import Documents"),
                ("3", "Bulk Update Metadata"),
                ("4", "Bulk Delete Documents"),
                ("5", "Data Migration"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.bulk_export_documents()
            elif choice == "2":
                await self.bulk_import_documents()
            elif choice == "3":
                await self.bulk_update_metadata()
            elif choice == "4":
                await self.bulk_delete_documents()
            elif choice == "5":
                await self.data_migration()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def bulk_export_documents(self):
        """Bulk export documents."""
        try:
            criteria_input = Prompt.ask("[bold cyan]Export criteria (JSON)[/bold cyan]", default="{}")
            format_type = Prompt.ask("[bold cyan]Export format[/bold cyan]",
                                   choices=["json", "csv", "xml", "markdown"], default="json")
            filename = Prompt.ask("[bold cyan]Output filename[/bold cyan]")

            import json
            criteria = json.loads(criteria_input)

            confirm = Confirm.ask(f"[bold yellow]This will export documents to {filename}. Continue?[/bold yellow]")

            if confirm:
                with self.console.status(f"[bold green]Exporting documents to {filename}...") as status:
                    response = await self.clients.post_json("bulk/data/export", {
                        "criteria": criteria,
                        "format": format_type,
                        "filename": filename
                    })

                if response.get("export_id"):
                    export_id = response["export_id"]
                    self.console.print(f"[green]✅ Bulk export started: {export_id}[/green]")
                    self.console.print(f"[yellow]Documents to export: {response.get('document_count', 0)}[/yellow]")
                    self.console.print(f"[yellow]Estimated file size: {response.get('estimated_size_mb', 0):.2f} MB[/yellow]")
                else:
                    self.console.print("[red]❌ Failed to start bulk export[/red]")
            else:
                self.console.print("[yellow]Bulk export cancelled.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error starting bulk export: {e}[/red]")

    async def bulk_import_documents(self):
        """Bulk import documents."""
        try:
            filename = Prompt.ask("[bold cyan]Import file path[/bold cyan]")
            format_type = Prompt.ask("[bold cyan]Import format[/bold cyan]",
                                   choices=["json", "csv", "xml", "markdown"], default="json")
            update_existing = Confirm.ask("[bold cyan]Update existing documents?[/bold cyan]", default=False)

            confirm = Confirm.ask(f"[bold yellow]This will import documents from {filename}. Continue?[/bold yellow]")

            if confirm:
                with self.console.status(f"[bold green]Importing documents from {filename}...") as status:
                    response = await self.clients.post_json("bulk/data/import", {
                        "filename": filename,
                        "format": format_type,
                        "update_existing": update_existing
                    })

                if response.get("import_id"):
                    import_id = response["import_id"]
                    self.console.print(f"[green]✅ Bulk import started: {import_id}[/green]")
                    self.console.print(f"[yellow]Documents to import: {response.get('document_count', 0)}[/yellow]")
                    self.console.print(f"[yellow]Will update existing: {'Yes' if update_existing else 'No'}[/yellow]")
                else:
                    self.console.print("[red]❌ Failed to start bulk import[/red]")
            else:
                self.console.print("[yellow]Bulk import cancelled.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error starting bulk import: {e}[/red]")

    async def bulk_update_metadata(self):
        """Bulk update document metadata."""
        try:
            criteria_input = Prompt.ask("[bold cyan]Selection criteria (JSON)[/bold cyan]")
            updates_input = Prompt.ask("[bold cyan]Metadata updates (JSON)[/bold cyan]")

            import json
            criteria = json.loads(criteria_input)
            updates = json.loads(updates_input)

            confirm = Confirm.ask(f"[bold yellow]This will update metadata for documents matching the criteria. Continue?[/bold yellow]")

            if confirm:
                with self.console.status("[bold green]Updating document metadata...") as status:
                    response = await self.clients.post_json("bulk/data/update-metadata", {
                        "criteria": criteria,
                        "updates": updates
                    })

                if response.get("update_id"):
                    update_id = response["update_id"]
                    self.console.print(f"[green]✅ Bulk metadata update started: {update_id}[/green]")
                    self.console.print(f"[yellow]Documents to update: {response.get('document_count', 0)}[/yellow]")
                else:
                    self.console.print("[red]❌ Failed to start bulk metadata update[/red]")
            else:
                self.console.print("[yellow]Bulk metadata update cancelled.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error starting bulk metadata update: {e}[/red]")

    async def bulk_delete_documents(self):
        """Bulk delete documents."""
        try:
            criteria_input = Prompt.ask("[bold cyan]Deletion criteria (JSON)[/bold cyan]",
                                      default='{"quality_score": {"$lt": 2}}')

            import json
            criteria = json.loads(criteria_input)

            confirm = Confirm.ask(f"[bold red]This will PERMANENTLY DELETE documents matching the criteria. Continue?[/bold red]")

            if confirm:
                # Double confirmation for destructive operation
                double_confirm = Confirm.ask("[bold red]ARE YOU ABSOLUTELY SURE? This action cannot be undone![/bold red]")

                if double_confirm:
                    with self.console.status("[bold green]Deleting documents...") as status:
                        response = await self.clients.post_json("bulk/data/delete", {
                            "criteria": criteria
                        })

                    if response.get("delete_id"):
                        delete_id = response["delete_id"]
                        self.console.print(f"[green]✅ Bulk deletion started: {delete_id}[/green]")
                        self.console.print(f"[yellow]Documents to delete: {response.get('document_count', 0)}[/yellow]")
                        self.console.print("[red]⚠️  This operation will permanently remove data![/red]")
                    else:
                        self.console.print("[red]❌ Failed to start bulk deletion[/red]")
                else:
                    self.console.print("[yellow]Bulk deletion cancelled at second confirmation.[/yellow]")
            else:
                self.console.print("[yellow]Bulk deletion cancelled.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error starting bulk deletion: {e}[/red]")

    async def data_migration(self):
        """Data migration operations."""
        try:
            source_criteria_input = Prompt.ask("[bold cyan]Source selection criteria (JSON)[/bold cyan]")
            target_service = Prompt.ask("[bold cyan]Target service[/bold cyan]",
                                      choices=["doc-store", "analysis-service", "external"])
            migration_type = Prompt.ask("[bold cyan]Migration type[/bold cyan]",
                                      choices=["copy", "move", "transform"], default="copy")

            import json
            source_criteria = json.loads(source_criteria_input)

            confirm = Confirm.ask(f"[bold yellow]This will migrate data to {target_service}. Continue?[/bold yellow]")

            if confirm:
                with self.console.status(f"[bold green]Starting data migration to {target_service}...") as status:
                    response = await self.clients.post_json("bulk/data/migrate", {
                        "source_criteria": source_criteria,
                        "target_service": target_service,
                        "migration_type": migration_type
                    })

                if response.get("migration_id"):
                    migration_id = response["migration_id"]
                    self.console.print(f"[green]✅ Data migration started: {migration_id}[/green]")
                    self.console.print(f"[yellow]Items to migrate: {response.get('item_count', 0)}[/yellow]")
                    self.console.print(f"[yellow]Migration type: {migration_type}[/yellow]")
                else:
                    self.console.print("[red]❌ Failed to start data migration[/red]")
            else:
                self.console.print("[yellow]Data migration cancelled.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error starting data migration: {e}[/red]")

    async def cross_service_workflows(self):
        """Cross-service workflows submenu."""
        while True:
            menu = create_menu_table("Cross-Service Workflows", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Document Processing Pipeline"),
                ("2", "Quality Assurance Workflow"),
                ("3", "Content Synchronization"),
                ("4", "Automated Reporting Chain"),
                ("5", "Custom Workflow Builder"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.document_processing_pipeline()
            elif choice == "2":
                await self.quality_assurance_workflow()
            elif choice == "3":
                await self.content_synchronization()
            elif choice == "4":
                await self.automated_reporting_chain()
            elif choice == "5":
                await self.custom_workflow_builder()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def document_processing_pipeline(self):
        """Document processing pipeline."""
        try:
            pipeline_config = {
                "steps": [
                    {"service": "source-agent", "action": "fetch"},
                    {"service": "source-agent", "action": "normalize"},
                    {"service": "doc-store", "action": "store"},
                    {"service": "analysis-service", "action": "analyze"}
                ]
            }

            confirm = Confirm.ask("[bold yellow]This will run the complete document processing pipeline. Continue?[/bold yellow]")

            if confirm:
                with self.console.status("[bold green]Starting document processing pipeline...") as status:
                    response = await self.clients.post_json("bulk/workflows/document-pipeline", pipeline_config)

                if response.get("workflow_id"):
                    workflow_id = response["workflow_id"]
                    self.console.print(f"[green]✅ Document processing pipeline started: {workflow_id}[/green]")
                    await self.monitor_bulk_operation(workflow_id, "workflow")
                else:
                    self.console.print("[red]❌ Failed to start document processing pipeline[/red]")
            else:
                self.console.print("[yellow]Document processing pipeline cancelled.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error starting document processing pipeline: {e}[/red]")

    async def quality_assurance_workflow(self):
        """Quality assurance workflow."""
        try:
            qa_config = {
                "quality_threshold": 7.0,
                "auto_fix": False,
                "notification_enabled": True
            }

            confirm = Confirm.ask("[bold yellow]This will run quality assurance on all documents. Continue?[/bold yellow]")

            if confirm:
                with self.console.status("[bold green]Starting quality assurance workflow...") as status:
                    response = await self.clients.post_json("bulk/workflows/quality-assurance", qa_config)

                if response.get("workflow_id"):
                    workflow_id = response["workflow_id"]
                    self.console.print(f"[green]✅ Quality assurance workflow started: {workflow_id}[/green]")
                    self.console.print(f"[yellow]Documents to check: {response.get('document_count', 0)}[/yellow]")
                    await self.monitor_bulk_operation(workflow_id, "workflow")
                else:
                    self.console.print("[red]❌ Failed to start quality assurance workflow[/red]")
            else:
                self.console.print("[yellow]Quality assurance workflow cancelled.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error starting quality assurance workflow: {e}[/red]")

    async def content_synchronization(self):
        """Content synchronization."""
        try:
            sync_config = {
                "source_services": ["doc-store", "source-agent"],
                "target_services": ["analysis-service", "search-index"],
                "sync_mode": "incremental"
            }

            confirm = Confirm.ask("[bold yellow]This will synchronize content across services. Continue?[/bold yellow]")

            if confirm:
                with self.console.status("[bold green]Starting content synchronization...") as status:
                    response = await self.clients.post_json("bulk/workflows/content-sync", sync_config)

                if response.get("workflow_id"):
                    workflow_id = response["workflow_id"]
                    self.console.print(f"[green]✅ Content synchronization started: {workflow_id}[/green]")
                    await self.monitor_bulk_operation(workflow_id, "workflow")
                else:
                    self.console.print("[red]❌ Failed to start content synchronization[/red]")
            else:
                self.console.print("[yellow]Content synchronization cancelled.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error starting content synchronization: {e}[/red]")

    async def automated_reporting_chain(self):
        """Automated reporting chain."""
        try:
            reporting_config = {
                "report_types": ["quality", "consistency", "usage"],
                "schedule": "daily",
                "recipients": []
            }

            confirm = Confirm.ask("[bold yellow]This will set up automated reporting. Continue?[/bold yellow]")

            if confirm:
                with self.console.status("[bold green]Setting up automated reporting chain...") as status:
                    response = await self.clients.post_json("bulk/workflows/auto-reporting", reporting_config)

                if response.get("workflow_id"):
                    workflow_id = response["workflow_id"]
                    self.console.print(f"[green]✅ Automated reporting chain started: {workflow_id}[/green]")
                else:
                    self.console.print("[red]❌ Failed to start automated reporting chain[/red]")
            else:
                self.console.print("[yellow]Automated reporting chain cancelled.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error starting automated reporting chain: {e}[/red]")

    async def custom_workflow_builder(self):
        """Custom workflow builder."""
        try:
            workflow_name = Prompt.ask("[bold cyan]Workflow name[/bold cyan]")
            steps_input = Prompt.ask("[bold cyan]Workflow steps (JSON)[/bold cyan]",
                                   default='[{"service": "doc-store", "action": "analyze"}]')

            import json
            steps = json.loads(steps_input)

            confirm = Confirm.ask(f"[bold yellow]This will create a custom workflow '{workflow_name}'. Continue?[/bold yellow]")

            if confirm:
                with self.console.status(f"[bold green]Building custom workflow '{workflow_name}'...") as status:
                    response = await self.clients.post_json("bulk/workflows/custom", {
                        "name": workflow_name,
                        "steps": steps
                    })

                if response.get("workflow_id"):
                    workflow_id = response["workflow_id"]
                    self.console.print(f"[green]✅ Custom workflow created: {workflow_id}[/green]")
                else:
                    self.console.print("[red]❌ Failed to create custom workflow[/red]")
            else:
                self.console.print("[yellow]Custom workflow creation cancelled.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error creating custom workflow: {e}[/red]")

    async def bulk_reporting(self):
        """Bulk reporting submenu."""
        while True:
            menu = create_menu_table("Bulk Reporting", ["Option", "Description"])
            add_menu_rows(menu, [
                ("1", "Generate All Reports"),
                ("2", "Quality Reports Batch"),
                ("3", "Service Usage Reports"),
                ("4", "Custom Report Generation"),
                ("5", "Scheduled Report Setup"),
                ("b", "Back")
            ])
            self.console.print(menu)

            choice = Prompt.ask("[bold green]Select option[/bold green]")

            if choice == "1":
                await self.generate_all_reports()
            elif choice == "2":
                await self.quality_reports_batch()
            elif choice == "3":
                await self.service_usage_reports()
            elif choice == "4":
                await self.custom_report_generation()
            elif choice == "5":
                await self.scheduled_report_setup()
            elif choice.lower() in ["b", "back"]:
                break
            else:
                self.console.print("[red]Invalid option. Please try again.[/red]")

    async def generate_all_reports(self):
        """Generate all reports."""
        try:
            report_types = ["quality", "consistency", "usage", "performance", "error"]

            confirm = Confirm.ask(f"[bold yellow]This will generate {len(report_types)} types of reports. Continue?[/bold yellow]")

            if confirm:
                with self.console.status("[bold green]Generating all reports...") as status:
                    response = await self.clients.post_json("bulk/reports/generate-all", {
                        "report_types": report_types
                    })

                if response.get("report_batch_id"):
                    batch_id = response["report_batch_id"]
                    self.console.print(f"[green]✅ All reports generation started: {batch_id}[/green]")
                    self.console.print(f"[yellow]Reports to generate: {len(report_types)}[/yellow]")
                else:
                    self.console.print("[red]❌ Failed to start report generation[/red]")
            else:
                self.console.print("[yellow]Report generation cancelled.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error starting report generation: {e}[/red]")

    async def quality_reports_batch(self):
        """Quality reports batch."""
        try:
            quality_config = {
                "metrics": ["overall", "by_type", "trends", "recommendations"],
                "time_range": "30d"
            }

            confirm = Confirm.ask("[bold yellow]This will generate quality reports batch. Continue?[/bold yellow]")

            if confirm:
                with self.console.status("[bold green]Generating quality reports batch...") as status:
                    response = await self.clients.post_json("bulk/reports/quality-batch", quality_config)

                if response.get("report_batch_id"):
                    batch_id = response["report_batch_id"]
                    self.console.print(f"[green]✅ Quality reports batch started: {batch_id}[/green]")
                else:
                    self.console.print("[red]❌ Failed to start quality reports batch[/red]")
            else:
                self.console.print("[yellow]Quality reports batch cancelled.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error starting quality reports batch: {e}[/red]")

    async def service_usage_reports(self):
        """Service usage reports."""
        try:
            usage_config = {
                "services": ["all"],
                "metrics": ["requests", "errors", "performance", "usage"],
                "time_range": "7d"
            }

            confirm = Confirm.ask("[bold yellow]This will generate service usage reports. Continue?[/bold yellow]")

            if confirm:
                with self.console.status("[bold green]Generating service usage reports...") as status:
                    response = await self.clients.post_json("bulk/reports/usage", usage_config)

                if response.get("report_batch_id"):
                    batch_id = response["report_batch_id"]
                    self.console.print(f"[green]✅ Service usage reports started: {batch_id}[/green]")
                else:
                    self.console.print("[red]❌ Failed to start service usage reports[/red]")
            else:
                self.console.print("[yellow]Service usage reports cancelled.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error starting service usage reports: {e}[/red]")

    async def custom_report_generation(self):
        """Custom report generation."""
        try:
            report_config_input = Prompt.ask("[bold cyan]Report configuration (JSON)[/bold cyan]",
                                           default='{"type": "custom", "metrics": ["quality"], "filters": {}}')

            import json
            report_config = json.loads(report_config_input)

            confirm = Confirm.ask("[bold yellow]This will generate a custom report. Continue?[/bold yellow]")

            if confirm:
                with self.console.status("[bold green]Generating custom report...") as status:
                    response = await self.clients.post_json("bulk/reports/custom", report_config)

                if response.get("report_id"):
                    report_id = response["report_id"]
                    self.console.print(f"[green]✅ Custom report generation started: {report_id}[/green]")
                else:
                    self.console.print("[red]❌ Failed to start custom report generation[/red]")
            else:
                self.console.print("[yellow]Custom report generation cancelled.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error starting custom report generation: {e}[/red]")

    async def scheduled_report_setup(self):
        """Scheduled report setup."""
        try:
            schedule_config = {
                "frequency": "daily",
                "report_types": ["quality", "usage"],
                "time": "09:00",
                "recipients": []
            }

            confirm = Confirm.ask("[bold yellow]This will set up scheduled reports. Continue?[/bold yellow]")

            if confirm:
                with self.console.status("[bold green]Setting up scheduled reports...") as status:
                    response = await self.clients.post_json("bulk/reports/schedule", schedule_config)

                if response.get("schedule_id"):
                    schedule_id = response["schedule_id"]
                    self.console.print(f"[green]✅ Scheduled reports setup: {schedule_id}[/green]")
                    self.console.print(f"[yellow]Frequency: {schedule_config['frequency']}[/yellow]")
                    self.console.print(f"[yellow]Report types: {', '.join(schedule_config['report_types'])}[/yellow]")
                else:
                    self.console.print("[red]❌ Failed to set up scheduled reports[/red]")
            else:
                self.console.print("[yellow]Scheduled reports setup cancelled.[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Error setting up scheduled reports: {e}[/red]")

    async def monitor_bulk_operation(self, operation_id: str, operation_type: str):
        """Monitor bulk operation progress."""
        try:
            import asyncio

            self.console.print(f"[yellow]Monitoring {operation_type} operation {operation_id}...[/yellow]")

            while True:
                await asyncio.sleep(3)

                try:
                    response = await self.clients.get_json(f"bulk/operations/{operation_id}/status")

                    if response.get("completed"):
                        status = response.get("status", "unknown")
                        if status == "success":
                            self.console.print(f"[green]✅ {operation_type.title()} operation {operation_id} completed successfully![/green]")
                        else:
                            self.console.print(f"[red]❌ {operation_type.title()} operation {operation_id} failed: {response.get('error', 'Unknown error')}[/red]")
                        break
                    else:
                        progress = response.get("progress", 0)
                        processed = response.get("processed_items", 0)
                        total = response.get("total_items", 0)
                        self.console.print(f"[yellow]⏳ Progress: {progress:.1f}% ({processed}/{total} items)[/yellow]")

                except KeyboardInterrupt:
                    self.console.print(f"[yellow]Stopped monitoring {operation_type} operation.[/yellow]")
                    break
                except Exception as e:
                    self.console.print(f"[red]Error monitoring operation: {e}[/red]")
                    break

        except Exception as e:
            self.console.print(f"[red]Error monitoring bulk operation: {e}[/red]")
