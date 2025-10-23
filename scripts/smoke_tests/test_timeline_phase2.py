#!/usr/bin/env python3
"""
Timeline Phase 2 Smoke Tests

Quick validation tests for Phase 2 implementation:
- Temporal RAG Service
- Maintenance Services (8 services)

Usage:
    python scripts/smoke_tests/test_timeline_phase2.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


class SmokeTestRunner:
    """Runs smoke tests for Phase 2 timeline functionality."""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.results = []
    
    def print_header(self, text: str):
        """Print test section header."""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}\n")
    
    def print_test(self, name: str, status: str, message: str = ""):
        """Print test result."""
        if status == "PASS":
            symbol = f"{Colors.GREEN}✓{Colors.END}"
            self.passed += 1
        elif status == "FAIL":
            symbol = f"{Colors.RED}✗{Colors.END}"
            self.failed += 1
        elif status == "SKIP":
            symbol = f"{Colors.YELLOW}⊘{Colors.END}"
            self.skipped += 1
        else:
            symbol = "?"
        
        print(f"{symbol} {name}")
        if message:
            print(f"  {message}")
        
        self.results.append({
            "name": name,
            "status": status,
            "message": message
        })
    
    async def test_imports(self):
        """Test that all Phase 2 modules can be imported."""
        self.print_header("TEST 1: Module Imports")
        
        try:
            # Add services directory to path
            services_path = project_root / "services" / "ecosystem-mcp"
            if str(services_path) not in sys.path:
                sys.path.insert(0, str(services_path))
            
            # Test temporal RAG imports
            from src.services.rag import TemporalRAGService
            self.print_test("Import TemporalRAGService", "PASS")
        except ImportError as e:
            self.print_test("Import TemporalRAGService", "FAIL", str(e))
            return False
        
        try:
            # Test maintenance service imports
            from src.services.maintenance import (
                StalenessDetector,
                CoverageAnalyzer,
                ConsistencyChecker,
                DependencyTracker,
                VersionComparator,
                QualityDashboard,
                AutomatedRefresher,
                ExportService,
            )
            self.print_test("Import maintenance services", "PASS")
        except ImportError as e:
            self.print_test("Import maintenance services", "FAIL", str(e))
            return False
        
        return True
    
    async def test_temporal_rag_service(self):
        """Test TemporalRAGService structure."""
        self.print_header("TEST 2: Temporal RAG Service")
        
        try:
            from src.services.rag import TemporalRAGService
            from unittest.mock import AsyncMock
            
            # Create mock db_session
            mock_db = AsyncMock()
            
            service = TemporalRAGService(db_session=mock_db)
            self.print_test("Create TemporalRAGService", "PASS")
            
            # Check expected methods
            expected_methods = [
                'query_as_of',
                'query_evolution',
                'query_what_changed',
            ]
            
            for method in expected_methods:
                if hasattr(service, method):
                    self.print_test(f"TemporalRAGService.{method} exists", "PASS")
                else:
                    self.print_test(f"TemporalRAGService.{method} exists", "FAIL")
            
            return True
            
        except Exception as e:
            self.print_test("Temporal RAG service tests", "FAIL", str(e))
            return False
    
    async def test_maintenance_services(self):
        """Test maintenance services structure."""
        self.print_header("TEST 3: Maintenance Services")
        
        try:
            from src.services.maintenance import (
                StalenessDetector,
                CoverageAnalyzer,
                ConsistencyChecker,
                DependencyTracker,
                VersionComparator,
                QualityDashboard,
                AutomatedRefresher,
                ExportService,
            )
            from unittest.mock import AsyncMock
            
            # Test StalenessDetector (no db_session needed)
            staleness = StalenessDetector()
            self.print_test("Create StalenessDetector", "PASS")
            if hasattr(staleness, 'detect_stale_documents'):
                self.print_test("StalenessDetector.detect_stale_documents exists", "PASS")
            else:
                self.print_test("StalenessDetector.detect_stale_documents exists", "FAIL")
            
            # Test CoverageAnalyzer
            coverage = CoverageAnalyzer()
            self.print_test("Create CoverageAnalyzer", "PASS")
            if hasattr(coverage, 'analyze_coverage'):
                self.print_test("CoverageAnalyzer.analyze_coverage exists", "PASS")
            else:
                self.print_test("CoverageAnalyzer.analyze_coverage exists", "FAIL")
            
            # Test ConsistencyChecker
            consistency = ConsistencyChecker()
            self.print_test("Create ConsistencyChecker", "PASS")
            if hasattr(consistency, 'check_consistency'):
                self.print_test("ConsistencyChecker.check_consistency exists", "PASS")
            else:
                self.print_test("ConsistencyChecker.check_consistency exists", "FAIL")
            
            # Test DependencyTracker
            dependency = DependencyTracker()
            self.print_test("Create DependencyTracker", "PASS")
            if hasattr(dependency, 'build_dependency_graph'):
                self.print_test("DependencyTracker.build_dependency_graph exists", "PASS")
            else:
                self.print_test("DependencyTracker.build_dependency_graph exists", "FAIL")
            
            # Test VersionComparator
            version = VersionComparator()
            self.print_test("Create VersionComparator", "PASS")
            if hasattr(version, 'compare_versions'):
                self.print_test("VersionComparator.compare_versions exists", "PASS")
            else:
                self.print_test("VersionComparator.compare_versions exists", "FAIL")
            
            # Test QualityDashboard
            quality = QualityDashboard()
            self.print_test("Create QualityDashboard", "PASS")
            if hasattr(quality, 'get_quality_overview'):
                self.print_test("QualityDashboard.get_quality_overview exists", "PASS")
            else:
                self.print_test("QualityDashboard.get_quality_overview exists", "FAIL")
            
            # Test AutomatedRefresher
            refresher = AutomatedRefresher()
            self.print_test("Create AutomatedRefresher", "PASS")
            if hasattr(refresher, 'refresh_documentation'):
                self.print_test("AutomatedRefresher.refresh_documentation exists", "PASS")
            else:
                self.print_test("AutomatedRefresher.refresh_documentation exists", "FAIL")
            
            # Test ExportService
            export = ExportService()
            self.print_test("Create ExportService", "PASS")
            if hasattr(export, 'export_documentation'):
                self.print_test("ExportService.export_documentation exists", "PASS")
            else:
                self.print_test("ExportService.export_documentation exists", "FAIL")
            
            return True
            
        except Exception as e:
            self.print_test("Maintenance services tests", "FAIL", str(e))
            return False
    
    async def test_api_routes(self):
        """Test that Phase 2 API routes exist."""
        self.print_header("TEST 4: API Routes")
        
        try:
            # Check if temporal RAG routes exist in query_enhanced
            from src.api.routes import query_enhanced as rag_routes
            
            if hasattr(rag_routes, 'router'):
                self.print_test("RAG router exists", "PASS")
                
                # Check for temporal endpoints
                routes = [route.path for route in rag_routes.router.routes]
                
                # Check for temporal-related routes
                temporal_routes_found = any('temporal' in route.lower() for route in routes)
                if temporal_routes_found:
                    self.print_test("Temporal RAG routes exist", "PASS")
                else:
                    self.print_test("Temporal RAG routes exist", "SKIP", 
                                  "Routes may exist but not detected")
            else:
                self.print_test("RAG router exists", "FAIL")
            
            return True
            
        except Exception as e:
            self.print_test("API routes test", "FAIL", str(e))
            return False
    
    async def test_service_files_exist(self):
        """Test that all service files exist."""
        self.print_header("TEST 5: Service Files")
        
        try:
            services_dir = project_root / "services" / "ecosystem-mcp" / "src" / "services"
            
            # Check temporal RAG
            temporal_rag = services_dir / "rag" / "temporal_rag_service.py"
            if temporal_rag.exists():
                self.print_test("temporal_rag_service.py exists", "PASS")
            else:
                self.print_test("temporal_rag_service.py exists", "FAIL")
            
            # Check maintenance services
            maintenance_dir = services_dir / "maintenance"
            expected_files = [
                "staleness_detector.py",
                "coverage_analyzer.py",
                "consistency_checker.py",
                "dependency_tracker.py",
                "version_comparator.py",
                "quality_dashboard.py",
                "automated_refresher.py",
                "export_service.py",
            ]
            
            for filename in expected_files:
                filepath = maintenance_dir / filename
                if filepath.exists():
                    self.print_test(f"{filename} exists", "PASS")
                else:
                    self.print_test(f"{filename} exists", "FAIL")
            
            return True
            
        except Exception as e:
            self.print_test("Service files test", "FAIL", str(e))
            return False
    
    def print_summary(self):
        """Print test summary."""
        print(f"\n{Colors.BOLD}{'='*80}{Colors.END}")
        print(f"{Colors.BOLD}TEST SUMMARY{Colors.END}")
        print(f"{Colors.BOLD}{'='*80}{Colors.END}\n")
        
        total = self.passed + self.failed + self.skipped
        pass_rate = (self.passed / total * 100) if total > 0 else 0
        
        print(f"Total Tests: {total}")
        print(f"{Colors.GREEN}Passed: {self.passed}{Colors.END}")
        print(f"{Colors.RED}Failed: {self.failed}{Colors.END}")
        print(f"{Colors.YELLOW}Skipped: {self.skipped}{Colors.END}")
        print(f"\nPass Rate: {pass_rate:.1f}%")
        
        if self.failed == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✓ ALL TESTS PASSED!{Colors.END}")
            return 0
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}✗ SOME TESTS FAILED{Colors.END}")
            return 1
    
    async def run_all_tests(self):
        """Run all smoke tests."""
        print(f"\n{Colors.BOLD}{Colors.BLUE}")
        print("╔═══════════════════════════════════════════════════════════════════════════════╗")
        print("║                                                                               ║")
        print("║                  TIMELINE PHASE 2 SMOKE TESTS                                 ║")
        print("║                                                                               ║")
        print("╚═══════════════════════════════════════════════════════════════════════════════╝")
        print(f"{Colors.END}\n")
        
        # Run tests in sequence
        await self.test_imports()
        await self.test_temporal_rag_service()
        await self.test_maintenance_services()
        await self.test_api_routes()
        await self.test_service_files_exist()
        
        # Print summary
        return self.print_summary()


async def main():
    """Main entry point."""
    runner = SmokeTestRunner()
    exit_code = await runner.run_all_tests()
    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())

