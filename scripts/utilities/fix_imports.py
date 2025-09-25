#!/usr/bin/env python3
"""Script to fix import issues in Python files efficiently."""

import os
import subprocess
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple


def find_python_files(directory: str) -> List[str]:
    """Find all Python files in the directory."""
    files = []
    for root, dirs, filenames in os.walk(directory):
        for filename in filenames:
            if filename.endswith('.py'):
                files.append(os.path.join(root, filename))
    return files


def fix_file_imports(file_path: str) -> Tuple[str, bool, str]:
    """Fix import issues in a single file."""
    try:
        # Run autoflake with a short timeout
        result = subprocess.run([
            'autoflake', '--remove-all-unused-imports', '--remove-unused-variables',
            '--in-place', file_path
        ], capture_output=True, text=True, timeout=5)

        if result.returncode == 0:
            return file_path, True, ""
        else:
            return file_path, False, result.stderr

    except subprocess.TimeoutExpired:
        return file_path, False, "timeout"
    except Exception as e:
        return file_path, False, str(e)


def main():
    """Main function to fix imports across all files."""
    if len(sys.argv) != 2:
        print("Usage: python fix_imports.py <directory>")
        sys.exit(1)

    directory = sys.argv[1]
    if not os.path.exists(directory):
        print(f"Directory {directory} does not exist")
        sys.exit(1)

    print(f"🔍 Finding Python files in {directory}...")
    python_files = find_python_files(directory)
    print(f"📁 Found {len(python_files)} Python files")

    fixed_count = 0
    error_count = 0
    processed_count = 0

    print("🔧 Fixing imports...")

    # Process files sequentially with detailed feedback to avoid overwhelming the system
    for file_path in python_files:
        processed_count += 1
        print(f"📄 [{processed_count}/{len(python_files)}] Processing {os.path.basename(file_path)}...", end="", flush=True)

        file_result, success, error = fix_file_imports(file_path)

        if success:
            fixed_count += 1
            print(" ✅")
            if fixed_count % 20 == 0:  # Progress update every 20 files
                print(f"📊 Progress: {processed_count}/{len(python_files)} files processed, {fixed_count} fixed")
        else:
            error_count += 1
            print(f" ❌ ({error})")
            if error_count <= 5:  # Only show first 5 errors in detail
                print(f"   Error details: {error}")

    print("\n📊 Summary:")
    print(f"✅ Fixed: {fixed_count} files")
    print(f"❌ Failed: {error_count} files")
    print(f"📁 Total: {len(python_files)} files")


if __name__ == "__main__":
    main()
