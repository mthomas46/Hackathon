#!/usr/bin/env python3
"""Fix docker-compose profiles by adding 'all' profile to each service correctly"""

import yaml
import re

def fix_profiles():
    """Fix the profiles in docker-compose.dev.yml"""

    # Read the file as text to preserve formatting
    with open('docker-compose.dev.yml', 'r') as f:
        content = f.read()

    # Pattern to find service definitions and add 'all' profile
    # This looks for lines that start with 2 spaces followed by service name and colon
    lines = content.split('\n')
    fixed_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]
        fixed_lines.append(line)

        # Check if this is a service definition (2 spaces + name:)
        if re.match(r'^  [a-zA-Z_-]+:', line) and not line.startswith('    ') and not line.startswith('      '):
            service_name = line.strip().rstrip(':')

            # Skip if this is not a real service (like 'services:' or 'volumes:')
            if service_name in ['services', 'volumes', 'networks']:
                i += 1
                continue

            # Look ahead to see if profiles already exist
            profiles_found = False
            j = i + 1
            while j < len(lines) and lines[j].startswith('    '):
                if 'profiles:' in lines[j]:
                    profiles_found = True
                    # Add 'all' profile to existing profiles
                    k = j + 1
                    while k < len(lines) and lines[k].startswith('      '):
                        k += 1
                    # Insert 'all' profile after the profiles: line
                    fixed_lines.insert(k, '      - all')
                    break
                j += 1

            # If no profiles found, add profiles section
            if not profiles_found:
                # Find where the service properties end (next service or end of services)
                j = i + 1
                while j < len(lines):
                    if re.match(r'^  [a-zA-Z_-]+:', lines[j]) and not lines[j].startswith('    '):
                        break
                    j += 1

                # Insert profiles section before the next service
                insert_pos = j
                fixed_lines.insert(insert_pos, '    profiles:')
                fixed_lines.insert(insert_pos + 1, '      - all')

        i += 1

    # Write back the fixed content
    with open('docker-compose.dev.yml', 'w') as f:
        f.write('\n'.join(fixed_lines))

    print("✅ Fixed profiles in docker-compose.dev.yml")

if __name__ == "__main__":
    fix_profiles()
