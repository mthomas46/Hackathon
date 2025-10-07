# MCP Portability Guide - "Docker for Knowledge Graphs"

## 📦 Overview

The MCP Portability system provides "Docker for Knowledge Graphs" functionality, enabling you to package, version, distribute, and hot-swap MCP knowledge across systems with zero downtime.

### Key Features

- **Package Export/Import**: Bundle MCP knowledge into portable `.mcp` files
- **Version Control**: Snapshot and rollback packages
- **Hot-Swapping**: Update packages with zero downtime
- **Gradual Rollout**: Deploy updates progressively
- **Compression**: Multiple compression formats (gzip, zstandard)
- **Validation**: Ensure package integrity

---

## 🏗️ Architecture

### Components

```
┌─────────────────────────────────────────────────────────┐
│                   Package Manager                        │
│                                                          │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────┐ │
│  │   Package    │  │   Versioning  │  │  Hot-Swap    │ │
│  │   Creation   │  │   & Snapshots │  │   Engine     │ │
│  └──────────────┘  └───────────────┘  └──────────────┘ │
│                                                          │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────┐ │
│  │   Export     │  │    Import     │  │  Validation  │ │
│  │   Engine     │  │    Engine     │  │   System     │ │
│  └──────────────┘  └───────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │    .mcp File Format    │
              │                        │
              │  • metadata.json       │
              │  • knowledge/          │
              │  • tar + compression   │
              └────────────────────────┘
```

### Package Structure

An `.mcp` file is a compressed TAR archive containing:

```
package.mcp
├── metadata.json       # Package metadata
└── knowledge/          # Knowledge items
    ├── item_0.json
    ├── item_1.json
    └── item_N.json
```

---

## 🚀 Quick Start

### 1. Create a Package

```python
from mcp_package_manager import PackageManager, PackageMetadata

# Initialize manager
manager = PackageManager(storage_dir="./packages")

# Create package metadata
metadata = PackageMetadata(
    name="my_awesome_package",
    version="1.0.0",
    description="My first MCP package",
    author="Your Name",
    tier_type="client",
    tags=["ml", "production"]
)

# Create package
package = manager.create_package(metadata)
```

### 2. Add Knowledge

```python
# Add knowledge items
manager.add_knowledge_to_package(
    package.package_id,
    content="Critical production knowledge",
    relevance=0.95
)

manager.add_knowledge_to_package(
    package.package_id,
    content="API documentation",
    relevance=0.90
)
```

### 3. Export to .mcp File

```python
from mcp_package_manager import ExportConfig, CompressionType

# Configure export
config = ExportConfig(
    include_metadata=True,
    include_knowledge=True,
    compression=CompressionType.GZIP
)

# Export
result = manager.export_package(
    package.package_id,
    "/path/to/my_package.mcp",
    config
)

if result.success:
    print(f"Exported to: {result.export_path}")
```

### 4. Import Package

```python
from mcp_package_manager import ImportConfig

# Configure import
config = ImportConfig(
    validate_metadata=True,
    overwrite_existing=False
)

# Import
result = manager.import_package("/path/to/my_package.mcp", config)

if result.success:
    print(f"Imported package ID: {result.package_id}")
```

---

## 🔄 Version Control

### Create Snapshots

```python
# Create a version snapshot
snapshot = manager.create_snapshot(
    package.package_id,
    tag="v1.0.0-stable"
)

print(f"Snapshot created: {snapshot.tag}")
```

### List Versions

```python
# Get all versions
versions = manager.list_versions(package.package_id)

for v in versions:
    print(f"{v.tag}: v{v.version} (created {v.created_at})")
```

### Rollback

```python
# Rollback to previous version
result = manager.rollback(
    package.package_id,
    version="1.0.0"
)

if result.success:
    print(f"Rolled back to: {result.rolled_back_to}")
```

---

## ⚡ Hot-Swapping

### Instant Hot-Swap (Zero Downtime)

```python
# Hot-swap from old to new package
result = manager.hot_swap(
    current_package_id=old_pkg.package_id,
    new_package_id=new_pkg.package_id
)

if result.success:
    print(f"Hot-swap complete! Downtime: {result.downtime_ms}ms")
```

### Gradual Rollout

```python
# Gradually rollout new version
percentages = [10, 25, 50, 75, 100]

for pct in percentages:
    result = manager.gradual_rollout(
        current_package_id=stable_pkg.package_id,
        new_package_id=beta_pkg.package_id,
        percentage=pct
    )
    
    print(f"Rollout at {pct}%")
    
    # Monitor metrics, then proceed...
```

---

## 🔍 Package Discovery

### Search by Name

```python
# Search packages
packages = manager.search_packages(name="my_package")

for pkg in packages:
    print(f"{pkg.metadata.name} v{pkg.metadata.version}")
```

### Filter by Tags

```python
# Find all ML packages
ml_packages = manager.search_packages(tags=["ml", "machine-learning"])

print(f"Found {len(ml_packages)} ML packages")
```

### List All Packages

```python
# Get all packages
all_packages = manager.list_packages()

for pkg in all_packages:
    info = manager.get_package_info(pkg.package_id)
    print(f"{info['name']}: {info['knowledge_count']} knowledge items")
```

---

## 📝 Package Metadata

### Required Fields

- `name`: Package name (must be unique per version)
- `version`: Semantic version (e.g., "1.0.0")

### Optional Fields

- `description`: Package description
- `author`: Package author
- `tier_type`: MCP tier ("client", "project", "team", "company", "ecosystem")
- `tags`: List of tags for discovery
- `metadata`: Additional custom metadata

### Metadata Example

```python
metadata = PackageMetadata(
    name="production_ml_model",
    version="2.1.0",
    description="Production ML model with embeddings",
    author="ML Team",
    tier_type="company",
    tags=["ml", "embeddings", "production", "v2"],
    metadata={
        "model_type": "transformer",
        "accuracy": 0.95,
        "training_date": "2025-01-15"
    }
)
```

---

## 🗜️ Compression

### Supported Formats

1. **None** - No compression (fastest)
2. **GZIP** - Standard compression (recommended)
3. **ZSTD** - Zstandard compression (best ratio)

### Compression Example

```python
from mcp_package_manager import CompressionType

# Use GZIP compression
config = ExportConfig(compression=CompressionType.GZIP)
manager.export_package(pkg_id, "package.mcp", config)

# Use ZSTD for best compression
config = ExportConfig(compression=CompressionType.ZSTD)
manager.export_package(pkg_id, "package_compressed.mcp", config)
```

---

## ✅ Validation

### Validate Package Structure

```python
# Validate package
result = manager.validate_package(package.package_id)

if result.is_valid:
    print("✓ Package is valid")
else:
    print("✗ Validation errors:")
    for error in result.errors:
        print(f"  - {error}")
```

### Import Validation

```python
# Enable validation on import
config = ImportConfig(
    validate_metadata=True,
    overwrite_existing=False
)

result = manager.import_package("package.mcp", config)

if not result.success:
    print(f"Import failed: {result.error}")
```

---

## 🌐 Distribution Workflows

### Workflow 1: Development → Production

```python
# Development environment
dev_manager = PackageManager(storage_dir="./dev_packages")

# Create and test package
pkg = dev_manager.create_package(metadata)
# ... add knowledge and test ...

# Export for production
dev_manager.export_package(pkg.package_id, "prod_package.mcp")

# Production environment (different machine)
prod_manager = PackageManager(storage_dir="./prod_packages")

# Import and deploy
result = prod_manager.import_package("prod_package.mcp")
print(f"Deployed to production: {result.package_id}")
```

### Workflow 2: Blue-Green Deployment

```python
# Blue (current stable)
blue_pkg = manager.create_package(
    PackageMetadata(name="app", version="1.0.0")
)

# Green (new version)
green_pkg = manager.create_package(
    PackageMetadata(name="app", version="2.0.0")
)

# Test green
# ... run tests ...

# Hot-swap to green
manager.hot_swap(blue_pkg.package_id, green_pkg.package_id)

# If issues, rollback to blue
manager.rollback(green_pkg.package_id, "1.0.0")
```

### Workflow 3: Multi-Environment Sync

```python
# Export from staging
staging_manager.export_package(pkg_id, "app_v2.mcp")

# Import to multiple production instances
for env in ["prod-us", "prod-eu", "prod-asia"]:
    env_manager = PackageManager(storage_dir=f"./{env}")
    result = env_manager.import_package("app_v2.mcp")
    print(f"{env}: {result.package_id}")
```

---

## 🎯 Best Practices

### 1. Versioning Strategy

```python
# Use semantic versioning
metadata = PackageMetadata(
    name="my_package",
    version="2.1.3"  # MAJOR.MINOR.PATCH
)

# Create snapshots for important milestones
manager.create_snapshot(pkg_id, tag="v2.1.3-stable")
manager.create_snapshot(pkg_id, tag="v2.1.3-production")
```

### 2. Knowledge Organization

```python
# Group related knowledge with metadata
manager.add_knowledge_to_package(
    pkg_id,
    content="API endpoint documentation",
    relevance=1.0,
    metadata={"category": "api", "priority": "high"}
)

manager.add_knowledge_to_package(
    pkg_id,
    content="Troubleshooting guide",
    relevance=0.8,
    metadata={"category": "support", "priority": "medium"}
)
```

### 3. Tag Conventions

```python
# Use consistent tag naming
tags = [
    "production",        # Environment
    "ml-models",         # Category
    "v2",                # Version family
    "team-data-science", # Owner
    "high-priority"      # Priority
]

metadata = PackageMetadata(name="pkg", version="1.0.0", tags=tags)
```

### 4. Validation Checks

```python
# Always validate before export
validation = manager.validate_package(pkg_id)

if validation.is_valid:
    # Export
    manager.export_package(pkg_id, "package.mcp")
else:
    print("Fix validation errors first!")
    for error in validation.errors:
        print(f"  • {error}")
```

### 5. Safe Hot-Swapping

```python
# Create snapshot before hot-swap
manager.create_snapshot(current_pkg_id, tag="pre-hotswap-backup")

# Hot-swap
result = manager.hot_swap(current_pkg_id, new_pkg_id)

if not result.success:
    # Rollback if failed
    manager.rollback(current_pkg_id, "1.0.0")
```

---

## 🔧 Advanced Usage

### Custom Export Configuration

```python
config = ExportConfig(
    include_metadata=True,
    include_knowledge=True,
    compression=CompressionType.GZIP
)

result = manager.export_package(pkg_id, "custom.mcp", config)
```

### Batch Operations

```python
# Export multiple packages
packages = manager.list_packages()

for pkg in packages:
    filename = f"{pkg.metadata.name}_v{pkg.metadata.version}.mcp"
    manager.export_package(pkg.package_id, filename)
```

### Package Statistics

```python
# Get comprehensive package info
info = manager.get_package_info(pkg_id)

print(f"Package: {info['name']} v{info['version']}")
print(f"Knowledge items: {info['knowledge_count']}")
print(f"Author: {info['author']}")
print(f"Tier: {info['tier_type']}")
print(f"Tags: {', '.join(info['tags'])}")
```

---

## 🐛 Troubleshooting

### Issue: Import Fails with "Package already exists"

**Solution**: Use `overwrite_existing=True` or delete existing package first.

```python
config = ImportConfig(overwrite_existing=True)
result = manager.import_package("package.mcp", config)
```

### Issue: Export File Too Large

**Solution**: Use ZSTD compression for better compression ratios.

```python
config = ExportConfig(compression=CompressionType.ZSTD)
manager.export_package(pkg_id, "package.mcp", config)
```

### Issue: Version Not Found for Rollback

**Solution**: Ensure snapshot was created before attempting rollback.

```python
# Create snapshot first
manager.create_snapshot(pkg_id, tag="v1.0.0")

# Then rollback
manager.rollback(pkg_id, "1.0.0")
```

### Issue: Validation Errors on Import

**Solution**: Check metadata requirements and file integrity.

```python
# Disable validation to see what's wrong
config = ImportConfig(validate_metadata=False)
result = manager.import_package("package.mcp", config)

if result.success:
    # Inspect imported package
    info = manager.get_package_info(result.package_id)
    print(info)
```

---

## 📊 Performance Considerations

### Package Size Limits

- **Maximum package size**: 1000 MB
- **Recommended size**: < 100 MB per package
- **Knowledge items**: Unlimited (within size limit)

### Compression Trade-offs

| Format | Speed      | Ratio      | Use Case             |
|--------|------------|------------|----------------------|
| None   | Fastest    | 1:1        | Local testing        |
| GZIP   | Fast       | 3:1        | General use          |
| ZSTD   | Moderate   | 4:1        | Network distribution |

### Hot-Swap Performance

- **Downtime**: 0ms (zero downtime)
- **Swap time**: < 50ms for typical packages
- **Memory overhead**: Minimal (< 10MB)

---

## 🔐 Security

### Package Integrity

```python
# Validate imported packages
config = ImportConfig(validate_metadata=True)
result = manager.import_package("package.mcp", config)

if not result.success:
    print(f"Security validation failed: {result.error}")
```

### Access Control

```python
# Restrict package operations by tier
if package.metadata.tier_type == "ecosystem":
    # Require admin privileges
    if not user.is_admin:
        raise PermissionError("Admin access required")
```

---

## 📚 API Reference

### PackageManager

#### `create_package(metadata: PackageMetadata) -> MCPPackage`

Create a new package.

#### `export_package(package_id: str, output_path: str, config: ExportConfig) -> ExportResult`

Export package to .mcp file.

#### `import_package(package_path: str, config: ImportConfig) -> ImportResult`

Import package from .mcp file.

#### `hot_swap(current_package_id: str, new_package_id: str) -> HotSwapResult`

Hot-swap packages with zero downtime.

#### `rollback(package_id: str, version: str) -> RollbackResult`

Rollback to previous version.

#### `create_snapshot(package_id: str, tag: str) -> PackageSnapshot`

Create version snapshot.

#### `list_packages() -> List[MCPPackage]`

List all packages.

#### `search_packages(name: str = None, tags: List[str] = None) -> List[MCPPackage]`

Search packages by criteria.

---

## 🎓 Examples

### Example 1: ML Model Packaging

```python
# Package ML model with embeddings
metadata = PackageMetadata(
    name="sentiment_model",
    version="3.2.0",
    description="Sentiment analysis model with pre-computed embeddings",
    author="ML Team",
    tier_type="company",
    tags=["ml", "nlp", "production"]
)

pkg = manager.create_package(metadata)

# Add model knowledge
manager.add_knowledge_to_package(
    pkg.package_id,
    content="Model architecture: BERT-base",
    relevance=1.0
)

manager.add_knowledge_to_package(
    pkg.package_id,
    content="Training data: 1M customer reviews",
    relevance=0.9
)

# Export for deployment
manager.export_package(pkg.package_id, "sentiment_model_v3.2.0.mcp")
```

### Example 2: API Documentation Package

```python
# Package API documentation
metadata = PackageMetadata(
    name="api_docs",
    version="1.0.0",
    description="Complete API documentation and examples",
    tags=["api", "documentation"]
)

pkg = manager.create_package(metadata)

# Add API endpoints
endpoints = [
    {"path": "/users", "method": "GET", "desc": "List users"},
    {"path": "/users/:id", "method": "GET", "desc": "Get user by ID"},
    # ... more endpoints
]

for endpoint in endpoints:
    manager.add_knowledge_to_package(
        pkg.package_id,
        content=f"{endpoint['method']} {endpoint['path']}: {endpoint['desc']}",
        relevance=1.0
    )

# Export
manager.export_package(pkg.package_id, "api_docs.mcp")
```

---

## 🚦 Status Codes

### Export Results

- `success=True`: Export completed successfully
- `success=False`: Export failed (check `error` field)

### Import Results

- `success=True, package_id=<id>`: Import successful
- `success=False, error="validation"`: Validation failed
- `success=False, error="duplicate"`: Package already exists

### Hot-Swap Results

- `success=True, downtime_ms=0`: Hot-swap successful
- `success=False`: Hot-swap failed (check `error` field)

---

## 📖 Related Documentation

- [5-Tier System Guide](./5_TIER_SYSTEM_GUIDE.md)
- [Hierarchical Retrieval Guide](./HIERARCHICAL_RETRIEVAL_GUIDE.md)
- [Context Pruning Guide](./CONTEXT_PRUNING_GUIDE.md)
- [Service Integration Guide](./SERVICE_INTEGRATION_GUIDE.md)

---

## 💡 Tips & Tricks

1. **Use descriptive names**: `ml_sentiment_v3` > `package_1`
2. **Tag liberally**: Tags make discovery easier
3. **Create snapshots before major changes**: Easy rollback
4. **Use GZIP compression**: Good balance of speed and size
5. **Validate packages**: Catch errors early
6. **Hot-swap gradually**: 10% → 50% → 100%
7. **Monitor after hot-swap**: Watch metrics for issues
8. **Keep packages focused**: One concern per package

---

## ❓ FAQ

**Q: Can I update a package in place?**
A: Yes, use `import_package()` with `overwrite_existing=True`.

**Q: How do I share packages between teams?**
A: Export to `.mcp` file and share via file system, S3, or artifact repository.

**Q: What's the difference between hot-swap and gradual rollout?**
A: Hot-swap is instant (100%), gradual rollout deploys incrementally.

**Q: Can I rollback after a hot-swap?**
A: Yes, if you created a snapshot before the swap.

**Q: How do I delete a package?**
A: Use `delete_package(package_id)` (coming soon).

**Q: Are packages portable across OS platforms?**
A: Yes, `.mcp` files are cross-platform.

---

**Made with ❤️ by the MCP Team**  
*Version 1.0.0 - October 2025*

