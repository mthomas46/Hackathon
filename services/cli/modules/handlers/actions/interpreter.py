from typing import Any, Dict, List, Tuple, Callable
from rich.prompt import Prompt
import json

from services.shared.integrations.clients.clients import ServiceClients
from ...utils.display_helpers import print_kv, print_list


def build_actions(console, clients: ServiceClients) -> List[Tuple[str, Callable[[], Any]]]:
    # ============================================================================
    # QUERY INTERPRETATION
    # ============================================================================

    async def interpret_query():
        """Interpret a natural language query."""
        query = Prompt.ask("Natural language query")
        session_id = Prompt.ask("Session ID (optional)", default="")
        user_context = Prompt.ask("User context JSON (optional)", default="{}")

        try:
            user_context_parsed = json.loads(user_context) if user_context.strip() else {}
        except:
            user_context_parsed = {}

        payload = {"query": query}
        if session_id.strip():
            payload["session_id"] = session_id
        if user_context_parsed:
            payload["user_context"] = user_context_parsed

        url = f"{clients.interpreter_url()}/interpret"
        rx = await clients.post_json(url, payload)
        print_kv(console, "Query Interpretation", rx)

    async def execute_workflow():
        """Interpret query and execute the resulting workflow."""
        query = Prompt.ask("Query to execute")
        session_id = Prompt.ask("Session ID (optional)", default="")
        user_context = Prompt.ask("User context JSON (optional)", default="{}")

        try:
            user_context_parsed = json.loads(user_context) if user_context.strip() else {}
        except:
            user_context_parsed = {}

        payload = {"query": query}
        if session_id.strip():
            payload["session_id"] = session_id
        if user_context_parsed:
            payload["user_context"] = user_context_parsed

        url = f"{clients.interpreter_url()}/execute"
        rx = await clients.post_json(url, payload)
        print_kv(console, "Workflow Execution", rx)

    # ============================================================================
    # INTENT DISCOVERY
    # ============================================================================

    async def list_supported_intents():
        """List all supported query intents with examples."""
        url = f"{clients.interpreter_url()}/intents"
        rx = await clients.get_json(url)
        print_list(console, "Supported Intents", rx.get("intents", []))

    # ============================================================================
    # INTERACTIVE QUERY BUILDING
    # ============================================================================

    async def build_complex_query():
        """Build a complex query interactively."""
        console.print("[bold cyan]Complex Query Builder[/bold cyan]")
        console.print("Answer the following questions to build your query:")

        # Query type
        query_types = ["search", "analyze", "report", "compare", "workflow"]
        console.print("\nAvailable query types:")
        for i, qtype in enumerate(query_types, 1):
            console.print(f"  {i}. {qtype}")
        choice = Prompt.ask("Select query type (number)", default="1")
        try:
            query_type = query_types[int(choice) - 1]
        except:
            query_type = "search"

        # Target
        target = Prompt.ask("What do you want to query?", default="documents")

        # Filters
        filters = []
        add_filters = Prompt.ask("Add filters? (yes/no)", default="no")
        if add_filters.lower() in ["yes", "y"]:
            filter_types = ["by_type", "by_category", "by_date", "by_author"]
            console.print("\nAvailable filter types:")
            for i, ftype in enumerate(filter_types, 1):
                console.print(f"  {i}. {ftype}")
            choice = Prompt.ask("Select filter type (number)", default="1")
            try:
                filter_type = filter_types[int(choice) - 1]
                filter_value = Prompt.ask(f"Filter value for {filter_type}")
                filters.append({"type": filter_type, "value": filter_value})
            except:
                pass

        # Build natural language query
        if query_type == "search":
            query = f"find {target}"
        elif query_type == "analyze":
            query = f"analyze {target}"
        elif query_type == "report":
            query = f"generate report on {target}"
        elif query_type == "compare":
            query = f"compare {target}"
        else:
            query = f"create workflow for {target}"

        if filters:
            filter_str = " with " + " and ".join([f"{f['type']} {f['value']}" for f in filters])
            query += filter_str

        console.print(f"\n[green]Generated query: {query}[/green]")

        # Execute the query
        execute_now = Prompt.ask("Execute this query now? (yes/no)", default="yes")
        if execute_now.lower() in ["yes", "y"]:
            await execute_workflow_interactive(query)

    async def execute_workflow_interactive(query: str):
        """Execute a workflow from the query builder."""
        console.print(f"\n[bold blue]Executing: {query}[/bold blue]")
        url = f"{clients.interpreter_url()}/execute"
        rx = await clients.post_json(url, {"query": query})
        print_kv(console, "Workflow Result", rx)

    # ============================================================================
    # BATCH OPERATIONS
    # ============================================================================

    async def batch_interpret_queries():
        """Interpret multiple queries in batch."""
        count = Prompt.ask("Number of queries to interpret", default="3")
        count = int(count)

        queries = []
        for i in range(count):
            console.print(f"\n[bold cyan]Query {i+1}/{count}[/bold cyan]")
            query = Prompt.ask(f"Query {i+1}")
            queries.append({"query": query, "index": i+1})

        console.print(f"\n[bold blue]Processing {count} queries...[/bold blue]")

        results = []
        for i, query_data in enumerate(queries):
            try:
                console.print(f"Processing query {i+1}/{count}: {query_data['query'][:50]}...")
                url = f"{clients.interpreter_url()}/interpret"
                result = await clients.post_json(url, {"query": query_data["query"]})
                results.append({
                    "index": i+1,
                    "query": query_data["query"],
                    "success": True,
                    "result": result
                })
            except Exception as e:
                results.append({
                    "index": i+1,
                    "query": query_data["query"],
                    "success": False,
                    "error": str(e)
                })

        # Display results
        console.print(f"\n[bold green]Batch Interpretation Results ({len(results)} queries)[/bold green]")
        successful = sum(1 for r in results if r["success"])
        console.print(f"Successful: {successful}/{len(results)}")

        for result in results:
            status = "✅" if result["success"] else "❌"
            console.print(f"\n{status} Query {result['index']}: {result['query'][:30]}...")
            if result["success"]:
                intent = result["result"].get("intent", "unknown")
                confidence = result["result"].get("confidence", 0)
                console.print(f"   Intent: {intent} (confidence: {confidence:.2f})")
            else:
                console.print(f"   Error: {result['error']}")

    # ============================================================================
    # TESTING AND DIAGNOSTICS
    # ============================================================================

    async def test_interpreter_health():
        """Test interpreter service health."""
        try:
            url = f"{clients.interpreter_url()}/health"
            rx = await clients.get_json(url)
            print_kv(console, "Interpreter Health", rx)
        except Exception as e:
            console.print(f"[red]Health check failed: {e}[/red]")

    async def benchmark_interpretation():
        """Benchmark query interpretation performance."""
        test_queries = [
            "find all documents about machine learning",
            "analyze the quality of this documentation",
            "generate a report on system architecture",
            "compare version 1 and version 2 of the API docs"
        ]

        iterations = Prompt.ask("Number of iterations per query", default="3")
        iterations = int(iterations)

        console.print(f"\n[bold blue]Benchmarking {len(test_queries)} queries, {iterations} iterations each...[/bold blue]")

        import time
        results = []

        for query in test_queries:
            console.print(f"\nTesting query: {query[:40]}...")
            query_times = []

            for i in range(iterations):
                try:
                    start_time = time.time()
                    url = f"{clients.interpreter_url()}/interpret"
                    await clients.post_json(url, {"query": query})
                    end_time = time.time()
                    query_times.append(end_time - start_time)
                except Exception as e:
                    console.print(f"[red]Iteration {i+1} failed: {e}[/red]")

            if query_times:
                avg_time = sum(query_times) / len(query_times)
                min_time = min(query_times)
                max_time = max(query_times)

                results.append({
                    "query": query[:40],
                    "avg_time": avg_time,
                    "min_time": min_time,
                    "max_time": max_time,
                    "iterations": len(query_times)
                })

        # Display results
        console.print(f"\n[bold green]Benchmark Results ({len(results)} queries)[/bold green]")
        table_data = []
        for result in results:
            table_data.append([
                result["query"],
                f"{result['avg_time']:.3f}s",
                f"{result['min_time']:.3f}s",
                f"{result['max_time']:.3f}s",
                str(result["iterations"])
            ])

        from rich.table import Table
        table = Table(title="Query Interpretation Benchmark")
        table.add_column("Query", style="cyan")
        table.add_column("Avg Time", style="white")
        table.add_column("Min Time", style="green")
        table.add_column("Max Time", style="red")
        table.add_column("Iterations", style="white")

        for row in table_data:
            table.add_row(*row)

        console.print(table)

    # ============================================================================
    # ORGANIZE ACTIONS BY CATEGORY
    # ============================================================================

    return [
        # Core Query Processing
        ("🔍 Interpret query", interpret_query),
        ("⚡ Execute workflow", execute_workflow),

        # Discovery & Exploration
        ("📋 List supported intents", list_supported_intents),

        # Advanced Query Building
        ("🔨 Build complex query", build_complex_query),
        ("📦 Batch interpret queries", batch_interpret_queries),

        # Testing & Diagnostics
        ("🩺 Service health check", test_interpreter_health),
        ("⚡ Benchmark interpretation", benchmark_interpretation),
    ]


