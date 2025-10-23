#!/usr/bin/env python3
"""
Timeline Phase 1 Smoke Tests

Quick validation tests for Phase 1 timeline implementation.
Tests core functionality without requiring full test infrastructure.

Usage:
    python scripts/smoke_tests/test_timeline_phase1.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
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
    """Runs smoke tests for timeline functionality."""
    
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
        """Test that all timeline modules can be imported."""
        self.print_header("TEST 1: Module Imports")
        
        try:
            # Add services directory to path
            services_path = project_root / "services" / "ecosystem-mcp"
            if str(services_path) not in sys.path:
                sys.path.insert(0, str(services_path))
            
            from src.services.timeline import (
                TemporalConfidenceCalculator,
                TimelineManager,
                PeriodGenerator,
                DocumentPlacer,
                GapAnalyzer,
                DriftDetector,
                ReportGenerator,
                DocumentConsolidator,
            )
            self.print_test("Import timeline services", "PASS")
        except ImportError as e:
            self.print_test("Import timeline services", "FAIL", str(e))
            return False
        
        try:
            from src.models.timeline import (
                Timeline,
                TimelineCreate,
                TimePeriod,
                TemporalConfidence,
            )
            self.print_test("Import timeline models", "PASS")
        except ImportError as e:
            self.print_test("Import timeline models", "FAIL", str(e))
            return False
        
        try:
            from src.api.routes.timeline import router
            self.print_test("Import timeline API routes", "PASS")
        except ImportError as e:
            self.print_test("Import timeline API routes", "FAIL", str(e))
            return False
        
        return True
    
    async def test_confidence_calculator(self):
        """Test TemporalConfidenceCalculator."""
        self.print_header("TEST 2: Confidence Calculator")
        
        try:
            from src.services.timeline import TemporalConfidenceCalculator
            from src.models.timeline import TemporalConfidence
            from unittest.mock import AsyncMock, MagicMock
            
            # Create mock db_session
            mock_db = AsyncMock()
            mock_db.execute = AsyncMock()
            mock_db.scalars = AsyncMock()
            
            calculator = TemporalConfidenceCalculator(db_session=mock_db)
            self.print_test("Create TemporalConfidenceCalculator", "PASS")
            
            # Check that calculator has expected methods
            if hasattr(calculator, 'calculate_confidence'):
                self.print_test("TemporalConfidenceCalculator.calculate_confidence exists", "PASS")
            else:
                self.print_test("TemporalConfidenceCalculator.calculate_confidence exists", "FAIL")
            
            if hasattr(calculator, 'db'):
                self.print_test("TemporalConfidenceCalculator has db_session", "PASS")
            else:
                self.print_test("TemporalConfidenceCalculator has db_session", "FAIL")
            
            # Note: Full functional tests require database connection
            self.print_test("TemporalConfidenceCalculator structure validated", "PASS")
            
            return True
            
        except Exception as e:
            self.print_test("Confidence calculator tests", "FAIL", str(e))
            return False
    
    async def test_period_generator(self):
        """Test PeriodGenerator."""
        self.print_header("TEST 3: Period Generator")
        
        try:
            from src.services.timeline import PeriodGenerator
            from src.models.timeline import PeriodStrategy
            from unittest.mock import AsyncMock
            
            # Create mock db_session
            mock_db = AsyncMock()
            mock_db.execute = AsyncMock()
            mock_db.scalars = AsyncMock()
            
            generator = PeriodGenerator(db_session=mock_db)
            self.print_test("Create PeriodGenerator", "PASS")
            
            # Check that generator has expected methods
            if hasattr(generator, 'generate_periods'):
                self.print_test("PeriodGenerator.generate_periods exists", "PASS")
            else:
                self.print_test("PeriodGenerator.generate_periods exists", "FAIL")
            
            if hasattr(generator, 'db'):
                self.print_test("PeriodGenerator has db_session", "PASS")
            else:
                self.print_test("PeriodGenerator has db_session", "FAIL")
            
            # Check PeriodStrategy enum values
            if hasattr(PeriodStrategy, 'MONTHLY'):
                self.print_test("PeriodStrategy.MONTHLY exists", "PASS")
            else:
                self.print_test("PeriodStrategy.MONTHLY exists", "FAIL")
            
            if hasattr(PeriodStrategy, 'QUARTERLY'):
                self.print_test("PeriodStrategy.QUARTERLY exists", "PASS")
            else:
                self.print_test("PeriodStrategy.QUARTERLY exists", "FAIL")
            
            # Note: Full functional tests require database connection
            self.print_test("PeriodGenerator structure validated", "PASS")
            
            return True
            
        except Exception as e:
            self.print_test("Period generator tests", "FAIL", str(e))
            return False
    
    async def test_api_routes(self):
        """Test that API routes are properly configured."""
        self.print_header("TEST 4: API Routes")
        
        try:
            from src.api.routes.timeline import router
            
            # Check router has expected endpoints
            routes = [route.path for route in router.routes]
            
            expected_routes = [
                "/api/v1/timelines",
                "/api/v1/timelines/{timeline_id}",
                "/api/v1/timelines/{timeline_id}/periods",
                "/api/v1/timelines/{timeline_id}/documents",
            ]
            
            for expected in expected_routes:
                # Check if route exists (may have prefix variations)
                found = any(expected in route for route in routes)
                if found:
                    self.print_test(f"Route exists: {expected}", "PASS")
                else:
                    self.print_test(f"Route exists: {expected}", "FAIL",
                                  f"Route not found in {routes}")
            
            return True
            
        except Exception as e:
            self.print_test("API routes test", "FAIL", str(e))
            return False
    
    async def test_database_models(self):
        """Test that database models are properly defined."""
        self.print_header("TEST 5: Database Models")
        
        try:
            from src.storage.db_models import (
                TimelineModel,
                TimePeriodModel,
                DocumentPlacementModel,
            )
            
            self.print_test("Import TimelineModel", "PASS")
            self.print_test("Import TimePeriodModel", "PASS")
            self.print_test("Import DocumentPlacementModel", "PASS")
            
            # Check TimelineModel has expected fields
            expected_fields = [
                "id", "name", "service_name", "start_date", "end_date",
                "confidence_level", "confidence_metadata", "created_at"
            ]
            
            for field in expected_fields:
                if hasattr(TimelineModel, field):
                    self.print_test(f"TimelineModel.{field} exists", "PASS")
                else:
                    self.print_test(f"TimelineModel.{field} exists", "FAIL",
                                  f"Field {field} not found")
            
            return True
            
        except Exception as e:
            self.print_test("Database models test", "FAIL", str(e))
            return False
    
    async def test_migration_exists(self):
        """Test that timeline migration exists."""
        self.print_header("TEST 6: Database Migration")
        
        try:
            migration_path = project_root / "services" / "ecosystem-mcp" / "src" / "storage" / "migrations" / "009_add_timeline_tables.py"
            
            if migration_path.exists():
                self.print_test("Migration 009_add_timeline_tables.py exists", "PASS")
                
                # Check migration has upgrade and downgrade functions
                with open(migration_path, 'r') as f:
                    content = f.read()
                    
                if "async def upgrade" in content:
                    self.print_test("Migration has upgrade() function", "PASS")
                else:
                    self.print_test("Migration has upgrade() function", "FAIL")
                
                if "async def downgrade" in content:
                    self.print_test("Migration has downgrade() function", "PASS")
                else:
                    self.print_test("Migration has downgrade() function", "FAIL")
                
                return True
            else:
                self.print_test("Migration 009_add_timeline_tables.py exists", "FAIL",
                              f"File not found at {migration_path}")
                return False
            
        except Exception as e:
            self.print_test("Migration test", "FAIL", str(e))
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
        print("║                  TIMELINE PHASE 1 SMOKE TESTS                                 ║")
        print("║                                                                               ║")
        print("╚═══════════════════════════════════════════════════════════════════════════════╝")
        print(f"{Colors.END}\n")
        
        # Run tests in sequence
        await self.test_imports()
        await self.test_confidence_calculator()
        await self.test_period_generator()
        await self.test_api_routes()
        await self.test_database_models()
        await self.test_migration_exists()
        
        # Print summary
        return self.print_summary()


async def main():
    """Main entry point."""
    runner = SmokeTestRunner()
    exit_code = await runner.run_all_tests()
    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())

