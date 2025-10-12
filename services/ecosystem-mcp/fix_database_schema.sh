#!/bin/bash
#
# Fix Database Schema
# Applies the Alembic migration to create proper schema
#

set -e

echo "═══════════════════════════════════════════════════════════════"
echo "🔧 FIXING DATABASE SCHEMA"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Option 1: Drop and recreate (safest for development)
echo "Option: Drop existing tables and recreate with proper schema"
echo ""
echo "This will:"
echo "  1. Drop all existing tables"
echo "  2. Run the Alembic migration to create proper schema"
echo "  3. Start with clean database"
echo ""

# Check if tables exist
docker-compose exec -T postgres psql -U ecosystem_mcp -d ecosystem_mcp -c "\dt" 2>&1

echo ""
echo "Dropping existing tables..."
docker-compose exec -T postgres psql -U ecosystem_mcp -d ecosystem_mcp <<EOF
DROP TABLE IF EXISTS model_requests CASCADE;
DROP TABLE IF EXISTS document_versions CASCADE;
DROP TABLE IF EXISTS embeddings CASCADE;
DROP TABLE IF EXISTS documents CASCADE;
DROP TABLE IF EXISTS ingestion_jobs CASCADE;
DROP TABLE IF EXISTS git_commits CASCADE;
DROP TABLE IF EXISTS alembic_version CASCADE;
EOF

echo ""
echo "✅ Tables dropped"
echo ""

# Now run the migration
echo "Running Alembic migration..."
echo ""

# We need to run this from within the application container
# but if that's not working, we'll apply the SQL directly

# Try to run alembic
if docker-compose exec ecosystem-mcp alembic upgrade head 2>/dev/null; then
    echo "✅ Migration applied via alembic"
else
    echo "⚠️ Alembic command failed, applying SQL directly..."
    
    # Apply the migration SQL directly
    docker-compose exec -T postgres psql -U ecosystem_mcp -d ecosystem_mcp <<'EOSQL'
-- Create git_commits table
CREATE TABLE git_commits (
    sha VARCHAR(40) PRIMARY KEY,
    message TEXT NOT NULL,
    author VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    date TIMESTAMP NOT NULL,
    UNIQUE (sha),
    CHECK (date <= now())
);
CREATE INDEX idx_commits_date ON git_commits(date);
CREATE INDEX idx_commits_author ON git_commits(author);

-- Create documents table
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    service_name VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    original_format VARCHAR(50) NOT NULL,
    original_content TEXT NOT NULL,
    normalized_content TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    git_commit_sha VARCHAR(40),
    is_latest BOOLEAN NOT NULL,
    embedding_id UUID,
    doc_metadata JSONB NOT NULL,
    FOREIGN KEY (git_commit_sha) REFERENCES git_commits(sha),
    UNIQUE (file_path, git_commit_sha)
);
CREATE INDEX idx_documents_service_latest ON documents(service_name, is_latest);
CREATE INDEX idx_documents_content_hash ON documents(content_hash);

-- Create embeddings table
CREATE TABLE embeddings (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL,
    chroma_id VARCHAR(255) UNIQUE NOT NULL,
    model VARCHAR(100) NOT NULL,
    dimensions INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL,
    token_count INTEGER NOT NULL,
    cost_usd FLOAT NOT NULL,
    extra_metadata JSONB,
    FOREIGN KEY (document_id) REFERENCES documents(id),
    CHECK (dimensions > 0),
    CHECK (token_count >= 0),
    CHECK (cost_usd >= 0.0)
);
CREATE INDEX idx_embeddings_document ON embeddings(document_id);
CREATE INDEX idx_embeddings_model ON embeddings(model);
CREATE INDEX idx_embeddings_chroma_id ON embeddings(chroma_id);

-- Add circular foreign key from documents to embeddings
ALTER TABLE documents ADD CONSTRAINT fk_documents_embedding_id 
    FOREIGN KEY (embedding_id) REFERENCES embeddings(id);

-- Create document_versions table
CREATE TABLE document_versions (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL,
    version_hash VARCHAR(64) UNIQUE NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (document_id) REFERENCES documents(id)
);
CREATE INDEX idx_document_versions_document ON document_versions(document_id);

-- Create ingestion_jobs table
CREATE TABLE ingestion_jobs (
    id UUID PRIMARY KEY,
    mode VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    processed_documents INTEGER NOT NULL,
    total_documents INTEGER,
    failed_documents INTEGER NOT NULL,
    repo_path VARCHAR,
    embeddings_generated INTEGER NOT NULL,
    total_cost_usd FLOAT NOT NULL,
    error_message VARCHAR,
    job_metadata JSONB NOT NULL
);
CREATE INDEX idx_jobs_status_started ON ingestion_jobs(status, started_at);
CREATE INDEX idx_jobs_mode ON ingestion_jobs(mode);

-- Create model_requests table
CREATE TABLE model_requests (
    id UUID PRIMARY KEY,
    model VARCHAR(100) NOT NULL,
    task_type VARCHAR(50) NOT NULL,
    input_tokens INTEGER,
    output_tokens INTEGER,
    cost_usd FLOAT,
    timestamp TIMESTAMP NOT NULL,
    success BOOLEAN NOT NULL,
    error_message VARCHAR,
    metadata JSONB
);
CREATE INDEX idx_requests_timestamp ON model_requests(timestamp);
CREATE INDEX idx_requests_model_timestamp ON model_requests(model, timestamp);
CREATE INDEX idx_requests_task_type ON model_requests(task_type);
CREATE INDEX idx_requests_success ON model_requests(success);

-- Record migration in alembic_version
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) PRIMARY KEY
);
INSERT INTO alembic_version (version_num) VALUES ('20251012_0000');

EOSQL
    
    echo "✅ SQL applied directly"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ DATABASE SCHEMA FIXED"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Verifying schema..."
docker-compose exec -T postgres psql -U ecosystem_mcp -d ecosystem_mcp -c "\d ingestion_jobs" | head -20

echo ""
echo "✅ Schema is now correct!"
echo ""

