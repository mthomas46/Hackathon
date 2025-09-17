from typing import Any, Dict, List, Tuple, Callable
from rich.prompt import Prompt
import json

from services.shared.integrations.clients.clients import ServiceClients
from ...utils.display_helpers import print_kv, print_list


def build_actions(console, clients: ServiceClients) -> List[Tuple[str, Callable[[], Any]]]:
    # ============================================================================
    # CODE ANALYSIS ENDPOINTS
    # ============================================================================

    async def analyze_code():
        """Analyze code and extract structural information."""
        console.print("[bold cyan]🔍 Code Analysis[/bold cyan]")
        console.print("Enter the code to analyze (or leave empty to provide a file path):")

        code_input = Prompt.ask("Code")
        if not code_input.strip():
            file_path = Prompt.ask("File path")
            try:
                with open(file_path, 'r') as f:
                    code_input = f.read()
                console.print(f"✅ Loaded code from {file_path} ({len(code_input)} characters)")
            except Exception as e:
                console.print(f"[red]❌ Failed to read file: {e}[/red]")
                return

        language = Prompt.ask("Language", default="python")
        include_functions = Prompt.ask("Include functions?", default="yes").lower() in ["yes", "y", "true"]
        include_classes = Prompt.ask("Include classes?", default="yes").lower() in ["yes", "y", "true"]

        payload = {
            "code": code_input,
            "language": language,
            "include_functions": include_functions,
            "include_classes": include_classes
        }

        url = f"{clients.code_analyzer_url()}/analyze"
        rx = await clients.post_json(url, payload)

        if rx.get("success"):
            console.print("[green]✅ Code Analysis Completed[/green]")
            data = rx.get("data", {})

            # Display language info
            print_kv(console, "Language", data.get("language", "unknown"))

            # Display functions
            if data.get("functions"):
                console.print(f"\n[bold blue]📋 Functions ({len(data['functions'])})[/bold blue]")
                for func in data["functions"]:
                    console.print(f"  • {func['name']}({', '.join(func.get('parameters', []))})")
                    if 'purpose' in func:
                        console.print(f"    └─ {func['purpose']}")
                    if 'return_type' in func:
                        console.print(f"    └─ Returns: {func['return_type']}")

            # Display classes
            if data.get("classes"):
                console.print(f"\n[bold blue]🏗️  Classes ({len(data['classes'])})[/bold blue]")
                for cls in data["classes"]:
                    console.print(f"  • {cls['name']}")
                    if 'purpose' in cls:
                        console.print(f"    └─ {cls['purpose']}")
                    if 'methods' in cls:
                        console.print(f"    └─ Methods: {', '.join(cls['methods'])}")

            # Display complexity
            if data.get("complexity"):
                console.print("
[bold blue]📊 Complexity Analysis[/bold blue]"                complexity = data["complexity"]
                console.print(f"  • Overall: {complexity.get('overall', 'N/A')}")

                if complexity.get("functions"):
                    console.print("  • Function complexity:"                    for func_name, score in complexity["functions"].items():
                        console.print(f"    └─ {func_name}: {score}")

                if complexity.get("classes"):
                    console.print("  • Class complexity:"                    for class_name, score in complexity["classes"].items():
                        console.print(f"    └─ {class_name}: {score}")

            # Display imports and patterns
            if data.get("imports"):
                console.print(f"\n[bold blue]📦 Imports ({len(data['imports'])})[/bold blue]")
                for imp in data["imports"]:
                    console.print(f"  • {imp}")

            if data.get("patterns"):
                console.print(f"\n[bold blue]🎨 Patterns ({len(data['patterns'])})[/bold blue]")
                for pattern in data["patterns"]:
                    console.print(f"  • {pattern}")

        else:
            console.print(f"[red]❌ Analysis failed: {rx.get('error', 'Unknown error')}[/red]")

    async def analyze_file():
        """Analyze a code file from disk."""
        file_path = Prompt.ask("File path")
        language = Prompt.ask("Language (auto-detect if empty)", default="")

        try:
            with open(file_path, 'r') as f:
                code = f.read()

            console.print(f"📁 Analyzing file: {file_path}")
            console.print(f"📏 File size: {len(code)} characters")

            # Auto-detect language if not specified
            if not language:
                if file_path.endswith('.py'):
                    language = 'python'
                elif file_path.endswith('.js'):
                    language = 'javascript'
                elif file_path.endswith('.java'):
                    language = 'java'
                elif file_path.endswith('.cpp') or file_path.endswith('.cc'):
                    language = 'cpp'
                else:
                    language = Prompt.ask("Could not auto-detect language. Please specify")

            payload = {
                "code": code,
                "language": language,
                "include_functions": True,
                "include_classes": True
            }

            url = f"{clients.code_analyzer_url()}/analyze"
            rx = await clients.post_json(url, payload)

            if rx.get("success"):
                console.print("[green]✅ File Analysis Completed[/green]")
                # Reuse the display logic from analyze_code
                data = rx.get("data", {})
                print_kv(console, "Language", data.get("language", "unknown"))

                if data.get("functions"):
                    console.print(f"\n[bold blue]📋 Functions ({len(data['functions'])})[/bold blue]")
                    for func in data["functions"][:5]:  # Show first 5
                        console.print(f"  • {func['name']}")

                if data.get("classes"):
                    console.print(f"\n[bold blue]🏗️  Classes ({len(data['classes'])})[/bold blue]")
                    for cls in data["classes"][:5]:  # Show first 5
                        console.print(f"  • {cls['name']}")

                console.print(f"\n[dim]💡 Use 'analyze_code' command for detailed output[/dim]")

            else:
                console.print(f"[red]❌ Analysis failed: {rx.get('error', 'Unknown error')}[/red]")

        except FileNotFoundError:
            console.print(f"[red]❌ File not found: {file_path}[/red]")
        except Exception as e:
            console.print(f"[red]❌ Error: {e}[/red]")

    async def batch_analyze():
        """Analyze multiple code snippets or files."""
        count = Prompt.ask("Number of items to analyze", default="3")
        count = int(count)

        analysis_type = Prompt.ask("Type (snippets|files)", default="snippets")

        items = []
        for i in range(count):
            console.print(f"\n[bold cyan]Item {i+1}/{count}[/bold cyan]")

            if analysis_type == "files":
                file_path = Prompt.ask(f"File path {i+1}")
                try:
                    with open(file_path, 'r') as f:
                        code = f.read()
                    language = Prompt.ask("Language", default="python")
                    items.append({
                        "name": file_path,
                        "code": code,
                        "language": language
                    })
                except Exception as e:
                    console.print(f"[red]❌ Failed to read {file_path}: {e}[/red]")
                    continue
            else:
                code = Prompt.ask(f"Code snippet {i+1}")
                language = Prompt.ask("Language", default="python")
                name = f"snippet_{i+1}"
                items.append({
                    "name": name,
                    "code": code,
                    "language": language
                })

        console.print(f"\n[bold blue]🔄 Analyzing {len(items)} items...[/bold blue]")

        results = []
        for item in items:
            try:
                console.print(f"  Analyzing: {item['name'][:30]}...")

                payload = {
                    "code": item["code"],
                    "language": item["language"],
                    "include_functions": True,
                    "include_classes": True
                }

                url = f"{clients.code_analyzer_url()}/analyze"
                rx = await clients.post_json(url, payload)

                results.append({
                    "name": item["name"],
                    "language": item["language"],
                    "success": rx.get("success", False),
                    "functions_count": len(rx.get("data", {}).get("functions", [])),
                    "classes_count": len(rx.get("data", {}).get("classes", [])),
                    "complexity": rx.get("data", {}).get("complexity", {}).get("overall"),
                    "error": rx.get("error") if not rx.get("success") else None
                })

            except Exception as e:
                results.append({
                    "name": item["name"],
                    "language": item["language"],
                    "success": False,
                    "functions_count": 0,
                    "classes_count": 0,
                    "complexity": None,
                    "error": str(e)
                })

        # Display batch results
        console.print(f"\n[bold green]📊 Batch Analysis Results ({len(results)} items)[/bold green]")

        successful = sum(1 for r in results if r["success"])
        console.print(f"✅ Successful: {successful}/{len(results)}")

        from rich.table import Table
        table = Table(title="Analysis Summary")
        table.add_column("Name", style="cyan", max_width=25)
        table.add_column("Language", style="white")
        table.add_column("Functions", style="green")
        table.add_column("Classes", style="blue")
        table.add_column("Complexity", style="yellow")
        table.add_column("Status", style="red")

        for result in results:
            status = "✅" if result["success"] else "❌"
            complexity = str(result["complexity"]) if result["complexity"] is not None else "N/A"

            table.add_row(
                result["name"][:25],
                result["language"],
                str(result["functions_count"]),
                str(result["classes_count"]),
                complexity,
                status
            )

        console.print(table)

        # Show errors if any
        failed_results = [r for r in results if not r["success"]]
        if failed_results:
            console.print(f"\n[bold red]❌ Failed Items:[/bold red]")
            for result in failed_results:
                console.print(f"  • {result['name']}: {result.get('error', 'Unknown error')}")

    # ============================================================================
    # TESTING AND DIAGNOSTICS
    # ============================================================================

    async def test_code_analyzer_health():
        """Test code analyzer service health."""
        url = f"{clients.code_analyzer_url()}/health"
        rx = await clients.get_json(url)
        print_kv(console, "Code Analyzer Health", rx)

    async def benchmark_analysis():
        """Benchmark code analysis performance."""
        test_codes = [
            "def hello():\n    print('Hello World')",
            "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n-1)",
            "class Calculator:\n    def add(self, a, b):\n        return a + b\n    def multiply(self, a, b):\n        return a * b",
            "import os\nimport sys\ndef main():\n    path = os.getcwd()\n    print(f'Current directory: {path}')\n    return 0\n\nif __name__ == '__main__':\n    main()"
        ]

        iterations = Prompt.ask("Number of iterations per code sample", default="3")
        iterations = int(iterations)

        console.print(f"\n[bold blue]⚡ Benchmarking with {len(test_codes)} code samples, {iterations} iterations each...[/bold blue]")

        import time
        results = []

        for i, code in enumerate(test_codes):
            console.print(f"\nTesting sample {i+1}/{len(test_codes)} ({len(code)} chars)...")
            sample_times = []

            for j in range(iterations):
                try:
                    start_time = time.time()
                    url = f"{clients.code_analyzer_url()}/analyze"
                    await clients.post_json(url, {
                        "code": code,
                        "language": "python",
                        "include_functions": True,
                        "include_classes": True
                    })
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
                    "size": len(code),
                    "avg_time": avg_time,
                    "min_time": min_time,
                    "max_time": max_time,
                    "iterations": len(sample_times)
                })

        # Display results
        console.print(f"\n[bold green]📊 Benchmark Results ({len(results)} samples)[/bold green]")

        from rich.table import Table
        table = Table(title="Analysis Performance Benchmark")
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
            console.print(f"\n[bold cyan]📈 Overall Average: {overall_avg:.3f}s per analysis[/bold cyan]")

    # ============================================================================
    # ORGANIZE ACTIONS BY CATEGORY
    # ============================================================================

    return [
        # Core Analysis
        ("🔍 Analyze code snippet", analyze_code),
        ("📁 Analyze code file", analyze_file),
        ("📦 Batch analyze multiple items", batch_analyze),

        # Testing & Diagnostics
        ("🩺 Service health check", test_code_analyzer_health),
        ("⚡ Benchmark analysis performance", benchmark_analysis),
    ]
