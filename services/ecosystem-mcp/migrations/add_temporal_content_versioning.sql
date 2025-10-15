-- Migration: Add Temporal Content Versioning System
-- Description: Hybrid approach using content hash + timestamps for deduplication and timeline queries
-- Date: 2025-10-15

BEGIN;

-- ==========================================
-- Content Store (Deduplicated Storage)
-- ==========================================
CREATE TABLE IF NOT EXISTS document_content_store (
    content_hash VARCHAR(64) PRIMARY KEY,
    content BYTEA,
    mime_type VARCHAR(100),
    compression_type VARCHAR(20),
    storage_location TEXT,
    content_size BIGINT NOT NULL DEFAULT 0,
    first_seen_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reference_count INTEGER DEFAULT 0,
    
    CONSTRAINT check_content_hash_format CHECK (length(content_hash) = 64)
);

-- ==========================================
-- Enhanced Document Versions (Temporal + Content)
-- ==========================================
-- Add new columns to existing document_versions table if not exists
DO $$ 
BEGIN
    -- Content identity
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='document_versions' AND column_name='content_hash') THEN
        ALTER TABLE document_versions ADD COLUMN content_hash VARCHAR(64);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='document_versions' AND column_name='content_size') THEN
        ALTER TABLE document_versions ADD COLUMN content_size BIGINT;
    END IF;
    
    -- Temporal metadata
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='document_versions' AND column_name='modified_at') THEN
        ALTER TABLE document_versions ADD COLUMN modified_at TIMESTAMP WITH TIME ZONE;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='document_versions' AND column_name='effective_date') THEN
        ALTER TABLE document_versions ADD COLUMN effective_date TIMESTAMP WITH TIME ZONE;
    END IF;
    
    -- Version numbering
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='document_versions' AND column_name='version_number') THEN
        ALTER TABLE document_versions ADD COLUMN version_number INTEGER;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='document_versions' AND column_name='version_id') THEN
        ALTER TABLE document_versions ADD COLUMN version_id VARCHAR(128);
    END IF;
    
    -- Timeline positioning
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='document_versions' AND column_name='timeline_position') THEN
        ALTER TABLE document_versions ADD COLUMN timeline_position BIGINT;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='document_versions' AND column_name='temporal_sequence') THEN
        ALTER TABLE document_versions ADD COLUMN temporal_sequence INTEGER;
    END IF;
    
    -- Provenance
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='document_versions' AND column_name='created_by') THEN
        ALTER TABLE document_versions ADD COLUMN created_by VARCHAR(255);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='document_versions' AND column_name='modified_by') THEN
        ALTER TABLE document_versions ADD COLUMN modified_by VARCHAR(255);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='document_versions' AND column_name='source_path') THEN
        ALTER TABLE document_versions ADD COLUMN source_path TEXT;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='document_versions' AND column_name='title') THEN
        ALTER TABLE document_versions ADD COLUMN title TEXT;
    END IF;
    
    -- Version relationships
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='document_versions' AND column_name='is_latest') THEN
        ALTER TABLE document_versions ADD COLUMN is_latest BOOLEAN DEFAULT TRUE;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='document_versions' AND column_name='previous_version_id') THEN
        ALTER TABLE document_versions ADD COLUMN previous_version_id UUID;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='document_versions' AND column_name='next_version_id') THEN
        ALTER TABLE document_versions ADD COLUMN next_version_id UUID;
    END IF;
END $$;

-- Add foreign key constraints if they don't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_prev_version' AND table_name = 'document_versions'
    ) THEN
        ALTER TABLE document_versions 
        ADD CONSTRAINT fk_prev_version 
        FOREIGN KEY (previous_version_id) REFERENCES document_versions(id);
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_next_version' AND table_name = 'document_versions'
    ) THEN
        ALTER TABLE document_versions 
        ADD CONSTRAINT fk_next_version 
        FOREIGN KEY (next_version_id) REFERENCES document_versions(id);
    END IF;
END $$;

-- ==========================================
-- Document Timeline (Event Stream)
-- ==========================================
CREATE TABLE IF NOT EXISTS document_timeline (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_id UUID REFERENCES document_versions(id) ON DELETE CASCADE,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    event_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    actor VARCHAR(255),
    metadata JSONB,
    
    CONSTRAINT unique_timeline_event UNIQUE (version_id, event_timestamp, event_type)
);

-- ==========================================
-- Indexes for Performance
-- ==========================================

-- Content store indexes
CREATE INDEX IF NOT EXISTS idx_content_first_seen ON document_content_store(first_seen_at DESC);
CREATE INDEX IF NOT EXISTS idx_content_ref_count ON document_content_store(reference_count DESC);

-- Version temporal indexes
CREATE INDEX IF NOT EXISTS idx_versions_modified ON document_versions(modified_at DESC) WHERE modified_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_versions_created ON document_versions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_versions_timeline ON document_versions(timeline_position) WHERE timeline_position IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_versions_content_hash ON document_versions(content_hash) WHERE content_hash IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_versions_is_latest ON document_versions(document_id, is_latest) WHERE is_latest = TRUE;
CREATE INDEX IF NOT EXISTS idx_versions_source_path ON document_versions(source_path) WHERE source_path IS NOT NULL;

-- Timeline indexes
CREATE INDEX IF NOT EXISTS idx_timeline_timestamp ON document_timeline(event_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_timeline_document ON document_timeline(document_id, event_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_timeline_event_type ON document_timeline(event_type, event_timestamp DESC);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_versions_doc_modified ON document_versions(document_id, modified_at DESC) WHERE modified_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_timeline_doc_type ON document_timeline(document_id, event_type, event_timestamp DESC);

-- ==========================================
-- Helper Functions
-- ==========================================

-- Get next timeline position (global counter)
CREATE OR REPLACE FUNCTION get_next_timeline_position()
RETURNS BIGINT AS $$
DECLARE
    next_pos BIGINT;
BEGIN
    SELECT COALESCE(MAX(timeline_position), 0) + 1 INTO next_pos
    FROM document_versions;
    RETURN next_pos;
END;
$$ LANGUAGE plpgsql;

-- Get latest version of a document as of a specific date
CREATE OR REPLACE FUNCTION get_document_version_as_of(
    p_document_id UUID,
    p_as_of_date TIMESTAMP WITH TIME ZONE
)
RETURNS TABLE (
    id UUID,
    version_number INTEGER,
    content_hash VARCHAR(64),
    modified_at TIMESTAMP WITH TIME ZONE,
    created_by VARCHAR(255),
    title TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        v.id,
        v.version_number,
        v.content_hash,
        v.modified_at,
        v.created_by,
        v.title
    FROM document_versions v
    WHERE v.document_id = p_document_id
      AND v.modified_at <= p_as_of_date
    ORDER BY v.modified_at DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- Get all documents as of a specific date (latest version of each)
CREATE OR REPLACE FUNCTION get_all_documents_as_of(
    p_as_of_date TIMESTAMP WITH TIME ZONE
)
RETURNS TABLE (
    document_id UUID,
    version_id UUID,
    version_number INTEGER,
    content_hash VARCHAR(64),
    modified_at TIMESTAMP WITH TIME ZONE,
    created_by VARCHAR(255),
    title TEXT,
    source_path TEXT
) AS $$
BEGIN
    RETURN QUERY
    WITH latest_versions AS (
        SELECT DISTINCT ON (v.document_id)
            v.document_id,
            v.id as version_id,
            v.version_number,
            v.content_hash,
            v.modified_at,
            v.created_by,
            v.title,
            v.source_path,
            ROW_NUMBER() OVER (PARTITION BY v.document_id ORDER BY v.modified_at DESC) as rn
        FROM document_versions v
        WHERE v.modified_at <= p_as_of_date
    )
    SELECT 
        lv.document_id,
        lv.version_id,
        lv.version_number,
        lv.content_hash,
        lv.modified_at,
        lv.created_by,
        lv.title,
        lv.source_path
    FROM latest_versions lv
    WHERE lv.rn = 1
    ORDER BY lv.modified_at DESC;
END;
$$ LANGUAGE plpgsql;

-- Get document timeline (all versions chronologically)
CREATE OR REPLACE FUNCTION get_document_timeline(
    p_document_id UUID,
    p_start_date TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    p_end_date TIMESTAMP WITH TIME ZONE DEFAULT NULL
)
RETURNS TABLE (
    version_id UUID,
    version_number INTEGER,
    event_timestamp TIMESTAMP WITH TIME ZONE,
    event_type VARCHAR(50),
    actor VARCHAR(255),
    content_hash VARCHAR(64),
    title TEXT,
    is_latest BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        v.id as version_id,
        v.version_number,
        COALESCE(v.modified_at, v.created_at) as event_timestamp,
        'version_created'::VARCHAR(50) as event_type,
        v.created_by as actor,
        v.content_hash,
        v.title,
        v.is_latest
    FROM document_versions v
    WHERE v.document_id = p_document_id
      AND (p_start_date IS NULL OR COALESCE(v.modified_at, v.created_at) >= p_start_date)
      AND (p_end_date IS NULL OR COALESCE(v.modified_at, v.created_at) <= p_end_date)
    ORDER BY COALESCE(v.modified_at, v.created_at) ASC;
END;
$$ LANGUAGE plpgsql;

-- Increment content reference count
CREATE OR REPLACE FUNCTION increment_content_reference(p_content_hash VARCHAR(64))
RETURNS VOID AS $$
BEGIN
    UPDATE document_content_store
    SET reference_count = reference_count + 1
    WHERE content_hash = p_content_hash;
END;
$$ LANGUAGE plpgsql;

-- Decrement content reference count (and cleanup if zero)
CREATE OR REPLACE FUNCTION decrement_content_reference(p_content_hash VARCHAR(64))
RETURNS VOID AS $$
BEGIN
    UPDATE document_content_store
    SET reference_count = GREATEST(reference_count - 1, 0)
    WHERE content_hash = p_content_hash;
    
    -- Optionally delete content if no references
    -- DELETE FROM document_content_store
    -- WHERE content_hash = p_content_hash AND reference_count = 0;
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- Views for Common Queries
-- ==========================================

-- View: Latest versions of all documents
CREATE OR REPLACE VIEW latest_document_versions AS
SELECT 
    d.id as document_id,
    d.file_path,
    v.id as version_id,
    v.version_number,
    v.content_hash,
    v.created_at,
    v.modified_at,
    v.created_by,
    v.title,
    v.source_path,
    v.content_size,
    v.timeline_position
FROM documents d
JOIN document_versions v ON v.document_id = d.id
WHERE v.is_latest = TRUE;

-- View: Content deduplication statistics
CREATE OR REPLACE VIEW content_deduplication_stats AS
SELECT 
    COUNT(DISTINCT content_hash) as unique_content_items,
    COUNT(*) as total_versions,
    SUM(CASE WHEN reference_count > 1 THEN 1 ELSE 0 END) as deduplicated_items,
    SUM(content_size) as total_content_size,
    SUM(content_size * reference_count) as size_without_dedup,
    SUM(content_size * reference_count) - SUM(content_size) as space_saved
FROM document_content_store;

-- View: Timeline activity summary
CREATE OR REPLACE VIEW timeline_activity_summary AS
SELECT 
    DATE(event_timestamp) as activity_date,
    event_type,
    COUNT(*) as event_count,
    COUNT(DISTINCT document_id) as unique_documents,
    COUNT(DISTINCT actor) as unique_actors
FROM document_timeline
GROUP BY DATE(event_timestamp), event_type
ORDER BY activity_date DESC, event_type;

COMMIT;

-- ==========================================
-- Migration Notes
-- ==========================================
-- This migration adds:
-- 1. document_content_store: Deduplicated content storage
-- 2. Enhanced document_versions: Temporal metadata and relationships
-- 3. document_timeline: Event stream for all document activities
-- 4. Helper functions for temporal queries
-- 5. Indexes for optimized timeline and "as of" queries
-- 6. Views for common reporting needs

