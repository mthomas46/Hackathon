# Infrastructure Setup Guide

## Overview

The LLM Documentation Ecosystem requires specific infrastructure components for data storage and caching. This guide covers the setup and configuration of Redis and SQLite databases.

## Redis Setup

### Development Setup

Redis is used as an in-memory cache and session store throughout the application.

#### Docker Configuration (Recommended)

```yaml
# From docker-compose.dev.yml
redis:
  image: redis:7-alpine
  ports:
    - "6379:6379"
  volumes:
    - redis_data:/data
  command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 30s
    timeout: 10s
    retries: 3
```

#### Key Configuration Options

- **maxmemory**: 512MB (development), 1GB (production)
- **maxmemory-policy**: `allkeys-lru` (Least Recently Used eviction)
- **appendonly**: `yes` (enables AOF persistence)
- **appendfsync**: `everysec` (default, balance of performance/safety)

#### Manual Installation

```bash
# macOS with Homebrew
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt update
sudo apt install redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Verify installation
redis-cli ping  # Should return "PONG"
```

#### Redis Configuration File

Create `/etc/redis/redis.conf` or `~/.redis.conf`:

```ini
# Basic configuration
bind 127.0.0.1
port 6379
timeout 0
tcp-keepalive 300

# Memory management
maxmemory 512mb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000

# Logging
loglevel notice
logfile /var/log/redis/redis.log

# Security (development only)
# requirepass yourpasswordhere
```

#### Environment Variables

```bash
# Redis connection settings
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_URL=redis://localhost:6379

# Advanced settings
REDIS_MAX_CONNECTIONS=20
REDIS_RETRY_ON_TIMEOUT=true
```

### Production Setup

#### High Availability with Redis Cluster

For production deployments requiring high availability:

```yaml
# docker-compose.prod.yml (excerpt)
redis:
  image: redis:7-alpine
  command: redis-server /etc/redis/redis.conf
  volumes:
    - ./infrastructure/redis.conf:/etc/redis/redis.conf:ro
    - redis_data:/data
  networks:
    - doc-ecosystem-prod
  deploy:
    replicas: 3
    resources:
      limits:
        memory: 1G
      reservations:
        memory: 512M
```

#### Redis Sentinel (Automatic Failover)

```yaml
redis-sentinel:
  image: redis:7-alpine
  command: redis-sentinel /etc/redis/sentinel.conf
  volumes:
    - ./infrastructure/redis-sentinel.conf:/etc/redis/sentinel.conf:ro
  depends_on:
    - redis
  networks:
    - doc-ecosystem-prod
```

## SQLite Setup

### Development Setup

SQLite is used for persistent data storage in development and can be used in production for smaller deployments.

#### Database Files Location

```
services/
├── doc-store/
│   └── db.sqlite3          # Document storage
├── prompt-store/
│   └── prompt_store.db     # Prompt templates and history
└── shared/
    └── *.db                # Other service databases
```

#### Configuration

SQLite databases are configured in `config.yml`:

```yaml
sqlite:
  databases:
    doc_store:
      path: services/doc-store/db.sqlite3
      connection_pool_size: 5
    prompt_store:
      path: /app/data/prompt_store.db

  settings:
    journal_mode: WAL
    synchronous: NORMAL
    cache_size: -64000  # 64MB cache
    temp_store: memory
```

#### Docker Volume Configuration

```yaml
# docker-compose.dev.yml
volumes:
  doc_store_data:
    driver: local
  prompt_store_data:
    driver: local
```

### Production Setup

#### PostgreSQL Migration

For production deployments, migrate from SQLite to PostgreSQL:

1. **Install PostgreSQL**

```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib

# macOS
brew install postgresql
brew services start postgresql

# Initialize database
sudo -u postgres createuser --createdb doc_user
sudo -u postgres createdb -O doc_user doc_consistency
sudo -u postgres psql -c "ALTER USER doc_user PASSWORD 'secure_password';"
```

2. **Update Configuration**

```yaml
# config.yml
postgresql:
  enabled: true
  host: localhost
  port: 5432
  database: doc_consistency
  user: doc_user
  password: secure_password
```

3. **Migration Script**

```bash
# Export SQLite data
sqlite3 services/doc-store/db.sqlite3 .dump > doc_store_backup.sql

# Convert to PostgreSQL format and import
# (Use tools like pgloader or write custom migration scripts)
```

#### Backup Strategy

```bash
#!/bin/bash
# Daily SQLite backup script
BACKUP_DIR="/backups/sqlite"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup document store
sqlite3 services/doc-store/db.sqlite3 ".backup '${BACKUP_DIR}/doc_store_${DATE}.db'"

# Backup prompt store
sqlite3 /app/data/prompt_store.db ".backup '${BACKUP_DIR}/prompt_store_${DATE}.db'"

# Clean old backups (keep last 7 days)
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
```

### Database Schema Initialization

#### Document Store Schema

```sql
-- Document Store Schema (SQLite/PostgreSQL compatible)
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    title TEXT,
    content TEXT,
    metadata TEXT,  -- JSON
    flags TEXT,     -- JSON array
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_documents_source_type ON documents(source_type);
CREATE INDEX idx_documents_created_at ON documents(created_at);
```

#### Prompt Store Schema

```sql
-- Prompt Store Schema
CREATE TABLE IF NOT EXISTS prompts (
    id TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    name TEXT NOT NULL,
    prompt_text TEXT NOT NULL,
    variables TEXT,  -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(category, name)
);

CREATE INDEX idx_prompts_category ON prompts(category);
```

## Monitoring and Maintenance

### Redis Monitoring

```bash
# Basic monitoring commands
redis-cli info
redis-cli info memory
redis-cli info stats

# Key metrics to monitor
redis-cli --stat  # Real-time stats
redis-cli --latency  # Latency monitoring
```

### SQLite Maintenance

```sql
-- Analyze and optimize SQLite databases
ANALYZE;
VACUUM;

-- Check database integrity
PRAGMA integrity_check;

-- Optimize WAL mode
PRAGMA wal_checkpoint(TRUNCATE);
```

### Health Checks

#### Redis Health Check

```bash
#!/bin/bash
# Redis health check script
if redis-cli ping | grep -q PONG; then
    echo "Redis is healthy"
    exit 0
else
    echo "Redis is unhealthy"
    exit 1
fi
```

#### SQLite Health Check

```bash
#!/bin/bash
# SQLite health check script
DB_FILE=$1
if sqlite3 $DB_FILE "PRAGMA integrity_check;" | grep -q ok; then
    echo "SQLite database is healthy"
    exit 0
else
    echo "SQLite database is corrupted"
    exit 1
fi
```

## Troubleshooting

### Common Redis Issues

1. **Connection Refused**
   - Check if Redis is running: `redis-cli ping`
   - Verify port configuration
   - Check firewall settings

2. **Memory Issues**
   - Monitor memory usage: `redis-cli info memory`
   - Adjust maxmemory settings
   - Implement proper key eviction policies

3. **Persistence Issues**
   - Check AOF/RDB file permissions
   - Verify disk space availability
   - Monitor appendfsync settings

### Common SQLite Issues

1. **Database Locked**
   - Check for long-running transactions
   - Implement connection pooling
   - Use WAL mode for better concurrency

2. **Corruption**
   - Regular integrity checks: `PRAGMA integrity_check;`
   - Maintain backups
   - Monitor disk space

3. **Performance Issues**
   - Create appropriate indexes
   - Use EXPLAIN QUERY PLAN for optimization
   - Consider query restructuring

## Security Considerations

### Redis Security

```ini
# redis.conf security settings
# Disable dangerous commands in production
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command DEBUG ""
rename-command CONFIG ""

# Enable authentication
requirepass your_secure_password

# Bind to specific interface
bind 127.0.0.1
```

### SQLite Security

- Store database files in secure directories
- Implement proper file permissions (600)
- Use parameterized queries to prevent SQL injection
- Regular security audits of application code

## Performance Tuning

### Redis Tuning

```ini
# Performance optimizations
tcp-backlog 511
databases 16
maxclients 10000

# Memory optimization
maxmemory-samples 5
lazyfree-lazy-eviction yes
lazyfree-lazy-expire yes
```

### SQLite Tuning

```sql
-- Performance optimizations
PRAGMA cache_size = -64000;  -- 64MB cache
PRAGMA synchronous = NORMAL;  -- Balance safety/performance
PRAGMA wal_autocheckpoint = 1000;  -- Auto-checkpoint WAL
PRAGMA temp_store = memory;  -- Temp tables in memory
PRAGMA mmap_size = 268435456;  -- 256MB memory mapping
```
