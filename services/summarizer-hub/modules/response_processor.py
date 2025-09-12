"""Response processing for Summarizer Hub.

Handles consistency analysis and response normalization.
"""
from typing import Dict, Any, List


class ResponseProcessor:
    """Processes and normalizes summarization responses."""

    @staticmethod
    def analyze_consistency(summaries: Dict[str, str]) -> Dict[str, Any]:
        """Analyze consistency across provider outputs."""
        agreed: List[str] = []
        disagreements: Dict[str, List[str]] = {}

        provider_lines = {k: set((v or "").splitlines()) for k, v in summaries.items()}
        if not provider_lines:
            return {"agreed": [], "differences": {}}

        # Agreed lines: intersection across providers
        lines_sets = list(provider_lines.values())
        intersection = set(lines_sets[0])
        for s in lines_sets[1:]:
            intersection &= s
        agreed = sorted(l for l in intersection if l.strip())

        # Differences per provider: lines not in intersection
        for name, lines in provider_lines.items():
            diff = sorted(l for l in lines if l.strip() and l not in intersection)
            if diff:
                disagreements[name] = diff

        return {"agreed": agreed, "differences": disagreements}

    @staticmethod
    def normalize_response(summaries: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
        """Normalize summaries to a common structure."""
        normalized: Dict[str, Dict[str, Any]] = {}
        for name, text in summaries.items():
            lines = (text or "").splitlines()
            bullets = [l.strip("- ") for l in lines if l.strip().startswith("-")][:20]
            risks = [l for l in lines if "risk" in l.lower()][:10]
            decisions = [l for l in lines if "decision" in l.lower()][:10]
            normalized[name] = {
                "summary_text": text,
                "bullets": bullets,
                "risks": risks,
                "decisions": decisions,
            }
        return normalized


# Create singleton instance
response_processor = ResponseProcessor()
