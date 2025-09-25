"""File analysis services for different programming languages.

Provides specialized analysis functions for Python, JavaScript, and Java files.
"""

from typing import Dict, List


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

            # Extract function name
            if "function " in line:
                current_function = line.split("function ")[1].split("(")[0]
            else:
                current_function = f"anonymous_function_{i}"
            function_lines = 0

        if current_function:
            function_lines += 1
            brace_count += line.count("{") - line.count("}")

            # Check for complexity
            if (
                any(keyword in line for keyword in ["if", "for", "while"])
                and line.count("&&") + line.count("||") > 2
            ):
                issues["complex_functions"].append(f"{current_function} (line {i+1})")

            # End of function
            if brace_count == 0 and function_lines > 5:
                if function_lines > 40:
                    issues["long_methods"].append(
                        f"{current_function} ({function_lines} lines)"
                    )
                current_function = None
                function_lines = 0

    return issues


def analyze_java_file(lines: list) -> dict:
    """Analyze Java file for common issues."""
    issues = {"complex_functions": [], "long_methods": []}

    current_method = None
    method_lines = 0
    brace_count = 0

    for i, line in enumerate(lines):
        # Track method definitions
        if (
            any(modifier in line for modifier in ["public ", "private ", "protected "])
            and "(" in line
            and ")" in line
        ):
            if current_method and method_lines > 50:
                issues["long_methods"].append(
                    f"{current_method} ({method_lines} lines)"
                )

            # Extract method name
            method_start = line.find("(")
            method_name_start = line.rfind(" ", 0, method_start)
            if method_name_start != -1:
                current_method = line[method_name_start:method_start].strip()
            else:
                current_method = f"method_{i}"
            method_lines = 0
            brace_count = 0

        if current_method:
            method_lines += 1
            brace_count += line.count("{") - line.count("}")

            # Check for complexity
            if (
                any(keyword in line for keyword in ["if", "for", "while", "switch"])
                and line.count("&&") + line.count("||") > 2
            ):
                issues["complex_functions"].append(f"{current_method} (line {i+1})")

            # End of method
            if brace_count == 0 and method_lines > 5:
                if method_lines > 50:
                    issues["long_methods"].append(
                        f"{current_method} ({method_lines} lines)"
                    )
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
