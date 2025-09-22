#!/usr/bin/env python3
"""
Configuration Transition Helper

Helps transition services from hardcoded environment variables to proper config file usage.
"""

import os
import re
from pathlib import Path
import yaml
from typing import Dict, List


class ConfigTransitionHelper:
    """Helps transition services to use config files properly."""

    def __init__(self, services_dir: str = "services"):
        self.services_dir = Path(services_dir)

    def load_service_config(self, service_name: str) -> Dict:
        """Load a service's config file."""
        config_files = list(self.services_dir.glob(f"{service_name}/config.y*"))
        if not config_files:
            return {}

        try:
            with open(config_files[0], 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}

    def find_hardcoded_env_vars(self, service_name: str) -> List[Dict]:
        """Find hardcoded environment variables in service code."""
        service_dir = self.services_dir / service_name
        hardcoded_vars = []

        python_files = list(service_dir.glob("**/*.py"))
        python_files.extend(list(service_dir.glob("*.py")))

        for py_file in python_files:
            if 'test' in str(py_file) or '__pycache__' in str(py_file):
                continue

            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                    lines = content.split('\n')

                for line_num, line in enumerate(lines, 1):
                    # Find os.getenv and os.environ.get patterns
                    env_matches = re.finditer(r'os\.getenv\([^,)]+, [^\)]+\)', line)
                    environ_matches = re.finditer(r'os\.environ\.get\([^,)]+, [^\)]+\)', line)

                    for match in env_matches:
                        var_code = match.group(0)
                        hardcoded_vars.append({
                            'file': str(py_file.relative_to(service_dir)),
                            'line': line_num,
                            'code': var_code,
                            'type': 'os.getenv'
                        })

                    for match in environ_matches:
                        var_code = match.group(0)
                        hardcoded_vars.append({
                            'file': str(py_file.relative_to(service_dir)),
                            'line': line_num,
                            'code': var_code,
                            'type': 'os.environ.get'
                        })

            except Exception as e:
                print(f"Error reading {py_file}: {e}")

        return hardcoded_vars

    def generate_config_loading_code(self, service_name: str, hardcoded_vars: List[Dict]) -> str:
        """Generate config loading code for a service."""
        config_vars = set()

        # Extract variable names from hardcoded calls
        for var in hardcoded_vars:
            code = var['code']
            # Extract variable name from patterns like os.getenv("VAR_NAME", "default")
            match = re.search(r'["\']([^"\']+)["\']', code)
            if match:
                config_vars.add(match.group(1))

        if not config_vars:
            return ""

        # Generate import and loading code
        code_lines = [
            "# Configuration loading",
            "import yaml",
            "from pathlib import Path",
            "",
            "def load_config() -> dict:",
            "    \"\"\"Load service configuration from config file.\"\"\"",
            "    config_path = Path(__file__).parent / 'config.yaml'",
            "    if config_path.exists():",
            "        with open(config_path, 'r') as f:",
            "            return yaml.safe_load(f) or {}",
            "    return {}",
            "",
            "# Load configuration",
            "config = load_config()",
            "",
            "# Extract configuration values with environment variable override",
        ]

        for var_name in sorted(config_vars):
            code_lines.append(f"{var_name} = os.getenv('{var_name}', config.get('{var_name.lower().replace('_', '-')}', 'default_value'))")

        return "\n".join(code_lines)

    def transition_service_config(self, service_name: str) -> bool:
        """Transition a service to use config files properly."""
        print(f"🔄 Transitioning {service_name} to use config files...")

        # Load current config
        current_config = self.load_service_config(service_name)

        # Find hardcoded variables
        hardcoded_vars = self.find_hardcoded_env_vars(service_name)

        if not hardcoded_vars:
            print(f"✅ {service_name} already uses config files properly")
            return True

        print(f"📝 Found {len(hardcoded_vars)} hardcoded variables in {service_name}")

        # Generate config loading code
        config_code = self.generate_config_loading_code(service_name, hardcoded_vars)

        if config_code:
            # Find main service file
            main_files = ['main.py', 'app.py', '__main__.py']
            main_file = None

            for main_candidate in main_files:
                candidate_path = self.services_dir / service_name / main_candidate
                if candidate_path.exists():
                    main_file = candidate_path
                    break

            if main_file:
                # Read current content
                with open(main_file, 'r') as f:
                    content = f.read()

                # Check if config loading already exists
                if 'load_config()' not in content:
                    # Add config loading after imports
                    import_end_pattern = r'(?m)^import|^from.*import'
                    matches = list(re.finditer(import_end_pattern, content))

                    if matches:
                        last_import = matches[-1]
                        insert_pos = last_import.end()

                        # Find next non-empty line
                        lines = content.split('\n')
                        for i in range(last_import.end() // len(content.split('\n')[0]) + 1, len(lines)):
                            if lines[i].strip():
                                insert_pos = sum(len(lines[j]) + 1 for j in range(i))
                                break

                        new_content = content[:insert_pos] + '\n\n' + config_code + '\n\n' + content[insert_pos:]
                        with open(main_file, 'w') as f:
                            f.write(new_content)

                        print(f"✅ Added config loading to {main_file}")
                    else:
                        print(f"⚠️  Could not find import section in {main_file}")
                else:
                    print(f"ℹ️  Config loading already exists in {main_file}")
            else:
                print(f"⚠️  Could not find main file for {service_name}")

        return True

    def transition_critical_services(self) -> None:
        """Transition the most critical services first."""
        critical_services = [
            'llm-gateway',  # Most complex config
            'orchestrator',  # Core service
            'analysis-service',  # Complex service
            'doc_store',  # Data service
            'prompt_store',  # Data service
            'summarizer-hub',  # AI service
        ]

        for service in critical_services:
            self.transition_service_config(service)


def main():
    """Main entry point."""
    print("🔄 Starting configuration transition...")

    helper = ConfigTransitionHelper()

    print("🎯 Transitioning critical services...")
    helper.transition_critical_services()

    print("\n✅ Configuration transition complete!")
    print("\n📋 Next steps:")
    print("1. Review the generated config loading code")
    print("2. Update config.yaml files with proper default values")
    print("3. Test each service to ensure config loading works")
    print("4. Remove old hardcoded os.getenv() calls")


if __name__ == "__main__":
    main()
