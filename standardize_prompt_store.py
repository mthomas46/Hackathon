#!/usr/bin/env python3
"""Script to standardize prompt_store repositories and services."""

import os
import re
from pathlib import Path

def update_repository_file(repo_file: Path):
    """Update a repository file to use standardized SqlRepository."""
    content = repo_file.read_text()

    # Skip if already updated
    if "from services.shared.utilities import SqlRepository" in content:
        return

    # Update imports
    content = re.sub(
        r'from services\.prompt_store\.core\.repository import BaseRepository',
        'from services.shared.utilities import SqlRepository, validate_sql_identifier',
        content
    )

    # Find class definitions and update them
    class_pattern = r'class (\w+Repository)\(BaseRepository\[(\w+)\]\):'
    matches = re.findall(class_pattern, content)

    for repo_class, entity_class in matches:
        # Update class inheritance
        content = re.sub(
            rf'class {repo_class}\(BaseRepository\[{entity_class}\]\):',
            rf'class {repo_class}(SqlRepository[{entity_class}]):',
            content
        )

        # Add connection_string parameter to __init__
        init_pattern = rf'(\s+)def __init__\(self\):\s*\n(\s+)super\(\).__init__\("(\w+)"\)'
        init_replacement = rf'\1def __init__(self, connection_string: str):\n\2from ..db.connection import get_prompt_store_connection_string\n\2super().__init__({entity_class}, connection_string or get_prompt_store_connection_string())\n\n\2# Validate table name to prevent SQL injection\n\2if not validate_sql_identifier(self.table_name):\n\2    raise ValueError(f"Invalid table name: {{self.table_name}}")'
        content = re.sub(init_pattern, init_replacement, content)

        # Replace _row_to_entity with _dict_to_entity
        if '_row_to_entity' in content:
            content = re.sub(r'_row_to_entity', '_dict_to_entity', content)

    # Remove old methods that are now handled by SqlRepository
    # Remove custom CRUD methods
    methods_to_remove = [
        r'\s+def save\(self, entity: \w+\) -> \w+:\n.*?(?=\n\s+def|\nclass|\n@|\Z)',
        r'\s+def get_by_id\(self, entity_id: str\) -> Optional\[\w+\]:\n.*?(?=\n\s+def|\nclass|\n@|\Z)',
        r'\s+def get_all\(self,.*?\) -> .*?:\n.*?(?=\n\s+def|\nclass|\n@|\Z)',
        r'\s+def update\(self, entity_id: str, updates: Dict\[str, Any\]\) -> Optional\[\w+\]:\n.*?(?=\n\s+def|\nclass|\n@|\Z)',
        r'\s+def delete\(self, entity_id: str\) -> bool:\n.*?(?=\n\s+def|\nclass|\n@|\Z)',
        r'\s+def exists\(self, entity_id: str\) -> bool:\n.*?(?=\n\s+def|\nclass|\n@|\Z)',
        r'\s+def count\(self, \*\*filters\) -> int:\n.*?(?=\n\s+def|\nclass|\n@|\Z)',
        r'\s+def _entity_to_row\(self, entity: \w+\) -> Dict\[str, Any\]:\n.*?(?=\n\s+def|\nclass|\n@|\Z)',
    ]

    for pattern in methods_to_remove:
        content = re.sub(pattern, '', content, flags=re.DOTALL)

    repo_file.write_text(content)

def update_service_file(service_file: Path):
    """Update a service file to use standardized BaseService."""
    content = service_file.read_text()

    # Skip if already updated
    if "from services.shared.utilities import BaseService" in content:
        return

    # Update imports
    content = re.sub(
        r'from services\.prompt_store\.core\.service import BaseService',
        'from services.shared.utilities import BaseService',
        content
    )

    # Update constructor to pass connection string
    init_pattern = r'(\s+)def __init__\(self\):\s*\n(\s+)super\(\).__init__\((.+?)\(\)\)'
    init_replacement = r'\1def __init__(self):\n\2from ...db.connection import get_prompt_store_connection_string\n\2super().__init__(\3(get_prompt_store_connection_string()))'
    content = re.sub(init_pattern, init_replacement, content)

    # Convert create_entity to _validate_entity and _create_entity_from_data
    if 'def create_entity(self,' in content:
        # Extract the validation logic from create_entity
        create_entity_match = re.search(r'def create_entity\(self, data: Dict\[str, Any\], entity_id: Optional\[str\] = None\) -> (\w+):\n(.*?)(?=\n\s+def|\nclass|\n@|\Z)', content, re.DOTALL)
        if create_entity_match:
            entity_type = create_entity_match.group(1)
            create_body = create_entity_match.group(2)

            # Extract validation logic
            validation_lines = []
            creation_lines = []

            lines = create_body.split('\n')
            in_validation = False
            in_creation = False

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Look for validation patterns
                if any(keyword in line.lower() for keyword in ['validate', 'required', 'missing', 'check', 'if not', 'raise valueerror']):
                    in_validation = True
                    validation_lines.append(line)
                elif any(keyword in line for keyword in ['= ', 'entity =', f'{entity_type}(']):
                    in_creation = True
                    creation_lines.append(line)
                elif in_validation and not in_creation:
                    validation_lines.append(line)
                elif in_creation:
                    creation_lines.append(line)

            # Create _validate_entity method
            validate_method = f'''
    def _validate_entity(self, entity: {entity_type}) -> None:
        """Validate {entity_type} entity."""
        # Extracted validation logic from create_entity
        {"\n        ".join(validation_lines)}
'''

            # Create _create_entity_from_data method
            create_method = f'''
    async def _create_entity_from_data(self, entity_id: str, data: Dict[str, Any]) -> {entity_type}:
        """Create {entity_type} entity from data."""
        # Extracted creation logic from create_entity
        {"\n        ".join(creation_lines)}
        return entity
'''

            # Replace create_entity with the new methods
            content = re.sub(
                r'def create_entity\(self, data: Dict\[str, Any\], entity_id: Optional\[str\] = None\) -> \w+:\n.*?(?=\n\s+def|\nclass|\n@|\Z)',
                f'{validate_method}\n{create_method}',
                content,
                flags=re.DOTALL
            )

    service_file.write_text(content)

def main():
    """Main standardization function."""
    prompt_store_dir = Path("services/prompt_store")

    # Update all repository files
    print("🔄 Updating repository files...")
    for repo_file in prompt_store_dir.glob("domain/*/repository.py"):
        if repo_file.name != "__init__.py":
            print(f"  📝 Updating {repo_file}")
            update_repository_file(repo_file)

    # Update all service files
    print("🔄 Updating service files...")
    for service_file in prompt_store_dir.glob("domain/*/service.py"):
        if service_file.name != "__init__.py":
            print(f"  📝 Updating {service_file}")
            update_service_file(service_file)

    print("✅ Prompt store standardization complete!")

if __name__ == "__main__":
    main()
