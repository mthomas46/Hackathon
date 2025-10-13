#!/usr/bin/env python3
"""
Dashboard validation script.

Run this to validate the dashboard configuration and connectivity.
"""

import os
import sys
from pathlib import Path

# Add the dashboard directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from utils.config_validator import ConfigValidator


def main():
    """Run dashboard validation."""
    print("╔═══════════════════════════════════════════════════════════════════════════╗")
    print("║                                                                           ║")
    print("║              🔍 DASHBOARD VALIDATION & HEALTH CHECK 🔍                    ║")
    print("║                                                                           ║")
    print("╚═══════════════════════════════════════════════════════════════════════════╝")
    print()
    
    # Get API base URL from environment
    api_base_url = os.getenv("API_BASE_URL", "http://host.docker.internal:8000")
    print(f"🔗 API Base URL: {api_base_url}")
    print()
    
    # Create validator
    validator = ConfigValidator()
    
    # Run all validations
    print("🔄 Running validations...")
    print()
    
    results, all_passed = validator.run_all_validations(api_base_url)
    
    # Display results
    print("═" * 79)
    print("VALIDATION RESULTS")
    print("═" * 79)
    print()
    
    passed_count = sum(1 for r in results if r.passed)
    failed_count = len(results) - passed_count
    
    for result in results:
        status_icon = "✅" if result.passed else "❌"
        print(f"{status_icon} {result.check_name}")
        print(f"   {result.message}")
        
        if result.details:
            if "missing" in result.details and result.details["missing"]:
                for item in result.details["missing"]:
                    print(f"      ❌ Missing: {item}")
            
            if "present" in result.details and result.details["present"]:
                for item in result.details["present"]:
                    print(f"      ✅ Present: {item}")
            
            if "available" in result.details and result.details["available"]:
                print(f"      ✅ Available: {len(result.details['available'])} items")
            
            if "unavailable" in result.details and result.details["unavailable"]:
                for item in result.details["unavailable"]:
                    print(f"      ❌ Unavailable: {item}")
            
            if "healthy" in result.details and result.details["healthy"]:
                for item in result.details["healthy"]:
                    print(f"      🟢 Healthy: {item}")
            
            if "unhealthy" in result.details and result.details["unhealthy"]:
                for item in result.details["unhealthy"]:
                    print(f"      🔴 Unhealthy: {item}")
        
        print()
    
    # Summary
    print("═" * 79)
    print("SUMMARY")
    print("═" * 79)
    print()
    print(f"Total Checks: {len(results)}")
    print(f"✅ Passed: {passed_count}")
    print(f"❌ Failed: {failed_count}")
    print()
    
    if all_passed:
        print("🎉 ALL VALIDATIONS PASSED! Dashboard is ready to use.")
        print()
        print(f"🌐 Access dashboard at: http://localhost:8501")
        print()
        return 0
    else:
        print("⚠️ SOME VALIDATIONS FAILED. Please review and fix issues above.")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())

