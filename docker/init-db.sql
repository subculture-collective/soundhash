-- PostgreSQL initialization script for SoundHash
-- This script runs when the PostgreSQL container starts for the first time

-- Create additional indexes for performance
-- (The main tables are created by SQLAlchemy when the app starts)

-- Set timezone
SET timezone = 'UTC';

-- Optimize PostgreSQL for audio fingerprinting workload
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;

-- Enable extensions that might be useful
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create a function to calculate audio fingerprint similarity
-- (This will be used later for advanced matching)
CREATE OR REPLACE FUNCTION similarity_score(fp1 bytea, fp2 bytea)
RETURNS float AS $$
BEGIN
    -- Placeholder for custom similarity function
    -- For now, return 0.0 - this will be implemented in application logic
    RETURN 0.0;
END;
$$ LANGUAGE plpgsql;