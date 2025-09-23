#!/usr/bin/env python3
"""Automated linting fixes for the LLM Documentation Ecosystem.

This script automatically fixes common linting issues across the codebase.
"""

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Set


def run_command(cmd: List[str], cwd: str = None) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def find_python_files(directory: str) -> List[Path]:
    """Find all Python files in the given directory."""
    return list(Path(directory).rglob("*.py"))


def fix_docstring_issues(file_path: Path) -> bool:
    """Fix common docstring issues in a file."""
    content = file_path.read_text()
    modified = False

    # Fix D400: First line should end with a period
    lines = content.split("\n")
    if lines and lines[0].startswith('"""') and not lines[0].endswith('."""'):
        # Find the closing docstring
        for i, line in enumerate(lines[1:], 1):
            if line.strip().endswith('"""'):
                # Add period to the last line before closing quotes
                if not lines[i - 1].strip().endswith("."):
                    lines[i - 1] = lines[i - 1].rstrip() + "."
                    modified = True
                break

    if modified:
        file_path.write_text("\n".join(lines))

    return modified


def remove_unused_imports(file_path: Path) -> bool:
    """Remove unused imports from a file using autoflake."""
    result = run_command([sys.executable, "-m", "pip", "install", "--quiet", "autoflake"])

    if result.returncode != 0:
        print("Failed to install autoflake")
        return False

    result = run_command(
        [sys.executable, "-m", "autoflake", "--remove-all-unused-imports", "--in-place", str(file_path)]
    )

    return result.returncode == 0


def fix_line_lengths(file_path: Path, max_length: int = 120) -> bool:
    """Fix lines that are too long by breaking them appropriately."""
    content = file_path.read_text()
    lines = content.split("\n")
    modified = False

    for i, line in enumerate(lines):
        if len(line) > max_length and not line.strip().startswith("#"):
            # Simple line breaking for function calls and assignments
            if "(" in line and line.count("(") > line.count(")"):
                # Break after opening parenthesis
                indent = len(line) - len(line.lstrip())
                lines[i] = line[: max_length - 1] + " \\"
                lines.insert(i + 1, " " * (indent + 4) + line[max_length - 1 :].lstrip())
                modified = True
            elif "=" in line and "," in line:
                # Break after comma in assignments
                indent = len(line) - len(line.lstrip())
                parts = line.split(",")
                if len(parts) > 1:
                    lines[i] = parts[0] + ","
                    for part in parts[1:]:
                        lines.insert(i + 1, " " * (indent + 4) + part.lstrip())
                    modified = True

    if modified:
        file_path.write_text("\n".join(lines))

    return modified


def main():
    """Main function to run automated linting fixes."""
    if len(sys.argv) != 2:
        print("Usage: python lint_fixes.py <directory>")
        sys.exit(1)

    target_dir = sys.argv[1]

    if not os.path.exists(target_dir):
        print(f"Directory {target_dir} does not exist")
        sys.exit(1)

    print(f"Running automated linting fixes on {target_dir}")

    python_files = find_python_files(target_dir)
    print(f"Found {len(python_files)} Python files")

    fixed_files = 0

    for file_path in python_files:
        print(f"Processing {file_path}")
        file_modified = False

        # Fix docstring issues
        if fix_docstring_issues(file_path):
            print(f"  Fixed docstring issues in {file_path}")
            file_modified = True

        # Remove unused imports
        if remove_unused_imports(file_path):
            print(f"  Removed unused imports from {file_path}")
            file_modified = True

        # Fix line lengths (basic approach)
        if fix_line_lengths(file_path):
            print(f"  Fixed line lengths in {file_path}")
            file_modified = True

        if file_modified:
            fixed_files += 1

    print(f"\nCompleted automated fixes on {fixed_files} files")

    # Run final formatting
    print("Running final code formatting...")
    run_command([sys.executable, "-m", "black", target_dir, f"--line-length=120"])
    run_command([sys.executable, "-m", "isort", target_dir, "--profile=black", "--line-length=120"])


if __name__ == "__main__":
    main()
