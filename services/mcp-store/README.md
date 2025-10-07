# 🎯 MCP Store Service

**"Docker for Knowledge Graphs"** - A versioned package registry for MCP contexts.

Package, version, and distribute knowledge graphs like Docker distributes containers.

---

## 📖 Overview

MCP Store is a package registry service that enables:
- 📦 **Package Management** - Create, update, and manage MCP packages
- 🔢 **Semantic Versioning** - Version packages (1.0.0, 1.2.3-beta, etc.)
- 🔍 **Search & Discovery** - Find packages by name, tags, categories
- 📥 **Upload/Download** - Distribute `.mcp` package files
- 🗜️ **Compression** - Efficient storage with Zstandard
- ☁️ **Binary Storage** - MinIO/S3 for scalable file storage
- 🔐 **Integrity** - SHA256 checksums for verification

---

## 🏗️ Architecture

### **Technology Stack**
- **Framework:** FastAPI 0.104 (async REST API)
- **Database:** SQLite + aiosqlite (metadata)
- **Storage:** MinIO (S3-compatible, binary files)
- **ORM:** SQLAlchemy 2.0 (async)
- **Compression:** Zstandard
- **Validation:** Pydantic 2.5

### **Design Pattern**
Domain-Driven Design (DDD) with 4 layers:
1. **Presentation** - FastAPI REST API
2. **Application** - Use cases + DTOs
3. **Domain** - Entities + repositories
4. **Infrastructure** - SQLite/MinIO implementations

---

## 🚀 Quick Start

### **Using Docker Compose (Recommended)**

```bash
# 1. Clone or navigate to the service directory
cd services/mcp-store

# 2. Start the service with MinIO
docker-compose up -d

# 3. Check health
curl http://localhost:5648/health

# 4. Access API docs
open http://localhost:5648/docs

# 5. Access MinIO console
open http://localhost:9001
# Login: minioadmin / minioadmin
```

### **Local Development**

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start MinIO (in another terminal or Docker)
docker run -d -p 9000:9000 -p 9001:9001 \
  --name minio \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin \
  minio/minio server /data --console-address ":9001"

# 3. Configure environment (optional, has defaults)
cp .env.example .env
# Edit .env as needed

# 4. Run the service
python main.py

# OR with uvicorn
uvicorn main:app --reload --port 5648
```

---

## 📡 API Endpoints

### **Package Endpoints**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/packages` | Create a new package |
| `GET` | `/packages/{package_id}` | Get package details |
| `PUT` | `/packages/{package_id}` | Update package metadata |
| `DELETE` | `/packages/{package_id}` | Delete package |
| `GET` | `/packages` | List & search packages |

### **Version Endpoints**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/packages/{package_id}/versions` | Upload new version |
| `GET` | `/packages/{package_id}/versions/{version_id}` | Get version details |
| `GET` | `/packages/{package_id}/versions` | List versions |
| `GET` | `/packages/{package_id}/versions/{version_id}/download` | Download version |
| `PUT` | `/packages/{package_id}/versions/{version_id}` | Update version metadata |
| `DELETE` | `/packages/{package_id}/versions/{version_id}` | Delete version |

### **Utility Endpoints**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/` | Service info |

---

## 💻 Usage Examples

### **1. Create a Package**

```bash
curl -X POST "http://localhost:5648/packages" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-company-mcp",
    "description": "Company-wide MCP knowledge base",
    "owner_id": "org-123",
    "tags": ["company", "production"],
    "categories": ["knowledge-base"],
    "is_public": false
  }'
```

**Response:**
```json
{
  "package_id": "pkg-abc123",
  "name": "my-company-mcp",
  "description": "Company-wide MCP knowledge base",
  "owner_id": "org-123",
  "status": "draft",
  "tags": ["company", "production"],
  "categories": ["knowledge-base"],
  "is_public": false,
  "download_count": 0,
  "star_count": 0,
  "created_at": "2025-10-07T12:00:00Z",
  "versions": []
}
```

### **2. Upload a Version**

```bash
curl -X POST "http://localhost:5648/packages/pkg-abc123/versions?version_string=1.0.0&release_notes=Initial%20release" \
  -F "file=@my-mcp-package.mcp"
```

**Response:**
```json
{
  "version_id": "ver-xyz789",
  "package_id": "pkg-abc123",
  "version_string": "1.0.0",
  "storage_path": "packages/pkg-abc123/1.0.0.mcp",
  "checksum": "abc123...",
  "size_bytes": 1048576,
  "release_notes": "Initial release",
  "is_active": true,
  "created_at": "2025-10-07T12:05:00Z"
}
```

### **3. Search Packages**

```bash
# Search by keyword
curl "http://localhost:5648/packages?search=company&limit=10"

# Filter by tags
curl "http://localhost:5648/packages?tags=production&sort_by=download_count&sort_order=desc"

# Filter by status and owner
curl "http://localhost:5648/packages?owner_id=org-123&status=published&is_public=false"
```

### **4. Download a Version**

```bash
curl "http://localhost:5648/packages/pkg-abc123/versions/ver-xyz789/download" \
  -o downloaded.mcp
```

### **5. List Versions**

```bash
curl "http://localhost:5648/packages/pkg-abc123/versions"
```

---

## 🔧 Configuration

### **Environment Variables**

| Variable | Description | Default |
|----------|-------------|---------|
| `SERVICE_NAME` | Service name | `mcp-store` |
| `SERVICE_VERSION` | Service version | `1.0.0` |
| `SERVICE_PORT` | HTTP port | `5648` |
| `DATABASE_URL` | SQLite database URL | `sqlite+aiosqlite:///./data/mcp_store.db` |
| `DATABASE_ECHO` | Log SQL queries | `false` |
| `STORAGE_TYPE` | Storage type (`minio` or `s3`) | `minio` |
| `STORAGE_ENDPOINT` | MinIO/S3 endpoint | `localhost:9000` |
| `STORAGE_ACCESS_KEY` | Access key | `minioadmin` |
| `STORAGE_SECRET_KEY` | Secret key | `minioadmin` |
| `STORAGE_BUCKET` | Bucket name | `mcp-packages` |
| `STORAGE_USE_SSL` | Use HTTPS | `false` |

---

## 📊 Database Schema

### **Packages Table**

| Column | Type | Description |
|--------|------|-------------|
| `package_id` | VARCHAR(PK) | Unique package ID (UUID) |
| `name` | VARCHAR(UNIQUE) | Package name |
| `description` | TEXT | Description |
| `owner_id` | VARCHAR | Owner user/org ID |
| `status` | VARCHAR | Status (draft, published, etc.) |
| `tags` | JSON | Array of tags |
| `categories` | JSON | Array of categories |
| `latest_version_id` | VARCHAR(FK) | Latest version ID |
| `download_count` | INTEGER | Total downloads |
| `star_count` | INTEGER | Total stars |
| `is_public` | BOOLEAN | Public visibility |
| `created_at` | TIMESTAMP | Creation time |
| `updated_at` | TIMESTAMP | Last update time |
| `metadata` | JSON | Additional metadata |

### **Versions Table**

| Column | Type | Description |
|--------|------|-------------|
| `version_id` | VARCHAR(PK) | Unique version ID (UUID) |
| `package_id` | VARCHAR(FK) | Parent package ID |
| `version_string` | VARCHAR | Semantic version (e.g., 1.0.0) |
| `storage_path` | VARCHAR | Path in MinIO/S3 |
| `checksum` | VARCHAR | SHA256 checksum |
| `size_bytes` | INTEGER | File size |
| `release_notes` | TEXT | Release notes |
| `is_active` | BOOLEAN | Active status |
| `created_at` | TIMESTAMP | Creation time |
| `updated_at` | TIMESTAMP | Last update time |
| `metadata` | JSON | Additional metadata |

**Constraints:**
- Unique constraint on `(package_id, version_string)`
- Cascade delete from packages to versions

---

## 🧪 Testing

```bash
# Install dev dependencies
pip install pytest pytest-asyncio httpx

# Run tests (when implemented)
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

---

## 🐳 Docker Commands

```bash
# Build image
docker build -t mcp-store:latest .

# Run container
docker run -d -p 5648:5648 --name mcp-store mcp-store:latest

# View logs
docker logs -f mcp-store

# Stop container
docker stop mcp-store

# Using docker-compose
docker-compose up -d      # Start
docker-compose down       # Stop
docker-compose logs -f    # View logs
docker-compose ps         # Status
```

---

## 📈 Monitoring

### **Health Check**
```bash
curl http://localhost:5648/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "mcp-store",
  "version": "1.0.0"
}
```

### **Metrics** (Future)
- Total packages
- Total versions
- Total downloads
- Storage usage
- Request rate

---

## 🔒 Security Considerations

1. **Authentication** - Not yet implemented (add JWT/OAuth2)
2. **Authorization** - Basic owner_id checks
3. **Rate Limiting** - Not yet implemented
4. **Input Validation** - Pydantic models
5. **File Size Limits** - Not yet enforced
6. **Malware Scanning** - Not yet implemented

**For Production:**
- Add authentication middleware
- Implement rate limiting
- Add virus scanning for uploads
- Use HTTPS/TLS
- Implement audit logging

---

## 🔮 Future Enhancements

- [ ] Export/import entire packages as `.mcp` files
- [ ] Package dependency management
- [ ] Package ratings and reviews
- [ ] Usage analytics dashboard
- [ ] Automated testing
- [ ] CI/CD integration
- [ ] Kubernetes deployment
- [ ] Multi-region replication

---

## 📚 Related Services

- **MCP Registry** - Package discovery and registration
- **MCP Provisioner** - MCP lifecycle management
- **MCP Composer** - Compose multiple MCPs
- **Training Coordinator** - Build MCPs from data

---

## 🐛 Troubleshooting

### **MinIO Connection Error**
```
Error: Failed to connect to MinIO
```
**Solution:** Ensure MinIO is running and accessible at the configured endpoint.

### **Database Locked**
```
Error: database is locked
```
**Solution:** SQLite only supports one writer. Use connection pooling or switch to PostgreSQL for production.

### **Large File Upload Fails**
```
Error: Request Entity Too Large
```
**Solution:** Increase FastAPI file size limit or use streaming uploads.

---

## 📝 License

Part of the MCP ecosystem project.

---

## 🤝 Contributing

1. Follow DDD architecture patterns
2. Add tests for new features
3. Update documentation
4. Use type hints
5. Format with black/ruff

---

**Built with ❤️ as part of the MCP ecosystem**

For more information, see the main project documentation.
