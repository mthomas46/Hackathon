-- MCP Performance Store Database Schema
-- TimescaleDB optimized for time-series performance data

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Orchestration Executions Table (Time-Series)
CREATE TABLE IF NOT EXISTS orchestration_executions (
    execution_id UUID PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    
    -- Query Information
    query TEXT NOT NULL,
    mcp_id VARCHAR(255) NOT NULL,
    mcp_version VARCHAR(50) NOT NULL,
    pattern_used VARCHAR(100) NOT NULL,
    composition_id VARCHAR(255),
    
    -- Performance Metrics
    latency_ms INTEGER NOT NULL,
    token_usage INTEGER NOT NULL,
    cost_cents DECIMAL(10, 4) NOT NULL,
    success BOOLEAN NOT NULL,
    error TEXT,
    
    -- Quality Metrics
    accuracy_score DECIMAL(5, 4) NOT NULL,
    confidence DECIMAL(5, 4) NOT NULL,
    hallucination_detected BOOLEAN DEFAULT FALSE,
    citation_count INTEGER DEFAULT 0,
    user_satisfaction DECIMAL(5, 4),
    
    -- Context
    prompt TEXT NOT NULL,
    response TEXT NOT NULL,
    context_length INTEGER NOT NULL,
    retrieved_sources JSONB DEFAULT '[]'::jsonb,
    
    -- Environment
    environment VARCHAR(50) NOT NULL,
    user_id VARCHAR(255),
    session_id VARCHAR(255),
    
    -- Metadata
    tags TEXT[],
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Convert to hypertable for time-series optimization
SELECT create_hypertable(
    'orchestration_executions',
    'timestamp',
    if_not_exists => TRUE,
    chunk_time_interval => INTERVAL '1 day'
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_executions_mcp_id ON orchestration_executions(mcp_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_executions_pattern ON orchestration_executions(pattern_used, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_executions_success ON orchestration_executions(success, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_executions_composition ON orchestration_executions(composition_id, timestamp DESC) WHERE composition_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_executions_user ON orchestration_executions(user_id, timestamp DESC) WHERE user_id IS NOT NULL;

-- GIN index for JSONB fields
CREATE INDEX IF NOT EXISTS idx_executions_metadata ON orchestration_executions USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_executions_sources ON orchestration_executions USING GIN (retrieved_sources);

-- Pattern Performance Table (Regular table, not time-series)
CREATE TABLE IF NOT EXISTS pattern_performance (
    pattern_id VARCHAR(255) PRIMARY KEY,
    pattern_name VARCHAR(100) NOT NULL,
    version VARCHAR(50) NOT NULL,
    
    -- Overall Metrics
    total_executions INTEGER DEFAULT 0,
    success_rate DECIMAL(5, 4) DEFAULT 0.0,
    avg_latency_ms DECIMAL(10, 2) DEFAULT 0.0,
    p50_latency_ms DECIMAL(10, 2) DEFAULT 0.0,
    p95_latency_ms DECIMAL(10, 2) DEFAULT 0.0,
    p99_latency_ms DECIMAL(10, 2) DEFAULT 0.0,
    avg_cost_cents DECIMAL(10, 4) DEFAULT 0.0,
    avg_accuracy DECIMAL(5, 4) DEFAULT 0.0,
    avg_confidence DECIMAL(5, 4) DEFAULT 0.0,
    
    -- Time Window Metrics (JSONB for flexibility)
    last_hour JSONB DEFAULT '{}'::jsonb,
    last_day JSONB DEFAULT '{}'::jsonb,
    last_week JSONB DEFAULT '{}'::jsonb,
    last_month JSONB DEFAULT '{}'::jsonb,
    
    -- Trends
    trend_direction VARCHAR(20) DEFAULT 'unknown',
    anomalies_detected JSONB DEFAULT '[]'::jsonb,
    
    -- Timestamps
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(pattern_name, version)
);

-- Indexes for pattern lookups
CREATE INDEX IF NOT EXISTS idx_pattern_name ON pattern_performance(pattern_name);
CREATE INDEX IF NOT EXISTS idx_pattern_trend ON pattern_performance(trend_direction);
CREATE INDEX IF NOT EXISTS idx_pattern_updated ON pattern_performance(last_updated DESC);

-- Continuous Aggregates for Real-Time Analytics

-- Hourly aggregates
CREATE MATERIALIZED VIEW IF NOT EXISTS executions_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', timestamp) AS bucket,
    pattern_used,
    mcp_id,
    COUNT(*) AS total_executions,
    AVG(latency_ms) AS avg_latency,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY latency_ms) AS p50_latency,
    percentile_cont(0.95) WITHIN GROUP (ORDER BY latency_ms) AS p95_latency,
    percentile_cont(0.99) WITHIN GROUP (ORDER BY latency_ms) AS p99_latency,
    AVG(token_usage) AS avg_tokens,
    AVG(cost_cents) AS avg_cost,
    AVG(accuracy_score) AS avg_accuracy,
    AVG(confidence) AS avg_confidence,
    SUM(CASE WHEN success THEN 1 ELSE 0 END)::FLOAT / COUNT(*) AS success_rate,
    SUM(CASE WHEN hallucination_detected THEN 1 ELSE 0 END) AS hallucination_count
FROM orchestration_executions
GROUP BY bucket, pattern_used, mcp_id;

-- Add refresh policy for continuous aggregates
SELECT add_continuous_aggregate_policy('executions_hourly',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- Daily aggregates
CREATE MATERIALIZED VIEW IF NOT EXISTS executions_daily
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', timestamp) AS bucket,
    pattern_used,
    mcp_id,
    COUNT(*) AS total_executions,
    AVG(latency_ms) AS avg_latency,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY latency_ms) AS p50_latency,
    percentile_cont(0.95) WITHIN GROUP (ORDER BY latency_ms) AS p95_latency,
    percentile_cont(0.99) WITHIN GROUP (ORDER BY latency_ms) AS p99_latency,
    AVG(token_usage) AS avg_tokens,
    AVG(cost_cents) AS avg_cost,
    AVG(accuracy_score) AS avg_accuracy,
    AVG(confidence) AS avg_confidence,
    SUM(CASE WHEN success THEN 1 ELSE 0 END)::FLOAT / COUNT(*) AS success_rate
FROM orchestration_executions
GROUP BY bucket, pattern_used, mcp_id;

-- Add refresh policy
SELECT add_continuous_aggregate_policy('executions_daily',
    start_offset => INTERVAL '3 days',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Data Retention Policies

-- Compress old data (older than 7 days)
SELECT add_compression_policy('orchestration_executions',
    INTERVAL '7 days',
    if_not_exists => TRUE
);

-- Drop raw data older than retention period (90 days by default)
SELECT add_retention_policy('orchestration_executions',
    INTERVAL '90 days',
    if_not_exists => TRUE
);

-- Helper Functions

-- Function to calculate quality score
CREATE OR REPLACE FUNCTION calculate_quality_score(
    p_accuracy DECIMAL,
    p_confidence DECIMAL,
    p_hallucination BOOLEAN,
    p_success BOOLEAN,
    p_citations INTEGER,
    p_satisfaction DECIMAL
) RETURNS DECIMAL AS $$
DECLARE
    base_score DECIMAL;
    hallucination_penalty DECIMAL := 0.0;
    error_penalty DECIMAL := 0.0;
    citation_bonus DECIMAL;
    satisfaction_bonus DECIMAL := 0.0;
    quality_score DECIMAL;
BEGIN
    -- Base score from accuracy and confidence
    base_score := (p_accuracy * 0.5) + (p_confidence * 0.3);
    
    -- Penalties
    IF p_hallucination THEN
        hallucination_penalty := 0.2;
    END IF;
    
    IF NOT p_success THEN
        error_penalty := 0.3;
    END IF;
    
    -- Bonuses
    citation_bonus := LEAST(0.1, p_citations * 0.02);
    
    IF p_satisfaction IS NOT NULL THEN
        satisfaction_bonus := p_satisfaction * 0.1;
    END IF;
    
    quality_score := base_score - hallucination_penalty - error_penalty + citation_bonus + satisfaction_bonus;
    
    RETURN GREATEST(0.0, LEAST(1.0, quality_score));
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to detect anomalies
CREATE OR REPLACE FUNCTION detect_anomalous_latency(
    p_latency INTEGER,
    p_pattern VARCHAR,
    p_threshold_factor DECIMAL DEFAULT 2.0
) RETURNS BOOLEAN AS $$
DECLARE
    baseline_latency DECIMAL;
BEGIN
    -- Calculate baseline from recent data
    SELECT AVG(latency_ms) INTO baseline_latency
    FROM orchestration_executions
    WHERE pattern_used = p_pattern
    AND timestamp > NOW() - INTERVAL '1 hour'
    LIMIT 1000;
    
    IF baseline_latency IS NULL THEN
        RETURN FALSE;
    END IF;
    
    RETURN p_latency > (baseline_latency * p_threshold_factor);
END;
$$ LANGUAGE plpgsql;

-- Comments for documentation
COMMENT ON TABLE orchestration_executions IS 'Time-series data for all MCP orchestration executions';
COMMENT ON TABLE pattern_performance IS 'Aggregated performance metrics for LLM patterns';
COMMENT ON MATERIALIZED VIEW executions_hourly IS 'Hourly aggregates of execution metrics';
COMMENT ON MATERIALIZED VIEW executions_daily IS 'Daily aggregates of execution metrics';
