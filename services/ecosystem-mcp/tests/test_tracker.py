"""
Test Execution Tracker

Tracks test fixes and progress during Phase 4.
"""
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class TestTracker:
    """Track test execution and fixes."""
    
    def __init__(self, output_dir: str = "test_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results = {
            "session_id": self.session_id,
            "start_time": datetime.now().isoformat(),
            "baseline": {},
            "fixes": [],
            "current": {},
            "history": []
        }
    
    def set_baseline(self, passed: int, failed: int, errors: int, total: int):
        """Set baseline test results."""
        self.results["baseline"] = {
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "total": total,
            "pass_rate": round(passed / total * 100, 2) if total > 0 else 0
        }
    
    def record_fix(self, test_name: str, category: str, description: str):
        """Record a test fix."""
        self.results["fixes"].append({
            "timestamp": datetime.now().isoformat(),
            "test_name": test_name,
            "category": category,
            "description": description
        })
    
    def update_current(self, passed: int, failed: int, errors: int, total: int):
        """Update current test results."""
        baseline_pass_rate = self.results["baseline"].get("pass_rate", 0)
        current_pass_rate = round(passed / total * 100, 2) if total > 0 else 0
        
        self.results["current"] = {
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "total": total,
            "pass_rate": current_pass_rate,
            "improvement": round(current_pass_rate - baseline_pass_rate, 2),
            "tests_fixed": passed - self.results["baseline"].get("passed", 0)
        }
        
        # Add to history
        self.results["history"].append({
            "timestamp": datetime.now().isoformat(),
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "pass_rate": current_pass_rate
        })
    
    def save(self):
        """Save results to file."""
        output_file = self.output_dir / f"test_tracker_{self.session_id}.json"
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        return output_file
    
    def print_summary(self):
        """Print current summary."""
        baseline = self.results["baseline"]
        current = self.results["current"]
        
        print("\n" + "="*80)
        print("TEST EXECUTION TRACKER - SUMMARY")
        print("="*80)
        
        if baseline:
            print(f"\n📊 BASELINE:")
            print(f"   Passed: {baseline['passed']}/{baseline['total']} ({baseline['pass_rate']}%)")
            print(f"   Failed: {baseline['failed']}")
            print(f"   Errors: {baseline['errors']}")
        
        if current:
            print(f"\n📈 CURRENT:")
            print(f"   Passed: {current['passed']}/{current['total']} ({current['pass_rate']}%)")
            print(f"   Failed: {current['failed']}")
            print(f"   Errors: {current['errors']}")
            print(f"\n✨ IMPROVEMENT:")
            print(f"   Tests Fixed: +{current['tests_fixed']}")
            print(f"   Pass Rate: +{current['improvement']}%")
        
        if self.results["fixes"]:
            print(f"\n🔧 FIXES APPLIED: {len(self.results['fixes'])}")
            
            # Group by category
            categories = {}
            for fix in self.results["fixes"]:
                cat = fix["category"]
                categories[cat] = categories.get(cat, 0) + 1
            
            for cat, count in categories.items():
                print(f"   {cat}: {count} fixes")
        
        print("\n" + "="*80 + "\n")


def create_tracker() -> TestTracker:
    """Create a new test tracker."""
    return TestTracker()


if __name__ == "__main__":
    # Example usage
    tracker = create_tracker()
    tracker.set_baseline(passed=113, failed=60, errors=2, total=175)
    tracker.print_summary()

