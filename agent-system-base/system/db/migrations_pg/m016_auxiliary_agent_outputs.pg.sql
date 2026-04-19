-- Auxiliary agent outputs table.

CREATE TABLE IF NOT EXISTS auxiliary_agent_outputs (
  id BIGSERIAL PRIMARY KEY,
  project_id BIGINT NOT NULL REFERENCES projects(id),
  agent_role TEXT NOT NULL,
  content TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected')),
  target_core_agent TEXT,
  related_requirement_ref TEXT,
  related_decision_id BIGINT REFERENCES decisions(id),
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_aao_project_status ON auxiliary_agent_outputs(project_id, status);
CREATE INDEX IF NOT EXISTS idx_aao_agent_role ON auxiliary_agent_outputs(agent_role)
