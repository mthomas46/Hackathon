#!/usr/bin/env python3
"""Comprehensive Error Audit Script for Project Simulation Service.

This script systematically checks for common error patterns we've been fixing:
1. Import path issues
2. Circular import potential
3. Missing dependencies
4. Syntax errors
5. Missing __init__.py files
6. Incorrect attribute access
7. Path configuration issues
"""

import os
import sys
import ast
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
import subprocess


class CodebaseAuditor:
    """Comprehensive auditor for common codebase issues."""

    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.issues: Dict[str, List[str]] = {
            'import_paths': [],
            'circular_imports': [],
            'missing_dependencies': [],
            'syntax_errors': [],
            'indentation_errors': [],
            'missing_init_files': [],
            'attribute_access': [],
            'path_config': []
        }

    def audit(self) -> Dict[str, List[str]]:
        """Run all audit checks."""
        print("🔍 Starting comprehensive codebase audit...")

        self.check_import_paths()
        self.check_import_errors()
        self.check_shared_module_imports()
        self.check_fallback_patterns()
        self.check_circular_imports()
        self.check_missing_dependencies()
        self.check_syntax_errors()
        self.check_indentation_errors()
        self.check_missing_init_files()
        self.check_attribute_access_issues()
        self.check_path_configuration()

        return self.issues

    def generate_import_fixes(self) -> Dict[str, str]:
        """Generate suggested fixes for import issues."""
        print("🔧 Generating import fixes...")

        fixes = {}

        # Generate fixes for missing shared module imports
        for issue in self.issues.get('missing_dependencies', []):
            if 'Imports from non-existent shared module:' in issue:
                # Extract the import line
                parts = issue.split(': Imports from non-existent shared module: ')
                if len(parts) == 2:
                    file_path = parts[0]
                    import_line = parts[1]

                    # Generate a try-except fallback
                    fix = f"""
# Original import (commented out):
# {import_line}

# Fallback implementation:
try:
    {import_line}
except ImportError:
    # Fallback implementation for missing shared module
    pass  # Add appropriate fallback logic here
"""
                    fixes[file_path] = fix

        # Generate fixes for imports without try-except
        for issue in self.issues.get('import_paths', []):
            if 'Shared import without try-except fallback:' in issue:
                parts = issue.split(': Shared import without try-except fallback: ')
                if len(parts) == 2:
                    file_path = parts[0]
                    import_line = parts[1]

                    fix = f"""
# Add try-except around this import:
try:
    {import_line}
except ImportError:
    # Fallback implementation
    pass
"""
                    if file_path not in fixes:
                        fixes[file_path] = ""
                    fixes[file_path] += fix

        return fixes

    def check_import_paths(self):
        """Check for problematic import paths."""
        print("  📂 Checking import paths...")

        python_files = self.find_python_files()

        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Check for absolute imports that might be wrong
                abs_imports = re.findall(r'from\s+services\.project_simulation\.', content)
                if abs_imports and 'services/project-simulation' in str(file_path):
                    self.issues['import_paths'].append(
                        f"{file_path}: Found absolute import that should be relative: {abs_imports[0]}"
                    )

                # Check for relative imports that go beyond top level
                rel_imports = re.findall(r'from\s+\.\.\.\.\.\.', content)
                if rel_imports:
                    self.issues['import_paths'].append(
                        f"{file_path}: Found overly relative import: {rel_imports[0]}"
                    )

                # Check for hardcoded paths
                hardcoded_paths = re.findall(r'/Users/[^\'"\s]+', content)
                if hardcoded_paths:
                    self.issues['import_paths'].append(
                        f"{file_path}: Found hardcoded absolute paths: {hardcoded_paths}"
                    )

            except Exception as e:
                self.issues['import_paths'].append(f"{file_path}: Error reading file - {e}")

    def check_circular_imports(self):
        """Check for potential circular import issues."""
        print("  🔄 Checking for circular import potential...")

        python_files = self.find_python_files()
        import_graph = {}

        for file_path in python_files:
            module_name = self.get_module_name(file_path)
            imports = self.get_imports_from_file(file_path)
            import_graph[module_name] = imports

        # Simple circular import detection
        for module, imports in import_graph.items():
            for imported in imports:
                if imported in import_graph and module in import_graph.get(imported, []):
                    self.issues['circular_imports'].append(
                        f"Potential circular import: {module} <-> {imported}"
                    )

    def check_missing_dependencies(self):
        """Check for missing Python dependencies."""
        print("  📦 Checking for missing dependencies...")

        # Check if PyYAML is available
        try:
            import yaml
        except ImportError:
            self.issues['missing_dependencies'].append("PyYAML not available")

        # Check other common dependencies
        required_deps = ['fastapi', 'uvicorn', 'pydantic', 'httpx', 'websockets']
        for dep in required_deps:
            try:
                __import__(dep)
            except ImportError:
                self.issues['missing_dependencies'].append(f"{dep} not available")

    def check_import_errors(self):
        """Check for actual import errors by attempting to import modules."""
        print("  🔍 Checking for actual import errors...")

        python_files = self.find_python_files()

        # Special check for main.py
        main_py = self.root_path / "main.py"
        if main_py.exists():
            try:
                print("    Testing main.py imports...")
                # Try to import main.py in a subprocess to avoid affecting current process
                import subprocess
                import sys
                result = subprocess.run([
                    sys.executable, "-c",
                    "import sys; sys.path.insert(0, '.'); import main"
                ], cwd=str(self.root_path), capture_output=True, text=True, timeout=10)

                if result.returncode != 0:
                    self.issues['import_paths'].append(
                        f"main.py: Import failed - {result.stderr.strip()}"
                    )
            except subprocess.TimeoutExpired:
                self.issues['import_paths'].append(
                    "main.py: Import timed out - possible circular import"
                )
            except Exception as e:
                self.issues['import_paths'].append(
                    f"main.py: Error testing imports - {e}"
                )

        for file_path in python_files:
            try:
                # Get the module name for this file
                module_name = self.get_module_name(file_path)

                # Try to import the module to see if it has import errors
                try:
                    # Only try to import if it's not the main entry point
                    if 'main.py' not in str(file_path) and '__init__.py' not in str(file_path):
                        # Use importlib to try importing
                        import importlib.util
                        spec = importlib.util.spec_from_file_location(module_name, file_path)
                        if spec and spec.loader:
                            module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(module)
                except ImportError as e:
                    self.issues['import_paths'].append(
                        f"{file_path}: Import error - {e}"
                    )
                except Exception as e:
                    # Other execution errors during import
                    if 'ImportError' in str(e) or 'ModuleNotFoundError' in str(e):
                        self.issues['import_paths'].append(
                            f"{file_path}: Module import failed - {e}"
                        )

            except Exception as e:
                self.issues['import_paths'].append(f"{file_path}: Error checking imports - {e}")

    def check_shared_module_imports(self):
        """Check for imports from shared modules that might not exist."""
        print("  🔗 Checking shared module imports...")

        python_files = self.find_python_files()

        shared_import_patterns = [
            r'from services\.shared\.',
            r'import services\.shared\.',
            r'from \.\..*\.shared\.',
            r'import \.\..*\.shared\.'
        ]

        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                for pattern in shared_import_patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        # Check if this shared module actually exists
                        module_path = match.replace('from ', '').replace('import ', '').strip()
                        if '.' in module_path:
                            # Try to resolve the module path
                            module_parts = module_path.split('.')
                            potential_paths = [
                                self.root_path / 'services' / 'shared' / f"{'/'.join(module_parts[2:])}.py",
                                self.root_path / 'services' / 'shared' / f"{'/'.join(module_parts[2:])}/__init__.py"
                            ]

                            exists = any(path.exists() for path in potential_paths)
                            if not exists:
                                self.issues['missing_dependencies'].append(
                                    f"{file_path}: Imports from non-existent shared module: {match}"
                                )

            except Exception as e:
                self.issues['import_paths'].append(f"{file_path}: Error checking shared imports - {e}")

    def check_fallback_patterns(self):
        """Check for missing try-except fallback patterns around shared imports."""
        print("  🛡️  Checking fallback patterns for shared imports...")

        python_files = self.find_python_files()

        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Look for shared imports without try-except blocks
                shared_imports = re.findall(r'from services\.shared\.[^\n]+', content)

                for import_line in shared_imports:
                    # Check if there's a try-except around this import
                    lines = content.split('\n')
                    import_line_num = None

                    for i, line in enumerate(lines):
                        if import_line in line:
                            import_line_num = i
                            break

                    if import_line_num is not None:
                        # Look for try-except pattern around this line
                        start_check = max(0, import_line_num - 5)
                        end_check = min(len(lines), import_line_num + 10)

                        has_try_except = False
                        for i in range(start_check, end_check):
                            if 'try:' in lines[i]:
                                has_try_except = True
                                break

                        if not has_try_except:
                            self.issues['import_paths'].append(
                                f"{file_path}:{import_line_num + 1}: Shared import without try-except fallback: {import_line.strip()}"
                            )

            except Exception as e:
                self.issues['import_paths'].append(f"{file_path}: Error checking fallback patterns - {e}")

    def check_syntax_errors(self):
        """Check for syntax errors in Python files."""
        print("  ⚠️  Checking for syntax errors...")

        python_files = self.find_python_files()

        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Check for unterminated strings
                if 'print("' in content or "print('" in content:
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if ('print("' in line or "print('" in line) and not line.strip().endswith('")') and not line.strip().endswith("')"):
                            if '"""' not in line and "'''" not in line:  # Skip docstrings
                                self.issues['syntax_errors'].append(
                                    f"{file_path}:{i+1}: Potential unterminated string in print statement"
                                )

                # Check for indentation issues
                ast.parse(content)  # This will raise SyntaxError if there are issues

            except SyntaxError as e:
                self.issues['syntax_errors'].append(f"{file_path}: Syntax error - {e}")
            except Exception as e:
                self.issues['syntax_errors'].append(f"{file_path}: Error parsing - {e}")

    def check_indentation_errors(self):
        """Check for indentation errors and inconsistencies in Python files."""
        print("  📏 Checking for indentation errors...")

        python_files = self.find_python_files()

        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                self._check_indentation_consistency(file_path, lines)
                self._check_indentation_levels(file_path, lines)
                self._check_block_alignment(file_path, lines)

            except Exception as e:
                self.issues['syntax_errors'].append(f"{file_path}: Error checking indentation - {e}")

    def _check_indentation_consistency(self, file_path, lines):
        """Check for consistent use of tabs vs spaces."""
        has_tabs = False
        has_spaces = False
        mixed_lines = []

        for i, line in enumerate(lines):
            # Skip empty lines and comments for this check
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue

            # Check for tabs and spaces in indentation
            indent_part = line[:len(line) - len(line.lstrip())]
            if '\t' in indent_part:
                has_tabs = True
            if ' ' in indent_part:
                has_spaces = True

            if has_tabs and has_spaces:
                mixed_lines.append(i + 1)

        if has_tabs and has_spaces:
            self.issues['indentation_errors'].append(
                f"{file_path}: Mixed tabs and spaces detected on lines: {mixed_lines[:10]}{'...' if len(mixed_lines) > 10 else ''}"
            )
        elif has_tabs:
            self.issues['indentation_errors'].append(
                f"{file_path}: Uses tabs for indentation (should use 4 spaces)"
            )

    def _check_indentation_levels(self, file_path, lines):
        """Check for proper indentation levels."""
        expected_indent = 0
        indent_stack = []

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Skip empty lines, comments, and docstrings
            if not stripped or stripped.startswith('#'):
                continue
            if stripped.startswith('"""') or stripped.startswith("'''"):
                continue
            if stripped.endswith('"""') or stripped.endswith("'''"):
                continue

            # Calculate actual indentation
            actual_indent = len(line) - len(line.lstrip())

            # Track block starts
            if stripped.endswith(':') and not stripped.startswith(('return', 'yield', 'break', 'continue', 'pass', 'raise')):
                # This is likely the start of a block
                indent_stack.append(expected_indent)
                expected_indent += 4
            elif stripped in ['pass', 'continue', 'break', '...', 'raise']:
                # These can be at any indentation level but shouldn't cause issues
                pass
            elif actual_indent != expected_indent and stripped:
                # Check for indentation mismatches
                if actual_indent > expected_indent:
                    if actual_indent - expected_indent != 4:
                        self.issues['indentation_errors'].append(
                            f"{file_path}:{i+1}: Incorrect indentation (expected {expected_indent}, got {actual_indent})"
                        )
                elif actual_indent < expected_indent:
                    # Check if we're ending a block properly
                    if indent_stack and actual_indent == indent_stack[-1]:
                        expected_indent = indent_stack.pop()
                    elif actual_indent < expected_indent:
                        self.issues['indentation_errors'].append(
                            f"{file_path}:{i+1}: Unexpected dedentation (expected {expected_indent}, got {actual_indent})"
                        )

    def _check_block_alignment(self, file_path, lines):
        """Check for proper alignment of code blocks."""
        block_keywords = ['def', 'class', 'if', 'elif', 'else', 'for', 'while', 'try', 'except', 'finally', 'with']

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Skip empty lines and comments
            if not stripped or stripped.startswith('#'):
                continue

            # Check for function/class definitions and control structures
            for keyword in block_keywords:
                if stripped.startswith(keyword + ' ') or stripped == keyword or \
                   (keyword in ['else', 'finally', 'except'] and stripped.startswith(keyword)):
                    # Check if the line ends with :
                    if not stripped.endswith(':') and not any(char in stripped for char in ['(', '[', '{']):
                        if keyword in ['else', 'finally'] and ':' in stripped:
                            continue  # These can be on same line
                        if not stripped.endswith(':'):
                            self.issues['indentation_errors'].append(
                                f"{file_path}:{i+1}: {keyword} statement should end with ':'"
                            )
                    break

            # Check for hanging indentation (line continuations)
            if line.rstrip().endswith('\\'):
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    if next_line.strip() and not next_line.startswith((' ', '\t')):
                        self.issues['indentation_errors'].append(
                            f"{file_path}:{i+1}: Line continuation should be indented"
                        )

    def generate_indentation_fixes(self) -> Dict[str, str]:
        """Generate suggested fixes for indentation issues."""
        print("🔧 Generating indentation fixes...")

        fixes = {}

        for issue in self.issues.get('indentation_errors', []):
            if 'indentation' in issue.lower() or 'indent' in issue.lower() or 'mixed tabs' in issue.lower() or 'tabs for indentation' in issue.lower():
                # Parse the issue to extract file path and line number
                parts = issue.split(':')
                if len(parts) >= 2:
                    file_path = parts[0]
                    if len(parts) >= 3:
                        try:
                            line_num = int(parts[1])
                        except ValueError:
                            line_num = None

                        fix = f"""
# Fix indentation issue{f' at line {line_num}' if line_num else ''}
# Common indentation fixes:
# 1. Use 4 spaces per indentation level (not tabs)
# 2. Ensure consistent indentation within blocks
# 3. Check that control statements end with ':'
# 4. Verify line continuations are properly indented

# Example of correct indentation:
# def function():
#     if condition:
#         return True
#     else:
#         return False
"""
                        if file_path not in fixes:
                            fixes[file_path] = ""
                        fixes[file_path] += fix

        return fixes

    def check_missing_init_files(self):
        """Check for missing __init__.py files."""
        print("  📁 Checking for missing __init__.py files...")

        for root, dirs, files in os.walk(self.root_path):
            # Skip certain directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'test_venv']]

            if '__init__.py' not in files and any(f.endswith('.py') for f in files):
                self.issues['missing_init_files'].append(
                    f"Missing __init__.py in directory: {root}"
                )

    def check_attribute_access_issues(self):
        """Check for potential attribute access issues."""
        print("  🔧 Checking for attribute access issues...")

        python_files = self.find_python_files()

        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Check for common attribute access patterns that might fail
                problematic_patterns = [
                    r'\.environment\s*=',
                    r'\.service\s*=',
                    r'config\.environment',
                    r'config\.service',
                    r'\._services\[',
                    r'\.get_service\(',
                ]

                for pattern in problematic_patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        self.issues['attribute_access'].append(
                            f"{file_path}: Potential attribute access issue with pattern '{pattern}': {matches[:3]}"
                        )

            except Exception as e:
                self.issues['attribute_access'].append(f"{file_path}: Error reading file - {e}")

    def check_path_configuration(self):
        """Check for path configuration issues."""
        print("  🛣️  Checking path configuration...")

        python_files = self.find_python_files()

        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Check for sys.path manipulation
                if 'sys.path.' in content:
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if 'sys.path.' in line:
                            self.issues['path_config'].append(
                                f"{file_path}:{i+1}: sys.path manipulation found: {line.strip()}"
                            )

                # Check for Path operations that might fail
                if 'Path(' in content and 'parent' in content:
                    path_ops = re.findall(r'Path\([^)]+\)\..*parent', content)
                    if path_ops:
                        self.issues['path_config'].append(
                            f"{file_path}: Complex Path operations: {path_ops}"
                        )

            except Exception as e:
                self.issues['path_config'].append(f"{file_path}: Error reading file - {e}")

    def find_python_files(self) -> List[Path]:
        """Find all Python files in the codebase."""
        python_files = []
        for root, dirs, files in os.walk(self.root_path):
            # Skip certain directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'test_venv', '.pytest_cache']]
            for file in files:
                if file.endswith('.py'):
                    python_files.append(Path(root) / file)
        return python_files

    def get_module_name(self, file_path: Path) -> str:
        """Get module name from file path."""
        rel_path = file_path.relative_to(self.root_path)
        return str(rel_path).replace('/', '.').replace('\\', '.').replace('.py', '')

    def get_imports_from_file(self, file_path: Path) -> List[str]:
        """Extract import statements from a Python file."""
        imports = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Simple regex to find import statements
            import_lines = re.findall(r'^(?:from\s+|\s*import\s+)([^\s\n]+)', content, re.MULTILINE)
            for imp in import_lines:
                # Clean up the import
                imp = imp.split('.')[0]  # Take only the top-level module
                if imp not in ['typing', 'os', 'sys', 'pathlib', 'datetime', 'json', 're']:
                    imports.append(imp)

        except Exception:
            pass

        return list(set(imports))  # Remove duplicates

    def print_report(self):
        """Print the audit report."""
        print("\n" + "="*80)
        print("📊 CODEBASE AUDIT REPORT")
        print("="*80)

        total_issues = sum(len(issues) for issues in self.issues.values())

        if total_issues == 0:
            print("✅ No issues found! Codebase looks clean.")
            return

        print(f"🚨 Found {total_issues} potential issues:")
        print()

        for category, issues in self.issues.items():
            if issues:
                print(f"🔍 {category.upper().replace('_', ' ')} ({len(issues)} issues):")
                for issue in issues[:10]:  # Show first 10 issues per category
                    print(f"  • {issue}")
                if len(issues) > 10:
                    print(f"  ... and {len(issues) - 10} more issues")
                print()


def main():
    """Main audit function."""
    # Use current directory if running from project-simulation directory
    import os
    current_dir = os.getcwd()
    if current_dir.endswith('project-simulation'):
        audit_path = "."
    else:
        audit_path = "services/project-simulation"

    print(f"🔍 Auditing directory: {audit_path}")
    auditor = CodebaseAuditor(audit_path)

    try:
        issues = auditor.audit()
        auditor.print_report()

        # Generate fixes for various issue types
        import_issues = issues.get('import_paths', []) + issues.get('missing_dependencies', [])
        syntax_issues = issues.get('syntax_errors', [])

        if import_issues or syntax_issues:
            print("\n🔧 CODE ISSUE ANALYSIS:")
            print("-" * 50)

            import_fixes = {}
            indent_fixes = {}

            # Import fixes
            if import_issues:
                import_fixes = auditor.generate_import_fixes()
                if import_fixes:
                    print("📝 Import Issue Fixes:")
                    for file_path, fix in import_fixes.items():
                        print(f"\n📄 {file_path}:")
                        print(fix)

            # Indentation fixes
            indent_issues = issues.get('indentation_errors', [])
            if indent_issues:
                print("\n📏 Indentation Issue Fixes:")
                indent_fixes = auditor.generate_indentation_fixes()
                for file_path, fix in indent_fixes.items():
                    print(f"\n📄 {file_path}:")
                    print(fix)

            if not import_fixes and not indent_fixes:
                print("No automated fixes available for the detected issues.")

        # Summary
        total_issues = sum(len(issue_list) for issue_list in issues.values())

        print("="*80)
        if total_issues == 0:
            print("🎉 AUDIT COMPLETE: No critical issues found!")
        else:
            print(f"⚠️  AUDIT COMPLETE: {total_issues} potential issues identified")
            print("   Review the issues above and fix them systematically.")
            if import_issues:
                print("   💡 Import issues detected - see suggested fixes above.")
        print("="*80)

    except Exception as e:
        print(f"❌ Audit failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
