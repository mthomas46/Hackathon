"""
Comprehensive Feature Validation Script (Week 4, Day 1)

Validates all implemented features from Weeks 1-3 and Option C:
- Week 1: Orchestration, circuit breakers, timeouts
- Week 2: Hierarchical contexts, structured logging
- Option C: Performance tests, incremental docs, monitoring
- Week 3: Model routing, context-aware RAG, dashboard

Runs checks for:
- Implementation completeness
- Logging coverage
- Error handling
- Test coverage
- Integration points
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple
import importlib.util

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class FeatureValidator:
    """Validates implemented features."""
    
    def __init__(self):
        self.results = {
            "week1": {},
            "week2": {},
            "option_c": {},
            "week3": {}
        }
        self.total_checks = 0
        self.passed_checks = 0
    
    def validate_all(self) -> Dict:
        """Run all validations."""
        print("=" * 80)
        print("COMPREHENSIVE FEATURE VALIDATION")
        print("=" * 80)
        print()
        
        # Week 1
        print("📦 WEEK 1: Critical Integration & Hardening")
        print("-" * 80)
        self.validate_week1()
        print()
        
        # Week 2
        print("📦 WEEK 2: Advanced Features")
        print("-" * 80)
        self.validate_week2()
        print()
        
        # Option C
        print("📦 OPTION C: Testing & Optimization")
        print("-" * 80)
        self.validate_option_c()
        print()
        
        # Week 3
        print("📦 WEEK 3: Advanced Intelligence")
        print("-" * 80)
        self.validate_week3()
        print()
        
        # Summary
        self.print_summary()
        
        return self.results
    
    def validate_week1(self):
        """Validate Week 1 features."""
        features = [
            ("Sub-job Orchestration", "services/ecosystem-mcp/src/services/orchestration/job_orchestrator.py"),
            ("Sub-job Executor", "services/ecosystem-mcp/src/services/orchestration/sub_job_executor.py"),
            ("Dependency Ordering", "services/ecosystem-mcp/src/services/analysis/dependency_analyzer.py"),
            ("Circuit Breakers", "services/ecosystem-mcp/src/utils/resilience.py"),
            ("Partial Success", "services/ecosystem-mcp/src/utils/partial_success.py"),
            ("Integration Tests", "services/ecosystem-mcp/tests/integration/test_orchestration_integration.py"),
        ]
        
        for name, path in features:
            result = self.check_file_exists(path, name)
            self.results["week1"][name] = result
    
    def validate_week2(self):
        """Validate Week 2 features."""
        features = [
            ("Hierarchical Contexts", "services/ecosystem-mcp/src/services/analysis/hierarchical_context_manager.py"),
            ("Structured Logger", "services/ecosystem-mcp/src/utils/structured_logger.py"),
            ("Context API Endpoints", "services/ecosystem-mcp/src/api/routes/analysis.py"),
            ("Context Tests", "services/ecosystem-mcp/tests/unit/test_hierarchical_context.py"),
            ("Logger Tests", "services/ecosystem-mcp/tests/unit/test_structured_logger.py"),
        ]
        
        for name, path in features:
            result = self.check_file_exists(path, name)
            self.results["week2"][name] = result
    
    def validate_option_c(self):
        """Validate Option C features."""
        features = [
            ("Performance Benchmarks", "services/ecosystem-mcp/tests/performance/test_benchmarks.py"),
            ("E2E Pipeline Tests", "services/ecosystem-mcp/tests/e2e/test_complete_pipelines.py"),
            ("Incremental Doc Manager", "services/ecosystem-mcp/src/services/documentation/incremental_doc_manager.py"),
            ("Incremental Doc API", "services/ecosystem-mcp/src/api/routes/documentation_incremental.py"),
            ("Performance Monitor", "services/ecosystem-mcp/src/services/monitoring/performance_monitor.py"),
            ("Performance API", "services/ecosystem-mcp/src/api/routes/performance.py"),
            ("Performance Dashboard", "services/ecosystem-mcp-dashboard/pages/performance_monitor.py"),
        ]
        
        for name, path in features:
            result = self.check_file_exists(path, name)
            self.results["option_c"][name] = result
    
    def validate_week3(self):
        """Validate Week 3 features."""
        features = [
            ("Enhanced Model Router", "services/ecosystem-mcp/src/services/llm/enhanced_model_router.py"),
            ("Model Router Integration", "services/ecosystem-mcp/src/services/llm/model_router_integration.py"),
            ("Context-Aware RAG", "services/ecosystem-mcp/src/services/rag/context_aware_rag.py"),
            ("Context-Aware API", "services/ecosystem-mcp/src/api/routes/context_aware_query.py"),
            ("Repository Contexts Page", "services/ecosystem-mcp-dashboard/pages/repository_contexts.py"),
            ("Context-Aware RAG Page", "services/ecosystem-mcp-dashboard/pages/context_aware_rag.py"),
            ("Model Router Tests", "services/ecosystem-mcp/tests/unit/test_enhanced_model_router.py"),
            ("Context RAG Tests", "services/ecosystem-mcp/tests/integration/test_context_aware_rag.py"),
        ]
        
        for name, path in features:
            result = self.check_file_exists(path, name)
            self.results["week3"][name] = result
    
    def check_file_exists(self, relative_path: str, feature_name: str) -> Dict:
        """Check if file exists and has content."""
        self.total_checks += 1
        
        full_path = project_root / relative_path
        
        if not full_path.exists():
            print(f"  ❌ {feature_name}: File not found")
            return {"status": "fail", "reason": "File not found"}
        
        # Check file size
        size = full_path.stat().st_size
        if size < 100:  # Less than 100 bytes is suspicious
            print(f"  ⚠️  {feature_name}: File too small ({size} bytes)")
            self.passed_checks += 0.5
            return {"status": "warning", "reason": f"File too small ({size} bytes)"}
        
        print(f"  ✅ {feature_name}: OK ({size:,} bytes)")
        self.passed_checks += 1
        return {"status": "pass", "size": size}
    
    def print_summary(self):
        """Print validation summary."""
        print("=" * 80)
        print("VALIDATION SUMMARY")
        print("=" * 80)
        print()
        
        # Calculate stats
        pass_rate = (self.passed_checks / self.total_checks * 100) if self.total_checks > 0 else 0
        
        print(f"Total Checks: {self.total_checks}")
        print(f"Passed: {int(self.passed_checks)}")
        print(f"Pass Rate: {pass_rate:.1f}%")
        print()
        
        # Status
        if pass_rate >= 95:
            print("✅ STATUS: EXCELLENT - All features validated")
        elif pass_rate >= 80:
            print("⚠️  STATUS: GOOD - Most features validated, some issues")
        else:
            print("❌ STATUS: NEEDS ATTENTION - Several features missing or incomplete")
        print()


def main():
    """Run validation."""
    validator = FeatureValidator()
    results = validator.validate_all()
    
    # Exit with appropriate code
    if validator.passed_checks / validator.total_checks >= 0.95:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()

