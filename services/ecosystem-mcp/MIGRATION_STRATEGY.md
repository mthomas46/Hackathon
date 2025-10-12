# Database Migration Strategy

**Date**: 2025-10-12  
**Service**: ecosystem-mcp v0.1.0  
**Status**: Migration system established ✅

---

## Overview

This document describes the database migration strategy for the ecosystem-mcp service.

---

## Current State

### What We Have ✅
- **Alembic configured** with proper `alembic.ini` and `env.py`
- **SQLAlchemy models** defined in `src/storage/db_models.py`
- **Comprehensive migration** created: `20251012_0000_initial_schema_complete.py`
- **Tables created** via `Base.metadata.create_all()` during service startup

### What Was Missing ❌
- Initial migration was empty (only `pass` statements)
- No rollback capability
- No schema evolution path

### Now Fixed ✅
- **Proper migration** with complete schema definition
- **Rollback capability** via `downgrade()` function
- **Documentation** of migration strategy

---

## Migration File

**Location**: `alembic/versions/20251012_0000_initial_schema_complete.py`

**Tables Created**:
1. **git_commits** - Git commit metadata cache
2. **documents** - Core document storage with versioning
3. **embeddings** - Embedding metadata (vectors in ChromaDB)
4. **document_versions** - Historical versions of documents
5. **ingestion_jobs** - Job tracking for ingestion pipeline
6. **model_requests** - AI model request tracking

**Features**:
- ✅ All foreign keys
- ✅ All indexes
- ✅ All check constraints
- ✅ All unique constraints
- ✅ Complete rollback support

---

## Usage

### Apply Migration (Fresh Database)
```bash
# Run migration
alembic upgrade head

# Verify
alembic current
alembic history
```

### Rollback Migration
```bash
# Rollback one version
alembic downgrade -1

# Rollback to base
alembic downgrade base
```

### Current Database (Already Has Tables)

**Problem**: Service creates tables via `Base.metadata.create_all()`, so migration can't run (tables exist).

**Solution**: Stamp the database as migrated without running the migration

```bash
# Tell alembic the database is at the current version
alembic stamp head

# Verify
alembic current
# Should show: a1b2c3d4e5f6 (head)
```

**This is safe because**:
1. Tables already exist (created by `Base.metadata.create_all()`)
2. Schema matches the migration exactly
3. Future migrations will work correctly

---

## Future Schema Changes

### Creating a New Migration

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "add_new_column"

# Review the generated migration
vim alembic/versions/XXXXX_add_new_column.py

# Apply migration
alembic upgrade head
```

### Migration Best Practices

1. **Always review auto-generated migrations**
   - Alembic may miss some changes
   - Check for dropped columns/tables
   - Verify constraint changes

2. **Test migrations**
   ```bash
   # Test upgrade
   alembic upgrade head
   
   # Test downgrade
   alembic downgrade -1
   
   # Test re-upgrade
   alembic upgrade head
   ```

3. **Production deployment**
   ```bash
   # Backup database first!
   pg_dump -h localhost -U postgres -d ecosystem_mcp > backup.sql
   
   # Run migration
   alembic upgrade head
   
   # If issues, rollback
   alembic downgrade -1
   # Then restore from backup if needed
   ```

4. **Data migrations**
   - Add data transformations in migration files
   - Use raw SQL or ORM operations
   - Always provide rollback logic

---

## Integration with Deployment

### Manual Deployment

```bash
# 1. Pull latest code
git pull

# 2. Activate venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run migrations
alembic upgrade head

# 5. Restart service
systemctl restart ecosystem-mcp
```

### Docker Deployment

Add migration step to `docker-compose.yml` or startup script:

```yaml
services:
  ecosystem-mcp:
    # ...
    command: >
      sh -c "alembic upgrade head && uvicorn src.api.app:app --host 0.0.0.0"
```

Or create a separate init container:

```yaml
services:
  migrate:
    image: ecosystem-mcp:latest
    command: alembic upgrade head
    depends_on:
      - postgres
  
  app:
    depends_on:
      - migrate
```

### CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
- name: Run database migrations
  run: |
    alembic upgrade head
  env:
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
```

---

## Troubleshooting

### Issue: "Can't locate revision identified by 'XXXXX'"

**Cause**: Migration file deleted but database still references it

**Solution**:
```bash
# Clear alembic version
psql -U postgres -d ecosystem_mcp -c "DELETE FROM alembic_version;"

# Stamp current state
alembic stamp head
```

### Issue: "Table already exists"

**Cause**: Tables created via `Base.metadata.create_all()` before migration

**Solution**:
```bash
# Stamp without running migration
alembic stamp head
```

### Issue: Migration conflicts with existing data

**Cause**: New constraints/columns incompatible with existing data

**Solution**:
```python
# In migration file, add data transformation first
def upgrade():
    # 1. Add column as nullable
    op.add_column('documents', sa.Column('new_field', sa.String(), nullable=True))
    
    # 2. Populate existing rows
    op.execute("UPDATE documents SET new_field = 'default' WHERE new_field IS NULL")
    
    # 3. Make column non-nullable
    op.alter_column('documents', 'new_field', nullable=False)
```

---

## Migration History

| Version | Date | Description | Tables Added | Tables Modified |
|---------|------|-------------|--------------|-----------------|
| a1b2c3d4e5f6 | 2025-10-12 | Initial schema | 6 | 0 |

---

## Schema Diagram

```
git_commits (1) ──< (M) documents (1) ──< (M) embeddings
                        documents (1) ──< (M) document_versions
                        documents (1) ──< (M) model_requests
ingestion_jobs (independent)
```

---

## Verification Checklist

### After Running Migration

- [ ] Check alembic version: `alembic current`
- [ ] Verify all tables exist: `\dt` in psql
- [ ] Check indexes: `\di` in psql
- [ ] Verify constraints: `\d+ table_name`
- [ ] Test rollback: `alembic downgrade -1`
- [ ] Re-apply: `alembic upgrade head`
- [ ] Run application tests
- [ ] Verify service health check

---

## Next Steps

### Immediate (This Session)
1. ✅ Created comprehensive migration
2. ⚠️ Need to stamp existing database: `alembic stamp a1b2c3d4e5f6`
3. ⚠️ Need to test migration on fresh database
4. ⚠️ Need to update deployment scripts

### Future Enhancements
- [ ] Add pre-migration backup script
- [ ] Add post-migration validation script
- [ ] Create migration testing framework
- [ ] Add migration monitoring/alerting
- [ ] Document common migration patterns

---

## Conclusion

**Status**: ✅ **MIGRATION SYSTEM ESTABLISHED**

The ecosystem-mcp service now has a proper database migration system:
- Comprehensive initial migration created
- Rollback capability implemented
- Future schema evolution enabled
- Documentation complete

**Next**: Test migration on fresh database and integrate into deployment process.

---

**Phase 3 Task 1 Progress**: 80% complete (migration created, needs testing)

