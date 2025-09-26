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
    """
    Determine file type from filename using comprehensive extension mapping.

    This is the centralized file type detection utility used across the analysis service.
    It provides consistent file type classification for all analysis operations.

    Args:
        filename: The filename or path to analyze

    Returns:
        String representing the file type (e.g., 'python', 'javascript', 'other')
    """
    # File extension to type mapping - comprehensive coverage
    extension_map = {
        # Programming languages
        (".py", ".pyc"): "python",
        (".js", ".jsx"): "javascript",
        (".ts", ".tsx"): "typescript",
        (".java",): "java",
        (".cpp", ".c++", ".cc", ".cxx", ".hpp", ".h"): "cpp",
        (".cs",): "csharp",
        (".php",): "php",
        (".rb",): "ruby",
        (".go",): "go",
        (".rs",): "rust",
        (".swift",): "swift",
        (".kt", ".kotlin"): "kotlin",
        (".scala",): "scala",
        (".pl", ".pm"): "perl",
        (".sh", ".bash"): "shell",
        (".ps1",): "powershell",
        # Web/markup
        (".html", ".htm"): "html",
        (".css",): "css",
        (".scss", ".sass"): "scss",
        (".less",): "less",
        # Data formats
        (".json",): "json",
        (".xml", ".xsd"): "xml",
        (".yml", ".yaml"): "yaml",
        # Documents
        (".md", ".markdown"): "markdown",
        (".txt",): "text",
        (".pdf",): "pdf",
        # Config files
        (".ini", ".cfg", ".conf", ".config"): "config",
        (".toml",): "toml",
        (".env",): "env",
        # Data science
        (".ipynb",): "jupyter",
        (".r", ".rmd"): "r",
        # Database
        (".sql",): "sql",
        # Docker
        ("Dockerfile", ".dockerfile"): "dockerfile",
        # Other
        (".gitignore", ".gitattributes"): "git",
        (".lock",): "lockfile",
    }

    # Extract filename if full path provided
    filename = filename.split("/")[-1].split("\\")[-1]

    # Check each extension group
    for extensions, file_type in extension_map.items():
        if isinstance(extensions, str):
            # Handle single extensions like "Dockerfile"
            if filename == extensions or filename.endswith(extensions):
                return file_type
        elif filename.lower().endswith(tuple(ext.lower() for ext in extensions)):
            return file_type

    # Default fallback
    return "other"


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


def generate_refactoring_suggestions(code_analysis: dict, structural_analysis: dict, quality_analysis: dict) -> dict:
    """Generate refactoring suggestions based on analysis results."""
    suggestions = []

    # Code complexity analysis
    if code_analysis.get("complex_functions"):
        suggestions.append("Consider refactoring complex functions")

    # Structural analysis
    if structural_analysis.get("long_methods"):
        suggestions.append("Consider refactoring long methods")
