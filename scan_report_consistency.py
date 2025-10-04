#!/usr/bin/env python3
"""Report Consistency Scanner

Scans all generated reports for inconsistencies, contradictions, and quality issues.
"""

import os
import re
import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple

class ReportConsistencyScanner:
    def __init__(self, demo_folder: str):
        self.demo_folder = Path(demo_folder)
        self.reports_folder = self.demo_folder / "reports"
        self.mock_data_file = self.demo_folder / "data" / "mock_data.json"
        
        self.ground_truth = {}
        self.extracted_metrics = defaultdict(dict)
        self.issues = []
        
    def load_ground_truth(self):
        """Load mock data as ground truth"""
        if self.mock_data_file.exists():
            with open(self.mock_data_file, 'r') as f:
                data = json.load(f)
                
            self.ground_truth = {
                'team_members': len(data.get('team_members', [])),
                'jira_tickets': len(data.get('jira_tickets', [])),
                'confluence_docs': len(data.get('confluence_docs', [])),
                'github_prs': len(data.get('github_prs', [])),
                'total_documents': len(data.get('jira_tickets', [])) + 
                                 len(data.get('confluence_docs', [])) + 
                                 len(data.get('github_prs', [])),
                'technologies': len(data.get('tech_stack', [])),
                'tech_stack': data.get('tech_stack', []),
            }
    
    def extract_metrics_from_report(self, report_name: str, content: str):
        """Extract key metrics from report content"""
        metrics = {}
        
        # Users/team members
        patterns = {
            'users': [
                r'(\d+)\s+users?\s+extracted',
                r'Team size:\s+(\d+)',
                r'(\d+)\s+team\s+members?',
                r'Team Members.*?\|\s+(\d+)',  # Table format
            ],
            'documents': [
                r'(\d+)\s+(?:historical\s+)?documents?',
                r'Total documents:\s+(\d+)',
                r'from\s+(\d+)\s+documents?',  # "from 4 documents"
            ],
            'technologies': [
                r'Technologies Covered.*?\|\s*(\d+)/(\d+)',  # Table format: | **Tech Covered** | 3/3 | (MUST BE FIRST)
                r'(\d+)\s+tech\s+stack',
                r'(\d+)\s+technology\s+stack',
                r'(\d+)\s+technologies',  # Generic - put last to avoid matching "0 technologies" from gaps
            ],
            'smes': [
                r'(\d+)\s+(?:subject\s+matter\s+)?experts?',
                r'(\d+)\s+SMEs?\s+identified',
                r'SME[s]?\s+Identified.*?\|\s+(\d+)',  # Table format
            ],
            'services': [
                r'(\d+)\s+services?\s+discovered',
                r'discovered\s+(\d+)\s+services?',
                r'Services Discovered.*?\|\s+(\d+)',  # Table format
                r'(\d+)\s+ecosystem[- ]level\s+services?',
            ],
        }
        
        for metric, pattern_list in patterns.items():
            for pattern in pattern_list:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    # Take first match
                    try:
                        match = matches[0]
                        # Handle tuple from patterns like "3/3" which capture both numbers
                        if isinstance(match, tuple):
                            # For "3/3" format, take the total (second number)
                            metrics[metric] = int(match[1]) if len(match) > 1 else int(match[0])
                        else:
                            metrics[metric] = int(match)
                        break  # Found a match, move to next metric
                    except (ValueError, IndexError, TypeError):
                        pass
        
        self.extracted_metrics[report_name] = metrics
    
    def scan_all_reports(self):
        """Scan all reports in the folder"""
        if not self.reports_folder.exists():
            print(f"❌ Reports folder not found: {self.reports_folder}")
            return
        
        report_files = list(self.reports_folder.glob("*.md"))
        print(f"📄 Scanning {len(report_files)} reports...\n")
        
        for report_file in sorted(report_files):
            with open(report_file, 'r') as f:
                content = f.read()
            
            report_name = report_file.stem
            self.extract_metrics_from_report(report_name, content)
            
            print(f"✅ {report_name}:")
            for metric, value in self.extracted_metrics[report_name].items():
                print(f"   {metric}: {value}")
            print()
    
    def check_consistency(self):
        """Check for inconsistencies across reports"""
        print("\n" + "="*80)
        print("🔍 CONSISTENCY CHECK")
        print("="*80 + "\n")
        
        # Group metrics by type
        metric_values = defaultdict(list)
        for report_name, metrics in self.extracted_metrics.items():
            for metric, value in metrics.items():
                metric_values[metric].append((report_name, value))
        
        # Check each metric
        for metric, values in metric_values.items():
            unique_values = set(v for _, v in values)
            
            if len(unique_values) > 1:
                self.issues.append({
                    'type': 'inconsistency',
                    'metric': metric,
                    'severity': 'HIGH',
                    'details': f"Multiple values found: {dict(values)}"
                })
                
                print(f"❌ INCONSISTENCY: {metric}")
                for report_name, value in values:
                    print(f"   {report_name}: {value}")
                print()
            else:
                print(f"✅ CONSISTENT: {metric} = {unique_values.pop() if unique_values else 'N/A'}")
    
    def compare_to_ground_truth(self):
        """Compare extracted metrics to ground truth"""
        print("\n" + "="*80)
        print("🎯 ACCURACY CHECK (vs Ground Truth)")
        print("="*80 + "\n")
        
        print(f"Ground Truth (from mock_data.json):")
        for key, value in self.ground_truth.items():
            if key != 'tech_stack':
                print(f"   {key}: {value}")
        print()
        
        # Check if any report matches ground truth
        for metric, gt_value in self.ground_truth.items():
            if metric == 'tech_stack':
                continue  # Skip list comparison
            
            # Find all report values for this metric
            found_values = []
            for report_name, metrics in self.extracted_metrics.items():
                if metric in metrics:
                    found_values.append((report_name, metrics[metric]))
            
            if not found_values:
                print(f"⚠️  {metric}: Not found in any report")
                continue
            
            # Check if any match
            matches = [r for r, v in found_values if v == gt_value]
            if matches:
                print(f"✅ {metric}: {gt_value} (accurate in {', '.join(matches)})")
            else:
                print(f"❌ {metric}: Expected {gt_value}, found {dict(found_values)}")
                self.issues.append({
                    'type': 'inaccuracy',
                    'metric': metric,
                    'severity': 'HIGH',
                    'details': f"Expected {gt_value}, found {dict(found_values)}"
                })
    
    def check_terminology(self):
        """Check for terminology inconsistencies"""
        print("\n" + "="*80)
        print("📝 TERMINOLOGY CHECK")
        print("="*80 + "\n")
        
        # Common terms that should be consistent
        terms_to_check = {
            'workflow': ['workflow', 'work flow'],
            'datastore': ['datastore', 'data store', 'data-store'],
            'service': ['service', 'microservice'],
        }
        
        term_usage = defaultdict(lambda: defaultdict(int))
        
        for report_file in self.reports_folder.glob("*.md"):
            with open(report_file, 'r') as f:
                content = f.read().lower()
            
            report_name = report_file.stem
            for term_group, variants in terms_to_check.items():
                for variant in variants:
                    count = content.count(variant)
                    if count > 0:
                        term_usage[term_group][variant] += count
        
        # Report findings
        for term_group, variant_counts in term_usage.items():
            if len(variant_counts) > 1:
                print(f"⚠️  '{term_group}' has multiple spellings:")
                for variant, count in sorted(variant_counts.items(), key=lambda x: -x[1]):
                    print(f"   '{variant}': {count} occurrences")
                print(f"   Recommendation: Standardize on most common variant\n")
                
                self.issues.append({
                    'type': 'terminology',
                    'term': term_group,
                    'severity': 'LOW',
                    'details': f"Multiple variants: {dict(variant_counts)}"
                })
            else:
                variant = list(variant_counts.keys())[0]
                print(f"✅ '{term_group}': Consistent (using '{variant}')")
    
    def generate_report(self):
        """Generate summary report"""
        print("\n" + "="*80)
        print("📊 SUMMARY")
        print("="*80 + "\n")
        
        # Count by severity
        severity_counts = defaultdict(int)
        for issue in self.issues:
            severity_counts[issue['severity']] += 1
        
        if not self.issues:
            print("✅ NO ISSUES FOUND - All reports are consistent!")
        else:
            print(f"Total Issues: {len(self.issues)}")
            for severity in ['HIGH', 'MEDIUM', 'LOW']:
                if severity_counts[severity] > 0:
                    print(f"   {severity}: {severity_counts[severity]}")
            
            print("\n" + "-"*80)
            print("DETAILED ISSUES:")
            print("-"*80 + "\n")
            
            for i, issue in enumerate(self.issues, 1):
                print(f"{i}. [{issue['severity']}] {issue['type'].upper()}: {issue.get('metric', issue.get('term', 'N/A'))}")
                print(f"   {issue['details']}\n")
    
    def run(self):
        """Run full consistency scan"""
        print("\n" + "="*80)
        print("🔍 REPORT CONSISTENCY SCANNER")
        print("="*80)
        print(f"Demo Folder: {self.demo_folder}\n")
        
        self.load_ground_truth()
        self.scan_all_reports()
        self.check_consistency()
        self.compare_to_ground_truth()
        self.check_terminology()
        self.generate_report()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        demo_folder = sys.argv[1]
    else:
        demo_folder = "service_offline_test"
    
    scanner = ReportConsistencyScanner(demo_folder)
    scanner.run()

