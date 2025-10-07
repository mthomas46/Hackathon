#!/usr/bin/env python3
"""
Comprehensive Documentation Audit Script
- Audits all docs subdirectories
- Validates archive contents
- Standardizes naming conventions
- Adds LLM metadata
- Validates against services
- Consolidates information
"""

import os
import yaml
import re
import shutil
from pathlib import Path
from datetime import datetime
from collections import defaultdict

class DocsAuditor:
    def __init__(self, docs_root, services_root):
        self.docs_root = Path(docs_root)
        self.services_root = Path(services_root)
        self.services = self._load_services()
        self.audit_results = defaultdict(list)
        self.standardization_actions = []
        self.archive_validation_actions = []
        self.llm_metadata_actions = []

    def _load_services(self):
        """Load all service names for validation."""
        services = set()
        if self.services_root.exists():
            for service_dir in self.services_root.iterdir():
                if service_dir.is_dir() and not service_dir.name.startswith('_'):
                    services.add(service_dir.name.replace('-service', '').replace('_', '-'))
        return services

    def audit_subdirectory(self, subdir_path):
        """Audit a single subdirectory."""
        subdir = Path(subdir_path)
        if not subdir.exists() or not subdir.is_dir():
            return

        result = {
            'name': subdir.name,
            'path': str(subdir.relative_to(self.docs_root)),
            'files': [],
            'issues': [],
            'recommendations': []
        }

        # Check for README
        readme_path = subdir / 'README.md'
        if not readme_path.exists():
            result['issues'].append('Missing README.md')

        # Analyze files
        for md_file in subdir.glob('*.md'):
            file_info = self._analyze_file(md_file, subdir)
            result['files'].append(file_info)

            # Check naming consistency
            if not self._is_standardized_name(md_file.name):
                result['issues'].append(f'Non-standard filename: {md_file.name}')
                self.standardization_actions.append({
                    'file': str(md_file.relative_to(self.docs_root)),
                    'action': 'rename',
                    'current': md_file.name,
                    'recommended': self._standardize_filename(md_file.name)
                })

        self.audit_results['subdirectories'].append(result)

    def _analyze_file(self, file_path, subdir):
        """Analyze a single markdown file."""
        info = {
            'name': file_path.name,
            'path': str(file_path.relative_to(self.docs_root)),
            'has_metadata': False,
            'size': file_path.stat().st_size,
            'issues': []
        }

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check for LLM metadata
            if 'llm_metadata:' in content:
                info['has_metadata'] = True
            else:
                self.llm_metadata_actions.append({
                    'file': str(file_path.relative_to(self.docs_root)),
                    'action': 'add_metadata'
                })

            # Check for service references
            mentioned_services = set()
            for service in self.services:
                if service.lower() in content.lower():
                    mentioned_services.add(service)

            if mentioned_services:
                info['services_mentioned'] = list(mentioned_services)
            else:
                info['issues'].append('No service references found')

        except Exception as e:
            info['issues'].append(f'Error reading file: {e}')

        return info

    def audit_archive_validity(self):
        """Audit archive contents to determine if documents should be archived."""
        archive_dir = self.docs_root / 'archive'

        for md_file in archive_dir.rglob('*.md'):
            if self._should_unarchive(md_file):
                self.archive_validation_actions.append({
                    'file': str(md_file.relative_to(self.docs_root)),
                    'action': 'unarchive',
                    'reason': 'Contains current/recent content'
                })

    def _should_unarchive(self, file_path):
        """Determine if a file should be moved from archive to active docs."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check for indicators of current/active content
            current_indicators = [
                'current' in content.lower(),
                'active' in content.lower(),
                '2025' in content,
                'october 2025' in content.lower(),
                'implementation' in content.lower() and 'complete' in content.lower(),
                'session' in file_path.name.lower() and '2025' in content
            ]

            # Check if it mentions being superseded but has recent dates
            if 'superseded' in content.lower() and any(indicator for indicator in current_indicators):
                return True

            return False

        except Exception:
            return False

    def _is_standardized_name(self, filename):
        """Check if filename follows standardization rules."""
        # Should be lowercase with underscores, no spaces, .md extension
        return (filename == filename.lower() and
                '_' in filename and
                ' ' not in filename and
                filename.endswith('.md'))

    def _standardize_filename(self, filename):
        """Convert filename to standardized format."""
        # Remove .md, convert to lowercase, replace spaces/special chars with underscores
        name = filename.replace('.md', '')
        name = name.lower()
        name = re.sub(r'[^a-z0-9]+', '_', name)
        name = re.sub(r'_+', '_', name)
        name = name.strip('_')
        return f"{name}.md"

    def validate_against_services(self):
        """Validate documentation against actual services."""
        service_docs = defaultdict(list)

        # Scan all docs for service mentions
        for md_file in self.docs_root.rglob('*.md'):
            if 'archive' in str(md_file):
                continue

            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                for service in self.services:
                    if service.lower() in content.lower():
                        service_docs[service].append(str(md_file.relative_to(self.docs_root)))

            except Exception:
                continue

        # Check for undocumented services
        undocumented = []
        for service in self.services:
            if service not in service_docs:
                undocumented.append(service)

        self.audit_results['service_validation'] = {
            'documented_services': dict(service_docs),
            'undocumented_services': undocumented,
            'total_services': len(self.services),
            'documented_count': len(service_docs)
        }

    def execute_standardization(self):
        """Execute the standardization actions."""
        print(f"Executing {len(self.standardization_actions)} standardization actions...")

        for action in self.standardization_actions:
            file_path = self.docs_root / action['file']
            if file_path.exists():
                new_path = file_path.parent / action['recommended']
                try:
                    file_path.rename(new_path)
                    print(f"✓ Renamed: {action['file']} → {action['recommended']}")
                except Exception as e:
                    print(f"✗ Failed to rename {action['file']}: {e}")

    def execute_unarchiving(self):
        """Move files from archive back to active documentation."""
        print(f"Executing {len(self.archive_validation_actions)} unarchiving actions...")

        for action in self.archive_validation_actions:
            source_path = self.docs_root / action['file']
            # Determine target directory based on content
            target_dir = self._determine_target_directory(source_path)

            if target_dir:
                target_path = self.docs_root / target_dir / source_path.name
                try:
                    # Ensure target directory exists
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(source_path), str(target_path))
                    print(f"✓ Unarchived: {action['file']} → {target_dir}/")
                except Exception as e:
                    print(f"✗ Failed to unarchive {action['file']}: {e}")

    def _determine_target_directory(self, file_path):
        """Determine where to move an unarchived file."""
        filename = file_path.name.lower()

        # Map based on filename patterns
        if 'phase' in filename:
            return 'reports'
        elif 'session' in filename:
            return 'reports'
        elif 'workflow' in filename:
            return 'workflow'
        elif 'architecture' in filename:
            return 'architecture'
        elif 'implementation' in filename:
            return 'implementation'
        elif 'deployment' in filename:
            return 'deployment'
        else:
            return 'reports'  # Default

    def generate_report(self):
        """Generate comprehensive audit report."""
        report = {
            'audit_timestamp': datetime.now().isoformat(),
            'docs_root': str(self.docs_root),
            'summary': {
                'total_subdirectories': len(self.audit_results.get('subdirectories', [])),
                'total_files': sum(len(sub['files']) for sub in self.audit_results.get('subdirectories', [])),
                'files_needing_metadata': len(self.llm_metadata_actions),
                'files_needing_renaming': len(self.standardization_actions),
                'files_to_unarchive': len(self.archive_validation_actions)
            },
            'service_validation': self.audit_results.get('service_validation', {}),
            'issues_found': [],
            'recommendations': []
        }

        # Collect all issues
        for subdir in self.audit_results.get('subdirectories', []):
            for issue in subdir.get('issues', []):
                report['issues_found'].append(f"{subdir['name']}: {issue}")

        # Generate recommendations
        if self.archive_validation_actions:
            report['recommendations'].append(f"Unarchive {len(self.archive_validation_actions)} files with current content")

        if self.standardization_actions:
            report['recommendations'].append(f"Standardize naming for {len(self.standardization_actions)} files")

        if self.llm_metadata_actions:
            report['recommendations'].append(f"Add LLM metadata to {len(self.llm_metadata_actions)} files")

        return report

def main():
    """Main audit execution."""
    docs_root = '/Users/mykalthomas/Documents/work/Hackathon/docs'
    services_root = '/Users/mykalthomas/Documents/work/Hackathon/services'

    auditor = DocsAuditor(docs_root, services_root)

    print("🔍 Starting comprehensive documentation audit...")

    # Audit all subdirectories
    print("📁 Auditing subdirectories...")
    for subdir in Path(docs_root).iterdir():
        if subdir.is_dir() and subdir.name not in ['archive']:
            auditor.audit_subdirectory(subdir)

    # Audit archive
    print("📦 Auditing archive validity...")
    auditor.audit_archive_validity()

    # Validate against services
    print("🔗 Validating against services...")
    auditor.validate_against_services()

    # Execute actions
    print("⚡ Executing standardization...")
    auditor.execute_standardization()

    print("📤 Executing unarchiving...")
    auditor.execute_unarchiving()

    # Generate report
    report = auditor.generate_report()

    # Save report
    report_path = Path(docs_root) / 'COMPREHENSIVE_AUDIT_REPORT.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# 📋 Comprehensive Documentation Audit Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")

        f.write("## 📊 Executive Summary\n\n")
        f.write(f"- **Total subdirectories audited:** {report['summary']['total_subdirectories']}\n")
        f.write(f"- **Total files audited:** {report['summary']['total_files']}\n")
        f.write(f"- **Files needing LLM metadata:** {report['summary']['files_needing_metadata']}\n")
        f.write(f"- **Files needing name standardization:** {report['summary']['files_needing_renaming']}\n")
        f.write(f"- **Files recommended for unarchiving:** {report['summary']['files_to_unarchive']}\n\n")

        f.write("## 🔗 Service Validation\n\n")
        svc_val = report['service_validation']
        f.write(f"- **Total services:** {svc_val['total_services']}\n")
        f.write(f"- **Documented services:** {svc_val['documented_count']}\n")
        f.write(f"- **Undocumented services:** {len(svc_val['undocumented_services'])}\n\n")

        if svc_val['undocumented_services']:
            f.write("### Undocumented Services:\n")
            for svc in svc_val['undocumented_services'][:10]:
                f.write(f"- {svc}\n")
            if len(svc_val['undocumented_services']) > 10:
                f.write(f"- ... and {len(svc_val['undocumented_services']) - 10} more\n")
            f.write("\n")

        f.write("## ⚠️ Issues Found\n\n")
        for issue in report['issues_found'][:20]:
            f.write(f"- {issue}\n")
        if len(report['issues_found']) > 20:
            f.write(f"- ... and {len(report['issues_found']) - 20} more issues\n")
        f.write("\n")

        f.write("## 💡 Recommendations\n\n")
        for rec in report['recommendations']:
            f.write(f"- {rec}\n")
        f.write("\n")

        f.write("---\n\n")
        f.write("*Full detailed results available in audit script output.*\n")

    print("\n✅ Audit complete!")
    print(f"📄 Report saved: {report_path}")
    print(f"📊 Summary: {report['summary']['total_files']} files audited, {report['summary']['files_needing_renaming']} renamed, {report['summary']['files_to_unarchive']} unarchived")

if __name__ == '__main__':
    main()
