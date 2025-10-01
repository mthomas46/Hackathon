#!/usr/bin/env python3
"""
LEGACY: Service Configuration Validation Script

⚠️  DEPRECATED: This script has been superseded by the new unified configuration
management system. Use the following instead:

For configuration audit:
  python scripts/hardening/unified_config_manager.py audit

For validation with JSON output:
  python scripts/hardening/unified_config_manager.py audit --format json --output validation_report.json

Migration guide: See CONFIGURATION_STANDARDIZATION_COMPLETE.md
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.hardening.configuration_management_system import UnifiedConfigurationManager

def main():
    """Run configuration validation"""
    manager = UnifiedConfigurationManager()

    print("🔍 Validating Service Configurations...")
    print("=" * 50)

    # Generate report
    report = manager.generate_configuration_report()

    # Print summary
    summary = report['validation_summary']
    print(f"Services with configs: {summary['services_with_configs']}")
    print(f"Services with ports: {summary['services_with_ports']}")
    print(f"Configuration conflicts: {summary['total_conflicts']}")
    print(f"Critical conflicts: {summary['critical_conflicts']}")
    print(f"High priority conflicts: {summary['high_priority_conflicts']}")

    # Print conflicts
    if report['configuration_conflicts']:
        print("\n🚨 Configuration Conflicts:")
        for conflict in report['configuration_conflicts']:
            severity_icon = "🔴" if conflict['severity'] == "critical" else "🟠" if conflict['severity'] == "high" else "🟡"
            print(f"  {severity_icon} {conflict['service']}: {conflict['description']}")
            if conflict['suggestion']:
                print(f"    💡 {conflict['suggestion']}")

    # Print recommendations
    if report['recommendations']:
        print("\n💡 Recommendations:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"  {i}. {rec}")

    # Exit with error code if critical conflicts
    if summary['critical_conflicts'] > 0:
        print("\n❌ Critical configuration issues found!")
        return 1

    print("\n✅ Configuration validation complete!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
