#!/usr/bin/env python3
"""
Logging Validation Script

Validates that a service implements standardized logging according to
the Standardized Logging Strategy.

Usage:
    python validate_logging.py <service-name>

Example:
    python validate_logging.py doc-store
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple


def check_structured_logger_import(service_path: Path) -> Tuple[bool, List[str]]:
    """Check if service imports StructuredLogger"""
    issues = []
    found = False
    
    # Check infrastructure/logging directory
    logging_dir = service_path / "infrastructure" / "logging"
    if not logging_dir.exists():
        issues.append("Missing infrastructure/logging directory")
        return False, issues
    
    logger_file = logging_dir / "logger.py"
    if not logger_file.exists():
        issues.append("Missing infrastructure/logging/logger.py")
        return False, issues
    
    content = logger_file.read_text()
    if "StructuredLogger" in content:
        found = True
    else:
        issues.append("StructuredLogger not imported in logger.py")
    
    return found, issues


def check_log_collector_client(service_path: Path) -> Tuple[bool, List[str]]:
    """Check if LogCollectorClient is available"""
    issues = []
    
    # Check common/clients/log_collector_client.py
    common_path = service_path.parent.parent / "common" / "clients" / "log_collector_client.py"
    
    if not common_path.exists():
        issues.append("LogCollectorClient not found in common/clients/")
        return False, issues
    
    return True, []


def check_logging_in_code(service_path: Path) -> Tuple[Dict[str, int], List[str]]:
    """Check for logging statements in code"""
    issues = []
    log_counts = {
        "info": 0,
        "error": 0,
        "warning": 0,
        "debug": 0,
        "critical": 0,
    }
    
    # Search all Python files for logging
    for py_file in service_path.rglob("*.py"):
        if "tests/" in str(py_file) or "__pycache__" in str(py_file):
            continue
        
        content = py_file.read_text()
        
        # Count logging statements
        log_counts["info"] += len(re.findall(r'logger\.info\(', content))
        log_counts["error"] += len(re.findall(r'logger\.error\(', content))
        log_counts["warning"] += len(re.findall(r'logger\.warning\(', content))
        log_counts["debug"] += len(re.findall(r'logger\.debug\(', content))
        log_counts["critical"] += len(re.findall(r'logger\.critical\(', content))
    
    total_logs = sum(log_counts.values())
    
    if total_logs == 0:
        issues.append("No logging statements found in service code")
    
    if log_counts["info"] == 0:
        issues.append("No INFO level logs found (core features should be logged)")
    
    if log_counts["error"] == 0:
        issues.append("No ERROR level logs found (errors should be logged)")
    
    return log_counts, issues


def check_correlation_id_tracking(service_path: Path) -> Tuple[bool, List[str]]:
    """Check if correlation IDs are tracked"""
    issues = []
    found = False
    
    # Check for correlation_id_var usage
    for py_file in service_path.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        
        content = py_file.read_text()
        
        if "correlation_id" in content.lower():
            found = True
            break
    
    if not found:
        issues.append("No correlation ID tracking found")
    
    return found, issues


def check_structured_log_format(service_path: Path) -> Tuple[bool, List[str]]:
    """Check if logs use structured format"""
    issues = []
    found_structured = False
    
    for py_file in service_path.rglob("*.py"):
        if "tests/" in str(py_file) or "__pycache__" in str(py_file):
            continue
        
        content = py_file.read_text()
        
        # Look for structured logging patterns
        if "operation=" in content and "metadata=" in content:
            found_structured = True
            break
    
    if not found_structured:
        issues.append("No structured logging format found (operation, metadata fields)")
    
    return found_structured, issues


def check_middleware_logging(service_path: Path) -> Tuple[bool, List[str]]:
    """Check if logging middleware is present"""
    issues = []
    
    middleware_dir = service_path / "presentation" / "api" / "middleware"
    if not middleware_dir.exists():
        issues.append("Missing middleware directory")
        return False, issues
    
    logging_middleware = middleware_dir / "logging_middleware.py"
    if not logging_middleware.exists():
        issues.append("Missing logging_middleware.py for HTTP request logging")
        return False, issues
    
    content = logging_middleware.read_text()
    
    required_patterns = [
        "correlation_id",
        "duration_ms",
        "http_request",
    ]
    
    for pattern in required_patterns:
        if pattern not in content.lower():
            issues.append(f"Logging middleware missing '{pattern}'")
    
    return True, issues


def check_no_sensitive_data(service_path: Path) -> Tuple[bool, List[str]]:
    """Check for potential sensitive data in logs"""
    issues = []
    sensitive_patterns = [
        r'password\s*=',
        r'api_key\s*=',
        r'secret\s*=',
        r'token\s*=',
        r'credential\s*=',
    ]
    
    violations = []
    
    for py_file in service_path.rglob("*.py"):
        if "tests/" in str(py_file) or "__pycache__" in str(py_file):
            continue
        
        content = py_file.read_text()
        
        # Check if file has logging
        if "logger." not in content:
            continue
        
        for pattern in sensitive_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                violations.append(f"{py_file.name}: potential sensitive data logged ({pattern})")
    
    if violations:
        issues.extend(violations)
        return False, issues
    
    return True, []


def check_performance_metrics(service_path: Path) -> Tuple[bool, List[str]]:
    """Check if performance metrics are logged"""
    issues = []
    found = False
    
    for py_file in service_path.rglob("*.py"):
        if "tests/" in str(py_file) or "__pycache__" in str(py_file):
            continue
        
        content = py_file.read_text()
        
        if "duration_ms" in content:
            found = True
            break
    
    if not found:
        issues.append("No performance metrics (duration_ms) found in logs")
    
    return found, issues


def calculate_score(results: Dict) -> int:
    """Calculate logging compliance score (0-100)"""
    checks = [
        results["structured_logger"],
        results["log_collector_client"],
        results["logging_statements"]["total"] > 0,
        results["correlation_id_tracking"],
        results["structured_format"],
        results["middleware_logging"],
        results["no_sensitive_data"],
        results["performance_metrics"],
    ]
    
    score = (sum(checks) / len(checks)) * 100
    return int(score)


def generate_report(service_name: str, results: Dict) -> Dict:
    """Generate validation report"""
    score = calculate_score(results)
    
    # Collect all issues
    all_issues = []
    for check, data in results.items():
        if isinstance(data, dict) and "issues" in data:
            all_issues.extend(data["issues"])
    
    status = "PASS" if score >= 80 else "FAIL"
    
    return {
        "service": service_name,
        "score": score,
        "status": status,
        "checks": {
            "structured_logger": {
                "passed": results["structured_logger"]["passed"],
                "issues": results["structured_logger"]["issues"],
            },
            "log_collector_client": {
                "passed": results["log_collector_client"]["passed"],
                "issues": results["log_collector_client"]["issues"],
            },
            "logging_statements": {
                "counts": results["logging_statements"]["counts"],
                "total": results["logging_statements"]["total"],
                "issues": results["logging_statements"]["issues"],
            },
            "correlation_id_tracking": {
                "passed": results["correlation_id_tracking"]["passed"],
                "issues": results["correlation_id_tracking"]["issues"],
            },
            "structured_format": {
                "passed": results["structured_format"]["passed"],
                "issues": results["structured_format"]["issues"],
            },
            "middleware_logging": {
                "passed": results["middleware_logging"]["passed"],
                "issues": results["middleware_logging"]["issues"],
            },
            "no_sensitive_data": {
                "passed": results["no_sensitive_data"]["passed"],
                "issues": results["no_sensitive_data"]["issues"],
            },
            "performance_metrics": {
                "passed": results["performance_metrics"]["passed"],
                "issues": results["performance_metrics"]["issues"],
            },
        },
        "recommendations": generate_recommendations(results, score),
    }


def generate_recommendations(results: Dict, score: int) -> List[str]:
    """Generate recommendations based on results"""
    recommendations = []
    
    if not results["structured_logger"]["passed"]:
        recommendations.append(
            "Implement StructuredLogger following the Standardized Logging Strategy"
        )
    
    if not results["log_collector_client"]["passed"]:
        recommendations.append(
            "Set up LogCollectorClient in common/clients/"
        )
    
    if results["logging_statements"]["total"] < 10:
        recommendations.append(
            "Add more logging statements to cover all core features"
        )
    
    if not results["correlation_id_tracking"]["passed"]:
        recommendations.append(
            "Implement correlation ID tracking for request tracing"
        )
    
    if not results["structured_format"]["passed"]:
        recommendations.append(
            "Use structured logging format with operation and metadata fields"
        )
    
    if not results["middleware_logging"]["passed"]:
        recommendations.append(
            "Add logging middleware to track all HTTP requests"
        )
    
    if not results["no_sensitive_data"]["passed"]:
        recommendations.append(
            "Review and remove sensitive data from logs"
        )
    
    if not results["performance_metrics"]["passed"]:
        recommendations.append(
            "Add duration_ms metrics to track operation performance"
        )
    
    if score < 80:
        recommendations.append(
            "Review the Standardized Logging Strategy documentation"
        )
    
    return recommendations


def main():
    """Main entry point"""
    if len(sys.argv) != 2:
        print("Usage: python validate_logging.py <service-name>")
        print("Example: python validate_logging.py doc-store")
        sys.exit(1)
    
    service_name = sys.argv[1]
    
    # Determine service path
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent.parent
    service_path = repo_root / "services" / service_name
    
    if not service_path.exists():
        print(f"✗ Service not found: {service_path}")
        sys.exit(1)
    
    print(f"\n🔍 Validating logging for '{service_name}'")
    print(f"   Path: {service_path}\n")
    
    # Run all checks
    results = {}
    
    print("Running checks...")
    
    # Check 1: StructuredLogger
    passed, issues = check_structured_logger_import(service_path)
    results["structured_logger"] = {"passed": passed, "issues": issues}
    print(f"  {'✓' if passed else '✗'} StructuredLogger import")
    
    # Check 2: LogCollectorClient
    passed, issues = check_log_collector_client(service_path)
    results["log_collector_client"] = {"passed": passed, "issues": issues}
    print(f"  {'✓' if passed else '✗'} LogCollectorClient availability")
    
    # Check 3: Logging statements
    log_counts, issues = check_logging_in_code(service_path)
    total_logs = sum(log_counts.values())
    results["logging_statements"] = {
        "counts": log_counts,
        "total": total_logs,
        "issues": issues,
    }
    print(f"  {'✓' if total_logs > 0 else '✗'} Logging statements ({total_logs} found)")
    
    # Check 4: Correlation ID tracking
    passed, issues = check_correlation_id_tracking(service_path)
    results["correlation_id_tracking"] = {"passed": passed, "issues": issues}
    print(f"  {'✓' if passed else '✗'} Correlation ID tracking")
    
    # Check 5: Structured format
    passed, issues = check_structured_log_format(service_path)
    results["structured_format"] = {"passed": passed, "issues": issues}
    print(f"  {'✓' if passed else '✗'} Structured log format")
    
    # Check 6: Middleware logging
    passed, issues = check_middleware_logging(service_path)
    results["middleware_logging"] = {"passed": passed, "issues": issues}
    print(f"  {'✓' if passed else '✗'} Middleware logging")
    
    # Check 7: No sensitive data
    passed, issues = check_no_sensitive_data(service_path)
    results["no_sensitive_data"] = {"passed": passed, "issues": issues}
    print(f"  {'✓' if passed else '✗'} No sensitive data in logs")
    
    # Check 8: Performance metrics
    passed, issues = check_performance_metrics(service_path)
    results["performance_metrics"] = {"passed": passed, "issues": issues}
    print(f"  {'✓' if passed else '✗'} Performance metrics")
    
    # Generate report
    report = generate_report(service_name, results)
    
    # Save report
    report_path = repo_root / "reports" / f"{service_name}_logging_validation.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print(f"\n📊 Logging Validation Results")
    print(f"   Score: {report['score']}/100")
    print(f"   Status: {report['status']}")
    print(f"   Report: {report_path}")
    
    if report['recommendations']:
        print(f"\n💡 Recommendations:")
        for rec in report['recommendations']:
            print(f"   - {rec}")
    
    print(f"\n📚 Reference:")
    print(f"   - Standardized Logging Strategy: docs/refactoring/STANDARDIZED_LOGGING_STRATEGY.md")
    
    # Exit with error if failed
    if report['status'] == "FAIL":
        sys.exit(1)


if __name__ == "__main__":
    main()

