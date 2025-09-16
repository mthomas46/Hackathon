"""Style examples management for code analyzer service."""

from typing import Dict, List, Any, Optional
import os
from services.shared.utilities import stable_hash  # type: ignore


class StyleExamplesManager:
    """Manages style examples with in-memory storage and optional persistence."""

    def __init__(self):
        self._examples: Dict[str, List[Dict[str, Any]]] = {}

    def add_examples(self, items: List[Dict[str, Any]]) -> None:
        """Add style examples, organizing by language."""
        for item in items:
            language = item.get("language", "").lower().strip()
            if language:
                if language not in self._examples:
                    self._examples[language] = []
                self._examples[language].append(item)

    def get_examples(self, language: Optional[str] = None) -> Dict[str, Any]:
        """Get style examples, optionally filtered by language."""
        if language:
            language_lower = language.lower().strip()
            # Try to get from in-memory store first
            examples = self._examples.get(language_lower, [])

            # Also check doc_store if configured
            ds = os.environ.get("DOC_STORE_URL")
            if ds:
                try:
                    from services.shared.clients import ServiceClients  # type: ignore
                    svc = ServiceClients(timeout=10)
                    doc_store_examples = svc.get_json(f"{ds}/style/examples", params={"language": language})
                    if doc_store_examples and "items" in doc_store_examples:
                        examples.extend(doc_store_examples["items"])
                except Exception:
                    pass  # Fall back to in-memory only

            return {"items": examples}

        # Return summary of all languages
        summary = {}
        for lang, examples in self._examples.items():
            summary[lang] = len(examples)

        # Also check doc_store for additional languages
        ds = os.environ.get("DOC_STORE_URL")
        if ds:
            try:
                from services.shared.clients import ServiceClients  # type: ignore
                svc = ServiceClients(timeout=10)
                doc_store_summary = svc.get_json(f"{ds}/style/examples")
                if doc_store_summary and "languages" in doc_store_summary:
                    for lang, count in doc_store_summary["languages"].items():
                        if lang not in summary:
                            summary[lang] = count
                        else:
                            summary[lang] += count
            except Exception:
                pass  # Fall back to in-memory only

        return {"items": [{"language": lang, "count": count} for lang, count in summary.items()]}

    def persist_examples(self, items: List[Dict[str, Any]]) -> None:
        """Persist style examples to doc_store if configured."""
        ds = os.environ.get("DOC_STORE_URL")
        if not ds:
            return

        try:
            from services.shared.clients import ServiceClients  # type: ignore
            svc = ServiceClients(timeout=10)

            for item in items:
                meta = {
                    "type": "style_example",
                    "language": item.get("language", ""),
                    "title": item.get("title"),
                    "description": item.get("description"),
                    "purpose": item.get("purpose"),
                    "tags": item.get("tags", []),
                }

                content = item.get("snippet", "")
                svc.post_json(f"{ds}/documents", {
                    "content": content,
                    "content_hash": stable_hash(content),
                    "metadata": meta,
                })
        except Exception:
            pass  # Persistence is optional, don't fail if it doesn't work

    @property
    def languages(self) -> List[str]:
        """Get list of available languages."""
        return list(self._examples.keys())


# Global instance
style_manager = StyleExamplesManager()
