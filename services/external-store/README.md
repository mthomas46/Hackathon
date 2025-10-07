---
llm_metadata:
  document_type: reference
  content_focus: technical
  platform:
    primary: shared
  status: active
  created_date: '2025-10-07'
  last_modified: '2025-10-07'
  topics:
  - external_storage
  - data_persistence
  - cloud_storage
  - backup_recovery
  - data_management
  concepts: []
  technologies:
  - python
  - boto3
  - azure_storage
  - google_cloud_storage
  - redis
  semantic_summary: Reference documentation for the External Store service providing unified cloud storage, backup, and data persistence capabilities across multiple providers
  archive_reason: n/a
  historical_value: current
  reference_value: high
semantic_embedding:
  model: text-embedding-ada-002
  embedding_date: '2025-10-07'
  embedding_checksum: pending
rag_metadata:
  chunk_strategy: semantic
  optimal_chunk_size: 512
  retrieval_priority: high
---

# ☁️ External Store Service

**Port: 8018** | **Purpose: Unified Cloud Storage & Data Persistence Platform**

The External Store Service provides comprehensive cloud storage integration, data persistence, backup, and recovery capabilities across multiple cloud providers, ensuring reliable data management for the LLM Documentation Ecosystem.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Applications   │    │ External Store  │    │  Cloud Storage  │
│                 │◄──►│   Service       │◄──►│   Providers     │
│ • File Uploads  │    │   (Port 8018)   │    │                 │
│ • Data Backup   │    │                 │    │ • AWS S3        │
│ • Content Mgmt  │    │ • Multi-Cloud   │    │ • Azure Blob    │
│ • Asset Storage │    │ • Encryption    │    │ • GCP Cloud     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                       ▲                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Cache    │    │   Backup Mgr    │    │   CDN Integration│
│   (Redis)       │    │                 │    │                 │
│                 │    │ • Scheduled     │    │ • Fast Access   │
│ • Performance   │    │ • Incremental   │    │ • Global Dist   │
│ • Compression   │    │ • Encryption    │    │ • Caching       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Core Features

### ☁️ Multi-Cloud Storage
- **AWS S3 Integration**: Complete S3-compatible storage support
- **Azure Blob Storage**: Enterprise-grade blob storage integration
- **Google Cloud Storage**: GCP storage bucket management
- **Provider Agnostic**: Unified API across all cloud providers

### 🔐 Security & Encryption
- **At-Rest Encryption**: AES-256 encryption for stored data
- **In-Transit Security**: TLS 1.3 encryption for data transfers
- **Key Management**: Integrated KMS support across providers
- **Access Control**: IAM and role-based access management

### 💾 Backup & Recovery
- **Automated Backups**: Scheduled and event-driven backups
- **Incremental Backup**: Efficient change-only backup strategies
- **Point-in-Time Recovery**: Restore to specific timestamps
- **Cross-Region Replication**: Disaster recovery and high availability

### 🚀 Performance Optimization
- **CDN Integration**: Global content delivery networks
- **Caching Layers**: Redis-based metadata and content caching
- **Compression**: Automatic data compression and optimization
- **Parallel Operations**: Concurrent upload/download operations

## 📋 Storage Categories

### User Content Storage
- **Document Assets**: Images, diagrams, and media files
- **User Uploads**: File uploads from applications and interfaces
- **Generated Content**: AI-generated images, reports, and exports
- **Temporary Files**: Session-based temporary storage

### Application Data
- **Configuration Backups**: Application configuration snapshots
- **Database Backups**: Automated database backup storage
- **Log Archives**: Compressed log file storage and retrieval
- **Cache Exports**: Serialized cache data for disaster recovery

### System Assets
- **Model Files**: Large AI model files and checkpoints
- **Training Data**: Dataset storage for model training
- **Documentation Assets**: Images, videos, and multimedia content
- **Build Artifacts**: CI/CD build outputs and packages

## 🛠️ API Endpoints

### File Operations
```bash
# Upload file
POST /api/v1/files/upload
Content-Type: multipart/form-data

# Form data:
# - file: (binary file data)
# - metadata: {"category": "documents", "tags": ["important"]}
# - provider: "aws" (optional, defaults to configured primary)

# Download file
GET /api/v1/files/{file_id}/download

# Get file metadata
GET /api/v1/files/{file_id}

# Delete file
DELETE /api/v1/files/{file_id}

# List files
GET /api/v1/files?category=documents&limit=50&offset=0
```

### Batch Operations
```bash
# Batch upload
POST /api/v1/files/batch-upload
{
  "files": [
    {
      "name": "document.pdf",
      "data": "base64-encoded-content",
      "metadata": {"type": "pdf", "size": "2MB"}
    }
  ],
  "options": {
    "parallel": true,
    "compression": true
  }
}

# Batch download
POST /api/v1/files/batch-download
{
  "file_ids": ["file1", "file2", "file3"],
  "format": "zip",
  "password": "optional-password"
}
```

### Backup Operations
```bash
# Create backup
POST /api/v1/backups
{
  "name": "weekly_backup_2025_10_07",
  "source": {
    "type": "database",
    "connection": "postgresql://...",
    "tables": ["users", "documents"]
  },
  "destination": {
    "provider": "aws",
    "bucket": "backups",
    "encryption": true
  },
  "schedule": "0 2 * * 1"  # Cron expression
}

# List backups
GET /api/v1/backups?status=completed&limit=20

# Restore from backup
POST /api/v1/backups/{backup_id}/restore
{
  "target": {
    "type": "database",
    "connection": "postgresql://...",
    "options": {"drop_existing": false}
  }
}
```

## ⚙️ Configuration

### Environment Variables
```bash
# Service Configuration
EXTERNAL_STORE_PORT=8018
EXTERNAL_STORE_HOST=0.0.0.0

# Primary Cloud Provider
PRIMARY_PROVIDER=aws
DEFAULT_REGION=us-east-1

# AWS Configuration
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_DEFAULT_REGION=us-east-1
AWS_S3_BUCKET=your-bucket-name

# Azure Configuration
AZURE_STORAGE_ACCOUNT=your-account
AZURE_STORAGE_KEY=your-key
AZURE_CONTAINER=your-container

# GCP Configuration
GOOGLE_CLOUD_PROJECT=your-project
GOOGLE_CLOUD_KEY_FILE=/path/to/key.json
GCP_BUCKET=your-bucket

# Redis Cache
REDIS_URL=redis://localhost:6379

# Security
ENCRYPTION_KEY=your-encryption-key
ENABLE_HTTPS=true
API_KEY=your-service-key
```

### Provider Configuration
```yaml
# providers.yaml
providers:
  aws:
    type: "s3"
    region: "us-east-1"
    bucket: "mcp-storage"
    encryption: "AES256"
    cdn_enabled: true

  azure:
    type: "blob"
    account: "mcpstorage"
    container: "documents"
    tier: "hot"
    replication: "geo"

  gcp:
    type: "gcs"
    project: "mcp-project"
    bucket: "mcp-storage"
    storage_class: "standard"
    versioning: true

caching:
  redis_url: "redis://localhost:6379"
  ttl_seconds: 3600
  compression: true

backup:
  schedules:
    daily: "0 2 * * *"
    weekly: "0 3 * * 1"
  retention_days: 30
  encryption: true
```

### Docker Deployment
```yaml
version: '3.8'
services:
  external-store:
    image: external-store:latest
    ports:
      - "8018:8018"
    environment:
      - PRIMARY_PROVIDER=aws
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./providers.yaml:/app/config/providers.yaml
      - ./cache:/app/cache
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
```

## 🔄 Data Management

### Storage Classes & Tiers
- **Hot Storage**: Frequently accessed data (S3 Standard, Azure Hot)
- **Cool Storage**: Infrequently accessed data (S3 IA, Azure Cool)
- **Cold Storage**: Archive data (S3 Glacier, Azure Archive)
- **Intelligent Tiering**: Automatic cost optimization based on access patterns

### Data Lifecycle Management
- **Retention Policies**: Configurable data retention rules
- **Automated Deletion**: Scheduled cleanup of expired data
- **Archival Processes**: Move old data to cheaper storage tiers
- **Compliance Handling**: Legal hold and retention for compliance

### Replication & Redundancy
- **Cross-Region Replication**: Automatic replication across regions
- **Multi-AZ Deployment**: High availability across availability zones
- **Versioning**: File versioning for data protection
- **Integrity Checks**: MD5/SHA256 checksum validation

## 🔐 Security Features

### Encryption
- **Client-Side Encryption**: Encrypt data before transmission
- **Server-Side Encryption**: Provider-managed encryption at rest
- **Key Rotation**: Automatic key rotation and management
- **Envelope Encryption**: Multiple layers of encryption

### Access Control
- **IAM Integration**: Cloud provider IAM role integration
- **API Key Authentication**: Service-level API key management
- **IP Whitelisting**: Network-level access restrictions
- **Audit Logging**: Comprehensive access and operation logging

### Compliance
- **GDPR Compliance**: Data subject access and deletion
- **HIPAA Ready**: Healthcare data protection capabilities
- **SOC 2 Type II**: Security and compliance certifications
- **Data Residency**: Regional data storage compliance

## 📊 Monitoring & Analytics

### Performance Metrics
- **Upload/Download Speeds**: Transfer performance monitoring
- **Storage Utilization**: Capacity and usage analytics
- **Cost Tracking**: Storage cost analysis and optimization
- **Error Rates**: Operation success and failure metrics

### Health Monitoring
```bash
# Service health check
GET /health

# Provider status
GET /health/providers

# Storage metrics
GET /metrics/storage

# Backup status
GET /metrics/backups
```

### Usage Analytics
- **Access Patterns**: File access frequency and patterns
- **Geographic Distribution**: Access location analytics
- **Bandwidth Usage**: Data transfer volume tracking
- **Cost Analysis**: Detailed cost breakdown by service and region

## 🔧 Troubleshooting

### Common Issues

#### Upload Failures
```bash
# Check provider credentials
curl http://localhost:8018/health/providers

# Verify bucket/container permissions
aws s3 ls s3://your-bucket/ --region us-east-1

# Check file size limits
curl http://localhost:8018/api/v1/config/limits
```

#### Download Issues
```bash
# Check file existence
curl http://localhost:8018/api/v1/files/{file_id}

# Verify access permissions
curl http://localhost:8018/health/permissions

# Check CDN configuration
curl http://localhost:8018/metrics/cdn
```

#### Backup Failures
```bash
# Check backup status
curl http://localhost:8018/api/v1/backups?status=failed

# Verify source connectivity
curl http://source-database:5432/health

# Check storage space
curl http://localhost:8018/metrics/storage
```

## 🔗 Integration Examples

### File Upload Integration
```python
import requests
import os

class StorageClient:
    def __init__(self, base_url="http://localhost:8018"):
        self.base_url = base_url

    def upload_file(self, file_path, category="documents", metadata=None):
        """Upload a file to cloud storage."""
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {
                'category': category,
                'metadata': json.dumps(metadata or {})
            }

            response = requests.post(
                f"{self.base_url}/api/v1/files/upload",
                files=files,
                data=data
            )

            return response.json()

    def download_file(self, file_id, output_path):
        """Download a file from storage."""
        response = requests.get(f"{self.base_url}/api/v1/files/{file_id}/download")

        with open(output_path, 'wb') as f:
            f.write(response.content)

        return output_path

# Usage
client = StorageClient()
result = client.upload_file("document.pdf", category="documents",
                           metadata={"author": "user123", "version": "1.0"})
file_id = result['file_id']
client.download_file(file_id, "downloaded.pdf")
```

### Backup Integration
```python
import requests
from datetime import datetime

class BackupManager:
    def __init__(self, base_url="http://localhost:8018"):
        self.base_url = base_url

    def create_database_backup(self, db_url, tables=None):
        """Create a database backup."""
        backup_config = {
            "name": f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "source": {
                "type": "database",
                "connection": db_url,
                "tables": tables or ["*"]
            },
            "destination": {
                "provider": "aws",
                "bucket": "backups",
                "encryption": True
            }
        }

        response = requests.post(f"{self.base_url}/api/v1/backups", json=backup_config)
        return response.json()

    def list_backups(self, status=None):
        """List available backups."""
        params = {}
        if status:
            params['status'] = status

        response = requests.get(f"{self.base_url}/api/v1/backups", params=params)
        return response.json()

# Usage
backup_mgr = BackupManager()
backup = backup_mgr.create_database_backup("postgresql://user:pass@localhost:5432/mydb")
backups = backup_mgr.list_backups(status="completed")
```

## 📚 Dependencies

- **Python 3.9+**
- **boto3**: AWS SDK for Python
- **azure-storage-blob**: Azure Storage SDK
- **google-cloud-storage**: GCP Storage SDK
- **redis**: Caching and session management
- **cryptography**: Encryption and security
- **fastapi**: Web API framework
- **aiofiles**: Asynchronous file operations

## 🚀 Getting Started

1. **Configure cloud provider credentials**
   ```bash
   # AWS
   export AWS_ACCESS_KEY_ID=your-access-key
   export AWS_SECRET_ACCESS_KEY=your-secret-key

   # Or use IAM roles/instance profiles
   ```

2. **Set service configuration**
   ```bash
   export EXTERNAL_STORE_PORT=8018
   export PRIMARY_PROVIDER=aws
   export REDIS_URL=redis://localhost:6379
   ```

3. **Create storage buckets/containers**
   ```bash
   # AWS S3
   aws s3 mb s3://your-bucket-name

   # Azure
   az storage container create --name your-container --account-name your-account

   # GCP
   gsutil mb gs://your-bucket-name
   ```

4. **Run the service**
   ```bash
   cd services/external-store
   python -m uvicorn main:app --host 0.0.0.0 --port 8018
   ```

5. **Test basic functionality**
   ```bash
   # Health check
   curl http://localhost:8018/health

   # Upload test file
   echo "test content" > test.txt
   curl -X POST http://localhost:8018/api/v1/files/upload \
     -F "file=@test.txt" \
     -F "metadata={\"test\": true}"
   ```

## 🎯 Use Cases

### Content Management
- **User Uploads**: Handle file uploads from web applications
- **Asset Storage**: Store images, videos, and media files
- **Document Archives**: Long-term document storage and retrieval
- **Generated Content**: Store AI-generated images and documents

### Data Backup & Recovery
- **Database Backups**: Automated database backup to cloud storage
- **Configuration Backups**: Application configuration snapshots
- **Log Archives**: Compressed log file storage and retrieval
- **Disaster Recovery**: Cross-region data replication and recovery

### Application Assets
- **Static Assets**: Serve static files through CDN
- **Model Storage**: Store large AI model files and checkpoints
- **Build Artifacts**: CI/CD pipeline artifact storage
- **Package Repository**: Store and distribute software packages

### Compliance & Archiving
- **Regulatory Storage**: GDPR, HIPAA, SOX compliant storage
- **Audit Trails**: Immutable audit log storage
- **Data Retention**: Configurable retention policies
- **Legal Holds**: Preserve data for legal requirements

## 🤝 Contributing

### Development Setup
```bash
# Clone repository
git clone <repository>
cd services/external-store

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure cloud credentials
cp config/providers.example.yaml config/providers.yaml
# Edit with your credentials

# Run tests
pytest tests/

# Start development server
uvicorn main:app --reload --host 0.0.0.0 --port 8018
```

### Adding New Providers
1. **Create provider module** in the providers directory
2. **Implement storage interface** with upload/download/delete operations
3. **Add provider configuration** to the config schema
4. **Update provider selection logic** in the main service
5. **Add comprehensive tests** for the new provider

## 📄 License

This service is part of the LLM Documentation Ecosystem. See project LICENSE for details.

---

**Status:** 🟢 Production Ready | **Port:** 8018 | **Providers:** AWS S3, Azure Blob, GCP | **Features:** Multi-cloud, Backup, CDN
