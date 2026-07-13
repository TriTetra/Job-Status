-- PostgreSQL initialization script
-- Runs once on first container start

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
-- CREATE EXTENSION IF NOT EXISTS "vector";  -- Phase 2: pgvector for LanceDB

-- Timezone
SET timezone = 'UTC';
