"""Template processing and rendering for bedrock proxy service."""

from typing import Dict, List

from .utils import bullets_from_text


# Template configurations
TEMPLATES = {
    "summary": {
        "sections": {
            "Summary": lambda text: bullets_from_text(text, 5),
            "Key Points": ["Decision captured", "Risks identified", "Actions listed"]
        }
    },
    "risks": {
        "sections": {
            "Risks": [
                "Ambiguous requirements may delay delivery",
                "Insufficient test coverage could miss regressions",
                "Integration dependencies might slip schedules",
            ],
            "Mitigations": [
                "Clarify acceptance criteria with PO",
                "Add unit/integration tests",
                "Decouple feature flags to reduce risk",
            ]
        }
    },
    "decisions": {
        "sections": {
            "Decisions": [
                "Use FastAPI for microservices",
                "Adopt Redis Pub/Sub for events",
                "Store short-term context in memory-agent",
            ],
            "Rationale": [
                "Fast API iteration and testability",
                "Simple, reliable eventing",
                "Lightweight context persistence",
            ]
        }
    },
    "pr_confidence": {
        "sections": {
            "Inputs": ["Jira: TICKET-123", "GitHub PR: org/repo#42", "Confluence: Design v1"],
            "Extracted Endpoints": ["/hello", "/health"],
            "Confidence": ["Score: 82", "Implements 2/2 endpoints", "No extra endpoints detected"],
            "Suggestions": ["Add negative tests", "Document error codes in OpenAPI"]
        }
    },
    "life_of_ticket": {
        "sections": {
            "Timeline": [
                "2025-01-01T09:00Z — jira — To Do -> In Progress",
                "2025-01-02T10:00Z — github — PR opened (#42)",
                "2025-01-03T16:00Z — jira — In Review -> Done",
            ],
            "Summary": ["Work completed", "Docs updated", "Tests passing"]
        }
    }
}

VALID_TEMPLATES = list(TEMPLATES.keys())
VALID_FORMATS = ["md", "txt", "json"]


def detect_template_from_prompt(prompt: str) -> str:
    """Auto-detect template type from prompt content."""
    if not prompt:
        return ""

    text_lower = prompt.lower()

    if "summary" in text_lower:
        return "summary"
    elif "risk" in text_lower:
        return "risks"
    elif "decision" in text_lower:
        return "decisions"
    elif ("pr" in text_lower or "pull request" in text_lower) and "confidence" in text_lower:
        return "pr_confidence"
    elif ("life" in text_lower or "track" in text_lower) and "ticket" in text_lower:
        return "life_of_ticket"

    return ""


def generate_default_title(template: str) -> str:
    """Generate default title for a template."""
    title_map = {
        "pr_confidence": "PR Confidence Report",
        "life_of_ticket": "Life of the Ticket",
        "summary": "Summary"
    }
    return title_map.get(template, "Bedrock Proxy Output")


def build_template_sections(template: str, prompt: str) -> Dict[str, List[str]]:
    """Build sections for a given template."""
    if not prompt:
        return {"Notes": ["Empty prompt received."]}

    template_config = TEMPLATES.get(template)
    if not template_config:
        # Default echo-like but structured summary
        return {"Echo": bullets_from_text(prompt, 5)}

    sections = {}
    for section_name, content in template_config["sections"].items():
        if callable(content):
            sections[section_name] = content(prompt)
        else:
            sections[section_name] = content

    return sections


def render_markdown(title: str, sections: Dict[str, List[str]]) -> str:
    """Render sections as markdown."""
    lines: List[str] = [f"# {title}"]
    for h, items in sections.items():
        lines.append("")
        lines.append(f"## {h}")
        for it in items:
            lines.append(f"- {it}")
    return "\n".join(lines)


def render_text(title: str, sections: Dict[str, List[str]]) -> str:
    """Render sections as plain text."""
    lines: List[str] = [title]
    for h, items in sections.items():
        lines.append(f"\n{h}:")
        for it in items:
            lines.append(f"- {it}")
    return "\n".join(lines)
