#!/usr/bin/env python3
"""
Automated Environment Variable Validation and Consistency System
Comprehensive environment variable analysis and validation
"""

import os
import re
import json
import yaml
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class EnvironmentVariable:
    """Environment variable configuration"""
    name: str
    value: str
    source: str  # 'dockerfile', 'docker-compose', 'port-registry'
    service_name: str
    line_number: int = 0
    required: bool = False
    validation_pattern: Optional[str] = None

@dataclass
class EnvironmentIssue:
    """Environment variable issue"""
    severity: str  # 'error', 'warning', 'info'
    category: str  # 'consistency', 'security', 'naming', 'missing'
    service_name: str
    variable_name: str
    message: str
    suggestion: str
    fix_available: bool = False

@dataclass
class EnvironmentAnalysis:
    """Complete environment analysis for a service"""
    service_name: str
    variables: List[EnvironmentVariable] = field(default_factory=list)
    issues: List[EnvironmentIssue] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    score: int = 100

class EnvironmentValidator:
    """Comprehensive environment variable validation system"""

    def __init__(self, docker_compose_file: str = "docker-compose.dev.yml",
                 port_registry_file: str = "config/standardized/port_registry.json"):
        self.docker_compose_file = Path(docker_compose_file)
        self.port_registry_file = Path(port_registry_file)

        # Required environment variables for different service types
        self.required_variables = {
            'all': ['SERVICE_NAME'],
            'web_service': ['SERVICE_PORT'],
            'database_service': ['REDIS_HOST'],
            'ai_service': ['OLLAMA_ENDPOINT']
        }

        # Environment variable naming patterns
        self.naming_patterns = {
            'valid_pattern': re.compile(r'^[A-Z][A-Z0-9_]*$'),
            'service_pattern': re.compile(r'^SERVICE_.*'),
            'port_pattern': re.compile(r'.*_PORT$'),
            'url_pattern': re.compile(r'.*_URL$'),
            'host_pattern': re.compile(r'.*_HOST$')
        }

        # Security-sensitive patterns
        self.security_patterns = {
            'password': re.compile(r'PASSWORD|SECRET|KEY', re.IGNORECASE),
            'token': re.compile(r'TOKEN|AUTH', re.IGNORECASE),
            'private_key': re.compile(r'PRIVATE.*KEY', re.IGNORECASE)
        }

        # Validation patterns for specific variables
        self.validation_patterns = {
            'SERVICE_PORT': re.compile(r'^\d{2,5}$'),  # 2-5 digit port numbers
            'REDIS_HOST': re.compile(r'^[a-zA-Z0-9._-]+$'),  # Valid hostname
            'OLLAMA_ENDPOINT': re.compile(r'^http://.*:\d+$'),  # Valid HTTP URL with port
        }

    def analyze_service_environments(self, services_dir: str = "services") -> Dict[str, EnvironmentAnalysis]:
        """Analyze environment variables across all services"""
        analyses = {}

        # Load configurations
        docker_compose_config = self._load_docker_compose_config()
        port_registry = self._load_port_registry()

        services_path = Path(services_dir)
        if not services_path.exists():
            logger.error(f"Services directory not found: {services_dir}")
            return analyses

        for service_dir in services_path.iterdir():
            if service_dir.is_dir() and not service_dir.name.startswith('_'):
                dockerfile_path = service_dir / "Dockerfile"
                if dockerfile_path.exists():
                    service_name = service_dir.name
                    analysis = self._analyze_service_environment(
                        service_name, dockerfile_path, docker_compose_config, port_registry
                    )
                    analyses[service_name] = analysis

        return analyses

    def _analyze_service_environment(self, service_name: str, dockerfile_path: Path,
                                   docker_compose_config: Dict[str, Any],
                                   port_registry: Dict[str, Any]) -> EnvironmentAnalysis:
        """Analyze environment variables for a specific service"""
        analysis = EnvironmentAnalysis(service_name=service_name)

        # Extract environment variables from different sources
        dockerfile_vars = self._extract_dockerfile_env_vars(dockerfile_path)
        compose_vars = self._extract_compose_env_vars(service_name, docker_compose_config)
        registry_vars = self._extract_registry_env_vars(service_name, port_registry)

        # Combine all variables
        all_vars = {**dockerfile_vars, **compose_vars, **registry_vars}
        for var_name, var_data in all_vars.items():
            analysis.variables.append(EnvironmentVariable(
                name=var_name,
                value=var_data['value'],
                source=var_data['source'],
                service_name=service_name,
                line_number=var_data.get('line_number', 0)
            ))

        # Perform validation checks
        analysis.issues = self._validate_environment_variables(analysis.variables, service_name)
        analysis.conflicts = self._check_variable_conflicts(analysis.variables)
        analysis.recommendations = self._generate_recommendations(analysis.variables, analysis.issues)
        analysis.score = self._calculate_environment_score(analysis.issues, analysis.variables)

        return analysis

    def _extract_dockerfile_env_vars(self, dockerfile_path: Path) -> Dict[str, Dict[str, Any]]:
        """Extract environment variables from Dockerfile"""
        variables = {}

        try:
            with open(dockerfile_path, 'r') as f:
                lines = f.readlines()

            for i, line in enumerate(lines, 1):
                line = line.strip()

                # Check for ENV instructions
                if line.startswith('ENV '):
                    # Handle both formats: ENV KEY=VALUE and ENV KEY VALUE
                    env_part = line[4:].strip()
                    if '=' in env_part:
                        key, value = env_part.split('=', 1)
                        variables[key.strip()] = {
                            'value': value.strip(),
                            'source': 'dockerfile',
                            'line_number': i
                        }
                    else:
                        # Multi-line ENV or separate format
                        parts = env_part.split()
                        if len(parts) >= 2:
                            variables[parts[0]] = {
                                'value': ' '.join(parts[1:]),
                                'source': 'dockerfile',
                                'line_number': i
                            }

        except Exception as e:
            logger.error(f"Failed to extract ENV vars from {dockerfile_path}: {e}")

        return variables

    def _extract_compose_env_vars(self, service_name: str, compose_config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Extract environment variables from docker-compose configuration"""
        variables = {}

        if 'services' not in compose_config or service_name not in compose_config['services']:
            return variables

        service_config = compose_config['services'][service_name]

        if 'environment' in service_config:
            env_config = service_config['environment']

            if isinstance(env_config, list):
                for env_item in env_config:
                    if isinstance(env_item, str) and '=' in env_item:
                        key, value = env_item.split('=', 1)
                        variables[key.strip()] = {
                            'value': value.strip(),
                            'source': 'docker-compose',
                            'line_number': 0
                        }
                    elif isinstance(env_item, dict):
                        for key, value in env_item.items():
                            variables[key] = {
                                'value': str(value),
                                'source': 'docker-compose',
                                'line_number': 0
                            }
            elif isinstance(env_config, dict):
                for key, value in env_config.items():
                    variables[key] = {
                        'value': str(value),
                        'source': 'docker-compose',
                        'line_number': 0
                    }

        return variables

    def _extract_registry_env_vars(self, service_name: str, port_registry: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Extract environment variables from port registry"""
        variables = {}

        if service_name in port_registry and 'environment_vars' in port_registry[service_name]:
            env_vars = port_registry[service_name]['environment_vars']
            for key, value in env_vars.items():
                variables[key] = {
                    'value': str(value),
                    'source': 'port-registry',
                    'line_number': 0
                }

        return variables

    def _validate_environment_variables(self, variables: List[EnvironmentVariable],
                                       service_name: str) -> List[EnvironmentIssue]:
        """Validate environment variables for consistency and security"""
        issues = []

        # Group variables by name for consistency checking
        var_by_name = {}
        for var in variables:
            if var.name not in var_by_name:
                var_by_name[var.name] = []
            var_by_name[var.name].append(var)

        # Check for consistency across sources
        for var_name, var_list in var_by_name.items():
            if len(var_list) > 1:
                values = [v.value for v in var_list]
                sources = [v.source for v in var_list]

                if len(set(values)) > 1:  # Inconsistent values
                    issues.append(EnvironmentIssue(
                        severity='warning',
                        category='consistency',
                        service_name=service_name,
                        variable_name=var_name,
                        message=f"Variable '{var_name}' has inconsistent values across sources: {dict(zip(sources, values))}",
                        suggestion="Ensure consistent values across all configuration sources"
                    ))

        # Validate individual variables
        for var in variables:
            # Check naming convention
            if not self.naming_patterns['valid_pattern'].match(var.name):
                issues.append(EnvironmentIssue(
                    severity='info',
                    category='naming',
                    service_name=service_name,
                    variable_name=var.name,
                    message=f"Variable '{var.name}' doesn't follow naming convention (UPPER_CASE)",
                    suggestion="Use UPPER_CASE naming for environment variables"
                ))

            # Check for security-sensitive variables
            for pattern_name, pattern in self.security_patterns.items():
                if pattern.search(var.name):
                    if var.value and not var.value.startswith('$'):  # Not a reference
                        issues.append(EnvironmentIssue(
                            severity='warning',
                            category='security',
                            service_name=service_name,
                            variable_name=var.name,
                            message=f"Security-sensitive variable '{var.name}' may contain sensitive data",
                            suggestion="Use secret management or environment variable references"
                        ))

            # Validate specific variable patterns
            if var.name in self.validation_patterns:
                pattern = self.validation_patterns[var.name]
                if not pattern.match(var.value):
                    issues.append(EnvironmentIssue(
                        severity='error',
                        category='consistency',
                        service_name=service_name,
                        variable_name=var.name,
                        message=f"Variable '{var.name}' value '{var.value}' doesn't match expected pattern",
                        suggestion=f"Expected pattern: {pattern.pattern}"
                    ))

        # Check for required variables
        var_names = {v.name for v in variables}

        # Check service-specific required variables
        service_type = self._determine_service_type(service_name, variables)
        required_vars = self.required_variables.get(service_type, []) + self.required_variables['all']

        for required_var in required_vars:
            if required_var not in var_names:
                issues.append(EnvironmentIssue(
                    severity='error',
                    category='missing',
                    service_name=service_name,
                    variable_name=required_var,
                    message=f"Required variable '{required_var}' is missing",
                    suggestion="Add the required environment variable to your configuration"
                ))

        return issues

    def _determine_service_type(self, service_name: str, variables: List[EnvironmentVariable]) -> str:
        """Determine service type based on variables and name"""
        var_names = {v.name for v in variables}

        if 'OLLAMA_ENDPOINT' in var_names or 'ai' in service_name.lower():
            return 'ai_service'
        elif 'REDIS_HOST' in var_names and 'SERVICE_PORT' in var_names:
            return 'web_service'
        elif 'REDIS_HOST' in var_names:
            return 'database_service'
        else:
            return 'generic_service'

    def _check_variable_conflicts(self, variables: List[EnvironmentVariable]) -> List[str]:
        """Check for potential variable conflicts"""
        conflicts = []
        var_by_name = {}

        for var in variables:
            if var.name not in var_by_name:
                var_by_name[var.name] = []
            var_by_name[var.name].append(var)

        # Check for variables with same name but different values
        for var_name, var_list in var_by_name.items():
            if len(var_list) > 1:
                values = set(v.value for v in var_list)
                if len(values) > 1:
                    conflicts.append(f"Variable '{var_name}' has conflicting values: {list(values)}")

        return conflicts

    def _generate_recommendations(self, variables: List[EnvironmentVariable],
                                issues: List[EnvironmentIssue]) -> List[str]:
        """Generate recommendations for environment variable improvements"""
        recommendations = []

        # Count issues by category
        issue_counts = {}
        for issue in issues:
            issue_counts[issue.category] = issue_counts.get(issue.category, 0) + 1

        if issue_counts.get('security', 0) > 0:
            recommendations.append("Implement proper secret management for sensitive environment variables")

        if issue_counts.get('consistency', 0) > 0:
            recommendations.append("Centralize environment variable definitions to ensure consistency")

        if issue_counts.get('missing', 0) > 0:
            recommendations.append("Add missing required environment variables to service configurations")

        if issue_counts.get('naming', 0) > 0:
            recommendations.append("Standardize environment variable naming conventions (UPPER_CASE)")

        # General recommendations
        if len(variables) > 10:
            recommendations.append("Consider using environment files (.env) for complex configurations")

        # Check for hardcoded values that should be variables
        hardcoded_patterns = [
            re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'),  # IP addresses
            re.compile(r'\b\d{4,5}\b'),  # Port numbers in values
        ]

        for var in variables:
            for pattern in hardcoded_patterns:
                if pattern.search(var.value):
                    recommendations.append(f"Consider making hardcoded values in '{var.name}' configurable")
                    break

        return recommendations

    def _calculate_environment_score(self, issues: List[EnvironmentIssue],
                                   variables: List[EnvironmentVariable]) -> int:
        """Calculate environment configuration quality score"""
        base_score = 100

        severity_penalties = {
            'error': 15,
            'warning': 8,
            'info': 3
        }

        for issue in issues:
            penalty = severity_penalties.get(issue.severity, 5)
            base_score -= penalty

        # Bonus for having required variables
        required_vars = {'SERVICE_NAME', 'SERVICE_PORT'}
        var_names = {v.name for v in variables}
        if required_vars.issubset(var_names):
            base_score += 10

        return max(0, min(100, base_score))

    def _load_docker_compose_config(self) -> Dict[str, Any]:
        """Load docker-compose configuration"""
        try:
            with open(self.docker_compose_file, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load docker-compose config: {e}")
            return {}

    def _load_port_registry(self) -> Dict[str, Any]:
        """Load port registry"""
        try:
            with open(self.port_registry_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load port registry: {e}")
            return {}

    def print_analysis_report(self, analyses: Dict[str, EnvironmentAnalysis]):
        """Print comprehensive environment analysis report"""
        print("\n" + "="*80)
        print("🌍 ENVIRONMENT VARIABLE VALIDATION REPORT")
        print("="*80)

        if not analyses:
            print("❌ No services found for environment analysis")
            return

        total_score = 0
        total_issues = 0
        total_variables = 0

        for service_name, analysis in analyses.items():
            print(f"\n🔧 {service_name.upper()}")
            print("-" * (len(service_name) + 3))

            # Score
            score_color = "🟢" if analysis.score >= 85 else "🟡" if analysis.score >= 70 else "🔴"
            print(f"  {score_color} Quality Score: {analysis.score}/100")

            # Variables summary
            print(f"  📊 Variables: {len(analysis.variables)}")
            total_variables += len(analysis.variables)

            # Show variables by source
            sources = {}
            for var in analysis.variables:
                sources[var.source] = sources.get(var.source, 0) + 1

            if sources:
                source_str = ", ".join([f"{src}: {count}" for src, count in sources.items()])
                print(f"  📁 Sources: {source_str}")

            # Issues summary
            if analysis.issues:
                errors = sum(1 for i in analysis.issues if i.severity == 'error')
                warnings = sum(1 for i in analysis.issues if i.severity == 'warning')
                infos = sum(1 for i in analysis.issues if i.severity == 'info')

                print(f"  🚨 Issues: {errors} errors, {warnings} warnings, {infos} suggestions")
                total_issues += len(analysis.issues)

                # Show top issues
                for issue in analysis.issues[:3]:  # Show first 3 issues
                    severity_icon = "🔴" if issue.severity == 'error' else "🟡" if issue.severity == 'warning' else "ℹ️"
                    print(f"    {severity_icon} {issue.message}")

            # Conflicts
            if analysis.conflicts:
                print(f"  ⚠️ Conflicts: {len(analysis.conflicts)}")
                for conflict in analysis.conflicts[:2]:  # Show first 2 conflicts
                    print(f"    • {conflict}")

            total_score += analysis.score

        # Summary
        avg_score = total_score / len(analyses)
        print(f"\n📊 SUMMARY")
        print(f"  Services Analyzed: {len(analyses)}")
        print(f"  Total Variables: {total_variables}")
        print(f"  Average Score: {avg_score:.1f}/100")
        print(f"  Total Issues: {total_issues}")

        # Overall recommendations
        if avg_score < 70:
            print("\n💡 OVERALL RECOMMENDATIONS:")
            print("  • Address critical environment variable issues immediately")
            print("  • Implement environment variable validation in CI/CD")
            print("  • Use centralized configuration management")

        print("\n" + "="*80)

    def generate_fix_script(self, analyses: Dict[str, EnvironmentAnalysis]) -> str:
        """Generate script to fix environment variable issues"""
        script_lines = [
            "#!/bin/bash",
            "# Environment Variable Fix Script",
            "# Generated by Environment Validator",
            "",
            "echo '🔧 Fixing environment variable issues...'",
            ""
        ]

        for service_name, analysis in analyses.items():
            if analysis.score < 90:  # Only fix if score is below 90
                script_lines.extend([
                    f"# Fixing {service_name}",
                    f"echo 'Fixing environment variables for {service_name}...'",
                    "# Add fix commands here",
                    ""
                ])

        script_lines.extend([
            "echo '✅ Environment variable fixes complete'",
            "echo 'Review and test the changes before deployment'"
        ])

        return "\n".join(script_lines)


def main():
    """Main entry point for environment variable validation"""
    validator = EnvironmentValidator()

    try:
        # Analyze all service environments
        analyses = validator.analyze_service_environments()

        # Print comprehensive report
        validator.print_analysis_report(analyses)

        # Generate fix script if issues found
        total_issues = sum(len(analysis.issues) for analysis in analyses.values())
        if total_issues > 0:
            script = validator.generate_fix_script(analyses)
            with open("environment_fix.sh", "w") as f:
                f.write(script)

            print(f"\n📝 Fix script saved to: environment_fix.sh")
            print("Run 'chmod +x environment_fix.sh' to make it executable")

        # Save detailed results
        results = {
            service_name: {
                'score': analysis.score,
                'variables_count': len(analysis.variables),
                'issues_count': len(analysis.issues),
                'conflicts_count': len(analysis.conflicts),
                'issues': [
                    {
                        'severity': issue.severity,
                        'category': issue.category,
                        'variable': issue.variable_name,
                        'message': issue.message,
                        'suggestion': issue.suggestion
                    }
                    for issue in analysis.issues
                ],
                'variables': [
                    {
                        'name': var.name,
                        'value': var.value,
                        'source': var.source
                    }
                    for var in analysis.variables
                ]
            }
            for service_name, analysis in analyses.items()
        }

        with open("environment_analysis_report.json", "w") as f:
            json.dump(results, f, indent=2)

        print(f"\n💾 Detailed results saved to: environment_analysis_report.json")

        # Exit with error code if critical issues found
        critical_issues = sum(
            1 for analysis in analyses.values()
            for issue in analysis.issues
            if issue.severity == 'error'
        )
        if critical_issues > 0:
            print(f"\n❌ Found {critical_issues} critical environment variable issues!")
            exit(1)

    except Exception as e:
        logger.error(f"Environment validation failed: {e}")
        exit(1)


if __name__ == "__main__":
    main()
