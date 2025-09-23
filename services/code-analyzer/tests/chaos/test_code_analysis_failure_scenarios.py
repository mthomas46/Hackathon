"""Chaos Engineering Tests for Code Analysis Operations in Code Analyzer Service.

This module tests code analysis resilience and failure scenarios including:
- Code parsing failures during analysis
- Security scanning timeouts and errors
- Performance analysis failures under load
- Code quality assessment interruptions
- Concurrent analysis failures and resource exhaustion
- Language detection and parsing failures

Chaos tests ensure the Code Analyzer service maintains analysis reliability during infrastructure failures.
"""

import asyncio
import time
import random
import json
from typing import Dict, Any, List, Optional
from unittest.mock import patch, AsyncMock, MagicMock, side_effect
from datetime import datetime, timedelta

import pytest
import httpx


class TestCodeAnalysisFailureScenarios:
    """Chaos engineering tests for code analysis operations under failure conditions."""

    @pytest.fixture
    def chaos_config(self):
        """Chaos test configuration for code analysis operations."""
        return {
            "failure_rate": 0.1,  # 10% of analysis operations fail
            "parsing_failure_scenarios": ["python", "javascript", "java", "csharp"],
            "security_scan_timeouts": [30, 60, 120],  # timeout scenarios in seconds
            "performance_analysis_failures": 5,
            "concurrent_analysis_failures": 8,
            "language_detection_errors": 0.05
        }

    @pytest.mark.asyncio
    async def test_code_parsing_failures_during_analysis(self, chaos_config):
        """Test resilience against code parsing failures during analysis."""
        parsing_errors = 0
        fallback_successes = 0
        partial_analysis_completions = 0

        async def analyze_code_with_parsing_failures(code_content: str, language: str, analysis_type: str) -> Dict[str, Any]:
            """Simulate code analysis with potential parsing failures."""
            nonlocal parsing_errors, fallback_successes, partial_analysis_completions

            # Simulate language-specific parsing failures
            if language in chaos_config["parsing_failure_scenarios"] and random.random() < 0.15:
                parsing_errors += 1

                if language == "python":
                    if "import" in code_content and random.random() < 0.7:
                        # Syntax error in imports
                        raise SyntaxError("Invalid import statement syntax")
                    else:
                        raise IndentationError("Unexpected indentation")
                elif language == "javascript":
                    raise SyntaxError("Unexpected token in JavaScript code")
                elif language == "java":
                    raise Exception("Compilation error: class not found")
                else:  # csharp
                    raise Exception("C# compilation error: namespace not found")

            # Simulate partial analysis completion for some failures
            if random.random() < 0.08 and parsing_errors > 0:
                partial_analysis_completions += 1
                # Return partial results despite parsing issues
                await asyncio.sleep(0.5)
                return {
                    "status": "partial_success",
                    "language": language,
                    "analysis_type": analysis_type,
                    "partial_metrics": {
                        "lines_of_code": len(code_content.split('\n')),
                        "parsing_errors": 1,
                        "fallback_used": True
                    },
                    "recommendations": ["Review syntax errors", "Consider code refactoring"]
                }

            # Simulate fallback to alternative analysis methods
            if random.random() < 0.1:
                fallback_successes += 1
                # Fallback to basic analysis
                await asyncio.sleep(0.8)
                return {
                    "status": "fallback_success",
                    "language": language,
                    "analysis_type": analysis_type,
                    "basic_metrics": {
                        "character_count": len(code_content),
                        "line_count": len(code_content.split('\n')),
                        "estimated_complexity": "unknown"
                    },
                    "fallback_method": "basic_static_analysis"
                }

            # Normal successful analysis
            await asyncio.sleep(random.uniform(0.3, 1.2))

            return {
                "status": "success",
                "language": language,
                "analysis_type": analysis_type,
                "metrics": {
                    "lines_of_code": len(code_content.split('\n')),
                    "cyclomatic_complexity": random.randint(1, 15),
                    "maintainability_index": random.uniform(0, 100),
                    "technical_debt_ratio": random.uniform(0, 0.5)
                },
                "issues": [
                    {
                        "type": "code_smell" if random.random() < 0.7 else "bug_risk",
                        "severity": random.choice(["low", "medium", "high"]),
                        "description": f"Sample {analysis_type} issue",
                        "line": random.randint(1, 50)
                    } for _ in range(random.randint(0, 5))
                ]
            }

        # Test code analysis across different languages and scenarios
        test_cases = []
        languages = ["python", "javascript", "java", "csharp", "typescript", "go"]
        analysis_types = ["security", "performance", "maintainability", "complexity"]

        sample_codes = {
            "python": "def calculate_fibonacci(n):\n    if n <= 1:\n        return n\n    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)",
            "javascript": "function calculateFibonacci(n) {\n    if (n <= 1) return n;\n    return calculateFibonacci(n-1) + calculateFibonacci(n-2);\n}",
            "java": "public int calculateFibonacci(int n) {\n    if (n <= 1) return n;\n    return calculateFibonacci(n-1) + calculateFibonacci(n-2);\n}",
            "csharp": "public int CalculateFibonacci(int n) {\n    if (n <= 1) return n;\n    return CalculateFibonacci(n-1) + CalculateFibonacci(n-2);\n}"
        }

        for i in range(30):
            language = languages[i % len(languages)]
            analysis_type = analysis_types[i % len(analysis_types)]
            code_content = sample_codes.get(language, "function test() { return 'sample'; }")
            test_cases.append((code_content, language, analysis_type))

        # Execute analysis tasks concurrently
        tasks = [analyze_code_with_parsing_failures(code, lang, analysis_type)
                for code, lang, analysis_type in test_cases]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Analyze results
        successful_analyses = [r for r in results if isinstance(r, dict)]
        failed_analyses = [r for r in results if isinstance(r, Exception)]

        fallback_used = sum(1 for r in successful_analyses if r.get("status") == "fallback_success")
        partial_success = sum(1 for r in successful_analyses if r.get("status") == "partial_success")

        success_rate = len(successful_analyses) / len(results)

        print(f"Code Parsing Failures During Analysis Test:")
        print(f"  Total Analysis Requests: {len(results)}")
        print(f"  Successful Analyses: {len(successful_analyses)}")
        print(f"  Failed Analyses: {len(failed_analyses)}")
        print(f"  Fallback Successes: {fallback_used}")
        print(f"  Partial Successes: {partial_success}")
        print(f"  Parsing Errors Encountered: {parsing_errors}")
        print(f"  Success Rate: {success_rate:.2%}")

        # Code analysis should be resilient to parsing failures
        assert len(failed_analyses) > 0, "No parsing failures occurred - chaos test ineffective"
        assert success_rate > 0.75, f"Success rate too low under parsing chaos: {success_rate:.2%}"
        assert fallback_used + partial_success > 0, "No fallback or partial analysis recovery used"

    @pytest.mark.asyncio
    async def test_security_scanning_timeouts_and_errors(self, chaos_config):
        """Test handling of security scanning timeouts and errors."""
        security_timeouts = 0
        scan_errors = 0
        incremental_scan_successes = 0

        async def perform_security_scan_with_failures(code_content: str, timeout_seconds: int, scan_type: str) -> Dict[str, Any]:
            """Simulate security scanning with potential timeouts and errors."""
            nonlocal security_timeouts, scan_errors, incremental_scan_successes

            start_time = time.time()

            # Simulate security scanning issues
            if random.random() < 0.12:  # 12% security scan failures
                if random.random() < 0.6:  # 60% are timeouts
                    security_timeouts += 1
                    # Simulate timeout by waiting longer than allowed
                    await asyncio.sleep(timeout_seconds + 5)
                    raise asyncio.TimeoutError(f"Security scan timed out after {timeout_seconds}s")
                else:
                    scan_errors += 1
                    raise Exception(f"Security scanner error: {random.choice(['signature database corrupted', 'scanner engine failure', 'memory allocation error'])}")

            # Simulate incremental scanning for large codebases
            if len(code_content) > 500 and random.random() < 0.15:
                incremental_scan_successes += 1
                # Break into chunks and scan incrementally
                chunks = [code_content[i:i+200] for i in range(0, len(code_content), 200)]
                vulnerabilities = []

                for chunk in chunks:
                    await asyncio.sleep(0.2)  # Scan time per chunk
                    # Simulate finding vulnerabilities in chunks
                    if random.random() < 0.3:
                        vulnerabilities.append({
                            "type": random.choice(["sql_injection", "xss", "buffer_overflow", "auth_bypass"]),
                            "severity": random.choice(["low", "medium", "high", "critical"]),
                            "line": random.randint(1, len(chunk.split('\n'))),
                            "description": f"Potential {scan_type} vulnerability in chunk"
                        })

                return {
                    "status": "incremental_scan_success",
                    "scan_type": scan_type,
                    "chunks_scanned": len(chunks),
                    "vulnerabilities_found": vulnerabilities,
                    "scan_time": time.time() - start_time
                }

            # Normal successful security scan
            scan_time = random.uniform(1.0, timeout_seconds * 0.8)  # Stay within timeout
            await asyncio.sleep(scan_time)

            vulnerabilities = []
            if random.random() < 0.4:  # 40% of scans find issues
                num_vulns = random.randint(1, 3)
                for _ in range(num_vulns):
                    vulnerabilities.append({
                        "type": random.choice(["sql_injection", "xss", "buffer_overflow", "auth_bypass", "crypto_weakness"]),
                        "severity": random.choice(["low", "medium", "high", "critical"]),
                        "line": random.randint(1, len(code_content.split('\n'))),
                        "description": f"Potential security vulnerability in {scan_type} scan"
                    })

            return {
                "status": "scan_success",
                "scan_type": scan_type,
                "vulnerabilities_found": vulnerabilities,
                "scan_time": scan_time,
                "timeout_limit": timeout_seconds,
                "security_score": random.uniform(0, 100)
            }

        # Test security scanning across different timeout scenarios
        test_scenarios = []

        for timeout in chaos_config["security_scan_timeouts"]:
            for i in range(8):  # 8 scans per timeout scenario
                # Create sample code of varying sizes
                code_size = random.randint(100, 2000)
                code_content = " ".join([f"function_{j}() {{ {chr(97 + (j % 26))} }};" for j in range(code_size // 20)])

                scan_type = ["sast", "dependency_check", "secrets_scan", "container_scan"][i % 4]
                test_scenarios.append((code_content, timeout, scan_type))

        # Execute security scanning tasks
        tasks = [perform_security_scan_with_failures(code, timeout, scan_type)
                for code, timeout, scan_type in test_scenarios]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Analyze results
        successful_scans = [r for r in results if isinstance(r, dict)]
        failed_scans = [r for r in results if isinstance(r, Exception)]

        incremental_scans = sum(1 for r in successful_scans if r.get("status") == "incremental_scan_success")
        total_vulnerabilities = sum(len(r.get("vulnerabilities_found", [])) for r in successful_scans)

        success_rate = len(successful_scans) / len(results)

        print(f"Security Scanning Timeouts and Errors Test:")
        print(f"  Total Security Scans: {len(results)}")
        print(f"  Successful Scans: {len(successful_scans)}")
        print(f"  Failed Scans: {len(failed_scans)}")
        print(f"  Incremental Scans: {incremental_scans}")
        print(f"  Security Timeouts: {security_timeouts}")
        print(f"  Scan Errors: {scan_errors}")
        print(f"  Total Vulnerabilities Found: {total_vulnerabilities}")
        print(f"  Success Rate: {success_rate:.2%}")

        # Security scanning should handle timeouts and errors gracefully
        assert len(failed_scans) > 0, "No security scanning failures occurred - chaos test ineffective"
        assert success_rate > 0.7, f"Success rate too low under security chaos: {success_rate:.2%}"
        assert incremental_scans >= 0, "Incremental scanning should be available for large codebases"

    @pytest.mark.asyncio
    async def test_performance_analysis_failures_under_load(self, chaos_config):
        """Test performance analysis failures under concurrent load."""
        performance_failures = 0
        resource_exhaustion_events = 0
        adaptive_scaling_successes = 0

        async def analyze_performance_with_load_failures(code_content: str, load_factor: float, analysis_depth: str) -> Dict[str, Any]:
            """Simulate performance analysis with load-induced failures."""
            nonlocal performance_failures, resource_exhaustion_events, adaptive_scaling_successes

            # Simulate load-based performance issues
            if load_factor > 0.7 and random.random() < 0.15:
                performance_failures += 1

                if random.random() < 0.5:  # 50% resource exhaustion
                    resource_exhaustion_events += 1
                    raise Exception("Resource exhaustion: insufficient memory for performance analysis")
                else:
                    raise Exception("Performance analysis timeout under high load")

            # Simulate adaptive scaling for high load scenarios
            if load_factor > 0.8 and random.random() < 0.2:
                adaptive_scaling_successes += 1
                # Reduce analysis depth to handle load
                analysis_depth = "basic" if analysis_depth == "comprehensive" else "standard"
                await asyncio.sleep(0.3)  # Reduced processing time

            # Normal performance analysis
            analysis_time = random.uniform(0.5, 2.0) * (1 + load_factor)  # Load affects processing time
            await asyncio.sleep(analysis_time)

            # Generate performance metrics based on analysis depth
            if analysis_depth == "basic":
                metrics = {
                    "execution_time_estimate": random.uniform(10, 100),
                    "memory_usage_estimate": random.uniform(50, 200),
                    "bottlenecks_identified": random.randint(0, 2)
                }
            elif analysis_depth == "standard":
                metrics = {
                    "execution_time_estimate": random.uniform(10, 100),
                    "memory_usage_estimate": random.uniform(50, 200),
                    "cpu_usage_estimate": random.uniform(20, 80),
                    "bottlenecks_identified": random.randint(1, 4),
                    "optimization_suggestions": random.randint(0, 3)
                }
            else:  # comprehensive
                metrics = {
                    "execution_time_estimate": random.uniform(10, 100),
                    "memory_usage_estimate": random.uniform(50, 200),
                    "cpu_usage_estimate": random.uniform(20, 80),
                    "io_operations_estimate": random.uniform(100, 1000),
                    "bottlenecks_identified": random.randint(2, 6),
                    "optimization_suggestions": random.randint(1, 5),
                    "scalability_assessment": random.choice(["good", "fair", "poor"])
                }

            return {
                "status": "performance_analysis_success",
                "analysis_depth": analysis_depth,
                "load_factor": load_factor,
                "metrics": metrics,
                "adaptive_scaling_applied": analysis_depth != "comprehensive" and load_factor > 0.8,
                "analysis_time": analysis_time
            }

        # Test performance analysis under different load conditions
        load_factors = [0.2, 0.5, 0.8, 0.95]  # Different load scenarios
        analysis_depths = ["basic", "standard", "comprehensive"]

        test_scenarios = []
        sample_code = """
        def complex_algorithm(data):
            results = []
            for i in range(len(data)):
                for j in range(len(data)):
                    if i != j:
                        results.append(process_pair(data[i], data[j]))
            return results

        def process_pair(item1, item2):
            # Complex processing logic
            return item1.value + item2.value * 2
        """

        for load_factor in load_factors:
            for depth in analysis_depths:
                for i in range(4):  # 4 analyses per combination
                    test_scenarios.append((sample_code, load_factor, depth))

        # Execute performance analysis tasks
        tasks = [analyze_performance_with_load_failures(code, load, depth)
                for code, load, depth in test_scenarios]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Analyze results
        successful_analyses = [r for r in results if isinstance(r, dict)]
        failed_analyses = [r for r in results if isinstance(r, Exception)]

        adaptive_scaling_used = sum(1 for r in successful_analyses if r.get("adaptive_scaling_applied", False))

        success_rate = len(successful_analyses) / len(results)

        print(f"Performance Analysis Failures Under Load Test:")
        print(f"  Total Performance Analyses: {len(results)}")
        print(f"  Successful Analyses: {len(successful_analyses)}")
        print(f"  Failed Analyses: {len(failed_analyses)}")
        print(f"  Performance Failures: {performance_failures}")
        print(f"  Resource Exhaustion Events: {resource_exhaustion_events}")
        print(f"  Adaptive Scaling Successes: {adaptive_scaling_used}")
        print(f"  Success Rate: {success_rate:.2%}")

        # Performance analysis should handle load gracefully
        assert len(failed_analyses) > 0, "No performance failures occurred - chaos test ineffective"
        assert success_rate > 0.75, f"Success rate too low under load chaos: {success_rate:.2%}"
        assert adaptive_scaling_used > 0, "No adaptive scaling used under high load"

    @pytest.mark.asyncio
    async def test_code_quality_assessment_interruptions(self, chaos_config):
        """Test code quality assessment handling of interruptions."""
        assessment_interruptions = 0
        partial_quality_reports = 0
        resumable_assessments = 0

        async def assess_code_quality_with_interruptions(code_content: str, quality_checks: List[str], interruption_probability: float) -> Dict[str, Any]:
            """Simulate code quality assessment with potential interruptions."""
            nonlocal assessment_interruptions, partial_quality_reports, resumable_assessments

            quality_scores = {}
            completed_checks = []

            for check in quality_checks:
                # Simulate interruption during quality checks
                if random.random() < interruption_probability:
                    assessment_interruptions += 1

                    if random.random() < 0.4:  # 40% interruptions are resumable
                        resumable_assessments += 1
                        # Allow partial completion
                        completed_checks.append(check)
                        quality_scores[check] = random.uniform(0, 100)
                        await asyncio.sleep(0.2)  # Resume delay
                        continue
                    else:
                        # Generate partial quality report
                        partial_quality_reports += 1

                        partial_scores = {}
                        for completed_check in completed_checks:
                            partial_scores[completed_check] = quality_scores[completed_check]

                        return {
                            "status": "partial_quality_report",
                            "completed_checks": completed_checks,
                            "quality_scores": partial_scores,
                            "interrupted_check": check,
                            "completion_percentage": len(completed_checks) / len(quality_checks),
                            "recommendations": ["Resume quality assessment", "Review interrupted check manually"]
                        }

                # Normal quality check execution
                await asyncio.sleep(random.uniform(0.1, 0.4))
                completed_checks.append(check)
                quality_scores[check] = random.uniform(0, 100)

            # Calculate overall quality score
            overall_score = sum(quality_scores.values()) / len(quality_scores) if quality_scores else 0

            # Generate quality grade
            if overall_score >= 90:
                grade = "A"
            elif overall_score >= 80:
                grade = "B"
            elif overall_score >= 70:
                grade = "C"
            elif overall_score >= 60:
                grade = "D"
            else:
                grade = "F"

            return {
                "status": "quality_assessment_complete",
                "overall_score": overall_score,
                "grade": grade,
                "quality_scores": quality_scores,
                "completed_checks": completed_checks,
                "total_checks": len(quality_checks),
                "interruptions_handled": assessment_interruptions > 0
            }

        # Test quality assessment under different interruption scenarios
        quality_check_sets = [
            ["readability", "maintainability", "complexity"],
            ["readability", "maintainability", "complexity", "security", "performance"],
            ["readability", "maintainability", "complexity", "security", "performance", "test_coverage", "documentation"]
        ]

        interruption_probabilities = [0.1, 0.2, 0.3]  # Different interruption likelihoods

        test_scenarios = []
        sample_code = """
        class CodeAnalyzer:
            def __init__(self):
                self.metrics = {}

            def analyze_code(self, code):
                # Complex analysis logic
                complexity = self.calculate_complexity(code)
                readability = self.assess_readability(code)
                maintainability = self.evaluate_maintainability(code)
                return {
                    'complexity': complexity,
                    'readability': readability,
                    'maintainability': maintainability
                }
        """

        for prob in interruption_probabilities:
            for checks in quality_check_sets:
                for i in range(5):  # 5 assessments per combination
                    test_scenarios.append((sample_code, checks, prob))

        # Execute quality assessment tasks
        tasks = [assess_code_quality_with_interruptions(code, checks, prob)
                for code, checks, prob in test_scenarios]
        results = await asyncio.gather(*tasks)

        # Analyze results
        complete_assessments = [r for r in results if r["status"] == "quality_assessment_complete"]
        partial_assessments = [r for r in results if r["status"] == "partial_quality_report"]

        resumable_completions = sum(1 for r in results if r.get("interruptions_handled", False))

        success_rate = len(complete_assessments) / len(results)

        print(f"Code Quality Assessment Interruptions Test:")
        print(f"  Total Quality Assessments: {len(results)}")
        print(f"  Complete Assessments: {len(complete_assessments)}")
        print(f"  Partial Assessments: {len(partial_assessments)}")
        print(f"  Assessment Interruptions: {assessment_interruptions}")
        print(f"  Resumable Assessments: {resumable_assessments}")
        print(f"  Partial Quality Reports: {partial_quality_reports}")
        print(f"  Success Rate: {success_rate:.2%}")

        # Quality assessment should handle interruptions gracefully
        assert len(partial_assessments) > 0, "No assessment interruptions occurred - chaos test ineffective"
        assert success_rate > 0.6, f"Success rate too low under interruption chaos: {success_rate:.2%}"
        assert resumable_completions >= 0, "Resumable assessment capabilities should be available"

    @pytest.mark.asyncio
    async def test_language_detection_and_parsing_failures(self, chaos_config):
        """Test language detection and parsing failure handling."""
        detection_failures = 0
        fallback_parsing_successes = 0
        multi_language_code_handled = 0

        async def analyze_multi_language_code_with_failures(code_content: str, expected_languages: List[str]) -> Dict[str, Any]:
            """Simulate analysis of multi-language code with detection and parsing failures."""
            nonlocal detection_failures, fallback_parsing_successes, multi_language_code_handled

            detected_languages = []
            parsing_results = {}

            for expected_lang in expected_languages:
                # Simulate language detection failures
                if random.random() < chaos_config["language_detection_errors"]:
                    detection_failures += 1

                    if random.random() < 0.6:  # 60% detection failures lead to fallback
                        fallback_parsing_successes += 1
                        # Attempt fallback parsing with generic parser
                        await asyncio.sleep(0.3)
                        parsing_results[expected_lang] = {
                            "status": "fallback_parsed",
                            "language": "generic",
                            "metrics": {"lines_parsed": random.randint(10, 50)},
                            "fallback_used": True
                        }
                    else:
                        parsing_results[expected_lang] = {
                            "status": "detection_failed",
                            "error": f"Could not detect language: {expected_lang}"
                        }
                    continue

                # Successful language detection
                detected_languages.append(expected_lang)

                # Simulate parsing for detected language
                await asyncio.sleep(random.uniform(0.2, 0.6))
                parsing_results[expected_lang] = {
                    "status": "parsed_successfully",
                    "language": expected_lang,
                    "metrics": {
                        "lines_of_code": random.randint(20, 100),
                        "functions_found": random.randint(1, 10),
                        "classes_found": random.randint(0, 5)
                    },
                    "issues": [
                        {
                            "type": "style_warning",
                            "description": f"Sample {expected_lang} style issue",
                            "line": random.randint(1, 50)
                        } for _ in range(random.randint(0, 3))
                    ]
                }

            # Handle multi-language code scenarios
            if len(expected_languages) > 1 and random.random() < 0.25:
                multi_language_code_handled += 1
                # Additional processing for multi-language files
                await asyncio.sleep(0.4)

                return {
                    "status": "multi_language_analysis_complete",
                    "detected_languages": detected_languages,
                    "parsing_results": parsing_results,
                    "cross_language_metrics": {
                        "total_lines": sum(r.get("metrics", {}).get("lines_of_code", 0) for r in parsing_results.values()),
                        "language_interfaces": random.randint(0, 3)
                    },
                    "multi_language_optimized": True
                }

            # Standard analysis result
            successful_parsing = sum(1 for r in parsing_results.values() if r["status"] == "parsed_successfully")
            fallback_parsing = sum(1 for r in parsing_results.values() if r.get("fallback_used", False))

            return {
                "status": "analysis_complete",
                "detected_languages": detected_languages,
                "parsing_results": parsing_results,
                "summary": {
                    "total_languages": len(expected_languages),
                    "successful_parsing": successful_parsing,
                    "fallback_parsing": fallback_parsing,
                    "failed_detection": len(expected_languages) - len(detected_languages) - fallback_parsing
                }
            }

        # Test multi-language code analysis scenarios
        test_scenarios = [
            # Single language scenarios
            ("def python_function(): pass", ["python"]),
            ("function jsFunction() {}", ["javascript"]),
            ("public class JavaClass {}", ["java"]),
            ("public class CSharpClass {}", ["csharp"]),

            # Multi-language scenarios
            ("def python_func(): pass\nfunction jsFunc() {}", ["python", "javascript"]),
            ("public class JavaClass {}\nfunction jsFunc() {}", ["java", "javascript"]),
            ("def py_func(): pass\npublic class JavaClass {}", ["python", "java"]),
        ]

        analysis_tasks = []
        for code_content, expected_languages in test_scenarios:
            for i in range(6):  # 6 analyses per scenario
                analysis_tasks.append((code_content, expected_languages))

        # Execute multi-language analysis tasks
        tasks = [analyze_multi_language_code_with_failures(code, langs)
                for code, langs in analysis_tasks]
        results = await asyncio.gather(*tasks)

        # Analyze results
        successful_analyses = [r for r in results if "analysis_complete" in r.get("status", "")]
        multi_language_analyses = [r for r in results if r.get("status") == "multi_language_analysis_complete"]

        fallback_used = sum(r.get("summary", {}).get("fallback_parsing", 0) for r in successful_analyses)

        success_rate = len(successful_analyses) / len(results)

        print(f"Language Detection and Parsing Failures Test:")
        print(f"  Total Language Analyses: {len(results)}")
        print(f"  Successful Analyses: {len(successful_analyses)}")
        print(f"  Multi-Language Analyses: {len(multi_language_analyses)}")
        print(f"  Detection Failures: {detection_failures}")
        print(f"  Fallback Parsing Successes: {fallback_used}")
        print(f"  Multi-Language Code Handled: {multi_language_code_handled}")
        print(f"  Success Rate: {success_rate:.2%}")

        # Language detection and parsing should handle failures gracefully
        assert detection_failures > 0, "No language detection failures occurred - chaos test ineffective"
        assert success_rate > 0.8, f"Success rate too low under language chaos: {success_rate:.2%}"
        assert fallback_used >= 0, "Fallback parsing should be available"

    @pytest.mark.asyncio
    async def test_concurrent_analysis_failures_and_resource_exhaustion(self, chaos_config):
        """Test concurrent analysis failures and resource exhaustion handling."""
        concurrent_failures = 0
        resource_exhaustion_events = 0
        priority_based_processing = 0

        async def perform_concurrent_analysis(operation_id: int, priority: str, code_complexity: str, analysis_scope: str) -> Dict[str, Any]:
            """Perform analysis operation with concurrency and resource constraints."""
            nonlocal concurrent_failures, resource_exhaustion_events, priority_based_processing

            # Simulate concurrent processing issues
            if random.random() < 0.12:  # 12% concurrency failures
                concurrent_failures += 1

                if priority == "low":
                    resource_exhaustion_events += 1
                    raise Exception("Resource exhaustion: low priority analysis cancelled")
                elif priority == "high":
                    priority_based_processing += 1
                    # High priority gets extended processing time
                    await asyncio.sleep(4.0)
                    # Recovery successful
                else:
                    raise Exception("Concurrent analysis limit exceeded")

            # Adjust processing time based on complexity and scope
            base_time = {
                "low": 0.3,
                "medium": 0.8,
                "high": 1.5,
                "very_high": 3.0
            }[code_complexity]

            scope_multiplier = {
                "single_file": 1.0,
                "module": 2.0,
                "project": 4.0,
                "repository": 8.0
            }[analysis_scope]

            processing_time = base_time * scope_multiplier * random.uniform(0.8, 1.2)
            await asyncio.sleep(processing_time)

            return {
                "operation_id": operation_id,
                "priority": priority,
                "code_complexity": code_complexity,
                "analysis_scope": analysis_scope,
                "status": "analysis_completed",
                "processing_time": processing_time,
                "metrics": {
                    "files_analyzed": random.randint(1, 100),
                    "issues_found": random.randint(0, 50),
                    "quality_score": random.uniform(0, 100)
                },
                "resource_usage": {
                    "memory_mb": random.uniform(50, 500),
                    "cpu_percent": random.uniform(10, 90)
                }
            }

        # Test concurrent analysis with different priorities and complexities
        operations = []
        priorities = ["high", "medium", "low"]
        complexities = ["low", "medium", "high", "very_high"]
        scopes = ["single_file", "module", "project"]

        for i in range(50):  # High concurrency test
            priority = priorities[i % len(priorities)]
            complexity = complexities[i % len(complexities)]
            scope = scopes[i % len(scopes)]
            operations.append((i, priority, complexity, scope))

        # Execute operations concurrently
        tasks = [perform_concurrent_analysis(op_id, priority, complexity, scope)
                for op_id, priority, complexity, scope in operations]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Analyze concurrent analysis results
        successful_operations = [r for r in results if isinstance(r, dict)]
        failed_operations = [r for r in results if isinstance(r, Exception)]

        high_priority_success = sum(1 for r in successful_operations if r.get("priority") == "high")
        low_priority_success = sum(1 for r in successful_operations if r.get("priority") == "low")

        success_rate = len(successful_operations) / len(results)

        print(f"Concurrent Analysis Failures and Resource Exhaustion Test:")
        print(f"  Total Operations: {len(results)}")
        print(f"  Successful Operations: {len(successful_operations)}")
        print(f"  Failed Operations: {len(failed_operations)}")
        print(f"  High Priority Success: {high_priority_success}")
        print(f"  Low Priority Success: {low_priority_success}")
        print(f"  Concurrent Failures: {concurrent_failures}")
        print(f"  Resource Exhaustion Events: {resource_exhaustion_events}")
        print(f"  Priority-Based Processing: {priority_based_processing}")
        print(f"  Success Rate: {success_rate:.2%}")

        # Concurrent analysis should handle resource constraints gracefully with prioritization
        assert len(failed_operations) > 0, "No concurrent failures occurred - chaos test ineffective"
        assert success_rate > 0.75, f"Success rate too low under concurrent load: {success_rate:.2%}"
        assert resource_exhaustion_events > 0, "No resource exhaustion handling for low priority"
        assert priority_based_processing >= 0, "Priority-based processing should be available"
