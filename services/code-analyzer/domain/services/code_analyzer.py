"""CodeAnalyzer domain service."""

import ast
from typing import Optional

from domain.entities.code_analysis import CodeAnalysis
from domain.entities.analysis_results import AnalysisResults, CodeStructure
from domain.entities.analysis_options import AnalysisOptions
from domain.value_objects import Language, ComplexityMetrics, Severity, SecurityFinding, StyleIssue
from domain.exceptions import InvalidCodeError, UnsupportedLanguageError


class CodeAnalyzer:
    """
    CodeAnalyzer domain service.
    
    Orchestrates code analysis by coordinating sub-analyzers and
    applying business rules.
    """
    
    # Constants
    MAX_LINE_LENGTH = 79
    DECISION_NODE_TYPES = (ast.If, ast.While, ast.For, ast.ExceptHandler)
    
    def analyze(
        self,
        code: str,
        language: Language,
        options: Optional[AnalysisOptions] = None
    ) -> CodeAnalysis:
        """
        Analyze code and return completed CodeAnalysis.
        
        Args:
            code: Source code to analyze
            language: Programming language
            options: Analysis options (optional)
            
        Returns:
            Completed CodeAnalysis entity
            
        Raises:
            InvalidCodeError: If code is invalid
            UnsupportedLanguageError: If language not supported
        """
        # Use default options if not provided
        if options is None:
            options = AnalysisOptions()
        
        # Create analysis entity
        analysis = CodeAnalysis(code_content=code, language=language)
        
        # Start analysis
        analysis.start_analysis()
        
        try:
            # Extract structures
            structures = self._extract_structures(code, language) if options.include_structure else []
            
            # Calculate complexity
            complexity_metrics = self._calculate_complexity(code, language) if options.include_complexity else {}
            
            # Scan for security issues
            security_findings = self._scan_security(code, language) if options.include_security else []
            
            # Check style
            style_issues = self._check_style(code, language) if options.include_style else []
            
            # Create results
            results = AnalysisResults(
                structures=structures,
                complexity_metrics=complexity_metrics,
                security_findings=security_findings,
                style_issues=style_issues
            )
            
            # Set results and complete
            analysis.set_results(results)
            analysis.complete_analysis()
            
        except Exception as e:
            # Mark as failed
            error_message = (
                f"syntax error in code: {str(e)}" 
                if self._is_syntax_error(e) 
                else f"analysis failed: {str(e)}"
            )
            analysis.mark_failed(error_message)
        
        return analysis
    
    @staticmethod
    def _get_code_lines(code: str) -> list[str]:
        """Split code into lines for analysis."""
        return code.split('\n')
    
    @staticmethod
    def _is_syntax_error(error: Exception) -> bool:
        """Check if error is a syntax error."""
        error_str = str(error).lower()
        return "syntax" in error_str or "never closed" in error_str
    
    def _extract_structures(self, code: str, language: Language) -> list:
        """Extract code structures (functions, classes, etc.)."""
        structures = []
        
        if language == Language.PYTHON:
            try:
                tree = ast.parse(code)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        structures.append(CodeStructure(
                            type="function",
                            name=node.name,
                            line_start=node.lineno,
                            line_end=node.end_lineno or node.lineno,
                            complexity=self._calculate_function_complexity(node)
                        ))
                    elif isinstance(node, ast.ClassDef):
                        structures.append(CodeStructure(
                            type="class",
                            name=node.name,
                            line_start=node.lineno,
                            line_end=node.end_lineno or node.lineno
                        ))
            except SyntaxError:
                raise
        
        return structures
    
    def _calculate_complexity(self, code: str, language: Language) -> dict:
        """Calculate complexity metrics."""
        if language != Language.PYTHON:
            return {}
        
        lines = self._get_code_lines(code)
        total_lines = len(lines)
        comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
        code_lines = total_lines - comment_lines
        
        # Basic complexity calculation
        cyclomatic = self._calculate_cyclomatic_complexity(code)
        cognitive = max(1, int(cyclomatic * 0.8))  # Rough estimate
        
        # Maintainability index (simplified formula)
        # MI = 171 - 5.2 * ln(HV) - 0.23 * G - 16.2 * ln(LOC)
        # Simplified: Higher complexity = lower maintainability
        maintainability = max(0, min(100, 100 - (cyclomatic * 3)))
        
        return {
            'cyclomatic_complexity': cyclomatic,
            'cognitive_complexity': cognitive,
            'maintainability_index': float(maintainability),
            'lines_of_code': code_lines,
            'comment_ratio': comment_lines / max(1, total_lines)
        }
    
    def _calculate_cyclomatic_complexity(self, code: str) -> int:
        """Calculate cyclomatic complexity."""
        try:
            tree = ast.parse(code)
            return self._count_complexity_in_tree(tree)
        except SyntaxError:
            return 1
    
    def _count_complexity_in_tree(self, tree: ast.AST) -> int:
        """Count complexity in an AST tree."""
        complexity = 1  # Start with 1
        
        for node in ast.walk(tree):
            # Decision points increase complexity
            if isinstance(node, self.DECISION_NODE_TYPES):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        
        return complexity
    
    def _calculate_function_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate complexity for a specific function."""
        return self._count_complexity_in_tree(node)
    
    def _scan_security(self, code: str, language: Language) -> list:
        """Scan for security vulnerabilities."""
        if language != Language.PYTHON:
            return []
        
        # Security patterns to check (pattern, severity, vuln_type, description, recommendation)
        security_patterns = [
            ('eval(', Severity.CRITICAL, "Code Injection", 
             "Use of eval() can execute arbitrary code",
             "Use ast.literal_eval() or avoid eval() entirely"),
            ('exec(', Severity.CRITICAL, "Code Injection",
             "Use of exec() can execute arbitrary code",
             "Refactor to avoid exec() or use safer alternatives"),
            ('pickle.loads(', Severity.HIGH, "Deserialization",
             "pickle.loads() can execute arbitrary code",
             "Use json or other safer serialization formats"),
        ]
        
        findings = []
        lines = self._get_code_lines(code)
        
        for line_num, line in enumerate(lines, 1):
            for pattern, severity, vuln_type, description, recommendation in security_patterns:
                if pattern in line:
                    findings.append(SecurityFinding(
                        severity=severity,
                        vulnerability_type=vuln_type,
                        line_number=line_num,
                        description=description,
                        recommendation=recommendation
                    ))
        
        return findings
    
    def _check_style(self, code: str, language: Language) -> list:
        """Check code style issues."""
        if language != Language.PYTHON:
            return []
        
        issues = []
        lines = self._get_code_lines(code)
        
        for line_num, line in enumerate(lines, 1):
            # Check line length
            if len(line) > self.MAX_LINE_LENGTH:
                issues.append(StyleIssue(
                    severity=Severity.WARNING,
                    line_number=line_num,
                    message=f"Line too long ({len(line)} > {self.MAX_LINE_LENGTH} characters)",
                    rule_id="E501"
                ))
        
        return issues

