#!/usr/bin/env python3
"""
Comprehensive Accuracy & Cohesion Audit Script

Audits all 5 generated reports for:
1. Data accuracy and consistency
2. Cross-report cohesion
3. Missing information
4. Enhancement opportunities
5. New report recommendations
"""

import json
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any


class ReportAuditor:
    """Comprehensive report auditor."""
    
    def __init__(self, demo_folder: str):
        self.demo_folder = Path(demo_folder)
        self.reports_folder = self.demo_folder / "reports"
        self.data_file = self.demo_folder / "data" / "mock_data.json"
        
        # Load mock data
        with open(self.data_file) as f:
            self.mock_data = json.load(f)
        
        # Load all reports
        self.reports = {}
        for report_file in self.reports_folder.glob("*.md"):
            with open(report_file) as f:
                self.reports[report_file.stem] = f.read()
        
        # Initialize findings
        self.findings = {
            "accuracy": [],
            "consistency": [],
            "cohesion": [],
            "enhancements": [],
            "missing_info": []
        }
    
    def extract_metrics_from_text(self, text: str) -> Dict[str, Any]:
        """Extract key metrics from report text."""
        metrics = {}
        
        # Team size
        team_match = re.search(r'(\d+)\s+team members', text, re.I)
        if team_match:
            metrics['team_size'] = int(team_match.group(1))
        
        # Users extracted
        users_match = re.search(r'(\d+)\s+unique users', text, re.I)
        if users_match:
            metrics['users_extracted'] = int(users_match.group(1))
        
        # Documents
        docs_match = re.search(r'(\d+)\s+documents', text, re.I)
        if docs_match:
            metrics['documents'] = int(docs_match.group(1))
        
        # Technologies
        tech_match = re.search(r'(\d+)\s+technologies', text, re.I)
        if tech_match:
            metrics['technologies'] = int(tech_match.group(1))
        
        # Services
        services_match = re.search(r'(\d+)\s+services', text, re.I)
        if services_match:
            metrics['services'] = int(services_match.group(1))
        
        # SMEs
        sme_match = re.search(r'(\d+)\s+subject matter experts', text, re.I)
        if sme_match:
            metrics['smes'] = int(sme_match.group(1))
        
        return metrics
    
    def audit_accuracy(self):
        """Audit data accuracy against source data."""
        print("\n🔍 AUDITING ACCURACY...")
        
        # Ground truth from mock data
        truth = {
            'team_size': len(self.mock_data.get('team_members', [])),
            'jira_tickets': len(self.mock_data.get('jira_tickets', [])),
            'github_prs': len(self.mock_data.get('github_prs', [])),
            'confluence_docs': len(self.mock_data.get('confluence_docs', [])),
            'total_docs': len(self.mock_data.get('jira_tickets', [])) + 
                         len(self.mock_data.get('github_prs', [])) + 
                         len(self.mock_data.get('confluence_docs', [])),
            'technologies': len(self.mock_data.get('tech_stack', [])),
            'services_discovered': len(self.mock_data.get('services_discovered', []))
        }
        
        print(f"\n📊 Ground Truth:")
        for key, value in truth.items():
            print(f"   • {key}: {value}")
        
        # Check each report
        for report_name, report_text in self.reports.items():
            metrics = self.extract_metrics_from_text(report_text)
            
            # Compare
            for key in ['team_size', 'technologies']:
                if key in metrics and key in truth:
                    if metrics[key] == truth[key]:
                        self.findings['accuracy'].append({
                            'report': report_name,
                            'metric': key,
                            'status': '✅ ACCURATE',
                            'expected': truth[key],
                            'actual': metrics[key]
                        })
                    else:
                        self.findings['accuracy'].append({
                            'report': report_name,
                            'metric': key,
                            'status': '❌ INACCURATE',
                            'expected': truth[key],
                            'actual': metrics[key]
                        })
        
        return truth
    
    def audit_consistency(self):
        """Audit consistency across reports."""
        print("\n🔍 AUDITING CROSS-REPORT CONSISTENCY...")
        
        # Extract metrics from all reports
        all_metrics = {}
        for report_name, report_text in self.reports.items():
            all_metrics[report_name] = self.extract_metrics_from_text(report_text)
        
        # Check consistency
        keys_to_check = ['team_size', 'users_extracted', 'technologies', 'services', 'smes']
        
        for key in keys_to_check:
            values = {}
            for report_name, metrics in all_metrics.items():
                if key in metrics:
                    values[report_name] = metrics[key]
            
            if values:
                unique_values = set(values.values())
                if len(unique_values) == 1:
                    self.findings['consistency'].append({
                        'metric': key,
                        'status': '✅ CONSISTENT',
                        'value': list(unique_values)[0],
                        'reports': list(values.keys())
                    })
                else:
                    self.findings['consistency'].append({
                        'metric': key,
                        'status': '⚠️ INCONSISTENT',
                        'values': values
                    })
    
    def audit_cohesion(self):
        """Audit narrative flow and cohesion."""
        print("\n🔍 AUDITING NARRATIVE COHESION...")
        
        # Check for cross-references
        report_names = list(self.reports.keys())
        
        for report_name, report_text in self.reports.items():
            cross_refs = []
            for other_report in report_names:
                if other_report != report_name:
                    # Look for references to other reports
                    if other_report.replace('_', ' ') in report_text.lower():
                        cross_refs.append(other_report)
            
            self.findings['cohesion'].append({
                'report': report_name,
                'cross_references': cross_refs,
                'status': '✅ WELL LINKED' if cross_refs else '⚠️ ISOLATED'
            })
        
        # Check for README integration
        readme_path = self.demo_folder / "README.md"
        if readme_path.exists():
            with open(readme_path) as f:
                readme_text = f.read()
            
            links_to_reports = sum(1 for report_name in report_names 
                                  if report_name in readme_text)
            
            self.findings['cohesion'].append({
                'component': 'README',
                'links': links_to_reports,
                'total_reports': len(report_names),
                'status': '✅ COMPLETE' if links_to_reports == len(report_names) else '⚠️ INCOMPLETE'
            })
    
    def identify_enhancements(self):
        """Identify enhancement opportunities."""
        print("\n🔍 IDENTIFYING ENHANCEMENT OPPORTUNITIES...")
        
        # Check for visual elements
        for report_name, report_text in self.reports.items():
            visual_count = report_text.count('```') + report_text.count('│') + report_text.count('█')
            
            self.findings['enhancements'].append({
                'report': report_name,
                'metric': 'visual_richness',
                'count': visual_count,
                'status': '✅ RICH' if visual_count > 50 else '⚠️ LIMITED',
                'recommendation': 'Add more diagrams' if visual_count < 50 else 'Excellent'
            })
        
        # Check for workflow references
        for report_name, report_text in self.reports.items():
            workflow_mentions = {
                'Workflow A': 'Workflow A' in report_text,
                'Workflow B': 'Workflow B' in report_text,
                'Workflow C': 'Workflow C' in report_text,
                'Workflow D': 'Workflow D' in report_text,
                'Workflow E': 'Workflow E' in report_text,
                'Workflow F': 'Workflow F' in report_text
            }
            
            mentioned = [k for k, v in workflow_mentions.items() if v]
            
            if len(mentioned) < 3:
                self.findings['enhancements'].append({
                    'report': report_name,
                    'issue': 'Limited workflow coverage',
                    'mentioned': mentioned,
                    'recommendation': 'Add more workflow context'
                })
    
    def identify_missing_info(self):
        """Identify missing information."""
        print("\n🔍 IDENTIFYING MISSING INFORMATION...")
        
        # Expected sections by report
        expected_sections = {
            'Planning_Service_Report': [
                'Executive Summary',
                'Timeline',
                'Story Points',
                'Risk Analysis',
                'SME',
                'Section 10'
            ],
            'Behind_the_Scenes_Report': [
                'Mock Data',
                'Workflow',
                'User Intelligence',
                'Section 11',
                'Extraction Statistics',
                'SME Scoring'
            ],
            'User_and_Team_Report': [
                'Team Members',
                'Skill Matrix',
                'Collaboration',
                'Training'
            ],
            'Ecosystem_Validation_Report': [
                'Service Validation',
                'Database Operations',
                'Module Imports'
            ],
            'Data_Architecture_Report': [
                'Data Stores',
                'Schema',
                'User Intelligence',
                'Section 7'
            ]
        }
        
        for report_name, sections in expected_sections.items():
            if report_name in self.reports:
                report_text = self.reports[report_name]
                missing = []
                for section in sections:
                    if section not in report_text:
                        missing.append(section)
                
                if missing:
                    self.findings['missing_info'].append({
                        'report': report_name,
                        'missing_sections': missing,
                        'status': '⚠️ INCOMPLETE'
                    })
    
    def recommend_new_report(self) -> Dict[str, Any]:
        """Recommend a new report type."""
        print("\n💡 GENERATING NEW REPORT RECOMMENDATION...")
        
        # Analyze gaps
        current_perspectives = {
            'Planning_Service_Report': 'Business/Stakeholder',
            'Behind_the_Scenes_Report': 'Technical Implementation',
            'User_and_Team_Report': 'Team Lead/HR',
            'Ecosystem_Validation_Report': 'QA/DevOps',
            'Data_Architecture_Report': 'Data Engineer/Architect'
        }
        
        # Missing perspectives
        missing_perspectives = [
            'End User/Customer Experience',
            'Security & Compliance',
            'Cost & Resource Analysis',
            'Change Management & Training',
            'Executive Dashboard (C-level)'
        ]
        
        # Recommend based on Workflow F and SME data
        recommendation = {
            'title': 'Executive Dashboard Report',
            'subtitle': 'C-Level Decision-Making Summary',
            'target_audience': 'C-suite, VPs, Directors',
            'why_needed': 'Current reports are too detailed for executives. Need high-level metrics.',
            'key_sections': [
                '1. One-Page Executive Summary',
                '2. ROI Analysis (cost, time, risk reduction)',
                '3. Team Readiness Score',
                '4. Technology Risk Heat Map (from Planning Report)',
                '5. Key Decision Points',
                '6. Go/No-Go Recommendation',
                '7. Alternative Scenarios (if team lacks skills)',
                '8. Expert Availability (from Workflow F)',
                '9. Competitive Timeline Comparison',
                '10. Budget vs. Reality Check'
            ],
            'estimated_length': '3-5 pages (vs current 10-40 pages)',
            'unique_value': 'Distills 121,037 chars across 5 reports into 3 pages for decision-makers',
            'data_sources': [
                'Workflow A-F results',
                'SME data from Workflow F',
                'Risk analysis from Planning Report',
                'Team skill gaps from User & Team Report',
                'Architecture complexity from Data Architecture Report'
            ],
            'key_metrics': [
                'Project Confidence Score (0-100%)',
                'Team Readiness Score (0-100%)',
                'Expert Availability Score (0-100%)',
                'Technology Risk Level (LOW/MEDIUM/HIGH)',
                'Estimated ROI (%)',
                'Time to Market (weeks)',
                'Budget Required vs. Available',
                'Go/No-Go Confidence (%)'
            ]
        }
        
        return recommendation
    
    def generate_report(self):
        """Generate comprehensive audit report."""
        print("\n" + "="*80)
        print(" " * 15 + "📊 COMPREHENSIVE ACCURACY & COHESION AUDIT")
        print("="*80)
        
        # Run all audits
        truth = self.audit_accuracy()
        self.audit_consistency()
        self.audit_cohesion()
        self.identify_enhancements()
        self.identify_missing_info()
        new_report_idea = self.recommend_new_report()
        
        # Print summary
        print("\n" + "="*80)
        print("AUDIT SUMMARY")
        print("="*80)
        
        print(f"\n📊 GROUND TRUTH:")
        print(f"   Team Size: {truth['team_size']}")
        print(f"   Total Documents: {truth['total_docs']}")
        print(f"   Technologies: {truth['technologies']}")
        print(f"   Services Discovered: {truth['services_discovered']}")
        
        print(f"\n✅ ACCURACY: {len([f for f in self.findings['accuracy'] if '✅' in f['status']])} accurate")
        print(f"❌ INACCURACIES: {len([f for f in self.findings['accuracy'] if '❌' in f['status']])}")
        
        print(f"\n✅ CONSISTENCY: {len([f for f in self.findings['consistency'] if '✅' in f['status']])} consistent metrics")
        print(f"⚠️  INCONSISTENCIES: {len([f for f in self.findings['consistency'] if '⚠️' in f['status']])}")
        
        print(f"\n✅ COHESION: {len([f for f in self.findings['cohesion'] if '✅' in f.get('status', '')])} well-linked components")
        print(f"⚠️  WEAK LINKS: {len([f for f in self.findings['cohesion'] if '⚠️' in f.get('status', '')])}")
        
        print(f"\n💡 ENHANCEMENTS IDENTIFIED: {len(self.findings['enhancements'])}")
        print(f"📋 MISSING INFO: {len(self.findings['missing_info'])}")
        
        print("\n" + "="*80)
        print("🚀 NEW REPORT RECOMMENDATION")
        print("="*80)
        print(f"\n📄 Title: {new_report_idea['title']}")
        print(f"🎯 Subtitle: {new_report_idea['subtitle']}")
        print(f"👥 Audience: {new_report_idea['target_audience']}")
        print(f"\n💡 Why Needed:")
        print(f"   {new_report_idea['why_needed']}")
        print(f"\n📏 Length: {new_report_idea['estimated_length']}")
        print(f"💎 Unique Value: {new_report_idea['unique_value']}")
        
        print("\n📊 Key Sections:")
        for section in new_report_idea['key_sections']:
            print(f"   {section}")
        
        print("\n🎯 Key Metrics:")
        for metric in new_report_idea['key_metrics']:
            print(f"   • {metric}")
        
        print("\n" + "="*80)
        
        return {
            'ground_truth': truth,
            'findings': self.findings,
            'new_report_idea': new_report_idea
        }


def main():
    auditor = ReportAuditor("accuracy_audit_demo")
    results = auditor.generate_report()
    
    # Save detailed findings
    output_file = "COMPREHENSIVE_ACCURACY_AUDIT_REPORT.md"
    
    with open(output_file, 'w') as f:
        f.write("# Comprehensive Accuracy & Cohesion Audit Report\n\n")
        f.write("**Date:** 2025-10-04\n")
        f.write("**Demo:** accuracy_audit_demo\n")
        f.write("**Reports Audited:** 5\n\n")
        f.write("---\n\n")
        
        # Ground Truth
        f.write("## 📊 Ground Truth (Source Data)\n\n")
        f.write("```\n")
        for key, value in results['ground_truth'].items():
            f.write(f"{key:.<40} {value}\n")
        f.write("```\n\n")
        
        # Accuracy Findings
        f.write("## ✅ Accuracy Audit\n\n")
        for finding in results['findings']['accuracy']:
            f.write(f"- {finding['status']} **{finding['report']}** - {finding['metric']}: ")
            f.write(f"Expected {finding['expected']}, Got {finding['actual']}\n")
        f.write("\n")
        
        # Consistency Findings
        f.write("## 🔗 Consistency Audit\n\n")
        for finding in results['findings']['consistency']:
            f.write(f"- {finding['status']} **{finding['metric']}**\n")
            if 'value' in finding:
                f.write(f"  - Consistent value: {finding['value']} across {len(finding['reports'])} reports\n")
            else:
                f.write(f"  - Inconsistent values: {finding['values']}\n")
        f.write("\n")
        
        # Cohesion Findings
        f.write("## 🌐 Cohesion Audit\n\n")
        for finding in results['findings']['cohesion']:
            if 'report' in finding:
                f.write(f"- {finding['status']} **{finding['report']}**\n")
                f.write(f"  - Cross-references: {', '.join(finding['cross_references']) if finding['cross_references'] else 'None'}\n")
            else:
                f.write(f"- {finding['status']} **{finding['component']}**: {finding['links']}/{finding['total_reports']} reports linked\n")
        f.write("\n")
        
        # Enhancement Opportunities
        f.write("## 💡 Enhancement Opportunities\n\n")
        for finding in results['findings']['enhancements']:
            if 'metric' in finding:
                f.write(f"- **{finding['report']}** - {finding['metric']}: {finding['status']}\n")
                f.write(f"  - Recommendation: {finding['recommendation']}\n")
            elif 'issue' in finding:
                f.write(f"- **{finding['report']}** - {finding['issue']}\n")
                f.write(f"  - Current: {', '.join(finding['mentioned'])}\n")
                f.write(f"  - Recommendation: {finding['recommendation']}\n")
        f.write("\n")
        
        # Missing Information
        f.write("## 📋 Missing Information\n\n")
        if results['findings']['missing_info']:
            for finding in results['findings']['missing_info']:
                f.write(f"- {finding['status']} **{finding['report']}**\n")
                f.write(f"  - Missing: {', '.join(finding['missing_sections'])}\n")
        else:
            f.write("✅ All expected sections present in all reports!\n")
        f.write("\n")
        
        # New Report Recommendation
        idea = results['new_report_idea']
        f.write("## 🚀 NEW REPORT RECOMMENDATION\n\n")
        f.write(f"### {idea['title']}\n")
        f.write(f"**{idea['subtitle']}**\n\n")
        f.write(f"**Target Audience:** {idea['target_audience']}\n\n")
        f.write(f"**Why Needed:** {idea['why_needed']}\n\n")
        f.write(f"**Estimated Length:** {idea['estimated_length']}\n\n")
        f.write(f"**Unique Value:** {idea['unique_value']}\n\n")
        
        f.write("#### Key Sections\n\n")
        for section in idea['key_sections']:
            f.write(f"{section}\n")
        f.write("\n")
        
        f.write("#### Key Metrics\n\n")
        for metric in idea['key_metrics']:
            f.write(f"- {metric}\n")
        f.write("\n")
        
        f.write("#### Data Sources\n\n")
        for source in idea['data_sources']:
            f.write(f"- {source}\n")
        f.write("\n")
    
    print(f"\n✅ Detailed audit saved to: {output_file}")


if __name__ == "__main__":
    main()

