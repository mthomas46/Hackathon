"""Utility functions for analysis operations.

Provides helper functions for file type detection, content extraction,
and commit message analysis.
"""


def extract_content_from_patch(patch: str) -> str:
    """Extract actual content from git diff patch."""
    if not patch:
        return ""

    lines = patch.split("\n")
    content_lines = []

    for line in lines:
        if line.startswith("+") and not line.startswith("+++"):
            content_lines.append(line[1:])  # Remove the + prefix
        elif line.startswith(" ") and not line.startswith("@@"):
            content_lines.append(line[1:])  # Remove the space prefix for context

    return "\n".join(content_lines)


def get_file_type(filename: str) -> str:
    """Determine file type from filename."""
    if filename.endswith((".py", ".pyc")):
        return "python"
    elif filename.endswith((".js", ".jsx")):
        return "javascript"
    elif filename.endswith((".ts", ".tsx")):
        return "typescript"
    elif filename.endswith((".java",)):
        return "java"
    elif filename.endswith((".cpp", ".c++", ".cc", ".cxx", ".hpp", ".h")):
        return "cpp"
    elif filename.endswith((".cs",)):
        return "csharp"
    elif filename.endswith((".php",)):
        return "php"
    elif filename.endswith((".rb",)):
        return "ruby"
    elif filename.endswith((".go",)):
        return "go"
    elif filename.endswith((".rs",)):
        return "rust"
    elif filename.endswith((".html", ".htm")):
        return "html"
    elif filename.endswith((".css",)):
        return "css"
    elif filename.endswith((".md", ".markdown")):
        return "markdown"
    elif filename.endswith((".json",)):
        return "json"
    elif filename.endswith((".xml", ".yml", ".yaml")):
        return "config"
    else:
        return "unknown"

def is_good_commit_message(message: str) -> bool:
    """Check if a commit message follows good practices."""
    # Basic checks for good commit messages
    if len(message) < 10:
        return False

    # Should start with capital letter
    if not message[0].isupper():
        return False

    # Should not end with period
    if message.endswith("."):
        return False

    # Should be descriptive but not too long
    if len(message) > 100:
        return False

    return True


def is_conventional_commit(message: str) -> bool:
    """Check if commit follows conventional commit format."""
    conventional_types = [
        "feat",
        "fix",
        "docs",
        "style",
        "refactor",
        "test",
        "chore",
        "perf",
        "ci",
        "build",
        "revert",
    ]
    first_word = message.split(":")[0].strip().lower()
    return first_word in conventional_types


def generate_refactoring_suggestions(
    code_analysis: dict, structural_analysis: dict, quality_analysis: dict
) -> dict:
    """Generate refactoring suggestions based on analysis results."""
    suggestions = []

    # Code complexity analysis
    if code_analysis.get("complex_functions"):
        suggestions.append("Consider refactoring complex functions")

    # Structural analysis
    if structural_analysis.get("long_methods"):
        suggestions.append("Consider refactoring long methods")