#!/bin/bash
#
# Pre-commit hook to validate JSONB field usage
#
# To install:
#   cp .pre-commit-hook-example.sh .git/hooks/pre-commit
#   chmod +x .git/hooks/pre-commit
#
# This hook will prevent commits if JSONB fields are modified without flag_modified()

echo "🔍 Checking JSONB field usage..."

# Run validation script
python3 scripts/validate_jsonb_usage.py --fail-on-error

EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "❌ Commit blocked: JSONB validation failed"
    echo ""
    echo "Fix violations by ensuring flag_modified() is called after JSONB field modifications:"
    echo ""
    echo "  from sqlalchemy.orm.attributes import flag_modified"
    echo ""
    echo "  # Modify JSONB field"
    echo "  obj.job_metadata = new_dict"
    echo ""
    echo "  # Mark as modified"
    echo "  flag_modified(obj, 'job_metadata')"
    echo ""
    echo "To skip this check (not recommended), use: git commit --no-verify"
    echo ""
    exit 1
fi

echo "✅ JSONB validation passed"
exit 0

