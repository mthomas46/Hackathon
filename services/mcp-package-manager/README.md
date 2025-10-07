# MCP Package Manager - "Docker for Knowledge Graphs"

**Package, version, and deploy MCP knowledge with zero downtime**

## 📋 Overview

The **MCP Package Manager** brings Docker-like capabilities to knowledge graphs, enabling portable, versionable, and hot-swappable MCP packages. It's the deployment engine for MCP knowledge across systems.

### Key Features

- **Package Export/Import**: Bundle MCP knowledge into portable `.mcp` files
- **Version Control**: Snapshot and rollback packages like Git
- **Hot-Swapping**: Update packages with zero downtime (0ms)
- **Gradual Rollout**: Deploy updates progressively (10% → 100%)
- **Cross-Platform**: Works seamlessly across all platforms
- **Compression**: Multiple formats (gzip, zstd)

## 🏗️ Architecture Role

### Position in MCP Ecosystem

```
┌─────────────────────────────────────────────────────────┐
│                   MCP Ecosystem                          │
│                                                          │
│  ┌──────────────┐         ┌──────────────┐            │
│  │ Tier Manager │────────▶│   Package    │            │
│  │  (Context)   │ Package │   Manager    │            │
│  └──────────────┘         │  (Storage)   │            │
│         │                 └──────────────┘            │
│         │                        │                     │
│         │                        ▼                     │
│         │                 ┌──────────────┐            │
│         │                 │  MCP Store   │            │
│         │                 │  (Backend)   │            │
│         │                 └──────────────┘            │
│         │                        │                     │
│         ▼                        ▼                     │
│  ┌──────────────┐         ┌──────────────┐            │
│  │ Orchestrator │◀────────│  Registry    │            │
│  │ (Deployment) │  Deploy │  (Catalog)   │            │
│  └──────────────┘         └──────────────┘            │
└─────────────────────────────────────────────────────────┘
```

### Core Responsibilities

1. **Package Lifecycle**
   - Create packages with metadata
   - Add knowledge items
   - Validate package integrity
   - Manage package versions

2. **Distribution**
   - Export to `.mcp` files (TAR format)
   - Import from `.mcp` files
   - Cross-system portability
   - Compression & optimization

3. **Deployment**
   - Hot-swap packages (0ms downtime)
   - Gradual rollout strategies
   - Blue-green deployment
   - Rollback capabilities

4. **Discovery**
   - Search by name/tags
   - Version history
   - Package dependencies
   - Usage analytics

## 🔗 Service Interactions

### Inbound: Services That Use Package Manager

| Service | Use Case | Integration |
|---------|----------|-------------|
| **MCP Tier Manager** | Package tier-specific knowledge | Export/import tier contexts |
| **MCP Orchestrator** | Deploy pattern packages | Hot-swap pattern implementations |
| **MCP Registry** | Catalog packages | Sync package metadata |
| **MCP Store** | Store package binaries | Backend for `.mcp` files |
| **Dashboard UI** | Package management interface | CRUD operations, analytics |

### Outbound: Services Package Manager Depends On

| Service | Purpose | Usage |
|---------|---------|-------|
| **MCP Store** | Binary storage | Store `.mcp` files and metadata |
| **MCP Registry** | Package catalog | Register package versions |
| **MCP Performance Store** | Deployment metrics | Track package performance |
| **MCP Logs** | Operation logging | Log all package operations |

## 🎯 Integration Points

### With MCP Tier Manager
```python
# Package tier-specific knowledge
tier_knowledge = tier_manager.get_tier_knowledge(tier_id)

# Create package
package = package_manager.create_package(
    metadata=PackageMetadata(
        name=f"tier_{tier_id}_knowledge",
        version="1.0.0",
        tier_type=tier.type
    )
)

# Add knowledge
for item in tier_knowledge:
    package_manager.add_knowledge_to_package(
        package.package_id,
        content=item.content,
        relevance=item.relevance
    )

# Export
package_manager.export_package(package.package_id, "tier_package.mcp")
```

### With MCP Orchestrator
```python
# Deploy pattern package
result = await orchestrator.deploy_pattern_package(
    pattern_name="rag_enhanced",
    package_path="rag_v2.mcp",
    strategy="gradual",  # Gradual rollout
    percentage=10  # Start with 10%
)
```

### With MCP Registry
```python
# Sync to registry
registry.register_package(
    name=package.metadata.name,
    version=package.metadata.version,
    metadata=package.metadata.to_dict(),
    location=package_path
)
```

## 🚀 Core Components

### 1. Package Creation
```python
from mcp_package_manager import PackageManager, PackageMetadata

manager = PackageManager()

# Create package
metadata = PackageMetadata(
    name="my_package",
    version="1.0.0",
    tags=["production", "ml"]
)
package = manager.create_package(metadata)

# Add knowledge
manager.add_knowledge_to_package(
    package.package_id,
    content="Important knowledge",
    relevance=0.95
)
```

### 2. Export/Import
```python
# Export
from mcp_package_manager import ExportConfig, CompressionType

config = ExportConfig(
    include_metadata=True,
    include_knowledge=True,
    compression=CompressionType.GZIP
)

result = manager.export_package(
    package.package_id,
    "package.mcp",
    config
)

# Import on different system
from mcp_package_manager import ImportConfig

config = ImportConfig(
    validate_metadata=True,
    overwrite_existing=False
)

result = manager.import_package("package.mcp", config)
```

### 3. Hot-Swapping
```python
# Zero-downtime hot-swap
result = manager.hot_swap(
    current_package_id=old_pkg.package_id,
    new_package_id=new_pkg.package_id
)

print(f"Downtime: {result.downtime_ms}ms")  # 0ms

# Gradual rollout
for percentage in [10, 25, 50, 75, 100]:
    result = manager.gradual_rollout(
        current_package_id=stable.package_id,
        new_package_id=beta.package_id,
        percentage=percentage
    )
    # Monitor metrics, then proceed
```

### 4. Version Control
```python
# Create snapshot
snapshot = manager.create_snapshot(
    package.package_id,
    tag="v1.0.0-stable"
)

# List versions
versions = manager.list_versions(package.package_id)

# Rollback
result = manager.rollback(package.package_id, "1.0.0")
```

## 📊 Data Flow

```
Create Package → Add Knowledge → Validate → Export to .mcp
                                               ↓
                                    Store in MCP Store
                                               ↓
                    Import on Target System ←─────
                                ↓
                         Hot-Swap/Deploy
                                ↓
                    Update Registry/Metrics
```

## 🔧 Configuration

### Environment Variables
```bash
MCP_PACKAGE_MANAGER_PORT=8012
MCP_PACKAGE_STORAGE=/data/packages
MCP_STORE_URL=http://mcp-store:8008
MCP_REGISTRY_URL=http://mcp-registry:8006
MAX_PACKAGE_SIZE_MB=1000
```

## 📈 Metrics & Monitoring

### Key Metrics
- Packages created/deployed
- Export/import operations
- Hot-swap operations
- Rollback frequency
- Package size distribution

### Health Checks
- `GET /health` - Service health
- `GET /metrics` - Prometheus metrics
- `GET /packages` - List packages

## 🎓 Usage Examples

### Create & Deploy Package
```python
# 1. Create
metadata = PackageMetadata(
    name="ml_model",
    version="2.0.0",
    tags=["ml", "production"]
)
package = manager.create_package(metadata)

# 2. Add knowledge
manager.add_knowledge_to_package(
    package.package_id,
    content="Model v2 documentation",
    relevance=1.0
)

# 3. Export
manager.export_package(package.package_id, "ml_model_v2.mcp")

# 4. Import on prod
result = manager.import_package("ml_model_v2.mcp")

# 5. Hot-swap
manager.hot_swap(current_pkg_id, result.package_id)
```

## 🔐 Security

- **Authentication**: JWT-based service authentication
- **Authorization**: Package-level access control
- **Validation**: Metadata and content validation
- **Integrity**: Checksums for all packages
- **Encryption**: TLS for transfers

## 🚦 Status

**Current**: Production-Ready ✅
- ✅ 29 unit tests (100% passing)
- ✅ 10 integration tests (100% passing)
- ✅ UI complete (6 tabs)
- ✅ Documentation complete

## 📚 Related Services

- **MCP Store**: Backend storage for `.mcp` files
- **MCP Registry**: Package catalog and discovery
- **MCP Tier Manager**: Source of tier-specific packages
- **MCP Orchestrator**: Package deployment automation
- **MCP Performance Store**: Deployment metrics

## 🔮 Future Enhancements

- Package signing & verification (GPG)
- Differential packages (delta updates)
- Package dependencies management
- Marketplace integration
- Automated testing on import
- CI/CD templates

---

**Version**: 1.0.0  
**Status**: Production-Ready ✅  
**Maintainer**: MCP Team

