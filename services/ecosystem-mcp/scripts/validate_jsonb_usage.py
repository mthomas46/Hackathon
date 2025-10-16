#!/usr/bin/env python3
"""
JSONB Field Validation Script

Validates that all JSONB field modifications are followed by flag_modified() calls.
Can be run manually or integrated into CI/CD pipeline.
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.jsonb_validator import validate_codebase, print_validation_report, save_validation_report


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate JSONB field usage in Python code"
    )
    parser.add_argument(
        "--root",
        type=Path,
        help="Root directory to validate (default: src/)",
        default=None
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file for report (default: stdout)",
        default=None
    )
    parser.add_argument(
        "--exclude",
        nargs="+",
        help="Patterns to exclude",
        default=None
    )
    parser.add_argument(
        "--fail-on-error",
        action="store_true",
        help="Exit with error code if violations found"
    )
    parser.add_argument(
        "--fail-on-warning",
        action="store_true",
        help="Exit with error code if warnings found"
    )
    
    args = parser.parse_args()
    
    # Run validation
    print("🔍 Validating JSONB field usage...")
    print()
    
    results = validate_codebase(
        root_dir=args.root,
        exclude_patterns=args.exclude
    )
    
    # Print or save report
    if args.output:
        save_validation_report(results, args.output)
        print(f"✅ Report saved to {args.output}")
    else:
        print_validation_report(results)
    
    # Determine exit code
    exit_code = 0
    
    if results['errors'] > 0:
        if args.fail_on_error:
            exit_code = 1
            print("❌ Validation failed: Errors found")
    
    if results['warnings'] > 0:
        if args.fail_on_warning:
            exit_code = 1
            print("⚠️  Validation failed: Warnings found")
    
    if exit_code == 0 and results['total_violations'] == 0:
        print("✅ All JSONB fields are properly handled with flag_modified()!")
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

