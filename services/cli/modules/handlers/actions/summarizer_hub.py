from typing import Any, Dict, List, Tuple, Callable
from rich.prompt import Prompt
import json

from services.shared.integrations.clients.clients import ServiceClients
from ...utils.display_helpers import print_kv, print_list


def build_actions(console, clients: ServiceClients) -> List[Tuple[str, Callable[[], Any]]]:
    # ============================================================================
    # SUMMARIZATION ENDPOINTS
    # ============================================================================

    async def summarize():
        """Summarize text content."""
        text = Prompt.ask("Text to summarize")
        format_type = Prompt.ask("Format (markdown|html|text)", default="markdown")
        max_length = Prompt.ask("Max length", default="500")

        url = f"{clients.summarizer_hub_url()}/summarize"
        rx = await clients.post_json(url, {
            "content": text,
            "format": format_type,
            "max_length": int(max_length)
        })
        print_kv(console, "Summary Result", rx)

    async def summarize_ensemble():
        """Summarize text using multiple AI providers."""
        text = Prompt.ask("Text to summarize")
        provider = Prompt.ask("Primary provider (ollama|bedrock)", default="ollama")
        model = Prompt.ask("Model (optional)", default="")
        providers = [{"name": provider, **({"model": model} if model else {})}]

        url = f"{clients.summarizer_hub_url()}/summarize/ensemble"
        rx = await clients.post_json(url, {
            "text": text,
            "providers": providers,
            "use_hub_config": True
        })
        print_kv(console, "Ensemble Summary", rx)

    # ============================================================================
    # CATEGORIZATION ENDPOINTS
    # ============================================================================

    async def categorize_document():
        """Categorize a single document."""
        doc_id = Prompt.ask("Document ID")
        content = Prompt.ask("Document content")
        candidate_categories_input = Prompt.ask("Candidate categories (comma-separated, optional)", default="")
        use_zero_shot = Prompt.ask("Use zero-shot classification? (yes/no)", default="yes")

        document = {"id": doc_id, "content": content}
        candidate_categories = None
        if candidate_categories_input.strip():
            candidate_categories = [cat.strip() for cat in candidate_categories_input.split(",") if cat.strip()]

        payload = {
            "document": document,
            "use_zero_shot": use_zero_shot.lower() == "yes"
        }
        if candidate_categories:
            payload["candidate_categories"] = candidate_categories

        url = f"{clients.summarizer_hub_url()}/categorize"
        rx = await clients.post_json(url, payload)
        print_kv(console, f"Categorization Result for {doc_id}", rx)

    async def categorize_batch():
        """Categorize multiple documents."""
        count = Prompt.ask("Number of documents to categorize", default="3")
        count = int(count)

        documents = []
        for i in range(count):
            console.print(f"\n[bold cyan]Document {i+1}/{count}[/bold cyan]")
            doc_id = Prompt.ask(f"Document {i+1} ID")
            content = Prompt.ask(f"Document {i+1} content")
            documents.append({"id": doc_id, "content": content})

        candidate_categories_input = Prompt.ask("Candidate categories (comma-separated, optional)", default="")
        candidate_categories = None
        if candidate_categories_input.strip():
            candidate_categories = [cat.strip() for cat in candidate_categories_input.split(",") if cat.strip()]

        payload = {
            "documents": documents,
            "use_zero_shot": True
        }
        if candidate_categories:
            payload["candidate_categories"] = candidate_categories

        url = f"{clients.summarizer_hub_url()}/categorize/batch"
        rx = await clients.post_json(url, payload)
        print_kv(console, "Batch Categorization Results", rx)

    async def list_categories():
        """List available document categories."""
        url = f"{clients.summarizer_hub_url()}/categorize/categories"
        rx = await clients.get_json(url)
        print_list(console, "Available Categories", rx.get("categories", []))

    # ============================================================================
    # PEER REVIEW ENDPOINTS
    # ============================================================================

    async def peer_review():
        """Perform peer review on documentation."""
        doc_id = Prompt.ask("Document ID")
        content = Prompt.ask("Document content")
        review_type = Prompt.ask("Review type (comprehensive|quick|technical)", default="comprehensive")
        criteria_input = Prompt.ask("Specific criteria (comma-separated, optional)", default="")

        criteria = None
        if criteria_input.strip():
            criteria = [crit.strip() for crit in criteria_input.split(",") if crit.strip()]

        payload = {
            "document_id": doc_id,
            "content": content,
            "review_type": review_type
        }
        if criteria:
            payload["criteria"] = criteria

        url = f"{clients.summarizer_hub_url()}/review"
        rx = await clients.post_json(url, payload)
        print_kv(console, f"Peer Review for {doc_id}", rx)

    async def compare_versions():
        """Compare two document versions."""
        doc_id = Prompt.ask("Document ID")
        version1_content = Prompt.ask("Version 1 content")
        version2_content = Prompt.ask("Version 2 content")
        comparison_type = Prompt.ask("Comparison type (semantic|structural|comprehensive)", default="comprehensive")

        payload = {
            "document_id": doc_id,
            "version1_content": version1_content,
            "version2_content": version2_content,
            "comparison_type": comparison_type
        }

        url = f"{clients.summarizer_hub_url()}/review/compare"
        rx = await clients.post_json(url, payload)
        print_kv(console, f"Version Comparison for {doc_id}", rx)

    async def list_review_types():
        """List available review types."""
        url = f"{clients.summarizer_hub_url()}/review/types"
        rx = await clients.get_json(url)
        print_list(console, "Available Review Types", rx.get("review_types", []))

    async def list_review_criteria():
        """List available review criteria."""
        url = f"{clients.summarizer_hub_url()}/review/criteria"
        rx = await clients.get_json(url)
        print_list(console, "Available Review Criteria", rx.get("criteria", []))

    # ============================================================================
    # TESTING AND DIAGNOSTICS
    # ============================================================================

    async def test_providers():
        """Test AI provider connectivity."""
        url = f"{clients.summarizer_hub_url()}/summarize/ensemble"
        try:
            rx = await clients.post_json(url, {"text": "ping", "providers": [{"name": "ollama"}], "use_hub_config": True})
            ok = rx and "success" in rx and rx["success"]
        except Exception as e:
            console.print(f"[red]Provider test failed: {e}[/red]")
            ok = False

        print_kv(console, "Provider Test Results", {"providers_ok": ok})

    async def test_summarizer_health():
        """Test overall summarizer service health."""
        url = f"{clients.summarizer_hub_url()}/health"
        rx = await clients.get_json(url)
        print_kv(console, "Summarizer Hub Health", rx)

    async def benchmark_summarization():
        """Benchmark summarization performance."""
        test_text = "This is a test document for benchmarking summarization performance. " * 10
        iterations = Prompt.ask("Number of iterations", default="3")
        iterations = int(iterations)

        import time
        start_time = time.time()

        for i in range(iterations):
            console.print(f"Benchmarking iteration {i+1}/{iterations}...")
            try:
                url = f"{clients.summarizer_hub_url()}/summarize"
                await clients.post_json(url, {
                    "content": test_text,
                    "format": "text",
                    "max_length": 100
                })
            except Exception as e:
                console.print(f"[red]Iteration {i+1} failed: {e}[/red]")

        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / iterations

        print_kv(console, "Benchmark Results", {
            "total_iterations": iterations,
            "total_time": f"{total_time:.2f}s",
            "average_time": f"{avg_time:.2f}s",
            "iterations_per_second": f"{iterations/total_time:.2f}"
        })

    # ============================================================================
    # ORGANIZE ACTIONS BY CATEGORY
    # ============================================================================

    return [
        # Summarization
        ("📝 Summarize document", summarize),
        ("🤖 Summarize with ensemble", summarize_ensemble),
        ("⚡ Benchmark summarization", benchmark_summarization),

        # Categorization
        ("🏷️  Categorize document", categorize_document),
        ("📦 Batch categorize documents", categorize_batch),
        ("📋 List available categories", list_categories),

        # Peer Review
        ("👥 Perform peer review", peer_review),
        ("⚖️  Compare document versions", compare_versions),
        ("📋 List review types", list_review_types),
        ("🎯 List review criteria", list_review_criteria),

        # Testing & Diagnostics
        ("🩺 Service health check", test_summarizer_health),
        ("🔧 Test AI providers", test_providers),
    ]


