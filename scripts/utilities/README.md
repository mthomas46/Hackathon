# Consolidated Development Utilities

This directory contains unified utility scripts for comprehensive development, maintenance, and operational tasks.

## Main Script

### `dev_utilities.py`
**Unified Development Utilities** - Comprehensive development toolkit combining all utility functionality:

**Features:**
- **Code Quality Tools**: Import fixing, bare except handling, code standardization
- **Data Management**: Prompt store browsing, document store route updates, data standardization
- **Infrastructure Tools**: Dockerfile optimization, environment fixes, port conflict resolution
- **Development Helpers**: Code analysis, configuration management, deployment preparation

**Capabilities:**
- Automated code refactoring and standardization
- Data store management and optimization
- Infrastructure configuration and optimization
- Development workflow automation
- Quality assurance and consistency checking

## What Was Consolidated

This unified approach combines functionality from all previously separate utility scripts:
- `doc_prompt_store_browser.py` → Data browsing and management
- `fix_bare_except.py` → Code quality improvements
- `fix_imports.py` → Import statement standardization
- `standardize_prompt_store.py` → Data store standardization
- `update_docstore_routes.py` → Route configuration management
- `dockerfile_optimization.sh` → Container optimization
- `environment_fix.sh` → Environment configuration
- `port_conflict_resolution.sh` → Deployment conflict resolution

## Usage Examples

```bash
# Fix code quality issues
python scripts/utilities/dev_utilities.py fix-code --imports --bare-except

# Optimize data stores
python scripts/utilities/dev_utilities.py optimize-data --prompt-store --doc-store

# Infrastructure optimization
python scripts/utilities/dev_utilities.py optimize-infra --dockerfiles --ports

# Browse and manage data
python scripts/utilities/dev_utilities.py browse-data --store prompt-store --limit 50

# Environment configuration
python scripts/utilities/dev_utilities.py fix-environment --conflicts --variables
```

## Categories of Utilities

### Code Quality & Standards
- Import statement normalization and fixing
- Bare except clause identification and fixing
- Code formatting and standardization
- Syntax error detection and correction

### Data Management
- Prompt store browsing and management
- Document store route optimization
- Data standardization and migration
- Content validation and cleanup

### Infrastructure & Deployment
- Dockerfile optimization and best practices
- Environment variable conflict resolution
- Port conflict detection and resolution
- Configuration validation and standardization

### Development Workflow
- Automated refactoring tools
- Quality assurance checks
- Development environment setup
- Deployment preparation scripts

## Purpose

The consolidated utilities provide:
- **Unified Interface**: Single command-line interface for all development tasks
- **Comprehensive Coverage**: All development, maintenance, and operational needs
- **Automation**: Reduce manual effort through automated tools
- **Quality Assurance**: Ensure code and configuration consistency
- **Productivity**: Streamline development workflows and reduce errors
- **Maintainability**: Centralized utilities are easier to maintain and update
