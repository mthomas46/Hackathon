"""File analysis services for different programming languages.

Provides specialized analysis functions for Python, JavaScript, and Java files.
"""

from typing import Dict, List

# Import centralized utilities
from ..utilities.analysis_utils import get_file_type


def analyze_python_file(lines: list) -> dict:
    """Analyze Python file for common issues."""
    issues = {"complex_functions": [], "long_methods": []}

    current_function = None
    function_lines = 0

    for i, line in enumerate(lines):
        # Track function definitions
        if line.strip().startswith("def "):
            if current_function and function_lines > 50:
                issues["long_methods"].append(
                    f"{current_function} ({function_lines} lines)"
                )

            current_function = line.split("def ")[1].split("(")[0]
            function_lines = 0
        elif current_function:
            function_lines += 1

            # Check for complexity indicators
            if (
                any(
                    keyword in line.lower()
                    for keyword in ["if", "elif", "for", "while"]
                )
                and line.count("and") + line.count("or") > 2
            ):
                issues["complex_functions"].append(f"{current_function} (line {i+1})")

    # Check last function
    if current_function and function_lines > 50:
        issues["long_methods"].append(f"{current_function} ({function_lines} lines)")

    return issues


def analyze_js_file(lines: list) -> dict:
    """Analyze JavaScript/TypeScript file for common issues."""
    issues = {"complex_functions": [], "long_methods": []}

    current_function = None
    function_lines = 0
    brace_count = 0

    for i, line in enumerate(lines):
        # Track function definitions
        if "function " in line or "=> " in line or "const " in line and " = (" in line:
            if current_function and function_lines > 40:
                issues["long_methods"].append(
                    f"{current_function} ({function_lines} lines)"
                )
def _extract_function_name_js(line: str, line_index: int) -> str:
    """Extract function name from JavaScript function definition."""
    if "function " in line:
        return line.split("function ")[1].split("(")[0]
    return f"anonymous_function_{line_index}"


def _is_js_function_definition(line: str) -> bool:
    """Check if line contains a JavaScript function definition."""
    return ("function " in line or "=> " in line or
            ("const " in line and " = (" in line))


def _check_js_complexity(line: str, current_function: str, line_index: int, issues: dict):
    """Check for complex JavaScript code patterns."""
    if (any(keyword in line for keyword in ["if", "for", "while"]) and
        line.count("&&") + line.count("||") > 2):
        issues["complex_functions"].append(f"{current_function} (line {line_index+1})")


def analyze_js_file(lines: list) -> dict:
    """Analyze JavaScript/TypeScript file for common issues."""
    issues = {"complex_functions": [], "long_methods": []}
    current_function = None
    function_lines = 0
    brace_count = 0

    for i, line in enumerate(lines):
        # Track function definitions
        if _is_js_function_definition(line):
            if current_function and function_lines > 40:
                issues["long_methods"].append(f"{current_function} ({function_lines} lines)")

            current_function = _extract_function_name_js(line, i)
            function_lines = 0
            brace_count = 0

        if current_function:
            function_lines += 1
            brace_count += line.count("{") - line.count("}")

            _check_js_complexity(line, current_function, i, issues)

            # End of function
            if brace_count == 0 and function_lines > 5:
                if function_lines > 40:
                    issues["long_methods"].append(f"{current_function} ({function_lines} lines)")
                current_function = None
                function_lines = 0

    return issues


def _extract_method_name_java(line: str, line_index: int) -> str:
    """Extract method name from Java method definition."""
    method_start = line.find("(")
    if method_start == -1:
        return f"method_{line_index}"

    method_name_start = line.rfind(" ", 0, method_start)
    if method_name_start != -1:
        return line[method_name_start:method_start].strip()
    return f"method_{line_index}"


def _is_java_method_definition(line: str) -> bool:
    """Check if line contains a Java method definition."""
    return (any(modifier in line for modifier in ["public ", "private ", "protected "]) and
            "(" in line and ")" in line)


def _check_java_complexity(line: str, current_method: str, line_index: int, issues: dict):
    """Check for complex Java code patterns."""
    if (any(keyword in line for keyword in ["if", "for", "while", "switch"]) and
        line.count("&&") + line.count("||") > 2):
        issues["complex_functions"].append(f"{current_method} (line {line_index+1})")


def analyze_java_file(lines: list) -> dict:
    """Analyze Java file for common issues."""
    issues = {"complex_functions": [], "long_methods": []}
    current_method = None
    method_lines = 0
    brace_count = 0

    for i, line in enumerate(lines):
        # Track method definitions
        if _is_java_method_definition(line):
            if current_method and method_lines > 50:
                issues["long_methods"].append(f"{current_method} ({method_lines} lines)")

            current_method = _extract_method_name_java(line, i)
            method_lines = 0
            brace_count = 0

        if current_method:
            method_lines += 1
            brace_count += line.count("{") - line.count("}")

            _check_java_complexity(line, current_method, i, issues)

            # End of method
            if brace_count == 0 and method_lines > 5:
                if method_lines > 50:
                    issues["long_methods"].append(f"{current_method} ({method_lines} lines)")
                current_method = None
                method_lines = 0

    return issues


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


# get_file_type is now imported from analysis_utils
