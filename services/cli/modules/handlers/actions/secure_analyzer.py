from typing import Any, Dict, List, Tuple, Callable
from rich.prompt import Prompt
import json

from services.shared.integrations.clients.clients import ServiceClients
from ...utils.display_helpers import print_kv, print_list


def build_actions(console, clients: ServiceClients) -> List[Tuple[str, Callable[[], Any]]]:
    # ============================================================================
    # SECURITY DETECTION ENDPOINTS
    # ============================================================================

    async def detect_security_risks():
        """Analyze content for sensitive information and security risks."""
        console.print("[bold red]🔒 Security Risk Detection[/bold red]")
        console.print("Enter the content to analyze for security risks:")

        content_input = Prompt.ask("Content")
        if not content_input.strip():
            file_path = Prompt.ask("File path")
            try:
                with open(file_path, 'r') as f:
                    content_input = f.read()
                console.print(f"✅ Loaded content from {file_path} ({len(content_input)} characters)")
            except Exception as e:
                console.print(f"[red]❌ Failed to read file: {e}[/red]")
                return

        # Optional keywords
        keywords_input = Prompt.ask("Additional keywords (comma-separated, optional)", default="")
        keywords = None
        if keywords_input.strip():
            keywords = [kw.strip() for kw in keywords_input.split(",") if kw.strip()]

        payload = {"content": content_input}
        if keywords:
            payload["keywords"] = keywords

        url = f"{clients.secure_analyzer_url()}/detect"
        rx = await clients.post_json(url, payload)

        if rx.get("success"):
            console.print("[green]✅ Security Analysis Completed[/green]")

            # Display security findings
            findings = rx.get("findings", [])
            if findings:
                console.print(f"\n[bold red]🚨 Security Findings ({len(findings)})[/bold red]")
                for i, finding in enumerate(findings, 1):
                    console.print(f"\n[red]Finding {i}:[/red]")
                    print_kv(console, "Type", finding.get("type", "unknown"))
                    print_kv(console, "Severity", finding.get("severity", "unknown"))
                    print_kv(console, "Description", finding.get("description", ""))
                    if finding.get("location"):
                        print_kv(console, "Location", finding.get("location"))
                    if finding.get("recommendation"):
                        print_kv(console, "Recommendation", finding.get("recommendation"))
            else:
                console.print("[green]✅ No security issues detected![/green]")

            # Display risk score
            risk_score = rx.get("risk_score", 0)
            if risk_score > 0:
                risk_level = "🔴 HIGH" if risk_score > 7 else "🟡 MEDIUM" if risk_score > 4 else "🟢 LOW"
                console.print(f"\n[bold]Risk Score: {risk_score}/10 - {risk_level}[/bold]")
            else:
                console.print("[green]✅ Risk Score: 0/10 - No risks detected[/green]")

            # Display analysis metadata
            metadata = rx.get("metadata", {})
            if metadata:
                console.print("
[bold blue]📊 Analysis Metadata[/bold blue]"                print_kv(console, "Processed at", metadata.get("processed_at", "unknown"))
                print_kv(console, "Processing time", f"{metadata.get('processing_time_ms', 0)}ms")
                print_kv(console, "Content size", f"{metadata.get('content_size_bytes', 0)} bytes")

        else:
            console.print(f"[red]❌ Security analysis failed: {rx.get('error', 'Unknown error')}[/red]")

    async def suggest_secure_providers():
        """Recommend appropriate AI models based on content sensitivity."""
        console.print("[bold blue]🤖 Secure AI Provider Recommendations[/bold blue]")
        console.print("Enter content to analyze for provider recommendations:")

        content = Prompt.ask("Content")
        if not content.strip():
            console.print("[red]❌ Content is required[/red]")
            return

        # Provider preferences
        preferred_providers = Prompt.ask("Preferred providers (comma-separated, optional)", default="")
        providers = None
        if preferred_providers.strip():
            providers = [p.strip() for p in preferred_providers.split(",") if p.strip()]

        # Security requirements
        security_level = Prompt.ask("Required security level (high|medium|low)", default="medium")

        payload = {
            "content": content,
            "security_level": security_level
        }
        if providers:
            payload["preferred_providers"] = providers

        url = f"{clients.secure_analyzer_url()}/suggest"
        rx = await clients.post_json(url, payload)

        if rx.get("success"):
            console.print("[green]✅ Provider Recommendations Generated[/green]")

            recommendations = rx.get("recommendations", [])
            if recommendations:
                console.print(f"\n[bold blue]🎯 Recommended Providers ({len(recommendations)})[/bold blue]")
                for i, rec in enumerate(recommendations, 1):
                    console.print(f"\n[blue]Recommendation {i}:[/blue]")
                    print_kv(console, "Provider", rec.get("provider", "unknown"))
                    print_kv(console, "Model", rec.get("model", "unknown"))
                    print_kv(console, "Security Score", f"{rec.get('security_score', 0)}/10")
                    print_kv(console, "Confidence", f"{rec.get('confidence', 0)*100:.1f}%")
                    print_kv(console, "Reason", rec.get("reason", ""))

                    if rec.get("security_features"):
                        console.print("  Security Features:"                        for feature in rec["security_features"]:
                            console.print(f"    • {feature}")
            else:
                console.print("[yellow]⚠️  No suitable providers found[/yellow]")

            # Display analysis summary
            summary = rx.get("summary", {})
            if summary:
                console.print("
[bold green]📊 Summary[/bold green]"                print_kv(console, "Risk Level", summary.get("risk_level", "unknown"))
                print_kv(console, "Compliance Status", summary.get("compliance_status", "unknown"))
                print_kv(console, "Processing Time", f"{summary.get('processing_time_ms', 0)}ms")

        else:
            console.print(f"[red]❌ Provider suggestion failed: {rx.get('error', 'Unknown error')}[/red]")

    async def secure_summarize():
        """Generate secure summaries with policy-based provider filtering."""
        console.print("[bold purple]📝 Secure Content Summarization[/bold purple]")
        console.print("Enter content to summarize securely:")

        content = Prompt.ask("Content")
        if not content.strip():
            console.print("[red]❌ Content is required[/red]")
            return

        # Summarization options
        max_length = Prompt.ask("Maximum summary length", default="200")
        format_type = Prompt.ask("Output format (text|markdown|json)", default="text")

        # Security options
        enforce_policies = Prompt.ask("Enforce security policies?", default="yes").lower() in ["yes", "y", "true"]
        allowed_providers = Prompt.ask("Allowed providers (comma-separated, optional)", default="")
        providers = None
        if allowed_providers.strip():
            providers = [p.strip() for p in allowed_providers.split(",") if p.strip()]

        payload = {
            "content": content,
            "max_length": int(max_length),
            "format": format_type,
            "enforce_policies": enforce_policies
        }
        if providers:
            payload["allowed_providers"] = providers

        url = f"{clients.secure_analyzer_url()}/summarize"
        rx = await clients.post_json(url, payload)

        if rx.get("success"):
            console.print("[green]✅ Secure Summary Generated[/green]")

            summary = rx.get("summary", {})
            if summary:
                console.print("
[bold purple]📋 Summary[/bold purple]"                print_kv(console, "Content", summary.get("content", ""))
                print_kv(console, "Length", f"{summary.get('length', 0)} characters")
                print_kv(console, "Format", summary.get("format", "unknown"))

                if summary.get("compression_ratio"):
                    print_kv(console, "Compression Ratio", f"{summary['compression_ratio']:.2f}x")

            # Display security metadata
            security = rx.get("security", {})
            if security:
                console.print("
[bold red]🔒 Security Information[/bold red]"                print_kv(console, "Risk Level", security.get("risk_level", "unknown"))
                print_kv(console, "Provider Used", security.get("provider_used", "unknown"))
                print_kv(console, "Policies Applied", str(security.get("policies_applied", [])))

                if security.get("content_filtered"):
                    console.print("[red]⚠️  Content was filtered for security[/red]")

            # Display processing metadata
            metadata = rx.get("metadata", {})
            if metadata:
                console.print("
[bold blue]⚙️  Processing Info[/bold blue]"                print_kv(console, "Processing Time", f"{metadata.get('processing_time_ms', 0)}ms")
                print_kv(console, "Provider Response Time", f"{metadata.get('provider_response_time_ms', 0)}ms")

        else:
            console.print(f"[red]❌ Secure summarization failed: {rx.get('error', 'Unknown error')}[/red]")

    # ============================================================================
    # BATCH OPERATIONS
    # ============================================================================

    async def batch_security_analysis():
        """Analyze multiple content items for security risks."""
        count = Prompt.ask("Number of items to analyze", default="3")
        count = int(count)

        analysis_type = Prompt.ask("Analysis type (detect|suggest|summarize)", default="detect")

        items = []
        for i in range(count):
            console.print(f"\n[bold cyan]Item {i+1}/{count}[/bold cyan]")
            content = Prompt.ask(f"Content {i+1}")
            name = f"item_{i+1}"
            items.append({"name": name, "content": content})

        console.print(f"\n[bold blue]🔍 Analyzing {len(items)} items for security...[/bold blue]")

        results = []
        for item in items:
            try:
                console.print(f"  Analyzing: {item['name']}...")

                if analysis_type == "detect":
                    payload = {"content": item["content"]}
                    endpoint = "/detect"
                elif analysis_type == "suggest":
                    payload = {"content": item["content"], "security_level": "medium"}
                    endpoint = "/suggest"
                else:  # summarize
                    payload = {"content": item["content"], "max_length": 100}
                    endpoint = "/summarize"

                url = f"{clients.secure_analyzer_url()}{endpoint}"
                rx = await clients.post_json(url, payload)

                results.append({
                    "name": item["name"],
                    "success": rx.get("success", False),
                    "risk_score": rx.get("risk_score", 0) if analysis_type == "detect" else None,
                    "recommendations_count": len(rx.get("recommendations", [])) if analysis_type == "suggest" else None,
                    "summary_length": len(rx.get("summary", {}).get("content", "")) if analysis_type == "summarize" else None,
                    "error": rx.get("error") if not rx.get("success") else None
                })

            except Exception as e:
                results.append({
                    "name": item["name"],
                    "success": False,
                    "risk_score": None,
                    "recommendations_count": None,
                    "summary_length": None,
                    "error": str(e)
                })

        # Display batch results
        console.print(f"\n[bold green]📊 Batch Security Analysis Results ({len(results)} items)[/bold green]")

        successful = sum(1 for r in results if r["success"])
        console.print(f"✅ Successful: {successful}/{len(results)}")

        from rich.table import Table
        table = Table(title=f"Batch {analysis_type.title()} Results")
        table.add_column("Name", style="cyan")
        table.add_column("Status", style="white")
        table.add_column("Risk Score", style="red")
        table.add_column("Details", style="blue")
        table.add_column("Result", style="green")

        for result in results:
            status = "✅" if result["success"] else "❌"

            if analysis_type == "detect":
                risk_score = str(result["risk_score"]) if result["risk_score"] is not None else "N/A"
                details = "N/A"
            elif analysis_type == "suggest":
                risk_score = "N/A"
                details = str(result["recommendations_count"]) if result["recommendations_count"] is not None else "N/A"
            else:  # summarize
                risk_score = "N/A"
                details = str(result["summary_length"]) if result["summary_length"] is not None else "N/A"

            result_text = "Success" if result["success"] else result.get("error", "Failed")[:30]

            table.add_row(
                result["name"],
                status,
                risk_score,
                details,
                result_text
            )

        console.print(table)

    # ============================================================================
    # TESTING AND DIAGNOSTICS
    # ============================================================================

    async def test_secure_analyzer_health():
        """Test secure analyzer service health."""
        url = f"{clients.secure_analyzer_url()}/health"
        rx = await clients.get_json(url)
        print_kv(console, "Secure Analyzer Health", rx)

        # Check circuit breaker status
        if rx.get("circuit_breaker_open"):
            console.print("[red]⚠️  Circuit breaker is OPEN - service may be degraded[/red]")
        else:
            console.print("[green]✅ Circuit breaker is CLOSED - service operating normally[/green]")

    async def benchmark_security_analysis():
        """Benchmark security analysis performance."""
        test_contents = [
            "This is normal content with no security issues.",
            "User password is 'admin123' and API key is 'sk-1234567890abcdef'",
            "SELECT * FROM users WHERE id = 1; DROP TABLE users;",
            "Contact: john.doe@email.com, SSN: 123-45-6789, Credit Card: 4111-1111-1111-1111",
            "Normal text content without any sensitive information or security risks."
        ]

        iterations = Prompt.ask("Number of iterations per content sample", default="3")
        iterations = int(iterations)

        console.print(f"\n[bold blue]🔒 Benchmarking security analysis with {len(test_contents)} samples, {iterations} iterations each...[/bold blue]")

        import time
        results = []

        for i, content in enumerate(test_contents):
            console.print(f"\nTesting sample {i+1}/{len(test_contents)} ({len(content)} chars)...")
            sample_times = []

            for j in range(iterations):
                try:
                    start_time = time.time()
                    url = f"{clients.secure_analyzer_url()}/detect"
                    await clients.post_json(url, {"content": content})
                    end_time = time.time()
                    sample_times.append(end_time - start_time)
                except Exception as e:
                    console.print(f"[red]Iteration {j+1} failed: {e}[/red]")

            if sample_times:
                avg_time = sum(sample_times) / len(sample_times)
                min_time = min(sample_times)
                max_time = max(sample_times)

                results.append({
                    "sample": f"sample_{i+1}",
                    "size": len(content),
                    "avg_time": avg_time,
                    "min_time": min_time,
                    "max_time": max_time,
                    "iterations": len(sample_times)
                })

        # Display results
        console.print(f"\n[bold green]📊 Security Analysis Benchmark Results ({len(results)} samples)[/bold green]")

        from rich.table import Table
        table = Table(title="Security Analysis Performance Benchmark")
        table.add_column("Sample", style="cyan")
        table.add_column("Size", style="white")
        table.add_column("Avg Time", style="green")
        table.add_column("Min Time", style="blue")
        table.add_column("Max Time", style="red")
        table.add_column("Iterations", style="white")

        for result in results:
            table.add_row(
                result["sample"],
                f"{result['size']} chars",
                f"{result['avg_time']:.3f}s",
                f"{result['min_time']:.3f}s",
                f"{result['max_time']:.3f}s",
                str(result["iterations"])
            )

        console.print(table)

        # Overall stats
        if results:
            avg_times = [r["avg_time"] for r in results]
            overall_avg = sum(avg_times) / len(avg_times)
            console.print(f"\n[bold cyan]📈 Overall Average: {overall_avg:.3f}s per security analysis[/bold cyan]")

    # ============================================================================
    # ORGANIZE ACTIONS BY CATEGORY
    # ============================================================================

    return [
        # Core Security Analysis
        ("🔍 Detect security risks", detect_security_risks),
        ("🤖 Suggest secure providers", suggest_secure_providers),
        ("📝 Generate secure summary", secure_summarize),

        # Batch Operations
        ("📦 Batch security analysis", batch_security_analysis),

        # Testing & Diagnostics
        ("🩺 Service health check", test_secure_analyzer_health),
        ("⚡ Benchmark security analysis", benchmark_security_analysis),
    ]
