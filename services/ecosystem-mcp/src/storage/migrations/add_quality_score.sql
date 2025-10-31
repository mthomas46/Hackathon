-- Migration: Add document quality scoring fields
-- Date: 2025-10-30
-- Purpose: Add quality_score, quality_grade, and score_breakdown columns for RAG weighting

BEGIN;

-- Add quality score column (0-100)
ALTER TABLE documents
ADD COLUMN IF NOT EXISTS quality_score FLOAT DEFAULT NULL;

-- Add quality grade column (S, A, B, C, D, F)
ALTER TABLE documents
ADD COLUMN IF NOT EXISTS quality_grade VARCHAR(1) DEFAULT NULL;

-- Add score breakdown column (JSONB for detailed breakdown)
ALTER TABLE documents
ADD COLUMN IF NOT EXISTS score_breakdown JSONB DEFAULT NULL;

-- Create index on quality_score for efficient RAG queries
CREATE INDEX IF NOT EXISTS idx_documents_quality_score ON documents(quality_score DESC);

-- Create composite index for quality + latest (common RAG query pattern)
CREATE INDEX IF NOT EXISTS idx_documents_latest_quality ON documents(is_latest, quality_score DESC) WHERE is_latest = TRUE;

-- Create index on quality grade for filtering
CREATE INDEX IF NOT EXISTS idx_documents_quality_grade ON documents(quality_grade);

COMMIT;

-- Verification query
SELECT 
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'documents' 
    AND column_name IN ('quality_score', 'quality_grade', 'score_breakdown')
ORDER BY column_name;

