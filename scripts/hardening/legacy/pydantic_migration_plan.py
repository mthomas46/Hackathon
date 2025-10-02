#!/usr/bin/env python3
"""
Pydantic Configuration Migration Plan

This script provides a comprehensive plan for migrating the LLM Documentation
Ecosystem configuration system from dataclasses to Pydantic-based configuration
management.

Migration Benefits:
- Enhanced type validation and error messages
- Automatic environment variable loading
- Field-level validation with constraints
- JSON schema generation for documentation
- Better IDE support and autocompletion
- Built-in settings sources management
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.shared.infrastructure.config.pydantic_config import (
    ServiceConfig, ServerConfig, RedisConfig, LoggingConfig,
    ServiceDependencies, LimitsConfig, HealthConfig, SecurityConfig,
    Environment, PYDANTIC_AVAILABLE
)


class PydanticMigrationPlanner:
    """
    Plan and execute migration from dataclass-based to Pydantic-based configuration.
    """

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.services_dir = self.project_root / "services"
        self.migration_steps = []
        self.validation_issues = []

    def analyze_current_system(self) -> Dict[str, Any]:
        """Analyze the current dataclass-based configuration system."""
        print("🔍 Analyzing Current Configuration System")
        print("-" * 50)

        analysis = {
            'services_with_config': [],
            'services_with_env_vars': [],
            'configuration_patterns': {},
            'validation_issues': [],
            'migration_readiness': {}
        }

        if not self.services_dir.exists():
            analysis['validation_issues'].append("Services directory not found")
            return analysis

        for service_dir in self.services_dir.iterdir():
            if not service_dir.is_dir() or service_dir.name.startswith('.') or service_dir.name == 'shared':
                continue

            service_name = service_dir.name
            config_file = service_dir / 'config.yaml'

            if config_file.exists():
                analysis['services_with_config'].append(service_name)

                try:
                    with open(config_file, 'r') as f:
                        config_data = yaml.safe_load(f) or {}

                    # Analyze configuration patterns
                    self._analyze_config_patterns(config_data, analysis['configuration_patterns'])

                    # Check environment variables
                    env_vars = self._extract_env_vars_from_config(config_data)
                    if env_vars:
                        analysis['services_with_env_vars'].append({
                            'service': service_name,
                            'env_vars': list(env_vars)
                        })

                except Exception as e:
                    analysis['validation_issues'].append(f"{service_name}: {str(e)}")

        return analysis

    def _analyze_config_patterns(self, config_data: Dict[str, Any], patterns: Dict[str, Any]):
        """Analyze configuration patterns in existing configs."""
        for key, value in config_data.items():
            if key not in patterns:
                patterns[key] = {'count': 0, 'types': set(), 'examples': []}

            patterns[key]['count'] += 1
            patterns[key]['types'].add(type(value).__name__)

            if len(patterns[key]['examples']) < 3:
                patterns[key]['examples'].append(value)

    def _extract_env_vars_from_config(self, config_data: Dict[str, Any]) -> set:
        """Extract environment variable references from configuration."""
        env_vars = set()

        def _find_env_vars(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if isinstance(value, str) and value.startswith('${'):
                        # Extract variable name
                        var_part = value[2:].split(':', 1)[0].split('}', 1)[0]
                        env_vars.add(var_part)
                    elif isinstance(value, (dict, list)):
                        _find_env_vars(value)
            elif isinstance(obj, list):
                for item in obj:
                    _find_env_vars(item)

        _find_env_vars(config_data)
        return env_vars

    def generate_migration_plan(self) -> List[Dict[str, Any]]:
        """Generate a detailed migration plan."""
        print("📋 Generating Pydantic Migration Plan")
        print("-" * 50)

        plan = []

        # Analyze current system
        analysis = self.analyze_current_system()

        # Phase 1: Foundation
        plan.append({
            'phase': 1,
            'name': 'Foundation Setup',
            'description': 'Set up Pydantic configuration infrastructure',
            'tasks': [
                'Verify Pydantic availability and version compatibility',
                'Create Pydantic configuration classes (ServerConfig, RedisConfig, etc.)',
                'Implement ServiceConfig with settings sources',
                'Add JSON schema generation for documentation',
                'Create migration utilities and backwards compatibility'
            ],
            'effort': 'Medium (2-3 days)',
            'risk': 'Low',
            'prerequisites': ['Pydantic installed', 'Current system working']
        })

        # Phase 2: Core Migration
        plan.append({
            'phase': 2,
            'name': 'Core Configuration Migration',
            'description': 'Migrate core configuration classes and validation',
            'tasks': [
                'Replace dataclass-based configs with Pydantic models',
                'Implement field-level validation (port ranges, URL formats, etc.)',
                'Add cross-field validation rules',
                'Update configuration loading to use Pydantic settings sources',
                'Maintain backwards compatibility during transition'
            ],
            'effort': 'High (1-2 weeks)',
            'risk': 'Medium',
            'prerequisites': ['Phase 1 complete', 'Tests passing']
        })

        # Phase 3: Service Integration
        plan.append({
            'phase': 3,
            'name': 'Service Integration',
            'description': 'Update all services to use Pydantic configuration',
            'tasks': [
                f"Migrate {len(analysis['services_with_config'])} services to Pydantic configs",
                'Update service main.py files to import new configuration classes',
                'Test configuration loading for all services',
                'Update Docker configurations if needed',
                'Validate environment variable handling'
            ],
            'effort': 'High (2-3 weeks)',
            'risk': 'Medium',
            'prerequisites': ['Phase 2 complete', 'All services tested']
        })

        # Phase 4: Advanced Features
        plan.append({
            'phase': 4,
            'name': 'Advanced Features Implementation',
            'description': 'Add advanced Pydantic features and optimizations',
            'tasks': [
                'Implement hot reload configuration',
                'Add configuration encryption for sensitive values',
                'Implement configuration caching and performance optimizations',
                'Add configuration monitoring and metrics',
                'Create configuration validation rules engine'
            ],
            'effort': 'Medium (1-2 weeks)',
            'risk': 'Low',
            'prerequisites': ['Phase 3 complete', 'System stable']
        })

        # Phase 5: Validation & Documentation
        plan.append({
            'phase': 5,
            'name': 'Validation & Documentation',
            'description': 'Comprehensive testing and documentation updates',
            'tasks': [
                'Run comprehensive configuration validation tests',
                'Update all documentation to reflect Pydantic usage',
                'Create migration guides for developers',
                'Add configuration examples and best practices',
                'Update CI/CD pipelines with new validation'
            ],
            'effort': 'Medium (1 week)',
            'risk': 'Low',
            'prerequisites': ['Phase 4 complete', 'All tests passing']
        })

        return plan

    def validate_pydantic_readiness(self) -> Dict[str, Any]:
        """Validate system readiness for Pydantic migration."""
        readiness = {
            'pydantic_available': PYDANTIC_AVAILABLE,
            'services_analyzed': 0,
            'config_files_found': 0,
            'env_vars_detected': 0,
            'potential_issues': [],
            'migration_complexity': 'Unknown'
        }

        if not PYDANTIC_AVAILABLE:
            readiness['potential_issues'].append("Pydantic not available - install required")
            return readiness

        # Analyze services
        analysis = self.analyze_current_system()
        readiness['services_analyzed'] = len([d for d in self.services_dir.iterdir()
                                           if d.is_dir() and not d.name.startswith('.') and d.name != 'shared'])
        readiness['config_files_found'] = len(analysis['services_with_config'])
        readiness['env_vars_detected'] = sum(len(s.get('env_vars', [])) for s in analysis['services_with_env_vars'])

        # Assess migration complexity
        if readiness['config_files_found'] == 0:
            readiness['migration_complexity'] = 'Simple'
        elif readiness['env_vars_detected'] < 50:
            readiness['migration_complexity'] = 'Medium'
        else:
            readiness['migration_complexity'] = 'Complex'

        readiness['potential_issues'] = analysis['validation_issues']

        return readiness

    def create_migration_script(self, service_name: str) -> str:
        """Generate a migration script for a specific service."""
        service_dir = self.services_dir / service_name
        config_file = service_dir / 'config.yaml'

        if not config_file.exists():
            return f"# Service {service_name} has no configuration file to migrate"

        migration_script = f'''#!/usr/bin/env python3
"""
Migration script for {service_name} to Pydantic configuration.

Generated by Pydantic Migration Planner.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def migrate_{service_name}_config():
    """Migrate {service_name} configuration to Pydantic."""

    print(f"🔄 Migrating {{service_name}} configuration to Pydantic...")
    print("-" * 50)

    try:
        # Import old configuration system
        from services.shared.infrastructure.config.configuration_manager import load_service_config as load_old_config

        # Load current configuration
        old_config = load_old_config("{service_name}")
        print(f"✅ Loaded existing configuration for {{old_config.service_name}}")

        # Import new Pydantic configuration system
        from services.shared.infrastructure.config.pydantic_config import ServiceConfig

        # Create new configuration with same values
        new_config = ServiceConfig(
            service_name="{service_name}",
            server={{
                'host': old_config.server.host,
                'port': old_config.server.port,
                'debug': old_config.server.debug,
                'workers': old_config.server.workers,
                'timeout': old_config.server.timeout
            }},
            redis={{
                'host': old_config.redis.host,
                'port': old_config.redis.port,
                'db': old_config.redis.db,
                'max_connections': old_config.redis.max_connections
            }},
            logging={{
                'level': old_config.logging.level,
                'format': old_config.logging.format,
                'structured': old_config.logging.structured,
                'console': old_config.logging.console
            }}
        )

        # Validate new configuration
        issues = new_config.validate_configuration()
        if issues:
            print("⚠️  Configuration validation issues:")
            for issue in issues:
                print(f"  - {{issue}}")
        else:
            print("✅ Configuration validation passed")

        # Test configuration loading
        print(f"✅ Pydantic configuration created for {{new_config.service_name}}")
        print(f"  Port: {{new_config.server.port}}")
        print(f"  Redis: {{new_config.redis.host}}:{{new_config.redis.port}}")
        print(f"  Environment: {{new_config.environment}}")

        return True

    except Exception as e:
        print(f"❌ Migration failed: {{e}}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = migrate_{service_name}_config()
    sys.exit(0 if success else 1)
'''

        return migration_script

    def generate_implementation_plan(self) -> Dict[str, Any]:
        """Generate a comprehensive implementation plan."""
        plan = {
            'readiness_check': self.validate_pydantic_readiness(),
            'migration_plan': self.generate_migration_plan(),
            'service_migration_scripts': {},
            'timeline': {},
            'risk_assessment': {},
            'rollback_plan': {}
        }

        # Generate migration scripts for services with configs
        analysis = self.analyze_current_system()
        for service in analysis['services_with_config']:
            plan['service_migration_scripts'][service] = self.create_migration_script(service)

        # Calculate timeline
        total_effort_days = sum([
            3 if phase['effort'].startswith('Low') else
            7 if phase['effort'].startswith('Medium') else
            14 if phase['effort'].startswith('High') else 0
            for phase in plan['migration_plan']
        ])
        plan['timeline'] = {
            'estimated_total_days': total_effort_days,
            'phases': len(plan['migration_plan']),
            'recommended_pace': '1 phase per week',
            'milestones': [phase['name'] for phase in plan['migration_plan']]
        }

        # Risk assessment
        readiness = plan['readiness_check']
        if not readiness['pydantic_available']:
            risk_level = 'High'
            risk_factors = ['Pydantic dependency missing']
        elif readiness['migration_complexity'] == 'Complex':
            risk_level = 'Medium'
            risk_factors = ['High number of environment variables to migrate']
        else:
            risk_level = 'Low'
            risk_factors = []

        plan['risk_assessment'] = {
            'overall_risk': risk_level,
            'risk_factors': risk_factors,
            'mitigation_strategies': [
                'Comprehensive testing before each phase',
                'Backwards compatibility during migration',
                'Rollback procedures documented',
                'Gradual rollout with feature flags'
            ]
        }

        # Rollback plan
        plan['rollback_plan'] = {
            'immediate_rollback': 'Revert service main.py imports to old configuration system',
            'full_rollback': 'Restore dataclass-based configuration files from backup',
            'partial_rollback': 'Use feature flags to switch between old and new systems',
            'testing_rollback': 'Automated tests to verify rollback functionality'
        }

        return plan


def main():
    """Main migration planning function."""
    print("🚀 Pydantic Configuration Migration Planner")
    print("=" * 60)
    print()

    planner = PydanticMigrationPlanner()

    # Check readiness
    print("📋 Checking System Readiness...")
    readiness = planner.validate_pydantic_readiness()

    print(f"✅ Pydantic Available: {readiness['pydantic_available']}")
    print(f"📊 Services Analyzed: {readiness['services_analyzed']}")
    print(f"📄 Config Files Found: {readiness['config_files_found']}")
    print(f"🔧 Env Vars Detected: {readiness['env_vars_detected']}")
    print(f"🎯 Migration Complexity: {readiness['migration_complexity']}")

    if readiness['potential_issues']:
        print("⚠️  Potential Issues:")
        for issue in readiness['potential_issues']:
            print(f"  - {issue}")

    print()

    # Generate migration plan
    print("📋 Generating Migration Plan...")
    plan = planner.generate_implementation_plan()

    print(f"📅 Estimated Timeline: {plan['timeline']['estimated_total_days']} days")
    print(f"🏗️  Migration Phases: {plan['timeline']['phases']}")
    print(f"⚡ Risk Level: {plan['risk_assessment']['overall_risk']}")

    print()
    print("🎯 Migration Phases:")
    for phase in plan['migration_plan']:
        print(f"  {phase['phase']}. {phase['name']} ({phase['effort']})")
        print(f"     {phase['description']}")

    print()
    print("💾 Generating Implementation Plan...")

    # Save comprehensive plan
    output_file = Path("pydantic_migration_plan.json")
    with open(output_file, 'w') as f:
        # Convert sets to lists for JSON serialization
        json_plan = json.loads(json.dumps(plan, default=str))
        json.dump(json_plan, f, indent=2)

    print(f"✅ Migration plan saved to {output_file}")

    # Generate migration scripts
    scripts_dir = Path("pydantic_migration_scripts")
    scripts_dir.mkdir(exist_ok=True)

    for service_name, script_content in plan['service_migration_scripts'].items():
        script_file = scripts_dir / f"migrate_{service_name}_config.py"
        with open(script_file, 'w') as f:
            f.write(script_content)
        print(f"  📝 Generated migration script: {script_file}")

    print()
    print("🎉 Migration planning complete!")
    print()
    print("📖 Next Steps:")
    print("1. Review the generated migration plan in pydantic_migration_plan.json")
    print("2. Test migration scripts on a single service first")
    print("3. Run Phase 1 (Foundation Setup) from the plan")
    print("4. Gradually migrate services following the phased approach")
    print("5. Use rollback procedures if issues arise")


if __name__ == "__main__":
    main()
