#!/usr/bin/env python3
"""Script to fix bare except clauses with more specific exception handling."""

import os
import re
from pathlib import Path


def fix_bare_except_in_file(file_path: str) -> int:
    """Fix bare except clauses in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return 0

    original_content = content
    fixes_made = 0

    # Pattern 1: Network/API calls - replace with Exception
    network_patterns = [
        (r'except:\s*$', 'except Exception:'),
    ]

    # Pattern 2: Date/time parsing - replace with ValueError
    datetime_patterns = [
        (r'except:\s*$', 'except ValueError:'),
    ]

    # Pattern 3: JSON parsing - replace with (ValueError, TypeError)
    json_patterns = [
        (r'except:\s*$', 'except (ValueError, TypeError):'),
    ]

    # Pattern 4: File operations - replace with (OSError, IOError)
    file_patterns = [
        (r'except:\s*$', 'except (OSError, IOError):'),
    ]

    # Apply fixes based on context
    lines = content.split('\n')
    fixed_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Check if this line has a bare except
        if stripped == 'except:':
            # Look at previous lines to understand context
            context_lines = []
            for j in range(max(0, i-5), i):
                context_lines.append(lines[j].strip())

            context = '\n'.join(context_lines).lower()

            # Determine appropriate exception based on context
            if any(keyword in context for keyword in ['http', 'request', 'client', 'api', 'post', 'get', 'json']):
                # Network/API operations
                fixed_lines.append(line.replace('except:', 'except Exception:'))
                fixes_made += 1
            elif any(keyword in context for keyword in ['date', 'time', 'datetime', 'timestamp', 'pd.to_datetime']):
                # Date/time operations
                fixed_lines.append(line.replace('except:', 'except ValueError:'))
                fixes_made += 1
            elif any(keyword in context for keyword in ['json', 'loads', 'dumps']):
                # JSON operations
                fixed_lines.append(line.replace('except:', 'except (ValueError, TypeError):'))
                fixes_made += 1
            elif any(keyword in context for keyword in ['open', 'read', 'write', 'file', 'path']):
                # File operations
                fixed_lines.append(line.replace('except:', 'except (OSError, IOError):'))
                fixes_made += 1
            else:
                # Generic case - use Exception
                fixed_lines.append(line.replace('except:', 'except Exception:'))
                fixes_made += 1
        else:
            fixed_lines.append(line)

        i += 1

    # Write back if changes were made
    if fixes_made > 0:
        new_content = '\n'.join(fixed_lines)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

    return fixes_made


def main():
    """Main function to fix bare except clauses across all files."""
    services_dir = Path('services')

    if not services_dir.exists():
        print("Services directory not found")
        return

    total_fixes = 0
    processed_files = 0

    print("🔧 Fixing bare except clauses...")

    for py_file in services_dir.rglob('*.py'):
        if py_file.is_file():
            processed_files += 1
            fixes = fix_bare_except_in_file(str(py_file))

            if fixes > 0:
                total_fixes += fixes
                print(f"✅ {py_file.relative_to(services_dir)}: {fixes} fixes")

            if processed_files % 100 == 0:
                print(f"📊 Processed {processed_files} files...")

    print("\n📊 Summary:")
    print(f"📁 Files processed: {processed_files}")
    print(f"🔧 Total fixes made: {total_fixes}")


if __name__ == "__main__":
    main()
