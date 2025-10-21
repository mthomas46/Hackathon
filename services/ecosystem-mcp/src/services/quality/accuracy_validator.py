"""
Accuracy Validator

Validates technical accuracy of documentation against source code.
"""

import logging
import re
import ast
from typing import Dict, List, Optional, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AccuracyResult:
    """Accuracy validation result."""
    overall_score: float  # 0-1
    code_example_issues: List[str]
    api_mismatches: List[str]
    type_errors: List[str]
    factual_errors: List[str]
    warnings: List[str]
    validated_examples: int
    total_examples: int
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'overall_score': self.overall_score,
            'code_example_issues': self.code_example_issues,
            'api_mismatches': self.api_mismatches,
            'type_errors': self.type_errors,
            'factual_errors': self.factual_errors,
            'warnings': self.warnings,
            'validated_examples': self.validated_examples,
            'total_examples': self.total_examples
        }


class AccuracyValidator:
    """
    Validates documentation accuracy.
    
    Checks:
    - Code examples are syntactically valid
    - API endpoints match actual implementation
    - Data types are consistent
    - Technical claims are accurate
    """
    
    def __init__(self):
        # Common vague terms
        self.vague_terms = [
            'might', 'maybe', 'probably', 'should work',
            'usually', 'sometimes', 'often', 'may'
        ]
        
        # HTTP methods
        self.http_methods = {'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'}
        
        logger.info("AccuracyValidator initialized")
    
    async def validate(
        self,
        artifact: Dict,
        source_code: Optional[Dict] = None,
        analysis_report: Optional[Dict] = None
    ) -> AccuracyResult:
        """
        Validate documentation accuracy.
        
        Args:
            artifact: Documentation artifact
            source_code: Optional source code context
            analysis_report: Optional analysis report from Phase 3
        
        Returns:
            Accuracy validation result
        """
        title = artifact.get('title', 'Unknown')
        logger.info(f"🔬 Validating accuracy: {title}")
        
        content = artifact.get('content', '')
        
        # Validate code examples
        code_issues, validated, total = await self._validate_code_examples(content)
        
        # Validate API documentation
        api_issues = await self._validate_api_docs(content, analysis_report)
        
        # Check for common errors
        type_errors = self._check_type_consistency(content)
        
        # Check for factual accuracy
        factual_errors = await self._check_factual_accuracy(content)
        
        # Generate warnings
        warnings = self._generate_warnings(content)
        
        # Calculate score
        score = self._calculate_accuracy_score(
            code_issues,
            api_issues,
            type_errors,
            factual_errors,
            validated,
            total
        )
        
        result = AccuracyResult(
            overall_score=score,
            code_example_issues=code_issues,
            api_mismatches=api_issues,
            type_errors=type_errors,
            factual_errors=factual_errors,
            warnings=warnings,
            validated_examples=validated,
            total_examples=total
        )
        
        logger.info(f"   ✅ Accuracy score: {score:.2f}")
        if code_issues:
            logger.warning(f"   ⚠️  Code issues: {len(code_issues)}")
        if api_issues:
            logger.warning(f"   ⚠️  API issues: {len(api_issues)}")
        
        return result
    
    async def _validate_code_examples(self, content: str) -> tuple[List[str], int, int]:
        """
        Validate code examples for syntax errors.
        
        Returns:
            Tuple of (issues, validated_count, total_count)
        """
        issues = []
        validated = 0
        total = 0
        
        # Extract code blocks with language
        code_blocks = re.findall(r'```(\w+)?\n(.*?)```', content, re.DOTALL)
        total = len(code_blocks)
        
        for lang, code in code_blocks:
            lang = (lang or '').lower()
            
            if not code.strip():
                issues.append(f"Empty code block (language: {lang or 'unknown'})")
                continue
            
            if lang in ['python', 'py']:
                try:
                    # Try to parse as Python AST
                    ast.parse(code)
                    validated += 1
                except SyntaxError as e:
                    issues.append(f"Python syntax error (line {e.lineno}): {e.msg}")
                except Exception as e:
                    issues.append(f"Python parsing error: {str(e)[:100]}")
            
            elif lang in ['javascript', 'js', 'typescript', 'ts']:
                # Basic JS/TS validation
                validation_result = self._validate_javascript(code)
                if validation_result:
                    issues.append(f"JavaScript issue: {validation_result}")
                else:
                    validated += 1
            
            elif lang == 'json':
                import json
                try:
                    json.loads(code)
                    validated += 1
                except json.JSONDecodeError as e:
                    issues.append(f"JSON syntax error: {e.msg}")
            
            elif lang in ['yaml', 'yml']:
                # Basic YAML validation
                if code.count(':') == 0:
                    issues.append("YAML appears invalid (no key-value pairs)")
                else:
                    validated += 1
            
            elif lang == 'bash' or lang == 'sh':
                # Basic bash validation
                if '$(' in code and code.count('$(') != code.count(')'):
                    issues.append("Bash: Unbalanced command substitution")
                else:
                    validated += 1
            
            else:
                # Can't validate, but don't count as issue
                validated += 1
        
        return issues, validated, total
    
    def _validate_javascript(self, code: str) -> Optional[str]:
        """
        Basic JavaScript validation.
        
        Returns:
            Error message if invalid, None if appears valid
        """
        # Check for common syntax errors
        if code.count('{') != code.count('}'):
            return "Unbalanced braces"
        if code.count('(') != code.count(')'):
            return "Unbalanced parentheses"
        if code.count('[') != code.count(']'):
            return "Unbalanced brackets"
        
        # Check for obvious syntax errors
        if '){' in code or '}(' in code:
            return "Suspicious syntax: ){  or }("
        
        return None
    
    async def _validate_api_docs(
        self,
        content: str,
        analysis_report: Optional[Dict]
    ) -> List[str]:
        """Validate API documentation against analysis."""
        issues = []
        
        # Extract documented endpoints
        # Pattern: METHOD /path or METHOD path
        endpoint_pattern = r'\b(GET|POST|PUT|DELETE|PATCH)\s+(/[\w\-/{}:]*)'
        documented_endpoints = re.findall(endpoint_pattern, content)
        
        if not documented_endpoints:
            # Check for less standard format
            endpoint_pattern2 = r'`(GET|POST|PUT|DELETE|PATCH)\s+([^\`]+)`'
            documented_endpoints = re.findall(endpoint_pattern2, content)
        
        # If we have analysis report with API info
        if analysis_report and 'api_endpoints' in analysis_report:
            documented = set(f"{m} {p}" for m, p in documented_endpoints)
            actual = set(analysis_report['api_endpoints'])
            
            missing = actual - documented
            if missing and len(missing) <= 5:  # Only flag if manageable number
                issues.append(f"Undocumented endpoints: {', '.join(list(missing)[:3])}")
            
            extra = documented - actual
            if extra:
                issues.append(f"Documented but not found in source: {', '.join(list(extra)[:3])}")
        
        # Validate endpoint formats
        for method, path in documented_endpoints:
            if not path.startswith('/'):
                issues.append(f"API path should start with '/': {method} {path}")
            if ' ' in path:
                issues.append(f"API path contains spaces: {method} {path}")
        
        return issues
    
    def _check_type_consistency(self, content: str) -> List[str]:
        """Check for type consistency in documentation."""
        errors = []
        
        content_lower = content.lower()
        
        # Check for inconsistent type terminology
        if 'string' in content_lower and 'str' in content_lower:
            if content_lower.count('string') > 5 and content_lower.count('str') > 5:
                errors.append("Inconsistent string type notation (string vs str)")
        
        if 'integer' in content_lower and 'int' in content_lower:
            if content_lower.count('integer') > 3 and content_lower.count('int') > 3:
                errors.append("Inconsistent integer type notation (integer vs int)")
        
        if 'boolean' in content_lower and 'bool' in content_lower:
            if content_lower.count('boolean') > 3 and content_lower.count('bool') > 3:
                errors.append("Inconsistent boolean type notation (boolean vs bool)")
        
        # Check for mixed null/None/nil
        null_terms = ['null', 'none', 'nil']
        found_null_terms = [t for t in null_terms if t in content_lower]
        if len(found_null_terms) > 1:
            errors.append(f"Mixed null representations: {', '.join(found_null_terms)}")
        
        return errors
    
    async def _check_factual_accuracy(self, content: str) -> List[str]:
        """Check for factually incorrect or confusing statements."""
        errors = []
        
        content_lower = content.lower()
        
        # Check for async/sync confusion
        if 'synchronous' in content_lower and 'async' in content_lower:
            # Check if these are in close proximity (potential confusion)
            sync_pos = content_lower.find('synchronous')
            async_pos = content_lower.find('async')
            if abs(sync_pos - async_pos) < 200:
                errors.append("Potential async/sync confusion - verify correctness")
        
        # Check for contradictory statements
        if 'required' in content_lower and 'optional' in content_lower:
            # This might be OK, but flag for review
            pass  # Don't flag - could be documenting multiple parameters
        
        # Check for version confusion
        if 'python 2' in content_lower and 'python 3' in content_lower:
            errors.append("Document mentions both Python 2 and 3 - clarify version requirements")
        
        # Check for deprecated mentions without alternatives
        if 'deprecated' in content_lower:
            deprecated_contexts = re.findall(r'.{0,100}deprecated.{0,100}', content_lower, re.DOTALL)
            for context in deprecated_contexts:
                if 'use' not in context and 'instead' not in context:
                    errors.append("Deprecated item mentioned without alternative")
                    break
        
        return errors
    
    def _generate_warnings(self, content: str) -> List[str]:
        """Generate warnings for potential issues."""
        warnings = []
        
        content_lower = content.lower()
        
        # Check for vague language
        found_vague = []
        for term in self.vague_terms:
            if term in content_lower:
                found_vague.append(term)
        
        if found_vague:
            warnings.append(f"Vague language detected: {', '.join(found_vague[:3])}")
        
        # Check for absolute statements (often problematic)
        absolute_terms = ['always', 'never', 'all', 'none', 'every']
        found_absolute = [t for t in absolute_terms if t in content_lower]
        if len(found_absolute) > 3:
            warnings.append(f"Many absolute statements - consider if they're accurate")
        
        # Check for TODO/FIXME in examples
        if 'todo' in content_lower or 'fixme' in content_lower:
            warnings.append("TODO/FIXME found in documentation")
        
        # Check for missing error handling in examples
        code_blocks = re.findall(r'```\w*\n(.*?)```', content, re.DOTALL)
        for code in code_blocks:
            if 'try' not in code.lower() and 'except' not in code.lower():
                if 'request' in code.lower() or 'fetch' in code.lower():
                    warnings.append("Code example lacks error handling")
                    break
        
        return warnings
    
    def _calculate_accuracy_score(
        self,
        code_issues: List[str],
        api_issues: List[str],
        type_errors: List[str],
        factual_errors: List[str],
        validated_examples: int,
        total_examples: int
    ) -> float:
        """Calculate accuracy score."""
        score = 1.0
        
        # Major penalties
        score -= len(code_issues) * 0.1
        score -= len(api_issues) * 0.15
        score -= len(factual_errors) * 0.2
        
        # Minor penalties
        score -= len(type_errors) * 0.05
        
        # Bonus for validated examples
        if total_examples > 0:
            validation_rate = validated_examples / total_examples
            score += (validation_rate - 0.5) * 0.1  # Bonus if >50% validated
        
        return max(0.0, min(1.0, score))


# Singleton instance
_accuracy_validator: Optional[AccuracyValidator] = None


def get_accuracy_validator() -> AccuracyValidator:
    """Get or create singleton accuracy validator."""
    global _accuracy_validator
    if _accuracy_validator is None:
        _accuracy_validator = AccuracyValidator()
    return _accuracy_validator

