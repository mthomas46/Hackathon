"""Quality assurance and validation service for prompt testing and bias detection."""

import re
from typing import Dict, Any, List, Optional
from ...core.service import BaseService
from services.shared.clients import ServiceClients
from services.shared.utilities import generate_id, utc_now
from .entities import PromptTestingResult, BiasDetectionResult


class ValidationService(BaseService[PromptTestingResult]):
    """Service for prompt quality assurance and validation."""

    def __init__(self):
        super().__init__(None)  # We'll implement repository methods as needed
        self.clients = ServiceClients()

    async def run_prompt_test(self, prompt_id: str, version: int, test_suite_id: str,
                            test_case: Dict[str, Any]) -> PromptTestingResult:
        """Run a single test case against a prompt."""
        # This would execute the prompt with test inputs and validate outputs
        # For now, return a mock result

        execution_time = 1.5  # Mock execution time
        passed = True  # Mock result
        quality_score = 0.85  # Mock quality score
        similarity = 0.92  # Mock similarity to expected output

        result = PromptTestingResult(
            id=generate_id(),
            prompt_id=prompt_id,
            version=version,
            test_suite_id=test_suite_id,
            test_case_id=test_case.get("id", "unknown"),
            test_name=test_case.get("name", "Unknown Test"),
            passed=passed,
            execution_time_ms=execution_time * 1000,
            output_quality_score=quality_score,
            expected_output_similarity=similarity,
            test_metadata=test_case
        )

        return result

    async def run_test_suite(self, prompt_id: str, version: int, test_suite: Dict[str, Any]) -> Dict[str, Any]:
        """Run a complete test suite against a prompt."""
        test_results = []
        passed_count = 0
        total_time = 0

        for test_case in test_suite.get("test_cases", []):
            result = await self.run_prompt_test(prompt_id, version, test_suite["id"], test_case)
            test_results.append(result.to_dict())

            if result.passed:
                passed_count += 1
            total_time += result.execution_time_ms

        suite_result = {
            "test_suite_id": test_suite["id"],
            "prompt_id": prompt_id,
            "version": version,
            "total_tests": len(test_results),
            "passed_tests": passed_count,
            "failed_tests": len(test_results) - passed_count,
            "success_rate": passed_count / len(test_results) if test_results else 0,
            "total_execution_time_ms": total_time,
            "average_execution_time_ms": total_time / len(test_results) if test_results else 0,
            "test_results": test_results
        }

        return suite_result

    def lint_prompt(self, prompt_content: str) -> Dict[str, Any]:
        """Lint a prompt for common issues and anti-patterns."""
        issues = []

        # Check for overly vague instructions
        if len(prompt_content.split()) < 10:
            issues.append({
                "type": "too_vague",
                "severity": "medium",
                "message": "Prompt is very short and may be too vague",
                "suggestion": "Add more specific instructions and context"
            })

        # Check for unclear pronouns
        if re.search(r'\b(it|they|them|this|that)\b', prompt_content, re.IGNORECASE):
            issues.append({
                "type": "unclear_reference",
                "severity": "low",
                "message": "Contains unclear pronouns that may confuse the AI",
                "suggestion": "Replace pronouns with specific nouns"
            })

        # Check for contradictory instructions
        contradictions = ["don't", "do not", "avoid", "never"]
        positive_indicators = ["do", "should", "must", "always"]

        contradiction_count = sum(1 for word in contradictions if word in prompt_content.lower())
        positive_count = sum(1 for word in positive_indicators if word in prompt_content.lower())

        if contradiction_count > positive_count * 2:
            issues.append({
                "type": "too_many_negatives",
                "severity": "medium",
                "message": "Too many negative instructions may confuse the AI",
                "suggestion": "Focus on positive instructions and desired outcomes"
            })

        # Check for formatting issues
        if prompt_content.count('\n\n') > 10:
            issues.append({
                "type": "overly_complex",
                "severity": "low",
                "message": "Prompt may be overly complex with too many sections",
                "suggestion": "Consider simplifying and focusing on key instructions"
            })

        return {
            "issues_found": len(issues),
            "issues": issues,
            "overall_score": max(0, 10 - len(issues) * 2) / 10  # Simple scoring
        }

    async def detect_bias(self, prompt_content: str, prompt_id: str = None, version: int = None) -> List[BiasDetectionResult]:
        """Detect potential biases in prompt content."""
        results = []

        # Pattern-based bias detection
        bias_patterns = self._get_bias_patterns()

        for bias_type, patterns in bias_patterns.items():
            detected_phrases = []
            severity_score = 0

            for pattern_info in patterns:
                pattern = pattern_info["pattern"]
                weight = pattern_info["weight"]

                matches = re.findall(pattern, prompt_content, re.IGNORECASE)
                if matches:
                    detected_phrases.extend(matches)
                    severity_score += weight * len(matches)

            if detected_phrases:
                result = BiasDetectionResult(
                    id=generate_id(),
                    prompt_id=prompt_id,
                    version=version,
                    bias_type=bias_type,
                    severity_score=min(severity_score, 1.0),  # Cap at 1.0
                    detected_phrases=list(set(detected_phrases)),  # Remove duplicates
                    suggested_alternatives=self._get_bias_alternatives(bias_type),
                    confidence_score=0.8,  # Pattern matching confidence
                    analysis_method="pattern_matching"
                )
                results.append(result)

        return results

    def _get_bias_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get bias detection patterns."""
        return {
            "gender": [
                {"pattern": r"\b(he|him|his)\b", "weight": 0.3},
                {"pattern": r"\b(she|her)\b", "weight": 0.3},
                {"pattern": r"\b(man|men|woman|women)\b", "weight": 0.2},
                {"pattern": r"\b(male|female)\b", "weight": 0.4}
            ],
            "racial": [
                {"pattern": r"\b(white|black|asian|hispanic)\b", "weight": 0.4},
                {"pattern": r"\b(race|ethnic|minority)\b", "weight": 0.3}
            ],
            "cultural": [
                {"pattern": r"\b(western|eastern|developed|developing|third.world)\b", "weight": 0.3},
                {"pattern": r"\b(civilized|primitive|savage)\b", "weight": 0.6}
            ],
            "political": [
                {"pattern": r"\b(liberal|conservative|left|right)\b", "weight": 0.4},
                {"pattern": r"\b(political|ideology|party)\b", "weight": 0.2}
            ],
            "socioeconomic": [
                {"pattern": r"\b(rich|poor|wealthy|impoverished)\b", "weight": 0.3},
                {"pattern": r"\b(class|elite|working.class)\b", "weight": 0.3}
            ]
        }

    def _get_bias_alternatives(self, bias_type: str) -> List[str]:
        """Get suggested alternatives for biased language."""
        alternatives = {
            "gender": ["they/them", "person", "individual", "user"],
            "racial": ["person", "individual", "user", "customer"],
            "cultural": ["person", "individual", "user", "global community"],
            "political": ["person", "individual", "user", "citizen"],
            "socioeconomic": ["person", "individual", "user", "customer"]
        }
        return alternatives.get(bias_type, ["person", "individual", "user"])

    async def validate_output(self, prompt_output: str, expected_criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Validate prompt output against expected criteria."""
        validation_results = {
            "overall_score": 1.0,
            "criteria_results": {},
            "issues": []
        }

        # Check minimum length
        min_length = expected_criteria.get("min_length", 0)
        if len(prompt_output) < min_length:
            validation_results["issues"].append({
                "type": "too_short",
                "message": f"Output is too short (minimum {min_length} characters)"
            })
            validation_results["overall_score"] *= 0.7

        # Check maximum length
        max_length = expected_criteria.get("max_length", float('inf'))
        if len(prompt_output) > max_length:
            validation_results["issues"].append({
                "type": "too_long",
                "message": f"Output is too long (maximum {max_length} characters)"
            })
            validation_results["overall_score"] *= 0.8

        # Check for required keywords
        required_keywords = expected_criteria.get("required_keywords", [])
        for keyword in required_keywords:
            if keyword.lower() not in prompt_output.lower():
                validation_results["issues"].append({
                    "type": "missing_keyword",
                    "message": f"Required keyword '{keyword}' not found"
                })
                validation_results["overall_score"] *= 0.9

        # Check for prohibited content
        prohibited_words = expected_criteria.get("prohibited_words", [])
        for word in prohibited_words:
            if word.lower() in prompt_output.lower():
                validation_results["issues"].append({
                    "type": "prohibited_content",
                    "message": f"Prohibited word '{word}' found in output"
                })
                validation_results["overall_score"] *= 0.5

        # Check structure (basic)
        if expected_criteria.get("requires_structure", False):
            if prompt_output.count('\n\n') < 2:
                validation_results["issues"].append({
                    "type": "poor_structure",
                    "message": "Output lacks proper structure"
                })
                validation_results["overall_score"] *= 0.8

        validation_results["criteria_results"] = {
            "length_check": len(prompt_output) >= min_length and len(prompt_output) <= max_length,
            "keyword_check": all(kw.lower() in prompt_output.lower() for kw in required_keywords),
            "prohibited_check": not any(word.lower() in prompt_output.lower() for word in prohibited_words),
            "structure_check": prompt_output.count('\n\n') >= 2 if expected_criteria.get("requires_structure") else True
        }

        return validation_results

    def create_test_suite(self, name: str, description: str, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a test suite for prompt validation."""
        test_suite = {
            "id": generate_id(),
            "name": name,
            "description": description,
            "test_cases": test_cases,
            "created_at": utc_now().isoformat(),
            "total_tests": len(test_cases)
        }

        return test_suite

    def get_standard_test_suites(self) -> List[Dict[str, Any]]:
        """Get standard test suites for common prompt types."""
        return [
            {
                "id": "code_generation_basic",
                "name": "Basic Code Generation Tests",
                "description": "Tests for basic code generation prompts",
                "test_cases": [
                    {
                        "id": "syntax_check",
                        "name": "Syntax Validity",
                        "input": "Write a function to add two numbers",
                        "expected_criteria": {
                            "min_length": 50,
                            "required_keywords": ["def", "return"],
                            "requires_structure": True
                        }
                    }
                ]
            },
            {
                "id": "content_writing_basic",
                "name": "Basic Content Writing Tests",
                "description": "Tests for content writing prompts",
                "test_cases": [
                    {
                        "id": "readability_check",
                        "name": "Readability Test",
                        "input": "Write a blog post about AI",
                        "expected_criteria": {
                            "min_length": 300,
                            "max_length": 2000,
                            "requires_structure": True
                        }
                    }
                ]
            }
        ]
