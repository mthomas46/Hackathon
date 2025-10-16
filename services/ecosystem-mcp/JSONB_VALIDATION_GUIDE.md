# JSONB Field Validation Guide

**Purpose:** Ensure all JSONB field modifications are properly tracked by SQLAlchemy using `flag_modified()`.

---

## 🔍 **The Problem**

SQLAlchemy's JSONB type does NOT automatically detect in-place modifications:

```python
# ❌ WRONG - SQLAlchemy doesn't detect this change
job.job_metadata['progress'] = 50
await session.commit()  # Nothing saved!

# ❌ WRONG - Same issue
metadata = job.job_metadata
metadata['status'] = 'done'
await session.commit()  # Nothing saved!
```

**Result:** Changes are lost, updates fail silently, data becomes stale.

---

## ✅ **The Solution**

Always use the **Copy-Modify-Reassign-Flag** pattern:

```python
from sqlalchemy.orm.attributes import flag_modified

# 1. Copy the JSONB field
metadata = job.job_metadata.copy() if job.job_metadata else {}

# 2. Modify the copy
metadata['progress'] = 50
metadata['status'] = 'done'

# 3. Reassign to trigger change detection
job.job_metadata = metadata

# 4. Explicitly mark as modified
flag_modified(job, 'job_metadata')

# 5. Commit
await session.commit()  # ✅ Now it saves!
```

---

## 🛡️ **Validation System**

We've built a comprehensive validation system to detect violations automatically.

### **Components**

1. **AST Analyzer** (`jsonb_validator.py`)
   - Parses Python code
   - Detects JSONB field modifications
   - Checks for `flag_modified()` calls
   - Reports violations

2. **CLI Tool** (`scripts/validate_jsonb_usage.py`)
   - Run manually or in CI/CD
   - Generate reports
   - Fail builds on violations

3. **API Endpoint** (`/api/v1/admin/code-quality/validate-jsonb`)
   - On-demand validation
   - Dashboard integration
   - Real-time results

4. **Pre-commit Hook** (`.pre-commit-hook-example.sh`)
   - Runs before commit
   - Blocks commits with violations
   - Enforces best practices

---

## 🚀 **Usage**

### **Manual Validation**

```bash
# Validate entire codebase
python3 scripts/validate_jsonb_usage.py

# Validate specific directory
python3 scripts/validate_jsonb_usage.py --root src/services/

# Save report to file
python3 scripts/validate_jsonb_usage.py --output report.txt

# Fail on errors (for CI/CD)
python3 scripts/validate_jsonb_usage.py --fail-on-error

# Fail on warnings too (strict mode)
python3 scripts/validate_jsonb_usage.py --fail-on-warning
```

### **API Endpoint**

```bash
# Run validation via API
curl http://localhost:8000/api/v1/admin/code-quality/validate-jsonb

# Response:
{
  "files_checked": 50,
  "files_with_violations": 2,
  "total_violations": 5,
  "errors": 3,
  "warnings": 2,
  "violations": [...]
}
```

### **Pre-commit Hook**

```bash
# Install hook
cp .pre-commit-hook-example.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

# Now commits are validated automatically
git commit -m "My changes"
# 🔍 Checking JSONB field usage...
# ✅ JSONB validation passed
```

---

## 📊 **What It Detects**

### **1. Direct Assignment (ERROR)**

```python
# ❌ Detected as violation
obj.job_metadata = {'key': 'value'}

# ✅ Should be:
metadata = {'key': 'value'}
obj.job_metadata = metadata
flag_modified(obj, 'job_metadata')
```

### **2. In-Place Modification (ERROR)**

```python
# ❌ Detected as violation
obj.job_metadata.update({'key': 'value'})
obj.job_metadata.pop('old_key')
obj.job_metadata.clear()

# ✅ Should be:
metadata = obj.job_metadata.copy()
metadata.update({'key': 'value'})
obj.job_metadata = metadata
flag_modified(obj, 'job_metadata')
```

### **3. Item Assignment (WARNING)**

```python
# ⚠️  Detected as warning
obj.job_metadata['key'] = 'value'

# ✅ Should be:
metadata = obj.job_metadata.copy()
metadata['key'] = 'value'
obj.job_metadata = metadata
flag_modified(obj, 'job_metadata')
```

### **4. Item Deletion (WARNING)**

```python
# ⚠️  Detected as warning
del obj.job_metadata['old_key']

# ✅ Should be:
metadata = obj.job_metadata.copy()
del metadata['old_key']
obj.job_metadata = metadata
flag_modified(obj, 'job_metadata')
```

---

## 🎯 **Known JSONB Fields**

The validator tracks these fields across our codebase:

- `job_metadata` (IngestionJobModel)
- `metadata` (various models)
- `config` (configuration models)
- `settings` (settings models)
- `properties` (property storage)
- `data` (generic data storage)

To add more fields, update `KNOWN_JSONB_FIELDS` in `jsonb_validator.py`.

---

## 📋 **Validation Report Example**

```
================================================================================
JSONB Field Validation Report
================================================================================

Files Checked: 50
Files with Violations: 2
Total Violations: 5
  - Errors: 3
  - Warnings: 2

Violations:
--------------------------------------------------------------------------------

📄 src/services/ingestion/job_processor.py
  ❌ Line 123: JSONB field 'job_metadata' assigned without flag_modified() call
     Code: job.job_metadata = metadata
  ⚠️  Line 456: JSONB field 'job_metadata' item modified without flag_modified() call
     Code: job.job_metadata['status'] = 'done'

📄 src/storage/repositories/document_repository.py
  ❌ Line 89: JSONB field 'metadata' modified with .update() without flag_modified() call
     Code: doc.metadata.update({'indexed': True})

================================================================================
```

---

## 🔧 **CI/CD Integration**

### **GitHub Actions**

```yaml
name: Code Quality

on: [push, pull_request]

jobs:
  validate-jsonb:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Validate JSONB usage
        run: |
          python3 scripts/validate_jsonb_usage.py --fail-on-error
```

### **GitLab CI**

```yaml
jsonb-validation:
  stage: test
  script:
    - python3 scripts/validate_jsonb_usage.py --fail-on-error
  only:
    - merge_requests
    - main
```

---

## 🧪 **Testing**

### **Run Tests**

```bash
# Run validator unit tests
pytest tests/test_jsonb_validator.py

# Test pre-commit hook
./scripts/validate_jsonb_usage.py --fail-on-error
```

### **Test Cases**

The validator includes tests for:
- Direct assignment detection
- In-place modification detection
- Item assignment detection
- `flag_modified()` presence check
- False positive prevention
- Multiple objects in same function

---

## 💡 **Best Practices**

### **1. Always Use the Pattern**

```python
# Copy
metadata = obj.job_metadata.copy() if obj.job_metadata else {}

# Modify
metadata['key'] = 'value'

# Reassign
obj.job_metadata = metadata

# Flag
flag_modified(obj, 'job_metadata')
```

### **2. Import at Top of File**

```python
from sqlalchemy.orm.attributes import flag_modified
```

### **3. Use in All Database Operations**

- Repository methods
- Service methods
- Worker functions
- API endpoints

### **4. Document Why**

```python
# Update job metadata - using copy pattern to ensure SQLAlchemy detects change
metadata = job.job_metadata.copy()
metadata['progress'] = 50
job.job_metadata = metadata
flag_modified(job, 'job_metadata')
```

### **5. Run Validation Before Commits**

```bash
# Install pre-commit hook
cp .pre-commit-hook-example.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

---

## ⚠️ **Common Mistakes**

### **Mistake 1: Forgetting to Copy**

```python
# ❌ BAD - modifying the same dict
metadata = job.job_metadata
metadata['key'] = 'value'
job.job_metadata = metadata
flag_modified(job, 'job_metadata')

# ✅ GOOD - copy first
metadata = job.job_metadata.copy()
```

### **Mistake 2: Wrong Field Name**

```python
# ❌ BAD - typo in field name
flag_modified(job, 'metadata')  # Should be 'job_metadata'

# ✅ GOOD - correct field name
flag_modified(job, 'job_metadata')
```

### **Mistake 3: Forgetting to Flag**

```python
# ❌ BAD - no flag_modified
metadata = job.job_metadata.copy()
metadata['key'] = 'value'
job.job_metadata = metadata
# Missing: flag_modified(job, 'job_metadata')

# ✅ GOOD - includes flag_modified
metadata = job.job_metadata.copy()
metadata['key'] = 'value'
job.job_metadata = metadata
flag_modified(job, 'job_metadata')
```

### **Mistake 4: Multiple Modifications**

```python
# ❌ BAD - flag_modified after each change
metadata = job.job_metadata.copy()
metadata['key1'] = 'value1'
job.job_metadata = metadata
flag_modified(job, 'job_metadata')

metadata = job.job_metadata.copy()
metadata['key2'] = 'value2'
job.job_metadata = metadata
flag_modified(job, 'job_metadata')

# ✅ GOOD - batch modifications
metadata = job.job_metadata.copy()
metadata['key1'] = 'value1'
metadata['key2'] = 'value2'
job.job_metadata = metadata
flag_modified(job, 'job_metadata')
```

---

## 📚 **Resources**

- **SQLAlchemy Docs:** https://docs.sqlalchemy.org/en/14/orm/session_api.html#sqlalchemy.orm.attributes.flag_modified
- **Our Fix:** `DATABASE_UPDATE_FIX_COMPLETE.md`
- **Protection Plan:** `SYSTEM_PROTECTIONS_AND_FALLBACKS.md`

---

## 🎯 **Success Metrics**

With this validation system:

- ✅ Prevent silent update failures
- ✅ Catch violations before commit
- ✅ Enforce best practices automatically
- ✅ Improve code quality
- ✅ Reduce debugging time
- ✅ Increase confidence in updates

---

## 🚨 **Alert: Breaking the Rules**

You can bypass validation with:

```bash
git commit --no-verify
```

**⚠️ WARNING:** Only use in emergencies! This bypasses critical safety checks.

Better approach:
1. Fix the violations
2. Run validation manually
3. Commit properly

---

## ✅ **Summary**

1. **Pattern:** Copy → Modify → Reassign → Flag
2. **Tool:** `scripts/validate_jsonb_usage.py`
3. **API:** `GET /api/v1/admin/code-quality/validate-jsonb`
4. **Hook:** `.pre-commit-hook-example.sh`
5. **CI/CD:** Integrate into pipeline
6. **Testing:** Run before every commit

**Result:** Zero silent JSONB update failures! 🎉

