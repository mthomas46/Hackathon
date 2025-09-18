#!/usr/bin/env python3
"""
Automated Dockerfile Validation and Standardization System
Comprehensive Dockerfile analysis, linting, and optimization
"""

import os
import re
import json
import subprocess
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class DockerfileIssue:
    """Represents a Dockerfile issue or improvement opportunity"""
    line_number: int
    severity: str  # 'error', 'warning', 'info'
    category: str  # 'syntax', 'security', 'optimization', 'best_practice'
    rule: str
    message: str
    suggestion: str
    fix_available: bool = False

@dataclass
class DockerfileAnalysis:
    """Complete analysis of a Dockerfile"""
    filepath: str
    service_name: str
    issues: List[DockerfileIssue] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    score: int = 0
    recommendations: List[str] = field(default_factory=list)

class DockerfileValidator:
    """Comprehensive Dockerfile validation and analysis system"""

    def __init__(self):
        self.best_practices = {
            'security': self._check_security_issues,
            'optimization': self._check_optimization_opportunities,
            'syntax': self._check_syntax_issues,
            'consistency': self._check_consistency_issues
        }

        # Security patterns to check
        self.security_patterns = {
            'root_user': re.compile(r'^USER root', re.MULTILINE | re.IGNORECASE),
            'sudo_usage': re.compile(r'sudo', re.IGNORECASE),
            'latest_tag': re.compile(r'FROM .*:latest', re.IGNORECASE),
            'privileged_ports': re.compile(r'EXPOSE (1[0-9]|[1-9])\b'),
            'weak_permissions': re.compile(r'chmod 777|chmod o\+w', re.IGNORECASE)
        }

        # Optimization patterns
        self.optimization_patterns = {
            'multiple_runs': re.compile(r'^RUN ', re.MULTILINE),
            'large_copy': re.compile(r'^COPY \.', re.MULTILINE),
            'unused_expose': re.compile(r'^EXPOSE ', re.MULTILINE)
        }

    def analyze_dockerfile(self, dockerfile_path: str, service_name: str) -> DockerfileAnalysis:
        """Perform comprehensive analysis of a Dockerfile"""
        analysis = DockerfileAnalysis(filepath=dockerfile_path, service_name=service_name)

        try:
            with open(dockerfile_path, 'r') as f:
                content = f.read()

            lines = content.split('\n')

            # Run all validation checks
            for category, check_func in self.best_practices.items():
                issues = check_func(content, lines)
                analysis.issues.extend(issues)

            # Calculate metrics
            analysis.metrics = self._calculate_metrics(content, lines)

            # Calculate overall score
            analysis.score = self._calculate_score(analysis.issues)

            # Generate recommendations
            analysis.recommendations = self._generate_recommendations(analysis)

        except Exception as e:
            logger.error(f"Failed to analyze {dockerfile_path}: {e}")
            analysis.issues.append(DockerfileIssue(
                line_number=0,
                severity='error',
                category='syntax',
                rule='file_access',
                message=f"Unable to read Dockerfile: {e}",
                suggestion="Ensure Dockerfile exists and is readable"
            ))

        return analysis

    def _check_security_issues(self, content: str, lines: List[str]) -> List[DockerfileIssue]:
        """Check for security vulnerabilities and best practices"""
        issues = []

        # Check for root user usage
        if self.security_patterns['root_user'].search(content):
            issues.append(DockerfileIssue(
                line_number=self._find_line_number(lines, 'USER root'),
                severity='warning',
                category='security',
                rule='no_root_user',
                message="Running as root user poses security risks",
                suggestion="Create a non-root user with appropriate permissions",
                fix_available=True
            ))

        # Check for latest tag usage
        latest_matches = self.security_patterns['latest_tag'].findall(content)
        if latest_matches:
            issues.append(DockerfileIssue(
                line_number=self._find_line_number(lines, ':latest'),
                severity='warning',
                category='security',
                rule='avoid_latest_tag',
                message=f"Using 'latest' tag in {len(latest_matches)} FROM instruction(s)",
                suggestion="Pin to specific version tags for reproducible builds",
                fix_available=True
            ))

        # Check for sudo usage
        if self.security_patterns['sudo_usage'].search(content):
            issues.append(DockerfileIssue(
                line_number=self._find_line_number(lines, 'sudo'),
                severity='warning',
                category='security',
                rule='avoid_sudo',
                message="Using sudo inside container",
                suggestion="Use proper user permissions instead of sudo",
                fix_available=True
            ))

        # Check for privileged ports
        privileged_matches = self.security_patterns['privileged_ports'].findall(content)
        if privileged_matches:
            issues.append(DockerfileIssue(
                line_number=self._find_line_number(lines, f'EXPOSE {privileged_matches[0]}'),
                severity='info',
                category='security',
                rule='privileged_ports',
                message=f"Exposing privileged port(s): {', '.join(privileged_matches)}",
                suggestion="Use ports above 1024 for better security"
            ))

        return issues

    def _check_optimization_opportunities(self, content: str, lines: List[str]) -> List[DockerfileIssue]:
        """Check for optimization opportunities"""
        issues = []

        # Count RUN instructions
        run_count = len(self.optimization_patterns['multiple_runs'].findall(content))
        if run_count > 3:
            issues.append(DockerfileIssue(
                line_number=0,
                severity='info',
                category='optimization',
                rule='consolidate_runs',
                message=f"Found {run_count} RUN instructions - consider consolidating",
                suggestion="Combine multiple RUN instructions to reduce layer count",
                fix_available=True
            ))

        # Check for large COPY operations
        if self.optimization_patterns['large_copy'].search(content):
            issues.append(DockerfileIssue(
                line_number=self._find_line_number(lines, 'COPY .'),
                severity='info',
                category='optimization',
                rule='optimize_copy',
                message="COPY . copies entire context including unnecessary files",
                suggestion="Use .dockerignore and copy only necessary files",
                fix_available=True
            ))

        # Check for WORKDIR usage
        workdir_count = sum(1 for line in lines if line.strip().startswith('WORKDIR'))
        if workdir_count > 2:
            issues.append(DockerfileIssue(
                line_number=0,
                severity='info',
                category='optimization',
                rule='minimize_workdir',
                message=f"Found {workdir_count} WORKDIR instructions",
                suggestion="Minimize WORKDIR changes to reduce layer count"
            ))

        return issues

    def _check_syntax_issues(self, content: str, lines: List[str]) -> List[DockerfileIssue]:
        """Check for syntax errors and inconsistencies"""
        issues = []

        # Check for missing FROM instruction - look for first non-comment, non-empty line
        found_from = False
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped and not stripped.startswith('#'):
                if stripped.startswith('FROM'):
                    found_from = True
                break

        if not found_from:
            issues.append(DockerfileIssue(
                line_number=1,
                severity='error',
                category='syntax',
                rule='missing_from',
                message="Dockerfile must start with FROM instruction",
                suggestion="Add FROM instruction at the beginning of the Dockerfile"
            ))

        # Check for missing CMD/ENTRYPOINT
        has_cmd = any(line.strip().startswith(('CMD', 'ENTRYPOINT')) for line in lines)
        if not has_cmd:
            issues.append(DockerfileIssue(
                line_number=len(lines),
                severity='warning',
                category='syntax',
                rule='missing_cmd_entrypoint',
                message="Dockerfile should have CMD or ENTRYPOINT instruction",
                suggestion="Add CMD or ENTRYPOINT to specify container startup command"
            ))

        # Check for inconsistent indentation
        for i, line in enumerate(lines, 1):
            stripped = line.lstrip()
            if stripped and line.startswith(' ') and not stripped.startswith(('RUN', 'COPY', 'ADD')):
                issues.append(DockerfileIssue(
                    line_number=i,
                    severity='info',
                    category='syntax',
                    rule='inconsistent_indentation',
                    message=f"Inconsistent indentation on line {i}",
                    suggestion="Use consistent indentation throughout the Dockerfile"
                ))

        return issues

    def _check_consistency_issues(self, content: str, lines: List[str]) -> List[DockerfileIssue]:
        """Check for consistency issues across the ecosystem"""
        issues = []

        # Check for missing LABEL maintainer
        has_maintainer = any('LABEL maintainer' in line for line in lines)
        if not has_maintainer:
            issues.append(DockerfileIssue(
                line_number=0,
                severity='info',
                category='consistency',
                rule='missing_maintainer',
                message="Missing LABEL maintainer instruction",
                suggestion="Add LABEL maintainer for consistency"
            ))

        # Check for missing LABEL service
        has_service_label = any('LABEL service' in line for line in lines)
        if not has_service_label:
            issues.append(DockerfileIssue(
                line_number=0,
                severity='info',
                category='consistency',
                rule='missing_service_label',
                message="Missing LABEL service instruction",
                suggestion="Add LABEL service for service identification"
            ))

        # Check for EXPOSE instruction
        has_expose = any(line.strip().startswith('EXPOSE') for line in lines)
        if not has_expose:
            issues.append(DockerfileIssue(
                line_number=0,
                severity='warning',
                category='consistency',
                rule='missing_expose',
                message="Missing EXPOSE instruction",
                suggestion="Add EXPOSE to document container ports"
            ))

        return issues

    def _calculate_metrics(self, content: str, lines: List[str]) -> Dict[str, Any]:
        """Calculate Dockerfile metrics"""
        metrics = {
            'total_lines': len(lines),
            'instruction_count': {},
            'layer_count': 0,
            'file_size_kb': len(content) / 1024,
            'has_multistage': 'FROM' in content and content.count('FROM') > 1
        }

        # Count instructions
        instructions = ['FROM', 'RUN', 'COPY', 'ADD', 'WORKDIR', 'EXPOSE', 'ENV', 'LABEL', 'USER', 'CMD', 'ENTRYPOINT']
        for instruction in instructions:
            count = sum(1 for line in lines if line.strip().startswith(instruction))
            if count > 0:
                metrics['instruction_count'][instruction] = count

        # Count layers (each instruction creates a layer)
        metrics['layer_count'] = sum(metrics['instruction_count'].values())

        return metrics

    def _calculate_score(self, issues: List[DockerfileIssue]) -> int:
        """Calculate overall Dockerfile quality score (0-100)"""
        base_score = 100

        severity_penalties = {
            'error': 20,
            'warning': 10,
            'info': 2
        }

        for issue in issues:
            penalty = severity_penalties.get(issue.severity, 5)
            base_score -= penalty

        return max(0, min(100, base_score))

    def _generate_recommendations(self, analysis: DockerfileAnalysis) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []

        # Score-based recommendations
        if analysis.score < 70:
            recommendations.append("Overall Dockerfile quality needs improvement - address critical issues first")
        elif analysis.score < 85:
            recommendations.append("Consider optimization opportunities to improve build performance")

        # Issue-specific recommendations
        error_count = sum(1 for issue in analysis.issues if issue.severity == 'error')
        if error_count > 0:
            recommendations.append(f"Fix {error_count} critical syntax/security errors immediately")

        # Layer optimization
        if analysis.metrics.get('layer_count', 0) > 20:
            recommendations.append("High layer count detected - consider multi-stage builds")

        return recommendations

    def _find_line_number(self, lines: List[str], pattern: str) -> int:
        """Find line number containing a pattern"""
        for i, line in enumerate(lines, 1):
            if pattern.lower() in line.lower():
                return i
        return 0

    def validate_service_dockerfiles(self, services_dir: str = "services") -> Dict[str, DockerfileAnalysis]:
        """Validate all service Dockerfiles"""
        analyses = {}

        services_path = Path(services_dir)
        if not services_path.exists():
            logger.error(f"Services directory not found: {services_dir}")
            return analyses

        for service_dir in services_path.iterdir():
            if service_dir.is_dir():
                dockerfile_path = service_dir / "Dockerfile"
                if dockerfile_path.exists():
                    service_name = service_dir.name
                    logger.info(f"Analyzing Dockerfile for {service_name}")
                    analysis = self.analyze_dockerfile(str(dockerfile_path), service_name)
                    analyses[service_name] = analysis
                else:
                    logger.warning(f"No Dockerfile found for service: {service_dir.name}")

        return analyses

    def print_analysis_report(self, analyses: Dict[str, DockerfileAnalysis]):
        """Print comprehensive analysis report"""
        print("\n" + "="*80)
        print("🐳 DOCKERFILE VALIDATION AND ANALYSIS REPORT")
        print("="*80)

        if not analyses:
            print("❌ No Dockerfiles found for analysis")
            return

        total_score = 0
        total_issues = 0

        for service_name, analysis in analyses.items():
            print(f"\n📦 {service_name.upper()}")
            print("-" * (len(service_name) + 3))

            # Score
            score_color = "🟢" if analysis.score >= 85 else "🟡" if analysis.score >= 70 else "🔴"
            print(f"  {score_color} Quality Score: {analysis.score}/100")

            # Metrics
            metrics = analysis.metrics
            if metrics:
                print(f"  📊 Lines: {metrics['total_lines']}, Layers: {metrics['layer_count']}")
                if metrics['has_multistage']:
                    print("  🔄 Multi-stage build detected")

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

            total_score += analysis.score

        # Summary
        avg_score = total_score / len(analyses)
        print(f"\n📊 SUMMARY")
        print(f"  Services Analyzed: {len(analyses)}")
        print(f"  Average Score: {avg_score:.1f}/100")
        print(f"  Total Issues: {total_issues}")

        # Overall recommendations
        if avg_score < 70:
            print("\n💡 OVERALL RECOMMENDATIONS:")
            print("  • Address critical security and syntax issues immediately")
            print("  • Implement Dockerfile linting in CI/CD pipeline")
            print("  • Consider using base images with security updates")

        print("\n" + "="*80)

    def generate_optimization_script(self, analyses: Dict[str, DockerfileAnalysis]) -> str:
        """Generate optimization script for Dockerfile improvements"""
        script_lines = [
            "#!/bin/bash",
            "# Dockerfile Optimization Script",
            "# Generated by Dockerfile Validator",
            "",
            "echo '🔧 Optimizing Dockerfiles...'",
            ""
        ]

        for service_name, analysis in analyses.items():
            if analysis.score < 90:  # Only optimize if score is below 90
                script_lines.extend([
                    f"# Optimizing {service_name}",
                    f"echo 'Optimizing {service_name}...'",
                    "# Add optimization commands here",
                    ""
                ])

        script_lines.extend([
            "echo '✅ Dockerfile optimization complete'",
            "echo 'Review and test optimized Dockerfiles before deployment'"
        ])

        return "\n".join(script_lines)


def main():
    """Main entry point for Dockerfile validation"""
    validator = DockerfileValidator()

    try:
        # Validate all service Dockerfiles
        analyses = validator.validate_service_dockerfiles()

        # Print comprehensive report
        validator.print_analysis_report(analyses)

        # Generate optimization script if issues found
        total_issues = sum(len(analysis.issues) for analysis in analyses.values())
        if total_issues > 0:
            script = validator.generate_optimization_script(analyses)
            with open("dockerfile_optimization.sh", "w") as f:
                f.write(script)

            print(f"\n📝 Optimization script saved to: dockerfile_optimization.sh")
            print("Run 'chmod +x dockerfile_optimization.sh' to make it executable")

        # Save detailed results
        results = {
            service_name: {
                'score': analysis.score,
                'issues_count': len(analysis.issues),
                'metrics': analysis.metrics,
                'issues': [
                    {
                        'line': issue.line_number,
                        'severity': issue.severity,
                        'category': issue.category,
                        'message': issue.message,
                        'suggestion': issue.suggestion
                    }
                    for issue in analysis.issues
                ]
            }
            for service_name, analysis in analyses.items()
        }

        with open("dockerfile_analysis_report.json", "w") as f:
            json.dump(results, f, indent=2)

        print(f"\n💾 Detailed results saved to: dockerfile_analysis_report.json")

        # Exit with error code if critical issues found
        critical_issues = sum(
            1 for analysis in analyses.values()
            for issue in analysis.issues
            if issue.severity == 'error'
        )
        if critical_issues > 0:
            print(f"\n❌ Found {critical_issues} critical Dockerfile issues!")
            exit(1)

    except Exception as e:
        logger.error(f"Dockerfile validation failed: {e}")
        exit(1)


if __name__ == "__main__":
    main()
