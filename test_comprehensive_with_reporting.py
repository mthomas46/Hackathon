#!/usr/bin/env python3
"""
COMPREHENSIVE END-TO-END PR CONFIDENCE ANALYSIS TEST WITH CONFIGURABLE REPORTING

This test demonstrates the complete ecosystem working together with optional
human-readable report generation. Users can choose which reports to generate
and in which formats.
"""

import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pathlib import Path

# Import the modular report generator
import sys
from pathlib import Path as PathLib
sys.path.append(str(PathLib(__file__).parent / "services" / "shared"))

from services.shared.reporting.human_readable_report_generator import HumanReadableReportGenerator

# Import existing test components
from test_comprehensive_pr_analysis import (
    OllamaLLMClient,
    DocumentArtifact,
    PromptArtifact,
    EcosystemTestHarness
)

class ConfigurableReportingTestHarness(EcosystemTestHarness):
    """
    Enhanced test harness with configurable reporting options.
    """

    def __init__(self, reporting_config: Dict[str, Any] = None):
        super().__init__()

        # Default reporting configuration
        self.reporting_config = reporting_config or {
            'generate_human_readable': True,
            'perspectives': ['developer', 'project_manager'],
            'output_formats': ['markdown'],
            'output_dir': 'test_reports',
            'include_metadata': True,
            'include_performance_metrics': True
        }

        # Initialize report generator
        self.report_generator = HumanReadableReportGenerator(
            output_dir=self.reporting_config.get('output_dir', 'test_reports'),
            include_perspectives=self.reporting_config.get('perspectives', ['developer', 'project_manager'])
        )

        self.generated_reports = []

    async def run_comprehensive_analysis_with_reporting(self) -> Dict[str, Any]:
        """Run the complete analysis with configurable reporting."""

        print("🔬 COMPREHENSIVE ANALYSIS WITH CONFIGURABLE REPORTING")
        print("=" * 60)

        # Run the base analysis
        results = await self.run_comprehensive_analysis()

        # Generate additional reports if configured
        if self.reporting_config.get('generate_human_readable', False):
            print("\\n📝 Generating Human-Readable Reports...")

            output_formats = self.reporting_config.get('output_formats', ['markdown'])
            workflow_id = results.get('analysis_workflow', {}).get('workflow_summary', {}).get('workflow_id', 'unknown')

            for fmt in output_formats:
                try:
                    report_metadata = self.report_generator.generate_report(
                        analysis_results=results,
                        workflow_type="pr_analysis",
                        output_format=fmt,
                        filename=f"pr_analysis_{workflow_id}"
                    )

                    self.generated_reports.append(report_metadata)
                    print(f"✅ Generated {fmt.upper()} report: {list(report_metadata.get('files_generated', {}).values())}")

                except Exception as e:
                    print(f"❌ Failed to generate {fmt.upper()} report: {e}")

        # Add reporting metadata to results
        results['reporting_config'] = self.reporting_config
        results['generated_reports'] = self.generated_reports

        return results

def create_reporting_presets() -> Dict[str, Dict[str, Any]]:
    """Create predefined reporting configuration presets."""

    return {
        'minimal': {
            'generate_human_readable': False,
            'description': 'No additional reports, only JSON results'
        },

        'developer_focus': {
            'generate_human_readable': True,
            'perspectives': ['developer'],
            'output_formats': ['markdown'],
            'output_dir': 'reports/developer',
            'description': 'Developer-focused reports only'
        },

        'management_focus': {
            'generate_human_readable': True,
            'perspectives': ['project_manager'],
            'output_formats': ['markdown'],
            'output_dir': 'reports/management',
            'description': 'Project manager-focused reports only'
        },

        'comprehensive': {
            'generate_human_readable': True,
            'perspectives': ['developer', 'project_manager'],
            'output_formats': ['markdown', 'html'],
            'output_dir': 'reports/comprehensive',
            'description': 'Full reports in multiple formats'
        },

        'enterprise': {
            'generate_human_readable': True,
            'perspectives': ['developer', 'project_manager', 'executive'],
            'output_formats': ['markdown', 'html', 'json'],
            'output_dir': 'reports/enterprise',
            'include_metadata': True,
            'include_performance_metrics': True,
            'description': 'Enterprise-grade reporting with all perspectives and formats'
        }
    }

async def run_test_with_preset(preset_name: str, custom_config: Dict[str, Any] = None) -> Dict[str, Any]:
    """Run test with a specific reporting preset."""

    presets = create_reporting_presets()

    if preset_name not in presets:
        raise ValueError(f"Unknown preset: {preset_name}. Available: {list(presets.keys())}")

    # Merge preset with custom config
    config = presets[preset_name].copy()
    if custom_config:
        config.update(custom_config)

    print(f"\\n🎯 Running test with preset: {preset_name}")
    print(f"📋 Description: {config.get('description', 'N/A')}")
    print(f"📊 Configuration: {json.dumps({k: v for k, v in config.items() if k != 'description'}, indent=2)}")

    # Initialize test harness with configuration
    harness = ConfigurableReportingTestHarness(reporting_config=config)

    # Run the analysis
    results = await harness.run_comprehensive_analysis_with_reporting()

    # Display results summary
    display_results_summary(results, preset_name)

    return results

def display_results_summary(results: Dict[str, Any], preset_name: str):
    """Display a summary of the test results."""

    executive_summary = results.get('executive_summary', {})

    print(f"\\n🎉 TEST RESULTS SUMMARY ({preset_name.upper()})")
    print("=" * 50)

    print(f"📊 Confidence Score: {executive_summary.get('confidence_score', 0)}%")
    print(f"🎯 Level: {executive_summary.get('confidence_level', 'unknown').upper()}")
    print(f"✅ Recommendation: {executive_summary.get('approval_recommendation', 'unknown').replace('_', ' ').title()}")
    print(f"⏱️  Total Time: {executive_summary.get('total_analysis_time', 0):.2f}s")
    print(f"📄 Documents: {executive_summary.get('documents_analyzed', 0)}")
    print(f"🤖 LLM Requests: {results.get('llm_integration', {}).get('total_requests', 0)}")

    # Show generated reports
    generated_reports = results.get('generated_reports', [])
    if generated_reports:
        print(f"\\n📝 Generated Reports:")
        for report in generated_reports:
            for fmt, filepath in report.get('files_generated', {}).items():
                print(f"   📄 {fmt.upper()}: {filepath}")

    print(f"\\n💾 Main Results: comprehensive_pr_analysis_results.json")

async def interactive_reporting_demo():
    """Interactive demo showing different reporting options."""

    print("🎭 INTERACTIVE REPORTING CONFIGURATION DEMO")
    print("=" * 50)

    presets = create_reporting_presets()

    print("\\n📋 Available Reporting Presets:")
    for name, config in presets.items():
        print(f"   🔸 {name}: {config.get('description', 'N/A')}")

    print("\\n" + "="*50)

    # Demo each preset
    for preset_name in ['minimal', 'developer_focus', 'management_focus', 'comprehensive']:
        print(f"\\n🚀 Testing preset: {preset_name}")
        try:
            results = await run_test_with_preset(preset_name)

            # Small delay between tests
            await asyncio.sleep(1)

        except Exception as e:
            print(f"❌ Test failed for preset {preset_name}: {e}")

    print("\\n🎉 All preset tests completed!")
    print("\\n📂 Check the 'test_reports' directory for generated reports")

async def main():
    """Main test execution function."""

    import argparse

    parser = argparse.ArgumentParser(description='Run comprehensive PR analysis with configurable reporting')
    parser.add_argument('--preset', choices=['minimal', 'developer_focus', 'management_focus', 'comprehensive', 'enterprise'],
                       default='comprehensive', help='Reporting preset to use')
    parser.add_argument('--interactive', action='store_true', help='Run interactive demo of all presets')
    parser.add_argument('--output-dir', default='test_reports', help='Output directory for reports')

    args = parser.parse_args()

    # Create output directory
    Path(args.output_dir).mkdir(exist_ok=True)

    if args.interactive:
        await interactive_reporting_demo()
    else:
        # Run single preset test
        custom_config = {'output_dir': args.output_dir}
        results = await run_test_with_preset(args.preset, custom_config)

        print("\n🎯 QUICK RESULTS SUMMARY:")
        print(f"   Confidence: {results.get("executive_summary", {}).get("confidence_score", 0)}%")
        print(f"   Level: {results.get("executive_summary", {}).get("confidence_level", "unknown").upper()}")
        print(f"   Recommendation: {results.get("executive_summary", {}).get("approval_recommendation", "unknown").replace("_", " ").title()}")
        generated_reports = results.get('generated_reports', [])
        if generated_reports:
            print(f"\\n📄 Generated Reports:")
            for report in generated_reports:
                for fmt, filepath in report.get('files_generated', {}).items():
                    print(f"   • {fmt.upper()}: {filepath}")

if __name__ == "__main__":
    asyncio.run(main())
