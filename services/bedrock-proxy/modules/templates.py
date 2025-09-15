"""Template processing and rendering for bedrock proxy service.

This module defines response templates for structured AI output generation,
including template detection, content building, and format rendering.
"""
from typing import Dict, List

from .utils import bullets_from_text

# Supported template types for response generation
SUPPORTED_TEMPLATES = [
    "summary",      # General summary with key points
    "risks",        # Risk assessment with mitigations
    "decisions",    # Decision documentation
    "pr_confidence", # Pull request confidence analysis
    "life_of_ticket" # Ticket lifecycle tracking
]

# Supported output formats
SUPPORTED_FORMATS = ["md", "txt", "json"]


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

# Extract valid values for validation (maintaining backward compatibility)
VALID_TEMPLATES = list(TEMPLATES.keys())
VALID_FORMATS = SUPPORTED_FORMATS


def detect_template_from_prompt(prompt: str) -> str:
    """Auto-detect the most appropriate template type from prompt content.

    Analyzes the input prompt text to determine which response template
    would be most suitable based on keywords and context.

    Args:
        prompt: Input text to analyze for template detection

    Returns:
        Template name string, or empty string if no match found
    """
    if not prompt:
        return ""

    text_lower = prompt.lower()

    # Check for template-specific keywords in order of specificity
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
    """Generate an appropriate default title for the given template type.

    Args:
        template: Template name (e.g., 'summary', 'risks', etc.)

    Returns:
        Human-readable title string for the template
    """
    title_map = {
        "pr_confidence": "PR Confidence Report",
        "life_of_ticket": "Life of the Ticket",
        "summary": "Summary",
        "risks": "Risk Assessment",
        "decisions": "Decision Analysis"
    }
    return title_map.get(template, "Bedrock Proxy Output")


def build_template_sections(template: str, prompt: str) -> Dict[str, List[str]]:
    """Build structured content sections for the specified template type.

    Processes the template configuration and generates appropriate content
    sections based on the template type and input prompt.

    Args:
        template: Template name to use for content structuring
        prompt: Input text that may be processed for dynamic content

    Returns:
        Dictionary mapping section names to lists of content strings
    """
    if not prompt:
        return {"Notes": ["Empty prompt received."]}

    template_config = TEMPLATES.get(template)
    if not template_config:
        # Fallback to a simple structured summary when template not found
        return {"Echo": bullets_from_text(prompt, 5)}

    sections = {}
    for section_name, content in template_config["sections"].items():
        if callable(content):
            # Dynamic content generation (e.g., bullet points from text)
            sections[section_name] = content(prompt)
        else:
            # Static content (predefined lists)
            sections[section_name] = content

    return sections


def render_markdown(title: str, sections: Dict[str, List[str]]) -> str:
    """Render structured content sections as formatted Markdown text.

    Args:
        title: Main title for the document
        sections: Dictionary of section names to content lists

    Returns:
        Complete Markdown document as a string
    """
    lines: List[str] = [f"# {title}"]

    for section_name, items in sections.items():
        lines.append("")  # Add spacing between sections
        lines.append(f"## {section_name}")
        for item in items:
            lines.append(f"- {item}")

    return "\n".join(lines)


def render_text(title: str, sections: Dict[str, List[str]]) -> str:
    """Render structured content sections as plain text format.

    Args:
        title: Main title for the document
        sections: Dictionary of section names to content lists

    Returns:
        Complete plain text document as a string
    """
    lines: List[str] = [title]

    for section_name, items in sections.items():
        lines.append(f"\n{section_name}:")
        for item in items:
            lines.append(f"- {item}")

    return "\n".join(lines)
