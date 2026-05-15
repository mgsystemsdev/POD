# Schemas

## `agent_output.schema.json`

Base JSON Schema for orchestrator step envelopes. **`orchestrator.models.validate_agent_output`** loads this shape.

## `agent_output_v2.schema.json`

Stricter **v2** envelope used by **`orchestrator.models.validate_agent_output_v2`** (called from **`orchestrator/controller.py`** simulate/execute paths and merge validation). The schema file’s `$id` / description note that it documents the v2 mirror; runtime validation is implemented in Python alongside the base validator.

v2 adds expectations such as `run_id`, `step_id`, and agent identity checks on top of the base envelope.

## Agent definitions vs validation

Some `agents/*.json` files list `inputs_schema` / `output_schema` pointing at **`agent_output.schema.json`**. Regardless of that metadata string, **simulate and execute** still validate produced JSON through **`validate_agent_output_v2`**.

## Minimal v2 example (illustrative)

See `runs/examples/` in this repo for committed samples; when authoring new outputs, validate against `agent_output_v2.schema.json` or run the orchestrator in `simulate` mode to generate conforming envelopes.
