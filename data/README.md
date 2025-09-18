# Data Directory

This directory contains database files and other persistent data used by the LLM Documentation Ecosystem services.

## Files

### Database Files
- `orchestrator_workflows.db` - SQLite database for orchestrator workflow data
- `prompt_store.db` - SQLite database for prompt store data

## Usage

These database files are automatically created and managed by their respective services. They contain:

### Orchestrator Workflows Database
- Workflow definitions and executions
- Service orchestration state
- Task scheduling and management
- Performance metrics and logs

### Prompt Store Database
- Prompt templates and versions
- A/B testing configurations
- Usage analytics and metrics
- Prompt optimization data

## Development Notes

### Local Development
- Database files are created automatically on first service startup
- Use the initialization scripts in `scripts/` to populate test data
- Files are ignored by git to prevent committing local development data

### Production
- In production environments, consider using external databases (PostgreSQL, etc.)
- Implement proper backup strategies for these files
- Monitor database file sizes and performance

### Cleanup
- Database files can be safely deleted to reset to a clean state
- Use `scripts/init_docstore_db.py` to recreate database schema
- Test data can be repopulated using `scripts/populate_*_test_data.py`

## Backup and Recovery

- Regularly backup database files in production
- Use database migration scripts for schema changes
- Consider implementing database export/import functionality

## Security

- Database files may contain sensitive data
- Ensure proper file permissions in production
- Consider encryption for sensitive databases
