#!/usr/bin/env python3
"""
CI/CD Security Integration - Hackathon Ecosystem
===============================================

Integrates security issue extraction into CI/CD pipelines.
Automatically extracts issues from security scans and creates/updates TODO items.

Features:
- Extracts issues from Bandit, Safety, and Trivy reports
- Creates structured TODO items for remediation
- Updates existing TODO files with new issues
- Generates GitHub Issues or PR comments
- Integrates with CI/CD workflows for automated security tracking

Author: Hackathon Security Framework
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import argparse
import subprocess

from security_issue_extractor import SecurityIssueExtractor


class CICDSecurityIntegration:
    """Integrates security issue extraction into CI/CD pipelines"""

    def __init__(self, workspace_dir: str = '.'):
        self.workspace_dir = Path(workspace_dir)
        self.extractor = SecurityIssueExtractor()

    def extract_and_process_issues(self,
                                  min_severity: str = 'Medium',
                                  create_github_issues: bool = False,
                                  update_todos: bool = True) -> Dict[str, Any]:
        """Extract issues and process them for CI/CD integration"""

        # Extract all issues
        all_issues = self.extractor.extract_all_issues()
        filtered_issues = self.extractor.filter_by_severity(min_severity)

        results = {
            'total_issues': len(all_issues),
            'filtered_issues': len(filtered_issues),
            'issues': [issue.to_dict() for issue in filtered_issues],
            'summary': self._generate_summary(filtered_issues),
            'todos_created': 0,
            'github_issues_created': 0
        }

        # Generate TODO items
        if update_todos:
            todos = self.extractor.generate_todo_items(filtered_issues)
            results['todos_created'] = len(todos)

            # Save TODOs to file
            todos_file = self.workspace_dir / 'security_todos.json'
            self._save_todos(todos_file, todos)

            # Update existing TODO file if it exists
            self._update_existing_todos(todos)

        # Create GitHub issues if requested
        if create_github_issues and filtered_issues:
            results['github_issues_created'] = self._create_github_issues(filtered_issues)

        return results

    def _generate_summary(self, issues: List) -> Dict[str, Any]:
        """Generate summary statistics"""
        summary = {
            'by_severity': {},
            'by_tool': {},
            'by_category': {}
        }

        for issue in issues:
            # Count by severity
            summary['by_severity'][issue.severity] = \
                summary['by_severity'].get(issue.severity, 0) + 1

            # Count by tool
            summary['by_tool'][issue.tool] = \
                summary['by_tool'].get(issue.tool, 0) + 1

            # Categorize by type
            if issue.package_name:
                summary['by_category']['dependency'] = \
                    summary['by_category'].get('dependency', 0) + 1
            elif issue.file_path:
                summary['by_category']['code'] = \
                    summary['by_category'].get('code', 0) + 1
            else:
                summary['by_category']['container'] = \
                    summary['by_category'].get('container', 0) + 1

        return summary

    def _save_todos(self, todos_file: Path, todos: List[Dict[str, Any]]):
        """Save TODO items to JSON file"""
        todos_data = {
            'generated_at': datetime.now().isoformat(),
            'total_todos': len(todos),
            'todos': todos
        }

        with open(todos_file, 'w') as f:
            json.dump(todos_data, f, indent=2)

        print(f"📝 Saved {len(todos)} TODO items to {todos_file}")

    def _update_existing_todos(self, new_todos: List[Dict[str, Any]]):
        """Update existing TODO file with new security issues"""
        # This would integrate with the existing TODO system
        # For now, we'll just print what would be updated
        print(f"🔄 Would update existing TODO system with {len(new_todos)} security issues")

        # In a real implementation, this would:
        # 1. Read existing TODO file
        # 2. Add new security TODOs
        # 3. Remove fixed TODOs
        # 4. Save updated TODO file

    def _create_github_issues(self, issues: List) -> int:
        """Create GitHub issues for security findings"""
        # This would use GitHub API to create issues
        # For now, just return count
        print(f"🐙 Would create {len(issues)} GitHub issues for security findings")
        return 0

    def generate_pr_comment(self, results: Dict[str, Any]) -> str:
        """Generate a PR comment with security findings"""
        comment = "## 🔒 Security Scan Results\n\n"

        if results['filtered_issues'] == 0:
            comment += "✅ **No security issues found!**\n\n"
            comment += "All security scans passed with no medium or higher severity issues detected.\n"
            return comment

        comment += f"⚠️ **{results['filtered_issues']} security issues found**\n\n"

        # Summary table
        summary = results['summary']
        comment += "| Severity | Count |\n|----------|-------|\n"
        for severity, count in summary['by_severity'].items():
            comment += f"| {severity} | {count} |\n"
        comment += "\n"

        # Issues by tool
        comment += "### Issues by Tool\n"
        for tool, count in summary['by_tool'].items():
            comment += f"- **{tool}**: {count} issues\n"
        comment += "\n"

        # Top issues
        todos = results.get('todos', [])
        if todos:
            comment += "### Priority Issues to Fix\n"
            for todo in todos[:5]:  # Show top 5
                comment += f"- {todo['content']}\n"
            if len(todos) > 5:
                comment += f"- ... and {len(todos) - 5} more issues\n"
            comment += "\n"

        comment += "### 📋 Next Steps\n"
        comment += "1. Review the detailed security report\n"
        comment += "2. Address high-priority issues first\n"
        comment += "3. Update dependencies to fix vulnerabilities\n"
        comment += "4. Implement security fixes in code\n\n"

        comment += "*This comment was automatically generated by the Security CI/CD Integration*"

        return comment

    def save_pr_comment(self, comment: str, filename: str = 'security_pr_comment.md'):
        """Save PR comment to file"""
        with open(filename, 'w') as f:
            f.write(comment)
        print(f"💬 PR comment saved to {filename}")


def main():
    """Main CLI interface for CI/CD integration"""
    parser = argparse.ArgumentParser(description="CI/CD Security Integration")
    parser.add_argument('--workspace', default='.', help='Workspace directory')
    parser.add_argument('--min-severity', default='Medium',
                       choices=['Low', 'Medium', 'High', 'Critical'],
                       help='Minimum severity level')
    parser.add_argument('--create-github-issues', action='store_true',
                       help='Create GitHub issues for findings')
    parser.add_argument('--pr-comment', action='store_true',
                       help='Generate PR comment with results')
    parser.add_argument('--pr-comment-file', default='security_pr_comment.md',
                       help='Filename for PR comment')
    parser.add_argument('--update-todos', action='store_true', default=True,
                       help='Update TODO items')

    args = parser.parse_args()

    integration = CICDSecurityIntegration(args.workspace)

    # Extract and process issues
    results = integration.extract_and_process_issues(
        min_severity=args.min_severity,
        create_github_issues=args.create_github_issues,
        update_todos=args.update_todos
    )

    # Print results
    print(f"\n🔍 CI/CD Security Integration Results")
    print(f"=====================================")
    print(f"Total issues found: {results['total_issues']}")
    print(f"Filtered issues (≥{args.min_severity}): {results['filtered_issues']}")
    print(f"TODOs created: {results['todos_created']}")
    print(f"GitHub issues created: {results['github_issues_created']}")

    # Generate PR comment if requested
    if args.pr_comment:
        comment = integration.generate_pr_comment(results)
        integration.save_pr_comment(comment, args.pr_comment_file)

        # Also print to stdout for CI/CD capture
        print(f"\n--- PR Comment ---")
        print(comment)

    # Set exit code based on findings
    if results['filtered_issues'] > 0:
        print(f"\n⚠️  Found {results['filtered_issues']} security issues requiring attention")
        sys.exit(1)  # Fail CI/CD if issues found
    else:
        print(f"\n✅ No security issues found!")
        sys.exit(0)


if __name__ == '__main__':
    main()
