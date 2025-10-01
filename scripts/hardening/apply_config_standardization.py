#!/usr/bin/env python3
"""
LEGACY: Automated Configuration Standardization Script

⚠️  DEPRECATED: This script has been superseded by the new unified configuration
management system. Use the following instead:

For standardization:
  python scripts/hardening/unified_config_manager.py standardize --apply

For dry-run preview:
  python scripts/hardening/unified_config_manager.py standardize --dry-run

Migration guide: See CONFIGURATION_STANDARDIZATION_COMPLETE.md
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.hardening.configuration_management_system import UnifiedConfigurationManager

def main():
    """Apply configuration standardization automatically"""
    print("🔧 Applying Configuration Standardization...")
    print("=" * 50)

    manager = UnifiedConfigurationManager()

    # Generate report first
    report = manager.generate_configuration_report()

    # Print summary
    summary = report['validation_summary']
    print(f"Services with configs: {summary['services_with_configs']}")
    print(f"Services with ports: {summary['services_with_ports']}")
    print(f"Configuration conflicts: {summary['total_conflicts']}")

    # Apply standardization
    print("\\n📝 Applying configuration standardization...")
    results = manager.apply_configuration_standardization()

    print("\\n📊 Standardization Results:")
    if results['files_updated']:
        print("Updated files:")
        for file in results['files_updated']:
            print(f"  ✅ {file}")

    if results['files_created']:
        print("Created files:")
        for file in results['files_created']:
            print(f"  🆕 {file}")

    if results['errors']:
        print("Errors:")
        for error in results['errors']:
            print(f"  ❌ {error}")
        return 1

    print("\\n✅ Configuration standardization complete!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
