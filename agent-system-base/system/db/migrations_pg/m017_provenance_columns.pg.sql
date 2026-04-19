-- Migration: Add provenance columns to core tables (Postgres Safe)

-- Blueprints
DO $$ 
BEGIN 
    BEGIN
        ALTER TABLE blueprints ADD COLUMN created_by TEXT;
    EXCEPTION WHEN duplicate_column THEN
        RAISE NOTICE 'column created_by already exists in blueprints';
    END;
    BEGIN
        ALTER TABLE blueprints ADD COLUMN correlation_id TEXT;
    EXCEPTION WHEN duplicate_column THEN
        RAISE NOTICE 'column correlation_id already exists in blueprints';
    END;
    BEGIN
        ALTER TABLE blueprints ADD COLUMN write_reason TEXT;
    EXCEPTION WHEN duplicate_column THEN
        RAISE NOTICE 'column write_reason already exists in blueprints';
    END;
    BEGIN
        ALTER TABLE blueprints ADD COLUMN source_proposal_ref TEXT;
    EXCEPTION WHEN duplicate_column THEN
        RAISE NOTICE 'column source_proposal_ref already exists in blueprints';
    END;
END $$;

-- Tasks
DO $$ 
BEGIN 
    BEGIN
        ALTER TABLE tasks ADD COLUMN created_by TEXT;
    EXCEPTION WHEN duplicate_column THEN
        RAISE NOTICE 'column created_by already exists in tasks';
    END;
END $$;

-- Decisions
DO $$ 
BEGIN 
    BEGIN
        ALTER TABLE decisions ADD COLUMN created_by TEXT;
    EXCEPTION WHEN duplicate_column THEN
        RAISE NOTICE 'column created_by already exists in decisions';
    END;
    BEGIN
        ALTER TABLE decisions ADD COLUMN correlation_id TEXT;
    EXCEPTION WHEN duplicate_column THEN
        RAISE NOTICE 'column correlation_id already exists in decisions';
    END;
    BEGIN
        ALTER TABLE decisions ADD COLUMN source_proposal_id INTEGER REFERENCES auxiliary_agent_outputs(id);
    EXCEPTION WHEN duplicate_column THEN
        RAISE NOTICE 'column source_proposal_id already exists in decisions';
    END;
END $$;

-- Memory
DO $$ 
BEGIN 
    BEGIN
        ALTER TABLE memory ADD COLUMN created_by TEXT;
    EXCEPTION WHEN duplicate_column THEN
        RAISE NOTICE 'column created_by already exists in memory';
    END;
    BEGIN
        ALTER TABLE memory ADD COLUMN write_reason TEXT;
    EXCEPTION WHEN duplicate_column THEN
        RAISE NOTICE 'column write_reason already exists in memory';
    END;
END $$;
