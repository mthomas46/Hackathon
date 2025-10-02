#!/usr/bin/env python3
"""Add 'all' profile to all services in docker-compose.dev.yml"""

import yaml
import sys
from pathlib import Path

def add_all_profile_to_services():
    """Add 'all' profile to all services in docker-compose.dev.yml"""

    compose_file = Path("docker-compose.dev.yml")

    if not compose_file.exists():
        print("docker-compose.dev.yml not found")
        return False

    # Read the compose file
    with open(compose_file, 'r') as f:
        compose_data = yaml.safe_load(f)

    # Add 'all' profile to each service
    if 'services' in compose_data:
        for service_name, service_config in compose_data['services'].items():
            if 'profiles' in service_config:
                if 'all' not in service_config['profiles']:
                    service_config['profiles'].insert(0, 'all')
            else:
                service_config['profiles'] = ['all']

    # Write back the updated compose file
    with open(compose_file, 'w') as f:
        yaml.dump(compose_data, f, default_flow_style=False, sort_keys=False)

    print(f"Added 'all' profile to all {len(compose_data['services'])} services")
    return True

if __name__ == "__main__":
    add_all_profile_to_services()
