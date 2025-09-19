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
            'missing_init_files': [],
            'attribute_access': [],
            'path_config': []
        }

    def audit(self) -> Dict[str, List[str]]:
        """Run all audit checks."""
        print("🔍 Starting comprehensive codebase audit...")

        self.check_import_paths()
        self.check_circular_imports()
        self.check_missing_dependencies()
        self.check_syntax_errors()
        self.check_missing_init_files()
        self.check_attribute_access_issues()
        self.check_path_configuration()

        return self.issues

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
    auditor = CodebaseAuditor("services/project-simulation")

    try:
        issues = auditor.audit()
        auditor.print_report()

        # Summary
        total_issues = sum(len(issue_list) for issue_list in issues.values())

        print("="*80)
        if total_issues == 0:
            print("🎉 AUDIT COMPLETE: No critical issues found!")
        else:
            print(f"⚠️  AUDIT COMPLETE: {total_issues} potential issues identified")
            print("   Review the issues above and fix them systematically.")
        print("="*80)

    except Exception as e:
        print(f"❌ Audit failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
