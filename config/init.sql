-- Aegis-AI Database Schema
-- Purpose: Store raw server logs and AI-classified threat intelligence
-- Author: Aditya Batra
-- Date: 2026-03-17

-- Create extension for UUID generation if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Main table: server_logs
-- Stores all incoming log entries with AI classification results
CREATE TABLE IF NOT EXISTS server_logs (
    -- Primary Key: Auto-incrementing unique identifier
    id SERIAL PRIMARY KEY,

    -- Temporal data: When the log event occurred
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Log metadata: Severity level (INFO, WARNING, ERROR, CRITICAL)
    log_level VARCHAR(20) NOT NULL,

    -- Security context: Origin IP address for threat correlation
    source_ip VARCHAR(45) NOT NULL,  -- IPv6 compatible (max 45 chars)

    -- Raw log content: The actual log message
    message TEXT NOT NULL,

    -- AI Analysis Results
    ai_classification VARCHAR(50) DEFAULT NULL,  -- SAFE, SUSPICIOUS, CRITICAL_THREAT

    -- Threat indicator: Boolean flag for quick filtering
    is_threat BOOLEAN DEFAULT FALSE,

    -- Audit trail: When AI analysis was performed
    analyzed_at TIMESTAMP DEFAULT NULL,

    -- Additional context: JSON field for flexible metadata storage
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Performance optimization: Index on timestamp for time-range queries
CREATE INDEX idx_logs_timestamp ON server_logs(timestamp DESC);

-- Security optimization: Index on source_ip for threat actor tracking
CREATE INDEX idx_logs_source_ip ON server_logs(source_ip);

-- Analysis optimization: Index on unclassified logs for AI polling
CREATE INDEX idx_logs_unclassified ON server_logs(ai_classification)
WHERE ai_classification IS NULL;

-- Threat detection optimization: Index on threat flags
CREATE INDEX idx_logs_threats ON server_logs(is_threat)
WHERE is_threat = TRUE;

-- Composite index: For dashboard queries filtering by time + threat status
CREATE INDEX idx_logs_threat_timeline ON server_logs(timestamp DESC, is_threat);

-- Comments for enterprise documentation
COMMENT ON TABLE server_logs IS 'Central repository for all system logs with AI-powered threat classification';
COMMENT ON COLUMN server_logs.ai_classification IS 'AI model output: SAFE, SUSPICIOUS, or CRITICAL_THREAT';
COMMENT ON COLUMN server_logs.is_threat IS 'Quick boolean flag derived from ai_classification for fast filtering';
COMMENT ON COLUMN server_logs.metadata IS 'Extensible JSON field for storing additional context like attack vectors, confidence scores';

-- Insert sample data for testing (optional - will be replaced by generator)
INSERT INTO server_logs (log_level, source_ip, message) VALUES
('INFO', '192.168.1.100', 'User authentication successful for admin'),
('WARNING', '10.0.0.50', 'Multiple failed login attempts detected'),
('ERROR', '172.16.0.5', 'SQL injection attempt blocked: SELECT * FROM users WHERE id=1 OR 1=1');
