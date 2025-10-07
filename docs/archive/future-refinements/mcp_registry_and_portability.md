---
llm_metadata:
  document_type: planning
  content_focus: historical
  platform:
    primary: mcp
    secondary: []
  status: archived
  created_date: '2024-09-01'
  archived_date: '2025-10-07'
  topics:
  - api_gateway
  - fastapi
  - python
  - postgresql
  - docker
  - kubernetes
  - rag
  - embeddings
  concepts: []
  technologies: []
  services_mentioned: []
  semantic_summary: Planning document about historical aspects of the mcp platform
  archive_reason: consolidated
  historical_value: medium
  reference_value: medium
semantic_embedding:
  model: text-embedding-ada-002
  embedding_date: '2025-10-07'
  embedding_checksum: pending
rag_metadata:
  chunk_strategy: semantic
  optimal_chunk_size: 512
  retrieval_priority: medium
---

# 📦 MCP Registry & Portability
## Import, Export, Hot-Swap, and Marketplace for Knowledge Graphs

**Document Type:** Architecture Enhancement  
**Status:** Design Complete  
**Parent Documents:**
- [HIERARCHICAL_MCP_TRAINING_PIPELINE.md](./HIERARCHICAL_MCP_TRAINING_PIPELINE.md)
- [CLIENT_SPECIFIC_MCP_ENHANCEMENT.md](./CLIENT_SPECIFIC_MCP_ENHANCEMENT.md)

**Enhancement:** Adds MCP portability, versioning, marketplace, and developer control  
**Concept:** "Docker for Knowledge Graphs" - portable, shareable, composable MCPs

---

## 📚 Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The MCP Portability Vision](#2-the-mcp-portability-vision)
3. [MCP Package Format](#3-mcp-package-format)
4. [Export Process](#4-export-process)
5. [Import Process](#5-import-process)
6. [MCP Versioning](#6-mcp-versioning)
7. [Hot-Swap Mechanism](#7-hot-swap-mechanism)
8. [MCP Registry & Marketplace](#8-mcp-registry--marketplace)
9. [Developer Control Panel](#9-developer-control-panel)
10. [MCP Composition](#10-mcp-composition)
11. [Use Cases](#11-use-cases)
12. [Implementation Guide](#12-implementation-guide)

---

## 1. Executive Summary

### 1.1 The Vision

**Transform MCPs from services into portable knowledge artifacts:**

```
Current State (Ephemeral):
├─ MCP runs as service
├─ Knowledge stored in databases
├─ If service stops, knowledge inaccessible
└─ No way to share or version knowledge

Enhanced State (Portable):
├─ MCP snapshot = portable package (.mcp file)
├─ Export knowledge at any time
├─ Import pre-trained knowledge
├─ Version MCPs (1.0.0, 2.0.0, etc.)
├─ Share via MCP Registry (public/private)
├─ Hot-swap MCPs without restart
└─ Compose multiple MCPs
```

**Analogy:** "Docker for Knowledge Graphs"
- **Docker Image** → **MCP Package** (.mcp file)
- **Docker Hub** → **MCP Registry** (marketplace)
- **docker pull** → **mcp import**
- **docker push** → **mcp export**
- **docker-compose** → **MCP Composition**

---

### 1.2 Key Capabilities

✅ **Export MCP** → Snapshot knowledge to `.mcp` file  
✅ **Import MCP** → Load pre-trained knowledge  
✅ **Version MCP** → Semantic versioning (1.0.0, 2.0.0)  
✅ **Hot-Swap MCP** → Switch MCP version without restart  
✅ **Share MCP** → Public/private registry  
✅ **Compose MCPs** → Combine multiple MCP packages  
✅ **Developer Control** → UI to manage active MCPs  
✅ **Marketplace** → Browse, search, download MCPs  

---

## 2. The MCP Portability Vision

### 2.1 "Docker for Knowledge Graphs"

**Inspiration:** Docker revolutionized software by making apps portable

**MCP Portability does the same for knowledge:**

| Docker | MCP Portability |
|--------|-----------------|
| **Image** (immutable snapshot) | **MCP Package** (.mcp file) |
| **Container** (running instance) | **MCP Instance** (running service) |
| **Dockerfile** (build instructions) | **MCP Manifest** (metadata) |
| **Docker Hub** (registry) | **MCP Registry** (marketplace) |
| **docker pull** (download) | **mcp import** (load knowledge) |
| **docker push** (upload) | **mcp export** (snapshot knowledge) |
| **docker run** (start) | **mcp start** (provision) |
| **docker-compose** (multi-container) | **mcp compose** (multi-MCP) |
| **Tags** (versions) | **Versions** (1.0.0, 2.0.0) |

---

### 2.2 Use Cases

#### **Use Case 1: Pre-Trained Company MCP**

**Scenario:** New developer joins company

**Old Way:**
1. Developer sets up ecosystem
2. MCPs start with zero knowledge
3. Takes weeks to accumulate useful patterns
4. Recommendations initially generic

**New Way (with MCP Import):**
1. Developer imports pre-trained Company MCP
   ```bash
   mcp import company-mcp:latest
   ```
2. Instantly has 2+ years of company knowledge
3. Day 1 recommendations are hyper-relevant
4. Onboarding time: weeks → hours

---

#### **Use Case 2: Client MCP Marketplace**

**Scenario:** Company works with common platforms (Shopify, Salesforce)

**Old Way:**
1. Each developer figures out Shopify API from scratch
2. Recreates same patterns repeatedly
3. Inconsistent implementations

**New Way (with MCP Marketplace):**
1. Download pre-trained Shopify MCP
   ```bash
   mcp import shopify-integration:latest
   ```
2. Contains:
   - All Shopify API endpoints
   - Authentication patterns
   - Common workflows (cart, checkout, fulfillment)
   - Best practices
   - Code examples
3. Instant expert-level knowledge

---

#### **Use Case 3: MCP Versioning for Rollback**

**Scenario:** MCP receives bad training data

**Old Way:**
1. Bad data corrupts MCP knowledge
2. No way to rollback
3. Must retrain from scratch

**New Way (with MCP Versioning):**
1. Export MCP daily
   ```bash
   mcp export client-a-mcp --tag 2025-10-06
   ```
2. Bad data detected
3. Rollback to previous version
   ```bash
   mcp rollback client-a-mcp --to 2025-10-05
   ```
4. Good knowledge restored

---

#### **Use Case 4: Hot-Swap for A/B Testing**

**Scenario:** Testing new training algorithms

**Old Way:**
1. Retrain MCP with new algorithm
2. If bad, lose all progress
3. Can't compare side-by-side

**New Way (with Hot-Swap):**
1. Create two MCP versions:
   - v1: Old algorithm
   - v2: New algorithm
2. Hot-swap between versions
   ```bash
   mcp swap client-a-mcp --version v2
   ```
3. Compare recommendation quality
4. Switch back if worse
   ```bash
   mcp swap client-a-mcp --version v1
   ```

---

#### **Use Case 5: Developer Customization**

**Scenario:** Developer wants minimal vs maximal knowledge

**Old Way:**
1. All MCPs always running
2. No control over knowledge scope

**New Way (with Developer Control):**
1. Developer chooses active MCPs:
   - ✅ Ecosystem MCP (self)
   - ✅ Team MCP (backend-team)
   - ✅ Company MCP (standards)
   - ❌ Project MCP (not needed now)
   - ✅ Client MCP (client-a only)
2. Recommendations hyper-focused
3. Faster queries (fewer MCPs)

---

## 3. MCP Package Format

### 3.1 MCP Package Structure

**An MCP Package (.mcp file) is a tarball containing:**

```
my-mcp-package-v1.0.0.mcp
├── manifest.json              # Metadata (name, version, description)
├── chromadb/                  # Vector database snapshot
│   ├── collections/
│   │   ├── code_patterns.parquet
│   │   ├── work_patterns.parquet
│   │   └── documentation.parquet
│   └── metadata.json
├── neo4j/                     # Graph database snapshot
│   ├── nodes.jsonl            # All nodes
│   ├── relationships.jsonl    # All relationships
│   └── schema.json            # Graph schema
├── config/                    # Configuration
│   ├── mcp_config.yaml        # MCP settings
│   └── resources.yaml         # Resource definitions
├── metadata/                  # Training metadata
│   ├── training_history.json  # When/how trained
│   ├── data_sources.json      # What data was used
│   └── statistics.json        # Stats (# patterns, # docs, etc.)
└── README.md                  # Human-readable description
```

---

### 3.2 Manifest Format

**`manifest.json`:**

```json
{
  "name": "company-mcp",
  "version": "2.5.3",
  "description": "Pre-trained Company MCP with 2 years of knowledge",
  "tier": 2,
  "tier_name": "Company",
  "created_at": "2025-10-06T14:30:00Z",
  "created_by": "mykal-thomas",
  "size_mb": 1234,
  "license": "MIT",
  "tags": ["company", "standards", "best-practices"],
  "compatibility": {
    "min_mcp_version": "1.0.0",
    "chromadb_version": "0.4.0",
    "neo4j_version": "5.12"
  },
  "statistics": {
    "total_patterns": 15234,
    "total_documents": 5678,
    "total_relationships": 23456,
    "training_hours": 1460,
    "data_sources": ["github", "jira", "confluence"],
    "date_range": {
      "start": "2023-01-01",
      "end": "2025-10-06"
    }
  },
  "dependencies": [],
  "changelog": {
    "2.5.3": "Added 500 new patterns from Q3 2025",
    "2.5.0": "Integrated new team best practices",
    "2.0.0": "Major update: restructured knowledge graph"
  },
  "checksum": "sha256:a3b5c7d9e1f2..."
}
```

---

### 3.3 Package Types

| Package Type | Tier | Typical Size | Sharing |
|--------------|------|--------------|---------|
| **Ecosystem MCP** | 4 | 100-500 MB | Private (personal) |
| **Team MCP** | 3 | 500 MB - 2 GB | Private (team only) |
| **Company MCP** | 2 | 1-5 GB | Private (company only) |
| **Project MCP** | 1 | 200 MB - 1 GB | Private (project team) |
| **Client MCP** | 0 | 500 MB - 2 GB | Private (client team) |
| **Public MCP** | Any | Varies | Public (marketplace) |

**Public MCP Examples:**
- `python-fastapi-patterns:latest` (1.2 GB)
- `react-hooks-best-practices:2.0.0` (800 MB)
- `shopify-integration:latest` (1.5 GB)
- `aws-serverless-patterns:latest` (2 GB)

---

## 4. Export Process

### 4.1 Export Command

**CLI:**

```bash
# Export running MCP to package
mcp export <mcp-name> [options]

# Examples:
mcp export company-mcp
mcp export company-mcp --tag 2.5.3
mcp export company-mcp --tag latest --description "Q3 2025 update"
mcp export client-a-mcp --output ./exports/
mcp export team-mcp --compress gzip
```

**API:**

```http
POST /mcp/export
{
  "mcp_name": "company-mcp",
  "tag": "2.5.3",
  "description": "Q3 2025 update",
  "include_training_data": false,
  "compress": true
}

Response:
{
  "export_id": "exp_abc123",
  "status": "in_progress",
  "estimated_time": 120
}
```

---

### 4.2 Export Process (Internal)

```python
# services/mcp-registry/domain/exporters/mcp_exporter.py

import tarfile
import json
import shutil
from pathlib import Path
import hashlib

class MCPExporter:
    """Export MCP to portable package"""
    
    async def export_mcp(
        self,
        mcp_name: str,
        tag: str = "latest",
        description: str = "",
        output_dir: Path = Path("./exports")
    ) -> Path:
        """
        Export MCP to .mcp package
        
        Returns: Path to .mcp file
        """
        
        print(f"📦 Exporting {mcp_name}:{tag}...")
        
        # 1. Create temporary directory
        temp_dir = Path(f"/tmp/mcp-export-{mcp_name}")
        temp_dir.mkdir(exist_ok=True)
        
        # 2. Export ChromaDB (vector database)
        print("  ├─ Exporting ChromaDB...")
        chromadb_path = temp_dir / "chromadb"
        await self._export_chromadb(mcp_name, chromadb_path)
        
        # 3. Export Neo4j (graph database)
        print("  ├─ Exporting Neo4j...")
        neo4j_path = temp_dir / "neo4j"
        await self._export_neo4j(mcp_name, neo4j_path)
        
        # 4. Export configuration
        print("  ├─ Exporting configuration...")
        config_path = temp_dir / "config"
        await self._export_config(mcp_name, config_path)
        
        # 5. Generate metadata
        print("  ├─ Generating metadata...")
        metadata_path = temp_dir / "metadata"
        await self._generate_metadata(mcp_name, metadata_path)
        
        # 6. Generate manifest
        print("  ├─ Generating manifest...")
        manifest = await self._generate_manifest(
            mcp_name=mcp_name,
            tag=tag,
            description=description,
            size_mb=self._calculate_size(temp_dir)
        )
        
        with open(temp_dir / "manifest.json", "w") as f:
            json.dump(manifest, f, indent=2)
        
        # 7. Generate README
        print("  ├─ Generating README...")
        await self._generate_readme(manifest, temp_dir / "README.md")
        
        # 8. Create tarball
        print("  ├─ Creating tarball...")
        package_name = f"{mcp_name}-v{tag}.mcp"
        package_path = output_dir / package_name
        
        with tarfile.open(package_path, "w:gz") as tar:
            tar.add(temp_dir, arcname=".")
        
        # 9. Calculate checksum
        print("  ├─ Calculating checksum...")
        checksum = self._calculate_checksum(package_path)
        
        # 10. Update manifest with checksum
        manifest['checksum'] = f"sha256:{checksum}"
        
        # 11. Clean up temp directory
        shutil.rmtree(temp_dir)
        
        print(f"  └─ ✅ Exported to {package_path}")
        print(f"     Size: {self._format_size(package_path.stat().st_size)}")
        print(f"     Checksum: {checksum[:16]}...")
        
        return package_path
    
    async def _export_chromadb(self, mcp_name: str, output_path: Path):
        """Export ChromaDB collections"""
        
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Get ChromaDB client
        chroma = self._get_chromadb_client(mcp_name)
        
        # Get all collections
        collections = chroma.list_collections()
        
        collections_path = output_path / "collections"
        collections_path.mkdir(exist_ok=True)
        
        for collection in collections:
            # Export collection to parquet
            data = collection.get(include=['documents', 'metadatas', 'embeddings'])
            
            # Save as parquet (efficient storage)
            import pandas as pd
            df = pd.DataFrame({
                'id': data['ids'],
                'document': data['documents'],
                'metadata': [json.dumps(m) for m in data['metadatas']],
                'embedding': data['embeddings']
            })
            
            df.to_parquet(collections_path / f"{collection.name}.parquet")
        
        # Save metadata
        metadata = {
            'collections': [c.name for c in collections],
            'total_items': sum(c.count() for c in collections)
        }
        
        with open(output_path / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)
    
    async def _export_neo4j(self, mcp_name: str, output_path: Path):
        """Export Neo4j graph"""
        
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Get Neo4j driver
        driver = self._get_neo4j_driver(mcp_name)
        
        with driver.session() as session:
            # Export all nodes
            nodes_result = session.run("MATCH (n) RETURN n")
            
            with open(output_path / "nodes.jsonl", "w") as f:
                for record in nodes_result:
                    node = record['n']
                    f.write(json.dumps({
                        'id': node.id,
                        'labels': list(node.labels),
                        'properties': dict(node)
                    }) + "\n")
            
            # Export all relationships
            rels_result = session.run("MATCH ()-[r]->() RETURN r")
            
            with open(output_path / "relationships.jsonl", "w") as f:
                for record in rels_result:
                    rel = record['r']
                    f.write(json.dumps({
                        'id': rel.id,
                        'type': rel.type,
                        'start_node': rel.start_node.id,
                        'end_node': rel.end_node.id,
                        'properties': dict(rel)
                    }) + "\n")
            
            # Export schema
            schema = session.run("CALL db.schema.visualization()").single()
            
            with open(output_path / "schema.json", "w") as f:
                json.dump(dict(schema), f, indent=2)
    
    async def _generate_manifest(
        self,
        mcp_name: str,
        tag: str,
        description: str,
        size_mb: float
    ) -> dict:
        """Generate manifest.json"""
        
        # Get MCP metadata
        mcp_metadata = await self._get_mcp_metadata(mcp_name)
        
        # Get statistics
        stats = await self._calculate_statistics(mcp_name)
        
        manifest = {
            "name": mcp_name,
            "version": tag,
            "description": description or f"MCP package for {mcp_name}",
            "tier": mcp_metadata.get('tier'),
            "tier_name": mcp_metadata.get('tier_name'),
            "created_at": datetime.now().isoformat(),
            "created_by": mcp_metadata.get('owner'),
            "size_mb": size_mb,
            "license": mcp_metadata.get('license', 'Proprietary'),
            "tags": mcp_metadata.get('tags', []),
            "compatibility": {
                "min_mcp_version": "1.0.0",
                "chromadb_version": "0.4.0",
                "neo4j_version": "5.12"
            },
            "statistics": stats,
            "dependencies": [],
            "checksum": ""  # Filled later
        }
        
        return manifest
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum"""
        
        sha256 = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        
        return sha256.hexdigest()
```

---

### 4.3 Export Automation

**Scheduled Exports (Cron):**

```yaml
# config/export_schedule.yaml

scheduled_exports:
  - name: daily_company_mcp
    mcp: company-mcp
    schedule: "0 2 * * *"  # 2 AM daily
    tag: "daily-${DATE}"
    retention: 30  # Keep last 30 days
    
  - name: weekly_team_mcp
    mcp: team-backend-mcp
    schedule: "0 3 * * 0"  # 3 AM Sunday
    tag: "weekly-${WEEK}"
    retention: 12  # Keep last 12 weeks
    
  - name: release_ecosystem_mcp
    mcp: ecosystem-mykal-mcp
    trigger: "on_release"
    tag: "${VERSION}"
```

**Trigger on Events:**

```python
# Auto-export on significant events

@app.on_event("mcp_trained")
async def auto_export_on_training(event: Dict):
    """Auto-export after significant training"""
    
    patterns_added = event['patterns_added']
    
    if patterns_added > 1000:  # Significant update
        await mcp_exporter.export_mcp(
            mcp_name=event['mcp_name'],
            tag=f"auto-{datetime.now().strftime('%Y%m%d-%H%M')}"
        )
```

---

## 5. Import Process

### 5.1 Import Command

**CLI:**

```bash
# Import MCP package
mcp import <package-file-or-url> [options]

# Examples:
mcp import company-mcp-v2.5.3.mcp
mcp import ./exports/team-mcp-v1.0.0.mcp --overwrite
mcp import https://registry.example.com/shopify-integration:latest
mcp import shopify-integration:latest --from-registry
mcp import client-a-mcp-v1.0.0.mcp --name client-a-mcp-restored
```

**API:**

```http
POST /mcp/import
{
  "source": "company-mcp-v2.5.3.mcp",
  "overwrite": false,
  "start_after_import": true
}

Response:
{
  "import_id": "imp_xyz789",
  "status": "in_progress",
  "estimated_time": 180
}
```

---

### 5.2 Import Process (Internal)

```python
# services/mcp-registry/domain/importers/mcp_importer.py

import tarfile
import json
from pathlib import Path

class MCPImporter:
    """Import MCP from package"""
    
    async def import_mcp(
        self,
        package_path: Path,
        overwrite: bool = False,
        name: Optional[str] = None
    ) -> str:
        """
        Import MCP from .mcp package
        
        Returns: MCP name
        """
        
        print(f"📥 Importing MCP from {package_path.name}...")
        
        # 1. Extract package to temporary directory
        temp_dir = Path(f"/tmp/mcp-import-{uuid.uuid4()}")
        temp_dir.mkdir(exist_ok=True)
        
        print("  ├─ Extracting package...")
        with tarfile.open(package_path, "r:gz") as tar:
            tar.extractall(temp_dir)
        
        # 2. Load and validate manifest
        print("  ├─ Validating manifest...")
        manifest = self._load_manifest(temp_dir / "manifest.json")
        
        await self._validate_manifest(manifest)
        await self._check_compatibility(manifest)
        
        mcp_name = name or manifest['name']
        
        # 3. Check if MCP already exists
        if await self._mcp_exists(mcp_name) and not overwrite:
            raise ValueError(f"MCP '{mcp_name}' already exists. Use --overwrite to replace.")
        
        # 4. Verify checksum
        print("  ├─ Verifying checksum...")
        expected_checksum = manifest['checksum'].replace('sha256:', '')
        actual_checksum = self._calculate_checksum(package_path)
        
        if expected_checksum != actual_checksum:
            raise ValueError("Checksum mismatch! Package may be corrupted.")
        
        # 5. Import ChromaDB
        print("  ├─ Importing ChromaDB...")
        await self._import_chromadb(temp_dir / "chromadb", mcp_name)
        
        # 6. Import Neo4j
        print("  ├─ Importing Neo4j...")
        await self._import_neo4j(temp_dir / "neo4j", mcp_name)
        
        # 7. Import configuration
        print("  ├─ Importing configuration...")
        await self._import_config(temp_dir / "config", mcp_name)
        
        # 8. Register MCP in registry
        print("  ├─ Registering MCP...")
        await self._register_mcp(mcp_name, manifest)
        
        # 9. Clean up temp directory
        shutil.rmtree(temp_dir)
        
        print(f"  └─ ✅ Imported {mcp_name}:{manifest['version']}")
        print(f"     Patterns: {manifest['statistics']['total_patterns']}")
        print(f"     Documents: {manifest['statistics']['total_documents']}")
        
        return mcp_name
    
    async def _import_chromadb(self, source_path: Path, mcp_name: str):
        """Import ChromaDB collections"""
        
        # Get ChromaDB client for this MCP
        chroma = self._get_chromadb_client(mcp_name)
        
        # Load metadata
        with open(source_path / "metadata.json") as f:
            metadata = json.load(f)
        
        # Import each collection
        collections_path = source_path / "collections"
        
        for collection_name in metadata['collections']:
            # Load parquet file
            import pandas as pd
            df = pd.read_parquet(collections_path / f"{collection_name}.parquet")
            
            # Create or get collection
            collection = chroma.get_or_create_collection(collection_name)
            
            # Add all items
            collection.add(
                ids=df['id'].tolist(),
                documents=df['document'].tolist(),
                metadatas=[json.loads(m) for m in df['metadata']],
                embeddings=df['embedding'].tolist()
            )
    
    async def _import_neo4j(self, source_path: Path, mcp_name: str):
        """Import Neo4j graph"""
        
        # Get Neo4j driver for this MCP
        driver = self._get_neo4j_driver(mcp_name)
        
        with driver.session() as session:
            # Clear existing graph (if overwrite)
            session.run("MATCH (n) DETACH DELETE n")
            
            # Import nodes
            node_id_map = {}  # Old ID → New ID
            
            with open(source_path / "nodes.jsonl") as f:
                for line in f:
                    node_data = json.loads(line)
                    
                    # Create node
                    labels = ":".join(node_data['labels'])
                    props = node_data['properties']
                    
                    result = session.run(
                        f"CREATE (n:{labels}) SET n = $props RETURN id(n) as new_id",
                        props=props
                    )
                    
                    new_id = result.single()['new_id']
                    node_id_map[node_data['id']] = new_id
            
            # Import relationships
            with open(source_path / "relationships.jsonl") as f:
                for line in f:
                    rel_data = json.loads(line)
                    
                    # Map old IDs to new IDs
                    start_id = node_id_map[rel_data['start_node']]
                    end_id = node_id_map[rel_data['end_node']]
                    
                    # Create relationship
                    session.run(
                        f"""
                        MATCH (a), (b)
                        WHERE id(a) = $start_id AND id(b) = $end_id
                        CREATE (a)-[r:{rel_data['type']}]->(b)
                        SET r = $props
                        """,
                        start_id=start_id,
                        end_id=end_id,
                        props=rel_data['properties']
                    )
```

---

## 6. MCP Versioning

### 6.1 Semantic Versioning

**Follow Semantic Versioning (semver):**

```
MAJOR.MINOR.PATCH

Examples:
1.0.0 → Initial release
1.1.0 → New patterns added (backward compatible)
1.1.1 → Bug fixes
2.0.0 → Breaking changes (knowledge restructured)
```

**Version Tags:**

```bash
# Version tags
company-mcp:1.0.0
company-mcp:1.2.3
company-mcp:2.0.0
company-mcp:latest  # Points to highest version

# Special tags
company-mcp:stable     # Last stable release
company-mcp:beta       # Beta testing
company-mcp:nightly    # Daily snapshot
```

---

### 6.2 Version History

**Track all versions:**

```json
{
  "mcp_name": "company-mcp",
  "versions": [
    {
      "version": "2.5.3",
      "released_at": "2025-10-06T14:30:00Z",
      "size_mb": 1234,
      "patterns": 15234,
      "changelog": "Added 500 new patterns from Q3 2025"
    },
    {
      "version": "2.5.0",
      "released_at": "2025-09-01T10:00:00Z",
      "size_mb": 1180,
      "patterns": 14734,
      "changelog": "Integrated new team best practices"
    },
    {
      "version": "2.0.0",
      "released_at": "2025-06-15T08:00:00Z",
      "size_mb": 980,
      "patterns": 12000,
      "changelog": "Major update: restructured knowledge graph"
    }
  ]
}
```

---

## 7. Hot-Swap Mechanism

### 7.1 Hot-Swap Process

**Switch MCP version without restarting services:**

```bash
# Current: company-mcp:2.5.0
# Want: company-mcp:2.5.3

mcp swap company-mcp --version 2.5.3

# Process:
# 1. Load new version into memory
# 2. Warm up (prepare for queries)
# 3. Switch active version (atomic)
# 4. Unload old version
# Total downtime: <1 second
```

---

### 7.2 Hot-Swap Implementation

```python
# services/mcp-provisioner/domain/hot_swap.py

class MCPHotSwapper:
    """Hot-swap MCP versions without downtime"""
    
    def __init__(self):
        self.active_mcps = {}  # mcp_name → active version
        self.loaded_mcps = {}  # (mcp_name, version) → loaded instance
    
    async def hot_swap(
        self,
        mcp_name: str,
        target_version: str,
        warmup_queries: List[str] = None
    ):
        """
        Hot-swap MCP to different version
        
        Zero-downtime swap!
        """
        
        current_version = self.active_mcps.get(mcp_name)
        
        print(f"🔄 Hot-swapping {mcp_name}:")
        print(f"   Current: {current_version}")
        print(f"   Target:  {target_version}")
        
        # 1. Check if target version is already loaded
        if (mcp_name, target_version) in self.loaded_mcps:
            print("  ├─ Target version already loaded (instant swap)")
        else:
            # 2. Load target version (in background)
            print("  ├─ Loading target version...")
            await self._load_mcp_version(mcp_name, target_version)
        
        # 3. Warm up new version
        print("  ├─ Warming up new version...")
        if warmup_queries:
            await self._warmup_mcp(mcp_name, target_version, warmup_queries)
        
        # 4. Atomic swap (change pointer)
        print("  ├─ Swapping (atomic)...")
        old_version = self.active_mcps[mcp_name]
        self.active_mcps[mcp_name] = target_version
        
        # 5. Wait for in-flight queries to complete
        print("  ├─ Draining in-flight queries...")
        await self._drain_queries(mcp_name, old_version)
        
        # 6. Unload old version (optional, can keep for quick rollback)
        if self._should_unload(mcp_name, old_version):
            print("  ├─ Unloading old version...")
            await self._unload_mcp_version(mcp_name, old_version)
        else:
            print("  ├─ Keeping old version loaded (for quick rollback)")
        
        print(f"  └─ ✅ Swapped to {mcp_name}:{target_version}")
    
    async def _load_mcp_version(self, mcp_name: str, version: str):
        """Load MCP version into memory"""
        
        # Import MCP package
        package_path = await self._get_package_path(mcp_name, version)
        
        mcp_instance = await mcp_importer.import_mcp(
            package_path=package_path,
            name=f"{mcp_name}-{version}"  # Unique name for this version
        )
        
        # Start MCP service
        await mcp_provisioner.provision_mcp(f"{mcp_name}-{version}")
        
        # Store in loaded_mcps
        self.loaded_mcps[(mcp_name, version)] = mcp_instance
    
    async def _warmup_mcp(
        self,
        mcp_name: str,
        version: str,
        warmup_queries: List[str]
    ):
        """Warm up MCP with common queries"""
        
        mcp_url = await self._get_mcp_url(mcp_name, version)
        
        # Run warmup queries
        for query in warmup_queries:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{mcp_url}/query",
                    json={"query": query},
                    timeout=30.0
                )
    
    async def _drain_queries(self, mcp_name: str, version: str):
        """Wait for in-flight queries to complete"""
        
        # Check active query count
        while True:
            active_queries = await self._get_active_query_count(mcp_name, version)
            
            if active_queries == 0:
                break
            
            await asyncio.sleep(0.1)  # Wait 100ms
```

---

### 7.3 Rollback Command

**Quick rollback to previous version:**

```bash
# Rollback to previous version
mcp rollback company-mcp

# Rollback to specific version
mcp rollback company-mcp --to 2.5.0

# Rollback to specific date
mcp rollback company-mcp --to 2025-10-05
```

---

## 8. MCP Registry & Marketplace

### 8.1 MCP Registry Architecture

**Central registry for sharing MCPs:**

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP REGISTRY                             │
│            https://registry.mcp.example.com                 │
└─────────────────────────────────────────────────────────────┘

Components:
├─ Storage Backend (S3/MinIO)
│   └─ Stores .mcp packages
├─ Metadata Database (PostgreSQL)
│   └─ Package info, versions, downloads, ratings
├─ Search Engine (Elasticsearch)
│   └─ Full-text search for packages
├─ API Server (FastAPI)
│   └─ Upload, download, search endpoints
└─ Web UI (React)
    └─ Browse, search, download packages
```

---

### 8.2 Registry API

**Upload MCP:**

```http
POST /registry/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: company-mcp-v2.5.3.mcp
visibility: private | public
license: MIT
tags: ["company", "standards"]

Response:
{
  "package_id": "pkg_abc123",
  "name": "company-mcp",
  "version": "2.5.3",
  "url": "https://registry.mcp.example.com/company-mcp:2.5.3",
  "download_url": "https://registry.mcp.example.com/download/pkg_abc123"
}
```

**Download MCP:**

```http
GET /registry/download/{package_name}:{version}

Response:
Binary .mcp file
```

**Search MCPs:**

```http
GET /registry/search?q=shopify&tags=integration

Response:
{
  "results": [
    {
      "name": "shopify-integration",
      "version": "1.5.0",
      "description": "Pre-trained MCP for Shopify API integration",
      "downloads": 1234,
      "rating": 4.8,
      "size_mb": 1500,
      "created_at": "2025-09-01T10:00:00Z"
    }
  ],
  "total": 1
}
```

---

### 8.3 Public MCP Marketplace

**Example Public MCPs:**

```
Popular MCPs:
├─ python-fastapi-patterns:latest (4.9★, 5.2K downloads)
│   └─ FastAPI best practices, 2000+ patterns
├─ react-hooks-best-practices:2.0.0 (4.7★, 3.8K downloads)
│   └─ React Hooks patterns, performance tips
├─ shopify-integration:latest (4.8★, 2.1K downloads)
│   └─ Shopify API, webhooks, authentication
├─ aws-serverless-patterns:latest (4.6★, 1.9K downloads)
│   └─ Lambda, API Gateway, DynamoDB patterns
├─ kubernetes-deployment:latest (4.5★, 1.5K downloads)
│   └─ K8s best practices, Helm charts
└─ stripe-payments:latest (4.7★, 1.3K downloads)
    └─ Stripe API, payment flows, webhooks
```

---

## 9. Developer Control Panel

### 9.1 Web UI for MCP Management

**Dashboard:**

```
┌────────────────────────────────────────────────────────────┐
│  MCP Control Panel                           [mykal-thomas] │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Active MCPs                                [+ Import MCP]  │
│  ──────────────────────────────────────────────────────    │
│                                                            │
│  ✅ Ecosystem MCP (mykal)                    v1.5.2  🔄 HOT │
│     Personal patterns                        1.2 GB        │
│     [Settings] [Export] [Swap Version]                     │
│                                                            │
│  ✅ Team MCP (backend-team)                  v2.1.0  🔄 HOT │
│     Team practices                           2.5 GB        │
│     [Settings] [Export] [Swap Version]                     │
│                                                            │
│  ✅ Company MCP                               v2.5.3  🔄 HOT │
│     Company standards                        4.2 GB        │
│     [Settings] [Export] [Swap Version]                     │
│                                                            │
│  ❌ Project MCP (api-v2)                     v1.0.0  ❄️ COLD │
│     Not currently needed                     800 MB        │
│     [Activate]                                             │
│                                                            │
│  ✅ Client MCP (client-a)                    v1.2.1  🔄 HOT │
│     Healthcare client                        1.8 GB        │
│     [Settings] [Export] [Swap Version]                     │
│                                                            │
│  ──────────────────────────────────────────────────────    │
│  Total Active: 4 / 5 MCPs                   9.7 GB / 50 GB │
│                                                            │
│  Marketplace                              [Browse All →]   │
│  ──────────────────────────────────────────────────────    │
│                                                            │
│  🔥 shopify-integration:latest               1.5 GB  4.8★  │
│     Shopify API integration                               │
│     [Import] [Preview]                     2.1K downloads  │
│                                                            │
│  🔥 aws-serverless-patterns:latest           2.0 GB  4.6★  │
│     AWS Lambda, API Gateway patterns                      │
│     [Import] [Preview]                     1.9K downloads  │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

### 9.2 Fine-Grained Control

**Per-MCP Settings:**

```
┌────────────────────────────────────────────────────────────┐
│  Company MCP Settings                                      │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  General                                                   │
│  ├─ Status: ● Active                                       │
│  ├─ Version: 2.5.3                                         │
│  ├─ Auto-update: [x] Enable                                │
│  └─ Query priority: High                                   │
│                                                            │
│  Knowledge Filtering                                       │
│  ├─ Include patterns from:                                 │
│  │   [x] All teams                                         │
│  │   [ ] My team only                                      │
│  ├─ Date range:                                            │
│  │   From: [2023-01-01] To: [2025-10-06]                  │
│  └─ Confidence threshold: [━━━━━●───] 70%                  │
│                                                            │
│  Resource Limits                                           │
│  ├─ Max memory: [━━━━●──────] 5 GB                         │
│  ├─ Max query time: [━━●────────] 10 seconds               │
│  └─ Cache size: [━━━●───────] 1 GB                         │
│                                                            │
│  [Save] [Reset to Defaults]                                │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## 10. MCP Composition

### 10.1 Combine Multiple MCPs

**Problem:** Want knowledge from multiple sources

**Solution:** MCP Composition (like docker-compose)

**`mcp-compose.yaml`:**

```yaml
version: "1.0"

mcps:
  # Personal MCP
  ecosystem-mcp:
    import: mykal-ecosystem-mcp:latest
    active: true
    priority: 1  # Highest priority
    
  # Team MCP
  team-mcp:
    import: backend-team-mcp:latest
    active: true
    priority: 2
    
  # Company MCP
  company-mcp:
    import: company-mcp:2.5.3
    active: true
    priority: 3
    
  # Client MCP
  client-a-mcp:
    import: client-a-healthcare-mcp:1.2.1
    active: true
    priority: 4
    
  # Public MCP (Shopify)
  shopify-mcp:
    import: shopify-integration:latest
    from_registry: https://registry.mcp.example.com
    active: false  # Not active by default
    priority: 5

# Rules for combining knowledge
composition_rules:
  # When multiple MCPs have same pattern, use priority
  conflict_resolution: priority
  
  # Query all active MCPs, synthesize response
  query_strategy: all
  
  # Cache synthesized responses
  cache_enabled: true
  cache_ttl: 3600  # 1 hour
```

**Usage:**

```bash
# Start all MCPs from compose file
mcp-compose up

# Start specific MCPs
mcp-compose up ecosystem-mcp team-mcp

# Stop all
mcp-compose down

# Check status
mcp-compose ps
```

---

### 10.2 Layered Knowledge

**MCPs stack like Docker layers:**

```
Query: "How do I authenticate users for Client A?"

Layer 1 (Bottom): Company MCP
  → "Use OAuth2 + JWT (company standard)"

Layer 2: Team MCP
  → "Backend team uses FastAPI dependencies"

Layer 3: Client A MCP
  → "Client A requires SAML 2.0 + MFA (HIPAA)"

Layer 4 (Top): Ecosystem MCP (mykal)
  → "Alice prefers async/await, specific exceptions"

Result: Synthesized from all 4 layers
```

---

## 11. Use Cases

### 11.1 New Developer Onboarding

**Before (No MCP Portability):**
- Day 1: Developer has zero knowledge
- Week 1: Generic recommendations
- Month 1: Starting to get useful patterns
- Month 3: Finally has good context

**After (With MCP Import):**
```bash
# Day 1:
mcp import company-mcp:latest
mcp import team-backend-mcp:latest

# Instantly:
# - 2 years of company knowledge
# - All team best practices
# - Day 1 recommendations are expert-level
```

---

### 11.2 Client Project Kickoff

**Before:**
- Weeks to understand client's APIs, workflows
- Recreate patterns from scratch
- Inconsistent implementations

**After:**
```bash
mcp import client-a-healthcare-mcp:latest

# Instantly know:
# - Epic FHIR API endpoints
# - HIPAA compliance requirements
# - Patient intake workflow
# - Medical terminology
```

---

### 11.3 Contractor/Consultant Integration

**Scenario:** Hire contractor for 3-month project

**Before:**
- Weeks of onboarding
- Generic code
- Leaves, takes knowledge with them

**After:**
```bash
# Give contractor:
mcp import company-mcp:latest  # Company standards
mcp import project-xyz-mcp:latest  # Project context

# Contractor productive Day 1

# When done:
mcp export contractor-contributions --tag contractor-final
# Keep their patterns!
```

---

### 11.4 A/B Testing Training Algorithms

**Scenario:** New training algorithm, want to test

**Before:**
- Retrain MCP
- If bad, lose all progress
- Can't compare

**After:**
```bash
# Baseline
mcp export company-mcp --tag baseline

# Train with new algorithm
mcp train company-mcp --algorithm new

# Test
mcp swap company-mcp --version new

# If worse, rollback instantly
mcp rollback company-mcp --to baseline
```

---

## 12. Implementation Guide

### 12.1 New Services

**`mcp-registry` (Port 5400):**
- Upload/download MCP packages
- Search marketplace
- Version management
- Access control

**`mcp-composer` (Port 5410):**
- MCP composition (mcp-compose.yaml)
- Start/stop multiple MCPs
- Synthesize knowledge from multiple sources

**Enhanced `mcp-provisioner`:**
- Import/export commands
- Hot-swap capability
- Version tracking

---

### 12.2 Storage Requirements

**Per-MCP Package:**
- Ecosystem MCP: 100-500 MB
- Team MCP: 500 MB - 2 GB
- Company MCP: 1-5 GB
- Client MCP: 500 MB - 2 GB

**Registry Storage:**
- 100 packages × 2 GB avg = 200 GB
- With versions (10 versions/package) = 2 TB
- Recommendation: S3/MinIO for cost-effective storage

---

### 12.3 CLI Tool

```bash
# Install MCP CLI
pip install mcp-cli

# Export
mcp export company-mcp --tag 2.5.3

# Import
mcp import company-mcp-v2.5.3.mcp

# Hot-swap
mcp swap company-mcp --version 2.5.3

# Rollback
mcp rollback company-mcp

# List versions
mcp versions company-mcp

# Registry
mcp search shopify
mcp pull shopify-integration:latest
mcp push company-mcp:2.5.3 --registry https://registry.mcp.example.com

# Compose
mcp-compose up
mcp-compose down
mcp-compose ps
```

---

## 13. Conclusion

### 13.1 Summary

You now have a complete architecture for **MCP Portability**:

✅ **Export MCP** → Snapshot to .mcp file (like Docker image)  
✅ **Import MCP** → Load pre-trained knowledge  
✅ **Version MCP** → Semantic versioning, rollback capability  
✅ **Hot-Swap MCP** → Switch versions without downtime  
✅ **Share MCP** → Public/private registry (marketplace)  
✅ **Compose MCPs** → Combine multiple MCPs (like docker-compose)  
✅ **Developer Control** → Fine-grained control over active MCPs  
✅ **Marketplace** → Browse, search, download public MCPs  

**This makes MCPs:**
- **Portable** (take knowledge anywhere)
- **Shareable** (collaborate across teams)
- **Versioned** (track evolution, rollback if needed)
- **Composable** (combine knowledge sources)
- **Customizable** (developer controls what's active)

---

### 13.2 The Transformation

**Before:**
- MCPs = ephemeral services
- Knowledge locked in databases
- No sharing, no versioning
- All or nothing (can't customize)

**After:**
- MCPs = portable packages
- Knowledge = shareable artifact
- Full versioning & rollback
- Marketplace of pre-trained MCPs
- Developer controls active knowledge
- Compose multiple MCPs
- Hot-swap without downtime

**This is "Docker for Knowledge Graphs"!** 🐳🧠

---

📍 **Location:** `/docs/MCP_REGISTRY_AND_PORTABILITY.md`  
📄 **Status:** Design complete  
🎯 **Enhancement:** MCP export, import, versioning, marketplace  
📊 **Concept:** "Docker for Knowledge Graphs"  
⏱️ **Timeline:** 8-10 weeks to implement  
💾 **Storage:** ~2 TB for 100 packages with 10 versions each  

**Your MCP architecture is now a COMPLETE ECOSYSTEM with portability, sharing, and marketplace!** 🚀


