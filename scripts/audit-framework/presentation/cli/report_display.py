#!/usr/bin/env python3
"""
Report Display Utility for Audit Framework

Displays audit reports from JSON files in various formats.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional


def display_report(service_name: str, profile: str = "strict", output_format: str = "rich", verbose: bool = False):
    """Display an audit report for a service."""
    
    # Construct the report file path
    report_file = Path("audit-results") / profile / f"audit_{service_name}.json"
    
    if not report_file.exists():
        print(f"❌ Report file not found: {report_file}")
        print(f"Available profiles: relaxed, standard, strict, ci_fast, ci_comprehensive")
        print(f"Available services: check audit-results/{profile}/ directory")
        return False
    
    # Load and parse the report
    try:
        with open(report_file, 'r') as f:
            report_data = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load report: {e}")
        return False
    
    if output_format == "json":
        print(json.dumps(report_data, indent=2, default=str))
        return True
    elif output_format == "summary":
        _display_summary(report_data)
        return True
    else:  # rich format (default)
        _display_rich_report(report_data, verbose)
        return True


def _display_rich_report(report_data: Dict[str, Any], verbose: bool = False):
    """Display a rich-formatted audit report."""
    
    print(f"📊 Audit Report for {report_data.get('service_name', 'Unknown')} ({report_data.get('profile_used', 'unknown')} profile)")
    print("=" * 80)
    print(f"Overall Score: {report_data.get('overall_score', 'N/A'):.1f}")
    print(f"Grade: {report_data.get('grade', 'N/A')}")
    print(f"Analysis Timestamp: {report_data.get('analysis_timestamp', 'N/A')}")
    print()
    
    # Display dimensions
    dimensions = report_data.get('dimensions', {})
    if dimensions:
        print("📈 Dimension Scores:")
        for dim, score in dimensions.items():
            dim_name = dim.replace('_', ' ').title()
            if score >= 80:
                status = "🟢"
            elif score >= 60:
                status = "🟡"
            else:
                status = "🔴"
            print(f"  {status} {dim_name}: {score:.1f}")
        print()
    
    # Display recommendations
    recommendations = report_data.get('recommendations', [])
    if recommendations:
        print("💡 Key Recommendations:")
        for rec in recommendations[:15]:  # Show first 15 recommendations
            print(f"  • {rec}")
        if len(recommendations) > 15:
            print(f"  ... and {len(recommendations) - 15} more")
        print()
    
    # Display critical issues
    critical_issues = report_data.get('critical_issues', [])
    if critical_issues:
        print("🚨 Critical Issues:")
        for issue in critical_issues[:10]:  # Show first 10 critical issues
            print(f"  • {issue}")
        if len(critical_issues) > 10:
            print(f"  ... and {len(critical_issues) - 10} more critical issues")
        print()
    
    # Display detailed issues if verbose
    if verbose:
        detailed_issues = report_data.get('detailed_issues', [])
        if detailed_issues:
            print("🔍 Detailed Issues:")
            # Group by severity
            critical = [i for i in detailed_issues if i.get('severity') == 'critical']
            warnings = [i for i in detailed_issues if i.get('severity') == 'warning']
            info = [i for i in detailed_issues if i.get('severity') == 'info']
            
            for severity, issues, icon in [
                ('Critical', critical, '🚨'),
                ('Warnings', warnings, '⚠️'),
                ('Info', info, 'ℹ️')
            ]:
                if issues:
                    print(f"  {icon} {severity} ({len(issues)}):")
                    for issue in issues[:5]:  # Show first 5 per severity
                        desc = issue.get('description', 'No description')
                        print(f"    • {desc}")
                        if issue.get('file_path'):
                            print(f"      📁 {issue['file_path']}")
                        if issue.get('line_number'):
                            print(f"      📍 Line {issue['line_number']}")
                    if len(issues) > 5:
                        print(f"    ... and {len(issues) - 5} more {severity.lower()}")
                    print()
    
    # Show metadata
    metadata = report_data.get('metadata', {})
    if metadata:
        service_info = metadata.get('service_info', {})
        if service_info:
            print("ℹ️  Service Information:")
            print(f"  Name: {service_info.get('name', 'N/A')}")
            print(f"  Path: {service_info.get('path', 'N/A')}")
            print(f"  Type: {service_info.get('type', 'N/A')}")
            print()
    
    # Show effort estimate
    effort_days = report_data.get('estimated_effort_days', 0)
    if effort_days > 0:
        print("⏱️  Estimated Effort to Fix:")
        print(f"  {effort_days:.1f} days of development work")
        print()


def _display_summary(report_data: Dict[str, Any]):
    """Display a concise summary of the audit report."""
    print("📋 AUDIT SUMMARY")
    print("-" * 40)
    print(f"Service: {report_data.get('service_name', 'Unknown')}")
    print(f"Score: {report_data.get('overall_score', 0):.1f}/100")
    print(f"Grade: {report_data.get('grade', 'F')}")
    
    dimensions = report_data.get('dimensions', {})
    if dimensions:
        print("Dimensions:")
        for dim, score in dimensions.items():
            print(f"  {dim}: {score:.1f}")
    
    print(f"Critical Issues: {len(report_data.get('critical_issues', []))}")
    print(f"Detailed Issues: {len(report_data.get('detailed_issues', []))}")
    print(f"Recommendations: {len(report_data.get('recommendations', []))}")
    print(f"Estimated Effort: {report_data.get('estimated_effort_days', 'Unknown')} days")


def list_available_reports(profile: str = "strict"):
    """List all available audit reports for a profile."""
    report_dir = Path("audit-results") / profile
    if not report_dir.exists():
        print(f"❌ Profile directory not found: {report_dir}")
        return
    
    reports = list(report_dir.glob("audit_*.json"))
    if not reports:
        print(f"❌ No reports found in {report_dir}")
        return
    
    print(f"📊 Available Reports ({profile} profile):")
    print("-" * 50)
    
    for report_file in sorted(reports):
        service_name = report_file.stem.replace("audit_", "")
        try:
            with open(report_file, 'r') as f:
                data = json.load(f)
            score = data.get('overall_score', 0)
            grade = data.get('grade', 'F')
            issues = len(data.get('detailed_issues', []))
            
            if score >= 80:
                icon = "🟢"
            elif score >= 60:
                icon = "🟡"
            else:
                icon = "🔴"
                
            print(f"  {icon} {service_name}: {score:.1f} ({grade}) - {issues} issues")
        except Exception as e:
            print(f"  ❓ {service_name}: Error loading report")


if __name__ == "__main__":
    # Simple CLI for testing
    if len(sys.argv) < 2:
        print("Usage: python report_display.py <service_name> [profile] [--verbose] [--summary] [--json]")
        sys.exit(1)
    
    service = sys.argv[1]
    profile = sys.argv[2] if len(sys.argv) > 2 else "strict"
    verbose = "--verbose" in sys.argv
    output_format = "json" if "--json" in sys.argv else "summary" if "--summary" in sys.argv else "rich"
    
    display_report(service, profile, output_format, verbose)
