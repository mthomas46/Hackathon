#!/usr/bin/env python3
"""
DEMONSTRATION: Configurable Human-Readable Reporting

This demo shows how to use the configurable reporting system
to generate different types of reports from analysis results.
"""

import asyncio
import json
from pathlib import Path

def demo_reporting_presets():
    """Demonstrate different reporting presets."""

    print("🎭 CONFIGURABLE REPORTING SYSTEM DEMONSTRATION")
    print("=" * 60)

    presets = {
        'minimal': {
            'description': 'JSON results only',
            'output': 'comprehensive_pr_analysis_results.json only',
            'use_case': 'API integrations, automated systems'
        },

        'developer_focus': {
            'description': 'Technical details for developers',
            'output': 'developer-focused markdown reports',
            'use_case': 'Code reviews, technical assessments'
        },

        'management_focus': {
            'description': 'Business-focused for managers',
            'output': 'project manager markdown reports',
            'use_case': 'Project planning, stakeholder updates'
        },

        'comprehensive': {
            'description': 'Full reports for all stakeholders',
            'output': 'developer + manager reports in markdown + HTML',
            'use_case': 'Complete documentation, multiple audiences'
        },

        'enterprise': {
            'description': 'Enterprise-grade reporting',
            'output': 'All perspectives in markdown, HTML, and JSON',
            'use_case': 'Enterprise deployments, compliance reporting'
        }
    }

    print("\\n📋 AVAILABLE REPORTING PRESETS:")
    print("-" * 40)

    for name, config in presets.items():
        print(f"\\n🔸 {name.upper()}")
        print(f"   Description: {config['description']}")
        print(f"   Output: {config['output']}")
        print(f"   Use Case: {config['use_case']}")

def show_usage_examples():
    """Show practical usage examples."""

    print("\\n\\n📚 PRACTICAL USAGE EXAMPLES:")
    print("=" * 40)

    examples = [
        ("Run comprehensive analysis with default reporting",
         "python test_comprehensive_with_reporting.py"),

        ("Run analysis with specific reporting preset",
         "python test_comprehensive_with_reporting.py --preset developer_focus"),

        ("Run interactive demo of all presets",
         "python test_comprehensive_with_reporting.py --interactive"),

        ("Generate reports from existing results",
         "python generate_reports.py comprehensive_pr_analysis_results.json"),

        ("Generate specific preset reports",
         "python generate_reports.py comprehensive_pr_analysis_results.json --preset management_focus"),

        ("List all available presets",
         "python generate_reports.py --list-presets"),

        ("Use custom output directory",
         "python test_comprehensive_with_reporting.py --output-dir ./my_reports")
    ]

    for i, (description, command) in enumerate(examples, 1):
        print(f"\\n{i}. {description}")
        print(f"   ```bash\\n   {command}\\n   ```")

def demonstrate_workflow_integration():
    """Show how reporting integrates into workflows."""

    print("\\n\\n🔄 WORKFLOW INTEGRATION EXAMPLES:")
    print("=" * 40)

    integration_examples = [
        ("CI/CD Pipeline Integration",
         """# In your CI/CD pipeline
name: PR Analysis
on: pull_request

jobs:
  analyze:
    steps:
      - uses: actions/checkout@v2
      - name: Run PR Analysis
        run: |
          python test_comprehensive_with_reporting.py --preset developer_focus
      - name: Upload Reports
        uses: actions/upload-artifact@v2
        with:
          name: pr-analysis-reports
          path: reports/"""),

        ("GitHub Actions Integration",
         """# .github/workflows/pr-analysis.yml
name: PR Analysis & Reporting

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  analysis:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run Analysis with Developer Focus
        run: python test_comprehensive_with_reporting.py --preset developer_focus

      - name: Comment on PR
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const report = fs.readFileSync('reports/developer/pr_analysis_developer_focus.md', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '## 🤖 PR Analysis Results\\n\\n' + report
            });"""),

        ("API Integration",
         """# Integrate with your existing API
from services.shared.reporting.human_readable_report_generator import HumanReadableReportGenerator

def analyze_and_report(pr_data, preset='comprehensive'):
    # Run your analysis
    analysis_results = run_pr_analysis(pr_data)

    # Generate human-readable reports
    generator = HumanReadableReportGenerator()
    report_metadata = generator.generate_report(
        analysis_results=analysis_results,
        workflow_type='pr_analysis',
        output_format='markdown'
    )

    # Return both structured data and readable reports
    return {
        'analysis_results': analysis_results,
        'reports': report_metadata['files_generated']
    }""")
    ]

    for title, code in integration_examples:
        print(f"\\n🔸 {title}:")
        print("-" * 40)
        print(code)

def show_configuration_options():
    """Show configuration customization options."""

    print("\\n\\n⚙️  CONFIGURATION CUSTOMIZATION:")
    print("=" * 40)

    config_options = {
        "Perspectives": [
            "developer - Technical details and implementation notes",
            "project_manager - Business impact and project status",
            "executive - High-level strategic overview"
        ],

        "Output Formats": [
            "markdown - GitHub-friendly readable format",
            "html - Web-ready with styling",
            "json - Structured data for integrations"
        ],

        "Customization Options": [
            "output_dir - Where to save generated reports",
            "include_metadata - Add technical metadata",
            "include_performance_metrics - Add timing data",
            "auto_generate_filename - Automatic naming",
            "filename_pattern - Custom naming patterns"
        ]
    }

    for category, options in config_options.items():
        print(f"\\n🔧 {category}:")
        for option in options:
            print(f"   • {option}")

def run_demo():
    """Run the complete demonstration."""

    demo_reporting_presets()
    show_usage_examples()
    demonstrate_workflow_integration()
    show_configuration_options()

    print("\\n" + "="*60)
    print("🎯 READY TO GET STARTED?")
    print("="*60)
    print("\\n🚀 Try these commands:")
    print("   python test_comprehensive_with_reporting.py --interactive")
    print("   python generate_reports.py --list-presets")
    print("   python test_comprehensive_with_reporting.py --preset developer_focus")
    print("\\n📂 Reports will be saved in the 'test_reports/' directory")

if __name__ == "__main__":
    run_demo()
