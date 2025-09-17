# Migration Scripts

This directory contains scripts for database migrations and data transformation during system updates.

## Migration Scripts

### DDD Migration Scripts
- `create_ddd_migration.py` - Create DDD migration scripts
- `create_ddd_schema_migrations.py` - Generate schema migrations for DDD refactor
- `generate_ddd_migrations_simple.py` - Simplified DDD migration generation

### Data Migration Scripts
- `migrate_existing_data.py` - Migrate existing data to new schema

## Usage

```bash
# Generate DDD migration scripts
python scripts/migration/create_ddd_migration.py

# Create schema migrations
python scripts/migration/create_ddd_schema_migrations.py

# Migrate existing data
python scripts/migration/migrate_existing_data.py
```

## Migration Scope

Migration scripts handle:
- ✅ Database schema updates
- ✅ Data transformation between versions
- ✅ Backward compatibility during transitions
- ✅ Rollback capabilities
- ✅ Data integrity validation

## Safety Considerations

Migration scripts should:
- Create backups before migration
- Provide rollback mechanisms
- Validate data integrity
- Handle error scenarios gracefully
- Include dry-run capabilities
