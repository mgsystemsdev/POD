#!/usr/bin/env python3
"""
Sync Project State: Fetches the latest project data from the Railway POD API 
and writes it to local .claude/ JSON files for agent context.
"""

import os
import json
import requests
import sys
from pathlib import Path

def load_config():
    config_path = Path(".claude/config.json")
    if not config_path.exists():
        print(f"Error: {config_path} not found. Run project initialization first.")
        sys.exit(1)
    with open(config_path, "r") as f:
        return json.load(f)

def sync():
    config = load_config()
    project_id = config.get("project_id")
    api_url = config.get("api_url", "http://localhost:8765").rstrip("/")
    api_key = config.get("api_key")
    
    headers = {"X-API-Key": api_key} if api_key else {}
    
    endpoints = {
        "blueprints": f"/api/projects/{project_id}/blueprints",
        "requirements": f"/api/projects/{project_id}/requirements", # Note: Placeholder endpoint
        "tasks": f"/api/tasks?project_id={project_id}",
        "decisions": f"/api/projects/{project_id}/decisions",
        "memory": f"/api/projects/{project_id}/memory",
        "session-logs": f"/api/projects/{project_id}/session-logs"
    }
    
    output_dir = Path(".claude/state")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Syncing project {project_id} from {api_url}...")
    
    for resource, path in endpoints.items():
        try:
            response = requests.get(f"{api_url}{path}", headers=headers)
            response.raise_for_status()
            data = response.json()
            
            output_file = output_dir / f"{resource}.json"
            with open(output_file, "w") as f:
                json.dump(data, f, indent=2)
            print(f"  ✓ {resource}.json updated")
            
        except Exception as e:
            print(f"  ✗ Failed to sync {resource}: {e}")

if __name__ == "__main__":
    sync()
