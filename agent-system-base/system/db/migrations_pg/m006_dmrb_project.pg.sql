-- Data migration: create DMRB project and reassign imported tasks from project 1.

INSERT INTO projects (name, slug, root_path, created_at, updated_at)
VALUES (
  'DMRB Production',
  'dmrb',
  '/Users/miguelgonzalez/Projects/Sand box/DRMB_PROD',
  NOW()::TEXT,
  NOW()::TEXT
) ON CONFLICT (slug) DO NOTHING;

UPDATE tasks
SET project_id = (SELECT id FROM projects WHERE slug = 'dmrb'),
    updated_at  = NOW()::TEXT
WHERE project_id = 1
  AND source = 'import'
