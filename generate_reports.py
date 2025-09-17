#!/usr/bin/env python3
"""
Report Generation Utility

Generate human-readable reports from existing analysis results.
Can be used to re-generate reports with different configurations
or create reports from saved analysis data.
"""

import json
import yaml
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add the services path for imports
import sys
sys.path.append(str(Path(__file__).parent / "services" / "shared"))

from services.shared.reporting.human_readable_report_generator import HumanReadableReportGenerator

def load_config(config_file: str) -> Dict[str, Any]:
    """Load reporting configuration from YAML file."""
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)

def load_analysis_results(results_file: str) -> Dict[str, Any]:
    """Load analysis results from JSON file."""
    with open(results_file, 'r') as f:
        return json.load(f)

def generate_reports_from_config(analysis_results: Dict[str, Any],
                               config: Dict[str, Any],
                               preset_name: str = None) -> List[Dict[str, Any]]:
    """
    Generate reports based on configuration.

    Args:
        analysis_results: The analysis results to report on
        config: Reporting configuration
        preset_name: Specific preset to use (optional)

    Returns:
        List of generated report metadata
    """

    generated_reports = []

    # Determine which presets to use
    if preset_name:
        presets_to_use = [preset_name]
    else:
        presets_to_use = list(config['reporting']['presets'].keys())

    print(f"🎯 Generating reports for presets: {presets_to_use}")

    for preset in presets_to_use:
        if preset not in config['reporting']['presets']:
            print(f"⚠️  Skipping unknown preset: {preset}")
            continue

        preset_config = config['reporting']['presets'][preset]

        if not preset_config.get('generate_human_readable', False):
            print(f"⏭️  Skipping preset '{preset}' (human-readable reports disabled)")
            continue

        print(f"\\n📝 Generating reports for preset: {preset}")
        print(f"   Description: {preset_config.get('description', 'N/A')}")

        # Initialize report generator with preset configuration
        output_dir = preset_config.get('output_dir', f'reports/{preset}')
        perspectives = preset_config.get('perspectives', ['developer', 'project_manager'])
        output_formats = preset_config.get('output_formats', ['markdown'])

        report_generator = HumanReadableReportGenerator(
            output_dir=output_dir,
            include_perspectives=perspectives
        )

        # Generate reports for each output format
        for fmt in output_formats:
            try:
                report_metadata = report_generator.generate_report(
                    analysis_results=analysis_results,
                    workflow_type="pr_analysis",
                    output_format=fmt,
                    filename=f"pr_analysis_{preset}"
                )

                generated_reports.append(report_metadata)
                print(f"   ✅ Generated {fmt.upper()} report")

                # Show file paths
                for file_fmt, filepath in report_metadata.get('files_generated', {}).items():
                    print(f"      📄 {filepath}")

            except Exception as e:
                print(f"   ❌ Failed to generate {fmt.upper()} report: {e}")

    return generated_reports

def display_available_presets(config: Dict[str, Any]):
    """Display all available reporting presets."""

    print("📋 AVAILABLE REPORTING PRESETS")
    print("=" * 50)

    presets = config['reporting']['presets']
    for name, preset_config in presets.items():
        print(f"\\n🔸 {name.upper()}")
        print(f"   Description: {preset_config.get('description', 'N/A')}")

        if preset_config.get('generate_human_readable', False):
            perspectives = preset_config.get('perspectives', [])
            formats = preset_config.get('output_formats', [])
            output_dir = preset_config.get('output_dir', 'reports')

            print(f"   Perspectives: {', '.join(perspectives) if perspectives else 'None'}")
            print(f"   Formats: {', '.join(formats) if formats else 'None'}")
            print(f"   Output Dir: {output_dir}")
        else:
            print("   Status: Disabled (JSON results only)")

    print(f"\\n🎯 Default Preset: {config['reporting'].get('default_preset', 'comprehensive')}")

def show_usage_examples():
    """Show usage examples for the report generator."""

    print("\\n📚 USAGE EXAMPLES")
    print("=" * 30)

    examples = [
        "# Generate reports using default preset",
        "python generate_reports.py results.json",

        "# Generate reports for specific preset",
        "python generate_reports.py results.json --preset developer_focus",

        "# Generate reports for multiple presets",
        "python generate_reports.py results.json --preset developer_focus management_focus",

        "# Use custom config file",
        "python generate_reports.py results.json --config my_config.yaml",

        "# List all available presets",
        "python generate_reports.py --list-presets",

        "# Show help",
        "python generate_reports.py --help"
    ]

    for example in examples:
        if example.startswith("#"):
            print(f"\\n{example}")
        else:
            print(f"   {example}")

def main():
    """Main entry point for the report generation utility."""

    parser = argparse.ArgumentParser(
        description='Generate human-readable reports from analysis results',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_reports.py results.json
  python generate_reports.py results.json --preset developer_focus
  python generate_reports.py results.json --list-presets
        """
    )

    parser.add_argument('results_file', nargs='?', help='Analysis results JSON file')
    parser.add_argument('--config', default='config/reporting_config.yaml',
                       help='Reporting configuration YAML file')
    parser.add_argument('--preset', action='append',
                       help='Specific preset(s) to use (can be used multiple times)')
    parser.add_argument('--list-presets', action='store_true',
                       help='List all available presets and exit')
    parser.add_argument('--output-dir', help='Override output directory for all reports')

    args = parser.parse_args()

    # Load configuration
    try:
        config = load_config(args.config)
    except FileNotFoundError:
        print(f"❌ Configuration file not found: {args.config}")
        return 1
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        return 1

    # Handle preset listing
    if args.list_presets:
        display_available_presets(config)
        show_usage_examples()
        return 0

    # Require results file for generation
    if not args.results_file:
        print("❌ Results file is required for report generation")
        print("   Use --help for usage examples")
        return 1

    # Load analysis results
    try:
        analysis_results = load_analysis_results(args.results_file)
    except FileNotFoundError:
        print(f"❌ Results file not found: {args.results_file}")
        return 1
    except Exception as e:
        print(f"❌ Error loading results: {e}")
        return 1

    # Override output directory if specified
    if args.output_dir:
        for preset_config in config['reporting']['presets'].values():
            if isinstance(preset_config, dict):
                preset_config['output_dir'] = args.output_dir

    print("🎭 HUMAN-READABLE REPORT GENERATOR")
    print("=" * 40)
    print(f"📄 Results File: {args.results_file}")
    print(f"⚙️  Config File: {args.config}")

    # Determine presets to use
    presets_to_use = args.preset if args.preset else None

    if presets_to_use:
        print(f"🎯 Target Presets: {', '.join(presets_to_use)}")
    else:
        default_preset = config['reporting'].get('default_preset', 'comprehensive')
        print(f"🎯 Using Default Preset: {default_preset}")
        presets_to_use = [default_preset]

    # Generate reports
    try:
        generated_reports = generate_reports_from_config(
            analysis_results=analysis_results,
            config=config,
            preset_name=None if len(presets_to_use) > 1 else presets_to_use[0]
        )

        # Summary
        print(f"\\n🎉 REPORT GENERATION COMPLETE!")
        print("=" * 40)
        print(f"📊 Total Reports Generated: {len(generated_reports)}")

        if generated_reports:
            print("\\n📂 Generated Files:")
            for i, report in enumerate(generated_reports, 1):
                print(f"   {i}. {report.get('workflow_type', 'Unknown')} report:")
                for fmt, filepath in report.get('files_generated', {}).items():
                    print(f"      📄 {fmt.upper()}: {filepath}")

        return 0

    except Exception as e:
        print(f"❌ Report generation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
