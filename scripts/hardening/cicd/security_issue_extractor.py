#!/usr/bin/env python3
"""
Security Issue Extractor - Hackathon Ecosystem
===============================================

Extracts and analyzes security issues from various security scanning tools
(Bandit, Safety, Trivy, etc.) and provides structured reporting for CI/CD integration.

Features:
- Parses Bandit JSON reports for code security issues
- Parses Safety JSON reports for dependency vulnerabilities
- Parses Trivy SARIF reports for container vulnerabilities
- Filters issues by severity (Medium, High, Critical)
- Generates structured TODO items for remediation
- Integrates with CI/CD pipelines for automated issue tracking

Author: Hackathon Security Framework
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import argparse


@dataclass
class SecurityIssue:
    """Represents a security issue found by scanning tools"""
    tool: str
    severity: str
    confidence: Optional[str] = None
    title: str = ""
    description: str = ""
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    cwe_id: Optional[str] = None
    test_id: Optional[str] = None
    package_name: Optional[str] = None
    package_version: Optional[str] = None
    vulnerability_id: Optional[str] = None
    remediation: Optional[str] = None
    url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'tool': self.tool,
            'severity': self.severity,
            'confidence': self.confidence,
            'title': self.title,
            'description': self.description,
            'file_path': self.file_path,
            'line_number': self.line_number,
            'cwe_id': self.cwe_id,
            'test_id': self.test_id,
            'package_name': self.package_name,
            'package_version': self.package_version,
            'vulnerability_id': self.vulnerability_id,
            'remediation': self.remediation,
            'url': self.url
        }

    def __str__(self) -> str:
        """String representation for display"""
        location = ""
        if self.file_path:
            location = f"{self.file_path}"
            if self.line_number:
                location += f":{self.line_number}"

        details = []
        if self.package_name:
            details.append(f"Package: {self.package_name}")
        if self.vulnerability_id:
            details.append(f"ID: {self.vulnerability_id}")
        if self.test_id:
            details.append(f"Test: {self.test_id}")
        if self.cwe_id:
            details.append(f"CWE: {self.cwe_id}")

        detail_str = f" ({', '.join(details)})" if details else ""

        return f"[{self.tool}] {self.severity}: {self.title}{detail_str}" + (f" in {location}" if location else "")


class SecurityIssueExtractor:
    """Main class for extracting security issues from various tools"""

    def __init__(self):
        self.issues: List[SecurityIssue] = []

    def extract_from_bandit(self, bandit_file: str) -> List[SecurityIssue]:
        """Extract issues from Bandit JSON report"""
        issues = []

        try:
            with open(bandit_file, 'r') as f:
                data = json.load(f)

            # Parse results - can be list of dicts or list of lists
            results = data.get('results', [])
            for item in results:
                if isinstance(item, dict):
                    # Single issue format
                    severity = item.get('issue_severity', 'Low').title()  # Normalize case
                    if severity in ['Medium', 'High']:
                        issues.append(SecurityIssue(
                            tool='Bandit',
                            severity=severity,
                            confidence=item.get('issue_confidence'),
                            title=item.get('issue_text', ''),
                            description=item.get('issue_text', ''),
                            file_path=item.get('filename'),
                            line_number=item.get('line_number'),
                            cwe_id=item.get('issue_cwe', {}).get('id') if item.get('issue_cwe') else None,
                            test_id=item.get('test_id'),
                            url=item.get('more_info')
                        ))
                elif isinstance(item, list):
                    # List of issues format (older Bandit versions)
                    for issue in item:
                        if isinstance(issue, dict):
                            severity = issue.get('issue_severity', 'Low').title()  # Normalize case
                            if severity in ['Medium', 'High']:
                                issues.append(SecurityIssue(
                                    tool='Bandit',
                                    severity=severity,
                                    confidence=issue.get('issue_confidence'),
                                    title=issue.get('issue_text', ''),
                                    description=issue.get('issue_text', ''),
                                    file_path=issue.get('filename'),
                                    line_number=issue.get('line_number'),
                                    cwe_id=issue.get('issue_cwe', {}).get('id') if issue.get('issue_cwe') else None,
                                    test_id=issue.get('test_id'),
                                    url=issue.get('more_info')
                                ))

        except Exception as e:
            print(f"Error parsing Bandit report {bandit_file}: {e}", file=sys.stderr)

        return issues

    def extract_from_safety(self, safety_file: str) -> List[SecurityIssue]:
        """Extract issues from Safety JSON report"""
        issues = []

        try:
            with open(safety_file, 'r') as f:
                data = json.load(f)

            # Safety reports vulnerabilities in different structures
            vulnerabilities = data.get('vulnerabilities', [])
            for vuln in vulnerabilities:
                severity = vuln.get('severity', 'Unknown')
                if severity in ['Medium', 'High', 'Critical']:
                    issues.append(SecurityIssue(
                        tool='Safety',
                        severity=severity,
                        title=vuln.get('vulnerability', ''),
                        description=vuln.get('description', ''),
                        package_name=vuln.get('package'),
                        package_version=vuln.get('version'),
                        vulnerability_id=vuln.get('vulnerability_id'),
                        url=vuln.get('more_info_url')
                    ))

        except Exception as e:
            print(f"Error parsing Safety report {safety_file}: {e}", file=sys.stderr)

        return issues

    def extract_from_trivy_sarif(self, trivy_file: str) -> List[SecurityIssue]:
        """Extract issues from Trivy SARIF report"""
        issues = []

        try:
            with open(trivy_file, 'r') as f:
                data = json.load(f)

            # Parse SARIF format
            runs = data.get('runs', [])
            for run in runs:
                results = run.get('results', [])
                for result in results:
                    # Map severity levels
                    severity_map = {
                        'error': 'High',
                        'warning': 'Medium',
                        'note': 'Low',
                        'none': 'Info'
                    }

                    level = result.get('level', 'none')
                    severity = severity_map.get(level, 'Unknown')

                    if severity in ['Medium', 'High', 'Critical']:
                        # Extract location info
                        locations = result.get('locations', [])
                        file_path = None
                        if locations:
                            physical_location = locations[0].get('physicalLocation', {})
                            artifact_location = physical_location.get('artifactLocation', {})
                            file_path = artifact_location.get('uri')

                        issues.append(SecurityIssue(
                            tool='Trivy',
                            severity=severity,
                            title=result.get('message', {}).get('text', ''),
                            description=result.get('message', {}).get('text', ''),
                            file_path=file_path,
                            vulnerability_id=result.get('ruleId')
                        ))

        except Exception as e:
            print(f"Error parsing Trivy SARIF report {trivy_file}: {e}", file=sys.stderr)

        return issues

    def extract_all_issues(self, reports_dir: str = 'reports') -> List[SecurityIssue]:
        """Extract issues from all available reports"""
        issues = []

        # Look for various report files
        report_files = {
            'bandit': ['bandit-results.json', 'bandit-*.json'],
            'safety': ['safety-results.json', 'safety-*.json'],
            'trivy': ['trivy-results.sarif', 'trivy-*.sarif']
        }

        for tool, patterns in report_files.items():
            for pattern in patterns:
                # Simple glob implementation
                if '*' in pattern:
                    base_pattern = pattern.replace('*', '')
                    for file in Path(reports_dir).glob(f"**/{pattern}"):
                        if tool == 'bandit':
                            issues.extend(self.extract_from_bandit(str(file)))
                        elif tool == 'safety':
                            issues.extend(self.extract_from_safety(str(file)))
                        elif tool == 'trivy':
                            issues.extend(self.extract_from_trivy_sarif(str(file)))
                else:
                    report_path = Path(reports_dir) / pattern
                    if report_path.exists():
                        if tool == 'bandit':
                            issues.extend(self.extract_from_bandit(str(report_path)))
                        elif tool == 'safety':
                            issues.extend(self.extract_from_safety(str(report_path)))
                        elif tool == 'trivy':
                            issues.extend(self.extract_from_trivy_sarif(str(report_path)))

        # Also check current directory
        for file in Path('.').glob('bandit-*.json'):
            issues.extend(self.extract_from_bandit(str(file)))
        for file in Path('.').glob('safety-*.json'):
            issues.extend(self.extract_from_safety(str(file)))
        for file in Path('.').glob('trivy-*.sarif'):
            issues.extend(self.extract_from_trivy_sarif(str(file)))

        self.issues = issues
        return issues

    def filter_by_severity(self, min_severity: str = 'Medium') -> List[SecurityIssue]:
        """Filter issues by minimum severity level"""
        severity_order = {'Low': 0, 'Medium': 1, 'High': 2, 'Critical': 3}

        min_level = severity_order.get(min_severity, 1)

        return [issue for issue in self.issues
                if severity_order.get(issue.severity, 0) >= min_level]

    def group_by_tool(self) -> Dict[str, List[SecurityIssue]]:
        """Group issues by scanning tool"""
        grouped = {}
        for issue in self.issues:
            if issue.tool not in grouped:
                grouped[issue.tool] = []
            grouped[issue.tool].append(issue)
        return grouped

    def generate_todo_items(self, issues: List[SecurityIssue]) -> List[Dict[str, Any]]:
        """Generate TODO items for the issues"""
        todos = []

        for i, issue in enumerate(issues, 1):
            todo_id = f"security_fix_{issue.tool.lower()}_{i}"

            # Create descriptive title
            title_parts = []
            if issue.package_name:
                title_parts.append(f"{issue.package_name}")
            if issue.file_path:
                title_parts.append(f"{Path(issue.file_path).name}")
            if not title_parts:
                title_parts.append("security vulnerability")

            title = f"Fix {issue.severity} severity {issue.tool} issue in {' '.join(title_parts)}"

            # Create description
            description = f"{issue.title}"
            if issue.description and issue.description != issue.title:
                description += f" - {issue.description}"

            todos.append({
                'content': title,
                'description': description,
                'severity': issue.severity,
                'tool': issue.tool,
                'file_path': issue.file_path,
                'line_number': issue.line_number,
                'vulnerability_id': issue.vulnerability_id,
                'id': todo_id,
                'status': 'pending'
            })

        return todos

    def save_report(self, output_file: str, issues: Optional[List[SecurityIssue]] = None):
        """Save issues report to JSON file"""
        if issues is None:
            issues = self.issues

        report = {
            'generated_at': datetime.now().isoformat(),
            'total_issues': len(issues),
            'issues': [issue.to_dict() for issue in issues],
            'summary': {
                'by_severity': {},
                'by_tool': {}
            }
        }

        # Generate summary
        for issue in issues:
            report['summary']['by_severity'][issue.severity] = \
                report['summary']['by_severity'].get(issue.severity, 0) + 1
            report['summary']['by_tool'][issue.tool] = \
                report['summary']['by_tool'].get(issue.tool, 0) + 1

        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)

    def print_summary(self, issues: Optional[List[SecurityIssue]] = None):
        """Print a summary of issues"""
        if issues is None:
            issues = self.issues

        print(f"\n🔍 Security Issue Summary")
        print(f"==========================")
        print(f"Total issues found: {len(issues)}")

        if not issues:
            print("✅ No security issues found!")
            return

        # Group by tool and severity
        grouped = {}
        for issue in issues:
            key = f"{issue.tool} ({issue.severity})"
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(issue)

        for category, category_issues in grouped.items():
            print(f"\n{category}: {len(category_issues)} issues")
            for issue in category_issues[:5]:  # Show first 5
                print(f"  • {issue}")
            if len(category_issues) > 5:
                print(f"  ... and {len(category_issues) - 5} more")


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description="Extract security issues from scan reports")
    parser.add_argument('--reports-dir', default='reports', help='Directory containing report files')
    parser.add_argument('--min-severity', default='Medium', choices=['Low', 'Medium', 'High', 'Critical'],
                       help='Minimum severity level to include')
    parser.add_argument('--output', '-o', help='Output JSON report file')
    parser.add_argument('--generate-todos', action='store_true', help='Generate TODO items for issues')
    parser.add_argument('--bandit-file', help='Specific Bandit JSON file to parse')
    parser.add_argument('--safety-file', help='Specific Safety JSON file to parse')
    parser.add_argument('--trivy-file', help='Specific Trivy SARIF file to parse')

    args = parser.parse_args()

    extractor = SecurityIssueExtractor()

    # Extract from specific files or scan directory
    if args.bandit_file:
        extractor.issues.extend(extractor.extract_from_bandit(args.bandit_file))
    if args.safety_file:
        extractor.issues.extend(extractor.extract_from_safety(args.safety_file))
    if args.trivy_file:
        extractor.issues.extend(extractor.extract_from_trivy_sarif(args.trivy_file))
    else:
        # Scan for all reports
        extractor.extract_all_issues(args.reports_dir)

    # Filter by severity
    filtered_issues = extractor.filter_by_severity(args.min_severity)

    # Print summary
    extractor.print_summary(filtered_issues)

    # Save report if requested
    if args.output:
        extractor.save_report(args.output, filtered_issues)
        print(f"\n📄 Report saved to: {args.output}")

    # Generate TODOs if requested
    if args.generate_todos:
        todos = extractor.generate_todo_items(filtered_issues)
        todos_file = args.output.replace('.json', '_todos.json') if args.output else 'security_todos.json'

        with open(todos_file, 'w') as f:
            json.dump({
                'generated_at': datetime.now().isoformat(),
                'total_todos': len(todos),
                'todos': todos
            }, f, indent=2)

        print(f"\n📝 TODOs generated: {todos_file}")

        # Print TODO summary
        print(f"\n📋 Generated {len(todos)} TODO items:")
        for todo in todos[:10]:  # Show first 10
            print(f"  • {todo['content']}")
        if len(todos) > 10:
            print(f"  ... and {len(todos) - 10} more")


if __name__ == '__main__':
    main()
