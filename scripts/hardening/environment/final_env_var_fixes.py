#!/usr/bin/env python3
"""
Final Environment Variable Fixes

Fixes the remaining environment variable naming issues identified in the analysis.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def fix_remaining_env_var_issues():
    """
    Fix the remaining environment variable issues found in the analysis.
    """
    print("🔧 Fixing Remaining Environment Variable Issues")
    print("=" * 50)

    # Define the fixes needed based on the analysis
    fixes = [
        {
            'file': 'services/project-simulation/docker-compose.dev.yml',
            'old_var': 'PROMETHEUS_METRICS_API_PORT',
            'new_var': 'METRICS_PORT'
        },
        {
            'file': 'services/project-simulation/docker-compose.yml',
            'old_var': 'POSTGRES_DB',
            'new_var': 'DATABASE_NAME'
        },
        {
            'file': 'services/project-simulation/docker-compose.yml',
            'old_var': 'POSTGRES_USER',
            'new_var': 'DATABASE_USER'
        },
        {
            'file': 'services/project-simulation/docker-compose.yml',
            'old_var': 'POSTGRES_PASSWORD',
            'new_var': 'DATABASE_PASSWORD'
        },
        {
            'file': 'services/project-simulation/docker-compose.yml',
            'old_var': 'POSTGRES_INITDB_ARGS',
            'new_var': 'DATABASE_INITDB_ARGS'
        }
    ]

    files_modified = 0

    for fix in fixes:
        file_path = project_root / fix['file']

        if not file_path.exists():
            print(f"⚠️  File not found: {fix['file']}")
            continue

        try:
            # Read the file
            with open(file_path, 'r') as f:
                content = f.read()

            # Check if the old variable exists
            if fix['old_var'] in content:
                # Replace the variable
                new_content = content.replace(fix['old_var'], fix['new_var'])

                # Write back to file
                with open(file_path, 'w') as f:
                    f.write(new_content)

                print(f"✅ Fixed {fix['file']}: {fix['old_var']} → {fix['new_var']}")
                files_modified += 1
            else:
                print(f"ℹ️  Variable {fix['old_var']} not found in {fix['file']}")

        except Exception as e:
            print(f"❌ Error processing {fix['file']}: {e}")

    print(f"\n📊 Summary: Modified {files_modified} files")
    return files_modified


def fix_docker_compose_syntax_issues():
    """
    Fix Docker Compose syntax issues that are preventing validation.
    """
    print("\n🔧 Fixing Docker Compose Syntax Issues")
    print("=" * 45)

    # Files that failed validation
    problematic_files = [
        'docker-compose.simulation.yml',
        'docker-compose.yml',
        'docker-compose.prod.yml',
        'docker-compose.infrastructure.yml'
    ]

    files_fixed = 0

    for filename in problematic_files:
        file_path = project_root / filename

        if not file_path.exists():
            print(f"⚠️  File not found: {filename}")
            continue

        try:
            # Try to validate with docker-compose
            import subprocess
            result = subprocess.run(
                ['docker-compose', '-f', str(file_path), 'config', '--quiet'],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                print(f"❌ Syntax error in {filename}: {result.stderr[:200]}...")

                # Try to fix common issues
                with open(file_path, 'r') as f:
                    content = f.read()

                # Fix common issues
                original_content = content

                # Fix indentation issues
                lines = content.split('\n')
                fixed_lines = []

                for line in lines:
                    # Fix common YAML indentation issues
                    if line.strip().startswith('-') and not line.startswith('  '):
                        # Add proper indentation for list items
                        if any(keyword in line for keyword in ['ports:', 'volumes:', 'environment:', 'depends_on:']):
                            # This might be a parent key, not a list item
                            pass
                        else:
                            # This is likely a list item that needs indentation
                            line = '    ' + line

                    fixed_lines.append(line)

                content = '\n'.join(fixed_lines)

                # If content changed, write it back
                if content != original_content:
                    with open(file_path, 'w') as f:
                        f.write(content)
                    print(f"✅ Attempted to fix syntax in {filename}")
                    files_fixed += 1
                else:
                    print(f"ℹ️  Could not auto-fix {filename} - manual review needed")
            else:
                print(f"✅ {filename} syntax is valid")

        except subprocess.TimeoutExpired:
            print(f"⏰ Timeout validating {filename}")
        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")

    print(f"\n📊 Summary: Fixed {files_fixed} files")
    return files_fixed


def add_missing_default_networks():
    """
    Add missing default networks to Docker Compose files.
    """
    print("\n🔧 Adding Missing Default Networks")
    print("=" * 40)

    # Files that need default networks based on the validation
    files_needing_networks = [
        'docker-compose.dev.yml',
        'services/project-simulation/docker-compose.dev.yml',
        'docker-compose.yml',
        'docker-compose.infrastructure.yml',
        'services/simulation-dashboard/docker-compose.yml'
    ]

    files_modified = 0

    for filename in files_needing_networks:
        file_path = project_root / filename

        if not file_path.exists():
            print(f"⚠️  File not found: {filename}")
            continue

        try:
            import yaml

            with open(file_path, 'r') as f:
                config = yaml.safe_load(f)

            if not config:
                continue

            # Check if networks section exists and has hackathon_default
            has_default_network = False
            if 'networks' in config:
                if 'hackathon_default' in config['networks']:
                    has_default_network = True
            else:
                config['networks'] = {}

            if not has_default_network:
                config['networks']['hackathon_default'] = {'driver': 'bridge'}

                # Write back
                with open(file_path, 'w') as f:
                    yaml.dump(config, f, default_flow_style=False, sort_keys=False)

                print(f"✅ Added hackathon_default network to {filename}")
                files_modified += 1
            else:
                print(f"ℹ️  {filename} already has hackathon_default network")

        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")

    print(f"\n📊 Summary: Modified {files_modified} files")
    return files_modified


def remove_duplicate_volumes():
    """
    Remove duplicate volume mounts from Docker Compose files.
    """
    print("\n🔧 Removing Duplicate Volume Mounts")
    print("=" * 40)

    # Files with duplicate volumes based on validation
    files_with_duplicates = [
        'services/code-analyzer/docker-compose.yml',
        'docker-compose.dev.yml',
        'services/memory-agent/docker-compose.yml'
    ]

    files_modified = 0

    for filename in files_with_duplicates:
        file_path = project_root / filename

        if not file_path.exists():
            print(f"⚠️  File not found: {filename}")
            continue

        try:
            import yaml

            with open(file_path, 'r') as f:
                config = yaml.safe_load(f)

            if not config or 'services' not in config:
                continue

            modified = False

            # Process each service
            for service_name, service_config in config['services'].items():
                if 'volumes' in service_config and isinstance(service_config['volumes'], list):
                    original_volumes = service_config['volumes']
                    seen_volumes = set()
                    deduplicated = []

                    for volume in original_volumes:
                        volume_str = str(volume)
                        if volume_str not in seen_volumes:
                            seen_volumes.add(volume_str)
                            deduplicated.append(volume)

                    if len(deduplicated) < len(original_volumes):
                        service_config['volumes'] = deduplicated
                        modified = True
                        print(f"✅ Removed {len(original_volumes) - len(deduplicated)} duplicate volumes from {service_name} in {filename}")

            if modified:
                with open(file_path, 'w') as f:
                    yaml.dump(config, f, default_flow_style=False, sort_keys=False)
                files_modified += 1

        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")

    print(f"\n📊 Summary: Modified {files_modified} files")
    return files_modified


def main():
    """Main execution function."""
    print("🚀 FINAL CONFIGURATION STANDARDIZATION IMPROVEMENTS")
    print("=" * 60)

    total_modified = 0

    # Fix remaining environment variable issues
    total_modified += fix_remaining_env_var_issues()

    # Fix Docker Compose syntax issues
    total_modified += fix_docker_compose_syntax_issues()

    # Add missing default networks
    total_modified += add_missing_default_networks()

    # Remove duplicate volumes
    total_modified += remove_duplicate_volumes()

    print(f"\n🎉 TOTAL IMPROVEMENTS MADE: {total_modified} files modified")

    # Run final validation
    print("\n🔍 RUNNING FINAL VALIDATION...")
    print("=" * 35)

    import subprocess
    try:
        result = subprocess.run([sys.executable, 'scripts/hardening/ci_cd_validator.py', '--quiet'],
                              capture_output=True, text=True, cwd=str(project_root))

        if result.returncode == 0:
            print("✅ ALL VALIDATIONS PASSED!")
        else:
            print("⚠️  Some validations still failing - review output above")
            print(result.stdout)
            if result.stderr:
                print("Errors:", result.stderr)

    except Exception as e:
        print(f"❌ Error running final validation: {e}")


if __name__ == "__main__":
    main()
