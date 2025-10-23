#!/usr/bin/env python3
"""
Automated Test Fix Script

Systematically fixes common test issues and tracks progress.
"""
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from tests.test_tracker import TestTracker


class TestFixer:
    """Automated test fixer."""
    
    def __init__(self, test_dir: Path):
        self.test_dir = test_dir
        self.tracker = TestTracker()
        self.fixes_applied = 0
    
    def run_tests(self) -> Tuple[int, int, int, int]:
        """Run tests and return results."""
        print("🧪 Running tests...")
        result = subprocess.run(
            ["pytest", "tests/functional/", "tests/smoke/", "-v", "--no-cov", "--tb=no", "-q"],
            cwd=self.test_dir,
            capture_output=True,
            text=True
        )
        
        # Parse output
        output = result.stdout + result.stderr
        
        # Extract counts
        passed = failed = errors = 0
        
        # Look for summary line: "X passed, Y failed, Z errors"
        match = re.search(r'(\d+) passed', output)
        if match:
            passed = int(match.group(1))
        
        match = re.search(r'(\d+) failed', output)
        if match:
            failed = int(match.group(1))
        
        match = re.search(r'(\d+) error', output)
        if match:
            errors = int(match.group(1))
        
        total = passed + failed + errors
        
        return passed, failed, errors, total
    
    def fix_attribute_errors(self) -> int:
        """Fix doc.content -> doc.normalized_content."""
        print("\n🔧 Fixing attribute errors (doc.content -> doc.normalized_content)...")
        
        fixes = 0
        test_files = list(self.test_dir.glob("tests/**/*.py"))
        
        for file_path in test_files:
            content = file_path.read_text()
            original = content
            
            # Replace doc.content with doc.normalized_content
            # But be careful not to replace in comments or strings
            content = re.sub(
                r'\bdoc\.content\b(?!\s*=)',  # Don't replace assignments
                'doc.normalized_content',
                content
            )
            
            # Also fix document.content
            content = re.sub(
                r'\bdocument\.content\b(?!\s*=)',
                'document.normalized_content',
                content
            )
            
            if content != original:
                file_path.write_text(content)
                fixes += 1
                self.tracker.record_fix(
                    file_path.name,
                    "Attribute Error",
                    "Changed doc.content to doc.normalized_content"
                )
                print(f"   ✅ Fixed {file_path.name}")
        
        return fixes
    
    def fix_api_parameters(self) -> int:
        """Fix common API parameter mismatches."""
        print("\n🔧 Fixing API parameter mismatches...")
        
        fixes = 0
        test_files = list(self.test_dir.glob("tests/**/*.py"))
        
        replacements = [
            # DriftDetector
            (r'\.detect_drift\([^)]*file_path=', '.detect_drift(service_name='),
            
            # CitationFormatter
            (r'\.format_citations\([^)]*format=', '.format_citations(citation_format='),
            
            # VersionComparator
            (r'\.compare_versions\([^)]*version1=', '.compare_versions(doc_id_1='),
            (r'\.compare_versions\([^)]*version2=', '.compare_versions(doc_id_2='),
            
            # AutomatedRefresher
            (r'\.schedule_refresh\([^)]*interval_days=', '.schedule_refresh(interval_hours='),
            
            # DynamicTimelineConstructor
            (r'\.construct_timeline\([^)]*topic=', '.construct_timeline(query='),
        ]
        
        for file_path in test_files:
            content = file_path.read_text()
            original = content
            
            for pattern, replacement in replacements:
                content = re.sub(pattern, replacement, content)
            
            if content != original:
                file_path.write_text(content)
                fixes += 1
                self.tracker.record_fix(
                    file_path.name,
                    "API Parameter",
                    "Fixed parameter names to match actual API"
                )
                print(f"   ✅ Fixed {file_path.name}")
        
        return fixes
    
    def fix_method_names(self) -> int:
        """Fix method name mismatches."""
        print("\n🔧 Fixing method name mismatches...")
        
        fixes = 0
        test_files = list(self.test_dir.glob("tests/**/*.py"))
        
        replacements = [
            # DependencyTracker
            (r'\.track_dependencies\(', '.analyze_dependencies('),
            (r'\.analyze_impact\(', '.get_impact_analysis('),
            
            # QualityDashboard
            (r'\.generate_dashboard\(', '.get_quality_metrics('),
            
            # AutomatedRefresher
            (r'\.trigger_refresh\(', '.refresh_stale_documents('),
        ]
        
        for file_path in test_files:
            content = file_path.read_text()
            original = content
            
            for pattern, replacement in replacements:
                content = re.sub(pattern, replacement, content)
            
            if content != original:
                file_path.write_text(content)
                fixes += 1
                self.tracker.record_fix(
                    file_path.name,
                    "Method Name",
                    "Fixed method names to match actual implementation"
                )
                print(f"   ✅ Fixed {file_path.name}")
        
        return fixes
    
    def run(self):
        """Run the automated fix process."""
        print("\n" + "="*80)
        print("AUTOMATED TEST FIXER - PHASE 4")
        print("="*80)
        
        # Get baseline
        print("\n📊 Establishing baseline...")
        passed, failed, errors, total = self.run_tests()
        self.tracker.set_baseline(passed, failed, errors, total)
        self.tracker.print_summary()
        
        # Apply fixes
        print("\n🔧 Applying automated fixes...")
        
        fixes = 0
        fixes += self.fix_attribute_errors()
        fixes += self.fix_api_parameters()
        fixes += self.fix_method_names()
        
        print(f"\n✨ Applied {fixes} automated fixes")
        
        # Run tests again
        print("\n📊 Running tests after fixes...")
        passed, failed, errors, total = self.run_tests()
        self.tracker.update_current(passed, failed, errors, total)
        
        # Save and print summary
        output_file = self.tracker.save()
        self.tracker.print_summary()
        
        print(f"📁 Results saved to: {output_file}")
        print("\n" + "="*80 + "\n")


def main():
    """Main entry point."""
    test_dir = Path(__file__).parent.parent
    fixer = TestFixer(test_dir)
    fixer.run()


if __name__ == "__main__":
    main()

