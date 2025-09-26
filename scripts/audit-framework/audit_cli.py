#!/usr/bin/env python3
"""
Entry point for the LLM Ecosystem Audit Framework CLI.
"""

import sys
from pathlib import Path

# Add the audit-framework directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import and run the CLI
from presentation.cli.audit_cli import main

if __name__ == "__main__":
    main()
