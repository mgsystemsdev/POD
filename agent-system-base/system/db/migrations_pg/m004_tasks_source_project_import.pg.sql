-- Extend tasks.source CHECK to allow 'project_import'.

ALTER TABLE tasks DROP CONSTRAINT IF EXISTS tasks_source_check;
ALTER TABLE tasks ADD CONSTRAINT tasks_source_check
  CHECK (source IN ('manual', 'cron', 'api', 'import', 'orchestrator', 'other', 'project_import'))
