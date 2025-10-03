#!/usr/bin/env python3
"""Query log-collector for datastore operation logs."""

import requests
import json

# Query log-collector
response = requests.get("http://localhost:8104/logs?service=doc_store&limit=10")
data = response.json()

logs = data.get('items', [])
print(f"╔══════════════════════════════════════════════════════════════════════════╗")
print(f"║                 📊 DOC_STORE OPERATION LOGS                              ║")
print(f"╚══════════════════════════════════════════════════════════════════════════╝")
print()
print(f"✅ Found {len(logs)} log entries for doc_store")
print()

if logs:
    for i, log in enumerate(logs[:5], 1):
        print(f"Log #{i}:")
        print(f"  📝 Message: {log.get('message', 'N/A')}")
        print(f"  📊 Level: {log.get('level', 'N/A')}")
        print(f"  ⏰ Timestamp: {log.get('timestamp', 'N/A')}")
        
        ctx = log.get('context', {})
        if ctx:
            print(f"  🔧 Operation:")
            print(f"    • Type: {ctx.get('operation_type', 'N/A')}")
            print(f"    • Method: {ctx.get('method', 'N/A')}")
            print(f"    • Path: {ctx.get('path', 'N/A')}")
            print(f"    • Duration: {ctx.get('duration_ms', 'N/A')} ms")
            print(f"    • Status: {ctx.get('status_code', 'N/A')}")
            print(f"    • Success: {ctx.get('success', 'N/A')}")
            print(f"    • Phase: {ctx.get('phase', 'N/A')}")
            if 'workflow_id' in ctx:
                print(f"    • Workflow ID: {ctx['workflow_id']}")
        print()
else:
    print("❌ No logs found. The middleware may not be sending logs.")
    print()
    print("Troubleshooting:")
    print("  1. Ensure doc_store service is running")
    print("  2. Make a request to doc_store")
    print("  3. Check service logs for errors")

