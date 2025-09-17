"""Service Import Validation Script

Tests that all service modules can be imported correctly after the DDD refactor.
This validates the module structure and import dependencies without requiring
the full service to be running.
"""

import sys
import importlib
import traceback
from typing import Dict, List, Any
from pathlib import Path


class ServiceImportValidator:
    """Validates service imports and module structure."""

    def __init__(self, service_path: str):
        """Initialize validator."""
        self.service_path = Path(service_path)
        self.results = {}

    def validate_all_modules(self) -> Dict[str, Any]:
        """Validate imports for all service modules."""
        print("🔧 Starting service import validation...")

        # Define modules to test
        modules_to_test = self._get_modules_to_test()

        successful_imports = 0
        failed_imports = 0
        total_modules = len(modules_to_test)

        import_results = []

        for module_path in modules_to_test:
            result = self._test_module_import(module_path)
            import_results.append(result)

            if result["success"]:
                successful_imports += 1
                print(f"✅ {module_path}")
            else:
                failed_imports += 1
                print(f"❌ {module_path} - {result['error']}")

        # Calculate summary
        success_rate = (successful_imports / total_modules) * 100 if total_modules > 0 else 0

        summary = {
            "total_modules": total_modules,
            "successful_imports": successful_imports,
            "failed_imports": failed_imports,
            "success_rate": round(success_rate, 2),
            "import_results": import_results,
            "failed_modules": [
                r for r in import_results if not r["success"]
            ]
        }

        print("\n📊 IMPORT VALIDATION SUMMARY:")
        print(f"✅ Successful: {successful_imports}/{total_modules} ({success_rate:.1f}%)")
        print(f"❌ Failed: {failed_imports}/{total_modules}")

        if summary["failed_modules"]:
            print("\n❌ Failed Modules:")
            for failed in summary["failed_modules"]:
                print(f"   {failed['module']} - {failed['error']}")

        return summary

    def _get_modules_to_test(self) -> List[str]:
        """Get list of modules to test."""
        return [
            # Domain layer
            "services.analysis-service.domain.entities.document",
            "services.analysis-service.domain.entities.analysis",
            "services.analysis-service.domain.entities.finding",
            "services.analysis-service.domain.services.analysis_service",
            "services.analysis-service.domain.services.document_service",
            "services.analysis-service.domain.services.finding_service",
            "services.analysis-service.domain.factories.document_factory",
            "services.analysis-service.domain.factories.analysis_factory",
            "services.analysis-service.domain.factories.finding_factory",

            # Application layer
            "services.analysis-service.application.use_cases.perform_analysis_use_case",
            "services.analysis-service.application.dto.request_dtos",
            "services.analysis-service.application.dto.response_dtos",
            "services.analysis-service.application.services.application_service",

            # Infrastructure layer
            "services.analysis-service.infrastructure.repositories.sqlite_document_repository",
            "services.analysis-service.infrastructure.repositories.sqlite_analysis_repository",
            "services.analysis-service.infrastructure.repositories.sqlite_finding_repository",
            "services.analysis-service.infrastructure.config.infrastructure_config",

            # Presentation layer
            "services.analysis-service.presentation.controllers.analysis_controller",
            "services.analysis-service.presentation.controllers.workflow_controller",
            "services.analysis-service.presentation.controllers.distributed_controller",
            "services.analysis-service.presentation.models.analysis",
            "services.analysis-service.presentation.models.base",

            # Core modules
            "services.analysis-service.modules.semantic_analyzer",
            "services.analysis-service.modules.sentiment_analyzer",
            "services.analysis-service.modules.cross_repository_analyzer",
            "services.analysis-service.modules.maintenance_forecaster",
            "services.analysis-service.modules.quality_degradation_detector",
            "services.analysis-service.modules.risk_assessor",
            "services.analysis-service.modules.automated_remediator",
            "services.analysis-service.modules.workflow_trigger",
            "services.analysis-service.modules.distributed_processor",
            "services.analysis-service.modules.change_impact_analyzer",

            # Main service
            "services.analysis-service.main_new"
        ]

    def _test_module_import(self, module_path: str) -> Dict[str, Any]:
        """Test importing a specific module."""
        try:
            # Remove any cached modules
            if module_path in sys.modules:
                del sys.modules[module_path]

            # Attempt import
            module = importlib.import_module(module_path)

            return {
                "module": module_path,
                "success": True,
                "error": None,
                "has_classes": hasattr(module, '__all__') or len(dir(module)) > 0
            }

        except ImportError as e:
            return {
                "module": module_path,
                "success": False,
                "error": f"ImportError: {str(e)}",
                "traceback": traceback.format_exc()
            }
        except Exception as e:
            return {
                "module": module_path,
                "success": False,
                "error": f"Error: {str(e)}",
                "traceback": traceback.format_exc()
            }


def validate_service_structure(service_path: str) -> Dict[str, Any]:
    """Validate the overall service structure."""
    print("🏗️  Validating service directory structure...")

    service_dir = Path(service_path)
    structure_issues = []

    # Check required directories exist
    required_dirs = [
        "domain",
        "application",
        "infrastructure",
        "presentation",
        "modules",
        "tests"
    ]

    for dir_name in required_dirs:
        dir_path = service_dir / dir_name
        if not dir_path.exists():
            structure_issues.append(f"Missing directory: {dir_name}")
        elif not dir_path.is_dir():
            structure_issues.append(f"Not a directory: {dir_name}")

    # Check DDD structure
    ddd_dirs = [
        "domain/entities",
        "domain/services",
        "domain/factories",
        "domain/repositories",
        "application/use_cases",
        "application/dto",
        "application/services",
        "infrastructure/repositories",
        "infrastructure/config",
        "presentation/controllers",
        "presentation/models"
    ]

    for ddd_path in ddd_dirs:
        full_path = service_dir / ddd_path
        if not full_path.exists():
            structure_issues.append(f"Missing DDD directory: {ddd_path}")

    # Check for __init__.py files
    init_files_missing = []
    for dir_path in service_dir.rglob("**/"):
        if dir_path.is_dir() and not (dir_path / "__init__.py").exists():
            rel_path = dir_path.relative_to(service_dir)
            init_files_missing.append(str(rel_path))

    if init_files_missing:
        structure_issues.append(f"Missing __init__.py files in: {init_files_missing[:5]}...")

    return {
        "structure_valid": len(structure_issues) == 0,
        "issues": structure_issues,
        "missing_init_files": init_files_missing
    }


def main():
    """Main validation function."""
    import argparse

    parser = argparse.ArgumentParser(description="Service Import Validation")
    parser.add_argument("--service", default="services/analysis-service",
                       help="Path to service directory")
    parser.add_argument("--output", default="import_validation_results.json",
                       help="Output file for results")

    args = parser.parse_args()

    print("🔧 Service Import & Structure Validation")
    print("=" * 50)

    # Validate service structure
    structure_result = validate_service_structure(args.service)

    if structure_result["structure_valid"]:
        print("✅ Service structure is valid")
    else:
        print("❌ Service structure issues found:")
        for issue in structure_result["issues"]:
            print(f"   {issue}")

    print()

    # Validate module imports
    validator = ServiceImportValidator(args.service)
    import_result = validator.validate_all_modules()

    # Combine results
    final_result = {
        "structure_validation": structure_result,
        "import_validation": import_result,
        "overall_success": structure_result["structure_valid"] and import_result["success_rate"] >= 95,
        "recommendations": []
    }

    # Generate recommendations
    if not structure_result["structure_valid"]:
        final_result["recommendations"].append("Fix service directory structure issues")
    if import_result["success_rate"] < 95:
        final_result["recommendations"].append("Fix module import issues before deployment")

    # Save results
    import json
    with open(args.output, 'w') as f:
        json.dump(final_result, f, indent=2, default=str)

    print(f"\n💾 Results saved to: {args.output}")

    # Final assessment
    if final_result["overall_success"]:
        print("🎉 EXCELLENT: Service structure and imports are solid!")
        return 0
    else:
        print("⚠️  ISSUES FOUND: Review and fix before deployment")
        return 1


if __name__ == "__main__":
    sys.exit(main())
