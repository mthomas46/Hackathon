#!/usr/bin/env python3
"""
Command-line interface for the comprehensive audit framework.

Usage:
    python audit_cli.py audit --service doc_store
    python audit_cli.py audit --service analysis-service --output markdown
    python audit_cli.py compare --services doc_store,prompt_store
"""

import sys
import os
import asyncio
from pathlib import Path

# Add the scripts directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from audit_framework import main

if __name__ == '__main__':
    main()
