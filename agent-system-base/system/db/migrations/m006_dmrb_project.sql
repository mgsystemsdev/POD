-- SAFE TO ABORT: run `cp database.sqlite database.sqlite.bak` before applying.
-- Reassigns 132 imported tasks from project 1 (claude-global) to a proper DMRB project.

INSERT INTO projects (name, slug, root_path, created_at, updated_at)
VALUES (
  'DMRB Production',
  'dmrb',
  '/Users/miguelgonzalez/Projects/Sand box/DRMB_PROD',
  datetime('now'),
  datetime('now')
);

UPDATE tasks
SET project_id = (SELECT id FROM projects WHERE slug = 'dmrb'),
    updated_at  = datetime('now')
WHERE project_id = 1
  AND source = 'import';
