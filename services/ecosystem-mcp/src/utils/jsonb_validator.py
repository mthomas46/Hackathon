"""
JSONB Field Validator

Ensures flag_modified() is called for all JSONB field updates.
Provides audit tools and enforcement mechanisms.
"""

import ast
import logging
from pathlib import Path
from typing import List, Dict, Any, Set, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class JsonbViolation:
    """Represents a JSONB update without flag_modified."""
    file_path: str
    line_number: int
    code: str
    field_name: str
    severity: str  # 'error', 'warning'
    message: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "file": self.file_path,
            "line": self.line_number,
            "code": self.code,
            "field": self.field_name,
            "severity": self.severity,
            "message": self.message
        }


class JsonbFieldValidator:
    """
    Validates JSONB field usage in Python code.
    
    Detects patterns like:
    - obj.jsonb_field = value
    - obj.jsonb_field.update(...)
    - obj.jsonb_field['key'] = value
    
    Ensures flag_modified(obj, 'jsonb_field') is called after modification.
    """
    
    # Known JSONB fields in our codebase
    KNOWN_JSONB_FIELDS = {
        'job_metadata',      # IngestionJobModel
        'metadata',          # Various models
        'config',            # Configuration models
        'settings',          # Settings models
        'properties',        # Property storage
        'data',              # Generic data storage
    }
    
    # Patterns that indicate JSONB modification
    MODIFICATION_PATTERNS = [
        'assignment',     # obj.field = value
        'update',         # obj.field.update(...)
        'pop',            # obj.field.pop(...)
        'clear',          # obj.field.clear()
        'setdefault',     # obj.field.setdefault(...)
        'item_assign',    # obj.field['key'] = value
        'item_delete',    # del obj.field['key']
    ]
    
    def __init__(self, strict: bool = False):
        """
        Initialize the validator.
        
        Args:
            strict: If True, treat warnings as errors
        """
        self.strict = strict
        self.violations: List[JsonbViolation] = []
    
    def validate_file(self, file_path: Path) -> List[JsonbViolation]:
        """
        Validate a single Python file for JSONB field usage.
        
        Args:
            file_path: Path to Python file
        
        Returns:
            List of violations found
        """
        violations = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            # Parse the Python source code
            try:
                tree = ast.parse(source, filename=str(file_path))
            except SyntaxError as e:
                logger.warning(f"Syntax error in {file_path}: {e}")
                return violations
            
            # Analyze the AST
            analyzer = JsonbAnalyzer(file_path, source, self.KNOWN_JSONB_FIELDS)
            analyzer.visit(tree)
            violations.extend(analyzer.violations)
        
        except Exception as e:
            logger.error(f"Failed to validate {file_path}: {e}")
        
        return violations
    
    def validate_directory(
        self,
        directory: Path,
        exclude_patterns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Validate all Python files in a directory.
        
        Args:
            directory: Root directory to scan
            exclude_patterns: List of glob patterns to exclude
        
        Returns:
            Dict with validation results
        """
        if exclude_patterns is None:
            exclude_patterns = [
                '*/venv/*',
                '*/test_*',
                '*/__pycache__/*',
                '*/migrations/*',
                '*/alembic/*'
            ]
        
        all_violations = []
        files_checked = 0
        files_with_violations = 0
        
        # Find all Python files
        for py_file in directory.rglob('*.py'):
            # Check exclusions
            if any(py_file.match(pattern) for pattern in exclude_patterns):
                continue
            
            files_checked += 1
            violations = self.validate_file(py_file)
            
            if violations:
                files_with_violations += 1
                all_violations.extend(violations)
        
        # Group violations by severity
        errors = [v for v in all_violations if v.severity == 'error']
        warnings = [v for v in all_violations if v.severity == 'warning']
        
        result = {
            "files_checked": files_checked,
            "files_with_violations": files_with_violations,
            "total_violations": len(all_violations),
            "errors": len(errors),
            "warnings": len(warnings),
            "violations": [v.to_dict() for v in all_violations]
        }
        
        return result
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """
        Generate a human-readable report.
        
        Args:
            results: Validation results from validate_directory
        
        Returns:
            Formatted report string
        """
        report_lines = [
            "=" * 80,
            "JSONB Field Validation Report",
            "=" * 80,
            "",
            f"Files Checked: {results['files_checked']}",
            f"Files with Violations: {results['files_with_violations']}",
            f"Total Violations: {results['total_violations']}",
            f"  - Errors: {results['errors']}",
            f"  - Warnings: {results['warnings']}",
            "",
        ]
        
        if results['violations']:
            report_lines.extend([
                "Violations:",
                "-" * 80,
                ""
            ])
            
            # Group by file
            by_file = {}
            for v in results['violations']:
                file_path = v['file']
                if file_path not in by_file:
                    by_file[file_path] = []
                by_file[file_path].append(v)
            
            for file_path, violations in sorted(by_file.items()):
                report_lines.append(f"📄 {file_path}")
                for v in violations:
                    icon = "❌" if v['severity'] == 'error' else "⚠️ "
                    report_lines.append(
                        f"  {icon} Line {v['line']}: {v['message']}"
                    )
                    report_lines.append(f"     Code: {v['code']}")
                report_lines.append("")
        else:
            report_lines.append("✅ No violations found!")
        
        report_lines.extend([
            "=" * 80,
            ""
        ])
        
        return "\n".join(report_lines)


class JsonbAnalyzer(ast.NodeVisitor):
    """
    AST visitor that analyzes JSONB field usage.
    """
    
    def __init__(
        self,
        file_path: Path,
        source: str,
        known_fields: Set[str]
    ):
        self.file_path = str(file_path)
        self.source_lines = source.split('\n')
        self.known_fields = known_fields
        self.violations: List[JsonbViolation] = []
        
        # Track flag_modified calls in current function
        self.flag_modified_calls: Set[tuple] = set()  # (obj_name, field_name)
        self.current_function = None
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definition."""
        # Save previous context
        prev_function = self.current_function
        prev_flag_calls = self.flag_modified_calls
        
        # Reset for this function
        self.current_function = node.name
        self.flag_modified_calls = set()
        
        # First pass: find all flag_modified calls
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name) and child.func.id == 'flag_modified':
                    # Extract arguments
                    if len(child.args) >= 2:
                        obj_arg = child.args[0]
                        field_arg = child.args[1]
                        
                        obj_name = self._extract_name(obj_arg)
                        if isinstance(field_arg, ast.Constant):
                            field_name = field_arg.value
                            if obj_name and field_name:
                                self.flag_modified_calls.add((obj_name, field_name))
        
        # Second pass: check for JSONB modifications
        self.generic_visit(node)
        
        # Restore previous context
        self.current_function = prev_function
        self.flag_modified_calls = prev_flag_calls
    
    def visit_Assign(self, node: ast.Assign):
        """Visit assignment statement."""
        for target in node.targets:
            if isinstance(target, ast.Attribute):
                # Check for obj.field = value
                obj_name = self._extract_name(target.value)
                field_name = target.attr
                
                if field_name in self.known_fields:
                    # Check if flag_modified is called
                    if not self._has_flag_modified(obj_name, field_name):
                        self._add_violation(
                            node,
                            field_name,
                            f"JSONB field '{field_name}' assigned without flag_modified() call",
                            'error'
                        )
            
            elif isinstance(target, ast.Subscript):
                # Check for obj.field['key'] = value
                if isinstance(target.value, ast.Attribute):
                    obj_name = self._extract_name(target.value.value)
                    field_name = target.value.attr
                    
                    if field_name in self.known_fields:
                        if not self._has_flag_modified(obj_name, field_name):
                            self._add_violation(
                                node,
                                field_name,
                                f"JSONB field '{field_name}' item modified without flag_modified() call",
                                'warning'  # Less critical if using copy pattern
                            )
        
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call):
        """Visit function call."""
        # Check for obj.field.update(...), .pop(...), etc.
        if isinstance(node.func, ast.Attribute):
            method_name = node.func.attr
            
            if method_name in ['update', 'pop', 'clear', 'setdefault', 'append', 'extend']:
                if isinstance(node.func.value, ast.Attribute):
                    obj_name = self._extract_name(node.func.value.value)
                    field_name = node.func.value.attr
                    
                    if field_name in self.known_fields:
                        if not self._has_flag_modified(obj_name, field_name):
                            self._add_violation(
                                node,
                                field_name,
                                f"JSONB field '{field_name}' modified with .{method_name}() without flag_modified() call",
                                'error'
                            )
        
        self.generic_visit(node)
    
    def visit_Delete(self, node: ast.Delete):
        """Visit delete statement."""
        for target in node.targets:
            if isinstance(target, ast.Subscript):
                # Check for del obj.field['key']
                if isinstance(target.value, ast.Attribute):
                    obj_name = self._extract_name(target.value.value)
                    field_name = target.value.attr
                    
                    if field_name in self.known_fields:
                        if not self._has_flag_modified(obj_name, field_name):
                            self._add_violation(
                                node,
                                field_name,
                                f"JSONB field '{field_name}' item deleted without flag_modified() call",
                                'warning'
                            )
        
        self.generic_visit(node)
    
    def _extract_name(self, node: ast.AST) -> Optional[str]:
        """Extract variable name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            # For chained attributes, just use the last part
            return node.attr
        return None
    
    def _has_flag_modified(self, obj_name: Optional[str], field_name: str) -> bool:
        """Check if flag_modified was called for this obj.field."""
        if not obj_name:
            return False
        return (obj_name, field_name) in self.flag_modified_calls
    
    def _add_violation(
        self,
        node: ast.AST,
        field_name: str,
        message: str,
        severity: str
    ):
        """Add a violation to the list."""
        line_number = node.lineno
        code = self.source_lines[line_number - 1].strip() if line_number <= len(self.source_lines) else ""
        
        violation = JsonbViolation(
            file_path=self.file_path,
            line_number=line_number,
            code=code,
            field_name=field_name,
            severity=severity,
            message=message
        )
        self.violations.append(violation)


# Convenience functions

def validate_codebase(
    root_dir: Optional[Path] = None,
    exclude_patterns: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Validate entire codebase for JSONB field usage.
    
    Args:
        root_dir: Root directory (defaults to services/ecosystem-mcp/src)
        exclude_patterns: Patterns to exclude
    
    Returns:
        Validation results
    """
    if root_dir is None:
        # Default to ecosystem-mcp src directory
        root_dir = Path(__file__).parent.parent.parent / "src"
    
    validator = JsonbFieldValidator()
    results = validator.validate_directory(root_dir, exclude_patterns)
    
    return results


def print_validation_report(results: Dict[str, Any]) -> None:
    """
    Print validation report to console.
    
    Args:
        results: Validation results
    """
    validator = JsonbFieldValidator()
    report = validator.generate_report(results)
    print(report)


def save_validation_report(
    results: Dict[str, Any],
    output_file: Path
) -> None:
    """
    Save validation report to file.
    
    Args:
        results: Validation results
        output_file: Output file path
    """
    validator = JsonbFieldValidator()
    report = validator.generate_report(results)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    logger.info(f"Validation report saved to {output_file}")

