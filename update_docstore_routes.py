#!/usr/bin/env python3
"""Script to update doc_store routes to use standardized response system."""

import re
from pathlib import Path

def update_routes_file():
    """Update the doc_store routes file to use standardized responses."""

    routes_file = Path("services/doc_store/api/routes.py")

    if not routes_file.exists():
        print("Routes file not found")
        return

    content = routes_file.read_text()

    # Pattern to match route decorators with response_model
    route_pattern = r'(@router\.(get|post|put|delete|patch)\("([^"]+)"(?:,.*?)?response_model=[^,)]+)'

    def replace_response_model(match):
        """Replace response_model with standardized response wrapper."""
        route_decorator = match.group(1)
        method = match.group(2)
        path = match.group(3)

        # Remove response_model parameter
        updated_decorator = re.sub(r',?\s*response_model=[^,)]+', '', route_decorator)

        return updated_decorator

    # Remove all response_model specifications
    updated_content = re.sub(route_pattern, replace_response_model, content)

    # Now we need to add standardized response wrappers to the function bodies
    # This is more complex, so let's do it manually for now

    # Write back the updated content
    routes_file.write_text(updated_content)
    print("Updated routes file - removed response_model specifications")

if __name__ == "__main__":
    update_routes_file()
