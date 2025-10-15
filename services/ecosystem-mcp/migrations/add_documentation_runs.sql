-- Migration: Add Documentation Run Management
-- Description: Persist documentation generation runs and their generated documents
-- Date: 2025-10-15

BEGIN;

-- ==========================================
-- Documentation Runs Table
-- ==========================================
CREATE TABLE IF NOT EXISTS documentation_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Run metadata
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',  -- pending, running, completed, failed, cancelled
    
    -- Configuration used
    source_directory TEXT NOT NULL,
    output_format VARCHAR(50) DEFAULT 'markdown',
    response_size VARCHAR(10),  -- S, M, L, XL
    tier VARCHAR(50),  -- desktop, docker, auto
    
    -- Multi-pass configuration
    num_passes INTEGER DEFAULT 3,
    questions_per_pass INTEGER DEFAULT 5,
    
    -- Timing
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    
    -- Results
    total_documents INTEGER DEFAULT 0,
    successful_documents INTEGER DEFAULT 0,
    failed_documents INTEGER DEFAULT 0,
    
    -- Storage
    output_directory TEXT,
    archive_path TEXT,  -- Optional: path to ZIP archive of all docs
    
    -- Metadata
    created_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB,
    
    -- Checksums for verification
    config_hash VARCHAR(64),  -- Hash of configuration for deduplication
    
    CONSTRAINT valid_status CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled'))
);

-- ==========================================
-- Generated Documents Table
-- ==========================================
CREATE TABLE IF NOT EXISTS generated_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relationship to run
    run_id UUID NOT NULL REFERENCES documentation_runs(id) ON DELETE CASCADE,
    
    -- Document metadata
    title TEXT NOT NULL,
    filename VARCHAR(500) NOT NULL,
    file_path TEXT,  -- Full path where document is stored
    
    -- Content
    content TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL,  -- SHA256 of content
    content_size INTEGER NOT NULL,
    
    -- Generation details
    pass_number INTEGER,  -- Which pass generated this (for multi-pass)
    question TEXT,  -- The question that generated this document
    source_files TEXT[],  -- Source files used to generate this
    
    -- Status
    status VARCHAR(50) DEFAULT 'generated',  -- generated, exported, archived
    generation_time_seconds NUMERIC(10, 2),
    
    -- Quality metrics (optional)
    word_count INTEGER,
    relevance_score NUMERIC(5, 2),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB
);

-- ==========================================
-- Run Progress Tracking (for live updates)
-- ==========================================
CREATE TABLE IF NOT EXISTS documentation_run_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES documentation_runs(id) ON DELETE CASCADE,
    
    -- Progress details
    current_pass INTEGER,
    total_passes INTEGER,
    current_question INTEGER,
    total_questions INTEGER,
    
    -- Current operation
    current_operation TEXT,  -- e.g., "Generating question 3 of pass 2"
    progress_percentage NUMERIC(5, 2),
    
    -- Real-time stats
    documents_generated INTEGER DEFAULT 0,
    documents_failed INTEGER DEFAULT 0,
    estimated_time_remaining_seconds INTEGER,
    
    -- Timestamps
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Only keep latest progress per run
    CONSTRAINT unique_run_progress UNIQUE (run_id)
);

-- ==========================================
-- Indexes
-- ==========================================
CREATE INDEX IF NOT EXISTS idx_doc_runs_status ON documentation_runs(status);
CREATE INDEX IF NOT EXISTS idx_doc_runs_created ON documentation_runs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_doc_runs_started ON documentation_runs(started_at DESC) WHERE started_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_doc_runs_completed ON documentation_runs(completed_at DESC) WHERE completed_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_doc_runs_config_hash ON documentation_runs(config_hash);

CREATE INDEX IF NOT EXISTS idx_gen_docs_run ON generated_documents(run_id);
CREATE INDEX IF NOT EXISTS idx_gen_docs_created ON generated_documents(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_gen_docs_content_hash ON generated_documents(content_hash);
CREATE INDEX IF NOT EXISTS idx_gen_docs_status ON generated_documents(status);

CREATE INDEX IF NOT EXISTS idx_run_progress_run ON documentation_run_progress(run_id);

-- ==========================================
-- Helper Functions
-- ==========================================

-- Update run status and timing
CREATE OR REPLACE FUNCTION update_documentation_run_status(
    p_run_id UUID,
    p_status VARCHAR(50),
    p_total_docs INTEGER DEFAULT NULL,
    p_successful_docs INTEGER DEFAULT NULL,
    p_failed_docs INTEGER DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    UPDATE documentation_runs
    SET 
        status = p_status,
        updated_at = NOW(),
        total_documents = COALESCE(p_total_docs, total_documents),
        successful_documents = COALESCE(p_successful_docs, successful_documents),
        failed_documents = COALESCE(p_failed_docs, failed_documents),
        completed_at = CASE 
            WHEN p_status IN ('completed', 'failed', 'cancelled') THEN NOW()
            ELSE completed_at
        END,
        duration_seconds = CASE
            WHEN p_status IN ('completed', 'failed', 'cancelled') AND started_at IS NOT NULL
            THEN EXTRACT(EPOCH FROM (NOW() - started_at))::INTEGER
            ELSE duration_seconds
        END
    WHERE id = p_run_id;
END;
$$ LANGUAGE plpgsql;

-- Get run statistics
CREATE OR REPLACE FUNCTION get_documentation_run_stats(p_run_id UUID)
RETURNS TABLE (
    total_docs INTEGER,
    successful_docs INTEGER,
    failed_docs INTEGER,
    avg_generation_time NUMERIC,
    total_content_size BIGINT,
    total_word_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::INTEGER as total_docs,
        COUNT(*) FILTER (WHERE status = 'generated')::INTEGER as successful_docs,
        COUNT(*) FILTER (WHERE status = 'failed')::INTEGER as failed_docs,
        AVG(generation_time_seconds) as avg_generation_time,
        SUM(content_size)::BIGINT as total_content_size,
        SUM(word_count)::BIGINT as total_word_count
    FROM generated_documents
    WHERE run_id = p_run_id;
END;
$$ LANGUAGE plpgsql;

-- Update run progress
CREATE OR REPLACE FUNCTION update_run_progress(
    p_run_id UUID,
    p_current_pass INTEGER,
    p_total_passes INTEGER,
    p_current_question INTEGER,
    p_total_questions INTEGER,
    p_current_operation TEXT,
    p_docs_generated INTEGER,
    p_docs_failed INTEGER
)
RETURNS VOID AS $$
DECLARE
    v_progress NUMERIC;
BEGIN
    -- Calculate progress percentage
    v_progress := ((p_current_pass - 1) * p_total_questions + p_current_question) * 100.0 / (p_total_passes * p_total_questions);
    
    INSERT INTO documentation_run_progress (
        run_id,
        current_pass,
        total_passes,
        current_question,
        total_questions,
        current_operation,
        progress_percentage,
        documents_generated,
        documents_failed,
        updated_at
    )
    VALUES (
        p_run_id,
        p_current_pass,
        p_total_passes,
        p_current_question,
        p_total_questions,
        p_current_operation,
        v_progress,
        p_docs_generated,
        p_docs_failed,
        NOW()
    )
    ON CONFLICT (run_id) DO UPDATE SET
        current_pass = EXCLUDED.current_pass,
        total_passes = EXCLUDED.total_passes,
        current_question = EXCLUDED.current_question,
        total_questions = EXCLUDED.total_questions,
        current_operation = EXCLUDED.current_operation,
        progress_percentage = EXCLUDED.progress_percentage,
        documents_generated = EXCLUDED.documents_generated,
        documents_failed = EXCLUDED.documents_failed,
        updated_at = EXCLUDED.updated_at;
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- Views
-- ==========================================

-- Active runs view
CREATE OR REPLACE VIEW active_documentation_runs AS
SELECT 
    r.*,
    p.current_operation,
    p.progress_percentage,
    p.estimated_time_remaining_seconds
FROM documentation_runs r
LEFT JOIN documentation_run_progress p ON r.id = p.run_id
WHERE r.status IN ('pending', 'running')
ORDER BY r.created_at DESC;

-- Completed runs with stats
CREATE OR REPLACE VIEW documentation_run_summary AS
SELECT 
    r.id,
    r.name,
    r.description,
    r.status,
    r.source_directory,
    r.started_at,
    r.completed_at,
    r.duration_seconds,
    r.total_documents,
    r.successful_documents,
    r.failed_documents,
    r.created_by,
    r.created_at,
    COUNT(gd.id) as actual_document_count,
    SUM(gd.content_size) as total_content_size,
    SUM(gd.word_count) as total_word_count,
    AVG(gd.generation_time_seconds) as avg_generation_time
FROM documentation_runs r
LEFT JOIN generated_documents gd ON r.id = gd.run_id
GROUP BY r.id
ORDER BY r.created_at DESC;

-- Recent documents view
CREATE OR REPLACE VIEW recent_generated_documents AS
SELECT 
    gd.*,
    r.name as run_name,
    r.status as run_status,
    r.created_by as run_creator
FROM generated_documents gd
JOIN documentation_runs r ON gd.run_id = r.id
ORDER BY gd.created_at DESC
LIMIT 100;

COMMIT;

-- ==========================================
-- Migration Notes
-- ==========================================
-- This migration adds:
-- 1. documentation_runs: Track each documentation generation run
-- 2. generated_documents: Store all generated documents with metadata
-- 3. documentation_run_progress: Real-time progress tracking
-- 4. Helper functions for run management and statistics
-- 5. Views for common queries (active runs, summaries, recent docs)
-- 6. Indexes for performance

